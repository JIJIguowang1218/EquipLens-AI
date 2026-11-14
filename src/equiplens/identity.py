# -*- coding: utf-8 -*-
"""车型标识规范（第一段规划去重 / 第二段图片核验共用）。

背景（2026-11-14 审计）：
- 第一段 `planning._CODE_PATTERNS` 要求"字母 + ≥3 位数字"，第二段
  `RuleVerifier` 另写了一个"字母 1-4 + ≥3 位数字"的正则，两边不一致；
- `HF 8066`（空格）、`K-65959`（连字符）、`CPD50-B`（2 位数字）在两段表现不同；
  `XS265HS` 在标题写成 `XS265` 时被判不是同一台；
- `code in title` 是子串匹配，`RS45（B921）` 会把括号里的 `B921` 当车型码去命中 `B921RR`。

本模块只做"标识符归一化"，**不做主题判断**（是不是车/配件由门卫负责），
也不做模糊匹配：型号代码必须可指认，模糊相似度会把不同型号并在一起。

规则：
1. 主码 = 括号外的第一个"强"标识；括号里的底盘/备注不算主身份；
2. 允许字母/数字之间的空格、连字符、下划线、点（`HF 8066` / `K-65959` / `TGM18.290`）；
   但"品牌词 + 空格 + 型号"不算一个码（`John Deere 6170R` → 取 `6170R`）；
3. 核心候选 = 去掉尾部纯字母后缀（XS265HS→XS265、CPD50B→CPD50）；
   点分段额外保留"到最后一个点分段"的前缀（TGM18.290B6→TGM18.290，不退化到 TGM18）；
4. 匹配 = 左边界严格、右侧允许字母延伸、不允许数字延伸
   （XS265 命中 XS265HS/XS202JE，不命中 XS2650）；
5. 纯数字代码必须带尾部字母才当标识（6170R），且按完整串匹配。
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_STOP_WORDS = {"GVW", "HP", "KW", "NM", "KG", "MM", "CM", "CC",
               "RPM", "TON", "MPH", "KPH"}

# 连续写法：XS265HS / ZZ4257V455GF1 / FE4P25N
_CONTIG_RE = re.compile(
    r"(?<![A-Za-z0-9])(?P<letters>[A-Za-z]{0,6})(?P<digits>\d{1,6})"
    r"(?P<rest>(?:\.\d{1,4})*)(?P<tail>[A-Za-z0-9]*)"
)
# 分隔写法：HF 8066 / K-65959 / SMV 4542（字母前缀 ≤4，避免把品牌词当码）
_SPACED_RE = re.compile(
    r"(?<![A-Za-z0-9])(?P<letters>[A-Za-z]{1,4})[\s\-_]{1,2}(?P<digits>\d{2,6})"
    r"(?P<rest>(?:\.\d{1,4})*)(?P<tail>[A-Za-z0-9]*)"
)
_CONFIG_RE = re.compile(r"^\d+[Xx]\d+$")
_SPEC_UNIT_RE = re.compile(r"^\d+(?:\.\d+)?[TL]$")
_TRAIL_LETTERS_RE = re.compile(r"[A-Z]+$")
_LAST_DOT_SEG_RE = re.compile(r"^(.*\.\d+)")


@dataclass(frozen=True)
class CodeToken:
    """一个可核验的车型标识。"""

    full: str               # 字母+数字+点分段+尾部（去分隔符、大写）
    cores: tuple[str, ...]  # 可匹配的核心（含退化候选）

    @property
    def letters(self) -> str:
        return re.match(r"[A-Z]*", self.full).group(0)

    @property
    def weak(self) -> bool:
        """纯数字核心太泛（18 / 340）——必须有尾部字母才算标识。"""
        return not self.letters and not _TRAIL_LETTERS_RE.search(self.full)


def _canon(text: str) -> str:
    return re.sub(r"[^A-Z0-9.]", "", (text or "").upper())


def _cores_of(full: str) -> tuple[str, ...]:
    cores: list[str] = []
    base = _TRAIL_LETTERS_RE.sub("", full)
    tail_len = len(full) - len(base)
    if tail_len >= 3:
        return (full,)  # 尾部是上装/变体编码：整串匹配，不退化
    if base and base != full:
        cores.append(base)
    m = _LAST_DOT_SEG_RE.match(base or full)
    if m:
        cores.append(m.group(1))
    if not cores:
        cores.append(full)
    seen: list[str] = []
    for c in cores:
        if c and c not in seen:
            seen.append(c)
    return tuple(seen)


def tokenize_codes(text: str) -> list[CodeToken]:
    """抽取文本里的候选标识（按出现顺序，去重）。"""
    upper = (text or "").upper()
    found: list[tuple[int, str]] = []
    for m in _CONTIG_RE.finditer(upper):
        found.append((m.start(), m.group(0)))
    for m in _SPACED_RE.finditer(upper):
        found.append((m.start(), m.group(0)))
    found.sort()

    out: list[CodeToken] = []
    seen: set[str] = set()
    for _, raw in found:
        # 分离字母/数字/点分段/尾部
        m = re.match(
            r"(?P<letters>[A-Z]{0,6})[\s\-_]{0,2}(?P<digits>\d{1,6})"
            r"(?P<rest>(?:\.\d{1,4})*)(?P<tail>[A-Za-z0-9]*)", raw)
        if not m:
            continue
        letters = m.group("letters") or ""
        digits = m.group("digits") or ""
        rest = m.group("rest") or ""
        tail = _canon(m.group("tail") or "")
        if not digits:
            continue
        full = f"{letters}{digits}{rest}{tail}"
        if full in seen:
            continue
        if _CONFIG_RE.match(full) or _SPEC_UNIT_RE.match(full):
            continue
        if letters in _STOP_WORDS:
            continue
        if tail.upper() in _STOP_WORDS:
            continue  # 371HP / 340KW 是功率不是型号
        if len(re.sub(r"[^0-9]", "", full)) < 2:
            continue
        if not letters:
            # 纯数字开头只接受“单个尾部字母”的型号（6170R）；12CUBIC / 10WHEELS 是容量
            tail_only = full[len(re.sub(r"[A-Z]+$", "", full)):]
            if not re.fullmatch(r"[A-Z]", tail_only):
                continue
        seen.add(full)
        out.append(CodeToken(full=full, cores=_cores_of(full)))
    return out


def primary_code(model: str) -> CodeToken | None:
    """主身份码：括号外的第一个强标识；括号内的底盘/备注不算。"""
    outside = re.sub(r"[（(][^）)]*[）)]", " ", model or "")
    for tok in tokenize_codes(outside):
        if not tok.weak:
            return tok
    # 括号外没有码时，允许括号内列出的型号（北奔 ND5180 这类写法）
    inner = " ".join(re.findall(r"[（(]([^）)]*)[）)]", model or ""))
    for tok in tokenize_codes(inner):
        if not tok.weak:
            return tok
    return None


def validate_model_code(value: str) -> bool:
    """LLM 给的 `slots.model_code` 是否真的是型号代码（防 `4X2`/`8方`/`340Hp`）。"""
    raw = (value or "").strip()
    if not raw or not re.search(r"[A-Za-z]", raw):
        return False
    if len(re.findall(r"\d", raw)) < 2:
        return False
    if _CONFIG_RE.match(re.sub(r"[\s\-_]", "", raw).upper()):
        return False
    return any(not t.weak for t in tokenize_codes(raw))


def _flex_pattern(flat: str) -> str:
    """把 "HF8066" 变成允许字符间插分隔符的正则。"""
    parts = [re.escape(ch) for ch in flat]
    return r"(?<![A-Z0-9])" + r"[\s\-_.]{0,2}".join(parts) + r"(?![0-9])"


def matches_core(token: CodeToken, title: str) -> bool:
    """标题里是否出现该标识（左边界严格、右侧允许字母、不允许数字）。"""
    text = (title or "").upper().replace("×", "X")
    if not token.letters:
        # 纯数字开头（6170R）：必须连尾部字母整体出现，避免 6170 命中“6170元”
        pat = _flex_pattern(token.full).replace(r"(?![0-9])", r"(?![A-Z0-9])")
        return re.search(pat, text) is not None
    for core in token.cores:
        flat = core.replace(".", "")
        if re.search(_flex_pattern(flat), text):
            return True
    return False


def code_in_title(model: str, title: str) -> bool:
    """第二段核验入口：模型名的主码是否出现在图片标题里。"""
    tok = primary_code(model)
    return bool(tok) and matches_core(tok, title)
