# Process Schema 设计笔记

> 本文归档 `backend/process/schemas/` 的**思路过程**（为什么这样设计）。
> 源码只保留「怎么用」——字段语义、必填性、形状、约束、陷阱；判据见
> `code-comment-standard.md` §一「读者分层」。
>
> 迁出范围：`schemas/optimization.py`、`schemas/rule.py`（2026-11-17）。

---

## 一、optimization.py

### 1.1 上下文三维按实体归属分组，不扁平化

`mold_info` / `machine_info` / `polymer_info` 不合并成一个扁平字典，三条理由：

1. 与 DB 模式反查的三张表 1:1 对应，字段来源可追溯；
2. 调用方可按自己「知道什么」分段填，不必在混合字段堆里判断；
3. 与 initialize 的 FromProvided 保持同一心智模型。

### 1.2 必填性分两层

维度对象本身必填（`mold_info` / `machine_info` / `polymer_info` 必须出现）—— 它们对应
`AlgorithmContext` 的必需 key，缺一个维度等于缺整类判级依据。

对象内字段的必填等级**不写在 pydantic**，而是定义在 `algorithms/fuzzy/specs.py`，由
`OptimizeDataValidator` 在算法入口校验。理由：pydantic 表达不了「液压机必填」这类条件必填；
且算法层校验能让 service / 第三方 / CLI 所有调用方自动受约束，而不是只守住一个 HTTP 入口。

所以 pydantic 里字段全是 Optional —— 那是传输形状，不是契约强度。

### 1.3 调优不复用 initialization 的三维 schema

调优的消费面与初始化不同：模具 / 材料只需极少数（多为规则筛选键与边界值），设备是重点
（HMI 设定上限决定推荐值的物理可行性）⇒ 不复用 `initialization.py` 的
`MoldInfoSchema` / `MachineInfoSchema` / `PolymerInfoSchema`。

### 1.4 optimize 无 process_set 维度

段数与模式（`inj_stg` / `hold_stg` / `vps_mode` ...）属于当前工艺本身，已包含在
`parameter` 基线内，不是外部配置 ⇒ 是三维而非四维。

### 1.5 OptimizeMoldInfoSchema：未纳入的字段

需成对使用才有意义的字段不纳入：

- `projected_area`（在 `GatingSystem` 表，按 `shot_index` 选）
  + 机台 `max_clamping_force`（在 `InjectionMoldingMachine` 主表）
  → 飞边类推荐的压力上界。两者跨两张表，单独取其一无法算出所需锁模力。

### 1.6 OptimizeMachineInfoSchema：为何必需设备维度

fuzzy 算法构造隶属度函数时需要参数论域 `[min_val, max_val]`，而现状两处都不看设备：

- `RuleKeyword` 覆盖到的参数：论域取 `keyword.range_min` / `range_max`（全厂通用值）
- 未覆盖的参数：论域取 当前值 × 2（自我参照，等于猜）

后果：同一套参数在 180MPa 与 350MPa 的机上被判成同一模糊等级，规则条件命中失真。

算法侧接设备实际值的改造另行讨论，本 schema 先把契约钉死。

### 1.7 OptimizeMachineInfoSchema：未纳入的能力字段

`screw_diameter` / `max_injection_volume` / `plasticizing_capacity` 等 —— 对调优无意义，
initialize 才需要。

**例外**：`max_injection_stroke`（最大注射行程）**两条链路都纳入** —— 它是位置类
判级论域上界的**唯一权威源**（fuzzy 必填），也是 expert 契约的必填字段
（初始化链路同样缺了就报错）。两个对外 schema 都有它，否则会被 `extra="ignore"`
静默丢弃。

### 1.8 OptimizeMachineInfoSchema：命名空间

本 schema 的字段名 == ORM 字段名（`InjectionUnit` / `InjectionMoldingMachine`），
fuzzy 侧的命名空间就是业务 / ORM 名 —— 这些机器属性字段**不在** fuzzy 的命名映射表内
（`field_names.FIELD_NAME_ALIAS` 只收工艺参数，如 `inj_spd` → `IV`）。

### 1.9 parameter 一律 flat

两个入口的 `parameter` 都用 flat 形状（key 都是 ORM 字段名），三条理由：

- 算法契约源头就是 flat（`AlgorithmContext.process_parameter`，`FIELD_NAME_ALIAS`
  按 flat 业务名翻译为算法名），上游嵌套 = 多一层翻译、多一处故障点；
- 服务契约是镜像（`ProcessParameterSchema` 镜像 ORM，与 `_to_full_dict` 同源），用 flat
  后调用方无歧义；
- 即使是「稀疏覆盖」（只带要改的几个键），也用 flat 形状 —— 与「全量基线」的差别只在
  数量，不在 length。

差异在「数量」而非「length」：

- FromProvided 用全量基线：第三方需要明确契约，传不齐就是漏数据；
- FromCondition 用稀疏覆盖：调用方只带要改的几个键，service 按 `_resolve_baseline`
  （入参优先，否则 ORM 反查）补齐未传的字段。

### 1.10 rule_library_code 为何不在公共入参

该字段是算法内部的资源选择（哪一套规则库），调优侧不需知道该概念。
`RuleQueryContext` 已自带 fallback 链（user 指定 → 按 `polymer_abbreviation` +
`product_category` 自动解析），上游完全可以自解，传出来只是多一个泄漏点。

实际取用路径：由 service 从 `condition.process_context_snapshot` 注入。

---

## 二、rule.py

### 2.1 规则中心列表专用 Schema 的由来

规则库 / 规则关键字 / 规则方法 / 专家规则列表接口原先复用通用 `PaginationBaseSchema`，
而它只声明 `page_no` / `page_size` / `sort` ⇒ 前端传的筛选参数（`owner_type` /
`library_type` / `library_name` / `is_active` / `keyword_type` / `rule_code` ...）
在校验阶段被**直接丢弃**，导致列表页筛选框全部失效（个别接口靠 view 里手工
`request.GET.get` 兜住了部分参数，漏掉的那些则静默失效）。

因此单独建了规则中心列表专用 Schema，字段名与 `process.services.rule` 对应 service 的
形参**一一对应** —— view 层用 `**cleaned_data` 透传，名字必须严格对齐，否则会 TypeError。

---

## 三、initialization.py

### 3.1 单射设计 ⇒ 维度字段扁平化到同一层

工艺推理时一台机台只取一个 `InjectionUnit`（按 `injection_index` 选取）⇒ `injection_unit`
的字段扁平化到 `machine_info` 同一层，避免 view 层做二次融合。

同理，一个 mold 只取第一个 cavity / gate ⇒ `product` / `cavity` / `gate` 的字段扁平化到
`mold_info` 同一层。

### 3.2 masterdata 入口的内部流程

- 入口适配：3 个 masterdata ID + `shot_index` + `injection_index`
- 数据前处理：service 层从 ORM 构建完整快照（`process_context_snapshot`）
- 推理算法 + 落库：创建 Condition（存完整快照）+ ProcessParameter

---

## 四、parameter.py

### 4.1 SettingProcessSchema 内部字段用 dict 而非强类型子 schema

三条理由：

1. `table_data` 是动态结构 `[{label, unit, sections: [n, ...]}, ...]`，段数由 `max_stage` 决定；
2. 子结构由前端工艺参数组件维护（optimization 用 `TuningParameterPanel`，library 用
   `LibraryParameterForm`），后端只透传；
3. 业务上 schema 只需保证各段存在这层结构。

### 4.2 NEST 容器的可扩展字段

`ProcessParameterNestSchema` 计划中的可扩展字段（直接平铺到该 schema，不另起 schema）：

- `metadata`：参数元数据
- `algorithm_hint`：算法侧配置
- 其他 parameter 业务相关字段

---

## 五、record.py

### 5.1 按"结构"而非"段归属"命名

`ProcessConditionAndParameterSchema` 描述的是「condition + parameter 组合」这一结构，
而非 records 段的归属 —— 便于跨段复用。

### 5.2 四条设计选择

- 保留 `parameter` 包装层（不顶层平铺 `setting_process`）；
- `parameter` 为 Optional：不传则不创建空 parameter，避免数据库污染（业务上用户可能先建
  condition 骨架，后续填数据再调 `PUT /api/processes/records/<int:condition_id>/`）；
- 100% 真实流量来自前端 UI（NEST）；
- 算法 / 移植 / 优化请直接用 `ProcessParameterSchema`（FLAT）。
