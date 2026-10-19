"""
算法入参契约——算法需要哪些字段（接口格式 + 必填项）

字段定义集中放在算法层（单一来源），避免 service / 算法两边重复。
- source_model: ORM 模型类名（如 Mold / GatingSystem / Cavity / Gate / InjectionUnit / InjectionMoldingMachine / Polymer）
- source: 人类可读的来源描述（含计算表达式 / 或运算时的主路径）
- attr_name: ORM 属性名（计算字段时为 None，service 层特殊处理）
- desc: 业务描述
- type: 类型
- condition: 必填等级（必填 / 液压机必填 / 条件必填 / 推荐 / 可选）
- condition_when: 条件必填的触发条件字典

调用方（service / 第三方 / CLI）通过 DataValidator 统一校验，
保证算法入参符合接口契约，缺失字段由 MaterialDatabase 智能兜底。
"""

from typing import Any, Dict, Tuple

from ..field_contract import (
    audit_field_completeness,
    derive_required_fields,
    drive_system_to_power_method,
)


# ---- Machine 设备级字段 ----
# ① 大部分字段来自 InjectionUnit
# ② drive_system 来自 InjectionMoldingMachine（算法层负责 drive_system → power_method 转换）
MACHINE_INFO_FIELDS: Dict[str, Dict[str, Any]] = {
    # ① 动力系统（来自 Machine 主表，算法层负责 drive_system → power_method 标准化）
    'drive_system': {
        'source_model': 'InjectionMoldingMachine',  # ← Machine 主表（不是 InjectionUnit）
        'source': 'InjectionMoldingMachine.drive_system',
        'attr_name': 'drive_system',  # ORM 字段名是 drive_system
        'desc': '动力系统原始值（液压/电动/...），算法层自动标准化为 power_method',
        'type': str,
        'condition': '必填',  # algorithm 用于判断液压机特需字段
    },
    # ② 喷嘴与螺杆参数
    'nozzle_type': {
        'source_model': 'InjectionUnit',
        'source': 'InjectionUnit.nozzle_type',
        'attr_name': 'nozzle_type',
        'desc': '喷嘴类型（直通型/锁定型/...）',
        'type': str,
        'condition': '必填',  # algorithm _validate_inputs 检查
    },
    'screw_diameter': {
        'source_model': 'InjectionUnit',
        'source': 'InjectionUnit.screw_diameter',
        'attr_name': 'screw_diameter',
        'desc': '螺杆直径 [mm]',
        'type': float,
        'condition': '必填',  # algorithm _validate_inputs + total_len 计算
    },

    # ② 塑化与注射能力（设备极限）
    'max_injection_stroke': {
        'source_model': 'InjectionUnit',
        'source': 'InjectionUnit.max_injection_stroke',
        'attr_name': 'max_injection_stroke',
        'desc': '最大注射行程 [mm]',
        'type': float,
        'condition': '可选',
    },
    'max_injection_pressure': {
        'source_model': 'InjectionUnit',
        'source': 'InjectionUnit.max_injection_pressure',
        'attr_name': 'max_injection_pressure',
        'desc': '最大注射压力 [MPa]（设备极限）',
        'type': float,
        'condition': '可选',
    },
    'max_injection_velocity': {
        'source_model': 'InjectionUnit',
        'source': 'InjectionUnit.max_injection_speed',  # ORM 用 _speed（不是 _velocity）
        'attr_name': 'max_injection_speed',
        'desc': '最大注射速度 [mm/s]（设备极限）',
        'type': float,
        'condition': '可选',
    },
    'max_holding_pressure': {
        'source_model': 'InjectionUnit',
        'source': 'InjectionUnit.max_holding_pressure',
        'attr_name': 'max_holding_pressure',
        'desc': '最大保压压力 [MPa]（设备极限）',
        'type': float,
        'condition': '可选',
    },
    'max_holding_velocity': {
        'source_model': 'InjectionUnit',
        'source': 'InjectionUnit.max_holding_speed',  # ORM 用 _speed
        'attr_name': 'max_holding_speed',
        'desc': '最大保压速度 [mm/s]（设备极限）',
        'type': float,
        'condition': '可选',
    },
    'max_screw_rotation_speed': {
        'source_model': 'InjectionUnit',
        'source': 'InjectionUnit.max_screw_rotation_speed',
        'attr_name': 'max_screw_rotation_speed',
        'desc': '最大螺杆转速 [rpm]（设备极限）',
        'type': float,
        'condition': '可选',
    },
    'max_metering_back_pressure': {
        'source_model': 'InjectionUnit',
        'source': 'InjectionUnit.max_metering_back_pressure',
        'attr_name': 'max_metering_back_pressure',
        'desc': '最大计量背压 [MPa]',
        'type': float,
        'condition': '可选',
    },
    'max_decompression_velocity': {
        'source_model': 'InjectionUnit',
        'source': 'InjectionUnit.max_decompression_speed',  # ORM 用 _speed
        'attr_name': 'max_decompression_speed',
        'desc': '最大松退速度 [mm/s]',
        'type': float,
        'condition': '可选',
    },

    # ②+ 液压机特需（设备极限）
    # 说明：这两个字段原标「液压机必填」，但算法层（algorithm_engine 等）完全未引用，
    #        仅为 InjectionUnit 的「设备能力描述」，并不参与工艺推导。
    #        保留在 spec 是为了前端能编辑/展示，但不应阻塞初始化推理。
    'max_metering_pressure': {
        'source_model': 'InjectionUnit',
        'source': 'InjectionUnit.max_metering_pressure',
        'attr_name': 'max_metering_pressure',
        'desc': '最大计量压力 [MPa]（液压机设备能力描述，算法未使用）',
        'type': float,
        'condition': '可选',
    },
    'max_decompression_pressure': {
        'source_model': 'InjectionUnit',
        'source': 'InjectionUnit.max_decompression_pressure',
        'attr_name': 'max_decompression_pressure',
        'desc': '最大松退压力 [MPa]（液压机设备能力描述，算法未使用）',
        'type': float,
        'condition': '可选',
    },

    # ③ HMI 可设定范围（操作界面限制）
    'max_set_injection_pressure': {
        'source_model': 'InjectionUnit',
        'source': 'InjectionUnit.max_set_injection_pressure',
        'attr_name': 'max_set_injection_pressure',
        'desc': '最大可设定注射压力 [MPa]（HMI）',
        'type': float,
        'condition': '必填',
    },
    'max_set_injection_velocity': {
        'source_model': 'InjectionUnit',
        'source': 'InjectionUnit.max_set_injection_speed',  # ORM 用 _speed
        'attr_name': 'max_set_injection_speed',
        'desc': '最大可设定注射速度 [mm/s]（HMI）',
        'type': float,
        'condition': '必填',
    },
    'max_set_holding_pressure': {
        'source_model': 'InjectionUnit',
        'source': 'InjectionUnit.max_set_holding_pressure',
        'attr_name': 'max_set_holding_pressure',
        'desc': '最大可设定保压压力 [MPa]（HMI）',
        'type': float,
        'condition': '必填',
    },
    'max_set_holding_velocity': {
        'source_model': 'InjectionUnit',
        'source': 'InjectionUnit.max_set_holding_speed',  # ORM 用 _speed
        'attr_name': 'max_set_holding_speed',
        'desc': '最大可设定保压速度 [mm/s]（HMI）',
        'type': float,
        'condition': '必填',
    },
    'max_set_screw_rotation_speed': {
        'source_model': 'InjectionUnit',
        'source': 'InjectionUnit.max_set_screw_rotation_speed',
        'attr_name': 'max_set_screw_rotation_speed',
        'desc': '最大可设定螺杆转速 [rpm]（HMI）',
        'type': float,
        'condition': '必填',
    },
    'max_set_metering_back_pressure': {
        'source_model': 'InjectionUnit',
        'source': 'InjectionUnit.max_set_metering_back_pressure',
        'attr_name': 'max_set_metering_back_pressure',
        'desc': '最大可设定计量背压 [MPa]（HMI）',
        'type': float,
        'condition': '液压机必填',
    },
    'max_set_decompression_velocity': {
        'source_model': 'InjectionUnit',
        'source': 'InjectionUnit.max_set_decompression_speed',  # ORM 用 _speed
        'attr_name': 'max_set_decompression_speed',
        'desc': '最大可设定松退速度 [mm/s]（HMI）',
        'type': float,
        'condition': '可选',
    },

    # ③+ 液压机特需（HMI 可设定范围）
    'max_set_metering_pressure': {
        'source_model': 'InjectionUnit',
        'source': 'InjectionUnit.max_set_metering_pressure',
        'attr_name': 'max_set_metering_pressure',
        'desc': '最大可设定计量压力 [MPa]（HMI）',
        'type': float,
        'condition': '液压机必填',
    },
    'max_set_decompression_pressure': {
        'source_model': 'InjectionUnit',
        'source': 'InjectionUnit.max_set_decompression_pressure',
        'attr_name': 'max_set_decompression_pressure',
        'desc': '最大可设定松退压力 [MPa]（HMI）',
        'type': float,
        'condition': '液压机必填',
    },
}


# ---- Polymer 材料级字段 ----
POLYMER_INFO_FIELDS: Dict[str, Dict[str, Any]] = {
    'abbreviation': {
        'source_model': 'Polymer',
        'source': 'Polymer.abbreviation',
        'attr_name': 'abbreviation',
        'desc': '材料缩写（ABS/PP/PC+ABS/...）',
        'type': str,
        'condition': '必填',  # algorithm 多处使用 + 材料分支
    },
    'category': {
        'source_model': 'Polymer',
        'source': 'Polymer.category',
        'attr_name': 'category',
        'desc': '材料类型（结晶型/无定形/...）',
        'type': str,
        'condition': '可选',
    },
    'recommend_melt_temperature': {
        'source_model': 'Polymer',
        'source': 'Polymer.recommended_melt_temp',  # ORM 用 _temp（不是 _temperature）
        'attr_name': 'recommended_melt_temp',
        'desc': '推荐成型温度 [℃]',
        'type': float,
        'condition': '必填',  # algorithm 默认 250
    },
    'recommend_shear_linear_speed': {
        'source_model': 'Polymer',
        'source': 'Polymer.recommended_shear_line_speed',  # ORM 用 _line（不是 _linear）
        'attr_name': 'recommended_shear_line_speed',
        'desc': '推荐剪切线速度 [mm/s]',
        'type': float,
        'condition': '必填',  # algorithm 默认 160
    },
    'recommend_back_pressure': {
        'source_model': 'Polymer',
        'source': 'Polymer.recommend_back_pressure',
        'attr_name': 'recommend_back_pressure',
        'desc': '推荐背压 [MPa]',
        'type': float,
        'condition': '必填',  # algorithm 默认 10.0
    },
    'recommend_mold_temperature': {
        'source_model': 'Polymer',
        'source': 'Polymer.recommended_mold_temp',  # ORM 用 _temp
        'attr_name': 'recommended_mold_temp',
        'desc': '推荐模具温度 [℃]',
        'type': float,
        'condition': '必填',  # algorithm 默认 0
    },
    'ejection_temperature': {
        'source_model': 'Polymer',
        'source': 'Polymer.ejection_temp',  # ORM 用 _temp
        'attr_name': 'ejection_temp',
        'desc': '顶出温度 [℃]',
        'type': float,
        'condition': '可选',
    },
    'melt_density': {
        'source_model': 'Polymer',
        'source': 'Polymer.melt_density',
        'attr_name': 'melt_density',
        'desc': '熔体密度 [g/cm³]',
        'type': float,
        'condition': '必填',  # algorithm 默认 0.95
    },
}


# ---- mold_info 字段完整性标准（多源：Mold / GatingSystem / Cavity / Gate） ----
# spec: { source_model, source, attr_name, desc, type, condition, condition_when }
#   - source_model: ORM 模型类名，service 层据此查 snapshot[model] 取模型实例
#   - source: 人类可读的来源描述（可含计算/或运算）
#   - attr_name: ORM 属性名（计算字段时为 None，service 层特殊处理）
#   - condition: "必填" / "液压机必填" / "条件必填" / "可选" / "推荐"
#   - condition_when: 条件必填的触发条件字典
# service 层 _build_mold_info_from_snapshot 按 (source_model, attr_name) 通用提取，
# 特殊 case（如 Gate.outer_diameter / 2）针对字段写代码处理
MOLD_INFO_SPEC: Dict[str, Dict[str, Any]] = {
    # ---- Mold ORM 主表字段 ----
    'product_type': {
        'source_model': 'Mold',
        'source': 'Mold.product_type',
        'attr_name': 'product_type',
        'desc': '制品类型（历史字段，algorithm 未使用）',
        'type': str,
        'condition': '可选',
    },
    'shot_count': {
        'source_model': 'Mold',
        'source': 'Mold.shot_count',
        'attr_name': 'shot_count',
        'desc': '注射次数（多色成型），1=单次，2=两次',
        'type': int,
        'condition': '可选',
    },
    'inject_cycle_require': {
        'source_model': 'Mold',
        'source': 'Mold.target_cycle_time',  # ORM 用 target_cycle_time（不是 inject_cycle_require）
        'attr_name': 'target_cycle_time',
        'desc': '目标成型周期 [s]（用于推导冷却时间）',
        'type': float,
        'condition': '可选',
    },

    # ---- GatingSystem 关联字段 ----
    'runner_weight': {
        'source_model': 'GatingSystem',
        'source': 'GatingSystem.runner_weight (or estimated_runner_weight)',
        'attr_name': 'runner_weight',
        'desc': '流道重量 [g]（热流道可不填/0）',
        'type': float,
        # 条件必填：runner_type 不是「热流道」时才必填（冷流道/热转冷都有凝料）
        # 物理依据：热流道系统流道内塑料始终保持熔融态，无凝料 → 重量 = 0 / N/A
        'condition': '条件必填',
        'condition_when': {'runner_type__nin': ['热流道']},
    },
    'product_weight': {
        'source_model': 'GatingSystem',
        'source': 'GatingSystem.total_product_weight',
        'attr_name': 'total_product_weight',  # ORM 用 total_ 前缀
        'desc': '制品总重量 [g]',
        'type': float,
        'condition': '必填',  # algorithm 注射量 + 冷却时间
    },
    'runner_type': {
        'source_model': 'GatingSystem',
        'source': 'GatingSystem.runner_type',
        'attr_name': 'runner_type',
        'desc': '流道类型（热流道/冷流道/热转冷）',
        'type': str,
        'condition': '必填',  # 决定 runner_weight 是否必填（热流道不强制）
    },

    # ---- Cavity 关联字段 ----
    'max_thickness': {
        'source_model': 'Cavity',
        'source': 'Cavity.max_wall_thickness',  # ORM 用 max_ 壁厚，不是 max_thickness
        'attr_name': 'max_wall_thickness',
        'desc': '制品最大壁厚 [mm]',
        'type': float,
        'condition': '必填',  # algorithm 冷却时间 + 保压
    },
    'ave_thickness': {
        'source_model': 'Cavity',
        'source': 'Cavity.ave_wall_thickness',  # ORM 用 ave_
        'attr_name': 'ave_wall_thickness',
        'desc': '制品平均壁厚 [mm]',
        'type': float,
        'condition': '必填',  # algorithm 冷却 + 保压 + 注塑
    },
    'max_length': {
        'source_model': 'Cavity',
        'source': 'Cavity.max_flow_length (or flow_ratio * ave_wall_thickness)',
        'attr_name': 'max_flow_length',
        'desc': '制品最大流长 [mm]',
        'type': float,
        'condition': '必填',  # algorithm 注射行程
    },

    # ---- Gate 关联字段 ----
    'gate_type': {
        'source_model': 'Gate',
        'source': 'Gate.gate_type',  # ORM 字段名是 gate_type
        'attr_name': 'gate_type',
        'desc': '浇口类别（直浇口/侧浇口/点浇口/护耳式/...）',
        'type': str,
        'condition': '必填',  # algorithm 多处分支 + 保压推导
    },

    # ---- Gate 扩展字段（按 gate_type 动态展开）----
    # process_generate.py 94-106 的动态检查：
    #   - 侧浇口+圆形：gate_shape, gate_radius
    #   - 侧浇口+矩形：gate_shape, gate_length, gate_width
    'gate_shape': {
        'source_model': 'Gate',
        'source': 'Gate.gate_shape',  # ORM 字段名是 gate_shape
        'attr_name': 'gate_shape',
        'desc': '浇口形状（圆形/矩形）',
        'type': str,
        'condition': '条件必填',
        'condition_when': {'gate_type': '侧浇口'},
    },
    'gate_radius': {
        'source_model': 'Gate',
        'source': 'Gate.diameter (or outer_diameter) / 2',  # 计算字段
        'attr_name': None,  # attr_name 为 None，service 层特殊处理
        'desc': '浇口半径(圆) [mm]',
        'type': float,
        'condition': '条件必填',
        'condition_when': {'gate_type': '侧浇口', 'gate_shape': '圆形'},
    },
    'gate_length': {
        'source_model': 'Gate',
        'source': 'Gate.length',  # ORM 字段名是 length
        'attr_name': 'length',
        'desc': '浇口长(矩形) [mm]',
        'type': float,
        'condition': '条件必填',
        'condition_when': {'gate_type': '侧浇口', 'gate_shape': '矩形'},
    },
    'gate_width': {
        'source_model': 'Gate',
        'source': 'Gate.width',  # ORM 字段名是 width
        'attr_name': 'width',
        'desc': '浇口宽(矩形) [mm]',
        'type': float,
        'condition': '条件必填',
        'condition_when': {'gate_type': '侧浇口', 'gate_shape': '矩形'},
    },
}


# ---- 派生：单一数据源原则 ----
# 通用机制（condition 求值 / 必填集派生 / 完整性核查 / 驱动形式标准化）已下沉到
# algorithms/field_contract.py —— 那是与具体算法无关的纯函数，各算法只保留自己的字段字典。
# 本文件 re-export 仅为兼容既有调用方（data_validator / initializer 都从 specs 取这些名字）；
# 新代码请直接 import algorithms.field_contract，不要再经由某个算法包转发。
# 算法包之间不互相 import：fuzzy 的契约见 algorithms/fuzzy/specs.py（字段名属 fuzzy
# 自己的 ORM 命名空间，与这里的 expert 契约名不同，不可混用）。

# 单一数据源：自动从 mapping.condition 派生
REQUIRED_MOLD_INFO_FIELDS: Tuple[str, ...] = derive_required_fields(MOLD_INFO_SPEC)
REQUIRED_MACHINE_FIELDS: Tuple[str, ...] = derive_required_fields(MACHINE_INFO_FIELDS)
REQUIRED_POLYMER_FIELDS: Tuple[str, ...] = derive_required_fields(POLYMER_INFO_FIELDS)


# 字段完整性校验与字段转换函数：见 algorithms/field_contract.py
#（通用机制，非 expert 专属；本文件只定 expert 自己的字段字典）


__all__ = [
    # 字段定义
    "MACHINE_INFO_FIELDS",
    "POLYMER_INFO_FIELDS",
    "MOLD_INFO_SPEC",
    # 派生（自动从 mapping 推导）
    "REQUIRED_MOLD_INFO_FIELDS",
    "REQUIRED_MACHINE_FIELDS",
    "REQUIRED_POLYMER_FIELDS",
    # 以下为 algorithms/field_contract.py 的 re-export（兼容旧调用方，非本文件定义）
    "audit_field_completeness",
    "drive_system_to_power_method",
]
