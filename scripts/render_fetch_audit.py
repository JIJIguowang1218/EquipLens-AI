# -*- coding: utf-8 -*-
"""把 loop 抓取日志渲染成人工审核页（含未通过门卫的图）。

用法:
  python scripts/render_fetch_audit.py data-test/runs/loop-c01-audit
"""
from __future__ import annotations

import html
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

REASON_CN = {
    "too_small": "过长边/宽下限（<320/350）",
    "undecodable": "无法解码",
    "too_large": ">8MB",
    "animated": "动图",
    "extreme_aspect": "长宽比 >4",
    "near_uniform": "近空白/纯色",
    "gate_drop": "CLIP 反例胜出",
    "interior_suspect": "内饰强信号",
    "low_res_overview": "长边 <800",
    "low_res_part": "长边 <1200",
}
LABEL_CN = {
    "row or lineup": "多车队列",
    "interior cabin": "内饰舱",
    "grid or collage": "网格拼图",
    "screenshot of a web page": "网页截图",
    "advertisement": "广告字",
    "passenger bus": "客车",
    "logo, icon": "logo/图标",
    "chart, diagram": "图表",
    "people, a meeting": "人物会议",
    "building, office": "建筑室内",
    "text document": "文档截图",
    "one truck in the foreground": "主体一台+背景车",
    "single truck in the foreground": "主体一台+背景车",
    "single heavy truck": "单台重卡",
    "construction machinery": "工程车",
    "close-up photo of a truck part": "部件特写",
}


def label_cn(s: str) -> str:
    t = (s or "").lower()
    for k, v in LABEL_CN.items():
        if k in t:
            return v
    return (s or "")[:18]


def main(argv=None) -> int:
    run_dir = Path(argv[1] if argv and len(argv) > 1 else
                   "data-test/runs/loop-c01-audit")
    log = run_dir / "fetch_log.jsonl"
    if not log.exists():
        print(f"missing {log}")
        return 1
    rows = [json.loads(x) for x in
            log.read_text(encoding="utf-8").splitlines() if x.strip()]

    merged: dict[tuple, dict] = {}
    for r in rows:
        if not r.get("ok"):
            continue
        key = (r["model"], r.get("sha1"))
        m = merged.get(key)
        if m is None:
            m = dict(r)
            m["parts"] = [r.get("part")]
            merged[key] = m
        else:
            if r.get("part") not in m["parts"]:
                m["parts"].append(r.get("part"))
            m["res_standard"] = m.get("res_standard") or r.get("res_standard")
            m["res_high"] = m.get("res_high") or r.get("res_high")
            m["reference_ok"] = m.get("reference_ok") or r.get("reference_ok")
    items = sorted(merged.values(),
                   key=lambda x: (x["model"], -(x.get("margin") or -9)))
    failed = [r for r in rows if not r.get("ok")]

    # “过门卫”只是 CLIP/预筛语义；进交付包还要“车型占槽 + 图写进 state.assets”。
    # 分辨率只做档位标记，绝不从交付包里删图（2026-11-10 口径）。
    selected_ids: set[str] = set()
    package_by_model: dict[str, set[str]] = {}
    delivered_models: set[str] = set()
    identity_by_model: dict[str, str] = {}
    state_path = run_dir / "state.json"
    if state_path.exists():
        try:
            st = json.loads(state_path.read_text(encoding="utf-8"))
            # 占槽车型以 units.accepted_targets 为准；assets 里还有“抓过图但没占槽”的
            delivered_models = {tid for u in (st.get("units") or {}).values()
                                for tid in (u.get("accepted_targets") or [])}
            package_by_model = {
                tid: {a for v in ((st.get("assets") or {}).get(tid) or {}).values()
                      for a in (v or [])}
                for tid in delivered_models
            }
            package_ids = {a for ids in package_by_model.values() for a in ids}
            identity_by_model = {
                tid: (t.get("identity_kind") or "")
                for tid, t in (st.get("targets") or {}).items()
            }
            # “已核验”= 属于交付包，且有 accepted 的核验记录
            for key, rec in (st.get("verifications") or {}).items():
                aid = key.split(":")[0]
                if rec.get("accepted") and aid in package_ids:
                    selected_ids.add(aid)
        except (json.JSONDecodeError, OSError):
            selected_ids, package_by_model, delivered_models = set(), {}, set()
            identity_by_model = {}
    for it in items:
        it["identity_kind"] = identity_by_model.get(it["model"], "")
        it["selected"] = it.get("sha1") in selected_ids
        it["in_package"] = it.get("sha1") in package_by_model.get(it["model"], set())
        it["delivered"] = it["model"] in delivered_models

    per_model = defaultdict(Counter)
    for it in items:
        c = per_model[it["model"]]
        c["total"] += 1
        c["pass"] += bool(it.get("gate_pass"))
        c["selected"] += bool(it.get("selected"))
        c["pkg"] += bool(it.get("in_package"))
        c["delivered"] = 1 if it.get("delivered") else 0
        c["ov"] += bool(it.get("res_standard", it.get("overview_ok")))
        c["part"] += bool(it.get("res_high", it.get("part_ok")))
        c["ref"] += bool(it.get("reference_ok"))
    for r in failed:
        per_model[r["model"]]["fail_dl"] += 1

    def chip(label, value, cls=""):
        return (f'<div class="stat {cls}"><b>{value}</b>'
                f'<span>{html.escape(label)}</span></div>')

    def fail_text(it: dict) -> str:
        """具体拒绝原因：优先写清“哪个反例胜出”，而不是笼统的“CLIP 拒绝”。"""
        if it.get("stage") == "prefilter":
            pre = it.get("pre_reasons") or []
            return "预筛拒绝：" + "、".join(REASON_CN.get(x, x) for x in pre)
        if not it.get("gate_pass"):
            drop = label_cn(it.get("drop_label", ""))
            keep = label_cn(it.get("keep_label", ""))
            margin = it.get("margin")
            m = f"{margin:+.4f}" if margin is not None else "—"
            return (f"CLIP 拒绝：“{drop}”胜出"
                    f"（{m} = keep {keep} {(it.get('keep') or 0):+.4f}"
                    f" − drop {drop} {(it.get('drop') or 0):+.4f}）")
        reasons = it.get("reasons") or []
        if reasons:
            return "分辨率/分层：" + "、".join(REASON_CN.get(x, x) for x in reasons)
        return ""

    IDENTITY_CN = {"code": "型号码", "series": "车系", "generic": "泛称"}
    cards = []
    for it in items:
        if it.get("selected"):
            cls, badge = "slot", "已交付 · 已核验"
        elif it.get("in_package"):
            cls, badge = "pkg", "已交付 · 未核验"
        elif it.get("gate_pass"):
            cls, badge = "warn", "备选 · 未占槽"
        else:
            cls, badge = "bad", "未过门卫"
        if it.get("res_standard"):
            badge += " · 标准"
        if it.get("res_high"):
            badge += " · 高清"
        elif it.get("reference_ok"):
            badge += " · 低清参考"
        margin = it.get("margin")
        margin_txt = f"{margin:+.4f}" if margin is not None else "—"
        chips = "".join(
            f'<span class="chip">{html.escape(REASON_CN.get(x, x))}</span>'
            for x in (it.get("reasons") or []))
        ftext = fail_text(it)
        fail_block = (f'<p class="fail">{html.escape(ftext)}</p>' if ftext else "")
        cards.append(
            f'<article class="card" data-pass="{1 if it.get("gate_pass") else 0}"'
            f' data-sel="{1 if it.get("selected") else 0}"'
            f' data-pkg="{1 if it.get("in_package") else 0}"'
            f' data-ov="{1 if it.get("res_standard") else 0}"'
            f' data-part="{1 if it.get("res_high") else 0}"'
            f' data-ref="{1 if it.get("reference_ok") else 0}"'
            f' data-generic="{1 if it.get("identity_kind") == "generic" else 0}">'
            f'<div class="thumb"><img loading="lazy" src="images/{html.escape(it["image"])}" alt="">'
            f'<span class="badge {cls}">{html.escape(badge)}</span></div>'
            f'<div class="body"><h3>{html.escape(it["model"])}'
            f'{"" if it.get("delivered") else "（未占槽车型）"}</h3>'
            f'<p class="sub">{it["width"]}×{it["height"]} · 裕量 {margin_txt}'
            f' · 部件 {html.escape(",".join(it["parts"]))}'
            f' · 交付包 {"是" if it.get("in_package") else "否"}'
            f' · 身份 {IDENTITY_CN.get(it.get("identity_kind") or "", "—")}</p>'
            f'<p class="sub">keep {html.escape(label_cn(it.get("keep_label", "")))} '
            f'{(it.get("keep") or 0):+.4f} ／ drop '
            f'{html.escape(label_cn(it.get("drop_label", "")))} {(it.get("drop") or 0):+.4f}</p>'
            f'<p class="sub">视角 {html.escape(str(it.get("view") or "—"))}'
            f' · gap {it.get("view_gap") or 0:.4f}'
            f' · 门卫 {html.escape(str(it.get("gate_version")))}</p>'
            f'<p class="chips">{chips}</p>{fail_block}'
            f'<p class="url">{html.escape((it.get("url") or "")[:90])}</p>'
            f'</div></article>')

    total = len(items)
    passed = sum(1 for i in items if i.get("gate_pass"))
    selected = sum(1 for i in items if i.get("selected"))
    packaged = sum(1 for i in items if i.get("in_package"))
    extras = passed - packaged
    generic = sum(1 for i in items if i.get("identity_kind") == "generic")
    ov = sum(1 for i in items if i.get("res_standard"))
    part = sum(1 for i in items if i.get("res_high"))
    ref = sum(1 for i in items if i.get("reference_ok"))
    models = len({i["model"] for i in items})
    global_unique = len({i.get("sha1") for i in items})

    model_rows = "".join(
        f"<tr><td>{'✓ ' if c['delivered'] else ''}{html.escape(m)}</td>"
        f"<td>{c['total']}</td><td>{c['pkg']}</td><td>{c['selected']}</td>"
        f"<td>{c['pass']}</td><td>{c['ov']}</td><td>{c['part']}</td><td>{c['ref']}</td>"
        f"<td>{c['fail_dl']}</td></tr>"
        for m, c in sorted(per_model.items(),
                           key=lambda kv: (-kv[1]["delivered"], -kv[1]["part"],
                                           -kv[1]["pass"])))

    css = """
:root{--bg:#0f1012;--card:#181A1D;--line:#2A2D31;--ink:#E8E6E1;--dim:#8C9095;
--ok:#3E9E6A;--bad:#C8442E}
body{margin:0;background:var(--bg);color:var(--ink);
font:14px/1.5 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
header{padding:26px 30px 12px;border-bottom:1px solid var(--line)}
h1{margin:0 0 4px;font-size:20px}.meta{color:var(--dim);font-size:12px}
.sum{display:flex;flex-wrap:wrap;gap:10px;padding:16px 30px;border-bottom:1px solid var(--line)}
.stat{background:var(--card);border:1px solid var(--line);border-radius:8px;
padding:8px 12px;min-width:96px}
.stat b{display:block;font:600 18px/1.2 ui-monospace,Consolas,monospace}
.stat span{color:var(--dim);font-size:11px}
.stat.ok b{color:var(--ok)}.stat.bad b{color:var(--bad)}
.stat.warn b{color:#D9A441}
table{border-collapse:collapse;margin:14px 30px;font-size:12px}
th,td{border:1px solid var(--line);padding:4px 10px;text-align:left}
th{color:var(--dim);font-weight:400;background:#1B1E22}
.filters{display:flex;gap:8px;flex-wrap:wrap;padding:10px 30px;
border-bottom:1px solid var(--line)}
.filters button{background:transparent;color:var(--ink);border:1px solid var(--line);
border-radius:999px;padding:5px 12px;font-size:12px;cursor:pointer}
.filters button.on{background:#DF4A1B;border-color:#DF4A1B}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));
gap:16px;padding:20px 30px 60px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;
overflow:hidden}
.thumb{position:relative;background:#000;aspect-ratio:16/10}
.thumb img{width:100%;height:100%;object-fit:contain}
.badge{position:absolute;left:8px;top:8px;font-size:11px;padding:2px 8px;
border-radius:999px;color:#fff;background:var(--bad)}
.badge.ok,.badge.slot{background:var(--ok)}
.badge.pkg{background:#3E6E9E}
.badge.warn{background:#B07A25}
.body{padding:10px 12px 12px}
h3{margin:0 0 4px;font-size:13px}
.sub{margin:0 0 4px;color:var(--dim);font-size:11px}
.chips{margin:6px 0 0;display:flex;gap:5px;flex-wrap:wrap}
.chip{font-size:10.5px;padding:2px 7px;border-radius:4px;background:#2A2020;
color:#E6A99B;border:1px solid #3A2A26}
.url{margin:6px 0 0;color:#5C6167;font-size:10px;word-break:break-all}
.fail{margin:7px 0 0;padding:6px 8px;border-radius:5px;background:#2A1E1B;
border:1px solid #432C26;color:#F0B6A6;font-size:11px;line-height:1.45}
"""
    js = """
const cards=[...document.querySelectorAll('.card')];
const F={all:()=>true,slot:c=>c.dataset.sel==='1',pkg:c=>c.dataset.pkg==='1',
sel:c=>c.dataset.sel==='1',pass:c=>c.dataset.pass==='1',
extra:c=>c.dataset.pass==='1'&&c.dataset.pkg==='0',
fail:c=>c.dataset.pass==='0',generic:c=>c.dataset.generic==='1',
ov:c=>c.dataset.ov==='1',part:c=>c.dataset.part==='1',ref:c=>c.dataset.ref==='1'};
let cur='all';
function apply(){cards.forEach(c=>c.style.display=F[cur](c)?'':'none');
document.querySelectorAll('.filters button').forEach(b=>b.classList.toggle('on',b.dataset.f===cur));}
document.querySelectorAll('.filters button').forEach(b=>b.onclick=()=>{cur=b.dataset.f;apply();});
apply();
"""
    gate_version = (items[0].get("gate_version") if items else "?")
    doc = (
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
        f"<title>检索抓取审核 · {run_dir.name}</title><style>{css}</style></head><body>"
        f"<header><h1>检索抓取审核 · {run_dir.name}</h1>"
        f'<p class="meta">门卫版本 {html.escape(str(gate_version))}'
        f" · 图 {total} 张（车型内按 sha1 去重）/ 全局唯一 {global_unique} · 下载失败行 {len(failed)}"
        f" · 生成于 {time.strftime('%Y-%m-%d %H:%M')}</p>"
        '<p class="meta">口径：<b>过门卫</b> = 预筛 + CLIP 语义通过（分辨率只分档，<b>不淘汰</b>）；'
        '<b>已交付</b> = 属于占槽车型、写进了交付包；'
        '<b>已核验</b> = 另有规则核验通过的记录。'
        '过门卫但车型没占槽的图标“备选 · 未占槽”，仍保留在 images/ 里可人工取用。</p></header>'
        '<section class="sum">'
        + chip("车型", models) + chip("图（车型内去重）", total)
        + chip("全局唯一图", global_unique)
        + chip("交付车型", f"{len(delivered_models)}", "ok")
        + chip("交付包图", packaged, "ok")
        + chip("其中已核验", selected, "ok")
        + chip("备选（未占槽）", extras, "warn")
        + chip("过门卫合计", passed, "ok")
        + chip("标准清晰 ≥800", ov, "ok")
        + chip("高清 ≥1200", part, "ok") + chip("低清参考", ref)
        + chip("泛称车型", generic, "warn")
        + chip("未过门卫", total - passed, "bad")
        + "</section>"
        "<table><tr><th>车型（✓=已占槽）</th><th>总图</th><th>交付包</th><th>已核验</th>"
        "<th>过门卫</th><th>概览</th><th>部件</th><th>参考</th><th>下载失败</th></tr>"
        f"{model_rows}</table>"
        '<div class="filters">'
        f'<button class="on" data-f="all">全部 {total}</button>'
        f'<button data-f="pkg">交付包 {packaged}</button>'
        f'<button data-f="slot">已核验 {selected}</button>'
        f'<button data-f="extra">备选·未占槽 {extras}</button>'
        f'<button data-f="pass">过门卫 {passed}</button>'
        f'<button data-f="fail">未过门卫 {total - passed}</button>'
        f'<button data-f="ov">概览 {ov}</button>'
        f'<button data-f="part">高清≥1200 {part}</button>'
        f'<button data-f="ref">参考 {ref}</button>'
        f'<button data-f="generic">泛称车型 {generic}</button>'
        f'</div><main class="grid">{"".join(cards)}</main>'
        f"<script>{js}</script></body></html>"
    )
    out = run_dir / "audit.html"
    out.write_text(doc, encoding="utf-8")
    print(json.dumps({"images": total, "package": packaged, "verified": selected,
                      "delivered_models": len(delivered_models),
                      "pass": passed, "extra": extras,
                      "overview": ov, "part": part, "reference": ref,
                      "models": models, "failed_downloads": len(failed)},
                     ensure_ascii=False))
    print(f"out: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
