"""
算法入参契约——调优（fuzzy）需要哪些字段（接口格式 + 必填等级）

本文件**独立定义**调优的字段字典：字段选哪些、叫什么名、必填到什么程度，
是算法自己的决定，由本算法包自行维护。

命名空间（易错点，务必看清再抄字段名）：
- 本契约的 target_key == ORM 字段名（max_set_injection_speed）。
  依据：本契约描述的是 machine_info / polymer_info / mold_info 三维上下文，
  它的 target_key 就是 ORM 字段名；service 侧按本契约的白名单
  （`source_model` + `attr_name`）从 ORM 提取，不走 `_to_full_dict(InjectionUnit)`
  （那会把 ORM 元数据也传给算法）。
- 【注意】别把 process_parameter 也当成本契约的一部分：工艺参数走的是**另一套**
  命名空间——由算法侧命名契约 `field_names.to_algo_params` 翻译
  （业务 1-based → 算法 0-based，如 `inj_spd_1` → `IV0`），
  见 `process/algorithms/common/field_names.py`。

设备设定上限（max_set_*）是判级论域上界的**必需来源**，不是可选的裁剪参考：
- **标必填**（计量压力 / 计量背压为「液压机必填」：全电机无油缸，HMI 上没有
  这两栏，缺失属物理正常，不能按数据缺失拦人）；缺失 ⇒ 校验器抛 ValueError
  ⇒ service 层转 BizException 400；
- 判级论域 = **下界取 RuleKeyword.range_min（经验域）+ 上界取设备实测值**
  （上限表由 service 层解析好、经 ``context['param_limits']`` 传入）——
  算法层**不知道**参数有没有上下限，只收表；
- 仍兼作**推荐值物理天花板**（裁剪，同一张表）—— 两者同源，
  不是两套互不相干的数据。

【注意】必填与替换**只对必填等级字段生效**：必填字段必须校验并替换，其余字段的
论域可以用默认值。

⇒ 必填等级（`必填` / `液压机必填`）字段：缺失即报错，且论域上界替换成设备实测值；
⇒ 其余字段（`可选` / `推荐`，如保压时间 PT / 料筒温度 BT / 注射位置 IL）：
  论域保持 RuleKeyword 默认域（range_min / range_max），**不动**。
判定入口：:func:`resolve_domain_limits`（论域上界替换）；
「哪些参数参与校验」由 service 层决定（见 `services/shared/param_limits.py`）。

【注意】反过来 `drive_system` **不是必填**：它既不参与论域也不参与裁剪，只用于判定
「液压机必填」这一等级；缺失时按「非液压机」处理（计量类字段一律不要求，
宽松放过 —— 宁可少一项要求，也不误伤液压机）。

【注意】**单位不在算法层考虑**：取的就是界面值，算法侧不需要关心单位。

⇒ 这里取的就是 **HMI 面板显示值**，算法侧**直接用**：不做单位换算、不做单位一致性
校验、也**不在字段描述里断言单位**（ORM 层的 `verbose_name` 声明了单位，那是数据层
的事实，不在算法契约层重复声明 —— 声明了等于替数据层担保，而算法并不保证这一点）。
同理，数值「物理上说不通」（如计量背压 100 而经验域 [10,50]）也**不在算法层做
特殊处理**：脏数据照用，只在引擎层留一条 warning（见 `engine._apply_device_bound`）
—— 现阶段要的是**逻辑正确**，不是数据清洗。

校验机制复用 algorithms/common/field_contract.py（与具体算法无关的纯函数）：
condition 的 5 个等级、「液压机必填」的驱动判定、condition_when 的条件求值，
以及「必填集自动派生」都无需在此重写。各算法字段字典的 entry 结构统一
（source_model / source / attr_name / desc / type / condition），因此 service 层
可以用同一套遍历代码按 (source_model, attr_name) 从 ORM 提取本维度的数据。

调用方（service / 第三方 / CLI）在进算法前调用 OptimizeDataValidator.validate()，
校验失败 raise ValueError，service 层负责转 BizException 400（算法层保持纯净，
不 import 业务异常）。
"""

from typing import Any, Dict, List, Optional, Tuple

# 【注意】**设备上限的「来源声明」归 service 层**（算法层**不知道**
#    参数的上下限）：
#    「哪个参数配哪个设备字段、限值多大」由 service 层声明与组装
#    （`services/shared/param_limits.py`：来源清单 ⇒ 业务键区间表），
#    **取值**（字段存不存在、值多少）同在 service 层，**校验**（越限识别与
#    拒绝）也在 service 层（同文件）。
#    算法层只保留**限值表处理**（`algorithms/fuzzy/device_limits.py` 的
#    `lookup_limit` / `param_family` / `to_family_limits`）
#    —— **纯命名 + 纯查表**，不含任何上下限语义。
#    本模块保留「必填等级」这条口径的**取值**
#    （:func:`resolve_domain_limits`：已解析的族表 → 判级论域上界）。
from .device_limits import param_family

# 【注意】**为什么 import 公共底座**：
#   `specs.py` 属【层 0 对外契约】，而 `common/` 是**比算法包更低一层的零外部依赖
#   公共底座**（不 import 任何算法包 / Django / ORM）⇒ 这是**向底层依赖**，
#   **不是**「反向依赖上层包」。
#   【注意】**此处不依赖 `algorithms/` 门面** ⇒ `algorithms/__init__.py` 为触发
#   AlgorithmRegistry.register 而显式 import 各算法子包时，不会牵连本模块。
#   三个函数（`audit_field_completeness` / `derive_required_fields` /
#   `drive_system_to_power_method`）都是纯函数、无副作用 ⇒ 运行时行为正确。
from ..common.field_contract import (
    audit_field_completeness,
    derive_required_fields,
    drive_system_to_power_method,
)
# 【注意】**物理常量来自中立层**（`algorithms/common/material_physics.py`）：
#    冷却时间 ∝ 最大壁厚²、材料大类系数是**物理事实**，不属于任何算法包的私有口径
#    ⇒ 专家引擎（推导初值）与模糊引擎（标定判级论域）共用同一份，
#    依赖方向恒为「算法包 → algorithms 根」（算法包之间不互相 import）。
from ..common.material_physics import compute_cool_time, parse_material_family
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
    # --- 论域上界：位置类参数（注射位置 IL / 计量位置 ML / 储料终止位置 MEL /
    #     VP 切换位置 VPTL）—— 权威源 = 最大注射行程 ----------------------
    # 【注意】位置类的真实值域远超 RuleKeyword 种子默认域 ⇒ 用经验域会大面积
    #    越界，「充填量第一优先」的那组规则会失活。
    #
    # 【注意】**位置类与压力 / 速度类同构**：判定路径只有一条，差别只在
    #    「上限取自哪个设备字段」⇒ 本字段只声明上限来源。
    #
    # 【注意】condition = 「必填」：行程是这组参数判级论域上界的
    #    **唯一**权威源 ⇒ 缺失 ⇒ 判级区间没有上界 ⇒ 「充填量第一优先」的那组
    #    规则失活 ⇒ **报错**（service 层转 400），**不**回落经验论域。
    #    （引擎层仍保留「回落经验论域」分支，但那是**防御性**的：当前值超行程 /
    #    脏数据，见 ``engine._apply_declared_bound`` —— 正常调优链路走不到那里。）
    "max_injection_stroke": {
        "source_model": "InjectionUnit",
        "source": "InjectionUnit.max_injection_stroke",
        "attr_name": "max_injection_stroke",
        "desc": "最大注射行程 [mm]（螺杆向前推进的最大距离）；位置类参数的"
                "**判级论域上界来源**"
                "（注射位置 / 计量位置 / 储料终止位置 / VP 切换位置"
                "一律以行程为上界）；**必填** —— 缺失即报错（论域上界无法确定）",
        "type": float,
        "condition": "必填",
    },
    "max_set_decompression_pressure": {
        "source_model": "InjectionUnit",
        "source": "InjectionUnit.max_set_decompression_pressure",
        "attr_name": "max_set_decompression_pressure",
        "desc": "最大可设定松退压力（HMI 界面值）；松退压力类**推荐值物理天花板**"
                "（工艺侧无对应可调参数，不参与裁剪）"
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
# mold_info —— 模具维度（规则筛选键 + 制品级物理基准）
# ============================================================================
# 两类内容：
# 1. **规则筛选键**（``product_category``）：规则库精确筛选（specificity 1/3）。
# 2. **制品级物理基准**（壁厚 / 制品重 / 流道 / 浇口）：判级论域的权威源 ——
#    冷却时间 ∝ 最大壁厚²（Fourier 热扩散）⇒ 没有壁厚就没有冷却时间的判级基准
#    （见 :func:`resolve_product_limits`）。
#
# 【注意】**制品级字段来自 Mold 下的关联表**（不是 Mold 主表）：
#    ``GatingSystem``（流道）→ ``Cavity``（型腔）→ ``Gate``（浇口）
#    ⇒ service 层按「逐级取第一个」展开后交给
#    ``services.shared.spec_extract.extract_mold_info``
#    （见 ``services.shared.spec_extract.extract_mold_info``）；某一级缺失 ⇒ 该字段缺失
#    ⇒ 回落经验论域，**不报错、不阻塞**。
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

    # --- 制品级物理基准（Cavity：型腔壁厚）----------------------------
    #     冷却时间（CT）的判级论域上界 = f(最大壁厚, 材料大类)
    #     ⇒ 壁厚是**判级基准的必需输入**，缺失 ⇒ 该参数回落经验域。
    "max_wall_thickness": {
        "source_model": "Cavity",
        "source": "Cavity.max_wall_thickness",
        "attr_name": "max_wall_thickness",
        "desc": "制品最大壁厚 [mm]；**冷却时间（CT）判级论域的物理基准输入**"
                "（冷却时间 ∝ 壁厚²，见 resolve_product_limits）；"
                "缺失 ⇒ 冷却时间回落经验域（不报错、不阻塞）",
        "type": float,
        "condition": "可选",
    },
    "ave_wall_thickness": {
        "source_model": "Cavity",
        "source": "Cavity.ave_wall_thickness",
        "attr_name": "ave_wall_thickness",
        "desc": "制品平均壁厚 [mm]；平均壁厚（后续保压时间基准的候选输入）；"
                "本轮**未被算法消费**（先入契约备查）",
        "type": float,
        "condition": "可选",
    },

    # --- 制品级物理基准（GatingSystem：流道 / 制品总重）---------------
    "total_product_weight": {
        "source_model": "GatingSystem",
        "source": "GatingSystem.total_product_weight",
        "attr_name": "total_product_weight",
        "desc": "制品总重 [g]；充填量基准的候选输入；"
                "本轮**未被算法消费**（先入契约备查）",
        "type": float,
        "condition": "可选",
    },
    "runner_type": {
        "source_model": "GatingSystem",
        "source": "GatingSystem.runner_type",
        "attr_name": "runner_type",
        "desc": "流道类型（冷流道 / 热流道 / ...）；保压时间修正的候选输入；"
                "本轮**未被算法消费**（先入契约备查）",
        "type": str,
        "condition": "可选",
    },

    # --- 制品级物理基准（Gate：浇口类型）------------------------------
    "gate_type": {
        "source_model": "Gate",
        "source": "Gate.gate_type",
        "attr_name": "gate_type",
        "desc": "浇口类型（直浇口 / 侧浇口 / 点浇口 / ...）；保压时间修正的候选输入；"
                "本轮**未被算法消费**（先入契约备查）",
        "type": str,
        "condition": "可选",
    },
}

# ============================================================================
# 缺陷反馈（feedback.defects[]）字段字典
# ============================================================================
#
# 与前三个维度的**结构差异**：这是一个**列表**（每一项缺陷各一份），
# 且有两个字段是**条件必填** —— DEFECTFREE（无缺陷）时前端不展示
# 程度/位置输入框，这两项免校验。
#
# 【注意】「条件必填」用 condition_when 的 `keyword_name__nin` 表达：
#   `eval_condition_when` 只在**同一个 info_dict 内**求值 ⇒ 列表项天然成立
#   （每项在自己的 dict 里评估自己的 keyword_name）。
#
# 【注意】校验口径与**算法的消费口径对齐**（每一条都有算法侧的理由）：
#   - keyword_name 必填  —— 查规则的唯一键，缺了必然查不到规则
#   - level 必填且合法    —— 决定命中哪一套调整方案；非法值放行会导致该缺陷的
#                           规则被全过滤，对外只会报「无可用规则」，
#                           用户看不出是自己填错了
#   - position 必填      —— 缺陷位置（多段成型下用于定位到对应参数段），
#                           算法侧作为 IF 条件变量使用

# 「无缺陷」sentinel keyword 名称（前端合法选项，本身不参与规则匹配）
# 单一真相源：定义在契约层，service 层直接引用这里。
DEFECTFREE_KEYWORD_NAME = "DEFECTFREE"


def _validate_defect_level_value(value: Any, info_dict: Dict[str, Any]) -> Optional[str]:
    """缺陷程度（level）的取值合法性（`value_validator` 钩子）。

    返回错误描述（**不含**「第 N 项缺陷」前缀 —— 那是维度名，由机制统一拼）；
    返回 None 表示合法。

    【注意】词表引用 `VALID_DEFECT_LEVEL_WORDS_TEXT`（定义在本文件后段）——
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
}


def audit_feedback_defects(defects: Any, allow_empty: bool = False) -> List[str]:
    """缺陷反馈列表项的完整性 / 合法性审计（返回问题清单，空 = 通过）。

    与 `OptimizeDataValidator.validate` 的三个维度分开审计：**列表项维度**
    每一项各审一份，问题描述带「第 N 项」。

    【注意】返回清单而不是抛异常 —— 对外文案（`BizException`）由 service 层决定，
    算法层不 import 业务异常（与 `OptimizeDataValidator` 的分工一致）。

    Args:
        defects: 缺陷列表。
        allow_empty: 允许空列表 —— 无缺陷但有主反馈的场景（如产品已合格、
            仍想继续做工艺优化）不应被拦在入口外。
    """
    issues: List[str] = []
    if not isinstance(defects, list) or len(defects) == 0:
        return [] if allow_empty else ['请填写缺陷反馈信息']
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
    """调优算法入参校验器（纯本算法实现，不依赖其它算法包）。

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
# 【注意】职责边界：接口层只负责「输入是不是合法档位词」，**不**负责
#   「规则库有没有这一档」。缺陷档位**不用于筛规则**
#   （library.rules.RuleService.match_defect_name 只比缺陷名，不比档位）——
#   档位已作为**算法输入**进推理网络，由隶属度表达「越严重越激进」；
#   5/7 档独有词（very_low 等）在此语义上完全正确，接口层不该拦。
#   【注意】现网业务已统一收敛到 3 档（RuleKeyword.fuzzy_level 全量 5→3），
#      但**本表保留 5/7 档词**：它是**接口入参**的合法词集合，收窄会让
#      历史客户端（仍传 very_low 等）直接 400，而不是降级处理。
_LEVEL_WORD_DISPLAY_ORDER = (
    'extremely_low', 'very_low', 'low', 'mid', 'medium',
    'high', 'very_high', 'extremely_high',
)


def _build_valid_level_words() -> Tuple[str, ...]:
    """合法档位词（按语义顺序排列，供错误提示展示）。"""
    ordered = [w for w in _LEVEL_WORD_DISPLAY_ORDER if w in ALL_LEVEL_WORDS]
    ordered += sorted(w for w in ALL_LEVEL_WORDS if w not in ordered)
    return tuple(ordered)


VALID_DEFECT_LEVEL_WORDS: Tuple[str, ...] = _build_valid_level_words()


def _build_level_words_text(words: Tuple[str, ...]) -> str:
    """档位词展示文本：把 level1..level7 这类连续编号词折叠为区间。

    不折叠的话提示会变成 15 个词的串（8 个语义词 + 7 个编号词），
    在界面上过长反而看不清重点。
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


def resolve_domain_limits(param_limits: Dict[str, float]) -> Dict[str, float]:
    """已解析的设备上限表 → {算法参数族: 判级论域上界}。

    **按 service 层送来的表取值**：传进来的表**已经由 service 层
    筛好**（`services/shared/param_limits.py` 的来源清单 ⇒ 业务键区间表 ⇒
    算法层 `device_limits.to_family_limits` 翻译出的族表）
    ⇒ 本函数只做「取值 + 转 float」，**不再自己筛等级**。

    ⇒ 「哪些字段参与」的筛选发生在 **service 层**（它才知道哪些字段是必填）：
      必填等级的设备上限缺失 ⇒ 报错（OptimizeDataValidator），
      有值 ⇒ **替换**判级论域上界；
    ⇒ 其余等级（可选 / 推荐）的论域保持 RuleKeyword 默认域
      （range_min / range_max），不动 —— 它们**根本不会进表**。

    【注意】**H1 守卫在引擎层**：设备上限已低于当前设定值时，引擎**不**拿它当
    判级上界（保留经验域 + 留痕 ``kept_experience_domain``）——
    见 ``engine.FuzzyEngine._device_limit_below_current``。

    【注意】**与「推荐值裁剪用的那份上限表」同源**：裁剪
    （``engine._apply_machine_limits``）与论域替换（此处）用的是同一张
    service 送来的表 ⇒ 两者的「哪些族参与」口径天然一致，不会一处改一处不改。

    【注意】**上限表由 service 层解析好传入**（`services/shared/param_limits.py`
    的来源清单 + 算法层 `device_limits.to_family_limits` 的翻译）——
    算法层不碰 ORM 字段名，也不认「哪个参数配哪个字段」。

    Args:
        param_limits: 设备上限表（键 = 算法参数族 → 上限值），
            由 service 层从 ``machine_info`` 解析并按必填等级筛选得到。

    Returns:
        {算法参数族: 论域上界}，如 {'IP': 100.0, 'IV': 80.0}
    """
    limits = param_limits or {}
    domain_limits: Dict[str, float] = {}
    for family, value in limits.items():
        try:
            domain_limits[family] = float(value)
        except (TypeError, ValueError):
            continue
    return domain_limits


# ============================================================================
# 温度类论域 —— 材料温度区间（权威源 = 材料维度）
# ============================================================================
# 温度类的权威源是**材料**，不是设备：
#   - 设备 HMI **不提供**料筒/喷嘴/模具温度的可设上限 ⇒ 温度类没有设备上限字段
#     （service 层的上限来源清单里没有温度族，也是有原因的）；
#   - 材料的熔体/模温区间是**物理红线**：超出即降解 / 变色 / 成型不良。
#
# 【注意】**只列「整段」温度参数，不列分段温度参数**：
#   - `NT` 喷嘴温度 / `BT` 整体料筒温度 / `ET` 下料口温度 = **熔体侧**温度
#   - `MT` 模具温度 = **模温侧**温度
#   - `BT1..BT9` / `MT0..MT19` / `HRT0..HRT49` = **分段加热器设定值**，
#     物理上沿轴向递减（PP 的 `BT1..BT5` = 250/240/227/213/197℃，
#     后段本就低于熔体下限）⇒ 材料熔体区间**不是**它们的权威源；
#     套上去会让后段恒落在论域外 ⇒ 相关规则恒失活（把「可判档」变成「判不出」）。
#
# 【注意】为什么用**显式名单**而不是 `RuleKeyword.keyword_type`：
#   `keyword_type='temperature'` 覆盖 83 个参数（含 79 个分段），但它
#   **区分不了熔体侧与模温侧**（`NT` 与 `MT` 的 keyword_type 完全相同），
#   也区分不了「整段」与「分段」⇒ 用它会把这张表建错。
#   （`keyword_type` 还要改 `adapters.py` / `profiles.py` / `nets.py` 三个核心文件，
#   收益为零 ⇒ 不做。）
TEMPERATURE_DOMAIN_FIELDS: Dict[str, Tuple[str, str]] = {
    # ---- 熔体侧（料筒/喷嘴/下料口都测的是熔体温度）----
    "NT": ("min_melt_temp", "max_melt_temp"),   # 喷嘴温度
    "BT": ("min_melt_temp", "max_melt_temp"),   # 整体料筒温度
    "ET": ("min_melt_temp", "max_melt_temp"),   # 下料口温度
    # ---- 模温侧 ----
    "MT": ("min_mold_temp", "max_mold_temp"),   # 模具温度
}


def resolve_temperature_limits(
    polymer_info: Dict[str, Any],
) -> Dict[str, Tuple[float, float]]:
    """polymer_info → {算法参数名: (论域下界, 论域上界)}（温度类）。

    温度类的**判级基准**取材料温度区间（权威源 = 材料维度，见
    :data:`TEMPERATURE_DOMAIN_FIELDS`）。与 :func:`resolve_domain_limits`
    （设备实测值换论域上界）**分属两套语义**：
    设备回答「机器能设多高」，材料回答「这个料在这个场景下该在什么温度窗口」。

    【注意】**缺权威源不报错、不阻塞**（既定口径：温度类字段的 condition 是「推荐」
    不是「必填」）⇒ 缺值 / 区间倒挂 / 非数值 ⇒ **该参数不产出**，
    调用方据此**回落经验域**（`RuleKeyword.range_min/max`）照常推理。

    Args:
        polymer_info: 材料维度入参（键为 ORM 字段名，如 'min_melt_temp'）

    Returns:
        {算法参数名: (下界, 上界)}，如 ``{'NT': (200.0, 280.0), 'MT': (20.0, 80.0)}``；
        缺权威源的参数**不在返回 dict 里**（调用方按「该参数回落经验域」处理）。
    """
    info = polymer_info or {}
    limits: Dict[str, Tuple[float, float]] = {}
    for param_name, (lo_field, hi_field) in TEMPERATURE_DOMAIN_FIELDS.items():
        raw_lo = info.get(lo_field)
        raw_hi = info.get(hi_field)
        if raw_lo is None or raw_hi is None:
            continue
        try:
            lo = float(raw_lo)
            hi = float(raw_hi)
        except (TypeError, ValueError):
            continue
        if not (lo < hi):
            # 区间倒挂（lo >= hi）⇒ 产出会让论域翻转（档位语义整体颠倒）
            # ⇒ 不产出，由调用方回落经验域。
            continue
        limits[param_name] = (lo, hi)
    return limits


# ============================================================================
# 时间类论域 —— CT 已接产品域；PT / IT / ID 仍回落经验域
# ============================================================================
# 时间类的**正确权威源是「制品级物理推导基准」**，不是设备、不是材料：
#   保压时间 / 冷却时间的合理区间**由制品壁厚决定** —— 厚壁件要保压更久、
#   冷却更久（专家引擎已有这套物理模型，见 ``expert/rule_matcher.py`` 的
#   ``family_gate_freeze_time``（薄/中/厚三桶）+ ``family_cool_factor``
#   （冷却时间 ∝ 最大壁厚²））。
#   ⇒ 制品级数据（型腔壁厚）**已接进模糊引擎的入参契约**
#   （``OPTIMIZE_MOLD_INFO_FIELDS`` 新增 ``max_wall_thickness`` 等 5 项）
#   ⇒ **CT 已接产品域**（见下方 :data:`PRODUCT_DOMAIN_FIELDS`），
#   **PT / IT / ID 仍回落经验域**（判定不划算，理由见下方产品域常量）。
#
# 【注意】**为什么用显式名单而不是 `RuleKeyword.keyword_type`**：
#   `keyword_type='time'`（由 ``init_rule_keyword.py::infer_keyword_type``
#   按「前缀 + 描述」推断）覆盖 **20 个**参数，但其中 9 个
#   （``SCT0..SCT8`` 阀口开启时间 / ``DTAM`` ``DTBM`` 松退时间 / ``MD`` 储料延迟）
#   **在 `field_names.py` 里没有值映射** ⇒ 永远进不了 ``process_parameter``
#   ⇒ **根本不参与判级**，标注它们只会让诊断清单变噪。
#   ⇒ 本表只收「时间类 ∧ **有工艺值来源**」= 11 个（PT0~PT4 / IT / CT / ID）。
#
# 【注意】**名单按「族 + 整段」给，不按参数逐个列**：
#   ``PT`` 是族前缀（保压时间分段 PT0~PT4）；``IT`` / ``CT`` / ``ID`` 是整段。
#   参数级增删不用改本表（新增 PT5 之类的分段会自动命中 ``PT`` 族）。
#
# 【注意】**时间类的经验域双向错位**：
#   时间类是**前件引用最多的族**（合计 **329 次**引用）：
#   ``PT0`` 147 / ``CT`` 93 / ``IT`` 85 / ``PT1`` 4
#   ⇒ 而时间类的经验域**双向错位**：
#   ``CT``[0,120] vs 真实 5~9.5（4.2%~7.9% 分位，恒判最低档）；
#   ``IT``[0,20] vs 真实 1.4~4.75（7%~23.8%）；
#   ``PT0``[0,10] vs 真实 1.88~**60**（18.8%~**600%**，主力值越界）。
#   ⇒ 本表只做「登记 + 可见化」：**精度问题要等产品维度权威源接入**，
#   动它会直接改变推荐输出。
TIME_DOMAIN_FIELDS: Dict[str, str] = {
    "PT": "保压时间（分段：PT0~PT4）",
    "IT": "注射时间",
    "CT": "冷却时间",
    "ID": "注射延迟时间",
}


def is_time_domain_field(param_name: str) -> bool:
    """该参数是否属于**时间类**（仅用于诊断标注，不参与论域替换）。

    【注意】**两级匹配**（时间类既有分段也有整段，与位置类同形）：
    - 整段参数（``CT`` / ``IT`` / ``ID``）→ **精确匹配**；
    - 分段参数（``PT0``~``PT4``）→ **族前缀匹配**
      （族前缀由 :func:`param_family` 的正则取 ⇒ 命名规则仍是单一真相源）。

    Args:
        param_name: 算法侧参数名（如 'PT0' / 'CT' / 'IV0'）

    Returns:
        True 表示是时间类参数
    """
    if not param_name:
        return False
    if param_name in TIME_DOMAIN_FIELDS:
        return True
    family = param_family(param_name)
    if family is None:
        return False
    return family in TIME_DOMAIN_FIELDS


# ============================================================================
# 产品维度论域 —— 制品级物理推导基准（权威源 = 产品维度）
# ============================================================================
# 冷却时间（CT）的**正确权威源是「制品级物理推导基准」**：冷却时间 ∝ 最大壁厚²
# （Fourier 热扩散）⇒ 厚壁件要冷却更久。这套物理模型专家引擎本来就有
# （``expert/rule_matcher.py::_BUILTIN_DEFAULTS['cooling']``），本轮把它抽到
# **中立层** ``algorithms/common/material_physics.py`` ⇒ 两个算法包共用同一份常量，
# 不会出现「专家推导的初值」与「模糊判级的坐标轴」两套口径。
#
# 【注意】**本轮只接 CT 一个参数**（实测判定，其余三个不做）：
#   - ``PT``（保压时间）：接产品域后**区分度恶化**（66.7% → 98.1%），
#     只换来可判率 75.9% → 100% ⇒ 不划算；
#   - ``IT``（注射时间）：缺可靠的产品级基准（充填时间还要流长 + 流量）；
#   - ``ID``（注射延迟时间）：真实值 54/54 全为 0.20 ⇒ 任何论域都恒判同档
#     ⇒ 数学上无解。
#
# 【注意】**下界统一取 0**（与位置类同口径）：时间类的经验下界是**档位语义**、
#   不是物理下限 ⇒ 冷却时间 0 有物理意义（不冷却）。
#
# 【注意】**上界 = 「刚好冷却到位」的物理时间**，不是设备天花板：
#   冷却时间没有机台可设上限（机台 HMI 不提供）⇒ 设备域只对**机台能设上限的
#   参数**（压力 / 速度 / 转速 / 位置）有意义 ⇒ 产品域与设备域**语义不同、
#   不可混用**。
PRODUCT_DOMAIN_FIELDS: Dict[str, str] = {
    "CT": "max_wall_thickness",   # 冷却时间：论域上界 = 制品级物理推导冷却时间
}


def resolve_product_limits(
    mold_info: Dict[str, Any],
    polymer_info: Dict[str, Any],
) -> Dict[str, Tuple[float, float]]:
    """mold_info + polymer_info → {算法参数名: (论域下界, 论域上界)}（产品维度）。

    冷却时间的**判级基准**取「制品最大壁厚 + 材料大类」推导出的物理冷却时间
    （权威源 = 产品维度，见 :data:`PRODUCT_DOMAIN_FIELDS`）。
    与 :func:`resolve_temperature_limits`（材料温度区间）、
    **设备域**（service 层 ``param_limits.build_limits`` —— 机台可设上限）
    **分属三套语义**：
    材料回答「这个料该在什么温度窗口」，设备回答「这台机器最多能设到多少」，
    产品回答「这个件该冷却多久」。

    【注意】**缺权威源不报错、不阻塞**（既定口径：制品级字段的 condition 是「可选」
    而不是「必填」）⇒ 缺壁厚 / 非数值 / 非正数 ⇒ **该参数不产出**，
    调用方据此**回落经验域**（`RuleKeyword.range_min/max`）照常推理。

    【注意】**材料大类识别不出 ⇒ 用默认系数**（`DEFAULT_COOL_FACTOR`），不报错 ——
    与专家引擎 `family_cool_factor_map.get(family, default_cool_factor)` 口径一致；
    **留痕由调用方（engine）负责**（诊断标 ``product_family_unknown``）。

    Args:
        mold_info: 模具维度入参（键为 ORM 字段名，如 'max_wall_thickness'）。
        polymer_info: 材料维度入参（键为 ORM 字段名，如 'abbreviation'）。

    Returns:
        {算法参数名: (下界, 上界)}，如 ``{'CT': (0.0, 15.88)}``；
        缺权威源的参数**不在返回 dict 里**（调用方按「该参数回落经验域」处理）。
    """
    info = mold_info or {}
    polymer = polymer_info or {}
    family = parse_material_family(polymer.get('abbreviation') or '')
    limits: Dict[str, Tuple[float, float]] = {}
    for param_name, field_name in PRODUCT_DOMAIN_FIELDS.items():
        raw = info.get(field_name)
        if raw is None:
            continue
        try:
            thickness = float(raw)
        except (TypeError, ValueError):
            continue
        if thickness <= 0:
            # 壁厚非正 ⇒ 物理上不存在这样的制品 ⇒ 不产出（调用方回落经验域）
            continue
        # 下界统一 0（冷却时间 0 有物理意义：等于不冷却）
        limits[param_name] = (0.0, compute_cool_time(thickness, family))
    return limits


# TODO（论域改造时一并处理）：
# 1. 温度类字段升级为「条件必填」：需先让 field_contract 支持从外部注入触发上下文
#    （如 context["involved_params"]），再按本次是否涉及温度参数决定等级。
#    【注意】温度类**没有设备上限字段**（HMI 不提供料筒/喷嘴/模具温度的可设上限），
#    所以它们的论域**改取材料温度区间**（见 `resolve_temperature_limits`），
#    不再依赖 RuleKeyword 经验域。
# 2. engine.py 的 keyword 兜底分支读本维度的 max_set_*：
#    必须用设备值，设备值没有就报错；判级反映本机真实能力边界是预期行为。
#    max_set_* 同时承担判级论域上界 + 推荐值物理天花板两个角色，同源不冲突。


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
    # 机台物理上限（推荐值裁剪）—— 算法层只做查表，来源声明与取值在 service 层
    "param_family",
    # 判级论域上界（必填等级字段：用设备实测值替换论域上界）
    "resolve_domain_limits",
    # 温度类判级论域（权威源 = 材料温度区间）
    "TEMPERATURE_DOMAIN_FIELDS",
    "resolve_temperature_limits",
    # 时间类（CT 已接产品域；PT / IT / ID 回落经验域）
    "TIME_DOMAIN_FIELDS",
    "is_time_domain_field",
    # 产品类判级论域（权威源 = 制品级物理推导基准）
    "PRODUCT_DOMAIN_FIELDS",
    "resolve_product_limits",
]
