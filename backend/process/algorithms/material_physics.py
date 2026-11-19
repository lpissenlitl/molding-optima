"""材料物理常量与派生公式（**跨算法包共享的物理归属地**）。

为什么有这个文件：
- 冷却/保压时间的**物理基准**由「制品壁厚 + 材料大类」决定（冷却时间 ∝ 壁厚²），
  这是**物理事实**，不属于任何一个算法包的私有口径。
- 专家引擎（``expert``）与模糊引擎（``fuzzy``）都要用它：
  专家引擎用它**推导**初始工艺参数，模糊引擎用它**标定判级论域**。
- 但两个算法包**不互相 import**（见 ``field_contract.py`` 的模块说明：
  「算法包之间不互相 import」）⇒ 物理常量必须放在**中立层**（``algorithms/`` 根），
  由两个包各自单向引用，依赖方向永远是「算法包 → algorithms 根」。

提供：
- ``COOL_FAMILY_FACTOR``      材料大类 → 冷却时间系数（11 family）
- ``DEFAULT_COOL_FACTOR``     材料未知时的保守中位系数
- ``COOL_TIME_MIN``           冷却时间下限 [s]（开模 + 顶出机械动作最小耗时）
- ``parse_material_family``   材料缩写 → 材料大类
- ``compute_cool_time``       最大壁厚 + 材料大类 → 基础冷却时间 [s]

【注意】**常量同源说明（改动时必须同步）**：
本文件的 ``COOL_FAMILY_FACTOR`` / ``DEFAULT_COOL_FACTOR`` / ``COOL_TIME_MIN``
与 ``expert/rule_matcher.py::_BUILTIN_DEFAULTS['cooling']`` **同源**
（行业共识策展数据：Tederic 2026 / Moldflow / 海天工艺手册）。
专家侧调整系数时，**本文件要同步改** —— 两处算出不同的冷却时间 ⇒
「专家推导的初值」与「模糊判级的坐标轴」会分叉。

【注意】**本模块只取物理公式的「基础项」**：
专家引擎的完整冷却时间是 4 维的
``t_cool = 壁厚² × 材料系数 × ΔT_factor × crystallinity_kick``，
其中 ``ΔT_factor``（5 档温差修正）与 ``crystallinity_kick``（结晶拉长）
在 expert 侧是**依赖具体材料参数**的分档逻辑。
本模块**刻意只实现前两项** —— 后两项若要纳入，应先从 expert 侧抽成公共函数，
而不是在这里抄第二套分档（抄了就是两套口径各自演化）。
"""

from typing import Dict


# --- 冷却时间物理常量 ---------------------------------------------------

#: 材料大类 → 冷却时间系数（t_cool ∝ 最大壁厚² × 本系数）
#: 与 ``expert/rule_matcher.py::_BUILTIN_DEFAULTS['cooling']['family_cool_factor']`` 同源。
COOL_FAMILY_FACTOR: Dict[str, float] = {
    'PP': 0.9, 'PE': 0.9,         # 易冷（无定形倾向 + 低 Tg）
    'PS': 1.0,                    # 无定形中位
    'ABS': 1.1, 'AS': 1.1,        # 无定形稍慢（玻璃化转变影响）
    'PMMA': 1.3,                  # 玻璃化转变较慢
    'PA': 1.6, 'POM': 1.6,        # 半结晶 + 中等结晶潜热
    'PBT': 1.7,                   # 半结晶 + 稍高黏度
    'PC': 1.8,                    # 高黏度无定形慢冷
    'PET': 2.0,                   # 半结晶 + 高结晶潜热（瓶盖长冷却）
}

#: 材料大类未知时的保守中位系数（与 expert 侧 ``default_cool_factor`` 一致）
DEFAULT_COOL_FACTOR: float = 1.2

#: 冷却时间下限 [s]（开模 + 顶出机械动作最小耗时；与 expert 侧 ``cool_time_min`` 一致）
COOL_TIME_MIN: float = 5.0


# --- 材料大类解析 -------------------------------------------------------

#: 材料大类的匹配顺序 —— **长前缀优先**
#: （``PET`` 必须排在 ``PE`` 之前，否则 ``'PET'.startswith('PE')`` 会误匹配成 PE）
_MATERIAL_FAMILY_ORDER = (
    'PP', 'PBT', 'PET', 'PE',      # PE 匹配 PE / HDPE / LDPE / LLDPE
    'PS', 'ABS', 'AS',
    'PC', 'PA', 'POM', 'PMMA',
    'PVC',
)


def parse_material_family(abbreviation: str) -> str:
    """材料缩写 → 材料大类。

    例：``'PA66+GF30' → 'PA'``、``'PC+ABS' → 'PC'``、``'PET' → 'PET'``、
    ``'HDPE' → 'PE'``。

    Args:
        abbreviation: 材料缩写（简称或全名均可）。

    Returns:
        材料大类（``PP`` / ``PE`` / ``PS`` / ``ABS`` / ``AS`` / ``PC`` / ``PA`` /
        ``POM`` / ``PMMA`` / ``PVC`` / ``PET`` / ``PBT``）；**识别不出返回空串**
        （调用方据此走默认系数兜底，**不报错、不阻塞**）。
    """
    if not abbreviation:
        return ''
    abbrev = str(abbreviation).upper().strip()
    for family in _MATERIAL_FAMILY_ORDER:
        if abbrev.startswith(family):
            return family
    return ''


# --- 派生公式 -----------------------------------------------------------


def compute_cool_time(max_thickness: float, family: str = '') -> float:
    """基础冷却时间 [s]（**物理公式的基础项**）。

    公式：``t = max(COOL_TIME_MIN, 最大壁厚² × 材料系数)``

    物理依据：Fourier 热扩散 —— 冷却时间 ∝ 壁厚² / 热扩散系数，
    材料系数是热扩散系数差异的归一化表达。

    【注意】**不含 ΔT_factor（模温差修正）与 crystallinity_kick（结晶拉长）**：
    这两项依赖具体材料参数（推荐熔温 / 模温 / 顶出温度 / 结晶类别），
    在 expert 侧实现；若要纳入完整 4 维公式，应先从 expert 侧抽公共函数。

    Args:
        max_thickness: 制品最大壁厚 [mm]。
        family: 材料大类（见 :func:`parse_material_family`）；**空串 ⇒ 默认系数**。

    Returns:
        基础冷却时间 [s]（已按 :data:`COOL_TIME_MIN` 钳制下界）。
    """
    factor = COOL_FAMILY_FACTOR.get(family, DEFAULT_COOL_FACTOR)
    return max(COOL_TIME_MIN, (max_thickness ** 2) * factor)


__all__ = [
    "COOL_FAMILY_FACTOR",
    "DEFAULT_COOL_FACTOR",
    "COOL_TIME_MIN",
    "parse_material_family",
    "compute_cool_time",
]