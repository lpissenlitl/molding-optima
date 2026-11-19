"""越限识别与**安全分层** —— 把「当前值超过本机可设定上限」这件事识别出来，
并按**上限来源**标明它属于哪一层风险。

为什么单独一个模块：
  「当前值越限」横跨**输入**（工艺参数当前值）与**设备能力**（`machine_info` 的
  物理上限），两边都不拥有它 ⇒ 放进任一层都会越位。

安全分层（用户口径：「不同的参数其实是有安全分层的概念，不是统一界定」）：

  =============  ==========  ==================================  ============
  limit_source   参数类型     风险性质                             处理
  =============  ==========  ==================================  ============
  device        设定值类     **操作设备涉及安全** —— 上限 100 而   **拒绝** 400
                             人为设 200 ⇒ 严重风险
  stroke        位置类       **产品做不出来** —— 当前值超出设备   留痕（不阻断）
                             注射行程 ⇒ 这台机做不出这个产品
  material      温度类       材料降解 / 变色（不涉及设备操作安全） 告警 / 兜底
  （无上限）      时间类       无设备约束                            不识别
  =============  ==========  ==================================  ============

【注意】``device`` 与 ``stroke`` 的**根本差别**（决定了处理方式不能统一）：
  - ``device``（设定值类）= 用户把某个参数**设错了**，改个值就好 ⇒ 值得拦；
  - ``stroke``（位置类）= **这个产品在这台设备上做不出来**（实测 MEL 56/70 行
    超行程：行程 200mm 而产品充填需 291mm）⇒ 用户**改不了** ⇒ 拦了也没有出路。
⇒ ``stroke`` **永不进** :data:`BLOCKING_LIMIT_SOURCES`。

【注意】**本模块不抛异常、不改建议**：
  - **不告警**：不改 `AlgorithmRecommendation`，不产出 `fuzzy.check` 文本建议；
  - **不拒绝**：`engine.recommend()` 的异常边界会把任何异常**降级成空推荐**
    （"什么都给不出来"，比不拦更糟）⇒ 拒绝必须由 **service 层**在**调用算法之前**
    转 `BizException`（`parameter_optimize._guard_over_limit_settings`）；
    判据是**纯事实**（当前设定值 vs 机台上限）⇒ 不需要结论做参照；
  - **不改建议**：推荐值侧的封顶裁剪在 `engine._apply_machine_limits`，本模块不碰。

本模块负责的是**分层口径**（哪些来源会阻断），**判定与拒绝的执行**在 service 层。

数据来源：
  - 上限：:func:`specs.resolve_param_limits`（机台物理天花板，7 个设定值类族）；
  - 参数名 → 族：:func:`specs.param_family`（`IP0` → `IP`）；
  - 位置类上限：:func:`specs.resolve_position_limits`（设备实测最大注射行程）。
"""
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from process.algorithms.fuzzy.field_names import to_business_name
from process.algorithms.fuzzy.specs import lookup_position_limit, param_family

# --- 上限来源（= 安全分层的维度）---
# 'device'   —— 机台物理上限（操作设备涉及安全）⇒ 越限必须阻断
# 'material' —— 材料工艺窗口（降解/变色）⇒ 不涉及设备操作安全 ⇒ 不阻断
# 'stroke'   —— 设备实测注射行程（位置类）⇒ 产品在本机做不出来 ⇒ 不阻断
LIMIT_SOURCE_DEVICE = 'device'
LIMIT_SOURCE_MATERIAL = 'material'
LIMIT_SOURCE_STROKE = 'stroke'

#: 会**阻断请求**的上限来源集合（分层口径固化在算法契约层，不写死在 service）。
BLOCKING_LIMIT_SOURCES = frozenset({LIMIT_SOURCE_DEVICE})

__all__ = [
    'OverLimitItem',
    'detect_over_limits',
    'detect_over_stroke_limits',
    'detect_blocking_over_limits',
    'LIMIT_SOURCE_DEVICE',
    'LIMIT_SOURCE_MATERIAL',
    'LIMIT_SOURCE_STROKE',
    'BLOCKING_LIMIT_SOURCES',
]


@dataclass(frozen=True)
class OverLimitItem:
    """一条越限记录（**纯识别结果**，不含任何处理动作）。

    Attributes
    ----------
    param_name : str
        算法参数名（如 ``IP0``）。
    param_family : str
        参数族前缀（如 ``IP``）—— 上限是**按族**给的。
    business_name : str
        业务字段名（如 ``inj_pres_1``）；映射不到时回落成算法参数名。
    current_value : float
        当前值。
    limit : float
        该参数适用的上限值。
    limit_source : str
        上限来源标记（``device`` = 机台物理上限；未来的 ``material`` = 材料上限）
        ⇒ **后续分层处理的依据**，本模块只透传、不解释。
    exceeded_by : float
        超出量（``current_value - limit``）。
    exceeded_ratio : float
        超出比例（``(current_value - limit) / limit``）。
    """

    param_name: str
    param_family: str
    business_name: str
    current_value: float
    limit: float
    limit_source: str
    exceeded_by: float
    exceeded_ratio: float

    def to_trace(self) -> Dict[str, Any]:
        """→ 可 JSON 序列化的留痕（进诊断容器 ⇒ **只进日志**，不进推荐结果）。"""
        return {
            'param': self.param_name,
            'family': self.param_family,
            'business_name': self.business_name,
            'current_value': self.current_value,
            'limit': self.limit,
            'limit_source': self.limit_source,
            'exceeded_by': self.exceeded_by,
            'exceeded_ratio': self.exceeded_ratio,
        }


def detect_over_limits(
    process_parameter: Dict[str, Any],
    limits: Dict[str, float],
    limit_source: str = 'device',
) -> List[OverLimitItem]:
    """识别「当前值超过上限」的参数（**只识别，不处理**）。

    Args:
        process_parameter: 算法命名的工艺参数当前值（``{'IP0': 200.0, ...}``）。
        limits: 参数族 → 上限（``{'IP': 100.0, ...}``）；由
            :func:`specs.resolve_param_limits`（机台）或未来的材料来源提供。
        limit_source: 上限来源标记（``device`` / 未来的 ``material``）
            ⇒ 后续分层处理的依据，本模块只透传。

    Returns:
        越限记录列表（**按参数名排序** ⇒ 结果可复现）。
    """
    if not process_parameter or not limits:
        return []

    items: List[OverLimitItem] = []
    for param_name in sorted(process_parameter):
        value = process_parameter[param_name]
        if value is None or isinstance(value, bool):
            continue
        try:
            current = float(value)
        except (TypeError, ValueError):
            continue

        family = param_family(param_name)
        if family is None:
            # 整段参数（IPOS 注射位置 / NT 喷嘴温度 / MT 模温）没有族前缀
            # ⇒ 没有机台上限 ⇒ 无从判断越限
            continue
        limit = limits.get(family)
        if limit is None:
            # 该族没有上限（温度类 / 时间类当前就是这种）⇒ 无从判断
            continue
        try:
            limit = float(limit)
        except (TypeError, ValueError):
            continue
        if limit <= 0.0:
            # 无效上限 ⇒ 不据此判定越限（避免把 0 当成"上限是 0"而误报）
            continue
        if current <= limit:
            continue

        exceeded_by = current - limit
        items.append(OverLimitItem(
            param_name=param_name,
            param_family=family,
            business_name=to_business_name(param_name) or param_name,
            current_value=current,
            limit=limit,
            limit_source=limit_source,
            exceeded_by=exceeded_by,
            exceeded_ratio=exceeded_by / limit,
        ))
    return items


def detect_over_stroke_limits(
    process_parameter: Dict[str, Any],
    position_limits: Dict[str, float],
) -> List[OverLimitItem]:
    """识别位置类参数的「当前值超出设备注射行程」（**只识别，不处理**）。

    与 :func:`detect_over_limits` 的两处区别：

    1. **匹配方式**：那边按**族前缀**查（:func:`specs.param_family`）⇒ 只能覆盖
       设定值类（``IP0`` → ``IP``）；位置类既有分段（``IL0``~``IL5`` /
       ``ML0``~``ML3``）也有**整段**（``MEL`` / ``VPTL``），整段取不到族 ⇒ 走
       位置类自己的**两级匹配**（:func:`specs.lookup_position_limit`）。
    2. **风险性质不同** ⇒ 处理方式不能统一（详见模块 docstring 的安全分层表）：
       设定值类超限 = 用户把参数设错了（改个值就好）⇒ 阻断；位置类超行程 =
       **这个产品在这台设备上做不出来**（实测 MEL 56/70 行超行程）⇒ 用户改不了
       ⇒ **只留痕，永不阻断**。

    【注意】本函数的产出**永远不进** :data:`BLOCKING_LIMIT_SOURCES`
    ⇒ 不参与 :func:`detect_blocking_over_limits` ⇒ service 层不会 400。

    Args:
        process_parameter: 算法命名的工艺参数当前值（``{'MEL': 491.04, ...}``）。
        position_limits: :func:`specs.resolve_position_limits` 的产物
            （位置类参数名 / 族前缀 → 设备实测行程）。

    Returns:
        超出行程的记录列表（**按参数名排序** ⇒ 结果可复现）。
    """
    if not process_parameter or not position_limits:
        return []

    items: List[OverLimitItem] = []
    for param_name in sorted(process_parameter):
        value = process_parameter[param_name]
        if value is None or isinstance(value, bool):
            continue
        try:
            current = float(value)
        except (TypeError, ValueError):
            continue

        limit = lookup_position_limit(param_name, position_limits)
        if limit is None:
            # 该参数不是位置类 / 没有权威源（机台没录行程）⇒ 无从判断
            continue
        try:
            limit = float(limit)
        except (TypeError, ValueError):
            continue
        if limit <= 0.0:
            continue
        if current <= limit:
            continue

        exceeded_by = current - limit
        items.append(OverLimitItem(
            param_name=param_name,
            # 位置类的整段参数（MEL / VPTL）**没有族前缀** ⇒ 留空
            param_family=param_family(param_name) or '',
            business_name=to_business_name(param_name) or param_name,
            current_value=current,
            limit=limit,
            limit_source=LIMIT_SOURCE_STROKE,
            exceeded_by=exceeded_by,
            exceeded_ratio=exceeded_by / limit,
        ))
    return items


def detect_blocking_over_limits(
    process_parameter: Dict[str, Any],
    limits: Dict[str, float],
    limit_sources: Optional[Iterable[str]] = None,
) -> List[OverLimitItem]:
    """只返回**会阻断请求**的越限项（安全分层的落地口径）。

    分层规则固化在算法契约层（不写死在 service）：阻断与否只看
    ``limit_source`` —— 默认只有 ``device``（设备安全红线）阻断；
    ``material``（材料降解/变色）不阻断 —— 风险性质不同，不该用同一把尺子。

    Args:
        process_parameter: 算法命名的工艺参数当前值（``{'IP0': 200.0, ...}``）。
        limits: 参数族 → 上限（``{'IP': 100.0, ...}``）。
        limit_sources: 视为「阻断」的来源集合；None ⇒ 用
            :data:`BLOCKING_LIMIT_SOURCES`。

    Returns:
        需要阻断的越限记录列表（**按参数名排序** ⇒ 结果可复现）。
    """
    items = detect_over_limits(process_parameter, limits)
    allowed = (BLOCKING_LIMIT_SOURCES if limit_sources is None
               else frozenset(limit_sources))
    return [item for item in items if item.limit_source in allowed]
