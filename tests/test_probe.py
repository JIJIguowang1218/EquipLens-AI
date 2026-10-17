"""判向探针 v2 单测：质心/留一/镜像法纯合成, DB 取数用内存库——全程不碰模型。"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np

from equiplens import db, probe


def _seed(n_per_class: int) -> tuple[np.ndarray, list[str]]:
    """三类完全分开的合成特征（类中心正交, 噪声极小）。"""
    rng = np.random.default_rng(7)
    centers = {"hero_lf": [1.0, 0.0, 0.0], "hero_rf": [0.0, 1.0, 0.0],
               "side_l": [0.0, 0.0, 1.0]}
    feats, labels = [], []
    for c, v in centers.items():
        for _ in range(n_per_class):
            f = np.asarray(v) + rng.normal(0, 0.01, 3)
            feats.append(f / np.linalg.norm(f))
            labels.append(c)
    return np.asarray(feats), labels


class TestCentroidProbe(unittest.TestCase):
    def test_fit_predict_separated(self):
        feats, labels = _seed(5)
        cents = probe.fit_centroids(feats, labels)
        self.assertEqual(set(cents), {"hero_lf", "hero_rf", "side_l"})
        for f, l in zip(feats, labels):
            self.assertEqual(probe.predict_one(f, cents)["view"], l)

    def test_predict_margin_and_scores(self):
        feats, labels = _seed(3)
        cents = probe.fit_centroids(feats, labels)
        r = probe.predict_one(feats[0], cents)
        self.assertIn("margin", r)
        self.assertGreater(r["margin"], 0)
        self.assertEqual(len(r["scores"]), 3)

    def test_loo_perfect_on_separated(self):
        feats, labels = _seed(6)
        rep = probe.loo_eval(feats, labels)
        self.assertEqual(rep["accuracy"], 1.0)
        self.assertEqual(rep["errors"], [])
        self.assertEqual(rep["per_class"], {"hero_lf": "6/6", "hero_rf": "6/6",
                                            "side_l": "6/6"})

    def test_loo_catches_outlier(self):
        feats, labels = _seed(6)
        feats = feats.tolist()
        labels = list(labels)
        # 伪造一条 hero_lf 样本实际落在 hero_rf 类中心附近
        feats[0] = [0.0, 1.0, 0.0]
        rep = probe.loo_eval(feats, labels)
        self.assertLess(rep["accuracy"], 1.0)
        self.assertTrue(any(e["true"] == "hero_lf" and e["pred"] == "hero_rf"
                            for e in rep["errors"]))

    def test_mirror_flip_to_side_r(self):
        feats, labels = _seed(6)
        cents = probe.fit_centroids(feats, labels)
        # 略偏离 side_l 类中心 [0,0,1] 的特征（cos≈0.958）
        f = np.asarray([0.3, 0.0, 1.0]) / np.linalg.norm([0.3, 0.0, 1.0])
        # 翻转图更贴近 side_l 质心（cos≈0.995）→ 判 side_r
        flip = np.asarray([0.1, 0.0, 1.0]) / np.linalg.norm([0.1, 0.0, 1.0])
        r = probe.predict_direction(f, flip, cents)
        self.assertEqual(r["view"], "side_r")
        self.assertIn("mirror", r)
        # 原图更像 → 维持 side_l
        flip2 = np.asarray([0.0, 0.6, 0.8]) / np.linalg.norm([0.0, 0.6, 0.8])
        r2 = probe.predict_direction(f, flip2, cents)
        self.assertEqual(r2["view"], "side_l")
        self.assertNotIn("mirror", r2)

    def test_mirror_sanity_counts(self):
        feats, labels = _seed(6)
        # 翻转特征取远离 side_l 的向量 → 9 条 side_l 全部一致
        flips = np.zeros_like(feats)
        flips[:, 1] = 1.0  # hero_rf 方向
        rep = probe.mirror_sanity(feats, flips, labels, cls="side_l")
        self.assertEqual(rep, {"n": 6, "consistent": 6})

    def test_unknown_backend_raises(self):
        with self.assertRaises(ValueError):
            probe.get_backend("nope")


class TestMirrorAugment(unittest.TestCase):
    """镜像增广: 翻转图的视角标签取镜像（hero_lf 翻转 = hero_rf, 物理成立）。"""

    def _norm(self, v):
        v = np.asarray(v, dtype=float)
        return v / np.linalg.norm(v)

    def test_fit_creates_side_r_from_flips(self):
        rng = np.random.default_rng(3)
        feats = np.asarray([self._norm([1, 0.1, 0]) + rng.normal(0, .01, 3)
                            for _ in range(4)])
        labels = ["side_l"] * 4
        flips = np.asarray([self._norm([0.1, 1, 0]) + rng.normal(0, .01, 3)
                            for _ in range(4)])  # 翻转图像 side_r
        cents = probe.fit_centroids_mirror(feats, flips, labels)
        self.assertEqual(set(cents), {"side_l", "side_r"})  # side_r 无中生有

    def test_symmetric_predict_two_sided_evidence(self):
        cents = {"hero_lf": self._norm([1, 0.2, 0]), "hero_rf": self._norm([0.2, 1, 0]),
                 "front": self._norm([0.9, 0.9, 0])}
        # 原图像 hero_lf, 翻转图像 hero_rf —— 两侧证据一致 → hero_lf
        r = probe.predict_symmetric(self._norm([1, 0.25, 0]),
                                    self._norm([0.25, 1, 0]), cents)
        self.assertEqual(r["view"], "hero_lf")
        # 翻转图不像 hero_rf（证据矛盾）→ 不再盲目押 hero_lf
        r2 = probe.predict_symmetric(self._norm([1, 0.25, 0]),
                                     self._norm([0.95, 0.95, 0]), cents)
        self.assertNotEqual(r2["view"], "hero_lf")

    def test_loo_mirror_rescues_single_sample_class(self):
        # 5 条 hero_lf + 1 条 hero_rf: 普通留一下 rf 类质心消失必错;
        # 镜像增广后 rf 类有 5 份翻转样本 → 全对
        feats = np.asarray([self._norm([1, 0, 0])] * 5 + [self._norm([0, 1, 0])])
        flips = np.asarray([self._norm([0, 1, 0])] * 5 + [self._norm([1, 0, 0])])
        labels = ["hero_lf"] * 5 + ["hero_rf"]
        plain = probe.loo_eval(feats, labels)
        mirror = probe.loo_eval_mirror(feats, flips, labels)
        self.assertEqual(plain["accuracy"], round(5 / 6, 4))
        self.assertEqual(mirror["accuracy"], 1.0)


class TestDbQueries(unittest.TestCase):
    def setUp(self):
        self.conn = db.connect(":memory:")
        db.init_db(self.conn)
        self.conn.execute(
            "INSERT INTO vehicles (id, brand, model_name, list_status, created_at,"
            " updated_at) VALUES ('v1','解放','J7','locked','2026-10-15','2026-10-15')")
        for i, (view, vb) in enumerate([("hero_lf", "provisional"),
                                        ("hero_45", "provisional"),
                                        ("side_l", "provisional"),
                                        ("rear", "provisional")]):
            self.conn.execute(
                "INSERT INTO assets (id, vehicle_id, binding_status, binding_evidence,"
                " kind, file_path, view_angle, asset_nature, confirm_status, hash_sha256,"
                " phash, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (f"a{i}", "v1", vb, "co_occurrence_labeled", "source_image",
                 f"assets/x{i}.jpg", "untagged", "real_photo", "machine_tagged",
                 str(i).zfill(64), str(i).zfill(16), "2026-10-15", "2026-10-15"))
        recs = [  # (asset, op_id, method, value, at)
            ("a0", "op-hash1", "single", "hero_lf", "2026-10-16T10:00:00"),
            ("a1", "op-view-1", "batch", "hero_45", "2026-10-15T10:00:00"),
            ("a2", "op-probe-20261016", "batch", "side_l", "2026-10-16T11:00:00"),
            ("a3", "op-view-2", "batch", "rear", "2026-10-15T10:00:00"),
        ]
        for j, (oid, op, m, val, at) in enumerate(recs):
            self.conn.execute(
                "INSERT INTO confirm_log (id, op_id, object_type, object_id, field,"
                " machine_value, confirmed_value, method, confirmed_at, confirmed_by)"
                " VALUES (?,?,?,?,?,?,?,?,?,?)",
                (f"c{j}", op, "asset", oid, "view_angle",
                 json.dumps("untagged"), json.dumps(val), m, at, "user"))

    def tearDown(self):
        self.conn.close()

    def test_latest_view_records(self):
        latest = probe._latest_view_records(self.conn)
        self.assertEqual(latest["a0"], {"value": "hero_lf", "method": "single",
                                        "op_id": "op-hash1"})
        self.assertEqual(latest["a1"]["value"], "hero_45")

    def test_load_labeled_only_single_direction(self):
        labeled = probe.load_labeled(self.conn)
        self.assertEqual([x["asset_id"] for x in labeled], ["a0"])
        self.assertEqual(labeled[0]["label"], "hero_lf")

    def test_probe_targets_transitional_and_v1(self):
        targets = probe.probe_targets(self.conn)
        ids = {t["asset_id"] for t in targets}
        self.assertEqual(ids, {"a1", "a2"})  # 过渡态 hero_45 + v1 定向 side_l
        self.assertNotIn("a0", ids)         # 人工值不复查
        self.assertNotIn("a3", ids)         # 机器终态 rear 不在本轮范围
        reasons = {t["asset_id"]: t["reason"] for t in targets}
        self.assertEqual(reasons["a1"], "过渡态待定向")
        self.assertEqual(reasons["a2"], "v1 探针定向待复查")


if __name__ == "__main__":
    unittest.main()
