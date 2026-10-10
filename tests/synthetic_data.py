"""合成黄金样例（第一档测试用，全合成、零真实素材、确定性可复现）。

三台车覆盖完备度 L2 / L1 / L0；一台孤立特写进待归号池；描述档案覆盖三轴全组合。
规范: docs/data-model-spec.md
"""

import hashlib
import struct
import zlib

TS = "2026-10-10T09:00:00+08:00"


def vid(i: int) -> str:
    return f"{i:08x}-0000-4000-8000-{i:012x}"


def make_png(rgb: tuple) -> bytes:
    """生成合法 1x1 PNG，每张素材用不同颜色 → 文件哈希唯一。"""
    def chunk(typ: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + typ + data
                + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF))
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    raw = b"\x00" + bytes(rgb)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


V1, V2, V3 = vid(1), vid(2), vid(3)
A1, A2, A3, A4, A5, A6, A7, A8 = (vid(i) for i in range(11, 19))
B1 = vid(21)
S1, S2, S3, S4, S5, S6 = (vid(i) for i in range(31, 37))
F1, F2, F3 = vid(41), vid(42), vid(43)
D1, D2, D3, D4, D5 = (vid(i) for i in range(51, 56))
L1, L2 = vid(61), vid(62)

PARTS = [  # 附录 B 词表 v0
    ("bumper", "保险杠与防护栏"), ("headlamp", "大灯与灯罩防护"),
    ("grille", "进气格栅（含冷却模块进风口）"), ("step", "登车踏步"),
    ("fender", "翼子板与轮拱"), ("mirror", "后视镜总成"),
    ("sunvisor", "外部遮阳板"), ("skirt", "下护板"),
    ("fluid_window", "可视液位窗"), ("width_pole", "示宽杆"),
    ("brand_zone", "品牌标识区"), ("paint", "涂装与分色"),
    ("other", "其他（待补充）"),
]

# 每张图的文件字节（唯一颜色 → 唯一哈希）
FILE_BYTES = {
    A1: make_png((200, 30, 30)), A2: make_png((30, 200, 30)), A3: make_png((30, 30, 200)),
    A4: make_png((200, 200, 30)), A5: make_png((30, 200, 200)), A6: make_png((200, 30, 200)),
    A7: make_png((100, 100, 100)), A8: make_png((10, 10, 10)), B1: make_png((220, 120, 40)),
}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _asset(aid, vehicle, status, evidence, kind, parent, bbox, path, angle, nature,
           part=None, wh=None, flags=None, confirm="confirmed"):
    return {
        "id": aid, "vehicle_id": vehicle, "binding_status": status, "binding_evidence": evidence,
        "kind": kind, "parent_asset_id": parent, "crop_bbox": bbox, "file_path": path,
        "view_angle": angle, "asset_nature": nature, "part_id": part,
        "width": wh[0] if wh else None, "height": wh[1] if wh else None,
        "quality_flags": flags or [], "hash_sha256": sha(FILE_BYTES[aid]),
        "phash": None, "confirm_status": confirm, "notes": None,
        "created_at": TS, "updated_at": TS,
    }


def build_bundle() -> dict:
    assets = [
        _asset(A1, V1, "confirmed", "human", "source_image", None, None,
               f"assets/{V1}/originals/{A1}.png", "hero_lf", "official_photo", wh=(1920, 1080)),
        _asset(A2, V1, "confirmed", "human", "source_image", None, None,
               f"assets/{V1}/originals/{A2}.png", "side_l", "real_photo", wh=(1600, 900),
               flags=["cluttered"]),
        _asset(A3, V1, "confirmed", "human", "source_image", None, None,
               f"assets/{V1}/originals/{A3}.png", "front", "official_photo", wh=(1200, 800)),
        _asset(A4, V1, "confirmed", "self_derived", "crop", A1,
               {"x": 100, "y": 80, "w": 300, "h": 200},
               f"assets/{V1}/crops/{A4}.png", "detail", "official_photo", part="grille",
               wh=(300, 200)),
        _asset(A5, V1, "confirmed", "self_derived", "crop", A1,
               {"x": 20, "y": 60, "w": 120, "h": 90},
               f"assets/{V1}/crops/{A5}.png", "detail", "official_photo", part="headlamp",
               wh=(120, 90)),
        _asset(A6, V1, "confirmed", "self_derived", "crop", A2,
               {"x": 240, "y": 300, "w": 80, "h": 120},
               f"assets/{V1}/crops/{A6}.png", "detail", "real_photo", part="step",
               wh=(80, 120)),
        # 孤立外源特写 → 待归号池（D2：不拒收，延迟归号）
        _asset(A7, None, "unbound", "none", "source_image", None, None,
               f"assets/pool/{A7}.png", "detail", "real_photo", wh=(800, 600),
               flags=["watermarked", "blur"], confirm="machine_tagged"),
        # 已对号但标签未确认 → 槽位"有·待确认"
        _asset(A8, V1, "confirmed", "self_derived", "crop", A1,
               {"x": 380, "y": 50, "w": 60, "h": 100},
               f"assets/{V1}/crops/{A8}.png", "detail", "official_photo", part="mirror",
               wh=(60, 100), confirm="machine_tagged"),
        _asset(B1, V2, "confirmed", "human", "source_image", None, None,
               f"assets/{V2}/originals/{B1}.png", "hero_lf", "official_photo", wh=(2000, 1200)),
    ]
    bundle = {
        "meta": {"format_version": "0.1", "exported_at": TS},
        "vocab": [{"id": p, "type": "part", "term": t, "status": "active", "note": None}
                  for p, t in PARTS],
        "vehicles": [
            {"id": V1, "brand": "样例品牌", "model_name": "样例T1", "category": "牵引车",
             "generation": "2024款", "list_status": "locked", "hero_asset_id": A1,
             "project_id": None, "created_at": TS},
            {"id": V2, "brand": "样例品牌", "model_name": "样例R1", "category": "装载机",
             "generation": None, "list_status": "candidate", "hero_asset_id": B1,
             "project_id": None, "created_at": TS},
            {"id": V3, "brand": "样例品牌", "model_name": "样例N0", "category": "矿卡",
             "generation": None, "list_status": "candidate", "hero_asset_id": None,
             "project_id": None, "created_at": TS},
        ],
        "assets": assets,
        "sources": [
            {"id": S1, "asset_id": A1, "url": "https://example.com/press/t1-hero.jpg",
             "platform": "官网新闻稿", "retrieved_at": TS, "license": "web_official",
             "is_primary": 1, "note": None},
            {"id": S2, "asset_id": A1, "url": None, "platform": "甲方邮件",
             "retrieved_at": TS, "license": "client_provided", "is_primary": 0,
             "note": "客户 2026-09 项目包"},
            {"id": S3, "asset_id": A2, "url": "https://forum.example.net/t/987",
             "platform": "用户论坛", "retrieved_at": TS, "license": "web_third_party",
             "is_primary": 1, "note": "授权待确认"},
            {"id": S4, "asset_id": A3, "url": "https://example.com/products/t1/front.jpg",
             "platform": "官网产品页", "retrieved_at": TS, "license": "web_official",
             "is_primary": 1, "note": None},
            {"id": S5, "asset_id": A7, "url": "https://dealer.example.org/p/x.jpg",
             "platform": "经销商页", "retrieved_at": TS, "license": "web_third_party",
             "is_primary": 1, "note": "孤立特写, 同源页面无型号标注"},
            {"id": S6, "asset_id": B1, "url": "https://example.com/press/r1.jpg",
             "platform": "官网新闻稿", "retrieved_at": TS, "license": "web_official",
             "is_primary": 1, "note": None},
        ],
        "facts": [
            {"id": F1, "vehicle_id": V1, "field_key": "curb_weight", "value": "8800",
             "unit": "kg", "source_id": S1, "confirm_status": "confirmed",
             "created_at": TS, "updated_at": TS},
            {"id": F2, "vehicle_id": V1, "field_key": "engine_power", "value": "460",
             "unit": "kW", "source_id": S1, "confirm_status": "confirmed",
             "created_at": TS, "updated_at": TS},
            {"id": F3, "vehicle_id": V1, "field_key": "cab_type", "value": "平顶驾驶室",
             "unit": None, "source_id": None, "confirm_status": "machine_tagged",
             "created_at": TS, "updated_at": TS},
        ],
        "descriptions": [
            {"id": D1, "vehicle_id": V1, "node_type": "whole", "part_id": None,
             "axis_type": "structure", "scope": "model",
             "body": "6×4 驱动，平顶驾驶室，总高 3.9 m",
             "evidence_asset_ids": [A1], "source_ids": [], "confirm_status": "confirmed",
             "version": 1, "created_at": TS, "updated_at": TS},
            {"id": D2, "vehicle_id": V1, "node_type": "whole", "part_id": None,
             "axis_type": "design_feature", "scope": "model",
             "body": "腰线自大灯上扬至货箱，前低后高",
             "evidence_asset_ids": [A2], "source_ids": [], "confirm_status": "confirmed",
             "version": 1, "created_at": TS, "updated_at": TS},
            {"id": D3, "vehicle_id": V1, "node_type": "whole", "part_id": None,
             "axis_type": "design_feature", "scope": "family",
             "body": "V 型家族前脸，镀铬饰条贯穿灯组",
             "evidence_asset_ids": [A1, A3], "source_ids": [], "confirm_status": "confirmed",
             "version": 1, "created_at": TS, "updated_at": TS},
            {"id": D4, "vehicle_id": V1, "node_type": "part", "part_id": "grille",
             "axis_type": "structure", "scope": "model",
             "body": "双层格栅，下层带可开检修盖",
             "evidence_asset_ids": [A4], "source_ids": [], "confirm_status": "confirmed",
             "version": 1, "created_at": TS, "updated_at": TS},
            {"id": D5, "vehicle_id": V1, "node_type": "part", "part_id": "grille",
             "axis_type": "intent", "scope": "family",
             "body": "黑色格栅压低视觉重心，传达可靠性",
             "evidence_asset_ids": [A4], "source_ids": [], "confirm_status": "confirmed",
             "version": 1, "created_at": TS, "updated_at": TS},
        ],
        "confirm_log": [
            {"id": L1, "op_id": "op-20261010-001", "object_type": "asset", "object_id": A1,
             "field": "view_angle", "machine_value": "\"scene\"", "confirmed_value": "\"hero_lf\"",
             "method": "batch", "confirmed_at": TS, "confirmed_by": "user"},
            {"id": L2, "op_id": "op-20261010-002", "object_type": "description", "object_id": D5,
             "field": "body", "machine_value": "\"黑色格栅显得稳重\"",
             "confirmed_value": "\"黑色格栅压低视觉重心，传达可靠性\"",
             "method": "single", "confirmed_at": TS, "confirmed_by": "user"},
        ],
    }
    return bundle


def write_asset_files(data_dir):
    """按目录约定落盘全部素材文件，返回 {asset_id: 相对路径}。"""
    from equiplens import db as edb
    from pathlib import Path
    data_dir = Path(data_dir)
    paths = {}
    for aid, data in FILE_BYTES.items():
        if aid == B1:
            rel = edb.save_original(data_dir, V2, aid, "png", data)
        elif aid == A7:
            dest = data_dir / f"assets/pool/{aid}.png"  # 待归号池无车属
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            rel = Path(f"assets/pool/{aid}.png")
        elif FILE_BYTES[aid] and aid in (A4, A5, A6, A8):
            rel = edb.save_crop(data_dir, V1, aid, "png", data)
        else:
            rel = edb.save_original(data_dir, V1, aid, "png", data)
        paths[aid] = rel
    return paths
