# -*- coding: utf-8 -*-
"""生成高保真用的 UI fixture（模拟数据），并自证合规。

数据来源（全部真实，不编造）：
- 名录与关联分级：data-test/evals/sample-association-list-desert.json
- 图片：data-test/ab-images/manifest.json（70 张实拍，按型号名匹配到名录目标）
- 构型名与部件族：data/part_taxonomy.json
- 风格词：data/style_vocabulary.json
- 关联散文：docs/ui-interaction-spec-v3.md §9「正本」
- 部件文案：本脚本内撰写，严格按 docs/superpowers/specs/2026-10-31-analysis-schema-design.md §2.2/§5

用法：
    PYTHONPATH=src python scripts/make_ui_fixtures.py
产物：
    data-test/ui-fixtures/s1-retrieval.json / s2-analysis.json / s3-report.json
契约：docs/ui-fixture-spec.md
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from equiplens import analysis  # noqa: E402

OUT = ROOT / "data-test" / "ui-fixtures"
IMG_ROOT = "data-test/ab-images"
TODAY = date.today().isoformat()

NOTICE = ("模拟数据：用于高保真填充与联调，数值与文案按真实链路的结构生成，"
          "不代表真实检索结果。生成脚本 scripts/make_ui_fixtures.py")

# ----------------------------------------------------------------- 真实词表
TAX_RAW = json.loads((ROOT / "data" / "part_taxonomy.json").read_text(encoding="utf-8"))
TAX = {slot: [t["name"] for t in spec["terms"]] for slot, spec in TAX_RAW["parts"].items()}
VOCAB_RAW = json.loads((ROOT / "data" / "style_vocabulary.json").read_text(encoding="utf-8"))
VOCAB = {k: v["words"] for k, v in VOCAB_RAW["clusters"].items()}
MANIFEST = json.loads((ROOT / "data-test" / "ab-images" / "manifest.json").read_text(encoding="utf-8"))
ROSTER = json.loads((ROOT / "data-test" / "evals" / "sample-association-list-desert.json")
                    .read_text(encoding="utf-8"))

SLOT_LABEL = {slot: spec["label"] for slot, spec in TAX_RAW["parts"].items()}
FAMILY_CN = {"sheet_metal": "钣金件", "frame_profile": "型材框架",
             "cast_forged": "铸锻件", "function_attachment": "功能件"}


def norm(s: str) -> str:
    return re.sub(r"[\s\-_·×xX/()（）]", "", s)


def images_for(family: str, models: list[str], limit: int = 4) -> list[str]:
    """一台车只取最匹配的一个图片目录，最多 limit 张。

    匹配优先级：型号名命中 > 车系名命中；同分取图片多的目录。
    """
    keys = [(norm(m), 2) for m in models if m] + [(norm(family), 1) if family else ("", 0)]
    keys = [k for k in keys if k[0]]
    best = None
    for m in MANIFEST:
        folder = (m.get("images") or [None])[0]
        if not folder:
            continue
        name = norm(folder.split("/")[0])
        score = max((w for k, w in keys if k in name or name in k), default=0)
        if score <= 0:
            continue
        cand = (score, len(m["images"]), m["images"])
        if best is None or cand[:2] > best[:2]:
            best = cand
    if not best:
        return []
    return [f"{IMG_ROOT}/{rel}" for rel in best[2][:limit]]


# ----------------------------------------------------------------- S2 文案
# 每台车：unit（region）+ 5 个部件定义；每个视角只决定 visible + bbox。
VEHICLES = [
    {
        "id": "v1", "name": "德龙 X3000", "brand": "陕汽", "configuration": "6×6 沙漠越野",
        "family": "德龙X3000", "models": ["德龙X3000 6x6"],
        "unit": {
            "slot": "front_face", "kind": "region",
            "members": ["grille", "bumper"],
            "gesture": "前脸竖直上收，面幅横向铺开。",
            "character_lines": ["横向饰条自格栅贯通至大灯上缘。", "格栅竖线止于保险杠上沿。",
                                "腰线自车门平直延至车尾。"],
            "proportion": "前脸接近 2:1 扁宽，驾驶室高宽比偏方（估）。",
            "cmf": "车身同色漆，格栅与保险杠下段哑黑。",
            "judgement": "横向分层压住车头体量。",
            "style_tags": [
                {"tag": "敦实", "cluster": "stability", "evidence": "横向饰条贯通至灯缘"},
                {"tag": "硬朗", "cluster": "tough", "evidence": "格栅直边与方形灯腔"},
                {"tag": "整面化", "cluster": "modern", "evidence": "保险杠与面罩同色连片"},
            ],
        },
        "parts_def": {
            "grille": {"term": "横置多层格栅", "aliases": ["多横幅格栅"], "part_family": "sheet_metal",
                       "family_reason": "三层板条连续排布",
                       "form": ["三层横向饰条贯通车头，止于大灯内缘。", "两端收进灯腔，宽度略窄于前脸。"],
                       "cmf": {"material_class": "钢板", "finish": "哑黑喷涂"},
                       "intent": "横向拉宽车头视觉，压低头部重心。"},
            "bumper": {"term": "整体式保险杠", "aliases": ["一体式前包围"], "part_family": "sheet_metal",
                       "family_reason": "单一连续件无横向分缝",
                       "form": ["单一连续件包住车头下部，无横向分缝。", "下沿内收，两端留出雾灯位。"],
                       "cmf": {"material_class": "钢板", "finish": "同色漆"},
                       "intent": "减少接缝积砂，便于冲洗。"},
            "wheel_arch": {"term": "方形轮拱", "aliases": [], "part_family": "sheet_metal",
                           "family_reason": "拱缘直边折角包住轮胎",
                           "form": ["拱缘带直边折角，外扩包住轮胎上半。", "后端与踏步护板相接，形成侧向折线。"],
                           "cmf": {"material_class": "塑料", "finish": "黑色未喷漆"},
                           "intent": "折角抬升离地感，兼挡飞石。"},
            "step": {"term": "两级固定踏板", "aliases": ["两级踏步"], "part_family": "function_attachment",
                     "family_reason": "独立踏板挂装于车门下沿",
                     "form": ["两级踏板上下错开，层间留可见空隙。", "踏面压防滑齿纹，最下层悬空。"],
                     "cmf": {"material_class": "钢板", "finish": "防滑涂层"},
                     "intent": "两级降低登车高度，悬空层避免托底。"},
            "side_guard": {"term": "型钢侧防护栏", "aliases": ["方钢护栏"], "part_family": "frame_profile",
                           "family_reason": "方管主体加竖支腿",
                           "form": ["方管横贯前后轮之间，三根竖支腿连车架。", "端部与轮拱留出装配间隙。"],
                           "cmf": {"material_class": "钢制型材", "finish": "防锈漆"},
                           "intent": "防对向车辆卷入，兼作侧向支撑。"},
        },
        "views": [
            {"image": 0, "view": "hero_lf",
             "visible": {"grille": [70, 420, 180, 550], "bumper": [20, 600, 220, 710],
                         "step": [200, 630, 310, 800]}},
            {"image": 1, "view": "side_l",
             "visible": {"wheel_arch": [560, 600, 700, 880], "step": [200, 640, 320, 820],
                         "side_guard": [310, 620, 600, 760]}},
            {"image": 2, "view": "front",
             "visible": {"grille": [80, 400, 210, 560], "bumper": [30, 590, 240, 720],
                         "wheel_arch": [600, 620, 720, 870]}},
        ],
    },
    {
        "id": "v2", "name": "豪沃 TX7", "brand": "重汽", "configuration": "6×6 牵引",
        "family": "豪沃", "models": ["豪沃 6x6"],
        "unit": {
            "slot": "front_face", "kind": "region",
            "members": ["grille", "bumper"],
            "gesture": "前脸整片网板，转折压在下沿。",
            "character_lines": ["网板外框宽出灯组外缘。", "下沿折线自保险杠上沿横贯两端。",
                                "A 柱前倾，与顶盖连成一道弧。"],
            "proportion": "网板宽高比约 1.6:1，占前脸三分之二（估）。",
            "cmf": "面罩哑黑，车身同色漆，踏步黑漆。",
            "judgement": "大面积网板压低视觉重心。",
            "style_tags": [
                {"tag": "稳重", "cluster": "stability", "evidence": "网板外框横向完整"},
                {"tag": "刚直", "cluster": "tough", "evidence": "灯腔转角接近直角"},
                {"tag": "参数化", "cluster": "modern", "evidence": "孔阵横向等距排布"},
            ],
        },
        "parts_def": {
            "grille": {"term": "冲孔网板格栅", "aliases": ["冲孔面板"], "part_family": "sheet_metal",
                       "family_reason": "整片网板一次冲孔",
                       "form": ["整片网板占满前脸中部，外框厚约一指。", "孔径沿横向等距排布。"],
                       "cmf": {"material_class": "钢板", "finish": "哑黑喷塑"},
                       "intent": "整片网板遮住散热器，减少积沙。"},
            "bumper": {"term": "分体式保险杠", "aliases": ["上下分体"], "part_family": "sheet_metal",
                       "family_reason": "上下两段可见分缝",
                       "form": ["上下两段以一道分缝隔开，上段同色。", "下段独立，两端包住雾灯。"],
                       "cmf": {"material_class": "塑料", "finish": "同色漆与哑黑"},
                       "intent": "下段可单独更换，降低维修成本。"},
            "wheel_arch": {"term": "分体式轮眉", "aliases": ["外挂轮眉"], "part_family": "sheet_metal",
                           "family_reason": "黑色包边外挂于翼子板",
                           "form": ["黑色包边外挂于翼子板，高出钣金面。", "后端沿车门下沿收回。"],
                           "cmf": {"material_class": "塑料", "finish": "黑色未喷漆"},
                           "intent": "外挂轮眉挡住飞石，减少钣金损伤。"},
            "step": {"term": "单级固定踏板", "aliases": ["一级踏板"], "part_family": "function_attachment",
                     "family_reason": "单级踏板挂装于车门下沿",
                     "form": ["单级踏板挂装于车门下沿，踏面外伸。", "下方以两根支架连车架。"],
                     "cmf": {"material_class": "钢板", "finish": "防滑涂层"},
                     "intent": "单级降低登车高度，结构简单。"},
            "side_guard": {"term": "管式侧防护栏", "aliases": ["圆管护栏"], "part_family": "frame_profile",
                           "family_reason": "圆管主体加竖支腿",
                           "form": ["圆管主体横贯前后轮之间，两端收进车架。", "三根竖支腿垂直落地。"],
                           "cmf": {"material_class": "钢管", "finish": "防锈漆"},
                           "intent": "圆管受力均匀，减少对向车卷入。"},
        },
        "views": [
            {"image": 0, "view": "hero_lf",
             "visible": {"grille": [60, 400, 200, 570], "bumper": [20, 590, 230, 720],
                         "step": [190, 640, 300, 810]}},
            {"image": 1, "view": "side_l",
             "visible": {"side_guard": [300, 630, 590, 770], "wheel_arch": [550, 600, 690, 870]}},
            {"image": 2, "view": "front",
             "visible": {"grille": [70, 390, 220, 580], "bumper": [30, 580, 250, 730]}},
        ],
    },
    {
        "id": "v3", "name": "解放 JH6", "brand": "一汽", "configuration": "6×4 牵引",
        "family": "解放", "models": ["JH6"],
        "unit": {
            "slot": "front_face", "kind": "region",
            "members": ["grille", "bumper"],
            "gesture": "前脸上收，转角落在灯腔外沿。",
            "character_lines": ["双横饰条压在格栅上三分之一。", "保险杠下沿平直，两端不外抛。",
                                "侧窗下沿与腰线平行。"],
            "proportion": "前脸接近 1.8:1，驾驶室偏高窄（估）。",
            "cmf": "车身同色漆，格栅镀铬，轮拱同色。",
            "judgement": "平直折线让前脸显干练。",
            "style_tags": [
                {"tag": "扎实", "cluster": "stability", "evidence": "保险杠下沿通长平直"},
                {"tag": "方峻", "cluster": "tough", "evidence": "灯腔与面罩成直角"},
                {"tag": "规整", "cluster": "precision", "evidence": "饰条等距平行"},
            ],
        },
        "parts_def": {
            "grille": {"term": "横置多层格栅", "aliases": ["多横幅格栅"], "part_family": "sheet_metal",
                       "family_reason": "两层横向板条",
                       "form": ["两道横向饰条压在上三分之一，镀铬包边。", "板条间距一致，止于灯腔内缘。"],
                       "cmf": {"material_class": "钢板", "finish": "镀铬与哑黑"},
                       "intent": "横向饰条拉宽前脸，镀铬提亮上沿。"},
            "bumper": {"term": "整体式保险杠", "aliases": ["一体式前包围"], "part_family": "sheet_metal",
                       "family_reason": "单一连续件",
                       "form": ["单一连续件包住车头下部，下沿通长平直。", "两端不外抛，与轮眉齐平。"],
                       "cmf": {"material_class": "钢板", "finish": "同色漆"},
                       "intent": "平直下沿保持离地间隙，便于判断接近角。"},
            "wheel_arch": {"term": "一体式同色轮拱", "aliases": ["齐平轮眉"], "part_family": "sheet_metal",
                           "family_reason": "与车身同色同曲面",
                           "form": ["轮拱与车身同色同曲面，无独立包边。", "拱缘一道浅折线收进翼子板。"],
                           "cmf": {"material_class": "钢板", "finish": "同色漆"},
                           "intent": "同色轮拱弱化轮眉，保持侧面整面。"},
            "step": {"term": "两级固定踏板", "aliases": ["两级踏步"], "part_family": "function_attachment",
                     "family_reason": "两级踏板挂装",
                     "form": ["两级踏板错开布置，层间留缝。", "踏面外缘与车门下沿齐平。"],
                     "cmf": {"material_class": "钢板", "finish": "防滑涂层"},
                     "intent": "两级降低登车高度，齐平外缘减少风阻。"},
            "side_guard": {"term": "型钢侧防护栏", "aliases": ["方钢护栏"], "part_family": "frame_profile",
                           "family_reason": "方管主体",
                           "form": ["方管横贯前后轮之间。", "支腿落在车架纵梁外侧。"],
                           "cmf": {"material_class": "钢制型材", "finish": "防锈漆"},
                           "intent": "满足法规侧防护要求。"},
        },
        "views": [
            {"image": 0, "view": "hero_lf",
             "visible": {"grille": [70, 410, 190, 560], "bumper": [20, 600, 220, 720],
                         "step": [200, 640, 310, 800]}},
            {"image": 1, "view": "side_l",
             "visible": {"wheel_arch": [560, 610, 700, 880], "step": [200, 650, 320, 820]}},
            {"image": 2, "view": "front",
             "visible": {"grille": [80, 400, 210, 570], "bumper": [30, 590, 240, 730]}},
        ],
    },
]


def build_view(veh: dict, view: dict, files: list[str]) -> dict:
    """按 §2.2 把「定义 + 视角可见性」拼成单视角 analysis（schema 结构）。"""
    parts = []
    for slot in ("grille", "bumper", "side_guard", "wheel_arch", "step"):
        d = veh["parts_def"][slot]
        bbox = view["visible"].get(slot)
        if bbox is None:
            parts.append({"slot": slot, "label": SLOT_LABEL[slot], "term": None, "aliases": [],
                          "part_family": None, "family_reason": None, "visible": "not_visible",
                          "bbox": None, "form": None, "cmf": None, "intent": None})
        else:
            parts.append({"slot": slot, "label": SLOT_LABEL[slot], "term": d["term"],
                          "aliases": d["aliases"], "part_family": d["part_family"],
                          "family_reason": d["family_reason"], "visible": "full",
                          "bbox": bbox, "form": list(d["form"]), "cmf": d["cmf"],
                          "intent": d["intent"]})
    return {"image": files[view["image"]], "view": view["view"],
            "analysis": {"unit": veh["unit"], "parts": parts, "unplaced": []}}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []

    # ---------------- S2 ----------------
    s2_vehicles = []
    for veh in VEHICLES:
        files = images_for(veh["family"], veh["models"])
        if len(files) < 3:
            errors.append(f"{veh['name']} 图片不足：{files}")
        views = [build_view(veh, v, files) for v in veh["views"]]
        for v in views:
            errs = analysis.validate_analysis(v["analysis"], [], VOCAB, TAX)
            if errs:
                errors.append(f"{veh['name']} {v['view']}: {errs}")
            for p in v["analysis"]["parts"]:
                if p.get("term_off_taxonomy"):
                    errors.append(f"{veh['name']} {v['view']} {p['slot']}: 构型名不在词表 "
                                  f"{p['term_off_taxonomy']}")
        s2_vehicles.append({
            "id": veh["id"], "name": veh["name"], "brand": veh["brand"],
            "configuration": veh["configuration"],
            "style_tags": veh["unit"]["style_tags"],
            "views": [{"id": f"{veh['id']}-m{i+1}", "view": v["view"], "image": v["image"],
                       "analysis": v["analysis"]} for i, v in enumerate(views)],
        })

    s2 = {"fixture": "s2-analysis", "version": "1.0", "generated_at": TODAY,
          "notice": NOTICE,
          "contract": "docs/ui-fixture-spec.md",
          "schema_ref": "docs/superpowers/specs/2026-10-31-analysis-schema-design.md",
          "slots": ["grille", "bumper", "side_guard", "wheel_arch", "step"],
          "slot_labels": {k: SLOT_LABEL[k] for k in
                          ("grille", "bumper", "side_guard", "wheel_arch", "step")},
          "vehicles": s2_vehicles}
    (OUT / "s2-analysis.json").write_text(json.dumps(s2, ensure_ascii=False, indent=1), encoding="utf-8")

    # ---------------- S1 ----------------
    by_id = {t["id"]: t for t in ROSTER["targets"]}
    picks = [(i, "recommended") for i in ("t01", "t02", "t03", "t04", "t07", "t08")]
    picks += [(i, "backup") for i in ("t09", "t12")]
    cards = []
    for tid, role in picks:
        t = by_id[tid]
        files = images_for(t["family"], t.get("models", []))
        cards.append({
            "id": tid, "role": role, "model": t["family"],
            "configuration": (t.get("models") or [""])[0] or t.get("category", ""),
            "relation": t["relation"], "tier": t.get("tier", 1),
            "confidence": t.get("confidence"),
            "selected": role == "recommended",
            "reason": t.get("reason", ""),
            "evidence": [{"title": e.get("title"), "url": e.get("url"), "grade": e.get("grade")}
                         for e in (t.get("evidence") or [])[:2]],
            "images": files, "image_count": len(files),
            "image_state": "ok" if files else "missing",
        })

    prose = ("沙漠牵引车以 6×6 为基型，前脸、格栅与保险杠属平台通用造型件，不随工况变化。"
             "沙漠工况的特化落在防护栏、进气防护、底盘离地与踏步防滑上，这些部件即使未被点名，"
             "亦构成本类车型的设计特征。前脸与驾驶室轮廓承自基型平台，同平台车型可验证其家族关系。"
             "踏步、爬梯与把手为功能件，构型跨车型可比，证据强度弱，仅作备选。")
    s1 = {"fixture": "s1-retrieval", "version": "1.0", "generated_at": TODAY,
          "notice": NOTICE, "contract": "docs/ui-fixture-spec.md",
          "prose_ref": "docs/ui-interaction-spec-v3.md §9",
          "request": {"raw": "沙漠牵引车，看踏步和防护栏，六台", "category": "沙漠牵引车",
                      "parts": ROSTER["parts_requested"], "want": 6},
          "analysis": {"axes": ["exact", "environment", "platform", "cross_vehicle"],
                       "prose": prose},
          "budget": {"recommended": 6, "backup": 2, "requested": ROSTER.get("requested", 12)},
          "cards": cards}
    (OUT / "s1-retrieval.json").write_text(json.dumps(s1, ensure_ascii=False, indent=1), encoding="utf-8")

    # ---------------- S3 ----------------
    s2_by_name = {v["name"]: v for v in s2_vehicles}
    roster_names = [("德龙 X3000", "陕汽 · 6×6 牵引车"), ("豪沃 TX7", "重汽 · 6×6 牵引车"),
                    ("解放 JH6", "一汽 · 6×4 牵引车"), ("德龙 6X6 沙漠版", "陕汽 · 6×6 环境特化"),
                    ("沙漠运输车", "重汽 · 6×6 环境特化"), ("德龙 M3000", "陕汽 · 4×2 基型平台"),
                    ("三一 STC800", "三一 · 跨车型"), ("天龙 KL", "东风 · 6×4 牵引车")]
    pages = [{"id": "p01", "type": "cover", "title": "沙漠牵引车",
              "subtitle": "竞品设计分析 · 2026 年 11 月", "status": "full", "blocks": []},
             {"id": "p02", "type": "method", "title": "方法与来源",
              "subtitle": "四层关联 · 八台参照", "status": "full", "blocks": []}]
    for i, (name, sub) in enumerate(roster_names):
        v = s2_by_name.get(name)
        blocks = [{"id": "title", "kind": "text", "text": name},
                  {"id": "subtitle", "kind": "text", "text": sub}]
        if v:
            blocks += [
                {"id": "style_words", "kind": "tags",
                 "items": [{"term": t["tag"], "evidence": t["evidence"]} for t in v["style_tags"]]},
                {"id": "hero", "kind": "image", "src": v["views"][0]["image"]},
                {"id": "parts", "kind": "grid",
                 "items": [{"term": p["term"], "cmf": f'{p["cmf"]["material_class"]} · {p["cmf"]["finish"]}'}
                           for p in v["views"][0]["analysis"]["parts"] if p["term"]][:4]},
                {"id": "note", "kind": "text", "text": v["views"][0]["analysis"]["unit"]["judgement"]},
            ]
            status = "full"
        else:
            blocks += [{"id": "placeholder", "kind": "note", "text": "该车型尚未完成部件分析"}]
            status = "thin"
        pages.append({"id": f"p{i+3:02d}", "type": "car", "title": name, "subtitle": sub,
                      "vehicle": name, "status": status, "blocks": blocks})
    pages += [{"id": "p11", "type": "overview", "title": "竞品总览",
               "subtitle": "八台 · 前脸与部件索引", "status": "full", "blocks": []},
              {"id": "p12", "type": "back", "title": "EquipLens",
               "subtitle": "2026 · 竞品设计分析", "status": "full", "blocks": []}]
    s3 = {"fixture": "s3-report", "version": "1.0", "generated_at": TODAY,
          "notice": NOTICE, "contract": "docs/ui-fixture-spec.md",
          "meta": {"category": "沙漠牵引车", "aspect": "16:9", "total": len(pages),
                   "title": "沙漠牵引车 · 竞品设计分析"},
          "pages": pages}
    (OUT / "s3-report.json").write_text(json.dumps(s3, ensure_ascii=False, indent=1), encoding="utf-8")

    if errors:
        print("[FAIL] 校验未通过：")
        for e in errors:
            print("  -", e)
        return 1
    print(f"[ok] s1 cards={len(cards)}  s2 vehicles={len(s2_vehicles)} "
          f"views={sum(len(v['views']) for v in s2_vehicles)}  s3 pages={len(pages)}")
    print("[ok] 全部视角通过 validate_analysis，构型名均在 part_taxonomy")
    return 0


if __name__ == "__main__":
    sys.exit(main())
