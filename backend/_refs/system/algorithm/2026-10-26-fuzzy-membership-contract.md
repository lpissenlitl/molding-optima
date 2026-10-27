# 隶属度函数统一契约规格（E25）

> **状态**：✅ **已实施**（E25-1 ~ E25-4 全部落地，验收全绿）—— 落地与本规格的差异见 **§10**
> **日期**：2026-10-26
> **范围**：`backend/process/algorithms/fuzzy/fuzzy_core/`
> **前置轮次**：E24（`functional.py` 瘦身 + tri 退役 + 桶中心收口），见
> `2026-10-23-fuzzy-entry-refactor-execution.md` §2.31

---

## 0. 一句话

把 `fuzzy_core/functional.py` 拆成 **`memberships.py`（隶属度函数族）** +
**`defuzz.py`（反模糊化）**，隶属度函数全部改用**统一签名**
`(x, center, width, shape=None)`，并按模糊理论标准族**补齐缺失形状**。

---

## 1. 问题诊断

### 1.1 命名

`functional.py` 是形容词/副词形式，Python 生态里默认指"函数式编程工具"，
与本文件实际内容（隶属度函数库 + 反模糊化）不符。仓库其余模块一律用复数名词
（`specs.py` / `contracts.py` / `profiles.py` / `nets.py` / `rules.py` /
`keywords.py` / `recommendations.py` / `field_names.py`），`functional` 是全仓孤例。

### 1.2 分类轴错误（原先的隐患）

`functional.py` 把**推理链首尾两端**装在一个文件里：

```
模糊化(隶属度函数) → 蕴含 → 聚合 → 去模糊化(centroid)
    functional.py            ↑ 蕴含/聚合在 nets.py L281/L291 内联   functional.py
```

- **推理阶段不同**：隶属度函数 = 模糊化阶段（推理链第 1 步）；
  反模糊化 = 结论阶段（推理链最后 1 步）。
- **输入范式不同**：隶属度函数 `(标量/数组, 中心, 宽…)` → 隶属度 ∈ [0,1]；
  反模糊化 `(采样点序列, 隶属度序列)` → 实数。
- **扩展节奏不同**：隶属度族扩展 = 加新**形状**；
  反模糊化族扩展 = 加新**方法** —— `macros.DEFUZZ_METHODS` 早已列出
  `centroid / bisector / mom / som / lom` 5 个，仅实现 1 个 ⇒ 这是一个已被预期的族。

### 1.3 族不完整（按"领域完备"判定，不按当前调用点判定）

隶属度函数族是模糊理论的标准词汇表。算法资产的完备性按**领域词汇覆盖**算。
现状只实现了 9 个函数里的 6 个，且其中 4 个零生产调用。

### 1.4 五个硬问题

| # | 问题 | 位置 | 性质 |
|---|---|---|---|
| 1 | `assert` 当运行时校验 —— `python -O` 下整条被优化掉，参数非法不报错、直接算出错误隶属度 | L73 / L113 | **真 bug 风险** |
| 2 | 3 个别名是纯转发 + 假契约（标注 `np.ndarray` 但实际支持 scalar），且 docstring 声称"供上层调用"而**上层从未调用** | L48 / L99 / L139 | 死代码 + 假契约 |
| 3 | 输入归一化（`isinstance` 三分支）抄了 3 遍 | L38-43 / L74-79 / L114-119 | 应抽私有 helper |
| 4 | 缺 `__all__` ⇒ `fuzzy_core/__init__.py` 的 `from .functional import *` 把 `np` / `Union` / `ArrayLike` / `centroid` / `bell_mf` / `singleton_mf` 泄漏到顶层 | 文件头 | **L5 后半，E24 登记未处理** |
| 5 | `bell_mf` 缺绝对值 ⇒ `b < 1` 时隶属度 > 1 甚至除零崩溃；且命名与公式错位（Mamdani 广义钟形是 `exp(-|…|^(2m))`） | L148-150 | **真 bug 风险** |

附带：`singleton_mf` 对 list 输入直接崩（`x == center` 得到标量 `False`），
与同文件其它函数的"支持 list"承诺不一致。

---

## 2. 命名决策

| 现状 | 目标 | 理由 |
|---|---|---|
| `functional.py` | **`memberships.py`** | 名实相符；仓库复数名词风格；全仓无撞名 |
| （同文件内） | **`defuzz.py`**（新建） | 反模糊化是独立族（见 §1.2 第 3 条） |

### 2.1 函数正名清单

| 旧名 | 新名 | 处置 |
|---|---|---|
| `gauss_mf` | `gaussian_mf` | **正名为主函数**（原 `gaussian_mf` 是别名，升级） |
| `tri_mf` | `triangular_mf` | **正名为主函数**（原 `triangular_mf` 是别名，升级） |
| `trap_mf` | `trapezoidal_mf` | **正名为主函数**（原 `trapezoidal_mf` 是别名，升级） |
| `bell_mf` = `1/(1+|((x-c)/a)^(2b))` | **`algebraic_bell_mf`** | 正名（代数型钟形 / Sugeno 型） |
| — | **`bell_mf`** = `exp(-|((x-c)/a)^(2m))` | **新名占用**（Mamdani 广义钟形，教材标准） |
| `singleton_mf` | `singleton_mf` | 保留，修 list 支持 |
| `centroid` / `defuzz` | 同名，移入 `defuzz.py` | 移动 |

**老 fuzzykit 名（`gauss_mf` / `tri_mf` / `trap_mf`）一律删除**：
零外部调用（`features.py` 与 `test_nets.py` 同步改名），依据 E24 已确立的
「内核遗留代码清理」判定。保留两套名字 = 假契约。

---

## 3. 统一签名契约（核心）

```python
def <shape>_mf(x, center, width, shape=None) -> ArrayLike
```

| 参数 | 语义 |
|---|---|
| `x` | 标量或数组（`float` / `int` / `list` / `np.ndarray`），统一转 float 数组 |
| `center` | **隶属度峰中心**（该桶在论域上的位置） |
| `width` | **总宽**（该桶占据的论域跨度） |
| `shape` | 形状参数；`None` = 该族默认形状；语义**因族而异**（见 §3.2） |

### 3.1 为什么是"总宽"

`features.py` 现有 σ 推导为 `论域宽 / (2 * (lvl-1))`，而 `bucket_centers` 是
**等分位点** ⇒ 相邻桶间距 = `论域宽 / (lvl-1)` ⇒ 恒有 `σ = 间距 / 2`。

统一签名下取 `width = 相邻桶间距`、`σ = width / 2` ⇒ **数值逐档完全相等**：

| 档数 | 论域 [0,200] 桶中心 | 相邻间距 | 新 width | 新 σ | 旧 σ |
|---|---|---|---|---|---|
| 3 | 0 / 100 / 200 | 100 | 100 | 50 | 50 |
| 5 | 0 / 50 / 100 / 150 / 200 | 50 | 50 | 25 | 25 |
| 7 | 0 / 33.3 / 66.7 / 100 / 133.3 / 166.7 / 200 | 33.33 | 33.33 | 16.67 | 16.67 |
| 9 | 0 / 25 / 50 / 75 / 100 / 125 / 150 / 175 / 200 | 25 | 25 | 12.5 | 12.5 |

⇒ **本轮改造可做到生产行为零变化。**

### 3.2 各族公式与 shape 语义

| 函数 | 公式 | `shape` 语义 | 默认 |
|---|---|---|---|
| `gaussian_mf` | `exp(-0.5·|((x-c)/σ)|^p)`，`σ = width/2`；**`p=2` 走老口径原式** `exp(-(x-c)²/(2σ²))` | `p` 形状指数 | `p=2`（标准高斯） |
| `two_piece_gaussian_mf` | 左右两段高斯，`σ_l = σ_r = width/2` | `(p_left, p_right)` | `(2, 2)` |
| `triangular_mf` | 顶点 `center`，底边 `[center - width·L, center + width·R]` | `(L, R)` 肩宽占比（**L + R = 1**） | `(0.5, 0.5)` 对称 |
| `trapezoidal_mf` | 底边 `[center - width/2, center + width/2]`，平顶两侧各留 `L·width` / `R·width` | `(L, R)` 平顶两侧占比（**L + R ≤ 1**，余下为平顶） | `(0.25, 0.25)` ⇒ 平顶宽 50% |
| `bell_mf` | `exp(-|((x-c)/a)|^(2m))`，`a = width/2` | `m` 陡峭度 | `m=1` |
| `algebraic_bell_mf` | `1/(1+|((x-c)/a)|^(2b))`，`a = width/2` | `b` 陡峭度 | `b=1` |
| `sigmoid_mf` | `1/(1+exp(-(x-c)/d))`，`d = width/4` | 无 | — |
| `z_sigmoid_mf` | `1/(1+exp((x-c)/d))`，`d = width/4` | 无 | — |
| `singleton_mf` | `x == center` | 无（`width` 忽略） | — |

**`d = width/4` 的依据**：S 型过渡带跨度 ≈ `4d` ⇒ 取 `width/4` 使过渡带
跨度约等于该桶宽度。

### 3.3 统一签名带来的收益

- `features.py` 只需**一套**参数推导（中心 + 宽度），新增形状 = 加一个函数
  + 加一行分派。
- 三角 / 梯形的"肩宽 / 平顶"不再是散落在调用方的魔数，而是**显式 shape 参数**。
- 补族时**不需要**改 `features.py`。

---

## 4. 分派表（声明与实现同源）

延续 E24-5「声明 = 实现」的成果，但**不退回手写 if/elif**：

```python
# memberships.py
@dataclass(frozen=True)
class MembershipSpec:
    func: Callable          # 统一签名的隶属度函数
    default_shape: Any      # 该族默认 shape
    desc: str               # 一句话说明

MEMBERSHIP_SPECS = {
    'gauss': MembershipSpec(gaussian_mf, 2, '高斯（σ = width/2，p=2）'),
    'tri':   MembershipSpec(triangular_mf, (1.0, 1.0), '三角形（对称）'),
    ...
}
```

`macros.MEMBERSHIP_TYPES` 改为**由分派表的键派生**：

```python
# macros.py
from .memberships import MEMBERSHIP_SPECS   # ← 会不会循环 import？见 §6.2
MEMBERSHIP_TYPES = tuple(MEMBERSHIP_SPECS)
```

⚠️ **循环 import 风险**：`macros.py` 被 `memberships.py` 依赖（若需要词表），
而 `memberships.py` 不应依赖 `macros.py`（隶属度函数是纯数学，不需要词表）⇒
`macros → memberships` 单向即可，**前提是 `memberships.py` 不 import `macros.py`**。
本规格中 `memberships.py` 零依赖（仅 numpy），满足该前提。

---

## 5. 影响面

| 文件 | 改动 |
|---|---|
| `fuzzy_core/memberships.py` | **新建**（原 `functional.py` 的隶属度部分重写） |
| `fuzzy_core/defuzz.py` | **新建**（原 `functional.py` 的 `centroid` / `defuzz` 移入） |
| `fuzzy_core/functional.py` | **删除** |
| `fuzzy_core/models/features.py` | 改分派；`membership_dict` 值由 `[mean, sigma]` 改为 `[center, width]`；`from ..functional import gauss_mf` → `from ..memberships import ...` |
| `fuzzy_core/models/nets.py` | `from ..functional import defuzz` → `from ..defuzz import defuzz` |
| `fuzzy_core/__init__.py` | `from .functional import *` → `from .memberships import *` + `from .defuzz import *`（各带 `__all__`） |
| `fuzzy_core/macros.py` | `MEMBERSHIP_TYPES` 由分派表派生；`DEFUZZ_METHODS` 保持 5 项不变 |
| `fuzzy_core/tests/test_nets.py` | 导入改名（`gauss_mf`→`gaussian_mf`，`tri_mf`→`triangular_mf`，`defuzz` 路径变） |
| `fuzzy_core/tests/test_macros.py` | 无需改（不依赖 functional） |

**`membership_dict` 语义变更的安全性**（已核）：
- 值的读取点**只有** `features.py` 自身的 `get_value_by_level` 解包；
- `test_nets.py` 只读 `.keys()`；
- `test_inference_gates.py` 只调 `get_value_by_level(x, level)`；
- `nets.py` 3 处 `FuzzyFeature(...)` 构造均显式传 `'gauss'`。

⇒ 内部表示由 `[mean, sigma]` 改 `[center, width]` 对外零影响。

---

## 6. 实施批次

### E25-1 拆文件改名（零行为变化）
- `functional.py` → `memberships.py` + 新建 `defuzz.py`（内容原样搬）
- 4 处 import 同步
- 验收：pytest 32 + 11 全过；等价对拍 diff = 0

### E25-2 隶属度模块重写（统一签名 + 正名 + 修 bug + 补族）
- `memberships.py` 重写：统一签名、正名、`assert`→`ValueError`、
  抽 `_to_array`、修 `singleton_mf` 的 list 支持、补 `|…|` 绝对值、
  补 `two_piece_gaussian_mf` / `sigmoid_mf` / `z_sigmoid_mf` /
  `algebraic_bell_mf` / 标准 `bell_mf`、加 `__all__` + `MEMBERSHIP_SPECS`
- `defuzz.py` 加 `__all__`
- 验收：pytest 全过；高斯路径数值与改前**逐点相等**；新族自检可跑

### E25-3 features.py 分派 + macros 派生
- `features.py`：按 `MEMBERSHIP_SPECS` 分派；`membership_dict` 改 `[center, width]`
- `macros.py`：`MEMBERSHIP_TYPES` 由分派表派生（`macros → memberships` 单向）
- 验收：默认 `'gauss'` 路径**数值逐点等于改前**；pytest 全过

### E25-4 全轮验收 + 文档同步
- 真实 DB 端到端 / 字段名对拍 / 零依赖 / library 布局 / compileall
- 执行纪要文档续写 §2.32

---

## 7. 明确不做

- **π 型、分段线性（非连续型）隶属度函数** —— 优先级低，当前论域场景用不上
- **1 阶 T-S 的加权最小二乘** —— 属结论层算法，不属本文件；且 `TskRuleNet` 仍是占位死类
- **`macros.DEFUZZ_METHODS` 的另外 4 个方法**（bisector / mom / som / lom）——
  本轮只搬移 `centroid`，其余仍 `NotImplementedError`
- **不改变默认隶属度类型** —— 仍是 `'gauss'`，生产行为零变化
- **不删 `centroid` 的 `len(x)==1` 特判** —— 属既有行为，移入 `defuzz.py` 时原样保留

---

## 8. 验收口径

| 项 | 口径 |
|---|---|
| 等价性 | 高斯路径（3/5/7/9 档 × 网格采样）改前改后**逐点数值相等** |
| 独立参照系 | 手工可算样例（高斯 μ(c)=1、μ(c±σ)=e^{-0.5}；三角 μ(c)=1、μ(a)=0） |
| 回归 | `pytest fuzzy_core/tests` + `pytest backend/tests` |
| 零依赖 | `import fuzzy_core` 不触发 Django ORM；顶层名泄漏 = 0 |
| 端到端 | 真实 DB 端到端 exit=0（numeric 10 / advisory 0） |

---

## 9. 待用户拍板项

- [x] 统一签名（用户拍板：**走统一签名**）
- [x] `bell_mf` 正名（用户拍板：**可以正名**）
- [x] 老 fuzzykit 名 `gauss_mf` / `tri_mf` / `trap_mf` 一并删除（按 E24 先例推定）
- [x] 三角 / 梯形的 `shape` 是否需要支持**非对称**（`(L, R)`）—— **落地按支持实施**：
      三角 `L+R=1`、梯形 `L+R≤1`，越界即 `ValueError`（校验规则见 §10.2）

---

## 10. 落地差异回填（E25 实施后）

> 本节记录**实施过程中偏离或补充本规格**之处，及其实测依据。
> 落地代码：`fuzzy_core/memberships.py`（581 行）、`fuzzy_core/defuzz.py`、
> `fuzzy_core/models/features.py`。
> 执行纪要见 `2026-10-23-fuzzy-entry-refactor-execution.md` §2.32。

### 10.1 规格未覆盖、落地新增的四条（均由实测 / 上游代码倒逼）

| # | 落地项 | 规格原状态 | 落地做法 | 依据 |
|---|---|---|---|---|
| 1 | **`width = 0`（退化论域）** | 未提 | **允许 0**，不抛错（`_non_negative`）；σ=0 ⇒ 高斯产出 `nan`（中心点）/ `0`（其余点） | 上游 `engine.py` 缺权威元数据时按实时值推测论域（`max_val = 当前值 * 2`）⇒ 当前值为 0 时论域**退化**为 `[0, 0]`。收紧为硬错误会把上游的**静默坏值变成内核崩溃** ⇒ 按“最坏情况更安全”原则保留旧语义（改前 `exp(-(x-μ)²/(2σ²))` 在 σ=0 时也是这个结果，**逐位一致**） |
| 2 | **倒序论域** | 未提 | `features.py` 取 `span = abs(high - low)` + `logger.warning` | 同上：当前值为**负**时 `max_val = 当前值 * 2` 使区间**倒挂**（如 `[0, -6]`）⇒ 改前 σ **带符号**，高斯只用 σ² ⇒ 取绝对后与改前**逐位相等**；对其余形状则是唯一自洽的定义（跨度非负） |
| 3 | **标量输入统一转 `np.float64`** | 未提 | `_prepare` 标量分支返回 `np.float64(x)`，**不是** Python `float` | ⚠️ **除零语义不同**：Python float 除零 → `ZeroDivisionError`（内核崩溃）；numpy 标量除零 → `inf`/`nan`（静默）。改前老实现把桶中心/σ 以 numpy 标量传入 ⇒ 走的是 numpy 语义 ⇒ 转 Python float 会把“静默 nan”变成“内核崩溃”。**实测**：转 Python float 时退化论域 **153/255** 处对拍差异（老 nan/0 vs 新 `ZeroDivisionError`）；改回 `np.float64` 后差异归 0 |
| 4 | **`shape` 校验规则** | 只列语义，未列约束 | 新增 `_shape_pair(shape, default, *, positive, sum_exact, sum_max, label)` 统一校验（见 §10.2） | 三角 `L+R≠1` 会让底边总跨度 ≠ `width`（与统一签名的“总跨度”语义自相矛盾）；梯形 `L+R>1` 会让 `b > c`（平顶变负）⇒ 均属**静默算错**，必须拦 |

### 10.2 `shape` 校验规则表（落地）

| 族 | 约束 | 违反时的行为 | 代码参数 |
|---|---|---|---|
| 三角形 `tri` | `L > 0`、`R > 0`、**`L + R = 1`**（容差 1e-9） | `ValueError` | `sum_exact=1.0` |
| 梯形 `trap` | `L > 0`、`R > 0`、**`L + R ≤ 1`**（余下为平顶） | `ValueError` | `sum_max=1.0` |
| 双高斯 `two_piece_gauss` | `L > 0`、`R > 0` | `ValueError` | `positive=True` + `_positive` 复核指数 |
| 高斯 `gauss` / 钟形 `bell` / 代数钟形 `algebraic_bell` | 指数 `> 0` | `ValueError` | `_positive` |
| S 型 / Z 型 / 单点 | 无 shape | — | — |

> ⚠️ 一律用 `ValueError` 而非 `assert` —— `python -O` 下 `assert` 被优化掉，等于没校验（本轮已把老实现的 `assert` 全部替换）。

### 10.3 落地对规格的四处修正

| # | 规格原文 | 落地 | 原因 |
|---|---|---|---|
| 1 | 三角默认 shape = `(1, 1)` | **`(0.5, 0.5)`** | 与新增的 `L+R=1` 约束**自相矛盾**（1+1=2）⇒ 按约束反推默认值 |
| 2 | 高斯公式 `exp(-|z|^p)` | **`p=2` 走老口径原式** `exp(-(x-μ)²/(2σ²))`，`p≠2` 才走 `exp(-0.5·|z|^p)` | 通用式在 `p=2` 时因**运算顺序**不同会产生 1 ULP 差异 ⇒ 改前逐位相等的生产路径必须走原式 |
| 3 | `fuzzy_core/__init__.py`：`from .defuzz import *` | **`from .defuzz import centroid`** | ⚠️ **模块与函数同名遮蔽**：`import *` 会把函数 `defuzz` 绑到包顶层、**覆盖同名子模块** `fuzzy_core.defuzz` ⇒ `from fuzzy_core import defuzz` 拿到的是函数（对拍脚本实测报 `AttributeError: 'function' object has no attribute 'centroid'`）⇒ 只导出 `centroid`，`defuzz` 保留模块语义 |
| 4 | 三角/梯形的非对称支持存疑 | **落地保留非对称支持**（`(L, R)`） | 落地按 §10.2 的约束支持非对称组合（三角 `L+R=1`、梯形 `L+R≤1`） |

### 10.4 落地确认无误、无需修正的规格条款

- **§3.1 数值等价性**：成立。σ 沿用原推导式（`论域宽 / (2*(lvl-1))`）、`width = 2σ`（乘 2 精确）、函数内 `σ = width/2`（精确还原）⇒ **逐位相等**（对拍实测 0 差异）。
- **§4 循环 import 风险**：`macros → memberships` 单向成立 —— `memberships.py` **零依赖**（仅 `numpy` + `dataclasses`/`typing`），不 import `macros.py`。
- **§5 `membership_dict` 语义变更**：成立 —— 读取点只有 `features.py` 自身解包，`test_nets.py` 只读 `.keys()`，`test_inference_gates.py` 只调 `get_value_by_level`。
- **§7 明确不做**：全部遵守（未加 π 型、未实现另外 4 种反模糊化方法、默认类型仍 `'gauss'`、`centroid` 的 `len(x)==1` 特判原样保留）。

### 10.5 落地后的验收结论

对拍脚本：`_dev_refs/_e25_diffcheck.py`（内嵌改前 `functional.py` 权威基线）。

| 项 | 结果 |
|---|---|
| 对拍（5 档） | **零差异** —— 严格档（高斯/centroid/defuzz，atol=0）/ 参数化重述档（rtol=1e-12）/ 有意行为变化档（5 项）/ 手算参照系（12 解析性质 + 9 形状值域 + 统一签名契约）/ FuzzyFeature 端到端（4 种论域 × 2 档 × 51 点逐点，含倒序与退化论域） |
| pytest | `fuzzy_core/tests` **32 passed** + `backend/tests` **11 passed** |
| 零依赖 | **PASS** —— 顶层名泄漏 = NONE |
| library 布局 | **PASS** |
| compileall | exit = 0 |
| 残留扫描 | `functional` / `gauss_mf` / `tri_mf` / `trap_mf` 命中项**全部**是历史说明文字（docstring）与测试函数名，**无生产代码残留** |
| 真实 DB 端到端 | ⚠️ **本轮未跑**（需真实 DB 环境）；内核改动已由 FuzzyFeature 端到端对拍逐点覆盖 |

**有意行为变化（5 项，与“零差异”并存）**：

1. 老 `bell_mf`（= 现 `algebraic_bell_mf`）缺 `|·|` ⇒ `b<1` 且 `x<center` 时隶属度 **> 1** ⇒ 已修。
2. 老 `singleton_mf` 对 list 输入 `x == center` 得标量 `False` ⇒ **结果全 0**（能跑但算错）⇒ 已修。
3. 老 `bell_mf` 不支持 list 输入（`list - float` → `TypeError`）⇒ 现支持。
4. `assert` → `ValueError`（`python -O` 下校验生效）。
5. 三角/梯形的 `shape` 越界（`L+R` 不合法）⇒ 现明确 `ValueError`，不再静默算错。
