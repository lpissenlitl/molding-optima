"""
算法入参契约的通用机制（字段字典 ⊥ 校验机制 分离）

为什么有这个文件：
- 每个算法的入参契约【字段字典】必须各自定义。字段选哪些、叫什么名、必填到什么
  程度，都是算法自己的决定，由各算法包内自行维护。
- 但「按字段字典评估必填等级」这套【机制】是纯函数，与任何具体算法无关：
  输入 (info_dict, mapping, dim_name, is_hydraulic)，输出缺失字段清单。
  各抄一份就会出现两套实现各自演化，condition 的语义迟早分叉。
- 所以：机制在这里共享一次，字段字典留在各算法包内。**算法包之间不互相 import**。

提供：
- eval_condition_when:          condition_when 的条件求值（== / __in / __nin）
- derive_required_fields:       从字段字典派生必填字段集（单一来源原则）
- audit_field_completeness:     按字段字典核查字段完整性，返回缺失清单
- drive_system_to_power_method: InjectionMoldingMachine.drive_system → '液压机' / '电动机'

字段字典的 entry 约定（各算法保持一致结构，便于 service 层用同一套提取代码）：
- source_model:   ORM 模型类名（跨表提取时据此选数据源）
- source:         人类可读来源描述（含计算表达式时写明）
- attr_name:      ORM 属性名（计算字段为 None，由 service 层特殊处理）
- desc:           业务描述
- type:           类型
- condition:      必填等级（必填 / 液压机必填 / 条件必填 / 推荐 / 可选）
- condition_when: 条件必填的触发条件字典
"""

from typing import Any, Dict, List, Optional, Tuple


def eval_condition_when(
    condition_when: Dict[str, Any],
    info_dict: Dict[str, Any],
) -> bool:
    """评估条件必填

    操作符（key 后缀）：
    - 无后缀（如 'gate_type'）：info_dict[key] == expected（向后兼容的相等匹配）
    - __in（如 'runner_type__in'）：info_dict[key] in expected（expected 为 list/tuple）
    - __nin（如 'runner_type__nin'）：info_dict[key] not in expected（expected 为 list/tuple）

    多个 key 默认为 AND 关系。

    例 1: {'gate_type': '侧浇口', 'gate_shape': '圆形'}
        当 info_dict['gate_type']=='侧浇口' 且 info_dict['gate_shape']=='圆形' 时返回 True

    例 2: {'runner_type__nin': ['热流道']}
        当 info_dict['runner_type'] 不在 ['热流道'] 中时返回 True
        （即 runner_type == 冷流道 或 热转冷 时触发）

    局限：只能对 **同一个 info_dict 内部** 的键求值。若某字段的触发条件落在别的维度
    （例如调优的温度字段取决于「本次是否涉及温度参数」，那是 process_parameter 的事），
    这里表达不了——需要由调用方在外部判断后另行校验，不要为了绕过限制而硬改等级标注。
    """
    if not condition_when:
        return False
    for key, expected in condition_when.items():
        if key.endswith('__in'):
            real_key = key[:-4]
            actual = info_dict.get(real_key)
            if not isinstance(expected, (list, tuple)):
                raise ValueError(
                    f"condition_when 的 {key!r} 期望 list/tuple，实际为 {type(expected).__name__}"
                )
            if actual not in expected:
                return False
        elif key.endswith('__nin'):
            real_key = key[:-5]
            actual = info_dict.get(real_key)
            if not isinstance(expected, (list, tuple)):
                raise ValueError(
                    f"condition_when 的 {key!r} 期望 list/tuple，实际为 {type(expected).__name__}"
                )
            # None 视为"不在列表中"（避免没填 runner_type 时被误判为热流道）
            check_list = [v for v in expected if v is not None]
            if actual in check_list:
                return False
        else:
            if info_dict.get(key) != expected:
                return False
    return True


def derive_required_fields(mapping: Dict[str, Dict[str, Any]]) -> Tuple[str, ...]:
    """从字段字典派生 condition 为必填等级的字段集

    包括 "必填" / "液压机必填"（所有液压机都必填）/ "条件必填"（按 context 评估）。

    单一来源原则：必填集不手写第二遍，改 condition 即自动同步。
    """
    result = []
    for target_key, spec in mapping.items():
        cond = spec.get('condition', '可选')
        if cond in ('必填', '液压机必填', '条件必填'):
            result.append(target_key)
    return tuple(result)


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
        mapping: 字段映射 spec（如 MACHINE_INFO_FIELDS、MOLD_INFO_SPEC）
        dim_name: 维度名（用于错误信息，如 "machine_info"）
        is_hydraulic: 是否液压机驱动（仅影响 condition='液压机必填' 的处理）

    Returns:
        缺失字段的描述列表

    condition 取值与处理：
        - "可选" / "推荐":  跳过
        - "必填":            在任何情况下都必填
        - "液压机必填":      仅 is_hydraulic=True 时必填
        - "条件必填":        按 spec.condition_when 评估（所有 k==v 匹配时必填）

    注意判空用的是 `not info_dict.get(key)`，因此 0 / 0.0 / '' 一律视为缺失。
    对本机制管理的设备边界类字段（压力/速度上限）而言，0 本来就不是合法上界，
    这样判是安全的；若将来某字段允许 0 为合法值，需改用 is None 判断。
    """
    missing: List[str] = []
    for target_key, spec in mapping.items():
        cond = spec.get('condition', '可选')

        if cond in ('可选', '推荐'):
            continue

        is_required = False
        if cond == '必填':
            is_required = True
        elif cond == '液压机必填':
            is_required = is_hydraulic
        elif cond == '条件必填':
            is_required = eval_condition_when(spec.get('condition_when', {}), info_dict)

        if is_required and not info_dict.get(target_key):
            missing.append(f"{dim_name}.{target_key} ({spec.get('desc', '')})")

    return missing


def drive_system_to_power_method(drive_system: Optional[str]) -> Optional[str]:
    """InjectionMoldingMachine.drive_system → 标准化的 power_method

    drive_system 字段取值多样：
        'hydraulic' / 'hydraulic_rear' / 'hydraulic_front' / '液压' / '液压机' → '液压机'
        其他 → '电动机'

    Args:
        drive_system: InjectionMoldingMachine.drive_system 原始值

    Returns:
        标准化的 power_method（'液压机' / '电动机' / None）

    用途：算法层评估「液压机必填」等级的前提。全电机无油缸，HMI 上没有
    「计量压力」这类输入栏，该字段缺失属物理正常，不能按数据缺失拦下来。
    """
    if not drive_system:
        return None
    ds = str(drive_system).lower()
    if 'hydraulic' in ds or '液压' in ds:
        return '液压机'
    return '电动机'


__all__ = [
    "eval_condition_when",
    "derive_required_fields",
    "audit_field_completeness",
    "drive_system_to_power_method",
]
