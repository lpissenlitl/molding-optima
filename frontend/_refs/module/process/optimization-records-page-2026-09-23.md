# 优化记录列表页面 —— 2026-09-23

> 状态：实施完成
> 范围：`/process/optimization-records` 路由 + 完整 list 页面

## 一、需求

`router/index.ts:129-134` 已定义 `process-optimization-records` 路由，指向 `OptimizationList.vue`（之前是占位页面）。需要完成：

1. 列表展示所有 ProcessCondition（每条 = 一次优化过程）
2. 凸显"调机轮次"——优化视角的核心信息
3. 行操作：查看调机历史 / 启动新优化 / 删除

## 二、设计决策

### 2.1 复用现有 API（不新建）

| 备选方案 | 优劣 |
|---------|------|
| A. 新建 `/api/processes/optimization-records/` | 改动大，需要 service + view + schema + url 4 处 |
| B. 复用 `/api/processes/parameter/`（ProcessParameterList 用的 API） | **最小改动**（只加 1 个 annotation） |

**选 B**。理由：
- `ProcessParameterList` 已经 100% 覆盖 `OptimizationList` 的查询需求
- 后端 list 已经是基于 ProcessCondition（一次试模上下文），与"优化记录"语义重合
- 唯一缺的字段：`parameters_count`（调机轮次）

### 2.2 后端最小改动

[main_service.py:388-394](backend/process/services/main_service.py#L388-L394)：
```python
qs = ProcessCondition.objects.filter(
    **filter_kwargs
).select_related(
    "mold", "injection_machine", "polymer"
).prefetch_related(
    "process_parameters"
).annotate(
    # 调机轮次数（关联的 ProcessParameter 数量）
    parameters_count_anno=Count("process_parameters"),
)
```

[main_service.py:419-420](backend/process/services/main_service.py#L419-L420)：在 results 字典里加：
```python
"parameters_count": item.parameters_count_anno,
```

**合计 2 处改动，4 行新增**。其他视图（ProcessParameterList）自动也拿到这个字段（无害）。

### 2.3 前端实现

[OptimizationList.vue](frontend/src/views/process/optimization/pages/OptimizationList.vue)（436 行）：

**组件复用**：
- `<ProcessSearchForm>` —— 与 ProcessParameterList 共用，避免重复开发
- `<BaseTable>` —— 接管 el-table + 分页 + 列筛选 + 偏好持久化

**调机视角的列定义**（去掉"产品大类 / 设备品牌 / 设备编号 / 塑料牌号"——优化视角不需要这些细节）：
```
工艺编号 | 调机轮次 | 状态 | 起源 | 模具编号 | 模具名称 | 设备型号 | 塑料简称 | 创建时间 | 操作
```

**调机轮次列**（核心信息，高亮）：
```vue
<el-tag :type="row.parameters_count > 1 ? 'warning' : 'info'" effect="plain">
  <AppIcon icon="mdi:repeat-variant" />
  {{ row.parameters_count ?? 0 }} 轮
</el-tag>
```
- `> 1` 用 warning 黄色（多轮调机）
- `= 1` 用 info 灰色（仅初始工艺）

### 2.4 调机历史 dialog

行操作"调机历史"打开 dialog，调用 `/api/processes/optimization/<id>/history/`，用 `el-timeline` 展示每轮调机：

```vue
<el-timeline>
  <el-timeline-item
    v-for="(item, idx) in history_items"
    :type="idx === history_items.length - 1 ? 'primary' : 'success'"
    :timestamp="formatDate(item.created_at)"
  >
    <el-card>
      <!-- seq_idx / parameter_id / 关键工艺参数摘要 -->
    </el-card>
  </el-timeline-item>
</el-timeline>
```

**字段兼容**：后端 history 返回 `seq_idx`，前端用 `item.sequence_index ?? item.seq_idx ?? '-'` 兼容两种命名。

## 三、API 路径

| 用途 | URL | 方法 |
|------|-----|------|
| 列表 | `/api/processes/parameter/` | GET（复用） |
| 调机历史 | `/api/processes/optimization/<id>/history/` | GET |
| 批量删除 | `/api/processes/parameter/batch_delete/` | POST |

## 四、文件改动

| 文件 | 改动 |
|------|------|
| `backend/process/services/main_service.py` | +1 import (Count), +3 annotation, +1 results 字段 |
| `frontend/src/views/process/optimization/pages/OptimizationList.vue` | 占位 → 完整 list（436 行） |

## 五、边界场景

1. **空数据**：`<el-empty description="该工艺条件下暂无调机记录">` 提示
2. **history 接口异常**：fetch 错误 console.error + toast，loading 状态正确关闭
3. **history 字段命名兼容**：`sequence_index` 与 `seq_idx` 都支持（fallback 链）
4. **批量删除**：复用 `processParameterBatchDelete`，因为 ProcessCondition 是级联删除单位

## 六、TypeScript 验证

`vue-tsc --noEmit --project tsconfig.app.json` 对 `OptimizationList.vue` 零错误。