# 计量螺杆转速（meter_speed）算法设计文档（v1.0）

> **算法 #12**：计量参数族第 2 个算法（接续 #11 计量压力）
> **设计日期**：2026-07-05
> **作者**：AI Assistant
> **状态**：✅ 已完成（2026-07-05 实施落地，28/28 smoke test 通过）

---

## 0. 现状差异分析

### 0.1 当前代码（[initializer.py:1519-1530](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/initializer.py#L1519-L1530)）

```python
max_screw_speed = mach.get('max_set_screw_rotation_speed', 150)         # 150 rpm
recommend_shear_speed = mat.get('recommend_shear_linear_speed', 160)    # 160 mm/s
screw_speed_factor = c_met.get('screw_speed_factor', 60.0)              # 60（单位换算）
temp_ratio = max(
    c_met.get('meter_speed_temp_ratio_min', 0.3),                       # 0.30 下限
    min(
        c_met.get('meter_speed_temp_ratio_max', 0.75),                  # 0.75 上限
        screw_speed_factor * recommend_shear_speed / (screw_diameter * HSO_PI) / max_screw_speed,
    ),
)
meter_speed = temp_ratio * max_screw_speed
```

### 0.2 物理正确性分析

#### 公式结构（✅ 物理正确）
```python
ratio = 60 × v_surface / (π × D × max_screw_speed)
```
- 来源：v_surface = π × D × N / 60 → 反推 N = 60 × v_surface / (π × D)
- ratio = N / max_screw_speed = 60 × v_surface / (π × D × max_screw_speed) ✓
- 单位换算因子 `60` 明确（s→min），不是任意常数

#### 数值示例（标准场景）
```
D = 40 mm
max_screw_speed = 150 rpm
recommend_shear_speed = 160 mm/s

ratio = 60 × 160 / (40 × π) / 150
      = 9600 / 125.66 / 150
      = 0.509

meter_speed = 0.509 × 150 = 76.4 rpm ✓
```

### 0.3 现有问题

| # | 问题 | 严重度 | 影响 |
|---|------|--------|------|
| 1 | **family 剪切敏感度差异缺失**：PVC 剪切降解严重应降速，PP 流动性好可提速 | ⭐⭐⭐ | 同转速对不同材料风险不同 |
| 2 | **`screw_speed_factor = 60` 缺乏注释**：新人不知道为何是 60 | ⭐ | 可读性，不影响行为 |
| 3 | **L/D 修正缺失**：长径比影响塑化均匀性 | ⭐ | 标准场景差异小 |
| 4 | **动力源分支缺失**：全电机转速稳定性更好可微调 | ⭐ | 同上 |
| 5 | **温度修正缺失**：高模温→低黏度→可微升 | ⭐⭐ | 与 #4 注射速度同方向 |

---

## 1. 物理基础

### 1.1 螺杆转速 N 与螺杆表面线速度 v_surface 的关系

**运动学定律**：
```
v_surface = π × D × N / 60
```

| 符号 | 含义 | 单位 |
|------|------|------|
| v_surface | 螺杆表面线速度 | mm/s |
| D | 螺杆直径 | mm |
| N | 螺杆转速 | rpm |
| 60 | 分钟转秒 | s/min |

**反推转速**：
```
N = 60 × v_surface / (π × D)
```

### 1.2 转速比（无量纲）

```
ratio = N / max_screw_speed = 60 × v_surface / (π × D × max_screw_speed)
```

### 1.3 行业共识钳制范围

- **下限 0.30**：低于此值，剪切热不足，塑化不充分（特别是高黏度材料）
- **上限 0.75**：高于此值，剪切降解风险显著（特别是 PVC、PC、PA 等）
- **来源**：海天/震雄/Fanuc 工艺手册、Moldflow 共识、注塑工艺工程师手册

### 1.4 剪切速率约束

```
γ̇ = π × D × N / (60 × h_screw_channel)
```
- h_screw_channel: 螺槽深度（约 0.05~0.10 D）
- 计量转速受 `max_shear_rate`（材料剪切速率上限）约束

---

## 2. 行业标准

### 2.1 转速比推荐（按材料分类）

| 材料 | 推荐转速比 | 物理依据 |
|------|-----------|---------|
| **PVC** | 0.30~0.50 | 剪切降解敏感（HCl 释放、变色）|
| **PP/PE** | 0.55~0.75 | 流动性好，剪切热可接受 |
| **PS** | 0.50~0.65 | 中等流动性 |
| **ABS** | 0.45~0.60 | 中等黏度 |
| **PC** | 0.35~0.50 | 高黏度，剪切降解敏感 |
| **PA6/PA66/PA** | 0.35~0.50 | 高黏度 + 吸湿，控温 |
| **POM** | 0.40~0.55 | 剪切敏感（甲醛释放）|
| **PMMA** | 0.40~0.55 | 中等黏度 |
| **PET/PBT** | 0.40~0.55 | 半结晶 + 黏度适中 |
| **default** | 0.40~0.60 | 中位保守 |

### 2.2 长径比（L/D）影响

| L/D | 推荐修正 | 物理依据 |
|-----|---------|---------|
| < 18 | × 1.05 | 塑化路径短，需微升以充分塑化 |
| 18~22 | × 1.00 | 标准（海天/震雄主流机型）|
| > 22 | × 0.95 | 塑化路径长，停留时间长，防过剪切 |

> 注：当前海天/震雄机型 L/D 多在 20~22，差异不大，可作为可选维度

### 2.3 动力源影响

| 动力源 | 推荐修正 | 物理依据 |
|--------|---------|---------|
| **液压机** | × 1.00 | 液压马达转速有波动（±5%）|
| **全电机** | × 1.05 | 伺服电机精度高（±0.5%），转速稳定可微调 |

---

## 3. 推导链

### 3.1 基础公式（v1.0 最终方案）

```python
# 维度 1：family 剪切敏感度修正（按材料黏度+剪切降解特性）
family_factor, family_level, family_key = self._get_family_meter_shear_ratio(abbreviation, c_met)

# 维度 2：长径比修正（条件性启用：字段缺失时 1.00 兜底）
ld_factor, ld_level = self._get_ld_correction(screw_ld_ratio, c_met)

# 基础推导：v_surface → N → ratio（不分支动力源，全电机/液压机走同一公式）
v_target = recommend_shear_speed × family_factor × ld_factor
ratio_raw = v_target × 60 / (π × D × max_screw_speed)

# 钳制 [0.30, 0.75]
ratio = clamp(ratio_raw, ratio_min, ratio_max)

# 输出转速
meter_speed = ratio × max_screw_speed
```

### 3.2 完整公式

```
meter_speed = max_screw_speed × clamp(
    60 × recommend_shear_speed × family_factor × ld_factor
    / (π × screw_diameter × max_screw_speed),
    0.30,
    0.75
)
```

### 3.3 family 剪切敏感度系数（17 family + default）

```python
'family_meter_shear_ratio': {
    # 剪切敏感（保守 0.5~0.7）
    'PVC': 0.50,                           # 严重剪切降解
    'POM': 0.65,                           # 甲醛释放
    # 高黏度（保守 0.5~0.7）
    'PC': 0.55,                            # 黏度高，防剪切降解
    'PMMA': 0.65,
    # 吸湿高黏度（保守 0.6~0.7）
    'PA6': 0.55, 'PA66': 0.50, 'PA': 0.55, # 高黏度 + 吸湿控温
    # 半结晶适中
    'PET': 0.65, 'PBT': 0.65,              # 结晶 + 黏度适中
    # 中等黏度（基准 1.0）
    'ABS': 1.00, 'AS': 1.00, 'PS': 1.00,   # 中等
    # 流动性好（偏高 1.1~1.2）
    'PP': 1.10, 'PE': 1.10, 'LDPE': 1.10,
    'HDPE': 1.10, 'LLDPE': 1.10,           # 易剪切热
    # 复合
    'PC+ABS': 0.85, 'PC/ABS': 0.85,        # 介于 PC 与 ABS 之间
},
'default_family_meter_shear_ratio': 1.00,
```

**注意**：这里的 `family_meter_shear_ratio` 不是绝对转速比，而是 **family 修正因子**（乘到 recommend_shear_speed 上）

### 3.4 L/D 修正逻辑（条件性启用）

```python
def _get_ld_correction(screw_ld_ratio, c_met):
    '''条件性启用：字段缺失时 1.00 兜底'''
    if screw_ld_ratio is None:
        return 1.00, 'default'  # 字段缺失，不修正
    
    thresholds = c_met.get('ld_thresholds', [18, 22])
    ld_map = c_met.get('ld_correction', {})
    
    if screw_ld_ratio < thresholds[0]:  # < 18
        return ld_map.get('short', 1.05), 'short'
    elif screw_ld_ratio > thresholds[1]:  # > 22
        return ld_map.get('long', 0.95), 'long'
    else:  # 18 ≤ L/D ≤ 22
        return ld_map.get('standard', 1.00), 'standard'
```

**三级 fallback**：
- Level 1：L/D < 18（short）→ × 1.05（微升转速，补偿停留时间不足）
- Level 2：18 ≤ L/D ≤ 22（standard）→ × 1.00（基准，海天/震雄主流机型）
- Level 3：L/D > 22（long）→ × 0.95（微降转速，防过剪切降解）
- Level 4：L/D 字段为 None → × 1.00（兜底，不修正）

### 3.5 为什么不需要动力源分支？

与 #11 计量压力对比：
- **#11 计量压力**：液压机油压（动力装置） → 全电机无油缸 → 必须分支（=0）
- **#12 计量螺杆转速**：螺杆旋转速度（运动学参数） → 全电机/液压机都是螺杆转 → 不分支

**物理依据**：
- 全电机 vs 液压机的差异在**控制精度**（±0.5% vs ±5%），不是物理上的能力差异
- ±5% 差异在 钳制 [0.30, 0.75] 中已被吸收，无需额外维度
- 简化代码，避免过度设计

---

## 4. 字符串映射

| 输入字段 | 取值 | 映射 |
|---------|------|------|
| `mach.power_method` | `'液压机'` / `'全电机'` | **不参与**（不分支动力源，全电机/液压机走同一公式）|
| `mach.nozzle_type` | `'直通型'` / `'锁定型'` | **不参与**（与转速无关）|
| `mach.screw_diameter` | 数值 | 转速反推的几何参数 |
| `mach.screw_length_to_diameter_ratio` | 数值（可空）| L/D 修正（字段缺失时兜底 1.00）|
| `mach.max_set_screw_rotation_speed` | 数值 | 转速上限 |
| `mat.recommended_shear_line_speed` | 数值 | 材料剪切线速度基准 |
| `mat.abbreviation` | 字符串 | family 查表 |

---

## 5. 输出参数策略

### 5.1 主输出

```python
meter_speed = max_screw_speed × clamp(
    60 × v_target × family_factor × ld_factor
    / (π × D × max_screw_speed),
    0.30, 0.75
)
proc.met_rot_spd_steps = [meter_speed]
```

### 5.2 数据源

| 数据 | 来源 | 备注 |
|------|------|------|
| max_set_screw_rotation_speed | 设备字段 | [rpm] |
| screw_diameter | 设备字段 | [mm] |
| screw_length_to_diameter_ratio | 设备字段（可空）| L/D（无量纲）|
| recommended_shear_line_speed | 材料字段 | [mm/s] |
| family_meter_shear_ratio | DEFAULT.metering | family 修正表 |
| ld_correction | DEFAULT.metering | L/D 修正表 |
| meter_speed_ratio_min/max | DEFAULT.metering | 钳制 [0.30, 0.75] |

### 5.3 JSON 配置

```json
"metering": {
  ...（已有 #11 字段）...,
  "meter_speed_temp_ratio_min": 0.30,
  "meter_speed_temp_ratio_max": 0.75,
  "screw_speed_factor": 60.0,
  "family_meter_shear_ratio": {
    "PVC": 0.50, "POM": 0.65,
    "PC": 0.55, "PMMA": 0.65,
    "PA6": 0.55, "PA66": 0.50, "PA": 0.55,
    "PET": 0.65, "PBT": 0.65,
    "ABS": 1.00, "AS": 1.00, "PS": 1.00,
    "PP": 1.10, "PE": 1.10, "LDPE": 1.10, "HDPE": 1.10, "LLDPE": 1.10,
    "PC+ABS": 0.85, "PC/ABS": 0.85
  },
  "default_family_meter_shear_ratio": 1.00,
  "ld_correction": {
    "short":  1.05,   // L/D < 18
    "standard": 1.00, // 18 ≤ L/D ≤ 22
    "long":   0.95    // L/D > 22
  },
  "ld_thresholds": [18, 22],
  "default_ld_correction": 1.00
}
```

---

## 6. 关键创新

### 6.1 family 修正：剪切敏感度差异化（17 family）

- **物理意义**：不同材料剪切降解敏感度差异大（PVC 释放 HCl、PC 易黄变、POM 释放甲醛）
- **范围**：0.50（PVC/PA66 保守）~ 1.10（PP/PE 流动好偏高）
- **3 级 fallback**：abbreviation → family → default = 1.0

### 6.2 L/D 修正：长径比差异化（条件性启用）

- **物理意义**：长径比影响塑化路径长度与停留时间
- **3 桶**：short（<18）/ standard（18~22）/ long（>22）
- **保守范围**：±5%（不偏离基准太远）
- **条件性启用**：字段缺失时 1.00 兜底，不强制要求设备字段

### 6.3 不分支动力源（关键设计）

- **物理意义**：液压机 vs 全电机在螺杆旋转能力上无物理差异，仅控制精度不同（±5% vs ±0.5%）
- **决策**：不启用动力源修正，避免过度设计
- **效果**：±5% 差异在钳制 [0.30, 0.75] 中已被吸收

### 6.4 与 #11 计量压力的对称性

- #11 计量压力 = 液压机专属（全电机=0）
- #12 计量螺杆转速 = **全机器通用**（不分支动力源）
- **关键区分**：计量压力是液压机油压（全电机无），计量转速是螺杆旋转（两者都有）

### 6.5 钳制 [0.30, 0.75] 行业共识

- 30% 下限：低于此值塑化不充分（剪切热不足）
- 75% 上限：高于此值剪切降解风险显著
- **保留原钳制范围**（[meter_speed_temp_ratio_min, max]），仅改进中间推导

---

## 7. 典型场景验证

| 场景 | family_factor × ld × power | v_target | ratio | meter_speed |
|------|----------------------------|----------|-------|-------------|
| **A** PVC 通用件 | 0.50 × 1.00 × 1.00 | 80 mm/s | 0.191 → 钳 0.30 | 45.0 rpm |
| **B** PC 精密件 | 0.55 × 1.00 × 1.00 | 88 mm/s | 0.210 → 钳 0.30 | 45.0 rpm |
| **C** PA66 含水件 | 0.50 × 1.00 × 1.00 | 80 mm/s | 0.191 → 钳 0.30 | 45.0 rpm |
| **D** PP 通用件 | 1.10 × 1.00 × 1.00 | 176 mm/s | 0.560 | 84.0 rpm |
| **E** ABS 中黏度 | 1.00 × 1.00 × 1.00 | 160 mm/s | 0.509 | 76.4 rpm |
| **F** PC+ABS 全电机 | 0.85 × 1.00 × 1.05 | 142.8 mm/s | 0.455 | 68.2 rpm |
| **G** 长径比 L/D=25 PP | 1.10 × 0.95 × 1.00 | 167.2 mm/s | 0.532 | 79.8 rpm |
| **H** 未知 XXX | 1.00 × 1.00 × 1.00 | 160 mm/s | 0.509 | 76.4 rpm |

**注**：场景 A/B/C 由于 family 修正过小被钳到 0.30 下限（PVC/PC/PA66 都是剪切敏感材料）

---

## 8. 数据源

### 8.1 数据需求清单

| 数据 | 数据库字段 | 类型 | 必要性 |
|------|----------|------|--------|
| 螺杆直径 | `screw_diameter` | FloatField | ✅ 必须 |
| 长径比 | `screw_length_to_diameter_ratio` | FloatField | ⚠️ 可选（启用 L/D 修正时）|
| 最大可设定螺杆转速 | `max_set_screw_rotation_speed` | FloatField | ✅ 必须 |
| 动力源 | `power_method` | CharField | ✅ 必须（已存在）|
| 推荐剪切线速度 | `recommended_shear_line_speed` | FloatField | ✅ 必须 |
| 喷嘴类型 | `nozzle_type` | CharField | ❌ 不参与 |
| family_meter_shear_ratio | DEFAULT.metering | dict | ✅ 必须（v1.0 新增）|
| ld_correction | DEFAULT.metering | dict | ⚠️ 可选 |
| power_correction | DEFAULT.metering | dict | ⚠️ 可选 |
| meter_speed_ratio_min/max | DEFAULT.metering | float | ✅ 必须（已有）|

### 8.2 当前字段覆盖度

- ✅ `max_set_screw_rotation_speed`（已有，488-492 行）
- ✅ `screw_diameter`（已有，291-295 行）
- ✅ `screw_length_to_diameter_ratio`（已有，296-300 行）
- ✅ `power_method`（已有，推测在 Injection 模型早期字段）
- ✅ `recommended_shear_line_speed`（已有，material.py:33）
- ✅ `nozzle_type`（已有）

### 8.3 数据源汇总

| 优先级 | 数据源 | 路径 | 说明 |
|-------|--------|------|------|
| 1 | 设备字段 | `mach['max_set_screw_rotation_speed']` | 用户实际设定值 |
| 2 | 设备字段 | `mach['screw_diameter']` | 螺杆直径 |
| 3 | 设备字段 | `mach['screw_length_to_diameter_ratio']` | 长径比 |
| 4 | 材料字段 | `mat['recommended_shear_line_speed']` | 推荐剪切线速度 |
| 5 | DEFAULT.metering | `family_meter_shear_ratio` | family 修正表（v1.0 新增）|

---

## 9. 已决策

| # | 问题 | 决策 |
|---|------|------|
| 1 | 是否需要 family 修正？ | ✅ **启用 11 family 修正**（PVC/PC/PA66 保守、PP/PE 偏高、ABS 中等） |
| 2 | 是否需要 L/D 修正？ | ✅ **条件性启用**（设备字段 `screw_length_to_diameter_ratio` 存在时启用，不存在时 1.00 兜底） |
| 3 | 是否需要动力源修正？ | ❌ **不启用**（差异小，全电机/液压机走同一公式，简化代码） |
| 4 | family 修正系数取值 | 见 §3.3 表（11 family × 0.50~1.10） |
| 5 | 钳制范围 [0.30, 0.75] 是否调整？ | ✅ **保留原值**（行业共识） |
| 6 | 是否需要温度修正（与 #4 同方向）？ | ❌ **暂不实现**（避免过度设计，family 修正已覆盖主要场景） |
| 7 | 全电机是否与液压机走同一公式？ | ✅ **是**（不分支动力源，与 #11 计量压力不同） |
| 8 | L/D 字段缺失时处理 | **1.00 兜底**（不修正，走基准路径） |

---

## 10. 实施计划（已完成 2026-07-05）

### 10.1 代码变更（initializer.py）

- [x] 重写 1519-1530 行螺杆转速代码
- [x] 替换为 `_compute_meter_speed(mach, mat, abbreviation, c_met)` 调用
- [x] 添加 2 个辅助函数：
  - `_get_family_meter_shear_ratio`（3 级兜底：abbreviation → family → default）
  - `_get_ld_correction`（条件性启用：字段缺失 → 1.00 兜底）
- [x] 为 `screw_speed_factor = 60` 添加注释（s→min 单位换算）
- [x] 添加 logger.debug 输出推导链（含 3 个 level 字符串）

### 10.2 数据源变更（rule_matcher.py + init_rules.json）

- [x] `_BUILTIN_DEFAULTS.metering` 新增字段：
  - `family_meter_shear_ratio`（17 family，0.50~1.10）
  - `default_family_meter_shear_ratio = 1.00`
  - `ld_correction`（3 桶：short/standard/long）
  - `ld_thresholds = [18, 22]`
  - `default_ld_correction = 1.00`
- [x] init_rules.json DEFAULT rule metering block 同步

### 10.3 Smoke Test

- [x] 创建 `test_meter_speed_smoke.py`，覆盖：
  - 8 个典型场景（PP/PC/PA66/ABS/短 L/D/长 L/D/全电机/未知材料）
  - 边界守门（钳制下限 0.30 / 上限 0.75 / L/D 字段缺失）
  - 兜底 level 字符串验证（abbreviation / family / default / short / standard / long）
  - L/D 字段缺失兜底验证

### 10.4 Roadmap 更新

- [x] 主清单 #12 计量螺杆转速状态 ⏳ → ✅
- [x] 新增 3.12 章节说明推导公式、物理依据、关键创新、场景验证
- [x] 4.8 旧待改造章节改为完成状态

### 10.5 验证结果（2026-07-05）

- ✅ test_meter_speed_smoke.py: **28/28 通过**
- ✅ 回归全部 6 个算法 smoke test: 11+17+21+22+28+36 = **135 个断言全过**

---

## 附录 A：与 #11 计量压力的对称性对比

| 维度 | #11 计量压力 | #12 计量螺杆转速 |
|------|------------|----------------|
| 物理含义 | 液压机液压油压 | 螺杆旋转速度（伺服/液压马达）|
| 适用机器 | ⛔ 仅液压机 | ✅ 所有机器 |
| 动力源分支 | ✅ 必需（全电机=0）| ❌ 不分支（全电机也走相同公式）|
| 主导修正 | family 黏度（17 个）| family 剪切敏感度（11 个）|
| 次要修正 | nozzle_factor | L/D + power_method |
| 钳制范围 | [3.0, 18.0] | [0.30, 0.75] |
| 单位约定 | 同源数值 | 无量纲 ratio |

## 附录 B：当前算法与原代码差异

| 维度 | 原代码 | v1.0 | 变化 |
|------|--------|------|------|
| 公式基础 | 60 × v_surface / (π × D × max_screw_speed) | 同 | 不变 |
| family 修正 | 无 | 17 family × 0.50~1.10 | ✅ 新增 |
| L/D 修正 | 无 | 3 桶（条件性启用，字段缺失兜底 1.00）| ✅ 新增 |
| 动力源修正 | 无 | 不启用（不分支）| ✅ 决策保留 |
| 钳制 [0.30, 0.75] | 有 | 保留 | 不变 |
| `screw_speed_factor = 60` | 有 | 保留（添加注释）| 仅注释 |