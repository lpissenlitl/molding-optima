# 工艺调整版本管理方案

## 1. 背景与目标

### 1.1 业务场景

在注塑工艺调优过程中，工程师会：
1. 初始录入一组工艺参数
2. 试模后发现缺陷，进行调参
3. 可能回撤到之前的版本，重新优化
4. 最终得到合格工艺

这个过程产生的数据是**树结构**而非线性序列：

```
ProcessCondition (工艺)
└── v1 (初始参数)
    ├── v1.1 (调参A)
    │   └── v1.1.1 (继续优化)
    └── v1.2 (回撤，改方向)
        └── v1.2.1 (合格!)
```

### 1.2 设计目标

- 将工艺调整过程管理**独立为单独接口模块**，保持基础工艺参数接口简洁
- 支持树结构的版本管理（创建、回撤、查看历史）
- 复用现有模型字段（`parent_param` 自关联、`seq_idx` 序列号）

## 2. 数据模型

### 2.1 现有字段支持

`ProcessParameter` 模型已有字段支持树结构：

```python
parent_param = models.ForeignKey(
    "self",
    on_delete=models.SET_NULL,
    null=True, blank=True,
    related_name="children",
)

seq_idx = models.IntegerField(
    null=True, blank=True,
    verbose_name="序列序号",
    default=0,
)
```

### 2.2 可选扩展字段

为支持更丰富的调整记录，建议在 `ProcessParameter` 添加：

```python
adjustment_note = models.CharField(
    null=True, blank=True,
    max_length=500,
    verbose_name="调整说明",
)

PARAMETER_STATUS_CHOICES = [
    ('active', '当前版本'),
    ('archived', '已归档'),
    ('baseline', '基准版本'),
]
param_status = models.CharField(
    max_length=20,
    choices=PARAMETER_STATUS_CHOICES,
    default='active',
    verbose_name="参数状态",
)
```

## 3. 接口设计

### 3.1 URL 结构

```
/api/processes/adjustment/
    ├── POST   /                          # 创建新版本（调参）
    ├── GET    /<condition_id>/tree/      # 获取版本树
    ├── GET    /<param_id>/lineage/       # 获取版本链路（从根到当前）
    └── POST   /<param_id>/revert/        # 回撤到指定版本
```

### 3.2 接口详细设计

#### 3.2.1 创建新版本（调参）

**URL**: `POST /api/processes/adjustment/`

**请求体**:
```json
{
    "parent_param_id": 123,           // 必填，基于哪个版本调参
    "adjustment_note": "调整注射压力解决短射问题",  // 可选
    "param_source": "manual_adjusted",
    "params": {
        "inj_pres_1": 70,
        "inj_spd_1": 45,
        ...
    }
}
```

**响应**:
```json
{
    "code": 0,
    "data": {
        "id": 456,
        "parent_param_id": 123,
        "seq_idx": 2,
        "seq_path": "1.2",
        "adjustment_note": "调整注射压力解决短射问题",
        "param_source": "manual_adjusted",
        "created_at": "2026-06-29T10:30:00Z",
        "params": { ... }
    }
}
```

**业务逻辑**:
1. 根据 `parent_param_id` 获取父版本
2. 复制父版本参数，填入新参数值
3. 设置 `parent_param` 指向父版本
4. 计算 `seq_idx`（同一父节点下递增）和 `seq_path`（如 "1.2"）
5. 标记父版本为非当前（`param_status='archived'`）

#### 3.2.2 获取版本树

**URL**: `GET /api/processes/adjustment/<condition_id>/tree/`

**响应**:
```json
{
    "code": 0,
    "data": {
        "condition_id": 1,
        "tree": {
            "id": 100,
            "seq_path": "1",
            "param_source": "manual",
            "param_status": "archived",
            "adjustment_note": null,
            "created_at": "2026-06-28T09:00:00Z",
            "params": { ... },
            "children": [
                {
                    "id": 101,
                    "seq_path": "1.1",
                    "param_source": "manual_adjusted",
                    "param_status": "archived",
                    "adjustment_note": "第一次调参",
                    "children": [
                        {
                            "id": 103,
                            "seq_path": "1.1.1",
                            "param_status": "active",
                            "children": []
                        }
                    ]
                },
                {
                    "id": 102,
                    "seq_path": "1.2",
                    "param_status": "archived",
                    "children": [
                        {
                            "id": 104,
                            "seq_path": "1.2.1",
                            "param_status": "active",
                            "children": []
                        }
                    ]
                }
            ]
        }
    }
}
```

#### 3.2.3 获取版本链路

**URL**: `GET /api/processes/adjustment/<param_id>/lineage/`

**响应**:
```json
{
    "code": 0,
    "data": {
        "lineage": [
            { "id": 100, "seq_path": "1", "created_at": "2026-06-28T09:00:00Z" },
            { "id": 102, "seq_path": "1.2", "created_at": "2026-06-28T14:00:00Z" },
            { "id": 104, "seq_path": "1.2.1", "created_at": "2026-06-29T10:00:00Z" }
        ],
        "depth": 3
    }
}
```

#### 3.2.4 回撤到指定版本

**URL**: `POST /api/processes/adjustment/<param_id>/revert/`

**请求体**:
```json
{
    "note": "回撤到第一次调参结果"
}
```

**响应**:
```json
{
    "code": 0,
    "data": {
        "id": 105,
        "parent_param_id": 104,
        "seq_path": "1.2.1.1",
        "note": "回撤到第一次调参结果",
        "params": { ... }  // 复制自 param_id=101 的参数
    }
}
```

**业务逻辑**:
1. 获取目标版本参数
2. 基于当前版本（最新 active）创建新版本
3. 复制目标版本参数值
4. 记录回撤原因

## 4. 服务层设计

### 4.1 文件结构

```
backend/process/
├── services/
│   ├── process_service.py          # 现有基础服务
│   └── process_adjustment_service.py  # 新增：调整版本管理服务
```

### 4.2 服务函数

```python
# process_adjustment_service.py

def create_adjustment_version(condition_id, parent_param_id, params, adjustment_note=None):
    """创建调整版本"""
    pass

def get_version_tree(condition_id):
    """获取版本树"""
    pass

def get_version_lineage(param_id):
    """获取版本链路"""
    pass

def revert_to_version(param_id, note=None):
    """回撤到指定版本"""
    pass

def _build_tree(parameters):
    """构建树结构"""
    pass

def _calculate_seq_path(parent_path, sibling_count):
    """计算 seq_path"""
    pass
```

## 5. 前端 API 设计

### 5.1 API 封装

```typescript
// frontend/src/api/processAdjustment.ts

import { request, BaseRequest } from './index'

const processAdjustment = new BaseRequest('/api/processes/adjustment')

export const createAdjustmentVersion = (data: {
    parent_param_id: number
    adjustment_note?: string
    param_source?: string
    params: Record<string, any>
}) => request({
    url: processAdjustment.url('/'),
    method: 'post',
    data,
})

export const getVersionTree = (conditionId: number) => request({
    url: processAdjustment.url(`/${conditionId}/tree/`),
    method: 'get',
})

export const getVersionLineage = (paramId: number) => request({
    url: processAdjustment.url(`/${paramId}/lineage/`),
    method: 'get',
})

export const revertToVersion = (paramId: number, note?: string) => request({
    url: processAdjustment.url(`/${paramId}/revert/`),
    method: 'post',
    data: { note },
})
```

## 6. 实施计划

### 阶段一：基础功能（本次）
- [ ] 模型扩展（`adjustment_note`、`param_status`、`seq_path` 字段）
- [ ] 数据库迁移
- [ ] 服务层实现
- [ ] View 层实现
- [ ] URL 路由配置
- [ ] 前端 API 封装

### 阶段二：增强功能（可选）
- [ ] 版本对比（diff）
- [ ] 批量回撤
- [ ] 版本标签（标记"合格版本"等）

## 7. 待确认事项

1. **是否需要 `seq_path` 字段？** 如果需要精确显示版本路径如 "1.2.1"，需要新增字段；也可以前端动态计算
2. **`param_status` 状态管理** 是否需要数据库字段，还是仅通过 `is_deleted` 和时间判断？
3. **回撤行为** 回撤是创建新版本（推荐）还是直接修改 parent_param 指向？