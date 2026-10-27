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
- **扩展节奏不同**：本模块是"去模糊化**方法**"族 —— `macros.DEFUZZ_METHODS`
  已列出 `centroid / bisector / mom / som / lom` 5 种，当前只实现 `centroid`。
"""

import numpy as np


__all__ = ['centroid', 'defuzz']


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
# 模块级健全性自检（仅在 `python -m defuzz` 时执行）
# ============================================================================

if __name__ == '__main__':
    # 反模糊化
    x = np.linspace(0, 10, 201)
    mfx = np.exp(-((x - 5) ** 2.0) / (2 * 2 ** 2.0))
    print('defuzz(x, gauss_mf) =', defuzz(x, mfx))
