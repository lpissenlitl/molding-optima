# 参数限值域统一 —— 实施文档（批次 B）

> **状态：已实施完成（2026-11-24）。**
> 验收：`pytest tests` **226 passed**；`_verify_zero_dep.py` / `_verify_e2_offline.py` / `_verify_expert_smoke.py` 全 exit=0；
> `run_demo.py` exit=0（案例与历史基线逐位一致）；`export_case.py` import OK；
> **数值回归**：推荐值 **0 变动**、第4层新增判出 **0 条**（详见 §9.3 实测结果）。
>
> **【路径现状】**（2026-11-24 模块分割收口后）：**§2 记录的是「改前」事实，保留原样便于对照**；
> **当前限值域模块** = `backend/process/services/shared/param_limits.py`
> （§2 里的 `setting_limits.py` / `over_limit.py` **已并入本文件**；
> `STROKE_FIELD` / `_POSITION_KEYS` / `_SETTING_KEYS` / `build_setting_limits` /
> `build_position_limits` / `resolve_stroke_limit` **已退役**）
> ⇒ **当前导出**：`Limit` / `LimitSpec` / `LIMIT_SOURCES` / `build_limits` /
> `read_positive_float` / `OverLimit` / `find_over_limits` / `guard_parameter_limits` /
> `format_over_limit_message` / `format_limit_number` / `OverLimitItem` /
> `detect_over_limits` / `format_unfit_param_message` / `to_upper_limits`。
> 算法侧的查表件在 `backend/process/algorithms/fuzzy/device_limits.py`
> （`param_family` / `lookup_limit` / `to_family_limits`）。

---

## 1. 已拍板的口径（用户原话）

| # | 原话 | 含义 |
|---|---|---|
| 1 | 「param_limits.py 1-630 回到这个文件，优化一下写法，当前函数太多层了，我不认为需要区分setting和position」 | service 层不按 setting / position 二分；写法要收层 |
| 2 | 「inj_pos / met_end_pos / vps_pos 就是设定工艺参数，和 inj_pres 完全同类；唯一差别只是上限取自哪个设备字段（实测行程 vs 可设定最大值）。所以二分是伪分类。」 | **参数维度**的二分是伪分类 |
| 3 | 「修正一个描述，这里的 max_injection_stroke，其实也是可设定最大值，只是模式和 max_set 不一样罢了，概念是一样的」 | **上限来源维度**的二分也是伪的 |
| 4 | 「他们都是机器的可设定值，只是说数据类型不一样罢了，顶多行程的属于行程参数，压力、速度等等，数据类型不同，但是都是机器的设定参数。」 | 全部一视同仁；差别只是「参数所属的数据域」 |
| 5 | 「其实spec中有对字段的描述，我觉得给用户看的文案完全可以展示这是什么设定工艺，不管是注射压力还是注射行程，完全可以提示给用户」 | **对外文案**要展示具体设定工艺项（用字段描述 / 中文标签） |
| 6 | 「有些参数我们可能并没有指定限定来源，但是逻辑是一样的，配置了上下限的参数就校验，没有配置的就不校验」 | **校验范围由配置决定**；「上限来源」是**可缺省**的可选项，缺省即不校验 |
| 7 | 「直接用 LimitSpec.high（设备字段名）溯源即可，后者信息量更大（看得出是「注射行程」还是「注射压力」），我们本身就应该通过配置，决定哪些参数用来校验」 | **不加 `source` 标记**；溯源直接用设备字段名 |
| 8 | 「统一成「请更换能力更强的设备」可否？请检查参数设置或更换设备。因为也有可能是用户误输入」 | 出路 = **检查参数设置 或 更换设备**（不再只给「换机」） |
| 9 | 「顺手删掉即可，按照 YANGI 原则，需要的时候再加上」 | 删掉零引用的 `ERROR_PROCESS_PARAMETER_INVALID`（code 33）；code 33 留空不复用 |

### 1.1 由口径推出的硬约束

1. **不存在「两类参数」**：每个设定工艺参数各配**一个**该设备的可设定上限；判定路径只有一条。
2. **不存在「两类上限来源」**：`max_set_injection_pressure` 与 `max_injection_stroke` 都是「这台机器这个能力项最多能设到多少」，差别只是能力项不同 ⇒ service 层**不需要任何分类标记**。
3. **不存在「两套留痕」**：`device`/`stroke`、`H1`/`G6` 是同一件事（当前值 > 该参数自己的上限）的两三张皮 ⇒ 归一。
4. **上限来源可缺省**：`LimitSpec.high` 允许为 `None` ⇒ 该参数**不产出允许区间** ⇒ **不参与校验**（「有配置则校验，没有配置则不校验」）。**校验范围完全由 `LIMIT_SOURCES` 这份配置决定**，不靠代码里的分类逻辑。
   - 结构上已支持：`LimitSpec.high: Optional[str] = None`；`build_limits` 遇 `high` 为空即跳过。
   - ⇒ **不需要**为「未指定来源」新增任何分支、标记或第三种来源类型。
5. **YAGNI**：已定义但零引用的错误码直接删（code 33 `ERROR_PROCESS_PARAMETER_INVALID`）⇒ 需要时再加，code 33 留空不复用。

---

## 2. 改前现状事实（可核对）

### 2.1 service 层 `backend/process/services/shared/param_limits.py`（622 行）

| 符号 | 作用 |
|---|---|
| `LIMIT_SOURCES: Dict[str, LimitSpec]` | **唯一真相源**：11 个业务键 → 上限来源字段（7 个 `max_set_*` + 4 个 `max_injection_stroke`）；每项 `high` 均可为 `None`（不指定来源 ⇒ 不校验） |
| `STROKE_FIELD` | `'max_injection_stroke'`（设备维度字段名） |
| `_POSITION_KEYS` / `_SETTING_KEYS` | **批次 A 引入的派生键集合**（分类信息派生自 `LIMIT_SOURCES`） |
| `build_limits(machine_info)` | 全量业务键区间表 `{参数名: (下限, 上限)}`；缺来源/缺值 ⇒ 该参数不产出 |
| `build_setting_limits` / `build_position_limits` | 两个**分类**取表函数（批次 A 后为一层薄封装） |
| `resolve_stroke_limit(machine_info)` | 行程标量（`check_params.resolve_range_limits` 依赖它） |
| `OverLimit` + `find_over_limits` + `guard_parameter_limits` + `format_over_limit_message` | **入参校验**（业务键命名空间） |
| `OverLimitItem` + `detect_over_limits` + `format_position_over_stroke_message` | **第4层产出侧**（算法族键命名空间） |
| `LIMIT_SOURCE_DEVICE` / `LIMIT_SOURCE_STROKE` | 上限来源标记（第4层留痕用）—— **待退役**（口径 7） |

### 2.2 算法层

| 位置 | 事实 |
|---|---|
| `algorithms/common/limit_mapping.py::to_family_limits` | 业务键区间表 → 算法族上界表（**取上界**）；映射不到族的键跳过 |
| `algorithms/common/device_limits.py::lookup_limit` | 两级匹配：整段参数名精确命中 → 族前缀命中 |
| `algorithms/fuzzy/engine.py` L89-90 | `DOMAIN_SOURCE_DEVICE='device'` / `DOMAIN_SOURCE_STROKE='stroke'` |
| `algorithms/fuzzy/engine.py` L94-99 | `kept_experience_domain` 的触发条件注释里写着 **H1 / G6 / G7 三个守卫** |
| `engine.py::_apply_device_bound` | 只换**上界**，下界留经验域下界；**就地改**档案 |
| `engine.py::_apply_position_bound` | 整段换 **[0, 行程]**；**返回新档案**；当前值 > 行程 ⇒ 回落经验论域（G6） |
| `engine.py::_device_limit_below_current` | H1 守卫：当前值 > 设备上限 ⇒ 不替换上界 + 留痕 |
| `services/parameter_optimize.py::AlgorithmContext` | **两个槽位**：`param_limits`（设定值族）+ `position_limits`（位置族） |

### 2.3 批次 A（已完成、已验收、行为零变化）

用户明确选项「只砍冗余层，API 不变」授权范围内完成：

- **删除 5 个符号**：`_split_sources()` / `_SETTING_SOURCES` / `_POSITION_SOURCES` / `_build_limits()` / `_format_bound()`
- 取表层数 **4 → 2**；文案层数 **3 → 2**
- 对外 API 签名与产出**逐项等价**：`build_limits` ≡ 旧「设定值表 + 位置表」合并（键不重叠）；两个薄封装按派生键集合筛
- 分类信息从「两张表 + 拆分函数」变为**派生键集合** ⇒ 分类是派生信息，不是第二份声明
- 验收：`pytest tests` **224 passed**；`_verify_zero_dep.py` / `_verify_e2_offline.py` / `_verify_expert_smoke.py` 全 exit=0；`run_demo.py` exit=0；`export_case.py` import OK

### 2.4 第4层与对外文案现状

| 位置 | 事实 |
|---|---|
| `services/optimize_chain/check_params.py::ParamCheckReport` | 四类越界：`range_violations` / `window_violations` / `anchor_violations` / `position_violations` |
| `check_params.py::detect_position_violations` | 「单参数 vs 行程」，收**算法族表**（`position_limits`） |
| `param_limits.py::format_position_over_stroke_message` | 文案：`'{标签}需 {值}mm，超出本机注射行程 {上限}mm{另有N项}，请更换行程更大的设备'`；**`mm` 与「行程」是硬编码** |
| `param_limits.py::format_over_limit_message` | 入参校验文案：`'{参数名} 当前 {值} 超出允许区间 [{下}, {上}]'` —— **显示参数名**（如 `inj_pres_1`），不是中文标签 |
| `process/exceptions.py` L68 | `ERROR_PROCESS_OVER_STROKE = MOD_PROCESS, 38, "当前设备无法生产该制品"` |
| `services/shared/param_naming.py::param_label` | 业务字段名 → 中文标签，取 `ProcessParameter._meta.get_field(name).verbose_name`（`inj_pres_1` → 「一段注射压力」；`met_end_pos` → 「熔胶终止位置」；`vps_pos` → 「VP切换位置」） |

---

## 3. 要拆掉的三层伪分类

| # | 伪分类 | 表现 | 为什么是伪的 |
|---|---|---|---|
| 1 | **参数维度**：setting 类 vs position 类 | `build_setting_limits` / `build_position_limits`；`AlgorithmContext` 两个槽位；engine 两条论域分支 | 都是设定工艺参数（口径 2、4） |
| 2 | **上限来源维度**：`max_set_*` vs `max_injection_stroke` | `LIMIT_SOURCE_DEVICE` / `LIMIT_SOURCE_STROKE`；`DOMAIN_SOURCE_DEVICE` / `DOMAIN_SOURCE_STROKE` | 都是机器的可设定值，只是能力项不同（口径 3、4）；且**来源可缺省**（口径 6） |
| 3 | **守卫维度**：`H1` vs `G6` | 两个方法、两个标签 | 判据完全相同：**当前值 > 该参数自己的上限** ⇒ 同一个守卫 |

---

## 4. 目标形态

```
service 层（唯一真相源：LIMIT_SOURCES —— 「哪个参数、配了哪个能力项的上限」）
  build_limits(machine_info)  →  {业务键: (下限, 上界)}     ← 一张表，无分类；未配来源 ⇒ 不产出 ⇒ 不校验
  read_positive_float(info, field)  →  float | None         ← 通用取值：差值检查项按自己声明的字段名取上限
        │
        │ to_family_limits（算法层翻译，取上界）
        ▼
算法层  param_limits（单张全量族表）   ← position_limits 槽位退役
        │
        ▼
engine  一条「声明上界」路径：查该参数自己的上限 → 整段换 [0, 上界] → 守卫（当前值 > 上界 ⇒ 保留经验论域 + 留痕）
        │
        ▼
第4层   越限识别按「该参数自己的上限」；对外文案用字段描述（中文标签）说明是哪个设定工艺
```

### 4.1 溯源设计（口径 7）

- **不加 `source` 标记**：溯源直接用 `LimitSpec.high`（设备字段名），例如 `max_injection_stroke` / `max_set_injection_pressure` ⇒ 看得出是「注射行程」还是「注射压力」。
- **传递路径**：第4层在 **service 层**（`check_params.py` / `param_limits.py`）⇒ 可直接读 `LIMIT_SOURCES` ⇒ **不需要过 context、不需要新增槽位**。
- **落地形态**：`OverLimitItem` 增加一个字段 `limit_field: str`（= 该参数的上限来源设备字段名），由 `detect_over_limits` 依业务键回查 `LIMIT_SOURCES` 填入 ⇒ 文案与诊断留痕都可用。
  - 回查需「业务键 → 前缀」匹配（`inj_pres_1` → `inj_pres`）⇒ 复用现有的 `_match_limit` 同一套两级匹配思路。
- **「哪些参数参与校验」** = `LIMIT_SOURCES` 里配了来源的那些 ⇒ 配置决定，代码零分支。

### 4.2 不动的东西（边界）

- `LIMIT_SOURCES` 的**结构与判空口径**不变：上限缺失 ⇒ 该参数不产出 ⇒ 不判
- `to_family_limits` / `lookup_limit` 的翻译与匹配规则不变
- 温度类 / 产品类两条论域分支不变（它们是**权威源维度**的差别，不是参数类别的差别）
- 第4层「差值越限」（`RANGE_CHECKS`）的**判据不变** —— 它判的是**两个参数之间的差**，与单参数上限无关；变的只是它的**来源标记**（见批次 C，§13）
- 上限字段名由**检查项自己声明**（`limit_field`）⇒ 代码里不再有行程专属的取值入口

---

## 5. 改动清单（文件级）

> **状态：已全部实施完成（2026-11-24）** ⇒ 下表保留作为**变更记录**（动作均已落地）。

### 5.1 `backend/process/services/shared/param_limits.py`

| 动作 | 对象 | 说明 |
|---|---|---|
| 删 | `build_setting_limits` / `build_position_limits` | 分类取表函数退役 |
| 删 | `_POSITION_KEYS` / `_SETTING_KEYS` | 分类信息不再需要（批次 A 引入的中间产物） |
| 删 | `LIMIT_SOURCE_DEVICE` / `LIMIT_SOURCE_STROKE` | 溯源改用 `LimitSpec.high`（口径 7） |
| 改 | `__all__` | 同步删以上各项 |
| 留 | `LIMIT_SOURCES` / `build_limits` / `read_positive_float` | 唯一真相源与唯一取表函数（字段名常量 `STROKE_FIELD` 在批次 C 退役，见 §13） |
| 改 | `OverLimitItem` | 增字段 `limit_field`（设备字段名）⇒ 溯源用（§4.1） |
| 改 | `format_over_limit_message` | 参数名 → 中文标签（口径 5） |
| 改 | `format_position_over_stroke_message` | 去掉硬编码 `mm` 与「行程」措辞 ⇒ 通用「超本机可设定上限」文案；出路措辞按口径 8（§7） |

### 5.2 `backend/process/services/parameter_optimize.py`

| 动作 | 对象 |
|---|---|
| 改 | `AlgorithmContext`：删 `position_limits` 键 |
| 改 | `_compose_algorithm_context`：`'param_limits': to_family_limits(build_limits(machine_info))`；删 `'position_limits'` |
| 改 | 第4层调用：`validate(..., position_limits=...)` → 统一上限表 |
| 改 | 文案调用：`format_position_over_stroke_message(...)` → 新的通用文案函数 |

### 5.3 `backend/process/services/optimize_chain/check_params.py`

| 动作 | 对象 |
|---|---|
| 改 | `validate(...)`：删 `position_limits` 入参，改用统一上限表 |
| 改 | `detect_position_violations` → 并入通用 `detect_over_limits`（第4层统一识别） |
| 改 | `ParamCheckReport.position_violations` → `over_limit_violations` |
| 改 | `ParamCheckReport.messages()` / `summary()` 同步 |

### 5.4 `backend/process/algorithms/fuzzy/engine.py`

| 动作 | 对象 |
|---|---|
| 合并 | `_apply_device_bound` + `_apply_position_bound` → `_apply_declared_bound(profile, limits, current)`：查上限 → 整段换 `[0, 上界]` → 守卫 ⇒ 返回**新档案** |
| 合并 | `DOMAIN_SOURCE_DEVICE` / `DOMAIN_SOURCE_STROKE` → 一个（如 `'device'`） |
| 合并 | guard `H1` / `G6` → 一个（如 `'G_declared'`）；`kept_experience_domain` 的注释同步 |
| 改 | `_load_keyword_profiles` 的四类分支：设备类与位置类合为一条 |
| 改 | `_infer_numeric_layer` / `_infer_advisory_layer` 签名：删 `position_limits` |
| 改 | 推测论域分支（L766-789）：设备与位置两段合并 |

### 5.5 `backend/process/exceptions.py`

| 动作 | 对象 | 说明 |
|---|---|---|
| 删 | `ERROR_PROCESS_PARAMETER_INVALID`（code 33） | 全项目零引用 ⇒ 按 YAGNI 删掉；**code 33 留空不复用** |
| 改 | `ERROR_PROCESS_OVER_STROKE` → `ERROR_PROCESS_UNFIT_PARAM` | 名字去掉「行程」这个**能力项**残留（统一后判的是「任何配了上限的参数」）；**code `MOD_PROCESS, 38` 不动**（对外契约，前端按 code 分支不受影响） |
| 改 | message：「当前设备无法生产该制品」→「**参数不符合机台设定要求**」 | 原标题把**现象**写成了**结论**；新出路含「检查参数设置」（可能是误输入）⇒ 标题不预设原因 |
| 改 | L64-67 注释 | 「位置类参数超出机台最大注射行程 ⇒ …出路只有『换行程更大的机』」是旧口径的化石，整段改写 |

### 5.6 其余受影响文件

- `backend/process/algorithms/fuzzy/specs.py`：`resolve_domain_limits` 的口径注释
- `backend/process/algorithms/fuzzy/fuzzy_core/profiles.py`：`domain_source` 取值说明
- `backend/process/algorithms/fuzzy/examples/run_demo.py` / `export_case.py`：context 组装两行合一
- 测试：`tests/test_fuzzy_declared_domain.py`（原 `test_fuzzy_position_domain.py`）/ `tests/test_check_params_range_limits.py` / `tests/test_check_params_over_limit_violations.py`（原 `test_check_params_position_violations.py`）/ `tests/test_fuzzy_engine_limits.py` / `tests/test_spec_contract_alignment.py`（若受影响）

---

## 6. 行为变更（**数值会变**，不能当纯重构）

| # | 变更 | 影响 | 依据 |
|---|---|---|---|
| 1 | **设定值类论域下界：经验下界 → 0** | 隶属度计算变化 ⇒ 判档结果可能变化 ⇒ 推荐值可能变化 | 记忆 `37c7fa50` 早已拍板「整段换 `[声明下界, 声明上界]`、推广到全部族」，**至今未落地** |
| 2 | **位置类推荐值纳入机台上限裁剪** | 现在位置类不在 `param_limits` 里 ⇒ 位置类推荐值**不裁**；统一后按行程封顶 | 现状 `engine._apply_machine_limits(recommendations, param_limits)` |
| 3 | **设定值类档案改为返回新档案** | 顺带修掉设定值类的 H2 跨请求污染隐患（**改进**，非回归） | 现状 `_apply_device_bound` 就地改档案 |
| 4 | **留痕标签归一** | `device`/`stroke` 合并；`H1`/`G6` 合并 | 口径 1-4 |
| 5 | **对外文案变更** | 见 §7 | 口径 5、8 |
| 6 | **第4层开始判设定值类超限** | 第4层收全量族表 ⇒ 设定值 / 速度类参数**也会被判超限**（以前只判位置类）⇒ 优化链路会新拒绝「设定值超机台上限」的参数 | 统一口径的落点（口径 1-4） |

> **风险提示**：变更 1 与 2 直接影响**推荐值数值** ⇒ 必须做数值回归（§9.3），不能只看 pytest 绿不绿。

---

## 7. 对外文案方案（口径 5、8）

### 7.1 原则

- 用 **spec 里的字段描述**告诉用户「这是哪个设定工艺」⇒ 复用 `param_label()`（`ProcessParameter.verbose_name`）
- 不再按「位置类 / 设定值类」分两套文案
- 单位不硬编码（压力 MPa、位置 mm、转速 rpm 各不同）⇒ 由标签体现所属能力项
- **出路是两条**：**检查参数设置 或 更换设备**（口径 8）—— 因为超限也可能是**用户误输入**

### 7.2 改前 / 改后

| 场景 | 改前 | 改后 |
|---|---|---|
| 第4层超上限 | 「熔胶终止位置需 200mm，超出本机注射行程 180mm，请更换行程更大的设备」 | 「熔胶终止位置需 200，超出本机可设定上限 180，请检查参数设置或更换设备」 |
| 入参越限（`guard_parameter_limits`） | 「inj_pres_1 当前 200 超出允许区间 [0, 100]，请修正后再试」 | 「一段注射压力 当前 200 超出允许区间 [0, 100]，请修正后再试」 |
| 多项超限 | 「（另有 N 项超出行程）」 | 「（另有 N 项超出可设定上限）」 |

### 7.3 出路措辞与错误码（已拍板）

出路从「只给换机」改为「**检查参数设置 或 更换设备**」（口径 8）⇒ 结论「这个产品在本机做不出来」**不再总是成立**（可能是误输入）⇒

- **错误码改名**：`ERROR_PROCESS_OVER_STROKE` → **`ERROR_PROCESS_UNFIT_PARAM`**
  - 理由一：`STROKE` 是**某一个能力项**（行程）⇒ 统一后第4层判的是「任何配了上限的参数」⇒ 名字里留着 `STROKE` 等于把「位置类」这个已拆掉的分类留在错误码上；
  - 理由二：`UNFIT`（「不符合设定要求」）说的是**参数与设定上限的关系**，属**事实层**，不替用户下「制品做不出来」的结论；
  - **code `MOD_PROCESS, 38` 不动**；
- **message 改**：「当前设备无法生产该制品」→「**参数不符合机台设定要求**」（前端无硬编码该文案，界面直接生效）；
- **删除 `ERROR_PROCESS_PARAMETER_INVALID`（code 33）**：全项目零引用 ⇒ 按 YAGNI 删掉，code 33 留空不复用；
- 出路措辞保留在**正文**（`BizException` 的 message），结论性表述交给**错误码标题** —— 分工不变，只是标题内容跟着改。

---

## 8. 口径拍板状态

**已全部拍板**（§1 的 9 条 + 下表）⇒ 本文档具备实施条件。

| 拍板项 | 结论 |
|---|---|
| 上限来源标记 | 直接用 `LimitSpec.high`（设备字段名）溯源，不加 `source` 标记（口径 7） |
| 对外文案措辞 | 「请检查参数设置或更换设备」（出路两条）（口径 8） |
| 数值回归验收 | 不设百分比阈值 ⇒ 改前/改后 diff 清单**逐条判读**（§9.3） |
| 错误码 | 改名 `ERROR_PROCESS_UNFIT_PARAM`，message「参数不符合机台设定要求」，**code 38 不动** |
| 冗余错误码 | 删 `ERROR_PROCESS_PARAMETER_INVALID`（code 33，零引用），code 33 留空不复用（YANGI，口径 9） |

---

## 9. 验收方案

### 9.1 常规

1. `pytest tests -q`（当前基线 **224 passed**）
2. 三个独立护栏脚本 exit=0：`_verify_zero_dep.py` / `_verify_e2_offline.py` / `_verify_expert_smoke.py`
3. `run_demo.py` exit=0、`export_case.py` import OK（examples 直接消费这两张表）

### 9.2 契约自检

- `tests/test_spec_contract_alignment.py`（7 例，断言对外 schema ⊇ 必填集）必须仍全绿

### 9.3 数值回归（**本批次的关键，不可省**）

**不设百分比阈值** —— 本次是**口径修正**，变动的「正确性」只能靠业务语义判断，统计比例没有判据价值。验收方式：

1. 改前：跑一个固定用例，把**全部推荐值**导出成快照（参数名 → 当前值 / 推荐值 / 方向）
2. 改后：同用例再跑一次
3. 逐项 diff，产出**变动清单**（每条标注：参数名 / 改前 / 改后 / 变动方向）
4. **由业务方逐条判读**：哪些是预期变动（下界归 0 带来的档位变化、位置类纳入裁剪），哪些是意外回归
5. 快照脚本一次性，用完即删（不进 `tests/` 长期资产）

#### 实测结果（2026-11-24）

**用例**：离线案例 `fuzzy_shortshot_low`（真实调优记录导出：规则池快照 + 真实工艺参数 + 真实机台上限）⇒ 同一案例、同一规则库、同一当前值。

**对照口径**（旧实现未提交且已被覆盖 ⇒ **复刻**旧语义作对照）：

| 维度 | OLD（改前） | NEW（改后） |
|---|---|---|
| 论域替换 | 设定值族：**只换上界、保留下界** / 位置族：整段换 [0, 行程] | 全部：整段换 [0, 上限] |
| 推荐值裁剪表 | 只含 `max_set_*` 来源的族（位置族**不在**表里） | 全量族（位置族也在表里） |
| 守卫 | 设定值族 H1 / 位置族 G6 | 统一 H1 |

**行程取值矩阵**（覆盖「设备域替换 / 守卫回落 / 经验域回落」三种论域态）：

| 行程 | 论域态 | 推荐值变动 | 第4层新增判出 |
|---|---|---|---|
| 未录 | 位置族无权威源 ⇒ 回落经验论域 | **0 条** | **0 条** |
| 250mm | 行程 < MEL 当前值 288.25 ⇒ 守卫命中回落 | **0 条** | **0 条** |
| 300mm | 行程 > 全部位置类当前值 ⇒ 整段换 [0, 300] | **0 条** | **0 条** |
| 900mm（构造场景） | MEL 判低档 ⇒ 触发 MEL 规则 | **0 条** | **0 条** |

**结论**：

1. **推荐值逐位一致（0 变动）** —— 4 组行程取值下，OLD / NEW 的推荐值、置信度、方向**完全相同**；
2. **第4层新增判出 0 条** —— 案例里没有任何「设定值超机台上限」的参数（实测值均在上限内）⇒ 变更 6 在真实数据上**不产生新增拒绝**；
3. **稳健性**：旧「设定值族 step 怎么随上界变」不可考（旧实现未提交）⇒ 对**等比缩放**与**step 不变**两种假设各跑一遍，两者给出**同一推荐值** ⇒ 结论**不依赖假设**；
4. **「位置类纳入裁剪」实际几乎不触发**（结构性原因）：位置类要产出推荐，前提是它被判**低档**（当前值落在论域低位）；而它被判低档要求**当前值 < 上限**（否则 H1 守卫先命中回落经验域）⇒ 推荐值 ≈ 当前值 ≪ 上限 ⇒ 永远裁不到。**结论：位置类进裁剪表不改变实际结果**。

> **说明**：本次对照脚本是一次性产物（复刻旧语义 + monkeypatch 内部方法，易腐）⇒ **已删除**，结论固化在本节。

---

## 10. 回退

- 改动集中在 8 个文件，无数据迁移、无接口字段增删 ⇒ 回退 = 还原文件
- 批次 A（已完成部分）单独可回退：只动一个文件，删 5 个符号 + 换回两个模块级常量
- **不要**用 `git reset --hard` 之类会波及用户其它未提交改动的操作

---

## 11. 接续点

1. 先读本文 §1（口径）与 §6（行为变更）
2. 批次 B 已完成（2026-11-24）；批次 C 见 §13
3. 后续：若再发现「伪分类」残留，先查 `LIMIT_SOURCES` 是否已能表达；能表达则一律走配置，不再加分支
4. 数值回归脚本是一次性产物（复刻旧语义 + monkeypatch 内部方法）⇒ 结论固化在 §9.3，不再重建

## 12. 相关记忆

| 记忆 | 关系 |
|---|---|
| `37c7fa50` 设定值与位置类等价的设计原则 | 变更 1 的口径来源（「整段换 `[声明下界, 声明上界]`」）——**已落地**（批次 B） |
| `e6edd0f9` 参数超限校验的分层归属原则 | 本文件是它的延续；已同步批次 A 成果与三层伪分类口径 |
| `92a85485` Service层与算法层职责分离原则 | 边界不变；本批次只收敛 service 内部与 context 交接面 |
| `968c80b1` 重构改造需小步推进 | 本批次按文件逐步改 + 每步汇报 |
| `87cc468f` 测试验收集中在每轮结束 | §9.1/§9.2 集中在一轮结束时跑一次；数值回归脚本一次性 |

---

## 13. 批次 C：差值口径收敛（来源标记改字段名 + 行程专属入口退役）

**起因**（用户原话）：

1. 「差值越限那个行程上限，没必要单独写一个函数来判定，只是一行逻辑代码」；
2. 「`STROKE_FIELD` 这个还需要吗？我认为是不需要的」；
3. 「位置参数与设定值参数同构」这种表述有歧义 —— **位置参数本身就是设定值**；
4. 「`limit_mapping.py` 这个文件也没有意义」（落点经用户拍板：**并入 `device_limits.py`**）。

**根因**：`RANGE_CHECKS` 用 `'limit_source': 'stroke'` 这个**来源类型标记**表达「这条差值检查的上限取自行程」⇒ 为此必须有一个「行程专属的取值函数」来兑现这个标记 ⇒ `resolve_stroke_limit` 这层封装是被标记逼出来的，不是业务需要。同理，`:data:`STROKE_FIELD`` 这个常量也不承载任何独立语义（它只是 `'max_injection_stroke'` 的另一个名字）。而 ``algorithms/common/limit_mapping.py`` 是**夹缝模块** —— 它自己的 docstring 就写着「`field_names` 是纯命名映射、本模块要取上界 ⇒ 沾了上下限语义」「`device_limits` 是查表、不该承担造表职责」⇒ 两边口径都不沾它 ⇒ 只能自己开一个文件，而它的内容本质上是 `device_limits`（限值表模块）的自然延伸。

**改动**：

| 动作 | 对象 |
|---|---|
| 删 | `param_limits.resolve_stroke_limit`（行程专属取值入口） |
| 删 | `param_limits.STROKE_FIELD`（字段名常量） |
| 删 | `algorithms/common/limit_mapping.py`（整个文件） |
| 改 | `param_limits._read_positive_float` → 公开 `read_positive_float(info, field_name)`（通用取值件） |
| 改 | `param_limits` 注释措辞：「位置参数与设定值参数**同构**」→「**所有参数都是设定工艺参数**」（位置参数也是）；`LIMIT_SOURCES` 的分组标签从「位置类」改为「上限取自实测注射行程」（分类轴只剩**上限来源**一个） |
| 改 | `algorithms/common/device_limits.py` 承接 `Limit` 类型别名 + `to_family_limits`（模块口径从「查表」扩为「限值表」：区间类型 + 查表 + 跨命名空间翻译）；依赖从「零依赖」变为「只依赖同包 `field_names`」 |
| 改 | `check_params.RANGE_CHECKS`：`'limit_source': 'stroke'` → `'limit_field': 'max_injection_stroke'` |
| 改 | `check_params.RangeViolation.limit_source` → `limit_field`（与 `OverLimitItem.limit_field` 同名同义） |
| 改 | `check_params.resolve_range_limits`：按每条检查项**自己声明**的 `limit_field` 取值 ⇒ 新增检查项不必改接线 |
| 改 | 引用点 import 路径统一：`process.algorithms.common.limit_mapping` → `process.algorithms.common.device_limits`（生产 2 处 + examples 2 处 + 测试 5 处） |

**行为不变**：差值越限的判据、限值、报出项全部不变（`pytest` **226 passed**）。

**收益**：

1. 「来源类型标记」与「行程专属函数」一起消失 ⇒ 与单参数侧口径一致（口径 7：溯源用设备字段名）；
2. 接线更通用 —— 原来新增一条**非行程来源**的差值检查项压根没法接线（`limit_source` 只认 `'stroke'`），现在只需声明自己的 `limit_field`；
3. 「差值越限的上限 = 机台实测注射行程」这条口径落在**两张表各自的 `high` / `limit_field` 声明**里，不再靠一个名字维系 ⇒ 常量与口径解耦；
4. 参数维度不再分类 —— 保留的分类轴只剩**上限来源**（可设定最大值 vs 实测注射行程）；
5. `algorithms/common/` 从 3 个模块减为 2 个 ⇒ 限值表的**类型 / 查表 / 翻译**归一处，不再有「两边口径都不沾」的夹缝模块。
