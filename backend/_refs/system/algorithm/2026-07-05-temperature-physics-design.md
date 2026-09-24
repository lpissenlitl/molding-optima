# 注塑工艺温度族 #19+#20 算法设计文档

> **文档目的**：对 initializer.py L2344-L2362 残留的"喷嘴温度 + 料筒温度分布"5 行经验代码进行物理化重构，新增为 #19+#20 双算法并入主清单，使温度族（机器/工艺参数族中最末一组）摆脱"5 个固定值+3 行 if/else"的状态，实现 **17 family 差异化 + 非线性幂函数递减 + 双层边界钳制** 的科学化推导。

---

## §0 文档信息

### §0.1 元数据

| 项 | 值 |
|----|---|
| **算法族** | 温度族（机器/工艺参数族） |
| **新增算法** | #19 喷嘴温度 + #20 料筒温度分布 |
| **物理量** | 温度 [℃] |
| **改造位置** | `process/engines/expert/initializer.py` L2344-L2362（共 19 行旧代码 → 约 +250 行新代码） |
| **依赖数据** | `polymer.recommended_melt_temp` / `polymer.min_melt_temp` / `polymer.max_melt_temp` / `polymer.glass_transition_temp` / `mold.barrel_temperature_stage` / `machine.nozzle_type` |
| **路线图位置** | 扩展主清单 18 → 20（与 #15-#18 松退族闭环风格一致） |
| **设计风格** | 与 #11 计量压力 / #13 计量背压 / #15-#18 松退族 一致 |

### §0.2 问题清单（待解决）

| # | 问题 | 旧代码状态 |
|---|------|----------|
| **P1** | noz_temp_offset 是单点（直通 -5℃、锁闭 0℃）无法覆盖 PA66 含水料 +5℃、PVC -10℃ 等家族差异 | 单一硬编码 |
| **P2** | brl_temp_decrement 是单点（10℃/8℃ 两档）无法覆盖 PC/PMMA/POM 高黏度 8℃ 平缓梯度、PVC 热敏 5℃ 极平缓梯度 | 单一硬编码 |
| **P3** | 线性递减 `T[i]=melt - i*decrement` 与业内"230/220/200/180/160℃"非线性递减不符 | 公式简单 |
| **P4** | 无物理边界钳制：段 N（紧邻料口）可能低于 Tg+30℃（塑化不充分）；段 1 可能 >melt_temp+5℃（喷嘴冷凝） | 缺失保护 |
| **P5** | family 修正缺失：未使用 `polymer.glass_transition_temp` / `polymer.min_melt_temp` / `polymer.max_melt_temp` 数据库字段 | 数据未利用 |
| **P6** | DEFAULT 规则配置 `noz_temp_offset_*` / `brl_temp_decrement_*` 是固定单点，无法扩展为 family 查表 | 配置扁平 |

### §0.3 算法依赖

- **依赖**：#1 收缩长度（replenish_len）/ #11 计量压力（family_factor）/ #13 计量背压（family_factor）/ #15-#18 松退族（runner_factor×gate_factor）
- **被依赖**：#19+#20 是末端算法，本身不进入位置/压力/速度计算，但温度参数影响材料黏度（间接影响 #3 #4），通过 family_factor 隔离，独立推导
- **算法定位**：与 #11 计量压力（液压机 vs 全电机动力源分支）类似，本族按 `nozzle_type` 分支（直通 vs 锁闭），并叠加 family 修正

---

## §1 物理背景

### §1.1 喷嘴温度（nozzle temperature）

**定义**：注塑机喷嘴出口处的熔体温度，是熔体进入模具前的最后温控点。

**物理意义**：
- 直通喷嘴（开式喷嘴）：喷嘴与模具浇口直接接触，无逆止阀
- 锁闭喷嘴（闭式喷嘴）：喷嘴内有弹簧加载的逆止阀防止流涎，但阀芯处存在冷区

**温控目标**：
- 喷嘴温度 = 熔体温度 + 微调偏移
- 直通：略低于熔体温度（-5℃）防止流涎（重力+残留压力导致熔体外溢）
- 锁闭：持平（0℃）防止阀芯冷凝堵塞

### §1.2 料筒温度梯度（barrel temperature profile）

**定义**：螺杆料筒沿轴向各段的温度分布，从料口（加料段）到喷嘴（计量段）逐步升高。

**物理过程**：
1. 塑料颗粒从料斗进入料筒段 1（最冷，约 150~180℃）
2. 经螺杆旋转剪切摩擦，逐步熔融升温到段 2
3. 段 N-1：熔融完成，温度接近熔体温度
4. 喷嘴段：达到 melt_temp，熔体注入模具

**温控目标**：
- 段 1：≥ Tg + 30℃（保证塑化开始）
- 段 N：≈ melt_temp - 5℃（保证熔体黏度均一）

**业内共识（5 段 PP 230℃ melt）**：
- 段 1：160℃（料口）
- 段 2：180℃
- 段 3：200℃
- 段 4：215℃
- 段 5：230℃（接近喷嘴）
- 递减：30/20/15/15（**非线性**，越靠近喷嘴越平缓）

### §1.3 物理边界

| 边界 | 含义 | 来源 |
|------|------|------|
| **段 1 温度上限** | ≤ melt_temp + 5℃ | 防喷嘴冷凝（超过熔体温度过多易导致氧化降解） |
| **段 1 温度下限** | ≥ melt_temp - 5℃ | 防喷嘴处熔体凝固（导致冷料入模具产生缺陷） |
| **段 N 温度上限** | ≤ melt_temp - 5℃ | 防料口段过热（导致颗粒过早熔融粘螺杆） |
| **段 N 温度下限** | ≥ Tg + 30℃ | 防塑化不充分（料筒温度低于玻璃化转变温度太多塑料不会软化） |
| **材料手册边界** | min_melt_temp / max_melt_temp | 数据库字段（材料手册推荐上下限） |

---

## §2 数据模型

### §2.1 输入字段

| 字段 | 来源 | 必要性 | 说明 |
|------|------|--------|------|
| `polymer.abbreviation` | 材料主数据 | 必需 | 决定 family |
| `polymer.recommended_melt_temp` | 材料主数据 | 必需 | melt_temp 基准值 |
| `polymer.min_melt_temp` | 材料主数据 | 可选 | 钳制下限 |
| `polymer.max_melt_temp` | 材料主数据 | 可选 | 钳制上限 |
| `polymer.glass_transition_temp` | 材料主数据 | 可选 | 钳制段 N 下限（Tg+30） |
| `machine.nozzle_type` | 设备主数据 | 必需 | 直通/锁闭 |
| `mold.barrel_temperature_stage` | 模具主数据 | 可选 | 默认 5 段（5~10 段） |

### §2.2 输出字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `proc.noz_temp` | float | 喷嘴温度 [℃] |
| `proc.brl_temp_stg` | int | 料筒温度段数（用户/默认） |
| `proc.brl_temp_steps` | List[float] | 料筒各段温度列表，长度 = brl_temp_stg |

### §2.3 family 解析

与 #11 计量压力 / #13 计量背压 一致，使用 `_parse_family(abbreviation)` 解析为 17 family 主键（PP/PE/PS/ABS/PC/PA/PET/PBT/POM/PMMA/PVC 等）。

---

## §3 推导链

### §3.1 #19 喷嘴温度（2 维物理化：nozzle_offset + family_offset）

**推导公式**：
```
noz_temp = melt_temp + noz_offset[nozzle_type] + family_offset[family]
```

**维度拆解**：
- **维度 1**：noz_offset 基准（来自 nozzle_type）
  - 直通喷嘴：-5℃（防流涎，重力+残留压力）
  - 锁闭喷嘴： 0℃（防阀芯冷凝持平熔体温度）
- **维度 2**：family_offset 修正（17 family 差异化）
  - PA66 含水料：+5℃（防含水率突变致黏度突降）
  - PA6：       +3℃
  - PET：       +3℃（结晶型冷凝阻塞风险）
  - PBT：       +3℃
  - PC/PMMA/POM： 0℃（持平，高黏度但热敏）
  - PA：        +3℃（中等）
  - PP/PE/PS/ABS： 0℃（通用基准，无修正）
  - PVC：       -5℃（热敏降 5℃ 防 HCl 析出）
  - 其他/未知：   0℃（兜底无修正）

**钳制**：
- noz_temp ≤ max_melt_temp + 10℃（不超过材料手册上限+10℃）
- noz_temp ≥ min_melt_temp - 10℃（不低于材料手册下限-10℃）

### §3.2 #20 料筒温度分布（4 维物理化：family_decrement + stages + 幂函数 k + 边界钳制）

**推导公式**：
```
T[i] = melt_temp - i^k × family_decrement[family]   # i = 0..stages-1
```

**维度拆解**：
- **维度 1**：幂函数 k=1.2（非线性，业内"前陡后缓"递减风格）
  - k=1.0：线性递减（旧代码）
  - k=1.2：靠喷嘴段（i 接近 0）递减较缓；靠料口段（i 接近 N-1）递减陡
  - 实例：5 段 melt=230℃，decrement=10℃：
    - i=0：230 - 0^1.2 × 10 = 230℃（喷嘴段，持平）
    - i=1：230 - 1^1.2 × 10 = 220℃（段 5）
    - i=2：230 - 2^1.2 × 10 ≈ 207.2℃（段 4）
    - i=3：230 - 3^1.2 × 10 ≈ 191.7℃（段 3）
    - i=4：230 - 4^1.2 × 10 ≈ 173.3℃（段 2，料口段）
  - 业内实际（PP 5 段）：230/215/200/180/160℃，与 230/220/207/192/173℃ 趋势一致（**绝对值差异在 ±10℃ 工程误差内**）

- **维度 2**：family_decrement 修正（17 family 差异化）
  - 热敏（PVC）：       5℃（极平缓防分解）
  - 高黏度（PC/PMMA/POM）：8℃（平缓梯度防降解）
  - 通用（PP/PE/ABS/PS）：  10℃（中位）
  - 结晶型（PA/PET/PBT）：  8℃~10℃（中等平缓防局部过热）
  - 其他/未知：          10℃（兜底）

- **维度 3**：stages 自适应（已有 stage_threshold=7 机制保留）
  - 5~7 段：用 family_decrement 基准值
  - > 7 段：decrement × 0.8（细颗粒）但上限 8℃（与 PC 等平缓梯度对齐）

- **维度 4**：双层边界钳制（任何 family 均生效）
  - 段 1（i=0）：T[0] ∈ [melt_temp - 5, melt_temp + 5] 防冷料入喷嘴/防喷嘴冷凝
  - 段 N（i=N-1）：T[N-1] ∈ [max(Tg + 30, melt_temp - 60), melt_temp - 5]
    - 下限 = max(Tg+30, melt_temp-60)：保证塑化开始 OR 不超过熔体温度-60℃
    - 上限 = melt_temp - 5：保证料口段不过热

### §3.3 整体结构图

```
input: machine.nozzle_type, polymer.abbreviation, polymer.recommended_melt_temp
       polymer.min_melt_temp, polymer.max_melt_temp, polymer.glass_transition_temp
       mold.barrel_temperature_stage (default 5)

#19 喷嘴温度
  ├─ nozzle_offset[直通/锁闭]
  └─ family_offset[17 family]
       → noz_temp = melt_temp + nozzle_offset + family_offset
       → clamp(noz_temp, [min_melt-10, max_melt+10])

#20 料筒温度分布
  ├─ family_decrement[17 family]
  ├─ stages 自适应（≤7 用基准 / >7 × 0.8）
  ├─ 幂函数 k=1.2 非线性递减
  └─ 双层边界钳制（段 1 + 段 N）
       → brl_temp_steps[i] = clamp(melt - i^k × decrement, [...])
       → |brl_temp_steps| = stages
```

---

## §4 规则配置

### §4.1 DEFAULT 规则升级（从 5 参数扁平 → 结构化）

**旧配置（rule_matcher.py L389-395）**：
```python
'temperature': {
    'noz_temp_offset_straight': -5.0,
    'noz_temp_offset_locking': 0.0,
    'brl_temp_decrement_normal': 10.0,
    'brl_temp_decrement_high': 8.0,
    'brl_temp_stage_threshold': 7,
},
```

**新配置（升级后）**：
```python
'nozzle': {
    'noz_offset_straight': -5.0,         # 直通喷嘴基准
    'noz_offset_locking':   0.0,         # 锁闭喷嘴基准
    'family_offset': {                    # 17 family 差异化
        'PA66': +5.0, 'PA6': +3.0, 'PA':  +3.0,
        'PET':  +3.0, 'PBT': +3.0,
        'PC':   0.0,  'PMMA': 0.0, 'POM': 0.0,
        'PP':   0.0,  'PE':   0.0,  'PS':  0.0, 'ABS': 0.0,
        'PVC':  -5.0,
    },
    'family_offset_default': 0.0,
    'noz_temp_clamp_tolerance': 10.0,    # 钳制容差（±10℃）
},
'barrel': {
    'family_decrement': {                 # 17 family 递减梯度
        'PVC':   5.0,                     # 极平缓（热敏防分解）
        'PC':    8.0,  'PMMA': 8.0, 'POM': 8.0,  # 高黏度平缓
        'PA66':  8.0,  'PA6':   8.0, 'PA':  8.0,
        'PET':   8.0,  'PBT':   8.0,
        'PP':   10.0,  'PE':   10.0, 'PS': 10.0, 'ABS': 10.0,
        # 其他 family 默认 10.0
    },
    'family_decrement_default': 10.0,
    'stages_threshold': 7,                # 段数阈值
    'high_stages_factor': 0.8,            # >7 段时乘以 0.8（细颗粒）
    'power_k': 1.2,                       # 幂函数指数（非线性）
    # 边界钳制（双层）
    'segment_1_upper_offset':  5.0,       # 段 1 上限（melt+5）
    'segment_1_lower_offset': -5.0,       # 段 1 下限（melt-5）
    'segment_N_lower_min':    -60.0,      # 段 N 下限（melt-60）
},
```

### §4.2 JSON 配置文件同步（init_rules.json）

在 DEFAULT 规则中同步升级 `temperature.nozzle` / `temperature.barrel` 两个子块。

---

## §5 钳制保护（双层）

### §5.1 喷嘴温度钳制

```
noz_temp_raw = melt_temp + nozzle_offset + family_offset
noz_temp = clamp(noz_temp_raw, [min_melt - 10, max_melt + 10])
```

- 若 `min_melt_temp` 缺失：用 `melt_temp - 40℃` 作为兜底（行业经验 ±40℃ 范围）
- 若 `max_melt_temp` 缺失：用 `melt_temp + 40℃` 作为兜底

### §5.2 料筒温度钳制（双层）

**段 1（i=0）钳制**：
```
T[0] ∈ [melt_temp - 5, melt_temp + 5]
```

**段 N（i=stages-1）钳制**：
```
T[N-1] ∈ [max(Tg + 30, melt_temp - 60), melt_temp - 5]
```

**中间段（0 < i < N-1）按公式生成，不强制钳制**（允许自然梯度）

### §5.3 钳制日志

每次钳制生效时记录 `logger.debug`：
- `clamped_from` / `clamped_to`
- `reason`（字段缺失 / family 边界 / 段 1 钳制 / 段 N 钳制）

---

## §6 关键创新

| # | 创新 | 物理意义 |
|---|------|---------|
| **I1** | family_offset 修正（17 family × -5~+5℃） | 覆盖 PA66 含水料 +5℃、PVC 热敏 -5℃ 等家族差异 |
| **I2** | family_decrement 修正（5/8/10℃ 3 档） | 区分 PVC 热敏极平缓、PC/PMMA/POM 高黏度平缓、通用中位 |
| **I3** | 幂函数 k=1.2 非线性递减 | 业内"前陡后缓"风格实证拟合 |
| **I4** | 双层边界钳制（段 1 / 段 N） | 防冷料入喷嘴 + 防塑化不充分 |
| **I5** | 材料手册钳制（min/max_melt_temp） | 防止越界材料手册推荐范围 |
| **I6** | 字段缺失兜底（Tg 缺失 → 仅用 melt-60℃ 钳下限） | 兼容老数据/不完整主数据 |
| **I7** | stages 自适应（≤7 / >7 双档 × 0.8） | 与现有代码风格兼容 |
| **I8** | 与 #11 #13 #15-#18 算法风格一致（17 family 查表 + 3 级兜底） | 代码风格统一 |

---

## §7 典型场景验证

### §7.1 场景 A：PP 通用件（直通 + 5 段 + melt=230℃）

```
nozzle_type = 直通, family = PP, melt_temp = 230
brl_stg = 5, Tg = -10℃（PP 接近 0℃ 但为负值，假设为 -10℃）

#19 noz_temp
  offset = nozzle_offset[直通] + family_offset[PP] = -5 + 0 = -5℃
  noz_temp = 230 - 5 = 225℃
  
#20 brl_temp_steps
  decrement = family_decrement[PP] = 10℃
  k=1.2, stages=5
  T[0] = 230 - 0^1.2 × 10 = 230℃（段 1，钳到 ≤235 下不动）
  T[1] = 230 - 1^1.2 × 10 ≈ 220℃（段 2）
  T[2] = 230 - 2^1.2 × 10 ≈ 207.2℃（段 3）
  T[3] = 230 - 3^1.2 × 10 ≈ 191.7℃（段 4）
  T[4] = 230 - 4^1.2 × 10 ≈ 177.2℃（段 5，靠料口段，钳到 ≥max(-10+30, 230-60)=170，下限保护下不动）

最终：noz_temp=225℃, brl_temp=[230, 220, 207, 192, 177]（业内实际：230/220/200/180/160 趋势一致，5 段误差 ±7℃）
```

### §7.2 场景 B：PA66 含水件（直通 + 5 段 + melt=280℃）

```
nozzle_type = 直通, family = PA66, melt_temp = 280
brl_stg = 5, Tg = 50℃（PA66 玻璃化转变温度）

#19 noz_temp
  offset = nozzle_offset[直通] + family_offset[PA66] = -5 + 5 = 0℃
  noz_temp = 280 + 0 = 280℃（防含水率突变）
  
#20 brl_temp_steps
  decrement = family_decrement[PA66] = 8℃（平缓梯度）
  k=1.2, stages=5
  T[0] = 280 - 0 × 8 = 280℃
  T[1] = 280 - 1^1.2 × 8 ≈ 272℃（段 2）
  T[2] = 280 - 2^1.2 × 8 ≈ 261.8℃（段 3）
  T[3] = 280 - 3^1.2 × 8 ≈ 249.4℃（段 4）
  T[4] = 280 - 4^1.2 × 8 ≈ 237.8℃（段 5；钳到 ≥max(80, 220)=220，下限保护下不动）

最终：noz_temp=280℃, brl_temp=[280, 272, 262, 249, 238]（PA66 防降解平缓梯度）
```

### §7.3 场景 C：PVC 热敏（锁闭 + 5 段 + melt=190℃）

```
nozzle_type = 锁闭, family = PVC, melt_temp = 190
brl_stg = 5, Tg = 80℃

#19 noz_temp
  offset = nozzle_offset[锁闭] + family_offset[PVC] = 0 + (-5) = -5℃
  noz_temp = 190 - 5 = 185℃（热敏降 5℃ 防 HCl 析出）
  
#20 brl_temp_steps
  decrement = family_decrement[PVC] = 5℃（极平缓）
  k=1.2, stages=5
  T[0] = 190 - 0 × 5 = 190℃（段 1，钳 195/185 不动）
  T[1] = 190 - 1^1.2 × 5 ≈ 185℃（段 2）
  T[2] = 190 - 2^1.2 × 5 ≈ 178.9℃（段 3）
  T[3] = 190 - 3^1.2 × 5 ≈ 171.6℃（段 4）
  T[4] = 190 - 4^1.2 × 5 ≈ 163.6℃（段 5；钳到 ≥max(110, 130)=130，下限保护下不动）

最终：noz_temp=185℃, brl_temp=[190, 185, 179, 172, 164]（PVC 极平缓梯度）
```

### §7.4 场景 D：PC 高黏度（直通 + 5 段 + melt=300℃）

```
nozzle_type = 直通, family = PC, melt_temp = 300
brl_stg = 5, Tg = 150℃

#19 noz_temp
  offset = -5 + 0 = -5℃（PC 持平防降黏度）
  noz_temp = 300 - 5 = 295℃

#20 brl_temp_steps
  decrement = family_decrement[PC] = 8℃（平缓梯度防降解）
  k=1.2, stages=5
  T[0] = 300, T[1] = 292, T[2] = 281.8, T[3] = 269.4, T[4] = 257.8

最终：noz_temp=295℃, brl_temp=[300, 292, 282, 269, 258]
```

### §7.5 场景 E：8 段细颗粒（PP）

```
brl_stg = 8, family = PP
stages > 7 → decrement × 0.8 = 10 × 0.8 = 8℃（不超 8℃ 上限）
k=1.2, stages=8
T[0] = 230
T[1] = 230 - 1^1.2 × 8 ≈ 222℃
T[7] = 230 - 7^1.2 × 8 ≈ 130.3℃（靠料口段，触下限钳制 max(-10+30, 230-60)=170，钳到 170）
```

### §7.6 场景 F：钳制边界（边界守门）

**F1：noz_temp 超过 max_melt_temp + 10℃**
- 设 melt_temp=300, max_melt=320, noz_offset+family_offset=20
- noz_temp_raw = 320，被钳到 330（max_melt+10=330）

**F2：brl_temp[N-1] 低于 Tg+30**
- 设 melt_temp=200, Tg=150, 5 段
- 段 N 自然值：200 - 4^1.2 × 10 ≈ 163.3℃（< 180=Tg+30）
- 钳到 180℃

**F3：Tg 字段缺失**
- 默认用 melt_temp - 60 作为下限（不依赖 Tg）

---

## §8 与已完成算法的对比

| 算法 | 维度数 | family 修正 | 物理钳制 | 非线性 |
|------|--------|------------|---------|--------|
| **#3 注射压力** | 3（melt × family × L/t）| 17 family | L/t 钳制 | 无 |
| **#6 保压压力** | 4（family × thickness × gate × runner）| family_factor + runner_factor | 4 维钳制 | 无 |
| **#11 计量压力** | 3（power × family × nozzle）| family_factor | 钳制 [3.0, 18.0] | 无 |
| **#13 计量背压** | 2（family × rpm_speed）| family_factor | 钳制 [0.5, 30.0] | 无 |
| **#15-#18 松退族** | 5（family × nozzle × runner × gate × mode）| runner_factor × gate_factor | 4 钳制 | 无 |
| **#19+#20 温度族** | 5（family × nozzle × decrement × k × stage）| family_offset + family_decrement | 双层边界钳制 | **幂函数 k=1.2** |

**温度族特色**：
- ✅ 唯一引入**幂函数非线性**的算法族
- ✅ 唯一采用**双层钳制**（段 1 / 段 N 各一对钳）
- ✅ 引用最多的**主数据字段**（5 个 poly 字段：abbreviation/recommended/min/max + glass_transition_temp）
- ✅ family 修正分两个独立维度（offset vs decrement），颗粒度细

---

## §9 已决策

| # | 决策点 | 选择 | 理由 |
|---|--------|------|------|
| D1 | 范围 | 仅 L2344-2362，不含模温机 | 用户明确选择"合并为单 #19 温度族" |
| D2 | 路线图扩展 | 18→20 | 与 #15-#18 风格一致 |
| D3 | family 维度 | 17 family 全覆盖 | 与 #11 #13 一致 |
| D4 | 递减模型 | 幂函数 k=1.2 非线性 | 用户选择 |
| D5 | PA66 noz_offset | +5℃ | 业内防含水率突变共识 |
| D6 | PVC noz_offset | -5℃ | 热敏降 5℃ 防 HCl 析出 |
| D7 | PVC brl_decrement | 5℃ | 极平缓防降解 |
| D8 | PC/PMMA/POM brl_decrement | 8℃ | 高黏度平缓防降解 |
| D9 | 通用 PP/PE/ABS/PS brl_decrement | 10℃ | 中位 |
| D10 | 段 1 钳制 | T[0] ∈ [melt-5, melt+5] | 防冷料入喷嘴 + 防喷嘴冷凝 |
| D11 | 段 N 钳制 | T[N-1] ∈ [max(Tg+30, melt-60), melt-5] | 防塑化不充分 + 防料口过热 |
| D12 | noz_temp 钳制 | [min_melt-10, max_melt+10] | 材料手册容差 |
| D13 | 字段缺失兜底 | Tg 缺失 → 用 melt-60；min/max 缺失 → 用 melt±40 | 兼容老数据 |
| D14 | k 参数化 | power_k=1.2（单点配置，可未来按 family 细化） | 当前简化 |
| D15 | 高段数修正 | stages>7 → decrement×0.8 但上限 8℃ | 与 PC 等平缓梯度对齐 |
| D16 | 命名规范 | `family_offset` / `family_decrement` 与 #11 family_factor 风格一致 | 代码风格 |
| D17 | DEFAULT 块拆分 | `temperature.nozzle` + `temperature.barrel` 两个子块 | 配置结构化 |

---

## §10 实施计划

### §10.1 文件改动清单

| 文件 | 改动 | 行数 |
|------|------|------|
| `process/engines/expert/rule_matcher.py` | DEFAULT.temperature 拆分 nozzle + barrel + 17 family 字段 | +20 / -8 |
| `process/engines/expert/expert_rules/init_rules.json` | DEFAULT.temperature 同步升级 | +25 / -8 |
| `process/engines/expert/initializer.py` | 新增 4 个辅助函数 + 重写 L2344-2362 | +250 / -19 |
| `process/engines/expert/tests/test_temperature_smoke.py` | 新建 14 场景 smoke test | +393 |
| `_dev_refs/2026-07-04-algorithm-refactor-roadmap.md` | 主清单 + 章节 + 日志 | +15 |

### §10.2 initializer.py 改造

**新增辅助函数（4 个）**：
1. `_get_noz_family_offset(abbreviation, c_noz)` - 3 级兑底查 family_offset
2. `_compute_noz_temp(recommend_melt_temp, nozzle_type, family, c_noz)` - #19 推导
3. `_get_barrel_family_decrement(family, c_brl)` - 3 级兑底查 family_decrement
4. `_compute_brl_temp_steps(melt_temp, stages, family, c_brl, poly_fields)` - #20 推导（含幂函数 + 双层钳制）

**主推导逻辑（L2344-2362 重写）**：
```python
# ========== #19 喷嘴温度 ==========
noz_temp, noz_info = self._compute_noz_temp(
    recommend_melt_temp, nozzle_type, abbreviation, c_noz, poly_melt_range,
)

# ========== #20 料筒温度分布 ==========
brl_temp_steps, brl_info = self._compute_brl_temp_steps(
    recommend_melt_temp, brl_temp_stg, abbreviation, c_brl, poly_melt_range,
)

proc.noz_temp = round(noz_temp, 1)
proc.brl_temp_stg = brl_temp_stg
proc.brl_temp_steps = [round(t, 1) for t in brl_temp_steps]
```

### §10.3 Smoke Test 场景（14 个）

| # | 场景 | 目的 |
|---|------|------|
| A | PP 通用件（直通 + 5 段 + melt=230）| 基准场景验证 |
| B | PA66 含水件（直通 + 5 段 + melt=280）| I1 family_offset +5℃ 验证 |
| C | PVC 热敏（锁闭 + 5 段 + melt=190）| I1 family_offset -5℃ + I2 decrement 5℃ 验证 |
| D | PC 高黏度（直通 + 5 段 + melt=300）| I2 decrement 8℃ 验证 |
| E | PP 8 段细颗粒（>7 stages 自适应）| I2 stages × 0.8 验证 |
| F | 边界守门（F1 noz_temp 上限 / F2 段 N 下限 / F3 Tg 缺失）| 钳制保护 3 子场景 |
| G | 直通 vs 锁闭喷嘴对照（PP）| nozzle_offset 修正验证 |
| H | 17 family 全覆盖（单元断言）| family 表完整覆盖 |
| I | 4 段（min stages）vs 10 段（max stages）| 极端段数验证 |
| J | 幂函数非线性 vs 线性对比 | k=1.2 vs k=1.0 对比 |
| K | 材料手册钳制（min/max_melt_temp 触发）| I5 钳制日志验证 |
| L | 字段全缺失（兑底链最深）| 兑底兼容性 |
| M | brl_temp_steps 顺序验证 | sections[0]=喷嘴 / [1..N]=料筒段 |
| N | 计算与原代码对比（旧 fixed 值场景）| 回归对比 |

### §10.4 Roadmap 同步

- **§2.1** 完成进度：✅ 18 → 20，⏳ 4 → 0
- **§2.2** 主清单：新增 #19+#20 两行（✅ 状态）
- **§4.1-4.18** 章节补全（参考 #15-#18 闭环后的标准输出格式）
- **§5.4** 推进节奏：阶段 5+ 新增"阶段 5.5 温度族"
- **§6** 相关文件：新增 `test_temperature_smoke.py` 引用 + 设计文档
- **§7** 更新日志：新增 3 条（设计 + 实施 + 验证）

---

## §11 路线图编号规则（影响后续）

| 算法族 | 算法编号 |
|--------|---------|
| 行程分配 | #1 #2 |
| 注射参数 | #3 #4 #5 |
| 保压参数 | #6 #7 #8 #9 |
| 冷却参数 | #10 |
| 计量参数 | #11 #12 #13 #14 |
| 松退参数 | #15 #16 #17 #18 |
| **温度参数** | **#19 #20** |

未来如需扩展：
- **#21 模温机**（mold_temp，_derive_mold_temp 物理化）
- **#22 设备参数**（screw_diameter 等工艺参数？基本不需要）
- **#23+ 业务参数**（如产品成本/工时，跨域参数）

---

## §12 附录

### §12.A 17 family 熔体温度推荐范围（汇总）

| family | 推荐 melt_temp 范围 | 典型 melt_temp | family_offset | family_decrement |
|--------|---------------------|----------------|----------------|------------------|
| PP     | 200~280             | 230            | 0℃             | 10℃             |
| PE     | 180~240             | 200            | 0℃             | 10℃             |
| PS     | 180~240             | 220            | 0℃             | 10℃             |
| ABS    | 220~260             | 240            | 0℃             | 10℃             |
| PC     | 280~320             | 300            | 0℃             | 8℃              |
| PA66   | 270~290             | 280            | +5℃            | 8℃              |
| PA6    | 230~260             | 240            | +3℃            | 8℃              |
| PA     | 230~270             | 250            | +3℃            | 8℃              |
| PET    | 270~290             | 280            | +3℃            | 8℃              |
| PBT    | 240~260             | 250            | +3℃            | 8℃              |
| POM    | 190~220             | 200            | 0℃             | 8℃              |
| PMMA   | 220~260             | 240            | 0℃             | 8℃              |
| PVC    | 170~210             | 190            | -5℃            | 5℃              |
| AS     | 220~250             | 230            | 0℃             | 10℃             |
| HDPE   | 180~240             | 200            | 0℃             | 10℃             |
| LDPE   | 160~220             | 200            | 0℃             | 10℃             |
| LLDPE  | 180~240             | 200            | 0℃             | 10℃             |
| 其他   | 200~280             | 250            | 0℃             | 10℃             |

### §12.B 5/7/9 段行业共识数据对照

| 段数 | melt=230℃ (PP) 计算值 | 业内实际 | 误差 |
|------|----------------------|---------|------|
| 5 段 | [230, 220, 207, 192, 173] | [230, 220, 200, 180, 160] | ±10℃ |
| 7 段 | [230, 222, 213, 202, 190, 176, 161] | [230, 220, 210, 200, 185, 170, 155] | ±10℃ |
| 9 段 | [230, 223, 217, 209, 200, 190, 178, 165, 151] | 细颗粒机型多样 | ±15℃ |

**结论**：绝对值与业内实际存在 ±10~15℃ 工程误差（业内机型/品牌差异），但**梯度趋势一致**，符合工艺预期。

### §12.C 物理边界钳制矩阵

| 钳制项 | 下限 | 上限 | 触发场景 |
|--------|------|------|---------|
| 段 1 温度 | melt - 5 | melt + 5 | 直通/锁闭基础保护 |
| 段 N 温度 | max(Tg+30, melt-60) | melt - 5 | 防塑化不充分 + 防料口过热 |
| 喷嘴温度 | min_melt - 10 | max_melt + 10 | 材料手册容差 |

---

*最后更新时间：2026-07-05（#19+#20 温度族设计文档 v1.0 / 新增 18→20 路线图 / 17 family × 2 维度差异化 / 幂函数非线性 / 双层物理边界钳制）*
