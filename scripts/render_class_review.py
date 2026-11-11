# -*- coding: utf-8 -*-
"""类目词 query 盲评：accepted pending 全部 + unknown pending 分层抽样。"""
from __future__ import annotations

import html
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data-test" / "runs" / "source-expansion-class-query-20261111"
OUT = ROOT / "data-test" / "evals" / "source-expansion-class-review-20261111"
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass


def e(v):
    return html.escape(str(v or ""))


def main() -> int:
    rows = json.loads((SRC / "class-funnel.json").read_text(encoding="utf-8"))["images"]
    accepted = [r for r in rows if r["accepted"] and r["human_label"] == "pending"]
    unknown = [r for r in rows if not r["accepted"] and r["human_label"] == "pending"]
    by = defaultdict(list)
    for r in unknown:
        by[r["brief"]].append(r)
    sample = []
    # 每个 brief 至少 2，最多 5；总数控制 22
    for brief in sorted(by):
        sample.extend(by[brief][:3])
    sample = sample[:22]
    selected = accepted + sample
    OUT.mkdir(parents=True, exist_ok=True)
    imgdir = OUT / "images"
    imgdir.mkdir(exist_ok=True)
    cards = []
    for n, r in enumerate(selected, 1):
        local = ""
        src = SRC / (r.get("image") or "")
        if r.get("image") and src.exists():
            dst = imgdir / f"{n:03d}.jpg"
            try:
                from PIL import Image
                im = Image.open(src).convert("RGB")
                im.thumbnail((620, 620))
                im.save(dst, "JPEG", quality=78)
                local = f"images/{n:03d}.jpg"
            except Exception:  # noqa: BLE001
                pass
        img = (f"<img src='{local}' loading='lazy' alt=''>" if local
               else f"<img src='{e(r.get('url'))}' loading='lazy' referrerpolicy='no-referrer' alt=''>")
        cards.append(f"""
<article class="card" data-brief="{e(r.get('brief'))}">
  <div class="img">{img}</div>
  <div class="meta"><span class="tag">{e(r.get('brief'))}</span>
    <p><b>目标：</b>{e(r.get('model'))}</p>
    <p><b>query：</b>{e(r.get('query'))}</p>
    <p class="m"><b>标题：</b>{e(r.get('title') or '（空）')}</p>
    <p class="m"><a href="{e(r.get('url'))}" target="_blank">原图</a></p>
    <label>判断：<select data-v="v{n}"><option value="">—</option><option>是目标车</option><option>不是</option><option>不确定</option></select></label>
    <label>备注<input data-v="n{n}" placeholder="可选"></label>
  </div>
</article>""")
    briefs = sorted({r.get("brief") for r in selected})
    filters = "".join(f"<button data-f='{e(b)}'>{e(b)}</button>" for b in briefs)
    doc = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<title>类目词 query 盲评（{len(selected)} 图）</title><style>
body{{margin:0;background:#f5f4f1;color:#1d1d1f;font:14px/1.5 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}}
header{{padding:22px 30px;border-bottom:1px solid #ddd;background:#efece6}}
h1{{margin:0 0 6px;font-size:20px}}p{{margin:2px 0}}.m,.muted{{color:#6e6e73;font-size:11.5px}}
.bar{{position:sticky;top:0;z-index:3;background:#f5f4f1;border-bottom:1px solid #ddd;padding:8px 30px;display:flex;gap:8px;flex-wrap:wrap;align-items:center}}
button{{border:1px solid #ccc;background:#fff;border-radius:6px;padding:5px 10px;cursor:pointer}}button.p{{background:#1d1d1f;color:#fff;border-color:#1d1d1f}}
main{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px;padding:18px 30px 60px}}
.card{{background:#fff;border:1px solid #ddd;border-radius:9px;overflow:hidden}}
.img{{height:210px;background:#eee;display:flex;align-items:center;justify-content:center}}
.img img{{max-width:100%;max-height:210px;object-fit:contain}}
.meta{{padding:9px 11px;font-size:12px}}.tag{{display:inline-block;background:#f1efe9;border:1px solid #ddd;border-radius:999px;padding:2px 7px;font-size:11px;margin-bottom:4px}}
label{{display:block;margin:5px 0;color:#555}}select,input{{width:100%;padding:3px;border:1px solid #ccc;border-radius:4px;font:inherit}}
#outbox{{display:none;padding:10px 30px;background:#fff8e6;border-bottom:1px solid #e3c3bd}}textarea{{width:100%;font:12px monospace}}
</style></head><body>
<header><h1>类目词 query 盲评：{len(selected)} 张</h1>
<p class="muted">18 张 accepted + 22 张 unknown 分层抽样；隐藏 accepted/identity。</p>
<p class="muted">用于比较：类目词 query vs alias query 的 precision/unknown 目标率。</p></header>
<div class="bar"><button class="p" id="all">全部</button>{filters}<button id="export">导出标注</button><span class="muted" id="st">改选自动保存</span></div>
<div id="outbox"><p class="muted">下载被拦截时，复制下面 JSON。</p><textarea id="out" rows="5"></textarea><button id="copy">复制</button></div>
<main>{''.join(cards)}</main>
<script>
const KEY='source-expansion-class-review-20261111'; let all={{}};
try{{all=JSON.parse(localStorage.getItem(KEY)||'{{}}')||{{}};}}catch(e){{}}
function save(){{try{{localStorage.setItem(KEY,JSON.stringify(all));document.getElementById('st').textContent='已保存 '+new Date().toLocaleTimeString();}}catch(e){{document.getElementById('st').textContent='本地存储不可用，请导出';}}}}
document.querySelectorAll('[data-v]').forEach(el=>{{const k=el.dataset.v;if(all[k]!==undefined)el.value=all[k];const f=()=>{{all[k]=el.value;save();}};el.addEventListener('input',f);el.addEventListener('change',f);}});
document.getElementById('all').onclick=()=>document.querySelectorAll('.card').forEach(c=>c.style.display='');
document.querySelectorAll('[data-f]').forEach(b=>b.onclick=()=>{{const v=b.dataset.f;document.querySelectorAll('.card').forEach(c=>c.style.display=(c.dataset.brief===v?'':'none'));}});
document.getElementById('export').onclick=()=>{{const text=JSON.stringify(all,null,1);const box=document.getElementById('outbox'),out=document.getElementById('out');box.style.display='block';out.value=text;out.focus();out.select();try{{const b=new Blob([text],{{type:'application/json'}});const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='source-expansion-class-review.json';document.body.appendChild(a);a.click();a.remove();}}catch(e){{}}document.getElementById('st').textContent='已生成；如下载无反应请复制文本框';}};
document.getElementById('copy').onclick=async()=>{{const out=document.getElementById('out');try{{await navigator.clipboard.writeText(out.value);document.getElementById('st').textContent='已复制';}}catch(e){{out.focus();out.select();document.execCommand('copy');document.getElementById('st').textContent='已选中，请 Ctrl+C';}}}};
</script></body></html>"""
    (OUT / "review.html").write_text(doc, encoding="utf-8")
    (OUT / "review-data.json").write_text(json.dumps(selected, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"out": str(OUT / "review.html"), "rows": len(selected),
                      "accepted": len(accepted), "unknown_sample": len(sample)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
