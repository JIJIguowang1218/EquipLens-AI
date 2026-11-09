"""网页检索适配器（P2-W1）：360/百度/Bing 等通道，复用 imagesearch/gate。

层次：
  WebWorld.external_targets  → 搜索/发现层（型号候选）
  WebWorld.fetch             → 抓取/门卫层（下载 + 尺寸 + 门卫 + 视角）
  RuleVerifier.verify        → 规则核验层（标题/构型/视角/分辨率）
  EvidenceStore              → 证据落库层

P2-W1 只接 360；P2-W2 再扩 SearXNG/Tavily 等与源健康/熔断。
"""
from __future__ import annotations

import hashlib
import re
from io import BytesIO
from pathlib import Path
from typing import Callable

from .contracts import Asset, PartRequirement, Target, Verification


class NullLibraryAdapter:
    """网页-only 模式的空库：让状态机以为库内没有候选。"""

    def targets(self, unit) -> list[Target]:
        return []


class RuleVerifier:
    """规则核验：标题含型号、构型一致、分辨率达标；视角只记 warning。

    **视角不否决**：CLIP 视角的 top1−top2 中位数 ~0.003（见 gate.assess_from_gate
    与 docs/image-filter-pipeline.md），把视角当硬缺陷会误杀正视角整车。
    视角不符记进 `warnings`，供人工复核与排序；硬缺陷只剩低分辨率、
    型号身份、构型不一致。

    accepted=true 只代表“规则上可占槽的 candidate”，不做视觉身份判断。
    """

    def __init__(self, parts: dict[str, PartRequirement], *, min_width: int = 1200):
        self.parts = parts
        self.min_width = min_width

    def verify(self, asset: Asset, part: str) -> Verification:
        spec = self.parts.get(part)
        defects: list[str] = []
        warnings: list[str] = []
        if asset.width and asset.width < self.min_width:
            defects.append("low_resolution")
        # 视角只记 warning，不否决（CLIP 视角几乎不可分，见 gate 注释）
        if spec and spec.views and asset.view and asset.view not in spec.views:
            warnings.append("view_mismatch")
        if asset.view == "interior":
            warnings.append("view_interior_hint")
        if asset.model and asset.title:
            tokens = [t for t in re.findall(r"[A-Za-z0-9]+", asset.model)
                      if len(t) >= 3]
            if tokens and not any(t.lower() in asset.title.lower()
                                  for t in tokens):
                defects.append("wrong_identity")
            conf = re.findall(r"\d+\s*[x×]\s*\d+", asset.model)
            if conf:
                want = re.sub(r"[×\s]", "x", conf[0]).lower()
                got = [re.sub(r"[×\s]", "x", x).lower()
                       for x in re.findall(r"\d+\s*[x×]\s*\d+", asset.title)]
                if got and want not in got:
                    defects.append("wrong_config")
        accepted = not defects
        return Verification(
            accepted=accepted,
            identity="probable" if accepted else "unknown",
            visibility="full" if asset.width else "unknown",
            origin="unknown",
            grade="E1" if accepted else "",
            defects=tuple(defects),
            warnings=tuple(warnings),
        )


class WebWorld:
    """网页-only 世界：空库 + 型号候选 + 抓取 + 规则核验。"""

    def __init__(self, models: dict[str, list[str]] | list[str] | None,
                 parts: dict[str, PartRequirement], *,
                 fetch_fn: Callable[[Target, str], list[Asset]] | None = None,
                 library=None, verifier: RuleVerifier | None = None,
                 router=None, min_width: int = 1200,
                 image_dir=None, discover_limit: int = 12):
        if isinstance(models, list):
            models = {"*": models}
        self.models = models or {}
        self.image_dir = Path(image_dir) if image_dir else None
        self.discover_limit = discover_limit
        self._search_cache: dict[str, list] = {}
        self.parts = parts
        self.library = library or NullLibraryAdapter()
        self.fetch_fn = fetch_fn or self.live_fetch
        self.verifier = verifier or RuleVerifier(parts, min_width=min_width)
        self.router = router

    def library_targets(self, unit) -> list[Target]:
        return self.library.targets(unit)

    def external_targets(self, unit) -> list[Target]:
        names = self.models.get(unit.unit_id) or self.models.get("*") or []
        if not names:
            # 隔离测试：候选只来自实时检索（不读名录/历史批次）；库内检索后置。
            from .discover import discover_models
            names = [r["model"] for r in
                     discover_models(unit.scope, limit=self.discover_limit)]
        return [Target(target_id=m, model=m, source="web", tier=unit.tier,
                       parts=tuple(unit.parts), unit_id=unit.unit_id)
                for m in names]

    def fetch(self, target: Target, part: str) -> list[Asset]:
        return self.fetch_fn(target, part)

    def verify(self, asset: Asset, part: str) -> Verification:
        return self.verifier.verify(asset, part)

    # ------------------------------------------------------------------ live
    def live_fetch(self, target: Target, part: str) -> list[Asset]:
        """真实 360 → 下载 → 预筛 → 门卫 → 分层判定（视角只作 hint）。

        两段式：`imagesearch._download_and_gate` 已跑完第一段确定性预筛，
        预筛否决的图 `gate.pass=False` + `stage="prefilter"`，这里直接跳过，
        不会进 CLIP。只收 `overview_candidate`（门卫通过 + 长边 ≥800 + 非拼图）；
        分辨率 ≥1200 由 RuleVerifier 再判（part_candidate 口径）。
        """
        from .. import gate, imagesearch

        key = target.model
        if key in self._search_cache:
            hits = self._search_cache[key]
        else:
            if self.router is not None:
                hits, _diag = self.router.search(target.model, 6, target.model)
            else:
                hits, _diag = imagesearch.search_model_images(
                    target.model, limit=6, hd=True)
            self._search_cache[key] = hits
        out: list[Asset] = []
        for hit in hits:
            res = imagesearch._download_and_gate(hit)
            if res.get("error") or not res.get("data"):
                continue
            g = res.get("gate") or {}
            if not g.get("pass"):
                continue
            data = res["data"]
            pre = res.get("prefilter") or {}
            width = int(pre.get("width") or 0)
            height = int(pre.get("height") or 0)
            view_result = gate.classify_view(data)
            a = gate.assess_from_gate(g, view_result, width, height,
                                      prefilter_result=pre)
            if not a["overview_candidate"]:
                continue
            if self.image_dir:
                d = self.image_dir / re.sub(r"[^0-9A-Za-z一-鿿]+", "_",
                                            target.model)[:40]
                d.mkdir(parents=True, exist_ok=True)
                (d / f"{hashlib.sha1(hit['url'].encode('utf-8')).hexdigest()[:12]}.jpg")                     .write_bytes(data)
            out.append(Asset(
                asset_id=hashlib.sha1(hit["url"].encode("utf-8")).hexdigest()[:12],
                target_id=target.target_id,
                part=part,
                view=a["view"],
                width=width,
                height=height,
                url=hit.get("url", ""),
                title=hit.get("title", ""),
                model=target.model,
                channel=hit.get("channel", ""),
                status="gated",
            ))
        return out
