# 工艺参数写入前端 + 原子操作设计 —— 2026-09-23

> 状态：实施中
> 范围：`/initialization/from-masterdata/` 响应写入前端工艺参数；Condition + Parameter 原子性强化

## 一、需求

1. **前端字段映射**：后端推理响应（扁平字段）写入前端嵌套结构 `settingProcessForm`
2. **原子操作**：Condition + Parameter 落库必须是原子（要么都成功，要么都回滚）

## 二、字段映射关系

### 2.1 后端响应（扁平） → 前端嵌套

后端 `result.process`（来自 `ProcessParams.to_dict()`）：
```python
{
    'inj_stg', 'inj_spd_steps', 'inj_pres_steps', 'inj_pos_steps',
    'inj_t', 'inj_dly_t',
    'vps_mode', 'vps_pos', 'vps_t', 'vps_pres', 'vps_spd',
    'hold_stg', 'hold_pres_steps', 'hold_spd_steps', 'hold_time_steps', 'hold_limit_spd',
    'cool_t',
    'met_stg', 'met_pres_steps', 'met_rot_spd_steps', 'met_back_pres_steps', 'met_pos_steps', 'met_lim_t',
    'met_end_pos',
    'pre_met_decomp_mode', 'pre_met_decomp_pres', 'pre_met_decomp_spd', 'pre_met_decomp_t', 'pre_met_decomp_dist',
    'pst_met_decomp_mode', 'pst_met_decomp_pres', 'pst_met_decomp_spd', 'pst_met_decomp_t', 'pst_met_decomp_dist',
    'brl_temp_stg', 'noz_temp', 'brl_temp_steps',
}
```

前端 `settingProcessForm`（嵌套）：
```ts
{
  injection: {
    stage, table_data[压力/速度/位置], injection_time, delay_time, cooling_time
  },
  vp_switch: { mode, position, time, pressure, velocity },
  holding: {
    stage, table_data[压力/速度/时间]
  },
  metering: {
    stage, table_data[压力/螺杆转速/背压/位置], delay_time, ending_position
  },
  barrel_temperature: {
    stage, table_data[温度]
  }
}
```

### 2.2 映射规则

| 后端 | 前端 | 类型 |
|------|------|------|
| `process.inj_stg` | `injection.stage` | int |
| `process.inj_pres_steps[]` | `injection.table_data[0].sections[]` | float[] → 长度 6 |
| `process.inj_spd_steps[]` | `injection.table_data[1].sections[]` | float[] → 长度 6 |
| `process.inj_pos_steps[]` | `injection.table_data[2].sections[]` | float[] → 长度 6 |
| `process.inj_t` | `injection.injection_time` | float |
| `process.inj_dly_t` | `injection.delay_time` | float |
| `process.cool_t` | `injection.cooling_time` | float |
| `process.vps_mode` | `vp_switch.mode` | int |
| `process.vps_pos` | `vp_switch.position` | float |
| `process.vps_t` | `vp_switch.time` | float |
| `process.vps_pres` | `vp_switch.pressure` | float |
| `process.vps_spd` | `vp_switch.velocity` | float |
| `process.hold_stg` | `holding.stage` | int |
| `process.hold_pres_steps[]` | `holding.table_data[0].sections[]` | 长度 5 |
| `process.hold_spd_steps[]` | `holding.table_data[1].sections[]` | 长度 5 |
| `process.hold_time_steps[]` | `holding.table_data[2].sections[]` | 长度 5 |
| `process.met_stg` | `metering.stage` | int |
| `process.met_pres_steps[]` | `metering.table_data[0].sections[]` | 长度 4 |
| `process.met_rot_spd_steps[]` | `metering.table_data[1].sections[]` | 长度 4 |
| `process.met_back_pres_steps[]` | `metering.table_data[2].sections[]` | 长度 4 |
| `process.met_pos_steps[]` | `metering.table_data[3].sections[]` | 长度 4 |
| `process.met_lim_t` | `metering.delay_time` | float |
| `process.met_end_pos` | `metering.ending_position` | float |
| `process.brl_temp_stg` | `barrel_temperature.stage` | int |
| `process.brl_temp_steps[]` | `barrel_temperature.table_data[0].sections[]` | 长度 10 |
| `process.noz_temp` | （暂不映射，前端无对应字段） | - |

### 2.3 padding 规则

后端 steps 数组可能少于 max 长度（如 3 段压力但 max=6）：
- 后端填 null（已在 `_create_process_parameter` 实现）
- 前端直接用 sections（不需要 padding）

但前端 max_stage 是固定 6/5/4/10，如果 stages 短，sections 数组也短，会破坏 UI。

**方案**：前端映射时 padding 到 max 长度，缺的填 null。

## 三、原子操作设计

### 3.1 后端现状（已原子，但语义不显式）

`backend/process/services/initialization_service.py:967-1043` 的 Mode B：
```python
with transaction.atomic():
    # ... 算法推理
    condition = ProcessCondition.objects.create(...)  # 工艺条件
    parameter = cls._create_process_parameter(condition, result)  # 工艺参数
```

`with transaction.atomic():` 保证两个 ORM 写入都在同一事务里，要么都成功要么都回滚。**已经是原子的**。

### 3.2 前端现状（默认原子，但字段写入分散）

当前 `OptimizationCreate.vue` getInitialProcess：
```ts
if (result?.condition_id) form.condition.id = result.condition_id
if (result?.condition_no) form.condition.condition_no = result.condition_no
if (activeRound.value && result?.parameter_id) {
  activeRound.value.parameter_id = result.parameter_id
}
if (activeRound.value && result?.seq_idx != null) {
  activeRound.value.seq_idx = result.seq_idx
}
```

JS 单线程同步执行：
- 顺序执行，要么全部赋值，要么都不执行（catch 不执行任何赋值）
- **已经是原子的**（JS 单线程特性）

但分散写可读性差，缺一个明确的"应用响应"入口。

### 3.3 强化方案

**后端**（不改架构，仅文档化）：
- 在 `_create_process_parameter` 加注释说明"与 ProcessCondition 同事务，由调用方负责"
- 在 Mode B/C 入口的 docstring 明确说明原子语义

**前端**（封装响应处理）：
- 加 `applyInferResultToForm(result)` helper
- 把分散的字段赋值集中到 helper
- 调用点更清晰

## 四、实施清单

| 项 | 文件 | 改动 |
|----|------|------|
| 4.1 | `frontend/src/views/process/optimization/pages/OptimizationCreate.vue` | 加 `padSteps` + `mapInferResultToParameter` helper |
| 4.2 | `frontend/src/views/process/optimization/pages/OptimizationCreate.vue` | 加 `applyInferResultToForm(result)` 统一响应处理 |
| 4.3 | `frontend/src/views/process/optimization/pages/OptimizationCreate.vue` | `getInitialProcess` 调用新 helper |
| 4.4 | `backend/process/services/initialization_service.py` | 在 `_create_process_parameter` 加注释（说明同事务） |

## 五、边界场景

1. **后端 result 为空**：catch 处理，不进入赋值
2. **后端 result.process 缺失**：mapInferResultToParameter 返回 settingProcessForm 默认值
3. **后端 seq_idx 缺失**：parameter_id 写入但 seq_idx 保持 null（用户后续可点优化工艺触发 infer）
4. **mold_temp / hot_runner 未在前端展示**：暂不映射（前端 ProcessSettings 只覆盖 process 部分）
