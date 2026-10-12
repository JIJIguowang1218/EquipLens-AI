"""M1 导入与判重测试（Pillow 现场合成平滑噪声图，零真实素材、零模型调用）。

测试图像设计说明: 用低频平滑噪声(16x16 随机种子图放大到 128x128)——
不同种子图的 dHash 汉明距离约 32(远超阈值, 不误报); 同图缩小后距离约 0(命中近似重复)。
这正是真实场景: 同一张图的原片与缩略图, 文件哈希不同但感知哈希几乎一致。

覆盖: dHash/汉明距离单元、混合批次导入、重复导入、同内容多文件、
     近似重复(同图不同分辨率)不误杀、untagged 状态、来源透传、报告自洽。
运行: python tests/test_ingest.py
"""

import io
import json
import random
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from PIL import Image  # noqa: E402

from equiplens import db as edb  # noqa: E402
from equiplens import ingest  # noqa: E402

results = []


def check(name, fn):
    try:
        fn()
        results.append((name, "PASS", ""))
    except Exception as e:  # noqa: BLE001
        import traceback
        results.append((name, "FAIL", f"{type(e).__name__}: {e}"))
        traceback.print_exc()


# ---------------------------------------------------------------- 图像工厂

def noise_bytes(seed: int, size: int = 128) -> bytes:
    """低频平滑噪声图: 16x16 种子噪声双线性放大 → 结构稳定、对缩放不敏感。"""
    rng = random.Random(seed)
    small = Image.frombytes("L", (16, 16), bytes(rng.randrange(256) for _ in range(256)))
    img = small.resize((size, size), Image.BILINEAR)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def make_batch(src_dir: Path) -> list[Path]:
    """8 张互不相同图(种子 1–8, 其一在子目录) + 1 个损坏 PNG + 1 个文本文件。"""
    src_dir.mkdir(parents=True, exist_ok=True)
    files = []
    for i in range(8):
        base = src_dir if i < 7 else src_dir / "sub"
        base.mkdir(parents=True, exist_ok=True)
        f = base / f"img_{i}.png"
        f.write_bytes(noise_bytes(i + 1))
        files.append(f)
    bad = src_dir / "corrupt.png"
    bad.write_bytes(b"\x89PNG\r\n\x1a\n" + b"garbage-not-a-real-image")
    files.append(bad)
    txt = src_dir / "notes.txt"
    txt.write_text("不是图片", encoding="utf-8")
    files.append(txt)
    return files


# ---------------------------------------------------------------- 用例

def t01_dhash_unit():
    a = ingest.dhash(Image.open(io.BytesIO(noise_bytes(1))))
    b = ingest.dhash(Image.open(io.BytesIO(noise_bytes(2))))
    assert ingest.hamming(a, a) == 0
    assert len(a) == 16
    assert ingest.hamming("0000", "ffff") == 16, "已知值: 16 位全异或 = 64 比特? 不, 此处 16 位十六进制 = 64 比特中的 16 位样例"
    assert ingest.hamming(a, b) > ingest.NEAR_DUP_MAX_BITS, f"不同种子距离应超阈值, 实际 {ingest.hamming(a, b)}"


def t02_mixed_batch():
    global TD, SRC, CONN
    TD = Path(tempfile.mkdtemp(prefix="eq-m1-"))
    SRC = TD / "batch1"
    make_batch(SRC)
    (TD / "data").mkdir(parents=True, exist_ok=True)
    CONN = edb.connect(TD / "data" / "equiplens.db")
    edb.init_db(CONN)
    R = ingest.ingest_directory(TD / "data", SRC, platform="测试甲方包",
                                license="client_provided", conn=CONN)
    assert R["total"] == 10, f"应扫描 10 个文件, 实际 {R['total']}"
    assert len(R["imported"]) == 8, f"应导入 8 张, 实际 {len(R['imported'])}"
    assert len(R["skipped"]) == 2, "损坏文件+文本文件应跳过 2 个"
    assert len(R["near_duplicate"]) == 0, "不同种子图不得误报疑似重复"
    rows = CONN.execute("SELECT * FROM assets ORDER BY id").fetchall()
    assert len(rows) == 8
    for r in rows:
        assert r["binding_status"] == "unbound" and r["binding_evidence"] == "none"
        assert r["view_angle"] == "untagged" and r["asset_nature"] == "untagged"
        assert r["confirm_status"] == "machine_tagged" and r["kind"] == "source_image"
        assert len(r["phash"]) == 16
        # v0.1.1: 未对号素材落盘 _pool
        assert r["file_path"].startswith("assets/_pool/originals/")
        assert (TD / "data" / r["file_path"]).exists(), f"文件未落盘: {r['file_path']}"


def t03_reimport():
    R = ingest.ingest_directory(TD / "data", SRC, platform="测试甲方包",
                                license="client_provided", conn=CONN)
    assert len(R["imported"]) == 0 and len(R["merged"]) == 0
    assert len(R["source_exists"]) == 8, "重复导入应全部命中同来源"
    n_assets = CONN.execute("SELECT count(*) c FROM assets").fetchone()["c"]
    n_sources = CONN.execute("SELECT count(*) c FROM sources").fetchone()["c"]
    assert n_assets == 8 and n_sources == 8, "重复导入不得新增素材或来源"


def t04_same_content_two_files():
    sub = TD / "batch2"
    sub.mkdir(parents=True, exist_ok=True)
    data = noise_bytes(101)
    (sub / "copy_a.png").write_bytes(data)
    (sub / "copy_b.png").write_bytes(data)  # 同内容不同文件名
    R = ingest.ingest_directory(TD / "data", sub, platform="网络收集", conn=CONN)
    assert len(R["imported"]) == 1 and len(R["merged"]) == 1, "第二个文件应并入同一素材"
    # 合并的文件不建新素材: 两条来源指向同一素材
    dup = CONN.execute(
        "SELECT count(DISTINCT asset_id) c FROM sources WHERE note IN ('copy_a.png','copy_b.png')").fetchone()
    srcs = CONN.execute(
        "SELECT count(*) c FROM sources WHERE note IN ('copy_a.png','copy_b.png')").fetchone()
    assert dup["c"] == 1, "同内容不得新建两个素材"
    assert srcs["c"] == 2, f"同内容不同文件名应记 2 条来源, 实际 {srcs['c']}"


def t05_near_duplicate():
    """同图不同分辨率: 文件哈希必不同, 感知哈希应命中 → 标疑似不合并(D5 保守)。"""
    sub = TD / "batch3"
    sub.mkdir(parents=True, exist_ok=True)
    (sub / "master.png").write_bytes(noise_bytes(202, size=128))
    small = Image.open(io.BytesIO(noise_bytes(202, size=128))).resize((64, 64), Image.BILINEAR)
    buf = io.BytesIO()
    small.save(buf, format="PNG")
    (sub / "thumb.png").write_bytes(buf.getvalue())
    R = ingest.ingest_directory(TD / "data", sub, platform="网络收集", conn=CONN)
    assert len(R["near_duplicate"]) == 1, f"缩放图应标疑似重复, 实际报告: {R['near_duplicate']}"
    row = CONN.execute("SELECT notes FROM assets WHERE notes LIKE '疑似重复:%'").fetchone()
    assert row is not None, "疑似重复应写入 notes"
    total = CONN.execute("SELECT count(*) c FROM assets").fetchone()["c"]
    assert total == 11, f"疑似重复仍新建素材(不自动合并): 8(批次1)+1(T-04)+2(本批) = 11, 实际 {total}"


def t06_no_false_positive():
    n = CONN.execute("SELECT count(*) c FROM assets WHERE notes LIKE '疑似重复:%'").fetchone()["c"]
    assert n == 1, f"仅缩放图一条疑似, 实际 {n} 条"


def t07_source_passthrough():
    row = CONN.execute(
        "SELECT platform, license, note FROM sources WHERE platform = '测试甲方包'").fetchone()
    assert row["license"] == "client_provided" and row["note"].endswith(".png")


def t08_report_json():
    R = ingest.ingest_directory(TD / "data", SRC, platform="测试甲方包",
                                license="client_provided", conn=CONN)
    parsed = json.loads(json.dumps(R, ensure_ascii=False))
    assert parsed["total"] == R["total"]
    assert ingest.summarize(R).startswith("共")


def t09_db_not_corrupted():
    # 先写一条合法确认记录(空表上 UPDATE 不触发触发器, 是空操作而非通过)
    aid = CONN.execute("SELECT id FROM assets LIMIT 1").fetchone()["id"]
    edb.confirm(CONN, "asset", aid, "notes", "m", "c", "single", "op-t09")
    try:
        CONN.execute("UPDATE confirm_log SET field = 'x'")
        raise AssertionError("confirm_log 不应可写")
    except sqlite3.IntegrityError:
        pass


def main():
    check("T-01 dHash/汉明距离单元", t01_dhash_unit)
    check("T-02 混合批次: 8 导入 + 2 跳过, untagged 状态与 _pool 落盘", t02_mixed_batch)
    check("T-03 重复导入: 全部命中同来源, 素材/来源计数不变", t03_reimport)
    check("T-04 同内容不同文件名: 一个素材 + 两条来源(D5)", t04_same_content_two_files)
    check("T-05 近似重复: 同图缩放标疑似, 不自动合并", t05_near_duplicate)
    check("T-06 不同图无误报", t06_no_false_positive)
    check("T-07 授权/平台/文件名透传到来源记录", t07_source_passthrough)
    check("T-08 导入报告可 JSON 化且自洽", t08_report_json)
    check("T-09 全程不变量完好(confirm_log 仍只增不改)", t09_db_not_corrupted)

    fails = [r for r in results if r[1] == "FAIL"]
    w = max(len(n) for n, _, _ in results)
    for name, status, msg in results:
        print(f"{status:4}  {name.ljust(w)}  {msg}")
    print("-" * 78)
    print(f"合计 {len(results)} 项: 通过 {len(results) - len(fails)}, 失败 {len(fails)}")
    if "TD" in globals() and TD.exists():
        shutil.rmtree(TD, ignore_errors=True)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
