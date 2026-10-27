"""隶属度函数族（模糊化阶段）

模糊推理推理链的**第一段**：把精确值 x 映射为隶属度 μ(x) ∈ [0,1]。

**层定位**：模糊推理内核的**数学原语层**。本模块只做"模糊化"，
不含推理编排、不含反模糊化（反模糊化在 `fuzzy_core.defuzz`）。

---

## 统一签名契约

所有隶属度函数一律::

    mf(x, center, width, shape=None) -> ArrayLike

| 参数 | 语义 |
|---|---|
| `x` | 标量或数组（`float` / `int` / `list` / `ndarray`） |
| `center` | 隶属度峰中心（该桶在论域上的位置） |
| `width` | 该形状在论域上的**总跨度**（高斯 = 2σ；三角形 = c-a；梯形 = d-a） |
| `shape` | 形状参数；`None` = 该族默认；语义因族而异（见下） |

`shape` 各族语义：

| 函数 | `shape` 语义 | 默认 |
|---|---|---|
| `gaussian_mf` | `p` 形状指数 | `2` |
| `two_piece_gaussian_mf` | `(p_left, p_right)` 左右独立指数 | `(2, 2)` |
| `triangular_mf` | `(L, R)` 左/右肩占总跨度比例（L+R=1） | `(0.5, 0.5)` |
| `trapezoidal_mf` | `(L, R)` 平顶两侧肩宽占比（L+R<1，余下为平顶） | `(0.25, 0.25)` |
| `bell_mf` | `m` 陡峭度 | `1` |
| `algebraic_bell_mf` | `b` 陡峭度 | `1` |
| `sigmoid_mf` / `z_sigmoid_mf` / `singleton_mf` | 无 | — |

**为什么统一签名**：调用方（`models/features.py`）只需"中心 + 跨度"就能生成
任意形状的隶属度函数 ⇒ 新增形状 = 加一个函数 + 加一行分派，调用方零改动。

---

## 高斯的口径锚点（勿改）

本模块的高斯口径是 `exp(-(x-μ)² / (2σ²))`（σ = 标准差），
而教材标准的广义高斯是 `exp(-|((x-μ)/σ)|^p)` —— **两者差一个 2 的因子**
（`μ(c±σ)` 分别为 `0.6065` 与 `0.3679`）。

实现以 **p=2 对齐本口径**为锚点：`μ = exp(-0.5 * |((x-μ)/σ)|^p)`，
`p=2` 时与原式**逐位相等**；`p≠2` 走通用式。

---

## 本文件不装什么

- 反模糊化（`centroid` / `defuzz`）⇒ `fuzzy_core/defuzz.py`
- 档位词表 / 桶映射 ⇒ `fuzzy_core/macros.py`
- 推理网络 ⇒ `fuzzy_core/models/nets.py`
"""

from dataclasses import dataclass
from typing import Any, Callable, Union

import numpy as np


ArrayLike = Union[float, int, np.ndarray, list]

__all__ = [
    'ArrayLike',
    'MembershipSpec',
    'MEMBERSHIP_SPECS',
    'gaussian_mf',
    'two_piece_gaussian_mf',
    'triangular_mf',
    'trapezoidal_mf',
    'bell_mf',
    'algebraic_bell_mf',
    'sigmoid_mf',
    'z_sigmoid_mf',
    'singleton_mf',
]


# ============================================================================
# 内部工具
# ============================================================================

def _prepare(x: ArrayLike):
    """把输入统一成 float 标量或 float 数组。

    标量输入统一转成 **np.float64**（而不是 Python float）：
    σ=0（退化论域）时除法要按 numpy 语义产出 nan/inf，而不是 Python 的
    ZeroDivisionError —— 桶中心/σ 以 numpy 标量传入时走的正是 numpy 语义；
    改用 Python float 会把"静默 nan"变成"内核崩溃"。

    Returns
    -------
    (value, is_scalar)
        `value` 为 `np.float64`（标量输入）或 `np.ndarray(float)`（数组输入）。
    """
    if isinstance(x, np.ndarray):
        return x.astype(float), False
    if isinstance(x, (bool, int, float, np.integer, np.floating)):
        return np.float64(x), True
    if isinstance(x, (list, tuple)):
        return np.array(x, dtype=float), False
    raise TypeError(
        f'隶属度函数的 x 只接受标量 / list / ndarray，收到 {type(x).__name__}'
    )


def _restore_scalar(out, is_scalar: bool):
    """标量输入 ⇒ 返回 numpy 标量；否则原样返回数组。"""
    if is_scalar:
        return out[()]
    return out


def _shape_pair(shape, default, *, positive=True, sum_exact=None, sum_max=None, label='shape'):
    """把 `shape` 规整成 `(left, right)` 参数对，并按族的约束校验。

    Parameters
    ----------
    shape : tuple or None
        传入的形状参数；`None` 表示使用该族默认值
    default : tuple
        该族的默认 `(left, right)`
    positive : bool
        是否要求两端都 > 0（肩宽退化为 0 会导致除零）
    sum_exact : float, optional
        要求 `left + right` 等于该值（容差 1e-9）—— 三角形用（L+R=1）
    sum_max : float, optional
        要求 `left + right` 不超过该值 —— 梯形用（L+R≤1，余下为平顶）
    label : str
        报错信息里的族名

    Returns
    -------
    (left, right) : tuple[float, float]
    """
    if shape is None:
        left, right = float(default[0]), float(default[1])
    else:
        try:
            left, right = shape
        except (TypeError, ValueError):
            raise ValueError(
                f'{label} 的形状参数必须是 (left, right) 二元组，收到 {shape!r}'
            ) from None
        left, right = float(left), float(right)

    if left < 0 or right < 0:
        raise ValueError(f'{label} 的左右参数不能为负，收到 {shape!r}')
    if positive and (left <= 0 or right <= 0):
        raise ValueError(f'{label} 的左右参数必须 > 0，收到 {shape!r}')

    total = left + right
    if sum_exact is not None and abs(total - sum_exact) > 1e-9:
        raise ValueError(
            f'{label} 的左右参数之和必须等于 {sum_exact}，收到 {total!r}'
        )
    if sum_max is not None and total > sum_max + 1e-9:
        raise ValueError(
            f'{label} 的左右参数之和不得超过 {sum_max}，收到 {total!r}'
        )
    return left, right


def _positive(value: float, label: str) -> float:
    value = float(value)
    if value <= 0:
        raise ValueError(f'{label} 必须 > 0，收到 {value!r}')
    return value


def _non_negative(value: float, label: str) -> float:
    """允许 0 的正数校验。

    `width = 0` = **退化论域**（论域上下界相等 ⇒ 上游元数据缺失或实时值为 0）。
    此时 σ = 0，高斯退化为「除中心点外全 0、中心点为 nan」——
    与 `exp(-(x-μ)² / (2σ²))`（σ=0）**逐位一致**，
    故保留而非收紧为硬错误，避免把上游的静默坏值变成内核崩溃。
    """
    value = float(value)
    if value < 0:
        raise ValueError(f'{label} 不能为负，收到 {value!r}')
    return value


# ============================================================================
# 高斯族
# ============================================================================

def gaussian_mf(x: ArrayLike, center: float, width: float, shape=None):
    """高斯隶属度函数。

    μ(x) = exp(-0.5 * |((x - center) / σ)|^p)，σ = width / 2

    `p = 2`（默认）时与 `exp(-(x-μ)² / (2σ²))` **逐位相等**
    （σ 的口径 = 标准差，`width` = 两个标准差）。

    Parameters
    ----------
    x : float or array_like
        待求隶属度的值
    center : float
        隶属度峰中心
    width : float
        总跨度（= 2σ）
    shape : float, optional
        形状指数 p，默认 2

    Returns
    -------
    y : float or ndarray
        隶属度，取值 [0, 1]
    """
    x, is_scalar = _prepare(x)
    p = 2.0 if shape is None else float(shape)
    _positive(p, '高斯的形状指数 p')
    sigma = _non_negative(float(width), 'width') / 2.0
    center = float(center)
    if p == 2.0:
        # 走原式，保证与 p=2 口径逐位相等（通用式会因运算顺序产生 1 ULP 差异）
        out = np.exp(-((x - center) ** 2.0) / (2 * sigma ** 2.0))
    else:
        out = np.exp(-0.5 * np.abs((x - center) / sigma) ** p)
    return _restore_scalar(out, is_scalar)


def two_piece_gaussian_mf(x: ArrayLike, center: float, width: float, shape=None):
    """双高斯（两段式）隶属度函数。

    中心左侧与右侧各用一套形状指数，用于描述**不对称**的分布
    （如"升温快、降温慢"）。σ 两侧都是 `width / 2`，
    形状指数可独立指定。

    μ(x) = exp(-0.5 * |z|^p_left)  (x < center)
            exp(-0.5 * |z|^p_right) (x ≥ center)
    其中 z = (x - center) / σ

    Parameters
    ----------
    x : float or array_like
    center : float
        隶属度峰中心
    width : float
        总跨度（σ = width / 2）
    shape : tuple, optional
        `(p_left, p_right)`，默认 `(2, 2)`（此时与 `gaussian_mf` 等价）

    Returns
    -------
    y : float or ndarray
    """
    x, is_scalar = _prepare(x)
    p_left, p_right = _shape_pair(shape, (2.0, 2.0), label='双高斯')
    _positive(p_left, '双高斯的左形状指数')
    _positive(p_right, '双高斯的右形状指数')
    sigma = _non_negative(float(width), 'width') / 2.0
    z = (x - float(center)) / sigma
    out = np.where(
        z < 0,
        np.exp(-0.5 * np.abs(z) ** p_left),
        np.exp(-0.5 * np.abs(z) ** p_right),
    )
    return _restore_scalar(out, is_scalar)


# ============================================================================
# 线性族（三角形 / 梯形）
# ============================================================================

def triangular_mf(x: ArrayLike, center: float, width: float, shape=None):
    """三角形隶属度函数。

    顶点固定在 `center`，底边为 `[center - width*L, center + width*R]`。

    Parameters
    ----------
    x : float or array_like
    center : float
        三角形顶点
    width : float
        底边总跨度
    shape : tuple, optional
        `(L, R)` 左/右肩占总跨度的比例（L + R = 1），默认 `(0.5, 0.5)` 对称；
        L/R 必须 > 0，且 L + R 必须等于 1，否则抛 `ValueError`

    Returns
    -------
    y : float or ndarray
    """
    x, is_scalar = _prepare(x)
    left, right = _shape_pair(shape, (0.5, 0.5), sum_exact=1.0, label='三角形')
    span = _non_negative(float(width), 'width')
    a = float(center) - span * left
    b = float(center)
    c = float(center) + span * right
    if not a <= b <= c:
        raise ValueError(f'三角形参数不合法：a={a}, b={b}, c={c}')
    cond_list = [
        x < a,
        np.logical_and(x > a, x < b),
        x == b,
        np.logical_and(x > b, x <= c),
        x > c,
    ]
    func_list = [
        0,
        lambda v: (v - a) / (b - a),
        1,
        lambda v: (c - v) / (c - b),
        0,
    ]
    out = np.piecewise(x, cond_list, func_list)
    return _restore_scalar(out, is_scalar)


def trapezoidal_mf(x: ArrayLike, center: float, width: float, shape=None):
    """梯形隶属度函数。

    底边为 `[center - width/2, center + width/2]`，中间有一段平顶（隶属度恒为 1）。

    Parameters
    ----------
    x : float or array_like
    center : float
        平顶中心
    width : float
        底边总跨度
    shape : tuple, optional
        `(L, R)` 平顶左/右两侧肩宽占总跨度的比例（L + R ≤ 1，余下为平顶），
        默认 `(0.25, 0.25)` ⇒ 平顶占总跨度 50%；
        L/R 必须 > 0，且 L + R 不得超过 1，否则抛 `ValueError`

    Returns
    -------
    y : float or ndarray
    """
    x, is_scalar = _prepare(x)
    left, right = _shape_pair(shape, (0.25, 0.25), sum_max=1.0, label='梯形')
    span = _non_negative(float(width), 'width')
    a = float(center) - span / 2.0
    d = float(center) + span / 2.0
    b = a + span * left
    c = d - span * right
    if not a <= b <= c <= d:
        raise ValueError(f'梯形参数不合法：a={a}, b={b}, c={c}, d={d}')
    cond_list = [
        x < a,
        np.logical_and(x >= a, x < b),
        np.logical_and(x >= b, x < c),
        np.logical_and(x >= c, x < d),
        x >= d,
    ]
    func_list = [
        0.0,
        lambda v: (v - a) / (b - a),
        1.0,
        lambda v: (d - v) / (d - c),
        0.0,
    ]
    out = np.piecewise(x, cond_list, func_list)
    return _restore_scalar(out, is_scalar)


# ============================================================================
# 钟形族
# ============================================================================

def bell_mf(x: ArrayLike, center: float, width: float, shape=None):
    """广义钟形隶属度函数（Mamdani & Zakpur 形式，exp 型）。

    μ(x) = exp(-|((x - center) / σ)|^(2m))，σ = width / 2

    形状比代数型钟形**尾部更厚**，适合需要"明显过渡带"的场合。

    Parameters
    ----------
    x : float or array_like
    center : float
        峰中心
    width : float
        总跨度（σ = width / 2）
    shape : float, optional
        陡峭度 m，默认 1

    Returns
    -------
    y : float or ndarray
    """
    x, is_scalar = _prepare(x)
    m = 1.0 if shape is None else float(shape)
    _positive(m, '钟形的陡峭度 m')
    sigma = _non_negative(float(width), 'width') / 2.0
    out = np.exp(-np.abs((x - float(center)) / sigma) ** (2 * m))
    return _restore_scalar(out, is_scalar)


def algebraic_bell_mf(x: ArrayLike, center: float, width: float, shape=None):
    """代数型钟形隶属度函数（Sugeno 型）。

    μ(x) = 1 / (1 + |((x - center) / σ)|^(2b))，σ = width / 2

    与 `bell_mf` 同为钟形，但**尾部衰减更快**（代数衰减 vs 指数衰减）。

    ⚠️ 绝对值是**必需**的：缺 `|·|` 时 b < 1 会算出 **> 1** 的隶属度。

    Parameters
    ----------
    x : float or array_like
    center : float
        峰中心
    width : float
        总跨度（σ = width / 2）
    shape : float, optional
        陡峭度 b，默认 1

    Returns
    -------
    y : float or ndarray
    """
    x, is_scalar = _prepare(x)
    b = 1.0 if shape is None else float(shape)
    _positive(b, '代数钟形的陡峭度 b')
    sigma = _non_negative(float(width), 'width') / 2.0
    out = 1.0 / (1.0 + np.abs((x - float(center)) / sigma) ** (2 * b))
    return _restore_scalar(out, is_scalar)


# ============================================================================
# 单调族（S 型 / Z 型）
# ============================================================================

def sigmoid_mf(x: ArrayLike, center: float, width: float, shape=None):
    """S 型（sigmoid）隶属度函数 —— **单侧递增**。

    μ(x) = 1 / (1 + exp(-(x - center) / d))，d = width / 4

    过渡带跨度 ≈ 4d ≈ `width`。适合"越大越好"的量（如冷却时间）。

    Parameters
    ----------
    x : float or array_like
    center : float
        拐点中心
    width : float
        过渡带尺度（d = width / 4）
    shape : unused
        为签名对齐而保留，本函数不使用

    Returns
    -------
    y : float or ndarray
    """
    x, is_scalar = _prepare(x)
    d = _non_negative(float(width), 'width') / 4.0
    out = 1.0 / (1.0 + np.exp(-(x - float(center)) / d))
    return _restore_scalar(out, is_scalar)


def z_sigmoid_mf(x: ArrayLike, center: float, width: float, shape=None):
    """Z 型隶属度函数 —— **单侧递减**。

    μ(x) = 1 / (1 + exp((x - center) / d))，d = width / 4

    适合"越小越好"的量。

    Parameters
    ----------
    x : float or array_like
    center : float
        拐点中心
    width : float
        过渡带尺度（d = width / 4）
    shape : unused
        为签名对齐而保留，本函数不使用

    Returns
    -------
    y : float or ndarray
    """
    x, is_scalar = _prepare(x)
    d = _non_negative(float(width), 'width') / 4.0
    out = 1.0 / (1.0 + np.exp((x - float(center)) / d))
    return _restore_scalar(out, is_scalar)


# ============================================================================
# 离散族
# ============================================================================

def singleton_mf(x: ArrayLike, center: float, width=None, shape=None):
    """单点隶属度函数 —— 离散输入用。

    μ(x) = 1 当 x == center，否则 0。

    `width` / `shape` 为统一签名对齐而保留，本函数不使用。

    Parameters
    ----------
    x : float or array_like
    center : float
        单点位置
    width : unused
    shape : unused

    Returns
    -------
    y : float or ndarray
    """
    x, is_scalar = _prepare(x)
    if is_scalar:
        return np.float64(1.0) if float(x) == float(center) else np.float64(0.0)
    arr = np.asarray(x, dtype=float)
    out = np.zeros(arr.shape, dtype=float)
    out[arr == float(center)] = 1.0
    return out


# ============================================================================
# 形状分派表（声明与实现同源）
# ============================================================================

@dataclass(frozen=True)
class MembershipSpec:
    """一种隶属度形状的登记项。

    Attributes
    ----------
    func : Callable
        统一签名的隶属度函数 `(x, center, width, shape=None)`
    default_shape : Any
        该形状的默认 `shape`（`None` 表示用函数自身的默认值）
    desc : str
        一句话说明
    """

    func: Callable
    default_shape: Any
    desc: str


MEMBERSHIP_SPECS = {
    'gauss': MembershipSpec(
        gaussian_mf, None, '高斯（σ = width/2，形状指数 p=2）'),
    'two_piece_gauss': MembershipSpec(
        two_piece_gaussian_mf, (2.0, 2.0), '双高斯（左右独立形状指数，用于不对称分布）'),
    'tri': MembershipSpec(
        triangular_mf, (0.5, 0.5), '三角形（顶点居中，默认对称）'),
    'trap': MembershipSpec(
        trapezoidal_mf, (0.25, 0.25), '梯形（默认平顶占总跨度 50%）'),
    'bell': MembershipSpec(
        bell_mf, 1.0, '广义钟形 exp 型（尾部厚，适合明显过渡带）'),
    'algebraic_bell': MembershipSpec(
        algebraic_bell_mf, 1.0, '代数钟形 1/(1+|z|^2b)（尾部衰减快）'),
    'sigmoid': MembershipSpec(
        sigmoid_mf, None, 'S 型（单侧递增，适合越大越好的量）'),
    'z_sigmoid': MembershipSpec(
        z_sigmoid_mf, None, 'Z 型（单侧递减，适合越小越好的量）'),
    'singleton': MembershipSpec(
        singleton_mf, None, '单点（离散输入）'),
}


# ============================================================================
# 模块级健全性自检（仅在 `python -m memberships` 时执行）
# ============================================================================

if __name__ == '__main__':
    xs = np.linspace(0.0, 10.0, 11)
    for name, spec in MEMBERSHIP_SPECS.items():
        shape = spec.default_shape
        y = spec.func(xs, 5.0, 4.0, shape)
        print(f'{name:18s} μ(5)={float(np.asarray(y)[5]):.4f}  '
              f'min={float(np.min(y)):.4f}  max={float(np.max(y)):.4f}  {spec.desc}')
