# -*- coding: utf-8 -*-
"""T18-roster 三分类审核包生成器（HTML，供产品负责人抽查）。

输入: roster-eval-20261030.json（判定结果）+ roster-judge-sheet-20261030.json（段落原文）
输出: data-test/evals/review-roster-20261030.html

审核包默认只展示非 C 档（V/P/G 共 63 条），C 档折叠在末尾附录。
按钮交互与 review-l3-v1 同款（localStorage 已做 try/catch 降级，预览 iframe 可用）。
"""
import html
import json
from pathlib import Path

EVALS = Path(__file__).resolve().parents[1] / "data-test" / "evals"
evalj = json.loads((EVALS / "roster-eval-20261030.json").read_text(encoding="utf-8"))
sheet = {it["id"]: it for it in
         json.loads((EVALS / "roster-judge-sheet-20261030.json")
                    .read_text(encoding="utf-8"))["items"]}

TIER_META = {
    "V": ("V 指向车型整体", "#0f766e"),
    "P": ("P 部件构型及造型", "#1d4ed8"),
    "G": ("G 非指向参考", "#b45309"),
    "C": ("C 剔除", "#b91c1c"),
}
items = evalj["items"]
main_items = [i for i in items if i["tier"] != "C"]
c_items = [i for i in items if i["tier"] == "C"]


def card(it: dict, collapsed: bool = False) -> str:
    label, color = TIER_META[it["tier"]]
    text = html.escape(sheet.get(it["id"], {}).get("text", ""))
    anchor = html.escape(it.get("explicit_anchor") or "—")
    if collapsed:
        return (f"<li><b>{it['id']}</b> [{label}] {it['chars']}字 "
                f"{html.escape(it['title'][:44])} :: {text[:90]}</li>")
    return f"""
<div class="card" data-id="{html.escape(it['id'])}">
  <header>
    <span class="badge" style="background:{color}">{label}</span>
    <span class="badge grey">{it['chars']} 字</span>
    <span class="badge blue">规则:{it['rule_label']}</span>
    <h3>{html.escape(it['title'])}</h3>
    <div class="meta">类目：{html.escape(it['category'])} ｜ 锚点：{anchor} ｜ <a href="{html.escape(it['url'])}" target="_blank">原文</a></div>
  </header>
  <div class="body"><p class="passage">{text}</p>
  <p class="reason"><b>判定理由：</b>{html.escape(it['note'])}</p></div>
</div>"""


def main() -> int:
    t = evalj["tiers"]
    rows = "".join(
        f"<tr><td><span class='badge' style='background:{TIER_META[k][1]}'>"
        f"{TIER_META[k][0]}</span></td><td>{t[k]['count']}</td>"
        f"<td>{t[k]['chars']:,}</td><td>{t[k]['char_share']*100:.1f}%</td>"
        f"<td>{t[k]['chars']/evalj['body_chars_total']*100:.2f}%</td></tr>"
        for k in ("V", "P", "G", "C"))

    cat_rows = ""
    for cat, d in evalj["per_category"].items():
        tt = d["tiers"]
        cat_rows += ("<tr><td>{}</td>{}<td>{:,}</td></tr>".format(
            html.escape(cat),
            "".join(f"<td>{tt[k]['share_of_candidates']*100:.1f}%</td>"
                    for k in ("V", "P", "G", "C")),
            d["candidate_chars"]))

    page = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>T18-roster 三分类审核包</title>
<style>
:root{{--ink:#1c2430;--muted:#66707c;--line:#e3e7ec;--bg:#f6f7f9}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.75 "Microsoft YaHei","PingFang SC",system-ui,sans-serif}}
.wrap{{max-width:1000px;margin:0 auto;padding:32px 20px 120px}}
h1{{font-size:24px;margin:0 0 6px}} .sub{{color:var(--muted);margin-bottom:20px}}
table{{border-collapse:collapse;background:#fff;border:1px solid var(--line);border-radius:8px;overflow:hidden;margin:0 0 22px;width:100%}}
th,td{{padding:8px 14px;border-bottom:1px solid var(--line);text-align:left}}
th{{background:#eef1f5;font-weight:600}}
.badge{{display:inline-block;padding:1px 9px;border-radius:999px;font-size:12px;color:#fff;background:#64748b;margin-right:6px}}
.badge.grey{{background:#64748b}} .badge.blue{{background:#1d4ed8}}
.card{{background:#fff;border:1px solid var(--line);border-radius:10px;margin:0 0 16px;overflow:hidden}}
.card header{{padding:12px 18px;border-bottom:1px solid var(--line);background:#fbfcfd}}
.card h3{{font-size:15.5px;margin:6px 0 3px;line-height:1.45}}
.meta{{color:var(--muted);font-size:12.5px}} .meta a{{color:#2563eb}}
.body{{padding:8px 22px 14px}}
.passage{{background:#f8fafc;border-left:3px solid #94a3b8;padding:8px 12px;border-radius:0 6px 6px 0;margin:8px 0}}
.reason{{background:#fff7ed;border-left:3px solid #f59e0b;padding:8px 12px;border-radius:0 6px 6px 0;font-size:14px}}
details{{margin-top:20px}} summary{{cursor:pointer;color:#2563eb;font-weight:600}}
ul.c{{font-size:13.5px;color:#4b5563}} ul.c li{{margin:3px 0}}
.tip{{background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:12px 18px;margin:0 0 20px;font-size:14px}}
</style></head><body><div class="wrap">
<h1>T18-roster 全名录文本筛选 · 三分类审核包</h1>
<div class="sub">2026-10-30 ｜ 4 类目 39 车型 ｜ 判定 {len(items)} 段（非剔除 {len(main_items)} 段）｜ 请抽查 V/P/G 判定是否成立</div>
<div class="tip"><b>审核方式：</b>重点看 V（指向车型整体）与 G（非指向定调参考）的边界是否划对；P 档为部件/构型。看完在心里确认即可，无需勾选。</div>
<h2>占比汇总</h2>
<table><tr><th>类别</th><th>段数</th><th>字数</th><th>占候选段</th><th>占全部落盘正文</th></tr>{rows}</table>
<h2>按类目拆解（占该类目候选段字数）</h2>
<table><tr><th>类目</th><th>V</th><th>P</th><th>G</th><th>C</th><th>候选段字数</th></tr>{cat_rows}</table>
<h2>非剔除段（{len(main_items)} 条）</h2>
{"".join(card(i) for i in main_items)}
<details><summary>C 档剔除明细（{len(c_items)} 条，点击展开）</summary><ul class="c">
{"".join(card(i, collapsed=True) for i in c_items)}
</ul></details>
</div></body></html>"""
    out = EVALS / "review-roster-20261030.html"
    out.write_text(page, encoding="utf-8")
    print("生成:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
