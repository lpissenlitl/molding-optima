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
