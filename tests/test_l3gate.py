# -*- coding: utf-8 -*-
"""确定性闸门测试（离线）。"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from equiplens import l3gate  # noqa: E402

results = []


def check(name, fn):
    try:
        fn()
        results.append((name, "PASS", ""))
    except Exception as e:  # noqa: BLE001
        results.append((name, "FAIL", str(e)[:160]))


def test_pass_design():
    txt = "前脸采用V字形格栅，线条硬朗，镀铬饰条贯穿，营造出强烈的力量感与家族化识别。"
    r = l3gate.evaluate(txt, title="重卡实拍")
    assert r["pass"], r
    assert r["anchors"]["parts"], r


def test_reject_config_line():
    r = l3gate.evaluate("2024款 2.0T柴油商运版长轴高顶厢货2座D20TCIF1")
    assert not r["pass"] and "config_line" in r["reasons"], r


def test_reject_topic_type():
    r = l3gate.evaluate("工业设计竞赛报名全攻略：选题、组队到答辩的评分策略", title="竞赛攻略")
    assert not r["pass"] and "topic_type" in r["reasons"], r


def test_reject_empty_marketing():
    r = l3gate.evaluate("颜值高，外观大气，科技感强，设计出色，值得拥有。")
    assert not r["pass"], r


def test_reject_passenger_car():
    r = l3gate.evaluate("提车两个月，这台SUV底盘扎实，车主表示很满意，家用足够。")
    assert not r["pass"] and "passenger_car" in r["reasons"], r


def test_reject_enterprise_pr():
    r = l3gate.evaluate(
        "公司入选工信部智能制造试点示范项目，荣获国家级绿色工厂称号，"
        "拥有专利六千余件，构建全产业链体系，品牌价值持续提升。", title="关于我们")
    assert not r["pass"] and "enterprise_pr" in r["reasons"], r


def test_macro_g_pass():
    r = l3gate.evaluate(
        "重卡的造型设计要研究客户需求与市场趋势，未来升级换代将更关注"
        "人性化与家族化设计语言的传承，这决定产品辨识度，也是企业设计能力的一部分。",
        title="浅谈重卡造型设计")
    assert r["pass"] and "macro_analysis" in r["reasons"], r


def test_metrics():
    rows = [{"gate_pass": True, "usable": True}, {"gate_pass": True, "usable": False},
            {"gate_pass": False, "usable": True}, {"gate_pass": False, "usable": False}]
    m = l3gate.metrics(rows)
    assert m["precision"] == 0.5 and m["recall"] == 0.5, m


if __name__ == "__main__":
    check("设计描述通过", test_pass_design)
    check("配置行拒绝", test_reject_config_line)
    check("主题类型拒绝", test_reject_topic_type)
    check("营销空话拒绝", test_reject_empty_marketing)
    check("乘用车口碑拒绝", test_reject_passenger_car)
    check("企业通稿拒绝", test_reject_enterprise_pr)
    check("宏观分析 G 通过", test_macro_g_pass)
    check("指标计算", test_metrics)
    fails = [r for r in results if r[1] == "FAIL"]
    for name, status, err in results:
        print(f"  [{status}] {name}" + (f" — {err}" if err else ""))
    print(f"l3gate: {len(results) - len(fails)}/{len(results)} 通过")
    sys.exit(1 if fails else 0)
