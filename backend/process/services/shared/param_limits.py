"""参数限值 —— **准备允许区间 + 校验参数**（service 层，单文件双职责）。

本模块做两件事：

1. **准备**：从设定值上下文取出各设定工艺参数的**允许区间**（:func:`build_limits`）；
2. **校验**：当前值 vs 允许区间 ⇒ 越界项（:func:`find_over_limits`）/ 按严格度
   处理（:func:`guard_parameter_limits`）。

**按配置决定校验范围**：参数没登记区间来源 ⇒ 不进表 ⇒ 不判；不臆造限值、
不报错、不阻塞。

**用 ``strict`` 开关控制拒不拒**：strict=True ⇒ 命中即 400；strict=False ⇒
放行并返回越界项。

**对所有参数一视同仁**：都跟允许区间比，不分类、不设特例；差别只在「上限取自
哪个设备字段」。区间统一成 ``(下限, 上限)``（``None`` 表示该侧不限）⇒ 比较
逻辑只有一种。

**全程业务命名空间**：本模块产出与消费的键**一律是业务键**（``inj_pres`` /
``met_end_pos``）—— 入参校验、第4层越限识别、给算法的限值表都如此
⇒ **算法族（``IP`` / ``IL``）不出 service 层**；算法侧要的族表由算法层自己
从业务键表翻译（``fuzzy.device_limits.to_family_limits``）。

**把上限来源的声明权留在 service 层**：算法层只做字段映射与限值表处理，不持有
「哪个参数配哪个上限」的知识。

**零算法层依赖**（不 import ``process.algorithms.*``）。
"""
import logging
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Dict, List, NamedTuple, Optional, Tuple

from extensions.exceptions import BizException, ERROR_DATA_INVALID

from .param_naming import param_label  # 业务字段名 → 中文标签

_logger = logging.getLogger(__name__)

__all__ = [
    # --- 一、准备（允许区间表）---
    'Limit',
    'LimitSpec',
    'LIMIT_SOURCES',
    'build_limits',
    'read_positive_float',
    # --- 二、校验（业务键 vs 允许区间）---
    'OverLimit',
    'find_over_limits',
    'guard_parameter_limits',
    'format_over_limit_message',
    'format_limit_number',
    # --- 三、产出侧（第4层，业务键 vs 标量上限）---
    'OverLimitItem',
    'detect_over_limits',
    'format_unfit_param_message',
    'to_upper_limits',
]


#: 允许区间：``(下限, 上限)``；``None`` 表示该侧不限。
Limit = Tuple[Optional[float], Optional[float]]


# =============================================================================
# 一、准备 —— 允许区间表（业务键命名空间）
# =============================================================================

class LimitSpec(NamedTuple):
    """某个设定工艺参数的**允许区间**怎么来。

    Attributes:
        high: 上界取值字段（可设定最大值 / 实测注射行程）；``None`` = 不限。
        low: 下界取值字段；``None`` = **下界取 0**（这类来源的参数不会为负）。
    """

    high: Optional[str] = None
    low: Optional[str] = None


#: **设定工艺参数（ORM / 业务命名）→ 允许区间来源** —— 唯一真相源。
#:
#: **用 ORM / 业务命名**（``inj_pres`` / ``inj_pres_1``）—— 算法名（``IP``）
#:  只是算法线的内部命名，不是参数本身的名字。
#: **分段参数写前缀**（``inj_pres_1..6`` ⇒ 键写 ``inj_pres``），**整段参数写
#:  全名**（``met_end_pos`` / ``vps_pos``）。
#: **新增来源 = 加一行**：清单只认「哪个设定参数、配了哪个上限字段」，不绑
#:  「机器」这个实体 ⇒ 辅机的设定上限同样在此登记。
LIMIT_SOURCES: Dict[str, LimitSpec] = {
    # ---- 可设定最大值（不会设负值 ⇒ 下界 0）----
    'inj_pres':      LimitSpec(high='max_set_injection_pressure'),
    'inj_spd':       LimitSpec(high='max_set_injection_speed'),
    'hold_pres':     LimitSpec(high='max_set_holding_pressure'),
    'hold_spd':      LimitSpec(high='max_set_holding_speed'),
    'met_pres':      LimitSpec(high='max_set_metering_pressure'),
    'met_back_pres': LimitSpec(high='max_set_metering_back_pressure'),
    'met_rot_spd':   LimitSpec(high='max_set_screw_rotation_speed'),
    # ---- 上限取自实测注射行程（**同一个数**）----
    'inj_pos':       LimitSpec(high='max_injection_stroke'),
    'met_pos':       LimitSpec(high='max_injection_stroke'),
    'met_end_pos':   LimitSpec(high='max_injection_stroke'),
    'vps_pos':       LimitSpec(high='max_injection_stroke'),
}


def build_limits(machine_info: Dict[str, Any]) -> Dict[str, Limit]:
    """设定值上下文 → {参数键: 允许区间}（**唯一一张表**）。

    【注意】**只收正数、下界恒为 0**：上限 ≤ 0 视为「没录」⇒ 该参数整体不产出；
    ``LimitSpec.low`` 为字段名时才从数据取下界，否则取 0。

    Args:
        machine_info: 设定值所在上下文的扁平 dict（键为 ORM 字段名，如
            'max_set_injection_pressure'）—— 注塑机射台与辅机的设定上限配置
            都在这里，谁配了谁生效。

    Returns:
        {参数键: (下限, 上限)}，如 ``{'inj_pres': (0.0, 100.0)}``；缺配置的
        参数不出现。
    """
    info = machine_info or {}
    limits: Dict[str, Limit] = {}
    for param_name, spec in LIMIT_SOURCES.items():
        high = read_positive_float(info, spec.high) if spec.high else None
        if high is None:
            continue
        low = read_positive_float(info, spec.low) if spec.low else 0.0
        limits[param_name] = (low, high)
    return limits


def to_upper_limits(business_limits: Mapping[str, Limit]) -> Dict[str, float]:
    """业务键区间表 → 业务键**标量上限**表（**取区间上界**）。

    第4层判的是「单参数 vs 它自己的上限」⇒ 上限表的值是**标量**；
    而 :func:`build_limits` 产出的是**区间** ``(下限, 上界)`` ⇒ 这里取高位。

    【注意】**键空间不变**（仍是业务键）：族前缀（``inj_pres``）与整段全名
    （``met_end_pos``）都留在表里 ⇒ 第4层全程业务命名空间，算法族不出 service 层。

    【注意】**缺上界就不进表**（``None`` / 非数值）⇒ 不臆造限值。

    Args:
        business_limits: 业务键 → 允许区间（:func:`build_limits` 的产物）。

    Returns:
        业务键 → 上限值；缺上界的业务键不出现。
    """
    if not business_limits:
        return {}
    upper: Dict[str, float] = {}
    for business_key, interval in business_limits.items():
        if not interval:
            continue
        high = interval[1]
        if high is None:
            continue
        try:
            upper[business_key] = float(high)
        except (TypeError, ValueError):
            continue
    return upper


def read_positive_float(
    info: Dict[str, Any],
    field_name: str,
) -> Optional[float]:
    """从设定值上下文里读一个**正数**值（缺值 / 非数值 / 非正数 ⇒ 不产出）。

    【注意】**NaN 不产出**：``float('nan') > 0`` 恒为 False ⇒ NaN 走「不产出」分支。
    （NaN 若被放行成上限，下游「当前值 ≤ 上限」恒为 False ⇒ 配了上限的参数
    **全部**被判超限 ⇒ 误拒整轮优化。）

    Args:
        info: 设定值所在上下文的扁平 dict（键为 ORM 字段名）。
        field_name: 配置字段名。

    Returns:
        Optional[float]: 正数取值；缺值 / 非数值 / 非正数时返回 None。
    """
    raw = info.get(field_name)
    if raw is None:
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


# =============================================================================
# 二、校验 —— 业务键 vs 允许区间（入参校验）
# =============================================================================


@dataclass(frozen=True)
class OverLimit:
    """一条越界事实（**纯识别结果**，不含任何处理动作）。

    Attributes:
        param_name: 越界的工艺参数名（ORM / 业务命名，如 ``'inj_pres_1'``）。
        current_value: 当前值。
        interval: 该参数的允许区间 ``(下限, 上限)``；``None`` 表示该侧不限。
        side: 越的是哪一侧 —— ``'lower'``（低于下界）/ ``'upper'``（高于上界）。
    """

    param_name: str
    current_value: float
    interval: Limit
    side: str


#: 段号后缀（``inj_pres_1`` → ``inj_pres``）—— 分段参数靠它归到前缀。
_SEGMENT_SUFFIX = re.compile(r'_\d+$')


def _match_limit(param_name: str, limits: Mapping[str, Limit]) -> Optional[Limit]:
    """参数名 → 它该比的那个允许区间（**找不到就返回 None ⇒ 不比**）。

    两级匹配：
      ① **整段参数**精确命中（``met_end_pos`` / ``vps_pos``）；
      ② **分段参数**去掉末尾段号后命中前缀（``inj_pres_1`` → ``inj_pres``）。

    Args:
        param_name: 工艺参数名（ORM / 业务命名）。
        limits: 允许区间表（键为参数名或参数前缀）。

    Returns:
        Optional[Limit]: 命中的区间；没有登记该参数 ⇒ None（不参与比较）。
    """
    if not param_name or not limits:
        return None
    if param_name in limits:
        return limits[param_name]
    prefix = _SEGMENT_SUFFIX.sub('', param_name)
    if prefix == param_name:
        return None
    return limits.get(prefix)


def find_over_limits(parameters: Mapping[str, float],
                     limits: Mapping[str, Limit]) -> List[OverLimit]:
    """**通用参数区间校验**：工艺参数 vs 允许区间 ⇒ 越界项。

    Args:
        parameters: 待比较的工艺参数值（ORM / 业务命名，如 ``{'inj_pres_1': 200.0}``）。
        limits: 允许区间表（:func:`build_limits` 的产出）。

    Returns:
        越界项列表（一个参数两侧都越时会产出两条）。
    """
    over: List[OverLimit] = []
    for name, raw_value in (parameters or {}).items():
        bound = _match_limit(name, limits)
        if bound is None:
            continue
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            continue
        low, high = bound
        if low is not None and value < low:
            over.append(OverLimit(name, value, bound, 'lower'))
        if high is not None and value > high:
            over.append(OverLimit(name, value, bound, 'upper'))
    return over


def format_limit_number(value: Any) -> str:
    """上限 / 当前值的展示格式：整数不带小数尾巴（'100' 而不是 '100.0000'）。

    两条链路共用同一份展示规则 ⇒ 同一台机、同一产品，两边报错的数字长得一样。
    """
    try:
        if float(value) == int(value):
            return str(int(value))
    except (TypeError, ValueError):
        pass
    return ('%.4f' % value).rstrip('0').rstrip('.')


def format_over_limit_message(items: List[OverLimit]) -> str:
    """越界文案 —— 说清「哪个参数 / 当前值 / 允许区间」。

    **面向工艺员，用中文标签**：参数名 ``inj_pres_1`` 对用户没意义，显示 spec 里的
    字段描述（「一段注射压力」）才看得懂是哪个设定工艺。
    """
    details = []
    for item in items[:3]:
        low, high = item.interval
        details.append('%s 当前 %s 超出允许区间 [%s, %s]' % (
            param_label(item.param_name),
            format_limit_number(item.current_value),
            '不限' if low is None else format_limit_number(low),
            '不限' if high is None else format_limit_number(high)))
    if len(items) > 3:
        details.append('等 %d 项' % len(items))
    return '；'.join(details)


def guard_parameter_limits(
    *,
    parameters: Mapping[str, Any],
    limits: Mapping[str, Limit],
    strict: bool = True,
    scope: str = 'unknown',
    interface_tag: str = '',
) -> List[OverLimit]:
    """**统一的参数区间守卫** —— 越界 ⇒ strict 抛 400 / 非 strict 放行并返回越界项。

    Args:
        parameters: 待校验的工艺参数值（ORM / 业务命名，如 ``{'inj_pres_1': 200.0}``）。
        limits: 允许区间表（:func:`build_limits` 的产出）。
        strict: True ⇒ 越界即拒绝（400）；False ⇒ 只报不拒（返回越界项）。
        scope: 日志前缀用的链路标识（``'optimize'`` / ``'initialize'``）。
        interface_tag: 本次调用标识（进日志，便于定位是哪一次调用）。

    Returns:
        越界项列表（strict=True 时命中即抛异常 ⇒ 不会返回）。

    Raises:
        BizException(ERROR_DATA_INVALID): strict=True 且命中越界。
    """
    over = find_over_limits(parameters, limits)
    if not over:
        return []
    message = format_over_limit_message(over)
    trace = [(item.param_name, item.current_value, item.interval) for item in over]
    if strict:
        _logger.warning('[%s] %s 越界拒绝: %s ｜ %s', scope, interface_tag, trace, message)
        raise BizException(ERROR_DATA_INVALID, message + '，请修正后再试')
    _logger.warning('[%s] %s 越界告警（不阻断）: %s ｜ %s', scope, interface_tag, trace, message)
    return over


# =============================================================================
# 三、产出侧（第4层）—— 业务键 vs 标量上限
# =============================================================================


@dataclass(frozen=True)
class OverLimitItem:
    """一条越限记录（**纯识别结果**，不含任何处理动作）。

    Attributes
    ----------
    param_name : str
        业务字段名（如 ``inj_pres_1`` / ``met_end_pos``）。
    param_family : str
        业务族前缀（如 ``inj_pres``）—— 上限是**按族**给的；整段参数为空串。
    current_value : float
        当前值。
    limit : float
        该参数适用的上限值。
    limit_field : str
        上限来源的**设备字段名**（如 ``max_injection_stroke`` /
        ``max_set_injection_pressure``）⇒ **溯源用**：看得出这个上限取自
        哪个能力项（注射行程 / 注射压力 …）。
    exceeded_by : float
        超出量（``current_value - limit``）。
    exceeded_ratio : float
        超出比例（``(current_value - limit) / limit``）。
    """

    param_name: str
    param_family: str
    current_value: float
    limit: float
    limit_field: str
    exceeded_by: float
    exceeded_ratio: float

    def to_trace(self) -> Dict[str, Any]:
        """→ 可 JSON 序列化的留痕（进诊断容器 ⇒ **只进日志**，不进推荐结果）。"""
        return {
            'param': self.param_name,
            'family': self.param_family,
            'current_value': self.current_value,
            'limit': self.limit,
            'limit_field': self.limit_field,
            'exceeded_by': self.exceeded_by,
            'exceeded_ratio': self.exceeded_ratio,
        }


def _limit_field_for(business_name: str) -> str:
    """业务字段名 → 它那个上限的**来源设备字段名**（溯源用）。

    两级匹配（与 :func:`_match_limit` 同一套规则）：
      ① **整段参数**精确命中（``met_end_pos`` / ``vps_pos``）；
      ② **分段参数**去掉末尾段号后命中前缀（``inj_pres_1`` → ``inj_pres``）。

    **溯源直接用设备字段名**，不另设「来源类型」标记。

    Args:
        business_name: 业务字段名（带段号或整段全名）。

    Returns:
        str: 设备字段名（如 ``max_injection_stroke``）；查不到 ⇒ 空串。
    """
    if not business_name:
        return ''
    spec = LIMIT_SOURCES.get(business_name)
    if spec is None:
        prefix = _SEGMENT_SUFFIX.sub('', business_name)
        if prefix != business_name:
            spec = LIMIT_SOURCES.get(prefix)
    return spec.high if spec is not None and spec.high else ''


def _business_family(business_name: str) -> str:
    """业务字段名 → 业务族前缀（整段参数无族 ⇒ 空串）。

    分段参数去掉末尾段号（``inj_pres_1`` → ``inj_pres``）；整段参数
    （``met_end_pos`` / ``vps_pos``）没有段号 ⇒ 空串。
    """
    if not business_name:
        return ''
    prefix = _SEGMENT_SUFFIX.sub('', business_name)
    return prefix if prefix != business_name else ''


def _lookup_upper_limit(business_name: str, limits: Mapping[str, float]) -> Optional[float]:
    """业务字段名 → 该参数适用的上限（无上限返回 None）。

    **两级匹配**（与 :func:`_match_limit` 同一套规则）：
      ① **精确匹配** —— 整段参数（``met_end_pos`` / ``vps_pos``）在表里就是键本身；
      ② **族前缀匹配** —— 分段参数（``inj_pres_1``）去掉末尾段号后命中族键
         （``inj_pres``）；族键表就是 :data:`LIMIT_SOURCES` 的键（业务命名空间）
         ⇒ **单一真相源**，不另设族表。
    """
    if not business_name or not limits:
        return None
    if business_name in limits:
        return limits[business_name]
    prefix = _business_family(business_name)
    if not prefix:
        return None
    return limits.get(prefix)


def detect_over_limits(
    process_parameter: Dict[str, Any],
    limits: Dict[str, float],
) -> List[OverLimitItem]:
    """识别「当前值超过上限」的参数（**产出侧第4层在用**，只识别、不处理）。

    【注意】**本函数用业务字段名命名空间**（上限表 = 业务键 → 标量上限，
    参数按业务命名）⇒ 第4层全程业务命名空间，**算法族不出 service 层**；
    入参校验（:func:`find_over_limits` / :func:`guard_parameter_limits`）同口径。

    【注意】**表里没有的参数一律不判**：参数没登记上限来源 ⇒ 无从判断；
    机台没录上限 ⇒ 缺数据不等于参数不合理。

    Args:
        process_parameter: 业务命名的工艺参数当前值（``{'inj_pres_1': 150.0}``）。
        limits: 上限表（键 = 业务族前缀或整段业务参数名 → 上限值）。

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

        limit = _lookup_upper_limit(param_name, limits)
        if limit is None:
            # 无适用上限（机台没录）⇒ 无从判断
            continue
        try:
            limit = float(limit)
        except (TypeError, ValueError):
            continue
        if limit <= 0.0:
            # 无效上限 ⇒ 不判（避免把 0 当成「上限是 0」而误报）
            continue
        if current <= limit:
            continue

        exceeded_by = current - limit
        items.append(OverLimitItem(
            param_name=param_name,
            # 整段参数（met_end_pos / vps_pos）没有族前缀 ⇒ 留空
            param_family=_business_family(param_name),
            current_value=current,
            limit=limit,
            # 溯源：上限取自哪个设备字段（注射行程 / 注射压力 …）
            limit_field=_limit_field_for(param_name),
            exceeded_by=exceeded_by,
            exceeded_ratio=exceeded_by / limit,
        ))
    return items


def format_unfit_param_message(items: List[OverLimitItem]) -> str:
    """参数超出机台可设定上限的用户文案（**单一文案源**）。

    多个参数同时超限（IL0 / ML0 / MEL 一起超）⇒ 合并成一条：
    它们说的是同一件事（这台机设不进这个参数），逐条提示只会刷屏。
    取**超出量最大**的那项作代表。

    **只说事实、给出两条出路**：出路是「**检查参数设置 或 更换设备**」
    —— 超出上限有两种可能：① 机台能力确实不够（换机）；② **用户误输入**
    （改参数即可）⇒ 结论不预设，错误码标题也只说「参数不符合机台设定要求」。

    **单位不硬编码**（压力 MPa、位置 mm、转速 rpm 各不同）⇒ 由标签体现所属能力项。

    【注意】**供调用方复用**：识别结论若已由别处（如第4层校验）产出，
    仍走这里出文案 ⇒ 同一判据、同一文案，不会两处漂移。

    Args:
        items: 超出机台可设定上限的记录（:func:`detect_over_limits` 的产物）。

    Returns:
        面向用户的文案。
    """
    top = max(items, key=lambda item: item.exceeded_by)
    others = len(items) - 1
    label = param_label(top.param_name)
    return (
        '%s需 %s，超出本机可设定上限 %s%s，请检查参数设置或更换设备'
        % (label,
           format_limit_number(top.current_value),
           format_limit_number(top.limit),
           ('（另有 %d 项超出可设定上限）' % others) if others else '')
    )
