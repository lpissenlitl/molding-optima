# 模糊推理引擎重新设计 —— 交接文档与研发流程规范

> 日期：2026-10-23
> 用途：**新对话的起点**。本文档自包含，不需要重跑考古。
> 上一轮上下文已耗尽且过长，用户要求换会话继续。

---

## 0. 新对话怎么开始

新会话的第一句话建议是：

> 读 `backend/_refs/system/algorithm/2026-10-23-fuzzy-redesign-spec-handoff.md`，
> 然后从「§6 下一步行动清单」的 Step 1 开始。先只做 Step 1，做完汇报。

⚠️ 开工前必须先做的两件事（见 §7.3 新规范第 5 条）：

1. 检索 memory（关键词：模糊推理 / 分层架构 / 静默降级 / process_parameter）
2. 读 §8 错误台账

---

## 1. 任务红线（最重要，别再弄错）

> **本任务不是复制旧代码。**
>
> **参考旧代码的【思想】，重新设计一套全新的「工艺缺陷模糊推理流程」。**
>
> 旧版的**功能实现不认可**（漏洞太多）；旧版的**架构思想值得继承**（库/业务分离、纯函数化）。

具体拆解：

| 旧版 | 判定 | 处置 |
|---|---|---|
| 零阶 T-S 推理链（模糊化→规则库→t-norm 激活→按输出分组加权平均） | ✅ **思想正确** | 继承，并写清每一步语义 |
| 「库 / 业务」分离（fuzzykit 无 I/O，业务在 services） | ✅ **思想正确** | 继承 |
| 矩阵化（规则库编译成矩阵） | ⚠️ 可用，但**列布局成为隐式契约** | 继承思想，**列布局必须显式化** |
| 档位词全局静态表（low=0/high=2） | ❌ **实现粗糙** | 重新设计（见 §5-❶） |
| 静默跳过前件、continue 兜底 | ❌ **漏洞** | 重新设计（显式失败） |
| 桶峰位 `quantile` 计算 | ⚠️ 逐字保留但**语义要重新论证** | 保留实现，补论证 |
| `induction/` 目录（4778 行规则自动归纳） | ❌ 新版不需要 | 不迁移 |
| `HS_MAPPING_DICT` 全局表 | ❌ 混装了动作/编号/语义三种语义 | 拆分为语义层三张独立表 |

---

## 2. 根本病因：为什么之前一直在「修 bug」而不是「实现」

**用户原话**（2026-10-23）：

> 「你在改代码的时候好像一直是以修bug为主」
> 「由于我们一开始就没想明白怎么实现，导致我在看代码的时候，也非常含糊」

**诊断**：

1. **没有端到端规格** ⇒ 每一步都在**猜语义**
   - 猜 `low` 在 5 档字段落哪 → 造了 `LEVEL_WORDS_BY_LVL`
   - 猜规则/元数据不一致怎么办 → 造了字段三态分类
   - 猜 `process_parameter` 有什么 → 写错 docstring
   - 猜旧版为什么这么写 → 靠翻旧代码反推
2. **考古记录代替了地图** ⇒ 已产出 24 份文档（合计 ~450KB），但**没有一份是"一口气看完的全貌"** ⇒ 越查越看不清
3. **发现式驱动** ⇒ 缺陷是"碰巧发现的"，不是"设计排除的" ⇒ 永远修不完
4. **层间无契约** ⇒ 同一件事多层各做一遍（档位词表 3 处、档位→桶 2 处、字段名映射 3 处、字段元数据 3 处）

**结论**：
> 旧版 = 减法上的粗糙（少但直）
> 新版 = 加法上的不严谨（多但绕）
> **两版都缺同一个东西：一份写死的规格。**

**因此本轮起，第一优先级不是写代码，是把规格想清楚。**

---

## 3. 已确认的架构骨架

### 3.1 全景图

> **把「缺陷 + 当前参数」翻译成「参数该调多少」的一套规则翻译器。**

```
输入                                    处理                        输出
─────────────────────────────────────────────────────────────────────────────
缺陷反馈                   ┌──────────────┐
(缺陷名/程度/位置)         │  选规则       │
当前工艺参数               │ (缺陷+材料+产品)│──┐
                                                    ▼
规则库 1643 条 ───────────►┌──────────────┐
                            │  编译         │   解析→校验→模糊化→列布局→填矩阵
RuleKeyword 311 条 ───────►│  (构建阶段)    │
                            └──────────────┘
                                        │  编译产物（矩阵 + 论域）
                                        ▼
当前参数值                   ┌──────────────┐
                            │  推理         │   隶属度→激活→归一化→结论
                            └──────────────┘
                                        │
                                        ▼
                        ┌──────────────┐
                        │  聚合 + 分流   │   数值结论 / 提示结论 分开走
                        └──────────────┘
                                        │
                                        ▼
                              参数调整建议 (Recommendation)
```

### 3.2 一条规则的完整旅程（★ 讲清楚全貌的钥匙）

> ✅ **2026-10-23 已用真实数据填满**（Step 1 实测，脚本 `backend/_dev_refs/diag_fuzzy_rule_journey.py`）。
> 下方数值**全部是真实中间值**，不再是示意。

> **样例规则**：`#31 IF SHORTSHOT_high AND IV0_high THEN IV0_reduce_3.8`
> **当前工况**：IV0=90（RuleKeyword 论域 [0,120] 的 75% 分位）；缺陷=短射(high)；材料=PP；产品=酒瓶

| 阶段 | 真实发生了什么 | 真实产物 |
|---|---|---|
| **选规则** | `RuleQueryService` 三级特异性匹配（defect=SHORTSHOT / level=high / PP / 酒瓶） | 10 条 numeric 规则 / 0 条 advisory |
| **编译·解析** | `parse_rule()` | 前件 `{SHORTSHOT: high(defect), IV0: high(process)}`；结论 `{IV0: reduce 3.8}` |
| **编译·校验** | IV0 有 RuleKeyword（lvl=5、论域[0,120]）；`high` 是合法档位词 | 桶映射：现行 `high→桶2`；E2 `high→桶3` ⚠️**不一致** |
| **编译·模糊化** | `FuzzyFeature(IV0, [0,120], lvl=5, gauss)` | σ=15；峰位 = 0 / 30 / 60 / 90 / 120（=0%/25%/50%/75%/100%） |
| **编译·列布局** | IV0 `index=0`、`lvl=5` | 列区间 `[0,4]`；全矩阵 `(10, 45)` = 9 参数 × 5 桶 |
| **编译·填矩阵** | 本规则占第 3 行 | `connected_matrix[3][2] = 1`（桶2 = 峰位 60） |
| **推理·隶属度** | IV0=90 → 逐桶求高斯隶属度 | `[0.0, 0.000335, 0.135335, 1.0, 0.135335]` |
| **推理·激活** | prod 连接（仅 1 个门控列） | **0.13533528** |
| **推理·归一化** | **全局**归一化（分母 = 10 条规则激活度之和） | 权重×priority = **0.99999899** |
| **结论** | `solution_matrix = -3.8` | IV0 减 **3.799996** |

⚠️ **本旅程暴露的三个真实问题**（详见 §4.7）：

1. **“high” 的峰位在论域 50%**（现行语义），而“参数真的高”（75% 分位）只拿到 **0.1353** 的门控强度；若换成 E2 语义（峰位 75%）则为 **1.0** ⇒ **相差 7.39 倍**。
2. **归一化是全局的，不是“按输出参数分组”**（`nets.py` 用 `np.sum(rule_activations)` 做公共分母）⇒ 本文档 §3.1 的描述与实现不一致。
3. **缺陷前件完全不参与激活** ⇒ 只含缺陷前件的规则（实测 58 条）在数值层**激活度恒为 0**，永不生效。

### 3.3 分层职责表

| 层 | 只干这一件事 | 绝不允许出现 |
|---|---|---|
| **编排** | 拉数据、组装、分流、聚合、输出 | 算法细节、词表 |
| **契约** | 定义输入输出的形状与含义 | 任何计算 |
| **语义** | 参数名 / 档位词 / 动作词 / 维度类型（**是数据**） | 逻辑 |
| **构建** | 把规则+元数据编译成矩阵（**纯函数**） | I/O、日志、DB |
| **推理** | 纯数值计算（**无 I/O、无日志**） | 查表、跳过、容错 |

### 3.4 五条硬原则（将来审任何新代码的判据）

1. **推理层无 I/O、无日志、无 DB** —— 现 `nets.py` 里查档位表 + `logger.debug` ⇒ 违反
2. **构建层是纯函数** —— 输入相同，输出必然相同 ⇒ 现 `p_cols` 依赖执行顺序 ⇒ 违反
3. **语义是数据** —— 改档位词表只允许影响构建层 ⇒ 现改词表会波及推理 ⇒ 违反
4. **隐式契约 → 有名有姓的纯函数 + 单测** —— 这是「看代码含糊」的**直接解药**
5. **每层只有一个入口，跨层只调入口** —— 现 `fuzzy_algorithm` 直接摸 `nets.py` 内部 ⇒ 违反

⚠️ 每一条都对应一个**已经踩过的坑**，不是审美偏好。

---

## 4. 事实台账（2026-10-23 实测，新对话直接用，不必重跑）

### 4.1 数据规模

```
规则库：1646 条 = 数值 1547 + 提示 99 + Mamdani 0
RuleKeyword 表：311 条
  fuzzy_level 分布：3 档 1 条 / 5 档 310 条
规则前件字段：27 个，全部 5 档
  BT/BT1/CLAMP/CT/CUSION/DDAM/DVAM/ET/IL2/IP0/IP1/IPOS/IT/IV0/IV1/IV2/
  MBP0/MEL/MSR0/MT/NT/PP0/PP1/PT0/PT1/PV0/VPTL
RuleKeyword 查不到的字段：HOLDEXIST、injectstage3
档位词使用频次：low 1512 / high 1436 / medium 492
  语义词 3 种；编号词 levelN **0 次**；very_*/extremely_*/ultra_* **0 次**
缺陷名（DEFECT_CONST）：26 个条目 = 17 实际在用 + DEFECTFREE + 8 个老遗留词
规则库中 add_pct / reduce_pct：**0 次**
```

### 4.2 旧版 `HS_MAPPING_DICT` 原文（`HsMoldingService/mdprocess/utils/fuzzykit/macros.py`）

```python
HS_MAPPING_DICT = {
    'low': 0,
    'mid': 1,
    'high': 2,
    "level1": 0, "level2": 1, "level3": 2, "level4": 3, "level5": 4,
    "level6": 5, "level7": 6, "level8": 7, "level9": 8,
    'add': 1, 'reduce': -1, 'adjust': -2
}
```

⇒ 语义词**恒定 0/1/2，与字段级数无关**；编号词与级数解耦。**旧版无歧义。**

### 4.3 桶峰位计算（旧版与新版逐字相同）

```python
means = [f_interval[0],
         np.quantile(f_interval, np.arange(1, f_level - 1) / (f_level - 1)),
         f_interval[1]]
```

5 档 ⇒ 峰位落在 **0% / 25% / 50% / 75% / 100%**。

### 4.4 ⚠️ 词法层实测（2026-10-23）

```
IV0_very_low      -> name=IV0            level=very_low        ✅
IV0_extremely_low -> name=IV0            level=extremely_low   ✅
IV0_ultra_low     -> name=IV0            level=ultra_low       ✅
IV0_low           -> name=IV0            level=low             ✅
IV0_level3        -> name=IV0            level=level3          ✅
IV0_slightly_low  -> name=IV0_slightly   level=low             ❌ 字段名被污染
```

**根因**：`macros.py` 的 9 档词表（`LEVEL_WORDS_BY_LVL[9]`）里**没有** `slightly_low`，
但 `parsing.py:89` 的注释**明确宣称支持** `slightly_low`。
⇒ **注释与词表不一致**（`MULTI_SEGMENT_LEVEL_WORDS` 从 `ALL_LEVEL_WORDS` 派生，故不认识该词）。

### 4.5 ⚠️⚠️ 三条对上一轮结论的**重要更正**

> **更正 1：E2 的新档位语义至今未上线。**
> `resolve_bucket()` 在**生产代码中零调用**（只出现在 `macros.py` 定义 + `test_macros.py`）。
> `nets.py` L283 / L293 / L646 全部直接用 `HS_MAPPING_DICT[level]`。
> ⇒ **线上行为 = 旧版语义**（low→0, high→2）。
> ⇒ 上一轮我说"P1 是我们自己引入的语义变更"—— **错**。P1 至今未发生。

> **更正 2：当前 5 档字段实际只用到 3 个桶，且"高"侧只覆盖到论域 50%。**
> `HS_MAPPING_DICT` 的语义词最大是 `high`→2 ⇒ 5 档字段的桶 3（75%）、桶 4（100%）**永远为 0**。
> ⇒ 矩阵列有一半恒空，纯浪费。
> ⇒ 更要紧的是：`high` 的高斯峰位在 **50% 分位**，
> 意味着「参数高」只要到论域中位就算高 ⇒ **业务上明显偏松**。
> 这正是 P1 的真实内容，但它是**继承自旧版的**，不是新版引入的。

> **更正 3：`FUZZY_LEVELS` 在生产代码中零引用**（只有 `macros.py` 定义 + `test_macros.py` 断言）⇒ 死代码。
> ⚠️ 尚需核实前端是否依赖（前端另有 `LEVEL_WORDS`）。

### 4.6 现有代码资产（行数为 2026-10-23 实测）

| 文件 | 行数 | 归属 | 现状 |
|---|---|---|---|
| `fuzzy_algorithm.py` | 685 | 编排+契约 | 混 5 件事 |
| `fuzzy_core/models/nets.py` | 876 | 构建+推理+语义查询 | 混 3 件事 + 4 个引擎类 |
| `fuzzy_core/functional.py` | 356 | 推理 | 隶属度/反模糊化 |
| `specs.py` | 398 | 契约 | 与其他层有重复 |
| `services/rule_query_service.py` | 320 | 编排 | 选规则 |
| `adapters.py` | 294 | 契约适配 | 可用 |
| `sanity_check.py` | 244 | 诊断 | |
| `fuzzy_core/macros.py` | 238 | 语义 | 词表对，但语义被重新定义过 |
| `fuzzy_core/parsing.py` | 217 | 构建·解析 | 基本可用 |
| `fuzzy_core/utils/translate.py` | 161 | 契约 | |
| **合计（不含测试）** | **~3848** | | 旧版 fuzzykit ~6800（其中 induction/ 4778 无用） |

**测试基线**：`22 passed`
```
python -m pytest process/algorithms/fuzzy/fuzzy_core/tests/ tests/test_fuzzy_field_report.py -q
# 需要 $env:DJANGO_SETTINGS_MODULE="_moldx.settings"
```

### 4.7 ✅ Step 1 实测结果（2026-10-23 新增）

> 脚本：`backend/_dev_refs/diag_fuzzy_rule_journey.py`（只读诊断）
> 输出：`_dev_refs/_step1_out.txt`
> 复现：`cd backend; python _dev_refs\diag_fuzzy_rule_journey.py`

**选取的 4 条代表性规则（按 RuleMethod.id 固定）**

| 标签 | id | 规则 | 覆盖形态 |
|---|---|---|---|
| R1 | 623 | `IF FLASH_low THEN DVAM_reduce_1` | 纯数值·仅缺陷前件 |
| R2 | 31 | `IF SHORTSHOT_high AND IV0_high THEN IV0_reduce_3.8` | 纯数值·缺陷前件 + 参数门控 |
| R3 | 1427 | `IF SHADING_low THEN IV0_reduce_30%` | 百分比动作 |
| R4 | 88 | `IF FLASH_high AND CLAMP_worse THEN CLAMP_adjust_请检查锁模力是否不合理。` | 提示类(adjust) |

> **计数口径提醒**（避免与 §4.1 对不上）：
> `is_deleted=False AND is_active=True` 的规则 = **1643** 条（§4.1 的 1646 含 3 条非活跃）。
> 按“结论是不是 adjust/popup”分流 ⇒ 数值层 **1544** 条 + 提示层 **99** 条 = 1643。
> §4.1 的“数值 1547”是在 1646 全量上分的，两者不矛盾。

**新发现（此前未记录）**

| # | 发现 | 证据 |
|---|---|---|
| **F1** | **58 条规则（占数值层 3.76%）在数值层没有任何有效门控 ⇒ 激活度恒为 0 ⇒ 永不生效**。成因分布：**仅缺陷前件 6 条** + **仅 `worse` 前件 52 条** | 全库扫描 `analyze_zero_gate_rules()` |
| **F2** | **档位语义偏差已量化**：`high` 现行→桶2（峰位 50%），E2→桶3（峰位 75%）。参数取 75% 分位时门控隶属度 **0.135335 vs 1.0 ⇒ 相差 7.39 倍** | `bucket_semantics()` |
| **F3** | **现行桶语义导致“要么压死、要么等权”**：<br>· 偏高工况（75% 分位）：10 条规则里只有 1 条拿到权重 0.99999899，其余 9 条各 1.1e-07 ⇒ 9 条建议 delta ≈ 0<br>· 偏低工况（25% 分位）：10 条规则激活度**全部相等**（0.13533528），权重各 0.1 ⇒ IV0 同时收到 +3.8 与 −3.8 ⇒ **相反建议互相抵消为 0** | 两个生产场景 |
| **F4** | **归一化是全局的，不是“按输出参数分组”**。`nets.py` 用 `np.sum(rule_activations)` 做**公共分母**（所有规则共享）⇒ §3.1/§3.2 的描述与实现不一致，**规格必须先改** | §3.2 真实旅程 |
| **F5** | **缺陷程度已经通过“选规则”生效**（`RuleQueryService._match_defect_level` 按缺陷档位过滤规则，1646 条实测全部 `IF {defect}_{level} AND ...`）⇒ 分叉 ❷ 的现状答案是：**缺陷不参与激活是“选规则已过滤”的结果，不是遗漏** | `rule_query_service.py` |
| **F6** | **缺陷类 RuleKeyword 元数据完全未被使用**。RuleKeyword 表里 category='defect' 的 18 条（SHORTSHOT/FLASH/…，lvl=5、论域[0,1]）因 `collect_param_names` 剔除缺陷名而永远不会被加载 ⇒ 缺陷的连续论域在语义层存在、在推理层从未被引用 | 关键词表实测 |
| **F7** | **提示类规则不进数值层**：`NumTskRuleNet._is_check_rule` 排除后 `rule_nums=0`、`connected_matrix` 形状 `(0,0)`；提示文本由编排层直接产出（delta=0 / recommended_value=None / direction='check'）。另：`CLAMP_worse` 不是档位词 ⇒ 即便进数值层也无门控 | R4 追踪 |
| **F8** | **对拍通过**：本脚本复刻的聚合与真实 `FuzzyEngine.recommend()` 逐项一致（9/9 ✓）⇒ 上述结论不是自证 | `verify_against_real_engine()` |

**脚本实现中暴露的 2 个环境坑**

- 控制台默认 GBK，输出含 `⇒`/`⚠` 会抛 `UnicodeEncodeError` ⇒ 脚本内 `sys.stdout.reconfigure(encoding='utf-8')`。
- PowerShell 管道会把 python 的 UTF-8 输出按 GBK 解码 ⇒ 必须先设 `[Console]::OutputEncoding` / `$OutputEncoding` 为 UTF-8，否则中文全变乱码。

---

## 5. 四个待决分叉（必须逐个拍板，不能悬着）

### ❶ 「档位」到底是什么意思？★ 最核心，其余都挂在它下面

数据事实：字段**全是 5 档**、规则**只用 low/medium/high 三个词**。

| 解读 | `low` | `medium` | `high` | 浪费的桶 | 后果 |
|---|---|---|---|---|---|
| **旧版（现行线上）** | 桶0 = **0%** | 桶1 = 25% | 桶2 = **50%** | 桶3、4 | "高"只要到中位就算高 ⇒ **偏松** |
| **E2（已写好未接线）** | 桶1 = 25% | 桶2 = 50% | 桶3 = **75%** | 桶0、4 | "高"要过 75% ⇒ 更符合直觉，但**改 1643 条规则行为** |

**Step 1 已把后果量化（F2/F3）**：

- 参数取论域 75% 分位（“真的高”）时，现行语义的「high」门控强度 = **0.135335**，E2 = **1.0** ⇒ **相差 7.39 倍**。
- 现行语义下规则之间**要么被压死、要么等权抵消**：
  - 偏高工况：10 条规则只有 1 条拿到权重 0.99999899，其余 9 条各 1.1e-07 ⇒ 9 条建议 delta ≈ 0；
  - 偏低工况：10 条规则激活度**完全相等**（0.13533528）⇒ IV0 同时收到 +3.8 与 −3.8 两条相反建议 ⇒ **delta 抵消为 0**。
  - 根因：`low`→桶0（峰位 0%）、`high`→桶2（峰位 50%），**论域 25% 分位正好是二者中点** ⇒ 隶属度相等。

**我的倾向**：
1. 规格阶段**先把语义写清楚**（这是规格任务，不急着定数值）
2. 数值选择用**对拍 + A/B 数据**决定，不凭直觉
3. 迁移阶段不擅自改业务语义；改语义是“优化”，应单独排期、单独验证

⚠️ **这需要工艺/业务判断，不是编程判断。**

### ❷ 缺陷在算法里占几份权重？

规则形如 `IF SHORTSHOT_low AND IV0_high THEN IV0_reduce_10`。缺陷出现两次语义：
- **选规则**：`rule_query_service` 按 `defect_code` + 缺陷程度挑候选规则
- **判激活**：规则里的 `SHORTSHOT_low` 要不要作为门控参与激活？

**现状**：缺陷名被**排除出论域**（`collect_param_names` 剔除）⇒ 缺陷**不参与激活**，只参与选规则。
⇒ 这个对吗？还是应该：缺陷程度影响**该规则的权重**（严重缺陷的规则更该被采信）？

**Step 1 已澄清（F5/F6）**：缺陷程度**已经通过“选规则”生效**——`_match_defect_level` 按缺陷档位过滤规则集，
1646 条实测全部是 `IF {defect}_{level} AND ...` 格式，不同档位走的是**完全不同的三套调整方案**。
⇒ 所以“缺陷不参与激活”不是遗漏，而是**选规则已过滤后的必然结果**。
⇒ 若还要让缺陷程度影响权重，那是**叠加**而非“补漏”，需要先回答：“同一档位内，严重度还要怎么区分？”
（当前 `RuleQueryContext.defect_level` 只有 low/medium/high 三值，已被选规则吃掉。）
⇒ 另外：RuleKeyword 里 18 条 category='defect' 的元数据（lvl=5、论域[0,1]）**完全未被使用**，
若要引入“缺陷维度类型/论域”，这批元数据就是现成的落点。

### ❸ 是否引入「维度类型」？

`HOLDEXIST`（保压启用，布尔）、`injectstage3`（成型段，内部 one-hot 中间变量）—— 这类**没有连续论域**。
⇒ 引入「连续 / 枚举 / 布尔」后：布尔走**逻辑门控**，不走高斯。
⇒ 这才是它们的正确归属。**要不要引入这个概念？** 引入会让语义层多一维，但能让那 5 条规则得到正确处理。

### ❹ 矩阵化 vs 直接计算？

旧版用 numpy 矩阵（`connected_matrix`，1647×(27×5) ≈ 22 万格）。
- 矩阵：一次算完、天然是"编译产物"（契合"构建层"思路）；**但列布局成为隐式契约**（现在 `p_cols` 依赖执行顺序就是这个坑）
- 直接算：可读性好；每条规则算一遍

⚠️ **这个选择直接决定"构建层/推理层"怎么分** ⇒ 必须先定。

---

## 6. 下一步行动清单（有序，新对话按序执行）

> 全部**只读/诊断**性质，**不改生产代码**。每步做完汇报。

### Step 1 · 用真实数据填满「一条规则的旅程」★ ✅ 已完成（2026-10-23）

- ✅ 挑 4 条真实规则，覆盖：**纯数值 / 带缺陷前件 / 百分比动作 / 提示类（adjust）**
- ✅ 用真实 `RuleKeyword` 论域 + 示例参数值（论域 75% / 25% 分位）
- ✅ 跑出每一步真实中间值：解析 → 校验 → 隶属度函数参数（峰位/σ）→ 列区间 → 矩阵置位 → 每列隶属度 → 激活度 → 归一化权重 → 最终建议
- ✅ 结果已写入 §3.2 + §4.7（F1~F8）
- ✅ 附对拍：与真实 `FuzzyEngine.recommend()` 逐项一致（F8）
- 脚本：`backend/_dev_refs/diag_fuzzy_rule_journey.py`；输出 `_dev_refs/_step1_out.txt`

⚠️ **Step 1 暴露的待办**（需在后续步骤消化）：
- F1 的 58 条“死规则”（激活度恒 0）—— 算不算 bug？要不要纳入修复范围？
- F4 的“全局归一化 vs 按输出参数分组”—— 规格改哪边？
- F6 的缺陷类元数据闲置 —— 与分叉 ❸（维度类型）直接相关。

### Step 2 · 抽旧版 fuzzykit 作为「只读参照实现」+ 建对拍脚本

- 旧版 Django 依赖**只有 1 处**：`nets.py` 的 `from mdprocess.const import DEFECT_CONST`
  ⇒ 抽到 `backend/_dev_refs/legacy_fuzzykit/` 成本很低，stub 掉 `DEFECT_CONST` 即可
- 对拍脚本：同一份规则 + 同一份参数 ⇒ 旧/新双跑 ⇒ **逐条**比激活度、结论、排序
- 产出：一份「新版 vs 旧版」差异清单
- ⚠️ **价值**：这是**唯一独立于实现**的验收基准。所有后续修复都靠它，而不是靠我自证的测试。

### Step 3 · 展开「语义层」规格（含 ❶ 的 A/B 数据）

定死：参数名空间 / 档位词全集 / 动作词全集 / 维度类型 / 档位→桶的语义规则
⚠️ 同步清理 §4.4 那类"注释与词表不一致"（`slightly_low`）

### Step 4 · 展开「契约层」规格

定死：`context` 契约（**`process_parameter` 只含工艺参数**，设备/材料/模具各自独立 key）
/ 规则串格式 / `RuleKeyword` 每个字段的语义（`lvl` / `range` / `step` 到底代表什么）

### Step 5 · 展开「构建层 + 推理层」规格（含 ❹ 的选择）

### Step 6 · 现有代码 ↔ 新架构对照表（去留清单）

逐文件/逐函数标注：归属哪层 / 保留 / 拆分 / 删除。**重点是"删什么"**（当前死代码已识别：见 §9）。

### Step 7 · 才开始实现

按 §7.3 的批次规范推进。

---

## 7. 研发流程规范（本次确立，适用于后续所有算法/新功能研发）

### 7.1 保留有效的

- **考古先行**：读旧实现 + 实测统计，不凭印象下结论
- **小步推进，每步做完汇报**
- **实测验证**：写诊断脚本跑数据，不靠推理下结论
- **过程建文档**（`_refs/system/algorithm/`）

### 7.2 禁止的（都是这次实际踩过的）

| 禁止 | 实际后果 |
|---|---|
| **发现式修 bug**（没定规格就动手） | 本次根本病因，越修越多 |
| **一次性大改**（一次交付几百行） | 用户来不及审，错误被放过 |
| **批量 `replace_all`** | 把 10 处正确的"兜底"批量改错 |
| **自证式测试当验收** | 我写的测试测的是我刚定义的错误语义 |
| **事后才检索 memory** | `process_parameter` 糅合（memory 早有规范） |
| **用考古记录代替地图** | 24 份文档反而让人更看不清 |

### 7.3 新规范（7 条）

1. **方案卡先行**：动手前给「改哪些文件 / 每处意图 / 验收方式 / 回滚方式」，用户点头再落码
2. **单批上限**：≤ 80 行、≤ 2 个文件、每批独立可测
3. **交付卡必附**：① 对拍/实测数据 ② 我自曝的 3 个风险点 ③ 用户该重点看哪几行
4. **验收不认自证**：只认「对拍旧版 + 手算样例 + 契约测试」
5. **动手前强制**：读错误台账（§8）+ 检索 memory
6. **隐式契约必须显式化 + 单测**
7. **规格与代码冲突时，先改规格再改代码**

---

## 8. 错误台账（我犯过的错，防复发）

| 错误 | 根因 | 防复发 |
|---|---|---|
| docstring 写「process_parameter 含设备+材料参数」 | memory 早有规范，我没查 | 规范 §7.3-5 |
| `SearchReplace` 批量把"兜底"改成"兵底" | 方向搞反 + `replace_all` 无预览 | 批量替换前先 grep 计数，改后立即反向验证 |
| mock 无条件返回 2 项导致测试失败 | mock 没按入参过滤 | mock 必须尊重入参 |
| `_field_reports` 在单例引擎上无界增长（内存泄漏） | 单例 + 实例状态未重置 | 状态放请求作用域或显式重置 |
| 发明 `very_low` 等无人使用的档位词 | 自己造抽象，未查规则库实际用词 | 先统计实际用词再定抽象 |
| `resolve_bucket` 写好不接线 | 考古结论只写代码不接线 | 写代码必带接线点，或明确标注"未接线" |
| 一次交付 681 行改动 | 无批次概念 | 规范 §7.3-2 |
| 误报"P1 是我们引入的语义变更" | 没核实 `resolve_bucket` 是否接线 | 结论必须 grep 验证调用方 |
| 误判"5 档字段 7/9 档 0 字段" | 用 E2 词表推断，忽略 `fuzzy_level` 实为 5 | 用 DB 实测，不靠推断 |

---

## 9. 已知代码缺陷清单（2026-10-23 快照，行号可能漂移，**以代码片段为准**）

### 9.1 会静默产出错误结果的（**真 bug**）

**① 桶索引无越界检查**（`nets.py` 两处引擎都有）
```python
# nets.py:283（Mamdani 侧）与 nets.py:646（零阶 T-S 侧）
p_col_idx = self.pre_dict[name]['index'] + HS_MAPPING_DICT[level]
self.connected_matrix[row_idx][p_col_idx] = 1
```
⇒ `HS_MAPPING_DICT['level9']` = 8，若字段 `lvl=5` ⇒ `index + 8` **写到相邻字段的列上** ⇒ 静默污染别的参数门控。
⇒ 规则库当前 `levelN` 0 次使用 ⇒ **暂未触发**，但任何一条 `levelN` 规则都会中招。

**② 词法层字段名污染**（`parsing.py` + `macros.py`）
```python
# parsing.py:89 注释宣称支持
#   档位词可能是多段的（very_low / extremely_low / slightly_low ...），
# 但 macros.py 的 LEVEL_WORDS_BY_LVL[9] 没有 slightly_low
```
⇒ `IV0_slightly_low` → 字段名变成 `IV0_slightly` ⇒ 被当作一个不存在的参数 ⇒ 静默跳过。

### 9.2 失败被伪装成正常

**③ 三处 `except Exception` 兜底**（`fuzzy_algorithm.py` L380 / L478 / L555）
⇒ DB 故障被伪装成"正常猜论域"；算法崩溃被伪装成"无建议"。

**④ 越界防御写错地方**（`nets.py` L651 / L676）
```python
if row_idx < len(self.connected_matrix): ... else: logger.error("index ... out of bounds ...")
```
⇒ `row_idx` 来自 `enumerate`，**永远不可能越界** ⇒ 该分支是死代码；
⇒ 而真正该检查的 `p_col_idx` **一点检查都没有**（见 ①）。

### 9.3 归零项（纯删除，零行为变化）

| 位置 | 内容 |
|---|---|
| `nets.py:824` | `class TskRuleNet`（一阶 T-S，**死类**，Mamdani 侧实测 0 条规则） |
| `fuzzy_algorithm.py:678` | `def load_rules(self): ... pass`（占位） |
| `fuzzy_algorithm.py:194` | `self._rule_net = None  # 兼容旧接口，不使用`（死成员） |
| `macros.py:80-84` | `HS_MAPPING_DICT` 已被标注 `@deprecated`，但 `nets.py` **仍在用** ⇒ 归零需先接线 `resolve_bucket` |
| `macros.py:170` | `FUZZY_LEVELS`（生产零引用） |
| `macros.py:143-149` | `ADJUST_ACTIONS` 与 `ACTION_MAP` **两张动作表不一致**（前者有 `add_pct`/`reduce_pct`，后者没有）⇒ `ACTION_MAP.get(action, 0)` 会静默返回 0。⚠️ 规则库中 `_pct` 0 次 ⇒ 暂未触发 |
| `macros.py:131-134` | `MULTI_SEGMENT_LEVEL_WORDS` 从 `ALL_LEVEL_WORDS` 派生 ⇒ 遗漏见 ② |

---

## 10. 本轮已改动记录（2026-10-22 ~ 10-23）

| 文件 | 操作 |
|---|---|
| `fuzzy_core/field_registry.py` | **已删除**（292 行过度设计，经用户确认方案 A） |
| `fuzzy_core/tests/test_field_registry.py` | **已删除** |
| `fuzzy_algorithm.py` | `_build_field_registry()` → `_build_field_context()`（内联三态分类 + 字段体检）；`recommend()` 开头重置 `_field_reports`（修单例内存泄漏）；docstring 修正 `process_parameter` 语义 |
| `backend/tests/test_fuzzy_field_report.py` | **新建**（5 组用例，mock DB） |
| `backend/_dev_refs/diag_fuzzy_field_registry_regression.py` | 零行为变化回归脚本 |
| `backend/_dev_refs/diag_fuzzy_level_dist.py` | 档位词/等级分布统计 |
| `backend/_dev_refs/diag_fuzzy_parsing_probe.py` | 词法层探针（2026-10-23 新建） |
| `backend/_dev_refs/diag_fuzzy_rule_journey.py` | **Step 1 主脚本**（2026-10-23 新建）：单规则 8 阶段追踪 + 档位语义量化 + 生产场景 + 真实引擎对拍 + 无门控规则全库扫描 |
| `backend/_dev_refs/_step1_out.txt` | Step 1 完整输出（存档） |
| 本文档 §3.2 | 示意数值 → **真实中间值**（规则 #31 全链路） |
| 本文档 §4.7 | **新增**：Step 1 实测结果 F1~F8 + 环境坑 |
| 本文档 §5 ❶/❷ | 用 F2/F3/F5/F6 量化并部分回答两个分叉 |

---

## 11. 相关文档索引

| 文档 | 内容 | 建议 |
|---|---|---|
| `2026-10-22-fuzzy-legacy-vs-current.md`（1192 行） | 旧版 vs 新版全面考古 | ⚠️ **只查结论，别通读** |
| `2026-10-22-fuzzy-engine-design-defect-review.md` | 新版设计缺陷评审 | 查 §11 字段三态 |
| `2026-10-22-fuzzy-engine-paradigm-decision.md` | 范式讨论 | ⚠️ 与本文档有重叠，以本文档为准 |
| `2026-10-22-fuzzy-feature-full-chain-guide.md` | 全链路指南 | 查业务上下文 |
| `2026-10-22-fuzzy-algorithm-internals.md` | 引擎内部机制 | 查具体实现 |
| `2026-10-20-fuzzy-inference-review-and-roadmap.md` | 早期评审与路线 | 存档 |
| `2026-09-30-infer-context-boundary-redesign.md` | context 边界重设计 | 查 context 契约 |
| `algorithm-context-design.md` | context 设计 | 查 context 契约 |

---

## 12. 一句话总结

> **旧版的思想值得继承，旧版的实现不能照搬；新版的问题不是代码写得差，是从来没有一份写死的规格。**
> **下一步不是改代码，是把 §3 的骨架用真实数据填实、把 §5 的四个分叉逐个拍板。**
> **改动必须小批次、可审、每批附对拍数据和我自曝的风险点。**
