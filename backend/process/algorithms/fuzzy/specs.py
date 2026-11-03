"""
算法入参契约——调优（fuzzy）需要哪些字段（接口格式 + 必填等级）

本文件**独立定义**调优的字段字典：字段选哪些、叫什么名、必填到什么程度，
是算法自己的决定，由本算法包自行维护。

命名空间（易错点，务必看清再抄字段名）：
- 本契约的 target_key == ORM 字段名（max_set_injection_speed）。
  依据：本契约描述的是 machine_info / polymer_info / mold_info 三维上下文，
  它的 target_key 就是 ORM 字段名；service 侧按本契约的白名单
  （`source_model` + `attr_name`）从 ORM 提取，不是直接
  `_to_full_dict(InjectionUnit)`（那是旧做法，会把 ORM 元数据也传给算法）。
- ⚠️ 别把 process_parameter 也当成本契约的一部分：工艺参数走的是**另一套**
  命名空间——由算法侧命名契约 `field_names.to_algo_params` 翻译
  （业务 1-based → 算法 0-based，如 `inj_spd_1` → `IV0`），
  见 `process/algorithms/fuzzy/field_names.py`。

设备设定上限（max_set_*）的定位（2026-10-27 二次修正 · 用户口径）：

第一版把它们定位成「只是推荐值的物理天花板，标可选、不拦请求」，理由是
「判级论域来自 RuleKeyword.range_min / range_max（权威元数据），engine.py 从不读
machine_info 的 max_set_*」。**用户明确推翻这条口径**：
> 「从设备读取参数主要是为了用实际值补全参数的论域」
> 「必须用设备值，设备值没有就报错」

⇒ 设备实际值是**判级论域上界的必需来源**，不是可选的裁剪参考：
- **标必填**（计量压力 / 计量背压为「液压机必填」：全电机无油缸，HMI 上没有
  这两栏，缺失属物理正常，不能按数据缺失拦人）；缺失 ⇒ 校验器抛 ValueError
  ⇒ service 层转 BizException 400；
- 判级论域 = **下界取 RuleKeyword.range_min（经验域）+ 上界取设备实测值**
  （engine 从 context['machine_info'] 取，映射见 PARAM_LIMIT_FIELDS）；
- 仍兼作**推荐值物理天花板**（裁剪，见 PARAM_LIMIT_FIELDS）—— 两者同源，
  不再是两套互不相干的数据。

⚠️ 必填与替换**只对必填等级字段生效**（用户口径）：
> 「我们定义必填的字段，必须校验并且替换，其余字段的论域可以用默认值」

⇒ 必填等级（`必填` / `液压机必填`）字段：缺失即报错，且论域上界替换成设备实测值；
⇒ 其余字段（`可选` / `推荐`，如保压时间 PT / 料筒温度 BT / 注射位置 IL）：
  论域保持 RuleKeyword 默认域（range_min / range_max），**不动**。
判定入口：:func:`is_required_limit_field` / :func:`resolve_domain_limits`。

⚠️ 反过来 `drive_system` **不是必填**：它既不参与论域也不参与裁剪，只用于判定
「液压机必填」这一等级；缺失时按「非液压机」处理（计量类字段一律不要求，
宽松放过 —— 宁可少一项要求，也不误伤液压机）。

⚠️ **单位不在算法层考虑**（用户口径 2026-10-27）：
> 「我们取的就是界面值，不需要关心单位，当然我们也有单位，但是并不需要在算法这里考虑」

⇒ 这里取的就是 **HMI 面板显示值**，算法侧**直接用**：不做单位换算、不做单位一致性
校验、也**不在字段描述里断言单位**（ORM 层的 `verbose_name` 声明了单位，那是数据层
的事实，不在算法契约层重复声明 —— 声明了等于替数据层担保，而算法并不保证这一点）。
同理，数值「物理上说不通」（如计量背压 100 而经验域 [10,50]）也**不在算法层做
特殊处理**：脏数据照用，只在引擎层留一条 warning（见 `engine._apply_device_bound`）
—— 现阶段要的是**逻辑正确**，不是数据清洗。

校验机制复用 algorithms/field_contract.py（与具体算法无关的纯函数）：
condition 的 5 个等级、「液压机必填」的驱动判定、condition_when 的条件求值，
以及「必填集自动派生」都无需在此重写。各算法字段字典的 entry 结构统一
（source_model / source / attr_name / desc / type / condition），因此 service 层
可以用同一套遍历代码按 (source_model, attr_name) 从 ORM 提取本维度的数据。

调用方（service / 第三方 / CLI）在进算法前调用 OptimizeDataValidator.validate()，
校验失败 raise ValueError，service 层负责转 BizException 400（算法层保持纯净，
不 import 业务异常）。
"""

import re
from typing import Any, Dict, List, Optional, Tuple

# ⚠️ **层 0 反向依赖上层包**（2026-10-28 批 L-8 标注，**本轮不改**）：
#   `specs.py` 属【层 0 对外契约】，却 `from ..field_contract import` ⇒
#   层 0 反向依赖上层 `algorithms/` 包 ⇒ 打破「层 0 零依赖」的分层约定。
#
#   ⚠️ **为什么本轮不动**：拆开需要把 `audit_field_completeness` /
#     `derive_required_fields` / `drive_system_to_power_method` 三个纯函数
#     **下沉**到算法包内（或另起层 -1 公共契约模块），会牵动 `algorithms/` 下
#     其它算法包（`empirical` 等同层使用者）⇒ 属**跨包重构**，另开一轮处理。
#
#   ⚠️ **在解决前的定位**：这是**已知的分层瑕疵**，不是 bug —— 三个函数都是纯函数、
#     无副作用、无循环依赖，运行时行为正确 ⇒ 不影响算法结果，只影响分层纯度。
from ..field_contract import (
    audit_field_completeness,
    derive_required_fields,
    drive_system_to_power_method,
)
from .fuzzy_core.macros import ALL_LEVEL_WORDS
from .fuzzy_core.parsing import is_level_word


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
        "desc": "动力系统原始值（液压/电动/...），算法层标准化为 power_method；"
                "**可选** —— 只用于判定「液压机必填」这一等级，不参与论域也不参与裁剪；"
                "缺失时按非液压机处理（计量类字段一律不要求）",
        "type": str,
        "condition": "可选",
    },

    # --- 论域上界：注射 / 保压 / 螺杆转速类规则条件的判级依据 ---
    #     上界 = 设备实测值（缺失即报错）；下界仍取 RuleKeyword.range_min
    "max_set_injection_pressure": {
        "source_model": "InjectionUnit",
        "source": "InjectionUnit.max_set_injection_pressure",
        "attr_name": "max_set_injection_pressure",
        "desc": "最大可设定注射压力（HMI 界面值）；注射压力类**判级论域上界来源**"
                "（缺失即报错）兼**推荐值物理天花板**",
        "type": float,
        "condition": "必填",
    },
    "max_set_injection_speed": {
        "source_model": "InjectionUnit",
        "source": "InjectionUnit.max_set_injection_speed",
        "attr_name": "max_set_injection_speed",
        "desc": "最大可设定注射速度（HMI 界面值）；注射速度类**判级论域上界来源**"
                "（缺失即报错）兼**推荐值物理天花板**",
        "type": float,
        "condition": "必填",
    },
    "max_set_holding_pressure": {
        "source_model": "InjectionUnit",
        "source": "InjectionUnit.max_set_holding_pressure",
        "attr_name": "max_set_holding_pressure",
        "desc": "最大可设定保压压力（HMI 界面值）；保压压力类**判级论域上界来源**"
                "（缺失即报错）兼**推荐值物理天花板**",
        "type": float,
        "condition": "必填",
    },
    "max_set_holding_speed": {
        "source_model": "InjectionUnit",
        "source": "InjectionUnit.max_set_holding_speed",
        "attr_name": "max_set_holding_speed",
        "desc": "最大可设定保压速度（HMI 界面值）；保压速度类**判级论域上界来源**"
                "（缺失即报错）兼**推荐值物理天花板**",
        "type": float,
        "condition": "必填",
    },
    "max_set_screw_rotation_speed": {
        "source_model": "InjectionUnit",
        "source": "InjectionUnit.max_set_screw_rotation_speed",
        "attr_name": "max_set_screw_rotation_speed",
        "desc": "最大可设定螺杆转速（HMI 界面值）；螺杆转速类**判级论域上界来源**"
                "（缺失即报错）兼**推荐值物理天花板**",
        "type": float,
        "condition": "必填",
    },

    # --- 计量类：液压机才有油压（HMI 有「计量压力 / 计量背压」栏）---
    #     全电机无油缸 ⇒ 这两栏物理上不存在 ⇒ 缺失属正常 ⇒ 标「液压机必填」
    "max_set_metering_pressure": {
        "source_model": "InjectionUnit",
        "source": "InjectionUnit.max_set_metering_pressure",
        "attr_name": "max_set_metering_pressure",
        "desc": "最大可设定计量压力（HMI 界面值）；熔胶压力类**判级论域上界来源**"
                "（液压机必填：全电机 HMI 无此栏）兼**推荐值物理天花板**",
        "type": float,
        "condition": "液压机必填",
    },
    "max_set_metering_back_pressure": {
        "source_model": "InjectionUnit",
        "source": "InjectionUnit.max_set_metering_back_pressure",
        "attr_name": "max_set_metering_back_pressure",
        "desc": "最大可设定计量背压（HMI 界面值）；熔胶背压类**判级论域上界来源**"
                "（液压机必填：全电机 HMI 无此栏）兼**推荐值物理天花板**",
        "type": float,
        "condition": "液压机必填",
    },
    "max_set_decompression_pressure": {
        "source_model": "InjectionUnit",
        "source": "InjectionUnit.max_set_decompression_pressure",
        "attr_name": "max_set_decompression_pressure",
        "desc": "最大可设定松退压力（HMI 界面值）；松退压力类**推荐值物理天花板**"
                "（工艺侧无对应可调参数，本批不参与裁剪）"
                "；也不参与判级论域（无对应规则参数族）⇒ 保持可选",
        "type": float,
        "condition": "可选",
    },

    # --- 可选 ---
    # 松退速度对缺陷类规则的判级影响弱（且压力项已覆盖松退过度类缺陷的主要判据）
    "max_set_decompression_speed": {
        "source_model": "InjectionUnit",
        "source": "InjectionUnit.max_set_decompression_speed",
        "attr_name": "max_set_decompression_speed",
        "desc": "最大可设定松退速度（HMI 界面值）；工艺侧无对应可调参数，"
                "不参与裁剪；也不参与判级论域 ⇒ 保持可选",
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

# ============================================================================
# 缺陷反馈（feedback.defect[]）字段字典
# ============================================================================
#
# 与前三个维度的**结构差异**：这是一个**列表**（每一项缺陷各一份），
# 且有两个字段是**条件必填** —— DEFECTFREE（无缺陷）时前端不展示
# 程度/位置输入框，这两项免校验。
#
# ⚠️ 「条件必填」用 condition_when 的 `keyword_name__nin` 表达：
#   `eval_condition_when` 只在**同一个 info_dict 内**求值 ⇒ 列表项天然成立
#   （每项在自己的 dict 里评估自己的 keyword_name）。
#
# ⚠️ 校验口径与**算法的消费口径对齐**（每一条都有算法侧的理由）：
#   - keyword_name 必填  —— 查规则的唯一键，缺了必然查不到规则
#   - level 必填且合法    —— 决定命中哪一套调整方案；非法值放行会导致该缺陷的
#                           规则被全过滤，对外只会报「无可用规则」，
#                           用户看不出是自己填错了
#   - position 必填      —— 缺陷位置（多段成型下用于定位到对应参数段），
#                           算法侧作为 IF 条件变量使用

# 「无缺陷」sentinel keyword 名称（前端合法选项，本身不参与规则匹配）
# 单一真相源：定义在契约层，service 层原先的本地常量已改为从这里取。
DEFECTFREE_KEYWORD_NAME = "DEFECTFREE"


def _validate_defect_level_value(value: Any, info_dict: Dict[str, Any]) -> Optional[str]:
    """缺陷程度（level）的取值合法性（`value_validator` 钩子）。

    返回错误描述（**不含**「第 N 项缺陷」前缀 —— 那是维度名，由机制统一拼）；
    返回 None 表示合法。

    ⚠️ 词表引用 `VALID_DEFECT_LEVEL_WORDS_TEXT`（定义在本文件后段）——
       函数体在**调用时**才求值全局名，模块加载顺序不影响。
    """
    if is_level_word(value):
        return None
    return (
        f"的缺陷程度取值不合法：{value}"
        f"（合法取值：{VALID_DEFECT_LEVEL_WORDS_TEXT}）"
    )


OPTIMIZE_FEEDBACK_FIELDS: Dict[str, Dict[str, Any]] = {
    "keyword_name": {
        "desc": "缺陷类型",
        "type": str,
        "condition": "必填",
        "missing_desc": "未选择缺陷类型（keyword_name 必填）",
    },
    "level": {
        "desc": "缺陷程度",
        "type": str,
        "condition": "条件必填",
        "condition_when": {"keyword_name__nin": [DEFECTFREE_KEYWORD_NAME]},
        "missing_desc": "未选择缺陷程度",
        "value_validator": _validate_defect_level_value,
    },
    "position": {
        "desc": "缺陷位置",
        "type": str,
        "condition": "条件必填",
        "condition_when": {"keyword_name__nin": [DEFECTFREE_KEYWORD_NAME]},
        "missing_desc": "未填写缺陷位置",
    },
    "keyword_id": {
        "desc": "缺陷 ID",
        "type": int,
        "condition": "可选",
    },
    "position_3d": {
        "desc": "缺陷三维位置",
        "type": dict,
        "condition": "可选",
    },
}


def audit_feedback_defects(defects: Any) -> List[str]:
    """缺陷反馈列表项的完整性 / 合法性审计（返回问题清单，空 = 通过）。

    与 `OptimizeDataValidator.validate` 的三个维度分开审计：**列表项维度**
    每一项各审一份，问题描述带「第 N 项」。

    ⚠️ 返回清单而不是抛异常 —— 对外文案（`BizException`）由 service 层决定，
    算法层不 import 业务异常（与 `OptimizeDataValidator` 的分工一致）。
    """
    issues: List[str] = []
    if not isinstance(defects, list) or len(defects) == 0:
        return ['请填写缺陷反馈信息']
    for i, d in enumerate(defects, 1):
        if not isinstance(d, dict):
            issues.append(f"第 {i } 项缺陷格式错误：应为对象")
            continue
        issues.extend(
            audit_field_completeness(d, OPTIMIZE_FEEDBACK_FIELDS, f"第 {i } 项缺陷")
        )
    return issues


# 单一数据源：必填集自动从 condition 派生（不手写第二遍，改 condition 即同步）
REQUIRED_OPTIMIZE_MACHINE_FIELDS = derive_required_fields(OPTIMIZE_MACHINE_INFO_FIELDS)
REQUIRED_OPTIMIZE_POLYMER_FIELDS = derive_required_fields(OPTIMIZE_POLYMER_INFO_FIELDS)
REQUIRED_OPTIMIZE_MOLD_FIELDS = derive_required_fields(OPTIMIZE_MOLD_INFO_FIELDS)


class OptimizeDataValidator:
    """调优算法入参校验器（纯本算法实现，不依赖其它算法包）

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
                "调优入参不完整（设备设定上限缺失 ⇒ 判级论域上界无法确定，"
                "模糊等级会判错、规则命中失真）："
                + "；".join(missing)
            )


# ============================================================================
# 缺陷程度（level）词表契约
# ============================================================================
#
# 判定集合直接取 fuzzy_core.parsing.ALL_LEVEL_WORDS（= is_level_word 的依据），
# 不另起一套——两处真相源必然分叉。
#
# ⚠️ 职责边界：接口层只负责「输入是不是合法档位词」，**不**负责
#   「规则库有没有这一档」。缺陷档位**不再用于筛规则**
#   （library.rules.RuleService.match_defect_name 只比缺陷名，不比档位）——
#   档位已作为**算法输入**进推理网络，由隶属度表达「越严重越激进」；
#   very_low 在此语义上完全正确，接口层不该拦。
_LEVEL_WORD_DISPLAY_ORDER = (
    'extremely_low', 'very_low', 'low', 'mid', 'medium',
    'high', 'very_high', 'extremely_high',
)


def _build_valid_level_words() -> Tuple[str, ...]:
    """合法档位词（按语义顺序排列，供错误提示展示）"""
    ordered = [w for w in _LEVEL_WORD_DISPLAY_ORDER if w in ALL_LEVEL_WORDS]
    ordered += sorted(w for w in ALL_LEVEL_WORDS if w not in ordered)
    return tuple(ordered)


VALID_DEFECT_LEVEL_WORDS: Tuple[str, ...] = _build_valid_level_words()


def _build_level_words_text(words: Tuple[str, ...]) -> str:
    """档位词展示文本：把 level1..level9 这类连续编号词折叠为区间

    不折叠的话提示会变成 17 个词的串，在界面上过长反而看不清重点。
    """
    numbered = [w for w in words if w.startswith('level') and w[5:].isdigit()]
    others = [w for w in words if w not in numbered]
    if numbered:
        others.append(f"{numbered[0]}~{numbered[-1]}")
    return " / ".join(others)


VALID_DEFECT_LEVEL_WORDS_TEXT: str = _build_level_words_text(VALID_DEFECT_LEVEL_WORDS)


def is_valid_defect_level_word(word: Any) -> bool:
    """缺陷程度（level）是否为合法的模糊等级词。

    用途：接口层校验反馈里的 ``level``。非法值（如 '严重' / 'abc'）若放行，
    会走到规则档位过滤时被比不上 → 该缺陷的规则被全过滤 →
    对外表现为「无可用规则」的 400，而不是「档位填错了」。

    Args:
        word: 反馈里的 level 原值（None / 非字符串也安全）

    Returns:
        True 表示是合法档位词
    """
    return is_level_word(word)


# ============================================================================
# 机台物理上限 → 推荐值裁剪（2026-10-27）
# ============================================================================
# 映射表：算法参数**前缀**（不含段号）→ machine_info 里的机台上限字段名。
#
# 为什么键用算法参数名：裁剪发生在算法层，此时参数已是算法命名空间
# （业务名 → 算法名的翻译见 field_names.to_algo_params），业务名在算法层不可见。
#
# 前缀对应关系取自 field_names.FIELD_INDEX_OFFSET 的「业务前缀 ↔ 算法前缀」表：
#   inj_pres→IP / inj_spd→IV / hold_pres→PP / hold_spd→PV
#   met_pres→MP / met_back_pres→MBP / met_rot_spd→MSR
#
# 未列入的参数族没有机台上限（注射位置 IL / 料筒温度 BT / 喷嘴温度 NT / 模温 MT 等），
# 不参与裁剪。
PARAM_LIMIT_FIELDS: Dict[str, str] = {
    "IP":  "max_set_injection_pressure",      # 注射压力
    "IV":  "max_set_injection_speed",         # 注射速度
    "PP":  "max_set_holding_pressure",        # 保压压力
    "PV":  "max_set_holding_speed",           # 保压速度
    "MP":  "max_set_metering_pressure",       # 熔胶（计量）压力
    "MBP": "max_set_metering_back_pressure",  # 熔胶背压
    "MSR": "max_set_screw_rotation_speed",    # 螺杆转速
}

# 算法参数名 = 字母前缀 + 数字段号（IP0 / IV1 / MSR2）。
# 必须带数字后缀：整段参数（IPOS 注射位置 / NT 喷嘴温度 / MT 模温）没有机台上限，
# 也不能被当成某个分段参数的上限。
_ALGO_PARAM_PATTERN = re.compile(r'^([A-Za-z]+)(\d+)$')

# 「必填等级」的 condition 取值（与 field_contract 的等级语义一致）。
# 这两级字段：缺失即报错（由 OptimizeDataValidator 拦），且判级论域上界
# **必须**用设备实测值替换（用户口径 2026-10-27）。
_REQUIRED_CONDITIONS = ('必填', '液压机必填')


def is_required_limit_field(field_name: str) -> bool:
    """该设备上限字段的 condition 是否属**必填等级**。

    「必填等级」= ``必填`` / ``液压机必填``。这两级字段：
    缺失 ⇒ 校验器报错（400）；论域上界 ⇒ 用设备实测值替换。

    单一真相源：直接从字段字典读 condition，不另抄一份名单 ——
    改字段字典的 condition，这里的语义自动跟着变。
    """
    spec = OPTIMIZE_MACHINE_INFO_FIELDS.get(field_name) or {}
    return spec.get('condition', '可选') in _REQUIRED_CONDITIONS


def resolve_domain_limits(machine_info: Dict[str, Any]) -> Dict[str, float]:
    """machine_info → {算法参数前缀: 判级论域上界}（**只含必填等级字段**）

    用户口径（2026-10-27）：
    > 「我们定义必填的字段，必须校验并且替换，其余字段的论域可以用默认值」

    ⇒ 必填等级的设备上限：缺失 ⇒ 报错（OptimizeDataValidator），
      有值 ⇒ **替换**判级论域上界；
    ⇒ 其余字段的论域保持 RuleKeyword 默认域（range_min / range_max），不动。

    与 :func:`resolve_param_limits`（推荐值裁剪用）的区别：
    这里**多一道必填等级过滤** —— 回答的是「这个字段的论域要不要被设备值替换」；
    裁剪那份回答的是「推荐值要不要被封顶」。两者当前取值相同
    （PARAM_LIMIT_FIELDS 的 7 族全是必填等级），但语义不同，分开以免后续
    往 PARAM_LIMIT_FIELDS 里加可选字段时意外改到论域。

    Args:
        machine_info: 机器维度入参（键为 ORM 字段名，如 'max_set_injection_pressure'）

    Returns:
        {算法参数前缀: 论域上界}，如 {'IP': 100.0, 'IV': 80.0}
    """
    info = machine_info or {}
    limits: Dict[str, float] = {}
    for prefix, field_name in PARAM_LIMIT_FIELDS.items():
        if not is_required_limit_field(field_name):
            continue
        value = info.get(field_name)
        if value is None:
            continue
        try:
            limits[prefix] = float(value)
        except (TypeError, ValueError):
            continue
    return limits


def resolve_param_limits(machine_info: Dict[str, Any]) -> Dict[str, float]:
    """machine_info → {算法参数前缀: 机台物理上限值}

    只取 machine_info 里**实际有值**的上限字段。缺失的不补默认值：
    缺上限 ⇒ 该参数不裁剪（由调用方记 warning），
    缺数据不等于不能给建议。

    Args:
        machine_info: 机器维度入参（键为 ORM 字段名，如 'max_set_injection_pressure'）

    Returns:
        {算法参数前缀: 上限值}，如 {'IP': 100.0, 'IV': 80.0}
    """
    info = machine_info or {}
    limits: Dict[str, float] = {}
    for prefix, field_name in PARAM_LIMIT_FIELDS.items():
        value = info.get(field_name)
        if value is None:
            continue
        try:
            limits[prefix] = float(value)
        except (TypeError, ValueError):
            continue
    return limits


def param_family(param_name: str) -> Optional[str]:
    """算法参数名 → 参数族前缀（无族前缀返回 None）

    上限是**按族**给的（``{'IP': 100.0, 'IV': 80.0}``），所以任何要按上限
    判断参数的代码都需要「参数名 → 族」这一步。原先只有
    :func:`lookup_param_limit` 内部用正则取族，**族知识被封在函数里** ——
    需要「只要族、不要上限」时（越限识别）就无从下手。

    暴露这个函数 ⇒ 正则（``^([A-Za-z]+)(\\d+)$``）仍是**单一真相源**：
    修改命名规则只改这一处。

    Args:
        param_name: 算法侧参数名（如 'IP0' / 'IV1' / 'MSR2'）

    Returns:
        族前缀（如 'IP' / 'IV' / 'MSR'）；
        整段参数（'IPOS' / 'NT' / 'MT'，没有数字后缀）没有族 ⇒ 返回 None
    """
    if not param_name:
        return None
    matched = _ALGO_PARAM_PATTERN.match(param_name)
    if not matched:
        return None
    return matched.group(1)


def lookup_param_limit(
    param_name: str,
    limits: Dict[str, float],
) -> Optional[float]:
    """算法参数名 → 该参数的机台物理上限（无上限返回 None）

    Args:
        param_name: 算法侧参数名（如 'IP0' / 'IV1' / 'MSR2'）
        limits: :func:`resolve_param_limits` 的产物

    Returns:
        上限值；该参数没有对应上限时返回 None
    """
    if not param_name or not limits:
        return None
    family = param_family(param_name)
    if family is None:
        return None
    return limits.get(family)


# TODO（论域改造时一并处理）：
# 1. 温度类字段升级为「条件必填」：需先让 field_contract 支持从外部注入触发上下文
#    （如 context["involved_params"]），再按本次是否涉及温度参数决定等级。
#    ⚠️ 温度类**没有设备上限字段**（HMI 不提供料筒/喷嘴/模具温度的可设上限），
#    所以它们的论域仍只能来自 RuleKeyword 权威元数据。
# 2. ~~engine.py 的 keyword 兜底分支改为读本维度的 max_set_*~~ —— 2026-10-27 二次更正：
#    **做**（用户口径：「从设备读取参数主要是为了用实际值补全参数的论域」+
#    「必须用设备值，设备值没有就报错」）。此前"不做"的理由（同一套参数在不同
#    机器上判出不同等级、规则命中行为漂移）已被用户接受为**预期行为** ——
#    判级本来就该反映这台机的真实能力边界。
#    max_set_* 同时承担两个角色（判级论域上界 + 推荐值物理天花板），同源不冲突。
# 3. ~~FromCondition 侧 _extract_machine_unit 不含主表 drive_system~~ —— 已过时：
#    `_extract_machine_info`（services/parameter_optimize.py）已按 source_model
#    跨两张表合并（主表 drive_system + unit 的 max_set_*）。


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
    # 缺陷程度词表契约
    "VALID_DEFECT_LEVEL_WORDS",
    "VALID_DEFECT_LEVEL_WORDS_TEXT",
    "is_valid_defect_level_word",
    # 机台物理上限（推荐值裁剪）
    "PARAM_LIMIT_FIELDS",
    "resolve_param_limits",
    "lookup_param_limit",
    "param_family",
    # 判级论域上界（必填等级字段：用设备实测值替换论域上界）
    "is_required_limit_field",
    "resolve_domain_limits",
]
