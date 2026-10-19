"""
算法入参契约——调优（fuzzy）需要哪些字段（接口格式 + 必填等级）

本文件**独立定义**调优的字段字典，不 import expert 的任何契约：
字段选哪些、叫什么名、必填到什么程度，是算法自己的决定。两个算法对同一批
masterdata 字段的依赖强度并不相同，继承别人的字典等于替别人做决定。

命名空间（易错点，务必看清再抄字段名）：
- 本契约的 target_key == ORM 字段名（max_set_injection_speed）。
  依据：FuzzyEngine.FIELD_NAME_ALIAS 是空 dict，即 fuzzy 的端口命名空间就是
  业务/ORM 名；service 侧按本契约的白名单（`source_model` + `attr_name`）
  从 ORM 提取，不是直接 `_to_full_dict(InjectionUnit)`（那是旧做法，
  会把 ORM 元数据也传给算法）。
- expert（initialize）用的是它自己的契约名（max_set_injection_velocity，
  其 attr_name 才指向 ORM 的 max_set_injection_speed）。
- 跨算法抄名字的后果：audit 按 target_key 取值，名字对不上就取不到，
  会把「有数据」误判成「字段缺失」。

为什么设备设定上限要标「必填」（2026-10-15 结论）：
fuzzy 推理的第一步是按当前参数值判定它落在哪个模糊等级——FuzzyFeature 的论域
[min_val, max_val] 就是这个区间，再看规则前件是否命中。上界一旦缺失，算法退回
「当前值×2」自造区间（fuzzy_algorithm.py 的 keyword 兜底分支），后果是：
- 同一套参数在 180MPa 与 350MPa 的两台机上被判成同一模糊等级 → 前件命中失真
- 推荐值可能超出这台机 HMI 能设定的物理范围，操作工根本输不进去
所以「不传设备上限」不是精度略降，而是结论不可信。

校验机制复用 algorithms/field_contract.py（与具体算法无关的纯函数）：
condition 的 5 个等级、「液压机必填」的驱动判定、condition_when 的条件求值，
以及「必填集自动派生」都无需在此重写。字段字典的 entry 结构与 expert 保持一致
（source_model / source / attr_name / desc / type / condition），因此 service 层
可以用同一套遍历代码按 (source_model, attr_name) 从 ORM 提取本维度的数据。

调用方（service / 第三方 / CLI）在进算法前调用 OptimizeDataValidator.validate()，
校验失败 raise ValueError，service 层负责转 BizException 400（算法层保持纯净，
不 import 业务异常）。
"""

from typing import Any, Dict

from ..field_contract import (
    audit_field_completeness,
    derive_required_fields,
    drive_system_to_power_method,
)


# ============================================================================
# machine_info —— 调优的重点维度（设备可设定边界）
# ============================================================================
# 除 drive_system 在 InjectionMoldingMachine 主表外，其余全部来自 InjectionUnit。
# drive_system 是「液压机必填」能否正确评估的前提：全电机无油缸，HMI 上没有
# 「计量压力」输入栏，该字段缺失属物理正常，不能按数据缺失拦人。
OPTIMIZE_MACHINE_INFO_FIELDS: Dict[str, Dict[str, Any]] = {
    "drive_system": {
        "source_model": "InjectionMoldingMachine",
        "source": "InjectionMoldingMachine.drive_system",
        "attr_name": "drive_system",
        "desc": "动力系统原始值（液压/电动/...），算法层标准化为 power_method",
        "type": str,
        "condition": "必填",
    },

    # --- 论域上界：注射 / 保压 / 螺杆转速类规则条件的判级依据 ---
    "max_set_injection_pressure": {
        "source_model": "InjectionUnit",
        "source": "InjectionUnit.max_set_injection_pressure",
        "attr_name": "max_set_injection_pressure",
        "desc": "最大可设定注射压力 [MPa]（HMI）；注射压力类论域上界",
        "type": float,
        "condition": "必填",
    },
    "max_set_injection_speed": {
        "source_model": "InjectionUnit",
        "source": "InjectionUnit.max_set_injection_speed",
        "attr_name": "max_set_injection_speed",
        "desc": "最大可设定注射速度 [mm/s]（HMI）；注射速度类论域上界",
        "type": float,
        "condition": "必填",
    },
    "max_set_holding_pressure": {
        "source_model": "InjectionUnit",
        "source": "InjectionUnit.max_set_holding_pressure",
        "attr_name": "max_set_holding_pressure",
        "desc": "最大可设定保压压力 [MPa]（HMI）；保压压力类论域上界",
        "type": float,
        "condition": "必填",
    },
    "max_set_holding_speed": {
        "source_model": "InjectionUnit",
        "source": "InjectionUnit.max_set_holding_speed",
        "attr_name": "max_set_holding_speed",
        "desc": "最大可设定保压速度 [mm/s]（HMI）；保压速度类论域上界",
        "type": float,
        "condition": "必填",
    },
    "max_set_screw_rotation_speed": {
        "source_model": "InjectionUnit",
        "source": "InjectionUnit.max_set_screw_rotation_speed",
        "attr_name": "max_set_screw_rotation_speed",
        "desc": "最大可设定螺杆转速 [rpm]（HMI）；螺杆转速类论域上界",
        "type": float,
        "condition": "必填",
    },

    # --- 液压机必填（全电机 HMI 无对应输入栏，缺失属正常）---
    "max_set_metering_pressure": {
        "source_model": "InjectionUnit",
        "source": "InjectionUnit.max_set_metering_pressure",
        "attr_name": "max_set_metering_pressure",
        "desc": "最大可设定计量压力 [MPa]（HMI，仅液压机有该输入栏）",
        "type": float,
        "condition": "液压机必填",
    },
    "max_set_metering_back_pressure": {
        "source_model": "InjectionUnit",
        "source": "InjectionUnit.max_set_metering_back_pressure",
        "attr_name": "max_set_metering_back_pressure",
        "desc": "最大可设定计量背压 [MPa]（HMI，仅液压机有该输入栏）",
        "type": float,
        "condition": "液压机必填",
    },
    "max_set_decompression_pressure": {
        "source_model": "InjectionUnit",
        "source": "InjectionUnit.max_set_decompression_pressure",
        "attr_name": "max_set_decompression_pressure",
        "desc": "最大可设定松退压力 [MPa]（HMI，仅液压机有该输入栏）",
        "type": float,
        "condition": "液压机必填",
    },

    # --- 可选 ---
    # 松退速度对缺陷类规则的判级影响弱（且压力项已覆盖松退过度类缺陷的主要判据）
    "max_set_decompression_speed": {
        "source_model": "InjectionUnit",
        "source": "InjectionUnit.max_set_decompression_speed",
        "attr_name": "max_set_decompression_speed",
        "desc": "最大可设定松退速度 [mm/s]（HMI）",
        "type": float,
        "condition": "可选",
    },
}


# ============================================================================
# polymer_info —— 材料维度（规则筛选键 + 温度边界）
# ============================================================================
# 温度类字段全部标「推荐」而非「必填」，原因不是不重要，而是 field_contract 的
# condition_when 只能对**本维度内**的键求值，而温度类字段的触发条件在维度外
# （本次调优是否涉及 brl_temp_ / noz_temp，取决于匹配到的规则前件）。
# 若强行标必填，纯做压力类调优也会被拦——过度约束。
# 待论域改造落地时，由 service 侧按 involved_params 追加校验（见文末 TODO）。
OPTIMIZE_POLYMER_INFO_FIELDS: Dict[str, Dict[str, Any]] = {
    "abbreviation": {
        "source_model": "Polymer",
        "source": "Polymer.abbreviation",
        "attr_name": "abbreviation",
        "desc": "材料简称（ABS/PP/PC+ABS/...）；规则库精确筛选键（specificity 1/2）。"
                "精度旋钮：填了能命中高特异度规则，不填退到默认规则，算法不报"
                "缺这个值而无法运行",
        "type": str,
        "condition": "可选",
    },

    # --- 熔体温度边界（料筒/喷嘴推荐值的物理上界来自材料，不来自机器）---
    "min_melt_temp": {
        "source_model": "Polymer",
        "source": "Polymer.min_melt_temp",
        "attr_name": "min_melt_temp",
        "desc": "最小熔体温度 [℃]；温度的 0 无物理意义，故下限需真实数据，"
                "不能像压力/速度那样统一按 0 处理",
        "type": float,
        "condition": "推荐",
    },
    "max_melt_temp": {
        "source_model": "Polymer",
        "source": "Polymer.max_melt_temp",
        "attr_name": "max_melt_temp",
        "desc": "最大熔体温度 [℃]；超此值材料降解/变色，是温度类推荐的实际天花板",
        "type": float,
        "condition": "推荐",
    },
    "recommended_melt_temp": {
        "source_model": "Polymer",
        "source": "Polymer.recommended_melt_temp",
        "attr_name": "recommended_melt_temp",
        "desc": "推荐熔体温度 [℃]",
        "type": float,
        "condition": "推荐",
    },

    # --- 模温边界 ---
    "min_mold_temp": {
        "source_model": "Polymer",
        "source": "Polymer.min_mold_temp",
        "attr_name": "min_mold_temp",
        "desc": "最小模具温度 [℃]",
        "type": float,
        "condition": "推荐",
    },
    "max_mold_temp": {
        "source_model": "Polymer",
        "source": "Polymer.max_mold_temp",
        "attr_name": "max_mold_temp",
        "desc": "最大模具温度 [℃]",
        "type": float,
        "condition": "推荐",
    },
    "recommended_mold_temp": {
        "source_model": "Polymer",
        "source": "Polymer.recommended_mold_temp",
        "attr_name": "recommended_mold_temp",
        "desc": "推荐模具温度 [℃]",
        "type": float,
        "condition": "推荐",
    },
}


# ============================================================================
# mold_info —— 模具维度（调优只需两项）
# ============================================================================
# 调优不消费模具几何（浇口/壁厚/流长是初始化的推导输入）。
#
# 未来候选（本期未纳入，需成对使用才有意义）：
# - projected_area（在 GatingSystem 表，按 shot_index 选）
#   + 机台 max_clamping_force（在 InjectionMoldingMachine 主表）
#   → 飞边类推荐的压力上界。两者跨两张表，单独取其一无法算出所需锁模力。
OPTIMIZE_MOLD_INFO_FIELDS: Dict[str, Dict[str, Any]] = {
    "product_category": {
        "source_model": "Mold",
        "source": "Mold.product_category",
        "attr_name": "product_category",
        "desc": "产品大类（如 '空调' / '酒瓶'）；规则库精确筛选键（specificity 1/3）。"
                "精度旋钮：填了能命中高特异度规则，不填退到默认规则",
        "type": str,
        "condition": "可选",
    },
    "target_cycle_time": {
        "source_model": "Mold",
        "source": "Mold.target_cycle_time",
        "attr_name": "target_cycle_time",
        "desc": "目标成型周期 [s]；判断能否用周期换质量",
        "type": float,
        "condition": "可选",
    },
}

# 单一数据源：必填集自动从 condition 派生（不手写第二遍，改 condition 即同步）
REQUIRED_OPTIMIZE_MACHINE_FIELDS = derive_required_fields(OPTIMIZE_MACHINE_INFO_FIELDS)
REQUIRED_OPTIMIZE_POLYMER_FIELDS = derive_required_fields(OPTIMIZE_POLYMER_INFO_FIELDS)
REQUIRED_OPTIMIZE_MOLD_FIELDS = derive_required_fields(OPTIMIZE_MOLD_INFO_FIELDS)


class OptimizeDataValidator:
    """调优算法入参校验器（与 expert 的 DataValidator 同定位，各自实现互不依赖）

    位置：算法层入口。任何调用方（service / 第三方 / CLI）进 fuzzy 前都必须过这里，
    因此必填约束不依赖 pydantic schema，也不依赖某个具体 View。

    Usage:
        OptimizeDataValidator.validate(machine_info, polymer_info, mold_info)

    Raises:
        ValueError: 存在「必填 / 液压机必填」未满足的字段。
                    算法层不抛业务异常，由 service 层转 BizException 400。
    """

    @staticmethod
    def validate(
        machine_info: Dict[str, Any],
        polymer_info: Dict[str, Any],
        mold_info: Dict[str, Any],
    ) -> None:
        machine_info = machine_info or {}
        polymer_info = polymer_info or {}
        mold_info = mold_info or {}

        # 「液压机必填」等级依赖驱动形式：算法层负责 drive_system → power_method
        power_method = drive_system_to_power_method(machine_info.get("drive_system"))
        is_hydraulic = power_method == "液压机"

        missing = []
        for dim, info, spec in (
            ("machine_info", machine_info, OPTIMIZE_MACHINE_INFO_FIELDS),
            ("polymer_info", polymer_info, OPTIMIZE_POLYMER_INFO_FIELDS),
            ("mold_info", mold_info, OPTIMIZE_MOLD_INFO_FIELDS),
        ):
            missing.extend(
                audit_field_completeness(info, spec, dim, is_hydraulic=is_hydraulic)
            )

        if missing:
            raise ValueError(
                "调优入参不完整（论域上界缺失会使模糊等级判错、规则命中失真）："
                + "；".join(missing)
            )


# TODO（论域改造时一并处理，本次只钉契约）：
# 1. 温度类字段升级为「条件必填」：需先让 field_contract 支持从外部注入触发上下文
#    （如 context["involved_params"]），再按本次是否涉及温度参数决定等级。
# 2. fuzzy_algorithm.py 的 keyword 兜底分支（min_val=0, max_val=当前值×2）改为
#    读本维度的 max_set_* / max_*_temp，让论域真正等于设备与材料的物理边界。
# 3. utils/translate.py 已有未被使用的 ranges_provider 钩子，是第 2 点的现成接缝。
# 4. FromCondition 侧：_extract_machine_unit 目前只取 InjectionUnit，不含主表的
#    drive_system；接校验前需按 source_model 跨两张表合并（同 initialize 的
#    _build_machine_info 做法）。


__all__ = [
    # 字段定义
    "OPTIMIZE_MACHINE_INFO_FIELDS",
    "OPTIMIZE_POLYMER_INFO_FIELDS",
    "OPTIMIZE_MOLD_INFO_FIELDS",
    # 派生（自动从 condition 推导）
    "REQUIRED_OPTIMIZE_MACHINE_FIELDS",
    "REQUIRED_OPTIMIZE_POLYMER_FIELDS",
    "REQUIRED_OPTIMIZE_MOLD_FIELDS",
    # 校验
    "OptimizeDataValidator",
]
