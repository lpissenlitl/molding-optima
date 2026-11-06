"""反模糊化（结论阶段）

模糊推理推理链的**最后一段**：把模糊结论（采样点上的隶属度序列）
反模糊化成精确值。

**层定位**：模糊推理内核的**数学原语层**，只服务 **Mamdani 推理** ——
Mamdani 的结论本身是模糊集，必须反模糊化才能拿到可执行的数值。
零阶 T-S 的结论直接是数值（归一化加权平均），**不需要**本模块。

**为什么单独成文件**（与隶属度函数分家）：
- **推理阶段不同**：隶属度函数 = 模糊化（第 1 步），反模糊化 = 结论（最后 1 步），
  两者之间还隔着蕴含与聚合两步（在 `models/nets.py` 内联实现）。
- **输入范式不同**：隶属度函数是 `(标量/数组, 中心, 宽…)` → 隶属度 ∈ [0,1]；
  反模糊化是 `(采样点序列, 隶属度序列)` → 实数。
- **扩展节奏不同**：本模块是"去模糊化**方法**"族 —— `centroid` / `bisector` /
  `mom` / `som` / `lom` **均已实现**，用哪个由工艺定；
  ⚠️ **默认仍是 `centroid`**（`nets.py` 也显式传 `'centroid'`）⇒ 默认路径不改变任何现有输出。
"""

import numpy as np


__all__ = ['centroid', 'bisector', 'mom', 'som', 'lom', 'defuzz',
           'DEFUZZ_METHODS', 'UnsupportedDefuzzMode']


class UnsupportedDefuzzMode(NotImplementedError, ValueError):
    """不支持的反模糊化模式。

    ⚠️ 同时继承 `NotImplementedError`（历史抛出类型，保持向后兼容）
    与 `ValueError`（模式名非法本质是取值错误）⇒ 两种 ``except`` 都能兜住。
    """


# ============================================================================
# 反模糊化
# ============================================================================

def centroid(x: np.ndarray, mfx: np.ndarray) -> float:
    """重心法（centroid）反模糊化（Mamdani 用）"""
    sum_moment_area = 0.0
    sum_area = 0.0

    if len(x) == 1:
        denom = max(float(mfx[0]), np.finfo(float).eps)
        return float(x[0]) * float(mfx[0]) / denom

    for i in range(1, len(x)):
        x1, x2 = float(x[i - 1]), float(x[i])
        y1, y2 = float(mfx[i - 1]), float(mfx[i])

        if not (y1 == y2 == 0.0 or x1 == x2):
            if y1 == y2:
                moment = 0.5 * (x1 + x2)
                area = (x2 - x1) * y1
            elif y1 == 0.0 and y2 != 0.0:
                moment = 2.0 / 3.0 * (x2 - x1) + x1
                area = 0.5 * (x2 - x1) * y2
            elif y2 == 0.0 and y1 != 0.0:
                moment = 1.0 / 3.0 * (x2 - x1) + x1
                area = 0.5 * (x2 - x1) * y1
            else:
                moment = (2.0 / 3.0 * (x2 - x1) * (y2 + 0.5 * y1)) / (y1 + y2) + x1
                area = 0.5 * (x2 - x1) * (y1 + y2)

            sum_moment_area += moment * area
            sum_area += area

    denom = max(sum_area, np.finfo(float).eps)
    return sum_moment_area / denom


def defuzz(x: np.ndarray, mfx: np.ndarray, mode: str = 'centroid') -> float:
    """反模糊化统一入口

    Parameters
    ----------
    x : ndarray
        自变量序列（采样点）
    mfx : ndarray
        隶属度序列
    mode : str
        反模糊化方法，可选：
        - ``centroid`` 重心法（**默认**）
        - ``bisector`` 二分中位（面积平分点）
        - ``mom``     最大隶属度均值（mean of maxima）
        - ``som``     最小最大元（smallest of maxima）
        - ``lom``     最大最大元（largest of maxima）

    Returns
    -------
    u : float
    """
    x = np.asarray(x).ravel()
    mfx = np.asarray(mfx).ravel()
    n = len(x)
    if n != len(mfx):
        raise ValueError('x 与 mfx 长度不一致')

    method = DEFUZZ_METHODS.get(mode)
    if method is None:
        raise UnsupportedDefuzzMode(
            '不支持的 defuzz mode = %r（可用：%s）'
            % (mode, ' / '.join(sorted(DEFUZZ_METHODS))))
    if mfx.sum() == 0:
        raise ValueError('Empty membership function')
    return method(x, mfx)


# ============================================================================
# 其它反模糊化方法（默认仍走 centroid）
# ============================================================================

def _as_1d(x, mfx):
    """输入规整为一维 float 数组（各方法统一入口）。"""
    return np.asarray(x, dtype=float).ravel(), np.asarray(mfx, dtype=float).ravel()


def _trapezoid_area(x: np.ndarray, mfx: np.ndarray) -> float:
    """梯形积分 ∫μ(x)dx（逐段 0.5·(y1+y2)·Δx）。"""
    total = 0.0
    for i in range(1, len(x)):
        total += (0.5 * (float(mfx[i - 1]) + float(mfx[i]))
                  * (float(x[i]) - float(x[i - 1])))
    return total


def bisector(x: np.ndarray, mfx: np.ndarray) -> float:
    """二分中位（bisector）反模糊化。

    面积平分点：隶属度曲线下面积从左往右累加，到**一半**时对应的 x。
    """
    x, mfx = _as_1d(x, mfx)
    total = _trapezoid_area(x, mfx)
    if total <= 0:
        raise ValueError('Empty membership function')
    half = total / 2.0
    acc = 0.0
    for i in range(1, len(x)):
        seg = (0.5 * (float(mfx[i - 1]) + float(mfx[i]))
               * (float(x[i]) - float(x[i - 1])))
        if acc + seg >= half:
            frac = (half - acc) / seg if seg > 0 else 0.0
            return float(x[i - 1]) + frac * (float(x[i]) - float(x[i - 1]))
        acc += seg
    return float(x[-1])


def _maxima_indices(x: np.ndarray, mfx: np.ndarray):
    """达到**最大**隶属度的采样点下标（并列时全取）。"""
    mfx_max = float(np.max(mfx))
    idx = np.flatnonzero(mfx == mfx_max)
    if len(idx) == 0:  # 理论上不会发生（NaN 情况），兜底取 argmax
        idx = np.array([int(np.nanargmax(mfx))])
    return idx, mfx_max


def mom(x: np.ndarray, mfx: np.ndarray) -> float:
    """最大隶属度均值（mean of maxima）反模糊化。"""
    x, mfx = _as_1d(x, mfx)
    idx, _ = _maxima_indices(x, mfx)
    return float(np.mean(x[idx]))


def som(x: np.ndarray, mfx: np.ndarray) -> float:
    """最小最大元（smallest of maxima）反模糊化。"""
    x, mfx = _as_1d(x, mfx)
    idx, _ = _maxima_indices(x, mfx)
    return float(x[idx][0])


def lom(x: np.ndarray, mfx: np.ndarray) -> float:
    """最大最大元（largest of maxima）反模糊化。"""
    x, mfx = _as_1d(x, mfx)
    idx, _ = _maxima_indices(x, mfx)
    return float(x[idx][-1])


#: 可用反模糊化方法（`mode` 名 → 实现）
DEFUZZ_METHODS = {
    'centroid': centroid,
    'bisector': bisector,
    'mom': mom,
    'som': som,
    'lom': lom,
}


# ============================================================================
# 模块级健全性自检（仅在 `python -m defuzz` 时执行）
# ============================================================================

if __name__ == '__main__':
    # 反模糊化
    x = np.linspace(0, 10, 201)
    mfx = np.exp(-((x - 5) ** 2.0) / (2 * 2 ** 2.0))
    print('defuzz(x, gauss_mf) =', defuzz(x, mfx))
