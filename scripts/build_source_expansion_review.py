# -*- coding: utf-8 -*-
"""把扩源测试的 34 张门卫通过图渲染成人工核对页（本地缩略图）。"""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
from equiplens.imagesearch import _fetch_image  # noqa: E402

BASE = ROOT / "data-test" / "evals" / "source-expansion-review-20261111"
SRC = ROOT / "data-test" / "evals" / "source-expansion-verify-20261111.json"


def esc(v) -> str:
    return html.escape(str(v or ""))


def main() -> int:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    rows = []
    for rec in data:
        for i, r in enumerate(rec["rows"]):
            rows.append({**r, "group": rec["group"], "query": rec["query"], "i": i})
    img_dir = BASE / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    cards = []
    for n, r in enumerate(rows, 1):
        local = ""
        try:
            data_bytes = _fetch_image(r["url"], r.get("source") or "https://image.so.com/")
            if data_bytes:
                local = f"images/{n:02d}.jpg"
                (BASE / local).write_bytes(data_bytes)
        except Exception:  # noqa: BLE001
            pass
        ident = r.get("ident") or "unknown"
        accepted = "是" if r.get("accepted") else "否"
        reason = {
            "confirmed": "型号码命中标题",
            "probable": "品牌/车系 + 构型命中（或两个非通用词）",
            "unknown": "标题只有通用词/对不上目标；核验 unknown",
        }.get(ident, "")
        img = (f"<img src='{local}' loading='lazy' alt='{esc(r.get('title'))}'>"
               if local else f"<img src='{esc(r['url'])}' loading='lazy' referrerpolicy='no-referrer'>")
        cards.append(f"""
<article class="card" data-k="{n}">
  <div class="img">{img}</div>
  <div class="meta">
    <div class="badges"><span class="b {ident}">{ident}</span><span class="b">核验通过：{accepted}</span></div>
    <p><b>目标：</b>{esc(r['group'])}</p>
    <p><b>测试 query：</b>{esc(r['query'])}</p>
    <p><b>标题：</b>{esc(r.get('title') or '（空）')}</p>
    <p class="why"><b>核验理由：</b>{esc(reason)} {esc('；'.join(r.get('defects') or []))}</p>
    <p><a href="{esc(r['url'])}" target="_blank">原图 URL</a>
       {' · <a href="'+esc(r['source'])+'" target="_blank">来源页</a>' if r.get('source') else ''}</p>
    <label>我的判断：<select data-v="v{n}"><option value="">—</option><option>是目标车</option><option>不是</option><option>不确定</option></select></label>
    <label>备注<input data-v="n{n}" placeholder="可选"></label>
  </div>
</article>""")
    counts = {}
    for r in rows:
        counts[r.get("ident") or "unknown"] = counts.get(r.get("ident") or "unknown", 0) + 1
    doc = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<title>扩源测试 34 张图核对</title><style>
body{{margin:0;background:#f5f4f1;color:#1d1d1f;font:14px/1.5 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}}
header{{padding:24px 32px;border-bottom:1px solid #ddd;background:#efece6}}
h1{{margin:0 0 6px;font-size:20px}}p{{margin:3px 0}}.muted{{color:#6e6e73;font-size:12px}}
main{{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:14px;padding:20px 32px 60px}}
.card{{background:#fff;border:1px solid #ddd;border-radius:9px;overflow:hidden;display:flex;flex-direction:column}}
.img{{height:220px;background:#eee;display:flex;align-items:center;justify-content:center}}
.img img{{max-width:100%;max-height:220px;object-fit:contain}}
.meta{{padding:10px 12px;font-size:12px}}.badges{{display:flex;gap:6px;margin-bottom:5px}}
.b{{padding:2px 7px;border-radius:999px;background:#f1efe9;border:1px solid #ddd;font-size:11px}}
.b.probable{{background:#eef7f1;color:#2f7d4f;border-color:#b9d8c5}}
.b.unknown{{background:#fbefed;color:#b23b2e;border-color:#e3c3bd}}
.b.confirmed{{background:#e8f0fb;color:#245b9c;border-color:#bfd2ee}}
.why{{color:#555}}label{{display:block;margin:5px 0;color:#555}}
select,input{{width:100%;padding:3px;border:1px solid #ccc;border-radius:4px;font:inherit}}
.bar{{position:sticky;top:0;background:#f5f4f1;border-bottom:1px solid #ddd;padding:8px 32px;display:flex;gap:10px;align-items:center;z-index:2}}
button{{padding:6px 12px;border:1px solid #ccc;border-radius:6px;background:#fff;cursor:pointer}}
button.p{{background:#1d1d1f;color:#fff;border-color:#1d1d1f}}
</style></head><body>
<header><h1>扩源测试：34 张门卫通过图</h1>
<p class="muted">目标来自 3 个无图车型；测试 query 是短查询 + 来源页 harvest。门卫都通过，核验绝大多数 unknown。</p>
<p>核验分布：{esc(counts)}；核验通过仅 1 张（probable）。正常 run 的逐图核验通过率约 80–92%，本次约 3%。</p></header>
<div class="bar"><button class="p" id="save">保存到浏览器</button><button id="export">导出核对 JSON</button><span class="muted" id="st">改选后自动保存</span></div>
<main>{''.join(cards)}</main>
<script>
const KEY='source-expansion-review-20261111';
const all=JSON.parse(localStorage.getItem(KEY)||'{{}}');
document.querySelectorAll('[data-v]').forEach(el=>{{
  if(all[el.dataset.v]!==undefined) el.value=all[el.dataset.v];
  el.addEventListener('input',()=>{{all[el.dataset.v]=el.value;localStorage.setItem(KEY,JSON.stringify(all));document.getElementById('st').textContent='已保存 '+new Date().toLocaleTimeString();}});
}});
document.getElementById('save').onclick=()=>{{localStorage.setItem(KEY,JSON.stringify(all));document.getElementById('st').textContent='已保存';}};
document.getElementById('export').onclick=()=>{{const b=new Blob([JSON.stringify(all,null,1)],{{type:'application/json'}});const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='source-expansion-review.json';a.click();}};
</script></body></html>"""
    BASE.mkdir(parents=True, exist_ok=True)
    (BASE / "review.html").write_text(doc, encoding="utf-8")
    (BASE / "review-data.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"out": str(BASE / "review.html"), "rows": len(rows),
                      "images": len(list(img_dir.glob('*.jpg'))), "counts": counts},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
