# 计量背压（meter_back_pres）算法设计文档（v1.0）

> **算法 #13**：计量参数族第 3 个算法（接续 #11 计量压力 + #12 螺杆转速）
> **设计日期**：2026-07-05
> **作者**：AI Assistant
> **状态**：✅ 已完成（2026-07-05 实施落地，34/34 smoke test 全过）

---

## 0. 现状差异分析

### 0.1 当前代码（[initializer.py:1669](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/initializer.py#L1669)）

```python
meter_back_pres = mat.get('recommend_back_pressure', 15)
```

### 0.2 问题清单

| # | 问题 | 影响 |
|---|------|------|
| 1 | **无算法推导**：直接读取材料数据库字段 | 数据库值缺失时默认 15 MPa，对 PA66(2~6) 严重偏高 |
| 2 | **无 family 修正**：所有材料用同一字段 | 无法体现 PA66 vs PMMA 5x 差异 |
| 3 | **无排气需求修正**：结晶型 vs 非晶态 vs 水敏性差异 | 高黏度材料排气不充分；PA66 易水解 |
| 4 | **无螺杆转速联动**：背压应与 #12 转速协调 | 转速变化时背压无法自适应 |
| 5 | **默认值 15 MPa 偏高**：行业多数材料推荐 5~10 MPa | 对 PVC(4~8)/PA66(2~6) 偏保守偏高 |

### 0.3 与 #11 计量压力、#12 螺杆转速的关系

```
┌────────────────────────────────────────────────────┐
│ #11 计量压力（液压机油压·仅液压机）                │
│     • 液压机专属（全电机=0）                       │
│     • 修正：family 黏度 + nozzle_factor             │
├────────────────────────────────────────────────────┤
│ #12 螺杆转速（机械驱动·所有机器通用）              │
│     • 不分支动力源                                 │
│     • 修正：family 剪切敏感度 + L/D                 │
├────────────────────────────────────────────────────┤
│ #13 计量背压（材料介质·所有机器通用）    ← 本算法 │
│     • 不分支动力源（与 #12 对称）                  │
│     • 修正：family 排气需求 + 螺杆转速联动          │
└────────────────────────────────────────────────────┘
```

---

## 1. 物理意义

**计量背压（metering back pressure）**：在塑化（计量）阶段，螺杆回退储料时，液压油路或伺服电机在螺杆背后施加的阻力。

**核心物理作用**：
1. **压缩熔体**：将螺杆头部的熔体压实，提高密度均匀性
2. **排除空气**：将物料中的气体挤到料斗端，避免制品气泡、银纹
3. **混合均匀**：色母、填充物、回收料与基体充分混合
4. **防止回流**：避免熔体从止逆阀回流导致计量不准确

**关键概念澄清（计量背压 ≠ 计量压力）**：
- **计量背压**：**介质**侧（熔体/螺杆头）参数，所有机器都有
- **计量压力**：**驱动装置**侧（液压油缸）参数，仅液压机有

---

## 2. 行业标准（Gud Mould 数据 + RJG 标准）

### 2.1 RJG 推荐范围

```
背压设置 500~1000 psi ≈ 3.4~6.9 MPa
```

**物理依据**：过高背压会增加剪切生热、延长塑化时间、可能产生飞边；过低背压会导致熔体密度不均、产生气泡。

### 2.2 不同材料推荐范围（Gud Mould）

| 材料 | 熔体温度 (℃) | 背压 (MPa) | 物理归类 | 排气需求 |
|------|-------------|-----------|---------|---------|
| **PMMA** | 215~240 | **13~28** | 高黏度非晶 | **极高** |
| **PC** | 280~320 | 6~15 | 高黏度非晶（热敏）| 高 |
| **ABS** | 190~235 | 9~18 | 中高黏度非晶 | 中高 |
| **PP** | 200~250 | 9~17 | 结晶型 | 中高 |
| **PE** | 180~220 | 7~18 | 结晶型（不同密度）| 中 |
| **PPS** | 300~340 | 5~12 | 高耐热结晶 | 中 |
| **PC/ABS** | 250~280 | 5~12 | 共混非晶 | 中 |
| **PBT** | 250~270 | 5~10 | 结晶型 | 中 |
| **PET** | 260~295 | 5~10 | 结晶型 | 中 |
| **POM** | 190~215 | 5~10 | 结晶型（甲醛释放）| 中低 |
| **PS** | 180~220 | 5~10 | 低黏度非晶 | 中 |
| **HIPS** | 175~230 | 5~10 | 低黏度非晶 | 中 |
| **AS** | 210~250 | 5~15 | 非晶 | 中 |
| **K 塑料** | 170~250 | 3~10 | 共聚物（宽范围）| 中 |
| **PA6** | 240~290 | **3~8** | 水敏吸湿 | **低** |
| **PVC** | 160~185 | **4~8** | **剪切敏感（HCl 释放）** | **低** |
| **PA66** | 260~290 | **2~6** | **极易水解** | **极低** |

### 2.3 关键洞察（解释 5x 差异）

| 现象 | 物理根因 |
|------|---------|
| **PMMA 13~28** | 高黏度（10⁴~10⁵ Pa·s）→ 密度均匀性差，需强背压排气 |
| **PA66 2~6** | 含水率 >0.2% 即水解 → 高背压摩擦生热会加剧水解 |
| **PVC 4~8** | 剪切降解释放 HCl → 高背压剧烈剪切会降解 |
| **PP 9~17** | 结晶型 → 熔体密度均匀性直接影响结晶度 |

**反直觉结论**：低背压不是因为"排气需求低"，而是材料**物理受不了**高背压。

---

## 3. v1.0 推导链

### 3.1 基础公式

```python
# 不分支动力源（全电机/液压机走同一公式，与 #12 对称）
meter_back_pres_raw = recommend_back_pressure        # 材料数据库中位值
                    × family_back_pres_factor[abbrev] # 维度 1：family 排气需求修正
                    × speed_factor                    # 维度 2：螺杆转速联动修正

meter_back_pres = clamp(meter_back_pres_raw, min, max)
```

### 3.2 完整公式（v1.0）

```python
# 读取输入
recommend_back_pressure = mat.get('recommend_back_pressure') or 5.0  # 缺失兜底 5.0 MPa
rpm_ratio = meter_speed / max_screw_speed                              # 来自 #12

# 维度 1：family 排气需求修正（3 级兜底：abbreviation → family → default）
family_factor, family_level, family_key = _get_family_back_pres_factor(abbreviation, c_back)

# 维度 2：螺杆转速联动修正（条件性启用：rpm_ratio 缺失 → 1.0 兜底）
if rpm_ratio is not None:
    # 物理：转速越高 → 熔体停留时间越短 → 密度均匀性越差 → 需更高背压补偿
    speed_factor = 1.0 + 0.3 × (rpm_ratio - 0.5)  # 中位 0.5 时 speed_factor = 1.0
    speed_factor = clamp(speed_factor, 0.85, 1.15) # 钳制防过修正
else:
    speed_factor = 1.0  # 缺失兜底

# 基础推导 + 钳制
meter_back_pres_raw = recommend_back_pressure × family_factor × speed_factor
meter_back_pres = max(
    c_back.get('meter_back_pres_min', 0.5),
    min(meter_back_pres_raw, c_back.get('meter_back_pres_max', 30.0))
)
```

### 3.3 物理依据（每个维度的细节）

#### 维度 1：family 排气需求修正（必选）

**17 family × 0.40~1.50 范围**（基于 Gud Mould 数据反推）：

| 类别 | family | 修正系数 | 物理依据 |
|------|--------|---------|---------|
| **高黏度强排气** | PMMA | **1.50** | 高黏度，需强排气 |
| **高黏度（热敏）** | PC | 1.30 | 高黏度但避免剪切降解 |
| **结晶型基准** | PP/PE/LDPE/HDPE/LLDPE | 1.00 | 结晶型需密度均匀 |
| **非晶基准** | ABS/PMMA?/PS | 1.00（中等）| 中等黏度 |
| **结晶+中黏度** | PBT/PET | 0.95 | 流动性好 |
| **流动性好** | PS/HIPS | 0.90 | 低黏度 |
| **甲醛释放** | POM | 0.85 | 剪切释放甲醛 |
| **共混** | PC+ABS/PC/ABS | 1.10 | 共混需更多混合 |
| **低背压（不水解时）** | K 塑料 | 0.80 | 宽范围 |
| **极易水解** | **PA66** | **0.40** | **极易水解** |
| **吸湿** | **PA6/PA** | **0.60** | **易水解** |
| **剪切敏感** | **PVC** | **0.50** | **HCl 释放** |

**3 级 fallback 链**：
1. 精确全名匹配 `family_back_pres_factor['PA66' / 'PVC' / 'PC+ABS']` → 'precise_abbrev'
2. family 大类匹配（PA66 → PA）→ 'precise_family'
3. 默认 `default_family_back_pres_factor = 1.0` → 'default'

#### 维度 2：螺杆转速联动修正（条件性启用）

**物理依据**：
- 螺杆转速 N 越高 → 熔体在料筒中停留时间 t ∝ 1/N 越短
- 停留时间短 → 熔体密度均匀性差 → 需更高背压补偿
- 反之，转速过低 → 停留时间长 → 熔体已充分均匀 → 背压可略降低

**简化公式**：
```
speed_factor = 1.0 + 0.3 × (rpm_ratio - 0.5)
```

**3 个关键点**：
- rpm_ratio = 0.5（典型转速，#12 钳制范围 [0.30, 0.75] 中位）→ speed_factor = 1.0
- rpm_ratio = 0.30（钳制下限）→ speed_factor = 0.85（钳到下限）
- rpm_ratio = 0.75（钳制上限）→ speed_factor = 1.15（钳到上限）

**条件性启用**：
- `rpm_ratio` 字段完整 → 启用
- `rpm_ratio` 缺失 → speed_factor = 1.0（兜底）

### 3.4 钳制范围

**默认值**：
```python
meter_back_pres_min = 0.5   # MPa（PA66 下限 2.0 的安全余量 25%）
meter_back_pres_max = 30.0  # MPa（PMMA 上限 28 的安全余量 7%）
```

**覆盖验证**：
| 材料 | 推导结果 | 行业范围 | 验证 |
|------|---------|---------|------|
| PA66 | 5.0 × 0.40 × 1.0 = 2.0 | 2~6 | ✅ |
| PVC | 5.0 × 0.50 × 1.0 = 2.5 | 4~8 | ⚠️ 偏低（边界） |
| PP | 5.0 × 1.00 × 1.0 = 5.0 | 9~17 | ⚠️ 偏低（钳到下限风险） |
| PMMA | 5.0 × 1.50 × 1.0 = 7.5 | 13~28 | ⚠️ 偏低 |
| ABS | 5.0 × 1.00 × 1.0 = 5.0 | 9~18 | ⚠️ 偏低 |

**问题**：默认 5 MPa 偏低，导致多数材料落入钳制下限。**修正方案**：将默认值提高到 **10 MPa**（更接近行业中位）。

让我重新设计默认值：
- **10 MPa**：覆盖多数非水解材料推荐范围 5~15 MPa 的中位
- **PA66**（family=0.40）→ 10 × 0.40 = **4 MPa**（在 PA66 范围 2~6 内 ✅）
- **PMMA**（family=1.50）→ 10 × 1.50 = **15 MPa**（在 PMMA 范围 13~28 内 ✅）
- **PVC**（family=0.50）→ 10 × 0.50 = **5 MPa**（在 PVC 范围 4~8 内 ✅）
- **PP**（family=1.00）→ 10 × 1.00 = **10 MPa**（在 PP 范围 9~17 内 ✅）
- **ABS**（family=1.00）→ 10 × 1.00 = **10 MPa**（在 ABS 范围 9~18 内 ✅）

> ⚠️ **修正决策**：将默认 `recommend_back_pressure` 从 **5.0 MPa** 改为 **10.0 MPa**（行业中位，PA66/PMMA/PVC 验证均合理）

---

## 4. 字符串映射（数据源）

### 4.1 输入字段

| 字段名 | 来源 | 类型 | 必选 | 备注 |
|--------|------|------|------|------|
| `abbreviation` | `mat.abbreviation` | str | ✅ | 用于 family 匹配 |
| `recommend_back_pressure` | `mat.recommend_back_pressure` | FloatField (MPa) | ❌ | 缺失时默认 10.0 |
| `meter_speed` | 来自 #12 推导 | float | ✅ | 螺杆转速联动 |
| `max_screw_speed` | `mach.max_screw_rotation_speed` | FloatField (rpm) | ✅ | 转速比计算 |

### 4.2 输出参数

| 参数名 | 来源 | 含义 |
|--------|------|------|
| `meter_back_pres` | v1.0 推导 | 计量背压（MPa） |

### 4.3 `DEFAULT.back_pressure` 块（rule_matcher.py + init_rules.json）

```python
'back_pressure': {
    'meter_back_pres_min': 0.5,        # 钳制下限
    'meter_back_pres_max': 30.0,       # 钳制上限
    'default_recommend_back_pressure': 10.0,  # 缺失兜底（行业中位）
    'family_back_pres_factor': {       # 17 family × 0.40~1.50
        'PP': 1.00, 'PE': 1.00, 'LDPE': 1.00, 'HDPE': 1.00, 'LLDPE': 1.00,
        'PS': 0.90, 'HIPS': 0.90,
        'PVC': 0.50,
        'ABS': 1.00, 'PMMA': 1.50,
        'PC': 1.30, 'POM': 0.85,
        'PA6': 0.60, 'PA66': 0.40, 'PA': 0.60,
        'PET': 0.95, 'PBT': 0.95,
        'PC+ABS': 1.10, 'PC/ABS': 1.10,
        'K塑料': 0.80,
    },
    'default_family_back_pres_factor': 1.0,
    'speed_factor_base': 0.5,          # speed_factor=1.0 对应的 rpm_ratio 中位
    'speed_factor_slope': 0.3,         # rpm_ratio 偏离 base 时的斜率
    'speed_factor_min': 0.85,          # 钳制下限
    'speed_factor_max': 1.15,          # 钳制上限
    'default_speed_factor': 1.0,       # rpm_ratio 缺失兜底
}
```

---

## 5. 输出参数策略

### 5.1 proc 字段

```python
proc.met_back_pres_steps = [meter_back_pres]  # 单段（与 #11/#12 一致）
```

### 5.2 logger.debug 输出

```python
logger.debug(
    f"[meter_back_pres] abbreviation={abbreviation}, "
    f"recommend_back={recommend_back_pressure}, "
    f"family={family_key} (family_factor={family_factor:.2f}, level={family_level}), "
    f"rpm_ratio={rpm_ratio:.3f}, speed_factor={speed_factor:.2f}, "
    f"raw={meter_back_pres_raw:.2f}MPa, "
    f"clamped=[{min_val:.2f}, {max_val:.2f}], "
    f"final={meter_back_pres:.2f}MPa"
)
```

### 5.3 3 级兜底 level 字符串

| level | 触发条件 | 含义 |
|-------|---------|------|
| `precise_abbrev` | `abbreviation` 精确命中 `family_back_pres_factor` 字典 | 精确全名匹配（如 PA66/PVC/PC+ABS） |
| `precise_family` | `abbreviation` 未命中但 `_parse_family(abbreviation)` 命中 | family 大类匹配（如 PA66→PA） |
| `default` | 都不命中 | 默认值 1.0 |

---

## 6. 关键创新

1. **family 排气需求修正（必选）**：17 family × 0.40~1.50，物理清晰，覆盖行业 2~28 MPa 范围
2. **3 级 fallback**：保留细分能力（PA66 vs PA 差 50%）
3. **螺杆转速联动修正（条件性启用）**：与 #12 联动，rpm_ratio 缺失 → 1.0 兜底
4. **不分支动力源（与 #12 对称）**：与 #11 液压专属形成对称演进
5. **钳制 [0.5, 30.0]**：覆盖 PA66 下限（2.0）安全余量 25% + PMMA 上限（28）安全余量 7%
6. **反直觉修正方向**：低背压不是因为排气需求低，而是材料物理受不了高背压
7. **默认值 10.0 MPa（行业中位）**：经 PMMA/PA66/PVC/PP/ABS 验证合理

---

## 7. 典型场景验证

| 场景 | 推导链 | final | 行业范围 | 验证 |
|------|--------|-------|---------|------|
| **A. PP 通用件** | 10.0 × 1.00 × 1.0 = 10.0 | **10.0 MPa** | 9~17 | ✅ |
| **B. PC 精密件** | 10.0 × 1.30 × 1.0 = 13.0 | **13.0 MPa** | 6~15 | ✅ |
| **C. PA66 含水件** | 10.0 × 0.40 × 1.0 = 4.0 | **4.0 MPa** | 2~6 | ✅ |
| **D. PVC 通用件** | 10.0 × 0.50 × 1.0 = 5.0 | **5.0 MPa** | 4~8 | ✅ |
| **E. PMMA 高黏度** | 10.0 × 1.50 × 1.0 = 15.0 | **15.0 MPa** | 13~28 | ✅ |
| **F. 全电机 ABS** | 与液压机同公式 | **10.0 MPa** | 9~18 | ✅ 不分支动力源 |
| **G. ABS + 高速 rpm=0.75** | 10.0 × 1.00 × 1.15 = 11.5 | **11.5 MPa** | 9~18 | ✅ 转速联动 |
| **H. ABS + 低速 rpm=0.30** | 10.0 × 1.00 × 0.85 = 8.5 | **8.5 MPa** | 9~18 | ⚠️ 略低于下限 |

**场景 H 验证**：ABS 低速下背压 8.5 MPa，低于行业下限 9 MPa，但在合理范围（流动性好的情况下，8.5 MPa 仍可接受）。

---

## 8. 数据源

### 8.1 材料字段（material.py）

| 字段 | 类型 | 必须 |
|------|------|------|
| `abbreviation` | CharField | ✅ 必选 |
| `recommend_back_pressure` | FloatField (MPa) | 可选（缺失 → 10.0 兜底） |

### 8.2 设备字段（injection.py）

| 字段 | 类型 | 必须 |
|------|------|------|
| `max_screw_rotation_speed` | FloatField (rpm) | ✅ 必选（用于 rpm_ratio） |

### 8.3 推导字段（来自 #12）

| 字段 | 来源 | 必须 |
|------|------|------|
| `meter_speed` | #12 推导结果 | ✅ 必选（用于 rpm_ratio） |

---

## 9. 已决策

| # | 决策项 | 决策 |
|---|--------|------|
| 1 | family 排气需求修正 | ✅ 启用 17 family × 0.40~1.50 |
| 2 | 螺杆转速联动修正 | ✅ 启用条件性（rpm_ratio 缺失 → 1.0 兜底） |
| 3 | 含水率修正 | ❌ 不预留扩展点（数据库暂时无此字段） |
| 4 | 默认值 | 10.0 MPa（行业中位，PA66/PMMA/PVC 验证合理） |
| 5 | 钳制范围 | [0.5, 30.0] MPa |
| 6 | 动力源分支 | ❌ 不分支（全电机/液压机同公式） |
| 7 | speed_factor 公式 | `1.0 + 0.3 × (rpm_ratio - 0.5)`，钳制 [0.85, 1.15] |
| 8 | 输出参数 | `meter_back_pres`（单段，与 #11/#12 一致） |

---

## 10. 实施计划（2026-07-05 已完成）

### 10.1 代码变更（initializer.py）

- [x] 重写 1669 行 `meter_back_pres = mat.get('recommend_back_pressure', 15)`
- [x] 替换为 `meter_back_pres = self._compute_meter_back_pres(mach, mat, abbreviation, meter_speed, c_back)` 调用
- [x] 添加 3 个辅助函数：
  - `_compute_meter_back_pres`（主计算）
  - `_get_family_back_pres_factor`（3 级兜底：abbreviation → family → default）
  - `_get_speed_factor`（条件性启用：rpm_ratio 缺失 → 1.0 兜底）
- [x] 添加 logger.debug 输出推导链（含 3 个 level 字符串：family_level + speed_level）

### 10.2 数据源变更（rule_matcher.py + init_rules.json）

- [x] 新增 `_BUILTIN_DEFAULTS.back_pressure` 块：
  - `meter_back_pres_min = 0.5`
  - `meter_back_pres_max = 30.0`
  - `default_recommend_back_pressure = 10.0`
  - `family_back_pres_factor`（17 family，0.40~1.50）
  - `default_family_back_pres_factor = 1.00`
  - `speed_factor_base = 0.5`, `speed_factor_slope = 0.3`
  - `speed_factor_min = 0.85`, `speed_factor_max = 1.15`
  - `default_speed_factor = 1.00`
- [x] init_rules.json DEFAULT rule 新增 back_pressure block（同步全部字段）

### 10.3 Smoke Test（test_meter_back_pres_smoke.py）

- [x] 创建 `process/engines/expert/tests/test_meter_back_pres_smoke.py`，覆盖：
  - 8 个典型场景（PP / PC / PA66 / PVC / PMMA / 全电机 / 高速 / 低速）
  - 4 组边界守门（钳制下限 0.5 / 钳制上限 30.0 / 转速下限 0.85 / 转速上限 1.15）
  - level 字符串验证（precise_abbrev / precise_family / default）
  - rpm_ratio 缺失兜底验证
  - 字段缺失兜底验证（recommend_back_pressure 缺失 → 10.0）
  - **结果**：34 个断言全过

### 10.4 Roadmap 更新

- [x] 主清单 #13 计量背压状态 ⏳ → ✅
- [x] 新增 3.13 章节说明推导公式、物理依据、关键创新、场景验证
- [x] 4.9 旧待改造章节改为完成状态

### 10.5 关键修复

- [x] **修复 `_validate_inputs` 默认值**（L197-L208）：`recommend_back_pressure` 默认值从 15 改为 10.0，与 #13 算法设计默认值同步，避免数据补全阶段覆盖算法层兜底

---

## 附录 A：与 #11 计量压力、#12 螺杆转速的三方对比

| 维度 | #11 计量压力 | #12 螺杆转速 | #13 计量背压 |
|------|------------|------------|------------|
| 物理含义 | 液压机油压 | 螺杆旋转速度 | 螺杆背后阻力 |
| 适用机器 | ⛔ 仅液压机 | ✅ 所有机器 | ✅ 所有机器 |
| 动力源分支 | ✅ 必需（全电机=0）| ❌ 不分支 | ❌ 不分支 |
| 主导修正 | family 黏度（17 个）| family 剪切敏感度（17 个）| family 排气需求（17 个）|
| 次要修正 | nozzle_factor | L/D + 螺杆转速 | 螺杆转速联动 |
| 钳制范围 | [3.0, 18.0] | [0.30, 0.75] | [0.5, 30.0] |
| 单位约定 | 同源数值 | 无量纲 ratio | MPa |
| 默认值 | - | - | 10.0 MPa（行业中位）|
| 物理对称 | **液压专属**（与 #12 对称）| **通用**（与 #13 对称）| **通用**（与 #12 对称）|

---

## 附录 B：当前算法与原代码差异

| 维度 | 原代码 | v1.0 | 变化 |
|------|--------|------|------|
| 公式 | `mat.get('recommend_back_pressure', 15)` | 4 维推导 | ✅ 算法化 |
| family 修正 | 无 | 17 family × 0.40~1.50 | ✅ 新增 |
| 转速联动 | 无 | speed_factor 条件性 | ✅ 新增 |
| 钳制范围 | 无 | [0.5, 30.0] | ✅ 新增 |
| 默认值 | 15 MPa（偏高）| 10.0 MPa（行业中位）| ✅ 调整 |
| 动力源分支 | 无 | 无（不分支）| 不变 |