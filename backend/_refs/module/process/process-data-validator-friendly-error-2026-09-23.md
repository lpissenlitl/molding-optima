# 参数校验友好提示 —— 2026-09-23

> 状态：实施中
> 范围：`/api/processes/initialization/from-masterdata/` 参数不完整时的友好提示
> 关联文档：
> - [process-initialization-design-summary-2026-09-22.md](file:///f:/items/moldingx/molding-optima/docs/process-initialization-design-summary-2026-09-22.md)
> - [process-get-initial-frontend-integration-2026-09-23.md](file:///f:/items/moldingx/molding-optima/docs/process-get-initial-frontend-integration-2026-09-23.md)

## 一、问题背景

### 现象

调 `POST /api/processes/initialization/from-masterdata/` 接口返回 500：

```
ERROR middlewares catched error ValueError in /api/processes/initialization/from-masterdata/
ValueError: 模具/产品信息缺少必要字段: gate_type
```

### 根因

`backend/process/engines/expert/data_validator.py` 的 `_validate_mold` 抛 `ValueError`：

```python
for field in self.REQUIRED_MOLD_FIELDS:
    if not mold_info.get(field):
        raise ValueError(f"模具/产品信息缺少必要字段: {field}")
```

- `ValueError` 不被中间件识别为业务异常
- 走 `else` 分支 → 500 "内部错误"
- 致命：只报第一个缺失字段，用户修一个再试发现还有一个缺失，循环往复

### 既有错误码

`backend/process/exceptions.py:62` 已有：

```python
ERROR_PROCESS_INSUFFICIENT_FIELDS = BizErrorCode.create(MOD_PROCESS, 36, "工艺参数输入字段不足")
```

但 validator 没有用它。

## 二、修复策略

### Backend 改动（核心）

`data_validator.py`：
1. 改 `raise ValueError` 为 `raise BizException(ERROR_PROCESS_INSUFFICIENT_FIELDS, ...)`
2. 改为先收集所有缺失字段，最后一次性抛（让用户一次看全）
3. 在 message 中列出所有缺失字段名（逗号分隔）

### Backend 改动（小补丁）

`extensions/exceptions.py` 已经有 `BizException` 类，无需新增。

### Frontend 改动（去重）

`OptimizationCreate.vue getInitialProcess`：
- request.ts 拦截器已经 `ElMessage.warning` 了 `data.msg`
- 函数 catch 又 `ElMessage.error(err.message)` → 重复 toast
- 去掉 catch 的 toast，只留兜底日志

## 三、修复后的用户流程

```
用户点击 [获取初始工艺]
  ↓
前端：5 项必填校验（mold/machine/polymer/shot_index/injection_index）
  ↓ 通过
后端：从 mold 拿 gating_systems → 构造 mold_info
  ↓
后端：data_validator._validate_mold
  ↓ mold 缺 gate_type + product_weight
后端：抛 BizException(ERROR_PROCESS_INSUFFICIENT_FIELDS,
                  "工艺参数输入字段不足 - 模具/产品信息缺少字段: gate_type, product_weight")
  ↓
中间件：catch BizException → 400 + { status, msg, ... }
  ↓
前端：request.ts 拦截器 → ElMessage.warning 显示 msg
  ↓
用户看到："工艺参数输入字段不足 - 模具/产品信息缺少字段: gate_type, product_weight"
  ↓
用户去 masterdata 维护模具（补字段）
```

## 四、关键文件路径

- [backend/process/engines/expert/data_validator.py](file:///f:/items/moldingx/molding-optima/backend/process/engines/expert/data_validator.py) — 改 ValueError → BizException
- [backend/process/exceptions.py](file:///f:/items/moldingx/molding-optima/backend/process/exceptions.py) — 已有 ERROR_PROCESS_INSUFFICIENT_FIELDS
- [frontend/src/views/process/optimization/pages/OptimizationCreate.vue](file:///f:/items/moldingx/molding-optima/frontend/src/views/process/optimization/pages/OptimizationCreate.vue) — 去掉 catch 重复 toast