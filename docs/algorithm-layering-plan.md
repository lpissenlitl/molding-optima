# 算法分层改造计划（`_infer_kernel` 编排层）

> **状态：已实施完成（2026-11-24）。**
> 本文原为「待审阅的方案」，逐条拍板后已全部落地 —— 分层判定、目录归位、
> 命名空间收口均已实施；**当前路径以下方「路径变更公告」的最终形态为准**。
> 验收：`pytest tests` **290 passed**（含本轮新增护栏）。

---

## ⚠️ 路径变更公告（2026-11-23 · 目录归位；2026-11-24 · 收口定稿）

> **本文正文里的 `algorithms/xxx.py` 路径已随本次归位失效**，阅读时按下表换算。
> 下表是**最终形态**（2026-11-24 收口后）：算法命名空间只活在 `algorithms/fuzzy/`；
> 限值域归并为 `services/shared/param_limits.py` **一个模块**（零算法层依赖）。
> （表内旧路径均**相对 `backend/process/`**；正文若写作 `backend/process/algorithms/xxx.py`，
> 同样按下表换算 —— 前缀已含。）

| 旧路径 | 新路径（最终形态） |
|---|---|
| `algorithms/anchors.py` | `services/optimize_chain/anchors.py` |
| `algorithms/decide_direction.py` | `services/optimize_chain/decide_direction.py` |
| `algorithms/integrate_params.py` | `services/optimize_chain/integrate_params.py` |
| `algorithms/check_params.py` | `services/optimize_chain/check_params.py` |
| `algorithms/tuning_strategy.py` | `services/optimize_chain/tuning_strategy.py` |
| `algorithms/defect_selection.py` | `services/optimize_chain/defect_selection.py` |
| `algorithms/field_names.py` | `algorithms/fuzzy/field_names.py`（算法命名空间只在 fuzzy 内成立） |
| `algorithms/field_contract.py` | `algorithms/common/field_contract.py` |
| `algorithms/material_physics.py` | `algorithms/common/material_physics.py` |
| `algorithms/fuzzy/specs.py` 的设备侧上限**契约**件 | `algorithms/fuzzy/device_limits.py`（只留查表 + 跨命名空间翻译） |
| 设备上限**来源声明 + 取值 + 组装 + 识别 + 拦截 + 文案**（从 `machine_info` 挖值） | `services/shared/param_limits.py`（**唯一一张限值域模块**） |
| `algorithms/over_limit.py` | `services/shared/param_limits.py`（识别 + 拦截 + 文案，与越限守卫合并成一个模块） |
| `algorithms/common/over_limit.py` | **已并入** `services/shared/param_limits.py`（中途暂存于 common，最终归 service 层单模块） |
| `services/over_limit_guard.py` | **已合并进** `services/shared/param_limits.py` |
| `services/strategy_inputs.py` | `services/optimize_chain/tuning_strategy.py` |
| `services/spec_extract.py` | `services/shared/spec_extract.py` |
| `services/optimize_common.py` | `services/shared/param_naming.py`（同时改名） |
| `algorithms/common/field_names.py` | `algorithms/fuzzy/field_names.py`（中途暂存于 common，最终归 fuzzy） |
| `algorithms/common/device_limits.py` | `algorithms/fuzzy/device_limits.py`（同上） |
| `algorithms/common/limit_mapping.py` | **已并入** `algorithms/fuzzy/device_limits.py::to_family_limits` |
| `services/shared/setting_limits.py` | **已并入** `services/shared/param_limits.py` |
| `services/shared/over_limit.py` | **已并入** `services/shared/param_limits.py` |

**符号级换算**（正文里出现的旧符号名）：

| 旧符号 | 现位置 / 现状 |
|---|---|
| `SETTING_FAMILY_LIMIT_FIELDS` / `POSITION_FAMILY_LIMIT_FIELDS` | **已删** —— 族视图不再需要；`to_family_limits` 直接从业务键表翻译 |
| `resolve_param_limits` | `services/shared/param_limits.py::build_limits` |
| `resolve_stroke_limit` | **已删** —— 行程上限经 `LIMIT_SOURCES` 的 `max_injection_stroke` 统一出表 |
| `expand_position_limits` | **已删** —— 区间表直接可用；`to_upper_limits` 取上界 |
| `detect_blocking_over_limits` / `guard_setting_limit` / `guard_position_over_stroke` | 统一为 `find_over_limits` / `guard_parameter_limits` / `OverLimit`（`services/shared/param_limits.py`） |
| `PARAM_LIMIT_FIELDS` / `POSITION_LIMIT_FIELDS` / `STROKE_FIELD` | **已删**（`STROKE_FIELD` 退役见 §13） |
| `DOMAIN_SOURCE_STROKE` | **已删** —— 与 `DOMAIN_SOURCE_DEVICE` 归一（`fuzzy/engine.py`） |
| `engine._apply_device_bound` / `_apply_position_bound` | `engine._apply_declared_bound`（H1）/ `engine._apply_product_bound`（G7） |

**测试与验证脚本**（正文里出现的旧文件名）：

| 旧文件名 | 现址 / 现状 |
|---|---|
| `tests/test_fuzzy_position_domain.py` | `backend/tests/test_fuzzy_declared_domain.py`（声明域收口后改名） |
| `tests/test_check_params_position_violations.py` | `backend/tests/test_check_params_over_limit_violations.py`（越限守卫统一后改名） |
| `tests/test_fuzzy_machine_limits.py` | `backend/tests/test_fuzzy_engine_limits.py` |
| `_dev_refs/_verify_range_limits.py` / `_dev_refs/_verify_interval_limits.py` | **已删**（一次性等价性验证脚本，用完即弃、不入库） |

**为什么这样归**：
1. **调参链的 4 层**（L2 裁决 / L3 整合 / L4 校验 + 底座 `anchors` + 两份配套
   `tuning_strategy` / `defect_selection`）是**优化链路的编排与领域计算**，
   不是 AI 推理算法 ⇒ 移到 service 层 `services/optimize_chain/`
   （用户 2026-11-23 拍板）。判据：**不被任何算法线引用**，只被 service 层调用。
2. **跨算法线公共件**（字段名映射 / 越限判据 / 入参契约机制 / 材料物理常量）
   被 fuzzy / expert / empirical 与 service 层共同引用、变更原因相同
   ⇒ 归 `algorithms/common/`（该目录**不注册任何 algorithm_type** ⇒ 不会被
   误当成一条算法）。
3. **设备侧上限事实**（机台可设上限 `max_set_*` + 实测行程 `max_injection_stroke`）
   原本寄居在 `fuzzy/specs.py`，但越限识别、机台能力守卫、推荐值裁剪都要用
   ⇒ 它是**设备事实**、不是模糊算法的私有口径 ⇒ 先移到
   `algorithms/common/device_limits.py`（**第三批再细分**：只留「字段契约 + 查表」，
   **取值与校验下沉 service 层**，见下方「越限链路归位」公告）；
   `fuzzy/specs.py` 曾 re-export 这些名字 ⇒ **第三批已撤**（同一事实只留一个入口）。

4. **service 层的跨链路共用件**（越限守卫 / 参数提取 / 字段命名翻译）被**多条链路**
   （初始化 + 优化）共用，而 service 根目录是「一个业务用例一个文件」的按领域平铺
   ⇒ 归 `services/shared/`（**按角色**分组，与 `optimize_chain/` 的**按领域**
   分组并存）。命名用 `shared/` 而非 `common/`：`algorithms/common/` 是**算法层
   零依赖底座**，`services/common/` 依赖 ORM ⇒ 同名不同义会把层级判读变成猜。
   （`optimize_common.py` → `param_naming.py`：它被两条链路共用，"optimize" 前缀误导。）
5. **service 包不 re-export 模块**（2026-11-23 用户拍板）：`services/__init__.py`
   只留分组说明、**不 import 任何业务模块** ⇒ ① `import process.services` 不再拉起
   整条算法链（实测 django / process.models / process.algorithms 均**未进** sys.modules）
   ⇒ 离线 runner 的「不碰 service 层启动期」更干净；② 调用方**按需导入**、自己
   指明来源（`from process.services.tuning import TuningService`）⇒ 看得到自己要什么。
6. **2026-11-24 收口修正**：入件判据（谁引用它 / 变更原因是否相同）在收口时被
   **重新判了一次** —— **算法命名空间（`field_names` / `device_limits`）只被 fuzzy
   一条线使用 ⇒ 不属「跨算法线公共」** ⇒ 归 `algorithms/fuzzy/`；
   `algorithms/common/` 只剩**真跨算法线**的两件（`field_contract` 字段契约机制 /
   `material_physics` 材料物理常量），仍是零外部依赖的底座。
   设备侧上限事实的**最终**落点：**来源声明 + 取值 + 组装 + 识别 + 拦截**全在
   `services/shared/param_limits.py`（service 层，**零算法层依赖**）；
   算法层只留**查表 + 跨命名空间翻译**（`algorithms/fuzzy/device_limits.py`）。

**结果**：`algorithms/` 根目录只剩 `base.py`（`algorithm_type` 的标注处 + 门面）
⇒ **看文件落在哪，就知道它是不是算法**（无歧义）。

**`algorithms/common/` 全目录零外部依赖**（2026-11-23 补）—— 每个模块只 import
同包相对模块或标准库，**不 import 任何算法包 / Django / ORM** ⇒ 依赖方向恒为
「算法包 / service 层 → common」，公共底座**不反向依赖任何算法线**
⇒ **无循环导入风险** ⇒ `common/__init__` 里可 re-export 各模块
（此前 `over_limit` 因 import `fuzzy.specs` 而不可；**第三批它已整体归 service 层**
⇒ 不再在本目录）。

**设备能力字段命名统一到 ORM 真名**（2026-11-23 第二批）——「同一台机器的同一项
设备能力，全项目只有一个名字」：

- **命名分裂已消除（HMI 上限组）**：初始化接口此前用 `max_set_injection_velocity` /
  `max_set_holding_velocity`（`_velocity` 别名），而 ORM / 调优接口 / 前端一律用
  `_speed` ⇒ 同一能力两个名字。统一取 **ORM 真名**（`_speed`）⇒
  **ORM 属性名 = API 字段名 = 算法契约名**三者合一，不需要任何映射表；
- **初始化接口补齐 3 个 `max_set_*`**（松退压力 / 松退速度 / 计量背压）：此前多传的
  字段被 pydantic `extra="ignore"` **静默丢弃**，直到专家契约校验报「缺失」才暴露
  （第三方拿到 400，却看不出是哪一层吃掉了字段）⇒ 现初始化接口能承载
  **专家契约的全部必填上限字段**；
- **真相源 = ORM，不是「一份共享字段清单」**（用户口径：算法是独立单元，specs 各自
  独立，公共的只是校验方法）⇒ 字段真名对齐 ORM；**字段集合归各算法线自己决定**
  （expert 22 个 key / fuzzy 11 个，fuzzy ⊂ expert —— 这个差异是设计使然，不是漂移）。
  ⚠️ **刻意不做**：不设共享清单当基准、不约束两条 spec 集合相等 ——
  那会把公共清单变成两条线的最大公约数，任何一方多要一个字段都得改公共件；
- **护栏**：`backend/tests/test_spec_contract_alignment.py`（7 例）只护三件各线独立
  成立的事：① 一份 spec 内 `key == attr_name`；② `attr_name` 是 ORM 真实属性；
  ③ 对外 schema ⊇ 对应算法契约的**必填集**（单向包含，不要求相等）。

**验收**：pytest **187 passed**（180 + 新增 7 条契约对齐护栏）；零依赖不变量 **PASS**；
离线 runner（`run_demo.py --check`）退出码 **0** 且全程 **0 次 SQL**；
expert 离线 smoke 10/10 exit 0。

**遗留（待拍板，已在护栏里挂账）**：
- 上一轮登记的「`common/over_limit.py` 仍 import `fuzzy.specs` ⇒ 公共底座反向依赖
  某条算法线」已解除（**第三批**：`over_limit` 整体迁到 `services/shared/over_limit.py`，
  `common/device_limits.py` 只留契约 + 查表，`fuzzy/specs.py` 已**撤掉** re-export）；
- 本批登记的「设备能力字段两份真相源」已降为**命名层**：HMI 上限组已统一；
  **expert 设备极限组还有 3 个别名 key**（`max_injection_velocity` /
  `max_holding_velocity` / `max_decompression_velocity` —— 算法不消费、ORM 用 `_speed`）
  取舍待拍板：① 统一改名 ② 直接删除；
- 对外初始化接口缺 expert 必填的 `drive_system`（属机器主表字段）⇒
  **provided 入口对第三方目前必然 400**，要不要暴露到对外契约待拍板。

---

## ⚠️ 路径变更公告（2026-11-23 · 越限链路归位 · 第三批）

> **本轮把「参数上限校验」整条链路压到 service 层内部**（用户原话：
> 「说白了，算法根本就不知道 `device_limits.py` 24-29 我们程序是否有这些字段，
> 这些是 service 的 model 层面定义的，算法只有自己定义的一套参数命名……
> 我认为这里的参数上限校验，应该由 service 完成」）。

| 层 | 职责 | 位置 | 符号 |
|---|---|---|---|
| **算法层** | **查表**（**第七批**再瘦身：不再声明上限来源）：「怎么用一张上限表查某个参数」 | `algorithms/common/device_limits.py` | `param_family` / `lookup_limit`（原 `PARAM_LIMIT_FIELDS` / `POSITION_LIMIT_FIELDS` / `STROKE_FIELD` **已移 service 层**） |
| **service 层** | **来源声明 + 取值**：从 `machine_info` 挖出上限（**设定值类给表**、**位置类给标量**）+ 从来源清单派生族视图 | `services/shared/setting_limits.py` | `LIMIT_SOURCES` / `SETTING_FAMILY_LIMIT_FIELDS` / `POSITION_FAMILY_LIMIT_FIELDS` / `resolve_param_limits` / `resolve_stroke_limit` |
| **service 层** | **组装 + 识别 + 拦截**：行程标量 → 位置类上限表；当前值 vs 上限；命中 ⇒ 抛 `BizException` + 用户文案（**只收两张表**：入参表 + 上限表，不碰 `machine_info`） | `services/shared/over_limit.py` | `expand_position_limits` / `detect_over_limits` / `detect_blocking_over_limits` / `OverLimitItem` / `guard_setting_limit` / `guard_position_over_stroke` |

⇒ **「值 vs 上限」这条链路只跨 1 层**（service 内部的 2 个小模块）。

**算法层不再判入参超限**：

- `fuzzy/engine.py` 删掉整块「0) 输入体检」（那段判据 service 层已拦 ⇒ **永不命中**）；
- 设备上限表改由 **service 层解析好、经 `context` 传入**（`param_limits` /
  `position_limits`）⇒ 算法层**不碰 ORM 字段名**，只收「已经取好的表」；
- `fuzzy/specs.py` **撤掉 re-export**（`resolve_param_limits` / `lookup_param_limit` /
  `resolve_stroke_limit` / `lookup_position_limit` /
  `POSITION_LIMIT_FIELDS` / `STROKE_FIELD`）⇒ 同一事实**只留一个入口**；
- `diagnostics.py` 删掉 `over_limits` 空壳容器（引擎不再填它 ⇒ 恒为空）。

**等价性核对**（唯一一处差异，真实不可达）：旧 `lookup_param_limit` 是「仅族匹配」、
旧 `lookup_position_limit` 是「两级匹配」；统一为 `lookup_limit`（两级）后，
**裸族前缀**（如 `'IP'`）在设定值类表里会命中 100.0（旧为 `None`）。
真实参数名空间（`field_names.PREFIX_FIELD_ALIAS` / `FULL_FIELD_ALIAS`）**不存在**
这种形态 ⇒ 生产不可达；护栏 `tests/test_fuzzy_engine_limits.py` 已按新口径断言并注明边界。

**验收**：pytest **187 passed**（重构前后**一致**，零回归）。

### 第四批（同日追加 · 初始化链路补设定值类越限守卫）

用户拍板：「初始化链路补设定值类越限守卫」+ 命中处理「**拒绝 400**」
⇒ 与优化链路**同一守卫、同一错误码、同一文案**（不新造一套口径）。

| 链路 | 设定值类（设备安全红线） | 位置类（超注射行程） |
|---|---|---|
| 优化 | 预处理层（``guard_setting_limit``，判**入参**基线） | L4（``check_params.validate``，判**产出**） |
| 初始化 | **推理后立刻判初值**（``_guard_initial_params``） | **推理后立刻判初值**（``_guard_initial_params``） |

- **入口覆盖**：``initialize_from_masterdata`` / ``initialize_from_provided``；
- **不覆盖**：``initialize_from_condition`` —— 它**跳过推理算法**、直接复制源工艺的
  已有参数 ⇒ 没有「算法算出来的初值」⇒ 无初值可判（位置类同理）；
- **两道守卫成对执行**，**顺序 = 优化链路的判定顺序**（设定值类在前）；
- **命中即 400 拒绝**（初值机台根本设不进去 ⇒ 不产出错参数、不落库）；
- 归位后仍然满足「守卫层只收两张表」：``_guard_initial_params`` 内部先调
  ``setting_limits.resolve_*`` 取表，再把表交给守卫 ⇒ 守卫依旧不碰 ``machine_info``。

**实测（真实 expert 推理，非 mock）**：6 个场景（50g 基准 / 500g 冷流道 / 5g 小件 /
壁厚 6mm / 小机上限压低 / 未录行程）跑真实 ``ProcessInitializer.derive()`` ⇒

- **设定值类 0 项越限** ⇒ 新守卫**不会误拒**（expert 初值天然在机台可设定上限内）；
- 位置类仅「500g 冷流道」命中 4 项（``IL0`` / ``IL1`` / ``MEL`` / ``ML0`` 超 200mm
  行程）⇒ 属**既有行为**（位置类守卫早于本轮就已挂在初始化链路上），非本次新增。

**验收**：pytest **196 passed**（187 + 新增 9 条初始化链路护栏
``tests/test_initialize_over_limit_guard.py``）。

### 第五批（同日追加 · 识别层与拦截层合并成一个文件）

用户原话：「这两文件完全可以合并成一个，我觉得校验参数是一个很简单的功能，
没必要弄那么复杂」⇒ **``over_limit.py``（识别）与 ``over_limit_guard.py``
（拦截）合并为单个 ``services/shared/over_limit.py``**。

- **合并后的单一文件** = 常量（``LIMIT_SOURCE_*`` / ``BLOCKING_LIMIT_SOURCES``）
  + ``OverLimitItem`` + 识别（``detect_over_limits`` /
  ``detect_blocking_over_limits``）+ 文案（``format_limit_number`` /
  ``format_position_over_stroke_message``）+ 拦截（``_reject_if_over_limit`` /
  ``guard_setting_limit`` / ``guard_position_over_stroke``）；
- **函数名一律不动** ⇒ 调用点（初始化 / 优化 / L4 / 测试）只改 import 路径，
  **行为零变化**；
- 删掉 ``services/shared/over_limit_guard.py``（**路径变更公告**：旧路径
  ``services/shared/over_limit_guard.py`` → 新路径 ``services/shared/over_limit.py``）；
- **分层口径不变**：取值仍在 ``setting_limits.py``、字段契约仍在算法层
  ``device_limits.py`` ⇒ 「值 vs 上限」仍只跨 1 层（service 内部 2 个模块）。
  ⚠️ **第七批已收窄**：字段**契约**也从算法层移走 ⇒ 算法层只留查表
  （见下方第七批）。

**验收**：pytest **196 passed**（合并前后一致，零回归）。

### 第六批（同日追加 · 位置类上限的重复取值收敛）

用户原话：
> 「setting_limits.py 53-125 这两是一个东西 —— stroke 和 position 表示的都是位置，
> 依赖对象都是 max_injection_stroke，为什么要区分两个？」
> 「我不是太明白你这里实测注射行程字段是想表示什么」

**结论（三条）**：

1. **确实是重复** —— `resolve_stroke_limit`（标量）与 `resolve_position_limits`（表）
   取的是**同一个设备字段、同一个值**；且后者把同一个字段**读了 4 遍**
   （`POSITION_*_FIELDS` 的 4 个值全指向 `max_injection_stroke`）。
2. **`STROKE_FIELD` 不是新概念** —— 它就是 ORM 字段 `max_injection_stroke` 的
   **字段名别名**；之所以声明在算法层：算法层**不能反向依赖 service 层** ⇒
   字段名的声明必须住在算法层，service 层 import 它来取值。
   ⚠️ **第七批已改**：它是一个**上限来源字段** ⇒ 随「来源声明」一起归
   `services/shared/setting_limits.py`。
3. **两张契约表是同类的**（都是「参数族 → 设备上限字段名」）⇒
   `POSITION_DOMAIN_FIELDS` **改名** `POSITION_LIMIT_FIELDS`（与 `PARAM_LIMIT_FIELDS`
   对齐）。**但不合成一张表**：算法层有三处按「表里有哪些族」做筛选 ——
   推荐值裁剪（`fuzzy/engine._apply_machine_limits`）、判级论域上界
   （`fuzzy/specs.resolve_domain_limits`）、越限安全分层（`services/shared/over_limit`）
   —— 都假定「表里只有**设定值类**族」⇒ 合成一张会让位置类族混进**推荐值裁剪**与
   **判级论域上界**（位置类不是可调建议项，本就不参与裁剪）⇒ 行为变化。
   ⚠️ **第七批已改**：两张表**整体移入 service 层**，改由来源清单**派生**
   （`SETTING_FAMILY_LIMIT_FIELDS` / `POSITION_FAMILY_LIMIT_FIELDS`）⇒
   「不合成一张表」的理由不变（仍需分开），但**声明位置**换了。

**改动**：

| 文件 | 改动 |
|---|---|
| `algorithms/common/device_limits.py` | `POSITION_DOMAIN_FIELDS` → `POSITION_LIMIT_FIELDS`；`STROKE_FIELD` 注释写清「就是 ORM 字段名」 |
| `services/shared/setting_limits.py` | **删** `resolve_position_limits`（重复）；只留 `resolve_param_limits`（设定值类，读 `max_set_*`）+ `resolve_stroke_limit`（**标量**） |
| `services/shared/over_limit.py` | 新增 `expand_position_limits(stroke)` —— 按算法层契约把**行程标量**展开成位置类上限表（**唯一**的组装口） |
| `parameter_initialize.py` / `parameter_optimize.py` / `fuzzy/examples/*` / 4 个测试文件 | 调用点改为 `expand_position_limits(resolve_stroke_limit(machine_info))` |

⇒ **取值层只给「值」**（表或标量），**组装归识别层**（契约在算法层、数值来源在
service 层 ⇒ 组装落在两者之间）⇒ 不再抄第二张「同值四份」的表。

**验收**：pytest **196 passed**（零回归）；等价性实测
（`_dev_refs/_verify_range_limits.py`）⇒ 差异 **0**、位置类判定差异 **0**、
限值表与检查项一一对应 **True**（exit 0）。

### 第七批（2026-11-24 · 上限来源声明归 service 层 · 算法层只做字段映射）

用户原话（两条）：
> 「`device_limits.py` 1-185 那么算法的 limits 定义也就是有误了，算法只是起到一个字段映射的功能，并不考虑上下限的问题」
> 「算法层补充字段映射，不需要考虑上下限的问题，由服务层考虑，算法本身是不知道参数的上下限的」

⇒ **口径反转**：第三批的「契约归算法层、取值与校验归 service 层」收窄为
**「上限来源声明 + 取值 + 校验全归 service 层；算法层只留字段映射与查表」**。

**为什么**（用户判据）：算法层若持有「哪个族配哪个设备字段」⇒ 它就知道了
「这个参数有没有上下限」⇒ 与「算法本身是不知道参数的上下限」直接冲突。
而这些字段名（`max_set_*` / `max_injection_stroke`）本就是 **service 的 model
层面**的事实 ⇒ 声明就该住在 service 层。

**落法（A 方案 · 一份数据两个视图）**：

| 层 | 职责 | 位置 | 符号 |
|---|---|---|---|
| **算法层** | **字段映射**（纯命名） | `algorithms/common/field_names.py` | `to_algo_family`（业务参数键 → 算法族前缀，**新增**） |
| **算法层** | **查表**（族前缀解析 + 两级匹配） | `algorithms/common/device_limits.py` | `param_family` / `lookup_limit`（**两张表 + `STROKE_FIELD` 已删**） |
| **service 层** | **来源声明 + 取值 + 组装** | `services/shared/setting_limits.py` | `LIMIT_SOURCES`（唯一真相源）/ `STROKE_FIELD` / `SETTING_FAMILY_LIMIT_FIELDS` / `POSITION_FAMILY_LIMIT_FIELDS`（**派生视图**）/ `resolve_param_limits` / `resolve_stroke_limit` |
| **service 层** | **组装 + 识别 + 拦截** | `services/shared/over_limit.py` | `expand_position_limits`（改用 service 派生视图） |

**零重复声明**：`LIMIT_SOURCES`（业务键 → 上限来源字段）是**唯一真相源**；
`SETTING_FAMILY_LIMIT_FIELDS` / `POSITION_FAMILY_LIMIT_FIELDS` 由它
**经 `to_algo_family` 换键派生**（不是手写表）⇒ 改清单即改视图。

**必填等级筛选前移到 service 层**：`resolve_param_limits` 出表时按
`is_required_limit_field`（`fuzzy/specs.py`，读调优字段字典的 condition）筛掉
非必填等级的族 ⇒ `fuzzy/specs.resolve_domain_limits` **不再自己筛等级**
（只做「取值 + 转 float」）⇒ 算法层**不持有**「哪个族参与校验」的知识。

⚠️ **「不定义上下限」≠「不许用上界值」**：判级论域上界仍可**消费** service 送来的
上界值（`context['param_limits']`）—— 那是**消费值**，不是**定义来源**。
若连消费也禁掉 ⇒ IL / MEL 的「充填量第一优先」规则会集体失活
（位置类真实值域 27~716 远超经验域 IL [0,150] / MEL [0,200]）。

**改动**：

| 文件 | 改动 |
|---|---|
| `algorithms/common/field_names.py` | 新增 `to_algo_family(business_key)`（裸前缀 / 整段全名 → 算法族前缀；**纯命名**） |
| `algorithms/common/device_limits.py` | **删** `PARAM_LIMIT_FIELDS` / `POSITION_LIMIT_FIELDS` / `STROKE_FIELD` ⇒ 只剩 `param_family` / `lookup_limit` |
| `services/shared/setting_limits.py` | 接管 `STROKE_FIELD`；新增 `_derive_family_limit_fields()` + 两张派生视图；`resolve_param_limits` 加必填等级筛选 |
| `services/shared/over_limit.py` | `expand_position_limits` 改用 `POSITION_FAMILY_LIMIT_FIELDS` |
| `algorithms/fuzzy/specs.py` | `resolve_domain_limits` 去掉必填等级筛选（改为直接遍历传入表）；`__all__` 移除 `PARAM_LIMIT_FIELDS` |
| `algorithms/fuzzy/engine.py` | 仅注释同步（**引擎逻辑零改动**） |
| `tests/test_fuzzy_position_domain.py` | 改引 `POSITION_FAMILY_LIMIT_FIELDS` |

**验收**：pytest **192 passed**（零回归）；等价性脚本
`_dev_refs/_verify_interval_limits.py` ⇒ **RESULT: ALL PASS**；
派生视图与原手写表**逐项相等**（`SETTING MATCH: True` / `POSITION MATCH: True`）。

**附：严格度开关的形态（2026-11-24 用户定 · 只作为函数入参）**

用户原话：「目前就只是作为函数入参即可」⇒

- **外部来源 = 函数入参**：`guard_parameter_limits(..., strict=True)` 与
  `parameter_initialize._guard_initial_params(..., strict=True)` ⇒ **不外扩**为
  配置项、也**不进**对外接口入参；
- **默认值保持 `True`**（现状不变）：命中越限即 400；需要放宽的调用点
  **显式传 `strict=False`**（放行 + 返回越界项）即可 —— 函数入参形态正是为此保留；
- **非严格模式当前只「放行 + 报告」，不改参数值**：`find_over_limits` 是**纯识别**
  （只产出越界项、不改入参）⇒「自动补全（非严格模式）」**当前未实现**；
  **位置类是否也裁回行程内 ⇒ 待需要时再拍**（现状无任何代码依赖它）。

⚠️ **默认值仍为 `True` 的已知代价**（实测结论，供后来者参照）：真实库 64 condition
的历史落库行 **62.5% 越界**（位置类 186 / 设定值类 54）；真实初始化推理 8 个 condition
中 5 个命中位置类越界 ⇒ 「命中即 400」在这批数据上会**大面积拒绝**。
缓解手段只有一个：**调用点显式传 `strict=False`**。

---

## 〇、这份文档要解决什么

### 用户目标（原话）

> 「我当前想做的工作是这样的，就是将算法分层，每一层的工作互不影响，我不是要一次性完成所有的工作，因为我一次性审不过来」
>
> 「以上是我对这个函数流程的理解，还是我最初的方案，我不需要一次性完成每个阶段的详细功能，但是我每个阶段之间一定是互不干扰」

### 本轮的起点

用户逐段复述了 `backend/process/services/parameter_optimize.py::_infer_kernel`（L1417-1575）的 9 段流程，并提出两点判断：

1. **第 4 点「参数去噪」** —— 用户认为「这个应该属于算法部分的」
2. **第 8 点「零落地守卫」** —— 用户说「我其实没理解这是干什么用的，我认为参数校验都应该放在第 4 层」

### 本轮结论（三句话）

1. 用户的 9 段理解**基本准确**，与代码实际执行顺序一致。
2. 其中 **1 处归属需调整**（去噪：算法知识下沉、面向用户的表达留下）、**1 处需解答并改归属**（零落地守卫：不是第 4 层，是层间一致性守卫）、**1 处需拆分**（第 9 段：校验 vs 出口）。
3. 「层间互不影响」这个目标下，当前**只有一处真正的结构性跨层**（零落地守卫）⇒ 阶段 0 解决它之后，`_infer_kernel` 就是干净的 L1→L2→L3→L4 直线。

### 已拍板口径

| # | 口径 | 内容 | 日期 |
|---|---|---|---|
| 1 | **位置类参数物理下限** | **常量 10**（`vps_pos` / VPTL 等位置类整段参数）—— 用户：「这个本质需要根据产品来调整，我觉得现在你可以不纠结，就按照常量 10 作为下限即可」 | 2026-11-23 |
| 2 | **超限判定的归属** | **L4 统一判「产出是否超限」** —— 用户：「我的计划中，参数是否超限，这些问题都是由 L4 层来校验的，所以你在 L4 之前做参数是否超限的校验，我一直觉得很奇怪」⇒ **L1-L4 不做超限判定**；预处理层可拦**基线超限**（入参校验，见口径 #3）；L3 只在**求解时避开**已知约束（**约束 ≠ 校验**） | 2026-11-23 |
| 3 | **基线超限 = 入参错** | **超限直接拒绝，不进入 L1-L4** —— 用户：「这里报错是没问题的，超限直接拒绝不就行了？这里说明入参都是错的，我们就不需要强行调整参数了，**它不符合 L1-L4 层任何工作**」⇒ **基线超限**属**预处理层入参校验**（400）；只有**产出超限**才归 L4。<br>⚠️ **适用范围（2026-11-23 修正）**：这条**只适用于设定值类**（`guard_setting_limit` 已在预处理层）⇒ **位置类不适用**（基线位置超行程是常态，见 §五 阶段 1b） | 2026-11-23 |
| 4 | **拒不拒 = 严格度策略，不是分层问题** | 「其实拒绝和不拒绝是等价的，系统可以拒绝，也可以不拒绝，这就是 L4 的意义，如果你在别的地方又做出等价功能，那么整个语义就有冲突」—— **判定（产出是否合规）只在 L4 一处**；**直接拒绝 vs 返回给前端**是**系统严格度**的取舍（涉及设备安全 ⇒ 严格 ⇒ 拒；纯推理数据 ⇒ 可返回前端）。「L4 的意义 = 我可以很快去 L4 层定位，而不是还要关注别的地方」 | 2026-11-23 |

---

## 一、术语约定

| 术语 | 含义 | 代码位置 |
|---|---|---|
| **预处理层** | 三维上下文契约校验 + 缺陷选取（收敛成 1 条）+ 基线越限检查 | `parameter_optimize.py` L1430-1446 |
| **L1 推理** | 调引擎出**平级**建议（多条候选，不分主次） | L1448-1474 |
| **L2 裁决** | 结合调机场景决定用哪几条、按什么次序、谁让位 | L1476-1504 |
| **L3 整合** | 物理换算 + 锚点传导 + 联动调整 | L1506-1525 |
| **L4 校验** | **校验所有参数**（产出是否超限、差值越限、工艺窗口、锚点自检）—— **「产出是否超限」由 L4 统一判**；**基线超限（设定值类）**属预处理层入参校验 | L1531-1538 |
| **出口** | 量化 + 载荷组装 + 返回 —— **不是一层** | L1527-1529（量化）/ L1540-1558 |
| **守卫** | 横切关注点：设定值越限 / fail-fast / 位置类超行程（**阶段 1b：判定归 L4**） | L1441 / L1463 / ~~L1542~~（已挪进 L4） |
| **层间一致性守卫** | 判「上游说要调 vs 下游实际调成」 | **已消除**（阶段 0）—— 判定下沉 L3，主流程只读结论（L1516-1525）；详解见 §三「第 8 段详解」 |

---

## 二、「层间互不影响」的可检验定义

**定义**：每层只读上游**已固化的产出**，不回头修改上游的东西；每层对下游只提供**只读输入**。

**按此定义核对现状**（行号为注释精简后的当前状态）：

| 关系 | 现状 | 结论 |
|---|---|---|
| 预处理 → L1 | L1 只读 | ✔ 合规 |
| L1 → L2 | L2 **就地改** L1 的产出（`_apply_decision_status` L1500 写回 `decision_status` / `decision_reason`） | ⚠️ 违反 —— 但**是已拍板的设计**，见 §六 |
| L2 → L3 | L3 只读 `plan` | ✔ 合规 |
| L3 → L4 | L4 只读 `values` | ✔ 合规 |
| L2 ↔ L3 | ~~`_guard_zero_landing` 同时读 `plan.selection.kept` 与 `integrated.values`~~ | ❌ **唯一真正的结构性跨层** ⇒ **已消除**（阶段 0：判定下沉 L3，编排层只读结论） |

### 异常归属：「谁的问题谁判」

用户主张（2026-11-23）：

> 「我觉得每一层应该处理自己的异常……而不是应该抛给调用层，因为调用层并不知道会发生什么，这也是我说的每一层之间应该互不影响」

**这个主张成立，但需区分两件事**：

| | 含义 | 谁做 |
|---|---|---|
| **判定** | 「这件事是不是我的问题、我还能不能继续」 | **只有产生该信息的那一层知道** ⇒ 必须在本层判 |
| **呈现** | 「把这个结论变成用户看得懂的东西（错误码 + 文案）」 | 最外层做（service / 出口） |

⇒ 精确表述：**每层处理自己的异常 = 每层不把「自己能不能继续」的判断外包给上游；而「呈现」是出口的职责，不是上游的负担。**

**可操作的规律**（按各层现状逐条核对）：

| 异常 | 归谁 | 处置 | 现状 |
|---|---|---|---|
| L3 让位回退 / 锚点冲突 | L3 | 已有 `conflicts` / `superseded_fields` / `unresolved` 留痕 ⇒ **L3 内消化** | ✔ 已符合 |
| L2 规则没给出可用调整 | L2 | `yielded` / `deferred` 留痕（但**没有**「一条都没保留」的显式留痕）⇒ 基本属于 L2 内消化 | ⚠️ 部分符合（见 Q7） |
| **L3 判定「有保留项但值无变化」** | **L3** | 本层**无法继续**（不能返回「什么都没变」）⇒ 出结论，交出口呈现 | ❌ **现在在编排层判** |
| 上下文结构非法 | 预处理层 | 无法继续 ⇒ 上抛 | ✔ 已符合 |
| 引擎不可用 | L1 | 无法继续 ⇒ 上抛（fail-fast） | ✔ 已符合 |
| 参数差值越限 / 工艺窗口越界 | L4 | **只报不阻断** ⇒ L4 内消化（进 report） | ✔ 已符合 |

⇒ **规律**：**凡是「这一层还能继续往下走」的异常，就在这一层消化（留痕）；凡是「这一层没法继续」的异常，才上抛。**

**曾经唯一的违例**是零落地守卫 —— 编排层凭什么知道「值没变」是 L3 的问题？它只是**碰巧**手里同时有 `plan` 和 `integrated`。
⇒ 用户察觉到的「单独列出来有点奇怪」，本质是察觉到了这处违例。
⇒ **已于 2026-11-23 消除**（阶段 0：判定下沉 L3 ⇒ 见 §五 阶段 0）。

**它对阶段 0 的约束（更严的验收标准）**：

| 约束 | 怎么查 | 状态（2026-11-23） |
|---|---|---|
| L3 段内**不含任何判定逻辑** | `apply_plan` 内部完成判定 | ✅ |
| service 层那段**只读 `integrated.landing_blocked`**、**不读 `plan`** | 判定信息完全来自 L3 | ✅ |
| service 层**不决定「要不要继续」** | L3 已经决定了（`landing_blocked` 非空即「继续不了」） | ✅ |
| service 层那段**不做业务决策**，只做「结论 → 错误码 + 文案」 | 与 `OptimizeDataValidator` → ValueError → BizException 同构 | ✅ |

**⇒ 对其它阶段无影响**：阶段 1 / 2 / 3 的现状均符合上述规律，不需要改动。

### 判定唯一性：同一件事只能有一个判定点

用户口径（2026-11-23）：

> 「其实拒绝和不拒绝是等价的，系统可以拒绝，也可以不拒绝，这就是 L4 的意义，**如果你在别的地方又做出等价功能，那么整个语义就有冲突**」
> 「L4 管理产出后的参数，一旦算法给出的结果出问题，**我可以很快去 L4 层定位**，而不是还要关注别的地方，这才是设计的意义」
> 「至于 L4 层给出的结果是直接拒绝，还是返回给前端，这个是**系统严格度**的问题……这从来不是不得不的问题，只是**架构分层和取舍**的问题」

⇒ **架构上等价的**：L4 判「产出是否合规」这一件事 —— **判在哪是分层问题（必须唯一）**；**拒不拒是严格度策略（可配）**。
⇒ **推论（硬约束）**：**同一判据只能有一个判定点**。别处再做一次等价判定 ⇒ 两处结论可能漂移 ⇒ 用户定位不到 ⇒ 语义冲突。

⇒ **落到本方案**：`guard_position_over_stroke`（**已删**，原 `parameter_optimize.py` L1544-1555）判的就是「产出是否超限」⇒ **它有歧义**（超限该由 L4 判）⇒ 阶段 1b 已挪进 L4（`detect_position_violations`）。
⇒ 实施时的等价判定排查见 §五 阶段 1b「实施注意事项」（属实现细节，不影响审阅主线）。

### 守卫的归属判据：读「产出数据」还是读「决策结构」

用户原则（2026-11-23）：

> 「每一层做自己的工作，如果出现参数异常，也是由各自层自己管理，所以不存在外部检查参数这种情况」

⇒ 这条原则落到守卫上，需要一个可操作的判据：

| 守卫读什么 | 是否跨层 | 归属 |
|---|---|---|
| 只读上游的**产出数据**（`values` / `params` / 基线数值） | **否** | ✔ 可留在编排层（横切守卫） |
| 读上游的**决策结构**（`plan.selection` / `decision` / `kept` / `yielded`） | **是** | ❌ 应下沉到该层内部 |

**三个守卫逐个核对**：

| 守卫 | 读什么 | 判定 | 归属 |
|---|---|---|---|
| `guard_setting_limit`（L1441） | **基线**数值（转 algo params） | 只读产出 | ✔ **预处理层**（入参校验）—— 超限即 400，**不进入 L1-L4**（口径 #3） |
| `guard_position_over_stroke`（~~L1549~~ 已删） | `integrated.values`（**产出**） | 只读产出 | ⚠️ 原判「✔ 编排层」**已撤回**（2026-11-23）⇒ **全部归 L4**（产出超限的唯一判定点）⇒ 阶段 1b **删掉编排层这道** |
| ~~`_guard_zero_landing`~~ ⇒ 现**内联在主流程**（L1516-1525） | ~~`plan.selection.kept` + `integrated.values`~~ ⇒ 现只读 `integrated.landing_blocked` | ~~读决策结构~~ | ❌ 跨层 ⇒ 阶段 0 **已下沉 L3** |

⇒ **原结论「位置类超行程不属于 L3」已撤回**（见下方小节）⇒ 现归为 **阶段 1b**：**超限判定归 L4**（用户口径）+ **L3 求解时避开超限**（约束，不是校验）+ **编排层那道守卫删除**。

**⚠️ 关键区分：「基线超限」与「产出超限」是两件事**（2026-11-23 用户口径）

| | 判据 | 落点 | 动作 |
|---|---|---|---|
| **基线超限**（**仅设定值类**） | **入参本身超** ⇒ 入参是错的 | **预处理层**（`guard_setting_limit`，已在位） | **400 拒绝**，**不进入 L1-L4** —— 「参数都错了，谈不上『调』，它不符合 L1-L4 层任何工作」 |
| **产出超限** | L1-L4 **算出来的值**超 | **L4** | 判定 + 报告（阻断与否见 Q10） |

**⚠️ 这条区分只适用于「设定值类」（2026-11-23 修正）**：**位置类超行程不能按「基线超 = 入参错」处理** ——
实测 `MEL` / `IL0` / `ML0` 真实值 **122~758** vs 行程 **200**（`specs.py` L863：「多数工况值超行程」）
⇒ **多数工况的基线位置本来就超行程** ⇒ 挪进预处理层会**大面积误拒**。
⇒ 故：**位置类超行程全部归 L4**（判最终产出），**不拆**。
⇒ 现状那道「一道覆盖两种、无法区分」的问题**因此不是靠拆解决，而是靠把判定整体移到 L4**（L4 判的是最终产出那一份值，两种情形都体现在其中）。

#### ⚠️ 「位置类超行程留在编排层」—— **该结论已撤回**（2026-11-23，两轮修正）

本节原先的结论是「位置类超行程不下沉到 L3，留在编排层合规」，**该结论已撤回**。

**第一轮撤回理由**：当时的前提是「超限是关于**参数值**的静态事实核对，参照系是机台能力而非 L3 的事」——
**这个前提不成立**。用户场景（`vps_pos = 30` ⇒ MEL 超限 ⇒ 调 `vps_pos = 15` 固定 MEL 继续调）证明：
**超限会反过来改变本轮方案** ⇒ 它是**整合过程必须满足的约束**，不是事后的事实核对。

**第二轮修正（用户口径）**：
> 「我的计划中，参数是否超限，这些问题都是由 L4 层来校验的，所以你在 L4 之前做参数是否超限的校验，我一直觉得很奇怪」

⇒ 最终归属（**不是「下沉到 L3」，而是拆成两件事**）：

| | 是什么 | 归属 |
|---|---|---|
| **约束** | 求解时就知道会不会超限 ⇒ 主动选一个不超限的方案 | **L3**（求解过程的一部分） |
| **校验** | 事后判定产出是否合规 | **L4**（**唯一归属**） |

⇒ 编排层那道「检出即拒绝」**删除**（不是挪位置、不是降级）。
⇒ 详见 **阶段 1b**。

**判据本身的修正**：守卫归属不能只看「读不读上游的**决策结构**」，还要看「**这个约束会不会反过来改变方案**」——
若会，它就不是「检查」，而是「**约束**」，必须与产生方案的那一层在一起。
⇒ 但「**约束在哪求解**」与「**校验在哪判定**」是**两件事** ⇒ 约束进 L3、校验进 L4。

#### 附带发现（仍成立）

位置类超行程同时覆盖「**基线本来就超**」与「**本轮推过头**」，但只看 `integrated.values` ⇒ **无法区分是哪一种** ⇒ 用户看到的文案是笼统的。
⇒ 移到 L4 后**问题仍在**（L4 也只看产出值）⇒ 要区分就得**同时拿到基线值** ⇒ 见 §七 **Q10**（阻断语义）。

---

## 三、现状：`_infer_kernel` 的实际流程

| # | 段（用户编号） | 行号 | 调用 | 实际归属 |
|---|---|---|---|---|
| 1 | 整理入参，决定给算法的缺陷信息 | L1434-1439 | `select_defect`（`services/optimize_chain/defect_selection.py`） | 预处理层 |
| — | （三维上下文契约校验） | L1432 | `_validate_optimize_inputs` → `OptimizeDataValidator.validate` | 预处理层（**已收进预处理层段**） |
| 2 | 调算法前，确认当前参数是否超可设定上界 | L1440-1446 | `guard_setting_limit` → `detect_blocking_over_limits` + `resolve_param_limits` | 守卫 |
| 3 | 组装算法入参并调用算法 | L1450-1458 | `_compose_algorithm_context` → `_call_algorithms` | L1 |
| — | fail-fast（引擎无产出） | L1462-1471 | 抛 `ERROR_OPERATION_FAILED` | 守卫 |
| 4 | 参数去噪 | L1473-1474 | `_normalize_recommendations` | **待调整**（见阶段 2） |
| 5 | 实际调机过程和调机逻辑 | L1477-1490 | `build_scenario_context` → `derive_stage_progress` → `sorted_scenario_strategies` → `select_strategy`（**已摊平进主流程**） | L2 **备料** |
| — | 阶段进度留痕 | L1485 | `stage_progress.to_trace()` | L2 |
| 6 | 结合调机场景决定用哪个方案 | L1492-1498 | `_decide_plan_by_strategy` → `collect_candidates` + `build_plan` | L2 裁决 |
| — | 裁决状态回填（就地） | L1499-1502 | `_apply_decision_status` | L2 |
| 7 | 生成调整后参数 + 联动调整 | L1506-1511 | `apply_plan`（`algorithms.integrate_params`） | L3 |
| — | 位置类超行程 | ~~L1549-1554~~（**已删**） | ~~`guard_position_over_stroke`~~ ⇒ 改为 L4 `detect_position_violations` | 守卫 —— **阶段 1b：判定归 L4**（2026-11-23 已实施） |
| — | 差值越限 | L1531-1536（`validate` 调用） | `RANGE_CHECKS` + `resolve_range_limits`（**已接参照系**，2026-11-23） | L4 校验（阶段 3a ✅） |
| 8 | 零落地守卫 | L1516-1525 | **内联在主流程**（读 `integrated.landing_blocked` ⇒ 直接抛 `BizException`；判定在 `integrate_params.apply_plan` 内部） | **L3 自检**（阶段 0，2026-11-23 已实施） |
| 9 | 校验：越界 | L1531-1538 | `validate` | L4 校验 |
| — | 出口定稿：量化 | L1527-1529 | `_quantize_numeric_fields` | 出口（**量化必须在前** —— L4 判的是最终产出） |
| — | 位置类超行程拒不拒 + 载荷组装 + 返回 | L1540-1558 | `format_position_over_stroke_message` + `_build_suggestion_payload` | 出口 |

### 第 8 段详解：零落地守卫

**代码**：`parameter_optimize.py` L1516-1525 → **内联在主流程**（`if integrated.landing_blocked:` ⇒ 直接抛 `BizException`）；判定在 `integrate_params.apply_plan` 内部（L3 自检）

⇒ ⚠️ **形态说明（2026-11-23）**：判定下沉前它叫 `_guard_zero_landing` —— 当时它**自己判**（读 `plan.selection.kept` + 比对数值）⇒ 叫「守卫」名副其实。判定下沉后它**什么都不判**，只「读 L3 结论 → 抛异常」⇒ 先改名 `_raise_if_landing_blocked`，**再直接内联成 `if`** ⇒ 主流程里一眼看到「一个值都没变 ⇒ 中止」，不再隔着一个黑盒函数。

#### 它在防什么

第 2 层裁决说「本轮要调 A 和 B」，第 3 层整合时**两条都被打回**：

| 被打回的方式 | 机制（`integrate_params`） | 后果 |
|---|---|---|
| **让位回退** | `FREEDOM_OVERRIDES` —— 某些量让位给另一些量（如保压压力让位给保压速度） | 被让位的直接改动**不生效**，值回退为当前值 |
| **硬约束未处理** | G2 回抽链（各段熔胶位置必须严格递增）等硬约束 | 直接改动的量**被回退**，不生效 |

⇒ 结果：**第 2 层明明裁决出了建议，第 3 层整合完一个数值都没动。**

#### 不拦会怎样

不拦的话，这条路径会**走完全程**：

```
裁决出 2 条建议（decision_status = adopted）
   ↓
整合值 == 基线（一个数都没动）
   ↓
载荷照常返回 —— 前端显示「一屏建议」+ 状态「已应用」
   ↓
_create_new_round(baseline) ⇒ 新轮次参数 == 父轮参数
   ↓
用户照着建议调机 ⇒ 参数还是那个值 ⇒ 白调一轮，系统里还多了一模一样的一轮
```

⇒ 拦下来后给的是人话：

```
本轮调整无法落地（让位回退：inj_pres_1→inj_spd_1；硬约束未处理：G2 回抽链：…）
```

文案素材取自 `IntegratedParams.superseded_fields`（让位回退）与 `IntegratedParams.unresolved`（硬约束未处理），由 `_zero_landing_detail`（L706-726）拼。

#### 触发条件（两个都要满足）

**【已下沉到 L3】** 判定现在在 `integrate_params.apply_plan` 内部（L3 自检）：

```python
if not plan.kept:                                  return None   # ① 第2层没保留任何候选 → 不归它管
if diff_numeric_fields(baseline, outcome.values):  return None   # ② 确实动了 → 不归它管
return tuple(plan.kept)   # ③ 说好了要调却一个数都没动 → 落地被拦住
```

编排层（service）现在**只读结论**：

```python
if not integrated.landing_blocked:
    return
raise BizException(ERROR_OPERATION_FAILED, '本轮调整无法落地（%s）' % detail)
```

⇒ 只拦「**说好了要调**」且「**结果一个数都没动**」这一种组合。

#### 为什么不能放第 4 层 —— 两个参照系不同

| | 参照系 | 举例 |
|---|---|---|
| 第 4 层 `validate()` | **参数自身的物理/工艺约束** | 「保压时间 3.5s 落经验区间（2-8s）之外」—— 跟有没有说要调它无关 |
| 零落地守卫 | **上游的产出**（L2 说要调 ↔ L3 实际调成） | 「说要调 inj_spd_1，整合后它还是 50」—— 参数本身完全正常，是**层与层对不上** |

⇒ 前者要「参数 ↔ 参照系」，后者要「L2 产出 ↔ L3 产出」，**合并不了**。

#### 归属判断：它本来就属于第 3 层

判据是「L3 的产出（`integrated.values`）vs L3 的入参（`baseline` / `plan`）」⇒ 参照系完全落在第 3 层内。

它现在看着「单独列出来有点奇怪」，是因为**被放在了编排层**（原 L1558），而它的判定**不需要编排层提供任何额外信息** —— `apply_plan(baseline, plan, ...)` 的入参本来就同时带着这两样。

⇒ 正确形态是：**L3 自己判 ⇒ 在 `IntegratedParams` 上留自检结论 ⇒ service 层只负责翻译成业务异常**（见 §五 阶段 0）—— **已落地（2026-11-23）**。

#### 它「不管」的那一种形态（重要）

条件 ① 里 `plan.kept` 为空时**直接返回、不报错** —— 「规则没给出可用调整」属于另一回事。

这条路径的后果**同样是建出一个与父轮参数相同的轮次**（建议列表空、参数没动、接口返回成功）。
⇒ 这是**现状的既定行为**（零落地自检不覆盖「上层一条候选都没保留」的情形），本计划**暂不改动**，但在此显式记录其代价。

#### 相关空窗（另一条通往同一后果的路）

`fail-fast` 判的是「引擎原始产出」（L1463），**去噪在其后**（L1474）⇒ 若引擎有产出但全是零变化项，去噪后为空，同样走「建空转轮次」这条路。

### 依赖模块事实（供核对）

| 事实 | 位置 |
|---|---|
| `integrate_params` 有**两个**公开整合函数：`integrate(values, previous)`（参数集自洽）与 `apply_plan(baseline, plan, previous, fill_weights=)`（计划落地） | `integrate_params.py` L444 / L505 |
| `apply_plan` **只被优化链路调用**；初始化链路走 `integrate(flat)` | `parameter_optimize.py` L1508 / `parameter_initialize.py` L680 |
| `IntegratedParams` 携带 `values` / `direct_fields` / `derived_fields` / `superseded_fields` / `conflicts` / `unresolved` / `landed` / `fill_target` | `integrate_params.py` L337-359 |
| ⚠️ `IntegratedParams.touched` 判的是「联动 / 让位 / 回退 / 检出冲突」，**不含 `direct_fields`** ⇒ 它为 True **不代表值变了** | `integrate_params.py` L361-368 |
| `diff_numeric_fields(previous, current)` 在同文件，是「值有没有变」的判据 | `integrate_params.py` L411 |
| `check_params.validate(params, limits=None, windows=None)` —— **`limits` 缺省即不做差值越限、`windows` 缺省即不做工艺窗口**，锚点自检永远跑 | `check_params.py` L385-416 |
| `RANGE_CHECKS` / `WINDOW_CONSTRAINED_FIELDS` 已定义，但**生产代码 0 处传入参照系** ⇒ 这两类检查从未在生产链路启用 | `check_params.py` L82 / L171 |
| 传入参照系的**只有测试**（手写字典） | `tests/test_check_params_layer.py` L139 / L160 |
| `parameter_initialize.py` **没有**零落地守卫 | 已 grep 确认（无 `landing_blocked` / `零落地` / `diff_numeric_fields`） |
| `tuning_strategy.py` 承载「调机过程与调机逻辑」：`STAGE_ORDER` / `SCENARIO_STRATEGIES` / `derive_stage_progress` / `sort_defects_by_stage` | `tuning_strategy.py` L87-152 / L403 |
| 两处 `to_algo_params` 转换位置不对称：`guard_setting_limit` 由**调用方**转（`parameter_optimize.py` L1442），`guard_position_over_stroke` 由**被调方内部**转（`services/shared/over_limit.py`） | 已确认 |

---

## 四、目标分层图

```
预处理层  缺陷选取（收敛成 1 条）+ 三维上下文契约校验
   ↓
[守卫]    **基线准入校验**（推理前）：设定值类越限（设备红线）+ 位置类超行程（机台行程）
         ⇒ 命中即 400，**不进入 L1-L4**（入参就是错的，谈不上「调」）
         ⚠️ 现状位置类那道在**编排层**且混了「产出超」⇒ 阶段 1b 拆开
   ↓
L1 推理   组装上下文 → 调引擎 → 汇总选优 → 规范化（业务名 + 中文文案）
   ↓
[守卫]    fail-fast（引擎无产出）
   ↓
L2 裁决   读策略表（备料）→ 场景匹配 → 候选准入 → 裁决 → 状态回填
   ↓
L3 整合   物理换算 → 锚点传导 → 联动调整 → 自检（落不了地 ⇒ 报错）
         ▸〔阶段 1b〕求解时避开设备能力约束（行程上限 / 物理下限）⇒ 能化解则化解
   ↓
L4 校验   参数合法性 —— **产出超限的判定在此**（差值越限 / 位置类超行程 / 工艺窗口 / 锚点自检）
         （基线超限已在预处理层拒了 ⇒ 这里报出来的必然是「本轮推过头」）
   ↓
出口      量化 + 载荷组装 + 返回
```

**与用户 9 段的四处差异**：

1. **守卫横切出来** —— 越限 / fail-fast / 超行程不属于任何一层，它们是横切关注点。
2. **用户的第 5 段并进 L2** —— 它是 L2 的**备料**（读表），裁决在第 6 段。
3. **用户的第 8 段并进 L3** —— 见阶段 0。
4. **用户的第 9 段拆成 L4 + 出口** —— 见阶段 1。

### 各层的边界（源码里不写，文档里写）

**2026-11-23 起**：`_infer_kernel` 主流程的注释只留「**这一层干什么 / 输入从哪来 / 产出到哪去**」；设计约束与口径推理全部收进本文档，源码不再复述（避免同一语义两处展开）。

**L2（筛选规则）的边界** —— 只做规则筛选，**不碰参数**：

| 判据 | 归哪层 | 理由 |
|---|---|---|
| 「这个字段本机有没有值」 | **不在 L2 判** | L2 不读参数集 |
| 「这是不是工艺量」 | **候选准入**（进 L2 之前） | 命名契约：静态字段字典 ⇒ 非工艺量（`IPOS` 这类规则库专用参数）不进候选，不靠下游兜底 |
| 「让位对象当前有没有值」 | **不在 L2 判** | L2 不预判「改了会不会白改」 |
| 「改成多少」（`MEL` 标 → 计量位置的物理换算） | **L3** | L2 只带出「MEL 目标值 + 口径」 |

**L2 备料（策略数据怎么来）** —— **已摊平进主流程**（2026-11-23；`services/strategy_inputs.py` 已删除，service 层不再有「策略装配」中间层）：

| 步骤 | 产出 | 说明 |
|---|---|---|
| `build_scenario_context` | `ScenarioContext` | 实际情况：缺陷码 / 实测重量 / 制品总重 / 充填缺口，外加本轮处理的是哪条缺陷 |
| `derive_stage_progress` | `StageProgress` | 阶段进度：哪些阶段还有缺陷、当前该推进哪一步（**只推导，不裁决**） |
| `sorted_scenario_strategies` → `select_strategy` | `ScenarioStrategy`（可能为 `None`） | 读调机策略清单并按当前情况匹配；**匹配不上就不裁决**（与「不接第2层」行为一致） |

⇒ 三步都在算法层（`algorithms/decide_direction.py` + `algorithms/tuning_strategy.py`）；主流程里逐步摊平成独立变量，不再用结构体包一层。

**MEL 的翻译顺序**（歧义消解归 L2）：

算法返回的 `param` 是**算法命名空间**（`IV0` / `BT1`），必须先译回**业务字段名**（`inj_spd_1` / `brl_temp_1`）才能当候选；
**裁决定在 MEL 翻译之前** ⇒ 否则只看得到「调计量位置」，看不见 MEL 的意图，规则无处安放；
⇒ L2 裁的是「**MEL 这条建议要不要用**」，**翻成计量位置是 L3 的事**。

**L3（应用规则）的边界**：

- **「改成多少」在 L3 算** —— L2 只给「调哪个 + 什么口径」⇒ `MEL` 这类派生量的物理换算（标 → 计量位置）在这里做，它手上有旧值（`previous`）⇒ 换算得出。
- L3 放在出口之前 ⇒ **落库值与响应值同源**（响应体就是这份 dict）。

**L4（校验参数）的边界**：

- **产出是否超限只在这里判**（超限判定的唯一落点）—— 判据集 = 整合后的**最终产出**（落库 / 响应的同一份值）⇒「基线本来就超」与「本轮推过头」都体现在这份值上，**无需分开判**。
- 参照系（机台实测注射行程）由**设备**给 ⇒ **缺行程即不判**（缺数据不等于参数不合理）。
- 基线位置类超行程是**常态**（实测 `MEL`/`IL0`/`ML0` 真实值 **122~758** vs 行程 **200**）⇒ 不能当入参拒。
- 出口参数统一量化（最多 2 位小数）⇒ 落库与响应同源；**建议文案里的值不量化**（`applied_value` 取未量化的 `integrated.values`，`recommended_value` 取算法原始推荐值）⇒ 与前端 `appliedText` 的 1e-9 比较**同口径**（两边都不量化）⇒ 不误判。

**出口的边界**：

- 位置类超行程 = 产出不可落地 ⇒ 检出即**拒绝本轮优化**（不回退旧值、不剔建议）：这个产品在这台机上做不出来 ⇒ 用户改不了 ⇒ 出路只有换机（文案由守卫专区统一出 ⇒ 与初始化链路逐字一致）。
- 出口只**读结论 + 决定拒不拒**（判定在 L4）。

---

## 五、改造阶段（逐个可审、逐个可独立验收）

### 阶段 0：零落地守卫下沉到 L3 —— ✅ **已实施（2026-11-23）**

**目标**：消除唯一的结构性跨层，让 `_infer_kernel` 变成干净的 L1→L2→L3→L4 直线。**（已达成）**

**归属判断**：它语义上就是 **L3 的自检** —— 判据是「L3 的产出 vs L3 的入参」，参照系完全落在第 3 层内。现在之所以显得「单独列出来有点奇怪」，正是因为它被放在了编排层（L1558），而它的判据其实不需要编排层提供任何额外信息。**（异常归属依据见 §二「谁的问题谁判」）**

**为什么它能下沉**（已核实，非推测）：

- `apply_plan(baseline, plan, previous=...)` 的入参**本来就同时有 `baseline` 和 `plan`** ⇒ L3 自己就能判「说要调却没调成」
- `IntegratedParams` 已带 `superseded_fields` / `unresolved` / `conflicts` ⇒ `_zero_landing_detail` 要的素材一样不缺
- `diff_numeric_fields` 与 `apply_plan` **同文件** ⇒ 不新增依赖
- `apply_plan` **只被优化链路调用**（初始化走 `integrate`）⇒ 本阶段**不影响初始化链路**

**⚠️ 新查到的事实（决定了形态）**：

`integrate_params.py` 目前 **0 个 `raise`**；`decide_direction.py`（L2）同样 **0 个 `raise`**。
⇒ **算法层既有风格是「纯计算 + 留痕，不抛异常」** —— 问题用 `unresolved` / `conflicts` / `superseded_fields` 表达，而不是抛。
⇒ 所以下沉后的形态**不是**在 `apply_plan` 里抛异常，而是：

| 层 | 职责 |
|---|---|
| **L3（`apply_plan`）** | 内部判定「有保留项但值无变化」⇒ 在 `IntegratedParams` 上置一个**自检结论字段**（如 `landing_blocked: Optional[str]`，装人话说明）。**判定逻辑 100% 在 L3** |
| **service 层** | 看到该字段 ⇒ 抛 `BizException(ERROR_OPERATION_FAILED, '本轮调整无法落地（…）')`。**只做异常翻译，不再读 `plan`** |

⇒ 这与项目既有模式同构：`OptimizeDataValidator.validate` 抛 `ValueError` → service 层 `_validate_optimize_inputs` 转 `BizException`（`parameter_optimize.py` L1050-1078）。

**改动清单**：

| 文件 | 改动 | 状态 |
|---|---|---|
| `backend/process/algorithms/integrate_params.py` | `IntegratedParams` 增加自检结论字段；`apply_plan` 内部做判定并填充该字段（**不抛异常**） | ✅ 已做 |
| `backend/process/services/parameter_optimize.py` | 原 L1558 改为「读 L3 自检结论 → 转 `BizException`」；原 `_guard_zero_landing` 的判定部分迁入 L3，**文案拼接留在 service 层**（service 才知道「本轮调整无法落地」这句面向用户的话）；判定下沉后先改名 `_raise_if_landing_blocked`，**2026-11-23 再内联成主流程里的 `if`**（不再隔黑盒函数） | ✅ 已做 |

**验收标准（可检验）**：下沉后 `_infer_kernel` **不再用 `plan` 做判定** —— 判定信息全部来自 L3 的自检结论。

**验收结果（2026-11-23）**：✅ 通过 —— `pytest backend/tests` ⇒ **113 passed**（零回归）；新旧判据等价性实测 **4/4 一致**（拦 / 不拦 / 错误文案逐字相同）。

**额外收益（两个分支都归位）**：下沉后，原先那个「不管」分支也归位了 ——

| 分支 | 现状 | 下沉后 |
|---|---|---|
| L2 一条候选都没保留 | 编排层靠读 `plan.selection.kept` 判断「不归我管」 | **编排层不再读 `plan`** —— 这个状态由 L3 自检一并判掉（L3 本来就拿 plan 当入参，判它是合法的） |
| L3 有保留项但值无变化 | 编排层跨层判定 | **L3 自检结论** ⇒ 编排层只读结论 |

⇒ 两个分支都由**能判它的那一层**判定，编排层彻底不碰 `plan` 的内部结构。**（已落地）**

⚠️ **残留一处（非判定）**：`_infer_kernel` 里还有 `_apply_decision_status(algorithm_recommendations, plan.selection)` —— 它是「把 L2 的裁决状态标注回建议列表」（L2 产出 → 建议载荷的搬运），**不是判定** ⇒ 保留现状，属另一个议题。

⚠️ **但要诚实标注一点**：`StrategyDecision`（`decide_direction.py` L426-443）的留痕字段是 `kept` / `kept_reasons` / `yielded` / `deferred` / `order` / `scenario_code` —— **没有「一条都没保留」这种状态的显式留痕**（`unresolved` 是 L3 `IntegratedParams` 的字段，不是 L2 的）。
⇒ 也就是说：「L2 什么都没保留」这个状态目前**只有 `kept` 为空这一个事实**，没有配套的「为什么」留痕。
⇒ 是否要把这个状态也显式化，见 §七 **Q7**。

**⚠️ 实现注意**：

- **不能用 `IntegratedParams.touched`**（不含 `direct_fields`，为 True 不代表值变了）⇒ 必须用 `diff_numeric_fields(baseline, values)`
- 错误文案要保持现状口径：「本轮调整无法落地（让位回退：…；硬约束未处理：…）」

**实施落地形态（2026-11-23）与设计稿的偏差**：

| 项 | 设计稿 | 实际落地 | 理由 |
|---|---|---|---|
| 自检结论字段 | `landing_blocked: Optional[str]`（装人话说明） | `landing_blocked: Optional[Tuple[str, ...]]`（装**保留项**） | 算法层既有风格是「只留结构化事实、不写面向用户的中文措辞」⇒ 人话仍由 service 用 `superseded_fields` / `unresolved` 拼（`_zero_landing_detail` 原样不动） |
| 判据位置 | L3 内部 | L3 内部（`apply_plan` 末尾） | 判据 = L3 产出 vs L3 入参 |
| 判据内容 | `plan.kept` 非空 且 `diff_numeric_fields(baseline, values)` 为空 | **完全相同**（`plan.kept` == `plan.selection.kept`） | 行为零变化 |

**行为变化**：**无** —— 判据、错误码、用户文案、日志文案均逐字未变（等价性实测 4/4 一致）。

**验收（已完成）**：

- ✅ `pytest backend/tests` ⇒ **113 passed**（零回归）
- ✅ 新旧判据等价性实测 **4/4 一致**（含「有保留项但值未变」场景 ⇒ 同样的错、同样的文案）

**风险**：低。纯搬移。（已落地，无风险暴露）

---

### 阶段 1：拆分当前第 9 段（L4 校验 / 出口）—— ✅ **已收口（2026-11-23）**

**目标**：L4 只留「参数合法性」；量化与载荷组装归「出口」。

**实施结果**：

| 块 | 行号 | 内容 |
|---|---|---|
| 出口定稿（量化） | L1527-1529 | `_quantize_numeric_fields` |
| L4 校验 | L1531-1538 | `validate` + 结论（**只剩校验**） |
| 出口 | L1540-1558 | 拒不拒 + `_build_suggestion_payload` + 返回 |

**⚠️ 关键约束（与阶段 1b 耦合，改动时必须知道）**：**量化必须在 L4 之前**。

阶段 1b 的口径是「L4 判据集 = **最终产出**（落库/响应的同一份值）」⇒ 若 L4 改判**未量化**的值，边界值（200.004）会重新被误拒 ⇒ **阶段 1b 消除的假阳性会回来**。
⇒ 所以「量化归出口」指的是**归属**（它是出口的定稿步骤），**位置上**必须在 L4 前。

**行为变化**：**无**（纯结构调整；量化位置未动，校验逻辑未动）。

**验收（2026-11-23）**：

- ✅ `pytest backend` ⇒ **180 passed**（168 + 新增 12，零回归）
- ✅ smoke `verify_provided_smoke.py` ⇒ **6/6 PASSED**，exit 0
- ✅ `validate` 的入参只多了一个 `limits`（新增的差值越限参照系），四个识别函数未改

**⚠️ Q2 仍未拍板**：出口段是否**抽成独立私有函数**（`_build_response_payload` 之类）？本轮只做了「区块注释 + 量化独立成块」这一侧 ⇒ **未动函数结构**。

---

### 阶段 1b：产出超限判定归 L4 + 求解时避开设备能力约束 —— **判定部分已于 2026-11-23 实施**

**用户口径（2026-11-23，两条）**：

> ①「我的计划中，参数是否超限，这些问题都是由 L4 层来校验的，所以你在 L4 之前做参数是否超限的校验，我一直觉得很奇怪」
> ②「`parameter_optimize.py` 1459-1467 你这里不是有入参校验吗？这里报错是没问题的，超限直接拒绝不就行了？这里说明**入参都是错的，我们就不需要强行调整参数了，它不符合 L1-L4 层任何工作**」

⇒ **「参数是否超限」= L4 专属职责**（L1-L4 内部不做超限判定）。
⇒ ⇒ **基线超限（设定值类）**属**预处理层入参校验**（400 拒绝），**产出超限**才归 L4。

**⚠️ 第三条修正（2026-11-23 实施时发现）**：口径 ② 的「基线超限 = 入参错」**只适用于设定值类**。
实测 `MEL` / `IL0` / `ML0` 真实值 **122~758** vs 行程 **200**（`specs.py` L863：「多数工况值超行程」）
⇒ **多数工况的基线位置本来就超行程** ⇒ **位置类超行程不能挪进预处理层**（会大面积误拒）
⇒ **位置类全部归 L4**，**不拆**。

**触发场景**（用户原话要点）：

> `vps_pos = 30`，MEL 已经超限了，但其实可以通过调整 `vps_pos = 15`、固定 MEL 来继续调整（`vps_pos` 也有安全下限）

⇒ 这里有**两件不同的事**，必须分开：

| | 是什么 | 在哪 | 性质 |
|---|---|---|---|
| **约束** | 求解时就知道会不会超限 ⇒ **主动选一个不超限的方案** | **L3**（求解过程的一部分） | 不是校验 |
| **校验** | 事后判定产出是否合规 | **L4** | 用户口径 ✔ |

⇒ 「调 `vps_pos` 化解 MEL 超限」属于**前者** ⇒ L3 在反推时把行程上限当约束接进去；
⇒ 「这个值到底超没超」属于**后者** ⇒ L4 判。

**⚠️ 我此前两处误判（2026-11-23 修正）**：

| 我之前说 | 实际 |
|---|---|
| 「阶段 3 的参照系**没有数据源**」 | **只对 `windows` 成立**。`limits`（行程类）**有数据源**（`resolve_stroke_limit`）⇒ 接参照系是**接线活**，不是新建体系 |
| 「L4 里没有超限检查项」 | **L4 早就预留好了** —— `RANGE_CHECKS` 里有两条 `limit_source='stroke'` 的行程检查项，其中 `meter_end_position` **就是 MEL 超限**；只是 `limits` 从未传入 ⇒ 从未启用 |

**L4 已有的行程检查项**（`check_params.py` L82-95，已存在，从未启用）：

```python
RANGE_CHECKS = (
    {'range_id': 'injection_stroke',
     'label': '注射行程（末段熔胶位置 − VP 切换位置）',
     'members': ('met_pos_{last}', 'vps_pos'),
     'limit_source': 'stroke'},
    {'range_id': 'meter_end_position',
     'label': '储料终止位置',
     'members': ('met_end_pos',),
     'limit_source': 'stroke'},
)
```

⇒ **`meter_end_position` 正是用户场景里的「MEL 超限」**；`injection_stroke` 是差值口径（末段熔胶位置 − `vps_pos`）。
⇒ 且 `limit_source='stroke'` ⇒ 限值就是机台行程 ⇒ 与 `detect_over_stroke_limits` **同源**。

**L3 已有骨架**（已核实，非推测）：

| 已有机制 | 位置 | 对本场景的意义 |
|---|---|---|
| `MEL` 是**派生量**（`MEL = ML_N + DDAM`）；算法说「调 MEL」时先落成计量位置（决策量），MEL 再由它算出 | `anchors.py` L153-162（`apply_mel_targets`） | 「MEL 不能独立调」L3 已经知道 |
| `vps_pos` = 回抽链起点下界（`G2_VPS_FIELD`） | `anchors.py` L44-45 | vps_pos 与行程的关系 L3 已有 |
| 注射行程 = `ML_N − VPTL` | `integrate_params.py` L112 | 行程是**派生量** |
| 目标反推：目标行程 = 当前行程 × (目标重量/实测重量)；`ML_N` 目标 = `VPTL` + 目标行程 | `anchors.py` L236-242（`FillTarget`） | 「按目标反推落点」的机制已有 |
| G2 回抽链硬约束（严格递增 + 首段 > `vps_pos`） | `anchors.py` L238-252 | 位置类参数之间既有约束的处理方式可参照 |

⇒ **缺的只有一件事**：「设备行程上限 / 位置类物理下限」**没有作为约束接进求解**。

**已拍板**：位置类**物理下限 = 常量 10**（`vps_pos` / VPTL 等位置类整段参数）；最终需按产品维度调整，当前先取常量。

**目标形态**（✔ = 2026-11-23 已实施；▸ = 待办）：

```
预处理层（入参校验）
  ├─ 设定值类越限（设备红线）⇒ 400        ✔ 已在位
  └─ 位置类超行程（基线）⇒ **不设**（基线位置超行程是常态 ⇒ 误拒）

L3 整合（求解时避开设备能力约束）           ▸ 待办
  ├─ 输入新增：位置类上限字典 + 位置类物理下限（常量 10）
  ├─ 求解时：若落点会超出设备能力 ⇒ 尝试用既有联动机制化解
  │    （例：MEL 会超行程 ⇒ 调小 vps_pos 把 ML_N 目标拉回来，MEL 随之落在能力内）
  ├─ 化解成功 ⇒ 产出落在设备能力内，继续往下
  └─ 化解不了 ⇒ 在 IntegratedParams 留结论，交出口呈现

L4 校验（**所有参数的合法性都归这里**）
  ├─ 锚点自检 ✔ 已跑
  ├─ 位置类超行程（单参数）                ✔ 已实施（2026-11-23）
  ├─ 差值越限（接 limits 后启用）           ✔ 已实施（2026-11-23，阶段 3a）
  └─ 工艺窗口（inj_t / hold_t_1..5 —— 仍缺参照系，阶段 3b）

出口（**读 L4 结论 + 决定拒不拒**）
  └─ 位置类超行程 ⇒ 拒绝本轮优化（严格度策略，Q10）  ✔ 已实施
```

**改动清单**：

**✅ 已实施（2026-11-23）**

| 文件 | 改动 |
|---|---|
| `backend/process/algorithms/check_params.py` | 新增 `detect_position_violations`（复用 `detect_over_stroke_limits`，**只识别不处理**）；`validate` 增 `position_limits` 参照系；`ParamCheckReport` 增 `position_violations`（计入 `ok` / `messages` / `summary`）；`RANGE_CHECKS` 移除与之重复的 `meter_end_position` |
| `backend/process/services/over_limit_guard.py` | 抽出 `format_position_over_stroke_message`（**文案单一源**，守卫与 L4 共用）—— **第四批已合并进 `services/shared/over_limit.py`** |
| `backend/process/services/parameter_optimize.py` | ① 删掉编排层的 `guard_position_over_stroke` 调用；② L4 `validate` 传入 `resolve_position_limits(machine_info)`；③ 出口读 `validation.position_violations` ⇒ 拒绝（文案与守卫逐字一致） |
| `backend/tests/test_check_params_position_violations.py` | 新增护栏：命中 / 缺参照系不判 / 缺行程不判 / 边界不超 / 业务命名翻译 / 文案单一源 |

**▸ 待办**

| 文件 | 改动 |
|---|---|
| `backend/process/algorithms/fuzzy/specs.py` | 新增位置类**物理下限**常量表（**常量 10**，已拍板）；与 `POSITION_DOMAIN_FIELDS`（上限来源）同层，但**语义分开**（档位下界 ≠ 物理下限） |
| `backend/process/algorithms/integrate_params.py` | `apply_plan` 新增可选入参 `position_limits` / `position_floors`；求解时做设备能力约束与化解；化解不了 ⇒ 在 `IntegratedParams` 留结论（沿用阶段 0 的「留痕不抛异常」风格） |

**⚠️ 编排层那道守卫怎么处理 —— 全部归 L4（2026-11-23 已实施）**：

按用户口径（「超限由 L4 判」）⇒ 编排层那道**删除**，判定整体移到 L4：

| | 之前 | 现在 |
|---|---|---|
| **判据在哪** | 编排层 `guard_position_over_stroke` | **L4** `check_params.detect_position_violations` |
| **判什么** | `integrated.values`（**未量化**） | **最终产出** `new_parameter_dict`（量化后 = 落库/响应的同一份） |
| **拒不拒** | 守卫直接抛 | **出口读 L4 结论**再抛（严格度策略，Q10） |
| **文案** | 守卫内组装 | `format_position_over_stroke_message`（**单一文案源**，与初始化链路逐字一致） |

⇒ 「一道覆盖两种、无法区分是哪种」的病根**不是拆分，而是判定位置** —— 移到 L4 后，判据集就是「最终产出那一份值」，两种情形都体现在其中。
⇒ **行为变化**：① 判据从「未量化」改成「量化后」⇒ 边界值（200.004）不再误拒（**假阳性消除**）；② 判定顺序从「零落地守卫之前」变成「之后」（分层顺序 L3 自检 → L4 校验）。

**实施注意事项**（实现细节，不影响上面的审阅主线）：

- **等价判定排查（已落地）**：接超限判定时「MEL vs 行程」这**一个**判据在代码里有**两处实现** —— `check_params.RANGE_CHECKS` 的 `meter_end_position` 与 `over_limit.detect_over_stroke_limits`（`field_names.py` L94 确认 `met_end_pos` → `MEL`）⇒ L4 只能接一个。**已接 `detect_over_stroke_limits`**（与原守卫同源），**`meter_end_position` 已移除**。差值口径的 `injection_stroke` 与单参数口径不重叠，保留。
- **迁移而非新增**：位置类超行程判定复用 `detect_over_stroke_limits`（原由编排层那道守卫调用）⇒ L4 接它是**搬家**，不是写新逻辑。
- **命名空间**：`check_params` 收**业务字段名**（与其余三类检查一致），识别函数要**算法字段名** ⇒ `detect_position_violations` 内部转一次（`field_names.to_algo_params`）。

**机制路径推导**（代码可查，2026-11-23 补）：

| 环节 | 依据 |
|---|---|
| 注射行程 = `ML_N − VPTL` | `integrate_params.py` L112 |
| 目标反推：`ML_N` 目标 = `VPTL` + 目标行程 | `anchors.py` L240 |
| ⇒ **`VPTL`（`vps_pos`）变小 ⇒ `ML_N` 目标变小 ⇒ `MEL = ML_N + DDAM` 变小 ⇒ 不再超行程** | 三式串起来 |
| `vps_pos` 还有 G2 约束（`met_pos_1 > vps_pos`）⇒ 调**小**它只会让该约束**更容易**满足（不冲突） | `anchors.py` L248-249 |

⇒ **「调 `vps_pos` 化解 MEL 超限」的机制路径已经存在**（`FillTarget` 反推时把 `VPTL` 算进去了）⇒
阶段 1b 要做的**不是新建机制**，而是**把「行程上限」接进这个已有的求解**，让求解器在反推时避开超限。

⇒ 「固定 MEL」的含义也由此确定：**MEL 不独立可调**（它是 `ML_N + DDAM` 的派生量，`apply_mel_targets` 会先把 MEL 目标落成计量位置）⇒「固定 MEL」= **不让 `ML_N` 超出行程**。

**⚠️ 仍需你确认的一处取舍**：

`vps_pos = 15` 在**物理上**允许（≥ 已拍板的下限 10），但低于 `specs.py` L854 记的经验**档位**下界 30 ⇒ **判级论域**上会让 VPTL 相关规则失活（真实值低于档位下界时判不出档）。
⇒ 代价要不要接受？（若不接受，下限就不能是 10，而要 ≥ 30；这是「物理下限」与「档位下界」两种语义的取舍）

**行为变化**：**有**（2026-11-23 已发生的部分）—— ① 位置类超行程的**判定位置**从编排层挪到 L4（**错误码、用户文案、拒绝行为不变**）；② 判据从「未量化落地值」改成「量化后最终产出」⇒ 边界值（200.004）不再误拒（**假阳性消除**）；③ 判定顺序：零落地守卫 → L4 校验（分层顺序 L3 自检 → L4 校验）。
⇒ **尚未发生**：L3 求解时避开设备能力约束（待办）⇒ 化解能力上线后，被拒场景可能出方案。

**验收**（2026-11-23 已跑）：
- `pytest backend/tests` ⇒ **113 passed**（原 105 + 新增 8）
- 新旧路径等价性实测：9 个用例中 **8 个逐字一致**（错误码 + 文案）；唯一差异 = 量化边界（200.004 ⇒ 由拒改为不拒）
- 新增护栏 `test_check_params_position_violations.py`：命中 / 缺参照系不判 / 缺行程不判 / 边界不超 / 业务命名翻译 / 文案单一源

**风险**：**中**（判定位置变了但行为基本等价；L3 求解约束仍是新逻辑，待办）。

---

### 阶段 2：去噪下沉到算法引擎（落实用户第 4 点的判断）

**目标**：把「算法知识」还给算法，把「面向用户的表达」留在 service 层。

**现状**：`_normalize_recommendations`（`parameter_optimize.py` L894-927）干了两类事：

| 做什么 | 依据 | 目标归属 |
|---|---|---|
| 丢弃**零变化项**（推荐值 == 当前值） | 「来自激活度 ~0 的规则，是数值噪声」⇒ **算法知识** | **下沉到引擎** |
| `param` 译回业务字段名 | 命名契约（`field_names`） | 留在 service 层 |
| `reason` 重写为中文文案（"降低一段注射压力：70 → 60"） | 面向用户的表达 | 留在 service 层 |

**改动清单**（形态待定，见 §七 Q3）：

| 文件 | 改动 |
|---|---|
| `backend/process/algorithms/fuzzy/engine.py` | 引擎侧过滤零变化项（激活度 ~0 的规则本就不该产出建议） |
| `backend/process/services/parameter_optimize.py` | `_normalize_recommendations` 去掉去噪职责，只留翻译 + 文案；函数名可能需要改 |

**行为变化**：**有**（引擎输出变少）。需重点验证。

**验收**：

- `pytest backend/tests/test_fuzzy_recommendations.py backend/tests/test_optimize_smoke.py`
- 案例回归：按记忆口径用**单变量对照归因法**（FAIL 可能是数据陈旧而非代码退化，先确认是否本来就有零变化项被过滤）

**风险**：**中高**。涉及引擎输出 ⇒ 需跑一轮完整回归。

**⚠️ 前置**：需确认引擎侧过滤点选在哪一层（引擎内 vs 规则加载后），以及 `empirical` / `llm` 引擎是否也要同口径处理（它们不给数值，本就不产生零变化项）。

---

### 阶段 3：L4 接上参照系（`limits` / `windows`）

**目标**：让第 4 层真正名副其实 —— 三类检查（差值越限 / 工艺窗口 / 锚点自检）都跑起来。

**现状（2026-11-23 更新）**：L4 已接上**两类**参照系 —— **位置类超行程**（阶段 1b）与 **差值越限**（阶段 3a）；**工艺窗口（`windows`）仍缺参照系**（阶段 3b）。

**参照系数据源：两类不同，差别很大**（2026-11-23 修正）

| 需要 | 数据源 | 能不能接 |
|---|---|---|
| `limits`（行程类差值口径：`injection_stroke`） | **机台实测注射行程** ⇒ `specs.resolve_stroke_limit(machine_info)`；`RANGE_CHECKS` 已把检查项与成员写好，`limit_source='stroke'` 就是行程 | ✔ **能接** —— **接线活** —— ✅ **2026-11-23 已接** |
| `windows`（经验区间：`inj_t` / `hold_t_1..5`） | 注释明说「窗口上下限**不在本模块内置** —— 那是材料 × 壁厚维度的经验值，由调用方从工艺设定集 / 配置读出」⇒ **没有任何现成来源**；测试里用的是手写字典 | ✘ **不能接** —— 要先决定经验区间从哪来（新建数据表？硬编码？走配置？），属业务口径问题 |

⇒ **阶段 3 应拆成两半**：
- **3a**：接 `limits` ⇒ 差值越限**立即生效**（检查项已存在，只是没喂参照系）；单参数位置类超限已于 2026-11-23 经阶段 1b 生效 —— ✅ **已实施（2026-11-23）**
- **3b（暂不做）**：接 `windows` ⇒ 工艺窗口检查 —— 需先定经验区间的数据来源

#### 阶段 3a 实施记录（2026-11-23）

**查证到的关键事实（决定形态）**：

| 事实 | 影响 |
|---|---|
| `validate(limits=...)` 要的是 **`range_id` → 限值**（如 `{'injection_stroke': 200.0}`） | **不能**把 `resolve_position_limits` 的产物直接喂进去 —— 它是**位置类参数名/族 → 上限**（`{'IL': 200.0}`）⇒ **两者形状不同** |
| `POSITION_DOMAIN_FIELDS` 的四个 key（IL / ML / MEL / VPTL）**全指向同一个设备字段** `max_injection_stroke` | ⇒ 行程上限**就一个数** ⇒ 差值口径与单参数口径**同源**，不会各说各话 |
| `RANGE_CHECKS` 现有**只剩一条** `injection_stroke`（差值口径：`met_pos_{last} − vps_pos`）；`meter_end_position` 已在阶段 1b 移除（与单参数判定重复） | ⇒ 差值口径与单参数口径**不重叠**，两个都保留 |

**改动清单**：

| 文件 | 改动 |
|---|---|
| `backend/process/algorithms/fuzzy/specs.py` | 抽出 `STROKE_FIELD` 常量 + `_read_positive_float` helper；新增 `resolve_stroke_limit`（机台实测行程，缺权威源 ⇒ `None`）；`resolve_position_limits` 改为复用同一 helper |
| `backend/process/algorithms/check_params.py` | 新增 `resolve_range_limits`（**按 `RANGE_CHECKS` 遍历** ⇒ 限值表与检查项**天然一一对应**，将来加检查项不必改接线） |
| `backend/process/services/parameter_optimize.py` | L4 `validate` 传入 `limits=resolve_range_limits(machine_info)` |
| `backend/tests/test_check_params_range_limits.py` | 新增 12 条护栏（一一对应 / 缺参照系不判 / 命中 / 边界 / 成员缺失 / 末段跟随 / 差值与单参数口径互不顶替） |

**行为变化**：**用户可见行为无变化** —— 差值越限**只进日志**（`validation.ok` 为假 ⇒ 多一行 `_logger.info`），**不触发拒绝**（出口只读 `validation.position_violations`）⇒ 与阶段 1b 的「拒不拒」策略各自独立。

**⚠️ 已知差异（唯一一处，NaN 病态输入）**：`max_injection_stroke = NaN` 时，

- 旧实现（`value <= 0` 放行）⇒ NaN 成了上限 ⇒ 下游 `current <= limit` 恒 False ⇒ **位置类全部被判超行程** ⇒ 出口**误拒整轮优化**（错误文案「这个产品在这台机上做不出来」）；
- 新实现（`value > 0`）⇒ NaN **不产出** ⇒ 缺参照系 ⇒ 不判 ⇒ 放行。

⇒ 方向 = **消除假阳性误拒**，与「缺权威源不报错不阻塞」的既定口径一致；已在 `specs._read_positive_float` 的 docstring 写明。

**验收（2026-11-23）**：

- ✅ `pytest backend` ⇒ **180 passed**（168 + 新增 12，零回归）
- ✅ smoke `verify_provided_smoke.py` ⇒ **6/6 PASSED**，exit 0
- ✅ 等价性实测（`_dev_refs/_verify_range_limits.py`）⇒ `resolve_position_limits` 重构差异 **0**、位置类判定差异 **0**、限值表与检查项一一对应 **True**（exit 0）

**⚠️ 遗留待拍板**：差值越限**拒不拒**（属 §七 **Q10** 严格度策略）—— 本轮只铺判定，不改策略。

**附：按 §二 的「呈现在出口」，L4 还有一个独立缺口**

L4 **已经判了**（`validate` 返回 `ParamCheckReport`，含差值越限 / 工艺窗口 / 锚点自检），但结论**只进了日志**：

```python
validation = validate(new_parameter_dict)                              # L1548  L4 判了
if not validation.ok:
    _logger.info('infer validation: %s', validation.summary())        # L1553  只进日志
suggestion_payload = _build_suggestion_payload(                       # L1569  无 validation 参数
    algorithm_recommendations=..., algorithm_sources=...,
    baseline=..., applied_values=...)
return new_parameter_dict, suggestion_payload, algorithm_recommendations  # L1575  也未返回 validation
```

⇒ **判完了，算完就丢** —— 既不进响应体，也不在返回值里，上层拿不到。
⇒ 按「判定在本层、呈现在出口」，这属于**出口缺了一段**，不是 L4 的问题。
⇒ 与阶段 3 **互不依赖**：阶段 3 是让 L4 **多跑两类检查**（判定），这条是让 L4 **已有的结论能被看到**（呈现）。
⇒ 附带印证阶段 1：L1540-1548 的区块注释本身就把「第4层校验」和「出口量化」混着写 ⇒ 拆分第 9 段时这里正好一起理清（阶段 1 已收口）。

**验收（若将来做）**：`pytest backend/tests/test_check_params_layer.py` + 参照系缺失时仍不阻断。

**风险**：高（业务口径未定）。

---

### 阶段 4：L1/L2 解耦 —— **本轮明确不做**

**现状**：`_apply_decision_status`（L1500）**就地修改** L1 产出的 dict（写回 `decision_status` / `decision_reason`），违反「不回头改上游的东西」。

**为什么不列入本轮**：这是**用户之前已拍板的设计** —— 裁决结果回写到建议载荷并随建议落库，保证「当轮响应 / 落库 / 历史轮次回显」三处同源。改成「L2 另产出状态、下游合并」会牵动 `_build_suggestion_payload` 与 `_record_tuning_round` 的数据流，**收益（纯粹度）远小于风险（三处不一致）**。

⇒ 若将来要解耦，需先给出替代数据流方案再动。

---

## 六、明确不做的清单

| 不做 | 理由 |
|---|---|
| 改 L1→L2 的就地回填 | 已拍板的设计（展示与落库同源），收益小于风险 |
| 接上 `windows`（工艺窗口经验区间） | 参照系数据源不存在（阶段 3b）—— 但 `limits`（行程类）**有源可接**，见阶段 3a |
| 统一两处 `to_algo_params` 转换位置 | 属于「接口一致性」而非「分层」；可另开，但需确认两个守卫的入参约定哪个更合适 |
| ~~把 `guard_position_over_stroke` 下沉到 L3~~ | **已撤回**（2026-11-23，两轮）—— ① 原结论「留在编排层」的前提「超限是静态事实核对」不成立；② 用户口径「超限由 L4 校验」⇒ 最终不是「下沉到 L3」，而是**超限判定归 L4 + L3 求解时避开 + 编排层这道删除** ⇒ 见**阶段 1b** |
| 动 `feedback` 里的 `defect_selection` 留痕 key 是否进算法上下文 | 契约外 key 无害（引擎忽略）；属契约整洁性，与分层无直接关系 |
| 统一 `applied_value` 精度口径（未量化 vs 落库值已量化） | 属「出口精度」问题，不是分层问题；前端已有 `toFixed(2)` 兜底 |
| 改 `guard_setting_limit` 的调用顺序或位置 | 分层图里它就是「推理前的守卫」，位置正确 |

---

## 七、待你拍板的问题

| # | 问题 | 我的倾向 |
|---|---|---|
| **Q1** | 阶段 0 下沉后的**落地形态**（背景见 §二「谁的问题谁判」+ §五 阶段 0 的「新查到的事实」）：算法层 `integrate_params.py` 与 `decide_direction.py` 目前**均 0 个 raise** ⇒ 既有风格是「纯计算 + 留痕，不抛异常」。四个选项：① **L3 置自检结论字段（`IntegratedParams.landing_blocked`），service 层读字段转 `BizException`**（与 `OptimizeDataValidator` → ValueError → BizException 同构）；② L3 抛算法层自定义异常，service 层 catch 后转译；③ L3 直接抛 `BizException`（破例）；④ 只做位置归并（挪进 L3 段），判定仍留在 service 层 | **选 ①** —— ① 是唯一同时满足四条约束的（判定 100% 在 L3 + 算法层不抛异常 + service 只做呈现 + 与算法层既有「留痕不抛异常」风格同构）；④ 违背「谁的问题谁判」；② 与既有风格不一致；③ 破例 |
| **Q2** | 阶段 1 的出口段：**抽成独立私有函数**还是**只加区块注释**把三件事分开？ | 抽成独立函数（`_build_response_payload` 之类）—— 但这会动函数结构，需要你确认是否接受 |
| **Q3** | 阶段 2 的过滤点选在哪：引擎内产出时就不给零变化项，还是引擎产出后统一过滤？ | 引擎内过滤（更符合「算法自己知道激活度」），但需确认 `empirical` / `llm` 是否同口径 |
| **Q4** | 阶段顺序：现为 **0 → 1 → 1b → 2 → 3**。其中 **1b / 2 都有行为变化**（风险高），阶段 0 / 1 零行为变化。是否**先只做 0 + 1**（零行为变化），把 1b 与 2 各自单独走一轮？ | 先只做 0 + 1 |
| **Q5** | 阶段 0 是否需要**保留 service 层的一份兜底**（双保险）？还是完全下沉、service 层不再判？ | 完全下沉，避免两处判据漂移 |
| **Q6** | L4 的校验结论目前**只进日志、不进响应也不进返回值**（§五 阶段 3 附）⇒ 按「呈现在出口」，出口缺了一段。是否补一个阶段，把 `ParamCheckReport` 带进响应体？ | **建议补，且优先级升高** —— 超限判定归 L4 后（口径 #2），用户看到的「超没超」**只能从 L4 的结论来** ⇒ 若结论出不去，校验就等于白做（**位置类超行程会直接抛错、用户看得到；差值越限只进日志、用户看不到** —— 阶段 3a 后这个缺口多了一类）（但**响应体加字段属接口契约变更**，需确认前端是否愿意接、以及是放在顶层还是挂在 `suggestion` 下） |
| **Q7** | 「L2 一条候选都没保留」⇒ 现状是**静默建出与父轮相同的轮次**（不报错）。按「谁的问题谁判」，这是 L2 的结论，但 `StrategyDecision` 只有 `kept`/`kept_reasons`/`yielded`/`deferred`/`order`/`scenario_code` ⇒ **没有「什么都没保留」的显式留痕**。是否一并显式化？ | **本轮先不动**（与阶段 0 解耦）；但阶段 0 必须保证**编排层不再读 `plan`** ⇒ 这个判断交给 L3 自检一起判 |
| **Q8** | 编排层那道「检出即拒绝」的超行程守卫：按用户口径 ⇒ **删除**并**拆成两半**（基线超 ⇒ 预处理层 400；产出超 ⇒ L4）。确认？ | **删 + 拆** —— 编排层不该判超限；拆开后三处职责不重叠：预处理层拦**入参**、L3 **求解时避开**、L4 **事后判定** |
| **Q9** | 阶段 1b 的物理机制已从代码推出（`ML_N` 目标 = `VPTL` + 目标行程 ⇒ 调小 `vps_pos` ⇒ `MEL` 变小 ⇒ 不超行程）⇒ **只剩一处取舍**：位置类**物理下限 10** 低于经验**档位**下界 30 ⇒ 调小后会影响 VPTL 规则判级。接受这个代价吗？ | 需你确认 —— 接受则下限 10 生效；不接受则下限提高到 30（此时两个下限合为一个） |
| **Q10** | L4 判定完成后，**「直接拒绝」还是「返回给前端」**怎么表达？架构已定（判定唯一在 L4），剩下的是**严格度策略**放哪：① L4 报告项带严重级（block/warn），出口按级处置 ② 出口层按参数类别自己映射 ③ 调用方传严格度标志 | 需你拍 —— 但**架构无争议**：判定唯一在 L4，策略可配。倾向 ①：严重级随判定一起产出（出口只翻译，不重新判断） |

---

## 八、下一轮接续点

### 工作方式（用户 2026-11-23 明确）

> 「我们后续的工作都是先完善这个文档，然后再看代码怎么调整」

⇒ **本文档是唯一工作面**：每轮先把口径写进本文（用户审）⇒ 审过后才动代码。
⇒ 代码改动只是本文「已拍板章节」的执行结果，**不是独立产出**。

**先读什么**：

1. 本文的 §七（待拍板问题）—— **需要你逐条回复**
2. `backend/process/services/parameter_optimize.py` L1401-1559（`_infer_kernel` 全文）
3. `backend/process/algorithms/integrate_params.py` L337-368（`IntegratedParams`）与 L505-578（`apply_plan`）

**等用户拍哪几条**：**Q10**（严格度策略 —— 差值越限拒不拒、位置类超行程拒不拒）与 **Q6**（L4 结论要不要进响应体）⇒ 两者都卡在「出口怎么处置 L4 的结论」；其次 **Q2**（出口段要不要抽独立函数）、**Q3**（阶段 2 的过滤点）、**Q9**（位置类物理下限 10 vs 档位下界 30）。

**不要重做的**：

- ❌ 不要重做本轮的完整性检查结论（§三 / §四 已成文）
- ❌ 不要重做 2026-11-23 那轮的**文档清理**（`_dev_refs/` 已删、`docs/` 已收敛到 8 份 + 本文 ⇒ 清理后为 9 份；备份在 `f:\items\moldingx\_deleted-dev-refs-20261123.zip`）
- ❌ 不要重做 2026-11-23 那轮的**注释精简**（`parameter_optimize.py` 已完成，`+43/−60`，AST 比对 IDENTICAL）

**已知的、本计划之外但同区域的问题**（供参考，不在本计划范围）：

- `optimize_from_condition` 的 Step 2（推理）在 Step 3（事务落库）**之前** ⇒ 推理期任何异常都会让本轮评价、手改参数、采纳结算**全部不落库**
- 第 4 层的校验结果只进 `_logger.info`，**不进响应** ⇒ 用户看不到「参数不合理」（**位置类超行程会抛错、看得见；差值越限只看得到日志**）

---

## 附：术语纠正记录

| 用户的说法 | 实际口径 |
|---|---|
| 「第 8 点应该放在第 4 层（参数校验）」 | 不是参数校验 —— 参照系是「L2 说要调 vs L3 实际调成」；第 4 层的参照系是参数自身的物理/工艺约束。两者不可合并 |
| 「参数去噪应该属于算法部分」 | 对了一半 —— 去噪的**依据**是算法知识（该下沉），但**表达**（业务名 + 中文文案）留在 service 层 |
