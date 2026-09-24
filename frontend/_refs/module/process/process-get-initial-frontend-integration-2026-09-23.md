# getInitialProcess 接口打通 —— 2026-09-23

> 状态：实施中
> 范围：`OptimizationCreate.vue getInitialProcess` 接入 `/api/processes/initialization/from-masterdata/`
> 关联文档：[process-initialization-design-summary-2026-09-22.md](file:///f:/items/moldingx/molding-optima/docs/process-initialization-design-summary-2026-09-22.md)

## 一、目标

让 [获取初始工艺] 按钮真正打通后端：

- 5 个必填项（模具/注塑机/材料 + shot_index/injection_index）由 ProcessCondition 组件校验
- 通过校验后调用 `/api/processes/initialization/from-masterdata/` 接口
- 响应写入 `form.condition.id`（condition_id）和 `activeRound.parameter_id`（parameter_id）
- 成功提示 / 错误提示

## 二、范围边界

### ✅ 范围内
- API 函数封装（`api/index.ts`）
- `getInitialProcess` 函数实现（校验 + 调用 + 响应处理）
- `makeRound` 新增 `parameter_id` 字段（容纳后端响应）
- 错误处理（toast）

### ❌ 不在本次范围（留作下一轮）
- **工艺参数扁平 → 嵌套映射**：后端 `result.process` 是扁平结构
  （`inj_pres_steps/hold_time_steps/cool_t/noz_temp/vps_pos/...`），
  前端 `settingProcessForm` 是嵌套结构（`injection.table_data[0].sections`），
  二者映射需独立函数实现，差异较大，留作下一轮专题。
- `process` / `mold_temp` / `hot_runner` / `summary` 这些字段只 toast 摘要，不映射到表单。
- `getOptimizedProcess` 同样为 TODO，本次不动。

## 三、实施步骤

1. **api/index.ts** —— 新增 `processInitializationFromMasterdata`
2. **OptimizationCreate.vue** —— `makeRound` 加 `parameter_id`，`getInitialProcess` 实现

## 四、API 契约（参考 doc）

### POST `/api/processes/initialization/from-masterdata/`

请求：
```json
{
    "mold_id": 100,                   // 必填
    "polymer_id": 5,                  // 必填
    "injection_machine_id": 10,       // 必填
    "shot_index": 0,                  // 可选，默认 0
    "injection_index": 0,             // 可选，默认 0
    "process_set": {...}              // 可选
}
```

实际响应（service 返回）：
```json
{
    "condition_id": 88,
    "parameter_id": 92,
    "shot_index": 0,
    "injection_index": 0,
    "param_source": "algorithm_init",
    "matched_rules": [...],
    "process": {...},
    "mold_temp": {...},
    "hot_runner": {...},
    "summary": {...}
}
```

## 五、关键文件路径

- [frontend/src/api/index.ts](file:///f:/items/moldingx/molding-optima/frontend/src/api/index.ts) — API 函数
- [frontend/src/views/process/optimization/pages/OptimizationCreate.vue](file:///f:/items/moldingx/molding-optima/frontend/src/views/process/optimization/pages/OptimizationCreate.vue) — getInitialProcess 实现