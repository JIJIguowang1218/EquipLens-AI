"""M1 导入与判重流水线。

对一批本地图片执行: 解码校验 → 双哈希判重 → 四路分流 → 落盘入库 → 报告。
判重策略（规范 D5 同图多源）:
  - sha256 文件哈希精确命中 → 不新建素材, 新来源并入既有素材; 同来源重复导入整体跳过;
  - dHash 感知哈希命中(汉明距离 <= 阈值) → 仍新建素材但标记"疑似重复", 不自动合并(保守, 防误杀);
  - 均未命中 → 新建素材, 存入 _pool 暂存区, 待 M4 打标 / M2 对号。
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime
from io import BytesIO
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from . import db

NEAR_DUP_MAX_BITS = 8          # 64 位 dHash 允许的最大汉明距离
POOL_DIR = "_pool"             # 未对号素材暂存区（规范 §5, v0.1.1）
FORMAT_EXT = {"jpeg": "jpg", "tiff": "tif"}


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00")


def dhash(image: Image.Image) -> str:
    """差异哈希：缩放到 9x8 灰度，逐行比较相邻像素明暗 → 64 位 → 16 位十六进制。

    同图经压缩/缩放后文件字节会变（sha256 失效），但明暗结构不变（dHash 稳定）。
    """
    small = image.convert("L").resize((9, 8), Image.LANCZOS)
    pixels = list(small.getdata())
    bits = 0
    for row in range(8):
        for col in range(8):
            bits = (bits << 1) | (1 if pixels[row * 9 + col] > pixels[row * 9 + col + 1] else 0)
    return f"{bits:016x}"


def hamming(hex_a: str, hex_b: str) -> int:
    """两个哈希的汉明距离（不同的比特数）。0 = 完全一致。"""
    return bin(int(hex_a, 16) ^ int(hex_b, 16)).count("1")


def ingest_directory(data_dir: Path, source_dir: Path, *, platform: str = "本地导入",
                     license: str = "web_third_party", conn=None) -> dict:
    """导入 source_dir 下全部可解码图片。返回导入报告 dict。

    license: 本批素材的授权档（调用方声明，如甲方包=client_provided、网络收集=web_third_party）。
    """
    data_dir = Path(data_dir)
    source_dir = Path(source_dir)
    own_conn = conn is None
    if own_conn:
        data_dir.mkdir(parents=True, exist_ok=True)  # 首次使用: 数据目录尚不存在
        conn = db.connect(data_dir / "equiplens.db")
        db.init_db(conn)

    # 既有感知哈希一次载入，避免每张图全表扫描
    phashes: dict[str, str] = {r["id"]: r["phash"] for r in
                               conn.execute("SELECT id, phash FROM assets WHERE phash IS NOT NULL")}

    report = {"source_dir": str(source_dir), "platform": platform, "license": license,
              "total": 0, "imported": [], "merged": [], "source_exists": [],
              "near_duplicate": [], "skipped": []}

    for path in sorted(p for p in source_dir.rglob("*") if p.is_file()):
        report["total"] += 1
        try:
            data = path.read_bytes()
            img = Image.open(BytesIO(data))
            img.load()  # 强制解码，截断/损坏文件在此暴露
            width, height = img.size
            fmt = (img.format or path.suffix.lstrip(".")).lower()
        except Exception as e:  # noqa: BLE001  # 任何解码失败都跳过, 不中断整批
            report["skipped"].append({"file": str(path), "reason": f"无法解码为图片: {e}"})
            continue

        sha = hashlib.sha256(data).hexdigest()
        ext = FORMAT_EXT.get(fmt, fmt)
        note = path.name  # 来源备注记原始文件名，来源去重以此为键

        hit = db.find_asset_by_hash(conn, sha)
        if hit is not None:
            dup_src = conn.execute(
                "SELECT 1 FROM sources WHERE asset_id = ? AND platform = ? AND note = ?",
                (hit["id"], platform, note)).fetchone()
            if dup_src is None:
                conn.execute(
                    "INSERT INTO sources (id, asset_id, url, platform, retrieved_at, license,"
                    " is_primary, note) VALUES (?,?,?,?,?,?,?,?)",
                    (str(uuid.uuid4()), hit["id"], None, platform, _now(), license, 0, note))
                conn.commit()
                report["merged"].append({"file": str(path), "asset_id": hit["id"]})
            else:
                report["source_exists"].append({"file": str(path), "asset_id": hit["id"]})
            continue

        # 近似重复检查：与全部既有感知哈希比距离，取最近者
        new_hash = dhash(img)
        near_id, near_dist = None, None
        for aid, ph in phashes.items():
            dist = hamming(new_hash, ph)
            if near_dist is None or dist < near_dist:
                near_id, near_dist = aid, dist
        is_near = near_dist is not None and near_dist <= NEAR_DUP_MAX_BITS

        asset_id = str(uuid.uuid4())
        rel = db.save_original(data_dir, POOL_DIR, asset_id, ext, data)
        conn.execute(
            "INSERT INTO assets (id, vehicle_id, binding_status, binding_evidence, kind,"
            " parent_asset_id, crop_bbox, file_path, view_angle, asset_nature, part_id,"
            " width, height, quality_flags, hash_sha256, phash, confirm_status, notes,"
            " created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (asset_id, None, "unbound", "none", "source_image", None, None, rel,
             "untagged", "untagged", None, width, height, "[]", sha, new_hash,
             "machine_tagged",
             f"疑似重复:{near_id} 距离={near_dist}" if is_near else None,
             _now(), _now()))
        conn.execute(
            "INSERT INTO sources (id, asset_id, url, platform, retrieved_at, license,"
            " is_primary, note) VALUES (?,?,?,?,?,?,?,?)",
            (str(uuid.uuid4()), asset_id, None, platform, _now(), license, 1, note))
        phashes[asset_id] = new_hash
        conn.commit()
        entry = {"file": str(path), "asset_id": asset_id}
        (report["near_duplicate"] if is_near else report["imported"]).append(entry)

    if own_conn:
        conn.close()
    return report


def summarize(report: dict) -> str:
    return (f"共 {report['total']} 个文件: 新导入 {len(report['imported'])}, "
            f"并入既有素材 {len(report['merged'])}, 同来源重复 {len(report['source_exists'])}, "
            f"疑似重复 {len(report['near_duplicate'])}, 跳过 {len(report['skipped'])}")
