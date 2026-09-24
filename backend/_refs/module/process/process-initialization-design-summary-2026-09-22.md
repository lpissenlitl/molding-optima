# 工艺参数初始化接口重构总结

> 文档作者：Qoder AI
> 编写时间：2026-09-22
> 项目：molding-optima
> 范围：`/api/processes/initialization/*` 三个接口的重构

## 一、背景

molding-expert 项目原本已经实现了工艺参数初始化的两个接口，但搬到 molding-optima 后存在两个核心问题：

1. **业务语义重叠**：旧的 `from-masterdata/` 和 `from-condition/` 本质相同（都是"创建初始工艺"），前端调用入口模糊
2. **架构不清晰**：`process_context` 字段被同时用于"前端覆盖层"和"快照"，职责混乱

molding-optima 重构的核心目标：

- **明确 3 种初始化语义**（算法推荐 / 历史复制 / 纯推理）
- **拆分接口职责**，每种场景一个独立 URL
- **`process_context` 字段语义单一化**——只作为"后端调用入参快照"

## 二、最终架构

| URL | 算法 | 查库 | 落库 | 业务语义 | origin_type | param_source |
|---|---|---|---|---|---|---|
| `/initialization/from-source-condition/` | ❌ | ✅ | ✅ | 从源 condition 复制参数 | `legacy_import` | `template_copy` |
| `/initialization/from-masterdata/` | ✅ | ✅ | ✅ | 算法生成初始工艺 | `ai_recommendation` | `algorithm_init` |
| `/initialization/infer/` | ✅ | ❌ | ❌ | 纯推理试算 | — | — |

### 1. Mode A: 纯推理 (`/infer/`)

**使用场景**：前端在还没选定 masterdata ID 前，先用已知数据试算参数

**特征**：
- 前端直接传 4 维 dict（`mold_info` / `machine_info` / `polymer_info` / `process_set`）
- service **不查 DB**（因为 DB 里没数据）
- service **不落库**（没有 condition_id 可挂）
- 返回的是推理结果 dict，不含 `condition_id` / `parameter_id`

**核心实现**：`initialization_service.infer_from_dict(...)`

### 2. Mode B: 算法生成 + 落库 (`/from-masterdata/`)

**使用场景**：用户选定"模-料-机"后，系统自动生成初始工艺参数

**4 步逻辑**：
```
Step 1: 入口适配 —— 3 个 masterdata ID
Step 2: 数据前处理 —— ORM + process_context → 4 维 dict
Step 3: 推理算法 —— 内部调用 infer_initial_params
Step 4: 输出后处理 —— 落库（创建 Condition + ProcessParameter）
```

**特征**：
- 前端只传 3 个 ID + 可选 `process_set` / `condition_no`
- 后端自动检索 masterdata 构建快照
- 自动创建 `Condition(status=draft, origin_type=ai_recommendation)` + `ProcessParameter(param_source=algorithm_init)`
- **`process_context` 由后端自动写入**——记录本次调用传入的参数快照（audit 用）

**核心实现**：`initialization_service.infer_from_masterdata(...)`

### 3. Mode C: 历史复制 + 落库 (`/from-source-condition/`)

**使用场景**：工艺记录中已有"合格工艺"，复用作为新工艺的起点

**特征**：
- 前端只传 `source_condition_id` + 可选 `process_set`
- 后端会**重新检索当前 masterdata**（不直接复用源 snapshot，保证数据不过时）
- 读源 condition 的最新 ProcessParameter（`is_deleted=False` 按 id 倒序取首条）
- 自动创建 `Condition(origin_type=legacy_import)` + 拷贝参数 `ProcessParameter(param_source=template_copy)`
- **`process_context` 由后端自动写入**——记录调用入参（含 source_condition_id / source_parameter_id）

**关键设计决策**：必须重新检索 masterdata
- 源 condition 创建时的快照可能已过时
- 模具可能改过尺寸、材料可能换批次、机器可能换规格
- 新 condition 应反映"当前"的 masterdata 状态

**核心实现**：`initialization_service.infer_from_source_condition(...)`

## 三、`process_context` 字段语义统一

### 重构前

`process_context` 被用作两层：
- **前端覆盖层**（前端传，可以修改快照）
- **推理输入**

这导致问题：
- 前端可以覆盖快照值 → 不知道推理时用的实际数据
- audit 难以追溯（前端传了什么 vs 实际用了什么）

### 重构后

`process_context` 只用作**后端调用入参快照**（后端自动写入）：

```json
{
    "interface": "from_masterdata",        // 或 "from_source_condition"
    "shot_index": 0,
    "injection_index": 0,
    "process_set": {...},
    // history 接口还会包含：
    "source_condition_id": 50,
    "source_parameter_id": 88
}
```

**`process_context_snapshot`** 仍然存在——但只用于记录推理输入的快照（machine_info / polymer_info / mold_info / process_set），与 `process_context`（调用入参快照）严格区分。

## 四、关键设计决策

### 决策 1：分 URL 而非统一入口

**理由**（基于讨论后取舍）：
- ✅ 入参差异大（Mode B 需要 3 个 masterdata ID + 索引；Mode C 只需要 source_condition_id）
- ✅ 业务场景不同（新建 vs 复用）
- ✅ 错误处理不同（Mode B 关注 masterdata 缺失、规则匹配失败；Mode C 关注源 condition/parameter 不存在）
- ✅ 可读性更好（前端调用代码更易读）
- ⚠️ 抽象层级降低——但具体场景里反而更清晰

**这是合理的工程权衡**，符合 DSL 思维而非纯接口思维。

### 决策 2：参数拷贝走白名单

**理由**：
- 不依赖 ORM 反射（避免模型变更影响拷贝逻辑）
- 字段语义清晰（白名单即"业务上允许复制的字段"）
- 显式胜过隐式

**实现**：`initialization_service._COPYABLE_PARAM_FIELDS` 显式列出约 50 个可拷贝字段。

### 决策 3：复用快照路径

`_build_mold_snapshot` / `_build_machine_snapshot` / `_build_polymer_snapshot` 等函数被 Mode B 和 Mode C 共享：
- Mode B：从 3 个 masterdata ID 直接构建
- Mode C：从源 condition 拿 ID，重新查 DB 后构建

这是"快照路径复用"——避免重复实现。

### 决策 4：错误码复用

| 错误场景 | 错误码 |
|---|---|
| 源 condition 不存在 | `ERROR_PROCESS_CONDITION_NOT_FOUND` |
| 源 condition 没有 parameter | `ERROR_PROCESS_PARAMETER_NOT_FOUND` (107032) |

**未新增错误码**——现有错误码已足够。

## 五、文件变更清单

| 文件 | 变更类型 |
|---|---|
| `backend/process/services/initialization_service.py` | 大改：删 3 个旧函数 + 1 个旧方法；新增 1 个新方法 + 1 个辅助函数 + 字段列表；改 1 个方法（自动写 process_context） |
| `backend/process/schemas/initialization.py` | 改：删 1 个旧 schema；新增 1 个新 schema；更新 docstring |
| `backend/process/schemas/__init__.py` | 改：更新 import 导出 |
| `backend/process/views/processes.py` | 改：删 1 个旧视图；新增 1 个新视图；更新 import |
| `backend/process/urls.py` | 改：替换 import；替换路由；更新 docstring |

## 六、bug 修复汇总

### 1. `ERROR_FOLDER_NAME_NOT_ALLOWED` 缺失

**症状**：
```
ImportError: cannot import name 'ERROR_FOLDER_NAME_NOT_ALLOWED' from 'extensions.exceptions'
```

**原因**：`filecenter/utils.py` 引用了 3 处，但该错误码在 extensions 通用码中已被删除/重命名。

**修复**：新建 `filecenter/exceptions.py`，定义模块级错误码：
```
MOD_FILECENTER = "09"
├── 109001  ERROR_FOLDER_NAME_NOT_ALLOWED   文件夹名非法
├── 109002  ERROR_FILE_PATH_INVALID         文件路径非法
├── 109003  ERROR_TENANT_SLUG_INVALID       租户标识非法
├── 109004  ERROR_FILE_MD5_INVALID          文件 MD5 非法
├── 109005  ERROR_FILE_EXT_INVALID          文件扩展名非法
└── 109006  ERROR_FILE_TYPE_NOT_SUPPORTED   文件用途类型不支持
```

### 2. `ERROR_ACCESS_LIMIT` 缺失

**症状**：
```
ImportError: cannot import name 'ERROR_ACCESS_LIMIT' from 'extensions.exceptions'
```

**原因**：`process/services/rule_service.py` 6 处引用，但 extensions 通用码中只有 `ERROR_ACCESS_DENIED`（已被重命名）。

**修复**：在 `extensions/exceptions.py` 加别名：
```python
ERROR_ACCESS_LIMIT = ERROR_ACCESS_DENIED  # 兼容旧名
```

## 七、当前进展 & 待办

### ✅ 已完成
- 3 个初始化接口全部上线（Mode A / B / C）
- `process_context` 字段语义统一
- 2 个 import bug 修复
- 所有改动通过 AST 语法验证

### ⏳ 下一步
进入**优化接口设计**：
- 工艺参数调机树语义（`parent_param_id` + `parent_seq_idx`）
- 调机迭代 vs 步骤流程的边界
- 缺陷修正的 4 步逻辑具体实现

## 八、接口契约（参考）

### POST `/api/processes/initialization/from-source-condition/`

请求：
```json
{
    "source_condition_id": 50,    // 必填
    "process_set": {               // 可选
        "inj_stg": 4,
        "hold_stg": 3,
        "cool_stg": 1,
        "met_stg": 2,
        "vps_switch": true
    }
}
```

响应：
```json
{
    "condition_id": 88,
    "parameter_id": 92,
    "source_condition_id": 50,
    "source_parameter_id": 75,
    "shot_index": 0,
    "injection_index": 0,
    "param_source": "template_copy"
}
```

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

响应：
```json
{
    "condition_id": 88,
    "parameter_id": 92,
    "matched_rules": [...],            // 命中的规则列表（用于前端展示）
    "param_source": "algorithm_init"
}
```

### POST `/api/processes/initialization/infer/`

请求：
```json
{
    "mold_info": {...},        // 4 维 dict
    "machine_info": {...},
    "polymer_info": {...},
    "process_set": {...}       // 可选
}
```

响应：
```json
{
    "parameter": {...},        // 推理得到的参数（扁平 dict）
    "matched_rules": [...]
}
```

## 九、关键文件路径

- [backend/process/services/initialization_service.py](file:///f:/items/moldingx/molding-optima/backend/process/services/initialization_service.py) — service 层核心实现
- [backend/process/schemas/initialization.py](file:///f:/items/moldingx/molding-optima/backend/process/schemas/initialization.py) — Schema 定义
- [backend/process/views/processes.py](file:///f:/items/moldingx/molding-optima/backend/process/views/processes.py) — View 层
- [backend/process/urls.py](file:///f:/items/moldingx/molding-optima/backend/process/urls.py) — URL 路由
- [backend/filecenter/exceptions.py](file:///f:/items/moldingx/molding-optima/backend/filecenter/exceptions.py) — filecenter 模块错误码（新增）
- [backend/extensions/exceptions.py](file:///f:/items/moldingx/molding-optima/backend/extensions/exceptions.py) — 通用错误码（含 `ERROR_ACCESS_LIMIT` 别名）