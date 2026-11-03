"""fuzzy 诊断出口 —— **每请求一个**的诊断容器 + 结构化日志统一出口。

为什么单独一个模块：
  `FuzzyEngine` 是**模块级单例**（见 `engine.py` 末尾的
  `AlgorithmRegistry.register('fuzzy', FuzzyEngine())`），全进程一个实例。
  诊断数据原先放在**实例属性** `_field_reports` / `_diagnostics` 上：
  `recommend()` 开头无条件重置、推理过程中再追加 ⇒ 两个并发请求共用一个实例时，
  **B 请求开头会把 A 请求正在写的清单清掉**，A 醒来后读到的是 B 的内容。

  已实测复现：A 请求的条目（`PP0 → guessed`）消失，A 读到的是 B 的（`PP0 → unknown`）。

  之所以至今没炸成生产事故：这两个列表**只写不读**（没有任何 getter）。
  但本模块的目的正是让诊断**可见** ⇒ 继续留在实例属性上就是**跨请求串数据**。

  ⇒ 这里用 `contextvars.ContextVar` 承载容器：
  - 同步部署（WSGI/uWSGI 多线程）与异步部署（ASGI）都按「执行上下文」隔离
  - **不改任何现有方法签名**（容器靠上下文取，不靠参数一层层往下传）

对外契约不变：诊断只进**日志**，不进 HTTP 响应、不进推荐结果。
"""

import json
import logging
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Diagnostic:
    """单次 `recommend()` 请求的诊断容器。

    字段名与引擎原先的实例属性同名（`field_reports` / `diagnostics`），
    内容结构也**保持原样** —— 黄金快照 `_golden_ABC.json` 会记录
    `_diagnostics` 的 repr，结构一变快照就 diff。

    ⚠️ `selections` 是**后加的第三个容器**（决策级留痕，来源见
    `process/algorithms/defect_selection.py`）：刻意**独立**于上面两个清单 ——
    它们是「规则级诊断」，它是「决策级留痕」，性质不同；
    且**不动**那两个 ⇒ 黄金快照仍然零差异。

    ⚠️ `over_limits` 是**后加的第四个容器**（**输入体检级**留痕，来源见
    `process/algorithms/fuzzy/over_limit.py`）：性质与上面三个都不同 ——
    上面三个是「本次推荐**怎么算出来**的」，它是「**进来的参数本身**合不合规」；
    同样刻意独立、且**不动**前面三个 ⇒ 黄金快照仍然零差异。
    """

    # 字段定性降级清单（每层一条）+ 机台物理上限裁剪记录
    field_reports: List[Dict[str, Any]] = field(default_factory=list)
    # 规则级诊断清单（条目级跳过时记录）
    diagnostics: List[Dict[str, Any]] = field(default_factory=list)
    # 决策级留痕清单（本轮选了哪个缺陷 / 依据是什么）
    selections: List[Dict[str, Any]] = field(default_factory=list)
    # 输入体检清单（当前值超设备上限的记录）—— **只识别，不处理**
    over_limits: List[Dict[str, Any]] = field(default_factory=list)

    def is_empty(self) -> bool:
        return (not self.field_reports and not self.diagnostics
                and not self.selections and not self.over_limits)

    def to_payload(self) -> Dict[str, Any]:
        """→ 结构化日志的载荷（纯 dict，可 JSON 序列化）。"""
        return {
            'event': 'fuzzy.diagnostics',
            'field_reports': list(self.field_reports),
            'diagnostics': list(self.diagnostics),
            'selections': list(self.selections),
            'over_limits': list(self.over_limits),
        }

    def emit(self) -> None:
        """把本请求的诊断快照打成**一条**结构化日志。

        与散落在各处的 `logger.warning(...)` 是**两种粒度**：
        散点日志是「人读的即时告警」，这里是「机器读的请求级快照」。
        空容器不打（避免无诊断的请求刷屏）。
        """
        if self.is_empty():
            return
        logger.info('[fuzzy.diagnostics] %s',
                    json.dumps(self.to_payload(), ensure_ascii=False, default=str))


# 当前执行上下文的诊断容器（None = 本上下文还没建过）
_current = ContextVar('fuzzy_diagnostic', default=None)


@contextmanager
def request_diagnostics() -> Iterator[Diagnostic]:
    """一次请求的诊断作用域：进入时新建容器，退出时摘掉并打成结构化日志。

    - **进入**：在当前执行上下文挂一个**新容器** ⇒ 本次请求的诊断与其它请求
      完全隔离（同步多线程 / 异步多 task 都隔离）。
    - **退出**：`reset(token)` 把容器从上下文摘掉 —— 容器内容仍在返回的
      ``Diagnostic`` 对象里（调用方可以自行留存），但**不会**残留在上下文里
      影响后续调用。
    - **退出**：同时 `emit()` 一条结构化日志（放 finally ⇒ 推理失败时
      也能留下「失败前到底发生了什么」）。

    ⚠️ 「请求结束后仍能读到本次诊断」这个既有约定由调用方承担：
    `engine.py` 把容器移交给实例槽位 `_last_diag`，诊断脚本与快照脚本读它。
    """
    diag = Diagnostic()
    token = _current.set(diag)
    try:
        yield diag
    finally:
        _current.reset(token)
        diag.emit()


def current_diagnostic() -> Optional[Diagnostic]:
    """取当前执行上下文的诊断容器。

    正常路径（`recommend()` 内）已由 `begin_diagnostics()` 挂好 ⇒ 直接返回。
    没有活动容器时返回 **None** —— 由调用方决定兜底策略
    （引擎用「实例级游离容器」，见 `engine.py::_diag`）。
    """
    return _current.get()


__all__ = [
    'Diagnostic',
    'current_diagnostic',
    'request_diagnostics',
]
