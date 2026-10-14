"""M1 导入与判重流水线（渠道共用底层）。

两条入口:
  - ingest_directory: 批量目录导入（人工/甲方包）→ unbound 待归号池;
  - ingest_file_bytes: 单文件入库（渠道检索结果）→ 可携带车型 provisional 绑定与视角/部位标签。
判重策略（规范 D5 同图多源）:
  - sha256 精确命中 → 不新建素材, 新来源并入既有素材; 同来源重复导入整体跳过;
  - dHash 感知哈希命中(距离 <= 阈值) → 仍新建素材但标记"疑似重复", 不自动合并(保守, 防误杀);
  - 均未命中 → 新建素材落盘。
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


def _insert_source(conn, asset_id: str, platform: str, license: str, note: str,
                   is_primary: int, batch_id: str | None) -> None:
    conn.execute(
        "INSERT INTO sources (id, asset_id, url, platform, retrieved_at, license,"
        " is_primary, note, batch_id) VALUES (?,?,?,?,?,?,?,?,?)",
        (str(uuid.uuid4()), asset_id, None, platform, _now(), license, is_primary, note, batch_id))


def ingest_file_bytes(conn, data_dir: Path, *, name: str, data: bytes,
                      platform: str, license: str, batch_id: str,
                      vehicle_id: str | None = None,
                      binding_evidence: str = "none",
                      view_angle: str = "untagged",
                      part_id: str | None = None,
                      asset_nature: str = "untagged",
                      evidence_note: str | None = None) -> dict:
    """单文件入库。任何解码失败抛 ValueError（调用方按"跳过"处理）。

    vehicle_id 给定时按 binding_evidence 挂载: human→confirmed, 其余(T2 共现等)→provisional。
    """
    try:
        img = Image.open(BytesIO(data))
        img.load()
        width, height = img.size
        fmt = (img.format or Path(name).suffix.lstrip(".")).lower()
    except (UnidentifiedImageError, OSError, ValueError) as e:
        raise ValueError(f"无法解码为图片: {e}") from e

    sha = hashlib.sha256(data).hexdigest()
    ext = FORMAT_EXT.get(fmt, fmt)
    note = evidence_note or name

    hit = db.find_asset_by_hash(conn, sha)
    if hit is not None:
        dup_src = conn.execute(
            "SELECT 1 FROM sources WHERE asset_id = ? AND platform = ? AND note = ?",
            (hit["id"], platform, note)).fetchone()
        if dup_src is None:
            _insert_source(conn, hit["id"], platform, license, note, 0, batch_id)
            conn.commit()
            return {"status": "merged", "asset_id": hit["id"]}
        return {"status": "source_exists", "asset_id": hit["id"]}

    new_hash = dhash(img)
    near_id, near_dist = None, None
    for r in conn.execute("SELECT id, phash FROM assets WHERE phash IS NOT NULL"):
        dist = hamming(new_hash, r["phash"])
        if near_dist is None or dist < near_dist:
            near_id, near_dist = r["id"], dist
    is_near = near_dist is not None and near_dist <= NEAR_DUP_MAX_BITS

    asset_id = str(uuid.uuid4())
    dest = vehicle_id or POOL_DIR
    rel = save_original(data_dir, dest, asset_id, ext, data)
    if vehicle_id:
        binding_status = "confirmed" if binding_evidence == "human" else "provisional"
    else:
        binding_status = "unbound"
        binding_evidence = "none"
        vehicle_id = None
    conn.execute(
        "INSERT INTO assets (id, vehicle_id, binding_status, binding_evidence, kind,"
        " parent_asset_id, crop_bbox, file_path, view_angle, asset_nature, part_id,"
        " width, height, quality_flags, hash_sha256, phash, confirm_status, notes,"
        " created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (asset_id, vehicle_id, binding_status, binding_evidence, "source_image",
         None, None, rel, view_angle, asset_nature, part_id, width, height, "[]",
         sha, new_hash, "machine_tagged",
         f"疑似重复:{near_id} 距离={near_dist}" if is_near else None,
         _now(), _now()))
    _insert_source(conn, asset_id, platform, license, note, 1, batch_id)
    conn.commit()
    return {"status": "near_duplicate" if is_near else "imported", "asset_id": asset_id}


def ingest_directory(data_dir: Path, source_dir: Path, *, platform: str = "本地导入",
                     license: str = "web_third_party", conn=None,
                     batch_id: str | None = None) -> dict:
    """批量目录导入。返回导入报告 dict。"""
    data_dir = Path(data_dir)
    source_dir = Path(source_dir)
    own_conn = conn is None
    if own_conn:
        data_dir.mkdir(parents=True, exist_ok=True)  # 首次使用: 数据目录尚不存在
        conn = db.connect(data_dir / "equiplens.db")
        db.init_db(conn)
    batch_id = batch_id or str(uuid.uuid4())

    report = {"source_dir": str(source_dir), "platform": platform, "license": license,
              "batch_id": batch_id, "total": 0, "imported": [], "merged": [],
              "source_exists": [], "near_duplicate": [], "skipped": []}

    for path in sorted(p for p in source_dir.rglob("*") if p.is_file()):
        report["total"] += 1
        try:
            result = ingest_file_bytes(
                conn, data_dir, name=path.name, data=path.read_bytes(),
                platform=platform, license=license, batch_id=batch_id)
        except ValueError as e:
            report["skipped"].append({"file": str(path), "reason": str(e)})
            continue
        entry = {"file": str(path), "asset_id": result["asset_id"]}
        report[result["status"]].append(entry)

    if own_conn:
        conn.close()
    return report


def summarize(report: dict) -> str:
    return (f"共 {report['total']} 个文件: 新导入 {len(report['imported'])}, "
            f"并入既有素材 {len(report['merged'])}, 同来源重复 {len(report['source_exists'])}, "
            f"疑似重复 {len(report['near_duplicate'])}, 跳过 {len(report['skipped'])}")


def save_original(data_dir: Path, vehicle_id: str, asset_id: str, ext: str, data: bytes) -> str:
    """写入原图；目标已存在即拒绝（原图不可变）。返回相对 data_dir 的路径。"""
    rel = f"assets/{vehicle_id}/originals/{asset_id}.{ext}"
    dest = Path(data_dir) / rel
    if dest.exists():
        raise FileExistsError(f"原图不可覆盖: {rel}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return rel


def save_crop(data_dir: Path, vehicle_id: str, asset_id: str, ext: str, data: bytes) -> str:
    rel = f"assets/{vehicle_id}/crops/{asset_id}.{ext}"
    dest = Path(data_dir) / rel
    if dest.exists():
        raise FileExistsError(f"文件已存在: {rel}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return rel
