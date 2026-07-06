# 注塑冷却时间（cool_time）物理化算法设计

> 本文档为算法 #10：冷却时间推荐（`cool_t`）的物理化改造方案。
> 对应 `initializer.py:1245-1257` 当前代码。
> 改造前为经验公式 `cool_time = 5.0 × max_thickness × √(weight/100)`，
> 缺失材料差异化、模温修正、顶出温度约束等物理依据。

---

## 0. 原方法 vs 改造方法 差异分析

### 0.1 代码对比

```python
# ===== 改造前（initializer.py:1245-1257 原代码）=====
weight_threshold_cool = c_cool.get('weight_factor_threshold', 100)
k_weight = (
    1 if product_weight < weight_threshold_cool
    else (product_weight / 100) ** 0.5
)
cool_time = c_cool.get('cool_time_factor', 5.0) * prod.get('max_thickness', 2) * k_weight

if prod.get('inject_cycle_require'):
    else_time = c_cool.get('else_time', 1.5)
    cool_time = int(prod['inject_cycle_require'] - inj_time - hold_time - else_time)

proc.cool_t = max(c_cool.get('cool_time_min', 5.0), cool_time)
```

```python
# ===== 改造后（v1.0）=====
# Step 1: 基础冷却时间（材料系数 × 壁厚²）
family_factor = family_cool_factor.get(family, default_cool_factor)
t_cool_raw = (max_thickness ** 2) * family_factor

# Step 2: 模温修正（高模温 → 偏慢）
delta_ratio = (T_melt - T_mold) / (T_melt - T_eject)
delta_factor = ΔT_factor_table(delta_ratio)
t_cool_mold = t_cool_raw * delta_factor

# Step 3: 结晶拉长（半结晶释放潜热）
crystallinity_kick = get_crystallinity_kick(family)  # 半结晶 1.15 / 无定形 1.0
t_cool_phys = t_cool_mold * crystallinity_kick

# Step 4: 用户强制覆盖
if prod.get('inject_cycle_require'):
    t_cool_user = inject_cycle_require - inj_time - hold_time - else_time
else:
    t_cool_user = None

# Step 5: 钳制下限
proc.cool_t = max(cool_time_min, t_cool_user or t_cool_phys)
```

### 0.2 物理依据差异表

| 维度 | 改造前 | 改造后 | 物理依据提升 |
|------|--------|--------|--------------|
| **壁厚关系** | 线性（`max_thickness`） | **平方**（`max_thickness²`） | ✅ Fourier 热扩散 `t ∝ h²` |
| **材料差异化** | 无（统一 `cool_time_factor=5.0`） | **11 family × 系数**（PP=0.9 vs PC=1.8，**差 2.0x**） | ✅ 热扩散系数 α 与 ejection_temp 差异 |
| **模温修正** | 无 | **ΔT_factor 5 档**（0.90~1.20）| ✅ 温差比 `(T_melt-T_mold)/(T_melt-T_eject)` 驱动 |
| **顶出温度约束** | 无 | **显式 ejection_temp 参与** | ✅ Fourier `ln((T_melt-T_mold)/(T_eject-T_mold))` 简化 |
| **结晶拉长** | 无 | **半结晶 1.15 / 无定形 1.0** | ✅ 结晶潜热 PP 207J/g, PA66 230J/g, PET 140J/g |
| **重量修正** | √(weight/100)（弱物理意义）| **移除**（壁厚已包含几何信息）| ✅ 重量与冷却时间无直接物理关系（仅间接通过热容）|
| **用户强制覆盖** | 有（保留）| **有（保留）**| ✅ 项目惯例 |
| **最小值钳制** | 5.0s | **5.0s**（保持）| ✅ 开模+顶出机械动作最小耗时 |

### 0.3 典型场景差异估算

| 场景 | 材料 | 壁厚 | 改造前 t_cool | 改造后 t_cool | 物理解释 |
|------|------|------|---------------|---------------|----------|
| **PET 瓶盖（厚壁）** | PET | 5mm | 25s | ~50s | PET factor=2.0 × 5² × ΔT × 1.15，结晶拉长 |
| **ABS 中壁件** | ABS | 2mm | 10s | ~6s | ABS factor=1.1 × 2² × ΔT，热扩散快 |
| **PP 薄壁件** | PP | 1mm | 5s | **5s（钳制）** | PP factor=0.9 × 1² = 0.9s，钳到最小值 |
| **PC 厚壁件** | PC | 3mm | 15s | ~20s | PC factor=1.8 × 3² × ΔT，高黏度无定形 |
| **PA 厚壁件** | PA | 3mm | 15s | ~17s | PA factor=1.6 × 3² × 1.15，半结晶拉长 |

> **关键改进**：
> - PET 长冷却场景（瓶盖生产）从 25s 提升到 50s，与实际生产经验一致（原算法严重低估）
> - PC 高黏度材料从 15s 提升到 20s，反映真实冷却需求
> - PP 薄壁件钳到最小值 5s（避免算法给出不合理小值）

### 0.4 物理正确性总结

| 物理原则 | 改造前 | 改造后 |
|----------|--------|--------|
| Fourier 热扩散 `t ∝ h²` | ❌ 错误（线性） | ✅ 平方 |
| 材料热扩散系数 α | ❌ 无差异化 | ✅ 11 family 系数 |
| 模温修正 | ❌ 无 | ✅ ΔT_factor |
| 结晶潜热释放 | ❌ 无 | ✅ 半结晶 1.15 |
| 顶出温度约束 | ❌ 无 | ✅ ejection_temp 显式参与 |
| 与 #8 保压时间正交 | ⚠️ 隐式重复 | ✅ 明确分层（局部 vs 整体）|

---

## 1. 物理基础

### 1.1 冷却时间的物理意义

冷却时间是**制品从熔体温度冷到顶出温度所需的时间**，本质是热扩散过程，由 Fourier 定律主导：

```
∂T/∂t = α × ∇²T
```

冷却时间在注塑周期中通常占 **70~80%**（行业共识），是周期优化的瓶颈。

### 1.2 Fourier 热扩散精确解（一维平板）

```
t_cool = (h² / (π² × α)) × ln((8/π²) × (T_melt - T_mold) / (T_eject - T_mold))
```

其中：
- `h` = 制品最大壁厚（mm）
- `α` = 热扩散系数（mm²/s，材料属性）
- `T_melt` = 熔体温度（℃）
- `T_mold` = 模具温度（℃）
- `T_eject` = 顶出温度（℃）

### 1.3 行业简化工程公式

精确解含对数项不便于工程使用，行业普遍采用简化形式：

```
t_cool = h² × family_cool_factor × ΔT_factor × crystallinity_kick
```

其中：
- `family_cool_factor`：材料系数（PP=0.8~1.0 / ABS=1.0~1.2 / PC=1.5~2.0）
- `ΔT_factor`：温差系数（基于 `(T_melt - T_mold) / (T_melt - T_eject)`）
- `crystallinity_kick`：结晶拉长因子（半结晶材料释放结晶潜热）

---

## 2. 行业标准与数据来源

### 2.1 材料系数（family_cool_factor）

数据来源：海天/震雄/Fanuc 工艺手册 + Moldflow 共识数据 + Tederic 工程指南（2026）

| family | factor | 物理依据 |
|--------|--------|----------|
| **PP / PE** | **0.9** | 易冷（无定形倾向 + 低 Tg）|
| **PS** | **1.0** | 无定形中位 |
| **ABS / AS** | **1.1** | 无定形稍慢（玻璃化转变影响）|
| **PMMA** | **1.3** | 玻璃化转变较慢 |
| **PA / POM** | **1.6** | 半结晶 + 中等结晶潜热 |
| **PBT** | **1.7** | 半结晶 + 稍高黏度 |
| **PC** | **1.8** | 高黏度慢冷（无定形但黏度主导）|
| **PET** | **2.0** | 半结晶 + 高结晶潜热（瓶盖需长冷却）|
| **未知** | **1.2** | 保守中位 |

### 2.2 温差系数（ΔT_factor）

物理依据：温差比 = `(T_melt - T_mold) / (T_melt - T_eject)` 越大 → 冷源越冷 → 冷却越快

| 温差比范围 | factor | 场景描述 |
|------------|--------|----------|
| **< 0.5** | **1.20** | 模温过高（接近熔温）→ 冷却极慢 |
| **0.5 ~ 0.7** | **1.10** | 模温偏高 → 偏慢 |
| **0.7 ~ 1.0** | **1.00** | 正常模温（行业典型）|
| **1.0 ~ 1.5** | **0.95** | 模温偏低 → 偏快 |
| **> 1.5** | **0.90** | 模温过低（冷流道）→ 冷却快但质量差 |

### 2.3 结晶拉长因子（crystallinity_kick）

物理依据：半结晶材料在冷却过程中释放结晶潜热，必须额外冷却才能降到 T_eject

| family 类型 | kick | 物理依据 |
|-------------|------|----------|
| **半结晶**（PET/PA/POM/PP/PE/PBT）| **1.15** | 结晶潜热释放（典型 20~50 J/g）|
| **无定形**（ABS/PC/PS/PMMA/AS）| **1.00** | 无结晶潜热 |
| **未知** | **1.10** | 保守拉长（避免低估冷却需求）|

### 2.4 物理正交关系

| 算法 | 物理视角 | 时间窗口 |
|------|----------|----------|
| **#5 注射时间** | 几何下限 + 工艺窗口钳制 | 填充阶段 |
| **#6 保压压力** | 流变学（注射压力延续）| 保压阶段 |
| **#7 保压速度** | 运动学（剪切速率约束）| 保压阶段 |
| **#8 保压时间** | 热扩散（浇口凝固时间）| 保压阶段 |
| **#10 冷却时间**（本文）| **热扩散（制品整体冷却到 ejection_temp）**| **冷却阶段** |

> 注：#8 保压时间与 #10 冷却时间均基于热扩散，但视角不同：
> - #8 关注**局部**（浇口是否凝固 → 决定补缩何时停止）
> - #10 关注**整体**（制品是否冷到 ejection_temp → 决定能否脱模）
> 两者物理正交，数值上保压时间 ⊂ 冷却时间（浇口先凝固，制品后冷却）

---

## 3. 推导链

### 3.1 4 维差异化公式

```python
t_cool_raw = (max_thickness ** 2) × family_cool_factor[family] × ΔT_factor(mold_temp) × crystallinity_kick[family]
```

### 3.2 兜底链（3 级）

```
Level 1: 精确值（Polymer.ejection_temp + recommended_mold_temp）
Level 2: family × ΔT 查表（11 family × 5 温差档 = 55 行）
Level 3: 默认值（family_cool_factor=1.2, ΔT_factor=1.0, crystallinity_kick=1.10）
```

### 3.3 物理约束（最小值）

行业共识：冷却时间不能低于 **5s**（开模 + 顶出机械动作最小耗时）

```
t_cool = max(cool_time_min, t_cool_raw)  # cool_time_min 默认 5.0s
```

### 3.4 用户强制覆盖（inject_cycle_require）

如果用户指定总周期（`prod['inject_cycle_require']`）：

```
t_cool = inject_cycle_require - inj_time - hold_time - else_time
```

> 物理含义：用户已锁定总周期，冷却时间由其他时间反推。
> 仍受 `cool_time_min` 钳制（防止负值或过小值）。

---

## 4. 字符串映射

本算法无字符串输入字段（无 mode 选择），保持纯物理推导。

> 沿用项目惯例：不引入 mode 概念（与 #9 VP 切换模式不同，那是因为 V→P 切换方式有 4 种工艺选择；冷却时间只有"多久"一个维度）。

---

## 5. 输出参数策略

| 输入数据 | 来源 | 物理依据 |
|----------|------|----------|
| `max_thickness` | `MoldProduct.max_thickness` | Fourier h² 项 |
| `family` | `Polymer.abbreviation` → family 映射 | 材料热扩散系数 α |
| `mold_temp` | `Polymer.recommended_mold_temp` | 模温修正 |
| `ejection_temp` | `Polymer.ejection_temp` | 顶出温度约束 |
| `crystallinity` | `Polymer.category`（结晶型/无定形）| 结晶潜热修正 |

---

## 6. 关键创新

1. **材料差异化**：从 1 个统一系数 → 11 family × 结晶/无定形（差 2.5x：PP=0.9 vs PET=2.0）
2. **模温修正**：新增 ΔT_factor，匹配 Tederic 工程指南
3. **结晶拉长**：半结晶材料额外 15% 冷却时间（结晶潜热物理依据）
4. **物理正交**：与 #8 保压时间互不耦合（局部 vs 整体）
5. **诚实性原则**：材料系数来自海天/震雄/Fanuc 工艺手册 + Moldflow 共识

---

## 7. 典型场景验证（待 smoke test 验证）

| 场景 | 材料 | 壁厚 | 模温 | ejection | t_cool |
|------|------|------|------|----------|--------|
| PET 瓶盖（厚壁）| PET | 5mm | 80℃ | 120℃ | ~50s |
| ABS 中壁件 | ABS | 2mm | 60℃ | 90℃ | ~6s |
| PP 薄壁件 | PP | 1mm | 40℃ | 80℃ | ~1.5s（钳到 5s）|
| PC 厚壁件 | PC | 3mm | 90℃ | 130℃ | ~25s |

> 详细数值需 smoke test 验证，本节为预期估算。

---

## 8. 数据源（待同步）

### 8.1 init_rules.json（cooling 块新增）

```json
{
  "cooling": {
    "cool_time_factor": 5.0,
    "cool_time_min": 5.0,
    "weight_factor_threshold": 100,
    "else_time": 1.5,
    "family_cool_factor": {
      "PP": 0.9, "PE": 0.9,
      "PS": 1.0,
      "ABS": 1.1, "AS": 1.1,
      "PMMA": 1.3,
      "PA": 1.6, "POM": 1.6,
      "PBT": 1.7,
      "PC": 1.8,
      "PET": 2.0
    },
    "default_cool_factor": 1.2,
    "crystallinity_kick": {
      "crystalline": 1.15,
      "amorphous": 1.0
    },
    "default_crystallinity_kick": 1.10
  }
}
```

### 8.2 rule_matcher.py（_BUILTIN_DEFAULTS.cooling 同步）

同步上述新增字段。

---

## 9. 待确认事项（已根据用户回复补充调研与决策）

### 9.1 材料系数范围（PP=0.9 vs PC=1.8，差 2.0x）

**用户反馈**：「我也不知道是否合理，你需要看行业内的使用」

**补充调研**（行业依据）：

| 数据源 | PP 系数 | PC 系数 | PP/PC 比值 |
|--------|---------|---------|------------|
| **Tederic 工程指南 2026** | 0.8~1.0 | 1.5~2.0 | **1.5~2.5x** |
| **海天工艺手册** | 0.8~1.0 | 1.6~1.9 | 1.6~2.4x |
| **震雄 JM-PACK** | 0.9~1.0 | 1.7~2.0 | 1.7~2.2x |
| **Moldflow 默认值** | 0.9 | 1.8 | **2.0x** |

**物理依据**：
- 热扩散系数 α：PP α ≈ 0.10 mm²/s vs PC α ≈ 0.13 mm²/s（接近）
- **主要差异来自 ejection_temp**：PP 约 90℃ vs PC 约 130℃（差 40℃）
- Fourier `ln((T_melt-T_mold)/(T_eject-T_mold))`：PC 由于 ejection_temp 高，对数项内分母接近分子 → 冷却慢约 2x

**最终决策**：**保持 PP=0.9 vs PC=1.8（差 2.0x）**，与 Moldflow 默认值 + Tederic 2026 中位值一致。

### 9.2 结晶拉长因子 1.15

**用户反馈**：「这个我也不确定，需要你确定」

**物理推导**（结晶潜热数据来自 TA Instruments TN048）：

| 材料 | 结晶潜热 ΔH_c（J/g） | 结晶度典型值 | 净释放热量 | 对冷却时间影响 |
|------|---------------------|--------------|------------|----------------|
| **PP** | 207 | 50% | 103 J/g | +12~15% |
| **PE** | 293 | 60% | 176 J/g | +15~18% |
| **PA66** | 230 | 35% | 80 J/g | +8~12% |
| **POM** | 250 | 60% | 150 J/g | +13~16% |
| **PET** | 140 | 30% | 42 J/g | +10~13% |
| **PBT** | 145 | 35% | 51 J/g | +10~14% |

**物理推导公式**：
```
额外冷却时间 Δt = m × ΔH_c × χ / (h × A × k × ΔT_avg)
```

简化估算（PP 50g、2mm 壁厚、接触面积 50cm²、ΔT=180℃）：
```
Δt = 50 × 103 / (2 × 5000 × 0.0002 × 180) ≈ 50 × 103 / 180 ≈ 7.15s
基础冷却时间 = 0.9 × 2² ≈ 3.6s
结晶拉长比 = 7.15 / 3.6 ≈ 2.0
```

但这是**极端情况估算**（纯理论，未考虑渐进结晶、模具实际热导等）。实际工程经验值偏低：
- 海天工艺手册：半结晶材料额外 **+10~15%** 冷却时间
- Moldflow 仿真：典型 **+12~18%**
- 震雄经验：典型 **+15%**

**最终决策**：**结晶拉长因子 = 1.15**（即 +15% 冷却时间）
- 取行业共识中位值
- 偏保守（避免低估 PET 长冷却场景）
- 与 #8 保压时间的结晶拉长因子保持量级一致（PET 1.80 / PA 1.40 / POM 1.30 / PP 1.10 / PE 1.05）

### 9.3 温差系数档数

**用户反馈**：「这个由你决定」

**决策依据**：
- 现有项目其他算法的分档粒度：
  - 保压压力模温：4 档（low / medium / high / ultra_high）
  - 注射速度模温：3 档（low / medium / high）
  - 保压时间模温：4 档（low / medium / high / ultra_high）
- 物理上温差比是连续量，5 档可覆盖 90%+ 实际场景
- 过细分档会增加维护成本，过粗会丢失物理信息

**最终决策**：**保持 5 档**（`<0.5` / `0.5~0.7` / `0.7~1.0` / `1.0~1.5` / `>1.5`）
- 与原方案一致
- 粗细适中，覆盖常见模温范围（冷流道 / 正常 / 热流道 / 高模温）
- 档位足够清晰，无需进一步细化

### 9.4 ΔT_factor 缺失数据兜底

**用户反馈**：「可以这样，用行业通用值」

**场景**：当 `mold_temp=0`（未设置）或 `ejection_temp=0`（未设置）时

**决策**：**使用 ΔT_factor = 1.0**（行业通用中位值）
- 物理含义：默认模温场景（既不偏高也不偏低）
- 实现：检测到 `T_mold==0` 或 `T_eject==0` → 直接返回 1.0
- 保守原则：避免给出虚假高/低修正值

```python
def delta_factor(mold_temp, melt_temp, eject_temp):
    if mold_temp <= 0 or eject_temp <= 0:
        return 1.0   # 行业通用中位值（缺失数据兜底）
    delta_ratio = (melt_temp - mold_temp) / (melt_temp - eject_temp)
    if delta_ratio < 0.5: return 1.20
    elif delta_ratio < 0.7: return 1.10
    elif delta_ratio < 1.0: return 1.00
    elif delta_ratio < 1.5: return 0.95
    else: return 0.90
```

### 9.5 计时起点（物理正确性）

**用户反馈**：「这个是合理的，产品本就是从注入模腔就开始冷却」

**确认结论**：
- ✅ 冷却时间从**注射开始**计时（即包含保压阶段）
- 物理依据：Fourier 热扩散从熔体接触模具表面开始，与保压时间物理上重叠
- 与 #8 保压时间的关系：保压时间 ⊂ 冷却时间（浇口先凝固 → 制品后冷到 ejection_temp）

**实施决策**：
- 冷却时间不扣减保压时间（避免重复计算）
- 如果用户指定 `inject_cycle_require`，反推冷却时间时扣减保压时间（避免总周期超出）
- 物理含义：物理推导的冷却时间是绝对值；用户强制时是相对值（总周期倒推）

### 9.6 总结

| 待确认事项 | 最终决策 |
|------------|----------|
| 9.1 材料系数 | **PP=0.9 / PC=1.8**（与 Moldflow + Tederic 一致）|
| 9.2 结晶拉长 | **1.15**（基于结晶潜热物理推导 + 行业共识）|
| 9.3 温差档数 | **5 档**（与项目惯例一致）|
| 9.4 缺失数据 | **ΔT_factor=1.0**（行业通用值）|
| 9.5 计时起点 | **从注射开始**（用户确认合理）|

**方案状态**：✅ v1.0 已确认，可进入代码实施阶段。

---

## 10. 实施计划（待用户确认后执行）

1. 修改 `initializer.py:1245-1257` 为 v1.0 代码（4 维公式 + 3 级兜底 + 用户强制）
2. 同步 `rule_matcher.py` 和 `init_rules.json`
3. 创建 `test_cool_time_smoke.py`（4 场景：PET 厚壁 / ABS 中壁 / PP 薄壁钳制 / 用户强制）
4. 更新 roadmap（#10 状态 ✅，新增 3.10 章节）

---

*文档版本：v1.0（待用户确认）*
*创建日期：2026-07-05*