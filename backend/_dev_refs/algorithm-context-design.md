# 算法上下文双重来源设计

> 本文档记录工艺参数推理算法输入上下文的组成方式与设计原则。

## 1. 背景

工艺参数推理算法（如 `ProcessInitializer.derive`）需要扁平的输入字段，例如：
- `product_weight`、`gate_type`、`ave_thickness`
- `screw_diameter`、`max_injection_pressure`
- `abbreviation`、`recommend_melt_temperature`

但实际数据存储是**嵌套结构**：
- Mold → GatingSystem → Cavity → Gate（产品/浇口/壁厚）
- InjectionMoldingMachine → InjectionUnit（机器参数）
- Polymer（材料参数）

这中间存在**结构差异**，需要一层"上下文提取"逻辑来弥合。

同时，业务上经常出现**数据库数据不准确**的场景（如产品重量实测与建档值有偏差），需要允许用户在界面上主动调整。

因此，算法输入上下文具有**双重来源**。

## 2. 核心思想：上下文的双重来源

```
                  算法输入上下文（扁平字段）
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
        后端从嵌套结构提取        前端用户主动覆盖
        （数据库 → 算法字段）    （UI 编辑 → 算法字段）
                │                       │
                ▼                       ▼
        _build_product_info()     overrides
        _build_machine_info()     (前端请求体)
        _build_polymer_info()     产品/工艺字段
                │                       │
                └───────────┬───────────┘
                            ▼
                    最终上下文（扁平字段）
                            │
                            ▼
                  ProcessInitializer.derive()
                            │
                            ▼
                      工艺参数（推理结果）
```

**两条路径共同构成完整上下文**：
- 后端路径：嵌套结构 → 扁平字段（默认值）
- 前端路径：用户编辑 → 扁平字段（覆盖值）

## 3. 字段分层规则

不同字段的可调整性不同，需要明确边界：

| 字段分类 | 字段示例 | 来源 | 是否可覆盖 | 说明 |
|----------|----------|------|------------|------|
| **设备属性** | `screw_diameter`、`max_injection_pressure`、`max_injection_velocity` | 数据库 | ❌ 不可覆盖 | 物理设备能力，不可随意更改 |
| **材料属性** | `recommend_melt_temperature`、`melt_density` | 数据库 | ❌ 不可覆盖 | 材料固有特性 |
| **产品属性** | `product_weight`、`runner_weight` | 数据库 | ✅ 可覆盖 | 用户实测可能有偏差 |
| **工艺属性** | `gate_type`、`ave_thickness`、`max_thickness`、`max_length` | 数据库 | ✅ 可覆盖 | 用户可能根据实际调整 |
| **浇口几何** | `gate_radius`、`gate_length`、`gate_width` | 数据库 | ✅ 可覆盖 | 同上 |

### 字段分层原则

**设备/材料属性 → 必须从库读取**
- 原因：物理极限，由设备/材料本身决定
- 行为：后端从数据库提取，UI 不提供编辑入口

**产品/工艺/浇口属性 → 允许用户覆盖**
- 原因：经验值或测量值，可能与实际不符
- 行为：UI 提供编辑入口，前端通过 overrides 字段传递给后端

## 4. 数据流详解

### 4.1 后端提取路径

```python
# process/services/initialization_service.py

def _build_product_info(mold) -> Dict[str, Any]:
    """从 Mold（嵌套结构）提取 product_info（扁平字段）"""
    
    product_info = {}
    
    # 1. 模具级字段
    for attr in ['shot_count']:
        value = getattr(mold, attr, None)
        if value is not None:
            product_info[attr] = value
    
    # 2. 浇注系统 → 产品重量、流道重量
    gating = mold.gating_systems.first()
    if gating:
        product_info['product_weight'] = gating.total_product_weight
        product_info['runner_weight'] = gating.runner_weight or gating.estimated_runner_weight
    
    # 3. 型腔 → 壁厚、流长
    cavity = gating.cavities.first()
    if cavity:
        product_info['ave_thickness'] = cavity.ave_wall_thickness
        product_info['max_thickness'] = cavity.max_wall_thickness
        product_info['max_length'] = cavity.max_flow_length
    
    # 4. 浇口 → 浇口类型、尺寸
    gate = cavity.gates.first()
    if gate:
        product_info['gate_type'] = gate.gate_type
        product_info['gate_length'] = gate.length
        product_info['gate_width'] = gate.width
        if gate.outer_diameter:
            product_info['gate_radius'] = gate.outer_diameter / 2
    
    return product_info
```

### 4.2 前端覆盖路径

```json
// 前端请求体（POST /api/processes/initialization/）
{
    "condition_id": 123,           // 或 mold_id + polymer_id + machine_id（Mode B）
    
    // 用户覆盖字段（可选）
    "overrides": {
        "product_weight": 85.0,    // 覆盖后端默认值 80.0
        "gate_type": "侧浇口",      // 覆盖后端默认值 "点浇口"
        "ave_thickness": 2.8       // 覆盖后端默认值 2.5
    }
}
```

### 4.3 合并路径

```python
def prepare_context(condition_id=None, mold_id=None, ..., overrides=None):
    """组装最终上下文"""
    
    # 1. 从数据库提取（后端默认值）
    context = query_from_db(condition_id, mold_id, ...)
    
    # 2. 应用前端覆盖（用户编辑值）
    if overrides:
        context.update(overrides)
    
    # 3. 返回最终上下文
    return context
```

## 5. 与工艺条件 Condition 的关系

### 5.1 Condition 的本质

工艺条件 Condition 描述的是**一射的完整上下文**，包括：

```
condition = {
    shot_index,         // 第几射
    injection_index,    // 注塑机的哪个注射单元
    
    mold,               // 哪个模具
    injection_machine,  // 哪个注塑机
    polymer,            // 哪种材料
    
    // 嵌套关联（基于 molding-expert 工业级模型）
    gating_system,      // 模具的哪个浇注系统
    cavity,             // 该系统的哪个型腔
    gate,               // 该型腔的哪个浇口
    product             // 该型腔的哪个产品
}
```

### 5.2 Condition 与上下文的转换

```
condition（嵌套）
    ↓ _build_context_from_condition()
context（扁平，算法可消费）
```

Condition 是**业务层概念**，Context 是**算法层概念**，二者通过提取层相互转换。

### 5.3 用户的双角色

用户在工艺准备流程中扮演两个角色：

| 角色 | 行为 | 对应数据 |
|------|------|----------|
| **浏览者** | 查看数据库提取的字段值 | context 默认值 |
| **编辑者** | 修改某些字段值（如实测产品重量） | overrides |

这两种行为都构成算法的输入上下文。

## 6. 工业级模型 vs Demo 级模型

### 6.1 原 molding-optima 模型（Demo 级）

```python
# 简化假设：单射注塑机、单浇口、单一产品
class Mold:
    product_weight: float          # 直接字段
    gate_type: str                 # 直接字段
    ave_thickness: float           # 直接字段
```

**问题**：过于理想化，无法处理：
- 多射注塑机（多注射单元）
- 多浇注系统
- 多型腔 + 多产品
- 多浇口

### 6.2 molding-expert 模型（工业级）

```python
# 嵌套结构，反映实际工业场景
class Mold:
    gating_systems: GatingSystem[]   # 多浇注系统
    
class GatingSystem:
    cavities: Cavity[]                # 多型腔
    total_product_weight: float       # 产品重量（系统级）
    
class Cavity:
    gates: Gate[]                     # 多浇口
    ave_wall_thickness: float         # 壁厚（型腔级）
    
class Gate:
    gate_type: str                    # 浇口类型
    length: float                     # 浇口尺寸
```

**优势**：
- 准确描述工业实际
- 支持多射、多浇注系统、多型腔、多产品
- 每个字段归属于合适的层级

### 6.3 提取层的重要性

正是因为实际数据是嵌套的，算法需要扁平输入，所以**提取层是不可或缺的**：

```
工业级嵌套模型 ← 提取层 → 算法级扁平字段
```

提取层封装了"嵌套到扁平"的转换逻辑，是业务层与算法层的桥梁。

## 7. Schema 设计原则

基于双重来源设计，Schema 字段应满足：

```python
class ProcessInitializationSchema(BaseSchema):
    # ====== Condition/Masterdata 标识 ======
    condition_id: Optional[int]      # Mode A
    mold_id: Optional[int]            # Mode B
    polymer_id: Optional[int]         # Mode B
    injection_machine_id: Optional[int]  # Mode B
    
    # ====== 用户覆盖字段 ======
    # 仅包含产品/工艺相关字段（可调整）
    # 不包含设备/材料属性（不可调整）
    product_weight: Optional[float]
    runner_weight: Optional[float]
    gate_type: Optional[str]
    ave_thickness: Optional[float]
    max_thickness: Optional[float]
    max_length: Optional[float]
    gate_radius: Optional[float]
    gate_length: Optional[float]
    gate_width: Optional[float]
    
    # ====== 段数与模式 ======
    inj_stg: int
    hold_stg: int
    met_stg: int
    ...
```

## 8. 实施要点

| 实施点 | 说明 |
|--------|------|
| **Schema 字段** | 只允许覆盖产品/工艺相关字段，不暴露设备/材料属性 |
| **后端提取** | `_build_*_info()` 函数从嵌套结构提取扁平字段 |
| **前端覆盖** | UI 仅对产品/工艺字段提供编辑入口 |
| **合并逻辑** | 后端默认值 → 应用前端 overrides → 最终上下文 |
| **算法解耦** | 算法只接收扁平字段，不感知嵌套结构 |

## 9. 相关文件

| 文件 | 说明 |
|------|------|
| `process/services/initialization_service.py` | 提取层（`_build_*_info`）和合并逻辑 |
| `process/schemas.py` | `ProcessInitializationSchema` 定义覆盖字段边界 |
| `process/views/processes.py` | `ProcessInitializationView` 传递 overrides |
| `process/engines/expert/initializer.py` | 算法层（`ProcessInitializer`）接收扁平字段 |

---

*文档生成时间：2026-07-02*