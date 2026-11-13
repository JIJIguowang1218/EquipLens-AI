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

# 目标级早停：同一台车连续这么多张下载硬失败（403/死链）就放弃该台
EARLY_STOP_FAILS = 8


class _Done:
    """已算好的结果，伪装成 future（workers=1 的对照臂用）。"""
    __slots__ = ("_value",)

    def __init__(self, value):
        self._value = value

    def result(self):
        return self._value


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
        elif series_hit and cfg_hit:
            # 去表化证据（2026-11-14）：拉丁车系 + 构型双命中即可 probable，
            # 不再要求“品牌表认识这个牌子”。单靠品牌词不算（HOWO TX 会被误当
            # HOWO 全驱牵引车），必须两个信号。
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
            # ② 部件-可见性 / ③ 改装-原厂 已于 2026-11-12 归档
            # （见 docs/killed-strategies.md）：不再计算，也不再用“有宽高”冒充可见性。
            # 字段保留只是为了兼容旧 evidence 记录，值为 unknown。
            visibility="unknown",
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
                 citation_check: bool = True, api_key: str | None = None,
                 pins: list[str] | None = None,
                 unit_quotas: dict[str, int] | None = None,
                 platform_extra: str = "", code_prefilter: bool = False,
                 download_workers: int = 4, plan_meta: dict | None = None):
        if isinstance(models, list):
            models = {"*": models}
        self.models = models or {}
        self.download_workers = max(1, int(download_workers or 1))
        self.plan_meta = dict(plan_meta or {})
        self.image_dir = Path(image_dir) if image_dir else None
        self.discover_limit = discover_limit
        self._search_cache: dict[str, list] = {}
        self._fetch_cache: dict[str, dict] = {}   # url → _download_and_gate 结果
        self.plan = list(plan or [])
        self.platform_extra = (platform_extra or "").strip().lower()
        self.code_prefilter = bool(code_prefilter)
        self.pins = [p.lower() for p in (pins or [])]
        for c in self.plan:
            model = str(c.get("model") or "").lower()
            if any(x and x in model for x in self.pins):
                c["pinned"] = True
                c["role"] = "primary"
        self._plan_sorted = False
        self.unit_quotas = dict(unit_quotas or {})
        self._unit_queues: dict[str, list[dict]] = {}
        self._unit_used: set[str] = set()
        self._replacement: list[dict] = []
        self._replacement_cursor = 0
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
        # 实际发出的搜索请求数（一次 search 调用可能展开成多条查询，如 高清/大图）
        self.query_count = 0
        # 下载健康（按 host 学习拉黑）与每目标的抓取统计
        self._health = None
        self.fetch_stats: dict[str, dict] = {}

    def _count_queries(self, diag) -> None:
        """按诊断条目数累加真实查询数；无诊断时按 1 次计。"""
        try:
            n = len(diag) if isinstance(diag, (list, tuple)) else 1
        except TypeError:
            n = 1
        self.query_count += max(1, int(n))

    def download_stats(self) -> dict:
        """本次 run 的下载质量统计（供 summary/审核页解释“为什么没图”）。"""
        agg = {"hits": 0, "downloaded": 0, "failed": 0, "blocked": 0,
               "gate_pass": 0, "early_stop_models": 0}
        for d in self.fetch_stats.values():
            for k in ("hits", "downloaded", "failed", "blocked", "gate_pass"):
                agg[k] += int(d.get(k, 0) or 0)
            agg["early_stop_models"] += 1 if d.get("early_stop") else 0
        agg.update(self._health.stats() if self._health else
                   {"blocked_hosts": [], "fail_counts": {}})
        return agg

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
        """长名字 → 检索键：型号码优先（**包含括号里的码**），其次拉丁车系，最后类目短语。

        2026-11-13 修复三件事（见 docs/query-kill-chain-20261113.md）：
        - 型号码在括号里时，旧实现先删括号 → 码丢失；现在先在原始串上找码；
        - 不再无条件拼 `6x6`（叉车/压路机被带偏）；
        - 纯描述名去掉构型/驱动词后截短，避免超长中文查询召回差。
        """
        import re as _re
        raw = model or ""
        conf = next((c for c in ("6x6", "8x8", "4x4")
                     if c in raw.replace("×", "x").lower()), "")
        code = _re.search(r"[A-Z]{1,4}\d{3,}[A-Z0-9]*", raw)
        if code:
            pre = _re.sub(r"[（(][^）)]*[）)]", " ", raw[:code.start()])
            brand = _re.search(r"[一-鿿]{2,4}", pre)
            return " ".join(p for p in ((brand.group(0) if brand else ""),
                                        code.group(0), conf) if p).strip()
        s = _re.sub(r"[（(][^）)]*[）)]", " ", raw).replace("×", "x")
        s = " ".join(s.split())
        series = next((t for t in s.split()
                       if _re.fullmatch(r"[A-Za-z][A-Za-z\-]{2,}", t)), "")
        if series:
            return " ".join(p for p in (series, conf) if p).strip()
        # 纯描述名：去掉构型/驱动词，保留类目短语（纯字符串规则，不查表）
        key = _re.sub(r"(?i)(6x6|8x8|4x4|8x4|6x4|4x2|6x2|全轮驱动|全驱|六驱|八驱|四驱)",
                      " ", s)
        key = " ".join(key.split())[:14].strip(" /,、;")
        if conf and conf not in key.lower():
            key = f"{key} {conf}".strip()
        return key

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

    def _partition_plan(self) -> None:
        """按 unit 配额预留 primary；unit 的补位只能取 replacement，不能抢别人的 primary。"""
        if self._unit_queues or not self.unit_quotas:
            return
        self.plan.sort(key=self._candidate_key)
        pos = 0
        for uid, quota in self.unit_quotas.items():
            q = max(0, int(quota))
            self._unit_queues[uid] = self.plan[pos:pos + q]
            pos += q
        self._replacement = self.plan[pos:]

    @staticmethod
    def _candidate_key(c: dict) -> tuple:
        role = {"primary": 0, "backup": 1}.get(str(c.get("role") or ""), 2)
        return (0 if c.get("pinned") else 1, role,
                int(c.get("intent_rank") or 10 ** 9),
                0 if c.get("citation_ok") else 1,
                int(c.get("priority", 99)))

    def _plan_targets(self, unit) -> list[Target]:
        """从规划池取下一批候选（带引用）；intent 先验优先，citation 只作次序兜底。"""
        if not self._plan_sorted:
            self.plan.sort(key=self._candidate_key)
            self._plan_sorted = True
        self._partition_plan()
        quota = int(getattr(unit, "quota", 0) or 0) or self.batch_size
        limit = min(self.batch_size, quota)
        uid = getattr(unit, "unit_id", "")
        if self.unit_quotas and uid in self._unit_queues and uid not in self._unit_used:
            self._unit_used.add(uid)
            batch = self._unit_queues[uid]
        elif self.unit_quotas:
            batch = self._replacement[self._replacement_cursor:
                                      self._replacement_cursor + limit]
            self._replacement_cursor += len(batch)
        else:
            batch = self.plan[self._plan_cursor:self._plan_cursor + limit]
            self._plan_cursor += len(batch)
        rows = []
        for c in batch:
            ok, ev = (True, {}) if not self.citation_check else self._verify_citation(c)
            rows.append((c, ok, ev))
        rows.sort(key=lambda x: self._candidate_key(x[0]))
        out = []
        for c, ok, ev in rows:
            model = (c.get("model") or "").strip()
            if not model:
                continue
            out.append(Target(
                target_id=model, model=model, source="plan", tier=unit.tier,
                parts=tuple(unit.parts), unit_id=unit.unit_id,
                sources=tuple(c.get("sources") or []), citation_ok=ok,
                query=(c.get("query") or self.normalize_query(model)),
                identity_kind=(c.get("identity_kind") or ""),
                intent_rank=int(c.get("intent_rank") or 0),
                intent_band=str(c.get("intent_band") or ""),
                intent_reason=str(c.get("intent_reason") or ""),
                role=str(c.get("role") or ""),
                pinned=bool(c.get("pinned"))))
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

    @staticmethod
    def _code_ok(model: str, title: str) -> bool:
        import re as _re
        rx = _re.compile(r"[A-Z]{1,4}\d{3,}[A-Z0-9]*", _re.I)
        tc = {x.lower() for x in rx.findall(model or "")}
        hc = {x.lower() for x in rx.findall(title or "")}
        if not tc or not hc:
            return True
        return bool(tc & hc)

    def _filter_code(self, target, hits):
        if not self.code_prefilter or target.identity_kind != "code":
            return hits
        return [h for h in hits if self._code_ok(target.model, h.get("title", ""))]

    @staticmethod
    def _search_360_baidu(query: str, model: str) -> list[dict]:
        """平台层实验：360 + Baidu，下载前复用 _relevant 预筛。"""
        from .. import imagesearch

        got, _diag = imagesearch.search_platforms(
            query, limit=8, model=model, platforms=("360", "baidu"))
        return got

    def _iter_hit_results(self, hits: list[dict]):
        """按原顺序产出 `(hit, mode, future)`，同时把下载 I/O 并发起来。

        mode：
          - `cached`：URL 已在本次 run 的下载缓存里，不重复下载；
          - `blocked`：提交时该 host 已被拉黑，不下载；
          - `ok`：`future` 是 `_download_and_gate` 的结果（可能失败）。

        并发只发生在“下载 + 门卫”这一段；**结算严格按原顺序**在调用方单线程里做
        （拉黑记账、连续失败早停、fetch_log、缓存与计数），所以语义与串行一致，
        结果顺序也保持确定。窗口固定为 workers，最多多下 workers-1 张无效图。
        """
        from collections import deque
        from concurrent.futures import ThreadPoolExecutor

        from .. import imagesearch

        workers = max(1, int(getattr(self, "download_workers", 1) or 1))
        if workers == 1:
            for hit in hits:
                key = hit.get("url", "")
                if key in self._fetch_cache:
                    yield hit, "cached", None
                elif self._health.is_blocked(key):
                    yield hit, "blocked", None
                else:
                    yield hit, "ok", _Done(imagesearch._download_and_gate(hit, None))
            return

        ex = ThreadPoolExecutor(max_workers=workers)
        pending: deque = deque()
        it = iter(hits)
        exhausted = False

        def submit_until_full() -> None:
            nonlocal exhausted
            while len(pending) < workers and not exhausted:
                try:
                    hit = next(it)
                except StopIteration:
                    exhausted = True
                    break
                key = hit.get("url", "")
                if key in self._fetch_cache:
                    pending.append((hit, "cached", None))
                elif self._health.is_blocked(key):
                    pending.append((hit, "blocked", None))
                else:
                    pending.append((hit, "ok", ex.submit(
                        imagesearch._download_and_gate, hit, None)))
        try:
            submit_until_full()
            while pending:
                item = pending.popleft()
                submit_until_full()
                yield item
        finally:
            ex.shutdown(wait=False, cancel_futures=True)

    @staticmethod
    def _query_tier(model: str, query: str) -> str:
        """这张图来自查询阶梯的哪一档（待办A：来源分级）。

        exact=窄查询（normalize_query）命中；model=车型全名；alias=中文别名改写；
        part_fallback=部件 label + 车型兜底（今后若加类目回退，也归到这一档之后）。
        """
        from .. import imagesearch as _is
        q = (query or "").strip()
        if not q:
            return ""
        if q == WebWorld.normalize_query(model):
            return "exact"
        if q == (model or "").strip():
            return "model"
        if q == _is.alias_query(model):
            return "alias"
        return "part_fallback"

    def live_fetch(self, target: Target, part: str) -> list[Asset]:
        """真实 360 → 下载 → 两段式门卫 → 分层判定（视角只作 hint）。

        审计要求（2026-11-10）：**每一张下载到的图都落盘并写 `fetch_log.jsonl`**
        （含未通过门卫的），供人工核对“到底抓到了什么”。
        """
        from .. import gate, imagesearch

        self._part_query_used = ""
        key = target.query or target.model
        cache_key = key + "|" + self.platform_extra
        hits = self._search_cache.get(cache_key)
        if hits is None:
            variants = imagesearch.query_variants(key, target.model)
            hits = []
            for q in variants:
                _diag = None
                self._part_query_used = q
                if self.router is not None:
                    got, _diag = self.router.search(q, 6, target.model)
                else:
                    if self.platform_extra == "baidu":
                        got = self._search_360_baidu(q, target.model)
                    else:
                        got, _diag = imagesearch.search_images_hd(
                            q, limit=6, model=target.model)
                self._count_queries(_diag)
                got = self._filter_code(target, got)
                hits = got or hits
                if hits:
                    break
            if not hits:
                # 部件类型/位置的最后一个便宜兜底：用“部件 label + 车型”再搜一次。
                req = self.parts.get(part)
                if req is not None and getattr(req, "label", ""):
                    pq = f"{req.label} {target.query}".strip()
                    _diag = None
                    self._part_query_used = pq
                    if self.router is not None:
                        got, _diag = self.router.search(pq, 6, target.model)
                    else:
                        if self.platform_extra == "baidu":
                            got = self._search_360_baidu(pq, target.model)
                        else:
                            got, _diag = imagesearch.search_images_hd(
                                pq, limit=6, model=target.model)
                    self._count_queries(_diag)
                    got = self._filter_code(target, got)
                    if got:
                        hits = got
                        self._part_query_used = pq
            self._search_cache[cache_key] = hits
        if not self._part_query_used:
            # 缓存命中时没有走检索阶梯，用主查询键补记来源档位
            self._part_query_used = key

        log_path = None
        if self.image_dir:
            self.image_dir.mkdir(parents=True, exist_ok=True)
            log_path = self.image_dir.parent / "fetch_log.jsonl"

        if self._health is None:
            self._health = imagesearch.DomainHealth()
        stats = self.fetch_stats.setdefault(
            target.target_id, {"hits": 0, "downloaded": 0, "failed": 0,
                               "blocked": 0, "gate_pass": 0, "early_stop": False})
        stats["hits"] += len(hits)
        if stats.get("early_stop"):
            # 该目标已判定“整批结果都拿不到图”，后续部件不再尝试
            return []
        out: list[Asset] = []
        # 连续失败跨部件累计（同一台车不同部件共享一个计数）
        streak = int(stats.get("streak", 0) or 0)
        for hit, mode, fut in self._iter_hit_results(hits):
            url_key = hit.get("url", "")
            if mode == "cached" or url_key in self._fetch_cache:
                res = self._fetch_cache[url_key]
            elif mode == "blocked" or self._health.is_blocked(url_key):
                stats["blocked"] += 1
                streak += 1
                stats["streak"] = streak
                if log_path:
                    self._append_log(log_path, {
                        "model": target.model, "part": part, "url": url_key,
                        "title": hit.get("title", ""), "ok": False,
                        "error": "domain_blocked",
                        "part_query": getattr(self, "_part_query_used", ""),
                    })
                # 被拉黑的图床同样计入“连续失败”：整批结果都来自死图床时，
                # 这台车已经没有可下的图，早点放弃换下一个候选。
                if streak >= EARLY_STOP_FAILS and stats["downloaded"] == 0:
                    stats["early_stop"] = True
                    if log_path:
                        self._append_log(log_path, {
                            "model": target.model, "part": part, "ok": False,
                            "error": f"early_stop_after_{streak}_failures",
                            "part_query": getattr(self, "_part_query_used", ""),
                        })
                    break
                continue
            else:
                try:
                    res = fut.result()
                except Exception as e:  # noqa: BLE001
                    res = {"hit": hit, "data": None, "gate": None,
                           "error": str(e), "tries": 0}
                self._fetch_cache[url_key] = res
            data = res.get("data")
            if res.get("error") or not data:
                # 拉黑记账放到结算阶段（串行时由 _download_and_gate 内部做）：
                # 保证并发下载不改变“连续失败/拉黑”的判定顺序。
                self._health.record(hit.get("url", ""), res.get("error"))
                stats["failed"] += 1
                streak += 1
                stats["streak"] = streak
                if log_path:
                    self._append_log(log_path, {
                        "model": target.model, "part": part,
                        "url": hit.get("url", ""), "title": hit.get("title", ""),
                        "ok": False, "error": res.get("error") or "no_data",
                        "tries": res.get("tries"), "url_used": res.get("url_used"),
                        "upgraded": res.get("upgraded"),
                        "part_query": getattr(self, "_part_query_used", ""),
                    })
                # 目标级早停：该车连续多张下载硬失败（403/死链），
                # 继续试只是烧时间；把预算让给下一个候选（loop 会补抓）。
                if streak >= EARLY_STOP_FAILS and stats["downloaded"] == 0:
                    stats["early_stop"] = True
                    if log_path:
                        self._append_log(log_path, {
                            "model": target.model, "part": part, "ok": False,
                            "error": f"early_stop_after_{streak}_failures",
                            "part_query": getattr(self, "_part_query_used", ""),
                        })
                    break
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
                        "tries": res.get("tries"), "url_used": res.get("url_used"),
                        "upgraded": res.get("upgraded"),
                        "part_query": getattr(self, "_part_query_used", ""),
                        "query_tier": self._query_tier(
                            target.model, getattr(self, "_part_query_used", "")),
                    })
            stats["downloaded"] += 1
            streak = 0
            stats["streak"] = 0
            # 分辨率不再作为放行条件：通过两段式门卫的图都交给 loop/人审
            if not a.get("pass"):
                continue
            stats["gate_pass"] += 1
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
                scene=a.get("scene", ""),
                overview=bool(a.get("overview_candidate")),
                query_tier=self._query_tier(
                    target.model, getattr(self, "_part_query_used", "")),
                source_query=getattr(self, "_part_query_used", ""),
            ))
        return out
