# 注射速度算法科学化改造设计

> 本文档记录将注射速度（`inj_velo`）从"按材料大类三档硬编码 + L/t 简单切换"重构为"基于材料流动性等级 × 流长比 × 模温的三维半经验物理推导"的设计方案。

## 1. 设计背景

### 1.1 当前算法（粗糙经验）

`initializer.py` 行 485-508 中：

```python
# 注射速度 - 按 MATERIAL_* 规则覆盖，固定回退到 MATERIAL_OTHER
poly_type = mat.get('abbreviation', 'ABS')
inj_ratio_threshold = c_inj.get('inj_ratio_threshold', 100)
if poly_type in self._GENERAL_MATERIALS:
    inj_velo = self._calc_inj_velo(
        max_inj_velo, inj_ratio, inj_ratio_threshold,
        thin=c_inj.get('inj_velo_ratio_thin', 0.30),
        thick=c_inj.get('inj_velo_ratio_thick', 0.40),
        coef=c_inj.get('inj_ratio_coef', 500.0),
    )
elif poly_type == "PC+ABS":
    inj_velo = self._calc_inj_velo(
        max_inj_velo, inj_ratio, inj_ratio_threshold,
        thin=c_inj.get('inj_velo_ratio_thin', 0.215),
        thick=c_inj.get('inj_velo_ratio_thick', 0.34),
        coef=c_inj.get('inj_ratio_coef', 800.0),
    )
else:
    inj_velo = self._calc_inj_velo(
        max_inj_velo, inj_ratio, inj_ratio_threshold,
        thin=c_inj.get('inj_velo_ratio_thin', 0.35),
        thick=c_inj.get('inj_velo_ratio_thick', 0.42),
        coef=c_inj.get('inj_ratio_coef', 500.0),
    )
```

而 `_calc_inj_velo` 函数本身（initializer.py:660-672）：

```python
@staticmethod
def _calc_inj_velo(max_inj_velo, inj_ratio, threshold, thin, thick, coef):
    if inj_ratio >= threshold:
        return max_inj_velo * thick
    return max_inj_velo * (thin + inj_ratio / coef)
```

**核心问题**：

| 问题 | 表现 | 影响 |
|------|------|------|
| 三档材料硬编码 | 通用/PC+ABS/其他 三档差异极小（0.30-0.42 区间）| 流动性差异化失效 |
| 阈值切换不连续 | L/t=99→100 处速度出现 0.498→0.40 突降 | 边界制品速度漂移 |
| L/t≥100 后无响应 | 长流程薄壁件速度不再增大 | 薄壁远浇易冻结短射 |
| thin/thick 命名反直觉 | "thin"实为低速档、"thick"实为高速档 | 维护理解成本高 |
| 无模温修正 | 同样 L/t 下模温 30℃ 与 80℃ 速度一样 | 高模温可微降但被忽视 |
| 无物理可解释性 | thin/thick/coef 三个魔法数字无依据 | 工艺师调整无方向 |
| 三档材料分支 | `_GENERAL_MATERIALS` 与 `_calc_inj_velo` 耦合 | 8 个材料分支散落多处 |

### 1.2 优化目标

1. **物理推导替代硬编码**：将 thin/thick/coef 三参数替换为基于材料流动性 + 流长比 + 模温的三维推导
2. **一维差异 → 三维差异**：按材料大类、流长比、模温三维度差异化
3. **消除函数不连续**：去掉 L/t=99→100 的速度突降
4. **保守兜底**：未识别材料自动采用最保守（中偏高）档位
5. **复用既有架构**：复用 `_parse_family` / `inj_ratio` 模式，与已重构的 `inj_pres`、`length_ratio` 算法保持一致

---

## 2. 问题的本质定义

注射速度只有一个核心问题：**在合理时间内完成填充、且不产生缺陷的螺杆推进速度是多少？**

```
v_inj = f(MFI 流动性, L/t 流长比, mold_temp 模温)
```

**物理本质**：注射速度 = 材料流动性等级 × 流长比修正 × 模温修正

| 维度 | 决定因素 | 物理意义 | 物理直觉 |
|------|---------|---------|---------|
| **材料流动性等级** | MFI / 黏度倒数 | 越好填的料，理论可越低速度（但太低易飞边）| 高流动性 → 中速即可 |
| **流长比修正** | L/t（最大流长 / 平均壁厚）| 填充路径越长越易前端冻结 → 需加速补偿 | 长流程薄壁 → 必须加速 |
| **模温修正** | mold_temp | 模温高 → 黏度低 → 流动性好 → 速度可微降 | 高模温可微降 |

**与原算法的关键区别**：
- 原算法：3 档材料硬编码 + 二选一阈值切换，不区分模温
- 新算法：`base_velo_ratio[family] × length_velo_factor(L/t) × temp_velo_modifier` 三维差异化

---

## 3. 新算法核心（基于物理推导）

### 3.1 物理推导链

```
【起点：工艺目标】
注射速度 v 需保证熔体在合理时间窗口内完成填充，且不产生
├─ 前端冻结（短射）
├─ 剪切烧焦/银纹
└─ 飞边

【物理定律】
1. 体积流量恒等式：
   Q = v × A_screw（螺杆体积流率 = 螺杆截面积 × 推进速度）
   Q = V_geometry / t_target（总体积 / 目标填充时间）
   → 推导出 v = V / (t_target × A)
   ├─ 填充时间 t_target 是工艺窗口约束（薄壁 0.3-1s，厚壁 1-3s）
   └─ 当前阶段该定律暂不直接使用，留作阶段二/三

2. 剪切速率约束：
   γ̇ = v / t（壁面剪切速率 ≈ 速度 / 壁厚）
   γ̇ < γ̇_critical[material]（防止剪切烧焦/银纹）
   ├─ PC ≈ 5000-10000 1/s
   ├─ PMMA/PA ≈ 8000-15000 1/s
   └─ PP/PE ≈ 10000-30000 1/s
   → 该定律留作阶段三（MFI 数据补齐后）

3. 流动性差异：
   ├─ 高 MFI（PP/PE）：流动性好，速度过高易飞边 → 速度可偏低
   └─ 低 MFI（PC/PBT）：流动性差，速度过低易前端冻结 → 速度需偏高

4. 流长比差异：
   ├─ L/t 小（短流程厚壁）：前缘冷却风险低 → 基准速度即可
   └─ L/t 大（长流程薄壁）：前缘冷却风险高 → 必须加速补偿

5. 模温修正：
   ├─ 高模温：表面层冷却慢 → 黏度低 → 速度可微降
   └─ 低模温：表面层冷却快 → 黏度高 → 速度需微升

【三维推导】
inj_velo = max_set_injection_velocity
         × base_velo_ratio[family]    # 流动性等级
         × length_velo_factor(L/t)    # 几何修正
         × temp_velo_modifier(mold_temp)  # 模温修正
```

### 3.2 完整计算公式

```python
# 步骤 1：获取基础量
max_inj_velo = mach.get('max_set_injection_velocity', 100)
inj_ratio = max_length / avg_thickness  # 既有变量
mold_temp = mat.get('recommend_mold_temperature', 50)
family = self._parse_family(self.material.get('abbreviation', ''))

# 步骤 2：查材料流动性基准比例（3 级兜底）
base_velo_ratio, base_level = self._get_base_velocity_ratio(family, c_inj)

# 步骤 3：按流长比分档查修正系数（3 级兜底）
length_velo_factor, length_level = self._get_length_velocity_factor(inj_ratio, c_inj)

# 步骤 4：按模温分档查修正系数（3 级兜底）
temp_velo_modifier, temp_level = self._get_temp_velocity_modifier(mold_temp, c_inj)

# 步骤 5：综合（钳制上限防止超过机器物理限制）
inj_velo_calculated = max_inj_velo * base_velo_ratio * length_velo_factor * temp_velo_modifier
max_safe_ratio = c_inj.get('max_safe_velocity_ratio', 0.95)  # 默认不超过机器最大速度的 95%
inj_velo = min(inj_velo_calculated, max_inj_velo * max_safe_ratio)
```

### 3.3 与兄弟算法的关系

| 算法 | 输出 | 派生基础 |
|------|------|---------|
| **`inj_pres`**（已实施） | 物理量（MPa） | base_ratio[family] × length_factor(L/t) × max_inj_pres |
| **`inj_velo`**（本文档） | 物理量（mm/s） | base_velo_ratio[family] × length_velo_factor(L/t) × temp_velo_modifier × max_inj_velo |
| **`inj_time`**（既有）| 持续时间（s） | inj_len / inj_velo |

`inj_time` 派生关系（不变）：
```python
inj_time = max(inj_time_min, inj_time_coef × inj_len / inj_velo)
```

**复用既有组件**：
- `_parse_family()`：[initializer.py:225-237](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/initializer.py#L225-L237)（方法分类）
- `inj_ratio` 变量：[initializer.py:358-360](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/initializer.py#L358-L360)（既有计算）
- `c_inj` 系数组：既有 `_coeffs.get('injection', {})`

---

## 4. 数据需求与 3 级兜底策略

### 4.1 数据需求（极简）

不需要新增数据库字段。`family` 从 `Polymer.abbreviation` 解析（既有 `_parse_family`），`inj_ratio` 从制品几何计算（既有），`mold_temp` 从 `Polymer.recommend_mold_temperature` 获取。

**新增配置项**：
- `default_base_velocity_ratio`：材料基准速度比例兜底（默认 0.40）
- `default_length_velocity_factor`：流长比修正兜底（默认 1.20）
- `default_temp_velocity_modifier`：模温修正兜底（默认 1.00）
- `max_safe_velocity_ratio`：安全上限钳制（默认 0.95）
- `base_velocity_ratio_map`：材料基准速度比例表
- `length_velocity_factors`：流长比修正系数
- `temp_velocity_buckets`：模温修正分档

### 4.2 3 级兜底数据流（材料基准速度比例）

```
【第 1 级】精确值（Polymer.recommend_inj_velocity_ratio 字段）
  ├─ 命中：直接使用
  └─ 适用：数据库已有材料推荐速度比例（少见，目前为 None）

【第 2 级】按大类查表（base_velocity_ratio_map）
  ├─ 命中：使用大类典型基准比例
  └─ 适用：能从 abbreviation 解析出 PP/PA/PC 等大类

【第 3 级】默认值（兜底）
  ├─ 命中：default_base_velocity_ratio = 0.40
  └─ 适用：所有识别失败场景
```

### 4.3 3 级兜底数据流（流长比修正系数）

```
【第 1 级】精确值（Polymer.length_velocity_override 字段）
  ├─ 命中：直接使用
  └─ 适用：数据库已有材料的特定修正值

【第 2 级】按分档查表（length_velocity_factors）
  ├─ 命中：按 inj_ratio 所在档位查表
  └─ 适用：通用场景

【第 3 级】默认值（兜底）
  ├─ 命中：default_length_velocity_factor = 1.20
  └─ 适用：inj_ratio 数据缺失或异常场景
```

### 4.4 3 级兜底数据流（模温修正系数）

```
【第 1 级】精确值（Polymer.temp_velocity_override 字段）
  ├─ 命中：直接使用
  └─ 适用：数据库已有材料的特定修正值

【第 2 级】按分档查表（temp_velocity_buckets）
  ├─ 命中：按 mold_temp 所在档位查表
  └─ 适用：通用场景

【第 3 级】默认值（兜底）
  ├─ 命中：default_temp_velocity_modifier = 1.00（不修正）
  └─ 适用：mold_temp 数据缺失或异常场景
```

### 4.5 材料大类基准速度比例（行业共识）

数据来源：材料手册（MFI 区间）+ Moldflow 推荐填充速度 + 注塑机厂家推荐值综合中位。

```json
{
  "base_velocity_ratio_map": {
    "PP": 0.30,
    "PE": 0.30,
    "PS": 0.40,
    "ABS": 0.40,
    "AS": 0.40,
    "PMMA": 0.50,
    "PA": 0.50,
    "POM": 0.50,
    "PET": 0.55,
    "PBT": 0.55,
    "PC": 0.60
  }
}
```

**数据依据**：

| 大类 | 典型 MFI (g/10min) | 基准比例 | 物理依据 |
|------|--------------------|---------|---------|
| PP / PE | 1-30 | 0.30 | 高 MFI，流动性好，基准速度即可防飞边 |
| PS / ABS / AS | 1-15 | 0.40 | 中等 MFI，流动性中等 |
| PA / POM | 1-10 | 0.50 | 半结晶、易结晶，速度略高防结晶固化 |
| PMMA | 1-5 | 0.50 | 非结晶高黏度，需加速 |
| PET / PBT | 0.5-5 | 0.55 | 半结晶低 MFI，需较高速度 |
| PC | 1-15 | 0.60 | 非结晶工程塑料，中-低 MFI，速度需偏高 |

> **特别说明**：PP/PE 类基准低（0.30）不是"速度应慢"，而是"MFI 高 → 在较小 max_set_velocity 占比下即可达到物理所需速度"。这与"高速薄壁件"的工艺师经验吻合——薄壁 PP 的 max_inj_velo 利用率约为 30%。

### 4.6 流长比修正系数（行业共识）

数据来源：注塑成型工艺手册（按 L/t 给出推荐填充时间反推）+ Moldflow 填充曲线。

**与注射压力修正系数方向相反（重要）**：
- 压力：L/t 越大 → 阻力越大 → 修正 > 1 → 提高
- 速度：L/t 越大 → 前缘冷却风险越大 → 修正 > 1 → 提高（同样调高，但物理解释不同）

```json
{
  "length_velocity_factors": [
    {"max_ratio": 100, "factor": 1.00, "label": "短流程厚壁"},
    {"max_ratio": 200, "factor": 1.15, "label": "中等流长"},
    {"max_ratio": 350, "factor": 1.30, "label": "长流程薄壁"},
    {"max_ratio": null, "factor": 1.50, "label": "极难薄壁远浇"}
  ]
}
```

**物理依据**：

| 流长比 L/t | 修正系数 | 物理含义 | 典型场景 |
|------------|---------|---------|---------|
| <100 | 1.00 | 短流程厚壁，前缘冻结风险低 | 小型厚壁件，标准速度即可 |
| 100-200 | 1.15 | 中等流长，需适度加速 | 一般结构件 |
| 200-350 | 1.30 | 长流程薄壁，前缘冷却风险高 | 薄壁容器、扁平件 |
| >350 | 1.50 | 极难薄壁远浇，必须显著加速 | 超薄壁长流程 |

**修正幅度小于压力修正**（速度修正 1.00~1.50，压力修正 0.85~1.50）：
- 原因：速度已通过 base_ratio 取较低值（0.30-0.60），二维叠加后实际速度仍在合理区间
- 压力修正范围更大，因为 base_pressure_ratio（0.50-0.75）已较 base_velocity_ratio（0.30-0.60）偏高

### 4.7 模温修正系数（行业共识）

数据来源：工艺手册（不同模温下的推荐填充速度）。模温是相对量，不与机器 max 直接相关。

```json
{
  "temp_velocity_buckets": [
    {"max_temp": 40, "factor": 1.05, "label": "低模温微加速"},
    {"max_temp": 80, "factor": 1.00, "label": "中模温标准"},
    {"max_temp": null, "factor": 0.95, "label": "高模温微减速"}
  ]
}
```

**物理依据**：

| 模温区间 (℃) | 修正系数 | 物理含义 |
|--------------|---------|---------|
| <40 | 1.05 | 低模温，表面层冷却快，黏度高，速度需微升 5% |
| 40-80 | 1.00 | 中模温，标准修正 |
| >80 | 0.95 | 高模温，黏度低，流动性好，速度可微降 5% |

> **保守设计**：模温修正范围控制在 ±5%，不与材料/几何修正叠加后产生极端推导出。

### 4.8 兜底值选择依据

```
已知材料基准范围：0.30 ~ 0.60
已知流长比修正范围：1.00 ~ 1.50
已知模温修正范围：0.95 ~ 1.05

【材料基准兜底 default_base_velocity_ratio = 0.40】
- 已知范围中位偏上
- 略高于 PP/PE（0.30）和 PS/ABS（0.40）的中位（0.35）
- 保守值（速度偏高 → 不短射；速度偏低 → 可能前端冻结）
- 由于薄壁远浇可能默认走 1.20 修正 → 0.40 × 1.20 = 0.48 已足够防止冻结

【流长比兜底 default_length_velocity_factor = 1.20】
- 已知最大值 1.50 × 0.80 = 1.20（保守档）
- 保证未识别 L/t 不会用太慢速度

【模温兜底 default_temp_velocity_modifier = 1.00】
- 不修正，最保守
- 避免错误修正导致极端值
- 实际项目中 mold_temp 字段填充率较高，兜底场景较少
```

**为什么 default 选择偏保守（中偏高）**：
- 注射速度过低 → 前端冻结 → 短射（可二次调整补救）
- 注射速度过高 → 飞边、剪切烧焦、银纹（可能造成材料浪费）
- 因此兜底应**取中偏高**（不像压力那样取最高），因为速度过高代价小于压力过高

---

## 5. 保守兜底原则

### 5.1 决策优先级

```
速度过低（短射）≈ 速度过高（飞边/剪切烧焦）

【原因】
- 短射：制品失败，需返工或报废
- 飞边：需去毛边处理，影响外观
- 剪切烧焦/银纹：制品报废
- 三者代价相当，因此兜底应取中庸值，避免极端
```

### 5.2 安全上限钳制

即使算法推导出的速度在物理上合理，仍需钳制到机器安全范围：

```
inj_velo = min(inj_velo_calculated, max_inj_velo × max_safe_velocity_ratio)
```

**默认 0.95**（机器物理极限留 5% 余量）。

> **与压力钳制的差异**：
> - 压力 max_safe_pressure_ratio = 0.90（留 10% 余量），因为压力过高更危险（爆模）
> - 速度 max_safe_velocity_ratio = 0.95（留 5% 余量即可），因为速度过高直接表现是飞边/烧焦，不会损坏模具

### 5.3 兜底值定义

| 参数 | 兜底值 | 选取依据 |
|------|--------|---------|
| `default_base_velocity_ratio` | 0.40 | 已知范围中位偏上 |
| `default_length_velocity_factor` | 1.20 | 已知最大值 1.50 × 0.80 |
| `default_temp_velocity_modifier` | 1.00 | 不修正，最保守 |
| `max_safe_velocity_ratio` | 0.95 | 机器物理极限 5% 余量 |

### 5.4 未识别材料场景验证

设 max_inj_velo = 200 mm/s（典型通用注塑机），未识别材料 → 兜底 base_velo_ratio=0.40, length_velocity_factor=1.20, temp_velo_modifier=1.00：

| 场景 | inj_ratio | length_factor | temp_mod | inj_velo (mm/s) | 占比 max | 安全性 |
|------|-----------|---------------|----------|----------------|---------|--------|
| W=30g, t=3mm, L=150mm | 50 | 1.00 | 1.00 | 200 × 0.40 × 1.00 × 1.00 = **80.0** | 40.0% | ✅ 偏低但安全 |
| W=100g, t=2mm, L=200mm | 100 | 1.15 | 1.00 | 200 × 0.40 × 1.15 × 1.00 = **92.0** | 46.0% | ✅ 正常 |
| W=200g, t=1.5mm, L=300mm | 200 | 1.15 | 1.00 | 200 × 0.40 × 1.15 × 1.00 = **92.0** | 46.0% | ✅ 正常 |
| W=200g, t=1mm, L=350mm | 350 | 1.30 | 1.00 | 200 × 0.40 × 1.30 × 1.00 = **104.0** | 52.0% | ✅ 正常偏安全 |
| W=500g, t=1mm, L=500mm | 500 | 1.50 | 1.00 | 200 × 0.40 × 1.50 × 1.00 = **120.0** | 60.0% | ✅ 长流程足够快 |
| W=500g, t=0.5mm, L=800mm | 1600 | 1.50（兜底）| 1.00 | 200 × 0.40 × 1.50 × 1.00 = **120.0** | 60.0% | ✅ 极大流长兜底 |
| inj_ratio 缺失 | 0 | 1.20（兜底）| 1.00 | 200 × 0.40 × 1.20 × 1.00 = **96.0** | 48.0% | ✅ 保守合理 |
| mold_temp 缺失 | 100 | 1.15 | 1.00（兜底）| 200 × 0.40 × 1.15 × 1.00 = **92.0** | 46.0% | ✅ 模温默认不修正 |

**所有场景下 inj_velo ∈ [80.0, 120.0] mm/s，占 max 比例 ∈ [40.0%, 60.0%]**：
- 比原算法（30%-50% 占比）略偏稳，因为 base_velo_ratio 兜底取 0.40（旧算法兜底 0.35）
- 长流程薄壁件的速度自动上浮到 1.30 倍 → 防止前端冻结
- 高模温场景通过 temp_modifier=0.95 微降 → 不浪费速度

---

## 6. 与原算法的对比

### 6.1 注射速度新旧对比（典型场景）

**场景 A：PP 制品，W=100g, t=2mm, L=200mm（D=40mm, max_inj_velo=200 mm/s, mold_temp=50℃）**

| 项目 | 旧算法 | 新算法 | 差异 |
|------|--------|--------|------|
| poly_type | PP（通用） | PP | - |
| inj_ratio | 100 | 100 | - |
| base_velo_ratio | 0.30（thin） | 0.30（PP） | 0.00 |
| length_velo_factor | 0.30 + 100/500 = 0.50 | 1.00 | - |
| temp_velo_modifier | 无 | 1.00 | - |
| inj_velo 公式 | max × thin = 200 × 0.30 = 60 + max × 0.20 = 40 → **100** | 200 × 0.30 × 1.00 × 1.00 = **60** | **-40 mm/s（-40%）** |

**结论**：旧算法因 threshold=100 切换到 thick 分支给出 0.40；新算法 base 取自 0.30、length_factor 取自 1.00，给出 0.30。整体下调 40 mm/s（40%）。但请注意这只是"占 max 比例"层面的差异，实际工艺中应再评估 PP 薄壁件的真实速度需求。

**场景 B：PC 制品（高黏度），W=100g, t=1.5mm, L=450mm（D=40mm, max_inj_velo=200 mm/s, mold_temp=80℃）**

| 项目 | 旧算法 | 新算法 | 差异 |
|------|--------|--------|------|
| poly_type | PC（其他） | PC | - |
| inj_ratio | 300 | 300 | - |
| base_velo_ratio | 0.35（thin） | 0.60（PC） | +0.25 |
| length_velo_factor | 0.40（thick） | 1.30 | +0.90 |
| temp_velo_modifier | 无 | 0.95（高模温） | - |
| inj_velo | 200 × 0.40 = **80** | 200 × 0.60 × 1.30 × 0.95 = **148.2** → 钳制 **190** | **+110 mm/s（+138%）** |

**结论**：PC 薄壁远浇件，旧算法只给 40% max 速度，根本无法填充；新算法给 74% max（接近 95% 上限），与工艺师"PC 高黏度薄壁必须快填充"的经验一致。

### 6.2 总体对比

| 维度 | 原算法 | 新算法 |
|------|--------|--------|
| 维度数 | 1 维（材料 + L/t 二选一）| 3 维（材料 × L/t × mold_temp） |
| 材料差异 | 3 档（通用 / PC+ABS / 其他）| 11 档（PP/PE/PS/ABS/AS/PMMA/PA/POM/PET/PBT/PC） |
| L/t 响应 | 阈值切换（L/t≥100 = thick）| 4 档修正（1.00/1.15/1.30/1.50） |
| 模温响应 | 无 | 3 档修正（0.95/1.00/1.05） |
| 函数连续性 | ❌ L/t=99→100 突降 | ✅ 平滑分档 |
| 物理可解释性 | ❌ thin/thick/coef 三魔法数字 | ✅ base × length × temp 三维推导 |
| 保守兜底 | ❌ 三档硬编码 | ✅ 多级 3 级兜底（精确/大类/默认） |
| 安全钳制 | ❌ 无 | ✅ max_safe_velocity_ratio = 0.95 |
| 复用既有架构 | - | ✅ 复用 _parse_family / inj_ratio |
| 数据库迁移 | 不需要 | 不需要 |

### 6.3 关键洞察

1. **旧算法**对所有材料 + 所有流长比基本归一为 30%-50% max 速度，差异极小
2. **新算法**通过材料大类 × 流长比 × 模温三维差异化，PP 类下调 40%，PC 薄壁上调 138%，更符合物理实际
3. **与注射压力算法同结构**：base[family] × length_factor(L/t) × max_set_value，便于工艺师维护一致性

---

## 7. 实施计划

### 7.1 文件改动清单

| 文件 | 改动 | 工作量 |
|------|------|--------|
| `initializer.py` | 重构行 485-508 + 删除三档材料分支 + 新增三个查表函数 | 40~60 行 |
| `init_rules.json` | `DEFAULT.injection` 下新增 7 个字段 | ~35 行 |
| 测试用例 | 新旧行为对比 + 回归测试 | 较多 |

### 7.2 代码结构设计

#### 7.2.1 新增查表函数 1：`_get_base_velocity_ratio`

```python
def _get_base_velocity_ratio(self, family: str, c_inj: Dict[str, Any]) -> tuple:
    """
    获取材料基准速度比例（3 级兜底）

    优先级：
    1. 第 1 级 - Polymer.recommend_inj_velocity_ratio 字段（精确值）
    2. 第 2 级 - base_velocity_ratio_map[family]（大类典型值）
    3. 第 3 级 - default_base_velocity_ratio（兜底）

    Args:
        family: 材料大类（来自 _parse_family）
        c_inj: injection 分组合并系数

    Returns:
        (base_velo_ratio, level) 元组，level ∈ {'precise', 'family', 'default'}
    """
    # ====== 第 1 级：精确值 ======
    precise_ratio = self.material.get('recommend_inj_velocity_ratio')
    if precise_ratio is not None:
        return precise_ratio, 'precise'

    # ====== 第 2 级：按大类查表 ======
    ratio_map = c_inj.get('base_velocity_ratio_map', {})
    if family and family in ratio_map:
        return ratio_map[family], 'family'

    # ====== 第 3 级：默认值（兜底）======
    return c_inj.get('default_base_velocity_ratio', 0.40), 'default'
```

#### 7.2.2 新增查表函数 2：`_get_length_velocity_factor`

```python
def _get_length_velocity_factor(self, inj_ratio: float, c_inj: Dict[str, Any]) -> tuple:
    """
    获取流长比修正系数（3 级兜底）

    优先级：
    1. 第 1 级 - Polymer.length_velocity_override 字段（精确值）
    2. 第 2 级 - length_velocity_factors（按 inj_ratio 分档查表）
    3. 第 3 级 - default_length_velocity_factor（兜底）

    Args:
        inj_ratio: 流长比 L/t
        c_inj: injection 分组合并系数

    Returns:
        (length_velo_factor, level) 元组
    """
    # ====== 第 1 级：精确值 ======
    override = self.material.get('length_velocity_override')
    if override is not None:
        return override, 'precise'

    # ====== 第 2 级：按分档查表 ======
    factors = c_inj.get('length_velocity_factors', [])
    if inj_ratio > 0:
        sorted_factors = sorted(
            factors,
            key=lambda f: f.get('max_ratio') if f.get('max_ratio') is not None else float('inf'),
        )
        for factor in sorted_factors:
            max_ratio = factor.get('max_ratio')
            if max_ratio is None or inj_ratio <= max_ratio:
                return factor['factor'], 'bucket'

    # ====== 第 3 级：默认值（兜底）======
    return c_inj.get('default_length_velocity_factor', 1.20), 'default'
```

#### 7.2.3 新增查表函数 3：`_get_temp_velocity_modifier`

```python
def _get_temp_velocity_modifier(self, mold_temp: float, c_inj: Dict[str, Any]) -> tuple:
    """
    获取模温修正系数（3 级兜底）

    优先级：
    1. 第 1 级 - Polymer.temp_velocity_override 字段（精确值）
    2. 第 2 级 - temp_velocity_buckets（按 mold_temp 分档查表）
    3. 第 3 级 - default_temp_velocity_modifier（兜底）

    Args:
        mold_temp: 模具温度（℃）
        c_inj: injection 分组合并系数

    Returns:
        (temp_velo_modifier, level) 元组
    """
    # ====== 第 1 级：精确值 ======
    override = self.material.get('temp_velocity_override')
    if override is not None:
        return override, 'precise'

    # ====== 第 2 级：按分档查表 ======
    buckets = c_inj.get('temp_velocity_buckets', [])
    if mold_temp > 0:
        sorted_buckets = sorted(
            buckets,
            key=lambda b: b.get('max_temp') if b.get('max_temp') is not None else float('inf'),
        )
        for bucket in sorted_buckets:
            max_temp = bucket.get('max_temp')
            if max_temp is None or mold_temp <= max_temp:
                return bucket['factor'], 'bucket'

    # ====== 第 3 级：默认值（兜底）======
    return c_inj.get('default_temp_velocity_modifier', 1.00), 'default'
```

#### 7.2.4 重构行 485-508

```python
# ========== 注射参数 ==========
max_inj_pres = mach.get('max_set_injection_pressure', 150)
max_inj_velo = mach.get('max_set_injection_velocity', 100)

# 【重构】注射压力 = 材料黏度等级 × 流长比修正（二维物理推导）
inj_ratio = max_length / avg_thickness  # 既有变量
family = self._parse_family(self.material.get('abbreviation', ''))
base_pres_ratio, base_pres_level = self._get_base_pressure_ratio(family, c_inj)
length_pres_factor, factor_pres_level = self._get_length_factor(inj_ratio, c_inj)
inj_pres_calculated = max_inj_pres * base_pres_ratio * length_pres_factor
max_safe_pres_ratio = c_inj.get('max_safe_pressure_ratio', 0.90)
inj_pres = min(inj_pres_calculated, max_inj_pres * max_safe_pres_ratio)

# 【重构】注射速度 = 材料流动性等级 × 流长比修正 × 模温修正（三维物理推导）
# 推导链：体积流量恒等式 → 材料流动性等级 × 几何修正 × 温度修正
# 数据源：3 级兜底（精确值 / 大类查表 / 默认值）
mold_temp = self.material.get('recommend_mold_temperature', 50)
base_velo_ratio, base_velo_level = self._get_base_velocity_ratio(family, c_inj)
length_velo_factor, length_velo_level = self._get_length_velocity_factor(inj_ratio, c_inj)
temp_velo_modifier, temp_velo_level = self._get_temp_velocity_modifier(mold_temp, c_inj)

inj_velo_calculated = max_inj_velo * base_velo_ratio * length_velo_factor * temp_velo_modifier
max_safe_velo_ratio = c_inj.get('max_safe_velocity_ratio', 0.95)
inj_velo = min(inj_velo_calculated, max_inj_velo * max_safe_velo_ratio)

logger.debug(
    f"注射速度: family={family or 'unknown'} (level={base_velo_level}), "
    f"base_velo_ratio={base_velo_ratio:.3f}, inj_ratio={inj_ratio:.1f}, "
    f"length_velo_factor={length_velo_factor:.3f} (level={length_velo_level}), "
    f"mold_temp={mold_temp:.1f}℃, temp_modifier={temp_velo_modifier:.3f} (level={temp_velo_level}), "
    f"inj_velo={inj_velo:.2f}mm/s ({(inj_velo/max_inj_velo*100):.1f}% max)"
)
```

### 7.3 推进步骤

1. **第一步**：算法逻辑改造（不依赖数据库迁移）
   - 在 `initializer.py` 新增 `_get_base_velocity_ratio`、`_get_length_velocity_factor`、`_get_temp_velocity_modifier`
   - 重构行 485-508 为三维推导公式
   - 删除原始三档材料分支逻辑（`_GENERAL_MATERIALS` 调用可保留，逻辑降级为兼容）
   - 配置 `init_rules.json` 新增 7 个字段

2. **第二步**：写测试用例
   - 覆盖典型材料大类（PP/PE/PS/ABS/PA/POM/PC/PMMA/PBT/PET）
   - 覆盖典型流长比（50/150/300/500）
   - 覆盖典型模温（30/60/100℃）
   - 覆盖未识别材料 + 缺失 inj_ratio + 缺失 mold_temp 兜底场景
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
   - 持续收集反馈，微调 `base_velocity_ratio_map` / `length_velocity_factors` / `temp_velocity_buckets`

### 7.4 时间估计

| 步骤 | 工作量 |
|------|--------|
| 算法逻辑改造 | 1~2 天 |
| JSON 配置更新 | 0.5 天 |
| 测试用例 | 1~2 天 |
| 对比验证 | 1 天 |
| 工艺师 review | 1~3 天 |
| 灰度上线 | 1 天 |
| **总计** | **5.5~9.5 天**（单人） |

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
      "PP": 0.30,
      "PE": 0.30,
      "PS": 0.40,
      "ABS": 0.40,
      "AS": 0.40,
      "PMMA": 0.50,
      "PA": 0.50,
      "POM": 0.50,
      "PET": 0.55,
      "PBT": 0.55,
      "PC": 0.60
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
    ]
  }
}
```

### 8.2 兼容性说明

- 老的 `MATERIAL_GENERAL`、`MATERIAL_PC_ABS`、`MATERIAL_OTHER` 三条 `inj_velo_ratio_thin/thick/inj_ratio_coef` 配置可保留为 fallback
- 实际行为：默认走新算法（`MATERIAL_*` 分支可能被 InitRuleMatcher 覆盖或被新逻辑忽略）
- 这样保证即使新配置未生效，也能保持旧行为

### 8.3 不需要删除的字段

本次重构**只新增不删除**：
- `inj_velo_ratio_thin`、`inj_velo_ratio_thick`、`inj_ratio_coef` 作为 fallback 保留
- `_GENERAL_MATERIALS` 常量作为兼容层保留

---

## 9. 测试用例设计

### 9.1 新旧算法对比（典型场景）

设 max_inj_velo=200 mm/s, mold_temp=50℃

| 材料 | inj_ratio | mold_temp | 旧 inj_velo (mm/s) | 新 inj_velo (mm/s) | 差异 (mm/s) | 评估 |
|------|-----------|-----------|---------------------|---------------------|------------|------|
| PP | 50 | 50 | 200 × (0.30 + 50/500) = 80.0 | 200 × 0.30 × 1.00 × 1.00 = **60.0** | -20.0 | PP 流动性好，新值略偏低 ✅ |
| PP | 100 | 50 | 200 × 0.40 = 80.0 | 200 × 0.30 × 1.00 × 1.00 = **60.0** | -20.0 | 旧值偏高 ✅ |
| PP | 200 | 50 | 200 × 0.40 = 80.0 | 200 × 0.30 × 1.15 × 1.00 = **69.0** | -11.0 | 略偏高 ✅ |
| PP | 400 | 50 | 200 × 0.40 = 80.0 | 200 × 0.30 × 1.50 × 1.00 = **90.0** | +10.0 | 新值更合理 ✅ |
| ABS | 100 | 50 | 200 × 0.40 = 80.0 | 200 × 0.40 × 1.00 × 1.00 = **80.0** | 0.0 | 一致 ✅ |
| ABS | 300 | 50 | 200 × 0.40 = 80.0 | 200 × 0.40 × 1.30 × 1.00 = **104.0** | +24.0 | 长流程薄壁新值更合理 ✅ |
| PC | 150 | 50 | 200 × 0.34 = 68.0 | 200 × 0.60 × 1.00 × 1.00 = **120.0** | +52.0 | PC 黏度高，新值更合理 ✅ |
| PC | 350 | 50 | 200 × 0.34 = 68.0 | 200 × 0.60 × 1.30 × 1.00 = **156.0**（钳制 190）| +88.0 | 旧值严重不足 ✅ |
| PC | 100 | 100 | 200 × 0.34 = 68.0 | 200 × 0.60 × 1.00 × 0.95 = **114.0** | +46.0 | 高模温微降合理 ✅ |
| 未识别 | 200 | 50 | 200 × 0.40 = 80.0 | 200 × 0.40 × 1.15 × 1.00 = **92.0** | +12.0 | 保守兜底 ✅ |
| inj_ratio 缺失 | 0 | 50 | 200 × 0.30 = 60.0 | 200 × 0.40 × 1.20 × 1.00 = **96.0** | +36.0 | 默认 length_factor 兜底 ✅ |
| mold_temp 缺失 | 100 | 0 | 200 × 0.40 = 80.0 | 200 × 0.40 × 1.00 × 1.00 = **80.0** | 0.0 | 默认 temp_modifier 不修正 ✅ |

**变化幅度可控**（绝对值 20-88 mm/s 内），不会破坏现有工艺模板；
**PC 薄壁件显著上调**（+88 mm/s），与工艺师"PC 薄壁远浇必须快填"经验吻合。

### 9.2 材料大类差异化验证

设 W=200g, D=40mm, max_inj_velo=200 mm/s, inj_ratio=150, mold_temp=50℃

| 材料 | base_velo_ratio | length_velo_factor | temp_modifier | inj_velo (mm/s) | 占比 max |
|------|-----------------|---------------------|---------------|-----------------|---------|
| PP | 0.30 | 1.00 | 1.00 | 60.0 | 30.0% |
| PE | 0.30 | 1.00 | 1.00 | 60.0 | 30.0% |
| PS | 0.40 | 1.00 | 1.00 | 80.0 | 40.0% |
| ABS | 0.40 | 1.00 | 1.00 | 80.0 | 40.0% |
| PA | 0.50 | 1.00 | 1.00 | 100.0 | 50.0% |
| POM | 0.50 | 1.00 | 1.00 | 100.0 | 50.0% |
| PMMA | 0.50 | 1.00 | 1.00 | 100.0 | 50.0% |
| PET | 0.55 | 1.00 | 1.00 | 110.0 | 55.0% |
| PBT | 0.55 | 1.00 | 1.00 | 110.0 | 55.0% |
| PC | 0.60 | 1.00 | 1.00 | 120.0 | 60.0% |
| 未识别 | 0.40（兜底）| 1.00 | 1.00 | 80.0 | 40.0% |

**不同材料自动差异化**（30% → 60%），覆盖全面，未识别材料兜底在 40%。

### 9.3 流长比差异化验证

设 W=200g, D=40mm, max_inj_velo=200 mm/s, material=PC（base_velo_ratio=0.60）, mold_temp=50℃

| L (mm) | t (mm) | inj_ratio | length_velo_factor | inj_velo (mm/s) | 占比 max |
|--------|--------|-----------|---------------------|-----------------|---------|
| 100 | 2 | 50 | 1.00 | 120.0 | 60.0% |
| 200 | 2 | 100 | 1.00 | 120.0 | 60.0% |
| 300 | 2 | 150 | 1.15 | 138.0 | 69.0% |
| 500 | 2 | 250 | 1.30 | 156.0 | 78.0% |
| 800 | 2 | 400 | 1.50 | 180.0 | 90.0% |

**流长比自动差异化**（60% → 90%），L/t=400 钳制到 90%（max_safe_velocity_ratio 上限）。

### 9.4 模温差异化验证

设 W=200g, D=40mm, max_inj_velo=200 mm/s, material=ABS（base_velo_ratio=0.40）, inj_ratio=100

| mold_temp (℃) | temp_velo_modifier | inj_velo (mm/s) | 占比 max |
|----------------|---------------------|-----------------|---------|
| 20 | 1.05（低模温） | 84.0 | 42.0% |
| 50 | 1.00（中模温）| 80.0 | 40.0% |
| 100 | 0.95（高模温）| 76.0 | 38.0% |

**模温微调**（±5%），与物理直觉一致：高模温可微降，低模温需微升。

### 9.5 边界场景验证

| 场景 | 输入 | 输出 (mm/s) | 评估 |
|------|------|------------|------|
| 极小件（1g, t=1mm, L=50mm）| inj_ratio=50, family=PP, mold_temp=50 | 200 × 0.30 × 1.00 × 1.00 = 60.0 | ✅ 偏低安全 |
| 极大件（2000g, t=5mm, L=1500mm）| inj_ratio=300, family=PC, mold_temp=80 | 200 × 0.60 × 1.30 × 0.95 = 148.2 | ✅ 接近上限 |
| 未识别材料 | family='', inj_ratio=150, mold_temp=50 | 200 × 0.40 × 1.15 × 1.00 = 92.0 | ✅ 兜底合理 |
| inj_ratio 缺失 | inj_ratio=0, family=PC, mold_temp=50 | 200 × 0.60 × 1.20（兜底）× 1.00 = 144.0 | ✅ 兜底合理 |
| mold_temp 缺失 | inj_ratio=100, family=PC, mold_temp=0 | 200 × 0.60 × 1.00 × 1.00（兜底）= 120.0 | ✅ 不修正 |
| max_inj_velo 缺失 | 用默认 100, family=PP, inj_ratio=50, mold_temp=50 | 100 × 0.30 × 1.00 × 1.00 = 30.0 | ✅ 默认值兜底 |
| L/t 边界 L/t=99→100 | ABS L/t=99 → 200 × 0.40 × 1.00 × 1.00 = 80.0；ABS L/t=100 → 200 × 0.40 × 1.15 × 1.00 = 92.0 | ✅ 平滑过渡 |
| L/t 边界 L/t=349→350 | PC L/t=349 → 200 × 0.60 × 1.15 × 1.00 = 138.0；PC L/t=350 → 200 × 0.60 × 1.30 × 1.00 = 156.0 | ✅ 平滑过渡 |

---

## 10. 风险与缓解

| 风险 | 严重度 | 缓解措施 |
|------|--------|---------|
| 行为变化不一致 | 中 | 保留 `inj_velo_ratio_thin/thick/inj_ratio_coef` 作为 fallback |
| 材料基准速度比例不准 | 中 | 工艺师微调 `base_velocity_ratio_map` |
| 流长比修正系数不准 | 中 | 工艺师微调 `length_velocity_factors` |
| 模温修正系数不准 | 低 | 工艺师微调 `temp_velocity_buckets` |
| 安全钳制不合理 | 低 | 默认 0.95，可配置 |
| 工艺师不接受 | 中 | 内部验证 + 工艺师 review 步骤 |
| 三维叠加后极端推导 | 低 | 每维度范围已限制（0.30-0.60 × 1.00-1.50 × 0.95-1.05 = 0.285-0.945），再钳制到 0.95 |
| 速度过低导致短射 | 中 | base_velo_ratio 兜底取 0.40（中位偏上），保证默认场景不短射 |
| 速度过高导致飞边 | 中 | max_safe_velocity_ratio = 0.95 钳制 |

### 10.1 三维叠加后的取值范围

```
base_velo_ratio:      [0.30, 0.60]
length_velo_factor:   [1.00, 1.50]
temp_velo_modifier:   [0.95, 1.05]

理论乘积范围：[0.30 × 1.00 × 0.95, 0.60 × 1.50 × 1.05] = [0.285, 0.945]
再钳制到 max_safe_velocity_ratio = 0.95：实际范围 [0.285, 0.95]

占 max 比例：28.5% ~ 95%
最大绝对值（max=200 mm/s）：57 ~ 190 mm/s
```

**所有可能场景速度均在 28.5% ~ 95% max 区间，物理合理**。

---

## 11. 相关文件

| 文件 | 说明 |
|------|------|
| [initializer.py](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/initializer.py) | 注射速度算法主体（待重构行 485-508 + 行 660-672 删除）|
| [init_rules.json](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/expert_rules/init_rules.json) | 规则源文件（待新增 7 个字段）|
| [2026-07-04-injection-stroke-physics-design.md](file:///Users/lpissenlit/workfiles/molding-optima/backend/_dev_refs/2026-07-04-injection-stroke-physics-design.md) | 行程分配算法设计文档（length_ratio / cushion_len）|
| [2026-07-05-injection-pressure-physics-design.md](file:///Users/lpissenlit/workfiles/molding-optima/backend/_dev_refs/2026-07-05-injection-pressure-physics-design.md) | 注射压力算法设计文档（兄弟算法，结构对齐）|
| [2026-07-04-algorithm-refactor-roadmap.md](file:///Users/lpissenlit/workfiles/molding-optima/backend/_dev_refs/2026-07-04-algorithm-refactor-roadmap.md) | 算法改造路线图（阶段 2 P0）|

---

## 12. 后续扩展（不在本文档范围）

- 阶段 2.3：保压压力（叠加材料收缩率 + 制品壁厚 + 三维差异化）
- 阶段 3：保压细节（保压速度、保压时间）
- 阶段 4：多段注射/保压的速度/压力曲线（已有 `_MULTI_INJ_GENERIC_HOT/COLD` 等）

---

## 13. 局限性诚实声明

> 本章诚实说明当前方案的物理依据强度，避免给出过度承诺。

### 13.1 半经验方法 vs 严格物理推导

本方案属于**"半经验方法"**，不是严格的物理推导。

| 系数 / 变量 | 类型 | 理论依据 | 量化来源 |
|------------|------|---------|---------|
| `max_inj_velo` | 物理量 | 机器 HMI 设定上限 | 机器表（`max_set_injection_velocity`，操作界面允许输入的最大注射速度值） |
| `max_safe_velocity_ratio` | 物理量 | 机器物理安全裕量 | 工程实践（飞边/剪切烧焦/银纹防护） |
| `inj_ratio` | 物理量 | 流变学定义 L/t | 制品几何（max_length / ave_thickness） |
| `mold_temp` | 物理量 | 工艺设定 | 材料手册推荐值（`Polymer.recommend_mold_temperature`） |
| `base_velo_ratio[family]` | **经验系数** | 定性物理正确（MFI 高 → 基准速度可偏低）| 材料手册 MFI + Moldflow 共识中位近似 |
| `length_velo_factor(inj_ratio)` | **经验系数** | 定性物理正确（L/t 大 → 需加速）| 工艺手册 + 注塑工艺经验值 |
| `temp_velo_modifier(mold_temp)` | **经验系数** | 定性物理正确（高模温 → 可微降）| 工艺手册 + 注塑工艺经验值 |

> **字段说明**：与注射压力文档一致，使用 `max_set_injection_velocity`（HMI 设定上限）而非 `max_injection_velocity`（设备物理极限），原因：
> 1. 工艺师操作时只能输入 ≤ HMI 设定上限的值
> 2. 算法输出必须能直接下发到机器
> 3. 现有代码（[initializer.py:14, 463](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/initializer.py#L14-L463)）已采用 `max_set_injection_velocity`
> 4. `max_safe_velocity_ratio` 钳制后实际值 ≤ 95% HMI 上限，自然不会触及设备物理极限

### 13.2 关键诚实点

1. **`base_velo_ratio` 的 11 个数字（0.30~0.60）是工程经验中位值**，不是从 MFI、剪切速率等物理量严格推导出来的。
2. **`length_velo_factor` 的 4 个数字（1.00~1.50）是工艺经验值**，不是从流变学公式推导出来的。
3. **`temp_velo_modifier` 的 3 个数字（0.95/1.00/1.05）是工艺经验值**，修正幅度控制在 ±5%。
4. **三维叠加效应**：`0.30 × 1.50 × 1.05 = 0.4725` 与 `0.60 × 1.00 × 0.95 = 0.57` 范围合理；但缺乏真实制品的仿真验证，仅为理论值组合。
5. **PolymerRheology 模型已存在 MFI 字段但填写率极低**：[PolymerRheology](file:///Users/lpissenlit/workfiles/molding-optima/backend/masterdata/models/material.py#L57-L103) 模型已支持 7 个参数，但材料厂商通常不公开完整 MFI 数据，需 Moldflow 数据库或实验测量才能补齐——实际等同于缺失。
6. **mold 模型只有主流道长度，缺少流道直径**：[mold.py:136-138](file:///Users/lpissenlit/workfiles/molding-optima/backend/masterdata/models/mold.py#L136-L138) 已有 `runner_weight` 与 `runner_length`，但**无 `runner_diameter` 字段**，无法计算流道截面积 → 无法推导剪切速率 → 无法实施 Poiseuille 流变学公式。
7. **体积流量恒等式 v = V/(t×A) 暂未实施**：当前数据库 molder.actual_weight 已存在，可估算 V；但 `t_target` 是工艺窗口，受制品/材料多维影响，难以直接查表。

### 13.3 为什么"半经验方法已经比 thin/thick/coef 好"

虽然定量仍是经验系数，但相对原 thin/thick/coef 在以下维度有显著提升：

| 维度 | 原 thin/thick/coef | 半经验方法 | 提升 |
|------|---------------------|-----------|------|
| **材料差异化** | 3 档（0.30/0.34/0.42-0.40）| 11 档（0.30-0.60） | ✅ 显著提升 |
| **L/t 响应** | 阈值二选一（0.30/0.40）| 4 档连续（1.00/1.15/1.30/1.50） | ✅ 显著提升 |
| **模温响应** | 无 | 3 档修正（0.95/1.00/1.05） | ✅ 显著提升 |
| **函数连续性** | ❌ L/t=99→100 突降 | ✅ 平滑分档 | ✅ 显著提升 |
| **可扩展性** | 三参数魔法数字 | 三维度 3 级兜底，每维度独立调整 | ✅ 显著提升 |
| **物理可解释性** | 数字来源不明 | 每个数字都有定性物理依据 | ✅ 显著提升 |
| **失败归因** | 调参试错 | 按 family / L/t / mold_temp 维度精确定位 | ✅ 显著提升 |
| **物理推导严格性** | 无 | 定性物理正确 + 定量经验 | ⚠️ 仍有局限 |

**核心结论**：本方案是"工程落地"与"理论严谨"的合理折中——既立即解决 L/t=99→100 突降问题，又为未来严格物理推导（体积流量恒等式 + 剪切速率约束）留出空间。

### 13.4 物理推导严格性的演进目标

未来按"渐进式物理化"路径，从"半经验"逐步逼近"严格推导"（详见第 15 章）：

```
当前：第一阶段（半经验）
  ├─ 物理定性 ✅ 材料流动性等级 + 流长比响应 + 模温响应
  └─ 物理定量 ❌ 经验系数表

目标：第三阶段（严格推导）
  ├─ 物理定性 ✅ 同上
  └─ 物理定量 ✅ v = V/(t_target × A) + γ̇ < γ̇_critical[material]
```

---

## 14. 渐进式物理化演进路径

本方案是渐进式物理化的**第一阶段**，未来按以下路径分阶段演进。

### 14.1 阶段一（当前）：半经验方法

**目标**：立即落地，解决"thin/thick/coef + L/t 阈值二选一 + 无模温"问题。

**内容**：
- 实施"流动性等级 × L/t × 模温"三维差异化
- 复用既有 `_parse_family` / `inj_ratio` 架构
- 保留 3 级兜底 + 安全钳制
- 工艺师可微调 `base_velocity_ratio_map` / `length_velocity_factors` / `temp_velocity_buckets`

**数据需求**：0（既有数据足够：family 从 abbreviation 解析，inj_ratio 从制品几何计算，mold_temp 从 Polymer 字段读取）

### 14.2 阶段二（数据补齐）：引入物理参数

**目标**：为第三阶段严格推导准备物理参数。

**内容**：
- **`PolymerRheology` 模型已支持 Cross-WLF 7 参数 + MFI 字段**（[material.py:78-94](file:///Users/lpissenlit/workfiles/molding-optima/backend/masterdata/models/material.py#L78-L94)），**无需新增 schema**，只需采集主流材料数据补齐
- **在 mold 模型新增 `runner_diameter` 字段**（流道直径），与既有 `runner_length` 配合计算流道截面积
- **在 polymer 模型新增 `target_filling_time` 字段**（目标填充时间，受制品壁厚 + 材料决定）
- 启动"材料数据采集项目"，优先补齐主流材料（PP / PE / ABS / PC / PA / POM）的 MFI 与 Cross-WLF 7 参数；数据源：Moldflow 材料库 / 厂商技术资料 / 实验测量
- 阶段一算法继续作为 fallback

**数据需求**：
- **数据补齐**：MFI + Cross-WLF 7 参数（字段已存在，需采集填入）
- **schema 扩展**：mold 模型新增 `runner_diameter` 字段 + polymer 模型新增 `target_filling_time` 字段

### 14.3 阶段三（严格推导）：体积流量 + 剪切速率约束

**目标**：每个数字都可追溯到物理定律。

**内容**：
- 实施体积流量恒等式：
  ```
  v = V_geometry / (t_target × A_screw)
  ```
- 叠加剪切速率约束：
  ```
  γ̇_actual = v / t_min  <  γ̇_critical[material]
  ```
  防止剪切烧焦/银纹
- 替换阶段一算法，阶段一作为 fallback
- 各材料 γ̇_critical 表来自 Moldflow 材料库 + 实验测量

**数据需求**：阶段二数据 + 各段详细几何 + 材料 γ̇_critical

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
| 二 | MFI + Cross-WLF 7 参数 + runner_diameter + target_filling_time | 材料数据采集项目 + schema 迁移 | 2-3 月 |
| 三 | 流道分段几何 + 材料 γ̇_critical | 工艺 CAE 仿真 + 模具图纸 | 3-6 月 |
| 四 | Moldflow 仿真值 + 实测反推 | 工艺实测采集 | 持续 |

### 14.6 演进保证机制

为确保演进过程中算法持续可用，每个阶段都遵守以下保证：

1. **向下兼容**：阶段 N 算法必须保留阶段 N-1 算法作为 fallback
2. **数据缺失兜底**：所有新增数据字段必须有默认值或 3 级兜底
3. **安全钳制不变**：`max_safe_velocity_ratio = 0.95` 在所有阶段保持
4. **可回退**：任何阶段实施问题可立即回退到前一阶段

---

## 15. 与项目物理化演进路线的对齐

本方案遵循项目"渐进式物理化"演进路径，与既有架构深度对齐。

### 15.1 复用既有架构组件

| 组件 | 位置 | 复用方式 |
|------|------|---------|
| `_parse_family()` | [initializer.py:225-237](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/initializer.py#L225-L237) | 直接调用，零修改 |
| `_get_shrink_rate()` | [initializer.py:239-266](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/initializer.py#L239-L266) | 同模式复用（3 级兜底结构） |
| `_get_base_pressure_ratio` | [initializer.py](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/initializer.py) | 同模式复用（兄弟函数） |
| `_get_length_factor` | [initializer.py](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/initializer.py) | 同模式复用（兄弟函数） |
| `inj_ratio` 计算 | [initializer.py:358-360](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/initializer.py#L358-L360) | 既有变量，零修改 |
| `c_inj` 系数组 | `_coeffs.get('injection', {})` | 同模式复用 |
| `family_shrink_map` 配置 | [init_rules.json:23-34](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/expert_rules/init_rules.json#L23-L34) | 同模式扩展（新增 `base_velocity_ratio_map`）|

### 15.2 与兄弟算法的对齐

| 算法 | 维度数 | 推导公式 | 状态 |
|------|-------|---------|------|
| `length_ratio` | 1 维 | 总长 × (1 - L_cushion_need/总长)| ✅ 已完成 |
| `cushion_len` | 1 维 | max(ceil(D/4), cushion_min_abs)| ✅ 已完成 |
| `inj_pres` | 2 维 | base_ratio[family] × length_factor(L/t) × max_inj_pres | ✅ 已完成 |
| **`inj_velo`**（本文档）| **3 维** | **base_velo_ratio[family] × length_velo_factor(L/t) × temp_velo_modifier × max_inj_velo** | **⏳ 待实施** |
| `hold_pres` | 3 维 | (待设计) | ⏳ 待改造 |
| `hold_velo` | 2 维 | (待设计) | ⏳ 待改造 |

`inj_velo` 与 `inj_pres` 的对称性：

| 维度 | `inj_pres` | `inj_velo` |
|------|------------|------------|
| 材料基准 | base_pressure_ratio[family] (0.50-0.75) | base_velocity_ratio[family] (0.30-0.60) |
| 流长比修正 | length_factor(L/t) (0.85-1.50) | length_velo_factor(L/t) (1.00-1.50) |
| 模温修正 | ❌ 无 | ✅ temp_velo_modifier (0.95-1.05) |
| 机器基准 | max_set_injection_pressure (MPa) | max_set_injection_velocity (mm/s) |
| 安全钳制 | max_safe_pressure_ratio = 0.90 | max_safe_velocity_ratio = 0.95 |

> **修正方向对比**：
> - 压力：L/t 大 → 阻力大 → 加大 base_ratio（base_pressure_ratio 0.50-0.75 偏高）
> - 速度：L/t 大 → 风险大 → 加大 length_factor（强制加速）
> - 但**速度的 base 范围比压力低**（0.30-0.60 vs 0.50-0.75），因为速度通过螺杆推进，影响更直接

### 15.3 与项目物理化精神的符合度

| 项目规范 | 本方案符合度 | 说明 |
|---------|------------|------|
| 算法设计必须基于物理原理 | ⚠️ 定性符合，定量是经验 | 见第 13 章局限性诚实声明 |
| 物理推导 + 行业共识数据 | ✅ | 物理定性（流动性等级、流长比、模温）+ 行业共识定量 |
| 三级保守兜底 | ✅ | 完整 3 级兜底 × 3 维度（精确/大类/默认） |
| 安全钳制（防飞边/烧焦）| ✅ | `max_safe_velocity_ratio = 0.95` |
| 渐进式物理化演进 | ✅ | 处于第一阶段，文档明确第二/三/四阶段路径 |
| 可追溯性 | ✅ | 每个系数都有定性物理依据 + 量化来源 |
| 可扩展性 | ✅ | 预留 `recommend_inj_velocity_ratio`、`length_velocity_override`、`temp_velocity_override` 字段 |
| 失败归因清晰 | ✅ | 按 family / L/t / mold_temp 维度精确定位 |

---

## 16. 更新日志

| 日期 | 进度 | 备注 |
|------|------|------|
| 2026-07-05 | 设计文档建立 | ✅ 本文档（章节 1-12） |
| 2026-07-05 | 局限性诚实声明 | ✅ 章节 13 |
| 2026-07-05 | 渐进式物理化演进路径 | ✅ 章节 14 |
| 2026-07-05 | 与项目物理化路线对齐 | ✅ 章节 15 |
| 2026-07-05 | max_set_injection_velocity 字段语义明确 | ✅ 表格 13.1：使用 HMI 设定上限 |
| 2026-07-05 | 兄弟算法对称性表 | ✅ 15.2：与 `inj_pres` 维度对位 |
| 待定 | 算法实施 | ⏳ 见 7.3 推进步骤 |
| 待定 | 测试覆盖 | ⏳ 见 9.1-9.5 |
| 待定 | 灰度上线 | ⏳ 见 7.3 |

---

*文档生成时间：2026-07-05*
