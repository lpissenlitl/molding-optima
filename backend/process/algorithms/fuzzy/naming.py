"""命名契约 —— 业务字段名 ↔ 算法字段名 的双向映射。

**零外部依赖**：本模块不 import Django、不 import ORM ⇒ 可独立 import 与验证。

为什么独立成文件
----------------
命名契约是**静态数据**（3 张表 + 1 个反向函数），与引擎的运行时行为
（拉规则 / 推理 / 聚合）完全无关。放在 `FuzzyEngine` 类里，读者要在几十个
行为方法之间找「这个字段到底叫什么」；搬出来后，引擎只管流程，命名只管名字。

三张表的分工
------------
======================================  ======  ==============================
表                                      条数   语义
======================================  ======  ==============================
``PREFIX_FIELD_ALIAS``                  11     分段参数：业务前缀 → 算法前缀
                                                （要拼序号，且序号需按偏移表平移）
``FULL_FIELD_ALIAS``                    12     完整字段名：业务字段名 → 算法字段名
                                                （一对一）
``FIELD_INDEX_OFFSET``                  11     分段参数序号偏移
                                                （见下方「段号基准有两种」）
======================================  ======  ==============================

对外契约（**结构勿改**）
------------------------
``FIELD_NAME_ALIAS`` = 前缀表 + 完整表 的合并（23 条）。
编排层（``process/services/parameter_optimize.py``）直接拿它做键查表翻译，
历史结构保持不变 ⇒ 外部零改动。

⚠️ **段号基准有两种，不能一刀切**
   - **0-based**：注射 / 保压 / 熔胶各段（``inj_spd_1`` → ``IV0``），偏移 -1
   - **1-based**：料筒温度（``brl_temp_1`` → ``BT1``），偏移 0
     （业务侧 ``brl_temp_1..9`` 与规则库 ``BT1..BT9`` 同构）

⚠️ **为什么没有「整段族」映射表**
   早期规则库用单一 ``BT`` 表示整体料筒温度（334 次引用），业务侧却是
   ``brl_temp_1..9`` ⇒ 曾靠一张族表做「段 1 → BT、段 N → BTN」的特殊翻译。
   该写法让 **BT1 段号空缺**（第 1 段占了无号的 BT），实测两处后果：
   - ``BT1``（料筒温度一段，量程 150~350℃）永远拿不到值 ⇒ 相关规则失效；
   - ``BT`` 拿到的是 230~250℃ 的料筒温度，而它的档位区间是 0~50℃ ⇒
     169 条以 ``BT`` 为前件的规则**恒不命中**（内核实测：``BT_low`` 与
     ``BT_high`` 均不命中）。
   现在统一为 **1-based 段号对齐**（``brl_temp_1..9`` ↔ ``BT1..BT9``），
   段号错位与量纲错配一并消失，不再需要族表。

⚠️ **前缀映射必须与偏移表一一对应**
   业务 ``inj_spd_1`` → 算法 ``IV0`` 靠的是「前缀表给出 IV + 偏移表把 1 平移成 0」。
   两张表不同步 ⇒ 段号整体错位（``inj_spd_1`` 变成 ``IV1``，规则匹配不到）。
   故 import 时自检，不一致直接抛错，不留到运行期才发现。
"""

from typing import Dict, Optional


# ============================================================================
# 表 1：分段参数前缀映射（11 条）
#
# 业务字段是 N 个独立段（inj_spd_1..6），规则库侧只认一个前缀 + 段号。
# 段号基准不统一：多数参数业务 1-based → 规则库 0-based，料筒温度则是两边 1-based 同构，
# 详见 FIELD_INDEX_OFFSET。
# ============================================================================

PREFIX_FIELD_ALIAS: Dict[str, str] = {
    # ---- 注射阶段（inj_*_N → IL/IV/IP，前缀映射；算法侧段号 0-based）----
    "inj_pos":  "IL",   # 注射位置 1-6 → IL0-IL5
    "inj_spd":  "IV",   # 注射速度 1-6 → IV0-IV5
    "inj_pres": "IP",   # 注射压力 1-6 → IP0-IP5
    # ---- 保压阶段（hold_*_N → PP/PV/PT，前缀映射；算法侧段号 0-based）----
    # 注意：保压只有压力/速度/时间三组（无位置字段：算法 ML 实际是熔胶位置）
    "hold_pres": "PP",   # 保压压力 1-5 → PP0-PP4
    "hold_spd":  "PV",   # 保压速度 1-5 → PV0-PV4
    "hold_t":    "PT",   # 保压时间 1-5 → PT0-PT4
    # ---- 熔胶阶段（met_*_N → ML/MP/MBP/MSR，前缀映射；算法侧段号 0-based）----
    "met_pos":      "ML",   # 熔胶位置 1-4 → ML0-ML3（算法侧 ML 实际是熔胶位置）
    "met_pres":     "MP",   # 熔胶压力 1-4 → MP0-MP3
    "met_back_pres":"MBP",  # 背压 1-4 → MBP0-MBP3
    "met_rot_spd":  "MSR",  # 螺杆转速 1-4 → MSR0-MSR3
    # ---- 料筒温度（brl_temp_N → BTN，前缀映射；算法侧段号 1-based，与业务同构）----
    "brl_temp":  "BT",   # 料筒温度 1-9 → BT1-BT9（1-based，偏移 0）
}


# ============================================================================
# 表 2：完整字段名映射（12 条）
#
# 一对一映射：业务字段名 → 算法字段名，不带序号。
# （分段参数一律走表 1，此表只放「整段一个值」的参数）
# ============================================================================

FULL_FIELD_ALIAS: Dict[str, str] = {
    # ---- 温度 ----
    "noz_temp":  "NT",   # 喷嘴温度 → NT
    "cool_t":    "CT",   # 冷却时间 → CT
    # ---- 熔胶动作 ----
    "pre_met_decomp_dist":    "DDBM", # 熔胶前松退距离 → DDBM
    "pst_met_decomp_dist":    "DDAM", # 熔胶后松退距离 → DDAM
    "met_end_pos":            "MEL",  # 计量终点位置 → MEL
    # ---- 注射耗时 ----
    "inj_t":     "IT",       # 注射时间 → IT
    "inj_dly_t": "ID",       # 注射延迟 → ID
    # ---- VP 切换 ----
    "vps_mode": "VPTM",      # VP 切换模式 → VPTM
    "vps_pos":  "VPTL",      # VP 切换位置 → VPTL
    "vps_pres": "VPTP",      # VP 切换压力 → VPTP
    "vps_spd":  "VPTV",      # VP 切换速度 → VPTV
    "vps_t":    "VPTT",      # VP 切换时间 → VPTT
}


# ============================================================================
# 表 3：分段参数的序号偏移（11 条）
#
# 事实依据：规则库段号分两套基准
#   - 0-based：注射 / 保压 / 熔胶各段（IV0 719 次 / IV1 38 次 / IV2 15 次），
#     与 RuleKeyword 的 IV0~IV5 / PP0~PP4 完全吻合；而业务字段是 1-based
#     （inj_spd_1..6）⇒ 翻译层统一对齐规则库，偏移 -1。
#   - 1-based：料筒温度（BT1=料筒温度一段 150~350℃），与业务 brl_temp_1..9
#     同构 ⇒ 偏移 0（brl_temp_1 ↔ BT1，不平移）。
#
# 不在表里的前缀偏移为 0（整段参数，不带序号）。
# ============================================================================

FIELD_INDEX_OFFSET: Dict[str, int] = {
    "inj_pos": -1,      # 注射位置 1-6 → IL0-IL5
    "inj_spd": -1,      # 注射速度 1-6 → IV0-IV5
    "inj_pres": -1,     # 注射压力 1-6 → IP0-IP5
    "hold_pres": -1,    # 保压压力 1-5 → PP0-PP4
    "hold_spd": -1,     # 保压速度 1-5 → PV0-PV4
    "hold_t": -1,       # 保压时间 1-5 → PT0-PT4
    "met_pos": -1,      # 熔胶位置 1-4 → ML0-ML3
    "met_pres": -1,     # 熔胶压力 1-4 → MP0-MP3
    "met_back_pres": -1,  # 背压 1-4 → MBP0-MBP3
    "met_rot_spd": -1,  # 螺杆转速 1-4 → MSR0-MSR3
    "brl_temp": 0,      # 料筒温度 1-9 → BT1-BT9（1-based，不平移）
}


# ============================================================================
# 对外契约：合并表（结构与历史一致，编排层按它做键查表翻译）
# ============================================================================

FIELD_NAME_ALIAS: Dict[str, str] = {
    **PREFIX_FIELD_ALIAS,
    **FULL_FIELD_ALIAS,
}


# ============================================================================
# 反向映射：算法字段名 → 业务字段名
# ============================================================================

def to_business_name(algo_name: str) -> Optional[str]:
    """算法字段名 → 业务字段名。

    与「业务 → 算法」的翻译共用同一份声明，保证两向一致：

    - 分段参数（业务 1-based → 规则库 0-based）：``IV0`` → ``inj_spd_1``
    - 分段参数（业务与规则库同构 1-based）：``BT1`` → ``brl_temp_1``
    - 完整字段名：``NT`` → ``noz_temp``、``MEL`` → ``met_end_pos``

    ⚠️ ``BT``（无段号的整体料筒温度）已退役：它不是业务侧任何一个字段，
    本函数对它返回 None ⇒ 编排层会原样保留该算法名，推荐值写不回 baseline。
    规则库若要表达「第一段料筒温度」，请用 ``BT1``（与 ``brl_temp_1`` 一一对应）。

    编排层（``parameter_optimize``）用它把算法推荐写回业务字段：
    算法名与业务字段名不在同一个命名空间，直接覆盖 baseline 必然落空。

    Args:
        algo_name: 算法侧字段名（如 ``IV0`` / ``BT`` / ``NT``）。

    Returns:
        业务字段名；无对应业务字段时返回 None
        （如 ``IPOS`` / ``CUSION`` 这类规则库专用参数，ProcessParameter
        里没有对应列），调用方应原样保留。
    """
    name = (algo_name or '').strip()
    if not name:
        return None

    # 1) 分段参数（IV0 → inj_spd_1；BT1 → brl_temp_1）
    for business_prefix, offset in FIELD_INDEX_OFFSET.items():
        algo_prefix = PREFIX_FIELD_ALIAS.get(business_prefix)
        if not algo_prefix or not name.startswith(algo_prefix):
            continue
        suffix = name[len(algo_prefix):]
        if not suffix.isdigit():
            continue
        return f'{business_prefix}_{int(suffix) - offset}'

    # 2) 完整字段名（NT → noz_temp）
    #    只查完整表 —— 不用「遍历总表再排除前缀」的减法写法，
    #    免得以后新增前缀映射时忘了同步偏移表、把前缀误判成完整字段名。
    for business_key, algo_full in FULL_FIELD_ALIAS.items():
        if algo_full == name:
            return business_key

    return None


# ============================================================================
# import 时自检（不一致直接抛错，不留到运行期）
# ============================================================================

def _validate_tables() -> None:
    """校验三张表自洽。

    前缀表与偏移表必须**一一对应**（key 集合相同）：
    少一条 ⇒ 该参数段号不平移；多一条 ⇒ 该参数段号整体错位。
    """
    prefix_keys = set(PREFIX_FIELD_ALIAS)
    offset_keys = set(FIELD_INDEX_OFFSET)

    missing_offset = sorted(prefix_keys - offset_keys)
    extra_offset = sorted(offset_keys - prefix_keys)
    if missing_offset or extra_offset:
        raise RuntimeError(
            '[naming] 前缀映射与序号偏移表不一致：'
            f'缺偏移 {missing_offset}，多偏移 {extra_offset}。'
            '分段参数翻译会错位（inj_spd_1 会变成 IV1 而不是 IV0）。'
        )


_validate_tables()
