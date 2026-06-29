"""
Filename:membership.py
Function: 隶属度函数实现
Author:Guo Fei
"""
import numpy as np
import logging

def gauss_mf(x, mean, sigma):
    """
    Gaussian fuzzy membership function.

    Parameters
    ----------
    x : array_like
        Independent variable.
    mean : float
        Gaussian parameter for center (mean) value.
    sigma : float
        Gaussian parameter for standard deviation.

    Returns
    -------
    y : array_like
        Gaussian membership function for x.
    """
    if isinstance(x, np.ndarray):
        x = x.astype(np.float)

    if isinstance(x, int):
        x = float(x)

    return np.exp(-((x - mean) ** 2.) / (2 * sigma ** 2.))


def tri_mf(x, a, b, c):
    """
    三角形隶属度函数

    Parameters
    ----------
    x: int or float or ndarray, 输入精确值
    a: int or float, 三角形左端点
    b: int or float, 三角形上顶点
    c: int or float, 三角形右端点

    Returns
    -------
    y: int or float or ndarray, 输入对应的模糊隶属度
    """
    assert a <= b <= c, 'abc requires the three elements a <= b <= c.'
    if isinstance(x, np.ndarray):
        x = x.astype(np.float)

    if isinstance(x, int):
        x = float(x)

    cond_list = [x < a, np.logical_and(x > a, x < b), x == b, np.logical_and(x > b, x <= c), x > c]
    func_list = [0, lambda x: (x - a) / (b - a), 1, lambda x: (c - x) / (c - b), 0]
    return np.piecewise(x, cond_list, func_list)


def trap_mf(x, a, b, c, d):
    """
    梯形隶属度函数

    Parameters
    ----------
    x: int or float or ndarray, 输入精确值
    a: int or float, 梯形左下端点
    b: int or float, 梯形左上端点
    c: int or float, 梯形右上端点
    d: int or float, 梯形右下端点

    Returns
    -------
    y : int or float or ndarray, 输入对应的模糊隶属度
    """
    assert a <= b and b <= c and c <= d, ' requires the four elements  a <= b <= c <= d.'
    if isinstance(x, np.ndarray):
        x = x.astype(np.float)

    if isinstance(x, int):
        x = float(x)

    cond_list = [x < a, np.logical_and(x >= a, x < b), np.logical_and(x >= b, x < c), np.logical_and(x >= c, x < d),
                 x >= d]
    func_list = [0., lambda x: tri_mf(x, a, b, b), 1., lambda x: tri_mf(x, c, c, d), 0.]

    return np.piecewise(x, cond_list, func_list)


if __name__ == '__main__':
    x = np.arange(0, 11, 1)
