# 模糊推理 · 重构后回顾与优化空间清单

> ⚠️ **2026-11-03 目录合并说明**：原 `backend/_dev_refs/` 已合并至 `backend/_refs/`；
> **同日再整理**：可执行验收脚本与黄金基线已迁至**独立测试目录** `backend/tests/`
> （fuzzy 内核逐位锚点 = `backend/tests/fuzzy_kernel/`），`backend/_refs/` 回归**纯文档 + 数据源**目录。

> **日期**：2026-10-27
> **范围**：`backend/process/algorithms/fuzzy/`（含 `fuzzy_core/`、`library/`）
> **性质**：**讨论稿 / 体检报告**。本文只做「回顾 + 找空间」，**不含任何代码改动**。
> **基线**：`f181df6`（HEAD）· pytest `process/algorithms/fuzzy/fuzzy_core/tests` + `backend/tests` = **41 passed**（1.52s）
> **参照文档**：
> - `2026-10-20-fuzzy-inference-review-and-roadmap.md`（能力评估，P0-1~P0-4 / P1-1~P1-4）
> - `2026-10-23-fuzzy-entry-refactor-execution.md`（E1~E26 施工日志，遗留台账 L1~L27）

---

## 0. 一句话结论

> **结构重构（E1~E26）已经把「代码怎么组织」这件事做完了；
> 但「算法算出来的数对不对」这件事，一行都没动。**
>
> 重构解决的是**可读性与故障半径**（成果扎实、验收严谨）；
> 未解决的是**输出量级与契约落地**——前者决定建议值能不能用，后者决定契约是不是真的。

**关键量化事实**（本轮实测，非引用）：

| 场景 | 规则作者写的量 | 当前实现实际输出 | 偏差 |
|---|---|---|---|
| 1 条规则命中 1 个参数 | `IV0_add_3.8` → 3.8 | **3.8** | ✅ 正确 |
| 10 个参数各 1 条规则（激活度相同） | 每条 3.8 | 每条 **0.38** | ❌ **稀释 10×** |
| 同参数 6 副本 + 10 个其它参数 | 3.8 | **1.43** | ❌ **稀释 2.7×** |

⇒ **单规则场景看起来一切正常，缺陷只在多规则场景暴露**——而生产里一次缺陷反馈
（实测 `SHORTSHOT/low`）命中 **10 条**规则、覆盖多个参数 ⇒ **这是常态路径，不是边缘情况**。

⚠️ **本文档的实测数据在 2026-10-27 复核过一次**，§3.3 / §3.5 / §3.6 三节
补入真实库数据后，**原「跨库副本放大」伤害与「B1 风险=低」的判断被修正**，
详见那三节。

---

## 1. 本轮回顾：重构做成了什么

E1~E26 共 26 轮，**结构层的收益是真实的、且有强验收证据**：

| 维度 | 改造前 | 改造后 | 证据 |
|---|---|---|---|
| 入口文件 | `fuzzy_algorithm.py` 686 行，9 个私有方法混装 | `engine.py` 495 行，5 步一条直线 | R1~R4 验收标准 |
| 故障边界 | 4 种互不一致的策略 | 3 层（编排 / 层间 / 条目级） | §1.3 三层边界 |
| 中间态 | 匿名 dict | `RuleAdjustment` / `AggregatedAdjustment` | R2 |
| 聚合逻辑 | 混在引擎里的 `_merge_layer_results` | 独立 `recommendations.py` | R4 |
| 命名契约 | 散落、重复实现 | `field_names.py` 双向闭合 + import 时自检 | 往返闭合 0 不闭合 |
| 契约对象 | 裸 dict | `KeywordProfile` / `RuleProfile` | E9~E20 |
| 隶属度函数 | 5 组同名实现前后段覆盖 | 9 形状统一签名 + 分派表 | E24~E25 |
| 注释 | 设计用语 / 轮次考古 | 精简 218 行，**代码零改动** | E18 AST 比对 IDENTICAL |

**验收纪律值得延续**：每轮用「改前完整副本 + 同脚本对跑 ⇒ 整棵 JSON 逐条 diff = 0」
证明行为等价；每轮的「如实边界」段落如实登记未做项。**本轮的问题恰恰是那些
「如实边界」累积到第 27 项之后没人收口的结果。**

---

## 2. 结构层现状体检

### 2.1 当前分层（19 个文件，约 4400 行）

```
fuzzy/
├─ 【层 0 对外契约】specs.py          字段字典 + 校验器 + 档位词表（三合一，L22 未关）
├─ 【层 1 编排】  engine.py           FuzzyEngine 主流程 5 步
│                recommendations.py    推理结果 → 对外推荐契约
│                field_names.py        业务字段名 ↔ 算法字段名（双向）
├─ 【层 2 来源】  library/contracts.py 零 ORM 契约（AlgorithmResourceRepository）
│                library/rules.py      查库 + 规则串语义
│                library/keywords.py   关键字元数据
│                library/repository.py 选库 → 收集 → 组装
├─ 【层 3 内核】  fuzzy_core/profiles.py    内核输入契约（+ 校验函数）
│                fuzzy_core/parsing.py     规则串词法底座
│                fuzzy_core/macros.py      档位词表 + 桶映射
│                fuzzy_core/rules_filter.py 第 4 层：拆一次 → 分类 → 建对象
│                fuzzy_core/models/        features / rules / nets
│                fuzzy_core/memberships.py + defuzz.py   数学原语层
```

**结论**：分层本身是清楚的，依赖方向自洽（外 → 内，内核零 ORM 零 Django）。
**结构层没有大动作可做了。** 下面的问题**都不是结构问题**。

---

## 3. 算法语义层：4 个未闭合的缺口

### 3.1 【P0】聚合量级错误 —— 全局归一化 + 裸累加

**位置**：
- `fuzzy_core/models/nets.py:557-562`（归一化）
- `engine.py:409-418`（乘激活度）
- `recommendations.py:121-123`（裸累加）

**机制**（本轮实测推导）：

```
nets.py:  new_activations[i] = rule_activations[i] / Σ(全部规则激活度)   ← 全局分母
engine.py: delta = 结论值 × new_activations[i]
recommendations.py: merged[p].delta += adj.delta                          ← 累加
```

于是单个参数的最终调整量：

```
delta_p = (1 / Σ_all) × Σ_{i∈p} (z_i × act_i)
TSK 应为: delta_p = Σ_{i∈p} (act_i / Σ_{i∈p} act) × z_i
```

⇒ **分母用错**：全局分母把不同参数的激活度摊薄，再各自累加。
⇒ **量级 = 规则作者写的量 × (该参数激活度之和 / 全局激活度之和)**。

**为什么单规则场景看不出来**：只有一个参数命中时，全局分母 == 该参数分母 ⇒ 结果恰好正确。
**生产场景必然踩中**：实测 `SHORTSHOT/low` 一次命中 **10 条**规则、覆盖多个参数
⇒ 每个参数分到的权重不足 1/10。

**修法**（评审文档 §5.4 已给出，此处补上代码落点）：

```
① 归一化维度：全局 → 按输出变量分组
   w_i = act_i / Σ_{j: output_j = output_i} act_j
② 组内聚合：累加 → 加权平均
   delta_p = Σ_{i: output_i = p} w_i × z_i
```

改动落点：`nets.py:557-562` 改成按 `solution_matrix` 的输出列分组归一化，
`recommendations.py:121-123` 改成组内加权平均。
**这一刀同时消掉两个伤害**：跨参数稀释、同参反向简单相消。
（~~跨库副本放大~~ —— 该伤害只在**显式指定补充库**时成立，主链路当前不触发，见 §3.3 实测）

⚠️ **这是唯一会改变输出数值的改动**。必须先与工艺员对齐量级（见 §7 待决策 D3）。

---

### 3.2 【P0】`specs.py` 的论域上界契约 —— ✅ 已做（2026-10-27，原定性需更正）

**原定性（已被本轮推翻）**：「`max_set_*` 是论域上界（判级依据），标了必填但没人接」。

**更正后的定性**（逐条核对代码 + 实测数据）：

| 环节 | 原判断 | 实测 |
|---|---|---|
| 判级论域从哪来 | `machine_info.max_set_*` | **`RuleKeyword.range_min/range_max`**（规则库权威元数据；实测 `IP=[0,200]` / `IV=[0,120]` / `MSR=[0,200]` 全有行） |
| `engine.py` 是否读 `machine_info` | 「读不到论域上界」 | **完全不读**（只在 docstring `:96` 出现；真读的是 `polymer_info`/`mold_info`） |
| 「当前值×2」自造论域 | 缺上界就会触发 | **只在规则库元数据缺失时触发**（`engine.py:306-326`），与设备上限无关 |
| `max_set_*` 的真实身份 | 论域上界（判级依据） | **推荐值的机台物理天花板**（规则库论域普遍宽于机台上限：`IP` 论域 200 vs 同机 HMI 上限 100） |

⇒ 原「必填」等级与「判级依据」的理由**两处都与实现不符**；
⇒ `specs.py` TODO 2「让论域真正等于设备物理边界」是**错误方向**——改用机台上界做判级，
会让同一套参数在不同机器上判出不同等级、规则命中行为整体漂移（已更正该 TODO）。
⇒ 真正的缺陷是：**`max_set_*` 到了门口没人用，推荐值不受机台物理上限约束**
（实测：当前值 `inj_spd_1=110` → 推荐 106.3 > 同机上限 80，操作工输不进去）。

**本轮落地**（D2 拍板选 (c) 推理时 clip）：

| 改动 | 位置 |
|---|---|
| 8 个 `max_set_*` 的 desc 改「推荐值物理天花板」、condition 「必填/液压机必填」→「可选」 | `fuzzy/specs.py:64-148` |
| 新增 `PARAM_LIMIT_FIELDS` + `resolve_param_limits` + `lookup_param_limit` | `fuzzy/specs.py` |
| engine 读 `context['machine_info']` 做**推荐值裁剪**（越限封顶 + 方向重算 + 留痕） | `fuzzy/engine.py::_apply_machine_limits` |
| 新增护栏（8 组，参照系 = 机台物理上限 / 参数命名契约 / HMI 可设定范围） | `backend/tests/test_fuzzy_machine_limits.py` |

**口径（用户拍板）**：缺机台上限 ⇒ **warning + 不裁剪 + 不拦请求**（缺数据 ≠ 不能给建议）。
⇒ 故 `OptimizeDataValidator` **仍不接进生产链路**（字段已非必填，接了也不拦人），
原「契约校验未接线」这个缺口的前提不再成立。

**实测验收**：44 个 ProcessCondition 全跑对照 —— 温和当前值下 0 条被裁（无误伤）；
当前值在论域高端时 **42 条被裁**（`IV0` 106.2954 → 80.0000），
而 **cond=10 / cond=41 恰好未被裁**（正是机台没填上限的那 2 台）⇒ 缺口口径正确。
（完整实施记录见 §12）

---

### 3.3 【P0】跨库副本未去重 —— 但**主链路当前不触发**，属接线前置

**位置**：`library/repository.py:95`（`seen_ids = set()`）、`:103-104`、`:113`

去重键是 `rm.id`（数据库主键）。同一条业务规则在 `base` 库与补充库各存一份时，
主键不同 ⇒ 去重完全失效。

**全库实况**（2026-10-27 实测，开发库）：

| 指标 | 数值 |
|---|---|
| 活跃规则总数 | 1643 |
| 唯一 `(defect_code, rule_description)` | **940** |
| 重复组数 | **359**（全部跨库，同库重复 0 组） |
| 重复涉及行数 | 1062（占 64.6%） |
| 单组最大重复次数 | **9** |
| `rule_no` 可用性 | **1643 条全为 NULL** ⇒ 不能作业务键 |

**主链路当前不触发**：自动选库只命中 `base` 库（见 §3.6），
而 `base` 库内部无重复 ⇒ 实测 18 个真实上下文（9 产品 × 2 材料）
命中 180 条、唯一内容 180 条、**重复 0 条**。

**但一旦显式指定补充库就会触发**（`rule_library_code` 与 `product_category` 同时给）：

```
显式补充库 R20240516093115 + 产品=碗
  命中 13 条 | 唯一内容 12 条 | 重复 1 条
  ×2  IF SHORTSHOT_low AND MEL_low THEN MEL_add_2
       src=RuleMethod:1002（补充库，prod=碗）
       src=RuleMethod:20  （base 库，poly=None prod=None）
```

⇒ 补充库与 base 库**规则串完全相同**的比例实测 56%~77%（抽样三个库），
一旦产品库接线，重复是常态而非例外。

**修法（两步，顺序不可换）**：
1. **先修 specificity 标注**（§3.5）——「保留最特异」这个判据本身建立在
   specificity 正确之上，而现在它**系统性错位 2 级**。
2. 再把去重键从 `rm.id` 换成业务内容 `(defect_code, rule_description)`，
   保留真实特异级最高的那条（评审文档 D4）。

---

### 3.4 【P1】迭代趋势链路断（`_trend_to_factor` 是死代码）—— ⚠️ **2026-10-27 复核：定性推翻，改为「待废弃」**

> ⚠️ **本节结论已推翻**（2026-10-27 复核）。原标题写「链路断」是**误导**：
> “代码写好但没接”**不等于**“该接”。逐条复核后判定：
>
> **① 该策略业务上不成立** —— 趋势反映的是**历史轮次整体**走向，却被当成
> **本次建议幅度**的全局乘数（`worsening→0.5` / `improving→1.2`）：
> - **时间错配**：上轮调锁模力变好、本轮报缩水要动保压 ⇒ 拿 A 参数的结果放大 B 参数的建议；
> - **手段错配**：趋势恶化说明**上次思路错了**，正确反应是**换思路**，而非“同一思路少调一点”；
> - **全局 vs 局部**：一个乘数作用于全部参数，趋势判断却不针对具体参数。
> - **系数 0.5 / 1.2 无业务出处**（与 D1 档位口径同类）。
>
> **② 且本节所述 “§7 无对应决策项” 是文档缺陷** —— §6 批次表 B9 写「需 D4/D5 拍板」，
> 但 D4 = 跨库副本处理（§3.3）、D5 = 检查类建议展示位置（§4.6），**均不对应本节**
> ⇒ 本策略**从没有人给它定过业务口径**。
>
> **③ 接上还有必然的回归风险** —— `engine.py` 的 `is_available` 含
> `trend.get('trend') == 'final' → return False`；一旦接上 `iteration_trend`，
> 上一轮试模已 `qualified`/`unqualified` 时 **fuzzy 在 optimize 链直接不参与**
> ⇒ `_call_algorithms` 返回空 ⇒ `_infer_kernel` 抛
> `BizException("推荐算法暂不可用，请稍后重试或联系管理员")`
> ⇒ 用户看到的是“算法暂不可用”，而不是“已定稿，无需再调”。
>
> ⇒ **处置：明确标记废弃**（不接线 + 注释写清不接的理由 + 后续清理），
> **不作为“待接通的功能”**。若业务方确实需要“趋势感知”，应先定义
> **趋势针对哪个参数/缺陷**、以及“恶化时是换策略还是减幅度”，再重新设计。
>
> 以下为原始记录（保留供追溯）。

**位置**：`engine.py:186`（读 `context['iteration_trend']`）、`engine.py:249-258`（`_trend_to_factor`）

编排层 `parameter_optimize.py:483-489` 组装的 context 只有 5 个 key：

```
machine_info / polymer_info / mold_info / process_parameter / feedback
```

**没有 `iteration_trend`** ⇒ `context.get('iteration_trend', {})` 恒为 `{}`
⇒ `.get('trend', 'unknown')` 恒为 `'unknown'` ⇒ **系数恒为 1.0**。

⇒ `engine.py:185-186` 与 `engine.py:208-210`（`is_available` 里的 `trend == 'final'`）
两处都是**永不生效的分支**。
⇒ 评审文档 §5.6「`iteration_trend` 接入」未做。

---

### 3.5 【P0 前置】特异级（specificity）标注系统性错位

**位置**：`library/repository.py:87-92`（`specificity_filters`）、`:95/103`（`seen_ids`）、`:106`（specificity 入参）

**机制**：`RuleQueryService.get_methods` 对 polymer/product 做**精确等值过滤** ⇒
上下文缺一个维度时，同一语义层的两个 filter 变成**同一个查询**：

| 上下文 | 四级 filter | 实际不同查询 | 退化 |
|---|---|---|---|
| poly=None, prod=None | (1,∅,∅)(2,∅,∅)(3,∅,∅)(4,∅,∅) | 1 | 四级全同 |
| poly=PP, prod=None | (1,PP,∅)(2,PP,∅)(3,∅,∅)(4,∅,∅) | 2 | (1)=(2)、(3)=(4) |
| poly=None, prod=碗 | (1,∅,碗)(2,∅,∅)(3,∅,碗)(4,∅,∅) | 2 | (1)=(3)、(2)=(4) |

`seen_ids`（按 `rm.id`）把后出现的同一批 rm 挡掉 ⇒
**specificity 标签 = 「第一个碰巧命中该查询的 filter 序号」** ⇒ 系统性偏移。

**实测对照**（`SHORTSHOT/low`）：

| 上下文 | 规则真实特异级 | 实测标注 | 偏移 |
|---|---|---|---|
| 裸（poly=None, prod=None） | 4（默认） | **1** | −3 |
| prod=碗, poly=None | 3（部分-product） | **2** | −1 |
| poly=PP, prod=None | 4（默认） | **3** | −1 |
| prod=碗 + poly=PP | 1（精确） | **3** | −2 |
| 显式补充库 + prod=碗 | 补充库那条=3 / base 那条=4 | **1 / 2** | 都错，且**相对关系也反了** |

最后一行最要命：base 库的通用规则（应 4）被标成 2，补充库的产品专用规则（应 3）被标成 1
⇒ **「保留最特异」会选错那一条**。

**影响面**：`repository.py:117` 的排序 `sort(key=(specificity, -priority))` ⇒ 顺序错；
§3.3 去重的判据；后续 B2 若让 specificity/priority 参与组内加权，错标签直接进权重。

**修法候选**（需拍板，见 §7 D8）：
- **A（推荐）**：按**实际命中了哪个维度**判定 —— 比对 `rm.polymer_abbreviation` /
  `rm.product_category` 与上下文实际值（上下文为 None 时不算「匹配」）。
  语义最正；改动落在 `RuleAdapter.to_rule_profile` 的入参语义（契约不变）。
- **B**：构造 filter 时剔除重复查询项。查询次数减半，但**无法区分 L1/L2**
  （poly 匹配+prod 不限 与 poly 匹配+prod 精确，在 ORM 精确过滤下不可分）⇒ 标签仍不准。
- **C**：不修 specificity，B3 去重时改用「库 priority 更高者胜」绕开它。

---

### 3.6 【P0】补充规则库自动选库映射完全落空 —— 64% 的规则是死数据

**位置**：`library/rules.py:100-123`（`product_to_library_codes`）、`library/repository.py:52-56`

**库的实际情况**（11 个活跃库）：

| library_code | 类型 | 优先级 | RuleMethod 条数 | 说明 |
|---|---|---|---|---|
| `base` | fuzzy | 100 | **585** | 基础模糊规则库（JSON key='基础库'） |
| `R20230825161658` | fuzzy | 10 | 88 | 补充规则库（按产品/场景补充） |
| `R20230901163319` | fuzzy | 10 | 138 | 同上 |
| `R20231010100755` | fuzzy | 10 | 30 | 同上 |
| `R20231129160052` | fuzzy | 10 | 65 | 同上 |
| `R20240326160428` | fuzzy | 10 | 76 | 同上 |
| `R20240516093115` | fuzzy | 10 | 276 | 同上 |
| `R20240702164137` | fuzzy | 10 | 152 | 同上 |
| `R20240815104925` | fuzzy | 10 | 113 | 同上 |
| `R20240817094811` | fuzzy | 10 | 120 | 同上 |
| `expert_rules` | expert | 100 | 0 | 工艺初始化专家规则库（非 fuzzy） |

`product_to_library_codes` 的映射表是 `'酒瓶'/'食品包装'/'化妆品容器'/'通用包装' → packaging`、
`'汽车件' → auto_parts`、`'医疗器械' → medical`，
**而库里没有任何一个 library_code 属于这 6 个值**。

实测 9 个真实 product 值（0815 / 吹风筒手柄 / 微波炉控盒 / 手机外壳 / 把手 / 柜门 / 碗 / 耳机 / 通用）
→ 映射出的 code **全部命中不到任何库**。

⇒ **自动选库路径永远只加载 `base` 库** ⇒ 9 个补充库共 1058 条规则（占全库 64.4%）
在自动路径下是**死数据**。
⇒ 唯一能加载它们的方式是显式指定 `rule_library_code`；
而主链路 `parameter_optimize.py:483-489` 组装的 context 不含该字段
⇒ `engine.py:157` `context.get('rule_library_code')` 恒为 None。

> ⚠️ **2026-10-27 复核：原结论「库里没有这个关系」不准确，卡点定位已修正。**
>
> **① 「库↔产品」关系其实在库里** —— `RuleMethod.product_category` 上就有，
> 每个补充库对应**唯一一个具体产品**（实测全量分布）：
>
> | library_code | 规则数 | 库内 `product_category` |
> |---|---|---|
> | `base` | 585 | （全空 = 通用兜底） |
> | `R20240516093115` | 276 | 碗 |
> | `R20240702164137` | 155 | 通用 |
> | `R20230901163319` | 138 | 耳机 |
> | `R20240817094811` | 120 | 微波炉控盒 |
> | `R20240815104925` | 113 | 0815 |
> | `R20230825161658` | 88 | 把手 |
> | `R20240326160428` | 76 | 柜门 |
> | `R20231129160052` | 65 | 手机外壳 |
> | `R20231010100755` | 30 | 吹风筒手柄 |
>
> ⚠️ 但它是 **`RuleMethod` 上的字段，`RuleLibrary` 表上没有** ⇒ 原结论“查 RuleLibrary 找不到”
> 只是**查错了对象**。
>
> **② 自动选库仍走不通** —— `product_to_library_codes` 的映射表指向
> `packaging` / `auto_parts` / `medical` 等 6 个 code，**库里一个都没有**。
>
> **③ 更关键：两套产品命名完全无交集**（实测）——
> - 规则库侧（`RuleMethod.product_category`）：碗 / 通用 / 耳机 / 微波炉控盒 /
>   0815 / 把手 / 柜门 / 手机外壳 / 吹风筒手柄 —— **具体产品**
> - 主数据侧（`Mold.product_category`）：包装 / 家电 / 汽车内饰件 —— **产品大类**
>
> 交集 = **空**。且 `Mold.product_model` **全为空**，
> `mold_name` / `product_subcategory` / `product_description` **一个都命中不了**
> 规则库的 9 个产品名 ⇒ **「全库加载 + 按产品过滤」这条退路也不成立**
> （9 个库的规则会无差别涌进来 ⇒ 碗的规则会套到汽车内饰件上）。
>
> **④ 唯一可行通路：显式指定库** —— 引擎 `engine.py:175` 已读
> `context['rule_library_code']`，仓储层 `repository.py:50` 把它当作选库**第一优先级**
> ⇒ 通道**本就存在**，缺的只是「谁往里填值」。
>
> **⑤ 填值环节也是空的** —— `condition.process_context_snapshot.overrides`
> 实测 44 个 condition **key 分布 = {}** ⇒ 从没填过任何值；
> 且 **optimize 链压根没把这个字段传给算法**（`condition` 链传了）。
>
> ⇒ **卡点从「算法不会选库」修正为「建档时没人选库」**，分两半：
> ① 算法侧补 optimize 链的传参（**已做，见 §15**）；
> ② 数据侧补 `overrides.rule_library_code` 的填写入口（**需前端/业务，不在算法侧**）。

⚠️ 这不是算法 bug（`product_to_library_codes` 的注释自陈
「实际项目里这里应通过业务配置表/查找表展开，这里用启发式映射」），
但**影响面比聚合量级更大**：算法目前只用了全库 35% 的规则。

⚠️ 修法需要业务输入：**哪个库对应哪个产品**。库里没有这个关系
（`RuleLibrary` 无 polymer/product 字段，库名是 JSON key）⇒ 见 §7 D9。

---

## 4. 契约与实现脱节清单（重构后新暴露）

### 4.1 `RuleProfile.conclusion_kind` 是闲置字段 + 结论形态双判定 —— **已关闭（批 J-2，见 §19.3）**

- `profiles.py:109` 定义了 `conclusion_kind` 契约字段
- `library/rules.py:148-171`（`RuleService.classify_conclusion_kind`）**算出了它**
- `fuzzy_core/rules_filter.py:94-108`（`_conclusion_kind`）**完全不用它**，
  而是自己再判一遍，注释直言「**复刻** `library/rules.py::classify_conclusion_kind` 的判定口径」

⇒ **两份真相源**，且其中一份（契约字段）算完就扔。
⇒ 与 E7~E20 确立的「契约归内核所有、单一真相源」原则**直接冲突**。

**修法**：`rules_filter` 改读 `profile.conclusion_kind`；
或让 `RuleProfile` 直接携带拆解产物（见 4.2）。

### 4.2 「规则串只拆一次」的承诺跨层未兑现（**✅ 已关闭，见 §20.1**）

实测一条规则串被 `parse_rule()` **解析 3 次**：

| # | 位置 | 触发 |
|---|---|---|
| 1 | `library/rules.py:161` | `RuleAdapter.to_rule_profile` → `classify_conclusion_kind` |
| 2 | `library/rules.py:138` | `RuleService.match_defect_level` → `parse_rule` |
| 3 | `fuzzy_core/rules_filter.py:174` | `build_rule_objects` → `parse_rule` |

第 4 层 filter 的 docstring 宣称「规则串**只拆一次**」——它自己做到了，
但**来源层已经拆过两次**。1646 条规则 × 3 次解析。

**修法**：`RuleProfile` 携带 `parsed` 产物（契约层一次解析，下游复用），
或来源层加解析缓存。

> ✅ **已关闭（批 K，2026-10-28）**：采用「`RuleProfile` 携带 `parsed`」方案。
> 实测解析次数 **13 → 5（降 62%）**，等价性断言全绿；实现与验收见 §20.1。
>
> ⚠️ **行号已随批 K 变动**：原文三处调用点 `library/rules.py:161/138` 在重构后
> 已迁到 `library/semantics.py`（`classify_conclusion_kind` / `match_defect_name`），
> 第 3 处 `fuzzy_core/rules_filter.py` 仍在。

### 4.3 档位桶语义按 `lvl` 分裂 —— 同一规则词，门控位置不同（**已关闭，见 §18.3**）

- 权威元数据路径：`RuleKeyword.fuzzy_level` = **5**（183 个 parameter 词条全是 5）
  ⇒ `resolve_bucket(5, 'low')` = **桶 1**（论域 25% 分位）
- 推测论域路径：`engine.py:318` 硬编码 `lvl=3`
  ⇒ `resolve_bucket(3, 'low')` = **桶 0**（论域下界）

⇒ **同一个 `IV0_low`，在两条论域来源下指向不同的桶** ⇒ 门控强度差一个档位。
⇒ 这条不在既有台账（L26 只记了"倒序/退化"，没记"语义分裂"）。

> ✅ **已关闭（§18.3）**：真问题是**两条论域来源用了不同的 `lvl`**（权威 5 档 vs 推测硬编码 3 档），
> 已把推测论域的 `lvl` 由 3 改为 5。两条路径档数一致后，同一规则的落格自然一致。
>
> ⚠️ **不要误读成「档位语义漂移」**（2026-10-28 口径修正）：落格**随字段档数变化本身是正常的** ——
> 档位词是**绝对词义**（`low` 就是「偏低」这一档），它落在哪一格由**向量切了几格**决定。
> 5 档体系比 3 档体系多一个 `very_low` 在 `low` 之下 ⇒ `low` 自然上移一格（桶 1 = 25% 分位），
> **这是正确实现，不是缺陷**。详见 `_refs/system/algorithm/fuzzy-level-semantics-design.md` 决策 D1 / D3。
>
> **附带**（原表述已修正）：`LEVEL_WORDS_BY_LVL` 的 7/9 档词表里 `low` 落在 33%/25% 分位而 `medium` 在 50%
> —— 这是**该档位体系下的正常位置**（7 档体系有 `extremely_low`/`very_low` 在 `low` 之下，
> 9 档体系另有 `ultra_low`），**不是“失真”**。

### 4.4 契约层校验函数从未接线 —— **已关闭（批 J-3，见 §19.4）**

`profiles.py:131-174`（`validate_keyword_profiles` / `validate_rule_profiles`）的 docstring 写：

> 「这是"数据来源可插拔"的前提：解析出的档案必须**先过校验**才能进入构建层 ⇒
> 脏数据在边界被拦下，而不是等到内核算隶属度时才抛异常。」

**实际：生产链路零调用**（全仓仅 `_dev_refs/` 脚本与自身 `__main__` 自检）。
`library/repository.py:106`（`RuleAdapter.to_rule_profile`）与
`library/keywords.py:51`（`to_keyword_profiles`）都**不调用**校验。

⇒ 契约层写了关口，没装门。

### 4.5 诊断数据只写不读

- `engine.py:68/114`（`self._field_reports`）、`engine.py:175`（`self._diagnostics`）

全仓 grep：**只有写、没有读**。字段体检结论（authority / guessed / unknown 分类）
和规则跳过明细（`filtered.skipped`）都收集了，但**没有任何出口**——
既没进日志、也没进返回结构、也没进 `AlgorithmRecommendation`。

⚠️ **附带风险**：这两个字段挂在**模块级单例** `FuzzyEngine` 实例上
（`engine.py:494` `AlgorithmRegistry.register('fuzzy', FuzzyEngine())`）。
目前因为没人读，所以并发污染无害；**一旦接上诊断出口，必须先改成局部变量或
per-request 容器**，否则多线程下会串号。

### 4.6 检查类建议在 service 层被整批过滤

**位置**：`parameter_optimize.py:749-753`

```python
filtered_recs = [rec for rec in algorithm_recommendations
                 if _to_business_param_name(rec.get("param")) in baseline]
```

`CLAMP`（锁模力）等机台级参数不在 `ProcessParameter` 里 ⇒ 翻译后仍不在 baseline
⇒ **规则库 99 条 adjust/检查类规则的结论在 UI 上永远看不到**。
（评审文档 P1-4，未做。）

---

## 5. 清理项（不影响正确性）

| # | 项 | 位置 | 说明 |
|---|---|---|---|
| C1 | `percent_set` 只写不读 | `nets.py`（已删） | ✅ **已做（批 L-1，2026-10-28）**：删除 `percent_set` 的初始化 / 收集 / 追加三处（纯只写不读，无读取方） |
| C2 | `extra_dict` / `r_extra` 死路径 | `nets.py`（已删收集逻辑）、`models/rules.py`（**保留**） | popup 已被 filter 抽成 `advice_items`（`rules_filter.py` 直接 `continue`，不进任何推理网络）⇒ `r_extra` 恒空 ⇒ `extra_dict` 恒空<br>✅ **已做（批 L-2，2026-10-28）**：`nets.py` 删 `extra_dict` 收集（`tsk_inference` 改 `return res, {}`，docstring 说明「恒空、保留仅为签名兼容」）；⚠️ `models/rules.py` 的 `r_extra` **保留** —— `test_nets.py:141` 断言依赖它 |
| C3 | `is_numeric_value` 边界 | `parsing.py:145-157` | ~~`'--5'` 判 **True**（应为 False）；`' 5'` 判 False（`float(' 5')` 合法）~~ ✅ **已修（批 E，2026-10-27）** |
| C4 | `to_business_name` 前缀匹配**无「互不为前缀」护栏** | `field_names.py:257-264` | ⚠️ **定性修正（2026-10-28 核实）**：原文「`MP` 与 `MBP` 靠插入顺序侥幸不冲突」**不准确** —— `MP` 是 2 字符、`MBP` 是 3 字符，`'MBP0'.startswith('MP')` 为 False ⇒ **现状本就安全**，与 dict 插入顺序无关。真正缺的是**护栏**：`_validate_round_trip()` 只校验「正向译出 → 反向译回」闭合，**不校验「算法前缀之间互不为前缀」** ⇒ 将来新增 2 字符前缀（如 `MB`）会真冲突且静默错译<br>✅ **已做（批 L-3，2026-10-28）**：新增 `_validate_prefix_uniqueness()`，**import 时**校验①分段算法前缀两两互不为前缀 ②完整字段名不得形如「分段前缀+数字」⇒ 违反即 import 期抛错，不会静默错译 |
| C5 | `FuzzyRuleNet.inference` 的 `final_rule` 兜底 | `nets.py` | ✅ **已做（批 L-4，2026-10-28）**：改为**只从「命中了该输出变量」的规则里选**（`np.flatnonzero(rule_selected_list)`）；无命中时 action=0 / reason=-1 哨兵 + warning。⚠️ 语义等价：选中者激活度 ≥ 0 > -1 ⇒ 原 argmax 本就落在选中集合内 ⇒ **不改变任何有效路径的结果** |
| C6 | `_to_keyword_profile` 三分支兼容 | `engine.py` | 契约已保证返回 `KeywordProfile`（`library/keywords.py`），dict/对象分支是为测试替身留的补丁<br>⚠️ **不能删**（2026-10-28 核实）：`tests/fuzzy_kernel/_snapshot_core.py` 返回裸 dict、`_verify_defect_selection.py` / `_verify_diag_isolation.py` 返回 Kw 对象<br>✅ **已做（批 L-5，2026-10-28）**：三分支**全部保留**，改为「非契约形态记 `logger.warning` 留痕」（dict 分支与对象分支各一条）⇒ 既不破坏离线脚本，也不静默降级 |
| C7 | 倒序论域的桶序翻转 | `macros.py:161-185` | `bucket_centers` 对倒序区间产出递减中心 ⇒ 档位 0 对应论域高端，语义翻转（L26 的二阶问题）<br>⚠️ **2026-10-28 核实：生产路径不可达** —— 契约层 `library/adapters.py:220` / `:259` 对 `min_val >= max_val` 直接跳过 + warning ⇒ 倒序论域进不了内核；推测论域（`engine.py` `min=0.0` / `max=max(current*2, 0.01)`）也不会倒挂 ⇒ **只需防御性兜底，无需实现桶序翻转**<br>✅ **已做（批 L-6，2026-10-28）**：`bucket_centers` 对 `min >= max` 直接抛 `ValueError`（显式失败，不静默产出翻转的桶序）；因生产路径不可达 ⇒ 线上零影响 |
| C8 | `specs.py` 三合一 + 反向依赖 | `specs.py`（`from ..field_contract import`）、全文 | L22 / L11 未关闭：字段字典 + 校验器 + 词表挤一个文件；`specs.py` 属层 0，却 `from ..field_contract import` ⇒ **层 0 依赖上层包**（2026-10-28 核实仍在）<br>⚠️ **只标注，不动代码（批 L-8，2026-10-28，用户拍板）**：已在 `specs.py` 的 import 处加注释块标注「层 0 反向依赖 + 为何本轮不动 + 拆分需牵动其它算法包 ⇒ 属跨包重构，另开一轮」；⚠️ 该瑕疵**不影响算法结果**（三个函数都是纯函数、无副作用、无循环依赖），只影响分层纯度 |
| C9 | `_extract_defect_context` 只取首个缺陷 | `engine.py:225-247` | 反馈是 list，多缺陷时只有第一个生效 ⇒ 需业务确认口径 |
| C10 | 引擎注册双写 | `engine.py` + `parameter_optimize.py`（已删） | ✅ **已做（批 L-7，2026-10-28）**：**决定性发现** —— `fuzzy/__init__.py:22` 的 `from .engine import FuzzyEngine` 这条 import **本身就会触发 `engine.py` 模块级注册** ⇒ `parameter_optimize.py` 里 `if not get_algorithm("fuzzy")` 恒 False ⇒ 那整块是**死代码** ⇒ 删除（连同 `_engines_registered` 标志位与 `_ensure_engines_registered()` 函数），留说明性注释块指向唯一注册点 |

---

## 6. 建议推进顺序（分批，每批可独立验收）

> 原则沿用既有纪律：**小步推进、每轮工作结束统一跑一次现成验证**（pytest 41 + 黄金快照），
> **不新写测试框架**；改变数值的改动必须先与工艺员对齐量级。

| 批次 | 内容 | 风险 | 前置 |
|---|---|---|---|
| **B0** ✅ | **§3.5 specificity 标注修正**（按实际命中维度判定） | 中（命中集合不变，但规则顺序会变） | 需 D8 拍板 |
| **B1** ✅ | **§3.3 跨库去重**（去重键换业务内容，保留真实最特异） | 中（会改变命中条数**与输出数值**） | B0 完成 |
| **B2** ✅ | §3.1 聚合改为分组归一化 + 加权平均 —— **已做（批 A，2026-10-27：组内占比归一 ⇒ 聚合层裸累加等价加权平均）** | 中高（改变输出量级） | ✅ B1 完成；D3 已随之落地 |
| **B3** ✅ | **§3.2 机台物理上限落地**（2026-10-27，路线与原计划不同：不是「让论域等于机台上界」，而是「推荐值按机台上限裁剪」） | 中（越限时推荐值变；方向重算） | D2 已拍板 = (c) clip |
| **B4** ✅ | §4.1/4.2 契约收敛（`conclusion_kind` 单一真相源 + 规则串一次解析）—— **已做（批 J-2 + 批 K，2026-10-28）** | 低（结构收敛，行为应零变化） | 无 |
| **B5** ✅ | **§4.3 档位桶口径统一**（推测论域与权威论域用同一 lvl 口径）—— **已做（批 I，2026-10-28：推测论域 `lvl` 由硬编码 3 改为 5）** | 中（改变激活度） | ✅ D1 已随之落地 |
| **B6** ✅ | **§4.5 诊断出口**（先改局部变量消除单例污染，再决定出口形态）—— **已做（批 F，2026-10-27：每请求容器 + 结构化日志；诊断不进对外契约）** | 低 | 无 |
| **B7** ✅ | **§4.4 契约校验接线** —— **已做（批 J-3，2026-10-27：单条版 `keyword_profile_issues` / `rule_profile_issues`，三个出库点接线）** | 低 | 无 |
| **B8** ✅ | §5 清理项（C1~C10，可合并为一批）—— **已做（批 L，2026-10-28；C8 只标注、C9 待业务口径）** | 低 | 无 |
| **B9** ⚠️ | ~~§3.4 趋势链路~~ / §4.6 检查类建议可见性 | **不接**（§3.4 定性已推翻，见该节开头） | — | §3.4 废弃（待清理）；§4.6 前提不成立 ⇒ 实际剩 **D5**（前端分组，见 §31.2） |
| **B10** ⚠️ | **§3.6 补充库接线** —— ⚠️ **口径已改（批 Q，2026-10-29：未指定 ⇒ 全量模糊库）**，「自动选库必然落空」已消除；**业务侧「库↔产品」映射表仍未做** | 中（命中集合已变，量化见 §30.4） | ✅ B1 完成；仍需 D9 业务输入（补库规则的工艺验证 + 数据侧填写入口） |

**建议顺序理由（2026-10-27 复核后修正）**：
> ⚠️ **本表状态已于 2026-10-29 回填**（批 Q 之后）；下面的「顺序理由」是**当时的排序依据**，
> 历史记录保留 ⇒ 但**已完成的批次不再重排**，新批次从 §30/§31 接着走。
1. **新增 B0 前置于 B1** —— 「保留最特异」判据建立在 specificity 正确之上，
   而它现在**系统性错位 2 级**（§3.5）⇒ 不先修，B1 会选错保留哪一条。
2. B1 先于 B2 —— B2 的分组归一化会把副本显式放大。
3. ⚠️ **修正**：B1 不再是「纯过滤、风险低」—— 去重会缩小全局归一化的分母 ⇒
   **B1 与 B2 都会改变输出数值**，两批之间的中间态不可发布。
4. B4 放 B2 之后 —— B4 会动到结论形态判定路径，放前面可能白做两次。
5. **B10（补充库接线）风险最高且需业务输入** ⇒ 单独一批，且必须在 B1 之后，
   否则重复规则成倍计票。

---

## 7. 待决策项

| # | 决策点 | 选项 | 影响 |
|---|---|---|---|
| **D1** | 推测论域的档位口径 | (a) 推测也用 5 档（与权威一致）<br>(b) 权威路径降到 3 档<br>(c) 两者都按字段实际 `fuzzy_level` | §4.3；激活强度<br>✅ **已落地 = (a)（批 I，2026-10-28）**：推测论域 `lvl` 由硬编码 3 改为 5（规则库实测 310/311 条 `fuzzy_level=5`）⇒ 两条路径数值一致 ⇒ 同一条规则落格一致 |
| **D2** | 论域上界怎么用 | (a) `max_set_*` 直接作论域上界<br>(b) 历史数据分位数<br>(c) 推理时 clip | §3.2；**已拍板 = (c) clip（2026-10-27，批 D）** |
| **D3** | 组内聚合方式 | (a) TSK 加权平均（推荐）<br>(b) 保留累加<br>(c) 只取激活度最高的一条 | §3.1；**输出量级**<br>✅ **已落地 = (a)（批 A，2026-10-27：组内占比归一 ⇒ 聚合层裸累加等价加权平均）** |
| **D4** | 跨库副本处理 | (a) 业务内容去重留最 specific<br>(b) 全留 + priority 拉开权重<br>(c) 两者都做 | §3.3<br>✅ **已落地 = (a)（B1，2026-10-27：去重键换业务内容，留真实最特异）**；⚠️ (b) 那条路**走不通** —— `priority` 全库恒为 1（§31.1） |
| **D5** | 检查类建议展示位置 | 补机台级参数中文名与分组？单独分组？ | §4.6<br>⏳ **待拍板**（前端；见 §31.2）。⚠️ **编号歧义**：本文 §21.3 与 `fuzzy-level-semantics-design.md` 的 D5 指「`fuzzy_level` 可观测性」，**不是同一件事**（那一项已暂缓，见 §31.3） |
| **D6** | 缺陷档位是否额外加权 | (a) 不加权（结论值已编码档位）<br>(b) 按档位乘数加权 | 评审文档 P1-1，**业务语义**<br>⏳ **待拍板**（现状 = (a)：档位已进推理网络、不再硬过滤，但**不额外加权**；见 §31.1） |
| **D7** | 多缺陷反馈的处理 | 只认第一个缺陷？按缺陷分别推理后合并？ | §5 C9<br>⏳ **待拍板**（机制已就位：批 G 的 `defect_selection.py` 单一真相源 + 策略接口预留 ⇒ 接入只需新增一个策略类；见 §31.2） |
| **D8** | specificity 判定口径 | (a) 按实际命中维度判定（推荐）<br>(b) 剔除重复查询项<br>(c) 不修，去重时改用库 priority | §3.5；排序与去重判据<br>✅ **已落地 = (a)（B0，2026-10-27：按规则标签 × 当前上下文逐维比对）** |
| **D9** | 补充规则库接线范围 | (a) 本轮不接，只出诊断 + 映射建议<br>(b) 接，但需业务先给「库↔产品」映射表 | §3.6；命中集合大幅变化<br>⚠️ **部分解决（批 Q，2026-10-29）**：算法侧「自动选库落空」已消除（未指定 ⇒ 全量模糊库，适用性交规则级判定）；**业务侧仍缺**：库↔产品映射口径 + 数据侧填写入口 + 补库规则的工艺验证（见 §31.2） |

---

## 8. 与既有台账的对应关系

| 本文章节 | 对应既有台账 | 状态 |
|---|---|---|
| §3.1 聚合量级 | 评审文档 P0-3 / 台账 L1 | ✅ 已做（`engine.py:515` 组内占比归一，批 A） |
| §3.2 论域上界契约 | 评审文档 P0-2 / `specs.py` TODO 2 | ✅ 已做（批 D，2026-10-27；**路线与原计划不同**，定性已更正，见 §12） |
| §3.3 跨库副本 | 评审文档 P0-4 / 台账 L3 | ✅ 已做（B1，2026-10-27） |
| §3.4 趋势链路 | 评审文档 §5.6 | ⚠️ **定性已推翻**（2026-10-27）：引擎侧已调 `_trend_to_factor`（批 A）但**编排层从未接通**；复核判定该策略业务上不成立 ⇒ **不接、待废弃**（见 §3.4 开头） |
| §3.5 specificity 标注错位 | — | ✅ 已做（B0，2026-10-27） |
| §3.6 补充库映射落空 | — | ⚠️ **算法侧已闭合（批 Q，2026-10-29）**：自动选库落空的根因是那张写死的「产品类别 → 库编码」映射表指向的 code 在库里不存在 ⇒ **已删除该映射**，改为「未指定 ⇒ 全量模糊库，适用性交规则级判定」（见 §30）。**数据侧（`overrides.rule_library_code` 填写入口）仍待前端/业务**；**业务侧「库↔产品」映射口径 + 补库规则的工艺验证**仍未做（§31.2） |
| §4.1 结论形态双判定 | 台账 L21（契约未贯穿到内核）的近亲 | ✅ **已关闭（批 J-2 + 批 K，2026-10-28：`RuleProfile` 携带 `parsed` 产物，见 §4.1 标题与 §19.3）** |
| §4.2 规则串三重解析 | — | ✅ **已做**（批 K，2026-10-28：`RuleProfile` 携带 `parsed` 产物，解析次数 13→5，见 §20.1） |
| §4.3 档位桶口径分裂 | — | ✅ **已做（批 I，2026-10-28：推测论域 `lvl` 由硬编码 3 改为 5）** |
| §4.4 契约校验未接线 | 台账 L21 | ✅ **已做**（批 J-3，2026-10-27）：新增**单条**版 `keyword_profile_issues` / `rule_profile_issues`（不抛、逐条跳过），并在 `library/repository.py:130`、`library/assembly.py:157/218` 三个出库点接线；整批版 `validate_*_profiles` 保留给 fail-fast 调用方 |
| §4.5 诊断只写不读 | 台账 L28 | ✅ 已做（批 F，2026-10-27：每请求容器 + 结构化日志；**诊断仍不进对外契约**） |
| §4.6 检查类建议被过滤 | 评审文档 P1-4 | ⚠️ **前提不成立**（2026-10-27 复核）：`fuzzy.check` 一路保留到前端（`parameter_optimize.py` 的 `_build_description` 取提示文本、`_apply_recommendations_to_baseline` 只把**有数值**的建议写回参数）⇒ 实际剩 **D5 展示位置**（前端分组） |
| §5 C7 倒序论域桶序翻转 | 台账 L26 的二阶问题 | ✅ **已做**（批 L-6，2026-10-28：`bucket_centers` 倒序抛 `ValueError`；生产路径本不可达 ⇒ 线上零影响） |
| §5 C3 数值判定边界 | — | ✅ 已做（批 E，2026-10-27） |
| §5 清理项 C1/C2/C4/C5/C6/C8/C10 | — | ✅ **已做**（批 L，2026-10-28；C8 **只标注**、C9 待业务口径 ⇒ 详见 §5 表与 §20.2） |
| L26 推测论域退化/倒挂 | 台账 L26 | ✅ 已做（批 E，2026-10-27；只修上游正下限，C7 桶序翻转仍待做） |
| 多缺陷反馈（缺陷优先级） | — | ⚠️ **机制已做**（批 G，2026-10-27）：单一真相源 `process/algorithms/defect_selection.py` + 决策级留痕 + 策略接口预留；**业务优先级规则未实现**（等口径，机制已就位 ⇒ 接入只需新增一个策略类） |
| L28 诊断容器并发串扰 | 台账 L28 | ✅ 已做（批 F，2026-10-27） |
| §2 分层结构 | E1~E26 | ✅ **已完成**（不再动） |

**台账建议**：把本轮 §3.5 / §3.6 / §4.1 / §4.2 / §4.3 / §4.5 / C7 七项回填进
`2026-10-23-fuzzy-entry-refactor-execution.md` 的 §6 遗留问题台账，
避免下一轮再花一轮去重新发现。

---

## 9. 本轮验证记录

### 9.1 体检阶段

| 项 | 结果 |
|---|---|
| `pytest process/algorithms/fuzzy/fuzzy_core/tests tests -q` | **41 passed**（1.52s） |
| 临时量化脚本（全局归一化 + 裸累加的量级影响） | 跑完即删，未落库 |
| 代码改动 | **无**（体检阶段为只读） |

### 9.2 B0 实施后（特异级标注修正）

| 项 | 结果 |
|---|---|
| `pytest ... -q` | **41 passed**（0.96s） |
| 黄金快照 `_compare_golden.py`（`_golden_E26.json` vs 新快照） | **逐条差异 0** ⇒ 内核数值面未受影响 |
| `_verify_e2e_db.py` 命中条数 | **10 → 10**（集合零变化） |
| `_verify_e2e_db.py` specificity 分布 | 裸 **{1:10} → {4:10}** |
| 显式补充库 + prod=碗 | 命中 13 → 13；spec **{1:3, 2:10} → {3:3, 4:10}**（相对关系修正） |
| 新增自检（5 种上下文，脚本内独立参照系） | **标注与参照系一致 = True** |
| 代码改动 | `library/rules.py`（+`RuleService.resolve_specificity`）<br>`library/repository.py`（合并重复查询 + 改判定 + 删 `seen_ids`）<br>`tests/_verify_e2e_db.py`（+自检段） |

### 9.3 B1 实施后（跨库副本去重）

**实施口径（2026-10-27 用户拍板）**：

| 项 | 拍板结果 |
|---|---|
| 去重键 | 业务内容 = `(defect_code, 归一化规则串)`（不按规则主键） |
| 胜出判据 | **真实特异级优先**（同特异级则 priority 高者胜） |
| 溯源处理 | `source_ref` 保持指向胜出那条（不改格式）；被丢弃副本信息写日志 |

**全库形态（实测）**：

| 项 | 实测值 |
|---|---|
| 规则行 / 唯一业务内容 | 1646 / 942 |
| 重复组 | 360 组，**全部跨库**；**每个库内部 0 重复** |
| 重复对形态 | 一律是 `base` 的 `(poly=None, prod=None)` 行 ↔ 产品库的 `(poly/prod 明确)` 行 |
| 重复对的 priority 是否不同 | **360 组中 0 组不同**（全一致） |

**验收结果**：

| 项 | 结果 |
|---|---|
| `pytest ... -q` | **41 passed**（0.95s） |
| 黄金快照 `_compare_golden.py` | **逐条差异 0** ⇒ 内核数值面未受影响<br>（⚠️ 快照走 `FakeRepo`，**绕过 `ResourceRepository`** ⇒ 对本批改动无覆盖能力，仅作旁证） |
| 主链路（裸/prod/poly/prod+poly 四种上下文） | 命中 **10 → 10**；规则内容集合**逐条相同**；`recommended_value` 与 `confidence` **逐位相同** |
| 显式补充库场景命中条数 | 碗库 13→12、通用库 13→12、手机外壳库 14→11、0815库 13→10、<br>柜门库 13→12、耳机库 21→15、微波炉库 13→13、吹风筒库 14→14 |
| 输出数值最大绝对变化 | **0.1256**（耳机库场景）；其余场景 ≤ 5.4e-6 |
| 新增自检（第 8 段，7 种上下文，脚本内独立参照系） | **去重断言全部通过 = True** |

**数值变化机理**：去重缩小了全局归一化的分母 ⇒ 剩余规则权重上升 ⇒ 建议幅度略增。
这是**修正**而非回归 —— 重复条目本就不该参与计票。

⚠️ **本批次的实际影响面**：生产默认路径（自动选库 → 只加载 `base`）**库内 0 重复**
⇒ **命中条数与输出数值完全不变**。受影响的是「用户显式指定补充规则库」这条路径，
以及 B10 接线后会变成常态。

---

## 10. 批 A / B / C 实施记录（2026-10-27 收官）

> 本节把 §3.1（聚合量级）、§3.5（特异级权重）、§3.3（取数口径）三处缺口的
> **实际施工结果**落账，并给出新旧对比、缺陷回灌设计与三方对拍表。

### 10.1 实施批次与代码落点

按「先独立、后耦合」的顺序施工：**批 C（缺陷回灌）→ 批 B（权重链）→ 批 A（取数口径）**。

| 批次 | 项 | 内容 | 落点 |
|---|---|---|---|
| **C** | C1 | 档位词 → 论域数值纯函数（取**桶中心**） | `fuzzy_core/macros.py::level_to_domain_value` |
| | C2 | 缺陷类名字**独立**收集（缺陷名 + DL 位置名） | `fuzzy_core/rules_filter.py::FilteredRules.defect_param_names` |
| | C3 | 推理输入 = 工艺参数 + 缺陷数值（**与 `process_parameter` 分离**） | `engine.py::_infer_numeric_layer` |
| | C4 | 缺陷档位**不再硬过滤**（档位已由激活度承担） | `library/rules.py::RuleService.match_defect_name` |
| | C5 | 缺陷位置（DL）回灌：取 **high 档中心** | `engine.py::_build_defect_inputs` |
| **B** | B1 | 特异级衰减系数 ρ 常量 | `fuzzy_core/macros.py::SPECIFICITY_DECAY = 0.5` |
| | B2 | 特异级 → 匹配度权重纯函数 `s = ρ^(D-d)` | `fuzzy_core/macros.py::specificity_weight` |
| | B3 | TSK：**去全局分母** + 按**输出变量分组**归一化 | `fuzzy_core/models/nets.py::tsk_inference` |
| | B4 | delta 改为**已加权贡献**；activation 装原始激活度 | `engine.py` + `recommendations.py` |
| | B5 | **绝对激活度下限**（补闸，见 10.4） | `fuzzy_core/models/nets.py` |
| | §三⑦ | **confidence 改用原始激活度** | `recommendations.py::to_recommendations` |
| **A** | A1 | `get_methods`：**等值 → 匹配谓词** | `library/rules.py::RuleQueryService.get_methods` |
| | A2 | `get_rules`：**四级组合 → 每库一次查询** | `library/repository.py::ResourceRepository.get_rules` |

配套改动：`specs.py` 注释同步（`match_defect_level` 已删除）、`engine.py` 缺陷维度
论域取数与 `process_parameter` 解耦、`rules_filter.py` 缺陷名收集与参数名收集**互斥**。

### 10.2 新旧对比：权重链的三组量纲

改造后**三个权重**并存，各有明确职责（这是本轮最核心的结构变化）：

| 权重 | 定义 | 用途 | 旧行为 |
|---|---|---|---|
| `raw[i]` | `a_i · pri_i · s_i` | 规则原始权重 | 存在，但没有匹配度因子 `s_i` |
| `group_weight[i]` | 该规则在**所属输出参数组**内的占比（组内和 = 1） | **delta 缩放** | ❌ 旧为**全局分母**（含其它参数组的规则）⇒ 推荐值被稀释到 `1/N` |
| `raw_activation` | `a_i`（前件隶属度之积，不含 `pri`/`s`） | **confidence** | ❌ 旧用组内占比 ⇒ 「几乎没匹配上但独占一组」被报成 100% 置信 |

**匹配度权重表**（ρ = 0.5，D = 4）：

| 特异级 | 含义 | d | `s = ρ^d` |
|---|---|---|---|
| 1 | 精确匹配 | 0 | 1.0 |
| 2 | 部分材料匹配 | 1 | 0.5 |
| 3 | 部分产品匹配 | 1 | 0.5 |
| 4 | 通用兜底 | 2 | 0.25 |

⚠️ spec2 与 spec3 **同权**：两者都是「一个维度匹配、另一个不匹配」的半匹配，
信息量相同；给不同权重等于人为断言「材料比产品更重要」，规则库里没有依据。

**量级修正效果（真实库实测，2026-10-27）**：

| 场景 | 旧 recommended | 新 recommended | 旧 confidence | 新 confidence |
|---|---|---|---|---|
| `SHORTSHOT/low` | IV0 60.2（被稀释到 1/9） | **IV0 60.0**（组内无命中⇒不变） | 0.0768（组内占比） | **0.0768→原始激活度** |
| `SHORTSHOT/medium` | PP0 51.0 | **PP0 52.979** | 0.2933 | **0.2933** |
| `SHORTSHOT/high` | MEL 101.1 | **MEL 103.705** | 0.0768 | **0.0768** |
| `SHORTSHOT/very_low` | MEL 100.4 | **MEL 102.0** | 0.0183 | **0.0183** |

⇒ 旧版推荐值被**全局分母**压成作者所写量的 `1/N`（N = 全池规则条数）；
新版恢复成作者写的量级。

### 10.3 缺陷回灌设计（批 C）

**问题**：缺陷程度（`level`）与缺陷位置（`position`）此前只用于**选规则**，
从不作为**算法输入** ⇒ 「越严重越激进」这件事在算法里根本没被表达。

**方案**：

```
feedback.defect[].level     ─┐
                             ├─► level_to_domain_value(lvl, word, lo, hi)
                             │      = 该档位的**桶中心**（该档隶属度恰为 1.0，
                             │        相邻档按论域跨度自然衰减）
feedback.defect[].position  ─┘   position 恒取 'high'（规则库里 DL 前件档位
                                  实测 20 条 100% 为 high）⇒ 取 high 档中心
                                      │
                                      ▼
                          defect_inputs = {defect_name: v, position: v}
                                      │
                    ┌─────────────────┴─────────────────┐
                    ▼                                   ▼
        inference_input = {**process_parameter,      （缺陷维度**单独**追加）
                             **defect_inputs}
                    │
                    ▼
       NumTskRuleNet 的 membership_degrees ⇒ 缺陷维度参与前件门控
```

**三条硬约束**：

1. **缺陷维度绝不混进 `process_parameter`** —— 后者会被 `to_recommendations`
   当作「当前参数集合」，混进缺陷名会让推荐结果里冒出 `SHORTSHOT` 这种非参数条目。
2. **缺陷名与参数名分开收集** —— `defect_param_names` 与 `numeric_param_names`
   必须分开放：前者决定拉哪些缺陷关键词的论域；后者用于「规则缺一个门控条件」
   的字段体检，混进缺陷名会把缺陷维度误判为缺失门控。
3. **反馈没给数值的维度不建论域** —— 例如用户没填缺陷位置 ⇒ 该维度不建论域 ⇒
   其前件**不作为门控**（与改造前行为一致），不会因空列把整类规则压成 `EPSILON`。

⚠️ **批 C 是批 B 的前置条件**：绝对激活度下限（`a_i < 0.01001` ⇒ 出局）会让
「输入里缺该维度」的规则激活度恒为 `EPSILON` ⇒ 被闸门拦下 ⇒ **什么都不建议**。
因此缺陷维度必须先回灌（批 C），绝对下限（批 B5）才敢开。

**档位不再硬过滤（批 C4）的收益**：缺陷关键词是 5 档（`very_low` ~ `very_high`），
而规则库只写了 `low`/`medium`/`high` 三档 ⇒ 旧口径下用户选「极轻微 / 极严重」时
规则被**全部切光**，对外报「无可用规则」。现在档位进推理网络 ⇒ 「越严重越激进」有了算法依据。

> ⚠️ **实测校正（2026-10-28）**：本节原写「极严重时 `very_high` 档规则的激活度自然更高」，
> **不准确** —— 规则库里 **`very_high` 档规则 0 条**（前件等级词实测：low 1512 / medium 492 /
> high 1436，`very_low` / `very_high` **各 0**）。实际发生的是：
> 缺陷档位取 `very_high` ⇒ 论域值落到论域上界 ⇒ 命中的是 **high 类规则**，
> 但因高斯隶属度向相邻桶衰减，其激活度**仅为 0.1249**（= 0.1353 × 0.9231），
> 远低于「档位恰好落在桶中心」时的 0.9231。
> ⇒ 准确表述是：「**档位进推理网络后，极端档位经由相邻桶以衰减强度响应，而不是被硬过滤切光**」。

### 10.4 批 B 引入的真实回归与修法（重要）

`test_c2_low_activation_no_conclusion` 在批 B 落地后**失败**：去掉全局分母后，
「低激活度规则独占某个输出参数组」⇒ 组内占比 `1.0` ⇒ 反而独占 100% 建议权重。

⇒ 修法：**补回「绝对激活度下限」**（`a_i < MIN_ACTIVATION_THRESHOLD` ⇒ 出局）。
该闸门**与池大小无关**，不重引入全局分母。

| 方案 | 是否采纳 | 理由 |
|---|---|---|
| **绝对激活度下限**（`a_i < 0.01001` ⇒ 出局） | ✅ 采纳 | 与池大小无关；判据是「这条规则到底匹配得多准」，与人为权重无关 |
| 全局份额闸（恢复全局分母） | ❌ 否 | 会把「全池条数」重新变成稀释系数 ⇒ 回到 §3.1 的老问题 |
| 绝对下限取 `1e-3` | ❌ 否 | 与既有常量 `MIN_ACTIVATION_THRESHOLD` 语义不一致 |

⇒ **双闸门缺一不可**：绝对强度闸（`a_i`）+ 组内相对份额闸（`w_i`）。

真实链路影响：含下限 3 条 vs 放开下限 3 条，**差 0** ⇒ 对生产输出零影响。

### 10.5 批 A：取数口径（等值 → 匹配谓词）

**旧口径**（四级特异级组合）：上下文该维已知 ⇒ 规则该维必须**相等**；
上下文该维未知 ⇒ 只取「该维为 NULL」的那一级。

**新口径**（匹配谓词）：上下文该维已知 ⇒ 规则该维为 `NULL`（通用）**或**等于上下文值；
上下文该维未知（None）⇒ 该维**不设限**（「未指明」≠「不适用」）；已知但不等 ⇒ 排除。

```python
if polymer_abbreviation is not None:
    qs = qs.filter(Q(polymer_abbreviation__isnull=True)
                   | Q(polymer_abbreviation=polymer_abbreviation))
```

**四级组合的全部作用**只是把「该维为 NULL 或等于上下文值」这个集合拆成 4 段去查
⇒ 塌成**每库一次查询**后语义等价、查询数从 `4 × 库数` 降到 `库数`。

**实测影响面**（真实库，1643 条有效规则）：

| 场景 | 旧命中 | 新命中 | 差异 |
|---|---|---|---|
| 主链路（PE / 酒瓶） | 30 | 30 | **0**（逐条相同） |
| 显式库 + 缺维（`R20240702164137` + prod='通用'） | — | +9 | 多 9 条（该库 `(None,'通用')` 的通用规则） |
| 显式库 + 缺维（`R20240516093115` + prod='碗'） | — | +9 | 多 9 条（该库 `(None,'碗')` 的规则） |

⇒ 与批准方案的风险预判完全吻合：**仅「显式库 + 缺维」场景变；主链路零变化**。

### 10.6 三方对拍表（13 场景 + 1 跨组补充用例）

验收方式：**独立参照系**（论域 / 桶中心 / σ / 隶属度 / 档位表 / 权重链
在本脚本内**独立重写**，不 import 生产内核）× 生产 `FuzzyEngine` × **人工手算写死的期望值**，
三者必须全部一致（容差 `1e-9`）。

| # | 场景 | 参数 | 推荐值 | 置信度 | 方向 | 判定 |
|---|---|---|---|---|---|---|
| 1 | basic\|ctx_low | IV0 | 12.0 | 0.923116346387 | increase | OK |
| 2 | basic\|ctx_mid | IV0 | 52.0 | 0.018315638889 | increase | OK |
| 3 | basic\|ctx_high | （**无结论**） | — | — | — | OK |
| 4 | multi\|ctx_low | IV0 | 20.0 | 0.135335283237 | increase | OK |
| 5 | multi\|ctx_mid | inj_pres_1 | 105.0 | 0.135335283237 | increase | OK |
| 5 | multi\|ctx_mid | IV0 | 56.5 | 0.135335283237 | increase | OK |
| 6 | multi\|ctx_high | inj_pres_1 | 185.0 | 0.486752255960 | increase | OK |
| 6 | multi\|ctx_high | IV0 | 93.0 | 1.000000000000 | increase | OK |
| 7 | mixed\|ctx_low | IV0 | 12.0 | 0.923116346387 | increase | OK |
| 8 | mixed\|ctx_mid | IV0 | 52.0 | 0.018315638889 | increase | OK |
| 8 | mixed\|ctx_mid | inj_pres_1 | 105.0 | 0.135335283237 | increase | OK |
| 9 | mixed\|ctx_high | inj_pres_1 | 185.0 | 1.000000000000 | increase | OK |
| 10 | five_level\|ctx_mid | inj_pres_1 | 105.0 | 0.423556855491 | increase | OK |
| 11 | five_level\|ctx_high | inj_pres_1 | 185.0 | 0.606450646517 | increase | OK |
| 12 | level_number\|ctx_mid | inj_pres_1 | 105.0 | 1.000000000000 | increase | OK |
| 13 | spec_mix_same_group\|ctx_low | IV0 | **14.0** | 0.923116346387 | increase | OK |
| 14 | spec_mix_cross_group\|ctx_mid | IV0 | 53.0 | 0.135335283237 | increase | OK |
| 14 | spec_mix_cross_group\|ctx_mid | inj_pres_1 | 107.0 | 0.135335283237 | increase | OK |

**用例 13 的手算参照（批 B2 的核心断言）**：4 条同前件规则，特异级 1/2/3/4 ⇒
`s = [1.0, 0.5, 0.5, 0.25]` ⇒ 组内占比 `[4/9, 2/9, 2/9, 1/9]` ⇒
加权平均结论 `= (2×1 + 4×0.5 + 6×0.5 + 8×0.25) / 2.25 = 9 / 2.25 = 4.0`
⇒ 推荐值 `= 10 + 4 = 14.0` ✓（三方一致）。

**用例 3 的手算参照（绝对下限的语义）**：`a = exp(-8) × exp(-6.48) ≈ 5.15e-7`
< `0.01001` ⇒ **不产出任何结论**（缺陷是 high，规则要 low ⇒ 不该建议）。

### 10.7 本轮验收记录

| 项 | 结果 |
|---|---|
| `pytest process/algorithms/fuzzy -q` | **30 passed** |
| `pytest backend/tests -q`（fuzzy 相关） | **11 passed**（合计 **41 passed**） |
| 全量 `pytest -q` | 77 failed（**全部在 `process/algorithms/expert/tests/`**，原因 = `mold_info` 契约校验要求 `runner_weight`/`runner_type`/`gate_shape` 必填；**本轮未触及 expert 任何文件**，为预先存在） |
| 黄金快照 `_compare_golden.py`（`_golden_E26.json` → `_golden_ABC.json`） | 逐条差异 **152** ⇒ 全部归因到已批准的设计变更（见 10.8），**意外回归 = 0** |
| e2e 独立参照系对拍（`_verify_e2e_db.py`） | **8 段全部通过**（含新增 2 个缺维用例）；「标注与参照系一致 = True」「去重断言全部通过 = True」 |
| 13 场景三方对拍 | **14/14 通过** |
| **收尾复跑**（批 A/B/C 全部落地后） | `pytest process/algorithms/fuzzy tests` **41 passed**；`_golden_ABC.json` 自比对 **逐条差异 0（PASS）**；`_scen13_check.py` **14/14 通过**（退出码 0） |

⚠️ **回归资产归位**：13 场景对拍脚本原为一次性探针 `_tmp_scen13.py`，
但它内含**人工手算写死的期望值**、**不依赖 DB**、**可离线复跑** ⇒
归位为长期回归资产 `_dev_refs/_scen13_check.py`
（默认输出 `_dev_refs/_scen13_check.out`），§10.6 的表由它生成
⇒ 改动内核后应重跑。
其余一次性探针（`_tmp_attr.py` / `_tmp_probe_len.py` / `_tmp_probe_a.py` /
`_tmp_verify_b.py` / `_tmp_verify_c2.py` 及其输出）**已按约定用完即删**。

⚠️ **黄金快照的覆盖边界**（复用者必读）：快照走 `FakeRepo`，
**绕过 `ResourceRepository`** ⇒ 对批 A（取数口径）的改动**无覆盖能力**，
只能作旁证；批 A 的实际影响面靠 `_verify_e2e_db.py`（连真实库）验证。

### 10.8 黄金快照 152 条差异的归因

| 类别 | 条数 | 内容 |
|---|---|---|
| **A. 契约变更** | 114 | net 元组 3→4（新增 `raw_activation`，18 条）；infer 新增 `current_value`/`recommended_value`/`confidence` 三个键（72 条）；新增 spec_mix 场景（24 条） |
| **B. 已批准的设计变更** | 38 | 绝对激活度下限导致低激活度规则不再产出结论（`basic\|ctx_high` 0 条、`mixed\|ctx_high` 参数换人）；组内归一化导致同组多规则各自产出（`mixed\|ctx_mid` 1→2 条）；数值层来源覆盖 advisory 来源（`multi\|ctx_high` `hold`→`increase`）；缺陷维度回灌带来一次 `get_keywords_by_names('SHORTSHOT')` 调用 |
| **C. 意外回归** | **0** | — |

⚠️ **基线锚点**：`_golden_E26.json` 跨越多轮设计变更（输入组装口径、激活度闸、
特异级权重、置信度口径都变过）⇒ **不适合作为逐位回归锁**，其价值是历史留痕。
本轮起以 `_golden_ABC.json`（infer 30 场景 / activations 90 组 / gauss 2016 /
tri 63 / defuzz 12）为**新锚点**。

⚠️ 快照脚本的两处补强（本轮新增，否则对拍是「瞎的」）：
1. `infer` 段补记 `current_value` / `recommended_value` / `confidence` —— 之前只记
   `param_name`/`direction`/`reason` ⇒ 对**推荐值量级**与**置信度**的任何变化都无感。
2. `mk()` 支持 `(规则串, specificity)` 二元组 —— 之前 `specificity=4` **写死**
   ⇒ 31 个场景全是「通用规则」，特异级权重一次都没被测到。

### 10.9 遗留与风险

| 项 | 状态 |
|---|---|
| Mamdani 提示层仍**实际空跑** | 规则库中模糊等级结论 0 条（99 条 adjust/popup 走文本建议） |
| `spec_mix_same_group` 在 `ctx_high` 下产出 0 条 | 正确（IV0=90 ⇒ `IV0_low` 隶属度 `exp(-6.48)` < 下限 ⇒ 全部出局） |
| `expert` 模块 77 个 pytest 失败 | **预先存在**，与本轮无关（`mold_info` 契约）—— 根因已定性，见 **§11.2** |
| 缺陷位置（DL）取 high 档中心 | 依据是「规则库里 DL 前件档位实测 20 条 100% 为 high」；若后续规则库写入非 high 档，需同步调整 `engine._build_defect_inputs` |

---

## 11. 验收口径修正 + expert 基线定性（2026-10-27 收尾追加）

### 11.1 验收命令收窄（本轮起生效）

| 用途 | 命令（**在 `backend/` 目录下执行**） | 判据 |
|---|---|---|
| **默认验收**（fuzzy 改动） | `pytest process/algorithms/fuzzy tests -q` | **0 failed**（当前 = 41 passed） |
| 全量基线比对（低频） | `pytest -q` | **只报增量**（相对基线新增的失败数） |

> ⚠️ 路径注记：`backend/tests` 是**相对仓库根**的路径，而常规开发目录是 `backend/`（`manage.py` 所在）。
> 在 `backend/` 下用 `pytest backend/tests` 会得到「no tests ran」（pytest 退出码 5，**不是绿**）。

**为什么收窄**：fuzzy 与 expert **零 import 耦合**（`expert/` 对 `fuzzy` 的 import = 0 处），
fuzzy 的对外接触面只有 `process/schemas/optimization.py`，其覆盖已在 `backend/tests`（11 passed）内。
⇒ 「跑全量看 expert 有没有红」对 fuzzy 的回归判定**零增量信息**，却让每轮报告都要挂一段
「预先存在、与本轮无关」的免责声明，并用 `77 failed` 的红色标题盖住 `41 passed` 的真信号。

⚠️ **全量 pytest 不是「不用跑」** —— 它是**基线比对**用途：
一旦发现新增失败（≠ 77），即说明有跨模块影响，必须查。

### 11.2 expert 77 failed 的根因定性（与 fuzzy 无关）

| 项 | 事实 |
|---|---|
| 失败分布 | 10 个 smoke 文件 / 77 个用例，**全部**在 `process/algorithms/expert/tests/` |
| 直接原因 | `expert/specs.py` 升级了 6 个字段（**mold 侧 3 + machine 侧 3**），**10 个测试夹具里 9 个没跟上** |
| 诞生时间 | **2026-10-19**（`e019649` 引入 `runner_type` 必填 / `runner_weight` 条件必填 / `gate_shape` 条件必填）⇒ **比本轮开工早 8 天** |
| 夹具更新时间 | 2026-10-09（`1d157c52`）—— 其中 `test_suckback_smoke.py` **已更新**（带 `runner_type` / `runner_weight=30.0`），另外 9 个仍是旧版 ⇒ **那次升级漏改了 9 个文件** |
| 与 fuzzy 的关系 | **零**（零 import；`git status --porcelain -- backend/process/algorithms/expert/` 本轮为空） |

三字段的判定链（`field_contract.audit_field_completeness`）：

| 字段 | spec 要求 | 旧夹具实际 | 判定 |
|---|---|---|---|
| `runner_type` | `'condition': '必填'`（**无条件**） | **未给** | ❌ 缺失 |
| `runner_weight` | `'条件必填'`，`condition_when: {'runner_type__nin': ['热流道']}` | `0.0` | ❌ 缺失（`runner_type` 为 None ⇒ `None not in ['热流道']` 为真 ⇒ 条件成立；再叠加 `not 0.0` 为真） |
| `gate_shape` | `'条件必填'`，`condition_when: {'gate_type': '侧浇口'}` | **未给**（而 `gate_type='侧浇口'`） | ❌ 缺失 |

⇒ 3 个缺失一起抛 `ValueError: mold_info 校验失败`（`expert/data_validator.py:90`）
⇒ `ProcessInitializer` 构造失败 ⇒ 全部 smoke 用例挂掉。

> ⚠️ **补记（首轮定性时的遗漏）**：mold 侧 3 个字段之外，**machine 侧同批还漏改了 3 个字段**。
> 首轮只修了 mold 侧 ⇒ 重跑**仍 77 failed**，第二轮才定位到：

| 字段 | spec 要求 | 旧夹具实际 | 判定 |
|---|---|---|---|
| `drive_system` | `'condition': '必填'`（`MACHINE_INFO_FIELDS`；ORM 字段名就是 `drive_system`） | **未给** | ❌ 缺失 |
| `max_set_metering_back_pressure` | `'condition': '液压机必填'` | **未给** | ❌ 缺失（夹具 `power_method='液压机'` ⇒ 条件成立） |
| `max_set_decompression_pressure` | `'condition': '液压机必填'` | **未给** | ❌ 缺失（同上） |

⇒ **共 6 个字段 × 10 个文件**同批漏改 —— 这才是 B 批次的真实工作量上限（不是 3 个字段）。

### 11.3 夹具掩盖的三个真问题（**不能只补夹具就收工**）

| # | 问题 | 证据 | 性质 |
|---|---|---|---|
| ② | `runner_type` 被标为**无条件必填**，但 ORM 字段是 `null=True`（`masterdata/models/mold.py:123`） | 查库：`GatingSystem` 4 条，`runner_type` NULL=0、''=0（取值 `热流道`×2 / `冷流道`×2）⇒ **当前库安全**；但模型允许 NULL ⇒ **新建模具漏填即报错**（`ValueError` → `BizException`，`parameter_initialize.py:693`） | **潜在生产阻断**（属「运气好」而非「设计好」） |
| ③ | `gate_shape` 的**取值口径不一致**：模型无 `choices` 约束（自由文本），库里实际值是 `圆点`，而 spec 的 `condition_when` 硬编码 `'圆形'` | 查库：`Gate` 4 条，`gate_shape` 全为 `圆点`；`gate_type` 为 `针阀式热浇口`/`点浇口`/`热针点浇口`，**当前无「侧浇口」** ⇒ 条件必填暂不触发 | **潜在漏检**（一旦出现侧浇口 + `圆点`，`gate_radius` 永不判必填） |
| ④ | `not info_dict.get(key)` 把 `0`/`0.0` 判为缺失（`field_contract.py` docstring 自陈的隐患） | 逐条核验：`runner_weight` 条件必填触发时（冷流道）0 本就非法；`gate_radius`/`gate_length`/`gate_width`（侧浇口）0 非法；fuzzy 的必填字段全是**设备上限**（`max_set_*`）⇒ 0 非法 | **当前 spec 下是安全的** ⇒ **撤回 C 方案**（改成 `is None` 反而会放宽不该放宽的校验） |

### 11.4 处置分层（待拍板）

| 层 | 内容 | 影响面 | 状态 |
|---|---|---|---|
| **A** | 验收命令收窄 + 本节落文档 | 零代码改动 | ✅ **本轮已落地** |
| **B** | 10 个文件的 mold 夹具补 `runner_type`（`'热流道'`，与 `runner_weight=0.0` 语义自洽）+ `gate_shape`；machine 夹具补 `drive_system` + 2 个「液压机必填」 | 纯测试侧 | ✅ **已完成**（77 failed → 13 failed，详见 §11.5） |
| **②** | `runner_type` 无条件必填 vs ORM `null=True` 的矛盾 | 需业务决策（前端强制填 / 给默认 / 改条件必填） | ⏸ 待拍板 |
| **③** | `gate_shape` 取值域统一（加 `choices` 或改判定值） | 涉及数据口径 | ⏸ 待拍板 |
| **D** | 加 `pytest.ini` 的 `testpaths` 收口全仓收集范围 | 改工程配置，影响所有人的跑法 | ⏸ 待拍板 |

### 11.5 B 之后剩余 13 个失败的完整定性（2026-10-27 收尾）

**当前基线**（在 `backend/` 下执行 `pytest process/algorithms/expert/tests -q`）：**13 failed / 64 passed**。

这 13 个失败**分属三类，性质完全不同，不能一锅端**：

| 类 | 失败数 | 性质 | 归属 |
|---|---|---|---|
| **类 1** | 7 | 契约「必填」与兜底能力不匹配 ⇒ **真实生产阻断** | 新增待拍板项 ⑤（§11.6） |
| **类 2** | 1 | 夹具漏字段（与 B 同性质） | 纯测试侧补夹具 |
| **类 3** | 5 | **算法 / 设计缺陷**（原生，非本轮引入） | 生产代码变更，需拍板 ⑥⑦⑧（§11.6） |

#### 11.5.1 类 1：7 个（契约「必填」vs 兜底能力不匹配）

**根因**：`recommend_melt_temperature` / `recommend_mold_temperature` 在 `POLYMER_INFO_FIELDS` 中是
`condition: '必填'`（`specs.py:240-247` / `264-271`），但 `MaterialDatabase.get_defaults()` 只对
**名单内**的 abbreviation 返回默认值（`material_db.py:36-72` / `81-107`）
⇒ 查不到族 ⇒ 两个必填字段填不上 ⇒ `audit_field_completeness` 拦死（`data_validator.py:86-92`）
⇒ `ValueError` → `BizException` 400。

| # | 失败用例 | 子场景 | abbreviation | 说明 |
|---|---|---|---|---|
| 1 | `test_cool_time_smoke.py::test_scenario_b_material_gradient` | B4 | `XXX` | 未知材料兜底 |
| 2 | `test_hold_time_smoke.py::test_scenario_b_four_level_fallback` | B4 | `UNKNOWN_MATERIAL` | 未知 family 兜底 |
| 3 | `test_hold_time_smoke.py::test_scenario_c_boundary_guards` | — | `UNKNOWN_MATERIAL` | 同上 |
| 4 | `test_hold_velo_smoke.py::test_scenario_b_material_gradient` | B4 | `UNKNOWN_MATERIAL_XYZ` | 未知 family 兜底 |
| 5 | `test_inj_time_smoke.py::test_scenario_e_unknown_family` | — | `XXX_UNKNOWN` | 未知 family 兜底 |
| 6 | `test_meter_pres_smoke.py::test_scenario_f_unknown_material_default` | — | `XXX` | 未知材料保守兜底 |
| 7 | `test_temperature_smoke.py::test_scenario_h_hdpe_pe_family` | — | **`HDPE`** | **真实常用牌号** |

⇒ 前 6 个是**故意用未知材料**测兑底逻辑；第 7 个是 **HDPE**（常用牌号）⇒ **两套族解析口径不一致**：

| 层 | 实现 | 对 `HDPE` 的结果 |
|---|---|---|
| 算法层 | `helpers.parse_material_family()`（`helpers.py:96`） | → `'PE'` ✅ 认得 |
| 兜底层 | `MaterialDatabase.get_defaults()`（全名匹配 + `'+'` 拆分，**无族归并**） | → `{}` ❌ 认不得 |

⇒ `MATERIAL_DEFAULTS` 里只有 `'PE'`，**没有 `HDPE` / `LDPE` / `LLDPE`** ⇒ 这三个常用牌号在生产上**必然 400**。

**附带发现（3 条，均指向同一处设计不自洽）**：

1. `data_validator.py:94-107` 的「算法必需字段的最终检查」写了**区分性报错**
   （族里有但缺参数 vs 族里没有请补充材料参数）⇒ 但 Step 2 的 audit **先抛** ⇒ 这段**永远不可达**。
2. 该检查只列了 `melt_density` / `recommend_melt_temperature`，**漏了 `recommend_mold_temperature`**；
   而算法层 `algorithm_engine.py:2085` / `2308` 是**直接索引** `mat['recommend_mold_temperature']`
   ⇒ 若只放开契约而不补这一项，会从 400 变成 `KeyError` 500。
3. `specs.py:246` / `:270` 注释写「algorithm 默认 250 / 默认 0」，但算法层**并无默认值**
   ⇒ 注释与实现不符（实际靠 audit 兑底）。

#### 11.5.2 类 2：1 个（夹具漏字段，与 B 同性质）

| 失败用例 | 缺失字段 | 位置 |
|---|---|---|
| `test_inj_time_smoke.py::test_scenario_g_boundary`（G1） | `machine_info.max_set_injection_velocity`（必填） | `specs.py:153-160` |

⇒ 夹具 `_machine(max_velo=0.0)` 漏了该字段 ⇒ **补夹具即可，零算法改动**。

#### 11.5.3 类 3：5 个（算法 / 设计缺陷）

**3-A 崩溃（2 个用例）：`_apply_multi_injection` 热流道分支未处理 `vps_pos=None`**

| 项 | 事实 |
|---|---|
| 位置 | `algorithm_engine.py:2700`（`vp_pos = proc.vps_pos`）、`:2723-2727`（`vp_pos + pos_coefs[i] * (total_len + decomp_dist)`） |
| 为何可能是 None | `vps_pos` 是 `Optional[float]`，**仅** `vps_mode ∈ {0, 3}` 时赋值（`algorithm_engine.py:2179-2191`）；`vps_mode ∈ {1, 2}`（时间/压力切换）时保持 None |
| 触发条件 | 热流道（`runner_weight <= 0.01`）**且** `inj_stg > 1`（总重较大 ⇒ 自动 4 段）**且** `vps_mode ∈ {1, 2}` |
| 现象 | `TypeError: unsupported operand type(s) for +: 'NoneType' and 'float'` |
| **生产影响** | `parameter_initialize.py:693` **只捕 `ValueError`** ⇒ TypeError 直接冒泡 ⇒ **接口 500**（不是 400） |
| 第二个 None 源 | `decomp_dist = proc.pst_met_decomp_dist`（`pst_mode == 0` 时恒 None；当前默认 `pst_decomp_default_mode = 1` ⇒ 平时不触发） |
| 命中用例 | `test_vp_switch_mode_smoke.py::test_scenario_b_user_int`（B1 `vps_mode=1`）、`::test_scenario_d_boundary`（D1 `vps_mode=5` 越界→回退字符串 `'时间'`） |

**3-B 静默行为错误（1 个用例）：`vps_mode` 被默认值预填 ⇒ 字符串兼容分支永久失效**

| 项 | 事实 |
|---|---|
| 机制 | `ProcessSetDefaults.DEFAULTS['vps_mode'] = 0`（`process_set.py:107`）+ `fill_defaults` 用 `if not process_set.get(key)` **无条件填**（`process_set.py:133-135`） |
| 后果 | `algorithm_engine.py:2153-2156` 的 Level-1 判断**必然命中** ⇒ Level-2 字符串分支（`VP_switch_mode`）**永远不可达** |
| 实测证据 | 日志 `VP 切换参数: mode=0 (source=explicit)` —— 老数据传 `VP_switch_mode='时间'` 被**静默降级**为「位置切换」，**不报错、语义错** |
| 命中用例 | `test_vp_switch_mode_smoke.py::test_scenario_c_string_legacy`（C1 的 `source=legacy_string` 断言被 helper 吞成记录；C2 的 `vps_t=None` 抛 TypeError） |
| 引入时间 | `process_set.py` 于 **e019649（2026-10-19）新增** ⇒ 属**本轮之前引入**（不同于 3-A） |

**3-C 设计 vs 测试期望冲突（2 个用例）：`pst_met_decomp_t` 在距离模式下恒为 None**

| 项 | 事实 |
|---|---|
| 实现 | `algorithm_engine.py:2456-2460` 注释明确：「1（距离）：返回 压力/速度/距离，**时间字段 None**」；`pst_decomp_default_mode = 1`（`rule_matcher.py:373` / `expert_rules.json:582`） |
| 结论 | `proc.pst_met_decomp_t` 恒 None **是有意设计**（只输出“用户所选模式对应的那个物理量”） |
| 但 | 算法**内部已算出** `pst_time`（实测日志 `T=0.11s`）⇒ 物理量存在，只是不写回 |
| 命中用例 | `test_suckback_smoke.py::test_a_pp`（期望 T ≥ 0.06）、`::test_i_switch_handle`（期望 T = 0.26） |
| 定性 | **属测试期望过时**，不是算法 bug；但需业务确认口径（§11.6 ⑧） |

#### 11.5.4 时间线证据（决定性）

用 `git archive e2184d7 backend`（2026-10-09，算法与测试**同批诞生**的那个提交）还原到临时目录实测：

| 版本 | expert 测试结果 | 含义 |
|---|---|---|
| `e2184d7`（2026-10-09，算法+测试同批诞生） | **5 failed / 72 passed** | 失败的**正是**类 3 的那 5 个 ⇒ **类 3 是原生缺陷** |
| `e019649`（2026-10-19，契约升级 + 新增 `process_set.py`） | **77 failed**（全红） | 契约升级把 72 个绿的打红 ⇒ B 修的 64 个全在**偿还这 10 天的债** |
| 当前（B 修完夹具后） | **13 failed / 64 passed** | 类 1 的 7 个 + 类 2 的 1 个 + 类 3 的 5 个 |

⇒ **类 3 被 10-19 的契约错误掩盖了 10 天**；`e019649` 同时**新增**了 3-B。

### 11.6 新增待拍板项（本轮新发现）

| # | 问题 | 证据 | 性质 | 建议 |
|---|---|---|---|---|
| ⑤ | 类 1：两个温度字段「必填」 vs 兜底能力不匹配；`HDPE`/`LDPE`/`LLDPE` 无族默认值；`data_validator` 的区分性报错不可达；`recommend_mold_temperature` 漏检 | §11.5.1 | **真实生产阻断**（用户自建牌号 / HDPE 必然 400） | 新开一批：契约与兜底口径对齐（需业务确认放开哪一侧） |
| ⑥ | 类 3-A：`_apply_multi_injection` 未处理 `vps_pos=None` | §11.5.3 | **接口 500**（生产崩溃） | 修生产代码（需拍板兑底策略） |
| ⑦ | 类 3-B：`vps_mode` 默认预填 ⇒ `VP_switch_mode` 字符串兼容永久失效 | §11.5.3 | **静默行为错误**（老数据语义降级） | 修 `process_set.py` 填充策略或判定顺序 |
| ⑧ | 类 3-C：`pst_met_decomp_t` 距离模式恒 None | §11.5.3 | 口径待确认（设计 vs 测试） | 业务确认后二选一（改实现 or 改测试期望） |

---

## 12. 批 D：机台物理上限落地（2026-10-27 收尾追加）

### 12.1 起因：范围纠偏

上一轮（批 A/B/C）收尾后，焦点仍留在 expert 侧。核实后确认：

| 项 | 事实 |
|---|---|
| 批 A/B/C 之后的 expert 改动 | 10 个测试夹具（B 批次）+ 3 份文档，**零 fuzzy 生产代码** |
| fuzzy 生产代码最后修改 | 15:34~15:53（批 A/B/C 收官），此后未动 |
| expert 与 fuzzy 关系 | **零 import 耦合**，业务独立 ⇒ expert 的工作对 fuzzy 产出零贡献 |

⇒ 用户拍板：**切回 fuzzy**，本批从 fuzzy 本体的缺口起手。

### 12.2 §3.2 的定性修正（两次推翻）

原文把 §3.2 写成「`max_set_*` 是论域上界（判级依据），标了必填但没人接」。
逐条核对代码 + 实测数据后，**这个定性本身是错的**（详见 §3.2 表格）：

| 环节 | 原判断 | 实测 |
|---|---|---|
| 判级论域来源 | `machine_info.max_set_*` | **`RuleKeyword.range_min/range_max`** |
| engine 是否读 machine_info | 「读不到论域上界」 | **完全不读** |
| 「当前值×2」自造论域 | 缺上界即触发 | **只在规则库元数据缺失时触发** |
| `max_set_*` 真实身份 | 论域上界 | **推荐值的机台物理天花板** |

⚠️ **同时更正一处记录错误**：上一轮把「`OptimizeDataValidator.validate` 零调用」记为 §4.4，
实际那是 §3.2 的范畴；**§4.4 讲的是 `profiles.py` 的内核契约校验**
（`validate_keyword_profiles` / `validate_rule_profiles`），与本批无关，**状态仍是「未做」**。

### 12.3 拍板记录

| 决策点 | 选项 | 拍板 |
|---|---|---|
| 下一批放哪 | expert / fuzzy | **fuzzy，从 §3.2 起手** |
| 缺机台上限时 | 400 / warning 不裁剪 | **warning + 不裁剪 + 不拦请求**（缺数据 ≠ 不能给建议） |
| 上界怎么用（D2） | (a) 作论域上界 / (b) 分位数 / (c) 推理时 clip | **(c) clip** |

### 12.4 落地改动（4 处 + 1 护栏）

| # | 改动 | 位置 |
|---|---|---|
| 1 | 8 个 `max_set_*`：desc 改「推荐值物理天花板」，condition 「必填/液压机必填」→「可选」 | `fuzzy/specs.py:64-148` |
| 2 | 新增 `PARAM_LIMIT_FIELDS`（算法参数前缀 → machine_info 字段名）+ `resolve_param_limits` + `lookup_param_limit` | `fuzzy/specs.py` |
| 3 | engine 读 `context['machine_info']` 做推荐值裁剪：越限封顶 + **方向按裁剪后相对位置重算** + 写入 `_field_reports`（`layer='machine_limits'`）+ 日志留痕 | `fuzzy/engine.py::_apply_machine_limits` |
| 4 | `test_optimize_smoke.py` 5a/5b/5c 断言随口径同步（缺上限不再拒） | `backend/tests/` |
| 护栏 | 8 组用例：映射 / 缺值不补 / 段号取上限 / 整段参数不参与 / 封顶 / 方向重算 / 未越限不动 / 无上限不裁 | `backend/tests/test_fuzzy_machine_limits.py`（新建） |

**分层落点**：契约（`specs.py`，层 0）→ 编排（`engine.py`，层 1）；
`recommendations.py` 纯函数层**一行未动**；`parameter_optimize.py`（service）**一行未动**。

**方向重算的必要性**：规则说「调高」但被物理上限压回时，若不重算 `direction`，
前端会显示成「↑ 180→100」这种自相矛盾的箭头。

### 12.5 验收

| 项 | 结果 |
|---|---|
| fuzzy 全量（`pytest process/algorithms/fuzzy tests -q`） | **49 passed**（原 41 + 新护栏 8），无回归 |
| expert 全量 | **13 failed / 64 passed** —— 与本批改动前**完全一致**（fuzzy/expert 零耦合） |
| 裁剪前后对照（44 个 ProcessCondition 全跑） | 温和当前值：**0 条被裁**（无误伤）<br>当前值在论域高端：**42 条被裁**（`IV0` 106.2954 → 80.0000）<br>`cond=10` / `cond=41` **恰好未被裁**（正是机台没填上限的 2 台）⇒ 缺口口径正确 |
| 临时产物 | 3 个诊断脚本用完即删，仓库无残留 |

### 12.6 本批**不做**（明确边界）

| 项 | 理由 |
|---|---|
| 把 `max_set_*` 用作判级论域 | 会让同一套参数在不同机器上判出不同等级、规则命中行为整体漂移（已更正 `specs.py` TODO 2） |
| 把 `OptimizeDataValidator` 接进 service 层 | 字段已非必填，接了也不拦人；口径已定为「缺上限不拦」 |
| 改判级论域的来源 | 同第一行 |
| §4.4（`profiles.py` 内核契约校验接线） | 与本批无关，状态仍「未做」 |
| §3.6 补充库选库映射落空 | 独立缺口，需单独一批（64% 规则库是死数据） |
| expert 侧 ⑤⑦⑧（§11.6） | 用户已拍板不做，留挂 |

---

## 13. 批 E：数值边界与论域口径（2026-10-27 收尾追加）

### 13.1 起因与范围界定

§5 清理项里的 **C3（数值判定边界）** 与 §8 台账里的 **L26（推测论域退化/倒挂）**
是唯二「**不需要业务输入、不需要动口径、且能独立验收**」的算法侧欠账
⇒ 合并为**批 E**（延续本文既有的批 A/B/C/D 编号）。

**范围界定（明确排除）**：

| 排除项 | 理由 |
|---|---|
| B4 结构收敛 / B8 清理 / B9-① service 层可见性 | 均非「算法功能实现」 |
| B10 规则库接线 | 需业务输入 |
| §3.4 迭代趋势链路 | 引擎侧已做（`engine.py:187` 已调 `_trend_to_factor`），但编排层 `process/services/parameter_optimize.py::_compose_algorithm_context` **未把 `iteration_trend` 放进算法上下文** ⇒ 属 **service/编排层**，不在本轮 |

### 13.2 拍板记录

| 决策项 | 用户口径 | 对本批的影响 |
|---|---|---|
| 范围 | 四批全做 | 本批只做「不依赖任何待拍板项」的部分 |
| D1 档位口径 | **暂不动口径** | 推测论域继续用 `lvl=3`（权威路径是 `lvl=5`）⇒ **本批不碰** |
| D7 多缺陷 | 一次只解决一个缺陷，优先级机制**预留** | 不属本批 ⇒ 批 G |
| 诊断出口 | **结构化日志**（不动对外契约） | 不属本批 ⇒ 批 F |

### 13.3 改动落点（2 处代码）

#### ① `fuzzy_core/parsing.py::is_numeric_value` —— C3

该函数是「规则层 `library/rules.py::classify_conclusion_kind` 与第 4 层
`fuzzy_core/rules_filter.py` 必须共用的**唯一判定口径**」。原实现两个边界都错：

| 边界 | 原实现 | 后果 |
|---|---|---|
| 只去**一个**负号 | `lstrip('-')` 把 `--5` 削成 `5` | 判为数值 ⇒ 数值层 `float('--5')` 抛 ValueError ⇒ **一条脏规则拖垮整层**（正是本函数 docstring 自己警告的塌方） |
| 允许前后空白 | 不剥空白，`' 5'` 判为非数值 | 合法结论被降级成文本建议（方向相反：值是对的、形态错了） |

改后口径：剥空白 → 去百分号 → 去**一个**前导负号 → 去一个小数点 → 必须是纯数字。

> ⚠️ **实测发现（探针纠正了我一条错误预期）**：`'IV0_add_ 5'` 这种「结论值带前导空格」
> 的情形，**根本到不了** `is_numeric_value` —— 规则串按**空白分词**（`parse_rule`），
> `'IV0_add_ 5'` 在解析阶段就被拆成两个 token ⇒ 该边界只可能出现在
> **直接调用** `is_numeric_value` 的路径上。已在验证脚本里改成「分词后结论段数 = 2」的核对。

#### ② `engine.py::_load_keyword_profiles` 推测论域正下限 —— L26 上游修

原：上界 = `当前值 × 2`。当前值为 0 ⇒ 论域退化成 `[0, 0]`（σ=0 ⇒ 隶属度恒 0/nan）；
当前值为负 ⇒ 区间倒挂 `[0, 负数]`。两种情况都让该字段的**门控失效**（内核侧只告警）。

改后：**只在算出来的上界非正时兜底**为 `0.01` ⇒ 正数路径**逐位不变**。

> **刻意不用 `max(current*2, 0.01)`**：那会让 `current=0.001` 的论域从 `[0, 0.002]`
> 变成 `[0, 0.01]` —— 当前值相对位置从 50% 分位漂到 10% 分位 ⇒ **档位判断变化**。
> 「非正才兜底」是唯一能做到正数路径零扰动的写法。

### 13.4 验收

| 项 | 结果 |
|---|---|
| `pytest process/algorithms/fuzzy tests -q` | **49 passed**，无回归 |
| 黄金快照 `_golden_ABC.json` vs 新快照 | **逐条差异 0（PASS）** |
| `_scen13_check.py`（13 场景三方对拍 + 手算参照系） | **14/14 通过** |
| `_verify_e2e_db.py`（连真实库 8 段自检） | 全通过（去重断言 True、标注与参照系一致 True） |
| `_verify_edge_boundaries.py`（本批新建） | **EXITCODE=0，全部 PASS** |
| expert 全量 | **13 failed / 64 passed** —— 与改动前**完全一致**（fuzzy/expert 零耦合） |
| 临时产物 | 诊断脚本用完即删，仓库无残留（新增的 `_verify_edge_boundaries.py` 是长期回归资产） |

### 13.5 覆盖边界（如实说明）

**黄金快照对本批无覆盖能力**：

- 快照走 `FakeRepo`，论域在 `KEYWORDS` 里**显式给定** ⇒ **推测分支进不去**
- e2e 连真实库，但生产数据里没有「当前值为 0/负」的字段命中该分支

⇒ 故新建 `_dev_refs/_verify_edge_boundaries.py` 作为本批**专用回归资产**：
① `is_numeric_value` 边界（12 用例 + 8 条与 `float()` 可解析性的对齐断言）
② 推测论域正下限（当前值 0 / -5 / 0.001 / 10 / 100，断言 `min<max`、上界为正、
`step>0`、隶属度无 nan）③ `classify_conclusion_kind` 对 `'--5'` 判 advisory。
参照系是脚本内**独立写的期望值 + `float()` 解析性**，不复用被测函数。

### 13.6 归属澄清：2 个无元数据关键词（**规则库数据治理，非算法缺陷**）

排查中实测：规则前件引用 **49** 个关键词名，其中 **47** 个有 `RuleKeyword` 权威元数据，
**2 个没有**：

| 名称 | 出现次数 | 涉及规则 | 实测行为 |
|---|---|---|---|
| `HOLDEXIST` | 3 | `IF FLASH_* AND HOLDEXIST_high AND PP0_high THEN PP0_reduce_*` | 无元数据 + 无当前值 ⇒ `unknown` ⇒ **不建论域 ⇒ 门控被静默忽略** |
| `injectstage3` | 2 | `IF SHORTSHOT_* AND MEL_high AND IV1_low AND injectstage3_high THEN IV1_add_*` | 同上 |

⇒ 这 5 条规则的第三个门控条件**当前不生效**（激活度偏高）。
`IV3` 在 `RuleKeyword` 中**存在** ⇒ `injectstage3` 疑为 `IV3` 的历史写法；
`HOLDEXIST` 的业务含义不明。

**归属**：属**规则库数据治理**（补 `RuleKeyword` 元数据 + 修正规则串），
**不是算法缺陷**。算法侧只需让它**可见** —— 由批 F 的结构化诊断出口覆盖。

> 另：结论侧 27 个参数名**全部**有元数据；畸形数值结论实测 **0 条**
> ⇒ C3 是**预防性**修复，不是活 bug 的补救。

### 13.7 本批**不做**（明确边界）

| 项 | 理由 |
|---|---|
| D1 档位口径（推测 `lvl=3` → 权威 `lvl=5`） | 用户拍板「暂不动口径」 |
| §4.1 结论形态双判定收敛 | 需与批 F/H 一起做，避免重复拆解析 |
| §5 C7 桶序翻转 | 独立问题，与本批正下限无耦合 |
| `HOLDEXIST` / `injectstage3` 补元数据 | 规则库数据治理，需业务确认语义 |

---

## 14. 批 F：诊断出口（2026-10-27 收尾追加）

### 14.1 起因：不是「加日志」，是「单例 + 实例属性」的并发串扰

§4.5 记的是「诊断数据只写不读」—— 但动手前先查了现状，发现**比这严重一层**：

| 事实 | 位置 |
|---|---|
| `FuzzyEngine` 是**模块级单例**（全进程一个实例） | `engine.py` 末尾 `AlgorithmRegistry.register('fuzzy', FuzzyEngine())` |
| 诊断清单 `_field_reports` / `_diagnostics` 是**实例属性** | `engine.py::__init__` |
| `recommend()` 开头**无条件重置**这两个列表 | `engine.py::recommend` |
| 推理过程中再往里追加 | `engine.py` 三处写入点 |

⇒ 两个并发请求共用一个实例 ⇒ **B 请求开头会把 A 正在写的清单清掉**，
A 醒来后读到的是 **B 的内容**。

**已实测复现**（修复前）：A 的条目（`PP0 → guessed`）消失，A 读到 B 的（`PP0 → unknown`）。

之所以至今没炸成生产事故：这两个列表**只写不读**（没有任何 getter）。
但本批的目的正是让诊断**可见** ⇒ 继续留在实例属性上就是**跨请求串数据**。

### 14.2 拍板记录

| 决策项 | 用户口径 | 本批的落实 |
|---|---|---|
| 诊断出口 | **结构化日志** | 每次请求一条 JSON（`event` + `field_reports` + `diagnostics`） |
| 对外契约 | **不动** | 诊断**不进** HTTP 响应、不进推荐结果，只进日志 |

### 14.3 改动落点

| 文件 | 改动 |
|---|---|
| `fuzzy/diagnostics.py`（**新增**，层 1） | `Diagnostic` 容器 + `contextvars.ContextVar` 承载 + `request_diagnostics()` 作用域 + 结构化日志出口 |
| `fuzzy/engine.py` | 删两处实例属性；`recommend()` 改用诊断作用域；3 处写入点改走容器；新增 `_diag` / `_field_reports` / `_diagnostics` 兼容读取层 |
| `fuzzy/__init__.py` | 分层说明补上 `diagnostics` |

### 14.4 三个关键设计决策

**① 为什么用 `ContextVar` 而不是 `threading.local` / 传参**

- `threading.local` 在 **ASGI 协程**下不隔离（同一线程的多个 task 共享）；
  `ContextVar` 在同步（WSGI/uWSGI 多线程）与异步（ASGI）下都按「执行上下文」隔离。
- **传参**（`_recommend(ctx, diag)` 一层层往下传）要改 6 个方法签名；
  `ContextVar` **不改任何现有方法签名**。

**② 为什么内容结构一点没改**

`Diagnostic` 的字段名与内容结构**与旧的实例属性逐字一致**（`field_reports` / `diagnostics`）：
`tests/fuzzy_kernel/_snapshot_core.py` 会把 `_diagnostics` 的 `repr` 写进**黄金快照**，
结构一变快照就 diff ⇒ 改结构会把「重构」变成「行为变更」，白白多一轮验证。

**③ 为什么保留实例槽位 `_last_diag`**

既有读取约定是「`recommend()` 返回后**仍能读到**本次诊断」
（`tests/fuzzy_kernel/_snapshot_core.py` 与 `_verify_e2_offline.py` 都依赖它）。
`ContextVar` 在作用域退出时会把容器摘掉 ⇒ 需把容器**移交给**实例槽位。

⚠️ **如实标注**：并发下 `_last_diag` 会被别的请求覆盖 ⇒ 它**只供调试与脚本**，
生产不依赖它（诊断已在请求内由 `request_diagnostics` emit 成结构化日志）。

### 14.5 验收

| 项 | 结果 |
|---|---|
| `pytest process/algorithms/fuzzy tests -q` | **49 passed**，无回归（**零测试改动**） |
| 黄金快照 `_golden_ABC.json` vs 新快照 | **逐条差异 0（PASS）** |
| `_scen13_check.py`（三方对拍 + 手算参照系） | **14/14** |
| `_verify_e2e_db.py`（真实库 8 段） | 全通过 |
| `_verify_e2_offline.py` | 全 PASS（含「脏规则被记入诊断清单」） |
| `_verify_edge_boundaries.py`（批 E 资产） | 全 PASS |
| `_verify_diag_isolation.py`（**本批新建**） | **ALL PASS，EXITCODE=0** |
| expert 全量（`process/algorithms/expert`） | **13 failed / 64 passed** —— 与基线**完全一致** |

> ⚠️ **一处如实说明**：`molding-expert`（独立仓库）的全量测试**在本机跑不起来**
> （它的 `.venv` 缺 pytest / requests，optima 的 venv 缺 expert 的依赖）。
> 本轮**全部改动都在 `molding-optima` 内**，expert 仓库零改动（且 fuzzy/expert 零 import 耦合）
> ⇒ 那个基线数字本轮**未复跑**，但也不受影响。

### 14.6 覆盖边界与遗留

| 项 | 状态 |
|---|---|
| 并发隔离 | ✅ 已实测（修复前复现、修复后通过，两头都有脚本留证） |
| 结构化出口 | ✅ 每次请求一条 JSON |
| 诊断进对外契约 | ❌ **不做**（用户拍板「不动对外契约」） |
| 散点 `logger.warning` | **保留不动** —— 那是「人读的即时告警」，与「机器读的请求级快照」是两种粒度 |
| 日志量 | 每次请求多一条 INFO（字段分类几乎必然非空）⇒ 如嫌吵可降级为 debug，**本轮未做**（属调优项） |

### 14.7 本批**不做**（明确边界）

| 项 | 理由 |
|---|---|
| 诊断进 HTTP 响应 / 推荐结果 | 用户拍板「不动对外契约」 |
| 把散点 `logger.warning` 统一改写成结构化 | 会改变现有可观测行为，属另一轮 |
| §4.1 结论形态双判定收敛 | 需与批 H 一起做，避免重复拆解析 |
| 批 G 的缺陷选取留痕 | **批 G 已做**（2026-10-27，见 §16；落在 `Diagnostic.selections` 容器） |
| 批 H 的契约校验跳过留痕 | 批 H |

---

## 15. optimize 链的「显式指定规则库」通道（2026-10-27）

### 15.1 为什么做这个

§3.6 复核把卡点定位清楚后，**算法侧唯一能立刻落地的一环**是
「**optimize 链把 `rule_library_code` 传给算法**」—— 引擎与仓储层的通道本就存在
（`engine.py:175` → `RuleQueryContext` → `repository.select_libraries()` 第一优先级），
只有 optimize 链漏传。

⚠️ **零行为变更**：`overrides` 实测恒空 ⇒ 传入 `None` ⇒ 与现状完全等价
（黄金快照逐条差异 0 可证）。

### 15.2 改动落点

| 文件 | 改动 |
|---|---|
| `process/services/parameter_optimize.py` | 新增 `_extract_context_overrides()`；`_compose_algorithm_context` / `_infer_kernel` 加 `rule_library_code` 参数并透传；`infer()` 从 `condition.process_context_snapshot.overrides` 取值 |
| `process/algorithms/fuzzy/engine.py` | docstring 的 `rule_library_code` 示例值由**不存在的** `'packaging'` 改为真实 `'R20240516093115'` |
| `tests/_verify_e2e_db.py` | 新增第 9 段（5 条断言）锁住该通道 |

### 15.3 数据流

```
condition.process_context_snapshot.overrides.rule_library_code
    └─> _extract_context_overrides()          # service 层读取（容错：非 dict → {}）
            └─> _infer_kernel(rule_library_code=…)
                    └─> _compose_algorithm_context(...)
                            └─> context['rule_library_code']
                                    └─> engine.py:175 → RuleQueryContext
                                            └─> repository.select_libraries()
                                                    └─> 选库第一优先级
```

### 15.4 验收

| 项 | 结果 |
|---|---|
| `pytest process/algorithms/fuzzy tests -q` | **49 passed**（零测试改动） |
| 黄金快照 `_golden_ABC.json` vs 新快照 | **逐条差异 0（PASS）** ⇒ 证明零行为变更 |
| `_verify_e2e_db.py` | 8 段 + **新增第 9 段全通过** |
| `_scen13_check.py` | **14/14** |
| `_verify_e2_offline.py` / `_verify_edge_boundaries.py` / `_verify_diag_isolation.py` | 全 PASS |

**第 9 段实测**：

| 场景 | 命中 | 补充库规则 |
|---|---|---|
| 指定 `R20240516093115`（碗） | 36 条 | **6 条**（真的进来了） |
| 未指定 | 30 条 | 0（现状不变） |

### 15.5 本批**不做**

| 项 | 理由 |
|---|---|
| 修 `product_to_library_codes` 的映射表 | 库 code 与产品名是两套体系，缺业务判断 |
| 全库加载 + 按产品过滤 | 两套命名零交集 ⇒ 9 个库的规则会无差别涌进来 ⇒ 必然给错建议 |
| `overrides.rule_library_code` 的**填写入口** | 属前端/建档流程，**不在算法侧** |
| 补库规则下的推荐值重标定 | 补充库规则此前从未参与推理 ⇒ 其推荐值未经工艺验证 |

### 15.6 剩下的那一件事（**不在算法侧**）

让建档/优化流程能填 `condition.process_context_snapshot.overrides.rule_library_code`。

⚠️ **如实说明**：**这一件不做，本通道永远为空，用户仍然感知不到变化**；
做完之后 1058 条补充库规则即刻可用。这是算法侧能做的全部 —— 
剩下的卡在**谁去填这个值**。

---

## 16. 批 G：缺陷选取单一真相源 + 留痕 + 策略接口预留（2026-10-27 收尾追加）

### 16.1 起因：同一份反馈，两个引擎可能选不同的缺陷，且**没人知道为什么**

契约层**早就是列表 + 优先级语义** —— `process/schemas/optimization.py:94`
的字段说明写着「defect[]：缺陷反馈列表（多个，**算法识别优先级**）」。
但算法侧**从未实现**这个优先级语义，而是**各引擎各取各的**：

| 引擎 | 旧实现 | 后果 |
|---|---|---|
| fuzzy | 遍历取**第一个有 `keyword_name`** 的（跳过无效项） | — |
| empirical | **只看 `defects[0]`**，首项无效就**整体放弃**（不往后找） | 首项无效 ⇒ 经验引擎恒返回空推荐 |

⇒ **同一份反馈，两个引擎可能选中不同缺陷**；且选取依据**零记录** ——
事后无法回答「为什么选了短射、没选缩水」「前面那项为什么被跳过」。

用户口径（D7）：一次只解决一个缺陷，缺陷之间有**调整优先级**而非合并。
⇒ 本批做**机制**（真相源 + 留痕 + 策略接口），**不实现业务优先级规则**。

### 16.2 拍板记录

| 项 | 口径 |
|---|---|
| 批 G 交付边界 | **单一真相源 + 留痕 + 策略接口预留**（用户拍板） |
| D7 多缺陷 | 一次只解决一个缺陷；优先级机制**预留**，不实现规则 |
| 留痕出口 | fuzzy 走 per-request 诊断容器（批 F 的机制）；empirical 走结构化日志 |
| 对外契约 | **不动**（留痕只进诊断/日志，不进 HTTP 响应、不进推荐结果） |

### 16.3 改动落点

| 文件 | 改动 |
|---|---|
| `process/algorithms/defect_selection.py`（**新增**，213 行） | `DefectSelection`（产出物）/ `DefectSelectionStrategy`（Protocol，策略接口）/ `FirstValidDefectStrategy`（默认）/ `FirstOnlyDefectStrategy` / `select_defect()`（唯一入口）。**零 ORM 零 Django**（只认 context 里的裸 dict） |
| `process/algorithms/fuzzy/engine.py` | `_recommend`：选取改走真相源 + 写留痕到 `self._diag.selections`；`_extract_defect_context`：实现改为走真相源（**返回形状不变**） |
| `process/algorithms/empirical/empirical_algorithm.py` | `recommend` / `is_available`：改走真相源（各自策略）；新增 `_log_selection()` 结构化留痕 |
| `process/algorithms/fuzzy/diagnostics.py` | `Diagnostic` 新增**第三个容器** `selections`（决策级留痕，与规则级诊断分开） |

### 16.4 三个关键设计决策

**① 落点为什么在 `algorithms` 包根，而不是 `fuzzy/` 里**
跨包共用（fuzzy + empirical）⇒ 放包根，产出物 `DefectSelection` **具名**；
零 ORM 零 Django ⇒ 不污染边界。符合规范「跨包同类物同名、模块名指向产出物、
边界层用具名契约对象」。

**② 为什么两个引擎的策略不同（不强行统一）**
- fuzzy = `first_valid`（跳过无效项继续往后找）
- empirical = `first_only`（首项无效 ⇒ 整体放弃）

强行统一会让经验推理在「首项无效、次项有效」时**凭空多出推荐** ⇒ 行为变更。
⇒ 真相源统一的是**实现**，不是**语义**；语义差异**显式化为两个策略类**。

**③ 为什么 `selections` 是第三个容器，不塞进 `field_reports` / `diagnostics`**
那两个是**规则级**诊断（哪条规则被跳过、哪个字段降级）；缺陷选取是**决策级**
（本轮处理哪个缺陷）⇒ 性质不同，分开更清楚。
`Diagnostic.is_empty()` 已纳入 `selections` ⇒ 有选取就有诊断快照；
而黄金快照只记 `_diagnostics` ⇒ **快照零差异**。

### 16.5 验收

| 项 | 结果 |
|---|---|
| `pytest process/algorithms/fuzzy tests -q` | **49 passed** |
| 黄金快照对拍（`_golden_ABC.json`） | 逐条差异 **0** |
| `_scen13_check.py` / `_verify_e2e_db.py` / `_verify_e2_offline.py` / `_verify_edge_boundaries.py` | 全部 EXIT=0 |
| `_verify_diag_isolation.py` | ALL PASS |
| `_verify_defect_selection.py`（**本批新增**） | **ALL PASS** |

新增验收脚本 `_dev_refs/_verify_defect_selection.py` 覆盖 6 组性质：

1. **零行为变更** —— 与**旧实现逐字复刻**对拍（6 个用例 × 2 个引擎 = 12 条断言）
2. 两个引擎的语义差异**被保留**
3. 留痕能回答「选了谁 / 跳过了谁 / **为什么**」
4. 策略接口可替换（**调用点不变**）
5. empirical 行为等价 + 正常路径**零日志噪音**
6. 边界：空 / 脏输入不炸

### 16.6 覆盖边界与遗留（如实说明）

- 业务优先级规则**未实现**（等口径）⇒ 机制已就位，接上只需新增一个策略类，**不改调用点**
- 留痕出口：fuzzy 在 per-request 容器；empirical 在结构化日志（该引擎无 per-request 容器）
- empirical 的 `is_available` **不留痕** —— chain 调度频繁调用，每次都打日志是噪音
- 留痕**不进对外契约**（与批 F 一致）
- 本批**未改变任何推荐结果**（逐条对拍等价）

### 16.7 本批**不做**（明确边界）

| 项 | 理由 |
|---|---|
| 业务优先级规则本身 | 等业务口径（D7） |
| 多缺陷合并 / 并行处理 | 用户明确「不是合并逻辑」 |
| 留痕进 HTTP 响应 | 不动对外契约 |
| 把两个引擎的策略统一 | 会改变经验推理的历史行为 |
| 把选取记录塞进 `field_reports` | 决策级 ≠ 规则级，性质不同 |

---

## 17. 批 H：fuzzy 包缺口修复（④代数式 / ⑧静默吞异常 / ⑥反模糊化 / ②契约校验）

### 17.1 本批范围

用户授权的四项（**先查生产数据再动手**）：

| 编号 | 项 | 性质 | 结果 |
|---|---|---|---|
| ④ | 代数式结论分支是死代码且实现错误 | 零行为变更 | 已修 |
| ⑧ | `library/keywords.py` 静默吞异常 | 零行为变更 | 已修 |
| ⑥ | 反模糊化只实现 `centroid` | 零行为变更（默认不变） | 已补齐 |
| ② | `OptimizeDataValidator` 从未接线 | **会拦入参** | 已接线 |

### 17.2 ④ 代数式结论（`X=a*Y+b*Z`）

**真相**：那个分支**永远执行不到**。

- `parsing.split_phase` 对含 `=` 的结论返回 `{'name': X, 'kind': 'algebra'}`（**无 action**）
- `rules_filter._conclusion_kind`：`action` 为 None ⇒ 判为 **advisory** ⇒ **不会建 `NumTskRule`**
- ⇒ `NumTskRule._build_conclusions` 里的 algebra 分支是死代码
- 且它是 `np.zeros(...)` **恒零向量** ⇒ 即便执行也只会算出 0

**改法**：内核删除该死分支（连带删掉 `numpy` 依赖）；改在 **filter 层显式跳过并留痕**
（`rules_filter.build_rule_objects` 判定 0）⇒ 从「默默进 Mamdani 当空规则」变成
「明确跳过 + `skipped` 有记录」。

> 实测：当前规则库 algebra 结论 **0 条** ⇒ 线上零影响。

### 17.3 ⑧ `library/keywords.py` 静默吞异常

**真相（比「静默」更严重）**：一条 `range_min/range_max` 缺失/非数值的 keyword ⇒
`float(None)` 抛 TypeError ⇒ **整个 `get_keywords_by_names` 失败** ⇒ engine 兜底 ⇒
**全部字段**退化为「推测论域」（门控位置靠猜）⇒ **一条脏数据拖垮整批元数据**。

**改法**：

1. `_derive_step()` 单独抽出 —— 跨度算不出来（缺失/非数值/倒挂）**记 warning** 再退回 1.0，
   不留裸 `except`（与 `nets.py`「禁止静默降级」同一原则）
2. `_orm_to_profile` / `_dict_to_profile`：**论域不可用 ⇒ 返回 None**
3. `to_keyword_profiles`：**跳过坏的、保住好的**（不再整批崩）

> 实测：当前库 `range_min/range_max` 100% 非空（311 条），倒挂 2 条（`IL`/`VPTM`），
> 且这 2 个码**不在规则库用到的 49 个参数码里** ⇒ 线上零影响。

### 17.4 ⑥ 反模糊化补齐

`centroid` / `bisector` / `mom` / `som` / `lom` **五法齐备**。

- `centroid` **原样不动**（生产路径）
- `bisector`：梯形积分累计到面积一半的 x（自实现积分，不依赖 `np.trapz` 版本差异）
- `mom` / `som` / `lom`：取达到最大隶属度的采样点（均值 / 首 / 末）
- 非法 mode ⇒ 抛 `UnsupportedDefuzzMode`（**同时继承 `NotImplementedError` 与
  `ValueError`** ⇒ 历史 catch 与新 catch 都能兜住）
- ⚠️ **默认仍是 `centroid`**，`nets.py` 也显式传 `'centroid'` ⇒ **零行为变更**；
  「用哪个」留给工艺定

### 17.5 ② 契约校验接线（**唯一改输出的**）

**先查生产数据**（临时脚本，跑完即删）：

| 事实 | 值 |
|---|---|
| `InjectionMoldingMachine` 总数 | 3 |
| `drive_system` 缺失 | **0 / 3**（'全液压驱动' 2 · '全电动驱动' 1） |
| `ProcessCondition` 总数 | 44 |
| 其中 `injection_machine` 为空 | **0** |
| `injection_index` 超出 units 范围 | **0** |
| **可过校验（三个条件全满足）** | **44 / 44** |

⇒ **接线不会拦死任何线上机台 / 工艺条件**。

**改法**（service 层，`process/services/parameter_optimize.py`）：

- 新增模块级 `_validate_optimize_inputs()`（与 `_validate_feedback` 同层，两个入口共用）
- 调 `OptimizeDataValidator.validate()` ⇒ 捕 `ValueError` ⇒ 转
  `BizException(ERROR_REQUIRED_FIELD)`（400）
- ⚠️ **算法层不 import 业务异常**（fuzzy 包零业务耦合），错误码与文案由 service 定
- 接线点：`infer()`（`_assemble_context` 之后）与 `infer_from_provided()`（`_infer_kernel` 之前）

**当前实际拦截面**：三份字段字典里只有 `machine_info.drive_system` 标「必填」，
其余全是「可选 / 推荐」⇒ 本校验目前**只拦「机台没填驱动方式」**这一件事。

### 17.6 验收

| 项 | 结果 |
|---|---|
| `pytest process/algorithms/fuzzy tests -q` | **49 passed** |
| 黄金快照对拍（`_golden_ABC.json`） | 逐条差异 **0**，PASS |
| `_verify_kw_parity.py` | PASS（⑧ 论域对拍） |
| `_verify_zero_dep.py` | PASS（④ 删 numpy 后零依赖仍成立） |
| `_verify_field_names_forward_parity.py` | EXIT=0 |
| `_verify_defect_selection.py` | ALL PASS |
| `_verify_diag_isolation.py` | ALL PASS |
| `_scen13_check.py` | 14/14 通过 |
| `_verify_e2e_db.py` | 端到端复验完成 |
| `_verify_e2_offline.py` | 全部通过 |
| `_verify_edge_boundaries.py` | 全部通过 |
| `tests/verify_provided_smoke.py` | PASSED（② 直接相关） |
| `tests/test_optimize_smoke.py` | PASSED（含 6 条 `OptimizeDataValidator` 断言） |

**未新写测试脚本**（沿用现成验收手段）。

### 17.7 「设备参数 → 论域」的口径缺口（如实记录，待业务定）

用户口径：「**从设备读取参数主要是为了用实际值补全参数的论域**」。

**与现状的差距**（实测）：

| 事实 | 现状 |
|---|---|
| 判级论域来源 | **只**来自 `RuleKeyword.range_min/range_max`（311 条，100% 非空，覆盖规则库 49 码中的 47 码） |
| 设备参数参与判级？ | **否** —— 设备参数目前**只**用于裁剪推荐值（批 D 落的「物理天花板」） |
| 设备参数填充率 | `max_set_*` 九个字段 **仅 1/4 InjectionUnit 有值（25%）** |
| `fuzzy_level` 档位 | 310/311 都是 **5 档**（1 条 3 档）⇒ 引擎推测论域硬编码 `lvl=3` 会**错 2 档** |

⇒ 要把「设备实际值补全论域」落地，还差三个口径：
1. **叠加还是替换**？设备值与 `RuleKeyword` 域取交集 / 设备覆盖 / 仅在 RuleKeyword 缺失时兜底？
2. **填充率不足怎么办**？75% 的 unit 没有 `max_set_*` ⇒ 是降级为 RuleKeyword 域，还是拒？
3. **哪些字段该必填**？若设备值要参与论域，则「论域必需」的字段才该标「必填」，
   而不是现在的 `drive_system`。

> 本批**未动**这块（属口径决策，不在授权范围）。
>
> ✅ **后续**：用户已给出口径（见 §18），本文档 §17.7 的口径缺口**已关闭**。
> ⚠️ 其中「填充率 25%」是**分母错误**（按 4 个 InjectionUnit 统计）⇒ 按 44 个
> ProcessCondition 统计实际是 **42/44 = 95%**（详见 §18.5）。

---

## 18. 批 I：设备实际值 → 判级论域（契约层 + 引擎层）

### 18.1 用户口径（本批的授权依据）

| # | 原话 | 落地含义 |
|---|---|---|
| 1 | 「从设备读取参数主要是为了**用实际值补全参数的论域**」 | 设备值参与**判级论域**，不只是裁剪推荐值 |
| 2 | 「**必须用设备值，设备值没有就报错**」 | 缺失设备值 ⇒ 400，不是降级 |
| 3 | 「根据**关键字的模糊等级**决定用几档」 | 档位数 = `RuleKeyword.fuzzy_level`（权威）= 5；推测路径按主流档位 |
| 4 | 「**我们定义必填的字段，必须校验并且替换，其余字段的论域可以用默认值**」 | 必填等级字段：**校验 + 替换论域上界**；其余字段：论域不动 |
| 5 | 「`drive_system` 反而**不是必填**」 | `drive_system` 降为「可选」 |

⇒ 第 4 条是最终口径，把第 1~3 条收敛成一条可执行规则：
**必填等级字段（`必填` / `液压机必填`）⇒ 缺失报错 + 论域上界替换成设备实测值；
其余字段（`可选` / `推荐`）⇒ 论域保持 RuleKeyword 默认域。**

### 18.2 契约层改动（`process/algorithms/fuzzy/specs.py`）

| 改动 | 内容 |
|---|---|
| `drive_system` | `必填` → **`可选`**（不参与论域也不参与裁剪，只用于判定「液压机必填」等级） |
| 5 个设备上限 | `可选` → **`必填`**（IP / IV / PP / PV / MSR） |
| 2 个计量类设备上限 | `可选` → **`液压机必填`**（MP / MBP：全电机 HMI 物理上无此栏） |
| 2 个泄压类设备上限 | 保持 `可选`（无对应规则参数族 ⇒ 不参与论域） |
| 新增 `is_required_limit_field(field)` | 读字段字典的 `condition` 判断是否必填等级（**单一真相源**，不另抄名单） |
| 新增 `resolve_domain_limits(machine_info)` | 只取**必填等级**字段的设备上限 ⇒ 判级论域用 |
| 保留 `resolve_param_limits(machine_info)` | 取全部 `PARAM_LIMIT_FIELDS` ⇒ 推荐值裁剪用（两者语义分开） |

⚠️ `specs.py` 文件头原有的「2026-10-27 修正」段（把 `max_set_*` 定位成“只是天花板、
标可选、不拦请求”）与 TODO 第 2 条（“**不做**用机台上界做论域”）**已被用户口径推翻**，
本批一并改写，避免文档与代码自相矛盾。

### 18.3 引擎层改动（`process/algorithms/fuzzy/engine.py`）

| 位置 | 改动 |
|---|---|
| `_recommend` | 由 `context['machine_info']` 算 `domain_limits = resolve_domain_limits(...)`，传入两个推理层 |
| `_load_keyword_profiles` | 新增 `domain_limits` 参数；对权威 profile 调 `_apply_device_bound` |
| `_apply_device_bound`（新增） | 论域**上界** = 设备实测值；`step` 按跨度**等比缩放**（保持档位粒度比例不变）；设备值 ≤ 经验下界 ⇒ 记 warning 并保留经验域 |
| 推测论域 | `lvl` 由硬编码 `3` → **`5`**（规则库实测 310/311 条 `fuzzy_level = 5`）；上界优先用设备实测值，否则仍是「当前值 × 2」；`step` 改为随论域跨度（`span/3`），不再随当前值 |
| `_infer_numeric_layer` / `_infer_advisory_layer` / `_build_field_context` | 逐层透传 `domain_limits` |

⚠️ **只换上界，不换下界**：下界仍取 `RuleKeyword.range_min`（经验域下界）。

### 18.4 换算结果（实测：机台 machine=10 / unit=1）

| 前缀 | 经验域 | 设备实测 | 换算后论域 | 方向 | 档位 |
|---|---|---|---|---|---|
| IP | [0, 200] | 100 | [0, 100] | 收窄 | 5 |
| IV | [0, 120] | 80 | [0, 80] | 收窄 | 5 |
| PP | [0, 140] | 100 | [0, 100] | 收窄 | 5 |
| PV | [0, 100] | 80 | [0, 80] | 收窄 | 5 |
| MP | [0, 200] | 100 | [0, 100] | 收窄 | 5 |
| **MBP** | **[10, 50]** | **100** | **[10, 100]** | **变宽** | 5 |
| MSR | [0, 200] | 200 | [0, 200] | 不变 | 5 |

⚠️ **MBP（计量背压）是唯一变宽的一项**：设备能做到 100 而经验域只到 50 ⇒ 换算后
50~100 这段从“永远最高档”变成“中间档”。语义上成立（这台机的真实能力到 100），
但它是本批唯一一处「设备能力 > 经验共识」的字段，**值得业务再确认一次**。

### 18.5 段间差异安全性（换算会不会抹平段间差异？）

设备上限是**前缀级**（一个 `InjectionUnit` 一个上限），而参数码是**段级**（IP0/IP1…）
⇒ 换算若用前缀值，会不会把 IP0/IP1 的差异抹平？**实测：不会。**

| 前缀 | 各段经验上界 | 段间是否一致 | 换算后 |
|---|---|---|---|
| IP | IP0~IP5 全 [0,200] | **一致** | 无损 |
| IV | IV0~IV5 全 [0,120] | **一致** | 无损 |
| PP | PP0~PP4 全 [0,140] | **一致** | 无损 |
| PV | PV0~PV4 全 [0,100] | **一致** | 无损 |
| MP | MP0~MP3 全 [0,200] | **一致** | 无损 |
| MBP | MBP0~MBP3 全 [10,50] | **一致** | 无损 |
| MSR | MSR0~MSR3 全 [0,200] | **一致** | 无损 |
| **PT** | PT0[0,10] PT1[0,8] PT2[0,6] PT3[0,5] PT4[0,5] | **不一致** | **不参与换算**（PT 无设备上限字段 ⇒ 非必填 ⇒ 按口径用默认值） |

⇒ 规则库给同一前缀的所有段**经验上界本来就一致**；唯一段间不一致的 PT 恰好
**不在必填之列** ⇒ 换算无损。

### 18.6 线上影响面（实测）

| 项 | 数据 |
|---|---|
| `max_set_*` 填充率（按 44 个 ProcessCondition 统计） | **42/44 = 95%**（⚠️ §17.7 写的 25% 是分母错误，按 4 个 InjectionUnit 统计所致） |
| 会被新契约拦下的 condition | **2/44**：`condition=10`（机台 12 / unit=3，全空）、`condition=41`（机台 11 / unit=2，全空） |
| `condition=41` 是全电机 | 计量类（MP/MBP）按「液压机必填」豁免，但 IP/IV/PP/PV/MSR 仍缺 ⇒ 仍报错（符合“设备值没有就报错”） |
| `drive_system` 缺失的影响 | 缺失 ⇒ 按「非液压机」处理 ⇒ 计量类字段一律**不要求**（宽松放过，不误伤液压机） |
| 前端/调用方 | `infer` 链路（FromCondition）的 `machine_info` 由 `_extract_machine_info` 跨表合并 ⇒ 自动含设备字段；`infer_from_provided` **无生产调用方**（仅测试） |

### 18.7 验收（全部现成手段；未新增测试用例）

| 项 | 结果 |
|---|---|
| `pytest process/algorithms/fuzzy tests -q` | **49 passed** |
| 黄金快照对拍（`_golden_ABC.json`，快照脚本不传 machine_info ⇒ 零行为变更） | 逐条差异 **0**，PASS |
| `_verify_kw_parity.py` | PASS |
| `_verify_zero_dep.py` | PASS（零依赖不变量成立） |
| `_verify_field_names_forward_parity.py` | EXIT=0 |
| `_verify_defect_selection.py` / `_verify_diag_isolation.py` | ALL PASS / ALL PASS |
| `_scen13_check.py` | 14/14 |
| `_verify_e2e_db.py` / `_verify_e2_offline.py` / `_verify_edge_boundaries.py` | 完成 / 全过 / 全过 |
| `tests/verify_provided_smoke.py` / `tests/test_optimize_smoke.py` | PASSED / PASSED |
| compileall | exit=0 |
| 一次性验证（论域替换，跑完即删） | **ALL PASS**：IP0[0,100] / IV0[0,80] / MBP0[10,100] / MSR0[0,200]；PT0[0,10] / BT1[150,350] / IL0[0,150] 保持默认域；lvl 全 5；无设备值时全保持经验域 |

⚠️ **改了既有断言**（口径反转，不是新增用例）：`tests/test_optimize_smoke.py` 的
5a/5b 原先断言「缺设备上限**不拒**」⇒ 新口径下必拒 ⇒ 改为断言抛 `ValueError`；
5c（全电机缺计量压力不拒）仍然成立，语义从“上限一律不拦”变为“液压机必填 ⇒ 非液压机豁免”。
`tests/test_fuzzy_field_report.py` 的 monkeypatch 替身 `_fake_load` 补了
`domain_limits=None` 形参（签名跟随实现）。

### 18.8 未决项

1. ~~**MBP 变宽 + 疑似脏数据**~~ —— **已关闭**（用户口径 2026-10-27）：
   > 「脏数据也没关系，我们现阶段要的是逻辑正确」

   ⇒ 算法层**不做任何数值合理性判断**：设备值**无条件**作为论域上界使用，
   不因「物理上说不通」回退经验域、不做区间截断。引擎只在「设备上限 > 经验域上界」
   时打一条 warning 留痕（`engine._apply_device_bound`），文案只提「录入值」、
   **不提单位**（见 2）。
   ⚠️ 因此 §18.4 里 MBP0 从 [10,50] 变宽为 [10,100] 是**预期结果**、不是 bug；
   数据侧后续修正 `max_set_metering_back_pressure` 录入值后，论域会随设备值
   自动收窄（无需改代码）。
2. ~~**单位口径待确认**~~ —— **已关闭**（用户口径 2026-10-27）：
   > 「我们取的就是界面值，不需要关心单位，当然我们也有单位，但是并不需要在算法这里考虑」

   ⇒ **算法层不涉及单位**：不换算、不校验单位一致性、字段描述里也不声明单位。
   核查结论：fuzzy 算法包内**零换算代码** —— `process/services/parameter_transplant.py`
   的 `_convert_*` 是螺杆直径比换算、`expert/algorithm_engine.py` 的「60 = s→min」
   是转速换算，**均与 `max_set_*` 无关**；`_extract_machine_info` 直取 ORM 值。

   已同步的描述层：
   - `specs.py` 的 9 条 `max_set_*` desc：`[MPa]/[mm/s]/[rpm]` → 「（HMI 界面值）」；
   - `process/schemas/optimization.py` 的 9 条 Field description：同上。
   - 单位声明**只留在 ORM 层**（`masterdata/models/injection.py` 的 `verbose_name`）
     —— 那是数据层的事实；算法契约层重复声明 = 替数据层担保，而算法并不保证这一点。

   ⇒ 原先提的「若录成 bar 会偏大 10 倍」**不再是算法层待办**：算法拿到什么值就
   用什么值（录入规范归数据侧）。
3. **初始化链路未接校验器**：`process/services/parameter_initialize.py:627` 的
   `infer_from_provided`（工艺参数初始化，view `processes.py:575` 暴露）收同一套三维入参，
   但**未接** `OptimizeDataValidator` ⇒ 与调优链路口径不一致（见执行文档 L32/L34）。
   ⚠️ 该链路的 `MachineInfoSchema` 字段命名与调优链路**不一致**
   （`max_set_injection_velocity` vs `max_set_injection_speed`、
   `max_set_holding_velocity` vs `max_set_holding_speed`，且**无**计量背压与泄压两项）⇒
   即使接线，字段名也得先对齐。**接线前必须先查该链路的前端传参是否含设备上限字段**。

---

## 19. 批 J：契约层收口 + 内核副作用修复（2026-10-27）

> 起因：用户梳理 fuzzy 算法五层流程（specs 契约 → engine 编排 → library 来源 →
> fuzzy_core 内核 → recommendations 输出）后，要求检查「遗漏或 bug」。
> 本节记录据此产生的 4 批改造与验收证据。

### 19.1 层次归属的三处偏差（**描述修正，非代码改动**）

用户口述的流程与代码实际对照：

| 用户描述 | 代码实际 | 性质 |
|---|---|---|
| fuzzy_core「自动识别缺陷类型」 | 在 **engine 编排层**，且模块在 **fuzzy 包外**（`process/algorithms/defect_selection.py`，fuzzy + empirical 共用） | 跨算法公共机制，不是 fuzzy 的一层 |
| fuzzy_core「筛选关键字和规则」 | **适用性筛选在 library**；`fuzzy_core/rules_filter` 做的是**分类与建对象** | 内核自有五层 docstring 是对的，两套口径需在文档里区分 |
| fuzzy_core「将实际参数替换关键字参数论域」 | 在 **engine.py**（`_apply_device_bound`），内核只收已构造好的 `KeywordProfile` | 这个分层**是对的**（内核不碰业务数据），描述要改 |

### 19.2 批 J-1：内核不改调用方入参

**问题**：`fuzzy_core/models/nets.py` 的 `FuzzyRuleNet.inference` 有
`if x.get('MT') is None: x['MT'] = 0` —— **就地修改入参字典**。
提示层 `engine._infer_advisory_layer` 传的是 `process_parameter` **原对象**
⇒ 引擎的原始参数被写脏（数值层传的是副本，**两层口径不一致**）。

**改法**：
- `nets.py`：`x = {**x}` 先复制再补默认值；
- `engine.py`：`net.predict(dict(process_parameter), ...)` 传副本。

**行为等价**：对调用方而言推理结果完全不变，只是不再写回原字典
（对拍实测：inference 后入参未出现 `MT`）。

⚠️ **本行不删**：MT 的语义（见 19.7）待业务确认，删它属于业务决策而非顺手清理。

### 19.3 批 J-2：结论形态判定下沉到 `fuzzy_core/parsing.py`

**问题**：§4.1 记的双判定 —— `library/rules.py::classify_conclusion_kind`
（输入=规则串）与 `fuzzy_core/rules_filter.py::_conclusion_kind`
（输入=已拆解的 solutions）**各写一份**，而 `RuleProfile.conclusion_kind`
算完就扔（生产路径**只写不读**）。

**改法**：判定下沉到 `fuzzy_core/parsing.py::classify_conclusion_kind(solutions)`
（与 `is_numeric_value` 并列 —— 该文件 docstring 本就点名要求这两处共用同一份判定），
两个调用点都调它；`rules_filter._conclusion_kind` 删除。

**为什么不改用 `profile.conclusion_kind`**（§4.1 的第一个修法）：
1. 判定 2（数值类规则的**所有**结论值是否都是数字）需要逐条 solutions，
   整条级字段代替不了；
2. `RuleProfile.conclusion_kind` 默认值是 `'numeric'` ⇒ 漏填/伪造的 profile
   会被默认判成 numeric ⇒ 脏规则直接进数值层
   （正是 `parsing.is_numeric_value` docstring 警告的「一条脏规则拖垮整层」）；
3. 会让内核依赖上游字段，破坏「内核自带判定」的独立性。

**等价性**：全量 **1643 条**活跃规则逐条对拍，判定分叉 **0**。

### 19.4 批 J-3：内核契约校验接线（§4.4 关闭）

**改法**：`fuzzy_core/profiles.py` 新增**单条**校验
（`keyword_profile_issues` / `rule_profile_issues`，返回问题清单、不抛），
整批版 `validate_*_profiles` 复用它们（错误文案**逐字不变**）；
`library/repository.py` 的两个出库点（`get_rules` / `get_keywords_by_names`）
**逐条校验、跳过坏的、留 `logger.warning`**。

**为什么是「逐条跳过」而不是整批 raise**：`engine.recommend()` 的 try/except
会把任何异常吞成**空推荐** ⇒ 整批 raise 会让「一条脏档案」放大成
「整次调优无结果」。逐条跳过 = 一条脏档案只废掉自己。

**遗留**：`validate_rule_profiles` 只查 `conclusion_kind` **取值合法**，
不查它**语义正确** ⇒ 算错的 `conclusion_kind` 仍能过。
（当前无生产影响：内核分流不读该字段，见 19.3。）

### 19.5 批 J-4：缺陷反馈进契约层

**问题**：缺陷反馈的校验是 `process/services/parameter_optimize.py::_validate_feedback`
里的一条**手写 if 链**，游离在契约层之外 —— 而它是算法对外接口的一环
（用户口径：「缺陷反馈也是其中重要一环，即使是一个 dict，那也应该考虑一下，
需要对入参进行校验」）。

**改法**：
1. `process/algorithms/field_contract.py` 扩两个**通用**能力：
   - spec 可选键 `missing_desc` —— 自定义缺失描述（拼在维度名之后）；
   - spec 可选键 `value_validator` —— 取值合法性校验器
     `(value, info_dict) -> Optional[str]`，**与必填性独立**（可选字段填了也要合法）；
2. `fuzzy/specs.py` 新增 `OPTIMIZE_FEEDBACK_FIELDS`（5 字段）+
   `audit_feedback_defects(defects)` 审计入口 +
   `DEFECTFREE_KEYWORD_NAME`（sentinel 名收归契约层，service 本地常量已删）；
   - `level` / `position` 标「条件必填」，条件用
     `condition_when: {'keyword_name__nin': ['DEFECTFREE']}`
     —— `eval_condition_when` 本就支持 `__nin`，且**只在同一 info_dict 内求值**
     ⇒ 列表项天然成立；
   - `level` 的取值合法性用 `value_validator` 钩子（词表仍是
     `VALID_DEFECT_LEVEL_WORDS_TEXT` 单一真相源）；
3. `parameter_optimize.py::_validate_feedback` 手写 if 链删除，
   改为 `audit_feedback_defects(...)` + 转 `BizException`。

**对外文案逐字不变**：12 组输入对拍（空/非列表/非对象/缺 level/缺 position/
level 非法/合法/DEFECTFREE 免校验/多项列表等）**全部一致**。

⚠️ **一处行为变更**：`keyword_name` 的判空口径由 `is None` 变为
「空值即缺失」（`''` 也报错）—— 空串的 keyword_name 同样查不到规则，属口径收紧。
该判空口径已在 `field_contract` 的 docstring 注明。

### 19.6 本批验收

| 项 | 结果 |
|---|---|
| `pytest process/algorithms/fuzzy tests -q` | **49 passed** |
| 黄金快照对拍（`_golden_ABC.json`） | 逐条差异 **0** |
| `_verify_kw_parity.py` / `_verify_zero_dep.py` | PASS / PASS |
| `tests/verify_provided_smoke.py` / `tests/test_optimize_smoke.py` | PASSED / PASSED |
| `compileall`（fuzzy + field_contract + parameter_optimize） | exit 0 |
| 一次性对拍脚本（批 J-1~J-4） | FAILED_COUNT=**0**（用完即删） |

### 19.7 原未决项的定性结论（2026-10-28 核实：**规则问题，算法侧不改**）

**口径澄清（用户）**：算法中的模温是 **`MT`**，不是 `MD` ⇒ `specs.py` 注释里的
`MD` 是笔误，已改（见 19.8）。算法侧的权威名以 `RuleKeyword` 为准。

**核实方法**：一次性脚本（跑完即删）按两个条件逐条判定全部 1643 条活跃规则：
1. **是否作门控** —— 前件 level 必须是可判级词（`is_level_word` 为真）。
   `IPOS_worse` / `CUSION_worse` / `DDAM_worse` / `NT_worse` / `CLAMP_worse` /
   `ET_worse` 这类**不可判级**前件本就不作门控，规则**不因此而死**；
2. **算法侧能否取值** —— `field_names.to_business_name(name)` 是否命中
   `ProcessParameter` 的**实际字段**（分段参数还要检查段号是否越界）。

**结果**：1643 条活跃规则中 **170 条含死门控**（恒不命中）：

| 门控维度 | 死规则数 | 性质 |
|---|---|---|
| `BT`（整体料筒温度） | **167** | **规则问题**：`BT` 是**已退役**的算法名（业务侧只有分段 `brl_temp_1..9` ⇒ `BT1..BT9`），`to_business_name('BT')` 返回 None |
| `MT`（模温） | **3** | **规则问题**：`ProcessParameter` **没有模温列**（只有 `noz_temp` / `brl_temp_1..9`）⇒ 算法侧无输入源 |

⇒ **定性：170 条死规则全部是「规则库引用了业务侧不存在的字段」**。
按用户口径「如果是规则的问题那就不是问题，更新规则即可；算法的问题才需要考虑」
⇒ **算法侧本轮不动**（除注释纠错）。

⚠️ **本节数字已被运行时实测修正**（见 §19.10）：原先记的「190 条」里，
`DLUNDERSIZE1/2` / `DLOVERSIZE1/2` 那 20 条**并非死规则** ——
`DL` 前缀会被 `parsing.is_position_name` 识别为**缺陷位置名** ⇒ 走缺陷通道 ⇒
实测端到端**能产出正常推荐**。

⚠️ **修规则时的连带约束（BT / MT 通用）**：前件与结论**必须成对改**。
`to_business_name('BT')` / `to_business_name('MT')` 都返回 None ⇒ 结论
`BT_add_2` / `MT_add_5` 即使命中，推荐值也**写不回 baseline**
（`parameter_optimize` 按业务字段名回写）⇒ 把 `BT` 改成 `BT1..BT9` 时，
结论也要落到具体段号。

⚠️ **风险仍在（与「改名」同源）**：167 条 `BT` 规则一旦从 `BT` 改成 `BT1..BT9`，
会**突然全部生效**（此前恒不命中）⇒ 必须在同一批次里补可见化
（warning / 诊断清单），否则会出现「无人预期的推荐突现」。

### 19.8 本轮改动与验收

| 文件 | 改动 |
|---|---|
| `fuzzy/specs.py` | 注释「模温 **MD**」→「模温 **MT**」（L517 / L530），**无逻辑变化** |
| `tests/test_fuzzy_machine_limits.py` | 「整段参数」反例 `'MD'` → `'MT'`（`lookup_param_limit('MT', limits)` 仍为 `None`，断言语义不变） |

| 验收项 | 结果 |
|---|---|
| `pytest process/algorithms/fuzzy tests -q` | **49 passed** |
| 黄金快照对拍（`_golden_ABC.json`） | 逐条差异 **0**，PASS |
| `compileall`（specs.py + test_fuzzy_machine_limits.py） | exit 0 |
| 死规则面统计（一次性脚本，用完即删） | 190 条 / 1643 条，分布已入 19.7 |

### 19.9 规则修正底稿（2026-10-28，用户口径：**规则的问题就改规则**）

**用户口径**：算法依赖规则；规则错误时算法应按规则输出（哪怕输出是错的），
这本身是合理的 ⇒ **算法侧不因规则错误而担责**。

⚠️ **一处精确化**：当前算法对「引用了无值维度的规则」的处理是**保守丢弃**
（`membership` 保持 0.01 ⇒ 激活度低于 `MIN_ACTIVATION_THRESHOLD` ⇒ 规则不触发、
无输出），而不是「按规则输出一个错误结果」—— 算法手里没有该维度的值，
无法判定其档位。这是**保守且自洽**的行为（不编造激活度），
与「不可判级前件（`worse`）不作门控」是两条不同路径。

⚠️ **但对「按规则输出错误结果」这条诉求，改算法也没有可见收益**（下表 §19.9-2）：
190 条死规则里有 **170 条的结论参数同样在业务侧无字段** ⇒ 即便门控放开、规则命中、
推荐值算出来，**回写时也无处落地**（`parameter_optimize` 按业务字段名回写）
⇒ 用户界面仍然看不到任何东西。

#### 19.9-1 三组死规则的修正底稿（只读核查，**未改任何数据**）

| 组 | 条数 | 修法 | 需业务拍板 |
|---|---|---|---|
| **A. `defect_position` 组**<br>（`DLUNDERSIZE1/2`、`DLOVERSIZE1/2`） | **20** | ⚠️ **实测修正（§19.10）**：这 20 条**本来就正常工作并产出可见推荐**（`DL` 前缀走缺陷通道）⇒ **不需要改**。真正的问题是**位置条件无效**：`position` 不匹配时不是「排除规则」，而是「该维度不建论域 ⇒ 前件不作门控 ⇒ 规则照样命中」⇒ 规则作者写的 `AND DLUNDERSIZE1_high`（意图「**且**缺陷在位置1」）在算法里**表达不出来** | **是**：要么去掉位置条件（承认它无效），要么算法侧补「位置标识匹配」语义（让位置不匹配时真正排除） |
| **B. `BT` 组**<br>（族级料筒温度） | **167** | 前件+结论**成对**改到分段：`BT_low`→`BT1_low`…，`BT_add_2`→`BT1_add_2` | **是**：<br>① 一条族级规则要落成 9 条（167×9=1503），还是只选某几段？<br>② 论域量纲要换：`BT` 是 [0,50]（实为 step 值域）⇒ `BT1..BT9` 是 [150,350] 真实温度域，结论值 `2 / 3.0 / 3.8` 的业务含义要重新确认 |
| **C. `MT` 组**（模温） | **3** | 前件（`MT_low` 无值）与结论（`MT_add_5`）**两头都落不了地**（业务侧没有模温这个工艺参数）⇒ 只能停用 | **是**：停用，还是业务侧新增「模温设定值」字段（那需要加字段 + 算法补 `field_names` 映射 + 规则改写，是另一件事） |

#### 19.9-2 数值结论无处落地（194 条）

`BT` 167 + `CUSION` 23 + `DVAM` 1 + `MT` 3。其中：

- **170 条**（`BT` + `MT`）同时是死门控 ⇒ **自闭环**：前件与结论是同一个
  无业务列的参数 ⇒ 无论算法怎么跑，用户都看不到输出；
- **24 条**（`CUSION` 23 + `DVAM` 1）是**「跑得出来、落不了地」**：
  前件是 `X_worse`（不可判级 ⇒ 不作门控）⇒ **规则能命中**，
  但结论是数值型 `add/reduce`，目标参数在业务侧无字段 ⇒ 推荐值算出来即被丢弃。

#### 19.9-3 顺带发现的规则库数据质量（属改规则范畴）

1. **57 条规则有重复前件**，全部是 `IV0` 连写两次（复制粘贴残留）：
   `IF GASVEINS_low AND IV0_high AND IV0_high AND ...` ⇒ 改规则时顺手清。
2. `DLUNDERSIZE*` / `DLOVERSIZE*` 的 `RuleKeyword` 元数据自相矛盾：
   `range [0,1]` 却 `unit='mm'`。

⚠️ **与 19.7 的表述修正**：上轮说「改规则会突然全部生效」——
更准确的说法是：**只有「前件 + 结论」都改到真实存在的业务参数上，规则才会既生效又可见**；
只去掉前件（让门控失效）会让规则命中，但推荐值仍写不回 baseline ⇒ 对用户依旧不可见。

#### 19.9-4 用户确认（2026-10-28）：**静默丢弃是正常逻辑，算法侧不动**

**结论**：算法侧发现「门控维度取不到值」的规则并静默丢弃，**是正常且正确的设计**，
算法侧**不做任何改动**。

**机制（精确版）**：算法侧**没有**「判断规则有没有用」的能力，只有一个机制——
**数据不足 ⇒ 不激活**。两条路径要分清：

| 路径 | 触发条件 | 是否有记录 |
|---|---|---|
| filter 层跳过（`rules_filter.py`） | 条件本身不成立（`worse` 不可判级、词表不匹配） | **有**（`filtered.skipped` 明细） |
| 推理层阈值滤除（`too_weak`） | 门控维度**档案在**（进了 `pre_dict`）但**输入里没值** ⇒ membership 兜底 `EPSILON` ⇒ 激活度 ≈ 1e-7 ⇒ 低于 `MIN_ACTIVATION_THRESHOLD`(0.01001) | **无**（诊断只写不读，§4.5；内核侧只有 `logger.debug`） |

⚠️ **分界线是「档案是否进了 net」，不是「有没有值」**（§19.10 实测）：
档案**不在** `pre_dict` ⇒ 该前件**不作门控**（规则仍可命中）；
档案**在** `pre_dict` 但输入里没值 ⇒ 整条规则被丢。

`MT` 3 条 + `BT` 167 条走**第二条**（结论是 `add/reduce` 数值型 ⇒ 数值层）。

**为什么丢弃比输出更正确**：算法手里没有该维度的值，要「按规则输出」就必须**编一个档位**
（硬置 membership=1.0）⇒ 规则被放行 ⇒ 产出看似合理的推荐 ⇒ 用户会采纳 ⇒ **有害**。
用户口径「规则错了也该按规则输出错误结果」的前提是**规则本身可执行**（前件有值 + 结论能落地）；
而 `MT`/`BT` 两头都不可执行 ⇒ 输出的是「空气」⇒ 不如不输出。

**唯一可讨论点是「丢得静不静」**（可观测性，§4.5），不是正确性问题；且对这 170 条，
即使加可见化也只是让人知道「这些规则没跑」，界面依旧无输出 ⇒ 真实价值是
**帮业务定位该改哪条规则**，服务于「后续修正规则」。

⚠️ **小瑕疵（本轮不动）**：两层兜底值不一致 —— Mamdani 层写死字面量 `0.01`
（`models/nets.py` L232），NumTsk 层用 `EPSILON = 1e-7`（L552）。两者都低于阈值
0.01001 ⇒ 结论一致、不受影响；但 Mamdani 那处若将来有人调阈值容易踩坑。
改它会动到生产推理数值 ⇒ 需另立一轮。

### 19.10 运行时实测（2026-10-28）：静态推导的两处错误已被纠正

**起因**：用户质疑「你怎么知道算法能不能工作？」⇒ 复核发现前两轮的结论是
**静态推导**（读代码路径 + 阈值关系）+ **回归护栏**（pytest / 黄金快照对拍），
**不是运行时实测**。回归护栏只证明「没变」，**不证明「对」**。

⚠️ 而且静态判据**已错过两次**：
1. 第一版统计脚本把 `IPOS_worse` 等 154 条**活规则**误判成死规则
   （漏了「不可判级前件不作门控」）；
2. 第二版把 `DLUNDERSIZE1/2`、`DLOVERSIZE1/2` 20 条**活规则**误判成死规则
   （漏了 `parsing.is_position_name` 的 `DL` 前缀分支 ⇒ 它们走**缺陷通道**）。

⇒ **结论：死规则判定不能只靠静态归因，必须实测。**

#### 19.10-1 内核级三组对照（真实规则串 + 真实元数据，一次性脚本）

| 实验 | 档案 | x 里的值 | 实测结果 |
|---|---|---|---|
| R1-a `DLUNDERSIZE1` | 有 | 有 | ✅ 命中 `adj={'PP0': 5.0}`，raw_activation=1.0 |
| R1-b `DLUNDERSIZE1` | 有 | **无** | ❌ **无输出**（档案在 ⇒ 走路径③ ⇒ 整条规则被丢） |
| R1-c `DLUNDERSIZE1` | **不传** | 无 | ✅ **命中** `adj={'PP0': 5.0}`（不在 `pre_dict` ⇒ 前件不作门控） |
| R2-a `MT` | 有 | 无 | ❌ 无输出 ⇒ 死规则成立 |
| R2-b `MT` | 有 | 有（40.0） | ✅ 命中 `adj={'MT': 5.0}` ⇒ **规则本身是好的，缺的只是输入** |
| R2-c `MT` | **不传** | 无 | ⚠️ 命中但 `adj={}`（空调整；引擎 L740 `for param, value in adjustments.items()` ⇒ **不产生任何调整** ⇒ 不会产出脏推荐） |
| R3-a `BT` | 有 | 无 | ❌ 无输出 ⇒ 死规则成立 |
| R3-b `BT` | 有 | 有（37.5） | ✅ 命中 `adj={'BT': -2.0}` |

⇒ **关键机制（三条路径的分界）**：

| 路径 | 触发 | 结果 |
|---|---|---|
| ① 不可判级前件（`worse`） | `nets.py::NumTskRuleNet._construct_numtskruleNet`（`is_level_word` 分支，现 L481-488） | 该前件不作门控，规则仍可命中 |
| ② `pre_dict` 里没这维度 | 同上（`pre_dict` 分支，现 L489-493） | 该前件不作门控，规则仍可命中 |
| ③ `pre_dict` 里有、但输入里没值 | membership 兜底 `EPSILON` | **整条规则被丢** |
| ④ **档位词填不进该字段词表**（如 3 档字段上的 `very_low`） | 同上（`_resolve_bucket_safe` 返回 None，现 L496-501 + L510-514） | **整条规则激活度 0**（门控列清零）⇒ 不参与结论<br>⚠️ 2026-10-28 新增第四种，**与 ①② 严格区分**：①② 是「该条件不参与」，④ 是「条件**无法判定**」 |

⚠️ **分界是「档案是否进了 net」，不是「有没有值」**。

#### 19.10-2 端到端实测（真实 `engine.recommend` + 真实元数据 + 真实规则串）

| 场景 | 实测 |
|---|---|
| S1-a `position='DLUNDERSIZE1'` | ✅ **1 条推荐**：`PP0` 35.0 → 40.178804383033174，conf 0.5676676416183064；日志 `缺陷维度进推理输入: {'UNDERSIZE': 0.25, 'DLUNDERSIZE1': 0.75}` |
| S1-b `position` 不传 | ✅ **1 条推荐**，值**逐位相同**；日志 `{'UNDERSIZE': 0.25}`（无位置维度） |
| S1-c `position='浇口附近'` | ✅ **1 条推荐**，值**逐位相同** |
| S2 `MT` 组 | ❌ **0 条推荐**，0 条 WARNING；`field_reports.authority = ["MT"]` ⇒ profile 确实建了 |
| S3 `BT` 组 | ❌ **0 条推荐**，0 条 WARNING；`field_reports.authority = ["BT"]` |

⇒ **修正：死规则 = 170 条（`BT` 167 + `MT` 3），不是 190 条。**
⇒ 那 20 条 `DL*` 规则**正常工作并产出可见推荐** ⇒ §19.9-1 的 A 组
「去掉位置维度前件」是**错的建议**，已改。

⚠️ **附带发现（位置条件无效 —— 独立于死规则问题）**：
S1-a/b/c 三者结果**逐位相同** ⇒ `position` 不匹配时**不是「排除规则」**，
而是「该维度不建论域 ⇒ 前件不作门控 ⇒ 规则照样命中」
⇒ 规则作者写的 `AND DLUNDERSIZE1_high`（意图「**且**缺陷在位置1」）
**在算法里表达不出来** ⇒ 待决项：去掉位置条件（承认它无效），
还是算法侧补「位置标识匹配」语义（让位置不匹配时真正排除）。

⚠️ **「静默」的精确级**：`too_weak` 丢弃时内核有 `logger.debug`
（`nets.py` L480 / L499），但**没有 warning 及以上** ⇒ 生产默认日志级别下确实静默。

⚠️ **方法论沉淀**：凡「规则恒不命中 / 推荐为空」类结论，必须给出
① 静态推导（代码路径）② 运行时实测（能命中的对照 + 不能命中的对照）
③ 两者差异说明；只给静态推导会被质疑，且本项目已因此错过两次。

---

## 20. 批 K / 批 L：规则串一次解析 + §5 清理项（2026-10-28）

> 本节记录两批**结构收敛型**改动的实际施工结果。
> 共同特征：**不改变任何输出数值**（全部改完后 `run_demo --check` 与既有输出逐位一致）。

### 20.1 批 K：规则串只拆一次（§4.2 关闭）

#### 20.1-1 改动落点

| # | 文件 | 改动 |
|---|---|---|
| 1 | `fuzzy_core/profiles.py` | `RuleProfile` 新增 `parsed` 字段（`Optional[Dict[str, List[Dict[str, str]]]]`，默认 `None`）+ 详细 docstring |
| 2 | `library/semantics.py` | 新增 `RuleService.parse_rule()` —— **全链路唯一解析入口**；`match_defect_name` / `classify_conclusion_kind` 增可选 `parsed` 参数（`None` 时自行拆解 ⇒ 兼容旧调用方） |
| 3 | `library/adapters.py` | `to_rule_profile` 解析**一次**，把 `parsed` 放进 `RuleProfile` |
| 4 | `library/assembly.py` | `match_defect_name(..., profile.parsed)` |
| 5 | `fuzzy_core/rules_filter.py` | `build_rule_objects` 优先复用 `profile.parsed`，`None` 才兜底现拆 |

#### 20.1-2 为什么这样改（三个关键判断）

1. **拆解是纯函数**（结果只与规则串有关）⇒ 「拆一次、带着走」是唯一**无损**的收敛方式
   （缓存效果相同，但缓存的键/失效时机得额外维护）。
2. **`parsed` 设为可选（默认 `None`）** ⇒ 直接构造 `RuleProfile` 的调用方
   （测试替身 / 离线脚本 / demo 案例）**不必关心本字段** ⇒ 零破坏。
3. **两个来源同时受益** —— 数据库（`library/repository.py`）与文件
   （`library/files/repository.py`）**都走同一个 `RuleAssembler.assemble`** ⇒
   改一处，两个来源同时生效。

⚠️ **去重发生在解析之后**（实测确认）：去重胜负判据需 specificity / priority、
校验需 conclusion_kind ⇒ **必须先解析** ⇒ 解析次数的期望值是「**候选记录数**」
而非「去重后档案数」。这一点在验收断言里写错过一次，已修正。

#### 20.1-3 验收

| 项 | 结果 |
|---|---|
| 解析次数 | **13 → 5（降 62%）**（1646 条规则 ⇒ 4938 → 1646 次） |
| 等价性断言 ① | `profile.parsed == parse_rule(description)` **逐条相等** |
| 等价性断言 ② | 新路径解析次数 == 候选记录数，且 < 旧路径 |
| 等价性断言 ③ | 第 4 层分类结果（numeric / mamdani / advice / skipped）与「全部现拆」**逐条一致** |
| 临时脚本 | `_dev_refs/_tmp_check_once.py`，**跑完即删**（未落库） |

### 20.2 批 L：§5 清理项

#### 20.2-1 逐项落点

| 项 | 落点 | 手法 | 风险 |
|---|---|---|---|
| C1 | `fuzzy_core/models/nets.py` | 删 `percent_set` 的初始化 / 收集 / 追加 | 零（只写不读） |
| C2 | `fuzzy_core/models/nets.py` | 删 `extra_dict` 收集；`tsk_inference` 改 `return res, {}` | 零（恒空）；⚠️ `models/rules.py` 的 `r_extra` **保留**（`test_nets.py:141` 依赖） |
| C4 | `field_names.py` | 新增 `_validate_prefix_uniqueness()`，**import 时**校验 | 零（现状本就满足 ⇒ 不抛） |
| C5 | `fuzzy_core/models/nets.py` | `final_rule` 只从命中集合里选；无命中 ⇒ 哨兵 + warning | 零（语义等价，见 §5 表 C5） |
| C6 | `engine.py` | 三分支**保留**，非契约形态记 warning 留痕 | 零 |
| C7 | `fuzzy_core/macros.py` | `bucket_centers` 倒序 ⇒ 抛 `ValueError` | 零（生产不可达） |
| C8 | `specs.py` | **只标注**（用户拍板），不改代码 | 零 |
| C10 | `process/services/parameter_optimize.py` | 删重复注册块（死代码） | 零 |
| C3 | — | 批 E 已做（不属本轮） | — |
| C9 | `engine.py` | **未做** —— 需业务确认口径（D7） | — |

#### 20.2-2 两处「差点删错」的记录

1. **C6**：`tests/fuzzy_kernel/_snapshot_core.py:181` 返回裸 dict、
   `_verify_defect_selection.py:96` / `_verify_diag_isolation.py:104` 返回 Kw 对象
   ⇒ 三分支**不能删** ⇒ 改为「保留兜底 + warning 留痕」。
2. **C10**：`parameter_optimize.py:67` 的 import 语句**本身**就完成了注册
   ⇒ 其后的 `if not get_algorithm("fuzzy")` 恒 False ⇒ 整块是死代码 ⇒ 删之
   （不是「留哪边」的取舍问题）。

### 20.3 统一验收（2026-10-28）

| 项 | 结果 |
|---|---|
| `pytest process/algorithms/fuzzy tests -q` | **65 passed**（1.05s） |
| `_verify_sources_parity.py`（库来源 vs 文件来源逐条对拍） | **全部一致（失败项 0）**；102 组组合、3631 条规则、关键字 4 组全一致；引擎级端到端输出一致 |
| `_verify_field_names_forward_parity.py` | exit 0；⚠️ 报 36 处差异 = **已知口径差异**（旧合并表把裸前缀折叠成缩写 / 新拆分表保持原样），**非本轮回归**；真实入参集合 84 字段逐键差异 0、往返不闭合 0 |
| `_verify_kw_parity.py` | **[PASS]**（新链路中间产物全为 `KeywordProfile`、新旧逐键值/键序/类型全等、无 ORM 泄漏） |
| `_verify_zero_dep.py` | **[PASS]**（编排层/契约层 import 不触发 Django ORM、无顶层名泄漏） |
| `_verify_edge_boundaries.py` | **全部通过**（数值判定边界 / 推测论域正下限 / 脏结论值） |
| `_verify_e2_offline.py` | **[PASS]**（V1 注入 FakeRepository 可离线跑通 / V2 脏规则被捕获 / V3 查询异常降级为空推荐） |
| `_verify_defect_selection.py` | **ALL PASS**（含 empirical 侧零打扰） |
| `_verify_diag_isolation.py` | **ALL PASS**（单请求可读 / 并发不串扰） |
| `_verify_e2e_db.py` | exit 0 |
| `tests/verify_provided_smoke.py` | **PASSED**（6/6） |
| `tests/verify_fuzzy_algo_offline.py` | **[PASS]**（17 项全通过） |
| `tests/verify_fuzzy_algo_db.py` | **PASSED**（D1~D7） |
| `tests/verify_initialize_flat.py` | **PASSED**（B1~B3 / C1） |
| `run_demo.py --check` | **[PASS] fuzzy_shortshot_low —— 与期望输出完全一致**（MBP0/PV0/IT/PP0/IV0 五项建议值逐位一致） |

⚠️ **环境提示**：`_verify_zero_dep.py` 自身**未做 `sys.path` 注入** ⇒ 需带
`PYTHONPATH=.` 运行（其余脚本自带注入）；Windows 下中文输出需
`PYTHONIOENCODING=utf-8`，否则 GBK 乱码。

⚠️ **PowerShell 判读提示**：`2>&1` 合并后，日志（stderr）会被 PowerShell 判成
`NativeCommandError` ⇒ **必须以 `$LASTEXITCODE` 为准**，不能看终端红字。

---

## 21. 算法实现侧的剩余缺口（批 K / 批 L 之后）

> 用户 2026-10-28 口径：「两件旧事（自动整理规则 / `fuzzy_level` 可观测性）暂时不需要考虑，
> **重点还是在当前算法的实现上**」⇒ 本节汇总算法侧**还没做完**的项，
> 按「**能不能单独推进**」分三类，供下一轮选题。

### 21.1 语义已定，可直接做（但会改数值）

| # | 项 | 规格位置 / 现状 | 说明 |
|---|---|---|---|
| M-1 | **门控三态 + β_p 降权** | 规格：design 文档 §5.3（**2026-10-28 已做规格修正**，见下）<br>现状：`fuzzy_core/models/nets.py` 第二层已改用 `np.min`（批 M，2026-10-28） | 两级判据：**τ 管「要不要生效」、ε 管「生效但有多可信」**；`competition = μ_used − μ_alt`，`β_p = clamp(competition/ε, β_min, 1)`（连续衰减、无阶跃）；`weight_i = μ_i × priority_i × specificity_i × β_r`（β_r 是**规则级**因子）；输出标记 `boundary = true` + `competition`<br>⚠ **2026-10-28 规格修正**：原条文有**四处语义缝隙**（`μ_max` 口径 / β 的粒度 / τ 判在哪个 μ 上 / 权重式漏 `specificity`）⇒ 按字面实现**治不了"档位不符"** ⇒ 已改写为无歧义条文（design §5.3.1~§5.3.7），**语义未变、只把"怎么算"写死**<br>⚠ **2026-10-28 施工前只读量级预演已完成**（零生产代码改动，见 §24 + §25）⇒ 量级温和（档位错配规则的权重降 **80%**、**相符规则零误伤**、**方向变化 0 处**、最大相对变化 **0.928%**）⇒ **待用户/工艺员拍板 τ/ε/β_min 后即可施工** |
| M-2 | **冲突显式化** | 规格：design 文档 §5.5<br>现状：✅ **已实现**（批 N，2026-10-28）—— `recommendations.py::build_conflict_view` + `FuzzyRecommendation.conflict` | 同组内**方向不一致**已能显式标记（现被加权平均抹平）⇒ 输出的 `conflict` 视图（design §0.1）**拿得到数据了**（口径：**只加标记、不改数值**）；⚠️ **目标档位不一致仍未覆盖**（数值层结论是绝对量，无档位概念） |

⚠️ **M-1 会改变激活度与输出数值** ⇒ 沿用批 B 的纪律：改前先与工艺员对齐量级。
⚠️ **2026-10-28 更正**：原文写「M-1 / M-2 **都会**改变数值、两件合并为一批」——
**M-2 实际不改数值**（用户拍板：只加冲突标记），已单独成批（批 N）；
现在**只剩 M-1 是数值改动项**，不再需要“两件合并”。

⚠️ **2026-10-28 更新（批 M 之后）**：
- **M-1 的两处前提已变**：① 第二层连接方式已从 `np.prod` 改为 `np.min`（§5.2，见 §22），
  ⇒ `too_weak` 闸门被抬高，**参与结论的规则数 +36.6%**、**档位不符的规则占比 41.5% → 57.1%**
  ⇒ M-1 的「τ 判未命中」**从「可选优化」变成「先决条件」**（详见 §22.3 发现 2）；
- **M-2 的典型场景已现形**：GASVEINS/medium/MBP0 上 `MBP0_add_1.5` 与 `MBP0_reduce_1.5`
  互相抵消（§22.3 发现 3）—— 正好是「加权平均把相反方向抹平」的现实样本；
- **2026-10-28 更新（批 N 之后）**：**M-2 已落地**（`conflict` 视图，**只加标记、不改数值**，
  见 §23）⇒ 上面那个样本现在会被**显式标记**出来，不再静默。
  真实规则库扫描：**175 个（缺陷, 参数, 缺陷档位）组合上 add 与 reduce 并存**（§23.3）
  ⇒ 冲突不是边缘情况，而是**规则库里的普遍现象**。
- **2026-10-28 更新（批 O：M-1 施工前）**：**M-1 的规格已做修正**（design §5.3.1~§5.3.7）
  ⇒ 原条文有**四处语义缝隙**，其中最关键的一处是
  `competition = μ_max − μ_second` 里 **`μ_max` 到底是"所有桶里最大的"还是
  "规则实际引用的那个桶"** —— 按前者（字面）实现，"档位不符"的规则判下来仍是
  **明确态**、一点不降权 ⇒ **M-1 治不了它宣称要治的病**。
  ⇒ 已改为 `competition = μ_used − μ_alt`（`μ_used` = 规则引用的桶、`μ_alt` = 其余桶最高），
  τ 也改判在 `μ_used` 上 ⇒ **错配时 competition 为负 ⇒ 直接压到 `β_min`**。
  ⚠ **语义未变**（仍是三态 / 生效但降权 / 连续衰减无阶跃），只把"怎么算"写死；
  **本次只改文档、不动代码**。

### 21.2 语义未定，需先拍板

| # | 项 | 待定什么 |
|---|---|---|
| M-3 | **E5 矩阵替换**（`connected_matrix` numpy 矩阵 → dict + 循环） | 收益口径是什么：性能？可解释性？—— 口径不定 ⇒ 改法不定（`2026-10-22-fuzzy-engine-paradigm-decision.md` §6 标注「可延后」） |
| C9 | **`_extract_defect_context` 只取首个缺陷** | 多缺陷是「按优先级逐个推理后合并」还是「一次只解决一个」？（D7） |
| D6 | **缺陷档位是否额外加权** | 结论值里已编码了档位时，档位还要不要再乘一个权重？（D6，业务语义） |
| C8 | **层 0 反向依赖**（`specs.py` → `field_contract`） | 要不要动、动到什么程度 —— 拆开需把三个纯函数下沉并牵动 `empirical` 等包 ⇒ 属**跨包重构** |
| 位置条件语义 | `AND DLUNDERSIZE1_high` 在算法里**表达不出来** | 位置不匹配时是「**排除规则**」还是「该维度不作门控」？（§19.10 实测：现为后者 ⇒ 规则照样命中 ⇒ 作者意图无法表达） |

### 21.3 算法侧**不能单独推进**（卡在算法外）

| # | 项 | 卡在谁那里 |
|---|---|---|
| P0-2 | **经验域标定**（`RuleKeyword.range_min/range_max`） | 业务/工艺给真实分位数（E0 论域标定） |
| B10 | **补充规则库接线** | 算法侧通道已通（批 I），但 `overrides.rule_library_code` **无填写入口** ⇒ 前端/建档流程；且补库规则下的推荐值**未经工艺验证** |
| D5 | **`fuzzy_level` 可观测性** | 前端/接口层（2026-10-28 明确暂缓） |
| 自动整理规则 | **需求展开** | 纪要 D1/D4 是硬约束（2026-10-28 明确暂缓） |

### 21.4 下一轮建议顺序

⚠️ **2026-10-28 更新**：原建议的「M-1 + M-2 合并为一批」已拆开执行 ——
**§5.2 多前件连接（prod→min）已先行落地**（批 M，见 §22），
**M-2（冲突标记）也已落地**（批 N，见 §23），
只剩 **M-1（门控三态 + β_p）** 未动。
⚠️ **2026-10-28 更新**：M-1 的「① 拍板 β 合并方式」已拍板 = **(a) 最弱前件说了算**；
→「③ 跑只读预演拿量级」也已完成（见 §24 + §25）；
「② 标定 τ/ε/β_min」在**工艺员无法确认**的前提下改用**技术判据**完成（批 P-3，见 §26）
⇒ **M-1 的前置条件已全部就绪**。

1. ~~**M-1 + M-2 合并为一批**~~ —— ❌ 2026-10-28 已拆：**§5.2 先做**（批 M，已完成），
   **M-2 已做**（批 N，已完成；口径：只加标记、不改数值），
   M-1 留到下一批；
2. **M-1 门控三态 + β_p**（唯一剩下的数值改动项）—— ⚠ **2026-10-28 规格已修正**
   （design §5.3.1~§5.3.7，四处歧义已消除）⇒ 现在的待办是：
   ① 拍板 **β 的多前件合并方式** —— ✅ **2026-10-28 已拍板 = (a) 最弱前件说了算**；
   ② 标定 **τ / ε / β_min**（有物理锚点：相邻桶 μ 恒为 `exp(-2) ≈ 0.1353`，
   跨 3/5/7/9 档通用）—— ✅ **已定案**（2026-10-28 批 P-3）：工艺员无法确认，
   改用**技术判据**（τ 推导 / ε 零误伤反解 / β_min 区间夹逼）
   ⇒ **τ = 0.1353、ε = 0.10、β_min = 0.20**，含**失效边界与证伪信号**（见 §26.7）；
   ③ 跑只读预演拿量级给工艺员对齐（**这是发现 2 的收敛手段**）—— ✅ **已完成，见 §24**；
3. **C8**（纯结构、零数值风险）—— 但要动 `empirical` 等包 ⇒ 先确认影响面；
4. **M-3 / C9 / D6 / 位置条件语义** —— 等拍板再动（用户 2026-10-28 口径：暂时不管）。

⚠️ **不建议**先做 M-3：它与 M-1 都会动 `tsk_inference` 的核心计算，
分批做会让数值变化的归因变得困难 ⇒ **先做 M-1，再谈 M-3**。

---

## 22. 批 M：多前件连接 prod → min（§5.2 弱连接）+ 方向判定容差（2026-10-28）

> 本批**会改数值** ⇒ 按纪律先做**只读量级预演**（`unittest.mock.patch` 运行时替换，
> 零生产代码改动），把影响面摆给用户拍板后才动代码。

### 22.1 改了什么（两处代码 + 一处基线）

| # | 位置 | 改动 | 性质 |
|---|---|---|---|
| 1 | `fuzzy_core/models/nets.py` 第二层（规则层） | `np.prod(conditions)` → `np.min(conditions)` | **改数值**（§5.2 弱连接） |
| 2 | `recommendations.py::to_recommendations` | 方向判定加 **ε=1e-6 绝对容差**；残差视同“无变化”并把推荐值**钉在当前值**上 | **修既有缺陷**（不改真实方向） |
| 3 | `examples/cases/fuzzy_shortshot_low.json` | 4 个推荐值 + 4 个置信度更新 | 基线同步 |

⚠️ **旁证**：Mamdani 提示层（`nets.py:255`）**本来就是 `np.min`** —— 本批让
TSK 数值层与提示层的连接口径终于一致了。

### 22.2 预演量级（改代码**之前**跑出来的）

| 项 | 实测 |
|---|---|
| 规则库前件个数分布 | **2 个前件 585 条（100.0%）** ⇒ 全库规则都是双前件 ⇒ prod/min 差异**影响面是全局的** |
| 场景总数 / 输出有变化 | 51 / **51（100.0%）** |
| min 下新增的建议参数 | **0 条** |
| min 下消失的建议参数 | **0 条** ⇒ **建议条数不变** |
| 建议条数组合 (prod,min) | (2,2) (5,5) (6,6) (8,8) (10,10) (11,11) (14,14) —— 全部相等 |
| 推荐值变化处数 | 207 |
| **最大绝对变化** | **0.532672** |
| **最大相对变化** | **4.17%**（WELDLINE/low MBP0：6.000000 → 6.250000） |
| 绝对变化中位数 | 0.100000 |
| 置信度变化 | 137 处，最大 0.061804 |

**结论：量级温和** —— 条数零变化、最大相对变化 4.17% ⇒ 用户拍板「认可，推进改代码」。

### 22.3 预演挖出的三个发现

**发现 1 — 那 1 处方向变化，根因是既有缺陷，不是 min**

`recommendations.py` 原本用**精确浮点比较**判方向（`adjusted_delta > 0` / `< 0` / `== 0`）：

```
prod: MBP0 命中 2 条规则  delta = ±0.75              sum = 0.0（精确 0）  → hold
min : MBP0 命中 6 条规则  delta = ±0.1667/0.25/0.3167  sum = -5.55e-17    → decrease
```

而 `recommended_value = 5.0 + (-5.55e-17)` 在 float64 下**舍入回 5.0**
⇒ 输出**自相矛盾**：「推荐值 5.0 → 5.0（没动）」却标成 `decrease`。

- 全场景扫：`|adjusted_delta|` 落在 (0, 1e-6) 的**仅此 1 条**；
  真实方向依据最小是 **0.5**（prod）/ **0.531965**（min）
  ⇒ **ε=1e-6 有 5 个数量级余量**，不会误伤真实方向。
- 修法：`|adjusted_delta| <= ε` ⇒ 判 `hold` **且把推荐值钉在当前值上**
  ⇒ 输出严格自洽（hold ⇒ 推荐值与当前值逐位相等）。

**发现 2 — min 会放大「命中 ≠ 条件满足」的问题**

min 抬高激活度 ⇒ 原本被 `too_weak` 闸门（`MIN_ACTIVATION_THRESHOLD = 0.01001`）
拦掉的规则挤了进来：

| | prod | min |
|---|---|---|
| 参与结论的规则数 | 492 | **672（+36.6%）** |
| 档位相符 | 288 (58.5%) | **288（数量完全不变）** |
| 档位不符 | 204 (41.5%) | **384 (57.1%)** |

增加的 180 条**全部是档位不符的**（如 ABERRATION/low 场景里跑进了
`IF ABERRATION_medium AND ...`）。这正是 design §5.3 门控三态要治的病 ——
**min 单独做会让它更严重** ⇒ **M-1 从「可选优化」升为「先决条件」**（已回填 §21.1）。

⚠ **2026-10-28 补充（批 O：M-1 施工前）—— 本发现的两点重要澄清**：

**澄清 1 —— 这是「历史遗留」，不是批 M 引入的**。
上表的 prod 列**就是改造前的线上行为** ⇒ **204 条（41.5%）档位不符的规则
在批 M 之前就已经在参与结论**。批 M 只是把放行的那一侧**掀开**（41.5% → 57.1%），
**不是病因，是显影剂**。

**澄清 2 —— 改造前是「负负得正」**：prod 的指数级稀释**误杀真匹配规则**，
恰好在**对冲**"放行假匹配"这个毛病 ⇒ 两股反向误差互相抵消，
**表面上「池子干净、结论稳定」，实际两股误差从未被分别量化过**。
⇒ 这也解释了为什么该病能潜伏至今：它从不以「错」的形式出现，
只以「结论不够准」的形式出现。⇒ **批 M 拆掉了误杀这层保护 ⇒ M-1 必须补上。**

⚠ **2026-10-28 规格修正带来的第三个结论**：design §5.3 原条文按字面实现
**治不了本发现描述的病**（"档位不符"的规则若另一前件很强，
`competition = μ_max − μ_second` 仍为正 ⇒ 判成明确态 ⇒ 不降权）
⇒ 已改为 `competition = μ_used − μ_alt`、τ 判在 `μ_used` 上
（design §5.3.1~§5.3.7）。

**发现 3 — MBP0 那处就是 §5.5 的典型冲突**

`MBP0_add_1.5` 与 `MBP0_reduce_1.5` 互相抵消成 0 ——
正是「加权平均把相反方向抹平」的现实样本 ⇒ M-2（冲突标记）**有了现成的验证样本**。

### 22.4 验收

| 项 | 结果 |
|---|---|
| `pytest process\algorithms\fuzzy tests` | **65 passed** |
| 9 个 `_verify_*.py` | 全部 exit 0 |
| 4 个 `tests/verify_*.py` | 全部 exit 0 |
| `run_demo --check` | **[PASS] fuzzy_shortshot_low —— 与期望输出完全一致** |
| 事后对拍（改动后 vs `patch(np.min→np.prod)` 等价旧代码） | 场景 51 / 有变化 51 (100%)；新增 0 / 消失 0；条数组合全相等；**推荐值变化 207 处，最大绝对 0.532672，最大相对 4.17%**；**方向变化 0 处**（预演是 1 处 ⇒ 容差修复生效）；**自相矛盾 0 处** |

⚠️ **事后对拍的手法提醒**：改完代码后**不能**再用 `patch(np.prod→np.min)` 模拟旧行为
（新代码调的是 `np.min`，patch 不生效 ⇒ 会得到“0 差异”的假象）。
正确手法是 `patch(np.min→np.prod)`（把新函数换回旧函数）。

### 22.5 本批**没有**做的事

- **M-1 门控三态 + β_p 降权**（§5.3）—— 用户拍板「另开一批」；
- ~~**M-2 冲突标记**（§5.5）~~ —— 用户拍板「只加标记、不改数值」⇒ **已在本批之后落地（批 N，见 §23）**；
- 发现 2 的放大效应**未在本批收敛**（登记为已知风险，靠 §5.3 治）。

---

## 23. 批 N：冲突显式化（M-2 / design §5.5）（2026-10-28）

> 用户 2026-10-28 拍板口径：**「只加冲突标记（不改数值）」**。
> ⇒ 本批只加一层**输出视图**，**不动任何推荐数值**。

### 23.1 改了什么（1 个代码文件 + 1 个新验收脚本）

| 文件 | 改什么 |
|---|---|
| `backend/process/algorithms/fuzzy/recommendations.py` | ① `AggregatedAdjustment` 加 4 个**方向明细**字段（`positive_weight` / `negative_weight` / `positive_rules` / `negative_rules`）；② `aggregate()` 在数值层累加方向明细（**delta / activation_sum / raw_activation_sum / rule_count 的算法一字未动**）；③ 新增 `build_conflict_view()`；④ 新增 `FuzzyRecommendation`（`AlgorithmRecommendation` 子类，多挂 `conflict` 字段）；⑤ `to_recommendations()` 产出 `FuzzyRecommendation` 并挂上 conflict |
| `backend/_dev_refs/_verify_conflict_view.py` | **新增**（批 N 专用验收脚本，参照系内写在脚本里） |

⚠️ **基类 `base.py` 一个字未改** —— 理由见 §23.2「挂载点」。

### 23.2 conflict 视图的结构与判定口径

**挂载点：fuzzy 包内的 `FuzzyRecommendation` 子类**

`AlgorithmRecommendation` 是 **fuzzy / llm / empirical 三算法共用**的对外契约
（`base.py::to_dict()` 是它们统一的序列化出口）。冲突是**模糊推理独有的概念**
—— llm / empirical 没有“多条规则互相打架”这回事。
⇒ 若改基类，三个算法的输出 dict 都会凭空多一个键 ⇒ **白白扩大契约变更面**。
子类方案：**只有 fuzzy 的输出多一个 `conflict` 键**，llm / empirical 逐位不变。

**判定口径**

- **冲突存在** = 同一参数上既有 `delta > 0` 的规则（结论“调高”）、
  又有 `delta < 0` 的规则（结论“调低”）。
  符号口径与数值层完全一致（`ACTION_MAP`：add=+1 / reduce=-1）
  ⇒ **标记与数值必然自洽**：不会出现“标了冲突、净方向其实一边倒”。
- **`cancelled`** = 净方向被抵消（最终方向判成 `hold`）
  ⇒ **最危险的那种**（design §5.5 说的“静默失败”）：
  输出里有建议、实际什么也不会改。

**输出结构**

```python
{
  'has_conflict': True,
  'cancelled': False,          # True = 净方向被抵消（方向 = hold）
  'directions': [
      {'direction': 'increase', 'weight': 0.6, 'rule_count': 2, 'rules': ['IF ... THEN ...']},
      {'direction': 'decrease', 'weight': 0.4, 'rule_count': 1, 'rules': ['IF ... THEN ...']},
  ],
}
```

- `weight` = 该方向各规则的**组内占比**之和（数值层口径）；
- `rules` = **分歧依据**（规则串）；
- **无冲突时 `conflict = None`**（不给噪音；前端用 `rec.get('conflict')` 取）。
- ⚠️ **主导方向**不单独给字段 —— 它就是顶层的 `direction`（净方向）；
  冲突未抵消时 `direction` 即主导方向，抵消时 `direction = 'hold'`。

⚠️ **只覆盖“方向不一致”**；design §5.5 提到的**“目标档位不一致”未覆盖** ——
数值层（TSK）的结论是**绝对量**（`add_3.8`），没有“目标档位”概念；
档位型结论（`X_add_low`）在提示层（Mamdani），而规则库当前没有这种结论
⇒ 该场景实际为空集。

⚠️ **只统计数值层规则**：提示层（Mamdani）的 `activation` 是**原始激活度**
而非组内占比，权重语义不同质，混算无意义。

### 23.3 真实规则库的影响面（静态扫描）

扫描 `RuleMethod`（`is_active=True, is_deleted=False`）全部活跃规则：

| 实测 | 数据 |
|---|---|
| 活跃规则总数 | **1643** |
| （缺陷, 参数, 缺陷档位）组合数 | **444** |
| 其中 **add 与 reduce 并存**的组合 | **175（39.4%）** |
| 按（缺陷, 参数）聚合后的组合数 | **156** |
| 其中 add/reduce 并存的 | **59（37.8%）** |
| 涉及的规则条数（去重前） | **782** |

⇒ **冲突不是边缘情况，而是规则库里的普遍现象** ——
每一个“同一缺陷、同一参数、同一缺陷档位下既有调高又有调低规则”的组合，
都有可能在推理时**互相抵消**。此前这些抵消**全部静默**（只表现为“建议值不变”）。

典型：GASVEINS/MBP0（add=5 / reduce=7）、FLASH/IV0（add=7 / reduce=17）、
ABERRATION/IV0（add=10 / reduce=10）—— 后者量级完全对称，**抵消风险最高**。

⚠️ **口径提醒**：静态扫描是**上界** —— 两条规则还必须**同时命中**
（门控隶属度都过 `too_weak` 闸门）才会真的冲突。

### 23.4 验收

| 项 | 结果 |
|---|---|
| `pytest process\algorithms\fuzzy tests` | **65 passed** |
| 9 个 `_dev_refs/_verify_*.py` | 全部 exit 0（**含新增的 `_verify_conflict_view.py`**） |
| 4 个 fuzzy 相关 `tests/verify_*.py` | 全部 exit 0 |
| `run_demo --check` | **[PASS] fuzzy_shortshot_low —— 与期望输出逐位一致**（数值未变） |
| `_verify_conflict_view.py` | **全部 PASS**（判定口径 3 个场景 + 端到端 + 契约边界） |
| **“只加标记、不改数值”对拍** | 把 `build_conflict_view` 打成返回 `None` 重跑同一场景 ⇒ **条数、current/recommended/confidence/direction/source/reason 逐位相同** |
| **契约边界** | 基类 `to_dict()` 键集合 = **7 个，一字未变**（llm / empirical 不受影响）；fuzzy 的 `to_dict()` = 基类 7 键 **+ `conflict`** |
| 端到端真实触发 | 真实引擎 + 真实规则串下，同参数命中方向相反的规则 ⇒ **确实产出 conflict 视图**（MBP0：12.0 → 12.847，dir=increase，conflict=有，分歧依据 2 条规则） |

⚠️ **PowerShell 测量陷阱（本轮又踩了一次）**：
把多个脚本串成 `& python.exe x.py 2>&1 | Out-String` 循环时，
**stderr 有日志输出的脚本会被误判为 exit 1**（`verify_demo_machine_fields.py` 实为 exit 0）。
⇒ 判退出码必须 `1> file 2> file` 分开重定向后再读 `$LASTEXITCODE`。

⚠️ **另注**：`tests/verify_fail_fast_infer.py` / `verify_validate_feedback_backend.py` /
`verify_user_parameter_sync.py` 三个脚本**退出码非 0，但均为历史遗留失败**，
与本批**无任何关系**（它们的失败点分别落在：service 层错误码口径、
已删除的旧常量 `_DEFECTFREE_KEYWORD_NAME`、`fuzzy/specs.py` 的必填字段校验，
**全部发生在触及 fuzzy 推荐输出之前**）。

### 23.5 本批**没有**做的事

- **M-1 门控三态 + β_p 降权**（§5.3）—— 唯一剩下的数值改动项，未动；
- **“目标档位不一致”**的冲突标记 —— 未覆盖（数值层无档位概念，见 §23.2）；
- **冲突与建议的取舍策略**（冲突时到底该不该给建议值）—— 未做；
  本批严格遵守“只加标记、不改数值”，主建议照常产出（design §5.5 的口径）；
- **前端呈现** —— conflict 已在 API 输出里，**但前端是否展示、展示成什么样尚未定**；
- **§22.3 发现 2 的放大效应** —— 未收敛（靠 M-1 治）。

---

## 24. 批 P：M-1 施工前只读量级预演（2026-10-28）

> 按纪律「M-1 会改数值 ⇒ 改前先做**只读量级预演**，把影响面摆给用户/工艺员拍板后再动代码」。
> 本批**生产代码零改动** —— 预演脚本是一次性工具，跑完即删。

> ⚠️ **2026-10-28 批 P-2 口径修正（先读 §25 再读本节）**：
> 本节的「不符权重%」是**组内占比口径**，其**分母含相符规则**
> ⇒ 会被「相符规则被降权 ⇒ 分母变小」**污染** ⇒ **不能**用来判疗效；
> 受影响的结论：**§24.5「ε 越大 ⇒ 压得越狠」**与 **§24.7「推荐 ε=0.30」**
> ⇒ **均已在 §25 修正，以 §25 为准**。本节其余数据（指标 4-5 的推荐值影响面、
> 三态分布、competition 取值分布）仍然有效。
>
> ⚠️ **2026-10-28 批 P-3 追加**：§25.5 给 ε=0.10 的理由（「取保守侧」）是**软理由**，
> 已被 **§26 的实测硬判据**取代（零误伤上界 **ε\* = 0.180599**；ε ≥ 0.20 即开始误伤）
> ⇒ **三个阈值的定值规则与失效边界以 §26.7 为准**。

### 24.1 预演手法（怎么做到零生产代码改动）

| 项 | 做法 |
|---|---|
| 注入方式 | `inspect.getsource(NumTskRuleNet.tsk_inference)` → `dedent` → 逐行定位替换 → `exec(compile(src, '<m1-injected>', 'exec'))` ⇒ 得到带三态的 `tsk_inference`，**运行时**换到类属性上 |
| 注入点 | `raw = rule_activations * priority_array * spec_weights` ⇒ 改为 `raw = rule_activations * _beta_vec * priority_array * spec_weights`（`_beta_vec` = 规则级 β_r） |
| baseline 旁路 | baseline 时 β_r ≡ 1.0 ⇒ 乘 1.0 与原式**逐位相同**（已实测校验 = True）⇒ baseline 不是“另算一遍”，**就是原代码** |
| 场景集 | 活跃规则里出现的 **17 个缺陷码 × 3 个档位 = 51 个场景**；net 内 1647 条规则、3195 个前件（defect 1647 + param 1548） |
| 规则库 | 走真实 DB（`ResourceRepository.get_rules`）⇒ **不按档位筛规则** ⇒ 同缺陷名的所有档位规则都进池 —— 这正是 M-1 要治的病 |

### 24.2 场景取值怎么造（以及局限）

| 维度 | 造法 | 说明 |
|---|---|---|
| 缺陷维 | 档位**桶中心**（`level_to_domain_value`） | 相符档 μ=1.0、相邻档 μ=0.1353、隔一档 μ=3.35e-4 |
| 工艺参数维 | 该场景内被引用最多的档位的桶中心，再按 `shift`（单位 σ）偏移 | σ = span / (2×(lvl−1)) ⇒ 相邻桶间距恒为 2σ ⇒ 相邻桶 μ 恒为 `exp(-2) ≈ 0.1353`（跨 3/5/7/9 档通用） |

`shift` 的物理含义（σ = span/(2×(lvl−1))）：

| shift | 物理位置 | 参数维 competition |
|---|---|---|
| 0.00 | 桶中心（工况钉在档位中心） | +0.8647 |
| 0.25 | 桶中心 + 0.25σ | +0.7530 |
| 0.50 | 两桶正中间 | +0.5578 |
| 0.75 | 越过中点 | +0.2970 |
| 0.85 | 深入相邻档 | +0.1806 |

⚠️ **方法论局限（汇报时必须同步给工艺员）**：

1. **工艺参数取值是人工构造的**（众数档位桶中心 + shift），**不是真实机台的连续实测值** ⇒ 真实场景的相对变化可能更大；
2. **缺陷维始终是离散档位**（桶中心）⇒ 缺陷维 competition 只有 3 个取值（−0.9997 / −0.8647 / +0.8647）⇒ **ε 对缺陷维基本无区分度**；
3. 只覆盖 51 个（缺陷, 档位）场景，**未覆盖材料/产品维度**（polymer/product 留空 ⇒ 全部命中通用规则）；
4. “不符权重%” 的分母是「参与结论规则」的组内占比之和（不是规则条数）。

### 24.3 指标 1-3：核心疗效（档位不符规则被治住多少）

**shift = 0.00（工况钉在档位中心，ε=0.30、β_min=0.20）**

| 参数组 | 不符权重% | 不符条数% | 缺陷误杀% | 缺陷错放% | 相符保真% | 相符均β | 三态（未/边/明） |
|---|---|---|---|---|---|---|---|
| **baseline（β≡1）** | **15.05** | 57.14 | 0.00 | **100.00** | 100.00 | 1.000 | 0 / 0 / 1647 |
| τ=0.1353 ε=0.30 β_min=0.20 | **3.47** | 57.14 | 0.00 | **0.00** | 71.58 | 0.716 | 730 / 524 / 393 |
| τ=0.2000 ε=0.30 β_min=0.20 | **0.00** | 0.00 | 0.00 | 0.00 | 71.58 | 0.716 | 1254 / 0 / 393 |

- **核心疗效**：档位不符规则的**权重占比** 15.05% → 3.47%（**降 77%**）；缺陷错放率 100% → 0%；
- **条数不变**（57.14% → 57.14%）⇒ 完全符合 design §5.3.7「疗效在**权重**、不在条数」；
- **缺陷维误杀 0.00%** ⇒ 档位相符的规则没被缺陷维误伤。

**不符权重% 全景（按 shift）**

| shift | baseline | τ=0.1353 ε=0.3 β=0.2 | τ=0.20 | ε=0.1 | ε=0.2 | ε=0.5 | β_min=0.1 | β_min=0.3 |
|---|---|---|---|---|---|---|---|---|
| 0.00 | 15.05 | 3.47 | 0.00 | 3.47 | 3.47 | 3.47 | 1.70 | 5.10 |
| 0.25 | 15.42 | 3.57 | 0.00 | 3.57 | 3.57 | 3.57 | 1.75 | 5.25 |
| 0.50 | 16.60 | 3.89 | 0.00 | 3.89 | 3.89 | 3.89 | 1.91 | 5.71 |
| 0.75 | 18.72 | 4.52 | 0.00 | 4.48 | 4.48 | 7.17 | 2.24 | 6.61 |
| 0.85 | 19.88 | 7.61 | 0.00 | 4.82 | 5.28 | 11.88 | 3.92 | 10.95 |

### 24.4 指标 4-5：推荐值影响面（vs baseline，414 个（场景, 参数）对比点）

**shift = 0.00**

| 参数组 | 对比处数 | 值变化 | **方向变** | 最大绝对变化 | 最大相对% | 新增参数 | 消失参数 | 出局条数 | 其中相符 |
|---|---|---|---|---|---|---|---|---|---|
| τ=0.1353 ε=0.30 β_min=0.20 | 414 | 363 | **0** | 0.092849 | **0.928** | 0 | 0 | 0 | 0 |
| τ=0.2000 ε=0.30 β_min=0.20 | 414 | 363 | **0** | 0.119203 | 1.192 | 0 | 0 | 524 | **0** |
| τ=0.1000 ε=0.30 β_min=0.10 | 414 | 363 | **0** | 0.105850 | 1.059 | 0 | 0 | 0 | 0 |
| τ=0.1000 ε=0.30 β_min=0.30 | 414 | 363 | **0** | 0.080186 | 0.802 | 0 | 0 | 0 | 0 |

**全 shift 汇总（最大相对变化%）**

| 参数组 | 0.00 | 0.25 | 0.50 | 0.75 | 0.85 |
|---|---|---|---|---|---|
| τ=0.1353 ε=0.3 β_min=0.2 | 0.928 | 0.848 | 0.826 | 0.851 | 0.716 |
| τ=0.2000 ε=0.3 β_min=0.2 | 1.192 | 1.089 | 1.064 | 1.106 | 1.141 |
| τ=0.1000 ε=0.3 β_min=0.3 | 0.802 | 0.732 | 0.712 | 0.731 | 0.522 |

- **建议条数：0 增 0 消**；**方向变化：0 处**（全部参数组、全部 shift）；
- 最大绝对变化 0.092849（`ABERRATION`/low/`IP0`：52.1192 → 52.0264）；
- 最大相对变化 0.928%（`OVERSIZE`/low/`PT0`：current=2.5，3.0298 → 3.0066）。

### 24.5 三个参数的物理分工（预演实测出来的）

**τ = 「要不要生效」的开关（阶跃）**

- τ ∈ [0, 0.1353] **完全等价**（τ=0.05 / 0.10 / 0.1353 结果逐位相同：3.47%、三态 730/524/393）⇒ 因为相邻档 μ 恒为 0.1353，隔一档 μ=3.35e-4 远小于任何 τ；
- τ ≥ 0.20 ⇒ 相邻档（μ=0.1353 < τ）**直接出局** ⇒ 不符权重归零，但**出局 524 条**，其中「档位相符」**0 条** ⇒ 不是误杀，是“前提确实不成立”；
- 物理锚点：**τ = 0.1353 = exp(−2) = 相邻桶隶属度** ⇒ “低于相邻档隶属度的才算真没命中”。

**ε = 「生效但有多可信」的门槛（只在工况进过渡带时显区分度）**

| shift | competition | ε=0.1 | ε=0.2 | ε=0.3 | ε=0.5 |
|---|---|---|---|---|---|
| 0.00 | +0.8647 | β=1 | β=1 | β=1 | β=1 |
| 0.75 | +0.2970 | β=1 | β=1 | **β=0.99** | **β=0.594** |
| 0.85 | +0.1806 | β=1 | **β=0.903** | **β=0.602** | **β=0.361** |

- shift=0（工况钉在档位中心）时 ε ∈ {0.1, 0.2, 0.3, 0.5} 结果**完全相同**（3.47%）⇒ ε 只在工况落进过渡带时才起作用；
- ⚠️ **方向与直觉相反**：**ε 越大 ⇒ 越容易判边界态 ⇒ β 越低 ⇒ 压得越狠**（需工艺员确认这个方向是否符合工艺直觉）。

**β_min = 唯一连续旋钮**

- shift=0 时：β_min=0.1 → 1.70%；β_min=0.2 → 3.47%；β_min=0.3 → 5.10%；
- β_min 越大 ⇒ 越接近 baseline（β_min=0.3 时最大相对变化降到 0.802%）；
- β_min 还会决定“要不要出局”：β_min=0.1 时有 1.95% 的规则 β 落到 0 直接出局（不符条数 57.14% → 55.19%）。

### 24.6 β_r 分布（规则级）—— 验证「β=min 最弱前件说了算」

τ=0.10、ε=0.30、β_min=0.20：

| shift | β_r = 0.0 | β_r = 0.2 | β_r = 0.602 | β_r = 0.99 | β_r = 1.0 |
|---|---|---|---|---|---|
| 0.00 | 730 | 524 | — | — | 393 |
| 0.25 | 730 | 524 | — | — | 393 |
| 0.50 | 730 | 524 | — | — | 393 |
| 0.75 | 730 | 524 | — | 360 | 33 |
| 0.85 | 730 | 524 | 360 | — | 33 |

- β_r=0.0 的 730 条 = 缺陷档位**隔一档以上**（μ=3.35e-4 < τ）⇒ 出局；
- β_r=0.2 的 524 条 = 缺陷档位**相邻档**（μ=0.1353，competition<0 ⇒ β 被压到 β_min）⇒ **降权但不出局**；
- shift>0 时多出 β=0.99 / 0.602 的一档 = **工艺参数维**进了过渡带 ⇒ 整条规则被最弱前件拖累（方案 (a) 的直接体现）。

### 24.7 建议的参数组合（**待用户/工艺员拍板**）

> **τ = 0.1353、ε = 0.30、β_min = 0.20**

理由：

1. **τ = 0.1353**（= `exp(-2)`，相邻桶隶属度）：物理锚点明确；τ 区间 [0, 0.1353] 等价 ⇒ 取上界留余量；再高一档（0.20）就把 524 条规则**整个剔除**，虽然其中“档位相符”是 0 条，但剔除是**阶跃、不可调** ⇒ 0.1353 保留“降权而非剔除”的连续性；
2. **ε = 0.30**：落在中间。shift=0.75 时只把 β 压到 0.99（几乎不干扰），shift=0.85 时压到 0.602（有效压制）；ε=0.5 过狠（0.594@0.75），ε=0.2 过松（0.903@0.85）；
3. **β_min = 0.20**：中庸。不符权重 3.47%（核心疗效 77%）、最大相对变化 0.928%、方向变化 0 处。

⚠️ **但 ε 必须由工艺员用真实机台数据校准** —— 预演里工艺参数取值是人工构造的（§24.2 局限 1）⇒ 若真实工况分布集中在过渡带（shift>0.5），ε 的实际影响会**远大于**预演。

⚠️ **另一个需工艺员确认的业务语义**：预演中“档位相符规则”的**均 β = 0.716**（shift=0）⇒ 有 **28.42%** 的相符规则因**工艺参数维前提不成立**而被降权 —— 这**不是缺陷维误杀**，但确实改变了相符规则的权重 ⇒ 需确认“前提不成立就该降权”是否就是工艺意图。

### 24.8 本批**没有**做的事

- **生产代码零改动**（只读预演）；
- **没定 ε** —— 等工艺员给真实机台工艺参数的实测分布；
- **没跑全量验收** —— 因为没改代码（跑一遍没有意义）；
- **预演脚本是一次性工具**（`_dev_refs/_tmp_m1_preview.py` 等）⇒ 跑完即删，**不入库**；
- 「目标档位冲突」标记（§23.5 遗留）仍未覆盖。

---

## 25. 批 P-2：疗效口径修正 + **无真实数据**下的参数判定（2026-10-28）

> 用户口径：「**没有几台数据校准，目前只能基于当前情况看怎么判定**」
> ⇒ 本批把 §24 的预演换成**不会被污染的疗效口径**，并用**最坏情况（min-max）分析**
> 给出**不依赖真实机台数据**的参数判定。

### 25.1 为什么要换口径（§24 的「不符权重%」被污染了）

§24 的「不符权重%」= Σ(不符规则的**组内占比**) / Σ(全部参与规则的组内占比)
⇒ **分母里含相符规则**，而 M-1 会把相符规则**一起降权**（工艺参数维进过渡带时）
⇒ 分母变小 ⇒ 不符占比**被动抬高** ⇒ 表现为「**ε 越大 → 不符权重% 越高**」的反直觉现象：

| shift | ε=0.1 | ε=0.2 | ε=0.3 | ε=0.5 |
|---|---|---|---|---|
| 0.85 | 4.82% | 5.28% | 7.61% | **11.88%** |

⇒ **§24.5 的「ε 越大 ⇒ 压得越狠」与 §24.7 的「推荐 ε=0.30」据此修正**（见 §25.4）。

**污染机制**（`nets.py` 第三层）：

1. `raw = μ × priority × specificity × β` ⇒ β 直接乘在权重上；
2. 组内归一化 `group_weights[i] = raw[i] / Σraw[组]` ⇒ **降权会改变同组其它规则的占比**；
3. `group_weights < MIN_ACTIVATION_THRESHOLD(0.01001)` 的规则被剔除，剩下再重新归一化
   ⇒ **剔除 + 重归一化**让“占比”变成**耦合量**，不再能当权重看。

### 25.2 干净口径（分子分母各自独立）

在 `raw = ...` 那一行后**多抓一个 `raw` 向量**（未归一化的绝对权重）：

    raw_i = μ_i × priority_i × specificity_i × β_i

| 指标 | 定义 | 为什么干净 |
|---|---|---|
| **不符权重降幅** | `1 − Σ_{不符} raw(M-1) / Σ_{不符} raw(baseline)` | 分子只含不符规则 ⇒ 不受「相符被降权」「重归一化」影响 |
| **相符权重削减** | `1 − Σ_{相符} raw(M-1) / Σ_{相符} raw(baseline)` | 分母只含相符规则 ⇒ 同上 |
| **不符:相符** | `Σ_{不符} raw / Σ_{相符} raw` | 同一组内两个比值相除 ⇒ 组内归一化分母约掉 |

> ✅ **旁路校验**：「β≡1 旁路版」与「未注入原版」在前 6 个场景上逐位相同 = **True**（同 §24.1）。

### 25.3 判定结果（干净口径，5 档 shift 取最坏值）

| 参数组 | 不符权重降幅% | 相符权重削减%（最坏） | 不符:相符（全谱范围） |
|---|---|---|---|
| **baseline（β≡1）** | — | — | **0.1804 → 0.2498**（随工况漂 **38.5%**） |
| τ=0.05~0.1353 ε=0.30 β_min=0.20 | **80.00** | 35.17 | 0.0361 → 0.0771 |
| τ=0.20 / 0.30 ε=0.30 β_min=0.20 | **100.00** | 35.17 | 0.0000（全部出局） |
| **τ=0.10 ε=0.10 β_min=0.20** | **80.00** | **0.00** | **0.0361 → 0.0500** |
| τ=0.10 ε=0.20 β_min=0.20 | 80.00 | 8.57 | 0.0371 → 0.0547 |
| τ=0.10 ε=0.50 β_min=0.20 | 80.00 | **56.45** | 0.0404 → 0.1147 |
| τ=0.10 ε=0.30 β_min=0.10 | 90.61~90.76 | 35.17 | 0.0167 → 0.0362 |
| τ=0.10 ε=0.30 β_min=0.30 | 70.00 | 35.17 | 0.0541 → 0.1156 |

**帕累托前沿**（疗效 vs 误伤代价，二者不可兼得）：

| 参数组 | 最差降幅% | 最差削减% | 最差不符:相符 |
|---|---|---|---|
| τ=0.20 / 0.30 ε=0.30 β_min=0.20 | 100.00 | 35.17 | 0.0000 |
| **τ=0.10 ε=0.10 β_min=0.20** | 80.00 | **0.00** | 0.0500 |

### 25.4 三个参数的分工（**修正 §24.5**）

| 参数 | 真实作用 | 证据 |
|---|---|---|
| **τ** | **疗效开关（阶跃）** | τ ≤ 0.1353 ⇒ 降幅恒 80.00%；τ ≥ 0.20 ⇒ 降幅 100%（524 条相邻档规则整体出局） |
| **ε** | **误伤旋钮（不是疗效旋钮）** | 干净口径下 **疗效（降幅）与 ε 完全无关**（恒 80.00%）；ε 只改「相符权重削减」：ε=0.1⇒**0.00%**、ε=0.2⇒8.57%、ε=0.3⇒35.17%、ε=0.5⇒**56.45%** |
| **β_min** | **疗效的连续旋钮** | 降幅 ≈ `1 − β_min`：0.1→90.76%、0.2→80.00%、0.3→70.00% |

⚠️ **§24.5 的「ε 越大 ⇒ 压得越狠 ⇒ 疗效越好」是错的** —— 那是污染口径的假象：
ε 大 ⇒ **相符规则被削得更多**（代价），**疗效一点没多**。

### 25.5 判定结论（**无真实数据**下的推荐）

> **τ = 0.1353、ε = 0.10、β_min = 0.20**

| 理由 | 依据 |
|---|---|
| ① **疗效确定**：档位错配规则的权重降到 20%（降幅 **80.00%**），且 **5 档 shift 全谱恒定 80.00%** | §25.3 |
| ② **零误伤**：相符规则权重削减 **0.00%**（全谱）—— 全参数组里**唯一**做到零误伤的 ε | §25.3 |
| ③ **τ 取物理锚点**：`exp(-2) = 0.1353` = 相邻桶隶属度；“低于相邻档隶属度的才算真没命中” | §24.5 |
| ④ **β_min=0.2 中庸**：降 80%，且 β_min 直接就是「错配规则保留多少权重」，业务上可解释 | §25.4 |
| ⑤ **推荐值影响面温和**：最大相对变化 **0.928%**（shift=0）、全谱 ≤ **0.928%**、**方向变化 0 处**（§24.4，同参数组同场景） | §24.4 |

⚠️ **为什么在没有数据时选 ε 的保守侧**（⚠️ **本段已被 §26 取代为硬判据**）：

- ~~ε=0.10 的语义 =「**当前档只要领先相邻档 0.1 以上，就不降权**」⇒ **宁可少降权，不误伤相符规则**~~；
- ~~ε=0.30 在工况深度偏离时会削掉 **35%** 的相符规则权重（shift=0.85），而**疗效一点不多** ⇒ 纯代价~~；
- ⇒ **§26 实测给出了硬边界**：零误伤上界 **ε\* = 0.180599**；
  ε ≥ 0.20 ⇒ shift=0.85 工况下 **20% 的相符规则被误伤**；ε ≥ 0.30 ⇒ 累计 **40%**；
  ⇒ **ε = 0.10 的理由不再是「保守侧」（软理由），而是「实测落在零误伤区内」** ⇒ 见 §26.7。

⚠️ **原「仍需工艺员确认」的两点**（2026-10-28 批 P-3：**工艺员无法确认 ⇒ 改用技术判据**）：

1. 「**前提不成立就该降权**」是否就是工艺意图（工艺参数维前提不成立时，相符规则被降权）
   —— ⇒ **§26.5 已确认「工艺参数维的相符规则不会被降权」**（ε=0.10 时 β_p 只取 {1, β_min}，
   相符侧 competition 全部 ≥ ε）⇒ 该疑问在 M-1 的取值下**不会发生**；
2. β_min=0.20 意味着「档位错配的规则仍保留 20% 权重参与结论」—— 这个比例是否可接受
   —— ⇒ **§26.6 已给出技术判据**：错配残留 = `17.728922·b / (98.25 + 17.728922·b)`
   ⇒ b ∈ [0.113, 0.292] 对应「残留贡献 2%~5%」⇒ **取中点 0.20**（残留 3.48%，压 5.2 倍）。

### 25.6 基线结构（补充事实）

| 项 | 实测 |
|---|---|
| net 内规则 | 1647 条 |
| **实际参与结论** | **917 条**（相符 393 + 相邻档不符 524） |
| 被绝对激活度闸剔除 | **730 条**（缺陷档位**隔一档以上**，μ=3.35e-4 < `MIN_ACTIVATION_THRESHOLD`=0.01001） |
| Σraw 不符 / Σraw 相符（shift=0） | 17.728922 / 98.250000 ⇒ 比 0.1804 |
| 不符规则的缺陷档位分布 | medium 262 条、low 131 条、high 131 条 |

⇒ ⚠️ **口径澄清**：「档位错配」在**参与结论**的规则里只占 **524 / 917 = 57.14%**，
且**全是相邻档**（隔一档的早就被绝对闸剔了）⇒ **M-1 要治的病其实是“相邻档规则以 μ=0.1353 全额参与结论”**。

### 25.7 本批**没有**做的事

- **生产代码零改动**；
- **没有**用真实机台数据校准（无数据 ⇒ 改用最坏情况分析）；
- **没有**重新跑指标 4-5（沿用 §24.4 的同参数组数据）；
- 预演脚本仍是**一次性工具**，跑完即删。

---

## 26. 批 P-3：**阈值如何指定**（无工艺员、无真实数据下的定值规则）

> 用户口径（2026-10-28）：「**工艺员无法确认**，我现在的问题在于，**你这个阈值该如何指定**」
> ⇒ 本批回答的是**方法论**：阈值按什么规则定、判据是什么、定出来的值**什么时候失效**。
> ⇒ **结论：三个阈值分属三种性质，各有各的指定规则，全部不依赖工艺员与真实数据。**

### 26.1 为什么 §25 的「取保守侧」不算答案

§25.5 当时给 ε=0.10 的理由是「没有数据时取保守侧」—— 这是**软理由**：
不可复现、不可证伪（同理可以取 0.05 / 0.15 / 0.18），也没说清「保守到什么程度」。

本批把它换成**硬判据**：ε 的**唯一代价**（误伤相符规则）可以**实测出来**，
且它的**疗效贡献恒为 0**（§26.4）⇒ ε 的取值只需满足「代价 = 0」，
而这个代价有**明确的实测边界**。

### 26.2 三类阈值 · 三条指定规则

| 参数 | 性质 | 指定规则 | 定值 |
|---|---|---|---|
| **τ** | **结构量**（能推导） | **R1 推导优先**：能从数据结构推出的，绝不标定 | **0.1353 = exp(−2)** |
| **ε** | **纯代价旋钮**（零收益） | **R2 代价可测 + 取零**：无收益的旋钮，代价必须实测且取零 | **0.10** |
| **β_min** | **效果旋钮**（有收益） | **R3 区间夹逼 + 取中点**：把效果写成可算量，给可解释区间，取中点 | **0.20** |

> **R0（先决）：先给阈值分类，再分别指定。**
> 把三个阈值混在一起讨论「取保守还是激进」是无解的 —— 它们**性质不同**：
> 一个是**推导量**、一个是**纯代价**、一个是**效果旋钮** ⇒ 必须拆开。

### 26.3 R1 · τ 的指定规则：**推导，不是标定**

推导链（每一环都能在代码里核对）：

1. `features.py`：`σ = span / (2 × (lvl − 1))`
2. `macros.bucket_centers`：相邻桶中心距 ≡ `2σ`
3. 桶中心处对**相邻桶**的隶属度 ≡ `exp(−(2σ)² / (2σ²))` = **`exp(−2)` = 0.1353**
4. ⇒ **与档位数（3/5/7/9）、与 span 都无关** ⇒ 跨档位统一

⇒ **τ = 0.1353 就是「相邻桶隶属度」这个结构常数本身**，不是任何工况量。

**三条反向检验**（实测，§25.3）：

| τ | 后果 |
|---|---|
| 0.05 ~ 0.10 | 相邻档规则（μ=0.1353）**仍全部参与** ⇒ 疗效只有 **80%** |
| **0.1353** | 相邻档规则 μ_used = τ ⇒ **不满足「< τ」** ⇒ 压到 β_min 而**不出局** ⇒ 疗效 80% 且**保留连续性** |
| 0.20 ~ 0.30 | 相邻档规则 μ_used < τ ⇒ **整体出局** ⇒ 疗效 100%，但把「比相邻档还弱」这条语义边界**抹平**（阶跃、不可调） |

⇒ **0.1353 是唯一使「相邻档 = 压到 β_min 而不出局」精确成立的点**
⇒ **无需工艺员、无需真实数据**。

### 26.4 R2 · ε 的指定规则：**零误伤反解**

**前提（实测，见 §26.5）**：**ε 不产生任何疗效。**

错配侧（档位不符）的 competition **全为负**（−0.9997 ~ −0.6898）
⇒ `β_p = clamp(competition/ε, β_min, 1) = β_min` ⇒ **与 ε 无关**。

⇒ **ε 的唯一作用 = 误伤「归属一致但领先不足」的相符规则。**
⇒ **R2：既然 ε 只有代价没有收益，无数据时的唯一理性规则 = 取代价为 0 的最大 ε。**

**ε\* 的定义（可复现）**：

```
ε* = min { competition(p,b) | 归属一致（μ_used > μ_alt） }
```

### 26.5 实测（只读，零生产改动）

口径：`competition = μ_used − μ_alt`（design §5.3 修正后规格）；
工况 = 该参数**档位众数桶中心** + shift·σ（σ = span/(2(lvl−1))）；
shift ∈ {0, 0.25, 0.5, 0.75, 0.85}。

**取数**：全库 active 规则 **1643** 条 ⇒ 解析出 **1507** 条含工艺参数前件；
缺陷维前件 1643 个、工艺参数维前件 1797 个、不可判级（`worse` 等）154 个；
涉及工艺参数 27 个，其中 **25 个取到论域元数据**
（`HOLDEXIST` / `injectstage3` 缺元数据 ⇒ 不参与统计）；
评价点 **8960** 个（规则 × 前件 × shift），档位桶解析失败 **0** 次。

**相符侧 competition 分布**：

| shift | 条数 | min | p50 | max | <0.10 | <0.20 | <0.30 | <0.50 |
|---|---|---|---|---|---|---|---|---|
| 0.00 | 1066 | 0.8647 | 0.8647 | 0.8647 | 0% | 0% | 0% | 0% |
| 0.25 | 1066 | 0.7530 | 0.7530 | 0.7530 | 0% | 0% | 0% | 0% |
| 0.50 | 1066 | 0.5578 | 0.5578 | 0.5578 | 0% | 0% | 0% | 0% |
| 0.75 | 1066 | 0.2970 | 0.2970 | 0.2970 | 0% | 0% | 100% | 100% |
| 0.85 | 1066 | 0.1806 | 0.1806 | 0.1806 | 0% | 100% | 100% | 100% |

⇒ **全谱 min = 0.180599**；25 个参数的 min **完全相同**
⇒ 这是**桶几何的离散刻度**，与参数、与论域无关
⇒ **ε\* = 0.180599**

**各 ε 的误伤面**（含「允许的工况偏离 d\*」换算：d = 偏离桶中心的距离，单位 σ；桶间距 = 2σ）：

| ε | 误伤条数 | 误伤占比 | 最坏 shift | d\*（误伤起始） | 占桶间距 |
|---|---|---|---|---|---|
| 0.05 | 0 | 0.00% | — | 0.9588 | 47.9% |
| **0.10** | **0** | **0.00%** | — | **0.9174** | **45.9%** |
| 0.1353 (= τ) | 0 | 0.00% | — | 0.8880 | 44.4% |
| 0.15 | 0 | 0.00% | — | 0.8757 | 43.8% |
| **0.20** | 1066 | **20.00%** | 0.85 | 0.8336 | 41.7% |
| 0.25 | 1066 | 20.00% | 0.85 | 0.7909 | 39.5% |
| **0.30** | 2132 | **40.00%** | 0.75 | 0.7474 | 37.4% |
| 0.50 | 2132 | 40.00% | 0.75 | 0.5603 | 28.0% |

⇒ **刀口落在 0.1806 与 0.20 之间**：
ε ≥ 0.20 ⇒ shift=0.85 工况下**全部相符规则被误伤**；ε ≥ 0.30 ⇒ 再叠加 shift=0.75 ⇒ 累计 40%。
⇒ ⚠️ **误伤是阶跃的、不是渐变的**（competition 取值是离散刻度）
⇒ ε 落在刀口两侧，代价差一个量级。
⇒ 而这些 ε **疗效完全相同**（§26.4）⇒ **ε ≥ 0.20 是纯代价、零收益。**

### 26.6 R3 · β_min 的指定规则：**残留影响夹逼 + 取中点**

β_min 决定「错配规则保留多少权重」⇒ 它**直接就是**错配规则对结论的残留贡献。

**可算量**（baseline，干净口径，§25.6）：

- 错配规则 Σraw = **17.728922**（524 条 × 0.1353 × 0.25）
- 相符规则 Σraw = **98.250000**（393 条 × 1.0 × 0.25）
- ⇒ baseline 错配贡献 = **18.04%**

**M-1 后**（错配侧 β ≡ β_min，与 ε 无关）：

```
错配贡献(b) = 17.728922·b / (98.25 + 17.728922·b)
```

| β_min | 错配残留贡献 | 压制倍数 |
|---|---|---|
| 0.10 | 1.77% | 10.2× |
| **0.20** | **3.48%** | **5.2×** |
| 0.30 | 5.12% | 3.5× |

**判据（可解释区间）**：「把错配规则的贡献压到 **2% ~ 5%**」
⇒ b ≤ 0.113（≤2%）、b ≤ 0.292（≤5%）⇒ **β_min ∈ [0.113, 0.292]** ⇒ **取中点 0.20**

⇒ **0.20 有独立技术判据**（不是"中庸"），且区间两端都可解释、可复算。

⚠️ **批 P-5 修正（2026-10-28）**：本节区间的**下端 `0.113` 不可用**
（会让组内占比闸在 3.8% 的组上真的触发 ⇒ 实测反解的**可行性下界**为 `b ≥ 0.154`）。
⚠️ 但该下界是**可行性约束**、**不是本节效果区间的端点** ⇒
**本节区间与中点 `0.20` 均不变**，结论值也不变。
（推导与反证见 §28.6）

### 26.7 定值结论 + **失效边界与证伪信号**

> ### **τ = 0.1353、ε = 0.10、β_min = 0.20**

| 阈值 | 失效边界 | 证伪信号（上线后观测到什么 ⇒ 该调） |
|---|---|---|
| τ | τ > 相邻桶隶属度 ⇒ 相邻档规则**整体出局**（不可调的阶跃） | 参与结论的规则条数相对 baseline 骤降 |
| ε | **工况偏离桶中心 > 0.917σ**（= 桶间距的 45.9%）⇒ 开始误伤 | **相符规则上出现 `boundary` 标记**（零误伤被打破）⇒ 立即收紧 |
| β_min | 错配残留 > 5% ⇒ 病没治好；< 2% ⇒ 过度压制；**< 0.154 ⇒ 组内占比闸触发**（批 P-5 新增，见 §28.6） | 推荐值变化处数 / 最大相对变化超预期；**出现 `[fuzzy.net.group_share]` 剔除事件**（= 占比闸触发 ⇒ β 压过头） |

**三条规则各自的"决策链"**（可复现、不需人判断）：

```
τ   ：结构推导 → exp(-2) = 0.1353
ε   ：实测零误伤上界 → ε* = 0.180599 → 取安全值 0.10（d* = 0.917σ）
β_min：残留影响夹逼 → [0.113, 0.292] → 取中点 0.20
```

### 26.8 副产品结论：ε=0.10 下 **M-1 退化为纯二值门控**

实测：ε=0.10 时，相符侧 competition 取值集合 = {0.1806, 0.2970, 0.5578, 0.7530, 0.8647}
**全部 ≥ ε**；不符侧全部 ≤ −0.6898 ⇒ `clamp` 后 β_p 只取 **{1, β_min}** 两个值
（落在「0 < competition < ε」相带的前件数 = **0 / 5330**）。

⇒ **在 ε=0.10 下，M-1 = 「档位错配 ⇒ 压到 β_min；其余不动」的二值门控。**
好处：行为可解释、无中间态；代价：工况极靠近桶中点（d > 0.917σ）时才出现连续衰减。

### 26.9 本批的局限（必须说清）

1. **工况是构造的**：每参数独立偏移 shift·σ，**不是真实机台实测**
   ⇒ 单维 competition 的**取值集合**是构造谱的产物（离散刻度），
   **真实工况下会连续分布**
   ⇒ 「ε ≥ 0.20 误伤 20%」这个**具体数字**依赖谱的构造，
   但「**ε 越大误伤面越大**」的单调性与「**ε ≤ ε\* 零误伤**」这条**规则**是普适的；
2. **预演谱只到 d = 0.85σ** ⇒ ε 的零误伤边界会随真实工况分布移动
   ⇒ ε = 0.10 的余量（到 0.917σ）**不是无限安全**（失效边界已写进 §26.7）；
3. **competition 逐前件算** ⇒ 多参数工况**不改变单维结论**
   （min 弱连接只影响整条规则的激活度）；
4. **2 个参数缺论域元数据**（`HOLDEXIST` / `injectstage3`）⇒ 未参与统计；
5. **只读**：生产代码零改动；预演脚本一次性，跑完即删。

---

## 27. 批 P-4：**阈值拆分**（一个常量 → 三个量纲不同的常量）

> 用户口径（2026-10-28）：「最早的算法中，阈值给的是固定值 0.01，
> 但是由于 nets 中实际实现了多种方案，导致原有的这个固定阈值不够用了，
> 所以需要进行拆分？」⇒ 本批既执行拆分，也**修正这条因果链**。

### 27.1 因果链修正：「不够用」→「量纲错配」

用户的理解方向对，但根因不是「方案变多导致一个数值不够用」，而是
**「同一个常量被搬到了三个正交的问题域上」**。git 史实：

| 时点 | commit | 判据量（量纲） |
|---|---|---|
| 项目初始化 | `dcfb784 init` | `min_threshold = 0.01001` **内联**在 `nets.py` —— **输出侧**结论隶属度之和（**仅此一处**） |
| 提成常量 | `b2ac553 更新服务` | 移入 `macros.py`，改名 `MIN_ACTIVATION_THRESHOLD`（仍 1 处） |
| **转折点** | `e7a607a`（2026-10-23）「修 TSK 推理层两处缺陷（D 无效激活过滤 + B 门控取连接列）」 | TSK 主路**原本没有这道闸**，为补齐而搬过来 ⇒ 变成**组内占比**（量纲变了） |
| 批 B（分组归一化改造） | — | 去掉全局分母后**显式补上**绝对强度闸 `too_weak` ⇒ 再变成**输入侧绝对激活度** |

⇒ 三处判据量的**量纲互不相同**，却共用同一个数 ⇒ 无法单独调、无法各自解释、也无法各自给判据。

⚠️ `init` 时那行的原注释是「**决定需要填充的阈值**」（旁边还留着一行被注释掉的 `# max_threshold = 0.8`）
⇒ **这个数字从第一天起就没有推导依据**。

⚠️ `FuzzyRuleNet`（Mamdani）与 `NumTskRuleNet`（TSK）是**两个独立 class、不同推理路径**、不会同时生效
⇒ 「方案变多」本身**不构成**「一个值不够用」；真正的问题是 `e7a607a` 那次
「**语义对齐**」的复用 —— 对齐的是**名字**，不是量纲。

### 27.2 本批改动（**零行为变化**）

| 文件 | 改动 |
|---|---|
| `fuzzy_core/macros.py` | `MIN_ACTIVATION_THRESHOLD` **删除**，拆为 `MIN_CONCLUSION_DEGREE` / `MIN_RULE_ACTIVATION` / `MIN_GROUP_SHARE`，**三个值全部仍为 `0.01001`** |
| `fuzzy_core/models/nets.py` | 三处使用点分别引用对应常量；注释改写为「量纲」口径 |
| `2026-10-23-fuzzy-implementation-design.md` | 新增 **§5.3.8「阈值清单」**（判据量 / 量纲 / 依据 / 失效边界 / 谁负责调） |

⚠️ **不保留旧名别名** —— 留一个语义含糊的旋钮正是本次要消除的东西；
已确认生产代码中仅 `nets.py` 4 处引用（其余命中全在 `_refs/` 历史文档里）。
⚠️ `tests/verify_fuzzy_algo_offline.py` **自带本地副本**（L63）⇒ 它**不验证** `macros.py` 的常量
⇒ 本批的「零行为变化」不能只靠它，须靠下面的独立证据。

### 27.3 方案侧修订：`MAX_GROUP_AMPLIFY = 1.2` **撤掉**

上一轮口头方案里给的护栏常量：

```python
MAX_GROUP_AMPLIFY = 1.2   # ← 无判据，纯拍
```

⚠️ **它违反本文件 §26.1 自己的原则**（「软理由不可复现、不可证伪」）⇒ **不予合入**。
量化后更清楚：放大倍数 `= 1/(1−S)`，要求 `≤ 1.2` 等价于「被剔除规则的总份额 `S ≤ 16.67%`」
⇒ 但「16.67% 可接受」本身没有任何依据。

⇒ **改为**：占比闸**值保持 `0.01001` 不变**，只把「本次剔除导致的放大倍数」做成**可观测指标**
（记录 S 分布），等真实场景数据看到分布后，再决定要不要设护栏、设多少。
⇒ **先观测后定值**，而不是先拍一个护栏。

### 27.4 三处使用点的后续处置

| 常量 | 何时变 | 变成什么 |
|---|---|---|
| `MIN_CONCLUSION_DEGREE` | **不变** | 它本来就是输出侧判据，现状没有证据说它错 |
| `MIN_RULE_ACTIVATION` | **随 M-1 落地时删除** | τ=0.1353 的剔除集**严格包含**本闸的剔除集 ⇒ 冗余 |
| `MIN_GROUP_SHARE` | 需独立定值 | 判据 = 放大倍数上限（或先只观测）⇒ 见 §27.3 |

### 27.5 验收

| 手段 | 结果 |
|---|---|
| `tests/verify_fuzzy_algo_offline.py`（**venv / numpy 1.26.4**） | **[PASS] 17 项全通过**（EXIT=0） |
| 黄金快照 `_compare_golden.py`（`_golden_ABC.json` vs 新快照） | **逐条差异 3 条** ⇒ **非本批引入**，归因见 §27.6 |
| 文件编码 | `macros.py` / `nets.py` 的 UTF-8 BOM **原样保留**（`239,187,191`） |

### 27.6 ⚠️ 附带发现：黄金基线已**过期于批 M**

比对出的 3 条差异**全部**落在 `.infer.*.confidence`：

| 路径 | 基线 | 新快照 |
|---|---|---|
| `.infer.basic\|ctx_mid.recs[0].confidence` | `0.018315638888734182` = **exp(−4)** | `0.1353352832366127` = **exp(−2)** |
| `.infer.mixed\|ctx_mid.recs[0].confidence` | 同上 | 同上 |
| `.infer.multi\|ctx_low.recs[0].confidence` | `0.1353352832366127` = exp(−2) | `0.27803730045319414` |

⇒ **归因：批 M 的连接方式 `np.prod` → `np.min`**（弱连接）：

```
exp(−4) = exp(−2)·exp(−2)        ← prod 语义（两个前件各 exp(−2)）
exp(−2) = min(exp(−2), exp(−2))  ← min  语义
```

git 已证：

- `HEAD`（= `_golden_ABC.json` 的提交 `f181df6`，**2026-10-27**）版 `nets.py` 的 TSK 路径 = **`np.prod`**；
- **工作区**（批 M，**未提交**）版 = **`np.min`**；

⇒ 基线停留在批 M 之前 ⇒ **后续每轮验收都会持续误报这 3 条**。

⚠️ **本批未刷新基线**（工作区的批 M 尚未提交，不宜由本批代替它认可基线）
⇒ **建议在批 M 提交时一并刷新** `_golden_ABC.json`。

### 27.7 「零行为变化」的四层独立证据

| # | 证据 | 内容 |
|---|---|---|
| 1 | **值相同** | 三个新常量 == `0.01001` == 旧 `MIN_ACTIVATION_THRESHOLD` 的值（`git show dcfb784` 已证）⇒ 三处比较的右操作数、运算符完全未变 |
| 2 | **剔除集合未变** | 黄金比对**未报任何 `[len]` 差异** ⇒ 所有列表长度相同 ⇒ **没有规则被多剔或少剔** ⇒ 阈值行为未变 |
| 3 | **数学反证** | exp(−4)=0.0183 与 exp(−2)=0.1353 **都 > 0.01001** ⇒ 在阈值下判定结果相同（都不剔除）⇒ **阈值改名在数学上不可能**改变这两个值 |
| 4 | **归因闭合** | 3 条差异的数值形态精确吻合 `prod→min`，且 git 已证 HEAD=prod、工作区=min（§27.6） |

⚠️ **环境提示（本批踩到的坑）**：直接用系统 `python` 跑快照会得到 **75 条假差异**
（系统 numpy **2.0.0** 的 `repr(np.float64(3.0))` 带 `np.float64(...)` 包装，
而项目钉的是 `numpy==1.26.4`，其 repr 为 `3.0`）
⇒ **必须用项目 venv**（`..\.venv\Scripts\python.exe`）跑验收，
否则会把环境差异误判成代码回归。

### 27.8 本批**没有**做的事

- **没有**改任何阈值**数值**（三个值仍为 `0.01001`）；
- **没有**动 Mamdani / TSK 的推理逻辑；
- **没有**新增 `MAX_GROUP_AMPLIFY` 之类的无判据护栏；
- **没有**刷新黄金基线（理由见 §27.6）；
- **没有**实现 M-1（τ / ε / β_min 仍只是规格 + 文档登记）。

---

## 28. 批 P-5：`MIN_GROUP_SHARE` 可观测落地 + **真实规则库实测**（2026-10-28）

> 承接 §27.3 的待办：「**等真实场景数据看到分布后，再决定要不要设护栏**」
> ⇒ 本批把那个数据**取到了**，并由此得到一个**之前没发现的约束**（见 §28.5 / §28.6）。

### 28.1 本批做了什么（**零行为变化**）

| 文件 | 改动 |
|---|---|
| `fuzzy_core/models/nets.py` | 加 `import json`；在 TSK 第三层加**两条只读观测**（不改任何数值） |
| `2026-10-23-fuzzy-implementation-design.md` | §5.3.8 的 `MIN_GROUP_SHARE` / `β_min` 两行**补实测结论** |

⚠️ **本批只加观测，不改任何数值、不改任何剔除集合**（验收见 §28.8）。

### 28.2 观测点位置与日志格式

**位置**：`nets.py::NumTskRuleNet.tsk_inference` 第三层（分组归一化），
紧接 `weak_mask = group_weights < MIN_GROUP_SHARE` 之后。

**两条日志**（tag 不同、级别不同）：

| tag | 级别 | 触发条件 | 内容 |
|---|---|---|---|
| `[fuzzy.net.group_dist]` | **debug** | **每次推理一条** | `{rules, groups, min_share, min_share_group_size, median_share, max_share, threshold}` |
| `[fuzzy.net.group_share]` | **info** | **仅当确实发生剔除** | `{groups: [{param, alive, dropped, dropped_share, amplify}]}` |

**为什么这样分**：

- **分布摘要用 debug** ⇒ 生产默认不输出、不刷屏；但**需要时把日志级别开到 DEBUG 就能拿到全量分布**
  ⇒ 这就是 §27.3 说的「先观测」所需的**可复现入口**；
- **剔除明细用 info + 事件驱动** ⇒ 「真的剔了东西」是需要人看的事 ⇒ 正常级别就能抓到。

⚠️ **`group_dist` 的 `min_share` 是「剔除前」的组内占比**（在 `weak_mask` 置零之前采集）
⇒ 它直接回答「这道闸离触发还有多远」。

⚠️ **为什么用日志而不是 `extra` 通道**：`extra` **会进黄金快照**
（`_snapshot_core.py` L380 `'extra': repr(extra)`）⇒ 用它承载观测会污染基线；
而 `engine._diagnostics` 恒为 `None` ⇒ 改诊断容器不影响快照。
⇒ 日志是这里**唯一零副作用**的出口（`nets.py` 本就有 logger 惯例）。

### 28.3 真实规则库实测：**占比闸从未触发**

**输入构造**：全部 `category='parameter'` 的 RuleKeyword（**183 个**），
取值 = 论域中点；缺陷码 = 库里**全部 17 个** active `defect_code`。

| 阶段 | 扫描内容 | 场景数 |
|---|---|---|
| **A** | 17 缺陷码 × 3 档 level（中点输入） | 51 |
| **B** | 17 缺陷码 × **全局分位偏移** q ∈ {0.1, 0.3, 0.5, 0.7, 0.9} | 85 |
| **C** | 3 缺陷码 × **183 个参数逐个扰动**（q ∈ {0.1, 0.9}，其余保持中点） | 1098 |
| **D** | 3 缺陷码 × **9 个补充库**（`rule_library_code` 通道）+ 17 缺陷码 **带缺陷位置** | 44 |
| | **合计** | **1278** |

**结果**：

| 指标 | 实测 |
|---|---|
| 异常场景 / 空推荐场景 | **0 / 0** |
| `[fuzzy.net.group_dist]` 事件 | **1278**（每场景 1 条）⇒ **观测链路全程生效** |
| **`[fuzzy.net.group_share]`（剔除明细）事件** | **0** ⇒ **占比闸在 1278 个场景里一次都没触发** |
| 每组最小占比（全局） | **min 0.05325349** / median 0.25 / max 0.25 |
| **低于阈值 `0.01001` 的次数** | **0** |
| **余量倍数** | **5.32×** |
| 规则数 / 组数范围 | 12~45 条 / 3~10 组 |

⇒ **结论（回答 §27.3）**：`MIN_GROUP_SHARE` 在真实规则库上**是死代码**；
「剔除后重归一化 ⇒ 放大倍数 = 1/(1−S)」这件事 **S ≡ 0、放大倍数 ≡ 1.0**
⇒ **「放大倍数护栏」要防的事件在真实数据上不发生**。

### 28.4 为什么触发不了（**结构性解释**，不只是「没观测到」）

抓 `tsk_inference` 返回值的第 4 项（`raw_activation`）逐组看，发现 **raw 的取值空间是离散的**：

| raw | 含义 | 实测条数占比 |
|---|---|---|
| **1.0** | 缺陷档位命中（或缺陷维命中 + 工艺维 `worse` 不可判级） | 主形态 |
| **0.13533528** = `exp(−2)` | **档位错配一格**（相邻桶隶属度，§26.3 的 τ 同值） | 主形态 |
| （其它） | — | **0 条**（实测 `other = 0`） |

⇒ **组内占比 = raw_i / Σraw**，而组内 raw 只取两个值 ⇒
**最小占比 = `0.1353 / (m + k·0.1353)`**（m = 完全相符数，k = 错配一格数）

⇒ 实测形态分布（**10739 个组**）：

| 形态 | 组数 | 占比 |
|---|---|---|
| **m=0, k=2** | 5849 | 54.5% |
| **m=0, k=4** | 3949 | 36.8% |
| m=0, k=1 | 377 | 3.5% |
| **m=2, k=2** | 407 | 3.8% |
| m=0, k=3 / k=6 / k=5 | 67 / 58 / 1 | 1.2% |
| **m=2, k=4** | 4 | 0.04% |
| m=1, k=1 / k=2 | 24 / 3 | 0.25% |

⇒ **m=0 的组占 95.9%**（组内**全是错配规则**）⇒ 它们的占比恒为 `1/k`
（等比缩放不改变比例）⇒ **永远不可能跌破阈值**。
⇒ 真正敏感的只有 **m>0 的 438 个组**（4.1%）。

⇒ **要让占比闸触发**，需要 `0.1353/(m + k·0.1353) < 0.01001`
⇒ **m=1、k=1 就要 6 条以上错配规则同组** ⇒ 实测最多 6 条、且形态上是 `m=0` ⇒ **差一个数量级**。

### 28.5 ⚠️ 关键推论：**M-1 落地会把余量从 5.32× 压到 1.28×**

M-1（τ=0.1353、ε=0.10、β_min=0.20）落地后：

- **隔一档错配的规则**（μ=3.35e-4）**仍被 τ 剔**（§26.3：τ > 相邻桶隶属度 ⇒ 隔一档出局）
  ⇒ **组的 (m,k) 构成不变**；
- **相邻档错配的规则** raw 从 `0.1353` 压到 `0.1353 × β_min`；
- **相符规则** raw 不变（ε=0.10 下 β_p ≡ 1，§26.8 的二值门控结论）。

⇒ **最小占比 = `0.1353·b / (m + k·0.1353·b)`**（b = β_min）

| β_min | 触发占比闸的组数（占 10739） | 最坏余量 |
|---|---|---|
| 0.05 | **438**（4.1%） | — |
| 0.10 | **411**（3.8%） | — |
| **0.113**（§26.6 区间下端） | **411**（3.8%） | — |
| 0.15 | **411**（3.8%） | — |
| **0.20**（§26.6 推荐值） | **0** | **1.28×** |
| 0.25 / 0.292 / 0.30 / 0.40 / 0.50 | **0** | ≥ 1.28× |

**逐形态临界 β_min**（`b* = 0.01001·m / (0.1353·(1 − 0.01001·k))`）：

| 形态 | 组数 | `b*` |
|---|---|---|
| m=1, k=1 | 24 | 0.0747 |
| m=1, k=2 | 3 | 0.0755 |
| m=2, k=2 | 407 | **0.1510** |
| **m=2, k=4** | 4 | **0.1541** ← **全局最大** |

⇒ **全局零触发下界 `b₀ = 0.1541`**

⇒ ⚠️ **余量确实塌缩**：当前 5.32× ⇒ M-1（β_min=0.20）后 **1.28×**
⇒ 占比闸从「结构性死代码」变成「**薄冰**」⇒ **它不再是可以无视的东西了**。

⚠️ **推演前提（必须随数据一起读）**：

1. M-1 按 §26.3 / §26.8 实现（τ=0.1353 二值门控、β_min 一致施加于所有错配侧）；
2. **若 τ 改大到 0.20**（相邻档整体出局）⇒ k 变 0 ⇒ 组内只剩相符规则 ⇒ 占比全为 1/n
   ⇒ **闸更不可能触发** ⇒ **本推演偏保守**；
3. **若 β 按前件分别计算**（而非 `min`）⇒ 组内 raw 不再只有两个值 ⇒ 需重算。

### 28.6 ⚠️ 对 β_min 取值的新约束（**可行性约束，不是效果区间的端点**）

**性质区分（本节核心）**：

| 类别 | 判据量 | 给出 | 性质 |
|---|---|---|---|
| **效果判据**（R3，§26.6） | 错配残留占比 | `b ∈ [0.113, 0.292]` | **软锚点区间**（「2%~5%」是自设的、无外部基线）⇒ 中点 **0.20** |
| **可行性约束**（§28.5 新增） | 占比闸零触发 | `b ≥ 0.1541` | **硬判据**（实测反解，触发是确定性的） |

⇒ ⚠️ **两者不是同一个区间，不能合并后重取中点。**

⚠️ **若并入会产生荒谬链条**：

```
提高下界（约束收紧）⇒ 中点 0.20 → 0.223 ⇒ b 变大
⇒ 错配残留更多（3.48% → 3.87%）⇒ 疗效变弱
```

⇒ 即「**加一个防副作用的约束，反而牺牲了主疗效**」
⇒ **约束只做可行性检验，不参与目标值计算。**

⇒ **结论：`β_min = 0.20` 沿用**
（效果判据给出的中点 0.20 **通过**了可行性检验 `0.20 ≥ 0.1541`）。

**边际影响很小，不值得为形式一致性重算**：

| | β_min = 0.20 | β_min = 0.223 |
|---|---|---|
| 错配权重降幅（≈ 1−b，§25.3 线性） | **80.00%** | ≈77.7% |
| 错配残留贡献 | **3.48%** | ≈3.87% |
| 是否在「2%~5%」目标内 | ✅ | ✅ |

⚠️ 0.223 那两行是**按 §25.3 线性关系推的、非实测** —— 真要改就得实测。

⇒ 选 0.223 的代价 = §25 的疗效/误伤/推荐值影响面/不符:相符 **一整批数字重跑重算**，
收益仅是「区间端点同质」的形式一致性 ⇒ **不划算**。

⚠️ **遗留风险（必须留档）**：0.20 距硬边界 0.154 只有 **0.046（相对 23%）**。
以下情况会让 `b*` 漂移、须**重验** 0.20 的可行性：

- 规则库长大、单组条数变多 ⇒ `(m, k)` 形态变化；
- M-1 实现偏离「τ=0.1353 二值门控 + β 一致施加于所有错配侧」（如 β 按前件分别计算）。

⇒ **常设观测项**：「占比闸零触发」列为上线后**常设观测** ——
`[fuzzy.net.group_share]`（info 级）正是这个探针：
**一旦出现剔除事件 ⇒ 说明压过头了 ⇒ 立刻回查 β_min**（见 §28.2）。

**决策状态：已关闭**（2026-10-28）⇒ §26.6 的结论值 `β_min = 0.20` **不变**；
§26.6 区间端点 `0.113` 标注为「**不可用**」（**不是**「修正区间端点」），
另附一条**独立的可行性下界 `0.154`**。

### 28.7 护栏结论：**不需要设**（§27.3 从「暂不设」升级为「已量化：不需要」）

两条独立理由：

| # | 理由 | 依据 |
|---|---|---|
| 1 | **事件不发生** | 当前 1278 场景 **0 触发**；M-1（β_min=0.20）后仍 **0 触发** ⇒ S ≡ 0 ⇒ 放大倍数 ≡ 1.0 ⇒ 无事件可防 | 
| 2 | **即使发生也够小** | 放大倍数 `= 1 + k·0.1353·b/m` ⇒ 最坏形态（m=1, k=6, b=0.113）⇒ **1.092 < 1.2** ⇒ 连那个拍出来的 1.2 都不需要 |

⇒ **§27.3 的 `MAX_GROUP_AMPLIFY = 1.2` 维持撤掉** —— 现在有量化依据，不再只是「无判据」。

⇒ ⚠️ **但占比闸本身仍保留**（不删）：
它现在有了一个**新的真实作用** —— **它是 β_min 的护栏**（约束 β 不能压到让占比失真）。
⇒ 该作用已被 §28.5 量化 ⇒ 写进 design §5.3.8 的「判据量 / 依据」列。

### 28.8 验收

| 手段 | 结果 |
|---|---|
| `py_compile`（`nets.py` + `macros.py`） | **EXIT = 0** |
| `tests/verify_fuzzy_algo_offline.py`（**venv / numpy 1.26.4**） | **[PASS] 17 项全通过** |
| 黄金快照比对（`_golden_ABC.json` vs 新快照） | **逐条差异 3 条** ⇒ 全部是 `.infer.*.confidence` ⇒ **归因批 M**（§27.6），**非本批引入** |
| 真实库实测 | 1278 场景 / 0 异常 / 0 空推荐 |
| 临时脚本 | 一次性，跑完即删（`_dev_refs/` 下已清干净） |

### 28.9 本批**没有**做的事

- **没有**改任何阈值数值（三个常量仍为 `0.01001`）；
- **没有**实现 M-1（τ / ε / β_min 仍只是规格 + 文档登记）；
- **没有**改 `β_min` 的推荐值（仍是 `0.20`，新约束只作登记 + 列为待决策，见 §28.6）；
- **没有**删 `MIN_GROUP_SHARE`（它现在是 β_min 的护栏，见 §28.7）；
- **没有**新增任何无判据护栏；
- **没有**刷新黄金基线（理由见 §27.6）。

---

## 29. 批 M-1：**门控状态机落地**（2026-10-28）

> 本批把 design §5.3 的 M-1 从「规格 + 文档登记」变成**生产代码**。
> 三个常量按 §26.7 / §28.6 的定值结论取 **τ = 0.1353352832366127（exp(−2)）、
> ε = 0.10、β_min = 0.20**，一个都没改。

### 29.1 改了什么（生产代码 2 个文件）

| 文件 | 改动 |
|---|---|
| `fuzzy_core/macros.py` | 新增 `GATE_TAU` / `GATE_EPSILON` / `GATE_BETA_MIN` 三个常量（带判据量 / 量纲 / 依据 / 失效边界注释） |
| `fuzzy_core/models/nets.py` | ① 建网时记 `gate_specs`（参数名 / 桶索引 / 列下标）；② `tsk_inference` 第二层后加 M-1 三态计算块；③ `raw` 乘 β；④ `raw_activation` 含 β；⑤ 新增 `[fuzzy.net.m1_gate]` 观测日志 |

**内核的三个口径决策**：

| 决策 | 取法 | 理由 |
|---|---|---|
| 激活度聚合 | **min 弱连接**（批 M 已有） | 与 β_r = min 同哲学（最弱证据说了算） |
| τ 出局语义 | **AND**（任一前件 μ_used < τ ⇒ 整条规则出局） | 前件是 AND 关系；副产品：τ 剔除集 ⊇ MIN_RULE_ACTIVATION 剔除集 ⇒ 绝对闸对有可判级前件的规则永不触发 |
| β_r 聚合 | **min(β_p1..β_pk)**（方案 a） | 最弱前件说了算 |

### 29.2 实现中的三个坑（都踩过）

| # | 坑 | 现象 | 处置 |
|---|---|---|---|
| 1 | **计算块里 `break`** | τ 出局后不再算其余前件的 competition ⇒ 分不清「τ 误杀了相符规则」还是「出局的是本就不符的规则」⇒ **误杀率永远算不出来** | 计算块**不许 break**；另立 `m1_mismatch` / `m1_match` 两个分类标记 |
| 2 | **raw_activation 不含 β** | 被压到 β_min 的「档位不符」规则仍报 confidence = 1.0（而它实际只占组内 20% 权重）⇒ 前端把「把握不大」显示成「满把握」 | `raw_activation = a_i · β_i`（含 β，不含 priority / spec_weight） |
| 3 | **组内占比与置信度混用一套权重** | w = raw/(组内 Σraw)，raw 含 priority × spec_weight；confidence = Σ(a·β)/n ⇒ 两者权重集合**不同** | 两个口径分开实现并在注释里写明；§29.3 的数字按各自口径统计 |

### 29.3 真实库预演（§24.2 口径 + 5 档 shift）—— **逐位复现 §25.3**

预演脚本按 §24.2 的口径造工况（缺陷维 = 档位桶中心；工艺参数维 = **该场景内被引用最多的档位**的桶中心 + shift×σ），baseline 走「τ=0、β_min=1」旁路（与「未注入 M-1」逐位等价）。

| 指标 | §25.3 预期 | 实测（51 场景 × 5 档 shift） |
|---|---|---|
| 不符权重降幅（干净口径） | 80.00% | **80.0000001%**（5 档 shift **恒定**） |
| 相符权重削减 | 0.00% | **0.00%**（全谱） |
| 不符:相符（baseline） | 0.1804 → 0.2498（漂 38.5%） | **0.180447 → 0.249835**（漂 38.46%） |
| 不符:相符（M-1） | 0.0361 → 0.0500 | **0.036089 → 0.049967** |
| 三态（未/边/明） | 730 / 524 / 393 | **730 / 524 / 393**（524 条**全部**落在「归属不一致」子情形，「分不清」0 条） |
| 组内占比（baseline → M-1） | 15.05% → 3.47% | **15.047% → 3.469%** |
| 推荐值影响面 | 414 点 / 值变 363 | **414 / 363** |
| 方向变化 | 0 | **0** |
| 占比闸剔除事件 | 0 | **0**（最小占比余量 **1.28×**） |
| 误杀率（假阴性） | 0.00% | **0**（相符规则 393 条，出局 0 条） |

⇒ **§25.3 的预测表被逐位证实**（误差 ≤ 1e-6，为浮点尾数）。

⚠️ **一个新数据点（§24.4 没有的）**：ε=0.10 配置的最大相对变化 = **0.7208%**
< ε=0.30 配置的 0.928%（§24.4）⇒ **零误伤的代价反而更低** ——
因为 ε=0.30 的误伤本身会带来额外的权重扰动（§24.3 的「相符均β = 0.716」）。

### 29.4 ⚠️ 附带发现：疗效观感**对工况口径高度敏感**

同一份代码、同一批规则，只把「工艺参数维取值」从 §24.2 的「众数对齐」改成「全局中位桶」：

| 口径 | 相符规则数 | 不符:相符（baseline → M-1） | 组内占比（baseline → M-1） | 推荐值变化 |
|---|---|---|---|---|
| **§24.2 众数对齐** | **393** | 0.1804 → 0.0361 | 15.05% → **3.47%** | 363 / 414 |
| 全局中位桶 | **33** | 5.118 → 1.024 | 93.66% → **92.80%** | **9** / 414 |

⇒ **「疗效 80%」这个观感只在「众数对齐」口径下成立**。
「众数对齐」是**人为造出「相符规则作分母」的对照场景**（把每个参数的工艺维钉在
规则库里最常引用的那一档 ⇒ 造出大量「档位相符」规则作对照）⇒
**汇报时必须同时给出口径**，否则「93.66% → 92.80%」会被读成「M-1 没用」。

### 29.5 黄金快照差异：**分层**归因（批 M vs M-1）

| 对比 | 逐条差异 | 归因 |
|---|---|---|
| `_golden_ABC.json` vs **M-1 旁路**（τ=0、β_min=1） | **3** | 批 M 的 min 弱连接（全是 `.infer.*.recs[].confidence`）—— §27.6 已登记 |
| M-1 旁路 vs **M-1 开启** | **86** | M-1 层 |
| `_golden_ABC.json` vs **M-1 开启** | **86** | 两层叠加（批 M 的 3 条已被 M-1 覆盖） |

⚠️ **集合运算（关键）**：`ABC↔NOW` 与 `BYPASS↔NOW` 的**差异路径集合完全相同**
（各自减去对方后均为**空集**）⇒ **86 条全部由 M-1 引入**，批 M 的 3 条是其中的**子集**。

**86 条的结构化归因**：

| 差异路径类型 | 条数 |
|---|---|
| `results[].raw_activation` | **42** |
| `results[].group_weight`（组内占比） | **29** |
| `recs[].confidence` | **15** |
| **结构类**（条数变化 / 字段缺失 / 键增删） | **0** |

⇒ **零结构差异**（无条数变化、无字段缺失、无参数换人）。
且因为 `walk()` 逐叶比对，**「只有 confidence 变了」是穷尽性结论**：
`recs[]` 里除 `confidence` 外的每个字段（`param_name` / `recommended_value` /
`current_value` / `direction` / `reason` / `source`）**逐位相同**；
`results[]` 里除 `[1]`/`[3]` 外的 `[0]`（规则串）/ `[2]`（结论值）**逐位相同**。

**抽样核对**：`five_level|1.0|ctx_mid` 的 raw_activation `0.1353352832366127 → 0.027067056647322542`
（**精确 ×0.2** = β_min）；结论值 `{'inj_pres_1': 5.0}`、推荐值 **105.0**、方向 **increase** **全部不变**
⇒ 归因链闭合。

⇒ **意外回归 = 0**。

### 29.6 ⚠️ 附带发现：13 场景对拍资产**在批 M 之后就已经失效**

`_dev_refs/_scen13_check.py` 是「独立参照系 vs 生产 vs 手算期望值」三方对拍资产
（§10.6 的对拍表由它生成）。本批跑它 ⇒ **14 个用例 FAIL 8 个**。

**根因**：它的参照系与期望值**同时落后两层**——
① 激活度用**乘积**（生产在批 M 改成 min 弱连接）；
② **完全没有** M-1 的三态与 β（生产本批才加）。
⇒ 8 处 FAIL = 3 处（批 M 遗留）+ 5 处（M-1 引入）。

⚠️ **纪律教训**：**批 M 落地时没有同步更新这个回归资产** ⇒ 它在批 M 之后就已经是坏的
（只是没人跑）⇒ **回归资产的期望值必须与内核口径同时更新**，否则它只会「在没人跑的时候坏掉」。

**处置**（本批一次性对齐两层）：

| 项 | 处置 |
|---|---|
| 参照系 | 改 min 弱连接；加 M-1 三态（μ_used / μ_alt / competition / τ 出局 / β_r = min）；`raw` 乘 β；`raw_activation` 用 `a · β` |
| 隶属度公式 | 与生产**逐位一致**（`-((x−c)²)/(2σ²)`，不是 `-((x−c)/σ)²/2`）—— 两种写法可能差 1 ULP，而 **τ 的边界恰在 exp(−2)** 上 ⇒ 参考系用另一种写法会在 τ 边界上判出不同结果 |
| 期望值 | 8 处置信度按新口径重算（推导写在每条用例的注释里）；**推荐值 / 方向全部不变** |
| 结果 | **14 / 14 通过**（期望 == 参照系 == 生产，三方逐位一致） |

### 29.7 验收

| 手段 | 结果 |
|---|---|
| `pytest process/algorithms/fuzzy/fuzzy_core/tests -q` | **35 passed** |
| `pytest tests/test_fuzzy_recommendations.py tests/test_fuzzy_field_report.py tests/test_fuzzy_machine_limits.py -q` | **19 passed** |
| `_scen13_check.py`（13 场景三方对拍） | **14 / 14 通过**（EXIT=0） |
| 其余 13 个验收脚本（`_verify_*` / `tests/verify_*`） | 全 EXIT=0 |
| 黄金快照（`_golden_M1.json` vs 新快照） | **逐条差异 0（PASS）** |
| 真实库预演（51 场景 × 5 档 shift） | 逐位复现 §25.3（§29.3） |

⇒ **黄金锚点刷新**：`_golden_M1.json` 取代 `_golden_ABC.json` 成为**现役锚点**
（`_golden_ABC.json` 保留作历史留痕，与 `_golden_E26.json` 同例）——
理由同 §10.8：**已批准的设计变更**（批 M + M-1 两层）**全部归因完毕、意外回归 = 0**
⇒ 继续拿旧锚点当逐位回归锁，只会像 §27.6 那样**每轮误报 89 条**。

### 29.8 本批**没有**做的事

- **没有**改三个阈值的取值（τ = exp(−2) / ε = 0.10 / β_min = 0.20，与 §26.7 / §28.6 一致）；
- **没有**删 `MIN_RULE_ACTIVATION`（它现在对**有可判级前件**的规则已是冗余，但对**无前件**的规则仍是兜底 ⇒ 保留）；
- **没有**删 `MIN_GROUP_SHARE`（它是 β_min 的护栏，见 §28.7）；
- **没有**新增任何无判据护栏；
- **没有**改推荐值 / 方向的语义（只改权重与置信度口径）；
- **没有**把 `boundary` 标记透出到前端（本批只做内核 + 观测；design §5.3.6 的前端提示仍是遗留项）。

### 29.9 遗留

- **「目标档位冲突」标记**（§23.5 / design §5.5）仍未覆盖；
- **`boundary` 标记的前端透出**（design §5.3.6）未做 —— 本批只有内核三态与观测埋点；
- **M-1 的在线证伪监控**未接进巡检（`[fuzzy.net.m1_gate]` 日志已具备全部字段，待定是否做定时读取）；
- **规则库长大后**须重验 β_min 的可行性下界 0.154（§28.6 已标注：0.20 距 0.154 仅 0.046）。

---

## 30. 批 Q：选库口径 +「通用」语义改造（2026-10-29）

> **批次号说明**：本文的批次序列已用到 **P / P-5**；**N 已被 2026-10-28 的 M-2（冲突标记）批次占用**
> ⇒ 本批取下一个未用字母 **Q**。
> ⚠️ 本批**只改取数与判定口径**，**不动任何权重公式** ⇒ 内核数值面零变化。

### 30.1 起因：两个 P0 叠在一起

**① 自动选库必然落空**（§3.6 / optimize-contract §16.5 点 1，2026-10-28 已定性）——
旧实现用「产品类别 → 库编码」映射表（`RuleService.product_to_library_codes`）
展开候选，而那张表指向的 code（`packaging` / `auto_parts` / `medical`）
**在库里根本不存在**（实际库码是 `base` 与 `R2023*` / `R2024*` 这类编号）
⇒ 候选必然落空 ⇒ 未显式指定库时**永远只加载 `base` 库**
⇒ 9 个补充库共 1058 条规则（**占全库 64%**）从不参与推理。

**② 155 条「通用」规则被永久判冲突** —— 全库实测（2026-10-29）：
`R20240702164137` 的 155 条规则 `product_category` **全部是字面值「通用」**
（**不是 NULL**）⇒ 按旧口径（NULL 才算通用）这批规则
**在任何上下文下都被判为「产品类别冲突」而永不生效**。

⇒ 两个缺陷必须**一起**修：**只改选库口径** ⇒ 那 155 条仍被冲突排除；
**只改「通用」语义** ⇒ 其余 903 条补充库规则仍然进不来。

### 30.2 改动落点

| 文件 | 改动 |
|---|---|
| `library/assembly.py` | `RuleAssembler.library_code_candidates`：**未指定 ⇒ 返回 `None`**（= 全量）；`select_libraries` 增「全量模糊库」分支（`is_active` + `library_type=='fuzzy'`），**显式口径原样保留**（指定库 + `base` 兜底） |
| `library/rules.py` | 新增 `RuleQueryService.get_all_libraries()`（`filter(is_deleted=False).order_by('id')`，**与文件来源 `export_libraries` 同内容同顺序**）；`get_library_index(codes=None)` ⇒ 全量索引；**删除** `RuleService.product_to_library_codes` 与 `major_category_map` |
| `library/semantics.py` | 新增 `GENERIC_LABELS = {'通用'}` + `is_generic_label()`；`matches_context` / `resolve_specificity` 改按「NULL **或** 字面值『通用』」判通用 |
| `library/repository.py`、`library/files/repository.py`、`library/files/loader.py` | docstring 与口径对齐（未指定 ⇒ 全量；同码只留第一条 `setdefault`） |
| `library/files/tests/test_file_source.py` | 选库口径用例（未指定 ⇒ 全量模糊库 / 显式 ⇒ 只用它 / 停用库排除） |
| `examples/README.md` | 「已知边界」补选库口径变更说明与「哪些库真正改变了数值」 |
| `examples/export_case.py` | 案例描述文案去掉「自动选库在本上下文必然落空」的过时陈述（**仅文案**，不改期望值） |

### 30.3 四个关键决策

**① 未指定 ⇒ 全量模糊库，适用性下放到规则级判定**

选库从「按产品类别挑库」改成「把库全端上来，让**规则自己**说明适不适用」——
判据是规则自身的 `polymer_abbreviation` / `product_category` 标注
（`matches_context` 冲突硬排除 + `resolve_specificity` 特异级打分）。
这与 `specs.py` 对 `product_category` 的原始定义一致：
「规则库精确筛选键（specificity 1/3）… 填了能命中高特异级规则，不填退到默认规则」
⇒ **适用性本来就是「规则 × 上下文」的关系**，用一张写死的映射表提前做掉，
既是逻辑写死，也让规则库无法按产品灵活增删。

**② 「通用」双向同义：NULL 与字面值「通用」都算「该维无具体信息」**

规则标注里的「通用」**不是「NULL 没填」**，而是**明确写了「适用于所有产品/材料」**
—— 业务含义与 NULL 相同（该维不设限），但取值不同。
⇒ 判定统一走 `RuleService.is_generic_label`（NULL **或** 字面值「通用」）。
⚠️ **规则侧与上下文侧同义**：上下文该维写「通用」= 当前模具没有明确产品大类
⇒ 该维**不加限制**（「未指明」≠「不适用」）。

**③ 规则侧写「通用」**不算**匹配**

规则写「通用」= 该规则**没有**针对某个具体产品/材料
⇒ 不能因为上下文里恰好也写了「通用」就说它命中了产品维度
（否则 155 条「通用」规则会被误标成产品专用规则，特异级从 4 假升到 3）。
同理，规则写「通用」而上下文写了具体产品（如「酒瓶」）⇒ 也不算匹配
—— 规则没有针对酒瓶，只是**不冲突**。

**④ 显式指定仍「只用它」（+ `base` 兜底）**

用户已经明确圈定了范围，就尊重用户的指定，不给他掺别的库。
`base` 作为通用兜底追加在最后，且要求 `library_type=='fuzzy'`（专家库不能当模糊库兜底）。
⇒ 两条口径（显式 / 未指定）都按 `priority` 降序稳定排序。

### 30.4 量化证据（开发库实时实测，2026-10-29）

复现入口：`_dev_refs/_stat_candidates.py`（第 1~4 节）。

| 指标 | 改造前 | 改造后 |
|---|---|---|
| 候选规则集（17 缺陷码 × 6 上下文） | **3510** | **4771（+35.9%）** |
| 选中的库（未指定库） | **1**（`base`） | **10**（`base` + 9 个 `R2023*`/`R2024*`） |
| 特异级分布 | 恒 `{4}` | 出现 **{2} / {3}** |

- SHORTSHOT 裸上下文：`base` 30 条 + 9 库各 9 条 = **109 条**；
- SHORTSHOT + `poly=PP`：61 条，特异级 `{2: 16, 4: 45}`；
- SHORTSHOT + `prod=碗`：44 条，特异级 `{3: 9, 4: 35}`；
- 增幅最大的缺陷（裸上下文）：`WELDLINE` 36→96（+60）、`GASVEINS` 45→102（+57）、`FLASH` 39→80（+41）。

⇒ **附带效果：批 Q 是第一次让 `specificity` 乘数真正起作用**。
`specificity_weight`（1→1.0 / 2,3→0.5 / 4→0.25）在改造前因特异级**恒为 4**
而恒等于 **0.25**（零区分度）⇒ 现在才有 `{0.5, 0.25}` 两种取值（相对差 2×）。

### 30.5 验收

| 手段 | 结果 |
|---|---|
| `_dev_refs/_verify_sources_parity.py`（双来源对拍） | **EXIT=0，失败项 0** —— 选库 7 组 db=file 逐条一致（未指定 ⇒ 两边都 10 库；显式 ⇒ 指定库 + `base` 兜底；显式库 + `prod=通用` ⇒ 两边都 `[base, R20240702164137]`） |
| `pytest -q` | **71 passed** |
| 黄金快照 `_golden_M1.json` vs 新快照 | **逐条差异 0（PASS）** —— ⚠️ **但该锚点对选库口径没有覆盖能力**：`_snapshot_core.py` 走 `FakeRepo`、规则集在脚本内自带，**不连库** ⇒ 差异 0 只证明「内核数值面未被触碰」，**不**证明选库行为未变（那个由双来源对拍 + 候选集统计证明） |
| `_dev_refs/_stat_candidates.py` | **EXIT=0** —— 旧 3510 → 新 4771（+35.9%）、10 库、特异级 {2}/{3} |

### 30.6 本批**没有**做的事

- **没有**改权重公式：`raw = μ × priority × specificity × β` 一字未动 ⇒ 数值面零变化；
- **没有**动 `priority` 的取值（全库仍是 1646 条恒为 1 ⇒ 零区分度，见 §31.1 N-1）；
- **没有**做业务侧的「库 ↔ 产品」映射表（批 Q 只把**算法侧**的口径修对；映射口径要业务定，见 §31.2 S-6）；
- **没有**回改已导出的案例 JSON（`examples/data/*.json` 的 `rules` 仍是导出时刻的 `base` 库快照）；
- **没有**把 `rule_refs`（规则依据）透出到输出；
- **没有**动 `specs.py` 的层 0 反向依赖（C8）。

### 30.7 遗留

- `library/rules.py::get_methods` 的 docstring 曾写「『通用』一律用『该维为 NULL』判定」⇒ **本批已同步修正**（改为「NULL **或** 字面值『通用』」，并指明统一走 `RuleService.is_generic_label`）；
- `examples/data/*.json` 里已导出案例的 `description` 仍含旧文案（**导出器已改，存量数据未回改**）—— 需要时用 `export_case.py` 重新导出。

---

## 31. fuzzy 剩余开口台账（2026-10-29 收口）

> **怎么读**：一行 = 一个开口。
> **性质**列决定它能不能单独推进；**前置**列写「要动它，先得有什么」；
> **风险**列写「动错了会怎样」。
> **复现入口**：`_dev_refs/_stat_candidates.py` 第 4 节（权重与结论形态体检）/ 第 5 节（论域下界体检 + 规则引用面）。
> ⚠️ 本台账只登记「**还没做的事**」，**不代表都要做** —— §31.3 那两项是用户明确搁置的。

### 31.1 数值语义型（动它就会改输出数值）

| # | 项 | 现状（实测） | 性质 | 前置 | 风险 | 出处 |
|---|---|---|---|---|---|---|
| **N-1** | **`priority` 零区分度** | 全库 `RuleMethod.priority` **1646/1646 恒为 1**（取值种类数 = 1）。它是权重链的一等乘数（`nets.py`：`raw = μ × priority × specificity × β`）⇒ 乘上去等于没乘；剩余两处用途（去重次级判据 `prefer_candidate`、排序次级键）也因此零区分度 | 需业务给分级口径（roadmap §6 的「L1=10 / L2=5 / L3=4 / L4=1」协议**从未落地**） | 业务定 priority 分级规则 | **高** —— 一旦启用直接进组内占比归一 ⇒ 所有输出数值都变 | roadmap P0-4 / §7 D4 |
| **N-2** | **百分比结论与绝对值混组** | 9 条百分比结论规则落在 **4 个参数组**：`CT` 3+86、`IP0` 3+154、`IV0` 2+256、`MSR0` 1+75 ⇒ **4 组全部混组**。内核对百分比规则的**单条处理是对的**（转成比例值 + 输出层乘当前值），但同一参数组内两类规则进**同一套组内占比归一 + 加权平均** ⇒ 输出是「减 2 个单位」与「减 30%」的混合值，**业务上无法解释为任一语义** | 语义决策：百分比规则是否单独分组 / 单独成层 | 工艺员给口径 | 中（改法会改数值） | 本轮实测（`_stat_candidates.py` 第 4 节） |
| **N-3** | **论域按参数类型分场景构造（设备 / 材料 / 产品三维）** | **问题已重新定义**（2026-10-29 用户口径）：原表述「经验域下界填多少」不成立 —— 不同类型的参数**论域来源本就不同**。实测覆盖度：①**设定值类已接**面板最大设定值（下界 0），7 族中 6 族正常；②**温度类完全没接材料温度**（`polymer_info` 的 6 个温度字段在 fuzzy 包内**零消费**），且 `NT`/`ET` 经验域 `[0,50]` 与实测 123~275℃ 差一个量级 ⇒ **恒判顶档**；③**时间类是硬编码经验域**（`PT0`/`CT`/`IT` 共 **329 条**规则），与设备/材料/产品全无关；④**兜底已有四层**（算法不会 500 已成立），但必填设备字段缺失仍**抛 400 拦人** | 业务/工艺口径已给方向，**剩 3 处待拍板**（§32.5） | 材料**类别**兜底表 + 产品维度输入 | 中（改论域会改激活度与档位归属 ⇒ 改数值） | **§32**（本轮只读取证，未落代码） |
| **N-4** | **D6 缺陷档位是否额外加权** | 现状 = (a) 不加权：档位已进推理网络（隶属度表达「越严重越激进」）、不再硬过滤，但**不额外乘档位权重**（结论值里已编码档位） | **业务语义**决策 | 工艺员拍板 | 中 | roadmap P1-1 / §7 D6 |
| **N-5** | **「目标档位冲突」标记** | 已落地的是「同组内方向不一致」的冲突标记（`recommendations.py::build_conflict_view` + `FuzzyRecommendation.conflict`，**只加标记不改数值**）；**「目标档位不一致」仍未覆盖** —— 数值层结论是绝对量，没有档位概念 | 语义设计（要给数值结论补档位概念） | 先定「目标档位」怎么表达 | 中 | §23.5 / design §5.5 / §29.9 |

### 31.2 结构 / 呈现型（不改数值，改契约或展示）

| # | 项 | 现状 | 性质 | 前置 | 风险 | 出处 |
|---|---|---|---|---|---|---|
| **S-1** | **`boundary` 前端透出** | 内核已有三态与 `boundary` 标记，但**没进对外契约**、前端看不到 | 前端 / 契约 | 对外契约扩容拍板 | 低 | §29.9 / design §5.3.6 |
| **S-2** | **M-1 在线证伪监控未接巡检** | `[fuzzy.net.m1_gate]` 日志字段已齐全（含 τ/ε/β_min/competition/三态计数），但**没有定时读取** | 可观测性 | 定巡检口径与阈值 | 低 | §29.9 |
| **S-3** | **`rule_refs` 恒空** | 输出**不携带规则依据**，工艺员看不到「依据哪几条规则」（案例里能看到 `rules[].source_ref`，引擎产出里没有） | 输出契约 | 契约扩容拍板 | 低 | optimize-contract §16 / examples README |
| **S-4** | **D5 检查类建议展示位置** | 检查类结论（`X_adjust_请检查…`）一路保留到前端，剩「放哪一组」的前端问题 | 前端 | 前端拍板 | 低 | §7 D5 / §4.6 |
| **S-5** | **D7 多缺陷业务优先级** | 机制已就位（批 G：`defect_selection.py` 单一真相源 + 决策级留痕 + 策略接口预留）⇒ 接入只需新增一个策略类；**业务优先级规则未定** | 业务语义 | 业务定优先级 | 低 | §7 D7 / §5 C9 |
| **S-6** | **B10 数据侧 `rule_library_code` 入口** | 算法侧通道已通（§15 + 批 Q）；**`overrides.rule_library_code` 没有填写入口**（前端/建档流程）⇒ 且补库规则下的推荐值**未经工艺验证** | 业务 / 前端 | 前端入口 + 工艺验证 | 中（显式指定会改变命中集合） | §8 / §21.3 |
| **S-7** | **`specs.py` 层 0 反向依赖（C8）** | `specs.py` 属层 0 却 `from ..field_contract import` ⇒ 层 0 依赖上层包。**只标注、未动代码**（批 L-8，用户拍板）；三个函数都是纯函数、无副作用、无循环依赖 ⇒ **不影响算法结果**，只影响分层纯度 | 跨包重构 | 另开一轮（要牵动 `empirical` 等包） | 中 | §5 C8 / §21.2 |
| **S-8** | **案例集覆盖太窄** | `examples/` 只有 **1 个案例**（PP 包装件 · 短射低档），且只覆盖 **numeric 层**；提示层、多缺陷、多产品类别场景无案例；案例的 `rules` 还是**旧口径快照**（只有 `base` 库） | 回归资产 | 按 examples README 的案例格式补造 | 低 | optimize-contract §16 / examples README |
| **S-9** | **M-3 E5 矩阵替换** | `connected_matrix` 仍是 numpy 矩阵；是否换 dict + 循环取决于收益口径（性能？可解释性？）—— **口径不定 ⇒ 改法不定** | 可延后 | 先定收益口径 | 低 | §21.2 |
| **S-10** | **位置条件语义表达不出来** | `AND DLUNDERSIZE1_high` 这类「位置」前件在算法里表达不出来：实测口径是「位置不匹配时该维度**不作门控**」⇒ **规则照样命中**，作者意图无法表达 | 语义设计 | 先定「位置不匹配」是排除规则还是不作门控 | 中（改则改命中集合） | §19.10 / §21.2 |

### 31.3 已暂缓（用户明确搁置，不是待办）

| 项 | 用户口径 |
|---|---|
| **自动整理规则** | 2026-10-28：「暂时不需要考虑，我们重点还是在当前算法的实现上」⇒ `fuzzy-level-semantics-design.md` 的 D1 / D4 仍是该需求展开时的**硬约束** |
| **`fuzzy_level` 可观测性** | 2026-10-28 明确暂缓。待办内容本身是：改 `fuzzy_level` 时应提示「引用该关键字的 N 条规则门槛会变」——**当前完全静默**（optimize-contract §17.4 第 2 条） |

### 31.4 台账本身的两个坑

1. **编号歧义**：本文 §7 的 **D5 = 「检查类建议展示位置」**，而 §21.3 与 `fuzzy-level-semantics-design.md` 的 **D5 = 「`fuzzy_level` 可观测性」** ⇒ **两个 D5 不是同一件事**（后者已暂缓）。引用时务必带出处。
2. **§6 批次表不能当现状读**：§6 表的 B2 / B5 / B6 / B7 / B9 长期未打勾（实际已被批 A / 批 I / 批 F / 批 J-3 覆盖）⇒ **已于 2026-10-29 回填**；B10 标 ⚠️（口径已改、业务侧未做）。
   ⇒ **现状以 §30 / §31 与代码为准**。

---

## 32. N-3 取证：论域按参数类型分场景构造（2026-10-29）

> **本节定位**：N-3 原表述是「经验域下界填多少」（roadmap P0-2）。2026-10-29 用户口径把它换成了**另一个问题**：
>
> > 「你在考虑论域问题的时候，实际上参数是面临集中不同场景的」——
> > 设定值类、温度类、时间类的**论域来源本就不同**；而且「**算法是否准确是参数是否准确的问题，
> > 但是算法能否运行，需要的是兜底机制**」。
>
> ⇒ 本节只做**只读取证**（**未改任何算法代码、未改任何数据**），把四类参数的现状覆盖度、
>   缺口、可落地的路径摆清楚，**待拍板后再决定动不动**。
>
> **复现入口**：`_dev_refs/_stat_candidates.py` 第 5 / 5b 节。

### 32.1 用户口径 → 四类参数 → 四个论域来源

| 类 | 关键词（`keyword_type`） | 数量 | 下界 | 上界 | 缺数据时 |
|---|---|---|---|---|---|
| **① 设定值类**（面板可设：压力/速度/转速） | pressure 21 / speed 17 | 38 | **0** | **面板最大设定值**（`max_set_*`） | 设备值缺失 ⇒ 经验域 |
| **② 温度类** | temperature 83 | 83 | **材料温度下限** | **材料温度上限** | 材料值缺失 ⇒ 材料**类别**兜底表 ⇒ 经验域 |
| **③ 时间类** | time 20 | 20 | **0** | **随产品变**（薄壁短、厚壁长） | 产品数据缺失 ⇒ 经验域 |
| **④ 位置/枚举类** | position 163 / force 1 / length 6 | 170 | 0 | 经验域 | 经验域 |

> ⚠️ 「下界很多其实是 0」已被实测**完全证实**：311 个关键词中 `range_min > 0` 的 **65 个，
> 100% 是 `parameter_kind='setpoint'`（面板设定值）**；其余 246 个（实际值 / 缺陷 / 缺陷位置）下界全是 0。
> 温度类 83 个里有 60 个下界非 0（`BT1~BT9` / `HRT0~HRT49` / `MT`）—— 但这 60 个里
> **只有 2 个被规则引用**（`BT1` 3 条、`MT` 3 条）⇒ **绝大部分是元数据空转**。

### 32.2 逐类取证

#### 32.2.1 设定值类：**基本已经做到了**，只剩一个破口

现有机制（批 D / 批 I）：`specs.PARAM_LIMIT_FIELDS`（7 族）+ `engine._apply_device_bound`
**换上界 + step 等比缩放**，下界保持 `RuleKeyword.range_min`。

| 族 | 设备面板上限（库里 4 台） | 经验域 | 状态 |
|---|---|---|---|
| `IP` 注射压力 | 140 ~ 160 ~ 180 | [0, 200] | ✅ 论域收窄到设备值 |
| `IV` 注射速度 | 90 ~ 110 ~ 130 | [0, 120] | ✅ |
| `PP` 保压压力 | 140 ~ 160 ~ 180 | [0, 140] | ✅ |
| `PV` 保压速度 | 45 ~ 60 ~ 70 | [0, 100] | ✅ |
| `MSR` 螺杆转速 | 130 ~ 160 ~ 220 | [0, 200] | ✅（部分机台 >200 ⇒ 触发「设备能力 > 经验共识」warning） |
| `MP` 计量压力 | **10 ~ 10 ~ 10**（n=3） | [0, 200] | ✅ 但设备值录入偏低，**数据层要核** |
| `MBP` 计量背压 | **8 ~ 8 ~ 8** | **[10, 50]** | ❌ **破口** |

**唯一破口 = `MBP`（计量背压）**：经验域下界 **10** > 设备上限 **8**
⇒ 触发 `engine.py:542` 的降级保护（「设备上限不大于经验下界 ⇒ 保留经验论域」）
⇒ **论域永远卡在 [10, 50]，设备实测值根本进不来**。
佐证：材料主数据 `recommend_back_pressure` = **4 / 5 / 6**（PP / ABS / PA6-GF30）⇒ **3/3 低于经验下界**；
实测工艺参数 **58/58 条**落在下界外。
⇒ 与用户口径「设定值类最小值默认 0」**直接冲突**。

#### 32.2.2 温度类：**完全没接材料温度**，且 `NT`/`ET` 的经验域与真实量级差一个数量级

**接线状态**：`specs.OPTIMIZE_POLYMER_INFO_FIELDS` **已声明** 6 个温度字段
（`min/max/recommended_melt_temp`、`min/max/recommended_mold_temp`），但 **fuzzy 包内零消费**——
`engine.py` 只读 `polymer_info.abbreviation`（L195）一处
⇒ **材料温度进了接口、没进算法**。

> `specs.py` L648 的 TODO 1 早已登记这件事，当时的结论是「温度类**没有设备上限字段**
> （HMI 不提供）⇒ 论域只能来自 `RuleKeyword` 权威元数据」。
> ⇒ **这个结论现在需要更新**：温度类的上界确实不该来自设备，但该来自**材料**。

**量级错配（硬证据）**：

| 关键词 | 经验域 | 实测（n=59） | 材料主数据 | 后果 |
|---|---|---|---|---|
| `NT` 喷嘴温度 | **[0, 50]** | **123 ~ 250 ~ 275** | 熔体 200~290 | **恒判顶档**，档位零区分度（**31 条**规则） |
| `ET` 下料口温度 | **[0, 50]** | 无对应列 | 熔体 200~290 | 同上（**10 条**规则） |
| `MT` 模具温度 | [20, 100] | 无对应列 | 模温 **20~80 / 40~80 / 70~120** | PA6 上界 120 > 经验上界 100（**3 条**） |
| `BT1` 料筒温度一段 | [150, 350] | 220 ~ 250 ~ 270 | 熔体 200~290 | 域内 ✅ |

⇒ 温度类有引用的关键词共 5 个（`BT` 167 条属历史遗留，**按用户口径抛弃**），
实际会受影响的 = `NT` 31 + `ET` 10 + `MT` 3 + `BT1` 3 = **47 条**。

> 📌 **用户口述的「20~80」正是库里 PP 的模温区间**（`min_mold_temp=20` / `max_mold_temp=80`）
> ⇒ 「温度用材料推荐成型温度」在**数据层是现成的**，不是要新采集。

#### 32.2.3 时间类：**论域是硬编码的**，与设备 / 材料 / 产品全无关

20 个时间类关键词，**下界全是 0** ✅（用户口径天然成立）。
有引用的 4 个 = **329 条规则**：

| 关键词 | 经验域 | 引用规则 |
|---|---|---|
| `PT0` 保压时间一段 | [0, 10] | **147** |
| `CT` 冷却时间 | [0, 120] | 93 |
| `IT` 注射时间 | [0, 20] | 85 |
| `PT1` 保压时间二段 | [0, 8] | 4 |

**产品维度输入：数据层目前是空的**

- `ProcessCondition.process_context` 的 model help_text 里定义了 `ave_thickness` / `max_thickness` /
  `product_weight` / `max_length` / `gate_type` …（**字段通路已存在**），
  但实测 **49 条工艺条件、48 条有值，这 48 条的 JSON 里只有 4 个键**
  （`injection_index` / `interface` / `process_set` / `shot_index`）⇒ **壁厚、重量一条都没填**。
- `masterdata_mold` 里有 `target_cycle_time` / `total_injection_weight` / `shot_count` / `cavity_count` /
  `product_category` ⇒ **`target_cycle_time` 是当前唯一在库、在契约里、且真反映产品厚薄/复杂度的信号**
  （`specs.OPTIMIZE_MOLD_INFO_FIELDS` 已声明它，只是 `engine.py` 目前只读 `product_category`）。
- ⚠️ `mold_thickness` 是**模具厚度**，不是产品壁厚 ⇒ 不能当「薄壁 / 厚壁」用。

#### 32.2.4 兜底（保「算法能运行」）：**已有四层**，但有一处**反向**机制

现状四层：

1. `engine.py::_build_field_context` 的 `FIELD_SOURCE_GUESSED` 分支 —— 元数据缺失 ⇒ 推测论域
   （设备实测值 → 当前值 × 2 → 0.01），下界 0；
2. `library/adapters.py` —— `min_val >= max_val` ⇒ **跳过该关键词**（不报错）；
3. `fuzzy_core/models/features.py` —— 区间倒挂 ⇒ σ=0 ⇒ 隶属度恒 0/nan，**只告警不抛**；
4. `engine.recommend` 异常边界 —— 任何异常 ⇒ **降级为空推荐**（不炸整条 optimize 链）。

⇒ **「算法不会崩、不会 500」已成立** ✅

⚠️ **反向的一处**：`specs.OptimizeDataValidator` 对**必填等级**设备字段缺失 ⇒ 抛 `ValueError`
⇒ service 转 **400 拦人**（2026-10-27 用户口径：「必须用设备值，设备值没有就报错」）
⇒ **与 2026-10-29「算法能否运行需要兜底机制」方向相反** ⇒ **必须拍板**（§32.5 ①）。

### 32.3 ⚠️ 一处定性更正：论域外**不等于**隶属度 0

隶属度是**桶中心制高斯**（`fuzzy_core/models/features.py`：`σ = span/(2*(lvl-1))`、
`means = bucket_centers(...)`、`width = 2σ`）⇒ **无限支撑**
⇒ 实测影响是「**激活度打折**」，不是「规则不激活」：

| 关键词 | 经验域 | 实测 | 低于下界 | μ_低档 | 引用规则 |
|---|---|---|---|---|---|
| `MBP0` | [10, 50] | 3 ~ 5 ~ 6 | 58/58 | 0.375 ~ 0.726（**峰值桶仍是「低档」⇒ 档位归属不变**） | **182 条** |
| `VPTL` | [30, 60] | 13.92 ~ 27.04 ~ 37.1 | 50/58 | 0.000 ~ 0.990 | 82 条 |
| `BT` | [0, 50] | 220 ~ 250 ~ 270 | 0/58 | **0.000**（⇒ 恒不命中；**已按用户口径「历史遗留，抛弃」处理，不再列开口项**） | 167 条 |

⇒ 改论域的**真实影响面**是「激活度 + 档位归属」，改之前要按实测值算，不能按直觉估。
⚠️ 已实测：把 `MBP0` / `VPTL` 下界改 0 会**同时**修好 `VPTL` 卡死**和**翻转部分档位归属
⇒ 必须由工艺确认「低档的定义区间」再动。

### 32.4 落地方案草案（**待拍板，本轮不落代码**）

**原则**：论域 = f(参数类型, 设备, 材料, 产品)；**准确靠数据，可运行靠兜底**
⇒ 正常路径取最优数据源，任何一环缺失**逐级降级**，不报错。

| 类 | 一级（最优） | 二级 | 三级（兜底） |
|---|---|---|---|
| 设定值 | 面板最大设定值 | — | 经验域 `range_max` |
| 温度 | 材料 `min/max_*_temp` | 材料**类别**兜底表 | 经验域 `range_min/max` |
| 时间 | 产品 `target_cycle_time` / `total_injection_weight` 导出 | — | 经验域 |
| 位置/枚举 | 经验域 | — | — |

**候选动作清单（按确定性排序）**：

| # | 动作 | 证据 | 影响面 | 确定性 |
|---|---|---|---|---|
| 1 | `MBP0~MBP3` 经验下界 **10 → 0** | 设备上限 8；材料推荐 4/5/6；实测 58/58 在域外 | **182 条**规则激活度 0.375 → 0.726（**峰值桶不变**） | 高（但「低档定义区间」要工艺确认） |
| 2 | 温度类论域接**材料温度** | `NT`/`ET` 经验域 [0,50] vs 实测 123~275 | **47 条** | 高（口径已给，数据现成） |
| 3 | 温度类**类别兜底表** | 库里只有 3 个材料 | 兜底路径 | 中（表内容要工艺校核） |
| 4 | 时间类接**产品维度**（`target_cycle_time` 优先） | 329 条规则现用硬编码域；`process_context` 壁厚一条没填 | **329 条** | 中（口径要工艺确认；**契约零扩容**） |
| 5 | 缺设备上限：改 400 拦人为降级兜底 | §32.2.4 | 全部请求 | ⛔ **待拍板**（与 10-27 口径冲突） |

**明确不做（本轮）**：

- 不改任何算法代码（`specs.py` / `engine.py` / `fuzzy_core/`）；
- 不改 `RuleKeyword` 的经验域数据（改 0 属于**改数据**，需工艺确认后单独走）；
- 不动 `BT`（历史遗留，按用户口径抛弃）；
- 不新增测试用例（按仓库约定：每轮末统一跑现成验收手段）。

### 32.5 必须拍板的 3 件事

① **设定值类缺设备上限 ⇒ 400 拦人，还是降级到经验域继续跑？**
（10-27 口径「设备值没有就报错」 vs 10-29 口径「能否运行需要兜底」—— 两者冲突，影响所有 optimize 请求的可用性）

② **温度类论域用材料的哪个区间？**
推断：`[min_*_temp, max_*_temp]`（用户口述的「20~80」= PP 模温 min/max）；
待确认：是否要以 `recommended_*_temp` 为中心对称展开？

③ **时间类「随产品变」用哪个信号？**
`target_cycle_time`（现成、在契约里、反映厚薄/复杂度）—— 推荐；
或 `ave_thickness` / `product_weight`（语义最贴「薄壁/厚壁」，但**库里一条没填** ⇒ 要先补录）。

### 32.6 本节**没有**做的事

- 未改任何生产代码、未改任何数据库数据；
- 未给材料类别兜底表填内容（表内容属工艺知识，不自拟）；
- 未对 `MBP` 下界改 0 做实际改动（只给出实测影响面，等拍板）。
