"""EquipLens 数据层·第一档测试（全合成数据，零模型调用）。

覆盖: ①schema 合法性(正例+9 组负例) ②不变量(只增不改/CHECK/外键/原图不可变/机器原值保留+撤销)
     ③往返一致 ④派生查询正确性(完备度/槽位/待归号池/三轴查询)
运行: python tests/test_data_layer.py
"""

import copy
import json
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

import jsonschema  # noqa: E402

from equiplens import db as edb  # noqa: E402
import synthetic_data as fx  # noqa: E402

SCHEMA = json.loads((ROOT / "schemas" / "equip-data.schema.json").read_text(encoding="utf-8"))

results = []


def check(name, fn):
    try:
        fn()
        results.append((name, "PASS", ""))
    except Exception as e:  # noqa: BLE001
        results.append((name, "FAIL", f"{type(e).__name__}: {e}"))


def expect_raises(exc_type, fn, name=""):
    try:
        fn()
    except exc_type:
        return
    except Exception as e:  # noqa: BLE001
        raise AssertionError(f"[{name}] 期望 {exc_type.__name__}, 实际 {type(e).__name__}: {e}")
    raise AssertionError(f"[{name}] 期望 {exc_type.__name__}, 但调用成功")


# ---------------------------------------------------------------- Phase A 合法性

BUNDLE = fx.build_bundle()


def validate(b):
    jsonschema.validate(b, SCHEMA)


def mutated(fn):
    b = copy.deepcopy(BUNDLE)
    fn(b)
    return b


def phase_a():
    check("A-01 正例: 合成黄金样例整体通过 schema 校验", lambda: validate(BUNDLE))

    def neg(name, fn):
        check(name, lambda: expect_raises(jsonschema.ValidationError,
                                          lambda: validate(mutated(fn)), name))

    neg("A-02 负例: 视角取枚举外值", lambda b: b["assets"][0].__setitem__("view_angle", "鸟瞰"))
    neg("A-03 负例: 裁图缺 crop_bbox", lambda b: b["assets"][3].__setitem__("crop_bbox", None))
    neg("A-04 负例: 原图带 parent(违反只从原图裁)", lambda b: b["assets"][0].__setitem__("parent_asset_id", fx.A2))
    neg("A-05 负例: 描述无证据素材(evidence 空)", lambda b: b["descriptions"][0].__setitem__("evidence_asset_ids", []))
    neg("A-06 负例: 授权取枚举外值", lambda b: b["sources"][0].__setitem__("license", "网友自传"))
    neg("A-07 负例: 待归号池素材挂了车型", lambda b: b["assets"][6].__setitem__("vehicle_id", fx.V1))
    neg("A-08 负例: hash 非 sha256", lambda b: b["assets"][0].__setitem__("hash_sha256", "abc"))
    neg("A-09 负例: 确认方式取枚举外值", lambda b: b["confirm_log"][0].__setitem__("method", "maybe"))
    neg("A-10 负例: 部位描述缺 part_id", lambda b: b["descriptions"][3].__setitem__("part_id", None))
    neg("A-11 负例: 实体带未定义字段", lambda b: b["vehicles"][0].__setitem__("foo", 1))


# ---------------------------------------------------------------- Phase B 不变量

CONN = None
DATA_DIR = None


def setup_db():
    global CONN, DATA_DIR
    DATA_DIR = Path(tempfile.mkdtemp(prefix="equiplens-test-"))
    CONN = edb.connect(DATA_DIR / "equiplens.db")
    edb.init_db(CONN)
    fx.write_asset_files(DATA_DIR)
    edb.import_bundle(CONN, BUNDLE)


def phase_b():
    check("B-00 建库+落盘+导入", setup_db)

    def b1():
        expect_raises(sqlite3.IntegrityError,
                      lambda: CONN.execute("UPDATE confirm_log SET field = 'x'").fetchall(), "B-01")
    check("B-01 不变量: confirm_log 禁止 UPDATE(触发器 ABORT)", b1)

    def b2():
        expect_raises(sqlite3.IntegrityError,
                      lambda: CONN.execute("DELETE FROM confirm_log").fetchall(), "B-02")
    check("B-02 不变量: confirm_log 禁止 DELETE(触发器 ABORT)", b2)

    def b3():
        def ins():
            CONN.execute(
                "INSERT INTO assets (id, binding_status, binding_evidence, kind, parent_asset_id,"
                " crop_bbox, file_path, view_angle, asset_nature, hash_sha256, confirm_status,"
                " created_at, updated_at) VALUES"
                " ('x0','unbound','none','crop',NULL,NULL,'p.png','detail','real_photo',"
                " '0000000000000000000000000000000000000000000000000000000000000000',"
                " 'machine_tagged','2026-01-01T00:00:00+08:00','2026-01-01T00:00:00+08:00')")
        expect_raises(sqlite3.IntegrityError, ins, "B-03")
    check("B-03 不变量: 裁图必须有父图+bbox(CHECK 拒绝)", b3)

    def b4():
        def ins():
            CONN.execute(
                "INSERT INTO assets (id,binding_status,binding_evidence,kind,file_path,view_angle,"
                "asset_nature,hash_sha256,confirm_status,vehicle_id,created_at,updated_at)"
                " VALUES ('x1','unbound','none','source_image','p.png','detail','real_photo',"
                "'0000000000000000000000000000000000000000000000000000000000000000',"
                "'machine_tagged','x','2026-01-01T00:00:00+08:00','2026-01-01T00:00:00+08:00')")
        expect_raises(sqlite3.IntegrityError, ins, "B-04")
    check("B-04 不变量: unbound 不得挂车型(CHECK 拒绝)", b4)

    def b5():
        def ins():
            CONN.execute(
                "INSERT INTO assets (id,binding_status,binding_evidence,kind,file_path,view_angle,"
                "asset_nature,hash_sha256,confirm_status,part_id,created_at,updated_at)"
                " VALUES ('x2','unbound','none','source_image','p2.png','detail','real_photo',"
                "'1111111111111111111111111111111111111111111111111111111111111111',"
                "'machine_tagged','not_in_vocab','2026-01-01T00:00:00+08:00','2026-01-01T00:00:00+08:00')")
        expect_raises(sqlite3.IntegrityError, ins, "B-05")
    check("B-05 不变量: 部位必须取自词表(外键拒绝)", b5)

    def b6():
        # 机器原值保留 + 撤销恢复
        machine_text = "黑色格栅显得稳重"
        user_text = "黑色格栅压低视觉重心，传达可靠性（确认修改）"
        log_id = edb.confirm(CONN, "description", fx.D5, "body", machine_text, user_text,
                             "single", "op-test-001", at="2026-10-10T10:00:00+08:00")
        cur = CONN.execute("SELECT body FROM descriptions WHERE id = ?", (fx.D5,)).fetchone()
        assert cur["body"] == user_text, "确认后字段未更新"
        row = CONN.execute("SELECT machine_value, confirmed_value FROM confirm_log WHERE id = ?",
                           (log_id,)).fetchone()
        assert json.loads(row["machine_value"]) == machine_text, "机器原值未保留"
        edb.undo(CONN, log_id)
        cur = CONN.execute("SELECT body FROM descriptions WHERE id = ?", (fx.D5,)).fetchone()
        assert cur["body"] == machine_text, "撤销未恢复机器原值"
        CONN.execute("UPDATE descriptions SET body = ? WHERE id = ?", (user_text, fx.D5))
        CONN.commit()
    check("B-06 不变量: 确认写日志+机器原值保留, 撤销恢复原值", b6)

    def b7():
        expect_raises(FileExistsError,
                      lambda: edb.save_original(DATA_DIR, fx.V1, fx.A1, "png", fx.FILE_BYTES[fx.A1]),
                      "B-07")
    check("B-07 不变量: 原图不可覆盖(save_original 拒绝)", b7)

    def b8():
        expect_raises(ValueError,
                      lambda: edb.set_hero(CONN, fx.V1, fx.A2), "B-08")
        edb.set_hero(CONN, fx.V1, fx.A1)
        row = CONN.execute("SELECT hero_asset_id FROM vehicles WHERE id = ?", (fx.V1,)).fetchone()
        assert row["hero_asset_id"] == fx.A1
    check("B-08 约束: 主图指针仅接受该车 3/4 主视角素材", b8)

    def b9():
        n = CONN.execute(
            "SELECT count(*) c FROM assets a JOIN descriptions d ON d.vehicle_id = a.vehicle_id"
            " WHERE a.id = ? AND d.id = ?", (fx.A4, fx.D4)).fetchone()["c"]
        assert n == 1, "描述证据链断裂"
    check("B-09 溯源链: 描述证据素材存在且同车(NFR-6)", b9)


# ---------------------------------------------------------------- Phase C 往返一致

def phase_c():
    def c1():
        exp1 = edb.export_bundle(CONN)
        validate(exp1)
        td = tempfile.mkdtemp(prefix="equiplens-rt-")
        try:
            conn2 = edb.connect(Path(td) / "t.db")
            edb.init_db(conn2)
            edb.import_bundle(conn2, exp1)
            exp2 = edb.export_bundle(conn2)
            conn2.close()  # Windows: 必须先关连接才能清理目录
        finally:
            import shutil
            shutil.rmtree(td, ignore_errors=True)
        validate(exp2)
        e1, e2 = copy.deepcopy(exp1), copy.deepcopy(exp2)
        for e in (e1, e2):
            e["meta"].pop("exported_at")  # 时间戳天然不同, 不参与比对
        assert json.dumps(e1, sort_keys=True, ensure_ascii=False) == \
               json.dumps(e2, sort_keys=True, ensure_ascii=False), "两次导出内容不一致"
    check("C-01 往返一致: 导出→导入→导出逐字段一致, 且两次均过 schema", c1)


# ---------------------------------------------------------------- Phase D 派生查询

def phase_d():
    def d1():
        assert edb.completeness(CONN, fx.V1)["level"] == "L2", "V1 应为 L2(主图+正前+3裁图含前脸, 缺后视与内饰)"
        assert edb.completeness(CONN, fx.V2)["level"] == "L1", "V2 应为 L1(仅主图)"
        assert edb.completeness(CONN, fx.V3)["level"] == "L0", "V3 应为 L0(无素材)"
    check("D-01 派生: 完备度 L2/L1/L0 与人工预期一致", d1)

    def d2():
        assert edb.slot_state(CONN, fx.V1, "grille") == "有·已确认"
        assert edb.slot_state(CONN, fx.V1, "mirror") == "有·待确认"
        assert edb.slot_state(CONN, fx.V1, "fender") == "缺失"
    check("D-02 派生: 部位槽位三态正确", d2)

    def d3():
        pool = edb.unbound_pool(CONN)
        assert [r["id"] for r in pool] == [fx.A7], "待归号池应恰含孤立特写 A7"
    check("D-03 派生: 待归号池 = unbound 素材(D2 延迟归号)", d3)

    def d4():
        rows = edb.descriptions_query(CONN, vehicle_id=fx.V1, scope="family")
        assert {r["id"] for r in rows} == {fx.D3, fx.D5}, "品牌家族条目应为 D3/D5"
        rows = edb.descriptions_query(CONN, vehicle_id=fx.V1, node_type="part", part_id="grille")
        assert {r["id"] for r in rows} == {fx.D4, fx.D5}, "格栅部位条目应为 D4/D5"
        rows = edb.descriptions_query(CONN, vehicle_id=fx.V1, axis_type="intent", only_confirmed=True)
        assert {r["id"] for r in rows} == {fx.D5}
    check("D-04 派生: 描述三轴查询与页型取数一致", d4)

    def d5():
        row = edb.find_asset_by_hash(CONN, fx.sha(fx.FILE_BYTES[fx.A1]))
        assert row["id"] == fx.A1, "文件哈希判重(D5 同图多源入口)未命中"
    check("D-05 派生: 文件哈希判重命中已入库素材", d5)


phase_a()
phase_b()
phase_c()
phase_d()

fails = [r for r in results if r[1] == "FAIL"]
w = max(len(n) for n, _, _ in results)
for name, status, msg in results:
    print(f"{status:4}  {name.ljust(w)}  {msg}")
print("-" * 78)
print(f"合计 {len(results)} 项: 通过 {len(results) - len(fails)}, 失败 {len(fails)}")
sys.exit(1 if fails else 0)
