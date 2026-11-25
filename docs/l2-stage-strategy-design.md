# L2 阶段化调机：口径设计（2026-11-12）

> **目的**：把「调机按什么组织」定成**可落数据**的口径 —— 此前挂在 L2 形态讨论里的待办项。
> **状态**：**口径已定**（2026-11-12 拍板 A–G，见 §10）；**批次 12.1 / 12.2 / 12.3 / 12.4a / 12.5 / 12.6a / 12.6b / 12.6c / 12.7 / 13.0 / 13.1 / 14.1 / 15.1 / 15.2 / 15.3 / 15.4 已落地**（见 §11）。
> ⚠️ **2026-11-13 口径修正**：**L2 不重选缺陷**（L2 的输入 = 规则 + 已确定的缺陷信息），见 §5。
> ⚠️ **2026-11-13 口径修正 2**：**基线项不靠白名单排挤，而用独立的禁入清单**（见 §7.2）。
> **当前 pytest 基线：302 passed**（2026-11-25 实测；此前记录 236 / 135 / 80 passed —— 测试集规模已变）。
> **关联**：`backend/process/references/04-defect-adjustment-rules.md`（规则原料）、
> `backend/process/services/optimize_chain/decide_adjustment.py`（`ScenarioStrategy` 机制）、
> `docs/open-questions.md`（本文遗留的未决项）、
> `docs/qualified-tuning-boundary.md`（**合格态调机 · 功能边界** —— 第二阶段调机：降能耗 / 降周期）。

> ⚠️ **路径变更公告（2026-11-23 · 目录归位；2026-11-25 · L2 两模块合并并改名）**：
> **本文正文的 ``algorithms/xxx.py`` 路径已随目录归位失效**，阅读时按下表换算
> （机制本身未变，只是文件搬家 / 合并）：
>
> | 旧路径 | 现址 |
> |---|---|
> | `algorithms/decide_direction.py` | `services/optimize_chain/decide_adjustment.py`（2026-11-25 改名 + 并入 `tuning_strategy`） |
> | `algorithms/defect_selection.py` | `services/optimize_chain/defect_selection.py` |
> | `algorithms/tuning_strategy.py` | `services/optimize_chain/decide_adjustment.py`（阶段表 + 场景清单已并入，2026-11-25） |
> | `algorithms/stage_order.py` | `services/optimize_chain/decide_adjustment.py`（阶段表已并入） |
> | `algorithms/strategies.py` | `services/optimize_chain/decide_adjustment.py`（场景清单已并入） |
> | `services/policies.py` | `services/optimize_chain/decide_adjustment.py`（已并入） |
> | `services/optimize_chain/decide_direction.py` | `services/optimize_chain/decide_adjustment.py`（2026-11-25 改名） |
> | `services/optimize_chain/tuning_strategy.py` | `services/optimize_chain/decide_adjustment.py`（已并入，2026-11-25） |
> | `algorithms/integrate_params.py` | `services/optimize_chain/integrate_params.py` |
> | `algorithms/check_params.py` | `services/optimize_chain/check_params.py` |
> | `algorithms/anchors.py` | `services/optimize_chain/anchors.py` |
>
> **符号级换算**（正文里出现的旧符号名）：
>
> | 旧符号 | 现位置 / 现状 |
> |---|---|
> | `AdjustmentPlan` | `AdjustmentScheme`（`decide_adjustment.py`） |
> | `build_plan` | `resolve_scheme`（**入口** = `build_adjustment_scheme`） |
> | `apply_plan` | `apply_scheme`（`integrate_params.py`） |
> | `ScenarioContext` / `build_scenario_context` | **已删**（批次 15.2）⇒ 改**事实表**（`decide_adjustment.py::collect_facts`） |
> | `decide_tuning`（曾用名，**未落地**） | `decide_adjustment` |
>
> 归位理由见 `docs/algorithm-layering-plan.md` 的「路径变更公告」。

---

## 0. 问题的准确表述

「调参不是随机调的，是有策略的」—— 这句话在系统里对应的是**一个具体的断层**：

| 层 | 产出 | 现状 |
|---|---|---|
| L1 模糊推理 / 经验规则 / LLM | **一堆平级建议**（调什么能改善） | ✅ 在跑 |
| **L2 策略** | **这一轮调哪几个、按什么次序、口径多少、谁退出** | ✅ **12.3 起开始裁决**（清单：S1 一条 + 兜底一条） |
| L3 整合参数 | 自洽的参数集 | ✅ 在跑 |
| L4 校验 | 合理性体检 | ✅ 在跑 |

⇒ **L1 产出不变，换个 L2 策略，最终落地结果就不同**（用户原话，§2.1）。
⇒ L2 曾长期"空转"（`algorithms/strategies.py` 的 `STRATEGIES = ()`）：
**场景/次序/名额/口径这一层一条经验都没有** ⇒ 批次 12.3 起先落
**S1 一条（短射充填优先）+ 一条兜底（缺省一轮一个量，兼容旧版）**。

本设计回答三个问题：**阶段怎么划分 → 阶段怎么判定 → 阶段怎么变成数据**。

---

## 1. 先把三个概念分清（否则后面全是混淆）

| 概念 | 回答什么 | 落在哪 | 例子 |
|---|---|---|---|
| **规则 rule** | 「遇到这个现象 ⇒ 调这个量」 | 规则库（**已有**） | 短射 ⇒ `MEL` 加 2 |
| **策略 strategy** | 「**这一轮**允许调哪些、按什么次序、调几个、口径多少」 | `ScenarioStrategy`（**机制已有；12.3 起清单有 2 条**） | 短射场景 ⇒ 只准动 `met_end_pos`、一次一个、按重量比例算行程 |
| **阶段 stage** | 「这一轮处在调机的第几步」 | **本设计要定的**（尚未有） | 第 1 步打足 → 第 2 步补缩 → 第 3 步外观 |

> 一句话：**规则说"短射就加胶量"，策略说"这轮只准动充填量、一次一个、按比例算"，阶段说"现在还没轮到这一步"。**

⚠️ **阶段 ≠ 工艺组**。「注射组 / 保压组 / 计量组」是**参数分组**；
「打足 / 补缩 / 外观」是**要解决的问题**。两者恰好耦合，但不是一回事 —— 见 §2。

---

## 2. 阶段按「要解决的问题」划分，不按「工艺组」划分

用户口径：「先把产品打到差不多（注射行程）→ 再补缩（保压）→ 最后针对性处理外观缺陷」。

拆开看：**"注射行程""保压"是手段，"打足""补缩"才是阶段**。依据三条：

1. **阶段的进入/达成信号必须是可观测量** —— 缺陷码 + 重量缺口可观测；
   "保压参数"不可观测，无法判定"这一步过了没有"。
2. **阶段推进 = 缺陷优先级** ⇒ 与 `algorithms/defect_selection.py` 的既有可替换点**合一**
   （该模块 docstring 明写「业务优先级规则将来作为新策略接入，**不改调用点**」）。
   ⚠️ 该模块在 **L1 侧**（引擎选哪个缺陷去推理）；**L2 不重选**，只查阶段。
3. **跨轮幂等** —— 阶段可从反馈**推导**，不必落库（见 §4）。

---

## 3. 三个阶段的定义

### 3.1 缺陷码 → 阶段（**数据**，覆盖全部 17 类）

| 阶段 | 目标 | 归属缺陷码 |
|---|---|---|
| **S1 打足** | 充填到位 | `SHORTSHOT` |
| **S2 补缩** | 尺寸与形状达标 | `SHRINKAGE` `UNDERSIZE` `OVERSIZE` `WARPING` |
| **S3 外观** | 表面质量达标 | `WATERRIPPLE` `GASVEINS` `TOPWHITE` `HARDDEMOLDING` `ABERRATION` `WELDLINE` `FLASH` `AIRTRAP` `MATERIALFLOWER` `BURN` `GATEMARK` `SHADING` |

> 归类依据见 `references/04` 的缺陷章：
> `UNDERSIZE`/`OVERSIZE`/`WARPING` 的根因在收缩与冷却 ⇒ 归 S2；
> 其余 12 类是表面/外观问题 ⇒ S3。
> ⚠️ 这张表是**业务口径**，落库前需确认（WARPING 归 S2 还是 S3 是可讨论项）。

### 3.2 阶段的进入与达成（**信号**）

| 阶段 | 进入信号 | 达成信号 | 备注 |
|---|---|---|---|
| **S1** | 反馈含 `SHORTSHOT` **且** `fill_gap > 0` | `SHORTSHOT` 从反馈中消失（或 `fill_gap ≤ 阈值`） | 重量容差阈值**待标定** |
| **S2** | S1 已达成 **且** 反馈含 S2 类缺陷 | S2 类缺陷从反馈中消失 | S1 未达成 ⇒ **不进入** S2 |
| **S3** | S1、S2 均已达成 **且** 反馈含 S3 类缺陷 | S3 类缺陷清零 | 同上 |

⇒ **达成信号 = "这一类缺陷不见了"**，这是可观测的、且与"让位"语义天然对齐
（§5.3 讨论文档里的「条件式让位」："它要解决的问题已经被解决"）。

⚠️ **批次 12.5 已落地（观测部分）**：`algorithms/stage_order.py::derive_stage_progress()`
—— 达成 = 该阶段的缺陷码在本轮反馈中**全部消失**（**纯推导、不落库**，每轮重算）；
`current`（当前应推进的阶段）注入 `ScenarioContext.extra`（场景条件可引用，
**当前无场景引用 ⇒ 行为零变化**）+ 进第2层留痕。
⚠️ **2026-11-25 追加**（批次 15.2）：注入载体由 `ScenarioContext.extra` 改为**事实表**
（映射）—— `ScenarioContext` 已删（见 §12.2 的现状更新）。
⚠️ **让位机制本身未落地** —— 经核实，拿阶段达成信号做「前提」在现有架构下
**恒不触发**（场景命中即该阶段未达成；白名单又排在 `satisfied` 之前）⇒ 判据待定，见
`docs/open-questions.md` Q2。
⚠️ **2026-11-24 追加**：批次 13.1 落地的是**另一类**让位（上轮证伪 ⇒ 不再动它），
与这里说的「阶段达成信号 ⇒ 让位」是**两件事** ⇒ Q2 仍未闭环。

---

## 4. 阶段状态**不落库** —— 每轮从反馈推导

**决策**：不引入 `stage` 字段、不落库、不迁移。

**理由**：
1. 阶段 = `f(本轮反馈的缺陷构成, 重量数据)` —— **纯函数**，天然幂等；
2. 换模 / 轮次失败 / 反馈缺失 ⇒ **自动自愈**，不会出现"状态卡在 S2"的脏数据；
3. 与 `select_defect(context)` 每轮重算的现有形态一致 —— 引入状态反而要处理
   "状态与反馈矛盾时信谁"。

**代价**：阶段推进完全依赖反馈质量 ⇒ **反馈稀疏/滞后时阶段会原地踏步**。
这是可接受的（反馈本来就稀疏，`§5.5` 已定 feedback 是**事后证伪**不是事中门控）。

**何时才需要落库**：将来若出现「人工把机器锁在某个阶段」的需求 ⇒ 再引入
`stage_override`（可选覆盖值，默认 `None` = 纯推导）。**当前无此需求 ⇒ 不建。**

---

## 5. 阶段优先级表是**两处共同的数据源**（关键收敛点）

> ⚠️ **L2 不重选缺陷**（2026-11-13 用户界定）：
> **L2 的输入是「规则」+「已确定的缺陷信息」** —— 缺陷在进入第2层之前就已经确定，
> 第2层**不做选取、不做重排**，只拿确定的缺陷信息去匹配策略、裁决方向。
> ⇒ 「这一轮该处理哪个缺陷」**不是第2层的裁决**（此前把它划进 L2 是错的，已纠正）。
> ⇒ L2 做的只有三件：**这个缺陷属于哪个阶段 → 命中哪条策略 → 调什么 / 按什么次序 / 调几个**。

阶段一旦成立，它要同时喂给两个地方（**用法不同**）：

| 落点 | 职责 | 用阶段表做什么 | 现状 |
|---|---|---|---|
| `services/optimize_chain/defect_selection.py`（**L1 侧**） | 选哪个缺陷去推理 | **排**（按阶段优先级重排后取第一个） | ✅ **批次 12.7 起生效**：`StagePriorityDefectStrategy` = 按阶段优先级重排后取第一个（**当前唯一实现**；`FirstValidDefectStrategy` 已于 2026-11-19 删除） |
| `services/optimize_chain/decide_adjustment.py`（**L2 侧**） | 调什么、怎么调 | **查**（阶段进度 —— `derive_stage_progress()` 推导 `current_stage`，进**事实表**） | `select_strategy` 已就位；12.3 起清单有 2 条（S1 + 兜底） |

⚠️ **这两处必须读同一份阶段优先级表**，否则会打架：
选了 `SHORTSHOT`（S1），策略却匹配到 `SHRINKAGE`（S2）的条件 ⇒ 方向与缺陷对不上。

⇒ **落点建议**：阶段优先级表放 `algorithms/` 下（与 `strategies.py` 同级），
`defect_selection` 与 `strategies` 都从它读。**顺序**：

```text
反馈缺陷列表
   ↓ ① 按阶段优先级排序（S1 → S2 → S3，族内按缺陷码字典序稳定）   ← L1 侧：defect_selection
   ↓ ② 取第一个有效缺陷                                         ← L1 侧：defect_selection
   ↓ ③ 用「已确定的缺陷」匹配策略（查它属哪个阶段）                ← L2 侧：decide_adjustment
   ↓ ④ 裁决：准入 / 次序 / 名额 / 口径                            ← L2 侧
```

---

## 6. 阶段 → 策略场景的映射（**示意；场景清单已落库**于 `services/optimize_chain/decide_adjustment.py`）

```python
# S1 打足 —— 充填量两个旋钮，先 MEL 后 VPTL
ScenarioStrategy(
    scenario_code='stage1_filling',
    conditions=(
        {'field': 'defect_codes', 'operator': 'in_any', 'value': ('SHORTSHOT',)},
        {'field': 'fill_gap', 'operator': 'gt', 'value': 0},
    ),
    allowed_params=('met_end_pos', 'vps_pos'),   # 基线项 = 其余全部
    preferred_params=('met_end_pos', 'vps_pos'), # 有序 ⇒ 先 MEL，MEL 偏大后才轮到 VPTL
    max_items=1,                                 # 一次只改一个量
    target_modes={'met_end_pos': 'fill_ratio'},   # 口径**按字段**声明（按充填量比例解算行程）
    reason='充填未足 ⇒ 只动充填量：先胶量端 met_end_pos，MEL 偏大后才轮到 vps_pos',
    priority=10,
)

# S2 补缩 —— 二段压力 / 二段时间（锚点是浇口封冻）
ScenarioStrategy(
    scenario_code='stage2_shrinking',
    conditions=(
        {'field': 'defect_codes', 'operator': 'in_any',
         'value': ('SHRINKAGE', 'UNDERSIZE', 'OVERSIZE', 'WARPING')},
    ),
    allowed_params=('hold_pres_1', 'hold_t_1'),
    preferred_params=('hold_pres_1', 'hold_t_1'),
    max_items=1,
    target_mode='delta',
    reason='充填已足 ⇒ 只动保压：二段压力与二段时间（二段时间锚点是浇口封冻）',
    priority=20,
)
```

⚠️ S3（外观 12 类）**不是一个场景** —— 12 类缺陷各要不同的参数与口径
（`FLASH` 要减胶量/降二段压力、`BURN` 要先提示修模、`GASVEINS` 要查背压…）
⇒ S3 需**按缺陷码细分多条策略**，优先级由 §5 的阶段表 + 族内顺序决定。

⚠️ **`in_set` 是待新增的运算子**（现有 `in` 方向相反，见 §8 前提 ⑤）：
`_compare` 的 `in` = `_contains(field_value, target)` = **目标 ⊆ 字段值**，
而这里要的是「**选中缺陷 ∈ 缺陷码集合**」⇒ 必须新增 `in_set`（单值 ∈ 集合），
否则 S2（4 个码）/ S3（12 个码）的条件写不出来。

---

## 7. 「旋钮顺序」与「基线项」怎么表达（两个建模选择）

### 7.1 旋钮顺序 = **有序** `preferred_params`

`preferred_params` 是**元组**（有序）⇒ 天然能表达"先 A 后 B"。
⇒ 充填量的两旋钮（先 `met_end_pos`、MEL 偏大后 `vps_pos`）**不需要新机制**。

⚠️ 但"**MEL 偏大**"这个**退阶条件**要能写进 `conditions` ⇒ 见 §8 的前提 ①。

⚠️ **2026-11-24 追加**：已落地的**退阶**（批次 13.1）走的是**排除**路径、
**不是条件**路径 —— 「上轮试过这个旋钮且没改善 ⇒ 本轮不再动它」（`failed_params` 通道）
⇒ **零配置改动**（退出的是**被证伪的那一个**，`allowed_params` 的顺序即退阶路径）；
而「**本轮算出来 MEL 偏大**」这类**同轮推导**的退阶条件**仍未落地** ⇒ 见 §8 前提 ①。

### 7.2 基线项 = **禁入清单**（`blocked_params`），与白名单分开

用户口径：「注射速度属基线取值，不进阶段调机」。
⚠️ **2026-11-13 修正**：原先写的是「基线项 = `allowed_params` 的**补集**，不单独建模」——
**落不了地**：兜底场景**不写白名单**（不窄化），若靠白名单排挤基线项，
就得把“所有可调旋钮”列成全集（60+ 项字面量，且随新增旋钮漂移）⇒ 维护成本更高。

⇒ 改为**两类“不可调”分开表达**：

| 机制 | 字段 | 含义 | 语义 |
|---|---|---|---|
| **白名单** | `allowed_params`（空 = 不限制） | **场景范围** —— 这个场景该动哪些旋钮 | 不在名单 ⇒ 让位「本场景不允许」 |
| **禁入清单** | `blocked_params`（空 = 不禁） | **基线项** —— 任何场景都不该动的旋钮 | 在名单 ⇒ 让位「基线项 ⇒ 不参与阶段调机」 |

⇒ 基线项只需写 **6 个字面量**（`inj_spd_1`~`inj_spd_6`，见 `decide_adjustment.BASELINE_BLOCKED_PARAMS`），
**不需要全集** ⇒ 新增旋钮不用改清单。

⚠️ **禁入排在准入之前**（裁决序 §2 早于 §3）：基线项是**全局**理由，比
“本场景不允许”更强 ⇒ 同时命中两者时留痕要写**基线项**，否则更强的理由被掩盖。

⚠️ **代价（仍然存在）**：白名单是**枚举式** —— 场景新增可调参数时要记得加进白名单，
漏了 ⇒ 该参数在该场景被静默挡住（**安全方向的失败**：少调，不会误调）。
缓解：白名单只写该缺陷**公认的主旋钮**；兜底场景白名单留空（不窄化），
新旋钮至少在兜底场景能被调到。

---

## 8. 需要补的技术前提（**8 条，诚实列出**）

| # | 前提 | 现状 | 影响 |
|---|---|---|---|
| ① | **条件要能表达"MEL 偏大"与"选中哪个缺陷"** | ✅ **批次 12.2 已落地** —— `ScenarioContext` 加 `extra` 通道，条件可引用**任意键**（未知键 ⇒ 不命中）；`CONTEXT_FIELDS` 降级为**文档清单**（标准派生字段） | ① 退阶条件落不下去；② S3 细分策略匹配不到（现在只能拿到**全部**缺陷码，不是**选中**的那个） |
| ② | **"打满"的重量容差阈值** | 现在只有 `fill_gap > 0` 判缺口 | S1 达成信号只能是"缺陷码消失"，缺量化口径 |
| ③ | **阶段优先级表 + 缺陷码→阶段映射** | ✅ **批次 12.1 已落地** —— `algorithms/stage_order.py`（17 类全覆盖） | §5 的两处共同数据源缺失 |
| ④ | **S3 的 12 条子策略** | 不存在 | S3 无策略 ⇒ 阶段表有了也只到 S2 |
| **⑤** | **条件运算子缺 `in_set`** | ✅ **批次 12.2 已落地** —— 新增 `in_set`（单值 ∈ 集合）/ `not_in_set`；原 `in` = `_contains(field_value, target)` = **目标 ⊆ 字段值**，方向**保持不变**（两者并存，靠命名区分） | S2（4 个码）/ S3（12 个码）的条件**写不出来** ⇒ 需新增 `in_set`（单值 ∈ 集合） |
| **⑥** | **条件运算子缺「集合 ∈ 集合」** | ✅ **批次 12.4a 已落地** —— 新增 `in_any`（**字段值是集合** ⇒ 任一元素 ∈ 目标集合）；与 `in_set`（字段值是单值）**方向相反**，两者并存不混 | ⚠️ `defect_codes` 是**元组**（全部缺陷码）⇒ `in_set` 对它**永远为假** ⇒ S2 的 4 个码写不出来 |
| ⑦ | **条件引用的是「选中缺陷」还是「含该缺陷」** | ✅ **已修复**（2026-11-16）—— 缺陷选取上移到 **service 预处理层**（**只做一次**），结果经 `DefectSelection.to_context()` 随 context 的 `selected_defect` 下传；**L1（推理）与 L2（策略）共用同一份** ⇒ 场景条件改引用 `selected_defect`（`in_set`），不再用 `defect_codes`（全部缺陷码） | 已消除：多缺陷反馈下 L2 命中的场景 = **本轮实际处理的缺陷**对应的场景，不再错配（白名单不会再挡掉本该调的参数 ⇒ 不再“该轮无输出”） |
| ⑧ | **上一轮效果与上一轮落地参数要能进 L2** | ✅ **已落地**（2026-11-24，批次 13.1）—— `ScenarioContext` 加 `last_tuning_result`（上一轮试模评价）/ `last_advised_params`（上一轮**实际落地**的参数）两个标准字段；`resolve_priority` 加 `failed_params` 通道（上轮证伪 ⇒ 让位） | 原缺口：算法一直推**同一方向同一量**，换不了旋钮（用户口径：「一个调整逻辑一直打不出合格产品，算法仍然一直推荐相同的调整方向和调整量」） |
| ⑨ | **目标值求解口径要能按字段声明并被执行** | 🟡 **部分落地**（2026-11-24，批次 14.1）—— 口径位已从「场景级单值 + 只认 `met_end_pos`」换成**按字段声明**（`ScenarioStrategy.target_modes` / `AdjustmentPlan.target_modes`），L3 按字段取口径；**求解器注册表与第二个口径未做**（等 `peak_ratio` 一起定型） | 原缺口：非派生量旋钮（保压压力 / 注射压力 / 背压 / 料筒温度…）的目标值**全是 L1 的「大概值」直接落地**，L2 没有「用实测值修正调整量」的话语权 |

⚠️ **现状更新（2026-11-19）** —— 缺陷信息**已收进 `feedback`**（收敛后
`defects` 只剩本轮处理的那条）⇒ 前提 ⑥ 的「`defect_codes` 是全部缺陷码元组」
已不成立（现在只含本轮那条）⇒ `in_any` 仍在，但**当前无场景引用**它。
前提 ⑦ 的**载体变了、判定口径不变**：缺陷选取仍在 service 预处理层做**一次**，
结果**写回 `feedback`**（`defects` 收敛成一条 + `defect_selection` 留痕），
**不再**用 context 顶层键 `selected_defect` ⇒ L1 与 L2 仍共用同一份 ⇒
→→场景条件仍引用 `selected_defect`（由 `algorithms/decide_direction.py` 的
→→`build_scenario_context` **从 feedback 内部派生**后放入 `ScenarioContext.extra`
→→—— 优先取 `defect_selection['selected']['keyword_name']`（选取的一手出口），
→→ 回落 `defects[0]['keyword_name']`；**service 层不再注入**）。

⚠️ **现状更新（2026-11-24）** —— 场景条件的**载体统一到标准字段 `defect_codes`**：
`ScenarioContext.defect_codes`（标准字段，在 `CONTEXT_FIELDS` 里）由
`selected_defect` 派生 ⇒ **与选中的那一条恒等**（至多一个元素）⇒
6 条场景条件的 `field` 改用 `defect_codes`、运算子由 `in_set` 改 `in_any`
（集合字段专用）⇒ `ScenarioContext.extra` 只剩 `current_stage`（跨模块注入位）。
⇒ **判定口径不变**：命中的仍是「本轮实际处理的缺陷」对应的场景
—— `defect_codes` 恒为选中的那一条 ⇒ 不会因「含别的缺陷」而错配
（多缺陷反馈下实测：短射+缩水 ⇒ 命中 `filling_first`，不命中 `shrinking_first`）。

⚠️ **现状更新（2026-11-25 · 批次 15.2）** —— 上两段里的载体（`ScenarioContext` /
`build_scenario_context` / `CONTEXT_FIELDS`）**已全部退役** ⇒ 现状是**事实表**
（`decide_adjustment.py::collect_facts`，**映射结构**、无字段清单、无补丁通道）：
`defect_codes` 由 `_derive_selected_defect(feedback)` 派生（只认 `defect_selection`
这一手出口）；`current_stage` 由 `derive_stage_progress` 推导后一并放进事实表。
⇒ **判定口径不变**（仍指「本轮实际处理的缺陷」），只是**载体从对象换成映射**。

⚠️ **现状更新（2026-11-24 · 退阶）** —— 「**上轮试过没改善 ⇒ 本轮不再动它**」落地
（批次 13.1）：

- **两个字段各管一件事**（缺一不可）：
  `last_tuning_result` = **触发器**（上轮效果：`ineffective` / `unchanged` ⇒ 换）、
  `last_advised_params` = **定位器**（上轮**实际落地**了哪些参数 ⇒ 退哪几个）。
  「只有落地的才试过，没落地的没被证伪」⇒ 落地判据取 `decision_status == 'adopted'`。
- **事实从哪来**：service 预处理层查**父轮** `Recommendation`
  （`parent_param.parent_param_id` = 上一次提交反馈的那一轮）⇒ 从 `recommendations`
  JSON 里取已采纳项；上轮效果取 `feedback['tuning_result']`（`_to_algorithm_feedback`
  **已透传** ⇒ 零取数成本）。
- **判据分工**：**通用判据进代码**（`ineffective` / `unchanged` 都算没改善 ——
  调机师傅对这两种情况的反应一样：换旋钮再试）、**业务顺序进配置**
  （`allowed_params` 的顺序天然就是退阶路径 ⇒ **零配置改动**）。
- **三层边界**（用户口径「每一个环节的代码要有边界」）：service 层只提供**事实**（查库）、
  L2 `resolve_scheme` 只根据事实算**排除集**、`resolve_priority` 只执行**机制**（让位 + 留痕）。
- **优雅退化**：没有上一轮 / 老记录无 `decision_status` ⇒ 排除集为空 ⇒
  **行为与现状完全一致**（不臆造）；纯推理入口（`optimize_from_provided`）天然无上一轮。

⚠️ **现状更新（2026-11-24 · 口径位）** —— 「**改成多少**」的交接面已按字段建模
（批次 14.1，**零行为变化**）：`ScenarioStrategy.target_modes`（字段 → 口径名）、
`AdjustmentScheme.target_modes`（**只带保留项**）、L3 按 `plan.target_modes` 取口径。
⚠️ **只换形、不扩口径** —— 现有唯一口径仍是 `fill_ratio`（仍只作用于 `met_end_pos`）；
非派生量旋钮的目标值**仍是 L1 原样透传** ⇒ 前提 ⑨ 只**部分闭环**。
⇒ 详见 §12。

⚠️ ① 直接触及 `§6.2` 撤回策略表的理由②（「条件字段集写死在代码里 ⇒ 表达不了需要表达的东西」）
⇒ 扩字段时**不要再把字段名写死成枚举**，否则等于把撤回的理由又请回来。
**已落地口径**：条件引用上下文 mapping 的任意键（未知键 ⇒ 不命中），
`CONTEXT_FIELDS` 从白名单降级为「文档化字段清单」。

---

## 9. 与 L2 形态讨论差距清单的收敛

| §4 差距 | 阶段口径的影响 |
|---|---|
| ② 方向级次序（「先充填打满」） | ✅ **被阶段本身解决** —— 阶段就是方向级次序 |
| ③ 参数组级次序（「先注射再保压」） | ✅ **被阶段内的 `allowed_params` + 有序 `preferred_params` 解决** ⇒ 不需要独立的 group 排序机制（`PriorityEntry.group` 可继续只做标注） |
| ⑤ 条件式让位 | ✅ **被阶段达成信号解决** —— "它要解决的问题已被解决"就是阶段推进的副产物 |
| ④ `group` 未参与裁决 | 🟡 **可不做**（被 ③ 覆盖） |
| ⑥ 留痕缺依据 | ✅ 已补（`kept_reasons`） |
| ⑦ 建议列表与落地不一致 | ✅ **已解决**（批次 12.8 + 12.9）—— 12.8 修「零落地」；12.9 让每条建议带 `decision_status`（adopted / yielded / deferred）+ 原因 ⇒ 前端默认只显示已落地，开发模式 `?dev=1` 全量并逐条标记 |
| ① 准入白名单 | ✅ 已补（`allowed_params`） |

⇒ **阶段口径一旦定下，§4 的 4 条缺口会一起收敛** —— 这本身就是设计自洽的一个信号。

---

## 10. 拍板结果（2026-11-12，**口径已定**）

| # | 议题 | 拍板 | 影响面 |
|---|---|---|---|
| **A** | 阶段划分依据 | ✅ **按「要解决的问题」（缺陷族）** —— 打足 / 补缩 / 外观 | 决定后面全部 |
| **B** | 阶段状态 | ✅ **不落库，每轮从反馈推导** —— 纯函数、幂等、自愈；将来要「人工锁定」再引 `stage_override`（当前不建） | **零迁移** |
| **C** | 尺寸类归属 | ✅ **全归 S2** —— `SHRINKAGE` `UNDERSIZE` `OVERSIZE` `WARPING` 四个都归「补缩」 | 只改一张表（§3.1 已按此写） |
| **D** | 「打满」量化口径 | ✅ **以缺陷码消失为主信号**，重量容差作辅助（阈值待标定） | 阶段达成信号 |
| **E** | 条件字段集 | ✅ **改为引用上下文任意键**（未知键 ⇒ 不命中），`CONTEXT_FIELDS` 降级为文档清单 | 避免重蹈 §6.2 撤回理由② |
| **F** | 阶段优先级表位置 | ✅ **`algorithms/` 下独立文件** —— `defect_selection` 与 `strategies` **共读**（前者**排**、后者**查**） | 新增一个文件 |
| **G** | S3 本轮范围 | ✅ **先做 2–3 条验证形态** —— `FLASH` / `BURN` / `GASVEINS`（覆盖「减胶量」「先提示修模」「查背压」三种不同形态） | 决定本轮工作量 |
| **H** | 多缺陷反馈的选取口径 | ✅ **已定**（2026-11-16，批次 12.7）—— 选取**只做一次**、在 **service 预处理层**（不在算法层或各层各挑一遍）；**当前生效规则 = 阶段序**（`stage_priority`）：多缺陷按调机阶段取（打足 → 补缩 → 外观），**不按列表第一项**（用户口径：「结合入参进行分析」，例：短射+缩水⇒先短射；缩水+飞边⇒先缩水）。⚠️ **2026-11-19 更新**：`first_valid` 口径与 `FIRST_VALID_STRATEGY` 常量**已删除**（早期为跑通流程设计的占位实现，核验阶段已无价值）；**策略接口（Protocol）与 `strategy` 形参也一并删除** —— 当前用不到切换机制，按「用不到就不写代码」原则不留空壳，将来真有第二个口径时再加回 | L1/L2 选取口径统一；⚠️ **行为变化**：多缺陷反馈下选中项**可能不是列表第一条**（L1 推理对象 + L2 命中场景随之变） |
| **I** | L2 场景条件的缺陷口径 | ✅ **已修**（2026-11-16）—— 场景条件引用**本轮实际处理的缺陷码**；⚠️ **2026-11-24 载体统一**：字段名由 `selected_defect`（`ScenarioContext.extra`）改为标准字段 **`defect_codes`**（由 `selected_defect` 派生 ⇒ 与选中的那一条恒等），运算子 `in_set` → `in_any` | §8 ⑦ 闭环 |
| **J** | L2 怎么应对「上轮调了没改善」 | ✅ **已定**（2026-11-24，批次 13.1）—— **退阶**：上轮效果 = **触发器**（`ineffective` / `unchanged` ⇒ 换），上轮落地参数 = **定位器**（退哪几个）；**通用判据进代码、业务顺序进配置** | L2 入口从「零历史」变成「带一笔上一轮」；⚠️ **只解决「换旋钮」，不解决「改多少」** —— 非派生量目标值仍原样透传 L1 |
| **K** | 「改成多少」的口径怎么表达 | ✅ **已定**（2026-11-24，批次 14.1）—— **按字段声明口径名**（场景 → 字段 → 口径），算式落**第3层**；本批只换形（`target_mode` → `target_modes`），**不扩口径**；峰值压力类口径**挂起** | L2 从「只给绝对值」变成「能给口径」；⚠️ 尚未产生新口径 ⇒ 目标值行为**零变化** |

⚠️ 拍板 **E** 连带出一条**新增技术前提**（§8 前提 ⑤）：
现有 `_compare` 的 `in` 语义是「**目标 ⊆ 字段值**」（`_contains(field_value, target)`），
与「选中缺陷 ∈ 某个缺陷码集合」**方向相反** ⇒ 需新增 `in_set` 运算子（单值 ∈ 集合）。
⇒ 已在批次 12.2 落地（新增 `in_set` / `not_in_set`，原 `in` 语义不变）。

---

## 11. 建议的落地批次（**12.1 / 12.2 / 12.3 / 12.4a / 12.5 / 12.6a / 12.6b / 12.6c / 12.7 / 13.0 / 13.1 / 14.1 / 15.1 已执行**）

⚠️ **编号说明**：`12.5` 是「阶段达成信号」那条线（2026-11-16，**只落观测**）；
`12.6a/b/c` 是「缺陷选取单一入口」那条线（2026-11-16）；
`12.7` 是「多缺陷选取接阶段序」那条线（2026-11-16）；
`13.0` 是「阶段准入首次生效」那条线；`14.1` 是「口径位换形」那条线（**等价整理**）；
`15.1` 是「合格态调机策略」那条线（**复用现有分层，不新建引擎**）；
`15.2` 是「第2层收成单入口 + 事实表取代上下文对象」那条线；
`15.3` 是「实测输入归位到口径」那条线（**L3 自己从原料取**）；
`15.4` 是「L2 两模块合并并改名」那条线。
⚠️ **本文与 `docs/qualified-tuning-boundary.md` 共用同一条 `15.x` 序列**
（**15.1 是同一件事**：合格态调机策略）⇒ **15.5 留给合格态专项线**
（该文的排期从 **15.6** 起，⚠️ 2026-11-25 消歧 —— 此前两文在 15.2–15.5 上**重号**）。

| 批次 | 内容 | 验收 |
|---|---|---|
| **12.1** | ✅ **已落地** —— 新增 `algorithms/stage_order.py`（阶段表 + 缺陷码→阶段映射 + `stage_of`/`stage_rank`/`order_defects`）+ `defect_selection.py` 新增 `StagePriorityDefectStrategy`（**只加能力，不接线**：``DEFAULT_STRATEGY`` 未动） | ✅ 阶段表 17 类全覆盖；混合反馈（缩水+短射）默认选缩水、阶段选短射；同阶段保持原序；无效项完整审计；pytest **135 passed**（行为零变化） |
| **12.2** | ✅ **已落地** —— 条件字段集改造（§8 ①）+ **新增 `in_set` 运算子**（§8 ⑤） | ✅ 条件可引用 `extra` 里的任意键（如 `selected_defect`）；未知键 ⇒ 不命中（不静默通过）；`in_set` 与 `in` 方向不混淆；pytest **135 passed**（行为零变化） |
| **12.3** | ✅ **已落地**（2026-11-13）—— 策略清单落 **S1 一条**（条件引用**已确定的缺陷码** + `fill_gap`）+ **兜底一条**（`conditions=()` 恒命中、`max_items=1` ⇒ 兼容旧版「一轮只调一个量」） | ✅ 短射+缺料 ⇒ 只动 `met_end_pos`、按 `fill_ratio` 解算（``ML_N = VPTL + 行程×重量比``）；短射但重量充足 / 缩水 / 缺重量 ⇒ 落兜底（只留 1 个）；pytest **135 passed**；一次性核对 **34 项全过**（含「`max_items=None` ⇒ 多参数保留全部」的多参数出口验证） |
| **12.4** | **12.4a 已落地**（2026-11-13）—— 策略清单填 **S2 + S3 三条**（`shrinking_first` / `flash_first` / `burn_first` / `gasveins_first`）+ **两类不可调机制**（白名单 `allowed_params` = 场景范围、禁入清单 `blocked_params` = 基线项）+ **新增 `in_any` 运算子**（§8 ⑥） | ✅ pytest **135 passed**；一次性核对 **41 项全过**（含「白名单外全部让位 ⇒ 本场景无输出」「禁入清单优先于白名单」「`max_items=None` ⇒ 多参数保留全部」）；⚠️ **12.4b 未做**：切阶段选取策略 + 把 L1 选取结果透出给 L2（§8 ⑦） |
| **12.4b** | ❌ **已撤回**（2026-11-16）—— 原计划「① fuzzy 切阶段选取策略；② 把 L1 选取结果透出给 L2」：① **撤回**（阶段序接线把「只选第一条」换成另一套规则，且选取散落在两个引擎里 ⇒ 同一份反馈可能推出两个不同缺陷；用户定调「选取只做一次、在预处理层」）；② 改由 **12.6c** 落地 | ⚠️ 撤回后：当前生效规则 = **「只选第一条」**（`first_valid`）；`stage_priority` 降级为**未接线的候选规则**；`first_only` 仅作历史语义参照 —— ⚠️ **该状态已由 12.7 终结**（撤回理由里的「选取散落」已被 12.6 消除） |
| **12.5** | ✅ **已落地**（2026-11-16）—— **阶段达成信号 + 留痕**（**只观测，不裁决**）：`algorithms/stage_order.py` 新增 `derive_stage_progress()` + `StageProgress`（达成 = 该阶段缺陷码在本轮反馈中全部消失；**纯推导、不落库**）；`services/policies.py` 把 `current_stage` 注入 `ScenarioContext.extra`（场景条件可引用，**当前无场景引用 ⇒ 行为零变化**）+ `PolicyResolution.stage_progress` 进留痕 | ✅ pytest **135 passed**；核对 20 项全过；黄金快照差异数不变（仍为 6，历史遗留）；⚠️ **条件式让位未落地** —— 经核实「拿阶段达成信号当前提」在现有架构下**恒不触发** ⇒ 判据待定，见 `docs/open-questions.md` Q2 |
| **12.6a** | ✅ **已落地**（2026-11-16）—— **feedback 预处理层**（service 层）新增「缺陷整理」：调一次 `select_defect`，结果经 `DefectSelection.to_context()` 随 context 的 `selected_defect` 下传（**只加能力、不接线** ⇒ 行为零变化） | ✅ pytest **135 passed**；内联核对 3 项全过（多缺陷取第一条 / 首项无效跳过后选次项 / 载荷形状）；行为零变化 |
| **12.6b** | ✅ **已落地**（2026-11-16）—— **引擎侧改为只读载荷**：`fuzzy` / `empirical` 的 `recommend` / `is_available` 全部改读 `context['selected_defect']`，**不再各自调用 `select_defect`**；新增 `ensure_selected_defect(context)`（幂等）供绕过 service 层的调用点（condition chain / 离线 runner / 黄金快照脚本） | ✅ pytest **135 passed** + 4 个手工脚本全过 + 黄金快照差异数不变；内联核对 4 项全过（两引擎选中的缺陷 = 预处理层选的那个）；⚠️ 行为变化：① fuzzy 多缺陷下由阶段序回到「列表第一条」；② empirical 在「首项无效、次项有效」时由放弃改为处理次项 |
| **12.6c** | ✅ **已落地**（2026-11-16）—— **L2 接入同一份**：5 条场景条件的 `field` 由 `defect_codes` 改为 `selected_defect`（运算子统一 `in_set`）；`resolve_policies` 增 `selected_defect` 参数（经 `ScenarioContext.extra` 注入）；调用点由两个入口挪进 `_infer_kernel`（与 L1 同一层、同一份口径） | ✅ pytest **135 passed**；场景判定核对 4 项全过（多缺陷 ⇒ 命中本轮缺陷的场景 / 旧口径对照实证会错配 / 单缺陷零回归 / 无缺陷落兜底）⇒ **§8 ⑦ 闭环** |
| **12.7** | ✅ **已落地**（2026-11-16）—— **多缺陷选取接阶段序**：`algorithms/defect_selection.py` 的 `DEFAULT_STRATEGY` 由 `FirstValidDefectStrategy` 改为 `StagePriorityDefectStrategy`（`FIRST_VALID_STRATEGY` 保留为历史口径/回退开关）；`services/parameter_optimize.py` 预处理层落一条 `[optimize] … 缺陷选取` 日志 | ✅ pytest **135 passed**；核对 **18 项全过**（缩水+短射⇒短射 / 飞边+缩水⇒缩水 / 同阶段保序 / 无效项 `skipped` 完整 / 未知码排末位 / `ensure_selected_defect` 幂等不重算 / 留痕 `strategy=stage_priority` / 多缺陷 ⇒ L2 命中被选中缺陷的场景 + 旧口径对照）；黄金快照差异数不变（仍为 6，历史遗留）；⚠️ **行为变化**：多缺陷反馈下选中项**可能不是列表第一条** ⇒ L1 推理对象 + L2 命中场景随之变 |
| **13.0** | ✅ **已落地**（2026-11-16）—— **阶段准入首次生效**：策略清单新增 `filling_stage_first`（`priority=15`），条件 = `selected_defect in {SHORTSHOT}` + **`current_stage == 'filling'`** ⇒ **阶段进度从「只观测」升级为「参与场景匹配」**；白名单 = 胶量端 + 注射时间/压力 + 保压组 + 熔体侧 + 料筒温度组，优先集 = **胶量端 → 保压 → 背压 → 料筒温度**（用户拍板） | ✅ pytest **135 passed**；三离线脚本 e2=0 / algo=0 / nested=0；黄金快照差异数不变（仍为 6）；核对 **15 项全过**（短射+缺重量 ⇒ 命中本场景且落地 `met_end_pos`（`met_pos_1` 300→303）/ 料筒温度降为「名额已满」/ G3 让位与基线项理由仍可见 / **有重量数据时仍走 `filling_first`**（`fill_ratio` 不变）/ 缩水、飞边场景不受影响 / 短射规则库 13 个参数全部有归属 ⇒ 无「本场景无输出」风险）；⚠️ **`inj_t` 仍被 G3 彻底废掉**（让位对象 `inj_spd_1` 是基线项）⇒ 短射少一个强力旋钮，待用户另行拍板 |
| **13.1** | ✅ **已落地**（2026-11-24）—— **退阶（上轮证伪 ⇒ 本轮不再动它）**：`ScenarioContext` 加 `last_tuning_result` / `last_advised_params` 两个标准字段；service 层查**父轮** `Recommendation`（取 `decision_status == 'adopted'` 的项）⇒ 得到上轮**实际落地**的参数；`resolve_priority` 加 `failed_params` 通道（让位理由「上轮试过无改善 ⇒ 本轮不再动它」） | ✅ pytest **236 passed**；核对 **8 项全过**（无历史 ⇒ 首选不变 / `ineffective` ⇒ 退到次选 / `unchanged` ⇒ 退到次选 / `effective` ⇒ 同方向继续 / 上轮落地的是次选 ⇒ 首选仍保留 / 无关参数 ⇒ 无影响 / 条件可引用 `last_tuning_result` / 上下文字段取值正确）；⚠️ **只解决「换旋钮」，不解决「改多少」** —— 非派生量目标值仍原样透传 L1，`target_mode` 仍只作用于 `MEL`；⚠️ **本轮未做**「L2 自产候选（补充旋钮）」与「规则匹配度进裁决」 ⇒ 另批排期 |
| **14.1** | ✅ **已落地**（2026-11-24）—— **口径位换形**（等价整理）：`ScenarioStrategy.target_mode`（场景级单值）→ `target_modes`（**字段 → 口径名**）；`AdjustmentPlan.target_mode` → `target_modes`（**只带保留项**）；`build_plan` 带出保留项口径；L3 `apply_plan` 改为按字段取口径；口径名收进常量 `anchors.FILL_RATIO_MODE`（**唯一出处**）；删死代码 `ScenarioStrategy.uses_fill_ratio` | ✅ pytest **236 passed**；**零行为变化** —— `fill_ratio` 仍只作用于 `met_end_pos`，解算结果逐位等价；⚠️ **本批不扩口径** —— 非派生量目标值仍是 L1 原样透传；口径求解器注册表与 `peak_ratio` **挂起**（§12.5-① 方向歧义未解） |
| **15.1** | ✅ **已落地**（2026-11-25）—— **合格态调机策略**（**不新建引擎、不新判据源**）：① `ScenarioStrategy` 扩一个能力 `candidate_params`（**场景自带候选** —— 算法零产出时仍能有调机对象）；② 场景清单新增 `qualified_efficiency`（条件 = `last_tuning_result == 'qualified'`，候选/白名单/优先项 = `inj_pres_1`，`max_items=1`，口径 = `step_down`）；③ L3 新增**第二个口径 `step_down`**（递减步进：目标 = 当前设定 × (1 − 步长)，步长初值 5%）—— **不依赖物理模型**；④ `apply_scheme` 从「只对 `met_end_pos` 走口径」**推广为逐字段按口径**；⑤ fail-fast 从「L1 零产出」**移到「L2 零候选」**（**对非合格态行为完全等价**）；⑥ 前端恢复合格态【获取优化工艺】入口 | ✅ pytest **242 passed**（236 基线 + 6 条新用例）；契约用例 `tests/test_qualified_strategy.py` 6 条全过；前端 `type-check` 通过；⚠️ **步长 5% 是初值不是结论**（待实测标定）；⚠️ **只降压力** —— 省周期（`cool_t`）、「降过头」回退机制、「合格但无可省项」的前端表现**仍为预留项**（见 `docs/qualified-tuning-boundary.md` §6 R3–R5） |
| **15.2** | ✅ **已落地**（2026-11-25）—— **第2层收成单入口 + 事实表取代上下文对象**（**逻辑分层**：一个完整工作 = 多个依次完成的步骤，每步职责清晰）：① 新增 L2 单入口 `build_adjustment_scheme`（`optimize_chain/decide_adjustment.py`）—— 挑料（`collect_facts`）/ 派生（`fill_gap` / `current_stage`）/ 匹配（`select_strategy`）/ 裁决（`resolve_scheme`）/ 回填（`_apply_decision_status`）**全在它内部**；② `ScenarioContext` / `CONTEXT_FIELDS` / `build_scenario_context` **删除** ⇒ 条件求值改读**事实表**（映射）⇒ §10 拍板 E 真正落地（字段名不再写死在代码里）；③ service 层的「构建上下文」一步去掉 ⇒ 只**交原料**（`feedback` / `mold_info` / 上轮落地参数）拿**结论**（`AdjustmentScheme`）；④ L3 的实测输入由 `collect_weights` **直接从原料取**（不经 L2 转手） | ✅ pytest **302 passed**（全量；`tests/` 目录 247 条）；**行为零变化** —— 事实表只放取到的值，而条件求值「取不到 ⇒ 不命中」⇒ 与原「值为 `None` ⇒ 不命中」等价；⚠️ **回填时机前移**（进决策层内部 ⇒ 早于编排层的 fail-fast）⇒ 但 fail-fast 抛异常不返回 ⇒ **无外部可见差异**；⚠️ **阶段进度日志少了 `interface_tag`**（那条日志随阶段推导一起搬进了决策层） |
| **15.3** | ✅ **已落地**（2026-11-25）—— **实测输入归位到口径**（service 不替 L3 挑）：① `anchors.py`（**底座**）新增 `read_weights(feedback, mold_info)` + 键名常量 `ACTUAL_WEIGHT_KEY` / `TARGET_WEIGHT_KEY`；`to_float` 从 `decide_adjustment` **移到底座**（L3 也要用）；② L3 `apply_scheme` 的 `fill_weights` 入参**删除** ⇒ 改为收 `feedback` / `mold_info`，**自己**取重量喂 `resolve_fill_target`；③ 编排层的 `collect_weights` 调用**删除** ⇒ 只递原料；④ 决策层的 `collect_weights` / 两个键名常量**删除** ⇒ L2 也从 `anchors.read_weights` 取（L2 派生 `fill_gap`、L3 解算行程目标**同源**） | ✅ pytest **302 passed**（与 15.2 基线一致）；**行为零变化** —— 取数时机由「编排层在 L2 之后」移到「L3 内部」，同一份原料、同一套取数逻辑 ⇒ 值完全相同；⚠️ **取数次数减少** —— L3 只在 `fill_ratio` 口径且有 MEL 目标时才取（原先每次都取）⇒ 无副作用；⚠️ **`apply_scheme` 对外签名变更** —— `fill_weights` 参数删除（影响 1 处生产调用 + 2 处测试） |
| **15.4** | ✅ **已落地**（2026-11-25）—— **L2 两个模块合并为一个并改名**（**一个文件 = 一层**）：① `decide_direction.py`（**机制**：怎么裁决）+ `tuning_strategy.py`（**规则**：业务经验）→ 合并为 **`decide_adjustment.py`**（**机制 + 规则 + 入口同住一个文件**）；② `defect_selection.py` 仍只负责**缺陷选取**（只读 `sort_defects_by_stage`）⇒ 单一真相源不破；③ 缺陷码译文表另立公共底座 `algorithms/common/defect_codes.py`（**跨算法线公共**，零外部依赖） | ✅ pytest **302 passed**；**零行为变化** —— 纯文件合并 + 改名 + import 路径同步（调用点 3 处：`parameter_optimize.py` / `integrate_params.py` / `defect_selection.py`）；换算表见 `docs/algorithm-layering-plan.md`「路径变更公告」 |

⚠️ **现状更新（2026-11-19）** —— 缺陷选取的**载体**已改（**判定口径不变**）：

- `select_defect` 成为**唯一入口**，入参 = feedback，返回**收敛后的 feedback**
  （`defects` 只剩本轮处理的那条 + `defect_selection` 留痕）；
- `DefectSelection.to_context()` 与 `ensure_selected_defect(context)` **已删除**；
- context 顶层键 `selected_defect` **已移除**；
- `resolve_policies` 的 `selected_defect` 参数**已删**（改为从收敛后的
  `defects[0]` 自行取）；
- ⚠️ **2026-11-19 追加**：`FirstValidDefectStrategy` / `FIRST_VALID_STRATEGY` /
  `DefectSelectionStrategy` Protocol / `select_defect` 的 `strategy` 形参 ——
  **全部删除**（占位口径 + 用不到的切换机制，按「用不到就不写代码」原则不留空壳）。
- ⚠️ **2026-11-19 追加（纯改名 + 合并，行为零变化）**：调机策略全套（**阶段表 +
  场景清单**）合并为 **`algorithms/tuning_strategy.py`** —— 阶段表与场景规则是
  同一张表的两端（场景清单按 S1/S2/S3 分区，恰好对应三个阶段）。曾用名：
  `algorithms/stage_order.py`（阶段表）、`algorithms/strategies.py`（场景清单）。
  符号改名：`stage_of` → `stage_of_defect`、`stage_rank` → `rank_of_stage`、
  `order_defects` → `sort_defects_by_stage`、`DEFECT_STAGE` → `DEFECT_STAGE_MAP`、
  `STRATEGIES` → `SCENARIO_POLICIES`、`load_strategies()` →
  `sorted_scenario_policies()`、`BASELINE_EXCLUDED_PARAMS` → `BASELINE_BLOCKED_PARAMS`
  ⇒ 上文批次纪实里的旧名是**当时形态**。

⇒ 12.6a / 12.6b / 12.6c 三行里描述的「随 context 的 `selected_defect` 下传」
是**当时形态**；12.7 验收项里的「`ensure_selected_defect` 幂等不重算」
对应的函数已不存在（幂等性由「只收敛一次」保证）。
⇒ 另：`StageProgress` 的 `achieved` / `pending` 因收敛而只反映**本轮处理那条**
所在阶段（`current` 不受影响 ⇒ 场景判定零变化）。

⚠️ **每个批次结束跑一次现成 pytest**（不新写测试框架），
基线 **302 passed**（2026-11-25 实测；全量 = `tests/` 目录 247 条 + fuzzy 包内 55 条；
此前记录 80 / 135 / 236 / 242 passed —— 测试集规模已变）；
行为变化要能用留痕/`to_trace()` 说明白。

⚠️ **批次 12.1 的一个副产品（已记录在代码里）**：阶段重排把无效项挪到末位，
而选取是「遇到第一个有效项就停」⇒ 不预扫就会漏记无效项。
⇒ `StagePriorityDefectStrategy` 的 ``skipped`` 改为**记录全部无效项**（原始顺序），
包括「排在有效项之后」的那几个（``skipped`` 的语义是"用户提交了但没被采用的项"，
要完整审计）。

---

## 12. 「改成多少」：目标值求解口径（L2 → L3 的交接面）

> **状态**：§12.2 / §12.3 / §12.5 三条已由用户拍板（2026-11-24）；
> **批次 14.1 已落地**（口径位换形，零行为变化）。
> **批次 15.1 已落地**（2026-11-25）—— **第二个口径 `step_down`**（递减步进）
> 随合格态调机策略一同落地 ⇒ 口径位**从「一个口径」变成「两个口径」**。
> **仍挂起**：§12.5-① 的方向歧义 ⇒ 峰值压力类口径（`peak_ratio`）**本批不落**。
>
> **下一轮接续点**：先读 §12.5 的三条拍板结论；要做 `peak_ratio` 时先解 §12.5-① 的
> 方向歧义，再按 §12.4 定接口（求解器注册表 / 输入包届时定型）。**不要重做 §12.1**。
> ⚠️ **2026-11-25 更新**：14.2「求解器注册表」**仍未建** —— 15.1 的第二个口径
> `step_down` 走的是 `apply_scheme` 里的**直接分支**（与 `fill_ratio` 同款）⇒
> **注册表 / 输入包**依然待定型（等 `peak_ratio` 或第二个非派生量口径）。

### 12.1 现状体检（2026-11-24 核实）

| 环节 | 现状 | 证据 |
|---|---|---|
| L2 出口 | `AdjustmentScheme.assignments` = (字段名, L1 的 `recommended_value`) ⇒ **原样透传** | `decide_adjustment.py` |
| L2 口径位 | `ScenarioStrategy.target_mode: str`（**场景级单值**），且**只对 `met_end_pos` 生效**（`resolve_scheme` 只在 `G1_AUTO_FIELD` 保留时才记它） | `decide_adjustment.py` |
| L3 求解 | `apply_scheme` 读 `plan.target_mode == 'fill_ratio'` ⇒ `resolve_fill_target`（重量比例 → 行程）；**其余字段无分支** ⇒ 直接写 L1 绝对值 | `integrate_params.py` |
| 6 条场景 | 只有 `filling_first` 写 `target_mode='fill_ratio'`（作用于 `met_end_pos`）；其余 5 条走默认 `'delta'` | `decide_adjustment.py` |
| 死代码 | `ScenarioStrategy.uses_fill_ratio` **零调用点** | `decide_adjustment.py` |

⇒ **一句话**：现在只有「充填量 → 行程」一条口径通了；其余旋钮的目标值全是 L1 的
「大概值」直接落地。

⚠️ **术语澄清**：`G1_AUTO_FIELD = 'met_end_pos'`（**熔胶终止位置**，业务字段名），
**不是** `'MEL'`。`MEL` 是算法名，译出来才是 `met_end_pos` ⇒
`met_end_pos` 是「**标**」（不进 `assignments`，走 `mel_targets`），
`resolve_fill_target` 解出的落点是 `met_pos_N`（末段计量位置）= **决策量**。

⚠️ **现状更新（2026-11-24 · 批次 14.1）** —— 上表描述的是**批次前**形态；
本批把口径位从「场景级单值 + 只认 `met_end_pos`」换成「**按字段声明**」：

| 位置 | 批次前 | 批次后 |
|---|---|---|
| 场景策略 | `ScenarioStrategy.target_mode: str`（单值） | `ScenarioStrategy.target_modes: Mapping[str, str]`（字段 → 口径名） |
| 调整计划 | `AdjustmentScheme.target_mode: Optional[str]` | `AdjustmentScheme.target_modes: Mapping[str, str]`（**只带保留项**） |
| L3 读取 | `plan.target_mode == 'fill_ratio'` | `plan.target_modes.get(G1_AUTO_FIELD) == FILL_RATIO_MODE` |

⇒ **效果完全等价**（`fill_ratio` 仍只作用于 `met_end_pos`）；
口径名收进常量 `anchors.FILL_RATIO_MODE`（**唯一出处**，两侧不各写字面量）。
⇒ 死代码 `ScenarioStrategy.uses_fill_ratio` 已删（零调用点）。

### 12.2 三层职责（本批的边界）

| 层 | 职责 | 本批改动 |
|---|---|---|
| **service** | 提供**实测事实** | 已有 `actual_weight`；本批**可选**接 `peak_pressure` |
| **L2** | 「调哪个 / 次序 / 谁让位 / **每个字段用什么口径**」 | 场景清单加「字段 → 口径名」声明；`AdjustmentScheme` 带出口径映射 |
| **L3** | 按口径名**求解目标值**（手上有现值 + 实测输入） | 加口径求解器注册表；`apply_scheme` 按字段取口径 |
| **配置** | 「这个场景这个字段用什么口径」= **业务知识** | `decide_adjustment.py` 场景清单 |

**红线不变**：L2 仍**不读参数集**（不知道现值 ⇒ 算不出目标值）；
L3 不判断「该不该调」（那是 L2）；
口径的**算式**落代码（**逻辑**，解释规则的方式固定），
**哪个字段用什么口径**落配置（**业务**，可增长）。

⚠️ **现状更新（2026-11-25 · 批次 15.2）** —— 上表是**批次 12.x 的边界**；现状收紧了一层：

| 项 | 批次 12.x | 现状（15.3） |
|---|---|---|
| 第2层入口 | 散在编排层（`build_scenario_context` → `derive_stage_progress` → `select_strategy` → `build_plan` → `_apply_decision_status`） | **单入口** `build_adjustment_scheme`（`optimize_chain/decide_adjustment.py`）⇒ 上述五步全在它内部 |
| 事实载体 | `ScenarioContext` 对象（6 个写死字段 + `extra` 补丁通道）+ `CONTEXT_FIELDS` 清单 | **事实表**（映射）⇒ **无字段清单**、无补丁通道；条件求值读**任意键**（§10 拍板 E 落地） |
| service 层的活 | 拼上下文 + 派生 `fill_gap` + 推阶段 + 抽表 + 裁决 + 回填 | **只交原料、拿结论**（重量也不替 L3 挑 ⇒ L3 自己从原料取） |
| 派生量的归属 | `fill_gap`（总重−实测重）/ `current_stage`（阶段进度）由 service 层造 | **决策层自己造**（它们只为「条件能引用」而存在 ⇒ 属决策层） |
| 实测输入的归属 | L2 从 `ScenarioContext` 拿重量、L3 从编排层接 `fill_weights` | **底座统一**（`anchors.read_weights`）⇒ L2 派生 `fill_gap`、L3 解算行程目标**同源**；编排层**不出现重量** |

⇒ **「逻辑分层」落到代码上**：一个完整工作 = 多个依次完成的步骤，每步职责清晰；
**service 不边采购边处理**（不替决策层派生、不替它裁决）。

### 12.3 建模选择（推荐 ①）

| 方案 | 形态 | 评价 |
|---|---|---|
| **①** | **场景声明「字段 → 口径名」映射**（`ScenarioStrategy.target_modes: Mapping[str, str]`） | ✅ **推荐** —— 与 `allowed_params` / `preferred_params` / `blocked_params` **同构**（场景 → 字段集合/映射）⇒ 无新概念；口径**确实随场景变**（`fill_ratio` 只在充填场景成立） |
| ② | 全局「字段 → 口径名」注册表（类似 `BASELINE_BLOCKED_PARAMS`） | ❌ 口径**不是字段的固有属性**（同一字段在不同场景口径不同） |
| ③ | 场景级单值 + 字段级覆盖（两层） | ❌ 同一语义两处展开 ⇒ 违反「同一语义只在一处展开」 |

⚠️ **「字段固有默认口径」这层先不做**（YAGNI）—— 将来若发现某字段在**所有**场景同口径，
再加全局默认表（届时是自然扩展，不难）。

⚠️ **破坏性**：`ScenarioStrategy.target_mode`（`str`）→ `target_modes`（`Mapping`）；
`AdjustmentScheme.target_mode`（`Optional[str]`）→ `target_modes`（`Mapping[str, str]`）。
影响面小（§12.6）。

### 12.4 口径求解器（L3 · 代码）

⚠️ **本批不建注册表** —— 按项目「**用不到就不写代码**」原则：
现在只有 `fill_ratio` 一个口径 ⇒ 建注册表 = 空架子。
⇒ **接口等第二个口径（`peak_ratio`）落地时再定型**（届时一并定「输入包」形态）。

- 现有的 `resolve_fill_target`（`anchors.py`）**已经就是 `fill_ratio` 口径的求解器**
  ⇒ 本批直接沿用，未重写。
- 通用约定（**待定型**）：口径名 → 求解函数；求解函数返回 `Optional[目标值]`；
  **解不出 ⇒ `None` ⇒ 回落 L1 绝对值**（保证不退化）。
- ⚠️ **2026-11-25 更新（15.1）**：**第二个口径已来** —— `step_down`
  （`anchors.resolve_step_down`，递减步进）仍走**直接分支**（`apply_scheme` 内按字段取
  口径名 ⇒ 匹配则调对应求解器）⇒ **注册表依旧没建**（两个口径时仍是空架子）。
  ⇒ 14.2 保持「等 `peak_ratio` 或第二个非派生量口径再定型」。

### 12.4.1 两个口径的对照（2026-11-25 · 15.1 后）

| 口径 | 常量 | 求解器 | 适用字段 | 物理含义 | 是否依赖物理模型 |
|---|---|---|---|---|---|
| `fill_ratio` | `FILL_RATIO_MODE` | `resolve_fill_target` | `met_end_pos`（熔胶终止位置） | 重量比例 → 注射行程 | ✅ 依赖（重量比） |
| `step_down` | `STEP_DOWN_MODE` | `resolve_step_down` | 任意非派生量（首批只 `inj_pres_1`） | **当前设定 × (1 − 步长)** | ❌ **不依赖**（靠试模反馈逼近够用线） |

⚠️ **两条口径的分工**：`fill_ratio` 是**算出来的**（有物理关系）；
`step_down` 是**试探出来的**（「上一模合格」只说明当前设定够用，**不说明能降到哪**
⇒ 只能小步试探）⇒ **步长必须实测标定**，初值 5% 只是「一次只走一小步」这个原则的表达。

### 12.5 拍板结果（三条，2026-11-24）

**① 峰值压力 80% ⇒ 先不落，等方向想清**

- 用户拍板：**本批不落** `peak_ratio` ⇒ 下方那个方向歧义
  （提高时成立、降低时相反）**未解** ⇒ 批次 14.3 挂起。
- ⚠️ 挂起时**不要**按任一方向先实现 —— 算反了比不实现更糟。

**② 与规则原料 `SS-05` 的 ×1.2 的关系 ⇒ 只留 SS-05**

- 用户拍板：**只留 `SS-05` 的「× 1.2」**（需求侧冗余），
  **不另立**「实测反推 + 安全裕度」口径 ⇒ 将来落 `peak` 类口径时用 ×1.2 这条。

**③ `injection_time` / `cycle_time` ⇒ 先预留，已实现的不变更**

- `CycleObservationSchema` 的 4 个键**本批零改动**；
  `actual_product_weight` 的消费路径不变；
  `peak_pressure` / `injection_time` / `cycle_time` 保持「契约有、实现无」。

⚠️ **未解的方向歧义（挂起项）** —— 把上一模实测峰值压力当**目标值参照**时，
物理含义是「上一模打到了 P MPa ⇒ 这轮注射压力设 0.8P」——
这在**提高**注射压力时成立（设备能力参照）；在**降低**时方向相反
（短射轮次本来就打不满峰值，照搬只会更缺料）⇒ 需明确适用面。

> **后续（2026-11-24 · 已澄清适用面）** —— 上面三个键的**用途**已明确：
> 它们服务于**合格态经济性调机**（产品已合格后再降能耗 / 降周期），
> 边界见 `docs/qualified-tuning-boundary.md`，待定口径登记在 `docs/open-questions.md` Q12。
> ⇒ **本节的方向歧义在该场景下不适用**：合格态是**降低**方向，
> 而「上一模实测峰值当目标值参照」只在**提高**方向成立 ⇒ **两条路不重合**，
> 14.3 是否还要做，取决于经济性调机最终选哪条目标值算法（Q12 R1）。

### 12.6 影响面与批次落地

| 批次 | 内容 | 状态 |
|---|---|---|
| **14.1** | **口径位换形**：`target_modes` 替换 `target_mode`（场景 + 计划两处）+ `fill_ratio` 迁移 + 删死代码 `uses_fill_ratio` + 口径名收进常量 | ✅ **已落地**（2026-11-24）—— pytest **236 passed**；**零行为变化**（`fill_ratio` 仍只作用于 `met_end_pos`，效果逐位等价） |
| **14.2** | 口径求解器注册表 + 通用输入包 + 按字段遍历求解 | ⏸ **本批不做** —— 只有一个口径时是空架子 ⇒ 等 14.3 一起做（届时接口一次定型） |
| **14.3** | `peak_ratio` 口径 + `peak_pressure` 进上下文 | ⏸ **挂起** —— 等 §12.5-① 的方向歧义解开（另一条候选路径见 `docs/qualified-tuning-boundary.md`：合格态经济性调机；两者不重合，取决于 Q12 R1 的选择） |
| **15.1** | **合格态调机策略**（跨 §12 与 `docs/qualified-tuning-boundary.md`）：场景自带候选（`candidate_params`）+ **第二个口径 `step_down`**（递减步进）+ `apply_scheme` 逐字段按口径 + fail-fast 移到「L2 零候选」 | ✅ **已落地**（2026-11-25）—— pytest **242 passed**；⚠️ **注册表仍未建**（两个口径走直接分支）；⚠️ **步长 5% 待标定** |

**14.1 的实际改动面**（比 §12.1 预估的小）：

| 文件 | 改动 |
|---|---|
| `anchors.py` | 新增口径名常量 `FILL_RATIO_MODE`（**唯一出处**） |
| `decide_direction.py` | `ScenarioStrategy.target_mode` → `target_modes`；删死代码 `uses_fill_ratio`；`AdjustmentPlan.target_mode` → `target_modes`；`build_plan` 带出**保留项**的口径；`to_trace` 字段名 |
| `tuning_strategy.py` | `filling_first` 改 `target_modes={'met_end_pos': FILL_RATIO_MODE}`；其余 5 条不动 |
| `integrate_params.py` | `apply_plan` 改为按字段取口径（`plan.target_modes.get(G1_AUTO_FIELD)`） |
| `tests/test_decide_direction_layer.py` | 2 处构造改新形态 + 1 处断言改新形态 |

⇒ **service 层零改动**（口径从场景策略直接读，L2 不算目标值）。
