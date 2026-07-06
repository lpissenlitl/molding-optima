"""
工艺参数初始化服务

对应接口：
- POST /api/processes/initialization/                  （Mode A：基于 condition_id）
- POST /api/processes/initialization/from-masterdata/  （Mode B：基于 masterdata ID）
- POST /api/processes/initialization/infer/            （/infer/：纯推理，前端传完整数据）

设计原则（4 步清晰落地）：
  Step 1: 入口适配 —— condition_id / masterdata_id / 4维dict 三种入口
  Step 2: 数据前处理 —— ORM + process_context（关联 ID + 字段覆盖） → 4 维 dict
  Step 3: 推理算法 —— infer_initial_params（纯算法，无副作用）
  Step 4: 输出数据后处理 —— 格式化 + 可选落库

process_context 的角色（重要）：
  它不是中间数据结构，而是 Step 2 的"补充输入"，承载 ORM 无法表达的业务细节：
  - 关联 ID（gating_system_id / cavity_id / gate_id / injection_unit_id）：指定 1:N 中的子项
  - 字段覆盖（任意键）：覆盖 ORM 默认值

术语规范：
- 4 维上下文统一顺序：模具（mold_info）→ 设备（machine_info）→ 材料（polymer_info）→ 工艺设定（process_set）
- 一律使用 "mold" 不用 "product"（mold_info 覆盖模具级 + 产品/浇口/壁厚派生）
"""

import logging
from typing import Dict, Any, Optional, Tuple, List

from process.engines.expert.initializer import ProcessInitializer
from process.engines.expert.rule_matcher import InitRuleMatcher

logger = logging.getLogger(__name__)


# ============================================================
# 常量层：字段映射（algorithm 期望字段 → ORM 属性）
# ============================================================
# 以 process_generate.py 9-115 行的检查清单为标准，
# 按 4 步逻辑中的 Step 2（数据前处理）所需字段全列举。
#
# 字典方向：{target_key: attr_name}
#   target_key = algorithm 期望的字段名（如 `velocity`）
#   attr_name  = ORM 模型上的实际属性名（如 `_speed`）
#
# 此映射详实补充了原本未覆盖的字段（液压机特需、max_metering_back_pressure 等）。


# ---- Mold 模具级字段 ----
# Mold 是复合模型，产品/浇口/壁厚信息由 GatingSystem/Cavity/Gate 关联表取出，
# 不在此 mapping 中（_build_mold_info 函数内部表达）。本 mapping 只含 Mold 主表字段。
#
# spec 格式：
#   {
#     attr_name: ORM 属性名（用于 _map_model_to_dict 提取）
#     desc: 字段描述（用于错误信息、文档生成）
#     type: 字段类型（int/float/str）
#     condition: "必填" | "液压机必填" | "可选"
#   }
_MOLD_TO_MOLD = {
    'shot_count': {
        'attr_name': 'shot_count',
        'desc': '注射次数（多色成型），1=单次，2=两次',
        'type': int,
        'condition': '可选',
    },
    'inject_cycle_require': {
        'attr_name': 'target_cycle_time',
        'desc': '目标成型周期 [s]（用于推导冷却时间）',
        'type': float,
        'condition': '可选',
    },
}


# ---- Machine 设备级字段（全部来自 InjectionUnit） ----
# 注意：设备详情不在 InjectionMoldingMachine 主表，而在关联的 InjectionUnit 上。
# 下方按 process_generate.py 字段检查顺序组织，并补充液压机特需。
_MACHINE_TO_MACHINE = {
    # ① 喷嘴与螺杆参数
    'nozzle_type': {
        'attr_name': 'nozzle_type',
        'desc': '喷嘴类型（直通型/锁定型/...）',
        'type': str,
        'condition': '必填',  # algorithm _validate_inputs 检查
    },
    'screw_diameter': {
        'attr_name': 'screw_diameter',
        'desc': '螺杆直径 [mm]',
        'type': float,
        'condition': '必填',  # algorithm _validate_inputs + total_len 计算
    },

    # ② 塑化与注射能力（设备极限）
    'max_injection_stroke': {
        'attr_name': 'max_injection_stroke',
        'desc': '最大注射行程 [mm]',
        'type': float,
        'condition': '可选',
    },
    'max_injection_pressure': {
        'attr_name': 'max_injection_pressure',
        'desc': '最大注射压力 [MPa]（设备极限）',
        'type': float,
        'condition': '可选',
    },
    'max_injection_velocity': {
        'attr_name': 'max_injection_speed',  # ORM 用 _speed（不是 _velocity）
        'desc': '最大注射速度 [mm/s]（设备极限）',
        'type': float,
        'condition': '可选',
    },
    'max_holding_pressure': {
        'attr_name': 'max_holding_pressure',
        'desc': '最大保压压力 [MPa]（设备极限）',
        'type': float,
        'condition': '可选',
    },
    'max_holding_velocity': {
        'attr_name': 'max_holding_speed',  # ORM 用 _speed
        'desc': '最大保压速度 [mm/s]（设备极限）',
        'type': float,
        'condition': '可选',
    },
    'max_screw_rotation_speed': {
        'attr_name': 'max_screw_rotation_speed',
        'desc': '最大螺杆转速 [rpm]（设备极限）',
        'type': float,
        'condition': '可选',
    },
    'max_metering_back_pressure': {
        'attr_name': 'max_metering_back_pressure',
        'desc': '最大计量背压 [MPa]',
        'type': float,
        'condition': '可选',
    },
    'max_decompression_velocity': {
        'attr_name': 'max_decompression_speed',  # ORM 用 _speed
        'desc': '最大松退速度 [mm/s]',
        'type': float,
        'condition': '可选',
    },

    # ②+ 液压机特需（设备极限）
    'max_metering_pressure': {
        'attr_name': 'max_metering_pressure',
        'desc': '最大计量压力 [MPa]（液压机特需）',
        'type': float,
        'condition': '液压机必填',
    },
    'max_decompression_pressure': {
        'attr_name': 'max_decompression_pressure',
        'desc': '最大松退压力 [MPa]（液压机特需）',
        'type': float,
        'condition': '液压机必填',
    },

    # ③ HMI 可设定范围（操作界面限制）
    'max_set_injection_pressure': {
        'attr_name': 'max_set_injection_pressure',
        'desc': '最大可设定注射压力 [MPa]（HMI）',
        'type': float,
        'condition': '必填',
    },
    'max_set_injection_velocity': {
        'attr_name': 'max_set_injection_speed',  # ORM 用 _speed
        'desc': '最大可设定注射速度 [mm/s]（HMI）',
        'type': float,
        'condition': '必填',
    },
    'max_set_holding_pressure': {
        'attr_name': 'max_set_holding_pressure',
        'desc': '最大可设定保压压力 [MPa]（HMI）',
        'type': float,
        'condition': '必填',
    },
    'max_set_holding_velocity': {
        'attr_name': 'max_set_holding_speed',  # ORM 用 _speed
        'desc': '最大可设定保压速度 [mm/s]（HMI）',
        'type': float,
        'condition': '必填',
    },
    'max_set_screw_rotation_speed': {
        'attr_name': 'max_set_screw_rotation_speed',
        'desc': '最大可设定螺杆转速 [rpm]（HMI）',
        'type': float,
        'condition': '必填',
    },
    'max_set_metering_back_pressure': {
        'attr_name': 'max_set_metering_back_pressure',
        'desc': '最大可设定计量背压 [MPa]（HMI）',
        'type': float,
        'condition': '液压机必填',
    },
    'max_set_decompression_velocity': {
        'attr_name': 'max_set_decompression_speed',  # ORM 用 _speed
        'desc': '最大可设定松退速度 [mm/s]（HMI）',
        'type': float,
        'condition': '可选',
    },

    # ③+ 液压机特需（HMI 可设定范围）
    'max_set_metering_pressure': {
        'attr_name': 'max_set_metering_pressure',
        'desc': '最大可设定计量压力 [MPa]（HMI）',
        'type': float,
        'condition': '液压机必填',
    },
    'max_set_decompression_pressure': {
        'attr_name': 'max_set_decompression_pressure',
        'desc': '最大可设定松退压力 [MPa]（HMI）',
        'type': float,
        'condition': '液压机必填',
    },
}


# ---- Polymer 材料级字段 ----
_POLYMER_TO_POLYMER = {
    'abbreviation': {
        'attr_name': 'abbreviation',
        'desc': '材料缩写（ABS/PP/PC+ABS/...）',
        'type': str,
        'condition': '必填',  # algorithm 多处使用 + 材料分支
    },
    'category': {
        'attr_name': 'category',
        'desc': '材料类型（结晶型/无定形/...）',
        'type': str,
        'condition': '可选',
    },
    'recommend_melt_temperature': {
        'attr_name': 'recommended_melt_temp',
        'desc': '推荐成型温度 [℃]',
        'type': float,
        'condition': '必填',  # algorithm 默认 250
    },
    'recommend_shear_linear_speed': {
        'attr_name': 'recommended_shear_line_speed',
        'desc': '推荐剪切线速度 [mm/s]',
        'type': float,
        'condition': '必填',  # algorithm 默认 160
    },
    'recommend_back_pressure': {
        'attr_name': 'recommend_back_pressure',
        'desc': '推荐背压 [MPa]',
        'type': float,
        'condition': '必填',  # algorithm 默认 15
    },
    'recommend_mold_temperature': {
        'attr_name': 'recommended_mold_temp',
        'desc': '推荐模具温度 [℃]',
        'type': float,
        'condition': '必填',  # algorithm 默认 0
    },
    'ejection_temperature': {
        'attr_name': 'ejection_temp',
        'desc': '顶出温度 [℃]',
        'type': float,
        'condition': '可选',
    },
    'melt_density': {
        'attr_name': 'melt_density',
        'desc': '熔体密度 [g/cm³]',
        'type': float,
        'condition': '必填',  # algorithm 默认 0.95
    },
}


# ============================================================
# 常量层：字段完整性标准（按 process_generate.py 79-92 检查清单）
# ============================================================
# 这些字段是 algorithm 推理的有效输入最低要求（历史版本 + 当前算法）。
# 缺失时 algorithm 会用兑底默认值，
# 但 schema 完整性校验、错误信息、文档生成、前端字段提示都依赖此标准。

# ---- 制品（mold_info）字段 spec ----
# mold_info 来源于多个关联表（GatingSystem / Cavity / Gate），不是单一 ORM 字段。
# spec 格式：
#   source: 关联表 + ORM 属性（描述字段来源）
#   condition: "必填" / "液压机必填" / "条件必填" / "可选"
#   condition_when: 条件必填的触发条件字典（如 {'gate_type': '侧浇口'}）
# 未设 attr_name——_build_mold_info 内部按 source 自行提取（因为是多源）。
_MOLD_INFO_SPEC = {
    # ---- Mold ORM 主表字段 ----
    'product_type': {
        'source': 'Mold.product_type',
        'desc': '制品类型（历史字段，algorithm 未使用）',
        'type': str,
        'condition': '可选',
    },

    # ---- GatingSystem 关联字段 ----
    'runner_weight': {
        'source': 'GatingSystem.runner_weight (or estimated_runner_weight)',
        'desc': '流道重量 [g]',
        'type': float,
        'condition': '必填',  # algorithm 注射量 + 多级注塑分支
    },
    'product_weight': {
        'source': 'GatingSystem.total_product_weight',
        'desc': '制品总重量 [g]',
        'type': float,
        'condition': '必填',  # algorithm 注射量 + 冷却时间
    },
    'runner_type': {
        'source': 'GatingSystem.runner_type',
        'desc': '流道类型（热流道/冷流道/热转冷）',
        'type': str,
        'condition': '推荐',  # 多个算法依赖（保压压力/保压时间/冷却/松退）
    },

    # ---- Cavity 关联字段 ----
    'max_thickness': {
        'source': 'Cavity.max_wall_thickness',
        'desc': '制品最大壁厚 [mm]',
        'type': float,
        'condition': '必填',  # algorithm 冷却时间 + 保压
    },
    'ave_thickness': {
        'source': 'Cavity.ave_wall_thickness',
        'desc': '制品平均壁厚 [mm]',
        'type': float,
        'condition': '必填',  # algorithm 冷却 + 保压 + 注塑
    },
    'max_length': {
        'source': 'Cavity.max_flow_length (or flow_ratio * ave_wall_thickness)',
        'desc': '制品最大流长 [mm]',
        'type': float,
        'condition': '必填',  # algorithm 注射行程
    },

    # ---- Gate 关联字段 ----
    'gate_type': {
        'source': 'Gate.type',
        'desc': '浇口类别（直浇口/侧浇口/点浇口/护耳式/...）',
        'type': str,
        'condition': '必填',  # algorithm 多处分支 + 保压推导
    },

    # ---- Gate 扩展字段（按 gate_type 动态展开）----
    # process_generate.py 94-106 的动态检查：
    #   - 侧浇口+圆形：gate_shape, gate_radius
    #   - 侧浇口+矩形：gate_shape, gate_length, gate_width
    'gate_shape': {
        'source': 'Gate.shape',
        'desc': '浇口形状（圆形/矩形）',
        'type': str,
        'condition': '条件必填',
        'condition_when': {'gate_type': '侧浇口'},
    },
    'gate_radius': {
        'source': 'Gate.outer_diameter / 2',
        'desc': '浇口半径(圆) [mm]',
        'type': float,
        'condition': '条件必填',
        'condition_when': {'gate_type': '侧浇口', 'gate_shape': '圆形'},
    },
    'gate_length': {
        'source': 'Gate.length',
        'desc': '浇口长(矩形) [mm]',
        'type': float,
        'condition': '条件必填',
        'condition_when': {'gate_type': '侧浇口', 'gate_shape': '矩形'},
    },
    'gate_width': {
        'source': 'Gate.width',
        'desc': '浇口宽(矩形) [mm]',
        'type': float,
        'condition': '条件必填',
        'condition_when': {'gate_type': '侧浇口', 'gate_shape': '矩形'},
    },
}

# 从 _MOLD_INFO_SPEC 派生 mold_info 必需字段集（单一数据源原则）
_REQUIRED_MOLD_INFO_FIELDS: Tuple[str, ...] = _derive_required_fields(_MOLD_INFO_SPEC)


# ---- 工艺设置（process_set）必需字段 ----
# algorithm 在 _derive_process / _apply_multi_stage 中访问的字段。
_REQUIRED_PROCESS_SET_FIELDS = (
    'inj_stg',                          # 注射段数（1-6）
    'hold_stg',                         # 保压段数（1-5）
    'met_stg',                          # 计量段数（1-4）
    'barrel_temperature_stage',         # 料筒温度段数（1-10）
    'VP_switch_mode',                   # VP 切换模式（字符串：位置/时间/...）
    'vps_mode',                         # VP 切换模式（整数：0=位置/1=时间/2=其他）
    'pre_met_decomp_mode',              # 熔胶前松退模式
    'pst_met_decomp_mode',              # 熔胶后松退模式
)


# ---- 工艺设置字段历史名 → 当前名 ----
# 旧版本（process_generate.py）字段名与 algorithm 当前字段名不一致，
# 适用于 API 兼容层或外部数据导入场景。
_PROCESS_SET_LEGACY_TO_CURRENT = {
    'injection_stage': 'inj_stg',
    'holding_stage': 'hold_stg',
    'metering_stage': 'met_stg',
    'decompressure_mode_before_metering': 'pre_met_decomp_mode',
    'decompressure_mode_after_metering': 'pst_met_decomp_mode',
}


# ============================================================
# 常量层：process_context 中的关联 ID 键
# ============================================================
# 在 ORM 转 4 维 dict 时按 ID 精确指定 1:N 关系中的具体子项。
# 业务过程覆盖字段（product_weight / gate_type 等）走通用合并逻辑，不在此列出。

_MOLD_RELATION_ID_KEYS = ('gating_system_id', 'cavity_id', 'gate_id')
_MACHINE_RELATION_ID_KEYS = ('injection_unit_id',)


# ============================================================
# 辅助函数层：顺序按依赖关系（先通用后专用）
# ============================================================

def _map_model_to_dict(model_obj, mapping: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """按 mapping spec 从 ORM 对象提取字段到目标字典

    mapping spec 格式: {target_key: {'attr_name': str, 'desc': ..., 'type': ..., 'condition': ...}}
    仅提取 attr_name 对应的 ORM 属性值到 target_key。
    """
    result: Dict[str, Any] = {}
    for target_key, spec in mapping.items():
        attr_name = spec.get('attr_name')
        if not attr_name or not hasattr(model_obj, attr_name):
            continue
        value = getattr(model_obj, attr_name, None)
        if value is not None:
            result[target_key] = value
    return result


def _derive_required_fields(mapping: Dict[str, Dict[str, Any]]) -> Tuple[str, ...]:
    """从 mapping spec 派生必需字段集（condition != '可选'）

    单一数据源原则：mapping 定义字段类型与 condition，
    必需字段集自动派生，避免重复维护。
    """
    return tuple(
        target_key
        for target_key, spec in mapping.items()
        if spec.get('condition', '可选') != '可选'
    )


def audit_field_completeness(
    info_dict: Dict[str, Any],
    mapping: Dict[str, Dict[str, Any]],
    dim_name: str,
    *,
    is_hydraulic: bool = False,
) -> List[str]:
    """按 mapping spec 核查输入维度字段完整性，返回缺失字段清单

    Args:
        info_dict: 输入字典（如 machine_info、polymer_info、mold_info）
        mapping: 字段映射 spec（如 _MACHINE_TO_MACHINE、_MOLD_INFO_SPEC）
        dim_name: 维度名（用于错误信息，如 "machine_info"）
        is_hydraulic: 是否液压机驱动（仅影响 condition='液压机必填' 的处理）

    Returns:
        缺失字段的描述列表

    condition 取值与处理：
        - "可选":        跳过
        - "必填":        在任何情况下都必填
        - "液压机必填":   仅 is_hydraulic=True 时必填
        - "条件必填":    按 spec.condition_when 评估（所有 k==v 匹配时必填）
    """
    missing: List[str] = []
    for target_key, spec in mapping.items():
        cond = spec.get('condition', '可选')

        if cond == '可选':
            continue

        is_required = False
        if cond == '必填':
            is_required = True
        elif cond == '液压机必填':
            is_required = is_hydraulic
        elif cond == '条件必填':
            is_required = _eval_condition_when(spec.get('condition_when', {}), info_dict)

        if is_required and not info_dict.get(target_key):
            missing.append(f"{dim_name}.{target_key} ({spec.get('desc', '')})")

    return missing


def _eval_condition_when(
    condition_when: Dict[str, Any],
    info_dict: Dict[str, Any],
) -> bool:
    """评估条件必填：当 condition_when 中所有 (k, v) 对都在 info_dict 匹配时为 True

    例: condition_when={'gate_type': '侧浇口', 'gate_shape': '圆形'}
        当 info_dict['gate_type']=='侧浇口' 且 info_dict['gate_shape']=='圆形' 时返回 True
    """
    if not condition_when:
        return False
    for key, expected in condition_when.items():
        if info_dict.get(key) != expected:
            return False
    return True


# ---- 从 mapping spec 派生的必需字段集（单一数据源原则） ----
# `_REQUIRED_*_FIELDS` 不再重复列举，每一项都从 mapping 的 condition 自动派生。
# 修改 mapping.condition 即可同步必需字段集合。
_REQUIRED_MACHINE_FIELDS: Tuple[str, ...] = _derive_required_fields(_MACHINE_TO_MACHINE)
_REQUIRED_POLYMER_FIELDS: Tuple[str, ...] = _derive_required_fields(_POLYMER_TO_POLYMER)
_REQUIRED_MOLD_FIELDS: Tuple[str, ...] = _derive_required_fields(_MOLD_TO_MOLD)


def _drive_system_to_power_method(drive_system: Optional[str]) -> Optional[str]:
    """InjectionMoldingMachine.drive_system → ProcessInitializer 期望的 power_method

    drive_system 字段取值：
        'hydraulic' / 'hydraulic_rear' / 'hydraulic_front' / '液压' → '液压机'
        其他 → '电动机'
    """
    if not drive_system:
        return None
    ds = str(drive_system).lower()
    if 'hydraulic' in ds or '液压' in ds:
        return '液压机'
    return '电动机'


def _pick_related(
    parent,
    related_name: str,
    target_id: Optional[int],
    parent_label: str,
    child_label: str,
):
    """从 parent 的关联集合中按 ID 精确选取一个对象（找不到则取第一个，无则返回 None）

    Args:
        parent: 父对象（如 mold、gating、cavity）
        related_name: 父对象上的反向关联属性名（如 'gating_systems'）
        target_id: 目标关联记录的 ID（None 时取第一个）
        parent_label / child_label: 用于错误信息（如 'Mold' / 'GatingSystem'）

    Raises:
        ValueError: target_id 不属于 parent 的关联集合
    """
    if parent is None:
        return None
    qs = getattr(parent, related_name, None)
    items = list(qs.all() if qs is not None else [])
    if not items:
        return None
    if target_id is None:
        return items[0]
    target = next((item for item in items if item.id == target_id), None)
    if target is None:
        raise ValueError(
            f"{child_label}(id={target_id}) 不属于 {parent_label}(id={parent.id})，"
            f"该 {parent_label} 可用的 {child_label}: {[item.id for item in items]}"
        )
    return target


def _pop_relation_ids(
    process_context: Optional[Dict[str, Any]],
    keys: tuple,
) -> Dict[str, Optional[int]]:
    """从 process_context 中 pop 出指定 key 的值（副作用：会从传入 dict 中删除这些 key）

    用于让关联 ID 不被当作"字段覆盖"混入 mold_info / machine_info。
    """
    result: Dict[str, Optional[int]] = {k: None for k in keys}
    if not process_context:
        return result
    for k in keys:
        if k in process_context:
            value = process_context.pop(k)
            if value is not None and value != '':
                try:
                    result[k] = int(value)
                except (TypeError, ValueError):
                    pass
    return result


# ============================================================
# Step 2 业务函数层：ORM 模型 → 4 维 dict 转换
# ============================================================
# 这是"4 步逻辑"中的 Step 2（数据前处理）。三个组合入口
# (infer_from_condition / infer_from_masterdata) 都会通过这两个函数
# 把 ORM 模型 + process_context 转换成算法引擎所需的 4 维 dict。
# /infer/ 入口跳过这一步（前端已直接提供完整 4 维 dict）。

def _build_mold_info(
    mold,
    process_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """从 Mold（复合模型）组装 mold_info dict（Step 2 - 模具维度）

    process_context 的用途：
      - 关联 ID（gating_system_id / cavity_id / gate_id）：指定 1:N 中的具体子项
      - 字段覆盖（其余 key）：覆盖 ORM 默认值
    """
    # 复制 context 副本（避免污染原 dict，且关联 ID 需要从副本 pop）
    ctx = dict(process_context or {})
    relation_ids = _pop_relation_ids(ctx, _MOLD_RELATION_ID_KEYS)

    mold_info: Dict[str, Any] = {}

    # 1. 模具级字段
    for target_key, attr in _MOLD_TO_MOLD.items():
        value = getattr(mold, attr, None)
        if value is not None:
            mold_info[target_key] = value

    # 2. 关联记录选择（按 ID 精确指定，未传时取第一个）
    gating = _pick_related(mold, 'gating_systems', relation_ids['gating_system_id'], 'Mold', 'GatingSystem')
    cavity = _pick_related(gating, 'cavities', relation_ids['cavity_id'], 'GatingSystem', 'Cavity')
    gate = _pick_related(cavity, 'gates', relation_ids['gate_id'], 'Cavity', 'Gate')

    # 3. GatingSystem 字段（产品重量 / 流道）
    if gating is not None:
        if gating.total_product_weight is not None:
            mold_info['product_weight'] = gating.total_product_weight
        runner_w = gating.runner_weight or gating.estimated_runner_weight
        if runner_w is not None:
            mold_info['runner_weight'] = runner_w
        if getattr(gating, 'runner_type', None):
            mold_info['runner_type'] = gating.runner_type
        # 注：target_cycle_time / inject_cycle_require 已由 _MOLD_TO_MOLD 映射统一处理

    # 4. Cavity 字段（壁厚 / 最大流动长度）
    if cavity is not None:
        if cavity.ave_wall_thickness is not None:
            mold_info['ave_thickness'] = cavity.ave_wall_thickness
        if cavity.max_wall_thickness is not None:
            mold_info['max_thickness'] = cavity.max_wall_thickness
        if cavity.max_flow_length is not None:
            mold_info['max_length'] = cavity.max_flow_length
        elif cavity.flow_ratio and cavity.ave_wall_thickness:
            mold_info['max_length'] = cavity.flow_ratio * cavity.ave_wall_thickness

    # 5. Gate 字段（浇口类型 / 几何尺寸）
    if gate is not None:
        if gate.gate_type is not None:
            mold_info['gate_type'] = gate.gate_type
        if gate.length is not None:
            mold_info['gate_length'] = gate.length
        if gate.width is not None:
            mold_info['gate_width'] = gate.width
        if gate.outer_diameter is not None:
            mold_info['gate_radius'] = gate.outer_diameter / 2

    # 6. process_context 中的剩余字段作为 mold_info 覆盖（关联 ID 已被 pop）
    for k, v in ctx.items():
        if v is not None:
            mold_info[k] = v

    return mold_info


def _build_machine_info(
    machine,
    process_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """从 InjectionMoldingMachine + 选定的 InjectionUnit 组装 machine_info dict（Step 2 - 设备维度）

    process_context 的用途：
      - 关联 ID（injection_unit_id）：指定 InjectionUnit（多个时按 ID 精确选取）
    """
    ctx = dict(process_context or {})
    relation_ids = _pop_relation_ids(ctx, _MACHINE_RELATION_ID_KEYS)
    injection_unit_id = relation_ids['injection_unit_id']

    units_qs = getattr(machine, 'injection_units', None)
    units_list = list(units_qs.all() if units_qs is not None else [])

    # 没有注射单元时，仅返回机器级字段
    if not units_list:
        return {
            'power_method': _drive_system_to_power_method(
                getattr(machine, 'drive_system', None)
            ),
        }

    # 按 ID 精确选取 InjectionUnit
    if injection_unit_id is not None:
        unit = next((u for u in units_list if u.id == injection_unit_id), None)
        if unit is None:
            raise ValueError(
                f"InjectionUnit(id={injection_unit_id}) 不属于 "
                f"InjectionMoldingMachine(id={machine.id})，"
                f"该 machine 可用的 InjectionUnit: {[u.id for u in units_list]}"
            )
    else:
        unit = units_list[0]

    machine_info = _map_model_to_dict(unit, _MACHINE_TO_MACHINE)
    machine_info['power_method'] = _drive_system_to_power_method(
        getattr(machine, 'drive_system', None)
    )
    return machine_info


def _build_polymer_info(
    polymer,
    process_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """从 Polymer 组装 polymer_info dict（Step 2 - 材料维度）

    process_context 的用途：
      - 字段覆盖（任意 key）：覆盖 ORM 默认值（Polymer 无 1:N 关联，无需关联 ID 选取）

    说明：
      为与其他 _build_*_info 函数保持签名一致，仍接收 process_context 参数。
      目前不提取关联 ID，但留出扩展点（将来可能加 per-polymer 的某些关联）。
    """
    polymer_info = _map_model_to_dict(polymer, _POLYMER_TO_POLYMER)

    # process_context 字段覆盖（为对称保留接口）
    # 跳过 _POLYMER_TO_POLYMER 已映射的 ORM 字段名，避免覆盖 algorithm 所需的标准字段。
    polymer_attr_names = {spec['attr_name'] for spec in _POLYMER_TO_POLYMER.values()}
    if process_context:
        for k, v in process_context.items():
            if v is not None and k not in polymer_attr_names:
                polymer_info[k] = v

    return polymer_info


# ========== 工艺参数初始化服务（4 步逻辑清晰落地） ==========

class ProcessInitializationService:
    """工艺参数初始化服务（所有公开方法均为 @classmethod）

    服务架构清晰对应"4 步逻辑"：
      Step 3 核心算法：infer_initial_params(4 维 dict) → 4 维结果 dict（纯算法，无副作用）
      Step 1+2+3+4 Mode A 入口：infer_from_condition(condition_id, process_context, process_set) → 落库
      Step 1+2+3+4 Mode B 入口：infer_from_masterdata(mold_id, machine_id, polymer_id, ...) → 落库
      Step 1+3     /infer/ 入口：infer_from_dict(mold_info, machine_info, polymer_info, process_set) → 不落库
    """

    PARAM_SOURCE = "algorithm_init"

    # 类级缓存：所有 classmethod 共享同一个 InitRuleMatcher 实例
    _shared_rule_matcher: Optional[InitRuleMatcher] = None

    @classmethod
    def _get_rule_matcher(cls) -> InitRuleMatcher:
        if cls._shared_rule_matcher is None:
            cls._shared_rule_matcher = InitRuleMatcher()
        return cls._shared_rule_matcher

    # ============================================================
    # Step 3: 核心推理算法（纯算法，无任何副作用）
    # ============================================================

    @classmethod
    def infer_initial_params(
        cls,
        mold_info: Dict[str, Any],
        machine_info: Dict[str, Any],
        polymer_info: Dict[str, Any],
        process_set: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """【Step 3】纯算法推理：4 维输入 → 4 维参数输出（不查 DB、不写 DB、不涉及 ID）

        Args:
            mold_info / machine_info / polymer_info / process_set: 4 维推理上下文

        Returns:
            {
                "param_source", "matched_rules",
                "process": {...}, "mold_temp": {...}, "hot_runner": {...},
                "summary": {...}
            }
        """
        process_set = process_set or {}
        rule_matcher = cls._get_rule_matcher()

        logger.info(
            "工艺参数推理: polymer=%s, gate_type=%s, weight=%s",
            polymer_info.get("abbreviation"),
            mold_info.get("gate_type"),
            mold_info.get("product_weight"),
        )

        initializer = ProcessInitializer(
            mold_info=mold_info,
            machine_info=machine_info,
            polymer_info=polymer_info,
            process_set=process_set,
            rule_matcher=rule_matcher,
        )
        params = initializer.derive()
        matched_rules = list(rule_matcher.last_matched_codes)

        result = {
            "param_source": cls.PARAM_SOURCE,
            "matched_rules": matched_rules,
            "process": params.process.to_dict(),
            "mold_temp": params.mold_temp.to_dict(),
            "hot_runner": params.hot_runner.to_dict(),
            "summary": cls._build_summary(params),
        }

        logger.info(
            "推理完成: 规则=%s, inj_pres=%.2f, hold_t=%.2f, cool_t=%.2f",
            matched_rules,
            result["summary"]["injection_pressure"],
            result["summary"]["holding_time"],
            result["summary"]["cooling_time"],
        )
        return result

    @staticmethod
    def _build_summary(params) -> Dict[str, float]:
        """从 ProductionParams 抽取关键参数摘要"""
        proc = params.process
        return {
            "injection_pressure": (proc.inj_pres_steps[0] if proc.inj_pres_steps else 0.0),
            "injection_velocity": (proc.inj_spd_steps[0] if proc.inj_spd_steps else 0.0),
            "vp_switch_position": proc.vps_pos,
            "holding_pressure": (proc.hold_pres_steps[0] if proc.hold_pres_steps else 0.0),
            "holding_time": (proc.hold_time_steps[0] if proc.hold_time_steps else 0.0),
            "cooling_time": proc.cool_t,
            "injection_time": proc.inj_t,
            "barrel_nozzle_temp": proc.noz_temp,
            "barrel_temps": list(proc.brl_temp_steps),
            "metering_back_pressure": (
                proc.met_back_pres_steps[0] if proc.met_back_pres_steps else 0.0
            ),
            "mold_temp": params.mold_temp.mold_temp,
            "hot_runner_valve_num": params.hot_runner.valve_num,
        }

    # ============================================================
    # Mode A: 基于已有 condition_id 入口（4 步落地）
    # ============================================================

    @classmethod
    def infer_from_condition(
        cls,
        condition_id: int,
        process_context: Optional[Dict[str, Any]] = None,
        process_set: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """【Mode A】基于已有 condition_id 的"增量推理"入口

        Step 1: 入口适配 - condition_id → ORM
        Step 2: 数据前处理 - ORM + process_context → 4 维 dict
        Step 3: 推理算法 - 调用 infer_initial_params
        Step 4: 输出后处理 - 创建 ProcessParameter 挂到 condition
        """
        from django.db import transaction
        from process.models.process_condition import ProcessCondition

        with transaction.atomic():
            # Step 1: 入口适配
            condition = (
                ProcessCondition.objects
                .select_related('mold', 'injection_machine', 'polymer')
                .get(pk=condition_id)
            )

            # Step 2: 数据前处理
            mold_info = _build_mold_info(condition.mold, process_context=process_context)
            machine_info = _build_machine_info(condition.injection_machine, process_context=process_context)
            polymer_info = _build_polymer_info(condition.polymer, process_context=process_context)

            # Step 3: 推理算法
            result = cls.infer_initial_params(
                mold_info=mold_info,
                machine_info=machine_info,
                polymer_info=polymer_info,
                process_set=process_set,
            )

            # Step 4: 输出后处理（落库）
            parameter = cls._create_process_parameter(condition, result)
            result['condition_id'] = condition_id
            result['parameter_id'] = parameter.id

            logger.info(
                "Mode A 完成: condition_id=%s, parameter_id=%s, rules=%s",
                condition_id, parameter.id, result['matched_rules'],
            )
        return result

    # ============================================================
    # Mode B: 基于 masterdata ID 入口（4 步落地）
    # ============================================================

    @classmethod
    def infer_from_masterdata(
        cls,
        mold_id: int,
        injection_machine_id: int,
        polymer_id: int,
        process_context: Optional[Dict[str, Any]] = None,
        process_set: Optional[Dict[str, Any]] = None,
        condition_no: Optional[str] = None,
    ) -> Dict[str, Any]:
        """【Mode B】基于 masterdata ID 的"首次推理 + 建档"入口

        Step 1: 入口适配 - 3 个 ID → 3 个 ORM
        Step 2: 数据前处理 - ORM + process_context → 4 维 dict
        Step 3: 推理算法 - 调用 infer_initial_params
        Step 4: 输出后处理 - 创建 Condition + ProcessParameter

        status / origin_type 由后端固定为 draft / ai_recommendation。
        """
        from django.db import transaction
        from masterdata.models.mold import Mold
        from masterdata.models.injection import InjectionMoldingMachine
        from masterdata.models.material import Polymer
        from process.models.process_condition import ProcessCondition

        with transaction.atomic():
            # Step 1: 入口适配
            mold = Mold.objects.get(pk=mold_id)
            machine = InjectionMoldingMachine.objects.get(pk=injection_machine_id)
            polymer = Polymer.objects.get(pk=polymer_id)

            # Step 2: 数据前处理
            mold_info = _build_mold_info(mold, process_context=process_context)
            machine_info = _build_machine_info(machine, process_context=process_context)
            polymer_info = _build_polymer_info(polymer, process_context=process_context)

            # Step 3: 推理算法
            result = cls.infer_initial_params(
                mold_info=mold_info,
                machine_info=machine_info,
                polymer_info=polymer_info,
                process_set=process_set,
            )

            # Step 4: 输出后处理（创建 Condition + ProcessParameter）
            condition = ProcessCondition.objects.create(
                condition_no=condition_no or cls._auto_condition_no(mold_id, 1),
                status="draft",
                origin_type="ai_recommendation",
                mold_id=mold_id,
                injection_machine_id=injection_machine_id,
                polymer_id=polymer_id,
                process_context=process_context,
            )
            parameter = cls._create_process_parameter(condition, result)
            result['condition_id'] = condition.id
            result['parameter_id'] = parameter.id

            logger.info(
                "Mode B 完成: condition_id=%s, parameter_id=%s, rules=%s",
                condition.id, parameter.id, result['matched_rules'],
            )
        return result

    # ============================================================
    # /infer/ 入口（只跑 Step 3，跳过 Step 1 适配和 Step 4 落库）
    # ============================================================

    @classmethod
    def infer_from_dict(
        cls,
        mold_info: Dict[str, Any],
        machine_info: Dict[str, Any],
        polymer_info: Dict[str, Any],
        process_set: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """【/infer/】纯推理入口：不查 DB、不落库、4 维 dict 直传

        适用场景：第三方集成（无 masterdata）、算法试算。
        service 既不查 DB，也不写 DB。
        """
        return cls.infer_initial_params(
            mold_info=mold_info,
            machine_info=machine_info,
            polymer_info=polymer_info,
            process_set=process_set,
        )

    # ============================================================
    # 私有辅助方法（落库相关）
    # ============================================================

    @staticmethod
    def _auto_condition_no(mold_id: int, shot_index: int) -> str:
        """自动生成 condition_no：格式 C-{mold_id}-S{shot_index}-{ts}"""
        import time
        ts = int(time.time() * 1000000) % 1000000
        return f"C-{mold_id}-S{shot_index}-{ts:06d}"

    @staticmethod
    def _create_process_parameter(condition, params_result: Dict[str, Any]):
        """把推理结果拍扁为 ProcessParameter 字段并落库（Step 4 后处理）

        接收 infer_initial_params 的返回 dict（4 维输出）。
        """
        from process.models.process_parameter import ProcessParameter

        proc_dict = params_result['process']
        flat = {
            'process_condition': condition,
            'param_source': ProcessInitializationService.PARAM_SOURCE,
        }

        # 单值字段
        single_value_fields = [
            'inj_stg', 'inj_t', 'inj_dly_t',
            'vps_mode', 'vps_pos', 'vps_t', 'vps_pres', 'vps_spd',
            'hold_stg', 'cool_t',
            'met_stg', 'met_lim_t', 'met_end_pos',
            'pre_met_decomp_mode', 'pre_met_decomp_pres', 'pre_met_decomp_spd',
            'pre_met_decomp_t', 'pre_met_decomp_dist',
            'pst_met_decomp_mode', 'pst_met_decomp_pres', 'pst_met_decomp_spd',
            'pst_met_decomp_t', 'pst_met_decomp_dist',
            'brl_temp_stg', 'noz_temp',
        ]
        for f in single_value_fields:
            if f in proc_dict and proc_dict[f] is not None:
                flat[f] = proc_dict[f]

        # 数组 → 扁平字段
        steps_mappings = [
            ('inj_spd_steps',   'inj_spd_{}', 6),
            ('inj_pres_steps',  'inj_pres_{}', 6),
            ('inj_pos_steps',   'inj_pos_{}', 6),
            ('hold_pres_steps', 'hold_pres_{}', 5),
            ('hold_spd_steps',  'hold_spd_{}', 5),
            ('hold_time_steps', 'hold_t_{}', 5),
            ('met_pres_steps',  'met_pres_{}', 4),
            ('met_rot_spd_steps', 'met_rot_spd_{}', 4),
            ('met_back_pres_steps', 'met_back_pres_{}', 4),
            ('met_pos_steps',   'met_pos_{}', 4),
            ('brl_temp_steps',  'brl_temp_{}', 9),
        ]
        for src_attr, fmt, n_stages in steps_mappings:
            steps = proc_dict.get(src_attr) or []
            for i in range(n_stages):
                field = fmt.format(i + 1)
                flat[field] = steps[i] if i < len(steps) else None

        return ProcessParameter.objects.create(**flat)


# ============================================================
# 模块级公开 API（对外门面，转发到 classmethod）
# ============================================================
# 设计原则：
# - 对外暴露模块级函数；view 层通过 initialization_service.xxx() 调用
# - 内部实现用 @classmethod；便于共享状态（如 _shared_rule_matcher）
# - 模块级函数是"门面"，内部转发到 classmethod；后续重构类，公开 API 保持稳定

def infer_initial_params(
    mold_info: Dict[str, Any],
    machine_info: Dict[str, Any],
    polymer_info: Dict[str, Any],
    process_set: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """【Step 3 核心算法】纯推理入口"""
    return ProcessInitializationService.infer_initial_params(
        mold_info=mold_info,
        machine_info=machine_info,
        polymer_info=polymer_info,
        process_set=process_set,
    )


def infer_from_condition(
    condition_id: int,
    process_context: Optional[Dict[str, Any]] = None,
    process_set: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """【Mode A】基于 condition_id 入口"""
    return ProcessInitializationService.infer_from_condition(
        condition_id=condition_id,
        process_context=process_context,
        process_set=process_set,
    )


def infer_from_masterdata(
    mold_id: int,
    injection_machine_id: int,
    polymer_id: int,
    process_context: Optional[Dict[str, Any]] = None,
    process_set: Optional[Dict[str, Any]] = None,
    condition_no: Optional[str] = None,
) -> Dict[str, Any]:
    """【Mode B】基于 masterdata ID 入口"""
    return ProcessInitializationService.infer_from_masterdata(
        mold_id=mold_id,
        injection_machine_id=injection_machine_id,
        polymer_id=polymer_id,
        process_context=process_context,
        process_set=process_set,
        condition_no=condition_no,
    )


def infer_from_dict(
    mold_info: Dict[str, Any],
    machine_info: Dict[str, Any],
    polymer_info: Dict[str, Any],
    process_set: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """【/infer/】纯推理入口（不查 DB、不落库）"""
    return ProcessInitializationService.infer_from_dict(
        mold_info=mold_info,
        machine_info=machine_info,
        polymer_info=polymer_info,
        process_set=process_set,
    )
