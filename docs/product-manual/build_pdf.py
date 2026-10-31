# -*- coding: utf-8 -*-
"""Build the EquipLens-AI product dossier PDF from index.html.

The document is laid out as fixed A4 sheets and printed through Edge
(Chromium).  PDF bookmarks and metadata are added afterwards with PyMuPDF.

Usage:
    python docs/product-manual/build_pdf.py
"""

from __future__ import annotations

from pathlib import Path

import fitz
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
HTML = ROOT / "index.html"
PDF = ROOT / "EquipLens-AI-产品说明书-v1.0.pdf"


def render() -> None:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="msedge")
        page = browser.new_page(viewport={"width": 1200, "height": 1600})
        page.goto(HTML.as_uri(), wait_until="networkidle")
        page.pdf(
            path=str(PDF),
            width="210mm",
            height="297mm",
            print_background=True,
            margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
            prefer_css_page_size=True,
        )
        browser.close()


def decorate() -> None:
    doc = fitz.open(PDF)
    doc.set_metadata(
        {
            "title": "EquipLens-AI 产品说明书 v1.0",
            "author": "EquipLens-AI",
            "subject": "工程车辆外观部件设计前期分析报告工具",
            "keywords": "AI, 工程机械, 工业设计, 竞品分析, 报告生成, 产品说明书",
            "creator": "EquipLens-AI",
            "producer": "EquipLens-AI / Edge + PyMuPDF",
        }
    )
    toc = [
        [1, "封面", 1],
        [1, "目录与阅读导引", 2],
        [1, "01 产品概述", 3],
        [2, "前期分析的四类重复劳动", 3],
        [2, "产品定位与边界", 4],
        [1, "02 目标用户", 5],
        [2, "用户画像与任务", 5],
        [2, "工时分布与介入点", 6],
        [1, "03 核心功能", 7],
        [2, "五步业务流程", 7],
        [2, "立项与清单确认", 8],
        [2, "素材获取与确认", 9],
        [2, "单车分析页解剖", 10],
        [2, "审校、编辑与导出", 11],
        [1, "04 AI 的角色与价值", 12],
        [2, "四个工位与人机交接", 13],
        [2, "价值口径与能力边界", 14],
        [1, "05 技术实现思路", 15],
        [2, "分层架构", 15],
        [2, "检索与证据链", 16],
        [2, "数据契约与确定性渲染", 17],
        [2, "评测与可观测", 18],
        [1, "06 应用场景示例", 19],
        [2, "沙漠牵引车案例", 19],
        [2, "更多场景与适用边界", 20],
        [1, "07 落地路径", 21],
        [2, "路线图与当前进度", 21],
        [2, "风险与质量承诺", 22],
        [1, "结语", 23],
    ]
    doc.set_toc(toc)
    tmp = PDF.with_suffix(".tmp.pdf")
    doc.save(tmp, garbage=3, deflate=True)
    doc.close()
    tmp.replace(PDF)


if __name__ == "__main__":
    render()
    decorate()
    print(f"built: {PDF} ({PDF.stat().st_size / 1e6:.2f} MB)")
