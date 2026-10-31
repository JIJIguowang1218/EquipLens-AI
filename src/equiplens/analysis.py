"""分析模块（L5）：图片 → 结构化分析。

契约见 docs/superpowers/specs/2026-10-31-analysis-schema-design.md。

本模块只做四件事：
1. 组装 prompt（词表 + 构型名词表 + 文风规则 + 已用风格词）
2. 调 provider 拿 JSON
3. 校验（schema/可见性/三词/构型名）
4. 多视角合并

不碰数据库、不碰渲染——那两块在 scripts/ 里。
"""

from __future__ import annotations

import base64
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"

VISIBLE_RANK = {"full": 3, "partial": 2, "not_visible": 1}
REGION_FIELDS = ("gesture", "character_lines", "proportion", "cmf", "judgement")

SYSTEM = "你是商用车/工程机械造型分析师。只写图上看得见的。文字从简，一句一个判断。"

PROMPT_HEAD = """对象：{vehicle}
本报告已用风格词（不要再用）：{used}
风格词表（只能选，三词须来自三个不同簇）：
{vocab}
构型名词表（term 必须命中，不得自造；每条括注适用条件）：
{terms}

输出 JSON：
1) unit —— 前脸整体，kind=region，members=[grille, headlamp, bumper, brand_zone]
   gesture 一句≤30字；character_lines 2–3 条各≤30字，写清从哪到哪；
   proportion 一句（估读比例标"估"）；cmf 一句；judgement 一句≤30字；
   style_tags 恰好3个：{{"tag","cluster","evidence"}}，evidence ≤20字且必须指向图上图形。
2) parts —— {slots}
   slot, term（来自名词表）, aliases[], part_family（主体构成定族：连续板面=sheet_metal /
   杆件型材=frame_profile / 铸锻实体=cast_forged / 独立功能件=function_attachment）,
   family_reason, visible（full/partial/not_visible）, bbox[4]（0-1000 或 null）,
   form, cmf{{material_class,finish}}, intent（≤1句，因果最多两级）。
3) unplaced —— [{{"text","reason_not_fit","suggested_slot"}}]，无则空数组。

硬性：parts 里每个 slot 必须**原样使用**上面列出的名称（中文就写中文，不要改写成 front_face/bumper 之类）。

写作纪律：不用「由…构成/通过…实现/呈现出/值得注意的是」；不解释术语；不写「整体感强/大气/很有质感」；
同一信息不写两遍；不可见=not_visible 且 term/form/cmf/intent 一律 null，不许补；不要「其它」字段。
只输出 JSON。"""


def load_config(env_file: Path | None = None) -> dict:
    """读 .env + 环境变量（环境变量优先）。"""
    cfg = {}
    path = env_file or (ROOT / ".env")
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip()
    for k in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_VISION_MODEL", "LLM_MODEL"):
        if os.environ.get(k):
            cfg[k] = os.environ[k]
    return cfg


def load_vocab(path: Path | None = None) -> dict:
    d = json.loads((path or DATA / "style_vocabulary.json").read_text(encoding="utf-8"))
    return {c: v["words"] for c, v in d["clusters"].items()}


def load_taxonomy(path: Path | None = None) -> dict:
    d = json.loads((path or DATA / "part_taxonomy.json").read_text(encoding="utf-8"))
    return {k: [t["name"] for t in v["terms"]] for k, v in d["parts"].items()}


def taxonomy_with_when(path: Path | None = None) -> dict:
    d = json.loads((path or DATA / "part_taxonomy.json").read_text(encoding="utf-8"))
    return {k: v for k, v in d["parts"].items()}


# ---------------------------------------------------------------- 校验

def validate_analysis(data: dict, used, vocab: dict, tax: dict,
                      required_slots=("grille", "bumper", "side_guard",
                                      "wheel_arch", "step"),
                      require_unit: bool = True) -> list[str]:
    """返回违规项列表；空列表 = 通过。require_unit=False 用于补证的单视角调用。"""
    errs: list[str] = []
    unit = data.get("unit") or {}
    if require_unit:
        if unit.get("kind") != "region":
            errs.append("unit.kind 应为 region")

        tags = unit.get("style_tags") or []
        if len(tags) != 3:
            errs.append(f"style_tags 数量={len(tags)}，应为 3")
        clusters = [t.get("cluster") for t in tags]
        if len(set(clusters)) != len(clusters):
            errs.append(f"style_tags 同簇：{clusters}")
        used_set = set(used or [])
        for t in tags:
            w, c = t.get("tag"), t.get("cluster")
            if w not in vocab.get(c, []):
                errs.append(f"词 {w!r} 不在簇 {c!r}")
            if not (t.get("evidence") or "").strip():
                errs.append(f"词 {w!r} 缺 evidence")
            if w in used_set:
                errs.append(f"词 {w!r} 与本报告已用词重复")

        for f in ("gesture", "judgement"):
            s = unit.get(f) or ""
            if len(s) > 40:
                errs.append(f"{f} 长 {len(s)}，超 40 字")
        lines = unit.get("character_lines") or []
        if not 2 <= len(lines) <= 3:
            errs.append(f"character_lines 应为 2–3 条，实为 {len(lines)}")
        for i, ln in enumerate(lines):
            if len(ln) > 40:
                errs.append(f"character_lines[{i}] 长 {len(ln)}，超 40 字")

    parts = data.get("parts") or []
    if not isinstance(parts, list):
        errs.append("parts 不是数组")
        parts = []
    if any(not isinstance(p, dict) for p in parts):
        errs.append("parts 含非对象元素")
        parts = [p for p in parts if isinstance(p, dict)]
    slots = [p.get("slot") for p in parts]
    missing = [s for s in required_slots if s not in slots]
    if missing and not parts:
        errs.append(f"缺部件 {', '.join(missing)}")
    for p in parts:
        slot, vis = p.get("slot"), p.get("visible")
        if slot not in required_slots and slot not in set(required_slots):
            pass
        if vis not in VISIBLE_RANK:
            errs.append(f"{slot} visible={vis!r} 非法")
            continue
        if vis == "not_visible":
            for f in ("term", "form", "cmf", "intent"):
                if p.get(f):
                    errs.append(f"{slot} 标为 not_visible 却填了 {f}")
            continue
        if slot in tax and p.get("term") not in tax[slot]:
            errs.append(f"{slot} 的 term {p.get('term')!r} 不在名词表")
        if not p.get("part_family"):
            errs.append(f"{slot} 缺 part_family")
        bbox = p.get("bbox")
        if not (isinstance(bbox, list) and len(bbox) == 4
                and all(isinstance(x, (int, float)) and 0 <= x <= 1000 for x in bbox)):
            errs.append(f"{slot} bbox 非法")
    return errs


# ---------------------------------------------------------------- 合并

def merge_views(primary: dict, secondary: dict, view_tag: str = "second") -> dict:
    """用第二视角补齐/替换可见性更差的部件；主视角 region 不动。"""
    out = json.loads(json.dumps(primary))  # 深拷贝
    sec = {p.get("slot"): p for p in (secondary.get("parts") or [])}
    for i, p in enumerate(out.get("parts") or []):
        s = sec.get(p.get("slot"))
        if not s:
            continue
        if VISIBLE_RANK.get(s.get("visible"), 0) > VISIBLE_RANK.get(p.get("visible"), 0):
            merged = dict(s)
            merged["source_view"] = view_tag
            out["parts"][i] = merged
    out.setdefault("views", []).append(view_tag)
    return out


class TagLedger:
    """跨车风格词台账：给出已用词，检查簇均衡。"""

    def __init__(self, vocab: dict):
        self.vocab = vocab
        self.used: list[str] = []
        self.cluster_count: dict[str, int] = {}

    def take(self, tags: list[str]) -> list[str]:
        self.used.extend(tags)
        for t in tags:
            for c, words in self.vocab.items():
                if t in words:
                    self.cluster_count[c] = self.cluster_count.get(c, 0) + 1
        return tags

    def balance(self) -> int:
        counts = [self.cluster_count.get(c, 0) for c in self.vocab]
        return max(counts) - min(counts) if counts else 0


# ---------------------------------------------------------------- provider

class ApiProvider:
    """OpenAI 兼容的视觉调用。"""

    def __init__(self, config: dict, timeout: int = 300):
        self.base = config["LLM_BASE_URL"].rstrip("/")
        self.key = config["LLM_API_KEY"]
        self.model = config.get("LLM_VISION_MODEL") or config["LLM_MODEL"]
        self.timeout = timeout
        self.calls = 0
        self.tokens = 0

    def call(self, image: Path, prompt: str) -> str:
        b64 = base64.b64encode(image.read_bytes()).decode()
        mime = "image/png" if image.suffix.lower() == ".png" else "image/jpeg"
        payload = {
            "model": self.model,
            "reasoning_effort": "low",
            "max_tokens": 12000,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                ]},
            ],
        }
        req = urllib.request.Request(
            self.base + "/chat/completions",
            data=json.dumps(payload).encode(),
            headers={"Authorization": f"Bearer {self.key}",
                     "Content-Type": "application/json"},
        )
        for attempt in (1, 2, 3):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    d = json.load(r)
                self.calls += 1
                self.tokens += (d.get("usage") or {}).get("total_tokens", 0)
                return d["choices"][0]["message"]["content"] or ""
            except (urllib.error.URLError, TimeoutError) as e:
                if attempt == 3:
                    raise
                time.sleep(2 * attempt)
        raise RuntimeError("unreachable")


class MockProvider:
    """离线夹具：按预置 JSON 返回，用于测试与 CI。"""

    def __init__(self, responses: dict):
        self.responses = responses

    def call(self, image: Path, prompt: str) -> str:
        return self.responses[str(image)]


# ---------------------------------------------------------------- 主流程

def build_prompt(vehicle: str, used: list[str], slots: list[str],
                 vocab: dict | None = None, tax_when: dict | None = None) -> str:
    vocab = vocab or load_vocab()
    tax_when = tax_when or taxonomy_with_when()
    vocab_txt = json.dumps(vocab, ensure_ascii=False)
    term_lines = []
    for s in slots:
        info = tax_when.get(s)
        if info:
            names = "；".join(f"{t['name']}（{t['when']}）" for t in info.get("terms", []))
            term_lines.append(f"- {s} {info.get('label', '')}: {names}")
        else:
            term_lines.append(
                f"- {s}（自定义部位，不在词表）：按同一四槽结构描述；"
                f"term 用行业通称（如\"后视镜总成\"），没有公认叫法就写 null 并在 unplaced 里说明；"
                f"不要因为不在词表就跳过这个部位")
    return PROMPT_HEAD.format(
        vehicle=vehicle,
        used="、".join(used) if used else "（无）",
        vocab=vocab_txt,
        terms="\n".join(term_lines),
        slots="、".join(slots),
    )


def parse_json(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("无 JSON 输出")
    return json.loads(m.group(0))


def normalize_analysis(data: dict) -> list[str]:
    """把自相矛盾的字段就地修掉（记录修了什么），避免为一个空对象烧掉一次重试。"""
    repairs: list[str] = []
    parts = data.get("parts")
    if not isinstance(parts, list):
        return repairs
    for p in parts:
        if not isinstance(p, dict):
            continue
        if p.get("visible") == "not_visible":
            for f in ("term", "form", "cmf", "intent"):
                if p.get(f):
                    p[f] = None
                    repairs.append(f"{p.get('slot')}.{f}")
        if isinstance(p.get("bbox"), list) and len(p["bbox"]) != 4:
            p["bbox"] = None
            repairs.append(f"{p.get('slot')}.bbox")
    return repairs


def analyze(provider, vehicle: str, image: Path, slots: list[str],
            used: list[str], vocab: dict, tax: dict,
            view_tag: str = "hero", max_retry: int = 1) -> dict:
    prompt = build_prompt(vehicle, used, slots, vocab)
    errors: list[str] = []
    for attempt in range(max_retry + 1):
        p = prompt if not errors else (
            prompt + "\n\n上一次输出有下列问题，请修正后重新输出：\n- " + "\n- ".join(errors))
        raw = provider.call(image, p)
        try:
            data = parse_json(raw)
        except ValueError as e:
            errors = [str(e)]
            continue
        repairs = normalize_analysis(data)
        errors = validate_analysis(data, used, vocab, tax, required_slots=slots)
        if not errors:
            data["_meta"] = {"vehicle": vehicle, "view": view_tag,
                             "image": str(image), "attempts": attempt + 1,
                             "repairs": repairs}
            for part in data.get("parts", []):
                part.setdefault("source_view", view_tag)
            return data
    return {"_meta": {"vehicle": vehicle, "view": view_tag, "image": str(image),
                      "status": "needs_review", "errors": errors},
            "parts": [], "unit": {}}


SUPP_HEAD = """对象：{vehicle}（补证视角，只补这几个部位：{slots}）
构型名词表（term 必须命中，不得自造）：
{terms}

只输出 parts 块：{{"parts": [{{"slot","term","aliases","part_family","family_reason",
"visible"（只能取 full / partial / not_visible）,"bbox","form","cmf":{{"material_class","finish"}},"intent"}}]}}
part_family 按主体构成定族：连续板面=sheet_metal / 杆件型材=frame_profile /
铸锻实体=cast_forged / 独立功能件=function_attachment。
看不清 = not_visible，且 term/form/cmf/intent 一律 null，不许补。
每槽 ≤2 句、每句 ≤30 字；不用「由…构成/通过…实现/呈现出」；不写空评价。只输出 JSON。"""


def build_supp_prompt(vehicle: str, slots: list[str],
                      tax_when: dict | None = None) -> str:
    tax_when = tax_when or taxonomy_with_when()
    lines = []
    for s in slots:
        info = tax_when.get(s, {})
        names = "；".join(f"{t['name']}（{t['when']}）" for t in info.get("terms", []))
        lines.append(f"- {s} {info.get('label', '')}: {names}")
    return SUPP_HEAD.format(vehicle=vehicle, slots="、".join(slots), terms="\n".join(lines))


def analyze_supp(provider, vehicle: str, image: Path, slots: list[str],
                 vocab: dict, tax: dict, max_retry: int = 1) -> dict:
    """补证视角：只回 parts；失败带原因重试一次，仍失败则只回通过校验的部分。"""
    prompt = build_supp_prompt(vehicle, slots)
    errors: list[str] = []
    for _ in range(max_retry + 1):
        p = prompt if not errors else (
            prompt + "\n\n上一次输出有下列问题，请修正：\n- " + "\n- ".join(errors))
        raw = provider.call(image, p)
        try:
            data = parse_json(raw)
        except ValueError as e:
            errors = [str(e)]
            continue
        normalize_analysis(data)
        errors = validate_analysis(data, [], vocab, tax, required_slots=slots,
                                   require_unit=False)
        if not errors:
            return {"parts": data.get("parts", [])}
    return {"parts": [], "_errors": errors}


# ---------------------------------------------------------------- 渲染辅助

def render_prompt_preview(vehicle: str, slots: list[str], used: list[str]) -> str:
    """调试用：看 prompt 长什么样。"""
    return build_prompt(vehicle, used, slots)
