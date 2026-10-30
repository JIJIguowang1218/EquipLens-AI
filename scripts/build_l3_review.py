# -*- coding: utf-8 -*-
"""L3 评测集 v1 人工审核包生成器。

把 data-test/evals/l3-relevance-v1.json 里的 7 条标注还原成可视审核页：
每条附上"被关键词捞出的原文段落"（取自各 run 的 grade-*.json top_passages）、
复判等级与判定理由，并提供同意/改判/待议按钮，审核结论可一键复制回传。

用法：python tmp/build_l3_review.py
输出：data-test/evals/review-l3-v1.html
"""
import html
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
EVAL_PATH = ROOT / "data-test" / "evals" / "l3-relevance-v1.json"
RUNS_DIR = ROOT / "data-test" / "runs"
OUT_PATH = ROOT / "data-test" / "evals" / "review-l3-v1.html"

TIER_META = {
    "A_cat": ("A_cat 类目正中", "#0f766e"),
    "A_comp": ("A_comp 部件相关", "#1d4ed8"),
    "A_gen": ("A_gen 通用可迁移", "#b45309"),
    "C": ("C 不可用", "#b91c1c"),
}


def load_passages(run_name: str, url: str) -> tuple[list[str], str]:
    """在该 run 的 grade-*.json 中按 URL 找回被判 A 的原文段落。"""
    run_dir = RUNS_DIR / run_name
    for grade_file in sorted(run_dir.glob("grade-*.json")):
        try:
            data = json.loads(grade_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for doc in data.get("docs", []):
            if doc.get("url") == url:
                passages = doc.get("top_passages") or []
                meta = f"{grade_file.name} · {doc.get('chars', '?')}字"
                return passages, meta
    return [], "未在 grade-*.json 中找到"


def highlight_anchors(text: str, anchors: list[str]) -> str:
    """给段落里的具体性证据词打高亮，方便快速核对证据。"""
    escaped = html.escape(text)
    for anchor in sorted(anchors, key=len, reverse=True):
        a = html.escape(anchor)
        if a and a in escaped:
            escaped = escaped.replace(a, f"<mark>{a}</mark>")
    return escaped


def build_card(item: dict, index: int) -> str:
    passages, origin = load_passages(item["run"], item["url"])
    tier_label, tier_color = TIER_META.get(item["llm_tier"], (item["llm_tier"], "#64748b"))
    anchors = item.get("concrete_anchors", [])

    passage_html = "\n".join(
        f"<p class='passage'>{highlight_anchors(p, anchors)}</p>" for p in passages
    ) or "<p class='dim'>（该 run 的 grade 文件中未留存段落，可点上方原文链接核对）</p>"

    return f"""
<div class="card" data-id="{html.escape(item['id'])}">
  <header>
    <div class="row">
      <span class="badge grey">#{html.escape(item['id'])}</span>
      <span class="badge blue">关键词判 A · {item['current_a_chars']} 字</span>
      <span class="badge" style="background:{tier_color}">复判 {html.escape(tier_label)}</span>
    </div>
    <h3><a href="{html.escape(item['url'])}" target="_blank">{html.escape(item['title'])}</a></h3>
    <div class="meta">主题：{html.escape(item['subject'])} ｜ 来源 run：{html.escape(item['run'])} ｜ 段落出处：{html.escape(origin)}</div>
  </header>
  <div class="body">
    <h4 class="sec">被关键词打分为 A 的原文段落</h4>
    {passage_html}
    <h4 class="sec">复判理由</h4>
    <p class="reason">{html.escape(item['reason'])}</p>
    <p class="dim">文中具体性证据词：{'、'.join(html.escape(a) for a in anchors) or '（无）'}</p>
  </div>
  <div class="verdict">
    <button data-v="agree">✓ 同意复判</button>
    <button data-v="disagree">✗ 不同意，我改判</button>
    <button data-v="hold">? 待议</button>
    <span class="vstate"></span>
  </div>
</div>"""


def main() -> int:
    data = json.loads(EVAL_PATH.read_text(encoding="utf-8"))
    items = data["items"]
    summary = data.get("summary", {})
    cards = "\n".join(build_card(item, i) for i, item in enumerate(items))

    criteria_rows = "\n".join(
        f"<tr><td><code>{html.escape(k)}</code></td><td>{html.escape(v)}</td></tr>"
        for k, v in data["judging_criteria"].items()
    )

    page = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>L3 评测集 v1 人工审核包</title>
<style>
:root{{--ink:#1c2430;--muted:#66707c;--line:#e3e7ec;--bg:#f6f7f9}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);
 font:15px/1.75 "Microsoft YaHei","PingFang SC",system-ui,sans-serif}}
.wrap{{max-width:980px;margin:0 auto;padding:32px 20px 120px}}
h1{{font-size:24px;margin:0 0 6px}} .sub{{color:var(--muted);margin-bottom:24px}}
table{{border-collapse:collapse;background:#fff;border:1px solid var(--line);
 border-radius:8px;overflow:hidden;margin:0 0 28px;width:100%}}
th,td{{padding:8px 16px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}
th{{background:#eef1f5;font-weight:600}}
code{{background:#eef1f5;padding:1px 6px;border-radius:4px;font-size:13px}}
.card{{background:#fff;border:1px solid var(--line);border-radius:10px;margin:0 0 18px;overflow:hidden}}
.card header{{padding:14px 18px;border-bottom:1px solid var(--line);background:#fbfcfd}}
.card h3{{font-size:16px;margin:6px 0 4px;line-height:1.45}}
.card h3 a{{color:var(--ink);text-decoration:none}} .card h3 a:hover{{color:#2563eb}}
.meta{{color:var(--muted);font-size:12.5px}}
.badge{{display:inline-block;padding:1px 9px;border-radius:999px;font-size:12px;color:#fff;background:#64748b;margin-right:6px}}
.badge.grey{{background:#64748b}} .badge.blue{{background:#1d4ed8}}
.row{{display:flex;flex-wrap:wrap;gap:2px}}
.body{{padding:6px 22px 16px}}
.sec{{font-size:13px;color:var(--muted);margin:14px 0 6px;font-weight:600}}
.passage{{background:#f8fafc;border-left:3px solid #94a3b8;padding:8px 12px;margin:8px 0;border-radius:0 6px 6px 0}}
mark{{background:#fde68a;padding:0 2px;border-radius:3px}}
.reason{{background:#fff7ed;border-left:3px solid #f59e0b;padding:8px 12px;border-radius:0 6px 6px 0;margin:6px 0}}
.dim{{color:var(--muted);font-size:13px}}
.verdict{{padding:12px 18px;border-top:1px solid var(--line);background:#fbfcfd;display:flex;gap:10px;align-items:center;flex-wrap:wrap}}
.verdict button{{padding:6px 14px;border-radius:8px;border:1px solid var(--line);background:#fff;
 font-size:13.5px;cursor:pointer;font-family:inherit}}
.verdict button:hover{{border-color:#2563eb;color:#2563eb}}
.verdict button.on{{background:#2563eb;border-color:#2563eb;color:#fff}}
.vstate{{color:var(--muted);font-size:13px}}
.panel{{position:fixed;right:20px;bottom:20px;background:#1c2430;color:#fff;border-radius:12px;
 padding:14px 18px;box-shadow:0 8px 30px rgba(0,0,0,.25);max-width:340px;font-size:13px}}
.panel button{{margin-top:8px;padding:7px 14px;border:0;border-radius:8px;background:#2563eb;color:#fff;cursor:pointer;font-family:inherit;font-size:13.5px}}
.tip{{background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:12px 18px;margin:0 0 22px;font-size:14px}}
</style></head><body><div class="wrap">
<h1>L3 评测集 v1 · 人工审核包</h1>
<div class="sub">{html.escape(data.get('created',''))} 生成 ｜ 共 {len(items)} 篇，均为关键词打分判 A 的文章，请逐篇核对复判是否成立</div>

<div class="tip"><b>怎么审：</b>每张卡片里，灰底引用块是<strong>当时被关键词捞出的原文段落</strong>（黄色高亮=判定理由引用的具体性证据词），橙色块是<strong>复判等级与理由</strong>。看完点"同意/改判/待议"，最后点右下角"复制审核结论"贴回对话即可。</div>

<h2 style="font-size:18px">判定标准（四级）</h2>
<table><tr><th style="width:110px">等级</th><th>含义</th></tr>{criteria_rows}</table>

<h2 style="font-size:18px">当前汇总（待你复核）</h2>
<table>
<tr><th>关键词判 A 篇数 / 字数</th><th>复判 A_cat</th><th>复判 A_gen</th><th>复判 C（假阳性）</th><th>假阳性率</th></tr>
<tr><td>{summary.get('current_A_docs','?')} 篇 / {summary.get('current_A_chars','?')} 字</td>
<td>{summary.get('llm_A_cat','?')} 篇 / {summary.get('llm_A_cat_chars','?')} 字</td>
<td>{summary.get('llm_A_gen','?')} 篇 / {summary.get('llm_A_gen_chars','?')} 字</td>
<td>{summary.get('llm_C','?')} 篇 / {summary.get('llm_C_chars','?')} 字</td>
<td><b style="color:#b91c1c">{html.escape(str(summary.get('false_positive_rate','?')))}</b></td></tr>
</table>

{cards}
</div>
<div class="panel" id="panel">
  <div>已审核 <b id="done">0</b>/{len(items)} 篇</div>
  <button onclick="copyResult()">复制审核结论</button>
</div>
<script>
const LS_KEY='l3-review-v1';
let state={{}};
try{{state=JSON.parse(localStorage.getItem(LS_KEY)||'{{}}')||{{}};}}catch(e){{}}
function save(){{try{{localStorage.setItem(LS_KEY,JSON.stringify(state));}}catch(e){{}}}}
const items=[...document.querySelectorAll('.card')];
function render(){{
  let done=0;
  items.forEach(card=>{{
    const id=card.dataset.id, v=state[id];
    card.querySelectorAll('.verdict button').forEach(b=>b.classList.toggle('on',v===b.dataset.v));
    const label={{agree:'已确认复判',disagree:'你将改判（请在对话里说明新等级）',hold:'待议'}}[v]||'';
    card.querySelector('.vstate').textContent=label;
    if(v)done++;
  }});
  document.getElementById('done').textContent=done;
}}
items.forEach(card=>{{
  card.querySelectorAll('.verdict button').forEach(b=>b.addEventListener('click',()=>{{
    state[card.dataset.id]=b.dataset.v;
    localStorage.setItem(LS_KEY,JSON.stringify(state));render();
  }}));
}});
function copyResult(){{
  const names={{agree:'同意',disagree:'不同意(我改判)',hold:'待议'}};
  const lines=items.map(c=>`#${{c.dataset.id}} ${{c.querySelector('h3').textContent.trim()}} → ${{names[state[c.dataset.id]]||'未审'}}`);
  const text='L3 评测集 v1 审核结论\\n'+lines.join('\\n');
  if(navigator.clipboard&&navigator.clipboard.writeText){{
    navigator.clipboard.writeText(text).then(()=>alert('已复制：\\n\\n'+text),()=>prompt('自动复制失败，请手动复制：',text));
  }}else{{prompt('请手动复制：',text);}}
}}
render();
</script>
</body></html>"""

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(page, encoding="utf-8")
    print(f"已生成：{OUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
