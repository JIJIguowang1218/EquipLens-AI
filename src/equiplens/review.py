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

from . import workflow

VIEWS = ["untagged", "hero_lf", "hero_rf", "front", "rear", "side_l", "side_r",
         "ortho_sheet", "detail", "interior", "scene", "nameplate"]

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
 .card a{{color:#0366d6}}
 label{{margin-right:8px}}
 .reason{{width:95%}}
 .bar{{position:sticky;top:0;background:#fff;padding:8px;border-bottom:2px solid #0366d6;margin:-16px -16px 12px}}
 button{{padding:6px 14px;font-size:14px}}
</style></head><body>
<div class="bar"><b>批次 {batch}</b>（{count} 个素材）
 <button onclick="exportDecisions()">✅ 导出 decisions.json</button>
 <span style="color:#888">审完点导出，然后运行: python -m equiplens apply-review decisions.json</span>
</div>
{groups}
<script>
const BATCH_ID = {batch_json};
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

_CARD = """<fieldset class="card" data-asset="{aid}" data-vehicle="{vehicle_id}">
 <legend><b>{label}</b></legend>
 <img src="{thumb}" alt="">
 <div class="meta">{w}x{h}｜{view_label}｜{nature_label}</div>
 <div class="meta">来源: <a href="{url}" target="_blank">{platform}</a>｜授权: {license}</div>
 <div class="meta">{flags}</div>
 <label><input type="radio" name="{aid}" value="accept">接受</label>
 <label><input type="radio" name="{aid}" value="reject">驳回</label>
 <div>对号到当前车型? <label><input type="checkbox" class="dovehicle" checked>是</label></div>
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


def build_review_pack(conn, data_dir: Path, batch_id: str, out_path: Path) -> dict:
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
            flags = "、".join(json.loads(r["quality_flags"] or "[]")) or "无质量标记"
            view_opts = "".join(
                f'<option {"selected" if v == r["view_angle"] else ""}>{v}</option>' for v in VIEWS)
            cards.append(_CARD.format(
                aid=r["id"], vehicle_id=vfield, label=r["id"][:8],
                thumb=_thumb(Path(data_dir), r["file_path"]),
                w=r["width"] or "?", h=r["height"] or "?",
                view_label=r["view_angle"], nature_label=r["asset_nature"],
                url=html.escape(src["url"] or "#"), platform=html.escape(src["platform"] or "未知"),
                license=src["license"], flags=flags, view_opts=view_opts))
        parts_html.append(
            f'<details class="veh" open><summary>{html.escape(head)}'
            f'（{len(items)} 个素材）</summary><div class="grid">{"".join(cards)}</div></details>')

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(_HTML.format(batch=batch_id, batch_json=json.dumps(batch_id),
                                count=len(rows), groups="".join(parts_html)), encoding="utf-8")
    return {"batch_id": batch_id, "assets": len(rows), "groups": len(groups), "out": str(out)}


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
                workflow.reject_asset(conn, aid)
                if d.get("reason"):
                    conn.execute("UPDATE assets SET notes = ? WHERE id = ?",
                                 (f"驳回理由: {d['reason']}", aid))
                    conn.commit()
                summary["rejected"] += 1
            else:
                summary["accepted"] += 1
                if d.get("vehicle_id"):
                    workflow.bind_asset(conn, aid, d["vehicle_id"])
                    summary["bound"] += 1
                if d.get("view") and d["view"] != "untagged":
                    workflow.set_view(conn, aid, d["view"])
        except ValueError:
            summary["skipped"] += 1  # 素材不存在等单条异常: 跳过不中断整批（F3 部分成功原则）
    return summary
