# 未决口径清单

> **本文只列「还没拍板的事」** —— 每条 = 问题 + 影响面 + 关联代码位置。
> 不含推导过程与历史讨论（原讨论稿已清理，过程见 git 历史）。
>
> **口径拍板后**：把条目移出本文 → 在对应代码处落注释 → 若涉及对外契约，同步改 `docs/optimize-api-contract.md`。

---

## 一、需业务拍板

### Q1 · L2 参数组级次序配置层

- **问题**：是否要独立的「参数组级」配置层？现状 —— 组级次序只写在场景优先集里（如 `filling_stage_first` 把「胶量端 → 保压 → 熔体侧 → 料筒温度」排进优先集），没有独立的组级配置层。
- **影响面**：L2 裁决顺序、建议分组展示。
- **关联代码**：`backend/process/services/optimize_chain/decide_direction.py`、`backend/process/services/optimize_chain/tuning_strategy.py`

### Q2 · L2 条件式让位的前提判据

- **问题**：让位（`yielded`）的前提判据用什么？现状取「阶段达成信号」，但该信号在当前架构下**恒不触发** ⇒ 让位机制实际不生效。需另定判据（阶段准入 / 参数×缺陷派生量表）。
- **影响面**：`decision_status='yielded'` 永不出现。
- **关联代码**：`backend/process/services/optimize_chain/decide_direction.py`

### Q3 · feedback 评估节奏

- **问题**：离线？周期性？多久回看一次？（回看所需字段已具备）
- **影响面**：规则迭代 / 训练样本闭环节奏。
- **关联代码**：`backend/process/services/tuning.py`（`build_adjustments`）、规则晋升链路

### Q4 · L2 优先级顺序

- **问题**：「充填 → 保压 → 其他」的顺序是否确认？现状只做「场景优先集 + 名额」，组级次序未做。
- **影响面**：建议采纳顺序。
- **关联代码**：`backend/process/services/optimize_chain/decide_direction.py`、`optimize_chain/tuning_strategy.py::SCENARIO_POLICIES`

### Q5 · `VPTL` 下移下限

- **问题**：VP 切换位置下移到什么下限？涉及 `IL_1` 是否允许为 0。
- **影响面**：VP 切换位置的下界。
- **关联代码**：`backend/process/services/optimize_chain/anchors.py`、expert 引擎位置推导

### Q6 · L3 一致性层的落位 ✅ 已结（2026-11-23）

⇒ **结论：落 service 层** —— `backend/process/services/optimize_chain/`。
L3（及 L2 / L4 / 底座 `anchors` / 两份配套）属**优化链路的编排与领域计算**，
不是 AI 推理算法；判据 = **不被任何算法线引用**，只被 service 层调用。

⇒ **落地**：见 `backend/process/services/optimize_chain/__init__.py` 与
`docs/algorithm-layering-plan.md` 的「路径变更公告」（含旧→新路径对照表）。

⇒ **同批附带**：公共底座的反向依赖一并解除 —— 设备侧上限事实
从 `fuzzy/specs.py` 拆到算法层（**2026-11-24 收口后归 `algorithms/fuzzy/device_limits.py`**）
⇒ `algorithms/common/` **全目录零外部依赖**（不 import 任何算法包）
⇒ **依赖方向恒为「算法包 / service 层 → common」，**循环导入根源消除。

⇒ **同批附带（第三批 · 本轮）**：**上限链路按「契约 / 取值 / 校验」三层归位**
（用户口径：「算法根本就不知道我们程序是否有这些字段，这些是 service 的 model
层面定义的……我认为这里的参数上限校验，应该由 service 完成」）
**（2026-11-24 收口后：三层并成两层 —— 契约件在算法层 `algorithms/fuzzy/`，
取值 + 校验全在 service 层 `services/shared/param_limits.py` 一个模块）**：

- **查表 + 字段映射 + 跨命名空间翻译**（算法层）→ `algorithms/fuzzy/device_limits.py`
  （**第七批已瘦身**、**收口再瘦身**：只剩 `param_family` / `lookup_limit` /
  `to_family_limits`；原 `PARAM_LIMIT_FIELDS` / `POSITION_LIMIT_FIELDS` /
  `STROKE_FIELD` **已移 service 层**
  —— 算法层**不知道**参数有没有上下限）与
  `algorithms/fuzzy/field_names.py`（新增 `to_algo_family`：业务参数键 → 算法族前缀）；
- **来源声明 + 取值 + 组装 + 识别 + 拦截 + 文案**（service，**一个模块**）
  → `services/shared/param_limits.py`
  （`LIMIT_SOURCES` 唯一真相源 + `build_limits` 出业务键区间表 +
  `to_upper_limits` 取上界 + `find_over_limits` / `guard_parameter_limits` /
  `detect_over_limits` + `OverLimit` / `OverLimitItem` + 文案函数；
  **原 `setting_limits.py` 与 `over_limit.py` 已并入本文件**；
  原 `SETTING_FAMILY_LIMIT_FIELDS` / `POSITION_FAMILY_LIMIT_FIELDS` /
  `resolve_param_limits` / `resolve_stroke_limit` / `expand_position_limits` **已删**
  —— 位置类上限不再另抄一张表，行程标量经 `LIMIT_SOURCES` 的 `max_injection_stroke`
  统一出表；拦截层**只收两张表**：入参表 + 上限表，不碰 `machine_info`
  ⇒ 它不需要知道「哪台机器」）。

⇒ 算法层**不再判入参超限**（`fuzzy/engine.py` 的「0) 输入体检」整块删除），
设备上限表经 `context` 传入 ⇒ 算法层不碰 ORM 字段名。
详见 `docs/algorithm-layering-plan.md` 的「越限链路归位」公告。

⇒ **同批附带（第四批 · 本轮）**：**初始化链路补设定值类越限守卫**（用户拍板：
「初始化链路补设定值类越限守卫」+ 命中处理「**拒绝 400**」）⇒ 与优化链路
**同一守卫、同一错误码、同一文案**：

- `initialize_from_masterdata` / `initialize_from_provided`：**推理后立刻判初值**
  （新helper `parameter_initialize._guard_initial_params`，两道守卫成对执行、
  顺序与优化链路一致：设定值类 → 位置类）；
- `initialize_from_condition`：**不覆盖** —— 它**跳过推理算法**、直接复制源工艺的
  已有参数 ⇒ 没有「算法算出来的初值」⇒ 无初值可判；
- 实测（真实 expert 推理，6 个场景）：**设定值类 0 项越限** ⇒ 不会误拒；
  位置类仅「500g 冷流道」命中 4 项 ⇒ 属**既有行为**，非本次新增；
- 护栏：`backend/tests/test_initialize_over_limit_guard.py`（9 条）。

⇒ **同批附带（第二批）**：**设备能力字段命名统一到 ORM 真名**（用户口径：
「算法是独立单元，specs 各自独立，公共的只是校验方法」⇒ **真相源 = ORM**，
**不设「一份共享字段清单」当基准** —— 那会把两条算法线焊成最大公约数）：

- 初始化接口原用 `max_set_injection_velocity` / `max_set_holding_velocity`
  （`_velocity` 别名），而 ORM / 调优接口 / 前端一律用 `_speed` ⇒ 同一能力两个名字
  ⇒ 统一取 **ORM 真名**；
- 初始化接口原只声明 6 个 `max_set_*`，多传的 3 个（松退压力 / 松退速度 / 计量背压）
  被 pydantic `extra="ignore"` **静默丢弃**，直到专家契约校验报「缺失」才暴露
  ⇒ 现初始化接口能承载**专家契约的全部必填上限字段**（护栏按「⊇ 必填集」断言，
  **不要求两条 API 字段集合相等**）；
- 护栏测试 `backend/tests/test_spec_contract_alignment.py`（7 例）只护三件各线独立
  成立的事：① 一份 spec 内 `key == attr_name`；② `attr_name` 是 ORM 真实属性；
  ③ 对外 schema ⊇ 对应算法契约的必填集。**刻意不护**：expert 与 fuzzy 的字段集合
  相同（那是各自取舍，拉平即耦合）；
- **待拍板挂账**：expert 设备极限组 3 个别名 key（统一改名 or 删除）+
  对外初始化接口缺 `drive_system`（要不要暴露到对外契约）。

### Q7 · 旧版 D1/D2 跨轮递进策略

- **问题**：「效果佳 / 效果不佳」的跨轮递进策略是否纳入本期？（与轮次模型重构耦合）
- **影响面**：跨轮递进。
- **关联代码**：挖掘落地链路、`backend/process/services/tuning.py`

### Q8 · 短射规则方案（A5）的 4 项待确认

针对「短射 ⇒ `MEL` 进推荐、方向为加」这条规则改法：

| # | 问题 | 选项 |
|---|---|---|
| 8-1 | **delta 量级**：23 条规则量级不统一（2 / 3 / 3.0 / 3.8 / 5），相对 `MEL` 实测 282~758mm 只占 0.3%~1.8%，对短射够吗？ | (a) 沿用各库既有 mm 值（只改前件）｜(b) 全库统一按比例（+3%/+5%/+8%）｜(c) 统一固定 mm（2/3/3.8） |
| 8-2 | **是否同时补 `SHORTSHOT ⇒ IL0_add`**（注射位置是更直接的充填动作）？ | (a) 一起补｜(b) 本轮只做 `MEL`｜(c) `IL0` 下一轮 |
| 8-3 | **前件形态**：单前件 `SHORTSHOT`（有先例 rule 1001）还是双前件 `SHORTSHOT AND <可靠可测量>`？ | (a) 单前件｜(b) 双前件 |
| 8-4 | **改哪些库**：23 条分布在 9 个 system 拥有的 fuzzy 库（`base` + 8 个 `R*`）；租户私库属另一套体系、命中 0 | (a) 9 个库全改（推荐，保证一致性）｜(b) 只改 `base`｜(c) 只改 `base` + 含完整 `SHORTSHOT_*` 三件套的库 |

### Q9 · B1 线剩余三项

| # | 议题 | 内容 | 影响面 |
|---|---|---|---|
| 9-1 | **B1-1b 分段温度权威源** | 分段加热器设定值的权威源是什么（直接套材料熔体区间会「判不出档」，需另定） | `brl_temp_1..9` 判档 |
| 9-2 | **B1-2b 专家侧行程 / 射胶量校验** | `total_len` / `replenish_len` 超机台能力时**显式报出**，不再硬推一个位置（改的是 expert 产出算法 ⇒ 需单独决策） | expert 引擎输出 |
| 9-3 | **B1-2c 数据同源修复** | 位置类改用「产品充填量基准」判档（数据质量问题，价值独立，非本轮主线） | 位置类判档 |

### Q10 · 缺陷程度是否走硬路由

- **问题**：「缺陷程度 = 硬路由键（选哪套规则），而非权重维度」这个业务语义是否成立？
  成立 ⇒ 在方案 A（缺陷维 τ 边界 `<` 改 `<=`）与方案 B（精确匹配硬路由）之间选一个；
  希望「程度只微调幅度、跨档仍参与」⇒ 需重新定义权重口径。
- **配套三问**：
  1. 方案 A 还是方案 B？
  2. 该参数在当前缺陷下无同档规则时 —— 跳过，还是允许回落到相邻档？
  3. 硬路由只作用于缺陷维、不波及参数维门控 —— 是否认可？
  4. 纯缺陷维规则（如 `IF SHORTSHOT_low THEN BT1_add_1`，无参数前件）该保留吗？
- **影响面**：现状跨档规则 raw=0.135335 仍被放行 ⇒ 低档 / 中档规则会混入输出。
- **关联代码**：`backend/process/algorithms/fuzzy/fuzzy_core/models/nets.py`（缺陷维 τ 判定）、`algorithms/fuzzy/library/` 规则组装层

### Q11 · 挖掘置信度 / `lift` 未进推理（参数优先级机制）

- **问题**：「哪个参数调整更有效」的数据化表达（Apriori `lift`）要不要进推理排序？
  现状三个断点 —— `priority` 落地写死 1；引擎不读 `RuleMethod.confidence`；`priority` 一字两用（排序键 + 权重乘数）。
- **配套四问**：
  1. `priority` 的「排序」与「权重」怎么拆（新增字段 vs 引擎侧二级排序键）？
  2. 存量人工规则要不要补「有效性」标注（人工填 / 统计填 / 留空）？
  3. `iteration`（轮次）要不要进 Apriori 的关联维度？
  4. `lift` / `support` 怎么映射到有效性度量（`lift` 无限界需归一化）？
- **影响面**：挖掘出的有效性在推理侧完全不可见。
- **关联代码**：`backend/process/services/mining_landing.py`、`algorithms/fuzzy/library/adapters.py`、`fuzzy_core/models/nets.py`

---

## 二、一致性遗留待修（2026-11-23 `parameter_optimize.py` 一致性检查）

| # | 问题 | 位置 | 影响面 | 建议 |
|---|---|---|---|---|
| C1 | **合格态提交可能报错且不落库**：`tuning_result=qualified` ⇒ 缺陷列表为空 ⇒ 推理无输出 ⇒ 命中 fail-fast 抛 `ERROR_OPERATION_FAILED`；该异常发生在事务**之前** ⇒ 合格标签写不进 `TuningRecord` | `backend/process/services/parameter_optimize.py`（`_infer_kernel` fail-fast / `optimize_from_condition` Step2→Step3） | 合格态提交体验 + 合格标签丢失 | 待拍板：补合格态短路分支（只落库不推理），还是接受现行为并改文档 |
| C2 | **`source_type` 取值域三方不一致**：代码产出 `'fuzzy'`；ORM choices 是 `fuzzy_rule/rule_miner/llm/doe/genetic`；`'empirical'` 不在 choices 内 | `parameter_optimize.py::_resolve_primary_source`、`models/recommendation.py::SOURCE_TYPE_CHOICES` | 落库值不合规；历史回显回吐 `'fuzzy'` | 待拍板：统一到 choices，还是扩 choices 容纳 `'empirical'` |
| C3 | **优先级表漂移**：`_resolve_primary_source` 硬编码 `('expert','fuzzy','rule_miner','llm','doe','ga')`，而 `AlgorithmRegistry._priorities` 是 `{'fuzzy':1,'llm':2,'empirical':3}`；同文件另一处注释却写「取自 `_priorities`」 | `parameter_optimize.py::_resolve_primary_source` vs `algorithms/base.py::AlgorithmRegistry._priorities` | 自相矛盾；缺 `'empirical'` 只能靠兜底循环命中 | 改为直接读 `_priorities`（删硬编码表） |
| C4 | **字段名翻译双口径**：`_to_candidate_param_name` 翻不出 ⇒ `None`（不进候选）；`param_naming.to_business_param_name` 翻不出 ⇒ 原样返回 | `parameter_optimize.py`、`backend/process/services/shared/param_naming.py` | 落库的 `algorithm_recommendations[].param` 可能残留 `IPOS` / `BT` 等非工艺量名，而展示层会过滤掉 ⇒ 库里有、界面看不到 | 收敛为单一口径 |
| C5 | **service 层存量两个类形态**（`ParameterInitializeService` / `TuningService`）与「模块级函数 + 数据类为默认」的约定不一致 | `backend/process/services/parameter_initialize.py`、`backend/process/services/tuning.py` | 调用方写法不统一（类静态方法 vs 模块函数） | 待拍板：收敛到模块级函数，还是保留类形态并把约定改成「两类并存」 |

---

## 三、已关闭（勿再沿用）

2026-11-23 逐条核验，以下曾被记为待办，现已落地或已定性：

| 原结论 | 现状 | 证据 |
|---|---|---|
| `_apply_multi_injection` 未处理 `vps_pos=None` ⇒ 接口 500 | ✅ 已修（None 兑底到单段注射位置） | `backend/process/algorithms/expert/algorithm_engine.py` |
| `vps_mode` 默认预填 ⇒ 字符串兼容永久失效 | ✅ 已修（`default: None`；注释说明预填会让 Level-2 分支永久不可达） | `backend/process/algorithms/expert/process_set.py` |
| `pst_met_decomp_t` 距离模式恒 None | ✅ 已定性为**正确行为**（模式分派：mode=1 只写距离、mode=2 才写时间） | `expert/algorithm_engine.py` + `expert/tests/verify_suckback_smoke.py` |
| `runner_type` 契约必填 vs ORM 可空 | 🟡 形式矛盾仍在（expert 侧仍标「必填」，fuzzy 侧已降为「可选」），但算法层有 3 级兜底 ⇒ **数值影响为 0** | `expert/specs.py` / `fuzzy/specs.py` / `expert/algorithm_engine.py` |
