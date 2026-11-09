"""检索适配器协议 + 夹具实现（P1 用假世界，不联网）。

真实实现（P3）只要满足同样的协议即可替换：
  LibraryAdapter.targets(unit) -> list[Target]
  SearchAdapter.targets(unit) -> list[Target]
  FetchAdapter.fetch(target, part) -> list[Asset]
  Verifier.verify(asset, part) -> Verification
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Protocol

from .contracts import Asset, ResearchUnit, Target, Verification


class LibraryAdapter(Protocol):
    def targets(self, unit: ResearchUnit) -> list[Target]: ...


class SearchAdapter(Protocol):
    def targets(self, unit: ResearchUnit) -> list[Target]: ...


class FetchAdapter(Protocol):
    def fetch(self, target: Target, part: str) -> list[Asset]: ...


class Verifier(Protocol):
    def verify(self, asset: Asset, part: str) -> Verification: ...


class FakeWorld:
    """夹具驱动的假世界：库内/外检/抓取/核验都从 JSON 读。"""

    def __init__(self, data: dict):
        self.data = data
        self.calls: Counter[str] = Counter()
        self.call_log: list[tuple[str, str]] = []

    @classmethod
    def from_file(cls, path: str | Path) -> "FakeWorld":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def _targets(self, bucket: str, unit: ResearchUnit, source: str) -> list[Target]:
        self.calls[bucket] += 1
        self.call_log.append((bucket, unit.unit_id))
        rows = (self.data.get(bucket) or {}).get(unit.unit_id) or []
        return [Target.from_dict(x, source=source, tier=unit.tier) for x in rows]

    def library_targets(self, unit: ResearchUnit) -> list[Target]:
        return self._targets("library", unit, "library")

    def external_targets(self, unit: ResearchUnit) -> list[Target]:
        return self._targets("external", unit, "external")

    def fetch(self, target: Target, part: str) -> list[Asset]:
        self.calls["fetch"] += 1
        self.call_log.append(("fetch", f"{target.target_id}:{part}"))
        rows = ((self.data.get("assets") or {}).get(target.target_id) or {}).get(part) or []
        return [Asset.from_dict(x, target_id=target.target_id, part=part)
                for x in rows]

    def verify(self, asset: Asset, part: str) -> Verification:
        self.calls["verify"] += 1
        self.call_log.append(("verify", asset.asset_id))
        row = (self.data.get("verify") or {}).get(asset.asset_id)
        if not row:
            return Verification(accepted=False, defects=("no_verification",))
        return Verification.from_dict(row)
