# 保压压力（hold_pres）物理化设计文档

> 算法 #6 · 保压参数 · 半经验四维物理方法（材料 × 壁厚 × 浇口 × 流道）
>
> 文档版本：v1.1
> 设计日期：2026-07-05
> 关联 roadmap：算法清单 #6

---

## 1. 设计背景

### 1.1 现状定位

保压压力（hold_pres）是注塑成型保压阶段的瞬时压力设定值，决定了从 VP 切换到浇口凝固期间的补缩能力。它直接影响：

- **缩痕/凹陷**：保压压力不足 → 补缩不到位 → 制品厚壁处凹陷
- **飞边**：保压压力过高 → 锁模力不足 → 分型面溢料
- **变形**：保压压力不对称 → 内应力分布不均 → 翘曲

### 1.2 为什么需要改造

当前保压压力采用**两段硬切换的经验公式**：

```python
hold_pres = (
    c_hold.get('hold_pres_base_ratio', 0.25) * max_hold_pres       # 25% × 机器最大保压
    + c_hold.get('hold_pres_thickness_factor', 10) * avg_thickness  # 10 MPa/mm × 壁厚
)
if hold_pres >= c_hold.get('hold_pres_max_limit', 120):
    hold_pres = c_hold.get('hold_pres_inj_ratio', 0.65) * inj_pres  # 65% × 注射压力
```

主要问题：

| 问题 | 影响 |
|------|------|
| **两段公式硬切换** | 在 `hold_pres_max_limit = 120` 阈值附近，结果不连续 |
| **无材料差异** | PP（流动性好）vs PC（高黏度）共用同一 base_ratio = 0.25 |
| **无浇口差异** | 直浇口（大浇口）vs 点浇口（小浇口）一视同仁 |
| **无流道差异** | 热流道（流道不冷却）vs 冷流道（流道需补缩）一视同仁 |
| **物理含义模糊** | `base_ratio × max` 与 `inj_ratio × inj_pres` 是两套独立公式，没有共同物理基础 |
| **无安全钳制** | `10 × thickness` 在 t > 10mm 时可能超过 `max_hold_pres`（机器硬上限）|

### 1.3 设计目标

将保压压力从"两段经验公式硬切换"重构为**三维半经验物理方法**（材料 × 壁厚 × 浇口），所有系数都能追溯到材料手册/设备规范/行业共识。

---

## 2. 问题的本质定义

### 2.1 保压压力的物理本质

保压阶段发生在 VP 切换之后、浇口凝固之前。螺杆以设定的保压压力推动熔体持续补缩，补偿制品冷却收缩 + 流道冷却收缩。

保压压力的物理边界：

| 边界 | 物理含义 | 后果 |
|------|---------|------|
| **下限** | ≥ 浇口凝固压力 | 否则浇口处回流 → 缩痕/凹陷 |
| **上限** | < 飞边压力 | 否则分型面溢料 |
| **上限** | < 注射压力 | 保压是注射的延续，过高无意义 |
| **硬上限** | ≤ max_hold_pres | 机器能力上限 |

保压压力本质上是**一个"窗口值"**，需要在防凹陷下限与防飞边上限之间找最优。

### 2.2 物理驱动因素

保压压力受**四类因素**共同影响：

1. **材料因素**（family）：
   - 黏度等级（PP/PE 流动性好 → 保压上限偏低；PC 高黏度 → 保压上限偏高）
   - 结晶特性（PET/PA 等半结晶 → 结晶补缩需要更高保压）
   - 收缩率（高收缩材料需要更高保压补缩）

2. **几何因素**（壁厚 + 浇口）：
   - 壁厚（厚壁冷却收缩体积大 → 需要更高保压补缩）
   - 浇口尺寸（小浇口阻力大 → 需要更高保压克服阻力）

3. **流道因素**（runner_type）：
   - **热流道**：流道始终熔融 → 无流道冷却收缩 → 保压压力偏低（无流道补缩需求）
   - **冷流道**：流道随制品冷却 → 流道收缩需要保压补缩 → 保压压力偏高
   - **热转冷**：部分流道凝固（混合系统）→ 介于两者之间

4. **工艺因素**（注射压力）：
   - 保压压力通常为注射压力的 50%~70%（行业共识）
   - 高于注射压力无意义（保压是注射的延续）

### 2.3 设计约束

| 约束 | 取值 | 依据 |
|------|------|------|
| **保压压力物理上限** | ≤ max_hold_pres × 0.95 | 机器能力硬上限的 95%（安全裕度，与注射速度一致）|
| **保压压力物理下限** | ≥ inj_pres × 0.40 | 经验下限（过低会凹陷）|
| **保压压力物理上限** | ≤ inj_pres × 0.85 | 经验上限（过高无意义）|

---

## 3. 新算法核心（基于物理推导）

### 3.1 主公式

```python
hold_pres = min(
    inj_pres
    × family_hold_ratio[family]      # 维度 1：材料相对保压比例
    × thickness_factor(bucket)       # 维度 2：壁厚修正
    × gate_factor(gate_type)         # 维度 3：浇口修正
    × runner_factor(runner_type),    # 维度 4：流道修正（热/冷/热转冷）
    max_hold_pres × max_safe_hold_ratio  # 安全钳制（默认 0.95）
)
```

### 3.2 物理推导链

```
保压压力（瞬时 MPa）
  ↓
= 注射压力 × 相对保压比例    # 物理依据：保压是注射的延续
  ↓
  × family_hold_ratio          # 维度 1：材料黏度等级
  × thickness_factor           # 维度 2：壁厚补缩需求
  × gate_factor                # 维度 3：浇口阻力
  × runner_factor              # 维度 4：流道状态（热/冷/热转冷）
  ↓
clamp 到 [40%, 95%] × 机器能力  # 安全钳制：防凹陷下限 + 防飞边上限
```

### 3.3 维度 1：family_hold_ratio（11 family）

**物理依据**：
- 黏度等级：MFI 高 → 流动性好 → 保压上限偏低（防飞边）
- 黏度等级：高黏度（PC/POM）→ 保压上限偏高（防凹陷）
- 结晶特性：半结晶材料（PET/PA）→ 结晶补缩 → 保压偏高
- 行业共识：保压压力为注射压力的 50%~75%（海天/震雄/Fanuc 工艺手册 + Moldflow 共识中位）

| family | hold_pres_ratio | 物理依据 |
|--------|----------------|---------|
| **PP** | **0.50** | MFI 高（流动性好），低保压防飞边 |
| **PE** | **0.50** | 同 PP |
| **PS** | **0.55** | 中流动性（流动性中等）|
| **ABS** | **0.60** | 中流动性（流动性中等）|
| **PMMA** | **0.60** | 中流动性（流动性中等）|
| **PET** | **0.65** | 半结晶，结晶补缩需要更高保压 |
| **PBT** | **0.65** | 同 PET |
| **PA** | **0.70** | 高黏度，高保压防凹陷 |
| **POM** | **0.75** | 高黏度，高保压防凹陷 |
| **PC** | **0.75** | 高黏度，高保压防凹陷 |
| **AS** | **0.55** | 中流动性（与 ABS 相近）|
| **默认值** | **0.60** | 与原 `hold_pres_inj_ratio = 0.65` 中位相当（保守偏中）|

### 3.4 维度 2：thickness_factor（3 桶）

**复用注射时间的 `thickness_bucket_thresholds = [1.5, 3.0]`**：

| bucket | 范围 | factor | 物理依据 |
|--------|------|--------|---------|
| **thin** | t ≤ 1.5mm | **0.95** | 薄壁：收缩阻力小，收缩量小 → 可偏低 |
| **medium** | 1.5 < t ≤ 3.0mm | **1.00** | 中位：不修正 |
| **thick** | t > 3.0mm | **1.10** | 厚壁：冷却收缩体积大 → 需更高保压补缩 |

### 3.5 维度 3：gate_factor（按 gate_type 字符串）

| gate_type | factor | 物理依据 |
|-----------|--------|---------|
| **直浇口** | **0.95** | 大浇口，流阻小 → 可偏低 |
| **护耳式浇口** | **1.00** | 中等浇口 → 不修正 |
| **点浇口** | **1.10** | 小浇口，流阻大 → 需更高保压克服阻力 |
| **侧浇口** | **1.00** | 中等浇口 → 不修正 |
| **其他/默认** | **1.00** | 保守不修正 |

### 3.6 维度 4：runner_factor（按 runner_type 字符串）

| runner_type | factor | 物理依据 |
|-------------|--------|---------|
| **热流道** | **0.95** | 流道始终熔融 → 无流道冷却收缩 → 无流道补缩需求 → 保压可偏低 |
| **热转冷** | **1.00** | 部分流道凝固（混合系统）→ 介于热冷之间 → 中位 |
| **冷流道** | **1.05** | 流道随制品冷却 → 流道收缩需保压补缩 → 保压需偏高 |
| **未知/默认** | **1.00** | 保守不修正 |

**注意**：
- runner_type 来源：`GatingSystem.runner_type`（已升级枚举：热流道/冷流道/热转冷）
- 数据缺口：当前产品历史数据可能只填"热流道/冷流道"二分，缺"热转冷"
- 兑底兼容：`runner_weight == 0` 推断为热流道 → factor 0.95（向后兼容）

### 3.7 安全钳制

```python
max_safe_hold_ratio = c_inj.get('max_safe_hold_ratio', 0.95)
hold_pres = min(hold_pres, max_hold_pres * max_safe_hold_ratio)
```

**物理依据**：
- 机器最大保压压力的 95%（与注射速度安全裕度一致）
- 5% 缓冲：防止机台响应误差 + 液压冲击

### 3.8 物理边界保护（双钳制）

为防止意外超界，再叠加 **inj_pres 比例钳制**：

```python
hold_pres = max(0.40 * inj_pres, min(hold_pres, 0.85 * inj_pres))
```

**物理依据**：
- 下限：inj_pres × 0.40（保压不能太低，否则凹陷）
- 上限：inj_pres × 0.85（保压不能超过注射压力的 85%，否则无意义）

最终公式：

```python
hold_pres_raw = (
    inj_pres
    × family_hold_ratio[family]
    × thickness_factor(bucket)
    × gate_factor(gate_type)
    × runner_factor(runner_type)
)
hold_pres = min(
    max(0.40 * inj_pres, min(hold_pres_raw, 0.85 * inj_pres)),  # 物理比例钳制
    max_hold_pres * max_safe_hold_ratio                          # 机器硬上限
)
```

---

## 4. 数据需求与 3 级兜底策略

### 4.1 数据需求矩阵

| 数据 | 来源 | 必要性 | 兜底策略 |
|------|------|--------|---------|
| inj_pres | 已物理化（算法 #3）| 必须 | - |
| max_hold_pres | machine_info | 必须 | 默认 100 MPa |
| family | 已解析（_parse_family）| 必须 | 默认 "unknown" |
| max_thickness | mold_info | 必须 | 强制字段（_validate_inputs）|
| gate_type | mold_info | 必须 | 默认 "其他" → factor 1.00 |

### 4.2 3 级兜底策略

#### 4.2.1 family_hold_ratio 的兜底

```python
def _get_family_hold_ratio(self, family: str, c_hold: Dict[str, Any]) -> Tuple[float, str]:
    """
    获取材料相对保压比例（3 级兜底）

    优先级：
    1. 第 1 级 - Polymer.recommend_hold_pres_ratio（精确值）
    2. 第 2 级 - family_hold_ratio[family]（大类典型值）
    3. 第 3 级 - default_hold_ratio（兜底）
    """
    # 第 1 级：精确值
    if self.material.get('recommend_hold_pres_ratio') is not None:
        return self.material['recommend_hold_pres_ratio'], 'precise'

    # 第 2 级：大类查表
    family_ratio_map = c_hold.get('family_hold_ratio', {})
    if family and family in family_ratio_map:
        return family_ratio_map[family], 'family'

    # 第 3 级：兜底
    return c_hold.get('default_hold_ratio', 0.60), 'default'
```

#### 4.2.2 thickness_factor 的兜底

复用 `_get_thickness_bucket`（算法 #5 已实现）：

```python
bucket, bucket_level = self._get_thickness_bucket(max_thickness, c_inj)
thickness_factor_map = c_hold.get('thickness_factor', {
    'thin': 0.95, 'medium': 1.00, 'thick': 1.10
})
thickness_factor = thickness_factor_map.get(bucket, 1.00)
```

#### 4.2.3 gate_factor 的兜底

```python
def _get_gate_factor(self, gate_type: str, c_hold: Dict[str, Any]) -> float:
    """
    获取浇口修正因子（4 档 + 默认）
    """
    gate_factor_map = c_hold.get('gate_factor', {
        '直浇口': 0.95,
        '护耳式浇口': 1.00,
        '点浇口': 1.10,
        '侧浇口': 1.00,
    })
    return gate_factor_map.get(gate_type, 1.00)
```

#### 4.2.4 runner_factor 的兜底

```python
def _get_runner_factor(self, runner_type: str, runner_weight: float, c_hold: Dict[str, Any]) -> Tuple[float, str]:
    """
    获取流道修正因子（3 档 + 默认）

    优先级：
    1. 第 1 级 - mold.runner_pressure_factor（制品级精确值）
    2. 第 2 级 - runner_factor[runner_type]（查表）
    3. 第 3 级 - runner_weight 推断（向后兼容）
    4. 第 4 级 - 1.00（默认不修正）
    """
    from utils.constants import RUNNER_TYPE_HOT, RUNNER_TYPE_COLD, RUNNER_TYPE_HOT_TO_COLD

    # 第 1 级：精确值
    precise = self.mold.get('runner_pressure_factor')
    if precise is not None:
        return precise, 'precise'

    # 第 2 级：枚举查表
    runner_factor_map = c_hold.get('runner_factor', {
        RUNNER_TYPE_HOT: 0.95,
        RUNNER_TYPE_HOT_TO_COLD: 1.00,
        RUNNER_TYPE_COLD: 1.05,
    })
    if runner_type in runner_factor_map:
        return runner_factor_map[runner_type], 'runner_type'

    # 第 3 级：runner_weight 推断（向后兼容老数据）
    if runner_weight == 0:
        return 0.95, 'inferred_hot'  # runner_weight=0 → 热流道
    if runner_weight > 0 and runner_weight is not None:
        return 1.05, 'inferred_cold'  # runner_weight>0 → 冷流道

    # 第 4 级：默认
    return 1.00, 'default'
```

---

## 5. 保守兜底原则

### 5.1 兜底哲学

未识别场景采用**最保守值**，确保安全性：

| 场景 | 兜底值 | 保守依据 |
|------|--------|---------|
| **未知材料（family 未识别）** | default_hold_ratio = 0.60 | 中位值（与 ABS 相同），不偏向高/低 |
| **未知 gate_type** | 1.00 | 不修正，避免误判 |
| **未知 bucket** | 1.00 | 不修正，避免误判 |
| **max_thickness 缺失** | 强制抛 ValueError | 已在 _validate_inputs 中校验 |

### 5.2 与"渐进式物理化"路线对齐

本算法处于**半经验方法**阶段（定性物理正确 + 定量行业共识），与注射压力/速度/时间同档：

- ✅ **定性物理正确**：维度划分（family × thickness × gate）符合物理
- ✅ **定量行业共识**：所有数值（family_hold_ratio / thickness_factor / gate_factor）来自海天/震雄/Fanuc 工艺手册 + Moldflow 共识中位
- ❌ **不是严格物理推导**：未引入 Moldflow CAE 仿真验证

后续可升级为严格物理推导（详见第 14 章）。

---

## 6. 与原算法的对比

### 6.1 公式对比

| 维度 | 原算法 | 新算法 |
|------|--------|--------|
| **公式形态** | 两段硬切换（base_ratio + thickness → inj_ratio）| 单一连续公式（inj_pres × 三维因子）|
| **物理依据** | 无（纯经验）| 流变学 + 几何修正 |
| **材料差异** | ❌ 无 | ✅ 11 family × 3 段 |
| **壁厚差异** | ⚠️ 线性（10 MPa/mm）| ✅ 3 桶分档（0.95/1.00/1.10）|
| **浇口差异** | ❌ 无 | ✅ 4 档（0.95/1.00/1.10）|
| **安全钳制** | ❌ 无 | ✅ max_safe_hold_ratio = 0.95 |
| **连续性** | ❌ 120MPa 处硬切换 | ✅ 连续（单一公式）|

### 6.2 数值对比（典型场景）

| 场景 | 原算法 | 新算法 | 差异 |
|------|--------|--------|------|
| **PP + 2mm + 直浇口** | 25% × 100 + 10 × 2 = 45 MPa | 75 × 0.50 × 1.00 × 0.95 = 35.6 MPa | -21%（PP 不需要那么高）|
| **PC + 2mm + 点浇口** | 25% × 100 + 10 × 2 = 45 MPa | 112.5 × 0.75 × 1.00 × 1.10 = 92.8 MPa | +106%（PC 高黏度需更高）|
| **PET + 3mm + 直浇口** | 25% × 100 + 10 × 3 = 55 MPa | 97.5 × 0.65 × 1.00 × 0.95 = 60.2 MPa | +9%（结晶补缩略高）|
| **POM + 5mm + 点浇口** | 25% × 100 + 10 × 5 = 75 MPa | 97.5 × 0.75 × 1.10 × 1.10 = 88.5 MPa | +18%（厚壁 + 点浇口）|

**主要差异**：
- 低黏度材料（PP）：新算法偏低（防飞边，物理正确）
- 高黏度材料（PC）：新算法偏高（防凹陷，物理正确）
- 厚壁 + 点浇口：新算法显著偏高（双维度同时修正，物理正确）

### 6.3 收益总结

| 收益 | 说明 |
|------|------|
| **删除硬切换** | 单一连续公式，结果平滑 |
| **三维差异化** | 材料 × 壁厚 × 浇口，覆盖全面 |
| **物理正确** | 维度划分符合物理驱动 |
| **安全裕度** | max_safe_hold_ratio = 0.95 防飞边 |
| **可解释性** | 每个因子都有明确物理依据 |

---

## 7. 实施计划

### 7.1 阶段 1：辅助函数（无侵入）

在 `initializer.py` 中新增 3 个辅助函数（与算法 #5 同套路）：

```python
def _get_family_hold_ratio(self, family: str, c_hold: Dict[str, Any]) -> Tuple[float, str]:
    """获取材料相对保压比例（3 级兑底）"""
    # ...详见 4.2.1

def _get_gate_factor(self, gate_type: str, c_hold: Dict[str, Any]) -> float:
    """获取浇口修正因子（4 档 + 默认）"""
    # ...详见 4.2.3

def _get_runner_factor(self, runner_type: str, runner_weight: float, c_hold: Dict[str, Any]) -> Tuple[float, str]:
    """获取流道修正因子（3 档 + runner_weight 推断 + 默认）"""
    # ...详见 4.2.4
```

### 7.2 阶段 2：主调用重构

替换 `initializer.py:765-770` 的旧公式：

```python
# 【重构】保压压力 = 注射压力 × 材料相对保压比例 × 壁厚修正 × 浇口修正 × 流道修正
# 推导链：保压是注射的延续 → 材料黏度等级 × 几何修正（壁厚/浇口） × 流道状态 → 安全钳制
# 数据源：3 级兑底（精确值 / 大类查表 / 默认值）
# 物理详见 _dev_refs/2026-07-05-holding-pressure-physics-design.md
inj_pres_1st = proc.inj_pres_steps[0]  # 取第一段注射压力（已物理化）
gate_type = prod.get('gate_type', '其他')
max_thickness = prod.get('max_thickness', 0)
runner_type = prod.get('runner_type', '')
runner_weight = prod.get('runner_weight', 0)

family_hold_ratio, hold_level = self._get_family_hold_ratio(family, c_hold)
bucket, bucket_level = self._get_thickness_bucket(max_thickness, c_inj)
thickness_factor = c_hold.get('thickness_factor', {'thin': 0.95, 'medium': 1.00, 'thick': 1.10}).get(bucket, 1.00)
gate_factor = self._get_gate_factor(gate_type, c_hold)
runner_factor, runner_level = self._get_runner_factor(runner_type, runner_weight, c_hold)

hold_pres_raw = inj_pres_1st * family_hold_ratio * thickness_factor * gate_factor * runner_factor
hold_pres = min(
    max(0.40 * inj_pres_1st, min(hold_pres_raw, 0.85 * inj_pres_1st)),  # 物理比例钳制
    max_hold_pres * c_inj.get('max_safe_hold_ratio', 0.95)              # 机器硬上限
)

logger.debug(
    f"保压压力: family={family or 'unknown'} (level={hold_level}), "
    f"family_hold_ratio={family_hold_ratio:.3f}, "
    f"bucket={bucket} (level={bucket_level}), thickness_factor={thickness_factor:.3f}, "
    f"gate_type={gate_type}, gate_factor={gate_factor:.3f}, "
    f"runner_type={runner_type or 'inferred'} (level={runner_level}), runner_factor={runner_factor:.3f}, "
    f"hold_pres_raw={hold_pres_raw:.2f}MPa → hold_pres={hold_pres:.2f}MPa"
)
```

### 7.3 阶段 3：配置更新

更新 `init_rules.json` DEFAULT.holding 块，**追加** 4 个新字段：

```json
"holding": {
    "family_hold_ratio": {
        "PP": 0.50, "PE": 0.50, "PS": 0.55, "ABS": 0.60, "PMMA": 0.60,
        "AS": 0.55, "PET": 0.65, "PBT": 0.65, "PA": 0.70, "POM": 0.75, "PC": 0.75
    },
    "default_hold_ratio": 0.60,
    "thickness_factor": {
        "thin": 0.95, "medium": 1.00, "thick": 1.10
    },
    "gate_factor": {
        "直浇口": 0.95, "护耳式浇口": 1.00, "点浇口": 1.10, "侧浇口": 1.00
    },
    "max_safe_hold_ratio": 0.95,
    "hold_pres_inj_ratio_min": 0.40,
    "hold_pres_inj_ratio_max": 0.85
}
```

### 7.4 阶段 4：硬切换字段清理

**删除旧字段**（不再使用）：
- `hold_pres_base_ratio`（0.25）
- `hold_pres_thickness_factor`（10）
- `hold_pres_max_limit`（120）
- `hold_pres_inj_ratio`（0.65）

**保留字段**：
- `hold_velo_ratio`（保压速度，暂不动）
- `hold_time_min/max`（保压时间，暂不动，但 `hold_time_max = 10.0` 已在 roadmap 4.6 标记为待清理）

### 7.5 阶段 5：rule_matcher.py 同步

在 `_BUILTIN_DEFAULTS['holding']` 中同步追加 4 个新字段，与 JSON 保持一致。

---

## 8. JSON 配置示例

### 8.1 DEFAULT.holding 完整配置

```json
"holding": {
    "family_hold_ratio": {
        "PP": 0.50,
        "PE": 0.50,
        "PS": 0.55,
        "ABS": 0.60,
        "AS": 0.55,
        "PMMA": 0.60,
        "PET": 0.65,
        "PBT": 0.65,
        "PA": 0.70,
        "POM": 0.75,
        "PC": 0.75
    },
    "default_hold_ratio": 0.60,
    "thickness_factor": {
        "thin": 0.95,
        "medium": 1.00,
        "thick": 1.10
    },
    "gate_factor": {
        "直浇口": 0.95,
        "护耳式浇口": 1.00,
        "点浇口": 1.10,
        "侧浇口": 1.00
    },
    "runner_factor": {
        "热流道": 0.95,
        "热转冷": 1.00,
        "冷流道": 1.05
    },
    "max_safe_hold_ratio": 0.95,
    "hold_pres_inj_ratio_min": 0.40,
    "hold_pres_inj_ratio_max": 0.85,
    "hold_velo_ratio": 0.15,
    "hold_time_min": 2.0,
    "hold_time_max": 10.0,
    "hold_time_strategy": "quadratic",
    "hold_time_linear_a": 0.5,
    "hold_time_linear_b": 0.1,
    "hold_time_area_coef": 2.0,
    "hold_time_quadratic_a": 0.3,
    "hold_time_quadratic_b": 0.6
}
```

### 8.2 _BUILTIN_DEFAULTS['holding'] 同步配置

```python
'holding': {
    # 保压压力物理化默认值
    'family_hold_ratio': {
        'PP': 0.50, 'PE': 0.50, 'PS': 0.55, 'ABS': 0.60, 'AS': 0.55,
        'PMMA': 0.60, 'PET': 0.65, 'PBT': 0.65, 'PA': 0.70, 'POM': 0.75, 'PC': 0.75,
    },
    'default_hold_ratio': 0.60,
    'thickness_factor': {'thin': 0.95, 'medium': 1.00, 'thick': 1.10},
    'gate_factor': {
        '直浇口': 0.95, '护耳式浇口': 1.00, '点浇口': 1.10, '侧浇口': 1.00,
    },
    'runner_factor': {
        '热流道': 0.95, '热转冷': 1.00, '冷流道': 1.05,
    },
    'max_safe_hold_ratio': 0.95,
    'hold_pres_inj_ratio_min': 0.40,
    'hold_pres_inj_ratio_max': 0.85,
    # 保压速度（暂保留）
    'hold_velo_ratio': 0.15,
    # 保压时间（待路线图 4.6 节升级，详见 roadmap）
    'hold_time_min': 2.0,
    'hold_time_max': 10.0,
    'hold_time_strategy': 'quadratic',
    'hold_time_linear_a': 0.5,
    'hold_time_linear_b': 0.1,
    'hold_time_area_coef': 2.0,
    'hold_time_quadratic_a': 0.3,
    'hold_time_quadratic_b': 0.6,
},
```

---

## 9. 测试用例设计

### 9.1 单元测试（initializer 内部）

#### 9.1.1 维度 1：family_hold_ratio 兜底测试

| 场景 | 预期 | 覆盖 |
|------|------|------|
| **PP（family 已识别）** | 0.50（family 级别）| 第 2 级 |
| **PC（family 已识别）** | 0.75（family 级别）| 第 2 级 |
| **UNKNOWN（family 未识别）** | 0.60（default）| 第 3 级 |
| **空字符串 family** | 0.60（default）| 第 3 级 |
| **Polymer.recommend_hold_pres_ratio = 0.55（精确值）** | 0.55（precise）| 第 1 级 |

#### 9.1.2 维度 2：thickness_factor 测试

| max_thickness | 预期 bucket | 预期 factor | 物理依据 |
|---------------|------------|------------|---------|
| 1.0mm | thin | 0.95 | 薄壁 |
| 1.5mm | thin | 0.95 | 边界（含等号）|
| 1.51mm | medium | 1.00 | 边界外 |
| 3.0mm | medium | 1.00 | 边界（含等号）|
| 3.01mm | thick | 1.10 | 边界外 |
| 5.0mm | thick | 1.10 | 厚壁 |

#### 9.1.3 维度 3：gate_factor 测试

| gate_type | 预期 factor | 物理依据 |
|-----------|------------|---------|
| 直浇口 | 0.95 | 大浇口 |
| 护耳式浇口 | 1.00 | 中等 |
| 点浇口 | 1.10 | 小浇口 |
| 侧浇口 | 1.00 | 中等 |
| 其他 / 未识别 | 1.00 | 默认不修正 |

#### 9.1.4 维度 4：runner_factor 测试

| runner_type | runner_weight | 预期 factor | level | 物理依据 |
|-------------|---------------|------------|-------|---------|
| **热流道** | 0 | **0.95** | runner_type / inferred_hot | 流道不冷却 |
| **热转冷** | - | **1.00** | runner_type | 部分冷却 |
| **冷流道** | 10 | **1.05** | runner_type / inferred_cold | 流道随制品冷却 |
| **未指定** | 0 | **0.95** | inferred_hot | runner_weight=0 推断热流道 |
| **未指定** | 5 | **1.05** | inferred_cold | runner_weight>0 推断冷流道 |
| **未指定** | None（缺失） | **1.00** | default | 完全未知，保守不修正 |
| **精确值** `mold.runner_pressure_factor = 0.92` | - | **0.92** | precise | 制品级覆盖 |

### 9.2 端到端测试

#### 9.2.1 典型材料 × 壁厚 × 浇口 × 流道组合（四维）

| # | 材料 | 壁厚 | 浇口 | 流道 | inj_pres | hold_pres_raw | hold_pres |
|---|------|------|------|------|----------|---------------|-----------|
| 1 | **PP** | 2.0mm | 直浇口 | **热流道** | 75 MPa | 75 × 0.50 × 1.00 × 0.95 × 0.95 = **33.8** | 33.8 |
| 2 | **PP** | 2.0mm | 直浇口 | **冷流道** | 75 MPa | 75 × 0.50 × 1.00 × 0.95 × 1.05 = **37.4** | 37.4 |
| 3 | **PP** | 2.0mm | 直浇口 | **热转冷** | 75 MPa | 75 × 0.50 × 1.00 × 0.95 × 1.00 = **35.6** | 35.6 |
| 4 | **ABS** | 2.0mm | 直浇口 | 热流道 | 82.5 MPa | 82.5 × 0.60 × 1.00 × 0.95 × 0.95 = **44.7** | 44.7 |
| 5 | **PC** | 2.0mm | 点浇口 | 冷流道 | 112.5 MPa | 112.5 × 0.75 × 1.00 × 1.10 × 1.05 = **97.4** | 95.6（受 max_safe 钳制）|
| 6 | **PET** | 3.0mm | 直浇口 | 冷流道 | 97.5 MPa | 97.5 × 0.65 × 1.00 × 0.95 × 1.05 = **63.2** | 63.2 |
| 7 | **POM** | 5.0mm | 点浇口 | 冷流道 | 97.5 MPa | 97.5 × 0.75 × 1.10 × 1.10 × 1.05 = **92.9** | 92.9 |

**主要差异**：
- **流道差异（PP 热 vs 冷）**：37.4 - 33.8 = 3.6 MPa（+10.6%）✅ 冷流道需更高补缩压力
- **PET 冷流道 vs 直浇口冷流道**：结晶材料 + 冷流道叠加，物理正确

#### 9.2.2 边界场景

| # | 场景 | 预期 hold_pres | 钳制来源 |
|---|------|---------------|---------|
| 1 | **超大厚度 + 点浇口（极端情况）** | 受 `inj_pres × 0.85` 钳制 | 上限钳制 |
| 2 | **超小厚度 + 直浇口（极端情况）** | 受 `inj_pres × 0.40` 钳制 | 下限钳制 |
| 3 | **max_hold_pres 偏小（机器能力不足）** | 受 `max_hold_pres × 0.95` 钳制 | 机器硬上限 |

#### 9.2.3 回归对比（与原算法）

| # | 材料 | 壁厚 | 浇口 | 原算法 hold_pres | 新算法 hold_pres | 物理合理性 |
|---|------|------|------|----------------|----------------|----------|
| 1 | PP | 2.0mm | 直浇口 | 45 MPa | 35.6 MPa | ✅ PP 不需要那么高 |
| 2 | PC | 2.0mm | 点浇口 | 45 MPa | 92.8 MPa | ✅ PC 高黏度 + 点浇口需要更高 |
| 3 | PET | 3.0mm | 直浇口 | 55 MPa | 60.2 MPa | ✅ PET 结晶补缩略高 |

---

## 10. 风险与缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| **family_hold_ratio 数值偏差** | 中 | 中 | 与注射压力联动验证（PP 50% vs PC 75% 应该有 ~25% 差异）；后续 Moldflow 校准 |
| **gate_factor 数值偏差** | 中 | 中 | 物理依据明确（浇口流阻），但实际差异可能 ±5%，需试模验证 |
| **thickness_factor 跨桶边界不平滑** | 低 | 低 | 桶分界与注射时间共用，复用已验证阈值 `[1.5, 3.0]` |
| **runner_factor 冷热流道区分偏差** | 中 | 中 | 热流道 0.95 vs 冷流道 1.05 差异较大（+10.5%）；需试模验证。同时考虑老数据仅填 runner_weight=0/非 0 → 采用推断兑底 |
| **历史数据缺"热转冷"字段** | 中 | 低 | 第 3 级兑底：runner_weight=0 推断热流道 → 0.95；向后兼容。但建议补填"热转冷"字段 |
| **max_safe_hold_ratio = 0.95 过紧** | 低 | 中 | 与注射速度同档（0.95），如果飞边可降到 0.90 |
| **物理比例钳制 (0.40~0.85) 跨场景适用性** | 中 | 中 | 数值来自行业共识，但特殊材料（LCP/PPS）可能超出，需 case-by-case 调优 |

---

## 11. 相关文件

| 文件 | 角色 |
|------|------|
| `process/engines/expert/initializer.py` | 算法主体（待改造 `_derive_process` 中保压压力部分）|
| `process/engines/expert/expert_rules/init_rules.json` | 规则配置（DEFAULT.holding 待追加 4 字段）|
| `process/engines/expert/rule_matcher.py` | `_BUILTIN_DEFAULTS['holding']` 待同步 |
| `_dev_refs/2026-07-04-algorithm-refactor-roadmap.md` | roadmap（算法 #6 待标注完成）|
| `_dev_refs/2026-07-05-injection-pressure-physics-design.md` | 算法 #3 设计文档（inj_pres 来源）|
| `_dev_refs/2026-07-05-injection-time-physics-design.md` | 算法 #5 设计文档（thickness_bucket 复用）|
| `_dev_refs/2026-07-05-holding-pressure-physics-design.md` | 本文档（算法 #6）|

---

## 12. 后续扩展（不在本文档范围）

| 算法 | 优先级 | 文档 | 说明 |
|------|--------|------|------|
| **保压速度**（算法 #7）| P1 | 待出 | 与保压压力耦合，速度决定补缩速率 |
| **保压时间**（算法 #8）| **P0+**（已提升）| 待出 | **必须覆盖长保压场景（PET 瓶盖 100~300s），删除 `hold_time_max = 10.0` 硬上限** |
| **保压多段曲线** | P3 | - | 当前保压只支持 1 段（hold_stg = 1），后续可拆为 3 段（递减保压）|

---

## 13. 局限性诚实声明

### 13.1 当前阶段是"半经验物理方法"

本算法**不是严格的物理推导**，而是：

- ✅ **定性物理正确**：维度划分（family × thickness × gate × runner）符合物理驱动
- ✅ **定量行业共识**：所有数值（family_hold_ratio / thickness_factor / gate_factor / runner_factor）来自海天/震雄/Fanuc 工艺手册 + Moldflow 共识中位
- ❌ **不是严格物理推导**：未引入 Moldflow CAE 仿真验证每个数值
- ❌ **未覆盖极端材料**：LCP / PPS / 高填充玻纤等特殊材料未验证

### 13.2 关键假设

1. **保压压力与注射压力存在稳定比例关系**（行业共识 50%~75%）
2. **保压压力的物理窗口为 `[inj_pres × 0.40, inj_pres × 0.85]`**（来自工艺手册）
3. **family × thickness × gate × runner 四维独立可乘**（维度间无强耦合）
4. **机器最大保压压力的 95% 是安全裕度上限**（与注射速度同档）

### 13.3 数据缺口

| 缺口 | 现状 | 后续 |
|------|------|------|
| **family_hold_ratio 缺少试模验证** | 来自工艺手册 + Moldflow 共识中位 | 试模 3~5 次/材料后更新 |
| **gate_factor 缺少量化对比** | 物理依据明确但缺乏实验数据 | 同一材料 × 不同浇口对比试模 |
| **thickness_factor 桶分界缺乏过渡** | thin/medium/thick 硬分档 | 后续可改为连续函数（多项式/指数）|
| **runner_factor 热转冷区分** | 产品历史数据可能只填"热/冷"二分，缺"热转冷" | 后续补填枚举字段 |

---

## 14. 渐进式物理化演进路径

### 14.1 阶段一（当前文档）：半经验四维物理方法

```
hold_pres = inj_pres × family_hold_ratio[family] × thickness_factor(bucket) × gate_factor(gate_type) × runner_factor(runner_type)
```

**目标**：定性物理正确 + 定量行业共识。

### 14.2 阶段二（中期）：引入 PVT 数据

```
hold_pres = inj_pres × (1 + shrinkage_rate × crystallization_factor[family])
```

**依据**：半结晶材料（PET/PA/POM）的保压压力与结晶度直接相关，引入 PVT 数据可提升精度。

### 14.3 阶段三（长期）：Moldflow CAE 仿真校准

```
hold_pres = inj_pres × family_hold_ratio[family] × moldflow_calibration[part_id]
```

**依据**：每个制品的 Moldflow 仿真可给出精确的 family_hold_ratio 数值，彻底替代行业共识。

### 14.4 演进路径依赖

```
阶段一（当前） ── 数据积累 ──→ 阶段二 ── CAE 仿真集成 ──→ 阶段三
                                ↑
                          试模 3~5 次/材料
```

---

## 15. 与项目物理化演进路线的对齐

### 15.1 路线图位置

**算法 #6 · 保压参数 · 阶段 2 · P0**

| 阶段 | 算法 | 状态 |
|------|------|------|
| 阶段 1 | 行程分配（#1 收缩长度 + #2 料垫长度）| ✅ 已完成 |
| **阶段 2** | **核心工艺参数**（#3 注射压力 + #4 注射速度 + #5 注射时间 + #6 保压压力）| **本算法即将完成** |
| 阶段 2.5 | 保压时间（#8，**P0+ 提升**）| ⏳ 待设计（必须覆盖长保压场景）|
| 阶段 3 | 保压细节（#7 保压速度）| ⏳ 待设计 |
| 阶段 4 | 计量参数（#9~#12）| ⏳ 待设计 |
| 阶段 5 | 松退参数（#13~#15）| ⏳ 待设计 |

### 15.2 设计风格一致性

本设计文档沿用**已完成的算法 #3~#5 同套 16 章结构**，与项目物理化演进路线对齐：

- ✅ **第 1~2 章**：背景与本质定义
- ✅ **第 3 章**：物理推导链 + 公式
- ✅ **第 4~5 章**：3 级兜底 + 保守原则
- ✅ **第 6~7 章**：与原算法对比 + 实施计划
- ✅ **第 8~9 章**：JSON 配置 + 测试用例
- ✅ **第 10~12 章**：风险 + 相关文件 + 后续扩展
- ✅ **第 13~14 章**：局限性诚实声明 + 渐进式物理化演进路径
- ✅ **第 15~16 章**：与项目路线对齐 + 更新日志

### 15.3 物理基础一致性

| 算法 | 主物理依据 | 辅助物理依据 |
|------|-----------|------------|
| **#3 注射压力** | 流变学（黏度 → 阻力 → 压力）| 几何（L/t）|
| **#4 注射速度** | 流变学（黏度 → 流量 → 速度）| 几何（L/t）+ 温度（模温）|
| **#5 注射时间** | 体积守恒（几何下限） + 工艺窗口（钳制）| 材料 × 壁厚 |
| **#6 保压压力**（本文档）| 流变学（保压是注射的延续）| 材料 × 壁厚 × 浇口 × **流道** |

四个算法共同构成注塑工艺参数物理化体系：**注射 → 速度 → 时间 → 保压压力**，物理基础递进。

---

## 16. 更新日志

| 日期 | 版本 | 进度 | 备注 |
|------|------|------|------|
| 2026-07-05 | v1.0 | 算法 #6 保压压力 | ✅ 设计文档完成（半经验三维物理方法：材料 × 壁厚 × 浇口）|
| 2026-07-05 | v1.1 | 引入 runner_factor 第 4 维 | ✅ 流道类别（热流道/冷流道/热转冷）上升为独立维度；枚举升级 + 数据模型 + 助手函数同步 |

---

*最后更新时间：2026-07-05*