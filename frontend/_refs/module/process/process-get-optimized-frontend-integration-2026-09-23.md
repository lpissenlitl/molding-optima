# getOptimizedProcess 接口打通 —— 2026-09-23

> 状态：实施中
> 范围：`OptimizationCreate.vue getOptimizedProcess` 接入 `/api/processes/optimization/infer/`
> 关联文档：
> - [optimization-infer-design-status-2026-09-22.md](file:///f:/items/moldingx/molding-optima/docs/optimization-infer-design-status-2026-09-22.md)
> - [process-get-initial-frontend-integration-2026-09-23.md](file:///f:/items/moldingx/molding-optima/docs/process-get-initial-frontend-integration-2026-09-23.md)

## 一、目标

让 [获取优化工艺] 按钮真正打通后端：

- 前置校验：`form.condition.id` 和 `activeRound.seq_idx` 必须存在（必须先获取初始工艺）
- 调用 `/optimization/infer/` 接口
- 响应写入：创建新轮次（optimized）+ 切换 active_round_id
- 更新 `previousSuggestion`（用 infer 响应的 suggestion 字段）

## 二、范围边界

### ✅ 范围内
- API 函数封装（`api/index.ts`）
- `getOptimizedProcess` 函数实现（前置校验 + 调用 + 创建新轮次 + 切换 active）
- `makeRound` 新增 `seq_idx` 字段
- `getInitialProcess` 响应处理补 `seq_idx` 写入（**前置依赖**）
- **Backend 改动**：`infer_from_masterdata` 响应补 `seq_idx` 字段（**前置依赖**）
- 更新 `previousSuggestion` 为 infer 响应（替换 mock 数据）

### ❌ 不在本次范围
- **工艺参数扁平 → 嵌套映射**（与 getInitialProcess 一致，留作下一轮）
- `isFieldChanged` 等高亮逻辑（依赖上一轮 vs 本轮对比）
- manual-adjust 独立接口（文档原则 8）
- onSubmit（保存）打通

## 三、API 契约

### POST `/api/processes/optimization/infer/`

请求：
```json
{
    "condition_id": 88,             // 必填
    "parent_seq_idx": 1,           // 必填（业务编号）
    "parameter": {...},             // 可选（手动修改覆盖）
    "feedback": {
        "defect": [...],            // 缺陷反馈（多缺陷列表）
        "observations": [...],      // 实测观察（按需）
        "tuning_result": "effective" | "ineffective" | null
    }
}
```

响应：
```json
{
    "new_parameter": {
        ...参数 dict,
        "parameter_id": 92,
        "seq_idx": 2
    },
    "suggestion": {
        "source_type": "fuzzy_rule",
        "recommendation_id": 15,
        "groups": [
            {
                "category": "注射参数",
                "icon": "mdi:speedometer",
                "items": [
                    { "description": "...", "direction": "increase", "rule_refs": ["M001"] }
                ]
            }
        ]
    }
}
```

## 四、关键设计决策

### 决策 1：infer 后创建新轮次而非替换当前轮次

**理由**：
- 调机树语义：每轮是工艺的一次快照
- 用户可能想对比多轮之间的差异
- RoundTimeline 已支持多轮渲染

### 决策 2：previousSuggestion 来源是 infer 响应

**理由**：
- 文档已确认：`previousSuggestion` 是"上一轮 infer 返回的 suggestion 字段"
- 当前前端是 mock 数据（comment 明确说"开发阶段 mock"）
- infer 响应能精准展示上一轮算法建议

### 决策 3：seq_idx 存储位置

**位置**：放在 `round.seq_idx`（顶级字段），与 `parameter_id` 平级

**理由**：
- 不放在 `parameter` 内部，保持 settingProcessForm 纯度
- 与 docs 文档语义对齐（`parent_seq_idx` 是业务编号，非 DB ID）

### 决策 4：后端补 infer_from_masterdata 响应 seq_idx

**现状**：`backend/process/services/initialization_service.py` 的 `infer_from_masterdata` 只返回
`condition_id / parameter_id / shot_index / injection_index`，**没有 seq_idx**

**改动**：加一行 `result['seq_idx'] = parameter.seq_idx`（processCondition.enable 进入下一个 infer 必需）

**改动范围**：1 行 Python，1 行测试更新（如果存在）

## 五、关键文件路径

- [frontend/src/api/index.ts](file:///f:/items/moldingx/molding-optima/frontend/src/api/index.ts) — API 函数
- [frontend/src/views/process/optimization/pages/OptimizationCreate.vue](file:///f:/items/moldingx/molding-optima/frontend/src/views/process/optimization/pages/OptimizationCreate.vue) — getOptimizedProcess 实现
- [backend/process/services/initialization_service.py](file:///f:/items/moldingx/molding-optima/backend/process/services/initialization_service.py) — 补 seq_idx 返回（前置依赖）