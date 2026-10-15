"""M3 库内检索测试（合成数据, 零模型调用）。

覆盖: 组合过滤各维度与默认排除被拒、授权经来源联动过滤、质量标记过滤、
     同尺寸聚类、感知哈希相似检索、全局文字搜索、词表提名池流转、变体分组与撤销、
     旧库迁移(真实库副本无损升级)。
运行: python tests/test_query.py
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

from PIL import Image  # noqa: E402
import io  # noqa: E402

from equiplens import db as edb  # noqa: E402
from equiplens import ingest, query, workflow  # noqa: E402
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


TD = Path(tempfile.mkdtemp(prefix="eq-m3-"))
DATA = TD / "data"
CONN = None
V1 = V2 = None
A = []


def setup():
    global CONN, V1, V2, A
    DATA.mkdir(parents=True, exist_ok=True)
    CONN = edb.connect(DATA / "equiplens.db")
    edb.init_db(CONN)
    src = TD / "batch"; src.mkdir()
    # 6 张: 3 张 100px(种子1-3), 2 张 64px(种子4-5), 1 张 80px(种子6) → 聚类 (100,100)×3 + (64,64)×2
    sizes = [100, 100, 100, 64, 64, 80]
    for i, s in enumerate(sizes):
        (src / f"n{i}_{s}.png").write_bytes(noise_bytes(i + 1, size=s))
    rep = ingest.ingest_directory(DATA, src, platform="M3测试", license="client_provided", conn=CONN)
    A = [e["asset_id"] for e in rep["imported"]]
    assert len(A) == 6
    CONN.executemany("INSERT INTO vocab (id, type, term, status) VALUES (?, 'part', ?, 'active')",
                     [("grille", "进气格栅"), ("step", "踏步")])
    CONN.commit()
    V1 = workflow.create_vehicle(CONN, "品牌甲", "M-100", category="牵引车")
    V2 = workflow.create_vehicle(CONN, "品牌乙", "M-64", category="装载机")


def q01_filters():
    workflow.bind_asset(CONN, A[0], V1); workflow.set_view(CONN, A[0], "hero_lf")
    workflow.bind_asset(CONN, A[3], V2); workflow.set_view(CONN, A[3], "side_l")
    r = query.query_assets(CONN, view="hero_lf")
    assert [x["id"] for x in r] == [A[0]], "按视角过滤"
    r = query.query_assets(CONN, vehicle_id=V2)
    assert [x["id"] for x in r] == [A[3]], "按车型过滤"
    r = query.query_assets(CONN, binding_status="unbound")
    assert len(r) == 4, "按对号状态过滤"
    r = query.query_assets(CONN, kind="crop")
    assert r == [], "无裁图时 kind 过滤为空"


def q02_rejected_default_excluded():
    workflow.reject_asset(CONN, A[5])
    assert all(x["id"] != A[5] for x in query.query_assets(CONN)), "默认排除被拒"
    assert any(x["id"] == A[5] for x in query.query_assets(CONN, include_rejected=True)), "显式包含被拒"


def q03_license_via_sources():
    # A[1] 补一条第三方来源 → license 过滤命中它
    CONN.execute("INSERT INTO sources (id, asset_id, url, platform, license, is_primary)"
                 " VALUES (?, ?, 'https://x.example/a.png', '论坛', 'web_third_party', 0)",
                 ("s-test-1", A[1]))
    CONN.commit()
    r = query.query_assets(CONN, license="web_third_party")
    assert [x["id"] for x in r] == [A[1]]
    r = query.query_assets(CONN, license="self_captured")
    assert r == []


def q04_quality_flag():
    edb.confirm(CONN, "asset", A[2], "quality_flags", [], ["blur"], "single", "op-flag-1")
    r = query.query_assets(CONN, quality_flag="blur")
    assert [x["id"] for x in r] == [A[2]]
    r = query.query_assets(CONN, quality_flag="watermarked")
    assert r == []


def q05_clusters():
    groups = query.same_dimension_clusters(CONN)
    sizes = sorted((g[0]["width"], len(g)) for g in groups)
    assert sizes == [(64, 2), (100, 3)], f"应得 100×3 与 64×2 两组, 实际 {sizes}"


def q06_similar():
    # 同图缩放对: 种子6(80px) 的 40px 缩版 → 与 A[5]... 注意 A[5] 已被拒, 用 A[4](64px 种子5)
    master = CONN.execute("SELECT id FROM assets WHERE id = ?", (A[4],)).fetchone()
    sub = TD / "batch2"; sub.mkdir()
    (sub / "m.png").write_bytes(noise_bytes(5, size=64))
    small = Image.open(io.BytesIO(noise_bytes(5, size=64))).resize((32, 32), Image.BILINEAR)
    buf = io.BytesIO(); small.save(buf, format="PNG")
    (sub / "t.png").write_bytes(buf.getvalue())
    rep = ingest.ingest_directory(DATA, sub, platform="M3测试", license="client_provided", conn=CONN)
    thumb_id = rep["near_duplicate"][0]["asset_id"]
    hits = query.find_similar(CONN, thumb_id, max_dist=8)
    assert any(r["id"] == A[4] for r, d in hits), "缩放图应检索到其原图"
    hits_from_master = query.find_similar(CONN, A[4], max_dist=8)
    assert any(r["id"] == thumb_id for r, d in hits_from_master), "原图也应检索到缩放图(双向)"
    assert all(d <= 8 for r, d in hits)
    try:
        query.find_similar(CONN, "nonexistent")
        raise AssertionError("不存在素材应报错")
    except ValueError:
        pass


def q07_text_search():
    r = query.text_search(CONN, "M-100")
    assert any(x["id"] == A[0] for x in r), "按车型名命中"
    r = query.text_search(CONN, "n2_100")
    assert any(x["id"] == A[2] for x in r), "按文件名命中"
    r = query.text_search(CONN, "论坛")
    assert any(x["id"] == A[1] for x in r), "按来源平台命中"
    assert all(x["id"] != A[5] for x in query.text_search(CONN, "n5")), "被拒素材默认不出现在搜索"


def q08_vocab_pool():
    tid = query.vocab_add(CONN, "蓄电池箱", note="设计师临时添加")
    assert tid in [v["id"] for v in query.vocab_list(CONN, include_pending=True)]
    assert tid not in [v["id"] for v in query.vocab_list(CONN)], "默认词表不含提名池"
    # pending 词可直接用于裁图打标(FK 不限状态, 检索时可见但标记未受控)
    workflow.set_view(CONN, A[0], "hero_lf")  # 已是 hero_lf, 幂等改标
    workflow.crop_asset(CONN, DATA, A[0], {"x": 10, "y": 10, "w": 40, "h": 40}, tid)
    query.vocab_promote(CONN, tid)
    assert tid in [v["id"] for v in query.vocab_list(CONN)], "提升后进入正式词表"
    query.vocab_retire(CONN, "step")
    assert "step" not in [v["id"] for v in query.vocab_list(CONN)], "退役后不列"
    assert "step" in [v["id"] for v in query.vocab_list(CONN, include_retired=True)]


def q09_variant_group():
    cluster = [g for g in query.same_dimension_clusters(CONN) if g[0]["width"] == 100][0]
    ids = [r["id"] for r in cluster]
    op = workflow.link_variants(CONN, ids)
    group = CONN.execute("SELECT variant_group FROM assets WHERE id = ?", (ids[0],)).fetchone()["variant_group"]
    assert group is not None
    assert all(CONN.execute("SELECT variant_group g FROM assets WHERE id = ?",
                            (i,)).fetchone()["g"] == group for i in ids)
    edb.undo(CONN, op)
    assert all(CONN.execute("SELECT variant_group g FROM assets WHERE id = ?",
                            (i,)).fetchone()["g"] is None for i in ids), "撤销后分组清除"
    workflow.link_variants(CONN, ids)  # 重新归组, 供 CLI 展示
    try:
        workflow.link_variants(CONN, [ids[0]])
        raise AssertionError("单素材不得建组")
    except ValueError:
        pass


def q10_migration_on_real_copy():
    real = edb.connect("data/equiplens.db")
    copy_path = TD / "real_copy.db"
    real2 = edb.connect(copy_path)
    real2.executescript("\n".join(f"{r[0]};" for r in real.execute(
        "SELECT sql FROM sqlite_master WHERE sql IS NOT NULL AND type IN ('table','trigger','index')")))
    for t in ["vocab", "vehicles", "assets", "sources", "facts", "descriptions", "confirm_log"]:
        rows = real.execute(f"SELECT * FROM {t}").fetchall()
        if rows:
            cols = rows[0].keys()
            real2.executemany(f"INSERT INTO {t} ({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})",
                              [tuple(r) for r in rows])
    real2.commit()
    n_before = real2.execute("SELECT count(*) c FROM assets").fetchone()["c"]
    edb.init_db(real2)  # 触发迁移
    cols = {r[1] for r in real2.execute("PRAGMA table_info(assets)")}
    assert "variant_group" in cols, "迁移应补 variant_group 列"
    real2.execute("INSERT INTO vocab (id, type, term) VALUES ('mig-test', 'part', '迁移验证')")
    real2.execute("INSERT INTO confirm_log (id, op_id, object_type, object_id, field,"
                  " machine_value, confirmed_value, method, confirmed_at, confirmed_by)"
                  " VALUES ('miglog1','op-mig','vocab','mig-test','status','pending','active',"
                  "'single','2026-10-12T00:00:00+08:00','user')")
    real2.commit()
    n_after = real2.execute("SELECT count(*) c FROM assets").fetchone()["c"]
    assert n_before == n_after and n_before >= 1, f"迁移不得丢数据, 实际 {n_before}→{n_after}"
    try:
        real2.execute("UPDATE confirm_log SET field='x'")
        raise AssertionError("迁移后 confirm_log 仍应只增不改")
    except sqlite3.IntegrityError:
        pass
    real.close(); real2.close()


check("Q-00 建库+按尺寸导6张+词表+双车型", setup)
check("Q-01 组合过滤: 视角/车型/对号状态/裁图类型", q01_filters)
check("Q-02 被拒素材默认排除、可显式包含", q02_rejected_default_excluded)
check("Q-03 授权过滤经来源记录联动", q03_license_via_sources)
check("Q-04 质量标记过滤(JSON 列)", q04_quality_flag)
check("Q-05 同尺寸聚类: 100×3 与 64×2", q05_clusters)
check("Q-06 感知哈希相似检索(双向)", q06_similar)
check("Q-07 全局文字搜索: 车型/文件名/来源平台", q07_text_search)
check("Q-08 词表提名池: pending→转正/退役流转, pending 可用", q08_vocab_pool)
check("Q-09 变体分组: 归组/整组一致/可撤销/单素材拒绝", q09_variant_group)
check("Q-10 旧库迁移: 真实库副本无损升级+新约束生效", q10_migration_on_real_copy)

fails = [r for r in results if r[1] == "FAIL"]
w = max(len(n) for n, _, _ in results)
for name, status, msg in results:
    print(f"{status:4}  {name.ljust(w)}  {msg}")
print("-" * 78)
print(f"合计 {len(results)} 项: 通过 {len(results) - len(fails)}, 失败 {len(fails)}")
shutil.rmtree(TD, ignore_errors=True)
sys.exit(1 if fails else 0)
