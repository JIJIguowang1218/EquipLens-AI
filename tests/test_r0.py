"""R0 脚手架测试：检索计划换算、审核包生成与 decisions.json 回读落账。

运行: python tests/test_r0.py
"""

import json
import shutil
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
from equiplens import ingest, retrieval, review  # noqa: E402
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


TD = Path(tempfile.mkdtemp(prefix="eq-r0-"))
DATA = TD / "data"
CONN = None
V1 = V2 = None
BATCH = "batch-r0-test"
A = []


def setup():
    global CONN, V1, V2, A
    DATA.mkdir(parents=True, exist_ok=True)
    CONN = edb.connect(DATA / "equiplens.db")
    edb.init_db(CONN)
    src = TD / "batch"; src.mkdir()
    for i in range(5):
        (src / f"cand_{i}.png").write_bytes(noise_bytes(600 + i))
    rep = ingest.ingest_directory(DATA, src, platform="S1夹具渠道", license="web_third_party",
                                  conn=CONN, batch_id=BATCH)
    A = [e["asset_id"] for e in rep["imported"]]
    CONN.executemany("INSERT INTO vocab (id, type, term, status) VALUES (?, 'part', ?, 'active')",
                     [("grille", "进气格栅"), ("headlamp", "大灯"), ("step", "踏步")])
    CONN.commit()
    V1 = workflow_create("品牌甲", "车型X")
    V2 = workflow_create("品牌甲", "车型Y")


def workflow_create(brand, model):
    from equiplens import workflow
    return workflow.create_vehicle(CONN, brand, model, category="装载机")


def p01_full_plan():
    plan = retrieval.build_plan({"type": "full", "vehicles": ["品牌甲 车型X", "品牌甲 车型Y"],
                                 "parts": ["grille", "headlamp"],
                                 "page_types": [{"type": "vehicle_page", "pages": 2}]})
    kinds = [t["kind"] for t in plan["tasks"]]
    assert kinds.count("roster") == 1 and kinds.count("params") == 2 and kinds.count("images") == 2
    assert plan["quota_per_vehicle"] == 12, f"2 页 × 6 图 = 12, 实际 {plan['quota_per_vehicle']}"
    img = [t for t in plan["tasks"] if t["kind"] == "images"][0]
    assert img["parts"] == ["grille", "headlamp"] and img["quota"] == 12
    Path(TD / "plan_full.json").write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")


def p02_part_focus_plan():
    plan = retrieval.build_plan({"type": "part_focus", "vehicles": ["品牌甲 车型X"],
                                 "parts": ["step"],
                                 "page_types": [{"type": "vehicle_page", "pages": 1}]})
    assert [t["kind"] for t in plan["tasks"]] == ["part_images"]
    assert plan["tasks"][0]["part"] == "step" and plan["tasks"][0]["quota"] == 6


def p03_gap_fill_plan():
    # V1: 绑定+hero 打标 → L1; V2: 空 → L0
    from equiplens import workflow
    workflow.bind_asset(CONN, A[0], V1)
    workflow.set_view(CONN, A[0], "hero_lf")
    edb.confirm_many(CONN, [("asset", A[0], "confirm_status", "machine_tagged", "confirmed")],
                     op_id="op-cf", method="single")
    plan = retrieval.build_plan({"type": "gap_fill", "vehicles": [V1, V2],
                                 "parts": ["grille", "headlamp", "step"],
                                 "page_types": [{"type": "vehicle_page", "pages": 1}]}, conn=CONN)
    by_v = {t["vehicle"]: t for t in plan["tasks"]}
    assert by_v[V1]["missing_views"] == [], "V1 已有 hero, 视角无缺口"
    assert set(by_v[V1]["missing_parts"]) == {"grille", "headlamp", "step"}
    assert set(by_v[V2]["missing_views"]) == {"hero_lf", "hero_rf", "side_l", "side_r"}, "V2 空车全缺口"
    # 配置校验负例
    for bad in [{"type": "unknown", "vehicles": ["x"]},
                {"type": "part_focus", "vehicles": ["x"], "parts": []},
                {"type": "full", "vehicles": []},
                {"type": "full", "vehicles": ["x"], "page_types": [{"type": "mood", "pages": 1}]}]:
        try:
            retrieval.build_plan(bad, conn=CONN)
            raise AssertionError(f"非法配置应被拒绝: {bad}")
        except ValueError:
            pass


def r01_review_pack():
    out = TD / "review.html"
    info = review.build_review_pack(CONN, DATA, BATCH, out)
    # 5 个素材, 2 组: A0 已在 P-03 对号到 V1, 其余仍在待归号池
    assert info["assets"] == 5 and info["groups"] == 2, f"实际 {info}"
    html = out.read_text(encoding="utf-8")
    for aid in A:
        assert aid in html, f"审核包应包含素材 {aid}"
        assert f'name="{aid}"' in html
    assert html.count("data:image/jpeg") == 5, "缩略图应全部 base64 内嵌"
    assert "exportDecisions" in html and BATCH in html


def r02_apply_reject():
    decisions = {"batch_id": BATCH, "decisions": [
        {"asset_id": A[1], "action": "reject", "reason": "水印太大"},
        {"asset_id": A[2], "action": "accept"},
        {"asset_id": "nonexistent", "action": "reject"},
    ]}
    summary = review.apply_review(CONN, decisions, DATA)
    assert summary["rejected"] == 1 and summary["accepted"] == 1 and summary["skipped"] == 1, f"实际 {summary}"
    row = CONN.execute("SELECT confirm_status, notes FROM assets WHERE id = ?", (A[1],)).fetchone()
    assert row["confirm_status"] == "rejected" and "水印太大" in row["notes"]
    assert CONN.execute("SELECT confirm_status c FROM assets WHERE id = ?",
                        (A[2],)).fetchone()["c"] == "confirmed", "接受=人工确认素材可用(与驳回对称)"
    assert list((DATA / "reviews").glob("*.json")), "决策原件应归档"


def r03_apply_accept_with_bind():
    decisions = {"batch_id": BATCH, "decisions": [
        {"asset_id": A[3], "action": "accept", "vehicle_id": V1, "view": "hero_lf"},
    ]}
    summary = review.apply_review(CONN, decisions, DATA)
    assert summary["accepted"] == 1 and summary["bound"] == 1
    row = CONN.execute("SELECT vehicle_id, view_angle FROM assets WHERE id = ?", (A[3],)).fetchone()
    assert row["vehicle_id"] == V1 and row["view_angle"] == "hero_lf"
    # 接受+对号的决策也进账本
    n = CONN.execute("SELECT count(*) c FROM confirm_log WHERE object_type='asset'"
                     " AND object_id = ? AND field='binding_status'", (A[3],)).fetchone()["c"]
    assert n == 1, "对号应有账"


def r04_plan_cli_ready():
    # plan JSON 应符合"模块间走数据契约"精神: 可 json 序列化且含必要键
    plan = retrieval.build_plan({"type": "full", "vehicles": ["x"], "parts": []}, conn=CONN)
    json.dumps(plan, ensure_ascii=False)
    for key in ("plan_id", "type", "vehicles", "parts", "quota_per_vehicle", "tasks"):
        assert key in plan


check("P-00 建库+按批次导入5张+词表+双车型", setup)
check("P-01 full 计划: 任务树结构与配额换算", p01_full_plan)
check("P-02 part_focus 计划: 部件子任务", p02_part_focus_plan)
check("P-03 gap_fill 计划: 完备度缺口推导 + 4 组配置负例", p03_gap_fill_plan)
check("R-01 审核包: 素材齐全、缩略图内嵌、可交互结构", r01_review_pack)
check("R-02 apply-review: 驳回落账+理由入 notes+归档", r02_apply_reject)
check("R-03 apply-review: 接受+对号+打标进账本", r03_apply_accept_with_bind)
check("R-04 计划 JSON 可序列化且含必要键", r04_plan_cli_ready)

fails = [r for r in results if r[1] == "FAIL"]
w = max(len(n) for n, _, _ in results)
for name, status, msg in results:
    print(f"{status:4}  {name.ljust(w)}  {msg}")
print("-" * 78)
print(f"合计 {len(results)} 项: 通过 {len(results) - len(fails)}, 失败 {len(fails)}")
shutil.rmtree(TD, ignore_errors=True)
sys.exit(1 if fails else 0)
