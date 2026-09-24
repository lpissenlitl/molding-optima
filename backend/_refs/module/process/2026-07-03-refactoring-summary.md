# 2026-07-03 重构进展总结

> 本文档记录 2026-07-01 ~ 2026-07-03 三天内 molding-optima 工艺模块的关键重构决策与落地状态。
> 与本批次相关的源代码改动集中在 `process/` 目录下。

## 1. 重构总览

### 1.1 三大主线

1. **4 维独立 dict 重构**（职责清晰 / 单一数据来源）
   - 算法引擎 `ProcessInitializer` 接受 `machine_info / polymer_info / mold_info / process_set` 4 个独立 dict
   - service 层、view 层透传，**不再做中间组装**
2. **字段语义重构**
   - `process_context` 与 `process_context_snapshot` 字段分离（前端输入 vs 后端不可变快照）
   - `condition_code` → `condition_no`（业务唯一编号统一用 `_no` 后缀）
   - `override_fields` → `process_context`（与模型字段对齐）
   - 删除前端传的 `status / origin_type`（由后端固定为 `draft / ai_recommendation`）
3. **服务层架构重构**
   - main_service 整体复制 molding-expert，删除 `injection_unit_id` 字段
   - Service 模块 API 采用"模块函数门面"模式（view 调用模块级函数，内部用 classmethod）
   - mode A/B 响应统一 + mode A 修复"创建新 Parameter"未落库的 bug

### 1.2 当前进度（2026-07-03）

| 阶段 | 状态 | 说明 |
|------|------|------|
| 模型字段（ProcessCondition / ProcessParameter） | ✅ | 三层结构 + version tree + process_context + process_context_snapshot |
| main_service.py 基础 CRUD | ✅ | 整体复制 molding-expert process_service.py |
| 工艺初始化 ExpertEngine | ✅ | InitRuleMatcher 三级回退 + 8 条规则入库 |
| 工艺初始化接口 | ✅ | Mode A / Mode B 统一响应 + condition_no |
| 算法引擎 4 维独立 dict | ✅ | ProcessInitializer 接受 4 个独立 dict |
| Schema 扁平化 + 嵌套封装 | ✅ | MachineInfo / PolymerInfo / MoldInfo / ProcessSet |
| requirements 补 pydantic | ✅ | molding-expert + molding-optima 三处都补 pydantic==2.9.2 |
| FuzzyEngine 接入 service | ✅ | optimize_service / recommendation_service 都已注册 |
| FuzzyEngine 多引擎合并 / trend 后处理 | ⏳ | 留 TODO |
| 单元测试 | ⏳ | tests/ 仍空 |
| _dev_refs 文档同步 | ⏳ | 本文档先汇总 |

## 2. 4 维独立 dict 重构（核心）

### 2.1 设计动机

**之前（混合 dict 反模式）**：

```python
# 工艺推理上下文什么都塞进一个 dict
product_info = {
    **mold_info,           # 产品参数
    **process_set,         # 段数/模式
    "shot_index": 1,
    "injection_index": 1,
    ...
}
# 工艺设定（段数/模式）混在 product_info 里，语义错位
```

**问题**：
- 工艺设定（inj_stg / vps_mode 等）属于"工艺元数据"，与产品参数（product_weight / gate_type）本质不同
- view 层做数据融合违反职责分离
- 算法引擎 `ProcessInitializer.derive(product_info)` 接收什么都装的混合 dict

### 2.2 设计原则

| 维度 | 内容 | 数据源 |
|------|------|--------|
| `machine_info` | 设备信息（机台本身 + 注射单元合一） | masterdata.InjectionMoldingMachine + InjectionUnit |
| `polymer_info` | 材料信息 | masterdata.Polymer |
| `mold_info` | 模具信息（模具级 + 产品/浇口/壁厚派生合一） | masterdata.Mold + GatingSystem + Cavity + Gate |
| `process_set` | 工艺设置（段数 + 模式） | 前端传入 / 默认值 |

### 2.3 调用链（最终）

```
ProcessInferSchema（4 个字段）
  ├─ machine_info
  ├─ polymer_info
  ├─ mold_info
  └─ process_set
       ↓ view 直传
initialization_service.infer_initial_params(
    machine_info, polymer_info, mold_info, process_set
)
       ↓ 透传
ProcessInitializationService.infer_initial_params(
    machine_info, polymer_info, mold_info, process_set
)
       ↓ 透传
ProcessInitializer(
    machine_info=..., polymer_info=...,
    mold_info=...,        # self.mold
    process_set=...        # self.process_set
).derive()
```

**每个环节职责单一，没有中间组装**。

### 2.4 算法引擎内部（ProcessInitializer）

| 内部状态 | 来源 |
|----------|------|
| `self.machine` | `__init__(machine_info)` |
| `self.material` | `__init__(polymer_info)` |
| `self.mold` | `__init__(mold_info)`（产品/浇口/壁厚） |
| `self.process_set` | `__init__(process_set)`（段数/模式） |

字段读取：
- `prod['product_weight'] / 'gate_type' / 'ave_thickness' / ...` → `self.mold[...]`
- `prod['vps_mode'] / 'VP_switch_mode' / 'inj_stg' / 'hold_stg' / 'met_stg' / ...` → `self.process_set[...]`

### 2.5 规则匹配 context

`ProcessInitializer.derive()` 内 `rule_matcher.match()` 传入 4 维 context：

```python
self._coeffs = self.rule_matcher.match({
    'machine': self.machine,
    'material': self.material,
    'mold': self.mold,
    'process_set': self.process_set,
})
```

## 3. 字段语义重构

### 3.1 process_context vs process_context_snapshot 分离

| 字段 | 职责 | 写入方 | 用途 |
|------|------|--------|------|
| `process_context` | 业务覆盖输入 | 前端可控 | 保留用户意图 |
| `process_context_snapshot` | 不可变快照 | 后端自动生成 | 追溯/审计 |

**之前**：`override` 存到 snapshot.overrides，语义混乱
**现在**：`process_context` 独立字段；snapshot 保留 matched_rules + source

### 3.2 condition_code → condition_no

按 [唯一编号字段命名规范](../process-models-design.md)，业务唯一编号统一用 `_no` 后缀：

| 字段 | 之前 | 现在 |
|------|------|------|
| `condition_code` | 业务唯一编号（实际是 `_code`） | `condition_no` |
| `param_code` | 业务唯一编号（实际是 `_code`） | `param_code`（保持，**用户决定不改**） |

影响范围：
- models.py / models/process_condition.py
- schemas.py（ProcessConditionSchema / ProcessInitializationSchema）
- services/initialization_service.py（`condition_no or self._auto_condition_no()`）
- views/processes.py
- 私有函数 `_auto_condition_code` → `_auto_condition_no`
- molding-expert 同步（process_service.py / models.py）

### 3.3 override_fields → process_context（命名统一）

```json
// 之前
{
    "override_fields": {
        "product_weight": 80,
        "gate_type": "点浇口"
    }
}

// 现在
{
    "process_context": {
        "product_weight": 80,
        "gate_type": "点浇口"
    }
}
```

Schema 端删除 `OverrideFieldsSchema`（Pydantic 子结构），改用通用 `dict`。

### 3.4 status / origin_type 由后端固定

| 字段 | 之前 | 现在 |
|------|------|------|
| `status` | 前端传 | 后端固定 `'draft'` |
| `origin_type` | 前端传 | 后端固定 `'ai_recommendation'` |

**理由**：状态/起源是后端业务逻辑决定（刚创建未测试 / 本接口就是算法初始化入口），不应由前端传。

## 4. 初始化接口重构

### 4.1 响应统一（Mode A / Mode B）

```json
{
    "param_source": "algorithm_init",
    "condition_id": int,        // Mode A 沿用 / Mode B 新建
    "parameter_id": int,        // 两种模式都新建 ProcessParameter
    "matched_rules": [...],
    "process": {...},
    "mold_temp": {...},
    "hot_runner": {...},
    "summary": {...}
}
```

### 4.2 Mode A 落库 bug 修复

**之前**：`infer_initial_params(condition_id=...)` 只做推理不落库，与 view 注释"创建新 Parameter 记录"不符

**现在**：`infer_initial_params` 接受 `save: bool = True`（默认）参数；Mode A 调用时传 `save=True`，在已有 condition 上创建新 ProcessParameter

### 4.3 Infer 接口（/initialization/infer/）

```json
// 请求体
{
    "machine_info": {...},
    "polymer_info": {...},
    "mold_info": {...},
    "process_set": {...}
}

// 响应：与 /initialization/ 相同，但 condition_id / parameter_id 为 null
```

`save=False`（纯推理，不落库）。

## 5. 服务层架构

### 5.1 main_service 整体复制 molding-expert

- 新建 [process/services/main_service.py](file:///f:/items/moldingx/molding-optima/backend/process/services/main_service.py)（425 行）
- 修正原 molding-expert 的字段拼写错误（`paramter_code` → `param_code`、`prameter_source` → `param_source`）
- 删除 `injection_unit_id` 字段（molding-optima 用 `injection_machine + injection_index` 业务规则推导）
- view 层 import 从 `condition_service` 改 `main_service`
- 删除 `process/services/condition_service.py`

### 5.2 模块函数门面模式

**原则**：view 层只依赖模块名（`initialization_service.xxx()`），不直接调用类方法（避免耦合）

```python
# process/services/initialization_service.py

class ProcessInitializationService:
    """内部实现层（@classmethod + 类级单例）"""
    @classmethod
    def infer_initial_params(cls, machine_info, polymer_info, mold_info, process_set, ...):
        # ... 内部实现
        pass


# === 模块级公开 API（对外门面）===

def infer_initial_params(machine_info, polymer_info, mold_info, process_set, ...):
    """view 层调用的入口"""
    return ProcessInitializationService.infer_initial_params(...)
```

**view 层**：
```python
from process.services import initialization_service
return initialization_service.infer_initial_params(...)
```

**反例**（要避免）：
```python
# ❌ view 层耦合到类
from process.services.initialization_service import ProcessInitializationService
ProcessInitializationService.infer_initial_params(...)
```

### 5.3 InitRuleMatcher 三级回退

`InitRuleMatcher` 启动时按以下顺序构建规则缓存：

1. **数据库优先**：`ExpertRule.objects.filter(is_active=True).order_by('priority')`
2. **JSON 兜底**：[`InitRuleLoader`](file:///f:/items/moldingx/molding-optima/backend/process/engines/expert/rule_loader.py) 读取 `expert_rules/init_rules.json`
3. **内置默认**：`_build_fallback()` 提供硬编码 `DEFAULT_RULE` 系数

## 6. Schema 扁平化（inference-input）

### 6.1 4 个独立 Schema

```python
class MachineInfoSchema(BaseSchema):
    """设备信息（机台本身 + 注射单元合一）"""
    power_method: Optional[str]
    screw_diameter / max_set_injection_* / max_set_holding_* / max_set_screw_rotation_speed / max_set_metering_pressure / nozzle_type

class PolymerInfoSchema(BaseSchema):
    """材料信息"""
    abbreviation / recommend_melt_temperature / recommend_shear_linear_speed / recommend_back_pressure / recommend_mold_temperature / melt_density

class MoldInfoSchema(BaseSchema):
    """模具信息（模具级 + 产品/浇口/壁厚派生合一）"""
    shot_count / product_weight / runner_weight / ave_thickness / max_thickness / max_length
    gate_type / gate_radius / gate_length / gate_width / valve_num / inject_cycle_require

class ProcessSetSchema(BaseSchema):
    """工艺设置（段数 + 模式）"""
    inj_stg / hold_stg / met_stg / barrel_temperature_stage
    VP_switch_mode / vps_mode / pre_met_decomp_mode / pst_met_decomp_mode
```

### 6.2 ProcessInferSchema

```python
class ProcessInferSchema(BaseSchema):
    machine_info: MachineInfoSchema
    polymer_info: PolymerInfoSchema
    mold_info: MoldInfoSchema       # 合并了原 ProductInfoSchema
    process_set: ProcessSetSchema
```

### 6.3 ProcessInitializationSchema（落库接口）

```python
class ProcessInitializationSchema(BaseSchema):
    # Mode A
    condition_id: Optional[int]
    # Mode B
    mold_id / polymer_id / injection_machine_id
    shot_index / injection_index
    # 业务上下文（前端输入，独立字段）
    process_context: Optional[dict]    # 替代原 override_fields
    # 工艺设置（嵌套）
    process_set: Optional[ProcessSetSchema]
    # 不再有 status / origin_type / override_fields 顶层字段
    condition_no: Optional[str]      # 替代原 condition_code
```

## 7. dependencies 与工程配置

### 7.1 pydantic 依赖补充

| 文件 | 状态 |
|------|------|
| `molding-optima/requirements.txt` | ✅ 补 `pydantic==2.9.2` |
| `molding-expert/molding-expert-service/requirements.txt` | ✅ 补 `pydantic==2.9.2` |
| `molding-expert/molding-expert-service/requirements_new.txt` | ✅ 补 `pydantic==2.9.2` |

注：molding-expert 的两个 requirements.txt 文件末尾有 CRLF 混合换行符（导致 SearchReplace 工具无法匹配），用 `Add-Content` 绕过。

### 7.2 数据库迁移

由于本批次新增/修改字段，需要 `python manage.py makemigrations process` + `migrate`：

- 新增 `ProcessCondition.process_context` 字段（JSONField, null=True）
- `condition_code` → `condition_no`（RenameField）
- 后续根据 `process_context` 业务使用再生成迁移

## 8. 文件清单（本批次改动）

### 8.1 新增

- `process/services/main_service.py`（425 行，整体复制 molding-expert）
- `_dev_refs/2026-07-03-refactoring-summary.md`（本文档）

### 8.2 删除

- `process/services/condition_service.py`（被 main_service 取代）

### 8.3 主要修改

| 文件 | 改动 |
|------|------|
| `process/models.py` | condition_code → condition_no |
| `process/models/process_condition.py` | 新增 process_context 字段；condition_code → condition_no |
| `process/models/process_parameter.py` | 暂未改（param_code 用户决定不改） |
| `process/schemas.py` | 合并 MachineInfo/InjectionUnit、MoldInfo/ProductInfo；ProcessInferSchema 4 字段；ProcessInitializationSchema 删除 status/origin_type/override_fields |
| `process/services/initialization_service.py` | 4 维独立 dict；模块函数门面；移除 status/origin_type/overrides 参数；_build_product_info → _build_mold_info |
| `process/services/recommendation_service.py` | 引擎自注册（_register_default_engines）；_build_context 增加 trend 分析；返回带 param_source/parameter_id |
| `process/services/optimize_service.py` | 接入 FuzzyEngine（_infer_via_fuzzy_engine）；保留 DEFECT_OPTIMIZATION_HINTS 兜底 |
| `process/views/processes.py` | import 改为 main_service；覆盖字段提取改为 cleaned_data.get("process_context")；Mode A/B 响应注释同步 |
| `process/engines/expert/initializer.py` | __init__/derive 接受 4 维 dict；self.mold / self.process_set 分离 |
| `molding-expert/molding-expert-service/process/models.py` | 同步 condition_code → condition_no；新增 process_context 字段 |
| `molding-expert/molding-expert-service/process/services/process_service.py` | 同步 condition_code → condition_no |
| `requirements.txt` × 3 | 补 pydantic==2.9.2 |

## 9. 待办（按优先级）

### 9.1 短期

- [ ] `_dev_refs/process-models-design.md` 同步：condition_code → condition_no
- [ ] `_dev_refs/process-ai-architecture-design.md` 同步：process_context 字段、4 维独立 dict
- [ ] `_dev_refs/init-api-refactor-design.md` 同步：override_fields → process_context、status/origin_type 后端固定
- [ ] `_dev_refs/infer-input-flattening-design.md` 同步：5 个独立 Schema → 4 个
- [ ] 数据库迁移执行（makemigrations + migrate）
- [ ] `ProcessCondition.process_context` 实际使用验证（端到端测试）

### 9.2 中期

- [ ] FuzzyEngine trend 后处理（worsening/improving/stable 系数调整）
- [ ] FuzzyEngine 多引擎合并策略（同参数 confidence 取最高）
- [ ] recommend 接口接入 view（`/api/processes/recommend/`）
- [ ] 单元测试补充：InitRuleMatcher / ProcessInitializer / FuzzyEngine

### 9.3 长期

- [ ] RuleMinerEngine 接入（自学习闭环）
- [ ] LLMEngine 接入（RAG 检索 + 大模型推理）
- [ ] DOEGA 引擎预留接口

## 10. 关键设计原则（沉淀）

1. **4 维独立 dict**：每个维度职责单一，不要混在 product_info 这种什么都装的 dict 里
2. **业务唯一编号用 `_no` 后缀**：可重复的分类代码用 `_code`
3. **`process_context` 与 `process_context_snapshot` 分离**：前端输入 vs 后端不可变快照
4. **service 模块 API 用模块函数门面**：view 层只调用模块名，不耦合类
5. **后端固定决定状态/起源**：status/origin_type 不让前端传
6. **算法引擎纯计算**：不查库，所有数据由调用方提供（4 维 dict 透传）

## 11. 相关文档

- [algorithm-context-design.md](algorithm-context-design.md) — 业务覆盖与后端快照的"双重来源"原则
- [process-models-design.md](process-models-design.md) — 模型详细定义（部分需更新 condition_code → condition_no）
- [infer-input-flattening-design.md](infer-input-flattening-design.md) — 5 字段扁平化设计（已部分过时，5 字段 → 4 字段）
- [init-api-refactor-design.md](init-api-refactor-design.md) — Mode A/B 统一落库决策（部分需更新）
- [fuzzy-engine-migration-design.md](fuzzy-engine-migration-design.md) — FuzzyEngine 迁移方案（5 阶段）
- [process-ai-architecture-design.md](process-ai-architecture-design.md) — 完整 AI 架构（部分需更新）

---

*文档生成时间：2026-07-03*
*最后更新：2026-07-03*
