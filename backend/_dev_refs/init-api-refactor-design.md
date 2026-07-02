# 工艺初始化接口优化方案

> 本文档记录工艺初始化接口的重构决策。

## 1. 现状问题

重构前存在两个接口，职责有重叠且命名不够清晰：

| 路径 | 问题 |
|------|------|
| `/processes/initialization/` | 早期设计，承担 condition_id + 字典快照两种模式 |
| `/processes/initialization/from-ids/` | 第三方用户接口，与主接口功能部分重叠 |

## 2. 最终方案

### 2.1 接口结构（统一）

```
/processes/initialization/         → 统一接口（落库）
    ├─ Mode A：传 condition_id → 从 condition 提取 mold/machine/polymer → 推理 → 创建新 Parameter
    └─ Mode B：传 mold_id + polymer_id + machine_id → 从 masterdata 查询 → 推理 → 创建 Condition + Parameter

/processes/initialization/infer/   → 纯推理接口（不查库不落库）
    └─ 前端传完整 machine_info/polymer_info/product_info
```

### 2.2 接口对比

| 接口 | 数据来源 | 是否落库 | 适用场景 |
|------|----------|----------|----------|
| `/initialization/` Mode A | 已有 condition | ✅ 落库（创建新 Parameter） | 已有工艺，推理生成新参数版本 |
| `/initialization/` Mode B | masterdata ID | ✅ 落库（创建 Condition + Parameter） | 新建工艺 |
| `/initialization/infer/` | 前端传完整数据 | ❌ 不落库 | 第三方集成 / 纯算法试算 |

### 2.3 分层架构

```
┌─────────────────────────────────────────────────────────────┐
│  接口层                                                      │
│  ├── /initialization/     → 决定落库模式，调用 service       │
│  └── /initialization/infer/ → 调用 service，不落库           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Service 层                                                  │
│  - infer_initial_params(condition_id)        Mode A         │
│  - infer_initial_params(machine_info, ...)   infer          │
│  - create_and_infer_initial_params(...)       Mode B         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  推理引擎层（InitEngine）                                      │
│  ProcessInitializer.derive(product_info)                    │
│  → 纯计算，不查库，输入完整数据，返回推理参数                   │
└─────────────────────────────────────────────────────────────┘
```

**核心原则**：推理引擎不查库，所有数据由调用方提供。

### 2.4 统一 Schema

`ProcessInitializationSchema` 统一支持两种模式：

```json
{
    // Mode A 字段
    "condition_id": 123,
    
    // Mode B 字段（可选）
    "mold_id": 1,
    "polymer_id": 2,
    "injection_machine_id": 3,
    "shot_index": 1,
    "injection_index": 1,
    "status": "draft",
    "origin_type": "ai_recommendation",
    "condition_code": null,
    
    // 用户覆盖字段（两种模式通用）
    "product_weight": 80,
    "gate_type": "点浇口",
    "ave_thickness": 2.5,
    
    // 段数与模式（两种模式通用）
    "inj_stg": 1,
    "hold_stg": 1,
    "met_stg": 1,
    "barrel_temperature_stage": 5,
    "vps_mode": 0,
    "pre_met_decomp_mode": 0,
    "pst_met_decomp_mode": 0
}
```

**判断逻辑**：
```
if condition_id:
    # Mode A：从数据库查询 mold/machine/polymer，调用 infer_initial_params
elif mold_id and polymer_id and injection_machine_id:
    # Mode B：调用 create_and_infer_initial_params
else:
    # 报错：缺少必要参数
```

### 2.5 数据覆盖规则

| 字段类型 | 处理方式 | 示例 |
|----------|----------|------|
| **设备/材料属性** | 必须从库读取 | machine.max_pressure, polymer.melt_temp |
| **产品/工艺相关** | 允许用户覆盖 | product_weight, gate_type, ave_thickness |

```python
def prepare_context(condition_id=None, mold_id=None, ..., overrides=None):
    # 1. 查库获取基础数据
    context = query_from_db(condition_id, mold_id, ...)
    
    # 2. 用传参覆盖（前端用户修正的值优先）
    if overrides:
        context.update(overrides)
    
    return context
```

## 3. 实施记录

| 步骤 | 内容 | 状态 |
|------|------|------|
| 1 | 合并 `ProcessInitializationSchema` 与 `InitializationFromIdsSchema` | ✅ 完成 |
| 2 | 重构 `ProcessInitializationView`，同时支持 Mode A 与 Mode B | ✅ 完成 |
| 3 | 新增 `/initialization/infer/` 接口 | ✅ 完成 |
| 4 | 删除 `ProcessInitializationFromIdsView` 和 `InitializationFromIdsSchema` | ✅ 完成 |
| 5 | 更新 URL 路由，删除 `/initialization/from-ids/` | ✅ 完成 |
| 6 | 测试验证 | 待补充 |

## 4. 相关文件变更

| 文件 | 变更 |
|------|------|
| `process/schemas.py` | 合并 Schema，删除 `InitializationFromIdsSchema` |
| `process/views/processes.py` | 合并 View，删除 `ProcessInitializationFromIdsView` |
| `process/urls.py` | 删除 `from-ids` 路由 |

---

*文档生成时间：2026-07-02*
*最后更新：2026-07-02*