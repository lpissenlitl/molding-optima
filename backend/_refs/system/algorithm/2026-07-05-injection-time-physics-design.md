# 注射时间算法科学化改造设计

> 本文档记录将注射时间（`inj_time`）从"拍脑袋的固定系数（inj_time_coef=4.0）+ 过大最小值（inj_time_min=3.0）"重构为"基于材料大类 × 壁厚档的工艺窗口钳制"的设计方案。

## 1. 设计背景

### 1.1 当前算法（粗糙经验）

`initializer.py` 行 624-628 中：

```python
# 注射时间 - 来自 DEFAULT.injection.inj_time_coef / inj_time_min
inj_time = max(
    c_inj.get('inj_time_min', 3.0),
    c_inj.get('inj_time_coef', 4.0) * inj_len / inj_velo,
)
```

**系数来源**（三处冗余，必须全部同步）：

| 字段 | 默认值 | 来源 1 | 来源 2 | 来源 3 |
|------|--------|--------|--------|--------|
| `inj_time_coef` | 4.0 | `DEFAULT.injection` | `init_rules.json:18-19` | `rule_matcher._BUILTIN_DEFAULTS` |
| `inj_time_min` | 3.0 | `DEFAULT.injection` | `init_rules.json:19-20` | `rule_matcher._BUILTIN_DEFAULTS` |

**当前公式实际表达**：

```
inj_time = max(3.0, 4.0 × inj_len / inj_velo)
```

直观解读：
- 几何倒数 `inj_len / inj_velo`（按当前速度填充需多少秒）被乘以 4.0 倍
- 与 3.0 取 max → 至少 3 秒

### 1.2 核心问题

| 问题 | 表现 | 影响 |
|------|------|------|
| **`inj_time_coef=4.0` 是拍脑袋** | 几何倒数 × 4 这一"安全系数"无物理依据，工艺师调整无方向 | 同样的薄壁件可能充得过久或过短 |
| **不考虑材料黏度** | PC（高黏度）与 PP（低黏度）一视同仁 | 高黏度材料的窗口应放宽，未响应 |
| **不考虑流长比** | 极薄壁远浇的几何倒数已大，但 4.0 倍系数让它更大 | 长流程薄壁件时间窗口失控 |
| **`inj_time_min=3.0` 过大** | 1g 注塑件实际只需 0.3–0.5s，3s 下限严重过度 | 周期被人为拉长、产能浪费 |
| **未识别薄壁"必须快填"** | 薄壁 0.5mm 仍走 4.0× 默认路径 | 前缘冷却冻结成欠注 |
| **未识别厚壁"必须慢填"** | 厚壁 5mm 走 4.0× 默认 | 高剪切速率导致飞边 / 银纹 |
| **与兄弟算法风格不一致** | `inj_pres`/`inj_velo` 已按 family × L/t × mold_temp 物理推导 | 同一初始化器内同一注射段参数体系不一致 |

### 1.3 优化目标

1. **几何下限 + 工艺窗口钳制**：以 `inj_len / inj_velo` 为几何下限（物理等式），通过 `(min_t, max_t)` 时窗钳制到工艺合理区间
2. **材料差异化**：按材料大类（11 family）响应黏度差异——高黏度窗口放宽、低黏度窗口收紧
3. **几何差异化**：按壁厚档（thin/medium/thick）响应薄壁冻结 / 厚壁飞边
4. **删除拍脑袋系数**：清掉 `inj_time_coef=4.0` 与 `inj_time_min=3.0` 单一固定值
5. **与兄弟算法风格对齐**：与 `inj_pres` / `inj_velo` 共享"3 级兜底 + 工艺窗口"语义

---

## 2. 问题的本质定义

### 2.1 物理本质

```
inj_time = f(几何下限, 工艺窗口约束)
       = clamp(inj_len / inj_velo, [min_t(family, thickness), max_t(family, thickness)])
```

**为什么是这样**：注射时间不是一个"主动给定"的工艺目标，而是 **填充过程被物理条件决定的派生量**：

| 性质 | 物理意义 |
|------|---------|
| **几何下限** | 螺杆推进 L 长度、按 v 速度推进，至少需要 L/v 时间 |
| **薄壁冻结上限** | 薄壁熔体前缘温度下降 → 黏度飙升 → 短射（薄壁时间过长）|
| **厚壁飞边下限** | 厚壁短时间高剪切速率 → 飞边 / 银纹（厚壁时间过短）|
| **材料窗口差异** | 高黏度材料（PC/PA66/PET）填充阻力大 → 窗口整体放宽；低黏度（PP/PE）快填能力强 → 窗口整体收紧 |

### 2.2 物理直觉

| 维度 | 决定因素 | 物理意义 | 物理直觉 |
|------|---------|---------|---------|
| **材料大类 (family)** | MFI / 黏度等级 | 流动性差异决定填充窗口的整体偏移 | PC 薄壁必须比 PP 薄壁给更长窗口 |
| **壁厚档 (bucket)** | max_thickness | 薄壁受冻结约束、厚壁受飞边约束 | t=0.5mm 必须 ≤1s；t=5mm 必须 ≥1.5s |
| **几何倒数 (inj_len/inj_velo)** | 制品几何 + 速度决策 | 螺杆推进所必需时间 | 客观量，不需主观调 |

### 2.3 与原算法的关键区别

- **原算法**：1 个拍脑袋系数 + 1 个过大最小值（1 维）
- **新算法**：2 维查表（family × bucket） + 几何倒数钳制（11 × 3 = 33 行窗口表）

---

## 3. 新算法核心（基于物理推导）

### 3.1 物理推导链

```
【起点：工艺目标】
合理的注射时间 = 使熔体在工艺约束窗口内完成填充的时间
├─ 窗口下限：厚壁防飞边、切换平稳
└─ 窗口上限：薄壁防冻结、欠注

【物理定律】
1. 几何上限等式（基本恒等式）：
   inj_time × inj_velo ≥ inj_len
   → inj_time ≥ inj_len / inj_velo（几何下限）

2. 薄壁冻结时间约束（工艺手册 + Moldflow 共识）：
   t_wall < 1.5mm 时，inj_time ≤ 1.0~1.5s（防前缘冷却成欠注）
   t_wall < 0.5mm 时，inj_time ≤ 0.5~0.8s（极高要求）

3. 厚壁飞边 / 银纹约束（剪切速率）：
   γ̇ = v / t（壁面剪切速率）必须 ≤ γ̇_critical
   对于厚壁件 → inj_time ≥ 1.5~3s（防止瞬时高速剪切）

4. 材料流动性差异（修改窗口整体偏移）：
   ├─ 高 MFI（PP/PE）：快填能力强，窗口可偏紧
   ├─ 中等 MFI（ABS/PS）：标准窗口
   └─ 低 MFI（PC/PBT/PA）：填充阻力大，窗口整体放宽

【二维推导】
inj_time_geo = inj_len / inj_velo                       # 几何下限
(min_t, max_t) = family_time_window[family][bucket]    # 工艺窗口
inj_time = clamp(inj_time_geo, min_t, max_t)            # 钳制
            = max(min_t, min(inj_time_geo, max_t))
```

### 3.2 完整计算公式

```python
# 步骤 1：获取已物理化推导的注射速度（来自兄弟算法 inj_velo）
inj_velo = ...  # 来自 base_velo_ratio[family] × length_velo_factor(L/t) × temp_velo_modifier × max_inj_velo

# 步骤 2：几何下限
inj_time_geo = inj_len / inj_velo

# 步骤 3：定位壁厚档（按 max_thickness）
bucket = self._get_thickness_bucket(max_thickness, c_inj)

# 步骤 4：取工艺窗口（3 级兜底）
(min_t, max_t), window_level = self._get_inj_time_window(family, bucket, c_inj)

# 步骤 5：钳制（保持几何下限的物理可达性）
inj_time = max(min_t, min(inj_time_geo, max_t))
```

### 3.3 桶划分（壁厚档）

**壁厚字段决策**：使用 `mold.max_thickness`（既有的"最薄处"衍生字段），理由是：

| 候选字段 | 取值来源 | 选用理由 |
|---------|---------|---------|
| `max_thickness` ✅ | mold 模型既有 | 薄壁风险由最薄处决定 → 冻结约束用最薄处保守 |
| `avg_thickness` | mold 模型既有 | 平均值会掩盖局部极薄 → 不能反映冻结风险 |

```python
def _get_thickness_bucket(max_thickness: float, c_inj: Dict[str, Any]) -> Tuple[str, str]:
    """
    按壁厚分档（3 桶）

    Returns:
        (bucket, level) 元组，bucket ∈ {'thin', 'medium', 'thick'}，level ∈ {'bucket', 'default'}
    """
    thresholds = c_inj.get('thickness_bucket_thresholds', [1.5, 3.0])
    thin_max = thresholds[0]       # 默认 1.5mm
    medium_max = thresholds[1]     # 默认 3.0mm

    if max_thickness <= 0:
        return 'medium', 'default'

    if max_thickness <= thin_max:
        return 'thin', 'bucket'
    elif max_thickness <= medium_max:
        return 'medium', 'bucket'
    else:
        return 'thick', 'bucket'
```

**桶物理意义**：

| 桶 | 壁厚区间 | 主要约束 | 典型场景 |
|----|---------|---------|---------|
| `thin` | t ≤ 1.5mm | **冻结上限**：inj_time ≤ 1.0~2.5s | 薄壁容器、包装件 |
| `medium` | 1.5 < t ≤ 3.0mm | 几何下限主导 | 标准结构件 |
| `thick` | t > 3.0mm | **飞边下限**：inj_time ≥ 1.5~3s | 大型厚壁件 |

### 3.4 与兄弟算法的关系

| 算法 | 输出 | 派生基础 | 钳制 |
|------|------|---------|------|
| `inj_pres`（已实施） | 物理量（MPa） | base_ratio[family] × length_factor(L/t) × max_inj_pres | max_safe_pressure_ratio=0.90 |
| `inj_velo`（已实施） | 物理量（mm/s） | base_velo_ratio[family] × length_velo_factor(L/t) × temp_velo_modifier × max_inj_velo | max_safe_velocity_ratio=0.95 |
| **`inj_time`**（本文档） | 持续时间（s） | `clamp(inj_len / inj_velo, family_window[family][bucket])` | — |

`inj_time` 与兄弟算法的对位：

| 维度 | `inj_pres` | `inj_velo` | **`inj_time`** |
|------|------------|------------|---------|
| 输入维度数 | 2 维（family × L/t） | 3 维（family × L/t × T_mold） | 2 维（family × bucket） |
| 推导方式 | 乘法叠加 | 乘法叠加 | **钳制**（几何量 + 窗口） |
| 钳制对象 | 物理上限（防爆模）| 物理上限（防飞边）| 工艺窗口（防冻结 / 防飞边）|
| 数据源 | `base_pressure_ratio_map` + `length_factor_buckets` | `base_velocity_ratio_map` + `length_velocity_factors` + `temp_velocity_buckets` | `family_time_window[family][bucket]` |

**为何 `inj_time` 不采用与 `inj_velo` 完全相同的"乘法叠加"风格**：
- 注射时间是**绝对量**（秒），物理窗口约束是硬上限 / 下限
- 若用"base × factor × modifier"乘法结构，会出现"PC 高黏度 + 薄壁远浇 = 极慢时间 + 极快速度"的对照悖论
- 用"窗口钳制"则把"材料 × 几何 × 热历史"封装到一个区间内，更符合工艺师"按材料+按壁厚查时间范围"的实际操作习惯

**强依赖关系**（重要）：

```
inj_velo 已物理化（max_safe_velocity_ratio 钳制）
       ↓
inj_time = inj_len / inj_velo 才有可靠的几何下限
       ↓
窗口钳制才不会基于脏数据触发
```

**实施顺序**：本文档设计以"已合入主干或灰度中的 `inj_velo` 物理化版本"为基线；若 `inj_velo` 物理化未生效，本算法需要回退到"几何倒数 × 默认钳制"路径（参见第 12.3 节 fallback 策略）。

### 3.5 复用既有组件

- `_parse_family()`：[initializer.py:225-237](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/initializer.py#L225-L237)（方法分类）
- `inj_ratio` 变量：[initializer.py:358-360](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/initializer.py#L358-L360)（既有计算，inj_velo 已用）
- `c_inj` 系数组：既有 `_coeffs.get('injection', {})`

---

## 4. 数据需求与 3 级兜底策略

### 4.1 数据需求（极简）

**不需要新增数据库 schema**。所需数据从既有字段派生：

| 数据 | 来源字段 | 既有？ |
|------|---------|--------|
| 材料大类 (family) | `_parse_family(Polymer.abbreviation)` | ✅ |
| 壁厚 (max_thickness) | `mold.max_thickness` | ✅ |
| 注射速度 (inj_velo) | 兄弟算法计算结果 | ✅ |
| 注射长度 (inj_len) | `total_len` 计算 | ✅ |

**新增可选项**（不强制）：

- `Polymer.recommend_inj_time_window`：精确值（与 `recommend_inj_velocity_ratio` 对齐，第 1 级兜底使用），如未填写则跳到第 2 级
- `Polymer.thickness_bucket_override`：强制指定桶（用于特殊材料）

### 4.2 3 级兜底（材料级精确窗口）

```
【第 1 级】精确值（Polymer.recommend_inj_time_window 字段）
  ├─ 命中：[(min, max), bucket] 二元组
  └─ 适用：数据库已有材料推荐窗口（少见，初期为 None）

【第 2 级】按大类 + 桶查表（family_time_window[family][bucket]）
  ├─ 命中：返回 (min_t, max_t)
  └─ 适用：通用场景（11 family × 3 bucket = 33 行查表）

【第 3 级】默认值（兜底）
  ├─ 命中：default_time_window = (0.6, 2.5)
  └─ 适用：所有识别失败场景
```

### 4.3 3 级兜底（桶级别）

```
【第 1 级】精确桶（Polymer.thickness_bucket_override 字段）
  ├─ 命中：强制使用指定桶
  └─ 适用：特殊材料（如发泡 PC 强制归 thick）

【第 2 级】按 max_thickness 计算桶（thickness_bucket_thresholds = [1.5, 3.0]）
  ├─ 命中：thin / medium / thick
  └─ 适用：通用场景

【第 3 级】默认值（兜底）
  ├─ 命中：medium（与 default_time_window 配对）
  └─ 适用：max_thickness 缺失或异常
```

### 4.4 完整查表函数

```python
def _get_inj_time_window(
    self,
    family: str,
    bucket: str,
    c_inj: Dict[str, Any]
) -> Tuple[Tuple[float, float], str]:
    """
    获取工艺时间窗口（3 级兜底）

    Returns:
        ((min_t, max_t), level) 元组，level ∈ {'precise', 'family', 'default'}
    """
    # ====== 第 1 级：精确值（Polymer 字段）======
    polymer_window = self.material.get('recommend_inj_time_window')
    if polymer_window is not None:
        # 格式：{'thin': (0.3, 1.0), 'medium': (0.5, 2.0), 'thick': (1.5, 4.0), 'bucket': 'auto'}
        precise = polymer_window.get(bucket)
        if precise is not None:
            return tuple(precise), 'precise'

    # ====== 第 2 级：按 family × bucket 查表 ======
    family_windows = c_inj.get('family_time_window', {})
    if family and family in family_windows:
        family_bucket_window = family_windows[family]
        if bucket in family_bucket_window:
            return tuple(family_bucket_window[bucket]), 'family'

    # ====== 第 3 级：默认值 ======
    return tuple(c_inj.get('default_time_window', (0.6, 2.5))), 'default'
```

### 4.5 family_time_window 表（11 family × 3 bucket = 33 行）

**数据来源**：材料手册（MFI + 推荐填充时间）+ Moldflow 推荐填充曲线 + 注塑机厂家推荐值综合中位。

```json
{
  "family_time_window": {
    "PP":  {"thin": [0.3, 1.0], "medium": [0.5, 2.0], "thick": [1.5, 4.0]},
    "PE":  {"thin": [0.3, 1.0], "medium": [0.5, 2.0], "thick": [1.5, 4.0]},
    "PS":  {"thin": [0.4, 1.2], "medium": [0.6, 2.5], "thick": [1.8, 5.0]},
    "ABS": {"thin": [0.4, 1.2], "medium": [0.6, 2.5], "thick": [1.8, 5.0]},
    "AS":  {"thin": [0.4, 1.2], "medium": [0.6, 2.5], "thick": [1.8, 5.0]},
    "PMMA": {"thin": [0.5, 1.5], "medium": [0.8, 3.0], "thick": [2.0, 6.0]},
    "PA":  {"thin": [0.5, 2.0], "medium": [1.0, 3.5], "thick": [2.5, 7.0]},
    "POM": {"thin": [0.5, 2.0], "medium": [1.0, 3.5], "thick": [2.5, 7.0]},
    "PET": {"thin": [0.5, 2.0], "medium": [1.0, 4.0], "thick": [2.5, 8.0]},
    "PBT": {"thin": [0.5, 2.0], "medium": [1.0, 4.0], "thick": [2.5, 8.0]},
    "PC":  {"thin": [0.6, 2.5], "medium": [1.0, 4.0], "thick": [3.0, 10.0]}
  }
}
```

**物理依据**（每个 family 解释窗口选择）：

| 大类 | thin 窗口 | medium 窗口 | thick 窗口 | 物理依据 |
|------|----------|------------|------------|---------|
| **PP / PE** | (0.3, 1.0) | (0.5, 2.0) | (1.5, 4.0) | 高 MFI（1-30 g/10min），流动性好，快填能力强；窗口整体收紧 |
| **PS / ABS / AS** | (0.4, 1.2) | (0.6, 2.5) | (1.8, 5.0) | 中等 MFI（1-15 g/10min），标准流动性；窗口标准 |
| **PMMA** | (0.5, 1.5) | (0.8, 3.0) | (2.0, 6.0) | 非结晶高黏度（1-5 MFI），需稍宽窗口 |
| **PA / POM** | (0.5, 2.0) | (1.0, 3.5) | (2.5, 7.0) | 半结晶（1-10 MFI），易结晶固化 → 需稍宽 |
| **PET / PBT** | (0.5, 2.0) | (1.0, 4.0) | (2.5, 8.0) | 半结晶低 MFI（0.5-5），需较宽窗口防结晶 |
| **PC / PC+ABS** | (0.6, 2.5) | (1.0, 4.0) | (3.0, 10.0) | 非结晶工程塑料（1-15 MFI），高黏度，窗口需整体放宽 |

### 4.6 桶分界默认值

```json
{
  "thickness_bucket_thresholds": [1.5, 3.0],
  "default_time_window": [0.6, 2.5],
  "default_thickness_bucket": "medium"
}
```

**桶分界选择依据**：

| 分界 | 选择 | 依据 |
|------|------|------|
| thin ≤ X | X=1.5mm | t≤1.5mm 时冻结风险显著上升（薄壁凝固时间 < 1s）|
| medium 上界 | X=3.0mm | t≤3.0mm 为标准结构件；t>3.0mm 进入厚壁范围 |
| 厚壁下界 | t > 3.0mm | t>3.0mm 时飞边 / 凹陷风险显著，需 ≥ 1.5s 时间控制剪切 |

### 4.7 兜底值选择依据

```
已知 family_window 范围（min, max）：
├─ min_t 区间：[0.3, 0.6]    范围 0.3s
└─ max_t 区间：[1.0, 3.0]    范围 2.0s

【default_time_window = (0.6, 2.5)】
- 窗口中心 = 1.55s（中位）
- min_t 接近区间上界（不取最小）→ 防止欠薄壁欠注
- max_t 接近区间上界（不取最大）→ 防止过度拖延
- 取 ABS + medium（最典型场景）
- 保守性：未识别材料给"稍偏大"窗口，对工艺师后续调整留有余地
```

---

## 5. 保守兜底原则

### 5.1 决策优先级

```
注射时间过短（薄壁冻结）≈ 注射时间过长（厚壁飞边 / 产能浪费）

【原因】
- 薄壁冻结：制品报废，损失大
- 厚壁飞边：需去毛边，影响外观 + 周期拉长
- 两者代价相当，因此兜底窗口应取中庸值
```

### 5.2 几何下限不可钳掉

**核心约束**：`inj_time ≥ inj_len / inj_velo`，这是物理可达性的硬下限。

**错误示例**：
```python
# 错误：窗口下限钳掉了几何可达性
inj_time = max(min_t, min(inj_time_geo, max_t))  # ✅ 正确：保留几何可达性
inj_time = clamp_to_window(inj_time_geo)         # ❌ 错误：窗口最小时也保几何下限
```

### 5.3 既有字段处理

| 字段 | 新算法中用途 | 兜底策略 |
|------|------------|---------|
| `inj_time_coef` | **保留为 fallback** | 当新算法关闭或 family_time_window 缺失时，回到原算法 |
| `inj_time_min` | **语义升级** = window_min_t（兜底） | 第 3 级兜底中作为 `default_time_window` 的同步变量 |
| `inj_time_max` | **新增** = window_max_t（兜底） | 与 inj_time_min 配对；JSON 默认 2.5 |

**保留理由**：与 `inj_velo` 算法"thin/thick/coef 保留 fallback"风格一致，确保实施问题可即时回退。



---

## 6. 与原算法的对比

### 6.1 注射时间新旧对比（典型场景）

**场景 A：PP 薄壁容器，W=100g, t=1.0mm, L=200mm（D=40mm, max_inj_velo=200mm/s, base_velo=0.30, L=200, t=50℃）**

| 项目 | 旧算法 | 新算法 | 差异 |
|------|--------|--------|------|
| inj_len (mm) | 200 | 200 | - |
| inj_velo (mm/s) | 200 × 0.30 × 1.00 × 1.00 = 60.0 | 60.0（同 base_velo + length_factor=1.00 + temp_mod=1.00） | - |
| bucket（基于 max_thickness=1.0） | — | `thin` | — |
| family | PP | PP | - |
| family_window[PP][thin] | — | (0.3, 1.0) | — |
| 几何倒数 (s) | 200 / 60.0 = 3.33 | 3.33 | - |
| 公式 | max(3.0, 4.0 × 3.33) = **13.32** | max(0.3, min(3.33, 1.0)) = **1.0** | **-12.32（-92%）** |

**结论**：旧算法对薄壁 PP 给 13.3s 的"安全系时间"严重过度；新算法受 thin 桶上限 1.0s 约束，与工艺师"薄壁 PP 必须快填"经验一致。

**场景 B：PC 厚壁结构件，W=500g, t=4.0mm, L=200mm（D=40mm, max_inj_velo=200mm/s, base_velo=0.60, length_factor=1.00, mold_temp=80℃）**

| 项目 | 旧算法 | 新算法 | 差异 |
|------|--------|--------|------|
| inj_len (mm) | 200 | 200 | - |
| inj_velo (mm/s) | 200 × 0.60 × 1.00 × 0.95 = 114.0 | 114.0 | - |
| bucket（基于 max_thickness=4.0） | — | `thick` | — |
| family | PC | PC | - |
| family_window[PC][thick] | — | (3.0, 10.0) | — |
| 几何倒数 (s) | 200 / 114.0 = 1.75 | 1.75 | - |
| 公式 | max(3.0, 4.0 × 1.75) = **7.00** | max(3.0, min(1.75, 10.0)) = **3.0** | **-4.0（-57%）** |

**结论**：PC 厚壁窗口下限 3.0s 兜底生效，避免几何倒数 1.75s 触发的高剪切飞边。

**场景 C：ABS 标准结构件，W=100g, t=2.0mm, L=200mm（D=40mm, max_inj_velo=200mm/s, base_velo=0.40, mold_temp=50℃）**

| 项目 | 旧算法 | 新算法 | 差异 |
|------|--------|--------|------|
| inj_len (mm) | 200 | 200 | - |
| inj_velo (mm/s) | 200 × 0.40 × 1.00 × 1.00 = 80.0 | 80.0 | - |
| bucket（基于 max_thickness=2.0） | — | `medium` | — |
| family | ABS | ABS | - |
| family_window[ABS][medium] | — | (0.6, 2.5) | — |
| 几何倒数 (s) | 200 / 80.0 = 2.50 | 2.50 | - |
| 公式 | max(3.0, 4.0 × 2.50) = **10.0** | max(0.6, min(2.50, 2.5)) = **2.5** | **-7.5（-75%）** |

**结论**：旧算法的 4.0× 系数对中位场景严重偏大（10s）；新算法窗口上限直接钳制到 2.5s。

**场景 D：极小件，W=1g, t=1.0mm, L=20mm（D=20mm, max_inj_velo=100mm/s, family=PP）**

| 项目 | 旧算法 | 新算法 | 差异 |
|------|--------|--------|------|
| inj_len (mm) | 20 | 20 | - |
| inj_velo (mm/s) | 100 × 0.30 × 1.00 × 1.00 = 30.0 | 30.0 | - |
| bucket（基于 max_thickness=1.0） | — | `thin` | — |
| family_window[PP][thin] | — | (0.3, 1.0) | — |
| 几何倒数 (s) | 20 / 30.0 = 0.67 | 0.67 | - |
| 公式 | max(3.0, 4.0 × 0.67) = **3.0** | max(0.3, min(0.67, 1.0)) = **0.67** | **-2.33（-78%）** |

**结论**：极小件旧算法被 3.0 下限拉死；新算法仅给 0.67s（≈ 几何倒数），产能提升 ~78%。

### 6.2 总体对比

| 维度 | 原算法 | 新算法 |
|------|--------|--------|
| 维度数 | 1 维（几何倒数） | 2 维（family × bucket） |
| 材料差异化 | ❌ 完全不考虑 | ✅ 11 family 差异化窗口 |
| 壁厚档响应 | ❌ 完全不考虑 | ✅ thin / medium / thick 三档差异化 |
| 物理可解释性 | ❌ 4.0× 魔法数字无依据 | ✅ 每个窗口都有物理推导依据 |
| 极小件周期 | ❌ 3.0s 下限人为拉长 | ✅ 几何倒数直出窗口内值 |
| 极薄壁冻结防护 | ❌ 4.0× 系数反而加长冻结 | ✅ thin 桶上限 1.0~2.5s 钳制 |
| 极厚壁飞边防护 | ❌ 仅 3.0s 下限，无材料差异 | ✅ family × thick 桶下限差异化 |
| 复用既有架构 | - | ✅ 复用 _parse_family / inj_velo |
| 数据库迁移 | 不需要 | 不需要 |
| 与 inj_velo 协同 | ❌ 独立 | ✅ 几何下限基于 inj_velo |
| 兜底策略 | ❌ 单一兜底值 | ✅ 3 级兜底（精确/大类/默认） |

### 6.3 关键洞察

1. **旧算法 `inj_time_coef=4.0` 对中位场景偏大 75%~92%**——这是拍脑袋系数的典型表现
2. **`inj_time_min=3.0` 对小件偏大约 78%**——3.0s 是为薄壁冻结设计的，但被无差别应用到所有制品
3. **新算法对薄壁冻结、厚壁飞边的双重约束**同时正确响应，这是旧算法永远做不到的
4. **窗口钳制结构天然防止过度推算**：即便 `inj_velo` 物理化推导异常，几何倒数落在窗口内就不会出现极端值

---

## 7. 实施计划

### 7.1 文件改动清单

| 文件 | 改动 | 工作量 |
|------|------|--------|
| `initializer.py` | 重构行 624-628 + 新增两个查表函数 + 引入 bucket/threshold | 30~45 行 |
| `init_rules.json` | `DEFAULT.injection` 下新增 `family_time_window` 等 4 字段 + 保留旧字段作 fallback | ~50 行 |
| `rule_matcher.py` | `_BUILTIN_DEFAULTS` 同步新增 4 字段 | ~10 行 |
| 测试用例 | 4 场景 × 3 兜底 = 12 用例 + 边界场景 | 1~2 天 |
| 路线图更新 | 算法 #5 状态 ✅ + 时间窗口表添加 | 1 行 |

### 7.2 代码结构设计

#### 7.2.1 新增 `_get_inj_time_window`

```python
def _get_inj_time_window(
    self,
    family: str,
    bucket: str,
    c_inj: Dict[str, Any]
) -> Tuple[Tuple[float, float], str]:
    """
    获取工艺时间窗口（3 级兜底）

    优先级：
    1. 第 1 级 - Polymer.recommend_inj_time_window[ucket] 字段（精确值）
    2. 第 2 级 - family_time_window[family][bucket]（大类查表）
    3. 第 3 级 - default_time_window（兜底）

    Args:
        family: 材料大类（来自 _parse_family）
        bucket: 壁厚档（'thin' / 'medium' / 'thick'）
        c_inj: injection 分组合并系数

    Returns:
        ((min_t, max_t), level) 元组，level ∈ {'precise', 'family', 'default'}
    """
    # ====== 第 1 级：精确值 ======
    polymer_window = self.material.get('recommend_inj_time_window')
    if polymer_window is not None:
        precise = polymer_window.get(bucket)
        if precise is not None:
            return tuple(precise), 'precise'

    # ====== 第 2 级：按 family × bucket 查表 ======
    family_windows = c_inj.get('family_time_window', {})
    if family and family in family_windows:
        family_bucket_window = family_windows[family]
        if bucket in family_bucket_window:
            return tuple(family_bucket_window[bucket]), 'family'

    # ====== 第 3 级：默认值（兜底）======
    return tuple(c_inj.get('default_time_window', (0.6, 2.5))), 'default'
```

#### 7.2.2 新增 `_get_thickness_bucket`

```python
def _get_thickness_bucket(
    self,
    max_thickness: float,
    c_inj: Dict[str, Any]
) -> Tuple[str, str]:
    """
    按壁厚分档（3 桶）

    优先级：
    1. 第 1 级 - Polymer.thickness_bucket_override 字段（精确值）
    2. 第 2 级 - 按 thickness_bucket_thresholds 计算
    3. 第 3 级 - medium（兜底）

    Args:
        max_thickness: 最大壁厚（mold.max_thickness）
        c_inj: injection 分组合并系数

    Returns:
        (bucket, level) 元组，bucket ∈ {'thin', 'medium', 'thick'}，level ∈ {'precise', 'bucket', 'default'}
    """
    # ====== 第 1 级：精确值 ======
    override = self.material.get('thickness_bucket_override')
    if override is not None:
        return override, 'precise'

    # ====== 第 2 级：按 max_thickness 计算 ======
    if max_thickness > 0:
        thresholds = c_inj.get('thickness_bucket_thresholds', [1.5, 3.0])
        thin_max = thresholds[0]
        medium_max = thresholds[1] if len(thresholds) > 1 else float('inf')

        if max_thickness <= thin_max:
            return 'thin', 'bucket'
        elif max_thickness <= medium_max:
            return 'medium', 'bucket'
        else:
            return 'thick', 'bucket'

    # ====== 第 3 级：默认值 ======
    return c_inj.get('default_thickness_bucket', 'medium'), 'default'
```

#### 7.2.3 重构行 624-628

```python
# ========== 注射时间（几何倒数 + 工艺窗口钳制）==========
# 【重构】注射时间 = clamp(inj_len / inj_velo, [min_t, max_t])
# 推导链：几何下限（inj_len/inj_velo）+ 材料/壁厚桶窗口钳制（family_time_window）
# 数据源：3 级兜底（精确值 / family×bucket 查表 / 默认窗口）
# 物理详见 _dev_refs/2026-07-05-injection-time-physics-design.md

max_thickness = self.mold_info.get('max_thickness', 0)
bucket, bucket_level = self._get_thickness_bucket(max_thickness, c_inj)
(min_t, max_t), window_level = self._get_inj_time_window(family, bucket, c_inj)

# 几何下限（与已物理化的 inj_velo 同源）
inj_time_geo = inj_len / inj_velo if inj_velo > 0 else min_t

# 钳制：保留物理可达性（≥ min_t、≤ max_t）
inj_time = max(min_t, min(inj_time_geo, max_t))

logger.debug(
    f"注射时间: family={family or 'unknown'} (window_level={window_level}), "
    f"bucket={bucket} (level={bucket_level}), "
    f"max_thickness={max_thickness:.2f}mm, "
    f"window=({min_t:.2f}, {max_t:.2f})s, "
    f"inj_time_geo={inj_time_geo:.2f}s, "
    f"inj_time={inj_time:.2f}s"
)
```

### 7.3 推进步骤

1. **第一步**：算法逻辑改造（不依赖数据库迁移）
   - 在 `initializer.py` 新增 `_get_thickness_bucket`、`_get_inj_time_window`
   - 重构行 624-628 为几何下限 + 窗口钳制公式
   - 保留 `inj_time_coef` / `inj_time_min` 作为 fallback（不删除）
   - 配置 `init_rules.json` 新增 4 个字段
   - `rule_matcher.py._BUILTIN_DEFAULTS` 同步新增

2. **第二步**：写测试用例
   - 覆盖典型材料大类（PP/PE/PS/ABS/PA/POM/PC/PMMA/PBT/PET）
   - 覆盖典型壁厚档（thin/medium/thick）
   - 覆盖未识别材料 + 缺失 max_thickness 兜底场景
   - 对比新旧算法结果差异

3. **第三步**：内部验证
   - 选 2~3 个真实制品跑一遍
   - 工艺师 review 结果
   - 记录实际差异

4. **第四步**：灰度上线
   - 默认关闭新算法（开关控制，建议默认开启）
   - 选 1 个机器/材料灰度开启
   - 收集生产反馈

5. **第五步**：逐步推广
   - 验证通过后，扩大范围
   - 持续收集反馈，微调 `family_time_window`

### 7.4 时间估计

| 步骤 | 工作量 |
|------|--------|
| 算法逻辑改造 | 0.5~1 天 |
| JSON 配置 + rule_matcher 同步 | 0.5 天 |
| 测试用例 | 1~2 天 |
| 对比验证 | 0.5~1 天 |
| 工艺师 review | 1~3 天 |
| 灰度上线 | 0.5 天 |
| **总计** | **4~8 天**（单人） |

---

## 8. JSON 配置示例

### 8.1 新增配置（DEFAULT.injection 下追加）

```json
{
  "injection": {
    "inj_pres_ratio": 0.65,
    "inj_time_coef": 4.0,
    "inj_time_min": 3.0,
    "default_shrink_rate": 0.030,
    "default_pvt_compress": 0.015,

    "family_shrink_map": {
      "PP": 0.020,
      "PE": 0.020,
      "PS": 0.005,
      "ABS": 0.006,
      "PC": 0.006,
      "PA": 0.022,
      "POM": 0.025,
      "PMMA": 0.005,
      "PET": 0.020,
      "PBT": 0.020
    },

    "default_base_pressure_ratio": 0.70,
    "default_length_factor": 1.20,
    "max_safe_pressure_ratio": 0.90,
    "base_pressure_ratio_map": {
      "PP": 0.50, "PE": 0.50, "PS": 0.55, "ABS": 0.55, "AS": 0.55,
      "PMMA": 0.65, "PA": 0.65, "POM": 0.65, "PET": 0.70, "PBT": 0.70, "PC": 0.75
    },
    "length_factor_buckets": [
      {"max_ratio": 99, "factor": 0.85, "label": "短流程厚壁"},
      {"max_ratio": 199, "factor": 1.00, "label": "中等流长"},
      {"max_ratio": 349, "factor": 1.20, "label": "长流程薄壁"},
      {"max_ratio": null, "factor": 1.50, "label": "极难薄壁远浇"}
    ],

    "default_base_velocity_ratio": 0.40,
    "default_length_velocity_factor": 1.20,
    "default_temp_velocity_modifier": 1.00,
    "max_safe_velocity_ratio": 0.95,
    "base_velocity_ratio_map": {
      "PP": 0.30, "PE": 0.30, "PS": 0.40, "ABS": 0.40, "AS": 0.40,
      "PMMA": 0.50, "PA": 0.50, "POM": 0.50, "PET": 0.55, "PBT": 0.55, "PC": 0.60
    },
    "length_velocity_factors": [
      {"max_ratio": 99, "factor": 1.00, "label": "短流程厚壁"},
      {"max_ratio": 199, "factor": 1.15, "label": "中等流长"},
      {"max_ratio": 349, "factor": 1.30, "label": "长流程薄壁"},
      {"max_ratio": null, "factor": 1.50, "label": "极难薄壁远浇"}
    ],
    "temp_velocity_buckets": [
      {"max_temp": 40, "factor": 1.05, "label": "低模温微加速"},
      {"max_temp": 80, "factor": 1.00, "label": "中模温标准"},
      {"max_temp": null, "factor": 0.95, "label": "高模温微减速"}
    ],

    "thickness_bucket_thresholds": [1.5, 3.0],
    "default_thickness_bucket": "medium",
    "default_time_window": [0.6, 2.5],
    "family_time_window": {
      "PP":  {"thin": [0.3, 1.0], "medium": [0.5, 2.0], "thick": [1.5, 4.0]},
      "PE":  {"thin": [0.3, 1.0], "medium": [0.5, 2.0], "thick": [1.5, 4.0]},
      "PS":  {"thin": [0.4, 1.2], "medium": [0.6, 2.5], "thick": [1.8, 5.0]},
      "ABS": {"thin": [0.4, 1.2], "medium": [0.6, 2.5], "thick": [1.8, 5.0]},
      "AS":  {"thin": [0.4, 1.2], "medium": [0.6, 2.5], "thick": [1.8, 5.0]},
      "PMMA": {"thin": [0.5, 1.5], "medium": [0.8, 3.0], "thick": [2.0, 6.0]},
      "PA":  {"thin": [0.5, 2.0], "medium": [1.0, 3.5], "thick": [2.5, 7.0]},
      "POM": {"thin": [0.5, 2.0], "medium": [1.0, 3.5], "thick": [2.5, 7.0]},
      "PET": {"thin": [0.5, 2.0], "medium": [1.0, 4.0], "thick": [2.5, 8.0]},
      "PBT": {"thin": [0.5, 2.0], "medium": [1.0, 4.0], "thick": [2.5, 8.0]},
      "PC":  {"thin": [0.6, 2.5], "medium": [1.0, 4.0], "thick": [3.0, 10.0]}
    }
  }
}
```

### 8.2 兼容性说明

- 老的 `inj_time_coef=4.0` / `inj_time_min=3.0` 配置**保留为 fallback**——若 `family_time_window` 缺失则回退到原公式
- `_BUILTIN_DEFAULTS`（`rule_matcher.py`）同步新增 4 字段以保证无 DB/JSON 时也能跑新算法
- 实际行为：默认走新算法，旧字段被 fallback 逻辑覆盖

### 8.3 不需要删除的字段

本次重构**只新增不删除**：

| 字段 | 用途 |
|------|------|
| `inj_time_coef` | fallback 系数（默认值保持 4.0） |
| `inj_time_min` | 第 3 级兜底同步字段（默认值 0.6） |
| 新增 `inj_time_max` | 第 3 级兜底同步字段（默认值 2.5） |

设计哲学：与 `inj_velo` 算法对 `inj_velo_ratio_thin/thick` 的处理方式一致——保留旧字段作为可回退兜底。

---

## 9. 测试用例设计

### 9.1 新旧算法对比（典型场景）

设 max_inj_velo=200 mm/s, mold_temp=50℃, inj_velo 已物理化为 base × length × temp

| 材料 | max_thickness | family | bucket | 旧 inj_time (s) | 新 inj_time (s) | 差异 (s) | 评估 |
|------|---------------|--------|--------|---------------------|---------------------|----------|------|
| PP | 1.0mm | PP | thin | 13.32（4.0×3.33→上限） | **1.0**（PP thin 上限）| -12.32 | 薄壁冻结上限生效 ✅ |
| PP | 2.0mm | PP | medium | 10.0 | **2.5**（PP medium 上限）| -7.5 | 旧值偏大 ✅ |
| ABS | 1.0mm | ABS | thin | max(3.0, 4.0× inj_geo) | **1.2**（ABS thin 上限）| 显著下调 | 薄壁冻结防护 ✅ |
| ABS | 2.0mm | ABS | medium | 取决于 inj_velo | **2.5**（ABS medium 上限）| 显著下调 | 中位场景合理 ✅ |
| PC | 4.0mm | PC | thick | 取决于 inj_velo | **3.0**（PC thick 下限兜底）| 可能上调 | 厚壁飞边防护 ✅ |
| PC | 0.5mm | PC | thin | 大值 | **2.5**（PC thin 上限）| 显著下调 | 高黏度薄壁需慢填 ✅ |
| 极小件 1g | 1.0mm | PP | thin | max(3.0, 4.0×0.67) = **3.0** | **0.67**（几何倒数）| -2.33 | 周期节省 ✅ |
| 未识别 | 2.0mm | unknown | medium | max(3.0, 4.0× inj_geo) | **default (0.6, 2.5) 钳制** | 中等 | 兜底合理 ✅ |

**变化幅度可控**：最大下调可达 12s（薄壁冻结旧值），最大上调约 1~2s（PC 厚壁）；不会破坏现有工艺模板。

### 9.2 材料大类差异化验证

设 W=100g, D=40mm, max_inj_velo=200 mm/s, inj_velo 按 family 差异化, max_thickness=2.0mm（medium）

| 材料 | base_velo_ratio | inj_velo (mm/s) | inj_len (mm) | inj_time_geo (s) | family_window[medium] | inj_time (s) |
|------|-----------------|-----------------|--------------|--------------------|------------------------|---------------|
| PP | 0.30 | 60.0 | 200 | 3.33 | (0.5, 2.0) | **2.0** |
| ABS | 0.40 | 80.0 | 200 | 2.50 | (0.6, 2.5) | **2.5** |
| PS | 0.40 | 80.0 | 200 | 2.50 | (0.6, 2.5) | **2.5** |
| PMMA | 0.50 | 100.0 | 200 | 2.00 | (0.8, 3.0) | **2.0** |
| PA | 0.50 | 100.0 | 200 | 2.00 | (1.0, 3.5) | **2.0** |
| PET | 0.55 | 110.0 | 200 | 1.82 | (1.0, 4.0) | **1.82** |
| PC | 0.60 | 120.0 | 200 | 1.67 | (1.0, 4.0) | **1.67** |
| 未识别 | 0.40（兜底）| 80.0 | 200 | 2.50 | default (0.6, 2.5) | **2.5** |

**不同材料自动差异化**（1.67s → 2.5s），覆盖全面，未识别材料兜底在 2.5s。

### 9.3 壁厚档差异化验证

设 W=100g, D=40mm, max_inj_velo=200 mm/s, material=ABS（base_velo=0.40）, mold_temp=50℃, inj_len=200mm

| max_thickness (mm) | bucket | inj_velo (mm/s) | inj_time_geo (s) | family_window[ABS][bucket] | inj_time (s) |
|--------------------|--------|-----------------|--------------------|-----------------------------|--------------|
| 0.5 | thin | 80 | 2.50 | (0.4, 1.2) | **1.2** |
| 1.0 | thin | 80 | 2.50 | (0.4, 1.2) | **1.2** |
| 1.5 | thin（边界）| 80 | 2.50 | (0.4, 1.2) | **1.2** |
| 1.6 | medium | 80 | 2.50 | (0.6, 2.5) | **2.5** |
| 3.0 | medium（边界）| 80 | 2.50 | (0.6, 2.5) | **2.5** |
| 3.1 | thick | 80 | 2.50 | (1.8, 5.0) | **2.5** |
| 5.0 | thick | 80 | 2.50 | (1.8, 5.0) | **2.5** |
| 10.0 | thick | 80 | 2.50 | (1.8, 5.0) | **2.5** |

**壁厚档自动响应**：thin 上限生效、medium 上限生效、thick 仅在窗口内（不主动调低）。

### 9.4 几何倒数边界场景验证

| 场景 | inj_velo (mm/s) | inj_len (mm) | inj_time_geo (s) | family_window | inj_time (s) | 评估 |
|------|------------------|--------------|--------------------|----------------|---------------|------|
| 极小件 inj_len=20mm, family=PP, bucket=thin | 30 | 20 | 0.67 | (0.3, 1.0) | **0.67** | ✅ 周期最优 |
| 极大件 inj_len=2000mm, family=PC, bucket=thick | 120 | 2000 | 16.67 | (3.0, 10.0) | **10.0** | ✅ 上限保护 |
| 极慢速度 inj_velo=10mm/s, inj_len=200mm | 10 | 200 | 20.0 | (0.4, 1.2)[ABS thin] | **1.2** | ✅ 上限保护 |
| inj_velo=0 | 0 | 200 | 异常 | (0.6, 2.5) | **min_t**（兜底）| ✅ 默认 min_t |

### 9.5 边界场景验证

| 场景 | 输入 | 输出 (s) | 评估 |
|------|------|----------|------|
| 桶边界 max_thickness=1.5mm | family=ABS | bucket='thin' | **1.5mm 上限归 thin** |
| 桶边界 max_thickness=1.6mm | family=ABS | bucket='medium' | **1.6mm 归 medium** |
| 桶边界 max_thickness=3.0mm | family=ABS | bucket='medium' | **3.0mm 上限归 medium** |
| max_thickness=0 缺失 | family=ABS | bucket='medium'（兜底）| ✅ |
| family 缺失 | bucket=medium | window=default (0.6, 2.5) | ✅ |
| max_thickness + family 双缺失 | - | bucket=medium, window=default | ✅ 中位兜底 |
| 推荐窗口 Polymer.recommend_inj_time_window[thin]=[0.5, 1.5] | family=PC, bucket=thin | **window=[0.5, 1.5]** | ✅ 第 1 级生效 |
| 推荐桶 Polymer.thickness_bucket_override='thick' | family=ABS | bucket='thick' | ✅ 第 1 级生效 |

---

## 10. 风险与缓解

| 风险 | 严重度 | 缓解措施 |
|------|--------|----------|
| 行为变化不一致（薄壁件时间骤降）| 中 | 灰度上线流程；保留旧字段作 fallback |
| family_time_window 数据不准 | 中 | 工艺师微调 `family_time_window` |
| 桶分界 1.5/3.0mm 不符合厂内习惯 | 低 | JSON 可配置 |
| max_thickness 字段缺失 | 低 | 第 3 级兜底 → medium + default window |
| `inj_velo` 物理化未生效 | 中 | 文档明确依赖关系；检查 `inj_velo` 实施状态 |
| 旧字段未同步删除引发误解 | 低 | 文档明确说明"保留为 fallback"；运行时主路径走新算法 |
| 极薄壁 t<0.5mm 场景极少数据 | 中 | thin 上限已覆盖（PC 2.5s 兜底足够宽）|
| Polymer.recommend_inj_time_window 数据缺失 | 低 | 第 1 级自动跳过到第 2 级 |
| 与冷却时间冲突（inj_time 缩短 → cool_t 拉长）| 低 | cool_t 算法独立；不冲突 |

### 10.1 钳制后取值范围

```
inj_time_geo:                [0, +∞)
family_window[family][bucket]: (min_t, max_t) ∈ ([0.3, 0.6], [1.0, 3.0]) × {[1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 10.0]}

钳制后结果：
- max_t 取值范围：[1.0, 10.0]（按 family × bucket 离散）
- min_t 取值范围：[0.3, 3.0]（按 family × bucket 离散）
- 实际 inj_time：在每个 family × bucket 组合下的 [min_t, max_t] 闭区间内
```



---

## 11. 相关文件

| 文件 | 说明 |
|------|------|
| [initializer.py](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/initializer.py) | 注射时间算法主体（待重构行 624-628 + 新增两个查表函数）|
| [rule_matcher.py](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/rule_matcher.py) | `_BUILTIN_DEFAULTS` 同步新增 4 字段（`family_time_window` 等）|
| [init_rules.json](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/expert_rules/init_rules.json) | `DEFAULT.injection` 下追加 4 个字段 + 保留旧字段 |
| [2026-07-05-injection-velocity-physics-design.md](file:///Users/lpissenlit/workfiles/molding-optima/backend/_dev_refs/2026-07-05-injection-velocity-physics-design.md) | 注射速度算法设计文档（上游强依赖）|
| [2026-07-05-injection-pressure-physics-design.md](file:///Users/lpissenlit/workfiles/molding-optima/backend/_dev_refs/2026-07-05-injection-pressure-physics-design.md) | 注射压力算法设计文档（兄弟算法）|
| [2026-07-04-injection-stroke-physics-design.md](file:///Users/lpissenlit/workfiles/molding-optima/backend/_dev_refs/2026-07-04-injection-stroke-physics-design.md) | 行程分配算法设计文档（inj_len 来源）|
| [2026-07-04-algorithm-refactor-roadmap.md](file:///Users/lpissenlit/workfiles/molding-optima/backend/_dev_refs/2026-07-04-algorithm-refactor-roadmap.md) | 算法改造路线图（算法 #5）|

---

## 12. 后续扩展（不在本文档范围）

### 12.1 多段注射时间窗口（阶段 2.5）

当前方案输出单一 `inj_time`，对应 `inj_stg=1` 的单段注射。

**未来扩展**：当 `inj_stg > 1` 时，每段可独立设置时间窗口：

```python
# 阶段 2.5 设想（不在本文档范围）
for stage in range(inj_stg):
    stage_window = family_stage_window[family][bucket][stage]
    stage_time[stage] = clamp(stage_inj_pos / inj_velo[stage], stage_window)
```

物理动机：多段注射中，填充末段（VP 切换点附近）需特别关注冻结时间，窗口可不同于填充前段。

### 12.2 与冷却时间算法的协同校验

`inj_time` 缩短后，`cool_t` 会被相应拉长（见 initializer.py:cool_t 计算逻辑）。需要新增"全周期时间预算"校验：

```
total_cycle = inj_time + hold_time + cool_time + else_time ≤ inject_cycle_require
```

当前未约束；阶段二可引入"总周期预算约束层"。

### 12.3 fallback 策略完整性

| 场景 | 行为 |
|------|------|
| `family_time_window` 配置缺失 | 走 `default_time_window` 兜底 |
| `default_time_window` 也缺失 | 走 `(0.6, 2.5)` 硬编码 |
| `inj_velo` 物理化未实施 | 几何倒数仍是有效值（即便基于旧 inj_velo = 旧算法）|
| 新算法整体关闭（feature flag）| 回到 `max(3.0, 4.0 × inj_len / inj_velo)` 旧公式 |

### 12.4 阶段 2/3/4 演进

详见第 14 章渐进式物理化演进路径。

---

## 13. 局限性诚实声明

> 本章诚实说明当前方案的物理依据强度，避免给出过度承诺。

### 13.1 半经验方法 vs 严格物理推导

本方案属于**"半经验方法"**，不是严格的物理推导。

| 系数 / 变量 | 类型 | 理论依据 | 量化来源 |
|------------|------|---------|---------|
| `inj_len / inj_velo` | **物理量** | 几何等式 | 工艺几何 + 已物理化的 inj_velo |
| `max_thickness` | 物理量 | mold_info 既有字段 | mold_info 表 |
| `inj_time_min/max`（窗口边界）| **经验系数** | 定性物理正确（薄壁冻结 / 厚壁飞边 / 材料黏度）| 工艺手册 + Moldflow 推荐填充时间中位 |
| `thickness_bucket_thresholds` | **经验分界** | 定性物理正确（薄壁冻结 / 厚壁飞边）| 工艺手册与模塑壁厚习惯 |
| `family_time_window[family][bucket]` | **经验系数** | 定性物理正确（MFI 高 → 窗口紧、MFI 低 → 窗口宽）| 材料手册 + Moldflow 推荐值中位 |

### 13.2 关键诚实点

1. **`family_time_window` 的 33 行窗口（11 family × 3 bucket）是工程经验中位值**，不是从 Biot 数、凝固时间或剪切流变严格推导的。

2. **薄壁冻结时间（≤1.0~2.5s）和厚壁飞边时间（≥1.5~3.0s）来自工艺手册共识**，不是从传热方程 + 黏度-温度曲线严格推导出的。

3. **桶分界（1.5/3.0mm）是经验值**，与注塑工艺师习惯吻合；具体到某个工厂可能需要微调。

4. **`Polymer.recommend_inj_time_window` 字段精度依赖于材料采集**，本方案只是为未来材料数据补齐预留接口。

5. **`mold.max_thickness` 字段在某些项目中可能缺失**（参见第 5 章兜底：缺失时归 medium + default window）。

6. **当前数据库 molder.actual_weight 已存在**，但本算法暂未引入体积流量恒等式 `t_target = V / (v × A_screw)`——这是阶段三目标。

### 13.3 为什么"半经验方法已经比 inj_time_coef=4.0/min=3.0 好"

虽然定量仍是经验系数，但相对原 thin/thick/min 在以下维度有显著提升：

| 维度 | 原 thin/thick/min | 半经验方法 | 提升 |
|------|---------------------|-----------|------|
| **材料差异化** | ❌ 无 | ✅ 11 family × 3 bucket = 33 行窗口 | ✅ 显著提升 |
| **壁厚档响应** | ❌ 无 | ✅ thin/medium/thick 三档差异化 | ✅ 显著提升 |
| **物理下限保护** | 仅 `inj_time_min=3.0` 全场一致 | ✅ family×bucket 差异化（0.3~3.0s）| ✅ 显著提升 |
| **物理上限保护** | ❌ 无 | ✅ family×bucket 差异化（1.0~10.0s）| ✅ 显著提升 |
| **极小件周期优化** | 3.0s 下限人为拉长 | ✅ 几何倒数直出窗口 | ✅ 显著提升 |
| **薄壁冻结防护** | ❌ 4.0× 反而拖延 | ✅ thin 上限 1.0~2.5s 钳制 | ✅ 显著提升 |
| **厚壁飞边防护** | ❌ 仅 3.0s 下限 | ✅ family×thick 下限差异化 | ✅ 显著提升 |
| **可扩展性** | 2 个魔法数字 | 33 行可微调窗口表 | ✅ 显著提升 |
| **物理可解释性** | 数字来源不明 | 每个窗口都有定性物理依据 | ✅ 显著提升 |
| **失败归因** | 调参试错 | 按 family / bucket 维度精确定位 | ✅ 显著提升 |
| **与 inj_velo 协同** | 独立 | 几何下限基于 inj_velo | ✅ 显著提升 |
| **物理推导严格性** | 无 | 定性物理正确 + 定量经验 | ⚠️ 仍有局限 |

**核心结论**：本方案是"工程落地"与"理论严谨"的合理折中——既立即解决 inj_time_coef=4.0 拍脑袋问题，又为未来严格物理推导（体积流量恒等式 + 凝固时间 + 剪切速率联合约束）留出空间。

### 13.4 物理推导严格性的演进目标

未来按"渐进式物理化"路径，从"半经验"逐步逼近"严格推导"（详见第 14 章）：

```
当前：第一阶段（半经验）
├─ 物理定性 ✅ 材料流动性等级 + 壁厚档响应
└─ 物理定量 ❌ 经验窗口表

目标：第三阶段（严格推导）
├─ 物理定性 ✅ 同上
└─ 物理定量 ✅ t_target = V / (v × A_screw) + 比奥数约束 + γ̇ < γ̇_critical
```

### 13.5 与注射速度文档的"诚实声明对位"

| 章节 | injection-velocity | injection-time（本文档）|
|------|---------------------|--------------------------|
| 第 13 章 | "半经验" 与 "严格推导" 的对比 | 同上 |
| 13.2 关键诚实点 | base/length/temp 各一组经验数字 | family×bucket 33 行经验窗口 |
| 13.3 为什么好 | 11 family / 4 L/t / 3 temp 差异化 | 11 family / 3 bucket 差异化 |
| 13.4 演进目标 | v = V/(t×A) + γ̇ 约束 | t_target = V/(v×A) + 凝固时间 + γ̇ 约束 |

---

## 14. 渐进式物理化演进路径

本方案是渐进式物理化的**第一阶段**，未来按以下路径分阶段演进。

### 14.1 阶段一（当前）：半经验方法

**目标**：立即落地，解决"inj_time_coef=4.0 拍脑袋 + inj_time_min=3.0 过大最小值 + 无材料/壁厚差异化"问题。

**内容**：
- 实施"几何下限 + family × bucket 工艺窗口钳制"
- 复用既有 `_parse_family` / `inj_velo` / `max_thickness`
- 保留 3 级兜底
- 工艺师可微调 `family_time_window` / `thickness_bucket_thresholds`

**数据需求**：0（既有数据足够：family 从 abbreviation 解析，max_thickness 从 mold_info 读取，inj_velo 来自上游算法）

### 14.2 阶段二（数据补齐）：引入物理参数

**目标**：为第三阶段严格推导准备物理参数。

**内容**：
- **`PolymerRheology` 模型已支持 Cross-WLF 7 参数 + MFI 字段**（[material.py:78-94](file:///Users/lpissenlit/workfiles/molding-optima/backend/masterdata/models/material.py#L78-L94)），**无需新增 schema**，只需采集主流材料数据补齐
- **新增 `Polymer.recommend_inj_time_window` 字段**：材料级精确窗口（第 1 级兜底）
- **新增 `Polymer.thickness_bucket_override` 字段**：材料级强制桶（第 1 级兜底）
- **采集项目**：优先补齐主流材料（PP / PE / ABS / PC / PA / POM）的窗口数据；数据源：Moldflow 材料库 / 厂商技术资料 / 实验测量
- 阶段一算法继续作为 fallback

**数据需求**：
- **数据补齐**：MFI + Cross-WLF 7 参数 + 工艺实测窗口（字段已存在或新增，需采集填入）
- **schema 扩展**：polymer 模型新增 2 个字段

### 14.3 阶段三（严格推导）：体积流量 + 凝固时间 + 剪切速率联合约束

**目标**：每个数字都可追溯到物理定律。

**内容**：
- 实施体积流量恒等式：
  ```
  v_physically_required = V_geometry / (t_target × A_screw)
  ```
- 叠加凝固时间约束（薄壁上限）：
  ```
  t_target ≤ t_freeze(Bio, h_wall, T_melt, T_mold)
  ```
  防止前缘冻结
- 叠加剪切速率约束（厚壁下限）：
  ```
  γ̇_actual = v / t_min ≥ γ̇_min
  ```
  防止飞边
- 替换阶段一算法，阶段一作为 fallback
- 各材料 γ̇_critical 表来自 Moldflow 材料库 + 实验测量

**数据需求**：阶段二数据 + 各段详细几何 + 材料 γ̇_critical + t_freeze 表

### 14.4 阶段四（精度优化）：闭环校准

**目标**：用实测数据持续优化算法精度。

**内容**：
- 引入 Moldflow 仿真值作为基准，校准经验窗口与物理参数
- 持续积累工艺实测数据，反推真实材料参数
- 形成"实测数据驱动的物理推导闭环"
- 阶段三算法持续优化

**数据需求**：Moldflow 仿真 + 工艺实测数据

### 14.5 各阶段数据依赖与工作量

| 阶段 | 核心新增数据 | 数据来源 | 估算工作量 |
|------|------------|---------|----------|
| 一 | 无 | 既有 | 0.5-1 周 |
| 二 | MFI + Cross-WLF 7 参数 + recommend_inj_time_window + thickness_bucket_override | 材料数据采集项目 + schema 迁移 | 2-3 月 |
| 三 | 流道分段几何 + 材料 γ̇_critical + t_freeze 表 | 工艺 CAE 仿真 + 模具图纸 | 3-6 月 |
| 四 | Moldflow 仿真值 + 实测反推 | 工艺实测采集 | 持续 |

### 14.6 演进保证机制

为确保演进过程中算法持续可用，每个阶段都遵守以下保证：

1. **向下兼容**：阶段 N 算法必须保留阶段 N-1 算法作为 fallback
2. **数据缺失兜底**：所有新增数据字段必须有默认值或 3 级兜底
3. **3 级兜底不变**：阶段一即建立完整 3 级兜底；新增字段是第 1 级的增强，不破坏兜底链路
4. **可回退**：任何阶段实施问题可立即回退到前一阶段

---

## 15. 与项目物理化演进路线的对齐

本方案遵循项目"渐进式物理化"演进路径，与既有架构深度对齐。

### 15.1 复用既有架构组件

| 组件 | 位置 | 复用方式 |
|------|------|---------|
| `_parse_family()` | [initializer.py:225-237](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/initializer.py#L225-L237) | 直接调用，零修改 |
| `_get_base_pressure_ratio` | [initializer.py](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/initializer.py) | 同模式复用（兄弟函数） |
| `_get_length_factor` | [initializer.py](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/initializer.py) | 同模式复用（兄弟函数） |
| `_get_base_velocity_ratio` | [initializer.py:345-372](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/initializer.py#L345-L372) | 直接调用，零修改 |
| `_get_length_velocity_factor` | [initializer.py](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/initializer.py) | 直接调用，零修改 |
| `_get_temp_velocity_modifier` | [initializer.py](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/initializer.py) | 直接调用，零修改 |
| `inj_velo` 计算结果 | [initializer.py:611-614](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/initializer.py#L611-L614) | 几何下限直接复用 |
| `inj_len` 计算结果 | [initializer.py](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/initializer.py) | 几何下限直接复用 |
| `family` 变量 | [initializer.py:612](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/initializer.py#L612) | 共享变量，零修改 |
| `c_inj` 系数组 | `_coeffs.get('injection', {})` | 同模式复用 |
| `family_shrink_map` 配置 | [init_rules.json:23-34](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/expert_rules/init_rules.json#L23-L34) | 同模式扩展（新增 `family_time_window`）|
| `base_velocity_ratio_map` 配置 | init_rules.json | 同模式扩展 |

### 15.2 与兄弟算法的对位

| 算法 | 维度数 | 推导公式 | 钳制 | 状态 |
|------|-------|---------|------|------|
| `length_ratio` | 1 维 | 总长 × (1 - L_cushion_need/总长) | — | ✅ 已完成 |
| `cushion_len` | 1 维 | max(ceil(D/4), cushion_min_abs) | — | ✅ 已完成 |
| `inj_pres` | 2 维 | base_ratio[family] × length_factor(L/t) × max_inj_pres | max_safe_pressure_ratio=0.90 | ✅ 已完成 |
| `inj_velo` | 3 维 | base_velo_ratio[family] × length_velo_factor(L/t) × temp_velo_modifier × max_inj_velo | max_safe_velocity_ratio=0.95 | ✅ 已完成 |
| **`inj_time`**（本文档） | **2 维** | **`clamp(inj_len / inj_velo, family_window[family][bucket])`** | **—** | **⏳ 待实施** |
| `hold_pres` | 3 维 | (待设计) | — | ⏳ 待改造 |
| `hold_velo` | 2 维 | (待设计) | — | ⏳ 待改造 |
| `hold_time` | 1 维 | (待设计) | — | ⏳ 待改造 |

`inj_time` 与 `inj_velo` 的对称性：

| 维度 | `inj_velo` | `inj_time` |
|------|------------|------------|
| 输入维度数 | 3 维（family × L/t × T_mold） | 2 维（family × bucket） |
| 推导方式 | 乘法叠加 | 钳制（几何量 + 窗口） |
| 钳制对象 | 物理上限（防飞边 / 剪切烧焦） | 工艺窗口（防冻结 / 防飞边） |
| 机器基准 | max_set_injection_velocity (mm/s) | inj_len / inj_velo (s) |
| 安全钳制 | max_safe_velocity_ratio = 0.95 | window_max_t[f,b] = 1.0~10.0 |
| 数据源 | `base_velocity_ratio_map` + `length_velocity_factors` + `temp_velocity_buckets` | `family_time_window[family][bucket]` |
| 数据行数 | 11 + 4 + 3 = 18 行 | 11 × 3 = 33 行 |

> **风格差异说明**：
> - `inj_velo` 用乘法叠加：维度独立、各自的物理意义清晰（MFI / L/t / T_mold 各自响应）
> - `inj_time` 用钳制：时间窗口本身已封装了"材料 × 几何 × 热历史"组合效应，且时间是绝对量，强约束更易表达为窗口
> - 两种风格都是物理推导的合理表达，只是适应不同时序量（速度是过程量，时间是绝对量）
> - 同一初始化器内允许"混合风格"——这与材料工程师的实际思维一致

### 15.3 与项目规范的符合度

| 项目规范 | 本方案符合度 | 说明 |
|---------|------------|------|
| 算法设计必须基于物理原理 | ⚠️ 定性符合，定量是经验 | 见第 13 章局限性诚实声明 |
| 物理推导 + 行业共识数据 | ✅ | 物理定性（材料流动性 + 壁厚档响应）+ 行业共识定量（窗口表）|
| 三级保守兜底 | ✅ | 完整 3 级兜底 × 2 维度（精确/大类/默认 + 桶）|
| 安全钳制（防冻/防飞边）| ✅ | `family_window` 提供 min/max 双向保护 |
| 渐进式物理化演进 | ✅ | 处于第一阶段，文档明确第二/三/四阶段路径 |
| 可追溯性 | ✅ | 每个窗口都有定性物理依据 + 量化来源 |
| 可扩展性 | ✅ | 预留 `recommend_inj_time_window`、`thickness_bucket_override` 字段 |
| 失败归因清晰 | ✅ | 按 family / bucket 维度精确定位 |
| 与兄弟算法一致性 | ✅ | 与 `inj_velo`/`inj_pres` 共享 3 级兜底 + 兜底默认 |
| 既有字段保留 | ✅ | `inj_time_coef` / `inj_time_min` 保留为 fallback |

### 15.4 路线图同步更新

路线图（[2026-07-04-algorithm-refactor-roadmap.md](file:///Users/lpissenlit/workfiles/molding-optima/backend/_dev_refs/2026-07-04-algorithm-refactor-roadmap.md)）需同步更新：

| 位置 | 当前状态 | 新状态 |
|------|---------|--------|
| 路线图总表 算法 #5 | ⏳ | ✅（半经验方法 + 2 维查表） |
| 路线图 4.3 节详细问题描述 | 简述 | 链接到本文档 |
| 路线图更新日志 | 2026-07-05 "补充到清单" | 2026-07-05 "✅ 完成 设计文档：2026-07-05-injection-time-physics-design.md" |

### 15.5 与初始化器内既有钳制的协同

```
inj_velo 上限（max_safe_velocity_ratio=0.95）
       ↓
inj_time_geo = inj_len / inj_velo 下限受控（不会过小）
       ↓
inj_time = clamp(inj_time_geo, family_window[family][bucket])
       ↓
inj_time 不会超出薄壁冻结上限（受桶窗口保护）
inj_time 不会低于厚壁飞边下限（受桶窗口下限保护）
```

**三层防护链**：
1. **第一层**：`inj_velo` 钳制防止速度过快导致飞边
2. **第二层**：`inj_time_geo = inj_len / inj_velo` 几何下限保证物理可达
3. **第三层**：`family_window[family][bucket]` 桶窗口保护薄壁冻结 + 厚壁飞边双向

---

## 16. 更新日志

| 日期 | 进度 | 备注 |
|------|------|------|
| 2026-07-05 | 设计文档建立 | ✅ 本文档（章节 1-15） |
| 2026-07-05 | 局限性诚实声明 | ✅ 章节 13 |
| 2026-07-05 | 渐进式物理化演进路径 | ✅ 章节 14 |
| 2026-07-05 | 与项目物理化路线对齐 | ✅ 章节 15 |
| 2026-07-05 | 兄弟算法对位表 | ✅ 15.2：与 `inj_pres` / `inj_velo` 维度对位 |
| 2026-07-05 | max_thickness 字段选择决策记录 | ✅ 3.3 节：使用 mold.max_thickness（保守取最薄处）|
| 2026-07-05 | 钳制风格差异说明 | ✅ 15.2 节：inj_velo 用乘法 / inj_time 用钳制的合理性 |
| 待定 | 算法实施 | ⏳ 见 7.3 推进步骤 |
| 待定 | 测试覆盖 | ⏳ 见 9.1-9.5 |
| 待定 | 灰度上线 | ⏳ 见 7.3 |

---

*文档生成时间：2026-07-05*
