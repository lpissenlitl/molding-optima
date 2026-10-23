"""诊断：模糊推理的**设计层**缺陷（纯算法层，不依赖 Django / DB）

2026-10-22

与 `_dev_refs/diag_fuzzy_pipeline.py` 的分工：
- diag_fuzzy_pipeline.py  = 真实 DB 数据体检（数据量 / 论域 / 命中规则）
- 本脚本                 = 用最小构造数据，把"设计本身对不对"逐条跑成可复现事实

逐条验证：
  A1 缺陷前件是「恒真」还是「恒假」——AND 语义是否丢失
  A2 只有缺陷前件的规则，激活度是不是恒 0（规则完全失活）
  A3 跨参数全局归一化把调整量摊薄多少倍
  A4 fuzzy_level=5 时，规则写的 low/high 命中的是哪个桶
  A5 fuzzy_level=5 + 前件写 very_low / very_high → 是不是直接 KeyError
  A6 fuzzy_level=7 / 9 的情况
  A7 同一规则集下"只有缺陷前件"的规则占比影响（用构造数据说明）

运行：cd backend; ../.venv/Scripts/python.exe _dev_refs/diag_fuzzy_design.py
"""

import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(HERE)
FUZZY_DIR = os.path.join(BACKEND, "process", "algorithms", "fuzzy")
sys.path.insert(0, FUZZY_DIR)

from fuzzy_core.macros import FUZZY_LEVELS, ALL_LEVEL_WORDS
from _legacy_bucket_map import LEGACY_HS_MAPPING_DICT
from fuzzy_core.models.nets import FuzzyFeature, NumTskRuleNet


def hr(title):
    print()
    print("=" * 74)
    print(title)
    print("=" * 74)


def delta_of(net, x, top_k=50):
    """复刻 fuzzy_algorithm._infer_numeric_layer 的 delta 计算。"""
    results, extra = net.predict(x, top_k=top_k)
    out = {}
    for rule_str, activation, adjustments in results:
        for param, value in adjustments.items():
            out.setdefault(param, 0.0)
            out[param] += float(value) * float(activation)
    return out, results


# ===========================================================================
# A1  缺陷前件：恒真 还是 恒假？
# ===========================================================================
def case_a1_defect_precondition():
    hr("A1  缺陷前件是「恒真」还是「恒假」")

    kw = [{"keyword": "IP0", "lvl": 3, "min_val": 0, "max_val": 120, "step": 2}]
    x = {"IP0": 30}

    with_defect = [{"rule_description": "IF ABERRATION_low AND IP0_low THEN IP0_add_2"}]
    without_defect = [{"rule_description": "IF IP0_low THEN IP0_add_2"}]

    net_a = NumTskRuleNet(with_defect, kw, [1.0])
    net_b = NumTskRuleNet(without_defect, kw, [1.0])

    print("规则 A: IF ABERRATION_low AND IP0_low THEN IP0_add_2")
    print("规则 B: IF IP0_low             THEN IP0_add_2")
    print(f"  A 的 connected_matrix 非零元素 = {int((net_a.connected_matrix != 0).sum())} 个")
    print(f"  B 的 connected_matrix 非零元素 = {int((net_b.connected_matrix != 0).sum())} 个")
    print(f"  A 的 pre_set = {net_a.pre_set}")
    print(f"  A 的 pre_dict 键 = {list(net_a.pre_dict.keys())}")

    da, ra = delta_of(net_a, x)
    db, rb = delta_of(net_b, x)
    print(f"\n  A 结果: activation={ra[0][1]:.6f}  delta={da}")
    print(f"  B 结果: activation={rb[0][1]:.6f}  delta={db}")

    if ra[0][1] == rb[0][1]:
        print("\n  >>> 结论：两者激活度完全相同。")
        print("  >>> 缺陷前件被**静默丢弃**（恒真），AND 语义里只剩 IP0_low。")
        print("  >>> 推论：'IF ABERRATION_low AND IP0_low' 与 'IF IP0_low' 在网络层等价，")
        print("  >>>       缺陷在整个模糊推理中**只起『选哪套规则』的作用，没有任何权重语义**。")
    else:
        print(f"\n  >>> 结论：两者激活度不同（{ra[0][1]} vs {rb[0][1]}）。")


# ===========================================================================
# A2  只有缺陷前件的规则 → 激活度恒 0
# ===========================================================================
def case_a2_defect_only_rule():
    hr("A2  只有缺陷前件的规则，激活度是不是恒 0")

    kw = [{"keyword": "IP0", "lvl": 3, "min_val": 0, "max_val": 120, "step": 2}]
    rules = [{"rule_description": "IF SHORTSHOT_high THEN IP0_add_10"}]
    net = NumTskRuleNet(rules, kw, [1.0])

    print("规则: IF SHORTSHOT_high THEN IP0_add_10")
    print(f"  connected_matrix 非零元素 = {int((net.connected_matrix != 0).sum())} 个")
    print(f"  solution_matrix = {net.solution_matrix}")

    d, res = delta_of(net, {"IP0": 30})
    print(f"\n  结果: activation={res[0][1]:.10f}  delta={d}")
    if res[0][1] == 0.0:
        print("\n  >>> 结论：激活度恒 0 —— 这条规则**完全失活**，永远不会产生任何建议。")
        print("  >>> 原因：connected_matrix 全 0 → 没有任何前件能当门控 →")
        print("  >>>       conditions.size == 0 → rule_activations[i] 保持 0。")
        print("  >>> 这类规则在规则库里如果存在，等于不存在。")


# ===========================================================================
# A3  跨参数全局归一化摊薄调整量
# ===========================================================================
def case_a3_global_normalization():
    hr("A3  跨参数全局归一化，把调整量摊薄了多少倍")

    # 主参数 IP0 + N 个干扰参数（各自一条规则，激活度相当）
    n_noise = 8
    rules = [{"rule_description": "IF IP0_low THEN IP0_add_2"}]
    kw = [{"keyword": "IP0", "lvl": 3, "min_val": 0, "max_val": 120, "step": 2}]
    for i in range(n_noise):
        name = f"MBP{i}"
        rules.append({"rule_description": f"IF {name}_low THEN {name}_add_1"})
        kw.append({"keyword": name, "lvl": 3, "min_val": 0, "max_val": 120, "step": 1})

    x = {"IP0": 30}
    for i in range(n_noise):
        x[f"MBP{i}"] = 30

    net = NumTskRuleNet(rules, kw, [1.0] * len(rules))
    d, res = delta_of(net, x)

    print(f"规则数 = {len(rules)}（1 条 IP0 + {n_noise} 条其它参数）")
    print(f"规则写的调整量: IP0_add_2  → 期望 +2.0")
    print(f"实际推出: IP0 = {d.get('IP0'):.6f}")
    ratio = 2.0 / d["IP0"] if d.get("IP0") else float("inf")
    print(f"被摊薄倍数 = {ratio:.1f}×")

    # 对照：只有 IP0 一条规则时
    solo = NumTskRuleNet([{"rule_description": "IF IP0_low THEN IP0_add_2"}], kw[:1], [1.0])
    d_solo, _ = delta_of(solo, {"IP0": 30})
    print(f"\n对照组（只有 IP0 一条规则）: IP0 = {d_solo.get('IP0'):.6f}  ← 等于规则写的 2.0")

    print("\n  >>> 结论：归一化分母是**全部规则**的激活度之和（跨参数共享）。")
    print("  >>> 同一个『注射压力加 2MPa』这条工艺知识，")
    print("  >>> 仅仅因为同批次还命中了别的参数的规则，就被摊薄到 1/9。")
    print("  >>> 规则写的调整量是**工艺知识（绝对量）**，")
    print("  >>> 激活度是**该规则的相对适用强度**，两者相乘 = 语义混淆。")


# ===========================================================================
# A4  fuzzy_level=5 时的档位错位
# ===========================================================================
def case_a4_level_mapping_l5():
    hr("A4  fuzzy_level=5 时，规则写的 low/high 命中的是哪个桶")

    print(f"FUZZY_LEVELS[5] = {FUZZY_LEVELS[5]}")
    print(f"FUZZY_LEVELS[3] = {FUZZY_LEVELS[3]}")
    print(f"LEGACY_HS_MAPPING_DICT 里的档位词 = "
          f"{[k for k in LEGACY_HS_MAPPING_DICT if k not in ('add', 'reduce', 'adjust')]}")
    print()

    for lvl in (3, 5):
        words = FUZZY_LEVELS[lvl]
        ff = FuzzyFeature("IV0", [0, 120], f_level=lvl)
        mem = [ff.get_value_by_level(30, i) for i in range(lvl)]
        print(f"--- fuzzy_level={lvl}（桶序 = {words}）---")
        print(f"    x=30 的隶属度 = {[round(float(m), 4) for m in mem]}")
        for word in ("low", "mid", "medium", "high"):
            if word not in LEGACY_HS_MAPPING_DICT:
                continue
            bucket = LEGACY_HS_MAPPING_DICT[word]
            if bucket >= lvl:
                print(f"    规则前件 IV0_{word:<7} → bucket {bucket}  ← 越界")
                continue
            actual = words[bucket]
            flag = "OK" if actual == word or (
                word == "medium" and actual == "mid") else ">>> 错位"
            print(f"    规则前件 IV0_{word:<7} → bucket {bucket} = {actual:<10} "
                  f"隶属度={float(mem[bucket]):.4f}   {flag}")
        print()


# ===========================================================================
# A5  very_low / very_high → KeyError
# ===========================================================================
def case_a5_very_low_keyerror():
    hr("A5  前件写 very_low / very_high 会发生什么")

    print(f"ALL_LEVEL_WORDS 含 very_low ?  {'very_low' in ALL_LEVEL_WORDS}")
    print(f"LEGACY_HS_MAPPING_DICT 含 very_low ?  {'very_low' in LEGACY_HS_MAPPING_DICT}")
    print()

    # 先看词法层怎么切
    from fuzzy_core.parsing import split_phase
    print("--- 词法层切分（split_phase）---")
    for w in ("IV0_low", "IV0_very_low", "IV0_very_high",
              "IV0_extremely_low", "IV0_mid", "IV0_medium", "IV0_level3"):
        print(f"  {w:<22} -> {split_phase(w)}")
    print()
    print("  >>> 词法层情形 3『从右往左找第一个 level 词，前面的全归 name』")
    print("  >>> very / extremely 被当成**参数名的一部分** → name = 'IV0_very'")
    print()

    print("--- 引擎层后果 ---")
    for word in ("very_low", "very_high", "extremely_low"):
        kw = [{"keyword": "IV0", "lvl": 5, "min_val": 0, "max_val": 120, "step": 2}]
        rules = [{"rule_description": f"IF IV0_{word} THEN IV0_add_2"}]
        try:
            net = NumTskRuleNet(rules, kw, [1.0])
            d, res = delta_of(net, {"IV0": 30})
            print(f"  前件 IV0_{word:<14} → pre_dict 键 = {list(net.pre_dict.keys())}, "
                  f"activation={res[0][1]:.6f}, delta={d}")
        except Exception as e:
            print(f"  前件 IV0_{word:<14} → {type(e).__name__}: {e}")

    print()
    print("  >>> 没有 KeyError（走不到查表那步），但更糟：")
    print("  >>> 参数名变成 'IV0_very' → 查不到 RuleKeyword → 前件被丢弃")
    print("  >>> → connected_matrix 全 0 → 激活度恒 0 → **整条规则静默失活**")
    print("  >>> 结论：5 档 / 7 档 / 9 档在规则串层面**根本无法表达**。")
    print("  >>>      very_low 与 low 写进规则库是同一条规则（都是失活），")
    print("  >>>      区别只在名字上多了一个前缀。")


# ===========================================================================
# A6  fuzzy_level = 7 / 9
# ===========================================================================
def case_a6_level_7_9():
    hr("A6  fuzzy_level = 7 / 9（RuleKeyword 允许这两个值）")

    for lvl in (7, 9):
        words = FUZZY_LEVELS.get(lvl)
        print(f"--- fuzzy_level={lvl} ---")
        print(f"    macros.FUZZY_LEVELS 里有这个档位吗 ?  {words}")
        print(f"    FUZZY_LEVELS 只有键 {sorted(FUZZY_LEVELS.keys())}")
        # 引擎侧靠什么决定桶数？看 FuzzyFeature：桶数 = f_level，与 FUZZY_LEVELS 无关
        ff = FuzzyFeature("IV0", [0, 120], f_level=lvl)
        mem = [ff.get_value_by_level(30, i) for i in range(lvl)]
        print(f"    FuzzyFeature(f_level={lvl}) 建了 {lvl} 个桶，"
              f"x=30 隶属度={[round(float(m), 4) for m in mem]}")
        print(f"    但规则词 low→bucket {LEGACY_HS_MAPPING_DICT['low']}、"
              f"high→bucket {LEGACY_HS_MAPPING_DICT['high']}，"
              f"永远只落在最左 3 个桶")
        print(f"    → 档位 {lvl} 档与引擎的 3 档语义完全脱节")
        print()


# ===========================================================================
# A7  同一缺陷不同档位：三套方案同时命中时会怎样
# ===========================================================================
def case_a7_defect_level_fanout():
    hr("A7  缺陷档位（low/medium/high）三套方案在数值层如何参与")

    print("路由层 RuleQueryService._match_defect_level：")
    print("  - 传了 defect_level → 只保留该档的一套规则")
    print("  - 没传 defect_level → return True，三档规则**全部**进来")
    print()

    kw = [{"keyword": "IP0", "lvl": 3, "min_val": 0, "max_val": 120, "step": 2}]
    rules = [
        {"rule_description": "IF ABERRATION_low AND IP0_low THEN IP0_add_1"},
        {"rule_description": "IF ABERRATION_medium AND IP0_low THEN IP0_add_5"},
        {"rule_description": "IF ABERRATION_high AND IP0_low THEN IP0_add_10"},
    ]
    net = NumTskRuleNet(rules, kw, [1.0] * 3)
    d, res = delta_of(net, {"IP0": 30})
    print("三档规则同时进入数值层：")
    for rule_str, act, _ in res:
        print(f"    activation={act:.6f}  {rule_str}")
    print(f"  累加 delta = {d.get('IP0'):.6f}")
    print()
    print("  >>> 三套『不同工艺方案』被当成三条可叠加的证据直接相加。")
    print("  >>> 缺陷档位本该是**选哪套方案**的开关（或强度系数），")
    print("  >>> 现在的实现里它只在一处生效（路由过滤），且可被绕过。")


def main():
    cases = [
        case_a1_defect_precondition,
        case_a2_defect_only_rule,
        case_a3_global_normalization,
        case_a4_level_mapping_l5,
        case_a5_very_low_keyerror,
        case_a6_level_7_9,
        case_a7_defect_level_fanout,
    ]
    failed = 0
    for fn in cases:
        try:
            fn()
        except Exception:
            print(f"\n[FAIL] {fn.__name__}")
            traceback.print_exc()
            failed += 1
    print()
    print("=" * 74)
    print(f"诊断结束：{len(cases) - failed}/{len(cases)} 个 case 正常执行")
    print("=" * 74)
    return failed


if __name__ == "__main__":
    sys.exit(0 if main() == 0 else 1)
