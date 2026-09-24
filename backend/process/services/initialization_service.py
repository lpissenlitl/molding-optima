"""
工艺参数初始化服务

对应接口：
- POST /api/processes/initialization/                  Mode A：基于 condition_id
- POST /api/processes/initialization/from-masterdata/  Mode B：基于 masterdata ID
- POST /api/processes/initialization/infer/            /infer/：纯推理，前端传完整数据

4 步逻辑：入口适配 → 数据前处理 → 推理算法 → 输出后处理。
术语：4 维上下文统一顺序 mold → machine → polymer → process_set；一律用 "mold" 不用 "product"
（mold_info 覆盖模具级 + 产品/浇口/壁厚派生）。
process_context 是 Step 2 的补充输入，承载关联 ID（gating_system_id/cavity_id/gate_id/
injection_unit_id）和字段覆盖，ORM 表达不了。
"""

import logging
from typing import Dict, Any, Optional, Tuple, List

from extensions.exceptions import BizException
from process.engines.expert.initializer import ProcessInitializer
from process.engines.expert.rule_matcher import InitRuleMatcher

logger = logging.getLogger(__name__)


def _derive_required_fields(mapping: Dict[str, Dict[str, Any]]) -> Tuple[str, ...]:
    """从 mapping 派生必需字段集（condition != '可选'），单一数据源原则。"""
    return tuple(
        target_key
        for target_key, spec in mapping.items()
        if spec.get('condition', '可选') != '可选'
    )


# 字段映射（algorithm 期望字段 → ORM 属性）
# spec 格式：{attr_name, desc, type, condition}，condition 可选 "必填" / "液压机必填" / "可选"

# ---- Mold 模具级字段（主表） ----
# 产品/浇口/壁厚由 GatingSystem/Cavity/Gate 关联表取出，不在此 mapping
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


# mold_info 字段完整性标准（多源：GatingSystem / Cavity / Gate）
# spec: { source, desc, type, condition, condition_when }
#   - condition: "必填" / "液压机必填" / "条件必填" / "可选"
#   - condition_when: 条件必填的触发条件字典
# source 不是 ORM attr_name，_build_mold_info_from_snapshot 内部按 source 自行提取
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


# 必需字段集（单一数据源：自动从 mapping.condition 派生）
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
# 快照构建层：ORM → 完整快照（process_context_snapshot）
# ============================================================
# 设计原则：
#   - 快照是"完整的工艺上下文"，落库到 ProcessCondition.process_context_snapshot
#   - 快照包含：模具 + 选定 GatingSystem（含全部 cavities/gates）+ 选定 InjectionUnit + Polymer
#   - 快照与算法入参严格分离：快照完整结构 → service 从中抽取算法需要的字段
#   - 快照保留 masterdata 原始完整字段，便于历史回溯（masterdata 变更也不影响历史快照）
#
# 算法层不需要的字段依然保留在快照中：这是为了"反查 / 复现 / 调试"。
# 不要在快照层做"选 cavity / 选 gate"的操作——那是算法的职责。

def _build_mold_snapshot(
    mold,
    shot_index: int = 0,
) -> Dict[str, Any]:
    """从 Mold 主表 + 选定的 GatingSystem 构建完整 mold 快照

    Args:
        mold: Mold ORM 实例
        shot_index: 模具的第几射（0-based），对应 mold.gating_systems[shot_index]

    Returns:
        {
            "mold": {Mold 主表全部字段},
            "gating_system": {
                ...GatingSystem 字段,
                "cavities": [{Cavity 字段, "gates": [{Gate 字段}]}],
            }
        }

    Bug fix（2026-09-23）：
        必须 prefetch_related('gating_systems__cavities__gates')，否则
        gating.to_dict(include_rvs=True) 不会序列化 cavities/gates 字段。

        根因：extensions/models.py:to_dict(include_rvs=True) 只在
        _prefetched_objects_cache 存在时序列化反向关系（依赖 prefetch_related
        触发），未 prefetch 时 gating 字典里没有 cavities/gates，导致下游
        _build_mold_info_from_snapshot 拿不到 gate_type / ave_thickness /
        max_thickness / product_weight 等必填字段，报 ERROR_PROCESS_INSUFFICIENT_FIELDS。

        复现：未修复前 print(gating) 输出不含 'cavities' / 'gates' 键
        （手动验证：backend/process/services/initialization_service.py:742-744）。
    """
    # 必须 prefetch cavities 和 gates，否则 to_dict(include_rvs=True) 丢字段
    # 重新查询以触发 prefetch（保留 mold 原有属性，避免构造全新实例）
    mold_cls = type(mold)
    mold = mold_cls.objects.filter(pk=mold.pk).prefetch_related(
        'gating_systems__cavities__gates'
    ).first() or mold

    snapshot: Dict[str, Any] = {
        "mold": mold.to_dict(),
    }

    gating_systems = list(mold.gating_systems.all() if hasattr(mold, 'gating_systems') else [])
    if shot_index < len(gating_systems):
        gating = gating_systems[shot_index]
        snapshot["gating_system"] = gating.to_dict(include_rvs=True)
    else:
        snapshot["gating_system"] = None
        logger.warning(
            "shot_index=%s 超出 mold(id=%s) 的 gating_systems 范围（共 %s 套）",
            shot_index, mold.id, len(gating_systems),
        )

    return snapshot


def _build_machine_snapshot(
    machine,
    injection_index: int = 0,
) -> Dict[str, Any]:
    """从 InjectionMoldingMachine 主表 + 选定的 InjectionUnit 构建完整 machine 快照

    Args:
        machine: InjectionMoldingMachine ORM 实例
        injection_index: 注塑机的第几个射台（0-based），对应 machine.injection_units[injection_index]

    Returns:
        {
            "machine": {Machine 主表全部字段},
            "injection_unit": {InjectionUnit 全部字段} | None
        }
    """
    snapshot: Dict[str, Any] = {
        "machine": machine.to_dict(),
    }

    injection_units = list(machine.injection_units.all() if hasattr(machine, 'injection_units') else [])
    if injection_index < len(injection_units):
        unit = injection_units[injection_index]
        snapshot["injection_unit"] = unit.to_dict()
    else:
        snapshot["injection_unit"] = None
        logger.warning(
            "injection_index=%s 超出 machine(id=%s) 的 injection_units 范围（共 %s 个）",
            injection_index, machine.id, len(injection_units),
        )

    return snapshot


def _build_polymer_snapshot(polymer) -> Dict[str, Any]:
    """从 Polymer 构建完整 polymer 快照（Polymer 无 1:N 关系，扁平即可）

    Returns:
        {"polymer": {Polymer 全部字段}}
    """
    return {
        "polymer": polymer.to_dict(),
    }


def _jsonify(obj: Any) -> Any:
    """递归把 datetime/date 转 ISO 字符串（供 JSON 字段落库）

    Bug fix（2026-09-23）：
        ORM 模型的 to_dict() 返回含 datetime 字段（TracedModel.created_at/updated_at），
        存入 ProcessCondition.process_context_snapshot (JSONField) 时默认 JSONEncoder 无法序列化。
        现象：TypeError: Object of type datetime is not JSON serializable
        修复：在落库前递归清理。
    """
    import datetime as _dt
    if isinstance(obj, (_dt.datetime, _dt.date)):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: _jsonify(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_jsonify(v) for v in obj]
    if isinstance(obj, tuple):
        return tuple(_jsonify(v) for v in obj)
    return obj


def _build_process_context_snapshot(
    mold_snapshot: Dict[str, Any],
    machine_snapshot: Dict[str, Any],
    polymer_snapshot: Dict[str, Any],
    process_set: Optional[Dict[str, Any]] = None,
    shot_index: int = 0,
    injection_index: int = 0,
) -> Dict[str, Any]:
    """聚合 4 个维度的快照为完整的 process_context_snapshot

    顶层额外字段：
      - version: 快照格式版本
      - captured_at: 快照生成时间（ISO 格式）
      - shot_index / injection_index: 索引信息
    """
    from datetime import datetime, timezone
    raw = {
        "version": "1.0",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "shot_index": shot_index,
        "injection_index": injection_index,
        "mold_info": mold_snapshot,
        "machine_info": machine_snapshot,
        "polymer_info": polymer_snapshot,
        "process_set": process_set or {},
    }
    return _jsonify(raw)


# ============================================================
# 快照 → 算法入参：从完整快照中抽取 algorithm 需要的扁平字段
# ============================================================
# 设计原则：
#   - 算法入参（infer_initial_params）依然是扁平 dict，不变
#   - 这里只是"快照 → 算法入参"的转换层，算法不直接看快照
#   - 快照是完整的，算法入参是精简的（按算法需求）
#   - 如果算法以后改成接收完整结构，这些函数可以废弃


def _build_mold_info_from_snapshot(
    mold_snapshot: Dict[str, Any],
) -> Dict[str, Any]:
    """从 mold 快照构建算法入参 mold_info（Step 2b）

    Args:
        mold_snapshot: _build_mold_snapshot 的返回值
                       形如: {"mold": {...}, "gating_system": {..., "cavities": [...], "gates": [...]}}

    Returns:
        算法入参 mold_info（扁平 dict）
    """
    mold_info: Dict[str, Any] = {}
    mold_data = mold_snapshot.get("mold") or {}
    gating = mold_snapshot.get("gating_system")

    # 1. Mold 主表字段
    for target_key, attr in _MOLD_TO_MOLD.items():
        value = mold_data.get(attr.get('attr_name', ''))
        if value is not None:
            mold_info[target_key] = value

    # 2. GatingSystem 字段（产品重量 / 流道）
    if gating:
        if gating.get('total_product_weight') is not None:
            mold_info['product_weight'] = gating['total_product_weight']
        runner_w = gating.get('runner_weight') or gating.get('estimated_runner_weight')
        if runner_w is not None:
            mold_info['runner_weight'] = runner_w
        if gating.get('runner_type'):
            mold_info['runner_type'] = gating['runner_type']

    # 3. Cavity 字段（取第一个 cavity）
    cavities = (gating or {}).get('cavities') or []
    if cavities:
        cavity = cavities[0]
        if cavity.get('ave_wall_thickness') is not None:
            mold_info['ave_thickness'] = cavity['ave_wall_thickness']
        if cavity.get('max_wall_thickness') is not None:
            mold_info['max_thickness'] = cavity['max_wall_thickness']
        if cavity.get('max_flow_length') is not None:
            mold_info['max_length'] = cavity['max_flow_length']
        elif cavity.get('flow_ratio') and cavity.get('ave_wall_thickness'):
            mold_info['max_length'] = cavity['flow_ratio'] * cavity['ave_wall_thickness']

    # 4. Gate 字段（取第一个 cavity 的第一个 gate）
    if cavities:
        gates = cavities[0].get('gates') or []
        if gates:
            gate = gates[0]
            if gate.get('gate_type'):
                mold_info['gate_type'] = gate['gate_type']
            if gate.get('length') is not None:
                mold_info['gate_length'] = gate['length']
            if gate.get('width') is not None:
                mold_info['gate_width'] = gate['width']
            if gate.get('outer_diameter') is not None:
                mold_info['gate_radius'] = gate['outer_diameter'] / 2

    return mold_info


def _build_machine_info_from_snapshot(
    machine_snapshot: Dict[str, Any],
) -> Dict[str, Any]:
    """从 machine 快照构建算法入参 machine_info（Step 2b）

    Args:
        machine_snapshot: _build_machine_snapshot 的返回值
                          形如: {"machine": {...}, "injection_unit": {...}}

    Returns:
        算法入参 machine_info（扁平 dict）
    """
    machine_data = machine_snapshot.get("machine") or {}
    unit = machine_snapshot.get("injection_unit")

    machine_info: Dict[str, Any] = {}

    # 1. power_method 从 machine 推导
    machine_info['power_method'] = _drive_system_to_power_method(
        machine_data.get('drive_system')
    )

    # 2. InjectionUnit 字段（按 _MACHINE_TO_MACHINE 映射）
    if unit:
        for target_key, spec in _MACHINE_TO_MACHINE.items():
            attr_name = spec.get('attr_name')
            if attr_name and attr_name in unit and unit[attr_name] is not None:
                machine_info[target_key] = unit[attr_name]

    return machine_info


def _build_polymer_info_from_snapshot(
    polymer_snapshot: Dict[str, Any],
) -> Dict[str, Any]:
    """从 polymer 快照构建算法入参 polymer_info（Step 2b）

    Args:
        polymer_snapshot: _build_polymer_snapshot 的返回值
                          形如: {"polymer": {...}}

    Returns:
        算法入参 polymer_info（扁平 dict）
    """
    polymer_data = polymer_snapshot.get("polymer") or {}
    polymer_info: Dict[str, Any] = {}

    for target_key, spec in _POLYMER_TO_POLYMER.items():
        attr_name = spec.get('attr_name')
        if attr_name and attr_name in polymer_data and polymer_data[attr_name] is not None:
            polymer_info[target_key] = polymer_data[attr_name]

    return polymer_info


# Step 2 快照路径：ORM → snapshot → 4 维算法入参
# 快照保留完整 masterdata 上下文（便于反查/复现/历史回溯），两个 Mode 共享同一套 snapshot builders。
# /infer/ 入口跳过这一步（前端已直接提供完整 4 维 dict）。

class ProcessInitializationService:
    """工艺参数初始化服务（4 步逻辑对应 4 个公开入口）

    字段约定：
      - process_context_snapshot: 后端自动构建的不可变快照（完整 masterdata 上下文）
      - process_context:         后端自动填的"调用入参快照"（记录本次调用传了什么，便于审计）

    入口见模块 docstring。
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

    # Mode B
    @classmethod
    def infer_from_masterdata(
        cls,
        mold_id: int,
        injection_machine_id: int,
        polymer_id: int,
        shot_index: int = 0,
        injection_index: int = 0,
        process_set: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """【Mode B】基于 masterdata ID 的"首次推理 + 建档"入口

        status / origin_type 由后端固定为 draft / ai_recommendation。
        condition_no 由 service 层自动生成（后端不可用户改）。

        shot_index = 模具的"第几射"（0=第一射）；injection_index = 注塑机的"第几个射台"（0=第一台）。
        二者决定本次工艺条件"哪台机哪个射台打哪个产品"。
        """
        from django.db import transaction
        from masterdata.models.mold import Mold
        from masterdata.models.injection import InjectionMoldingMachine
        from masterdata.models.material import Polymer
        from process.models.condition import ProcessCondition
        from process.exceptions import (
            ERROR_MOLD_NOT_FOUND,
            ERROR_MACHINE_NOT_FOUND,
            ERROR_POLYMER_NOT_FOUND,
        )

        with transaction.atomic():
            # Step 1: 入口适配
            mold = Mold.objects.filter(pk=mold_id).first()
            if mold is None:
                raise BizException(ERROR_MOLD_NOT_FOUND, f"模具不存在: id={mold_id}")

            machine = InjectionMoldingMachine.objects.filter(pk=injection_machine_id).first()
            if machine is None:
                raise BizException(ERROR_MACHINE_NOT_FOUND, f"注塑机不存在: id={injection_machine_id}")

            polymer = Polymer.objects.filter(pk=polymer_id).first()
            if polymer is None:
                raise BizException(ERROR_POLYMER_NOT_FOUND, f"材料不存在: id={polymer_id}")

            # Step 2a: 构建完整快照（ORM → snapshot）
            mold_snapshot = _build_mold_snapshot(mold, shot_index=shot_index)
            machine_snapshot = _build_machine_snapshot(machine, injection_index=injection_index)
            polymer_snapshot = _build_polymer_snapshot(polymer)
            snapshot = _build_process_context_snapshot(
                mold_snapshot=mold_snapshot,
                machine_snapshot=machine_snapshot,
                polymer_snapshot=polymer_snapshot,
                process_set=process_set,
                shot_index=shot_index,
                injection_index=injection_index,
            )

            # Step 2b: 从快照构建算法入参
            mold_info = _build_mold_info_from_snapshot(mold_snapshot)
            machine_info = _build_machine_info_from_snapshot(machine_snapshot)
            polymer_info = _build_polymer_info_from_snapshot(polymer_snapshot)

            # Step 3: 推理算法
            result = cls.infer_initial_params(
                mold_info=mold_info,
                machine_info=machine_info,
                polymer_info=polymer_info,
                process_set=process_set,
            )

            # call_context：记录本次接口调用传了什么，审计/调试用
            call_context = {
                "interface": "from_masterdata",
                "shot_index": shot_index,
                "injection_index": injection_index,
                "process_set": process_set,
            }

            # Step 4: 落库
            condition = ProcessCondition.objects.create(
                condition_no=cls._auto_condition_no(mold_id, shot_index),
                status="draft",
                origin_type="ai_recommendation",
                mold_id=mold_id,
                shot_index=shot_index,
                injection_machine_id=injection_machine_id,
                injection_index=injection_index,
                polymer_id=polymer_id,
                process_context=call_context,
                process_context_snapshot=snapshot,
            )
            parameter = cls._create_process_parameter(condition, result)
            result['condition_id'] = condition.id
            result['parameter_id'] = parameter.id
            # 补上 seq_idx：前端进入下一个 infer 调用需要作为 parent_seq_idx（2026-09-23 轮 6）
            result['seq_idx'] = parameter.seq_idx
            result['shot_index'] = shot_index
            result['injection_index'] = injection_index

            logger.info(
                "Mode B done: condition_id=%s, parameter_id=%s, shot_index=%s, injection_index=%s, rules=%s",
                condition.id, parameter.id, shot_index, injection_index, result['matched_rules'],
            )
        return result

    # Mode C
    @classmethod
    def infer_from_source_condition(
        cls,
        source_condition_id: int,
        process_set: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """【Mode C】基于源 condition 复制初始工艺参数（不调推理算法）

        复用已有合格工艺为新工艺起点，snapshot 用最新 masterdata 重建。
        输出：Condition(origin_type='legacy_import') + 拷贝自源 param 的 ProcessParameter。
        """
        from django.db import transaction
        from masterdata.models.mold import Mold
        from masterdata.models.injection import InjectionMoldingMachine
        from masterdata.models.material import Polymer
        from process.models.condition import ProcessCondition
        from process.models.parameter import ProcessParameter
        from process.exceptions import (
            ERROR_PROCESS_CONDITION_NOT_FOUND,
            ERROR_PROCESS_PARAMETER_NOT_FOUND,
            ERROR_MOLD_NOT_FOUND,
            ERROR_MACHINE_NOT_FOUND,
            ERROR_POLYMER_NOT_FOUND,
        )

        with transaction.atomic():
            # Step 1: 入口适配（读源 condition 拿元数据）
            source = (
                ProcessCondition.objects
                .select_related('mold', 'injection_machine', 'polymer')
                .filter(pk=source_condition_id)
                .first()
            )
            if source is None:
                raise BizException(
                    ERROR_PROCESS_CONDITION_NOT_FOUND,
                    f"源工艺条件不存在: id={source_condition_id}",
                )

            source_mold_id = source.mold_id
            source_machine_id = source.injection_machine_id
            source_polymer_id = source.polymer_id
            source_shot_index = source.shot_index or 0
            source_injection_index = source.injection_index or 0

            # Step 2a: 重新检索最新 masterdata
            mold = Mold.objects.filter(pk=source_mold_id).first()
            if mold is None:
                raise BizException(ERROR_MOLD_NOT_FOUND, f"模具不存在: id={source_mold_id}")
            machine = InjectionMoldingMachine.objects.filter(pk=source_machine_id).first()
            if machine is None:
                raise BizException(ERROR_MACHINE_NOT_FOUND, f"注塑机不存在: id={source_machine_id}")
            polymer = Polymer.objects.filter(pk=source_polymer_id).first()
            if polymer is None:
                raise BizException(ERROR_POLYMER_NOT_FOUND, f"材料不存在: id={source_polymer_id}")

            mold_snapshot = _build_mold_snapshot(mold, shot_index=source_shot_index)
            machine_snapshot = _build_machine_snapshot(machine, injection_index=source_injection_index)
            polymer_snapshot = _build_polymer_snapshot(polymer)
            new_snapshot = _build_process_context_snapshot(
                mold_snapshot=mold_snapshot,
                machine_snapshot=machine_snapshot,
                polymer_snapshot=polymer_snapshot,
                process_set=process_set,
                shot_index=source_shot_index,
                injection_index=source_injection_index,
            )

            # Step 2b: 读源 condition 的最新 ProcessParameter（复制源）
            source_param = (
                ProcessParameter.objects
                .filter(process_condition_id=source_condition_id, is_deleted=False)
                .order_by('-id')
                .first()
            )
            if source_param is None:
                raise BizException(
                    ERROR_PROCESS_PARAMETER_NOT_FOUND,
                    f"源工艺条件下未找到工艺参数: condition_id={source_condition_id}",
                )

            # Step 3: 跳过推理算法

            # Step 4: 创建新 condition + 拷贝参数
            call_context = {
                "interface": "from_source_condition",
                "source_condition_id": source_condition_id,
                "source_parameter_id": source_param.id,
                "process_set": process_set,
            }
            new_condition = ProcessCondition.objects.create(
                condition_no=cls._auto_condition_no(source_mold_id, source_shot_index),
                status="draft",
                origin_type="legacy_import",
                mold_id=source_mold_id,
                shot_index=source_shot_index,
                injection_machine_id=source_machine_id,
                injection_index=source_injection_index,
                polymer_id=source_polymer_id,
                process_context=call_context,
                process_context_snapshot=new_snapshot,
            )
            new_parameter = cls._copy_process_parameter(source_param, new_condition)

            logger.info(
                "Mode C 完成: source_condition_id=%s, condition_id=%s, parameter_id=%s, copied_from_param_id=%s",
                source_condition_id, new_condition.id, new_parameter.id, source_param.id,
            )

            return {
                "condition_id": new_condition.id,
                "parameter_id": new_parameter.id,
                "source_condition_id": source_condition_id,
                "source_parameter_id": source_param.id,
                "shot_index": source_shot_index,
                "injection_index": source_injection_index,
                "param_source": "template_copy",
            }

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

        原子语义：
            本方法负责创建 ProcessParameter；ProcessCondition 由调用方负责创建。
            两者必须在同一个 `with transaction.atomic():` 里依次创建——
            任何一个报错都回滚，保证「工艺条件 ↔ 工艺参数」这对的不可分性。
            详见 infer_from_masterdata / copy_to_new_masterdata 入口实现。
        """
        from process.models.parameter import ProcessParameter

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

    # ProcessParameter 可拷贝的业务字段名（手工列出，避免依赖 Django ORM 不在 service 内启动）
    _COPYABLE_PARAM_FIELDS = (
        # 注射参数
        'inj_stg',
        'inj_spd_1', 'inj_spd_2', 'inj_spd_3', 'inj_spd_4', 'inj_spd_5', 'inj_spd_6',
        'inj_pres_1', 'inj_pres_2', 'inj_pres_3', 'inj_pres_4', 'inj_pres_5', 'inj_pres_6',
        'inj_pos_1', 'inj_pos_2', 'inj_pos_3', 'inj_pos_4', 'inj_pos_5', 'inj_pos_6',
        'inj_t', 'inj_dly_t',
        # VP 切换参数
        'vps_mode', 'vps_pos', 'vps_t', 'vps_pres', 'vps_spd',
        # 保压参数
        'hold_stg',
        'hold_pres_1', 'hold_pres_2', 'hold_pres_3', 'hold_pres_4', 'hold_pres_5',
        'hold_spd_1', 'hold_spd_2', 'hold_spd_3', 'hold_spd_4', 'hold_spd_5',
        'hold_t_1', 'hold_t_2', 'hold_t_3', 'hold_t_4', 'hold_t_5',
        # 冷却
        'cool_t',
        # 熔胶参数
        'met_stg',
        'met_pres_1', 'met_pres_2', 'met_pres_3', 'met_pres_4',
        'met_rot_spd_1', 'met_rot_spd_2', 'met_rot_spd_3', 'met_rot_spd_4',
        'met_back_pres_1', 'met_back_pres_2', 'met_back_pres_3', 'met_back_pres_4',
        'met_pos_1', 'met_pos_2', 'met_pos_3', 'met_pos_4',
        # 松退参数
        'pre_met_decomp_mode', 'pre_met_decomp_pres', 'pre_met_decomp_spd',
        'pre_met_decomp_t', 'pre_met_decomp_dist',
        'pst_met_decomp_mode', 'pst_met_decomp_pres', 'pst_met_decomp_spd',
        'pst_met_decomp_t', 'pst_met_decomp_dist',
        'met_lim_t', 'met_end_pos',
        # 料筒温度
        'brl_temp_stg', 'noz_temp',
        'brl_temp_1', 'brl_temp_2', 'brl_temp_3', 'brl_temp_4', 'brl_temp_5',
        'brl_temp_6', 'brl_temp_7', 'brl_temp_8', 'brl_temp_9',
    )

    @classmethod
    def _copy_process_parameter(cls, source_param, target_condition):
        """从 source_param 拷贝业务字段，创建新 ProcessParameter 挂到 target_condition

        不拷贝的字段：
          - pk / id / created_at / updated_at / is_deleted / created_by / ...（系统字段）
          - process_condition（FK，必须重写）
          - parameter_no（新参数生成）
          - parent_param / seq_idx（调机树字段，新一轮调参重置）
          - param_source（标记为 template_copy）
        """
        from process.models.parameter import ProcessParameter

        flat = {
            'process_condition': target_condition,
            'param_source': 'template_copy',
        }
        for field_name in cls._COPYABLE_PARAM_FIELDS:
            value = getattr(source_param, field_name, None)
            if value is not None:
                flat[field_name] = value

        return ProcessParameter.objects.create(**flat)


# 模块级公开 API（对外门面，转发到 classmethod）
# 对外暴露模块级函数，view 层通过 initialization_service.xxx() 调用；
# 内部用 @classmethod 便于共享状态（如 _shared_rule_matcher）。

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


def infer_from_masterdata(
    mold_id: int,
    injection_machine_id: int,
    polymer_id: int,
    shot_index: int = 0,
    injection_index: int = 0,
    process_set: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """【Mode B】基于 masterdata ID 入口（算法生成初始工艺）"""
    return ProcessInitializationService.infer_from_masterdata(
        mold_id=mold_id,
        injection_machine_id=injection_machine_id,
        polymer_id=polymer_id,
        shot_index=shot_index,
        injection_index=injection_index,
        process_set=process_set,
    )


def infer_from_source_condition(
    source_condition_id: int,
    process_set: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """【Mode C】基于源 condition 复制初始工艺入口（不调推理）"""
    return ProcessInitializationService.infer_from_source_condition(
        source_condition_id=source_condition_id,
        process_set=process_set,
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
