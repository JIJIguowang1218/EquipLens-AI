# -*- coding: utf-8 -*-
"""车型标识规范测试：第一段/第二段共用的 canon/primary/matching。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

from equiplens import identity  # noqa: E402

results = []


def check(name, fn):
    try:
        fn()
        results.append((name, "PASS", ""))
    except Exception as e:  # noqa: BLE001
        results.append((name, "FAIL", str(e)[:200]))


def test_primary_code_basic():
    assert identity.primary_code("HF 8066 6×6 重型越野底盘").full == "HF8066"
    assert identity.primary_code("KAMAZ K-65959").full == "K65959"
    assert identity.primary_code("XS265HS 单钢轮压路机").full == "XS265HS"
    assert identity.primary_code("Hyster RS45 正面吊").full == "RS45"
    assert identity.primary_code("CPD50-B 电动四轮叉车").full == "CPD50"  # 连字符后视为变体后缀
    assert identity.primary_code("诺力 FE4P25N 电动叉车").full == "FE4P25N"
    assert identity.primary_code("ZZ4257V455GF1").full == "ZZ4257V455GF1"
    assert identity.primary_code("John Deere 6170R").full == "6170R"


def test_parenthetical_not_identity():
    # 括号内是底盘/备注，不能当主身份
    assert identity.primary_code("华通牌HCQ5083TSLJX5扫路车（江铃凯锐N800）").full.startswith("HCQ5083")
    tok = identity.primary_code("RS45（B921）")
    assert tok and tok.full == "RS45", tok


def test_spec_not_code():
    for bad in ("4X2 消防车", "8方 搅拌车", "340Hp 牵引车", "3.0T 叉车",
                "18吨 卡车", "6×6 越野牵引头"):
        assert identity.primary_code(bad) is None, bad


def test_validate_model_code():
    for good in ("HF 8066", "K-65959", "CPD50-B", "RS45", "TGM18.290B6", "FE4P25N"):
        assert identity.validate_model_code(good), good
    for bad in ("4X2", "8方", "340Hp", "FE系列", "G6", "3.0T", "18吨", "VNX"):
        assert not identity.validate_model_code(bad), bad


def test_match_space_hyphen_short_digits():
    assert identity.code_in_title("HF 8066 6×6 重型越野底盘",
                                  "mol hf 8066 6x6越野底盘实拍")
    assert identity.code_in_title("KAMAZ K-65959", "kazma k65959 自卸车")
    assert identity.code_in_title("Hyster RS45 正面吊", "海斯特 rs45 正面吊交付")
    assert identity.code_in_title("CPD50-B 电动叉车", "合力 cpd50 电动叉车")


def test_match_suffix_tolerated():
    assert identity.code_in_title("XS265HS 单钢轮压路机", "徐工 XS265 压路机")
    assert identity.code_in_title("XS202", "徐工 XS202JE 压路机")
    assert identity.code_in_title("TGM18.290B6 4×2 泡沫消防车", "曼恩 tgm.18.290 消防车")


def test_match_rejects_variant_and_number_extension():
    assert not identity.code_in_title("TGM18.290B6 4×2 泡沫消防车", "曼恩 tgm18.320 消防车")
    assert not identity.code_in_title("XS265 压路机", "徐工 XS2650 压路机")
    assert not identity.code_in_title("华通 HCQ5083TSLJX5（江铃凯锐N800）", "江铃凯锐N800中体")
    assert not identity.code_in_title("RS45（B921）", "B921RR 配件报价")
    assert not identity.code_in_title("John Deere 6170R", "6170元 二手车")


def test_flexible_spacing_in_match():
    # 标题写法与车名写法不一致也应命中（空格/点/大小写）
    assert identity.code_in_title("TGM18.290B6", "曼恩 TGM 18.290 消防车")
    assert identity.code_in_title("HF8066", "MOL HF-8066 底盘")


def test_power_and_body_suffix():
    # 功率/规格尾部不是型号
    assert identity.primary_code("HOWO 371HP 全驱越野牵引车（6×6）") is None
    assert identity.code_in_title("HOWO 371HP 全驱越野牵引车", "sinotruk howo 371马力 6*4 牵引车") is False
    # 长尾部（上装编码）必须整串匹配：EQ5253JSQZM ≠ EQ5253CCYF2
    assert identity.code_in_title("东风EQ5253JSQZM随车起重运输车", "东风 EQ5253CCYF2 仓栅载货车") is False
    assert identity.code_in_title("东风EQ5253JSQZM随车起重运输车", "东风EQ5253JSQZM 随车吊") is True
    # 长尾部不退化：XS265JSIV ≠ XS265
    assert identity.code_in_title("XS265JSIV 压路机", "徐工 XS265 压路机") is False
    assert identity.code_in_title("XS265JSIV 压路机", "徐工 XS265JSIV 压路机") is True


def test_parenthetical_fallback():
    # 括号外没有码时，允许括号内列出的型号（北奔写法）
    tok = identity.primary_code("北奔沙漠车（ND5180TSMZ01/ND5140TSMZ02）")
    assert tok and tok.full.startswith("ND5180"), tok
    assert identity.code_in_title("北奔沙漠车（ND5180TSMZ01/ND5140TSMZ02）",
                                  "nd5180tsmz01 沙漠车参数") is True


if __name__ == "__main__":
    check("主码抽取", test_primary_code_basic)
    check("括号内不算主身份", test_parenthetical_not_identity)
    check("规格/构型不是码", test_spec_not_code)
    check("model_code 校验", test_validate_model_code)
    check("空格/连字符/短码匹配", test_match_space_hyphen_short_digits)
    check("尾部后缀容忍", test_match_suffix_tolerated)
    check("变体与数字延伸拒绝", test_match_rejects_variant_and_number_extension)
    check("分隔符容错", test_flexible_spacing_in_match)
    check("功率/上装尾部规则", test_power_and_body_suffix)
    check("括号内码兜底", test_parenthetical_fallback)
    fails = [r for r in results if r[1] == "FAIL"]
    for name, status, err in results:
        print(f"  [{status}] {name}" + (f" — {err}" if err else ""))
    print(f"identity: {len(results) - len(fails)}/{len(results)} 通过")
    sys.exit(1 if fails else 0)
