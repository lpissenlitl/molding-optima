"""
隶属度函数与反模糊化

从 `old/mdprocess/utils/fuzzykit/fuzzy_core/functional/membership.py` 与
`old/mdprocess/utils/fuzzykit/fuzzy_core/functional/defuzzy.py` 迁入。

对外暴露老 fuzzykit 的函数名（gauss_mf / tri_mf / trap_mf / defuzz），
以保持与 nets.py 的接口一致；同时提供 triangular_mf / trapezoidal_mf / gaussian_mf
等别名供上层调用。
"""

import numpy as np
from typing import Union


ArrayLike = Union[float, int, np.ndarray, list]


# ============================================================================
# 高斯隶属度函数
# ============================================================================

def gauss_mf(x: ArrayLike, mean: float, sigma: float) -> ArrayLike:
    """高斯隶属度函数（老 fuzzykit 命名，与 nets.py FuzzyFeature 配套使用）

    对 scalar 和 ndarray 都生效；老 fuzzykit 是 scalar 为 float64 单值。

    Parameters
    ----------
    x : float or ndarray
    mean : float
    sigma : float

    Returns
    -------
    y : float or ndarray
    """
    if isinstance(x, np.ndarray):
        x = x.astype(float)
    elif isinstance(x, (int, float)):
        x = float(x)
    elif isinstance(x, list):
        x = np.array(x, dtype=float)
    return np.exp(-((x - mean) ** 2.0) / (2 * sigma ** 2.0))


# 别名（与原 functional.py 保持兼容）
def gaussian_mf(x: np.ndarray, mean: float, sigma: float) -> np.ndarray:
    """gauss_mf 的别名"""
    return gauss_mf(x, mean, sigma)


# ============================================================================
# 三角形隶属度函数
# ============================================================================

def tri_mf(x: ArrayLike, a: float, b: float, c: float) -> ArrayLike:
    """三角形隶属度函数（老 fuzzykit 命名）

    要求 a <= b <= c。

    Parameters
    ----------
    x : scalar or ndarray
    a : 三角形左端点
    b : 三角形上顶点
    c : 三角形右端点

    Returns
    -------
    y : scalar or ndarray
    """
    assert a <= b <= c, 'abc requires the three elements a <= b <= c.'
    if isinstance(x, np.ndarray):
        x = x.astype(float)
    elif isinstance(x, (int, float)):
        x = float(x)
    elif isinstance(x, list):
        x = np.array(x, dtype=float)

    cond_list = [
        x < a,
        np.logical_and(x > a, x < b),
        x == b,
        np.logical_and(x > b, x <= c),
        x > c,
    ]
    func_list = [
        0,
        lambda x: (x - a) / (b - a),
        1,
        lambda x: (c - x) / (c - b),
        0,
    ]
    return np.piecewise(x, cond_list, func_list)


# 别名
def triangular_mf(x: np.ndarray, a: float, b: float, c: float) -> np.ndarray:
    """tri_mf 的别名"""
    return tri_mf(x, a, b, c)


# ============================================================================
# 梯形隶属度函数（老 fuzzykit 命名）
# ============================================================================

def trap_mf(x: ArrayLike, a: float, b: float, c: float, d: float) -> ArrayLike:
    """梯形隶属度函数（老 fuzzykit 命名）

    要求 a <= b <= c <= d。
    """
    assert a <= b and b <= c and c <= d, ' requires the four elements  a <= b <= c <= d.'
    if isinstance(x, np.ndarray):
        x = x.astype(float)
    elif isinstance(x, (int, float)):
        x = float(x)
    elif isinstance(x, list):
        x = np.array(x, dtype=float)

    cond_list = [
        x < a,
        np.logical_and(x >= a, x < b),
        np.logical_and(x >= b, x < c),
        np.logical_and(x >= c, x < d),
        x >= d,
    ]
    func_list = [
        0.0,
        lambda x: tri_mf(x, a, b, b),
        1.0,
        lambda x: tri_mf(x, c, c, d),
        0.0,
    ]
    return np.piecewise(x, cond_list, func_list)


# 别名
def trapezoidal_mf(x: np.ndarray, a: float, b: float, c: float, d: float) -> np.ndarray:
    """trap_mf 的别名"""
    return trap_mf(x, a, b, c, d)


# ============================================================================
# 钟形与单点（小众需求，保留原实现）
# ============================================================================

def bell_mf(x: np.ndarray, a: float, b: float, c: float) -> np.ndarray:
    """钟形隶属度函数"""
    return 1 / (1 + ((x - c) / a) ** (2 * b))


def singleton_mf(x: np.ndarray, center: float) -> np.ndarray:
    """单点隶属度函数"""
    y = np.zeros_like(x, dtype=float)
    y[x == center] = 1.0
    return y


# ============================================================================
# 反模糊化（迁自 defuzzy.py）
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
        反模糊化方法，目前仅支持 'centroid'（其它方法暂未实现）

    Returns
    -------
    u : float
    """
    x = np.asarray(x).ravel()
    mfx = np.asarray(mfx).ravel()
    n = len(x)
    if n != len(mfx):
        raise ValueError('x 与 mfx 长度不一致')

    if mode == 'centroid':
        if mfx.sum() == 0:
            raise ValueError('Empty membership function')
        return centroid(x, mfx)
    else:
        # 预留扩展：bisector / mom / som / lom
        raise NotImplementedError(f'暂不支持 defuzz mode = {mode}')


# ============================================================================
# 模块级健全性自检（仅在 `python -m functional` 时执行）
# ============================================================================

if __name__ == '__main__':
    # scalar 模糊化测试
    print('gauss_mf(0, 0, 1) =', gauss_mf(0, 0, 1))
    print('gauss_mf(np.array([0, 1, 2]), 0, 1) =', gauss_mf(np.array([0.0, 1.0, 2.0]), 0, 1))

    # tri 隶属度
    print('tri_mf(5, 0, 5, 10) =', tri_mf(5, 0, 5, 10))
    print('tri_mf(2, 0, 5, 10) =', tri_mf(2, 0, 5, 10))

    # 反模糊化
    x = np.linspace(0, 10, 201)
    mfx = gauss_mf(x, 5, 2)
    print('defuzz(x, gauss_mf) =', defuzz(x, mfx))
"""
隶属度函数

定义常用的隶属度函数
"""

import numpy as np
from typing import Tuple


def triangular_mf(x: np.ndarray, a: float, b: float, c: float) -> np.ndarray:
    """
    三角形隶属度函数

    Args:
        x: 输入值
        a: 左边界
        b: 峰值
        c: 右边界

    Returns:
        隶属度数组
    """
    y = np.zeros_like(x, dtype=float)
    y[x == b] = 1.0

    left_mask = (x > a) & (x < b)
    right_mask = (x > b) & (x < c)

    y[left_mask] = (x[left_mask] - a) / (b - a)
    y[right_mask] = (c - x[right_mask]) / (c - b)

    return y


def trapezoidal_mf(x: np.ndarray, a: float, b: float, c: float, d: float) -> np.ndarray:
    """
    梯形隶属度函数

    Args:
        x: 输入值
        a: 左下界
        b: 左上界
        c: 右上界
        d: 右下界

    Returns:
        隶属度数组
    """
    y = np.zeros_like(x, dtype=float)

    # 左上升段
    left_mask = (x >= a) & (x <= b)
    y[left_mask] = (x[left_mask] - a) / (b - a)

    # 平台段
    plateau_mask = (x > b) & (x < c)
    y[plateau_mask] = 1.0

    # 右下降段
    right_mask = (x >= c) & (x <= d)
    y[right_mask] = (d - x[right_mask]) / (d - c)

    return y


def gaussian_mf(x: np.ndarray, mean: float, sigma: float) -> np.ndarray:
    """
    高斯隶属度函数

    Args:
        x: 输入值
        mean: 中心
        sigma: 标准差

    Returns:
        隶属度数组
    """
    return np.exp(-((x - mean) ** 2) / (2 * sigma ** 2))


def bell_mf(x: np.ndarray, a: float, b: float, c: float) -> np.ndarray:
    """
    钟形隶属度函数

    Args:
        x: 输入值
        a: 宽度
        b: 斜度
        c: 中心

    Returns:
        隶属度数组
    """
    return 1 / (1 + ((x - c) / a) ** (2 * b))


def singleton_mf(x: np.ndarray, center: float) -> np.ndarray:
    """
    单点隶属度函数（清晰化用）

    Args:
        x: 输入值
        center: 中心点

    Returns:
        隶属度数组
    """
    y = np.zeros_like(x, dtype=float)
    y[x == center] = 1.0
    return y
