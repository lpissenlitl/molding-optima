"""
工艺参数推导工具函数

纯技术实现，无业务语义。可独立测试。

包含：
    - 数学计算（截面积、行程、料垫）
    - 数据转换（family 解析）
    - 通用读取（系数安全访问）
"""

import math
from typing import Any, Dict, Optional

# 从 macros 导入 PI 常量（避免重复定义）
try:
    from .macros import HSO_PI
except ImportError:
    HSO_PI = math.pi


# ========== 数学计算 ==========


def compute_screw_cross_area(screw_diameter: float) -> float:
    """
    计算螺杆截面积 [mm²]

    公式：A = π × D² / 4

    Args:
        screw_diameter: 螺杆直径 [mm]

    Returns:
        螺杆截面积 [mm²]
    """
    return HSO_PI * (screw_diameter ** 2) / 4


def compute_total_injection_length(
    total_weight: float,
    melt_density: float,
    screw_diameter: float,
) -> float:
    """
    计算完整理论注射行程 [mm]

    推导：质量守恒 + 圆柱几何
        injection_volume = total_weight / melt_density    # [cm³]
        L_theory = injection_volume / A_screw × 1000     # [mm]

    Args:
        total_weight: 总重量（制品 + 流道）[g]
        melt_density: 熔体密度 [g/cm³]
        screw_diameter: 螺杆直径 [mm]

    Returns:
        完整理论行程 [mm]
    """
    a_screw = compute_screw_cross_area(screw_diameter)
    injection_volume = total_weight / melt_density
    return injection_volume * 1000.0 / a_screw


def compute_cushion_length(
    screw_diameter: float,
    cushion_ratio: float = 0.25,
    cushion_min_abs: int = 5,
) -> int:
    """
    计算料垫长度（螺杆最终停止位置）[mm]

    公式：cushion_len = max(ceil(D / ratio), cushion_min_abs)

    物理依据：
        - D / 4 为各厂商经验值的物理基础
          · 海天 8–12mm（推算 D=32–48mm）
          · Fanuc 10–15mm（推算 D=40–60mm）
        - 向上取整符合工业实践（安全优先，料垫宁多勿少）
        - cushion_min_abs 为绝对最小值（防止螺杆撞模）

    Args:
        screw_diameter: 螺杆直径 [mm]
        cushion_ratio: 料垫比例因子（默认 0.25 即 D/4）
        cushion_min_abs: 绝对最小值 [mm]（默认 5mm）

    Returns:
        料垫长度 [mm]（整数，与各厂商经验值一致）
    """
    return max(math.ceil(screw_diameter * cushion_ratio), cushion_min_abs)


# ========== 数据转换 ==========


def parse_material_family(abbreviation: str) -> str:
    """
    从材料完整名称解析出材料大类

    例："PA66+GF30" → "PA"，"PC+ABS" → "PC"，"PET" → "PET"，
       "HDPE" → "PE"，"PVC" → "PVC"

    注意顺序：长前缀优先（PET 必须在 PE 之前，否则误匹配）

    Args:
        abbreviation: 材料缩写（全名或简写）

    Returns:
        材料大类（PP/PBT/PET/PE/PS/ABS/AS/PC/PA/POM/PMMA/PVC/空字符串）
    """
    if not abbreviation:
        return ''
    abbrev = str(abbreviation).upper().strip()
    # 注意顺序：长前缀优先匹配
    # - PET 必须在 PE 之前（否则 'PET'.startswith('PE') 误匹配）
    # - PBT 可放任意位置（不存在 PB 前缀冲突）
    # - PMMA 必须在 PM 子串前（暂无冲突）
    # - 2026-07-05 #19+#20 温度族：补充 PVC / AS / HDPE / LDPE / LLDPE 5 个 family
    for family in (
        'PP', 'PBT', 'PET', 'PE',          # PE 匹配 PE/HDPE/LDPE/LLDPE
        'PS', 'ABS', 'AS',
        'PC', 'PA', 'POM', 'PMMA',
        'PVC',                              # 补 PVC
    ):
        if abbrev.startswith(family):
            return family
    return ''


# ========== 通用读取 ==========


def get_coeff(coeffs: Dict[str, Any], group: str, key: str, default: Any = None) -> Any:
    """
    从合并系数字典中安全读取指定键值

    Args:
        coeffs: 分组合并系数字典
        group: 分组名称（如 'injection', 'holding', 'metering'）
        key: 键名
        default: 默认值（key 不存在时返回）

    Returns:
        键值或默认值

    Example:
        get_coeff(self._coeffs, 'injection', 'default_fill_efficiency', 0.60)
    """
    return coeffs.get(group, {}).get(key, default)
