# 超行程参数处理方案（初始化链路校验 + 优化侧矛盾修复 + DEMO 数据修正）

> 状态：**批次 1 / 2 / 3 全部实施完成并验收通过**（口径已由用户拍板，见 §3、§7）
> 起因：用户实测「智能调机 → 获取初始工艺」，产出的计量终止位置 758.07mm，而机台最大注射行程仅 200mm。

---

## §1 现象与实测证据

### 1.1 用户界面数据（DEMO）

| 维度 | 值 |
|---|---|
| 模具 | MOLD-DEMO-001 仪表盘外壳模具（2 腔，制品总重 560g） |
| 机台 | IMM-DEMO-001 海天 MA1600/540（最大注射行程 **200mm**、最大注射重量 240g、锁模力 160 **ton**） |
| 材料 | PP-H040 |
| 产出 | 计量终止位置 **758.07**、计量位置 752.47、注射位置 716.62/342.08/154.82/42.46 |

### 1.2 758.07 的完整来历（已逐位对上）

```
制品总重 560g ÷ PP 熔体密度 0.735 g/cm³ ÷ 36mm 螺杆截面积 1017.9mm²
  ⇒ 理论充填长度 total_len ≈ 748.6mm
  ⇒ met_pos_1 = VP 切换位置(3.87) + total_len = 752.47
  ⇒ met_end_pos = met_pos_1 + 储后松退距离(5.6) = 758.07   ← 专家引擎 #18 公式
```

### 1.3 实跑复现（cond 105，真实 DB + 真实规则库）

```
--- items (7) ---
   brl_temp_1      cur=230.0   rec=231.0                dir=increase
   met_end_pos     cur=758.07  rec=760.1892029220222    dir=increase   ← 推荐把超行程值再加大
   met_end_pos     cur=758.07  rec=None                  dir=check      ← 同时说"本机无法成形"
   inj_t           cur=4.0     rec=4.539                dir=increase
   inj_spd_1       cur=34.0    rec=36.298               dir=increase
   hold_spd_1      cur=14.0    rec=16.227               dir=increase
   hold_pres_1     cur=61.0    rec=63.382               dir=increase
--- new_parameter 变化 ---
   met_end_pos  758.07 -> 760.19     ← 推荐值真的写回参数
```

**同屏自相矛盾**：一条说「↑ 加大到 760」，一条说「🔍 本机无法成形」。

### 1.4 修复后（批次 1 + 批次 2 生效，同一 cond 105 重跑）

```
--- items (6) ---                                   ← 7 → 6（数值推荐那一条已被剔除）
   brl_temp_1      cur=230.0   rec=231.0                dir=increase
   inj_t           cur=4.0     rec=4.539                dir=increase
   inj_spd_1       cur=34.0    rec=36.298               dir=increase
   hold_spd_1      cur=14.0    rec=16.227               dir=increase
   hold_pres_1     cur=61.0    rec=63.382               dir=increase
   met_end_pos     cur=758.07  rec=None                  dir=check      ← 只剩告知
--- new_parameter ---
   met_end_pos = 758.07（不再被推到 760.19）            inj_pos_1 = 716.62
```

日志留痕：`剔除超行程位置参数的数值推荐: [{'param': 'MEL', 'current': 758.07, 'recommended': 760.189…}]`。

---

## §2 根因（三层，均已核实）

| 层 | 现状 | 有无范围校验 |
|---|---|---|
| **L1 专家引擎（设定值类）** | 压力/速度/转速按机台 `max_set_*` 钳位 | ✅ 118≤140、34≤90、61≤140 全部合规 |
| **L2 专家引擎（位置类）** | 充填长度 748.6mm 原样输出 | ❌ **无行程钳位** |
| **L3 初始化链路校验器** | `DataValidator` 只校验**字段完整性 / 必填 / 类型** | ❌ **不校验数值范围** |
| **L4 初始化 service** | `parameter_initialize.py` 中 `max_injection_stroke` / 行程 / 钳 / clip **零匹配** | ❌ 整条链路没碰机台上限 |
| **L5 优化链路** | 越限识别（`detect_over_stroke_limits`）+ check 告知 + 设定值类 400 | ✅ 有，**但只覆盖优化，不覆盖初始化** |

### 2.1 为什么优化侧照样推荐 760

规则 `IF SHORTSHOT_low THEN MEL_add_2` 的**前件是缺陷**，不是 MEL 当前值 ⇒
`MEL` 是**结论变量** ⇒ 758.07 根本没参与判档，规则说「加大 2.12」⇒ 758.07 + 2.12 = 760.19。
且位置类推荐值**从不被裁剪**（`_apply_machine_limits` 只按族裁设定值类，MEL 无族前缀）。

### 2.2 我此前「会校验」的说法为何不成立

此前说的「校验」是**模糊推理的论域层**（`fuzzy/specs.py` 位置类论域取设备行程 + G6 守卫），
那是**优化链路**、管的是**判档**不是**参数值**。**初始化链路从来没有这一层**。

---

## §3 口径决策（用户 2026-11-10 拍板）

| # | 议题 | 决策 |
|---|---|---|
| Q1 | 初始化位置类参数超出行程时怎么响应 | **拒绝报错 400**（不裁剪、不只告警） |
| Q2 | DEMO 数据本身不匹配要不要一起修 | **一起修** |
| Q3 | 优化侧「超行程仍推荐 760」的矛盾要不要一起修 | **一起修**（超行程位置类参数不产出数值推荐，只保留 check 告知） |

**为什么选「拒绝报错」而不是「钳位到上限」**：
产品充填需求 748.6mm 而行程仅 200mm ⇒ 本机做不出来（欠充填 3/4）。
钳到 200mm 仍是错的建议（缺料），会让操作工以为「调到 200 就行」⇒ 比报错更危险。

---

## §4 实施清单（分 3 批，每批独立可验证）

### 批次 1｜初始化链路超行程拒绝 400（根因）

| 文件 | 改动 |
|---|---|
| `backend/process/exceptions.py` | 新增 `ERROR_PROCESS_OVER_STROKE = BizErrorCode.create(MOD_PROCESS, 38, ...)` |
| `backend/process/services/parameter_initialize.py` | 新增 `_guard_over_stroke()`；在 `from_masterdata` 落库前、`infer_from_provided` 返回前调用 |

**判定实现（复用既有口径，不新建第二套）**：

```
machine_info ──resolve_position_limits()──► {IL/ML/MEL/VPTL: 200.0}     ← fuzzy/specs.py
flat 业务名 ──to_algo_params()─────────► {MEL: 758.07, ML0: 752.47, ...} ← fuzzy/field_names.py
            ──detect_over_stroke_limits()──► 超行程记录                   ← fuzzy/over_limit.py
```

复用理由：`fuzzy/over_limit.py` 是既有的越限识别口径唯一来源（纯函数），优化链路已在用；
`max_injection_stroke` **已在** `MACHINE_INFO_FIELDS` 里（`condition: 可选`，来自 `InjectionUnit`）
⇒ 初始化链路的 `machine_info` 已经带着行程值，**不需要改字段 spec**。

**依赖方向**：`process.services` → `process.algorithms.fuzzy.*`；
fuzzy 包不 import services ⇒ 无循环（`parameter_optimize.py` 已走同一方向）。

**文案口径**（与优化链路区分）：
- 优化链路 = 「用户把参数设错了」⇒ 改个值就能继续
- 初始化链路 = 「产品与机台能力不匹配」⇒ 用户改不了 ⇒ 文案指向**换机**
  （口径：**以产品为目标**，产品形态已定 ⇒ 不给「减重 / 减腔」这类迁就设备的建议）

**实施结果（已完成，验收通过）**：

- `exceptions.py`：新增 `ERROR_PROCESS_OVER_STROKE`（MOD_PROCESS / 38）—— 38 是 MOD_PROCESS 段最后一个已用码（30~37）。
- `parameter_initialize.py`：
  - 3 个 import：`to_algo_params` / `detect_over_stroke_limits` / `resolve_position_limits`；
  - 新增 `_param_label`（取 `ProcessParameter.verbose_name` ⇒ 中文标签，与
    `parameter_optimize._param_label` 同口径；**两处各写一份**，不抽公共模块）；
  - 新增 `_format_limit_number`（整数不带小数尾巴，同上口径）；
  - 新增 `_guard_over_stroke(process_flat, machine_info)`：
    **缺行程不判**（缺数据 ≠ 参数不合理）⇒ 超出则取 `exceeded_by` 最大项合并成一条文案，
    `raise BizException(ERROR_PROCESS_OVER_STROKE, message)`；
  - 调用点 1：`infer`（from_masterdata）Step 4 落库**前**新增「Step 3.5」
    （在 `transaction.atomic()` 内 ⇒ 抛异常自动回滚，不留脏 condition）；
  - 调用点 2：`infer_from_provided`（纯推理）flat 化之后。
- 文案（实测，精简后）：
  > 当前设备无法生产该制品 - **熔胶终止位置**需 758.07mm，超出本机注射行程 200mm
  > （另有 3 项超出行程），请更换行程更大的设备

  > ⚠️ 精简前的版本（已废弃，冗余且口径有偏）：
  > 「工艺参数超出机台可设定范围 - 按当前制品参数计算，熔胶终止位置需 758.07mm，
  > 超出本机最大注射行程 200mm（另有 3 项位置参数同样超出行程）—— 该产品的充填量需求
  > 超出本机行程能力，本机无法成形；请改用行程更大的设备，或减轻制品重量 / 减少型腔数」
  >
  > 两处废弃点：①「超出本机行程能力，本机无法成形」与前半句「超出最大注射行程」同义重复
  > （结论已由错误码标题承担）；②「减轻制品重量 / 减少型腔数」是站在「迁就设备」的口径，
  > 与「以产品为目标」相违 ⇒ 出路只保留「更换行程更大的设备」。
  >
  > 优化链路的告知文案（`parameter_optimize.py`）同步精简为同口径：
  > 「熔胶终止位置当前 758.07mm，超出本机注射行程 200mm（另有 3 项超出行程），
  > 本机无法生产该制品，请更换行程更大的设备」

### 批次 2｜优化侧：超行程位置类参数不产出数值推荐

| 文件 | 改动 |
|---|---|
| `backend/process/services/parameter_optimize.py` | 新增 `_drop_over_stroke_value_recommendations()`；`_append_position_over_stroke_notices()` 改为接收 `stroke_items`；调用点串联「识别 → 剔除 → 告知」 |

- 剔除发生在 `_normalize_recommendations` **之前** ⇒ 此时 `param` 是算法名 ⇒ 与
  `OverLimitItem.param_name` 同命名空间 ⇒ 可直接匹配剔除
- 只剔除**位置类超行程**的参数；其它参数（注射速度/压力/保压…）推荐照常
- check 告知保留（`direction='check'`，前端已支持展示）
- 剔除判据与 `_apply_recommendations_to_baseline` 的写回判据**严格一致**
  （都是 `recommended_value is not None`）⇒ 凡是会被写回 baseline 的数值推荐必被剔除 ⇒ 不漏网
- **不剔除当前值**：baseline 里超行程的原值照旧保留（那是既有工艺的事实），
  本轮只管「别再往上推」

**实施结果（已完成，验收通过）**：cond 105 重跑 ⇒ items 7 → 6，
`met_end_pos` 只剩 check 告知，`new_parameter met_end_pos = 758.07`（不再被推到 760.19），
其余 5 条数值推荐不受影响。

### 批次 3｜DEMO 数据修正

**当前是四重不匹配**（不只是重量）：

| 项 | 需求 | 供给（IMM-DEMO-001） | 能否靠减重解决 | 系统有判据吗 |
|---|---|---|---|---|
| 充填长度（位置类） | 748.6mm | 行程 200mm | ✅ 可（重量降下来即可） | ✅ **有**（本轮批次 1 补上） |
| 注射量 | 560g | 240g | ✅ 可 | ❌ 无 |
| **锁模力** | **800 ton** | **160 ton** | ❌ **不可**（由投影面积决定，与重量无关） | ❌ 无 |
| 模具尺寸 | 1200×900×850mm | 容模 ≤ 1100×1100、厚 ≤ 800 | ❌ 不可 | ❌ 无 |

⚠️ **单位更正**：模具 `Mold.min_clamping_force` / `Mold.recommended_tonnage` 单位是 **ton**
（`verbose_name="最小锁模力 [ton]"` / `"推荐注塑机吨位 [Ton]"`），机台
`InjectionMoldingMachine.max_clamping_force` 单位也是 **ton**
⇒ 800 ton vs 160 ton 是 **5 倍**缺口（不是原先估的 kN 量级）。

⚠️ **只有行程有判据**：锁模力校验需要 `projected_area`（GatingSystem 表）+ 机台锁模力
**成对**使用，而 `projected_area` 字段**不存在**（`fuzzy/specs.py` 注释已明说
「未来候选，本期未纳入」）⇒ 锁模力 / 注射量 / 模具尺寸三类机台约束**系统层面根本没有判据**
（`min/max_mold_length` 等容模参数全库零业务引用）⇒ 改了 DEMO 数据程序也不会拦
⇒ **只能靠数据本身改对**。

⇒ 仪表盘外壳这个模具**无论怎么减重都配不上 160T 机** ⇒ 批次 3 需要用户在几个方向里选（见 §7）。

**实施结果（已完成，验收通过）**：用户 2026-11-10 拍板 **选项 (c) 新增 2 台机**。

| 新机台 | 锁模力 | 螺杆 | 行程 | 注射量 | 模板 | 配的模具 |
|---|---|---|---|---|---|---|
| IMM-DEMO-004 海天 MA2500/800 | **800 ton** | 55mm | **700mm** | 1750g | 2400×2400×500 | MOLD-DEMO-001（仪表盘外壳） |
| IMM-DEMO-005 伊之密 UN300 | **300 ton** | 40mm | **450mm** | 600g | 1400×1400×360 | MOLD-DEMO-002（家电外壳） |

**关键点**：螺杆越大 ⇒ 同重量的充填长度越短（充填长度 ∝ 1/D²）。
所以 IMM-DEMO-004 用 55mm 螺杆时，DEMO-001 的充填需求从 748.6mm（36mm 螺杆）
降到 **320.9mm**，稳稳落在 700mm 行程内。

**验收矩阵（3 模具 × 5 机台，实跑）**：

| | IMM-001 (200mm) | IMM-002 (220mm) | IMM-003 (200mm) | IMM-004 (700mm) | IMM-005 (450mm) |
|---|---|---|---|---|---|
| **DEMO-001** | REJECT 758.07 | REJECT 617.81 | REJECT 758.07 | ✅ **OK 338.12** | REJECT 617.81 |
| **DEMO-002** | REJECT 437.34 | REJECT 357.62 | REJECT 437.34 | ✅ OK 199.51 | ✅ **OK 357.62** |
| **DEMO-003** | ✅ OK 184.54 | ✅ OK 153.25 | ✅ OK 184.54 | ✅ OK 92.41 | ✅ OK 153.25 |

⇒ 3 个 DEMO 模具**各有一台物理可行的机台**；不匹配的组合仍被守卫拒绝（不误放）。

**历史数据：不动**（用户拍板）。`init_demo` **不带 `--reset`** 跑 ⇒ 按 `device_no`
幂等去重，只新增不覆盖（已存在的机台只补 `None` 字段，不改人工维护过的值）。
实测：`ProcessCondition` 计数 **57 → 57**，cond 105 仍为
`MOLD-DEMO-001 + IMM-DEMO-001 / met_end_pos=758.07 / param_source=algorithm_init`，
原 3 台机台的螺杆 / 行程 / 锁模力字段全部未变。

---

## §5 验收口径

| # | 口径 | 手段 | 结果 |
|---|---|---|---|
| 1 | 初始化在超行程时返回 400 且文案说清「哪项 / 需多少 / 本机行程多少」 | 调初始化接口（cond 105 同款数据） | ✅ 通过（文案实测见 §4 批次 1） |
| 2 | 初始化在**不超行程**时正常产出（不误伤） | 3 模具 × 3 机台矩阵探针 | ✅ 通过（DEMO-003 × 3 机台均 OK） |
| 3 | 优化侧超行程位置类参数**不再出现在数值推荐里** | 实跑 cond 105，看 items | ✅ 通过（items 7 → 6） |
| 4 | 优化侧 check 告知**仍然存在**且文案不变 | 实跑 cond 105，看 items | ✅ 通过（`met_end_pos` check 仍在） |
| 5 | 优化侧其它参数推荐**不受影响** | 实跑 cond 105，比对非位置类 items | ✅ 通过（其余 5 条不变） |
| 6 | 初始化拒绝时**不留脏数据** | before/after 比对 `ProcessCondition` 计数 | ✅ 通过（57 → 57） |
| 7 | 无回归 | `pytest process/algorithms/fuzzy tests/` | ✅ 通过（87 passed） |
| 8 | DEMO 初始化不再撞 400 | 重新初始化 DEMO 条件 | ✅ 通过（3 模具 × 5 机台矩阵，见 §4 批次 3） |

---

## §6 边界（明确不做）

- 不改专家引擎的**充填量推导公式**（`total_len` 的物理口径不动 —— 它是对的，错的是没校验）
- 不改模糊推理的论域 / G6 守卫口径（那是判档层，与本轮无关）
- 不改设定值类的 `max_set_*` 钳位（本来就合规）
- 不做「产品-机台选型推荐」（B1-2c 已关闭，不在本轮重开）

---

## §7 待用户确认项（批次 3 的修法）

### 7.1 前提事实（已逐条核实）

| DEMO 模具 | 锁模力需求 | 充填长度需求 | 注射量需求 | 现有可行机台 |
|---|---|---|---|---|
| MOLD-DEMO-001 仪表盘外壳 | **800 ton** | 748.6mm（36mm 螺杆） | 560g | ❌ **无**（最大 200 ton / 220mm） |
| MOLD-DEMO-002 家电外壳 | 280 ton | 437.3mm（36mm）/ 357.6mm（40mm） | 320g | ❌ 无（200 ton / 220mm） |
| MOLD-DEMO-003 薄壁饭盒盖 | 160 ton | 184.5mm | 128g | ✅ IMM-DEMO-001 完全匹配 |

⇒ DEMO-001 与 DEMO-002 **无解**（锁模力缺口无法靠减重消除）。

### 7.2 四个选项

| 选项 | 做法 | 代价 / 后果 |
|---|---|---|
| **(a) 新增 1 台 800T 机** | IMM-DEMO-004：800 ton / 螺杆 55mm / 行程 700mm / 注射量 2400g / 模板 2400×2400 | DEMO-001、002 都拿到可行机台；但 DEMO-002 的 500×500×450mm 小模具装进 800T 机（工程上靠垫板可行，演示上别扭） |
| **(b) 改小 DEMO-001** | 制品 560g→约 140g、锁模需求 800→约 160ton、模具改小 | 「汽车仪表盘主体外壳」退化成小件，**语义失真**；且投影面积一变锁模需求就得重算 |
| **(c) 新增 2 台机**（推荐） | IMM-DEMO-004：800 ton / 55mm / 700mm / 2400g；IMM-DEMO-005：300 ton / 40mm / 450mm / 700g / 模板 1400×1400 | 3 个 DEMO 模具**各有一台物理可行的机**，演示链路全通；DEMO 数据 +2 台机 |
| **(d) 不改 DEMO 数据** | 只保留批次 1 的 400 拒绝 + 文案指引 | DEMO-001 在界面选**任何**现有机台都 400 ⇒ 演示链路直接断 |

### 7.3 附带确认项

- **cond 105**（MOLD-DEMO-001 + IMM-DEMO-001 的历史初始化产物，met_end_pos=758.07）
  修完 DEMO 数据后它仍是超行程值 ⇒ 是否一并清理/重建？
  → **用户拍板：保留，不动**（优化侧已只保留 check 告知、不再往上推）。
- `init_demo` 命令带 `--reset`（仅影响 system_demo 公司下的数据）⇒ 重建是否走这条路？
  → **不跑 `--reset`**：幂等去重下只新增两台机即可，且不碰历史 condition。
