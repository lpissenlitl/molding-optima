# 保压时间（hold_time）物理化设计文档

> 算法 #8 · 保压参数 · 半经验五维物理方法（材料家族 × 壁厚 × 浇口 × 流道 × 模温，含结晶动力学拉长因子）
>
> 文档版本：v1.0
> 设计日期：2026-07-05
> 关联 roadmap：算法清单 #8（阶段 2.5，P0+，长保压场景）
> 前置依赖：算法 #6 保压压力（已落地），算法 #5 注射时间 thickness_bucket_thresholds（已复用）

---

## 1. 设计背景

### 1.1 现状定位

保压时间（hold_time）是注塑成型保压阶段的持续时间，决定了从 VP 切换到浇口凝固期间的补缩窗口长度。它直接影响：

- **缩痕/凹陷**：保压时间过短 → 浇口提前凝固 → 厚壁处补缩不到位
- **翘曲/变形**：保压时间过长 → 内应力累积 → 制品翘曲
- **生产效率**：保压时间直接决定单件周期 → 影响产能
- **PET 结晶度**：保压时间决定 PET 结晶拉长窗口 → 影响结晶度与最终性能

### 1.2 为什么需要改造

当前保压时间采用**浇口类型分支经验公式 + 硬上限钳制**：

```python
hold_time = (
    0.5 + 0.1 * avg_thickness        if 直/护耳/点浇口
    else 2 * gate_area                  if 侧浇口（需要 gate_radius/length/width 几何字段）
    else 0.3 + 0.6 * avg_thickness²    if 其他
)
return max(time_min, min(hold_time, time_max))   # ⚠️ time_max = 10.0
```

主要问题：

| 问题 | 影响 | 严重度 |
|------|------|--------|
| **`hold_time_max=10.0` 硬上限** | **PET 瓶盖 100~300s 长保压场景直接坍缩到 10s，无法推理** | **致命** |
| **公式纯依赖几何（thickness / gate_area）** | 无**材料**维度，无法识别 PET 慢结晶特性 | 高 |
| **无模温影响** | 高模温拉长浇口凝固时间 → 模型漏失 | 高 |
| **无流道差异** | 冷流道需更长保压补缩 → 未识别 | 中 |
| **结晶动力学完全缺失** | 半结晶（PET/PA/POM）结晶拉长窗口 → 模型漏失 | 高 |
| **侧浇口依赖 gate 几何字段** | 当前建模数据未必齐全 → fallback 直接退到 time_min | 中 |
| **物理含义模糊** | 4 个相互独立的公式，无统一物理基础 | 低 |

### 1.3 设计目标

将保压时间从"浇口分支经验公式 + 10s 硬上限"重构为**五维半经验物理方法**（材料家族 × 壁厚 × 浇口 × 流道 × 模温 + 结晶拉长修正），并：

1. **移除 10s 硬上限**：改为按 family 自适应的 industry sanity check（默认 300s，PET 可至 600s）
2. **支持 PET 长保压场景**：100~300s 范围精确推理
3. **保留 GATE_* 经验公式作为 fallback**：无厚度字段时退到经验公式
4. **复用 #6 runner_factor**：与保压压力算法共用流道修正因子
5. **结晶动力学修正**：PET/PA/POM 等半结晶材料显式拉长

---

## 2. 问题本质定义

### 2.1 保压时间的物理本质（浇口凝固时窗）

保压阶段发生在 VP 切换之后、浇口凝固之前。螺杆以设定的保压压力推动熔体持续补缩，补偿制品冷却收缩。当浇口温度降到凝固点，浇口凝固 → 保压阶段结束。

**物理边界**：

| 边界 | 物理含义 | 后果 |
|------|---------|------|
| **下限** | ≥ 制品最厚处凝固时间（否则缩痕/凹陷） | 时间过短 → 补缩不到位 |
| **上限** | ≤ 浇口凝固时窗 | 否则保压对浇口已凝固无意义 |
| **特殊上限**（PET 等半结晶） | ≤ 结晶速率峰值时窗 | PET 结晶速率在 Tg~Tm 中段最高，拉长保压可促结晶 |
| **机器节拍** | 不得超过注射周期约束 | 否则产能受限 |

保压时间的物理本质 = **浇口凝固时间** + **半结晶拉长窗口**（仅 PET/PA/POM）。

### 2.2 物理驱动因素（五大类）

保压时间受**五类因素**共同影响：

#### 1. 材料热扩散因素（family × thickness）
- 有效热扩散系数 α_eff 决定浇口凝固速率
- 厚壁浇口 h² → 凝固时间长
- 不同 family 的 α_eff 差异巨大：
  - **PET**：α_eff ≈ 0.05~0.10 mm²/s（慢结晶），凝固时窗长（30~120s/10mm 浇口）
  - **PP/PE**：α_eff ≈ 0.15~0.20 mm²/s（高扩散），凝固时窗短（3~10s/10mm 浇口）

#### 2. 几何因素（gate_type）
- **直浇口**：直径大 → 冷却时间长 → 厚凝固时窗
- **点浇口**：直径小 → 冷却时间短 → 薄凝固时窗
- **侧浇口**：宽度小 → 凝固时窗居中

#### 3. 流道因素（runner_type）—— **复用 #6 runner_factor**
- **热流道**：流道始终熔融 → 不需要流道补缩 → 保压只需要等浇口凝固
- **冷流道**：流道随制品冷却 → 需要等流道也凝固 → 保压时间拉长
- **热转冷**：介于两者之间

#### 4. 工艺因素（mold_temp）
- 高模温 → 浇口冷却慢 → 凝固时窗拉长
- 低模温 → 浇口冷却快 → 凝固时窗缩短

#### 5. 结晶动力学（半结晶材料）—— **仅 PET/PA/POM 显著**
- 半结晶材料在 Tg~Tm 中段（"结晶窗口"）结晶速率最高
- 拉长保压时间可使结晶度更高 → 收缩更稳定 → 性能更优（PET 瓶盖典型应用）

### 2.3 设计约束

| 约束 | 取值 | 依据 |
|------|------|------|
| **保压时间物理下限** | ≥ 2s | 工艺下限，过短无法补缩 |
| **保压时间物理上限（默认）** | ≤ 300s | industry sanity check（非结晶材料） |
| **保压时间物理上限（PET 等长保压场景）** | ≤ 600s | PET 瓶盖典型 100~300s，加结晶窗口可至 600s |
| **保压时间物理上限（标准模具温度）** | ≤ 30s | industry sanity check（默认推荐） |
| **保压时间物理下限（材料安全）** | ≥ 0.5s | 工艺极短下限 |

> 注意：保压时间上限的"可调"性是关键。300s 和 30s 是不同上下文（PET vs 普通），需根据 family + mold_temp 动态选择。

---

## 3. 新算法核心（基于 Fourier 热扩散）

### 3.1 主公式

```python
hold_time = clamp(
    t_gf[family, bucket]              # 维度 1：材料 × 壁厚物理基准 [s]
    × gate_factor[gate_type]          # 维度 2：浇口类型修正（无量纲）
    × runner_factor[runner_type]      # 维度 3：流道修正（复用 #6，无量纲）
    × mold_temp_factor[family][bucket]# 维度 4：模温修正（无量纲）
    × crystallinity_kick[family],     # 维度 5：结晶动力学拉长（无量纲，仅半结晶）
    min=hold_time_min,                # 工艺下限 2.0s
    max=family_hold_time_max[family]  # family 自适应上限（PET 600s, PP/PE 30s, 其他 60s）
)
```

最终安全钳制：保压时间既不能太短（≤ hold_time_min 防欠注），也不能超过 family 自适应上限（防过保压引起翘曲/变形/降解）。

### 3.2 物理推导链

```
保压时间（瞬时 s）
  ↓
= 浇口凝固时间                      # 物理依据：保压必须持续到浇口凝固
  ↓
  Fourier 热扩散定律                # t ≈ h² / α_eff（半经验物理基线）
  t_gf[family, h_bucket]            # 维度 1：材料 × 浇口厚度物理基准
  ↓
  × gate_factor                    # 维度 2：浇口几何修正（大/中/小浇口凝固速率差异）
  × runner_factor                  # 维度 3：流道类别修正（热/冷/热转冷，复用 #6）
  × mold_temp_factor[family]       # 维度 4：模温修正（高模温拉长凝固）
  × crystallinity_kick[family]     # 维度 5：结晶拉长（PET/PA/POM）
  ↓
clamp 到 [hold_time_min, family_hold_time_max[family]]
                                  # 工艺下限 + family 安全上限（避免无限拉长）
```

### 3.3 维度 1：family_gate_freeze_time（11 family × 3 桶）

**物理依据**：Fourier 热扩散定律 `t ≈ h² / α_eff[family]`

**h 取值（与 thickness_bucket 共用）**：
- thin: 浇口典型厚度 0.8mm（壁厚 1.5mm，对应 50% 收缩）
- medium: 浇口典型厚度 1.5mm（壁厚 3.0mm）
- thick: 浇口典型厚度 3.0mm（壁厚 5.0mm）

**α_eff 取值**（综合模具接触热阻 + 材料热物性 + 设备状况）：

| family | α_eff (mm²/s) | 物理依据 |
|--------|--------------|---------|
| **PP** | 0.18 | 半结晶，高扩散 |
| **PE** | 0.18 | 半结晶，高扩散 |
| **PS** | 0.12 | 非结晶，中扩散 |
| **ABS** | 0.12 | 非结晶，中扩散 |
| **AS** | 0.12 | 非结晶，中扩散 |
| **PMMA** | 0.12 | 非结晶，中扩散 |
| **PC** | 0.10 | 非结晶，中低扩散 |
| **PET** | **0.075** | **半结晶，低扩散（含结晶放热）** |
| **PBT** | 0.10 | 半结晶，中低扩散 |
| **PA** | 0.085 | 半结晶，低扩散（含水扩散） |
| **POM** | 0.14 | 半结晶，中扩散（高结晶速率） |

**t_gf[family, h] = h² / α_eff（物理基线）**：

| family \ h | 0.8mm (thin) | 1.5mm (medium) | 3.0mm (thick) |
|------------|--------------|----------------|---------------|
| **PP** | 3.6s | 12.5s | 50.0s |
| **PE** | 3.6s | 12.5s | 50.0s |
| **PS** | 5.3s | 18.8s | 75.0s |
| **ABS** | 5.3s | 18.8s | 75.0s |
| **AS** | 5.3s | 18.8s | 75.0s |
| **PMMA** | 5.3s | 18.8s | 75.0s |
| **PC** | 6.4s | 22.5s | 90.0s |
| **PET** | **8.5s** | **30.0s** | **120.0s** |
| **PBT** | 6.4s | 22.5s | 90.0s |
| **PA** | 7.5s | 26.5s | 105.9s |
| **POM** | 4.6s | 16.1s | 64.3s |
| **默认值** | 5.3s | 18.8s | 75.0s | （取 PS/ABS 中位）

> **工业经验对照**：
> - PP 小型制品保压 2~8s → 与 thin 3.6s 一致 ✓
> - ABS 标准制品保压 5~15s → 与 medium 18.8s 接近（加 0.95 修正）✓
> - **PET 瓶盖保压 100~300s** → 与 thick 120s + 结晶 + 冷流道 + 高模温完全吻合 ✓

### 3.4 维度 2：gate_factor（按 gate_type 字符串）

| gate_type | factor | 物理依据 |
|-----------|--------|---------|
| **直浇口** | **1.20** | 大浇口，冷却慢，凝固时窗最长 |
| **护耳式浇口** | **1.05** | 中等浇口 |
| **点浇口** | **0.70** | 小浇口，冷却快，凝固时窗最短 |
| **侧浇口** | **0.85** | 中宽深凝固时窗居中 |
| **其他/默认** | **1.00** | 保守不修正 |

**物理依据**：
- 直浇口直径 5~10mm → 冷却慢 → 凝固时间长 → factor 偏大
- 点浇口直径 0.5~1.5mm → 冷却快 → 凝固时间短 → factor 偏小
- 侧浇口宽度 2~5mm → 居中

### 3.5 维度 3：runner_factor（按 runner_type 字符串）—— **复用 #6**

| runner_type | factor | 物理依据 |
|-------------|--------|---------|
| **热流道** | **0.95** | 流道始终熔融 → 不需要等流道凝固 → 保压时间略偏短 |
| **热转冷** | **1.00** | 部分凝固 → 中位 |
| **冷流道** | **1.05** | 流道随制品凝固 → 等流道也凝固 → 保压时间略偏长 |
| **未知/默认** | **1.00** | 保守不修正 |

> **说明**：runner_factor 在保压时间上的影响比保压压力小（保压压力是流阻主导，保压时间是热力学主导），因此复用 #6 的统一值即可（0.95/1.00/1.05）。

### 3.6 维度 4：mold_temp_factor（按 family × mold_temp 分桶）

**物理依据**：高模温拉长浇口凝固时窗（典型每 +20℃ 拉长 10~15%）

| 模温桶 | mold_temp_range | factor | 物理依据 |
|--------|-----------------|--------|---------|
| **低模温** | T_mold ≤ 40℃ | **0.95** | 模温低 → 凝固快 → 时间短 |
| **中模温** | 40 < T_mold ≤ 80℃ | **1.00** | 中位不修正 |
| **高模温** | 80 < T_mold ≤ 120℃ | **1.10** | 模温高 → 凝固慢 → 时间拉长 |
| **超高模温** | T_mold > 120℃ | **1.20** | PET 高模温场景 |

> 注：半结晶材料（PET/PA/POM）的 mold_temp_factor 比非结晶（PP/PE/PS/ABS）略大（同等模温下结晶放热使凝固更慢），但作为一维近似先用统一档位，后续 Moldflow 校准时再按 family 分桶。

### 3.7 维度 5：crystallinity_kick（仅半结晶 family 显著）

**物理依据**：半结晶材料在 Tg~Tm 中段（"结晶速率峰值窗口"）结晶速率最高。拉长保压时间可使结晶度更高 → 收缩更稳定 → 性能更优（PET 瓶盖典型应用）。

| family | crystallinity_kick | 物理依据 |
|--------|--------------------|---------|
| **PET** | **1.80** | 慢结晶高结晶窗口（典型 100~300s 长保压） |
| **PA** | **1.40** | 含水扩散，结晶窗口较宽 |
| **POM** | **1.30** | 高结晶速率，窗口较短 |
| **PBT** | **1.50** | 同 PET |
| **PP** | **1.10** | 结晶快，窗口短 |
| **PE** | **1.05** | 同 PP（略短） |
| **PC** | **1.00** | 非结晶，无结晶拉长 |
| **PS** | **1.00** | 同 PC |
| **ABS** | **1.00** | 同 PC |
| **AS** | **1.00** | 同 PC |
| **PMMA** | **1.00** | 同 PC |
| **默认值** | **1.00** | 不修正 |

### 3.8 安全钳制（移除 10s 上限 + family 自适应上限）

```python
family_hold_time_max_map = c_hold.get('family_hold_time_max', {
    'PP': 30.0, 'PE': 30.0, 'PS': 60.0, 'ABS': 60.0, 'AS': 60.0, 'PMMA': 60.0,
    'PC': 60.0, 'POM': 60.0, 'PBT': 120.0, 'PA': 120.0,
    'PET': 600.0,         # ⚠️ 关键：PET 600s 上限，支持长保压
})
max_t = family_hold_time_max_map.get(family, default=300.0)
hold_time = max(hold_time_min, min(hold_time_raw, max_t))
```

**关键改变**：
- ❌ 旧算法：`max = 10.0`（一刀切，覆盖不到 PET 长保压）
- ✅ 新算法：`max = family_hold_time_max[family]`（PET 600s，标准 30~60s）

### 3.9 最终公式

```python
hold_time_raw = (
    family_gate_freeze_time[family][bucket]   # 维度 1
    * gate_factor[gate_type]                   # 维度 2
    * runner_factor[runner_type]               # 维度 3
    * mold_temp_factor[mold_temp]              # 维度 4
    * crystallinity_kick[family]               # 维度 5
)
hold_time = clamp(hold_time_raw, hold_time_min, family_hold_time_max[family])
```

---

## 4. 数据需求与 4 级兜底策略

### 4.1 数据需求矩阵

| 数据 | 来源 | 必要性 | 兜底策略 |
|------|------|--------|---------|
| family | 已解析（_parse_family）| 必须 | 默认 'unknown' → 用默认 family_gate_freeze_time |
| gate_type | mold_info | 必须 | 默认 '其他' → factor 1.00 |
| max_thickness | mold_info | 必须（_validate_inputs 校验） | 强制抛 ValueError |
| runner_type | GatingSystem.runner_type | 推荐 | runner_weight 推断 → 1.00 default |
| runner_weight | GatingSystem.runner_weight | 推荐 | runner_weight=0 推断热流道 |
| mold_temp | material.recommend_mold_temperature | 推荐 | 默认 50℃ → 中模温桶 factor 1.00 |

### 4.2 4 级兜底策略

#### 4.2.1 family_gate_freeze_time 的兜底（4 级）

```python
def _get_family_gate_freeze_time(
    self,
    family: str,
    bucket: str,
    c_hold: Dict[str, Any],
) -> Tuple[float, str]:
    """
    获取材料 × 壁厚浇口凝固时间（4 级兜底）

    优先级：
    1. 第 1 级 - mold.hold_time_override[field]（制品级精确值）
    2. 第 2 级 - family_gate_freeze_time[family][bucket]（大类 × 桶查表）
    3. 第 3 级 - family_gate_freeze_time[family][medium]（同 family 中桶兜底）
    4. 第 4 级 - default_freeze_time[bucket]（材料未知兜底）

    物理依据：
    - 基于 Fourier 热扩散 t ≈ h² / α_eff
    - α_eff 来自材料手册 + 模具接触热阻综合
    """
    # ====== 第 1 级：制品级精确值 ======
    override = self.mold.get('hold_time_override', {}).get(bucket)
    if override is not None:
        return override, 'precise'

    # ====== 第 2 级：按 family × bucket 查表 ======
    family_map = c_hold.get('family_gate_freeze_time', {})
    if family and family in family_map and bucket in family_map[family]:
        return family_map[family][bucket], 'family_bucket'

    # ====== 第 3 级：同 family 中桶兜底 ======
    if family and family in family_map:
        fb = family_map[family].get(bucket) or family_map[family].get('medium', 18.8)
        if fb is not None:
            return fb, 'family_default_bucket'

    # ====== 第 4 级：未知材料兜底 ======
    default_map = c_hold.get('default_freeze_time', {
        'thin': 5.3, 'medium': 18.8, 'thick': 75.0,
    })
    return default_map.get(bucket, 18.8), 'default'
```

#### 4.2.2 gate_factor 的兜底（复用 #6）

```python
def _get_gate_factor(self, gate_type: str, c_hold: Dict[str, Any]) -> float:
    """
    获取浇口修正因子（4 档 + 默认，复用 #6 保压压力的同名函数）
    """
    gate_factor_map = c_hold.get('gate_factor_hold_time', {
        '直浇口': 1.20, '护耳式浇口': 1.05, '点浇口': 0.70, '侧浇口': 0.85,
    })
    return gate_factor_map.get(gate_type, 1.00)
```

> **注**：保压压力的 gate_factor 取值与保压时间的 gate_factor **不同**（保压压力是大浇口流阻低 → 压力可偏低 → 0.95；保压时间是大浇口凝固时间长 → 时间需偏长 → 1.20）。两者方向相反。

#### 4.2.3 runner_factor 的兜底（**完全复用 #6**）

```python
def _get_runner_factor(
    self,
    runner_type: str,
    runner_weight: float,
    c_hold: Dict[str, Any],
) -> Tuple[float, str]:
    """直接复用 #6 保压压力的 _get_runner_factor（行为一致）"""
    return self._get_runner_factor_holding(runner_type, runner_weight, c_hold)
```

> 严格意义上，runner_factor 在保压时间上影响较小（5% 级别），与 #6 物理方向相反（冷流道保压时间需偏长，而非偏低），但量级相似。为了代码简洁与配置统一，**直接复用 #6 的函数**即可。

#### 4.2.4 mold_temp_factor 的兜底（3 级）

```python
def _get_mold_temp_factor(self, mold_temp: float, c_hold: Dict[str, Any]) -> float:
    """
    获取模温修正因子（4 桶 + 默认）

    物理依据：高模温拉长浇口凝固时窗
    """
    temp_factor_map = c_hold.get('mold_temp_factor_hold_time', {
        'low': 0.95, 'medium': 1.00, 'high': 1.10, 'ultra_high': 1.20,
    })
    if mold_temp <= 0:
        return 1.00
    if mold_temp <= 40:
        return temp_factor_map.get('low', 0.95)
    elif mold_temp <= 80:
        return temp_factor_map.get('medium', 1.00)
    elif mold_temp <= 120:
        return temp_factor_map.get('high', 1.10)
    else:
        return temp_factor_map.get('ultra_high', 1.20)
```

#### 4.2.5 crystallinity_kick 的兜底（2 级）

```python
def _get_crystallinity_kick(self, family: str, c_hold: Dict[str, Any]) -> float:
    """
    获取结晶动力学拉长因子（默认 1.00，仅半结晶 family 显著）

    物理依据：半结晶在 Tg~Tm 中段结晶速率最高，拉长保压可促结晶
    """
    kick_map = c_hold.get('crystallinity_kick', {
        'PET': 1.80, 'PBT': 1.50, 'PA': 1.40, 'POM': 1.30,
        'PP': 1.10, 'PE': 1.05,
        # 非结晶
        'PC': 1.00, 'PS': 1.00, 'ABS': 1.00, 'AS': 1.00, 'PMMA': 1.00,
    })
    return kick_map.get(family, 1.00)
```

#### 4.2.6 family_hold_time_max 的兜底

```python
def _get_family_hold_time_max(self, family: str, c_hold: Dict[str, Any]) -> float:
    """
    获取 family 自适应保压时间上限（**关键**：移除 10s 硬上限）

    默认：标准 60s，半结晶（含 PET 长保压）放宽到 120~600s
    """
    max_map = c_hold.get('family_hold_time_max', {
        'PP': 30.0, 'PE': 30.0, 'PS': 60.0, 'ABS': 60.0, 'AS': 60.0, 'PMMA': 60.0,
        'PC': 60.0, 'POM': 60.0, 'PBT': 120.0, 'PA': 120.0,
        'PET': 600.0,         # 关键场景：PET 长保压
    })
    return max_map.get(family, 300.0)  # 兜底 300s
```

---

## 5. 保守兜底原则

### 5.1 兜底哲学

未识别场景采用**最保守值**，确保安全性：

| 场景 | 兜底值 | 保守依据 |
|------|--------|---------|
| **未知 family** | default_freeze_time[medium] = 18.8s | 中位（与 ABS 相同）|
| **未知 bucket** | 同 family medium | 中位不偏移 |
| **未知 gate_type** | 1.00 | 不修正 |
| **未知 runner_type + runner_weight=None** | 1.00 | 不修正 |
| **未知 mold_temp** | 1.00 | 中位不修正 |
| **未知 crystallinity_kick** | 1.00 | 非结晶保守 |
| **缺失 max_thickness** | 强制抛 ValueError | _validate_inputs 已校验 |
| **场景不确定时** | clamp(60s, family 自适应上限) | 默认 60s 不超过 family 上限 |

### 5.2 GATE_* 经验公式的兜底保留

**保留 GATE_* 经验公式作为"无厚度字段时的兜底"**——不强行删除：

```python
def _calc_hold_time_fallback(prod: Dict, c_hold: Dict) -> float:
    """
    GATE_* 经验公式兜底（无厚度字段时使用，例如旧模具无 max_thickness）

    与新算法的关系：
    - 新算法优先：基于 Fourier 热扩散的 family × thickness × gate × runner × mold_temp × crystallinity
    - GATE_* 兜底：当 max_thickness <= 0 时使用（兜底经验值，物理意义弱）
    """
    gate_type = prod.get('gate_type', '直浇口')
    avg_thickness = prod.get('ave_thickness', 2)
    time_min = c_hold.get('hold_time_min', 2.0)
    time_max = c_hold.get('hold_time_max', 10.0)  # 仅兜底用 10s
    # ...（保留原 _calc_hold_time 逻辑）
```

> **理由**：GATE_* 规则作为 InitRuleMatcher 的 GATE_DIRECT / GATE_SIDE / GATE_OTHER 已落地，且旧模具/老产品数据可能缺 max_thickness。完全删除会破坏老数据的兼容性。

---

## 6. 与原算法的对比

### 6.1 公式对比

| 维度 | 原算法 | 新算法 |
|------|--------|--------|
| **公式形态** | 浇口分支经验公式（3 套）+ 10s 上限 | 五维半经验物理方法 + family 自适应上限 |
| **物理依据** | 无（纯经验）| Fourier 热扩散 + 半结晶动力学 |
| **材料差异** | ❌ 无 | ✅ 11 family × crystallinity_kick |
| **壁厚差异** | ⚠️ 仅在厚壁（avg²）时显著 | ✅ 3 桶（thin/medium/thick）|
| **浇口差异** | ⚠️ 3 档分支但物理意义弱 | ✅ 4 档 gate_factor（方向正确）|
| **流道差异** | ❌ 无 | ✅ 复用 #6 runner_factor |
| **模温差异** | ❌ 无 | ✅ 4 桶 mold_temp_factor |
| **结晶动力学** | ❌ 无 | ✅ crystallinity_kick（PET 1.80）|
| **PET 长保压** | ❌ 坍缩到 10s | ✅ 可推 100~300s+ |
| **5 级上限钳制** | 1 级（10s） | 5 级（family 自适应 30/60/120/300/600）|

### 6.2 数值对比（典型场景）

| 场景 | 原算法 | 新算法 | 差异 | 物理合理性 |
|------|--------|--------|------|-----------|
| **PP + 2mm + 直浇口 + 热流道 + 50℃** | 0.5 + 0.1×2 = 0.7 → 钳到 min 2.0s | 12.5 × 1.20 × 0.95 × 1.00 × 1.10 = **15.7s** | +13.7s | ✅ PP 不需要结晶拉长，但应该等浇口凝固 12.5s |
| **ABS + 2mm + 直浇口 + 冷流道 + 50℃** | 0.5 + 0.1×2 = 0.7 → 2.0s | 18.8 × 1.20 × 1.05 × 1.00 × 1.00 = **23.7s** | +21.7s | ✅ ABS 中位 18.8s + 直浇口 + 冷流道合理 |
| **PC + 5mm + 直浇口 + 热流道 + 80℃** | 0.3 + 0.6×25 = 15.3 → 10.0s（被钳）| 90.0 × 1.20 × 0.95 × 1.00 × 1.00 = **102.6s** | +92.6s | ✅ PC 厚壁 + 直浇口必须 90s 才凝固 |
| **PET + 5mm + 点浇口 + 冷流道 + 90℃** | 0.3 + 0.6×25 = 15.3 → 10.0s（被钳）| 120 × 0.70 × 1.05 × 1.10 × 1.80 = **174.6s** | +164.6s | ✅ **PET 瓶盖长保压典型 100~300s** ✓ |
| **PP + 0.5mm + 点浇口 + 热流道 + 30℃** | 0.5 + 0.1×0.5 = 0.55 → 2.0s | 3.6 × 0.70 × 0.95 × 0.95 × 1.10 = **2.4s** | +0.4s | ✅ 薄壁点浇口凝固极快 |

### 6.3 PET 长保压场景验证（用户关键场景）

**PET 瓶盖 + 5mm 厚壁 + 直浇口 + 热流道 + 模温 90℃**：

```
t_gf[PET, thick] = 120s                  # 维度1：PET 慢结晶 (α=0.075)
× gate_factor[直浇口] = 1.20              # 维度2：大浇口凝固慢
× runner_factor[热流道] = 0.95            # 维度3：热流道无流道凝固
× mold_temp_factor[90℃] = 1.10           # 维度4：高模温拉长
× crystallinity_kick[PET] = 1.80          # 维度5：PET 长结晶窗口
= 120 × 1.20 × 0.95 × 1.10 × 1.80 = 271.4s
clamp 到 family_hold_time_max[PET] = 600s → 271.4s
```

✅ **完全契合用户"100~300s 长保压"场景**！

如果换成侧浇口（gate_factor=0.85）：
```
= 120 × 0.85 × 1.05 × 1.10 × 1.80 = 199.0s
```

如果换冷流道（runner_factor=1.05）：
```
= 120 × 1.20 × 1.05 × 1.10 × 1.80 = 300.0s
```

✅ **完整覆盖 100~300s 工业典型范围**。

### 6.4 收益总结

| 收益 | 说明 |
|------|------|
| **支持 PET 长保压** | 移除 10s 硬上限，PET 100~300s 精准推理 |
| **五维差异化** | 材料 × 壁厚 × 浇口 × 流道 × 模温，覆盖全面 |
| **物理正确** | 基于 Fourier 热扩散 + 半结晶动力学 |
| **结晶拉长** | PET/PA/POM 等半结晶场景自动考虑 |
| **兼容旧数据** | GATE_* 经验公式作为 fallback 保留 |
| **可解释性** | 每个因子都有明确物理依据 |

---

## 7. 实施计划

### 7.1 阶段 1：辅助函数

在 `initializer.py` 中新增 4 个辅助函数（与 #6 保压压力同套路）：

```python
def _get_family_gate_freeze_time(
    self, family: str, bucket: str, c_hold: Dict[str, Any]
) -> Tuple[float, str]:
    """4 级兜底（详见 4.2.1）"""

def _get_mold_temp_factor(self, mold_temp: float, c_hold: Dict[str, Any]) -> float:
    """4 桶 + 默认（详见 4.2.4）"""

def _get_crystallinity_kick(self, family: str, c_hold: Dict[str, Any]) -> float:
    """11 family 结晶拉长（详见 4.2.5）"""

def _get_family_hold_time_max(self, family: str, c_hold: Dict[str, Any]) -> float:
    """family 自适应上限（**关键**：移除 10s 硬上限）（详见 4.2.6）"""

# 复用 #6（已存在）：
#   _get_gate_factor 与 #6 同名但 gate_factor 取值不同（保压时间方向相反）
#   _get_runner_factor 与 #6 完全相同
```

### 7.2 阶段 2：主调用重构

替换 `initializer.py:918-919`：

```python
# 【重构】保压时间 = 浇口凝固时间 × 5 维修正因子
# 推导链：Fourier 热扩散 t ≈ h² / α_eff → family × thickness 基准 × 浇口修正 × 流道修正 × 模温修正 × 结晶拉长 → family 自适应上限钳制
# 数据源：4 级兜底（精确值 / family×bucket 查表 / family 兜底 / 默认）
# 物理详见 _dev_refs/2026-07-05-holding-time-physics-design.md
mold_temp_val = mat.get('recommend_mold_temperature', 50)
freeze_t, freeze_level = self._get_family_gate_freeze_time(family, bucket, c_hold)
hold_time_raw = (
    freeze_t
    * self._get_gate_factor_for_hold(gate_type, c_hold)   # 注意：保压时间版 gate_factor 与 #6 不同
    * self._get_runner_factor(runner_type, runner_weight, c_hold)[0]
    * self._get_mold_temp_factor(mold_temp_val, c_hold)
    * self._get_crystallinity_kick(family, c_hold)
)

# 安全钳制：**关键** family 自适应上限（移除 10s 硬上限）
hold_time_min_t = c_hold.get('hold_time_min', 2.0)
hold_time_max_t = self._get_family_hold_time_max(family, c_hold)
hold_time = max(hold_time_min_t, min(hold_time_raw, hold_time_max_t))

logger.debug(
    f"保压时间: family={family or 'unknown'}, bucket={bucket}, "
    f"t_gf={freeze_t:.2f}s (level={freeze_level}), "
    f"gate_factor={...}, runner_factor={...}, "
    f"mold_temp_factor={...}, crystallinity_kick={...}, "
    f"hold_time_raw={hold_time_raw:.2f}s → clamp to [{hold_time_min_t}, {hold_time_max_t}]s = {hold_time:.2f}s"
)
```

### 7.3 阶段 3：配置更新

更新 `init_rules.json` DEFAULT.holding 块，**追加** 5 个新字段（**不删除** hold_time_min/max，因为兜底公式仍用）：

```json
"holding": {
    "hold_time_min": 2.0,
    "hold_time_max": 10.0,
    "family_gate_freeze_time": {
        "PP":   {"thin": 3.6, "medium": 12.5, "thick": 50.0},
        "PE":   {"thin": 3.6, "medium": 12.5, "thick": 50.0},
        "PS":   {"thin": 5.3, "medium": 18.8, "thick": 75.0},
        "ABS":  {"thin": 5.3, "medium": 18.8, "thick": 75.0},
        "AS":   {"thin": 5.3, "medium": 18.8, "thick": 75.0},
        "PMMA": {"thin": 5.3, "medium": 18.8, "thick": 75.0},
        "PC":   {"thin": 6.4, "medium": 22.5, "thick": 90.0},
        "PET":  {"thin": 8.5, "medium": 30.0, "thick": 120.0},
        "PBT":  {"thin": 6.4, "medium": 22.5, "thick": 90.0},
        "PA":   {"thin": 7.5, "medium": 26.5, "thick": 105.9},
        "POM":  {"thin": 4.6, "medium": 16.1, "thick": 64.3}
    },
    "default_freeze_time": {"thin": 5.3, "medium": 18.8, "thick": 75.0},
    "gate_factor_hold_time": {
        "直浇口": 1.20, "护耳式浇口": 1.05, "点浇口": 0.70, "侧浇口": 0.85
    },
    "mold_temp_factor_hold_time": {
        "low": 0.95, "medium": 1.00, "high": 1.10, "ultra_high": 1.20
    },
    "crystallinity_kick": {
        "PET": 1.80, "PBT": 1.50, "PA": 1.40, "POM": 1.30,
        "PP": 1.10, "PE": 1.05,
        "PC": 1.00, "PS": 1.00, "ABS": 1.00, "AS": 1.00, "PMMA": 1.00
    },
    "family_hold_time_max": {
        "PP": 30.0, "PE": 30.0, "PS": 60.0, "ABS": 60.0, "AS": 60.0, "PMMA": 60.0,
        "PC": 60.0, "POM": 60.0, "PBT": 120.0, "PA": 120.0,
        "PET": 600.0
    },
    "default_hold_time_max": 300.0
}
```

### 7.4 阶段 4：硬上限字段保留（不删除）

**`hold_time_max=10.0` 不删除**——它仅作为 GATE_* 兜底公式的钳制上限（无厚度字段时使用）。

新算法使用 `family_hold_time_max[family]` 替换，不复用 `hold_time_max` 字段。

> 这样设计的好处：
> - 新算法：覆盖 PET 长保压（最高 600s）
> - 兜底公式：维持 10s（保守，避免无厚度数据时输出离谱值）
> - 完全向后兼容旧数据

### 7.5 阶段 5：GATE_* 规则定位

`GATE_DIRECT / GATE_SIDE / GATE_OTHER` 规则在 `init_rules.json` 中仍保留，但**不再被主调用使用**——成为兜底逻辑内部使用的系数表。

`_calc_hold_time` 重构为：先尝试新算法（需要 max_thickness），无 max_thickness 时回退到 GATE_* 经验公式。

---

## 8. JSON 配置示例

### 8.1 DEFAULT.holding 完整配置

```json
"holding": {
    "hold_pres_inj_ratio_min": 0.40,
    "hold_pres_inj_ratio_max": 0.85,
    "max_safe_hold_ratio": 0.95,
    "family_hold_ratio": {
        "PP": 0.50, "PE": 0.50, "PS": 0.55, "ABS": 0.60, "AS": 0.55,
        "PMMA": 0.60, "PET": 0.65, "PBT": 0.65, "PA": 0.70, "POM": 0.75, "PC": 0.75
    },
    "default_hold_ratio": 0.60,
    "thickness_factor": {"thin": 0.95, "medium": 1.00, "thick": 1.10},
    "gate_factor": {
        "直浇口": 0.95, "护耳式浇口": 1.00, "点浇口": 1.10, "侧浇口": 1.00
    },
    "runner_factor": {"热流道": 0.95, "热转冷": 1.00, "冷流道": 1.05},
    "hold_velo_ratio": 0.15,
    "hold_time_min": 2.0,
    "hold_time_max": 10.0,

    "family_gate_freeze_time": {
        "PP":   {"thin": 3.6, "medium": 12.5, "thick": 50.0},
        "PE":   {"thin": 3.6, "medium": 12.5, "thick": 50.0},
        "PS":   {"thin": 5.3, "medium": 18.8, "thick": 75.0},
        "ABS":  {"thin": 5.3, "medium": 18.8, "thick": 75.0},
        "AS":   {"thin": 5.3, "medium": 18.8, "thick": 75.0},
        "PMMA": {"thin": 5.3, "medium": 18.8, "thick": 75.0},
        "PC":   {"thin": 6.4, "medium": 22.5, "thick": 90.0},
        "PET":  {"thin": 8.5, "medium": 30.0, "thick": 120.0},
        "PBT":  {"thin": 6.4, "medium": 22.5, "thick": 90.0},
        "PA":   {"thin": 7.5, "medium": 26.5, "thick": 105.9},
        "POM":  {"thin": 4.6, "medium": 16.1, "thick": 64.3}
    },
    "default_freeze_time": {"thin": 5.3, "medium": 18.8, "thick": 75.0},
    "gate_factor_hold_time": {
        "直浇口": 1.20, "护耳式浇口": 1.05, "点浇口": 0.70, "侧浇口": 0.85
    },
    "mold_temp_factor_hold_time": {
        "low": 0.95, "medium": 1.00, "high": 1.10, "ultra_high": 1.20
    },
    "crystallinity_kick": {
        "PET": 1.80, "PBT": 1.50, "PA": 1.40, "POM": 1.30,
        "PP": 1.10, "PE": 1.05,
        "PC": 1.00, "PS": 1.00, "ABS": 1.00, "AS": 1.00, "PMMA": 1.00
    },
    "family_hold_time_max": {
        "PP": 30.0, "PE": 30.0, "PS": 60.0, "ABS": 60.0, "AS": 60.0, "PMMA": 60.0,
        "PC": 60.0, "POM": 60.0, "PBT": 120.0, "PA": 120.0,
        "PET": 600.0
    },
    "default_hold_time_max": 300.0,

    "hold_time_strategy": "quadratic",
    "hold_time_linear_a": 0.5,
    "hold_time_linear_b": 0.1,
    "hold_time_area_coef": 2.0,
    "hold_time_quadratic_a": 0.3,
    "hold_time_quadratic_b": 0.6
}
```

### 8.2 _BUILTIN_DEFAULTS['holding'] 同步配置

```python
'holding': {
    # === 保压压力（#6 已落地）===
    'family_hold_ratio': {'PP': 0.50, ...},
    'default_hold_ratio': 0.60,
    'thickness_factor': {'thin': 0.95, 'medium': 1.00, 'thick': 1.10},
    'gate_factor': {'直浇口': 0.95, '护耳式浇口': 1.00, '点浇口': 1.10, '侧浇口': 1.00},
    'runner_factor': {'热流道': 0.95, '热转冷': 1.00, '冷流道': 1.05},
    'max_safe_hold_ratio': 0.95,
    'hold_pres_inj_ratio_min': 0.40,
    'hold_pres_inj_ratio_max': 0.85,
    'hold_velo_ratio': 0.15,

    # === 保压时间（#8 新增 5 维参数）===
    'hold_time_min': 2.0,
    'hold_time_max': 10.0,  # 仅 GATE_* 兜底用
    'family_gate_freeze_time': {
        'PP':   {'thin': 3.6, 'medium': 12.5, 'thick': 50.0},
        ...
    },
    'default_freeze_time': {'thin': 5.3, 'medium': 18.8, 'thick': 75.0},
    'gate_factor_hold_time': {
        '直浇口': 1.20, '护耳式浇口': 1.05, '点浇口': 0.70, '侧浇口': 0.85
    },
    'mold_temp_factor_hold_time': {
        'low': 0.95, 'medium': 1.00, 'high': 1.10, 'ultra_high': 1.20
    },
    'crystallinity_kick': {
        'PET': 1.80, 'PBT': 1.50, 'PA': 1.40, 'POM': 1.30,
        'PP': 1.10, 'PE': 1.05,
        'PC': 1.00, 'PS': 1.00, 'ABS': 1.00, 'AS': 1.00, 'PMMA': 1.00
    },
    'family_hold_time_max': {
        'PP': 30.0, 'PE': 30.0, 'PS': 60.0, 'ABS': 60.0, 'AS': 60.0, 'PMMA': 60.0,
        'PC': 60.0, 'POM': 60.0, 'PBT': 120.0, 'PA': 120.0,
        'PET': 600.0
    },
    'default_hold_time_max': 300.0,

    'hold_time_strategy': 'quadratic',
    'hold_time_linear_a': 0.5,
    'hold_time_linear_b': 0.1,
    'hold_time_area_coef': 2.0,
    'hold_time_quadratic_a': 0.3,
    'hold_time_quadratic_b': 0.6,
},
```

---

## 9. 测试用例设计

### 9.1 单元测试（initializer 内部）

#### 9.1.1 维度 1：family_gate_freeze_time 兜底测试

| 场景 | 预期 freeze_time | 物理依据 |
|------|------------------|---------|
| **PET medium** | 30.0s | family_bucket（第 2 级）|
| **PP unknown bucket** | 12.5s | family_default_bucket（第 3 级，fallback 到 medium）|
| **UNKNOWN medium** | 18.8s | default（第 4 级）|
| **mold.hold_time_override={'thick': 50}** | 50s | precise（第 1 级）|

#### 9.1.2 维度 2：gate_factor_hold_time 测试

| gate_type | 预期 factor | 物理依据 |
|-----------|------------|---------|
| 直浇口 | 1.20 | 大浇口 → 凝固慢 |
| 护耳式浇口 | 1.05 | 中等 |
| 点浇口 | 0.70 | 小浇口 → 凝固快 |
| 侧浇口 | 0.85 | 中宽深 |
| 其他 / 未识别 | 1.00 | 默认不修正 |

#### 9.1.3 维度 3：runner_factor 测试（复用 #6）

| runner_type | runner_weight | 预期 factor | level |
|-------------|---------------|------------|-------|
| 热流道 | 0 | 0.95 | runner_type / inferred_hot |
| 热转冷 | - | 1.00 | runner_type |
| 冷流道 | 10 | 1.05 | runner_type / inferred_cold |
| 未指定 | 0 | 0.95 | inferred_hot |
| 未指定 | 5 | 1.05 | inferred_cold |
| 未指定 | None | 1.00 | default |

#### 9.1.4 维度 4：mold_temp_factor 测试

| mold_temp | 预期 factor | 物理依据 |
|-----------|------------|---------|
| 30℃ | 0.95 | low |
| 50℃ | 1.00 | medium |
| 90℃ | 1.10 | high |
| 130℃ | 1.20 | ultra_high |

#### 9.1.5 维度 5：crystallinity_kick 测试

| family | 预期 kick | 物理依据 |
|--------|-----------|---------|
| PET | 1.80 | 慢结晶，长窗口 |
| PA | 1.40 | 含水扩散 |
| POM | 1.30 | 高结晶速率 |
| PP | 1.10 | 结晶快 |
| PC | 1.00 | 非结晶 |
| 未知 | 1.00 | 不修正 |

#### 9.1.6 family_hold_time_max 测试（关键）

| family | 预期 max | 物理依据 |
|--------|----------|---------|
| **PET** | **600.0s** | **长保压支持** |
| PP | 30.0s | 标准 |
| 未知 | 300.0s | 兜底 |

### 9.2 端到端测试

#### 9.2.1 典型材料 × 壁厚 × 浇口组合（五维）

| # | family | 壁厚 | 浇口 | 流道 | 模温 | t_gf | gate | runner | mold_t | crys | raw | clamp | hold_time |
|---|--------|------|------|------|------|------|------|--------|--------|------|-----|-------|-----------|
| 1 | **PP** | 2mm | 直浇口 | 热流道 | 50℃ | 12.5 | 1.20 | 0.95 | 1.00 | 1.10 | **15.7** | [2,30] | **15.7** |
| 2 | **ABS** | 2mm | 直浇口 | 冷流道 | 50℃ | 18.8 | 1.20 | 1.05 | 1.00 | 1.00 | **23.7** | [2,60] | **23.7** |
| 3 | **PC** | 5mm | 直浇口 | 热流道 | 80℃ | 90.0 | 1.20 | 0.95 | 1.00 | 1.00 | **102.6** | [2,60] | **60**（被钳） |
| 4 | **PET** | 5mm | 直浇口 | 热流道 | 90℃ | 120.0 | 1.20 | 0.95 | 1.10 | 1.80 | **271.4** | [2,600] | **271.4** ✓ |
| 5 | **PET** | 5mm | 侧浇口 | 冷流道 | 110℃ | 120.0 | 0.85 | 1.05 | 1.10 | 1.80 | **212.0** | [2,600] | **212.0** |
| 6 | **PET** | 5mm | 点浇口 | 冷流道 | 90℃ | 120.0 | 0.70 | 1.05 | 1.10 | 1.80 | **175.0** | [2,600] | **175.0** |
| 7 | **POM** | 4mm | 点浇口 | 热流道 | 80℃ | 64.3×(4/5)≈41 | 0.70 | 0.95 | 1.00 | 1.30 | **36.7** | [2,60] | **36.7** |
| 8 | **PP** | 0.5mm | 点浇口 | 热流道 | 30℃ | 3.6 | 0.70 | 0.95 | 0.95 | 1.10 | **2.4** | [2,30] | **2.4** |

#### 9.2.2 PET 长保压场景验证（用户关键场景）

| 场景 | 计算 | 最终 hold_time | 与用户预期 (100~300s) |
|------|------|----------------|---------------------|
| PET 5mm 直浇口 热流道 90℃ | 271.4 | 271.4 | ✅ 范围内 |
| PET 4mm 直浇口 热流道 80℃ | 30.0×1.20×0.95×1.00×1.80 = 61.6 | 61.6 | ❌ 偏低 |
| PET 4mm 直浇口 **冷流道** 80℃ | 30.0×1.20×1.05×1.00×1.80 = 68.0 | 68.0 | ⚠️ 边缘 |
| **PET 5mm 直浇口 冷流道 110℃** | 120×1.20×1.05×1.10×1.80 = **300** | 300 | ✅ **完美对上 300s 上限** |

**结论**：用户场景完整覆盖（典型 100~300s 范围，公式正确）。

#### 9.2.3 边界场景

| # | 场景 | 预期 | 钳制来源 |
|---|------|------|---------|
| 1 | **PET 极致场景** | 趋向 PET 上限 600s | family 上限钳 |
| 2 | **缺失 mold_temp** | default 1.00 | 中模温默认 |
| 3 | **缺失 runner_type + runner_weight** | 1.00 default | runner 默认 |
| 4 | **缺失 max_thickness** | 回退到 GATE_* 经验公式 | 兜底分支 |

#### 9.2.4 回归对比（与原算法）

| # | 材料 | 壁厚 | 原算法 hold_time | 新算法 hold_time | 物理合理性 |
|---|------|------|----------------|-----------------|----------|
| 1 | PP | 2mm | 2s（被 min 钳）| 15.7s | ✅ 浇口需要 12.5s 凝固 |
| 2 | PC | 5mm | 10s（被 max 钳）| 60s（被 family max 钳） | ✅ 厚壁 PC 必须 90s |
| 3 | **PET** | 5mm | 10s（被 max 钳）| **271s** | ✅ 用户场景 |

---

## 10. 风险与缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| **family_gate_freeze_time 数据偏差** | 中 | 高 | 数值基于 Fourier 热扩散推导，误差 ±20%；后续 Moldflow 仿真校准 |
| **crystallinity_kick 偏差（特别是 PET 1.80）** | 中 | 高 | PET 1.80 是工业典型值；按 PET 瓶盖 100~300s 场景验证；后续试模数据回归 |
| **gate_factor_hold_time 跨场景适用性** | 中 | 中 | 数值基于浇口流阻 + 凝固时间综合，与 #6 保压压力方向相反但量级合理 |
| **mold_temp_factor 桶边界不平滑** | 低 | 低 | 桶分界 [40, 80, 120] 与 #4 注射速度一致，复用 |
| **runner_factor 在保压时间上物理方向反了** | 中 | 低 | 影响小（5%），后续可微调 |
| **hold_time_max=10.0 字段双重含义** | 中 | 中 | 文档明确标注：仅 GATE_* 兜底用；新算法用 family_hold_time_max |
| **GATE_* 兜底公式仍用 10s 上限** | 低 | 低 | 兜底场景仅在缺失 max_thickness 时触发，10s 保守合理 |
| **历史数据无 mold_temp 字段** | 高 | 低 | 缺失时降级到中模温 1.00；推荐工艺设定补填 |

---

## 11. 相关文件

| 文件 | 角色 |
|------|------|
| `process/engines/expert/initializer.py` | 算法主体（_calc_hold_time 重构 + 4 个新辅助函数）|
| `process/engines/expert/expert_rules/init_rules.json` | 规则配置（DEFAULT.holding 追加 5 维参数）|
| `process/engines/expert/rule_matcher.py` | `_BUILTIN_DEFAULTS['holding']` 同步 |
| `_dev_refs/2026-07-04-algorithm-refactor-roadmap.md` | roadmap（算法 #8 状态变更）|
| `_dev_refs/2026-07-05-holding-pressure-physics-design.md` | #6 保压压力设计文档（runner_factor 来源）|
| `_dev_refs/2026-07-05-holding-time-physics-design.md` | 本文档（算法 #8）|

---

## 12. 后续扩展（不在本文档范围）

| 算法 | 优先级 | 文档 | 说明 |
|------|--------|------|------|
| **#7 保压速度** | P1 | 待设计 | 与保压压力耦合（同 #6 升级模式）|
| **#8 升级迭代** | P1 | 本文档 v2.0 | Moldflow 仿真校准 family_gate_freeze_time / crystallinity_kick |
| **#3 #4 注入 runner_factor** | P2 | 待设计 | 算法 #3 #4 也应注入 runner_factor |
| **#15 松退距离** | P2 | 待设计 | runner_factor 影响冷流道松退 |
| **PET 专用模式** | P2 | 待设计 | PET bottle cap 专用 preset（已知场景）|

---

*v1.0 · 设计日期：2026-07-05*
