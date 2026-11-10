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
import json
import os
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
    视角不符记进 `warnings`，供人工复核与排序；硬缺陷只剩型号身份、构型不一致。
    **分辨率不否决**（2026-11-10）：只记 `low_resolution` warning + 质量档位，
    由人审时决定用不用；否则小图会被一刀切丢掉，素材更少。

    accepted=true 只代表“规则上可占槽的 candidate”，不做视觉身份判断。
    """

    def __init__(self, parts: dict[str, PartRequirement], *, min_width: int = 1200):
        self.parts = parts
        self.min_width = min_width

    GENERIC_CN = ("沙漠车", "牵引车", "卡车", "越野车", "越野", "底盘", "货车",
                  "工程车", "重型", "全驱", "六驱", "沙漠", "运输车")

    def verify(self, asset: Asset, part: str) -> Verification:
        """身份分级核验：只对“矛盾”硬拒，不再因为“标题没写型号码”整台拒。

        身份三档：
          confirmed = 型号码命中标题
          probable  = 品牌/车系（非通用词）命中 + 构型命中，或两个非通用词命中
          unknown   = 只有通用词/都对不上（不进正式槽，可用于兜底）
        硬缺陷只剩：构型矛盾（要求 6×6 却明确 8×4/4×2）。
        """
        spec = self.parts.get(part)
        defects: list[str] = []
        warnings: list[str] = []
        title = (asset.title or "").lower()
        model = asset.model or ""

        if asset.width and asset.width < self.min_width:
            warnings.append("low_resolution")
        if asset.title and re.search(r"底盘|车架|配件|驾驶室总成|内饰", asset.title)                 and not re.search(r"整车|实拍|外观", asset.title):
            warnings.append("not_whole_vehicle")
        if spec and spec.views and asset.view and asset.view not in spec.views:
            warnings.append("view_mismatch")
        if asset.view == "interior":
            warnings.append("view_interior_hint")

        # ---- 身份证据 ----
        code = re.search(r"[A-Z]{1,4}\d{3,}[A-Z0-9]*", model)
        code_hit = bool(code) and code.group(0).lower() in title
        cn_tokens = [t for t in re.findall(r"[一-鿿]{2,4}", model)
                     if t not in self.GENERIC_CN]
        cn_hit = [t for t in cn_tokens if t in title]
        confs = [re.sub(r"[×\s]", "x", x).lower()
                 for x in re.findall(r"\d+\s*[x×]\s*\d+", model)]
        title_confs = [re.sub(r"[×\s]", "x", x).lower()
                       for x in re.findall(r"\d+\s*[x×]\s*\d+", title)]
        cfg_hit = any(c in title_confs for c in confs) if confs else False
        # 外国车型的标题常是中文品牌（沃尔沃/卡玛斯）或只有车系（Zetros/Arocs），
        # 与模型名里的拉丁写法对不上；复用 imagesearch 的品牌别名/车系判定。
        brand_hit = series_hit = fallback_series = False
        try:
            from .. import imagesearch as _is
            group = _is._brand_group(model)
            brand_hit = any(_is._alias_in(a, title) for a in group)
            fallback_series = bool(group) and group[0] not in _is._BRAND_LOOKUP
            series = [t for t in _is._tokens(model)
                      if re.search(r"[a-z]", t) and not t.isdigit()
                      and len(t) >= 3 and t not in group and t not in _is.GENERIC]
            series_hit = any(t in title for t in series)
        except Exception:  # noqa: BLE001
            pass

        if model and model.lower() in title:
            identity, grade = "confirmed", "E1"
        elif code_hit:
            identity, grade = "confirmed", "E1"
        elif (cn_hit and cfg_hit) or len(cn_hit) >= 2:
            identity, grade = "probable", "E2"
        elif brand_hit and (series_hit or cfg_hit or fallback_series):
            identity, grade = "probable", "E2"
        else:
            identity, grade = "unknown", ""
            warnings.append("identity_unverified")

        # 构型矛盾：标题明确写了别的构型且不含目标构型
        if confs and title_confs and not cfg_hit:
            defects.append("wrong_config")

        accepted = identity in ("confirmed", "probable") and not defects
        return Verification(
            accepted=accepted,
            identity=identity,
            visibility="full" if asset.width else "unknown",
            origin="unknown",
            grade=grade if accepted else "",
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
                 image_dir=None, discover_limit: int = 12,
                 plan: list[dict] | None = None, batch_size: int = 12,
                 citation_check: bool = True, api_key: str | None = None):
        if isinstance(models, list):
            models = {"*": models}
        self.models = models or {}
        self.image_dir = Path(image_dir) if image_dir else None
        self.discover_limit = discover_limit
        self._search_cache: dict[str, list] = {}
        self._fetch_cache: dict[str, dict] = {}   # url → _download_and_gate 结果
        self.plan = list(plan or [])
        self.batch_size = batch_size
        self.citation_check = citation_check
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "") or self._file_key()
        self._plan_cursor = 0
        self._citation_cache: dict[str, dict] = {}
        self.parts = parts
        self.library = library or NullLibraryAdapter()
        self.fetch_fn = fetch_fn or self.live_fetch
        self.verifier = verifier or RuleVerifier(parts, min_width=min_width)
        self.router = router

    def library_targets(self, unit) -> list[Target]:
        return self.library.targets(unit)

    def external_targets(self, unit) -> list[Target]:
        if self.plan:
            return self._plan_targets(unit)
        names = self.models.get(unit.unit_id) or self.models.get("*") or []
        if not names:
            # 2026-11-11 废弃 discover fallback：它内部是 18 个国产品牌的硬编码
            # 名单，会让“实时发现”静默变成“国产-only”，与“不设品牌白名单”冲突。
            raise RuntimeError(
                "WebWorld 没有候选：请用 --plan（scripts/plan_candidates.py 的输出）"
                "或 --models 显式给候选；discover fallback 已废弃（内置国产品牌名单"
                "会造成静默偏置），不要再无 plan 跑 --web-only。")
        return [Target(target_id=m, model=m, source="web", tier=unit.tier,
                       parts=tuple(unit.parts), unit_id=unit.unit_id)
                for m in names]

    @staticmethod
    def _file_key() -> str:
        try:
            p = Path.home() / ".equiplens" / "deepseek.env"
            for line in p.read_text(encoding="utf-8").splitlines():
                if line.startswith("DEEPSEEK_API_KEY="):
                    return line.split("=", 1)[1].strip()
        except Exception:  # noqa: BLE001
            return ""
        return ""

    @staticmethod
    def normalize_query(model: str) -> str:
        """长名字 → 短检索键：去掉括号说明，取型号代码（优先）+ 品牌/车系 + 6x6。"""
        import re as _re
        s = _re.sub(r"[（(][^）)]*[）)]", " ", model or "")
        s = s.replace("×", "x").strip()
        code = _re.search(r"[A-Z]{1,4}\d{3,}[A-Z0-9]*", s)
        if code:
            brand = _re.search(r"[一-鿿]{2,4}", s[:code.start()])
            pre = brand.group(0) if brand else ""
            return f"{pre} {code.group(0)} 6x6".strip()
        words = [w for w in s.split() if w]
        key = " ".join(words[:3]).strip(" /,、;")
        return key if "6x6" in key.lower() else f"{key} 6x6"

    def can_replan(self) -> bool:
        return bool(self.plan) and not self.has_more()

    def has_more(self, unit=None) -> bool:
        """规划池里是否还有未激活候选。"""
        return self._plan_cursor < len(self.plan)

    def replan(self, failed_models: list[str], need: int = 4) -> int:
        """槽位未满时的重规划：按失败车型找替代候选（带引用），追加到池子。"""
        import json as _json
        import re as _re

        import requests as _req

        if not self.api_key:
            return 0
        existing = {(c.get("model") or "").strip() for c in self.plan}
        queries = [f"{m} 替代车型 6x6" for m in failed_models[:3]]
        queries.append("沙漠 6x6 牵引车 车型 品牌")
        results: list[dict] = []
        for q in queries[:4]:
            try:
                t0 = __import__("time").time()
                r = _req.post("https://api.deepseek.com/v1/tools/search",
                              headers={"Authorization": f"Bearer {self.api_key}",
                                       "Content-Type": "application/json"},
                              json={"query": q, "count": 10}, timeout=40)
                data = r.json() if r.status_code == 200 else {}
                got = data.get("results") or []
                self._api_log({"api": "search", "query": q, "status": r.status_code,
                               "results": len(got), "billable": bool(got),
                               "cost_usd": 0.00075 if got else 0,
                               "ms": round((__import__("time").time() - t0) * 1000)})
                results.extend(got)
            except Exception:  # noqa: BLE001
                continue
        if not results:
            return 0
        seen, uniq = set(), []
        for r in results:
            u = r.get("url", "")
            if u and u not in seen:
                seen.add(u)
                uniq.append(r)
        compact = [{"title": x.get("title", ""), "url": x.get("url", ""),
                    "summary": (x.get("summary") or "")[:250]} for x in uniq[:20]]
        prompt = (
            "下面是沙漠牵引车检索结果。已入选车型抓不到图，请补充最多 "
            f"{max(need * 2, 4)} 个**新的**候选车型（品牌+车系/型号代码），"
            "不要与已有重复；每条必须绑定下列结果中的 URL；只输出 JSON："
            '{"candidates":[{"model":"","query":"","sources":["url"]}]}。"' + chr(10) +
            f"已有：{_json.dumps(sorted(existing), ensure_ascii=False)}" + chr(10) +
            f"结果：{_json.dumps(compact, ensure_ascii=False)}"
        )
        try:
            r = _req.post("https://api.deepseek.com/chat/completions",
                          headers={"Authorization": f"Bearer {self.api_key}",
                                   "Content-Type": "application/json"},
                          json={"model": "deepseek-flash",
                                "messages": [{"role": "user", "content": prompt}],
                                "response_format": {"type": "json_object"},
                                "temperature": 0.2}, timeout=120)
            body = r.json()
            usage = body.get("usage") or {}
            self._api_log({"api": "chat", "model": "deepseek-flash",
                           "status": r.status_code,
                           "prompt_tokens": usage.get("prompt_tokens"),
                           "completion_tokens": usage.get("completion_tokens"),
                           "billable": r.status_code == 200})
            got = _json.loads(body["choices"][0]["message"]["content"])
        except Exception:  # noqa: BLE001
            return 0
        valid = {x["url"] for x in uniq}
        added = 0
        for c in got.get("candidates", []):
            model = (c.get("model") or "").strip()
            if not model or model in existing:
                continue
            srcs = [u for u in (c.get("sources") or []) if u in valid]
            if not srcs:
                continue
            self.plan.append({"model": model, "query": c.get("query") or "",
                              "sources": srcs, "replanned": True})
            existing.add(model)
            added += 1
        if self.image_dir:
            self._append_log(self.image_dir.parent / "replan_log.jsonl",
                             {"failed": failed_models[:5], "need": need,
                              "added": added, "at": __import__("time").strftime("%H:%M:%S")})
        return added

    def _plan_targets(self, unit) -> list[Target]:
        """从规划池取下一批候选（带引用）；引用核验后按可靠性排序。"""
        batch = self.plan[self._plan_cursor:self._plan_cursor + self.batch_size]
        self._plan_cursor += len(batch)
        rows = []
        for c in batch:
            ok, ev = (True, {}) if not self.citation_check else self._verify_citation(c)
            rows.append((c, ok, ev))
        rows.sort(key=lambda x: (not x[1], x[0].get("priority", 99)))
        out = []
        for c, ok, ev in rows:
            model = (c.get("model") or "").strip()
            if not model:
                continue
            out.append(Target(
                target_id=model, model=model, source="plan", tier=unit.tier,
                parts=tuple(unit.parts), unit_id=unit.unit_id,
                sources=tuple(c.get("sources") or []), citation_ok=ok,
                query=(c.get("query") or self.normalize_query(model))))
        return out

    def _api_log(self, row: dict) -> None:
        if not self.image_dir:
            return
        self._append_log(self.image_dir.parent / "api_log.jsonl", row)

    def _log_citation(self, row: dict) -> None:
        if not self.image_dir:
            return
        path = self.image_dir.parent / "citation_log.jsonl"
        self._append_log(path, row)

    def _verify_citation(self, cand: dict) -> tuple[bool, dict]:
        """用 DeepSeek Fetch 取引用页，确认页面确实提到该车型。"""
        import re as _re
        import time as _time

        import requests as _req

        model = (cand.get("model") or "").strip()
        srcs = list(cand.get("sources") or [])[:2]
        if not model or not srcs:
            self._log_citation({"model": model, "ok": False, "reason": "no_source"})
            return False, {"reason": "no_source"}
        # 取最具体的两个 token（型号代码/专名优先）
        toks = [t for t in _re.split(r"[^0-9A-Za-z一-鿿]+", model)
                if len(t) >= 3 and not t.isdigit()]
        toks.sort(key=len, reverse=True)
        toks = [t.lower() for t in toks[:2]]
        if not self.api_key:
            self._log_citation({"model": model, "ok": False, "reason": "no_api_key"})
            return False, {"reason": "no_api_key"}
        for url in srcs:
            cached = self._citation_cache.get(url)
            if cached is not None:
                continue
            t0 = _time.time()
            try:
                _t0 = _time.time()
                r = _req.post("https://api.deepseek.com/v1/tools/fetch",
                              headers={"Authorization": f"Bearer {self.api_key}",
                                       "Content-Type": "application/json"},
                              json={"url": url}, timeout=40)
                status = r.status_code
                body = r.json() if status == 200 else {}
                self._api_log({"api": "fetch", "url": url, "status": status,
                               "ms": round((_time.time() - _t0) * 1000),
                               "billable": status == 200,
                               "cost_usd": 0.00075 if status == 200 else 0})
            except Exception as e:  # noqa: BLE001
                status, body = 0, {}
                self._log_citation({"model": model, "url": url, "ok": False,
                                    "reason": f"{type(e).__name__}",
                                    "ms": round((_time.time() - t0) * 1000)})
                self._citation_cache[url] = {"ok": False}
                continue
            text = ((body.get("title") or "") + " " + (body.get("content") or "")).lower()
            hit = any(t in text for t in toks) if toks else bool(text)
            rec = {"model": model, "url": url, "status": status,
                   "chars": len(body.get("content") or ""), "tokens": toks,
                   "ok": bool(hit), "ms": round((_time.time() - t0) * 1000)}
            self._log_citation(rec)
            self._citation_cache[url] = rec
            if hit:
                return True, rec
        return False, {"reason": "no_source_matched"}

    def fetch(self, target: Target, part: str) -> list[Asset]:
        return self.fetch_fn(target, part)

    def verify(self, asset: Asset, part: str) -> Verification:
        return self.verifier.verify(asset, part)

    # ------------------------------------------------------------------ live
    def _append_log(self, path, rec: dict) -> None:
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + chr(10))

    def live_fetch(self, target: Target, part: str) -> list[Asset]:
        """真实 360 → 下载 → 两段式门卫 → 分层判定（视角只作 hint）。

        审计要求（2026-11-10）：**每一张下载到的图都落盘并写 `fetch_log.jsonl`**
        （含未通过门卫的），供人工核对“到底抓到了什么”。
        """
        from .. import gate, imagesearch

        key = target.query or target.model
        hits = self._search_cache.get(key)
        if hits is None:
            variants = imagesearch.query_variants(key, target.model)
            hits = []
            for q in variants:
                if self.router is not None:
                    got, _diag = self.router.search(q, 6, target.model)
                else:
                    got, _diag = imagesearch.search_images_hd(
                        q, limit=6, model=target.model)
                hits = got or hits
                if hits:
                    break
            self._search_cache[key] = hits

        log_path = None
        if self.image_dir:
            self.image_dir.mkdir(parents=True, exist_ok=True)
            log_path = self.image_dir.parent / "fetch_log.jsonl"

        out: list[Asset] = []
        for hit in hits:
            url_key = hit.get("url", "")
            if url_key in self._fetch_cache:
                res = self._fetch_cache[url_key]
            else:
                res = imagesearch._download_and_gate(hit)
                self._fetch_cache[url_key] = res
            data = res.get("data")
            if res.get("error") or not data:
                if log_path:
                    self._append_log(log_path, {
                        "model": target.model, "part": part,
                        "url": hit.get("url", ""), "title": hit.get("title", ""),
                        "ok": False, "error": res.get("error") or "no_data",
                    })
                continue
            pre = res.get("prefilter") or {}
            g = res.get("gate") or {}
            width = int(pre.get("width") or 0)
            height = int(pre.get("height") or 0)
            view_result = (gate.classify_view(data)
                           if (pre.get("ok") and g.get("pass")) else {})
            a = gate.assess_from_gate(g, view_result, width, height,
                                      prefilter_result=pre)
            asset_id = hashlib.sha1(hit["url"].encode("utf-8")).hexdigest()[:12]
            if self.image_dir:
                d = self.image_dir / re.sub(r"[^\w]+", "_", target.model)[:40]
                d.mkdir(parents=True, exist_ok=True)
                (d / f"{asset_id}.jpg").write_bytes(data)
                if log_path:
                    self._append_log(log_path, {
                        "model": target.model, "part": part,
                        "url": hit.get("url", ""), "title": hit.get("title", ""),
                        "sha1": asset_id, "image": f"{d.name}/{asset_id}.jpg",
                        "width": width, "height": height, "ok": True,
                        "stage": a.get("stage"),
                        "gate_version": gate.GATE_LABEL_VERSION,
                        "gate_pass": bool(g.get("pass")),
                        "margin": g.get("margin"),
                        "keep": g.get("keep"), "drop": g.get("drop"),
                        "keep_label": g.get("keep_label", ""),
                        "drop_label": g.get("drop_label", ""),
                        "scene": a.get("scene"),
                        "view": a.get("view", ""), "view_gap": a.get("view_gap"),
                        "res_standard": a.get("res_standard"),
                        "res_high": a.get("res_high"),
                        "reference_ok": a.get("reference_candidate"),
                        "reasons": a.get("reasons") or [],
                        "hints": a.get("hints") or [],
                        "pre_reasons": (pre.get("reasons") or []),
                    })
            # 分辨率不再作为放行条件：通过两段式门卫的图都交给 loop/人审
            if not a.get("pass"):
                continue
            out.append(Asset(
                asset_id=asset_id,
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
