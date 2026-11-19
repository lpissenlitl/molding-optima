"""第4层：校验参数合理性 —— **只读**的合理性检查（不传导、不改值）。

这一层回答一个问题：**这份参数集合不合理。**

定位（用户口径）：

- **参数检查是通用能力** —— 对工艺参数看现状，任何时候都能跑
  （初始化后、手工编辑保存前、优化前后），与「这次改动从哪来」无关；
- 与第3层整合是**两回事**：

  ==================  ==========================  =====================
  用法                输入                        输出
  ==================  ==========================  =====================
  整合（第3层）        改了哪些 + 参数集            连带算出来的参数集（改值）
  校验（本模块）      只有参数集                  哪里不合理（**不改值**）
  ==================  ==========================  =====================

  两者**共用同一批字段口径与锚点关系**（如 ``met_pos_{N}`` = 末段熔胶位置）。

三类检查的分工：

============  =======================================  ====================
检查          查什么                                  参照系
============  =======================================  ====================
差值越限      组内差值是否超限（行程约束的是位移）    设备物理行程
经验窗口      量是否落在经验区间外                    材料 × 壁厚经验值
锚点自检      量之间的锚点关系是否还成立              锚点关系本身
============  =======================================  ====================

与既有越限识别的分工：

- ``fuzzy/over_limit.py``：**单参数 vs 一个上限**（设备/材料上限），
  已在模糊推理主链路上；
- 本模块：**差值越限**（两个参数各自都不超限，但它们的**差值**超限）
  与**工艺窗口越限**（经验区间）。

只识别不处理：越限的**处理**（拒绝 / 裁剪 / 提示）落在 service 层，
识别层只透传事实，不拒绝、不截断。

字段名：**代码侧**业务字段名（与 ``ProcessParameterSchema`` 对齐）；
与算法/工艺侧命名的对照见 :mod:`process.algorithms.integrate_params` 的模块 docstring。
"""

from dataclasses import dataclass
from typing import Dict, List, Mapping, Optional, Tuple

from .anchors import (
    G1_AUTO_FIELD,
    G1_BACKOFF_FIELD,
    G2_VPS_FIELD,
    find_chain_break,
    last_stage_field,
    resolve_stage_count,
)


# --- 差值越限识别 ---------------------------------------------------------

@dataclass(frozen=True)
class RangeViolation:
    """一组量的越界事实。

    Attributes:
        range_id: 越界项标识。
        label: 业务说明。
        actual: 实际值（差值或单值）。
        limit: 限值。
        limit_source: 限值来源（``device`` / ``stroke`` 等）。
        members: 参与计算的业务字段名。
    """

    range_id: str
    label: str
    actual: float
    limit: float
    limit_source: str
    members: Tuple[str, ...] = ()


#: 差值越限检查项：**差值**才是设备行程约束的对象，
#: 单个位置不超行程并不代表位移不超行程。
RANGE_CHECKS: Tuple[Dict[str, object], ...] = (
    {
        'range_id': 'injection_stroke',
        'label': '注射行程（末段熔胶位置 − VP 切换位置）',
        'members': ('met_pos_{last}', 'vps_pos'),
        'limit_source': 'stroke',
    },
    {
        'range_id': 'meter_end_position',
        'label': '储料终止位置',
        'members': ('met_end_pos',),
        'limit_source': 'stroke',
    },
)


def detect_range_violations(
    params: Mapping[str, float],
    limits: Mapping[str, float],
    checks: Tuple[Dict[str, object], ...] = RANGE_CHECKS,
) -> List[RangeViolation]:
    """识别「组内差值」越界（**只识别，不处理**）。

    单参数越界由各算法包自己的越限识别层负责；本函数补的是**差值**这一类：
    两个参数各自都不超限，但它们的差值超限。

    Args:
        params: 当前工艺参数（业务字段名 → 数值）。
        limits: 限值表（``range_id`` → 限值）。
        checks: 检查项定义。

    Returns:
        越界项列表（按 ``range_id`` 排序，结果可复现）。
    """
    violations: List[RangeViolation] = []
    stage_count = 0
    raw_stage = params.get('met_stg')
    if raw_stage is not None:
        try:
            stage_count = int(raw_stage)
        except (TypeError, ValueError):
            stage_count = 0

    for check in checks:
        limit = limits.get(str(check['range_id']))
        if limit is None:
            continue
        members = list(check['members'])
        values: List[float] = []
        resolved: List[str] = []
        for member in members:
            name = member.replace('{last}', str(stage_count)) if '{last}' in member else member
            value = params.get(name)
            if value is None:
                values = []
                break
            values.append(float(value))
            resolved.append(name)
        if not values:
            continue
        actual = values[0] - sum(values[1:]) if len(values) > 1 else values[0]
        if actual > limit:
            violations.append(
                RangeViolation(
                    range_id=str(check['range_id']),
                    label=str(check['label']),
                    actual=actual,
                    limit=float(limit),
                    limit_source=str(check['limit_source']),
                    members=tuple(resolved),
                )
            )
    violations.sort(key=lambda item: item.range_id)
    return violations


# --- 工艺窗口校验 ---------------------------------------------------------

#: 受「工艺窗口」约束的字段（业务字段名）。
#:
#: - ``inj_t``：注射时间（注射阶段是**速度控制**，设定时间只是设定值）；
#: - ``hold_t_1..5``：各段保压时间（窗口按**材料族**取：下限固定，
#:   上限 family 自适应）。
#:
#: 窗口上下限**不在本模块内置** —— 那是材料 × 壁厚维度的经验值，
#: 由调用方从工艺设定集 / 配置读出后传入 :func:`detect_window_violations`。
#:
#: 注：保压**速度**走「单参数 vs 设备上限」（HMI 值）⇒ 归 ``fuzzy/over_limit.py``，
#: 不在本清单内。
WINDOW_CONSTRAINED_FIELDS: Tuple[str, ...] = (
    'inj_t',
    'hold_t_1', 'hold_t_2', 'hold_t_3', 'hold_t_4', 'hold_t_5',
)


@dataclass(frozen=True)
class WindowViolation:
    """一个量落在工艺窗口外的越界事实。

    Attributes:
        constraint_id: 约束标识。
        label: 业务说明。
        field: 越界的业务字段名。
        actual: 当前值。
        lower: 窗口下限。
        upper: 窗口上限。
        bound: 越界侧（``lower`` / ``upper``）。
    """

    constraint_id: str
    label: str
    field: str
    actual: float
    lower: float
    upper: float
    bound: str


def detect_window_violations(
    params: Mapping[str, float],
    windows: Mapping[str, Tuple[float, float]],
) -> List[WindowViolation]:
    """识别落在工艺窗口外的量（**只识别，不处理**）。

    工艺窗口是**经验区间**（材料 × 壁厚查表），不是物理恒等式 ——
    因此越界只能提示，不能靠联动修好。

    Args:
        params: 当前工艺参数（业务字段名 → 数值）。
        windows: 窗口表（业务字段名 → ``(下限, 上限)``）；缺项即该字段不检查。

    Returns:
        越界项列表（按字段名排序，结果可复现）。
    """
    violations: List[WindowViolation] = []
    for field_name, bounds in windows.items():
        value = params.get(field_name)
        if value is None:
            continue
        lower, upper = bounds
        actual = float(value)
        if actual < float(lower):
            violations.append(
                WindowViolation(
                    constraint_id=f'{field_name}.window',
                    label=f'{field_name} 的工艺窗口',
                    field=field_name,
                    actual=actual,
                    lower=float(lower),
                    upper=float(upper),
                    bound='lower',
                )
            )
        elif actual > float(upper):
            violations.append(
                WindowViolation(
                    constraint_id=f'{field_name}.window',
                    label=f'{field_name} 的工艺窗口',
                    field=field_name,
                    actual=actual,
                    lower=float(lower),
                    upper=float(upper),
                    bound='upper',
                )
            )
    violations.sort(key=lambda item: item.field)
    return violations


# --- 锚点关系自检 ---------------------------------------------------------

@dataclass(frozen=True)
class AnchorViolation:
    """锚点关系不成立的越界事实。

    Attributes:
        anchor_id: 锚点规则标识（与 ``integration.LINK_RULES`` 的 ``rule_id`` 对应）。
        label: 业务说明（关系本身）。
        detail: 不成立的具体说明。
        members: 参与该关系的业务字段名。
    """

    anchor_id: str
    label: str
    detail: str
    members: Tuple[str, ...] = ()


def detect_anchor_violations(
    params: Mapping[str, float],
    tolerance: float = 0.01,
) -> List[AnchorViolation]:
    """识别**锚点关系不成立**的量（**只识别，不处理**）。

    与另两类检查的区别：差值越限查「量本身合不合理」，经验窗口查「量是否落在
    经验区间外」；本函数查的是「量之间的锚点关系还成不成立」⇒ 参照系是
    **锚点关系本身**（如 ``MEL = ML_N + DDAM``）。

    与第3层整合（``integration.propagate``）**共用同一批锚点事实**
    （``algorithms/anchors.py``）⇒ 一个改值、一个只读，关系只定义一次。

    数据不全时**不臆造**（回落口径）：缺段数 / 缺端点量 ⇒ 不报。

    Args:
        params: 当前工艺参数（业务字段名 → 数值）。
        tolerance: 位置类关系的允许偏差（mm）。

    Returns:
        越界项列表（按 ``anchor_id`` 排序，结果可复现）。
    """
    violations: List[AnchorViolation] = []
    stage_count = resolve_stage_count(params)
    if stage_count is None:
        return violations

    auto = params.get(G1_AUTO_FIELD)
    backoff = params.get(G1_BACKOFF_FIELD)
    last_name = last_stage_field(stage_count)
    last = params.get(last_name)
    if auto is not None and backoff is not None and last is not None:
        expected = float(last) + float(backoff)
        actual = float(auto)
        if abs(actual - expected) > tolerance:
            violations.append(
                AnchorViolation(
                    anchor_id='g1.meter_end_position',
                    label='计量终止位置 = 末段熔胶位置 + 熔胶后松退距离',
                    detail=(
                        f'{G1_AUTO_FIELD}({actual}) ≠ {last_name}({last}) + '
                        f'{G1_BACKOFF_FIELD}({backoff}) = {expected}'
                    ),
                    members=(G1_AUTO_FIELD, last_name, G1_BACKOFF_FIELD),
                )
            )

    broken = find_chain_break(params, stage_count)
    if broken is not None:
        lower, higher, detail = broken
        violations.append(
            AnchorViolation(
                anchor_id='g2.suckback_chain',
                label='各段熔胶位置严格递增，且首段大于 VP 切换位置',
                detail=detail,
                members=tuple(name for name in (lower, higher) if name != G2_VPS_FIELD),
            )
        )

    violations.sort(key=lambda item: item.anchor_id)
    return violations


# --- 第4层的统一入口 ------------------------------------------------------

@dataclass(frozen=True)
class ParamCheckReport:
    """一次校验的结果（**只报，不改**）。

    Attributes:
        range_violations: 差值越限（两个参数各自的差值超出设备行程）。
        window_violations: 工艺窗口越限（量落在经验区间外）。
        anchor_violations: 锚点关系不成立（量之间的关系对不上）。
    """

    range_violations: Tuple[RangeViolation, ...] = ()
    window_violations: Tuple[WindowViolation, ...] = ()
    anchor_violations: Tuple[AnchorViolation, ...] = ()

    @property
    def ok(self) -> bool:
        """这份参数集**没有**查出问题。"""
        return not (
            self.range_violations
            or self.window_violations
            or self.anchor_violations
        )

    def messages(self) -> Tuple[str, ...]:
        """把三类越界压成可留痕的一行行文字。"""
        messages: List[str] = []
        messages.extend(
            f'{item.range_id}: {item.actual} > {item.limit}（{item.label}）'
            for item in self.range_violations
        )
        messages.extend(
            f'{item.constraint_id}: {item.actual} 越出 '
            f'[{item.lower}, {item.upper}]（{item.bound}）'
            for item in self.window_violations
        )
        messages.extend(
            f'{item.anchor_id}: {item.detail}'
            for item in self.anchor_violations
        )
        return tuple(messages)

    def summary(self) -> str:
        """一行可读摘要（给日志用）。"""
        return (
            f'range={[item.range_id for item in self.range_violations]} '
            f'window={[item.field for item in self.window_violations]} '
            f'anchor={[item.anchor_id for item in self.anchor_violations]}'
        )


def validate(
    params: Mapping[str, float],
    limits: Optional[Mapping[str, float]] = None,
    windows: Optional[Mapping[str, Tuple[float, float]]] = None,
) -> ParamCheckReport:
    """校验一份参数集是否合理（**只识别，不处理**）。

    三类检查一次跑完，缺省参照系即「不检查」：

    - ``limits`` 缺省 ⇒ 不做**差值越限**检查；
    - ``windows`` 缺省 ⇒ 不做**工艺窗口**检查；
    - **锚点自检**永远跑（参照系就是锚点关系本身，不需要外部数据）。

    【注意】**数据不全 ⇒ 不臆造**：缺段数 / 缺端点量 ⇒ 相应项不报。

    Args:
        params: 待校验的工艺参数（业务字段名 → 数值）。
        limits: 限值表（``range_id`` → 限值）。
        windows: 窗口表（业务字段名 → ``(下限, 上限)``）。

    Returns:
        :class:`ParamCheckReport` —— 三类越界事实（空 = 合理）。
    """
    return ParamCheckReport(
        range_violations=tuple(
            detect_range_violations(params, limits or {})
        ),
        window_violations=tuple(
            detect_window_violations(params, windows or {})
        ),
        anchor_violations=tuple(detect_anchor_violations(params)),
    )


__all__ = [
    'RANGE_CHECKS',
    'WINDOW_CONSTRAINED_FIELDS',
    'AnchorViolation',
    'RangeViolation',
    'WindowViolation',
    'ParamCheckReport',
    'detect_range_violations',
    'detect_window_violations',
    'detect_anchor_violations',
    'validate',
]
