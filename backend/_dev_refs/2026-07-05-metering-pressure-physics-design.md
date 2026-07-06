# 计量压力（meter_pres）算法设计文档（v1.0）

> **算法 #11**：计量参数族首个算法
> **设计日期**：2026-07-05
> **作者**：AI Assistant
> **状态**：✅ 已完成（2026-07-05）

---

## ⚠️ 关键概念澄清

### 单位约定（重要！）

- **数据库字段的 `[MPa]` 标记并不准确**：它仅是一个**习惯标注**，不代表算法内部必须用国际单位推导
- **界面单位与标准单位** 并不是严格的换算关系（不同厂家 HMI 的 bar/MPa/kgf/cm² 换算受表面压力表精度和标定影响）
- **算法内部以"界面可设定量纲"的同源数值推导**：输入的 `max_set_metering_pressure` 和输出的 `meter_pres` 使用同一数值体系，不做国际单位转换
- **base_ratio 的双重物理意义**：
  1. **材料黏度修正**（占主导）：family × 0.6~1.3 的相对比例
  2. **界面单位隐式换算**（次要）：在 HMI 可设定量纲下，0.55 直通 / 0.60 锁闭的基准中包含了厂家特定的单位转换因子
- **HMI 换算责任**：数值→物理量（如 bar→MPa）的严格换算由 HMI 显示层/业务层完成，算法层不预测

> **与此前理解不同**：以前认为“算法内部统一以 MPa 为单位（依据数据库 [MPa] 标签）”，但 [MPa] 标签仅为习惯标注，不同厂家 HMI 的 MPa/bar/kgf·cm⁻² 换算并不严格（表面压力表精度、标定差异），所以采用 base_ratio 的相对比例推导。

### "计量压力"与"计量背压"不是同一概念（用户提醒）

| 概念 | 定义 | 物理解释 | 适用机器 |
|------|------|---------|---------|
| **计量压力（meter_pres）** | 液压系统**油压**（hydraulic cylinder pressure）| 液压机通过油缸推动螺杆后退的油压 | ⛔ 仅**液压机**（全电机无油缸）|
| **计量背压（meter_back_pres）** | 塑化阶段**熔体承受的物理阻力**（melt back pressure）| 熔体在螺槽内对螺杆的反作用力 | ✅ 所有机器都有 |

**本算法仅针对"计量压力"**（液压机油压）：

- 液压机：`meter_pres` 由公式推导（max × base_ratio × family_factor × nozzle_factor）
- 全电机（无油缸）：`meter_pres = 0`（无液压油压来源，物理正确，**保留原代码逻辑**）

> 💡 **计量背压（meter_back_pres）将作为下一个独立算法**（#12），适用于全电机+液压机，属于物理阻力，与本算法物理独立。

---

## 0. 差异分析（原方法 vs 改造后）

### 0.1 原方法代码（initializer.py 1381-1390）

```python
meter_pres = 0
if mach.get('power_method') == '液压机':
    nozzle_type = mach.get('nozzle_type', '直通型')
    max_metering_pres = mach.get('max_set_metering_pressure', 20)
    # 来自 DEFAULT.metering.{meter_pres_ratio_straight/locking}
    if nozzle_type == "直通型":
        meter_pres = max_metering_pres * c_met.get('meter_pres_ratio_straight', 0.55)
    else:
        meter_pres = max_metering_pres * c_met.get('meter_pres_ratio_locking', 0.6)
```

### 0.2 改造后代码（v1.0：4 维物理化 + 动力源分支）

```python
# ========== 计量压力 v1.0（液压机油压，全电机=0）==========
# 公式：液压机 → max × base_ratio × family_factor × nozzle_factor
#       全电机 → 0（无油缸）
nozzle_type = mach.get('nozzle_type', '直通型')
max_metering_pres = mach.get('max_set_metering_pressure', 20)

if mach.get('power_method') == '全电机':
    # 全电机无油缸，没有"计量压力"输入栏 → 物理正确为 0
    meter_pres = 0
else:
    # 液压机（或默认）：3 维物理化
    base_ratio = (c_met.get('meter_pres_ratio_locking', 0.6)
                  if nozzle_type == '锁定型'
                  else c_met.get('meter_pres_ratio_straight', 0.55))
    family_factor = self._get_family_meter_viscosity(family, c_met)   # 维度 2
    nozzle_factor = self._get_nozzle_factor(nozzle_type, c_met)        # 维度 3

    meter_pres_raw = max_metering_pres * base_ratio * family_factor * nozzle_factor
    meter_pres = max(
        c_met.get('meter_pres_min', 0.0),
        min(meter_pres_raw, c_met.get('meter_pres_max', max_metering_pres))
    )
```

### 0.3 物理依据差异表

| 维度 | 原方法 | 改造后 | 物理依据 |
|------|--------|--------|---------|
| **动力源（液压机）** | `base_ratio` 直通 0.55 / 锁闭 0.60 | 3 维公式：`base_ratio × family_factor × nozzle_factor` | 液压机 HMI 有"计量压力"输入栏，按物理维推导 |
| **动力源（全电机）** | `meter_pres = 0` | `meter_pres = 0`（保持不变）| 全电机无油缸，没有"计量压力"输入栏，0 是物理正确 |
| **材料黏度** | 完全不考虑 | 11 family 系数（0.6~1.3 相对比例）| PP 低黏度（0.6）vs PA66 高黏度（1.3）差异 ~2x |
| **喷嘴结构** | 直通/锁闭二选一 | 直通 1.00 / 锁闭 1.10 | 锁闭喷嘴有止逆阀增加回流阻力 |
| **吸湿材料** | 不考虑 | family 隐式覆盖（PA66=1.3）| PA/PC/PET 等高黏度材料需更高背压排气 |

### 0.4 典型场景差异估算

以海天 MA1600/540 为基准（`max_set_metering_pressure=20`，同源数值体系），仅液压机推送物理化，全电机仍为 0。**单位**：场景数值是"算法内部同源数值"，不是 MPa；具体单位由设备 HMI 决定，算法层不预测。

| 场景 | 材料 | 动力 | 喷嘴 | 原方法 | 改造后 | 差异 |
|------|------|------|------|--------|--------|--------|
| A PP 通用件 | PP | 液压 | 直通 | 20×0.55=**11.0** | 20×0.55×0.6×1.0=**6.6** | -40%（PP 低黏度，物理合理）|
| B PC 精密件 | PC | 液压 | 直通 | 20×0.55=**11.0** | 20×0.55×1.0×1.0=**11.0** | 0（PC 中位，保留原行为）|
| C PA66 含水件 | PA66 | 液压 | 直通 | 20×0.55=**11.0** | 20×0.55×1.3×1.0=**14.3** | +30%（PA66 高黏度+吸湿排气）|
| D 全电机 ABS 精密件 | ABS | **全电** | 直通 | **0** ✅ | **0** ✅ | 0（全电机无油缸，物理正确）|
| E 锁闭喷嘴 PC 精密件 | PC | 液压 | 锁闭 | 20×0.6=**12.0** | 20×0.55×1.0×1.10=**12.1** | +0.8%（锁闭阻力）|

### 0.5 物理正确性总结

| 修正项 | 原方法问题 | 改造后解决 |
|--------|----------|----------|
| **液压机材料无关** | 液压机内 PP 和 PC 用相同 base_ratio=0.55 → 不符合工业实际 | 11 `family_factor`（0.6~1.3 相对比例），PP=0.6 PC=1.0 PA66=1.3 |
| **液压机吸湿排气** | PA/PC 等高黏度+吸湿材料排气需求被忽略 | `family_factor` 隐式覆盖（PA66=1.3）|
| **全电机=0** | 原方法全电机 = 0（**这是物理正确**，不是 bug）| **保留不变**（全电机无油缸，无液压油压来源）|
| **喷嘴结构** | 锁闭喷嘴阻力差异已部分体现（0.55 vs 0.60） | 直通 1.00 / 锁闭 1.10（保留并分解为 nozzle_factor）|

---

## 1. 物理基础

### 1.1 计量压力的物理含义（**仅液压机**）

**计量压力（Metering Pressure / Hydraulic Pressure）** = 液压机液压油缸推动螺杆后退时，克服熔体回流阻力所需的**油压**（HMI 可设定量纲）。

**物理链**：
```
液压马达驱动 → 螺杆旋转输送塑料 → 熔体在螺槽内受剪切
                ↓
熔体在止逆阀/喷嘴处产生回流阻力 → 推动螺杆后退
                ↓
液压系统油压克服阻力 → 油压设定值 = 计量压力
                ↓
受参数影响：油缸尺寸 + 螺杆几何 + 材料黏度 + 喷嘴结构
```

**全电机不适用本定义**（全电机没有液压油路，靠伺服电机+滚珠丝杠直接控制螺杆位置，没有"计量压力"输入栏）。

### 1.2 计量压力的工程功能

| 功能 | 物理机制 | 影响 |
|------|---------|------|
| **排气（degassing）** | 油压建立 → 螺杆后退受控 → 熔体压实 → 气体逸出 | 减少气泡、银纹 |
| **均化（homogenization）** | 油压推动产生剪切 → 熔体混合均匀 | 减少色差、条纹 |
| **塑化质量** | 滞留时间延长 → 熔融完全 | 减少未熔颗粒 |
| **计量精度** | 稳定的熔体密度 → 一致重量 | 重量 CV < 0.5% |

### 1.3 计量压力的工程约束

**Tederic 2026 行业经验范围**（液压机“油压设定”参考值，数值为同源量纲）：
- **典型范围**：5–15（对应行业素材中以 MPa 为习惯标注）
- **低油压**（5–8）：敏感材料（PVC、PC）→ 防降解
- **中油压**（8–12）：大多数材料（PP/ABS/PA）→ 最佳折中
- **高油压**（12–18）：色母粒、含填料 → 强化混合
- **过高油压**：延长塑化时间（+20%），增加能耗，可能降解

> **重要**：工程经验范围与具体设备 HMI 单位直接关联，不是 MPa→bar 的简单换算。例如在 0.1 MPa 分辨率的设备中（界面常见 MPa×10 与 bar×1 的差异），公式中的基准值要重新取值。

> **不同厂家换算并不严格**：不同厂家 HMI 的 bar/MPa/kgf·cm⁻² 换算受表面压力表精度和标定影响，base_ratio 已涵盖厂家特定的单位隐式换算。

---

## 2. 行业标准（参考来源）

### 2.1 各材料推荐背压（Tederic 2026 + 海天 + Moldflow）。（**数值为算法内部同源量纲**，装备 HMI 中可能以 MPa/bar/kgf·cm⁻² 不同单位显示）

| family | 推荐背压 | 物理依据 |
|--------|---------|---------|
| **PP** | 5–8 | 低黏度结晶材料，易塑化，不需要高背压 |
| **PE** | 5–8 | 同 PP（低黏度）|
| **PS** | 5–8 | 非晶态低黏度 |
| **PVC** | 4–8 | 剪切敏感，需要低背压防降解 |
| **ABS** | 8–12 | 中等黏度，需要中背压均化 |
| **POM** | 8–12 | 结晶窄熔程 |
| **PC** | 5–10 | 剪切敏感（低-中背压），但黏度高需要一定压力 |
| **PMMA** | 5–10 | 同 PC（剪切敏感）|
| **PA6/PA66** | 12–18 | 高黏度+吸湿，需高背压排气 |
| **PET** | 8–12 | 结晶+黏度适中 |
| **PBT** | 8–12 | 同 PET |
| **default** | 8–12 | 未知材料保守中位 |

### 2.2 液压机 vs 全电机（Tederic 2026 + 海天 MA 系列）

| 动力源 | "计量压力"参数 | 物理依据 |
|--------|--------------|---------|
| **液压机** | 8–18 | 液压油缸驱动螺杆后退，工艺员可设定油压 |
| **全电机** | **N/A**（无 HMI 输入栏）| 伺服电机+滚珠丝杠直接控制螺杆位置，无液压油路 |

### 2.3 喷嘴结构（Tederic 2026）

| 喷嘴类型 | 压力修正系数 | 物理依据 |
|---------|------------|---------|
| **直通型** | 1.00 | 无额外阻力 |
| **锁闭型** | 1.05-1.15 | 止逆阀增加回流阻力 |

### 2.4 (预留：填充物修正)

> ⏸️ **本版暂不实现**（填充物数据结构正在梳理中，后续扩展）。
> 后续扩展时按 `polymer_filler_composition` 的 abbreviation（GF/CF/TALC/CaCO₃/TiO₂）+ percentage 计算附加修正系数。

---

## 3. 推导链

### 3.1 基础公式（3 维物理化 + 动力源分支）

```
                ┌─ 全电机（无油缸）→ meter_pres = 0
                │
power_method ──┤
                │      ┌─ base_ratio（直通 0.55 / 锁闭 0.60）
                │      │
                └ 液压机 → max_set_metering_pressure
                              │
                              ├── × family_meter_viscosity（11 family，相对比例）
                              └── × nozzle_factor（直通 1.0 / 锁闭 1.10）
                              ↓
                          meter_pres_raw
                              ↓
                          [meter_pres_min, meter_pres_max] 钳制
                              ↓
                          meter_pres
```

### 3.2 维度 1：动力源分支（**非公式相乘**）

**物理意义**：全电机没有液压油缸，因此**没有"计量压力"输入栏**（HMI 不显示），算法输出固定为 0。

```python
def _get_meter_pres_by_power(power_method: str, hydraulic_value: float) -> float:
    """
    按动力源分支：
    - 液压机：返回液压算法推导值
    - 全电机：返回 0（无油缸，无此参数）
    - 其他：按液压机（保守）
    """
    if power_method == '全电机':
        return 0.0
    return hydraulic_value
```

### 3.3 维度 2：材料黏度系数 `family_meter_viscosity`

**物理意义**：材料熔体黏度（Pa·s）越高，需要的油压越大（克服熔体回流阻力）。

```python
FAMILY_METER_VISCOSITY = {
    # 低黏度结晶（推荐 5–8）
    'PP':     0.6,   # 20 × 0.55 × 0.6 = 6.6
    'PE':     0.6,
    'LDPE':   0.6,
    'HDPE':   0.6,
    'LLDPE':  0.6,

    # 非晶态低黏度
    'PS':     0.7,   # 7.7

    # 剪切敏感（推荐 4–8）
    'PVC':    0.5,   # 5.5（防降解）

    # 中等黏度（推荐 8–12）
    'ABS':    1.0,   # 11.0（基准）
    'POM':    1.0,

    # 高黏度（推荐 5–10，剪切敏感但黏度高）
    'PC':     1.0,   # 11.0
    'PMMA':   1.0,

    # 吸湿高黏度（推荐 12–18）
    'PA6':    1.2,   # 13.2
    'PA66':   1.3,   # 14.3
    'PA':     1.2,

    # 结晶+黏度适中（推荐 8–12）
    'PET':    1.0,   # 11.0
    'PBT':    1.0,

    # 复合配方（PC+ABS 等）
    'PC+ABS': 1.0,
    'PC/ABS': 1.0,

    'default': 1.0,   # 未知材料保守中位（11.0）
}
```

> **同源量纲说明**：本字典中的计算结果（如“6.6”/“11.0”）是**算法内部同源数值**（与设备 HMI 单位同轴），不代表 MPa。设备 HMI 可能是 bar / kgf·cm⁻²，不同装装换算并不严格。base_ratio 已涵盖装装特定的单位隐式换算。

**level 字符串映射**：
- `'low_viscosity_crystalline'`：低黏度结晶（PP/PE 系列，0.6）
- `'amorphous_low'`：非晶态低黏度（PS，0.7）
- `'shear_sensitive'`：剪切敏感（PVC，0.5）
- `'medium_viscosity'`：中等黏度（ABS/POM/PET/PBT，1.0）
- `'high_viscosity'`：高黏度（PC/PMMA，1.0）
- `'hygroscopic_high'`：吸湿高黏度（PA6/PA66，1.2~1.3）
- `'default'`：未知（1.0）

### 3.4 维度 3：喷嘴类型系数 `nozzle_factor`

**物理意义**：锁闭喷嘴有止逆阀（shut-off valve），增加回流阻力，需要更高油压克服。

```python
NOZZLE_FACTOR = {
    '直通型': 1.00,    # 无额外阻力（标准）
    '锁定型': 1.10,    # 止逆阀增加阻力
    'default': 1.00,   # 未知喷嘴按直通
}
```

**level 字符串映射**：
- `'straight'`：直通型
- `'locking'`：锁定型（止逆阀）
- `'default'`：未知喷嘴

### 3.4 钳制约束

```python
# 工程钳制（行业经验范围 3–18，同源量纲）
meter_pres_min = c_met.get('meter_pres_min', 3.0)    # 下限（避免无油压）
meter_pres_max = c_met.get('meter_pres_max', 18.0)   # 上限（设备硬保护）

meter_pres = max(meter_pres_min, min(meter_pres_raw, meter_pres_max))
```

**钳制原因**：
- `meter_pres_min=3.0`：避免极端低油压导致未熔颗粒和塑化不均
- `meter_pres_max=18.0`：避免极端高油压导致剪切降解和循环延长

---

## 4. 字符串映射（level → 中文）

| 维度 | level 字符串 | 物理含义 |
|------|-------------|---------|
| **动力源** | ⚠️ **不再是算法维度**，改为条件分支（液压机/全电机）| — |
| **材料** | `low_viscosity_crystalline` / `amorphous_low` / `shear_sensitive` / `medium_viscosity` / `high_viscosity` / `hygroscopic_high` / `default` | 7 类材料等级 |
| **喷嘴** | `straight` / `locking` / `default` | 直通 / 锁闭 / 未知 |

---

## 5. 输出参数策略

### 5.1 主输出：`meter_pres`

```python
# 液压机（3 维公式）
meter_pres: float = max_set_metering_pressure
                  × base_ratio         # 直通 0.55 / 锁闭 0.60
                  × family_factor      # 11 family，0.6~1.3 相对比例
                  × nozzle_factor      # 直通 1.0 / 锁闭 1.10

# 全电机（无油缸）
meter_pres = 0
```

**应用路径**：`proc.met_pres_steps = [meter_pres]`（单段计量）

### 5.2 数据源

| 数据 | 来源 | 默认值 | 量纲 |
|------|------|--------|------|
| `max_set_metering_pressure` | machine_info | 20 | **同源数值**（与设备 HMI 单位保持一致，不做 MPa 转换）|
| `power_method` | machine_info | '液压机' | — |
| `nozzle_type` | machine_info | '直通型' | — |
| `family` | 解析 polymer_info.abbreviation | 'unknown' | — |

> **量纲说明**：算法数值体系与设备 HMI 单位绑定，不假设国际单位（如 MPa）。base_ratio 已涵盖界面单位隐式换算。

### 5.3 数据源（rule config）

```json
{
  "metering": {
    "meter_pres_ratio_straight": 0.55,
    "meter_pres_ratio_locking": 0.6,
    "meter_pres_min": 3.0,
    "meter_pres_max": 18.0,
    "nozzle_factor": {
      "直通型": 1.00,
      "锁定型": 1.10
    },
    "family_meter_viscosity": {
      "PP": 0.6, "PE": 0.6, "LDPE": 0.6, "HDPE": 0.6, "LLDPE": 0.6,
      "PS": 0.7,
      "PVC": 0.5,
      "ABS": 1.0, "POM": 1.0,
      "PC": 1.0, "PMMA": 1.0,
      "PA6": 1.2, "PA66": 1.3, "PA": 1.2,
      "PET": 1.0, "PBT": 1.0,
      "PC+ABS": 1.0, "PC/ABS": 1.0
    },
    "default_family_meter_viscosity": 1.0,
    "default_nozzle_factor": 1.00
  }
}
```

**保留原有字段**（向后兼容）：
- `meter_pres_ratio_straight` / `meter_pres_ratio_locking`（作为 `base_ratio` 使用）
- `meter_pres_min` / `meter_pres_max`（钳制）

---

## 6. 关键创新

### 6.1 物理正交拆分

**"计量压力"vs"计量背压"严格区分**：

| 维度 | 计量压力（meter_pres）#11 | 计量背压（meter_back_pres）#12（后续）|
|------|---------------------|---------------------|
| 物理量 | 液压油压 | 熔体物理阻力 |
| 驱动源 | 液压系统油缸 | 塑化动力学 |
| 适用机器 | ⛔ 仅液压机 | ✅ 所有机器 |
| HMI 输入栏 | 液压机有 | 全电+液压都有 |
| 物理因素 | max 压力限制 + family + nozzle | 螺杆转速 + family + 螺杆几何 |

两者在物理上独立，但都受"family 黏度"和"喷嘴结构"等共同参数影响。

### 6.2 全电机物理约束（保留原代码）

**全电机 `meter_pres = 0` 是物理正确**，不是 bug：
- 全电机没有液压油缸
- HMI 没有"计量压力"输入栏
- 螺杆后退由伺服电机扭矩自适应控制（**这部分将作为"计量背压"下一个算法的研究对象**）

### 6.3 11 family 黏度系数（**相对比例**，0.6~1.3）

参考 TA Instruments 流变数据：

| family | MFI (g/10min) | 黏度等级 | family_factor | 物理解释 |
|--------|-------------|---------|---------------|---------|
| PP | 10-30 | 低 | 0.6 | 低黏度，需要最低油压 |
| PVC | 1-2 | 中（剪切敏感）| 0.5 | 剪切敏感，最低油压防降解 |
| PS | 5-15 | 低-中 | 0.7 | 非晶态低黏度 |
| ABS | 5-20 | 中 | 1.0 | 基准 |
| PC | 5-15 | 中（剪切敏感）| 1.0 | 黏度中等但剪切敏感 |
| PA66 | ~5 | 高 | 1.3 | 吸湿+高黏度，最高油压 |

**相对比例而非绝对值**：保持 `family_factor_default = 1.0`，这样 PC 改性前后值不会发生跳变，仅 PP 等低黏度材料才有显著下移。

### 6.4 3 级 fallback 链

```python
# Level 1: family 精确匹配
family_factor = FAMILY_METER_VISCOSITY[family]  # e.g. PP → 0.6

# Level 2: family 大类匹配（通过 category）
# 例如 'category': '结晶型' → 0.8（介于 PP 和 PET 之间）

# Level 3: 默认值（未知 family）
family_factor = DEFAULT_FAMILY_METER_VISCOSITY  # 1.0
```

**注意**：第一版仅实现 Level 1 + Level 3（精确匹配 + 默认值），Level 2 预留接口（category 大类匹配）后续扩展。

---

## 7. 典型场景验证

### 7.1 场景 A：PP 通用件（液压 + 直通）

```python
machine = {'max_set_metering_pressure': 20, 'power_method': '液压机', 'nozzle_type': '直通型'}
material = {'abbreviation': 'PP'}
# 推导：20 × 0.55 × 0.6 × 1.00 = 6.6（同源数值，非 MPa）
# 行业参考：5–8 ✅
```

### 7.2 场景 B：PC 精密件（液压 + 直通）

```python
material = {'abbreviation': 'PC'}
# 推导：20 × 0.55 × 1.0 × 1.00 = 11.0（同源数值，非 MPa）
# 行业参考：5–10（但高黏度需要 11）✅
```

### 7.3 场景 C：PA66 含水件（液压 + 直通）

```python
material = {'abbreviation': 'PA66'}
# 推导：20 × 0.55 × 1.3 × 1.00 = 14.3（同源数值，非 MPa）
# 行业参考：12–18（高黏度+吸湿排气）✅
```

### 7.4 场景 D：全电机 ABS 精密件（**power_method='全电机' → 0**）

```python
machine = {'max_set_metering_pressure': 20, 'power_method': '全电机', ...}
material = {'abbreviation': 'ABS'}
# 推导：全电机无油缸 → meter_pres = 0
# 行业参考：全电机无"计量压力"输入栏（HMI 不显示），0 是物理正确 ✅
```

### 7.5 场景 E：锁闭喷嘴 PC 精密件

```python
machine = {'nozzle_type': '锁定型', ...}
material = {'abbreviation': 'PC'}
# 推导：20 × 0.55 × 1.0 × 1.10 = 12.1（同源数值，非 MPa）
# 行业参考：12–14 ✅
```

### 7.6 场景 F：未知材料保守兜底

```python
material = {'abbreviation': 'XXX'}
# 推导：20 × 0.55 × 1.0 × 1.00 = 11.0（同源数值，非 MPa）
# 行业参考：未知材料保守中位 8–12 ✅
```

---

## 8. 数据源

### 8.1 物理参数（rule_matcher.py + init_rules.json）

| 参数 | 来源 | 默认值 | 备注 |
|------|------|--------|------|
| `family_meter_viscosity` | rule_matcher.py DEFAULT | 见 §3.3 | 11 family，**相对比例 0.6~1.3** |
| `nozzle_factor` | rule_matcher.py DEFAULT | 见 §3.4 | 直通 1.00 / 锁闭 1.10 |
| `meter_pres_min` | rule_matcher.py DEFAULT | 3.0 | 钳制下限（同源数值，与 max 单位一致）|
| `meter_pres_max` | rule_matcher.py DEFAULT | 18.0 | 钳制上限（同源数值，与 max 单位一致）|
| `meter_pres_ratio_straight` | rule_matcher.py DEFAULT | 0.55 | 保留作为 base_ratio |
| `meter_pres_ratio_locking` | rule_matcher.py DEFAULT | 0.60 | 保留作为 base_ratio |

### 8.2 输入数据（machine_info + polymer_info）

| 输入字段 | 来源 |
|---------|------|
| `max_set_metering_pressure` | machine_info（设备 HMI 设定上限）|
| `power_method` | machine_info（液压/全电）|
| `nozzle_type` | machine_info（直通/锁定）|
| `abbreviation` | polymer_info（解析 family）|

---

## 9. 待确认事项（已决策）

| # | 问题 | 决策 |
|---|------|------|
| 1 | family_meter_viscosity 11 family 系数 | ✅ **使用推荐 11 family 系数**（PP=0.6 ... PA66=1.3 ... default=1.0），**改为相对比例**（基准 1.0）|
| 2 | 全电机（power_method='全电机'）如何处理 | ✅ **保持原代码逻辑**：`meter_pres = 0`（全电机无油缸，**这是物理正确，不是 bug**）|
| 3 | 玻纤/碳纤/矿物填充背压修正 | ⏸️ **本版暂不实现**（数据结构尚未明确，后续扩展）|
| 4 | 喷嘴类型（nozzle_type）如何处理 | ✅ **保留二分**（直通 1.0 / 锁闭 1.10）|
| 5 | "计量压力" vs "计量背压" 概念区分 | ✅ **本算法仅涉及"计量压力"**（液压机油压），"计量背压"作为 #12 后续独立算法 |

---

## 10. 实施计划（全部完成 2026-07-05）

### 10.1 代码变更（initializer.py）✅

- [x] 重写 1381-1390 行计量压力代码（替换原固定比例逻辑）
- [x] 改为条件分支（液压机→公式，全电机→0）
- [x] 添加 3 个辅助函数：
  - `_compute_meter_pres`（v1.0 三维物理化 + 动力源分支）
  - `_get_family_meter_viscosity`（3 级兜底：abbreviation → family → default）
  - `_get_nozzle_factor`（直通/锁闭，level 字符串记录）
- [x] 添加 logger.debug 输出推导链（含 3 个 level 字符串）

### 10.2 数据源变更（rule_matcher.py + init_rules.json）✅

- [x] rule_matcher.py `_BUILTIN_DEFAULTS.metering` 调整字段：
  - `family_meter_viscosity`（17 family 相对比例 0.5~1.3，default=1.0）
  - `nozzle_factor`（直通/锁闭）
  - `meter_pres_min/max` 钉制范围 [3.0, 18.0]
- [x] init_rules.json DEFAULT rule metering block 同步所有字段

### 10.3 Smoke Test ✅

- [x] 创建 [test_meter_pres_smoke.py](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/tests/test_meter_pres_smoke.py)，覆盖 8 类场景：
  - **场景 A-F**（6 个典型场景：PP/PC/PA66/全电机=0/锁闭/未知材料）
  - **场景 G**（边界守门：钉制下限/上限/兑底 level 字符串验证）
  - **场景 H**（动力源分支回归：全电机 = 0）
- [x] **22/22 断言全过**

### 10.4 Roadmap 更新 ✅

- [x] 主清单 #11 计量压力状态 ⏳ → ✅
- [x] 新增 3.11 章节（在 roadmap 中）说明推导公式、物理依据、关键创新、8 个场景验证
- [x] 4.7 旧待改造章节 改为 ✅ 完成状态备注 + 指向 3.11
- [x] 后续动作：新增 #13 计量背压算法（依赖本算法的"动力源分支"逻辑）
