"""审核包（D13）：检索/整理结果的人工审核载体。

build_review_pack: 按批次生成自包含 HTML（缩略图 base64 内嵌，浏览器直接打开，
渐进披露：车型摘要 → 图墙；每图可接受/驳回，驳回留理由）。
apply_review: 回读 decisions.json —— 驳回→reject_asset；接受可携带对号/打标
（R1 起审核页按车型分组时使用）；决策原件归档 data/reviews/。
"""

from __future__ import annotations

import base64
import html
import io
import json
import uuid
from datetime import datetime
from pathlib import Path

from PIL import Image

from . import db as _db
from . import workflow

VIEWS = ["untagged", "hero_45", "hero_lf", "hero_rf", "front", "rear", "side", "side_l", "side_r",
         "ortho_sheet", "detail", "interior", "scene", "nameplate"]
# 人工下拉只给终态（规范 v0.2.4: 待定态=机器过渡态, 人必须定向, 不提供待定选项）
HUMAN_VIEWS = [v for v in VIEWS if v not in ("hero_45", "side")]
ZH_VIEW = {"untagged": "未打标", "hero_lf": "主视角·左前45°", "hero_rf": "主视角·右前45°",
           "hero_45": "3/4前视角·方向待定", "side": "正侧·方向待定",
           "front": "正前", "rear": "正后", "side_l": "左侧", "side_r": "右侧",
           "ortho_sheet": "三视图版", "detail": "局部特写", "interior": "内饰",
           "scene": "场景图", "nameplate": "铭牌/Logo"}
ZH_NATURE = {"untagged": "未打标", "render": "官方渲染", "official_photo": "官方宣传照",
             "real_photo": "实拍", "report_screenshot": "旧报告截图"}
ZH_FLAGS = {"blur": "模糊", "overexposed": "过曝", "occluded": "遮挡",
            "cluttered": "背景杂乱", "watermarked": "有水印", "multi_vehicle": "多车排列"}

_HTML = """<!doctype html>
<html lang="zh"><head><meta charset="utf-8">
<title>检索审核包 {batch}</title>
<style>
 body{{font-family:"Microsoft YaHei",sans-serif;margin:16px;background:#f7f7f7}}
 .veh{{background:#fff;border:1px solid #ddd;border-radius:8px;margin-bottom:14px;padding:10px}}
 .veh>summary{{cursor:pointer;font-weight:bold;font-size:15px}}
 .grid{{display:flex;flex-wrap:wrap;gap:10px;margin-top:8px}}
 .card{{width:230px;border:1px solid #ccc;border-radius:6px;padding:8px;font-size:12px}}
 .card img{{width:100%;height:150px;object-fit:contain;background:#eee}}
 .card .meta{{margin:4px 0;color:#333;word-break:break-all}}
 .card.rejected{{opacity:.42;border-color:#c66}}
 .badge{{font-size:11px;padding:1px 6px;border-radius:8px;margin-left:4px}}
 .badge.pending{{background:#fff3cd;color:#856404}}
 .badge.confirmed{{background:#d4edda;color:#155724}}
 .badge.rejected{{background:#f8d7da;color:#721c24}}
 .card a{{color:#0366d6}}
 label{{margin-right:8px}}
 .reason{{width:95%}}
 .bar{{position:sticky;top:0;background:#fff;padding:8px;border-bottom:2px solid #0366d6;margin:-16px -16px 12px}}
 button{{padding:6px 14px;font-size:14px}}
</style></head><body>
<div class="bar"><b>批次 {batch}</b>（{count} 个素材：{tally}）
 <button onclick="exportDecisions()">✅ 导出 decisions.json</button>
 <span style="color:#888">审完点导出，然后运行: python -m equiplens apply-review decisions.json</span>
</div>
{groups}
<script>
const BATCH_ID = {batch_json};
const LIVE = location.hostname === "127.0.0.1" || location.hostname === "localhost";
function flash(fs, msg) {{
  let b = fs.querySelector(".live-msg");
  if (!b) {{ b = document.createElement("div"); b.className = "live-msg";
    b.style.cssText = "color:#1a7f37;font-size:12px;margin-top:4px"; fs.appendChild(b); }}
  b.textContent = msg;
  setTimeout(() => b.textContent = "", 1800);
}}
if (LIVE) {{
  document.addEventListener("change", async (e) => {{
    const fs = e.target.closest("fieldset[data-asset]");
    if (!fs) return;
    const aid = fs.dataset.asset;
    if (e.target.type === "radio") {{
      const reason = (fs.querySelector(".reason") || {{value: ""}}).value;
      const view = (fs.querySelector(".view") || {{value: ""}}).value;
      const r = await fetch("/decision", {{method: "POST", body: JSON.stringify(
        {{asset_id: aid, action: e.target.value, reason, view,
          vehicle_id: fs.dataset.vehicle || null}})}});
      flash(fs, r.ok ? "✓ 已实时保存" : "✗ 保存失败");
    }} else if (e.target.classList.contains("view")) {{
      const r = await fetch("/view", {{method: "POST", body: JSON.stringify(
        {{asset_id: aid, view: e.target.value}})}});
      flash(fs, r.ok ? "✓ 视角已保存" : "✗ 保存失败");
    }}
  }});
}}
function exportDecisions(){{
  const ds = [];
  document.querySelectorAll('fieldset[data-asset]').forEach(fs => {{
    const action = fs.querySelector('input[type=radio]:checked');
    if (!action) return;
    ds.push({{ asset_id: fs.dataset.asset,
      action: action.value,
      reason: (fs.querySelector('.reason') || {{value:''}}).value,
      vehicle_id: fs.dataset.vehicle || null,
      view: (fs.querySelector('.view') || {{value:''}}).value || null }});
  }});
  const blob = new Blob([JSON.stringify({{batch_id: BATCH_ID, decisions: ds}}, null, 2)],
                        {{type: 'application/json'}});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob); a.download = 'decisions.json'; a.click();
}}
</script>
</body></html>"""

_CARD = """<fieldset class="card {css}" data-asset="{aid}" data-vehicle="{vehicle_id}">
 <legend><b>{label}</b> {badge}</legend>
 <img src="{thumb}" alt="">
 <div class="meta">{w}x{h}｜{view_label}｜{nature_label}</div>
 <div class="meta">来源: <a href="{url}" target="_blank">{platform}</a>｜授权: {license}</div>
 <div class="meta">{flags}</div>
 <div class="meta" style="color:#666">证据: {note}</div>
 <div class="meta" style="color:#a33">{asset_notes}</div>
 {bind_row}
 <label><input type="radio" name="{aid}" value="accept">接受</label>
 <label><input type="radio" name="{aid}" value="reject">驳回</label>
 <div>视角: <select class="view">{view_opts}</select></div>
 <input class="reason" placeholder="驳回理由（可空）">
</fieldset>"""


def _thumb(data_dir: Path, file_path: str) -> str:
    """缩略图 → base64 data URI；解码失败给灰色占位。"""
    try:
        img = Image.open(Path(data_dir) / file_path).convert("RGB")
        img.thumbnail((320, 320))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=70)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return ("data:image/svg+xml;base64," + base64.b64encode(
            b'<svg xmlns="http://www.w3.org/2000/svg" width="320" height="240">'
            b'<rect width="100%" height="100%" fill="#ddd"/></svg>').decode())


def render_review_html(conn, data_dir: Path, batch_id: str) -> tuple[str, dict]:
    """渲染审核包 HTML（服务端实时模式与文件模式共用）。返回 (html, stats)。"""
    rows = conn.execute(
        """SELECT DISTINCT a.* FROM assets a JOIN sources s ON s.asset_id = a.id
           WHERE s.batch_id = ? ORDER BY a.vehicle_id, a.id""", (batch_id,)).fetchall()
    if not rows:
        raise ValueError(f"批次 {batch_id} 无候选素材")

    veh_names = {r["id"]: f"{r['brand']} {r['model_name']}" for r in
                 conn.execute("SELECT id, brand, model_name FROM vehicles")}
    groups: dict[str, list] = {}
    for r in rows:
        groups.setdefault(r["vehicle_id"] or "_pool", []).append(r)

    parts_html = []
    for vid, items in sorted(groups.items(), key=lambda kv: kv[0] or ""):
        if vid == "_pool":
            head, vfield = "待归号池（未对号）", ""
        else:
            head, vfield = veh_names.get(vid, vid), vid
        cards = []
        for r in items:
            src = conn.execute(
                "SELECT * FROM sources WHERE asset_id = ? ORDER BY is_primary DESC LIMIT 1",
                (r["id"],)).fetchone()
            flags = "、".join(ZH_FLAGS.get(f, f) for f in json.loads(r["quality_flags"] or "[]")) or "无质量标记"
            view_opts = "".join(
                f'<option value="{v}" {"selected" if v == r["view_angle"] else ""}>{ZH_VIEW.get(v, v)}</option>'
                for v in HUMAN_VIEWS)
            if r["binding_status"] == "provisional":
                bind_row = '<div class="meta">机器已挂到本车型（接受 = 确认对号）</div>'
            elif vid != "_pool":
                bind_row = '<div class="meta">接受时对号到本车型</div>'
            else:
                bind_row = ""
            status = {"confirmed": "已确认", "rejected": "已驳回"}.get(r["confirm_status"], "待审")
            badge_css = {"confirmed": "confirmed", "rejected": "rejected"}.get(r["confirm_status"], "pending")
            cards.append(_CARD.format(
                aid=r["id"], vehicle_id=vfield, provisional=1 if r["binding_status"] == "provisional" else 0,
                label=r["id"][:8], css="rejected" if r["confirm_status"] == "rejected" else "",
                badge=f'<span class="badge {badge_css}">{status}</span>',
                asset_notes=html.escape(r["notes"] or ""),
                thumb=_thumb(Path(data_dir), r["file_path"]),
                w=r["width"] or "?", h=r["height"] or "?",
                view_label=ZH_VIEW.get(r["view_angle"], r["view_angle"]),
                nature_label=ZH_NATURE.get(r["asset_nature"], r["asset_nature"]),
                url=html.escape(src["url"] or "#"), platform=html.escape(src["platform"] or "未知"),
                license=src["license"], flags=flags, view_opts=view_opts,
                note=html.escape(src["note"] or "（无）"), bind_row=bind_row))
        parts_html.append(
            f'<details class="veh" open><summary>{html.escape(head)}'
            f'（{len(items)} 个素材）</summary><div class="grid">{"".join(cards)}</div></details>')

    from collections import Counter
    tally = Counter("已确认" if r["confirm_status"] == "confirmed"
                    else "已驳回" if r["confirm_status"] == "rejected" else "待审" for r in rows)
    html_text = _HTML.format(batch=batch_id, batch_json=json.dumps(batch_id),
                             count=len(rows),
                             tally=" ".join(f"{k} {v}" for k, v in tally.items()),
                             groups="".join(parts_html))
    stats = {"batch_id": batch_id, "assets": len(rows), "groups": len(groups)}
    return html_text, stats


_PROBE_HTML = """<!doctype html>
<html lang="zh"><head><meta charset="utf-8">
<title>判向复核·探针 {backend}</title>
<style>
 body{{font-family:"Microsoft YaHei",sans-serif;margin:16px;background:#f7f7f7}}
 .veh{{background:#fff;border:1px solid #ddd;border-radius:8px;margin-bottom:14px;padding:10px}}
 .veh>summary{{cursor:pointer;font-weight:bold;font-size:15px}}
 .grid{{display:flex;flex-wrap:wrap;gap:10px;margin-top:8px}}
 .card{{width:250px;border:1px solid #ccc;border-radius:6px;padding:8px;font-size:12px}}
 .card img{{width:100%;height:150px;object-fit:contain;background:#eee}}
 .card .meta{{margin:4px 0;color:#333;word-break:break-all}}
 .badge{{font-size:11px;padding:1px 6px;border-radius:8px;margin-left:4px;background:#e2e3ff;color:#2a2a8c}}
 .chg{{color:#a33;font-weight:bold}}
 .bar{{position:sticky;top:0;background:#fff;padding:8px;border-bottom:2px solid #0366d6;margin:-16px -16px 12px}}
</style></head><body>
<div class="bar"><b>判向复核·探针 {backend}</b>（{count} 张：{tally}）——
 下拉改成对的视角即<b>实时落账</b>（改过即人工值）；机器建议仅供参考，<b>方向以人眼为准</b></div>
{groups}
<script>
const LIVE = location.hostname === "127.0.0.1" || location.hostname === "localhost";
function flash(fs, msg) {{
  let b = fs.querySelector(".live-msg");
  if (!b) {{ b = document.createElement("div"); b.className = "live-msg";
    b.style.cssText = "color:#1a7f37;font-size:12px;margin-top:4px"; fs.appendChild(b); }}
  b.textContent = msg;
  setTimeout(() => b.textContent = "", 1800);
}}
if (LIVE) {{
  document.addEventListener("change", async (e) => {{
    const fs = e.target.closest("fieldset[data-asset]");
    if (!fs || !e.target.classList.contains("view")) return;
    const r = await fetch("/view", {{method: "POST", body: JSON.stringify(
      {{asset_id: fs.dataset.asset, view: e.target.value}})}});
    flash(fs, r.ok ? "✓ 视角已保存" : "✗ 保存失败");
  }});
}}
</script>
</body></html>"""


def render_probe_review_html(conn, data_dir: Path, suggest_path) -> tuple[str, dict]:
    """判向复核页（T12）：探针 v2 建议 vs 机器原值, 人工下拉定向实时落账。
    suggest_path: data-test/probe-suggest.json（probe-suggest 产出）。"""
    pack = json.loads(Path(suggest_path).read_text(encoding="utf-8"))
    veh_names = {r["id"]: f"{r['brand']} {r['model_name']}" for r in
                 conn.execute("SELECT id, brand, model_name FROM vehicles")}
    groups: dict[str, list] = {}
    for s in pack["suggestions"]:
        groups.setdefault(s["vehicle_id"] or "_pool", []).append(s)
    parts = []
    for vid, items in sorted(groups.items(), key=lambda kv: kv[0] or ""):
        head = veh_names.get(vid, "待归号池") if vid != "_pool" else "待归号池"
        cards = []
        for s in items:
            r = conn.execute("SELECT * FROM assets WHERE id=?", (s["asset_id"],)).fetchone()
            if r is None:
                continue
            cur = r["view_angle"]
            changed = "" if cur == s["suggested"] else ' class="chg"'
            opts = "".join(
                f'<option value="{v}" {"selected" if v == cur else ""}>{ZH_VIEW.get(v, v)}</option>'
                for v in HUMAN_VIEWS)
            mirror = f'｜镜检 orig={s["mirror"]["orig"]} flip={s["mirror"]["flip"]}' \
                if s.get("mirror") else ""
            scores = " ".join(f"{ZH_VIEW.get(k, k)}={v}" for k, v in s["scores"].items())
            if cur == s["suggested"]:
                delta = (f'<div class="meta">本轮已按机器建议落账'
                         f'（原机器值: {ZH_VIEW.get(s["current"], s["current"])}，仅历史记录）</div>')
            else:
                delta = (f'<div class="meta{changed}">机器原值: {ZH_VIEW.get(s["current"], s["current"])}'
                         f' → 建议: {ZH_VIEW.get(s["suggested"], s["suggested"])}（裕量 {s["margin"]}）</div>')
            cards.append(f'''<fieldset class="card" data-asset="{s["asset_id"]}">
 <legend><b>{r["id"][:8]}</b><span class="badge">{ZH_VIEW.get(s["suggested"], s["suggested"])}</span></legend>
 <img src="{_thumb(Path(data_dir), r["file_path"])}" alt="">
 <div class="meta">{veh_names.get(s["vehicle_id"], "")}｜{r["width"] or "?"}x{r["height"] or "?"}</div>
 {delta}
 <div class="meta">{s["reason"]}{mirror}</div>
 <div class="meta" style="color:#888">{scores}</div>
 <div class="meta">人工定向: <select class="view">{opts}</select></div>
</fieldset>''')
        parts.append(f'<details class="veh" open><summary>{html.escape(head)}'
                     f'（{len(items)} 张）</summary><div class="grid">{"".join(cards)}</div></details>')
    from collections import Counter
    tally = Counter(s["suggested"] for s in pack["suggestions"])
    html_text = _PROBE_HTML.format(
        backend=pack.get("backend", "?"), count=len(pack["suggestions"]),
        tally=" ".join(f"{ZH_VIEW.get(k, k)}×{v}" for k, v in tally.most_common()),
        groups="".join(parts))
    return html_text, {"assets": len(pack["suggestions"]), "groups": len(groups)}


def build_review_pack(conn, data_dir: Path, batch_id: str, out_path: Path) -> dict:
    """文件模式: 生成离线 HTML。实时模式用 render_review_html + reviewserver。"""
    html_text, stats = render_review_html(conn, data_dir, batch_id)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html_text, encoding="utf-8")
    stats["out"] = str(out)
    return stats


def apply_review(conn, decisions_input, data_dir: Path) -> dict:
    """回读审核决策。decisions_input: JSON 文件路径或 dict。

    驳回 → reject_asset（理由入 notes）；接受 → 若勾选对号则 bind + 视角打标。
    决策原件归档 data/reviews/<batch>-<时间>.json（审计不进账本，账本只记状态变更）。
    """
    if isinstance(decisions_input, (str, Path)):
        decisions = json.loads(Path(decisions_input).read_text(encoding="utf-8"))
    else:
        decisions = decisions_input
    batch_id = decisions.get("batch_id", "unknown")
    data_dir = Path(data_dir)
    arch = data_dir / "reviews"
    arch.mkdir(parents=True, exist_ok=True)
    (arch / f"{batch_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json").write_text(
        json.dumps(decisions, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {"accepted": 0, "rejected": 0, "bound": 0, "skipped": 0}
    for d in decisions.get("decisions", []):
        aid, action = d.get("asset_id"), d.get("action")
        if not aid or action not in ("accept", "reject"):
            summary["skipped"] += 1
            continue
        try:
            if action == "reject":
                row = conn.execute("SELECT confirm_status FROM assets WHERE id = ?",
                                   (aid,)).fetchone()
                if row is None:
                    raise ValueError(f"素材 {aid} 不存在")
                if row["confirm_status"] == "rejected":
                    summary["rejected"] += 1  # 幂等: 已驳回不重复落账
                    continue
                workflow.reject_asset(conn, aid)
                if d.get("reason"):
                    conn.execute("UPDATE assets SET notes = ? WHERE id = ?",
                                 (f"驳回理由: {d['reason']}", aid))
                    conn.commit()
                summary["rejected"] += 1
            else:
                row = conn.execute("SELECT binding_status, confirm_status FROM assets WHERE id = ?",
                                   (aid,)).fetchone()
                if row is None:
                    raise ValueError(f"素材 {aid} 不存在")
                if row["confirm_status"] == "rejected":
                    summary["skipped"] += 1  # 已驳回素材不复活
                    continue
                summary["accepted"] += 1
                if row["binding_status"] == "provisional":
                    # T2 机器挂载 → 人工接受 = 确认对号, 证据升级为 human
                    old_ev = conn.execute("SELECT binding_evidence FROM assets WHERE id = ?",
                                          (aid,)).fetchone()["binding_evidence"]
                    _db.confirm_many(conn, [
                        ("asset", aid, "binding_status", "provisional", "confirmed"),
                        ("asset", aid, "binding_evidence", old_ev, "human"),
                    ], op_id=f"op-accept-{uuid.uuid4().hex[:8]}", method="batch")
                    summary["bound"] += 1
                elif row["binding_status"] == "unbound" and d.get("vehicle_id"):
                    workflow.bind_asset(conn, aid, d["vehicle_id"])
                    summary["bound"] += 1
                if row["confirm_status"] == "machine_tagged":
                    # 人工接受 = 确认素材可用（与驳回对称, 状态可见可撤销）
                    _db.confirm(conn, "asset", aid, "confirm_status",
                                "machine_tagged", "confirmed",
                                method="batch", op_id=f"op-accept-{uuid.uuid4().hex[:8]}")
                if d.get("view") and d["view"] != "untagged":
                    workflow.set_view(conn, aid, d["view"])
        except ValueError:
            summary["skipped"] += 1  # 素材不存在等单条异常: 跳过不中断整批（F3 部分成功原则）
    return summary
