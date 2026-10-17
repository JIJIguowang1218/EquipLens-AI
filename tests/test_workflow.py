"""M2 确认工作流测试（合成数据, 零模型调用）。

覆盖: 车型管理、对号/退回(原子三字段)、视角打标(单条/批量)、裁图(内生自证+边界校验)、
     拒绝、完备度随工作流演进(L0→L1→L2)、主图约束、审计账本、按操作号整体撤销。
运行: python tests/test_workflow.py
"""

import io
import json
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from equiplens import db as edb  # noqa: E402
from equiplens import ingest, workflow  # noqa: E402
from test_ingest import noise_bytes  # noqa: E402  (有 main 守卫, 导入安全)

results = []


def check(name, fn):
    try:
        fn()
        results.append((name, "PASS", ""))
    except Exception as e:  # noqa: BLE001
        import traceback
        results.append((name, "FAIL", f"{type(e).__name__}: {e}"))
        traceback.print_exc()


TD = Path(tempfile.mkdtemp(prefix="eq-m2-"))
DATA = TD / "data"
CONN = None
V = None
A = []  # 4 张素材 id


def setup():
    global CONN, V, A
    DATA.mkdir(parents=True, exist_ok=True)
    CONN = edb.connect(DATA / "equiplens.db")
    edb.init_db(CONN)
    src = TD / "batch"
    src.mkdir()
    for i in range(4):
        (src / f"n{i}.png").write_bytes(noise_bytes(300 + i))
    rep = ingest.ingest_directory(DATA, src, platform="测试", license="client_provided", conn=CONN)
    A = [e["asset_id"] for e in rep["imported"]]
    # 词表: 最小部位集
    CONN.executemany("INSERT INTO vocab (id, type, term, status) VALUES (?, 'part', ?, 'active')",
                     [("grille", "进气格栅"), ("headlamp", "大灯"), ("step", "踏步")])
    CONN.commit()
    V = workflow.create_vehicle(CONN, "测试品牌", "T1", category="牵引车", generation="2024款")


def w01_vehicle():
    expect_dup = lambda: workflow.create_vehicle(CONN, "测试品牌", "T1", generation="2024款")
    try:
        expect_dup()
        raise AssertionError("同品牌+型号+年款应被 UNIQUE 拒绝")
    except sqlite3.IntegrityError:
        pass
    rows = edb.assets_for_vehicle(CONN, V)
    assert rows == [], "新车车型应为空"


def w02_bind():
    workflow.bind_asset(CONN, A[0], V)
    row = CONN.execute("SELECT vehicle_id, binding_status, binding_evidence FROM assets WHERE id = ?",
                       (A[0],)).fetchone()
    assert (row["vehicle_id"], row["binding_status"], row["binding_evidence"]) == (V, "confirmed", "human")
    assert len(edb.unbound_pool(CONN)) == 3, "对号后应退出待归号池"
    # 双绑拒绝
    try:
        workflow.bind_asset(CONN, A[0], V)
        raise AssertionError("已对号素材不得再次对号")
    except ValueError:
        pass


def w03_unbind_and_undo():
    workflow.unbind_asset(CONN, A[0])
    row = CONN.execute("SELECT binding_status, vehicle_id FROM assets WHERE id = ?", (A[0],)).fetchone()
    assert row["binding_status"] == "unbound" and row["vehicle_id"] is None
    op = workflow.bind_asset(CONN, A[0], V)
    # 按操作号整体撤销(用返回值, 不按时间取"最新"——同秒多操作无稳定顺序)
    edb.undo(CONN, op)
    row = CONN.execute("SELECT binding_status, vehicle_id FROM assets WHERE id = ?", (A[0],)).fetchone()
    assert row["binding_status"] == "unbound", "撤销对号操作后应回到 unbound"
    workflow.bind_asset(CONN, A[0], V)  # 恢复对号, 继续后续用例


def w04_tag_single_and_batch():
    workflow.set_view(CONN, A[0], "hero_lf")
    op = workflow.batch_set_view(CONN, [(A[1], "front"), (A[2], "side_l")])
    rows = CONN.execute("SELECT method, count(*) c FROM confirm_log WHERE op_id = ? GROUP BY method",
                        (op,)).fetchall()
    assert rows[0]["method"] == "batch" and rows[0]["c"] == 2, "批量打标应两字段同一操作号"
    for aid, expect in [(A[0], "hero_lf"), (A[1], "front"), (A[2], "side_l")]:
        got = CONN.execute("SELECT view_angle FROM assets WHERE id = ?", (aid,)).fetchone()["view_angle"]
        assert got == expect
    try:
        workflow.set_view(CONN, A[3], "俯视")
        raise AssertionError("枚举外视角应被拒绝")
    except ValueError:
        pass


def w05_crop():
    # 未对号素材不允许裁: A[3] 仍在池中
    try:
        workflow.crop_asset(CONN, DATA, A[3], {"x": 10, "y": 10, "w": 40, "h": 40}, "grille")
        raise AssertionError("未对号原图不得裁图")
    except ValueError:
        pass
    # 正常裁: 从 A[0](128x128) 中央裁 40x40
    cid = workflow.crop_asset(CONN, DATA, A[0], {"x": 44, "y": 44, "w": 40, "h": 40}, "grille")
    row = CONN.execute("SELECT * FROM assets WHERE id = ?", (cid,)).fetchone()
    assert row["kind"] == "crop" and row["parent_asset_id"] == A[0]
    assert row["binding_evidence"] == "self_derived", "内生裁图应自证(证据=self_derived)"
    assert json.loads(row["crop_bbox"]) == {"x": 44, "y": 44, "w": 40, "h": 40}
    assert (DATA / row["file_path"]).exists()
    # 越界拒绝
    try:
        workflow.crop_asset(CONN, DATA, A[0], {"x": 100, "y": 100, "w": 80, "h": 80}, "grille")
        raise AssertionError("越界 bbox 应被拒绝")
    except ValueError:
        pass
    # 不允许从裁图再裁
    try:
        workflow.crop_asset(CONN, DATA, cid, {"x": 0, "y": 0, "w": 10, "h": 10}, "grille")
        raise AssertionError("不得从裁图再裁(D1)")
    except ValueError:
        pass


def w06_completeness_evolution():
    # A1/A2 此前只打标未对号, 先对号; 再批量确认 A0/A1/A2 的标签(对号≠标签确认, 两个状态轴)
    workflow.bind_asset(CONN, A[1], V)
    workflow.bind_asset(CONN, A[2], V)
    edb.confirm_many(CONN, [("asset", aid, "confirm_status", "machine_tagged", "confirmed")
                            for aid in (A[0], A[1], A[2])],
                     op_id="op-confirm-tags", method="batch")
    # 当前: A0 已绑已标 hero_lf; A1/A2 已绑(front/side_l)
    lvl = edb.completeness(CONN, V)["level"]
    assert lvl == "L1", f"hero 打标后应为 L1, 实际 {lvl}"
    # 裁第二张前脸部位并确认两张裁图 → L2 (front 已有, ≥2 裁图, 含前脸)
    workflow.crop_asset(CONN, DATA, A[0], {"x": 20, "y": 20, "w": 40, "h": 40}, "headlamp")
    for cid in [r["id"] for r in CONN.execute(
            "SELECT id FROM assets WHERE kind='crop' AND vehicle_id=? ", (V,))]:
        edb.confirm(CONN, "asset", cid, "confirm_status", "machine_tagged", "confirmed",
                    "batch", "op-confirm-crops")
    lvl = edb.completeness(CONN, V)["level"]
    assert lvl == "L2", f"正前+2 张已确认前脸裁图应为 L2, 实际 {lvl}"


def w07_hero_and_reject():
    edb.set_hero(CONN, V, A[0])
    s = workflow.vehicle_summary(CONN, V)
    assert s["hero_asset_id"] == A[0]
    workflow.reject_asset(CONN, A[3])
    pool_ids = [r["id"] for r in edb.unbound_pool(CONN)]
    assert A[3] not in pool_ids, "被拒绝素材不得出现在待归号池"
    row = CONN.execute("SELECT confirm_status FROM assets WHERE id = ?", (A[3],)).fetchone()
    assert row["confirm_status"] == "rejected"


def w08_audit():
    # 每步操作都有账; 账本不可改写
    n = CONN.execute("SELECT count(*) c FROM confirm_log").fetchone()["c"]
    assert n >= 10, f"工作流操作应留痕 >=10 条, 实际 {n}"
    try:
        CONN.execute("UPDATE confirm_log SET field = 'x'")
        raise AssertionError("confirm_log 不应可写")
    except sqlite3.IntegrityError:
        pass


def w09_summary():
    s = workflow.vehicle_summary(CONN, V)
    assert s["asset_counts"]["confirmed"] == 5, f"A0/A1/A2 + 两张已确认裁图, 实际 {s['asset_counts']}"
    # A3 未对号即被拒, 不属于任何车型 → 车型摘要中不计, 库级查
    assert s["asset_counts"].get("rejected", 0) == 0, "车型摘要只统计本车素材"
    global_rejected = CONN.execute(
        "SELECT count(*) c FROM assets WHERE confirm_status = 'rejected'").fetchone()["c"]
    assert global_rejected == 1, "库级应有 1 条被拒素材"
    assert len(s["pending_confirm"]) == 0, f"全部标签均已确认, 实际待确认 {s['pending_confirm']}"
    assert s["completeness"]["level"] == "L2", f"完备度应 L2, 实际 {s['completeness']}"
    assert s["vehicle"]["model_name"] == "T1", f"车型信息错: {s['vehicle']}"


def w10_real_copy_demo():
    """真实库副本演练: 把 IEVCO 池中 1 张挂到演示车型再撤销, 不留改动。"""
    real = edb.connect("data-test/equiplens.db")
    real2 = edb.connect(TD / "real_copy.db")
    real2.executescript(
        "\n".join(f"{r[0]};" for r in real.execute(
            "SELECT sql FROM sqlite_master WHERE sql IS NOT NULL")))
    for t in ["vocab", "vehicles", "assets", "sources", "facts", "descriptions", "confirm_log"]:
        rows = real.execute(f"SELECT * FROM {t}").fetchall()
        if rows:
            cols = rows[0].keys()
            ph = ",".join("?" for _ in cols)
            real2.executemany(f"INSERT INTO {t} ({','.join(cols)}) VALUES ({ph})",
                              [tuple(r) for r in rows])
    real2.commit()
    vid = workflow.create_vehicle(real2, "依维柯", "演示车型")
    pool = edb.unbound_pool(real2)
    n_pool = len(pool)
    assert n_pool >= 1, "副本应有待归号池素材"
    target = next((a for a in pool if a["view_angle"] == "untagged"), None)
    if target is None:
        # 真实库池内素材可能已带视角标签（标注飞轮推进后是常态）:
        # 一次性副本上直接清为未打标（不走账本）, 保持"绑 1 张→完备度 L0"的演练前提
        target = pool[0]
        real2.execute("UPDATE assets SET view_angle='untagged' WHERE id=?",
                      (target["id"],))
        real2.commit()
    target = real2.execute("SELECT * FROM assets WHERE id=?", (target["id"],)).fetchone()
    cs_before = target["confirm_status"]
    workflow.bind_asset(real2, target["id"], vid)
    s = workflow.vehicle_summary(real2, vid)
    assert s["asset_counts"].get(cs_before, 0) == 1,         f"对号不改标签确认状态({cs_before}), 实际 {s['asset_counts']}"
    assert s["completeness"]["level"] == "L0"
    log = real2.execute("SELECT id FROM confirm_log ORDER BY confirmed_at DESC LIMIT 1").fetchone()
    edb.undo(real2, log["id"])
    assert len(edb.unbound_pool(real2)) == n_pool, "撤销后真实副本应回到初始状态"
    real.close(); real2.close()


check("W-00 建库+导入4张+词表+建车型", setup)
check("W-01 车型创建与唯一约束", w01_vehicle)
check("W-02 对号: 三字段原子变更+退出待归号池+双绑拒绝", w02_bind)
check("W-03 退回与按操作号整体撤销", w03_unbind_and_undo)
check("W-04 打标: 单条/批量/枚举外拒绝", w04_tag_single_and_batch)
check("W-05 裁图: 内生自证+bbox必记+越界/未对号/再裁拒绝", w05_crop)
check("W-06 完备度演进 L1→L2(确认裁图后)", w06_completeness_evolution)
check("W-07 主图约束与拒绝素材", w07_hero_and_reject)
check("W-08 审计账本: 全程留痕且不可改写", w08_audit)
check("W-09 车型摘要数字正确", w09_summary)
check("W-10 真实库副本演练(绑1张→摘要→撤销复原)", w10_real_copy_demo)

fails = [r for r in results if r[1] == "FAIL"]
w = max(len(n) for n, _, _ in results)
for name, status, msg in results:
    print(f"{status:4}  {name.ljust(w)}  {msg}")
print("-" * 78)
print(f"合计 {len(results)} 项: 通过 {len(results) - len(fails)}, 失败 {len(fails)}")
shutil.rmtree(TD, ignore_errors=True)
sys.exit(1 if fails else 0)
