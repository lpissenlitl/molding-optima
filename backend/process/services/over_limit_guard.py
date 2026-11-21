"""越限守卫专区 —— 把「参数值超出机台能力」挡在流程之外。

**判据**（哪些值越了、越了哪一层）统一在算法契约层
``process.algorithms.fuzzy.over_limit``；本模块只做 **service 层拦截**：
判据命中 ⇒ 抛 ``BizException``（400）+ 面向用户的文案。

两条链路（初始化 / 优化）**判据同源、文案一致** ⇒ 单一实现，调用方按需自取：

- **位置类超行程**（:func:`guard_position_over_stroke`）：初始化判「算出来的初值」，
  优化判「第3层整合后的落地值」—— 传入的参数集不同，判据与文案完全相同 ⇒
  同一台机、同一产品，初始化报错说什么、优化报错也说什么。
- **设定值类越限**（:func:`guard_over_limit_settings`）：当前设定值 vs 机台可设定
  上限 ⇒ 命中**设备安全红线**即拒绝。

【注意】**两个守卫的入参命名空间不同**（易错，务必看清）：

- ``guard_over_limit_settings`` 收**算法命名**的参数字典（``{'IP0': 200.0}``）；
- ``guard_position_over_stroke`` 收**业务命名**的参数字典（``{'inj_pres_1': 200.0}``），
  内部自己转算法命名。

【注意】缺上限（机台没录行程 / 没录可设定上限）⇒ **不判**：缺数据不等于
参数不合理（沿用各判据源的既定口径）。
"""
import logging
from collections.abc import Mapping
from typing import Any, Dict, List

from extensions.exceptions import BizException, ERROR_DATA_INVALID
from process.algorithms.fuzzy import field_names  # 命名契约：业务字段名 ↔ 算法字段名
from process.algorithms.fuzzy.over_limit import (
    detect_blocking_over_limits,  # 越限分层口径（device = 设备安全红线 ⇒ 阻断）
    detect_over_stroke_limits,  # 位置类超行程识别（stroke = 机台能力不足 ⇒ 阻断）
)
from process.algorithms.fuzzy.specs import (
    resolve_param_limits,  # 机台物理上限 → {参数族: 上限}
    resolve_position_limits,  # 设备实测注射行程 → {位置类参数名/族: 上限}
)
from process.exceptions import ERROR_PROCESS_OVER_STROKE  # 位置类超行程（机台能力不足）
from .optimize_common import param_label  # 业务字段名 → 中文标签

_logger = logging.getLogger(__name__)

__all__ = [
    'format_limit_number',
    'guard_over_limit_settings',
    'guard_position_over_stroke',
]


# --- 展示工具 ---

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


def _format_over_limit_message(items: List[Any]) -> str:
    """越限拒绝文案 —— 说清「哪个参数 / 当前值 / 上限」。

    否则用户只看到一个「数据无效」，无从下手改。
    """
    details = []
    for item in items[:3]:
        details.append('%s 当前 %s 超出机台上限 %s'
                       % (item.business_name or item.param_name,
                          format_limit_number(item.current_value),
                          format_limit_number(item.limit)))
    if len(items) > 3:
        details.append('等 %d 项' % len(items))
    return '；'.join(details) + '，该设定超出设备可设定范围，请修正后再试'


# --- 守卫 ---

def guard_over_limit_settings(
    *,
    process_parameter: Dict[str, Any],
    machine_info: Dict[str, Any],
    scope: str,
    interface_tag: str,
) -> None:
    """设定值类越限守卫 —— **设备安全红线**命中即拒绝（400）。

    判定时机：**调用算法之前**（service 预处理层）。
    判据是**纯事实**（当前设定值 vs 机台物理上限）⇒ 不需要结论做参照。

    判据：当前设定值 > 机台物理上限（``specs.resolve_param_limits``）。

    分层（安全分层口径，固化在算法契约层 ``over_limit.BLOCKING_LIMIT_SOURCES``）：
      - ``device``（设定值类）—— **操作设备涉及安全** ⇒ 阻断；
      - ``material``（温度类）—— 降解/变色，不涉及设备安全 ⇒ 不阻断（只告警）。

    【注意】缺上限（机台没填）⇒ **不阻断**：缺数据不等于参数不合理。

    Args:
        process_parameter: **算法命名**的工艺参数当前值（``{'IP0': 200.0}``）。
        machine_info: 算法入参 machine_info（含机台可设定上限字段）。
        scope: 日志前缀用的链路标识（``'optimize'`` / ``'initialize'``）。
        interface_tag: 本次调用标识（进日志，便于定位是哪一次调用）。

    Raises:
        BizException(ERROR_DATA_INVALID): 命中设备安全红线
    """
    blocking = detect_blocking_over_limits(
        process_parameter, resolve_param_limits(machine_info))
    if not blocking:
        return
    _logger.warning(
        "[%s] %s 越限拒绝（设备安全红线）: %s",
        scope, interface_tag, [item.to_trace() for item in blocking])
    raise BizException(ERROR_DATA_INVALID, _format_over_limit_message(blocking))


def guard_position_over_stroke(
    *,
    values: Mapping[str, Any],
    machine_info: Dict[str, Any],
    scope: str,
    interface_tag: str,
) -> None:
    """位置类超行程守卫 —— **机台能力校验**（超了直接拒绝，不产出错参数）。

    与 :func:`guard_over_limit_settings` 同属「越限处理」，但**判据不同**：

    - 那边 = **设定值类**超机台可设定上限（``limit_source='device'``）
      ⇒ 操作设备涉及安全 ⇒ 400 拒绝；
    - 这边 = **位置类**超设备实测注射行程（``limit_source='stroke'``）
      ⇒ 这个产品在这台机上做不出来 ⇒ **同样拒绝**（用户口径：
      「超限先报错」）。

    【注意】**拒绝而不是回退**：事后把值改回旧值会让「这一轮改了什么」不可追；
    而「剔建议、值照写」是更糟的**半处理**（用户被告知做不出来，系统却把
    更超行程的值落库）⇒ 检出即失败。

    【注意】判据取**调用方传入的参数集**：初始化传「算出来的初值」（初值本身就
    超行程 ⇒ 落到参数表里就是让操作工去设一个机台根本设不进去的值）；优化传
    「第3层整合后的落地值」（既覆盖「当前值本来就超」，也覆盖「本轮把它推超了」
    —— 整合值 ⊇ 基线值 ⇒ 一道覆盖两种）。

    【注意】**口径与初始化链路一致**（同一函数）⇒ 同一台机、同一产品，
    初始化报错说什么、优化报错也说什么。

    【注意】缺机台行程（``max_injection_stroke`` 没录）⇒ **不判**：缺数据不等于
    参数不合理（同 :func:`resolve_position_limits` 的既定口径）。

    Args:
        values: **业务命名**的工艺参数字典（``{'inj_pres_1': 200.0}``）。
        machine_info: 算法入参 machine_info（含 ``max_injection_stroke``）。
        scope: 日志前缀用的链路标识（``'optimize'`` / ``'initialize'``）。
        interface_tag: 本次调用标识（进日志，便于定位是哪一次调用）。

    Raises:
        BizException(ERROR_PROCESS_OVER_STROKE): 位置类参数超出机台注射行程
    """
    limits = resolve_position_limits(machine_info)
    if not limits:
        return
    items = detect_over_stroke_limits(field_names.to_algo_params(values), limits)
    if not items:
        return

    # 多个位置参数同时超出行程（IL0 / ML0 / MEL 一起超）⇒ 合并成一条：
    # 它们说的是同一件事（这个产品在本机做不出来），逐条提示只会刷屏。
    # 取**超出量最大**的那项作代表。
    # 【注意】文案三段式：**事实**（哪个参数、超多少）→ **出路**（换更大的机）；
    # 「本机做不出来」的结论由错误码标题承担（当前设备无法生产该制品），正文不重复。
    # 出路只给「换机」—— **以产品为目标**（产品形态已定），不给
    # 「减轻制品重量 / 减少型腔数」这类迁就设备的建议。
    top = max(items, key=lambda item: item.exceeded_by)
    others = len(items) - 1
    label = param_label(top.business_name or top.param_name)
    message = (
        '%s需 %smm，超出本机注射行程 %smm%s，请更换行程更大的设备'
        % (label,
           format_limit_number(top.current_value),
           format_limit_number(top.limit),
           ('（另有 %d 项超出行程）' % others) if others else '')
    )
    _logger.warning(
        "[%s] %s 位置类超行程，拒绝处理: %s ｜ %s",
        scope, interface_tag, [item.to_trace() for item in items], message)
    raise BizException(ERROR_PROCESS_OVER_STROKE, message)
