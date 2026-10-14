"""M3.1 补丁测试：hero 指针联动清理、undo 防覆盖守卫、doctor 巡检。

运行: python tests/test_m31.py
"""

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
from equiplens import doctor, ingest, workflow  # noqa: E402
from test_ingest import noise_bytes  # noqa: E402

results = []


def check(name, fn):
    try:
        fn()
        results.append((name, "PASS", ""))
    except Exception as e:  # noqa: BLE001
        import traceback
        results.append((name, "FAIL", f"{type(e).__name__}: {e}"))
        traceback.print_exc()


TD = Path(tempfile.mkdtemp(prefix="eq-m31-"))
DATA = TD / "data"
CONN = None
V = None
A = []


def setup():
    global CONN, V, A
    DATA.mkdir(parents=True, exist_ok=True)
    CONN = edb.connect(DATA / "equiplens.db")
    edb.init_db(CONN)
    src = TD / "batch"; src.mkdir()
    for i in range(4):
        (src / f"n{i}.png").write_bytes(noise_bytes(400 + i))
    rep = ingest.ingest_directory(DATA, src, platform="测试", license="client_provided", conn=CONN)
    A = [e["asset_id"] for e in rep["imported"]]
    V = workflow.create_vehicle(CONN, "品牌", "T1", category="牵引车")
    workflow.bind_asset(CONN, A[0], V)
    workflow.bind_asset(CONN, A[1], V)
    workflow.set_view(CONN, A[0], "hero_lf")
    workflow.set_view(CONN, A[1], "front")
    edb.set_hero(CONN, V, A[0])


def x01_reject_hero():
    workflow.reject_asset(CONN, A[0])
    hero = CONN.execute("SELECT hero_asset_id FROM vehicles WHERE id = ?", (V,)).fetchone()["hero_asset_id"]
    assert hero is None, "拒绝主图后指针应被清空"
    # 同 op 落账: 找到最近一次 reject 操作, 应含 vehicle.hero_asset_id 条目
    row = CONN.execute(
        """SELECT count(*) c FROM confirm_log WHERE object_type='vehicle' AND field='hero_asset_id'
           AND op_id = (SELECT op_id FROM confirm_log WHERE object_type='asset' AND object_id=?
                        AND field='confirm_status' AND confirmed_value='"rejected"'
                        ORDER BY rowid DESC LIMIT 1)""", (A[0],)).fetchone()
    assert row["c"] == 1, "清空指针应与拒绝同一操作落账"


def x02_unbind_hero():
    workflow.set_view(CONN, A[1], "hero_lf")  # 换 A1 为主视角并设主图
    edb.set_hero(CONN, V, A[1])
    assert CONN.execute("SELECT hero_asset_id FROM vehicles WHERE id = ?", (V,)).fetchone()["hero_asset_id"] == A[1]
    workflow.unbind_asset(CONN, A[1])
    assert CONN.execute("SELECT hero_asset_id FROM vehicles WHERE id = ?", (V,)).fetchone()["hero_asset_id"] is None, \
        "退回主图后指针应被清空"
    workflow.bind_asset(CONN, A[1], V)  # 恢复, 继续后续用例


def x03_reject_non_hero_untouched():
    edb.set_hero(CONN, V, A[1])
    workflow.reject_asset(CONN, A[2])  # A2 未对号, 与主图无关
    assert CONN.execute("SELECT hero_asset_id FROM vehicles WHERE id = ?", (V,)).fetchone()["hero_asset_id"] == A[1]
    workflow.set_view(CONN, A[1], "hero_lf")  # 确保后续一致


def x04_undo_guard():
    # 对同一字段连续两次修改
    op1 = workflow.set_view(CONN, A[1], "side_l")
    op2 = workflow.set_view(CONN, A[1], "hero_lf")
    assert CONN.execute("SELECT view_angle v FROM assets WHERE id = ?", (A[1],)).fetchone()["v"] == "hero_lf"
    try:
        edb.undo(CONN, op1)
        raise AssertionError("撤销旧操作应被守卫拦截")
    except ValueError:
        pass
    edb.undo(CONN, op2)  # 撤销最新操作放行
    assert CONN.execute("SELECT view_angle v FROM assets WHERE id = ?", (A[1],)).fetchone()["v"] == "side_l"
    # force 强制回退旧操作 → 恢复的是 op1 的机器原值(即 x03 设置的 hero_lf)
    edb.undo(CONN, op1, force=True)
    assert CONN.execute("SELECT view_angle v FROM assets WHERE id = ?", (A[1],)).fetchone()["v"] == "hero_lf"
    # 恢复状态供后续
    workflow.set_view(CONN, A[1], "hero_lf")
    workflow.set_view(CONN, A[0], "hero_lf")  # A0 已拒, 此句应报错? A0 confirm_status=rejected, set_view 不查状态 — 不报错, 视角可改


def x05_undo_other_field_allowed():
    # 不同字段(部位/其他素材)有更新操作不阻碍本字段撤销
    op = workflow.set_view(CONN, A[3], "side_r")
    edb.confirm(CONN, "asset", A[1], "notes", None, "测试备注", "single", "op-other-field")
    edb.undo(CONN, op)  # 不同对象, 守卫不应拦截
    assert CONN.execute("SELECT view_angle v FROM assets WHERE id = ?", (A[3],)).fetchone()["v"] == "untagged"


def x06_doctor_clean():
    report = doctor.doctor(CONN, DATA)
    assert report["ok"], f"健康库应无问题: {report['issues']}"


def x07_doctor_detects():
    # ① 孤儿文件
    orphan = DATA / "assets" / "_pool" / "originals" / "orphan.png"
    orphan.write_bytes(noise_bytes(999))
    # ② 缺失文件 (A2 在 X-03 已被拒, 删其文件)
    victim = CONN.execute("SELECT file_path FROM assets WHERE id = ?", (A[2],)).fetchone()["file_path"]
    (DATA / victim).unlink()
    # ④ 先建两人组 (A1 此刻仍为已确认态)
    workflow.link_variants(CONN, [A[3], A[1]])
    # ③ 再模拟绕过契约把 A1 标拒 → 同时制造悬空主图(A1 是 hero)与残留变体组(④)
    CONN.execute("UPDATE assets SET confirm_status='rejected' WHERE id = ?", (A[1],))
    CONN.commit()
    report = doctor.doctor(CONN, DATA)
    assert not report["ok"]
    assert len(report["issues"]["orphan_files"]) == 1
    assert len(report["issues"]["missing_files"]) == 1
    assert len(report["issues"]["dangling_hero"]) == 1
    assert len(report["issues"]["stale_variant_groups"]) == 1


def x08_set_hero_rejected():
    try:
        edb.set_hero(CONN, V, A[0])  # A0 已被拒
        raise AssertionError("被拒素材不得设为主图")
    except ValueError:
        pass


check("X-00 建库+导入+建车+对号+主图", setup)
check("X-01 拒绝主图 → 指针联动清空且同 op 落账", x01_reject_hero)
check("X-02 退回主图 → 指针联动清空", x02_unbind_hero)
check("X-03 拒绝非主图 → 主图不受影响", x03_reject_non_hero_untouched)
check("X-04 undo 守卫: 旧操作拦截/最新放行/force 强制", x04_undo_guard)
check("X-05 undo 守卫按对象+字段判定, 他字段不拦截", x05_undo_other_field_allowed)
check("X-06 doctor: 健康库巡检通过", x06_doctor_clean)
check("X-07 doctor: 孤儿/缺失/悬空主图/残留变体组全检出", x07_doctor_detects)
check("X-08 set_hero 拒绝被拒素材", x08_set_hero_rejected)

fails = [r for r in results if r[1] == "FAIL"]
w = max(len(n) for n, _, _ in results)
for name, status, msg in results:
    print(f"{status:4}  {name.ljust(w)}  {msg}")
print("-" * 78)
print(f"合计 {len(results)} 项: 通过 {len(results) - len(fails)}, 失败 {len(fails)}")
shutil.rmtree(TD, ignore_errors=True)
sys.exit(1 if fails else 0)
