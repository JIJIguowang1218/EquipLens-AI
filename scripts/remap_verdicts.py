# -*- coding: utf-8 -*-
"""旧判定 → 新稳定 ID 的映射。

补爬后判定表 ID 改为文本指纹（sha1），本脚本按"段落文本一致"把旧 ID 的判定
迁移到新 ID；未匹配上的即新增候选段（需重新判定）。
自审修正：沙漠-001（HOWO 悍将轻卡）属整车级跨类目，按 15 号先例（整车不可
迁移、部件可迁移）改判 C。

用法: python tmp/remap_verdicts.py
"""
import hashlib
import json
from pathlib import Path

EVALS = Path(__file__).resolve().parents[1] / "data-test" / "evals"
OLD_SHEET = EVALS / "roster-judge-sheet-20261030-v0.json"   # 旧序 ID（281 条）
OLD_VERDICTS = EVALS / "roster-verdicts-20261030-v0.json"   # 只读
NEW_SHEET = EVALS / "roster-judge-sheet-20261030.json"      # 重新生成后的稳定 ID
OUT_VERDICTS = EVALS / "roster-verdicts-20261030.json"      # 输出（不与备份混用）

# 自审修正：text 片段 → (tier, note)
OVERRIDES = [
    ("HOWO悍将25款轻卡", "C",
     "自审改判：轻卡整车描述，对沙漠牵引车/重卡类目为整车级跨类目，"
     "不可迁移（部件可迁移、整车不可迁移，参照 15 号先例）"),
]


def fingerprint(text: str) -> str:
    return hashlib.sha1(text.encode()).hexdigest()[:8]


def main() -> int:
    old_sheet = json.loads(OLD_SHEET.read_text(encoding="utf-8"))
    old_verd = json.loads(OLD_VERDICTS.read_text(encoding="utf-8"))
    new_sheet = json.loads(NEW_SHEET.read_text(encoding="utf-8"))

    # 旧 ID → (text, verdict)，按文本指纹索引
    by_fp: dict[str, tuple[str, dict]] = {}
    for it in old_sheet["items"]:
        v = old_verd.get(it["id"])
        if v:
            by_fp[fingerprint(it["text"])] = (it["text"], v)

    remapped: dict[str, dict] = {}
    unmatched: list[dict] = []
    for it in new_sheet["items"]:
        fp = fingerprint(it["text"])
        if fp in by_fp:
            text, v = by_fp[fp]
            remapped[it["id"]] = dict(v)
        else:
            unmatched.append(it)

    # 应用自审修正
    for it in new_sheet["items"]:
        for frag, tier, note in OVERRIDES:
            if frag in it["text"]:
                remapped[it["id"]] = {"tier": tier, "note": note}

    OUT_VERDICTS.write_text(
        json.dumps(remapped, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"迁移 {len(remapped)} 条；新增待判 {len(unmatched)} 条")
    for it in unmatched[:40]:
        print(f"  NEW {it['id']} [{it['rule_label']}] {it['title'][:34]} | "
              f"{it['chars']}字 | {it['text'][:70]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
