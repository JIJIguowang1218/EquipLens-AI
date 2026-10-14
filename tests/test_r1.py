"""R1 图文检索核心测试（S1 场景，夹具渠道离线跑，零模型调用）。

夹具: 现场生成 2 品牌 × 2 车型的模拟厂商页（HTML + 噪声 PNG），
每页含 1 张主视角图(alt 标左前45) + 2 张部件特写(格栅/大灯) + 参数表。

覆盖: 页面解析/车型命中、alt→视角与部位映射、T2 共现挂载(provisional)、
     证据链完整性(闸门: 每张候选可回答"为什么是这台车")、审核循环(接受=确认对号,
     证据升级 human)、重复检索幂等、未知车型空结果如实呈现、S1 全量四车型。
运行: python tests/test_r1.py
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
from equiplens import channels, retrieval, review  # noqa: E402
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


TD = Path(tempfile.mkdtemp(prefix="eq-r1-"))
DATA = TD / "data"
CONN = None
CHANNEL = None
PAGE_HTML = """<!doctype html><html><head><title>{brand} {model} - 官方产品页</title></head>
<body><h1>{brand} {model}</h1>
<img src="img/{slug}_hero.png" alt="{brand} {model} 左前45度外观官方图">
<img src="img/{slug}_grille.png" alt="{model} 进气格栅特写">
<img src="img/{slug}_headlamp.png" alt="{model} 大灯与灯罩防护特写">
<table>
<tr><th>整备质量</th><td>{mass} kg</td></tr>
<tr><th>额定功率</th><td>{power} kW</td></tr>
</table></body></html>"""

VEHICLES = [("品牌甲", "车型X", 8800, 460), ("品牌甲", "车型Y", 9200, 480),
            ("品牌乙", "车型Z", 7500, 350), ("品牌乙", "车型W", 11000, 520)]
VIDS = {}


def build_s1_fixture(root: Path, brands=None):
    """生成 S1 夹具: 每车型一页厂商页 + 引用的噪声 PNG。返回页数字典。"""
    brands = brands or VEHICLES
    (root / "pages").mkdir(parents=True, exist_ok=True)
    (root / "img").mkdir(parents=True, exist_ok=True)
    pages = {}
    for i, (brand, model, mass, power) in enumerate(brands):
        slug = f"p{i}"
        for suffix, seed in (("hero", 10 + i), ("grille", 20 + i), ("headlamp", 30 + i)):
            (root / "img" / f"{slug}_{suffix}.png").write_bytes(noise_bytes(seed))
        (root / "pages" / f"{slug}.html").write_text(
            PAGE_HTML.format(brand=brand, model=model, slug=slug, mass=mass, power=power),
            encoding="utf-8")
        pages[f"{brand} {model}"] = root / "pages" / f"{slug}.html"
    return pages


def setup():
    global CONN, CHANNEL
    DATA.mkdir(parents=True, exist_ok=True)
    CONN = edb.connect(DATA / "equiplens.db")
    edb.init_db(CONN)
    CONN.executemany("INSERT INTO vocab (id, type, term, status) VALUES (?, 'part', ?, 'active')",
                     [("grille", "进气格栅（含冷却模块进风口）"), ("headlamp", "大灯与灯罩防护"),
                      ("step", "登车踏步")])
    CONN.commit()
    from equiplens import workflow
    for brand, model, *_ in VEHICLES:
        VIDS[f"{brand} {model}"] = workflow.create_vehicle(CONN, brand, model, category="装载机")
    root = TD / "channel_s1"
    build_s1_fixture(root)
    CHANNEL = channels.FixtureChannel(root)


def f01_channel_parse():
    page = CHANNEL.parse_page(VIDS and Path(CHANNEL.root / "pages" / "p0.html"))
    assert page.h1 == "品牌甲 车型X" and "官方产品页" in page.title
    assert len(page.images) == 3 and page.images[0].alt.endswith("左前45度外观官方图")
    assert page.params == {"整备质量": "8800 kg", "额定功率": "460 kW"}
    hits = CHANNEL.find_vehicle_pages("品牌甲 车型X")
    assert len(hits) == 1 and hits[0].h1 == "品牌甲 车型X", "车型名命中恰一页"
    assert CHANNEL.find_vehicle_pages("不存在的车型") == [], "未知车型零命中"


def f02_alt_mapping():
    view, part = channels.map_alt_to_tags("品牌甲 车型X 左前45度外观官方图", CONN)
    assert view == "hero_lf" and part is None
    view, part = channels.map_alt_to_tags("车型X 进气格栅特写", CONN)
    assert view == "detail" and part == "grille", f"alt 部件映射, 实际 {view}/{part}"
    view, part = channels.map_alt_to_tags("车型Y 大灯与灯罩防护特写", CONN)
    assert view == "detail" and part == "headlamp"
    view, part = channels.map_alt_to_tags("一张没有说明的图", CONN)
    assert view == "untagged" and part is None


def r1_run_one():
    plan = retrieval.build_plan({"type": "full", "vehicles": ["品牌甲 车型X"],
                                 "parts": [], "page_types": [{"type": "vehicle_page", "pages": 1}]})
    result = retrieval.execute_plan(CONN, DATA, plan, CHANNEL)
    assert result["reports"][0]["candidates"] == 3, f"1 车型 3 张候选, 实际 {result['reports'][0]}"
    rows = CONN.execute(
        "SELECT a.* FROM assets a JOIN sources s ON s.asset_id=a.id WHERE s.batch_id=?",
        (result["batch_id"],)).fetchall()
    assert len(rows) == 3
    for r in rows:
        # T2: 同页标注型号 → provisional 绑定到该车
        assert r["vehicle_id"] == VIDS["品牌甲 车型X"] and r["binding_status"] == "provisional"
        assert r["binding_evidence"] == "co_occurrence_labeled"
    hero = [r for r in rows if r["view_angle"] == "hero_lf"]
    assert len(hero) == 1, "alt 左前45 → hero_lf"
    parts = {r["part_id"] for r in rows if r["part_id"]}
    assert parts == {"grille", "headlamp"}, f"alt 部位映射, 实际 {parts}"
    src = CONN.execute("SELECT note FROM sources WHERE asset_id = ?",
                       (hero[0]["id"],)).fetchone()["note"]
    assert "同页标注: 品牌甲 车型X" in src and "alt:" in src, "证据链写入来源备注"
    return result


def r1_review_loop():
    batch = CONN.execute("SELECT DISTINCT batch_id FROM sources WHERE batch_id IS NOT NULL"
                         " LIMIT 1").fetchone()["batch_id"]
    out = TD / "review.html"
    info = review.build_review_pack(CONN, DATA, batch, out)
    html = out.read_text(encoding="utf-8")
    assert "机器已挂到本车型" in html and "证据: alt:" in html, "审核包应展示 T2 状态与证据行"
    # 模拟人工: 接受全部候选 (确认对号) 但驳回一张 (错配场景: 人工判定不该收)
    rows = CONN.execute("SELECT a.id FROM assets a JOIN sources s ON s.asset_id=a.id"
                        " WHERE s.batch_id=?", (batch,)).fetchall()
    decisions = {"batch_id": batch, "decisions": [
        {"asset_id": rows[0]["id"], "action": "accept"},
        {"asset_id": rows[1]["id"], "action": "reject", "reason": "实为 Concept 渲染图"},
        {"asset_id": rows[2]["id"], "action": "accept"},
    ]}
    summary = review.apply_review(CONN, decisions, DATA)
    assert summary["rejected"] == 1 and summary["bound"] == 2, f"实际 {summary}"
    confirmed = CONN.execute("SELECT count(*) c FROM assets WHERE binding_status='confirmed'"
                             " AND vehicle_id = ?", (VIDS["品牌甲 车型X"],)).fetchone()["c"]
    assert confirmed == 2, "接受 = provisional→confirmed 且证据升级"
    ev = CONN.execute("SELECT binding_evidence FROM assets WHERE id = ?",
                      (rows[0]["id"],)).fetchone()["binding_evidence"]
    assert ev == "human", "人工接受后证据升级为 human"
    rej = CONN.execute("SELECT confirm_status, notes FROM assets WHERE id = ?",
                       (rows[1]["id"],)).fetchone()
    assert rej["confirm_status"] == "rejected" and "Concept" in rej["notes"]


def r1_rerun_idempotent():
    plan = retrieval.build_plan({"type": "full", "vehicles": ["品牌甲 车型X"],
                                 "parts": [], "page_types": [{"type": "vehicle_page", "pages": 1}]})
    result = retrieval.execute_plan(CONN, DATA, plan, CHANNEL)
    statuses = [s["status"] for s in result["reports"][0]["statuses"]]
    assert all(s in ("merged", "source_exists") for s in statuses), \
        f"重复检索应全部并入/跳过, 实际 {statuses}"
    n = CONN.execute("SELECT count(*) c FROM assets").fetchone()["c"]
    assert n == 3, f"重复检索不得新建素材, 实际 {n}"


def r1_unknown_vehicle():
    plan = retrieval.build_plan({"type": "full", "vehicles": ["品牌丙 幻影车型"],
                                 "parts": [], "page_types": [{"type": "vehicle_page", "pages": 1}]})
    # 名录里没有该车型 → G2 越界防护: 如实报告, 不检索
    result = retrieval.execute_plan(CONN, DATA, plan, CHANNEL)
    assert result["reports"][0]["candidates"] == 0
    assert "名录" in result["reports"][0]["status"]


def r1_full_s1():
    plan = retrieval.build_plan({"type": "full",
                                 "vehicles": [f"{b} {m}" for b, m, *_ in VEHICLES],
                                 "parts": [], "page_types": [{"type": "vehicle_page", "pages": 1}]})
    result = retrieval.execute_plan(CONN, DATA, plan, CHANNEL)
    # 车型X 的图已全部在库(上轮), 其余 3 车型各 3 张新图
    new_candidates = sum(r["candidates"] for r in result["reports"])
    assert new_candidates == 9, f"S1 全量应新增 9 张, 实际 {new_candidates}"
    for name, vid in VIDS.items():
        n = CONN.execute("SELECT count(*) c FROM assets WHERE vehicle_id = ?", (vid,)).fetchone()["c"]
        assert n == 3, f"{name} 应有 3 张, 实际 {n}"
    # 闸门自查: 每张已确认候选的证据链可回答"为什么是这台车"
    rows = CONN.execute(
        """SELECT a.id, s.note FROM assets a JOIN sources s ON s.asset_id=a.id
           WHERE a.vehicle_id IS NOT NULL""").fetchall()
    for r in rows:
        assert "同页标注" in r["note"] and "alt:" in r["note"], f"证据链缺失: {r['id']}"


def main():
    check("F-00 建库+词表+四车型+S1 夹具生成", setup)
    check("F-01 渠道解析: 标题/h1/图片/参数表 + 车型命中", f01_channel_parse)
    check("F-02 alt→视角/部位确定性映射", f02_alt_mapping)
    check("R1-01 单车型检索: 3 候选 T2 挂载+alt 打标+证据链", r1_run_one)
    check("R1-02 审核循环: 接受=确认对号+证据升级, 驳回落账", r1_review_loop)
    check("R1-03 重复检索幂等: 并入/跳过, 零新建", r1_rerun_idempotent)
    check("R1-04 未知车型: 空结果如实呈现(G2)", r1_unknown_vehicle)
    check("R1-05 S1 全量四车型 + 闸门自查(证据链完整)", r1_full_s1)

    fails = [r for r in results if r[1] == "FAIL"]
    w = max(len(n) for n, _, _ in results)
    for name, status, msg in results:
        print(f"{status:4}  {name.ljust(w)}  {msg}")
    print("-" * 78)
    print(f"合计 {len(results)} 项: 通过 {len(results) - len(fails)}, 失败 {len(fails)}")
    shutil.rmtree(TD, ignore_errors=True)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
