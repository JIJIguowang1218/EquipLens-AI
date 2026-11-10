"""诊断：外国品牌为什么进不了漏斗（只读 360，不花钱、不写 run）。

对每个候选车型，分别用「当前规划器 query」「车型全名」「人工改写 query」
三条路走 search_images_hd，打印每通道 raw/relevant 数量与前几条标题。
"""
from __future__ import annotations

import sys

from equiplens import imagesearch

CASES = [
    # (标签, 规划器实际 query, 车型名)
    ("Zetros", "Zetros 4051 AS 6x6", "Zetros 4051 AS（6×6沙漠牵引车）"),
    ("Arocs", "Arocs 6x6", "Arocs 6×6 / 8×8 全驱牵引车"),
    ("Volvo FMX", "Volvo FMX 6x6", "Volvo FMX 6×6 牵引车"),
    ("KAMAZ", "KAMAZ 6x6", "KAMAZ 6520 6×6"),
    ("Tatra", "Tatra 815 6x6", "Tatra 815 6×6"),
    ("MOL", "MOL-Brec TB 800 6x6", "MOL-Brec TB 800（KFM Desert Lion）"),
]

MANUAL = {
    "Zetros": ["奔驰 Zetros 6x6 牵引车", "Mercedes Zetros 6x6", "Zetros 沙漠"],
    "Arocs": ["奔驰 Arocs 6x6 牵引车", "Mercedes Arocs 6x6", "Arocs 8x8"],
    "Volvo FMX": ["沃尔沃 FMX 6x6", "Volvo FMX 6x6"],
    "KAMAZ": ["卡玛斯 6x6 牵引车", "KAMAZ 6520"],
    "Tatra": ["太脱拉 6x6", "Tatra 815"],
    "MOL": ["MOL 沙漠车", "MOL-Brec 6x6"],
}


def show(label: str, query: str, model: str) -> None:
    hits, diag = imagesearch.search_images_hd(query, limit=6, model=model)
    print(f"\n## {label} | q={query!r}")
    for d in diag:
        for c in d.get("channels") or []:
            print(f"   {d.get('query')} -> {c.get('channel')}: "
                  f"raw={c.get('returned')} rel={c.get('relevant')} "
                  f"status={c.get('status')}")
    for h in hits[:4]:
        print(f"   HIT {h.get('width')}x{h.get('height')} {h.get('title')!r}")
    if not hits:
        print("   (no hits)")


def raw(label: str, query: str) -> None:
    got, status = imagesearch._search_360(query, 20)
    print(f"\n== RAW {label} | q={query!r} status={status} n={len(got)}")
    for h in got[:6]:
        print(f"   {h.get('width')}x{h.get('height')} {h.get('title')!r}")


def main(argv) -> int:
    for label, q, model in CASES:
        show(label + " [plan]", q, model)
        for mq in MANUAL[label]:
            show(label + " [manual]", mq, model)
    for label, q, _model in CASES[:2]:
        raw(label, q)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
