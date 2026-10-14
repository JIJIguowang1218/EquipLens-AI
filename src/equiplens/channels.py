"""渠道适配器：R1 为夹具渠道（本地 HTML 模拟厂商页）；R7 起接入真实渠道时实现同接口。

页面抽取（stdlib HTMLParser，无第三方依赖）：标题/h1/图片(src,alt)/参数表(th→td)。
alt 文本确定性打标：图文对应证据链的第一条（④ alt 加权）——真正的机器打标属 M4 VLM，
夹具阶段用 alt 关键词作为可验证的替代。
"""

from __future__ import annotations

import hashlib
import html as html_mod
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path

from . import db

ALT_VIEW_RULES = [  # 顺序即优先级，首个命中生效
    ("左前", "hero_lf"), ("右前", "hero_rf"), ("正前", "front"), ("正后", "rear"),
    ("左侧", "side_l"), ("右侧", "side_r"), ("45", "hero_lf"),
    ("内饰", "interior"), ("铭牌", "nameplate"),
]


@dataclass
class ExtractedImage:
    src: str
    alt: str


@dataclass
class ExtractedPage:
    path: Path
    title: str
    h1: str
    images: list[ExtractedImage] = field(default_factory=list)
    params: dict = field(default_factory=dict)

    @property
    def designation(self) -> str:
        """页面明示的型号称呼（同页共现证据 T2 的锚点）。"""
        return (self.h1 or self.title).strip()


class _PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.h1 = ""
        self.images: list[ExtractedImage] = []
        self.params: dict = {}
        self._in_title = self._in_h1 = self._in_th = False
        self._in_td = False
        self._last_th = ""
        self._td_buf = ""

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "title":
            self._in_title = True
        elif tag == "h1":
            self._in_h1 = True
        elif tag == "img":
            self.images.append(ExtractedImage(src=d.get("src", ""), alt=d.get("alt", "")))
        elif tag == "th":
            self._in_th = True
        elif tag == "td":
            self._in_td = True
            self._td_buf = ""

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "h1":
            self._in_h1 = False
        elif tag == "th":
            self._in_th = False
        elif tag == "td":
            self._in_td = False
            if self._last_th and self._td_buf.strip():
                self.params[self._last_th] = self._td_buf.strip()
            self._last_th = ""

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        elif self._in_h1:
            self.h1 += data
        elif self._in_th:
            self._last_th += data
        elif self._in_td:
            self._td_buf += data


class FixtureChannel:
    """本地夹具渠道：root/pages/*.html 为厂商页，图片相对路径指向 root/ 下文件。"""

    name = "夹具渠道"

    def __init__(self, root: Path):
        self.root = Path(root)

    def find_vehicle_pages(self, vehicle_name: str) -> list[ExtractedPage]:
        """按车型名扫描全部夹具页，返回标题/h1 命中的页面（同页共现的来源）。"""
        hits = []
        for page_path in sorted((self.root / "pages").glob("*.html")):
            page = self.parse_page(page_path)
            if vehicle_name in page.title or vehicle_name in page.h1:
                hits.append(page)
        return hits

    def parse_page(self, page_path: Path) -> ExtractedPage:
        parser = _PageParser()
        parser.feed(page_path.read_text(encoding="utf-8"))
        return ExtractedPage(path=page_path, title=parser.title.strip(),
                             h1=parser.h1.strip(), images=parser.images,
                             params=parser.params)

    def read_bytes(self, src: str) -> bytes:
        """图片相对路径 → 字节（真实渠道此步为 HTTP 下载）。"""
        return (self.root / src).read_bytes()


def map_alt_to_tags(alt: str, conn) -> tuple[str, str | None]:
    """alt 文本 → (视角, 部位)。部位按 vocab 词表中文匹配；未命中视角时，有部位记 detail。"""
    view = "untagged"
    for key, v in ALT_VIEW_RULES:
        if key in alt:
            view = v
            break
    part = None
    for r in conn.execute("SELECT id, term FROM vocab WHERE status != 'retired'"):
        if r["term"] and r["term"].split("（")[0] in alt:
            part = r["id"]
            break
    if part and view == "untagged":
        view = "detail"
    return view, part


def resolve_vehicle(conn, name: str) -> str | None:
    """名录名 → vehicle_id：支持 型号 / 品牌 型号 / 品牌/型号 三种写法。"""
    row = conn.execute(
        "SELECT id FROM vehicles WHERE model_name = ? OR brand || ' ' || model_name = ?"
        " OR brand || '/' || model_name = ?", (name, name, name)).fetchone()
    return row["id"] if row else None


def file_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
