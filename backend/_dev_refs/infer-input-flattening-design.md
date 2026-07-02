# 工艺参数输入结构扁平化设计

> 本文档记录工艺参数推理接口输入结构的扁平化优化。

## 1. 问题诊断

历史的扁平化设计导致数据耦合问题：

```python
# 旧设计：product_info 字段含义模糊
class ProductInfoSchema(BaseSchema):
    product_weight: float      # ✅ 产品本身
    gate_type: str             # ✅ 产品/模具（来自 Gate）
    ave_thickness: float       # ✅ 产品/模具（来自 Cavity）
    
    inj_stg: Optional[int]     # ❌ 工艺设置，错误归属
    hold_stg: Optional[int]    # ❌ 工艺设置，错误归属
    # ❌ 缺少 gate_radius/length/width
```

**问题**：
- 字段按业务混合归类，未按信息归属拆分
- `inj_stg/hold_stg` 错误地放在 product_info
- 名字误导，让人误以为都是产品信息

## 2. 优化原则：按信息归属扁平化

**机器层面**（拆分）：
- `machine_info` - 机器本身（动力方式）
- `injection_unit` - 注射单元（螺杆、最大压力、喷嘴等）

**模具/产品层面**（拆分）：
- `mold_info` - 模具级（射数）
- `product_info` - 产品级（重量、壁厚、浇口等）

**工艺设置**（独立）：
- `process_set` - 段数与模式

**材料层面**：
- `polymer_info` - 材料信息

## 3. Schema 设计

```python
class MachineInfoSchema(BaseSchema):
    """注塑机本身信息"""
    power_method: Optional[str]   # 动力方式：液压机/电动机


class InjectionUnitSchema(BaseSchema):
    """注射单元参数"""
    screw_diameter: Optional[float]
    max_set_injection_pressure: Optional[float]
    max_set_injection_velocity: Optional[float]
    max_set_holding_pressure: Optional[float]
    max_set_holding_velocity: Optional[float]
    max_set_screw_rotation_speed: Optional[float]
    max_set_metering_pressure: Optional[float]
    nozzle_type: Optional[str]    # 喷嘴在注射单元上


class PolymerInfoSchema(BaseSchema):
    """材料信息"""
    abbreviation: Optional[str]
    recommend_melt_temperature: Optional[float]
    # ...
    melt_density: Optional[float]


class MoldInfoSchema(BaseSchema):
    """模具信息（模具级）"""
    shot_count: Optional[int]     # 模具射数


class ProductInfoSchema(BaseSchema):
    """产品信息（产品级，从 mold 的 cavity/gate 提取）"""
    # 产品本身特征
    product_weight: float
    runner_weight: Optional[float]
    # 产品尺寸（来自 Cavity）
    ave_thickness: float
    max_thickness: float
    max_length: Optional[float]
    # 浇口特征（来自 Gate）
    gate_type: str
    gate_radius: Optional[float]
    gate_length: Optional[float]
    gate_width: Optional[float]
    # 热流道 + 周期
    valve_num: Optional[int]
    inject_cycle_require: Optional[float]


class ProcessSetSchema(BaseSchema):
    """工艺设置（段数与模式）"""
    inj_stg: Optional[int]
    hold_stg: Optional[int]
    met_stg: Optional[int]
    barrel_temperature_stage: Optional[int]
    VP_switch_mode: Optional[str]
    vps_mode: Optional[int]
    pre_met_decomp_mode: Optional[int]
    pst_met_decomp_mode: Optional[int]
```

## 4. 完整请求示例（infer 接口）

```json
{
    "machine_info": {
        "power_method": "液压机"
    },
    "injection_unit": {
        "screw_diameter": 30.0,
        "max_set_injection_pressure": 180.0,
        "max_set_injection_velocity": 100.0,
        "max_set_holding_pressure": 80.0,
        "max_set_holding_velocity": 50.0,
        "max_set_screw_rotation_speed": 120.0,
        "max_set_metering_pressure": 5.0,
        "nozzle_type": "直通型"
    },
    "polymer_info": {
        "abbreviation": "ABS",
        "recommend_melt_temperature": 230.0,
        "recommend_shear_linear_speed": 25.0,
        "recommend_back_pressure": 0.5,
        "recommend_mold_temperature": 60.0,
        "melt_density": 1.05
    },
    "mold_info": {
        "shot_count": 1
    },
    "product_info": {
        "product_weight": 85.0,
        "runner_weight": 0,
        "ave_thickness": 2.5,
        "max_thickness": 3.5,
        "max_length": 150,
        "gate_type": "点浇口",
        "gate_radius": 1.5,
        "valve_num": 0,
        "inject_cycle_require": null
    },
    "process_set": {
        "inj_stg": 1,
        "hold_stg": 1,
        "met_stg": 1,
        "barrel_temperature_stage": 5,
        "VP_switch_mode": "位置"
    }
}
```

## 5. 数据来源追溯

| 字段 | 数据源 |
|------|--------|
| `machine_info.power_method` | InjectionMoldingMachine.drive_system |
| `injection_unit.*` | InjectionUnit.* （包括 nozzle_type）|
| `polymer_info.*` | Polymer.* |
| `mold_info.shot_count` | Mold.* |
| `product_info.product_weight` | GatingSystem.total_product_weight |
| `product_info.runner_weight` | GatingSystem.runner_weight |
| `product_info.ave_thickness` | Cavity.ave_wall_thickness |
| `product_info.gate_type` | Gate.gate_type |
| `process_set.*` | 前端用户配置 / 默认值 |

## 6. 优势

| 维度 | 说明 |
|------|------|
| **语义准确** | 每个字段归属正确层级 |
| **数据解耦** | 不同来源的数据独立 |
| **字段完整** | 补充了缺失的 gate_radius/length/width |
| **独立更新** | 工艺调整不需要重传机器参数 |
| **易于扩展** | 新增字段有明确归属 |
| **前端友好** | UI 可按模块组织数据录入 |

## 7. 实施要点

| 实施点 | 说明 |
|--------|------|
| **拆分 Schema** | 5 个独立 Schema：MachineInfo, InjectionUnit, PolymerInfo, MoldInfo, ProductInfo, ProcessSet |
| **View 层组装** | ProcessInitializationInferView 把拆分字段合并后调用 infer_initial_params |
| **初始化服务** | 保留现有 infer_initial_params 接口（接收合并后的 dict） |
| **后续演进** | 可让 ProcessInitializer 直接接收扁平化结构 |

## 8. 相关文件

| 文件 | 说明 |
|------|------|
| `process/schemas.py` | 5 个独立 Schema 定义 |
| `process/views/processes.py` | ProcessInitializationInferView 字段合并逻辑 |

---

*文档生成时间：2026-07-02*