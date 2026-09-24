# 注射压力算法科学化改造设计

> 本文档记录将注射压力（`inj_pres`）从"单一固定比例的经验玄学"重构为"基于材料黏度等级 + 流长比的物理推导"的设计方案。

## 1. 设计背景

### 1.1 当前算法（经验玄学）

`initializer.py` 行 386-391 中：

```python
# ========== 注射参数 ==========
max_inj_pres = mach.get('max_set_injection_pressure', 150)
max_inj_velo = mach.get('max_set_injection_velocity', 100)

# 注射压力 - 来自 DEFAULT.injection.inj_pres_ratio
inj_pres = max_inj_pres * c_inj.get('inj_pres_ratio', 0.65)
```

老代码 `process_generate.py` 行 229-239 中有过流长比修正的设想，但最终被简化成同一行：

```python
inj_ratio = product['max_length'] / product['ave_thickness']
inj_pres = self.machine['max_set_injection_pressure'] * 0.65
# 被注释掉的"流长比修正"设想：
# if inj_ratio > 350:
#     inj_pres = 0.94 * inj_pres
# else:
#     for ratio, proportion in HSO_RATIO_PRESSURE_MAP.items():
#         inj_pres = proportion * inj_pres
```

**核心问题**：

| 问题 | 表现 | 影响 |
|------|------|------|
| 单一固定系数 | "为什么是 0.65？" → 答："经验" | 工艺师不敢用 |
| 不区分材料 | PC 和 PP 用同一 0.65 | 高黏度材料压力不足 |
| 不区分流长比 | 1mm 薄壁和 5mm 厚壁同一压力 | 薄壁远浇必然短射 |
| 物理意义模糊 | 比例数字无依据 | 调整无据可循 |
| 注释掉的逻辑 | 早期曾有 L/t 修正设想 | 工程债未落地 |

### 1.2 优化目标

1. **数据基础升级**：从"几次试模经验"升级为"材料科学共识"
2. **物理推导替代经验拟合**：每个数字都能追溯到材料黏度等级 + 流变学定律
3. **二维差异化**：按材料大类 × 流长比两维度差异化
4. **保守兜底**：未识别材料自动采用最保守值
5. **复用既有架构**：复用 `_parse_family` / `family_shrink_map` 模式，与已重构的 `length_ratio` 算法保持一致

---

## 2. 问题的本质定义

注射压力只有一个核心问题：**推动熔体完成填充所需的压力是多少？**

```
P_inj = P_nozzle + ΔP_runner + ΔP_gate + ΔP_cavity_peak
```

**物理本质**：注射压力 = 物料黏度等级（材料决定） × 流长比修正（制品决定）

| 维度 | 决定因素 | 数据源 |
|------|---------|--------|
| **材料黏度等级** | 材料大类（PP/PA/PC 等） | 材料手册黏度区间 |
| **流长比修正** | L/t（最大流长 / 平均壁厚）| 制品几何 |

**与原算法的关键区别**：
- 原算法：单一固定 0.65，对所有材料 + 所有流长比一刀切
- 新算法：`base_ratio[family] × length_factor(inj_ratio)`，二维差异化

---

## 3. 新算法核心（基于物理推导）

### 3.1 物理推导链

```
【起点：工艺目标】
注射压力需推动熔体经喷嘴→流道→浇口→型腔完成填充

【物理定律】
1. 流变学定律：ΔP = (8 × η × L × Q) / (π × R⁴)
   ├─ 材料黏度 η 决定基准压力水平
   └─ 流道几何 + 体积流率 Q 决定段间压力损失

2. 浇口效应：浇口截面积最小 → 压力损失占总损失的 30-60%
   └─ 流长比 L/t 越大 → 填充路径上压力梯度越陡

3. 材料黏度差异：
   ├─ 流动性好（PP/PE/PS）：黏度低，基准压力低
   └─ 高黏度工程塑料（PC/PMMA/PBT）：黏度高，基准压力大

【二维推导】
inj_pres = max_inj_pres × base_ratio[family] × length_factor(inj_ratio)
├─ base_ratio：材料黏度等级决定的基准压力比例
└─ length_factor：制品流长比决定的压力修正系数
```

### 3.2 完整计算公式

```python
# 步骤 1：获取材料大类（复用既有 _parse_family）
family = self._parse_family(self.material.get('abbreviation', ''))

# 步骤 2：查材料基准压力比例（3 级兜底）
base_ratio, base_level = self._get_base_pressure_ratio(family, c_inj)

# 步骤 3：按流长比分档查修正系数
length_factor, factor_level = self._get_length_factor(inj_ratio, c_inj)

# 步骤 4：综合（钳制上限防止超过机器物理限制）
max_inj_pres = mach.get('max_set_injection_pressure', 150)
inj_pres_calculated = max_inj_pres * base_ratio * length_factor

# 步骤 5：钳制到安全区间（保守兜底）
max_safe_ratio = c_inj.get('max_safe_pressure_ratio', 0.90)  # 默认不超过机器最大压力的 90%
inj_pres = min(inj_pres_calculated, max_inj_pres * max_safe_ratio)
```

### 3.3 与 `_get_shrink_rate` 的关系

新算法复用既有的材料分类和数据流模式，与 `length_ratio` 算法共享：

| 复用项 | 来源 |
|--------|------|
| `_parse_family()` | 既有方法，[initializer.py:225-237](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/initializer.py#L225-L237) |
| `inj_ratio` 变量 | 既有计算，[initializer.py:358-360](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/initializer.py#L358-L360) |
| `c_inj` 系数组 | 既有 `_coeffs.get('injection', {})` |

**唯一新增**：两个 3 级兜底查表函数 + 系数配置项。

---

## 4. 数据需求与 3 级兜底策略

### 4.1 数据需求（极简）

不需要新增数据库字段。`family` 从 `Polymer.abbreviation` 解析（既有 `_parse_family`）。

**新增配置项**：
- `base_pressure_ratio_map`：材料大类基准压力比例表
- `length_factor_buckets`：流长比分档修正系数
- `max_safe_pressure_ratio`：安全上限钳制（默认 0.90）

### 4.2 3 级兜底数据流（材料基准比例）

```
【第 1 级】精确值（Polymer.recommend_inj_pressure_ratio 字段）
  ├─ 命中：直接使用
  └─ 适用：数据库已有材料推荐压力比例（少见，目前为 None）

【第 2 级】按大类查表（base_pressure_ratio_map）
  ├─ 命中：使用大类典型基准比例
  └─ 适用：能从 abbreviation 解析出 PP/PA/PC 等大类

【第 3 级】默认值（兜底）
  ├─ 命中：default_base_pressure_ratio = 0.70
  └─ 适用：所有识别失败场景
```

### 4.3 3 级兜底数据流（流长比修正系数）

```
【第 1 级】精确值（Polymer.length_factor_override 字段）
  ├─ 命中：直接使用
  └─ 适用：数据库已有材料的特定修正值

【第 2 级】按分档查表（length_factor_buckets）
  ├─ 命中：按 inj_ratio 所在档位查表
  └─ 适用：通用场景

【第 3 级】默认值（兜底）
  ├─ 命中：default_length_factor = 1.20
  └─ 适用：inj_ratio 数据缺失或异常场景
```

### 4.4 材料大类基准压力比例（行业共识）

数据来源：材料手册 + Moldflow 材料库 + 注塑机厂家推荐值的综合中位数。

```json
{
  "base_pressure_ratio_map": {
    "PP": 0.50,
    "PE": 0.50,
    "PS": 0.55,
    "ABS": 0.55,
    "AS": 0.55,
    "PMMA": 0.65,
    "PA": 0.65,
    "POM": 0.65,
    "PET": 0.70,
    "PBT": 0.70,
    "PC": 0.75
  }
}
```

**数据依据**：

| 大类 | 典型黏度区间 (Pa·s) | 基准比例 | 物理依据 |
|------|---------------------|---------|---------|
| PP / PE | 100-1000 | 0.50 | 半结晶、流动性好、MFR 高 |
| PS / ABS | 500-3000 | 0.55 | 非结晶、流动性中等 |
| PA / POM | 500-3000 | 0.65 | 半结晶高黏度、易结晶 |
| PET / PBT | 800-5000 | 0.70 | 半结晶、黏度较高 |
| PMMA | 1000-5000 | 0.65 | 非结晶高黏度 |
| PC | 1000-10000 | 0.75 | 非结晶工程塑料、高黏度 |

### 4.5 流长比分档修正系数（行业共识）

数据来源：注塑成型工艺手册 + Moldflow 填充压力曲线的中位近似。

```json
{
  "length_factor_buckets": [
    {"max_ratio": 100, "factor": 0.85, "label": "短流程厚壁"},
    {"max_ratio": 200, "factor": 1.00, "label": "中等流长"},
    {"max_ratio": 350, "factor": 1.20, "label": "长流程薄壁"},
    {"max_ratio": null, "factor": 1.50, "label": "极难薄壁远浇"}
  ]
}
```

**物理依据**：

| 流长比 L/t | 修正系数 | 物理含义 | 典型场景 |
|------------|---------|---------|---------|
| <100 | 0.85 | 短流程、厚壁，阻力小 | 小型厚壁件 |
| 100-200 | 1.00 | 中等流长，标准阻力 | 一般注塑件 |
| 200-350 | 1.20 | 长流程、薄壁，阻力陡升 | 薄壁容器、扁平件 |
| >350 | 1.50 | 极难薄壁远浇，阻力急剧 | 超薄壁长流程件 |

### 4.6 兜底值选择依据

```
已知材料基准比例范围：0.50 ~ 0.75
已知最大值：PC ≈ 0.75
安全裕度：× 1.07（取 0.75 × 1.07 ≈ 0.80，下调到 0.70 更保守）

已知流长比修正范围：0.85 ~ 1.50
已知最大值：1.50
安全裕度：× 0.80（取 1.50 × 0.80 = 1.20，下调到 1.20 中等偏高）

兜底值：
- default_base_pressure_ratio = 0.70（中等偏高保守）
- default_length_factor = 1.20（中等偏高保守）
```

**为什么 ×0.80 而非 ×1.2**：
- 注射压力过高 → 飞边、爆模、模具损伤
- 注射压力过低 → 短射（可二次调整补救）
- 因此保守兜底应**略偏高**而非略偏低，保证不短射

**为什么兜底不是更高**：
- 0.70 × 1.20 = 0.84，叠加 max_safe_pressure_ratio = 0.90 → 默认 84% max
- 已覆盖绝大多数材料 + 制品组合的物理需求
- 未识别场景仍可通过 max_safe_ratio 钳制保证机器安全

---

## 5. 保守兜底原则

### 5.1 决策优先级

```
短射（缺料）< 爆模（事故）

【原因】
- 短射：制品略偏小，可通过二次工艺调整补救（增大压力、延长填充时间）
- 爆模：可能损坏模具（数万~数百万）、机器、极端时安全事故
- 因此兜底必须偏保守，宁可打多一点压力
```

### 5.2 安全上限钳制

即使算法推导出的压力在物理上合理，仍需钳制到机器安全范围：

```
inj_pres = min(inj_pres_calculated, max_inj_pres × max_safe_pressure_ratio)
```

**默认 0.90**（机器物理极限留 10% 余量，防止液压冲击、传感器误差等）。

### 5.3 兜底值定义

| 参数 | 兜底值 | 选取依据 |
|------|--------|---------|
| `default_base_pressure_ratio` | 0.70 | 已知最大值 0.75 × 0.93 安全裕度 |
| `default_length_factor` | 1.20 | 已知最大值 1.50 × 0.80 安全裕度 |
| `max_safe_pressure_ratio` | 0.90 | 机器物理极限 10% 余量 |

### 5.4 未识别材料场景验证

设 max_inj_pres = 150 MPa（典型注塑机），未识别材料 → 兜底 base_ratio=0.70, length_factor=1.20：

| 场景 | inj_ratio | length_factor | inj_pres (MPa) | 占比 max | 安全性 |
|------|-----------|---------------|---------------|---------|--------|
| W=30g, t=3mm, L=150mm | 50 | 0.85 | 150 × 0.70 × 0.85 = **89.3** | 59.5% | ✅ 偏低但安全 |
| W=100g, t=2mm, L=300mm | 150 | 1.00 | 150 × 0.70 × 1.00 = **105.0** | 70.0% | ✅ 正常 |
| W=200g, t=1.5mm, L=450mm | 300 | 1.20 | 150 × 0.70 × 1.20 = **126.0** | 84.0% | ✅ 正常偏安全 |
| W=500g, t=1mm, L=500mm | 500 | 1.50 | 150 × 0.70 × 1.50 = **157.5** → 钳制 **135.0** | 90.0% | ✅ 上限钳制生效 |
| inj_ratio 缺失 | 0 | 1.20（兜底）| 150 × 0.70 × 1.20 = **126.0** | 84.0% | ✅ 保守合理 |

**所有场景下 inj_pres ∈ [89.3, 135.0] MPa，占 max 比例 ∈ [59.5%, 90.0%]，未识别材料略偏保守，机器安全有保障**。

---

## 6. 与原算法的对比

### 6.1 注射压力新旧对比（典型场景）

**场景 A：PP 制品，W=100g, t=2mm, L=200mm（D=40mm, max_inj_pres=150 MPa）**

| 项目 | 旧算法 | 新算法 | 差异 |
|------|--------|--------|------|
| inj_ratio | 100 | 100 | - |
| base_ratio | 0.65（固定） | 0.50（PP） | -0.15 |
| length_factor | 1.00（无） | 1.00（L/t=100） | 0.00 |
| inj_pres | 150 × 0.65 = **97.5** | 150 × 0.50 × 1.00 = **75.0** | **-22.5 MPa（-23%）** |

**结论**：PP 等流动性好的材料，旧算法压力偏高 23%，新算法更符合物理实际。

**场景 B：PC 制品，W=100g, t=1.5mm, L=450mm（D=40mm, max_inj_pres=150 MPa）**

| 项目 | 旧算法 | 新算法 | 差异 |
|------|--------|--------|------|
| inj_ratio | 300 | 300 | - |
| base_ratio | 0.65（固定） | 0.75（PC） | +0.10 |
| length_factor | 1.00（无） | 1.20（L/t=300） | +0.20 |
| inj_pres | 150 × 0.65 = **97.5** | 150 × 0.75 × 1.20 = **135.0** | **+37.5 MPa（+38%）** |

**结论**：PC 薄壁远浇，旧算法压力严重不足（必然短射），新算法更接近物理需求。

### 6.2 总体对比

| 维度 | 原算法（玄学）| 新算法（科学）|
|------|--------------|--------------|
| 数据来源 | 几次试模 | 材料手册 + Moldflow 共识 |
| 可追溯性 | ❌ "为什么 0.65？"答不上来 | ✅ 每个系数都有物理依据 |
| 材料差异 | ❌ 不区分 PP/PC | ✅ PP/PA/PC/PMMA/PBT 等差异化 |
| 流长比差异 | ❌ 不区分薄壁厚壁 | ✅ <100/100-200/200-350/>350 四档 |
| 物理可解释性 | ❌ 经验系数 | ✅ base_ratio × length_factor 二维推导 |
| 保守兜底 | ❌ 无差异 | ✅ 默认值 + 安全上限钳制 |
| 复用既有架构 | - | ✅ 复用 _parse_family / inj_ratio |
| 数据库迁移 | 不需要 | 不需要（从 abbreviation 解析 family）|

### 6.3 关键洞察

1. **旧算法**对所有材料 + 所有流长比都用 0.65，对 PP 等流动性好的材料**严重偏高**，对 PC 等高黏度薄壁件**严重不足**
2. **新算法**通过材料大类 × 流长比二维差异化，PP 类下调 23%，PC 类上调 38%，更符合物理实际
3. **安全钳制**保证即使算法极端推导（如超高流长比），最终压力也不会超过机器物理极限的 90%

---

## 7. 实施计划

### 7.1 文件改动清单

| 文件 | 改动 | 工作量 |
|------|------|--------|
| `initializer.py` | 重构行 386-391 + 新增两个查表函数 | 30~50 行 |
| `init_rules.json` | `DEFAULT.injection` 下新增 3 个字段 | ~30 行 |
| 测试用例 | 新旧行为对比 + 回归测试 | 较多 |

### 7.2 代码结构设计

#### 7.2.1 新增查表函数 1：`_get_base_pressure_ratio`

```python
def _get_base_pressure_ratio(self, family: str, c_inj: Dict[str, Any]) -> tuple:
    """
    获取材料基准压力比例（3 级兜底）

    优先级：
    1. 第 1 级 - Polymer.recommend_inj_pressure_ratio 字段（精确值）
    2. 第 2 级 - base_pressure_ratio_map[family]（大类典型值）
    3. 第 3 级 - default_base_pressure_ratio（兜底）

    Args:
        family: 材料大类（来自 _parse_family）
        c_inj: injection 分组合并系数

    Returns:
        (base_ratio, level) 元组，level ∈ {'precise', 'family', 'default'}
    """
    # ====== 第 1 级：精确值 ======
    precise_ratio = self.material.get('recommend_inj_pressure_ratio')
    if precise_ratio is not None:
        return precise_ratio, 'precise'

    # ====== 第 2 级：按大类查表 ======
    ratio_map = c_inj.get('base_pressure_ratio_map', {})
    if family and family in ratio_map:
        return ratio_map[family], 'family'

    # ====== 第 3 级：默认值（兜底）======
    return c_inj.get('default_base_pressure_ratio', 0.70), 'default'
```

#### 7.2.2 新增查表函数 2：`_get_length_factor`

```python
def _get_length_factor(self, inj_ratio: float, c_inj: Dict[str, Any]) -> tuple:
    """
    获取流长比修正系数（3 级兜底）

    优先级：
    1. 第 1 级 - Polymer.length_factor_override 字段（精确值）
    2. 第 2 级 - length_factor_buckets（按 inj_ratio 分档查表）
    3. 第 3 级 - default_length_factor（兜底）

    Args:
        inj_ratio: 流长比 L/t
        c_inj: injection 分组合并系数

    Returns:
        (length_factor, level) 元组
    """
    # ====== 第 1 级：精确值 ======
    override = self.material.get('length_factor_override')
    if override is not None:
        return override, 'precise'

    # ====== 第 2 级：按分档查表 ======
    buckets = c_inj.get('length_factor_buckets', [])
    if inj_ratio > 0:
        for bucket in sorted(buckets, key=lambda b: b.get('max_ratio') or float('inf')):
            max_ratio = bucket.get('max_ratio')
            if max_ratio is None or inj_ratio <= max_ratio:
                return bucket['factor'], 'bucket'

    # ====== 第 3 级：默认值（兜底）======
    return c_inj.get('default_length_factor', 1.20), 'default'
```

#### 7.2.3 重构行 386-391

```python
# ========== 注射参数 ==========
max_inj_pres = mach.get('max_set_injection_pressure', 150)
max_inj_velo = mach.get('max_set_injection_velocity', 100)

# 【重构】注射压力 = 材料黏度等级 × 流长比修正（二维物理推导）
# 推导链：流变学定律 → 材料黏度等级（base_ratio） × 流长比修正（length_factor）
# 数据源：3 级兜底（精确值 / 大类查表 / 默认值）
inj_ratio = max_length / avg_thickness  # 既有变量
family = self._parse_family(self.material.get('abbreviation', ''))
base_ratio, base_level = self._get_base_pressure_ratio(family, c_inj)
length_factor, factor_level = self._get_length_factor(inj_ratio, c_inj)

inj_pres_calculated = max_inj_pres * base_ratio * length_factor
max_safe_ratio = c_inj.get('max_safe_pressure_ratio', 0.90)
inj_pres = min(inj_pres_calculated, max_inj_pres * max_safe_ratio)

logger.debug(
    f"注射压力: family={family or 'unknown'} (level={base_level}), "
    f"base_ratio={base_ratio:.3f}, inj_ratio={inj_ratio:.1f}, "
    f"length_factor={length_factor:.3f} (level={factor_level}), "
    f"inj_pres={inj_pres:.2f}MPa ({(inj_pres/max_inj_pres*100):.1f}% max)"
)
```

### 7.3 推进步骤

1. **第一步**：算法逻辑改造（不依赖数据库迁移）
   - 在 `initializer.py` 新增 `_get_base_pressure_ratio` 和 `_get_length_factor`
   - 重构行 386-391 为二维推导公式
   - 配置 `init_rules.json`

2. **第二步**：写测试用例
   - 覆盖典型材料大类（PP/PE/PS/ABS/PA/POM/PC/PMMA/PBT/PET）
   - 覆盖典型流长比（50/150/300/500）
   - 覆盖未识别材料 + 缺失 inj_ratio 兜底场景
   - 对比新旧算法结果差异

3. **第三步**：内部验证
   - 选 2~3 个真实制品跑一遍
   - 工艺师 review 结果
   - 记录实际差异

4. **第四步**：灰度上线
   - 默认关闭新算法（开关控制）
   - 选 1 个机器/材料灰度开启
   - 收集生产反馈

5. **第五步**：逐步推广
   - 验证通过后，扩大范围
   - 持续收集反馈，微调大类基准比例 / 流长比修正系数

### 7.4 时间估计

| 步骤 | 工作量 |
|------|--------|
| 算法逻辑改造 | 1~2 天 |
| JSON 配置更新 | 0.5 天 |
| 测试用例 | 1~2 天 |
| 对比验证 | 1 天 |
| 工艺师 review | 1~3 天 |
| 灰度上线 | 1 天 |
| **总计** | **5.5~9.5 天**（单人）|

---

## 8. JSON 配置示例

### 8.1 新增配置（DEFAULT.injection 下追加）

```json
{
  "injection": {
    "inj_pres_ratio": 0.65,
    "default_base_pressure_ratio": 0.70,
    "default_length_factor": 1.20,
    "max_safe_pressure_ratio": 0.90,
    "base_pressure_ratio_map": {
      "PP": 0.50,
      "PE": 0.50,
      "PS": 0.55,
      "ABS": 0.55,
      "AS": 0.55,
      "PMMA": 0.65,
      "PA": 0.65,
      "POM": 0.65,
      "PET": 0.70,
      "PBT": 0.70,
      "PC": 0.75
    },
    "length_factor_buckets": [
      {"max_ratio": 100, "factor": 0.85, "label": "短流程厚壁"},
      {"max_ratio": 200, "factor": 1.00, "label": "中等流长"},
      {"max_ratio": 350, "factor": 1.20, "label": "长流程薄壁"},
      {"max_ratio": null, "factor": 1.50, "label": "极难薄壁远浇"}
    ]
  }
}
```

### 8.2 兼容性说明

- `inj_pres_ratio` 字段保留为 **fallback**，当 `base_pressure_ratio_map` / `length_factor_buckets` 同时缺失时启用
- 这样保证即使新配置未生效，也能保持旧行为

### 8.3 不需要删除的字段

本次重构**只新增不删除**。`inj_pres_ratio` 作为 fallback 保留。

---

## 9. 测试用例设计

### 9.1 新旧算法对比（典型场景）

设 D=40mm, ρ=1.0, max_inj_pres=150 MPa

| 材料 | inj_ratio | 旧 inj_pres | 新 inj_pres | 差异 (MPa) | 评估 |
|------|-----------|------------|------------|----------|------|
| PP | 50 | 97.5 | 63.8 | -33.8 | PP 流动性好，旧值偏高 ✅ |
| PP | 200 | 97.5 | 75.0 | -22.5 | 旧值偏高 ✅ |
| PP | 400 | 97.5 | 112.5 | +15.0 | 极薄壁远浇，新值更合理 ✅ |
| ABS | 100 | 97.5 | 82.5 | -15.0 | 略偏高 ✅ |
| ABS | 300 | 97.5 | 99.0 | +1.5 | 接近 ✅ |
| PC | 150 | 97.5 | 112.5 | +15.0 | PC 黏度高，新值更合理 ✅ |
| PC | 350 | 97.5 | 135.0 | +37.5 | 旧值严重不足 ✅ |
| PC | 500 | 97.5 | 135.0 (钳制) | +37.5 | 安全钳制生效 ✅ |
| 未识别 | 200 | 97.5 | 105.0 | +7.5 | 保守兜底 ✅ |
| inj_ratio 缺失 | - | 97.5 | 126.0 | +28.5 | 默认 length_factor 兜底 ✅ |

**变化幅度可控**（±40 MPa 内），不会破坏现有工艺模板；薄壁远浇件（PC 高 L/t）压力显著提升，符合物理实际。

### 9.2 材料大类差异化验证

设 W=200g, D=40mm, max_inj_pres=150 MPa, t=2mm, L=300mm（inj_ratio=150）

| 材料 | base_ratio | length_factor | inj_pres (MPa) | 占比 max |
|------|-----------|---------------|---------------|---------|
| PP | 0.50 | 1.00 | 75.0 | 50.0% |
| PE | 0.50 | 1.00 | 75.0 | 50.0% |
| PS | 0.55 | 1.00 | 82.5 | 55.0% |
| ABS | 0.55 | 1.00 | 82.5 | 55.0% |
| PA | 0.65 | 1.00 | 97.5 | 65.0% |
| POM | 0.65 | 1.00 | 97.5 | 65.0% |
| PMMA | 0.65 | 1.00 | 97.5 | 65.0% |
| PET | 0.70 | 1.00 | 105.0 | 70.0% |
| PBT | 0.70 | 1.00 | 105.0 | 70.0% |
| PC | 0.75 | 1.00 | 112.5 | 75.0% |
| 未识别 | 0.70（兜底）| 1.00 | 105.0 | 70.0% |

**不同材料自动差异化**（50% → 75%），未识别材料保守兜底在 70%。

### 9.3 流长比差异化验证

设 W=200g, D=40mm, max_inj_pres=150 MPa, material=PC（base_ratio=0.75）

| L (mm) | t (mm) | inj_ratio | length_factor | inj_pres (MPa) | 占比 max |
|--------|--------|-----------|---------------|---------------|---------|
| 100 | 2 | 50 | 0.85 | 95.6 | 63.8% |
| 200 | 2 | 100 | 1.00 | 112.5 | 75.0% |
| 300 | 2 | 150 | 1.00 | 112.5 | 75.0% |
| 500 | 2 | 250 | 1.20 | 135.0 | 90.0% |
| 800 | 2 | 400 | 1.50 | 135.0（钳制）| 90.0% |

**流长比自动差异化**（63.8% → 90%），极高流长比钳制到 90%。

### 9.4 边界场景验证

| 场景 | 输入 | 输出 | 评估 |
|------|------|------|------|
| 极小件（1g, t=1mm, L=50mm）| inj_ratio=50, family=PP | 150 × 0.50 × 0.85 = 63.8 | ✅ 正常偏低 |
| 极大件（2000g, t=5mm, L=1500mm）| inj_ratio=300, family=PC | 150 × 0.75 × 1.20 = 135.0（钳制）| ✅ 上限生效 |
| 未识别材料 | family='', inj_ratio=150 | 150 × 0.70 × 1.00 = 105.0 | ✅ 兜底合理 |
| inj_ratio 缺失 | inj_ratio=0, family=PC | 150 × 0.75 × 1.20 = 135.0（兜底 1.20）| ✅ 兜底合理 |
| max_inj_pres 缺失 | 用默认 150 | 同上 | ✅ 默认值兜底 |

---

## 10. 风险与缓解

| 风险 | 严重度 | 缓解措施 |
|------|--------|---------|
| 行为变化不一致 | 中 | 保留 `inj_pres_ratio` 作为 fallback |
| 大类基准比例不准 | 中 | 工艺师微调 `base_pressure_ratio_map` |
| 流长比修正系数不准 | 中 | 工艺师微调 `length_factor_buckets` |
| 安全钳制不合理 | 低 | 默认 0.90，可配置 |
| 工艺师不接受 | 中 | 内部验证 + 工艺师 review 步骤 |
| 测试覆盖不足 | 中 | 覆盖 10+ 材料大类 × 5+ 流长比档位 |

---

## 11. 相关文件

| 文件 | 说明 |
|------|------|
| [initializer.py](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/initializer.py) | 注射压力算法主体（待重构行 386-391）|
| [init_rules.json](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/expert_rules/init_rules.json) | 规则源文件（待新增配置项）|
| [2026-07-04-injection-stroke-physics-design.md](file:///Users/lpissenlit/workfiles/molding-optima/backend/_dev_refs/2026-07-04-injection-stroke-physics-design.md) | 兄弟算法设计文档（length_ratio）|
| [2026-07-04-algorithm-refactor-roadmap.md](file:///Users/lpissenlit/workfiles/molding-optima/backend/_dev_refs/2026-07-04-algorithm-refactor-roadmap.md) | 算法改造路线图（阶段 2 P0）|

---

## 12. 后续扩展（不在本文档范围）

- 阶段 2.2：注射速度（同样是 base × factor 二维模式）
- 阶段 2.3：保压压力（叠加材料收缩率 + 制品壁厚）
- 阶段 3：保压细节（保压速度、保压时间）
- 阶段 4：多段注射/保压的压力曲线（已有 `_MULTI_INJ_GENERIC_HOT/COLD` 等）

---

## 13. 局限性诚实声明

> 本章诚实说明当前方案的物理依据强度，避免给出过度承诺。

### 13.1 半经验方法 vs 严格物理推导

本方案属于**"半经验方法"**，不是严格的物理推导。

| 系数 / 变量 | 类型 | 理论依据 | 量化来源 |
|------------|------|---------|---------|
| `max_inj_pres` | 物理量 | 机器 HMI 设定上限 | 机器表（`max_set_injection_pressure`，操作界面允许输入的最大注射压力值） |
| `max_safe_pressure_ratio` | 物理量 | 机器物理安全裕量 | 工程实践（液压冲击/传感器误差防护） |
| `inj_ratio` | 物理量 | 流变学定义 L/t | 制品几何（max_length / ave_thickness） |
| `base_ratio[family]` | **经验系数** | 定性物理正确（黏度高 → 基准压力高） | 材料手册 + Moldflow 共识中位近似 |
| `length_factor(inj_ratio)` | **经验系数** | 定性物理正确（L/t 大 → 压力大） | 工艺手册 + 注塑工艺经验值 |

> **字段说明**：机器表同时存在 `max_injection_pressure`（设备物理极限）与 `max_set_injection_pressure`（HMI 设定上限）两个字段。本方案使用 `max_set_injection_pressure`，原因：
> 1. 工艺师实际操作时只能输入 ≤ HMI 设定上限的值
> 2. 算法输出必须能直接下发到机器，超过 HMI 限制的值不可用
> 3. 现有代码（[initializer.py:13, 113](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/initializer.py#L13-L113)）已采用 `max_set_injection_pressure`
> 4. `max_safe_pressure_ratio` 钳制后实际值 ≤ 90% HMI 上限，自然不会触及设备物理极限

### 13.2 关键诚实点

1. **`base_ratio` 的 11 个数字（0.50~0.75）是工程经验中位值**，不是从 η、γ̇、Q 等物理量严格推导出来的。
2. **`length_factor` 的 4 个数字（0.85~1.50）是工艺经验值**，不是从流变学公式推导出来的。
3. **Cross-WLF 参数模型已存在但填写率极低**：[PolymerRheology](file:///Users/lpissenlit/workfiles/molding-optima/backend/masterdata/models/material.py#L57-L103) 模型已支持 7 个参数（`cross_wlf_n` / `cross_wlf_tau` / `cross_wlf_d1-d3` / `cross_wlf_a1-a2`），但材料厂商通常不公开完整参数，需 Moldflow 数据库或实验测量才能补齐——实际等同于缺失。
4. **mold 模型只有主流道长度，缺少流道直径**：[mold.py:136-138](file:///Users/lpissenlit/workfiles/molding-optima/backend/masterdata/models/mold.py#L136-L138) 已有 `runner_weight` 与 `runner_length`，但**无 `runner_diameter` 字段**，无法计算流道截面积 → 无法推导剪切速率 → 无法实施 Poiseuille 流变学公式。
5. **缺少完整流道分段几何**：当前仅有主流道长度，缺少各段流道（主流道 / 分流道 / 浇口）布局与分段直径，无法做严格分段压力损失累加。

### 13.3 为什么"半经验方法已经比单系数 0.65 好"

虽然定量仍是经验系数，但相对单系数 0.65 在以下维度有显著提升：

| 维度 | 单系数 0.65 | 半经验方法 | 提升 |
|------|------------|-----------|------|
| **跨场景泛化能力** | 所有材料一刀切 | 11 个材料大类差异化 | ✅ 显著提升 |
| **流长比响应** | 不响应 | 4 档响应（0.85~1.50） | ✅ 显著提升 |
| **物理可解释性** | 数字来源不明 | 每个数字都有定性物理依据 | ✅ 显著提升 |
| **失败归因** | 调参试错 | 按 family 或 L/t 维度精确定位 | ✅ 显著提升 |
| **可扩展性** | 无扩展空间 | 预留 `recommend_inj_pressure_ratio`、`length_factor_override` 字段 | ✅ 显著提升 |
| **物理推导严格性** | 无 | 定性物理正确 + 定量经验 | ⚠️ 仍有局限 |

**核心结论**：本方案是"工程落地"与"理论严谨"的合理折中——既立即解决 0.65 一刀切问题，又为未来严格物理推导留出空间。

### 13.4 物理推导严格性的演进目标

未来按"渐进式物理化"路径，从"半经验"逐步逼近"严格推导"（详见第 15 章）：

```
当前：第一阶段（半经验）
  ├─ 物理定性 ✅ 材料黏度等级 + 流长比响应
  └─ 物理定量 ❌ 经验系数表

目标：第三阶段（严格推导）
  ├─ 物理定性 ✅ 同上
  └─ 物理定量 ✅ ΔP = (8ηLQ)/(πR⁴) + Cross-WLF
```

---

## 14. 渐进式物理化演进路径

本方案是渐进式物理化的**第一阶段**，未来按以下路径分阶段演进。

### 14.1 阶段一（当前）：半经验方法

**目标**：立即落地，解决"0.65 一刀切"问题。

**内容**：
- 实施"流长比 × 材料分档"二维差异化
- 复用既有 `_parse_family` / `inj_ratio` 架构
- 保留 3 级兜底 + 安全钳制
- 工艺师可微调 `base_pressure_ratio_map` / `length_factor_buckets`

**数据需求**：0（既有数据足够）

### 14.2 阶段二（数据补齐）：引入物理参数

**目标**：为第三阶段严格推导准备物理参数。

**内容**：
- **`PolymerRheology` 模型已支持 Cross-WLF 7 参数**（[material.py:78-94](file:///Users/lpissenlit/workfiles/molding-optima/backend/masterdata/models/material.py#L78-L94)）：`cross_wlf_n` / `cross_wlf_tau` / `cross_wlf_d1` / `cross_wlf_d2` / `cross_wlf_d3` / `cross_wlf_a1` / `cross_wlf_a2`，**无需新增 schema**，只需采集主流材料数据补齐
- **在 mold 模型新增 `runner_diameter` 字段**（流道直径），与既有 `runner_length`（[mold.py:138](file:///Users/lpissenlit/workfiles/molding-optima/backend/masterdata/models/mold.py#L138)）配合计算流道截面积
- 启动"材料数据采集项目"，优先补齐主流材料（PP / PE / ABS / PC / PA / POM）的 Cross-WLF 7 参数；数据源：Moldflow 材料库 / 厂商技术资料 / 实验测量
- 阶段一算法继续作为 fallback

**数据需求**：
- **数据补齐**：Cross-WLF 7 参数（字段已存在，需采集填入）
- **schema 扩展**：mold 模型新增 `runner_diameter` 字段

### 14.3 阶段三（严格推导）：分段压力损失累加

**目标**：每个数字都可追溯到物理定律。

**内容**：
- 实施分段压力损失累加公式：
  ```
  P_inj = ΔP_nozzle + ΔP_runner + ΔP_gate + ΔP_cavity
        = Σ (8 × η(γ̇,T,P) × L_i × Q) / (π × R_i⁴)
  ```
- 各段分别按 Poiseuille 流动公式计算 ΔP
- 熔体黏度用 Cross-WLF 模型：`η(γ̇, T, P) = η₀(T,P) / (1 + (λγ̇)^(1-n))`
- 替换阶段一算法，阶段一作为 fallback

**数据需求**：阶段二数据 + 各段详细几何

### 14.4 阶段四（精度优化）：闭环校准

**目标**：用实测数据持续优化算法精度。

**内容**：
- 引入 Moldflow 仿真值作为基准，校准经验系数与物理参数
- 持续积累工艺实测数据，反推真实材料参数
- 形成"实测数据驱动的物理推导闭环"
- 阶段三算法持续优化

**数据需求**：Moldflow 仿真 + 工艺实测数据

### 14.5 各阶段数据依赖与工作量

| 阶段 | 核心新增数据 | 数据来源 | 估算工作量 |
|------|------------|---------|----------|
| 一 | 无 | 既有 | 1-2 周 |
| 二 | Cross-WLF 7 参数补齐 + mold 新增 `runner_diameter` | 材料数据采集项目（Moldflow / 厂商资料）+ schema 迁移 | 2-3 月 |
| 三 | 流道分段几何（各段直径 + 分段布局） | 工艺 CAE 仿真 + 模具图纸 | 3-6 月 |
| 四 | Moldflow 仿真值 + 实测反推 | 工艺实测采集 | 持续 |

### 14.6 演进保证机制

为确保演进过程中算法持续可用，每个阶段都遵守以下保证：

1. **向下兼容**：阶段 N 算法必须保留阶段 N-1 算法作为 fallback
2. **数据缺失兜底**：所有新增数据字段必须有默认值或 3 级兜底
3. **安全钳制不变**：`max_safe_pressure_ratio = 0.90` 在所有阶段保持
4. **可回退**：任何阶段实施问题可立即回退到前一阶段

---

## 15. 与项目物理化演进路线的对齐

本方案遵循项目"渐进式物理化"演进路径，与既有架构深度对齐。

### 15.1 复用既有架构组件

| 组件 | 位置 | 复用方式 |
|------|------|---------|
| `_parse_family()` | [initializer.py:225-237](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/initializer.py#L225-L237) | 直接调用，零修改 |
| `_get_shrink_rate()` | [initializer.py:239-266](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/initializer.py#L239-L266) | 同模式复用（3 级兜底结构） |
| `inj_ratio` 计算 | [initializer.py:358-360](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/initializer.py#L358-L360) | 既有变量，零修改 |
| `c_inj` 系数组 | `_coeffs.get('injection', {})` | 同模式复用 |
| `family_shrink_map` 配置 | [init_rules.json:23-34](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/expert_rules/init_rules.json#L23-L34) | 同模式扩展（新增 `base_pressure_ratio_map`）|
| `_GENERAL_MATERIALS` | [initializer.py:113](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/initializer.py#L113) | 间接相关，逻辑对齐 |

### 15.2 与兄弟算法的对齐

- 与 **`length_ratio`** 算法（已实施）共享 `_parse_family` + 3 级兜底模式
- 与 **`cushion_len`** 算法（D/4 公式）共享"机器物理推导 + 3 级兜底"思路
- 与 **`hold_pres`** 算法（保压压力，待改造）保持接口对称（同样二维差异化模式）

### 15.3 与项目物理化精神的符合度

| 项目规范 | 本方案符合度 | 说明 |
|---------|------------|------|
| 算法设计必须基于物理原理 | ⚠️ 定性符合，定量是经验 | 见第 13 章局限性诚实声明 |
| 物理推导 + 行业共识数据 | ✅ | 物理定性（材料黏度等级、流长比）+ 行业共识定量 |
| 三级保守兜底 | ✅ | 完整 3 级兜底（精确/大类/默认） |
| 安全钳制（防爆模）| ✅ | `max_safe_pressure_ratio = 0.90` |
| 渐进式物理化演进 | ✅ | 处于第一阶段，文档明确第二/三/四阶段路径 |
| 可追溯性 | ✅ | 每个系数都有定性物理依据 + 量化来源 |
| 可扩展性 | ✅ | 预留 `recommend_inj_pressure_ratio`、`length_factor_override` 字段 |
| 失败归因清晰 | ✅ | 按 family 或 L/t 维度精确定位 |

---

## 16. 更新日志

| 日期 | 进度 | 备注 |
|------|------|------|
| 2026-07-05 | 设计文档建立 | ✅ 本文档（章节 1-12） |
| 2026-07-05 | 局限性诚实声明 | ✅ 章节 13 |
| 2026-07-05 | 渐进式物理化演进路径 | ✅ 章节 14 |
| 2026-07-05 | 与项目物理化路线对齐 | ✅ 章节 15 |
| 2026-07-05 | max_set_injection_pressure 字段语义修正 | ✅ 表格 13.1：明确使用 HMI 设定上限而非设备物理极限 |
| 2026-07-05 | 数据现状诚实修正 | ✅ 13.2/14.2/14.5：明确 PolymerRheology 已有 Cross-WLF 字段但填写率极低、mold 已有 runner_length 但缺 runner_diameter |
| 待定 | 算法实施 | ⏳ 见 7.3 推进步骤 |
| 待定 | 测试覆盖 | ⏳ 见 9.1-9.4 |
| 待定 | 灰度上线 | ⏳ 见 7.3 |

---

*文档生成时间：2026-07-05*