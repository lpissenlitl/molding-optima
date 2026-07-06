# 保压速度（hold_velo）物理化设计文档

> 算法 #7 · 保压参数 · 半经验三维物理方法（材料家族黏度等级 × 浇口尺寸 × 机器上限，剪切速率约束驱动）
>
> 文档版本：v1.0
> 设计日期：2026-07-05
> 关联 roadmap：算法清单 #7（阶段 3，P1，与保压压力耦合）
> 前置依赖：算法 #6 保压压力（runner_factor 复用），算法 #5 注射时间（thickness_bucket 复用），算法 #8 保压时间（守恒校验）

---

## 1. 设计背景

### 1.1 现状定位

保压速度（hold_velo）是注塑成型保压阶段螺杆推进熔体的线速度，是保压压力（#6）的"流量上限"约束。它直接影响：

- **补缩流量上限**：保压速度 × 螺杆截面积 = 单位时间补缩体积
- **剪切速率约束**：浇口处流速 = 螺杆速度 × (A_screw / A_gate)，过高的浇口流速会触发材料剪切降解/烧焦
- **机器能力释放**：注塑机 HMI 设定的 max_set_holding_velocity 是机器能力的硬上限
- **与保压压力耦合**：保压压力是流变学驱动力，保压速度是运动学流量上限；两者通过材料黏度隐式耦合

### 1.2 为什么需要改造

当前保压速度采用**固定比例 0.15 × max_hold_velo**：

```python
# initializer.py:1076-1077
hold_velo = max_hold_velo * c_hold.get('hold_velo_ratio', 0.15)
```

**问题诊断**：
1. **材料盲区**：所有材料（PP / PC / PA / PET / POM）共用 0.15，不区分黏度等级
   - 现状：PP 流动性好 → 应该 0.20~0.30 偏高（防补缩不足）
   - 现状：PET 高黏度 → 应该 0.08~0.12 偏低（防剪切过热）
2. **几何盲区**：不区分浇口尺寸与壁厚档
   - 现状：薄壁点浇口（h=0.8mm, A_gate=小）→ 浇口处流速 v_jet = v_screw × (A_screw / A_gate) 极大 → 剪切速率触发临界
   - 现状：厚壁直浇口（h=3.0mm, A_gate=大）→ 流速温和 → 可偏低防飞边
3. **机器能力浪费**：HMI 上限是给定的硬墙，但材料/几何修正后，**机器上限可能远高于物理合理值**
   - 现状：max_hold_velo=200mm/s × 0.15 = 30mm/s（对于 PP 完全合理）
   - 现状：max_hold_velo=200mm/s × 0.15 = 30mm/s（对于 PET 偏高，可能触发剪切降解）
4. **缺乏守恒校验**：保压速度 × 保压时间应该 ≥ 补缩长度（流量守恒），现状无法自检

### 1.3 与已有算法的协同基础

#7 保压速度可与已完成算法共享关键数据：
- **#6 保压压力**：复用 `runner_factor`（保压压力驱动 → 流道压力损失，保压速度同等依赖）
- **#5 注射时间**：复用 `thickness_bucket_thresholds = [1.5, 3.0]mm`（薄/中/厚壁 → 浇口尺寸）
- **#8 保压时间**：复用 `gate_thickness`（thin 0.8 / medium 1.5 / thick 3.0 mm，物理同源）

**正交拆分原则**（已在 #6 文档中确立）：
- 保压压力（#6）：流变学驱动量（Q = ΔP / R_hydraulic）
- 保压时间（#8）：热力学持续时间（浇口凝固时间 + 修正）
- 保压速度（#7）：运动学流量上限（剪切速率约束 + 修正）
- 三者正交互不耦合，分别对应流变学/热力学/运动学维度

---

## 2. 物理意义

### 2.1 保压速度的双重作用

保压速度在物理上同时承担**两个相互矛盾的角色**：

**角色 A：补缩流量上限**（驱动力侧）
- 螺杆以速度 v 推进 → 体积流量 Q = v × A_screw
- Q 越大 → 单位时间补缩越多 → 防凹陷/缩痕
- 应该**尽量快**

**角色 B：剪切速率约束**（阻力侧）
- 浇口处流速 v_jet = v × (A_screw / A_gate)
- 浇口处剪切速率 γ̇ = v_jet / h_gate = v × (A_screw / A_gate) / h_gate
- γ̇ 超过材料临界值 γ̇_critical → 熔体剪切过热/降解
- 应该**尽量慢**

**矛盾统一**：保压速度 = min(防凹陷下界, 剪切降解上界)

### 2.2 物理推导链

```
保压速度定义：v_hold = Q / A_screw
            = (ΔP × h_gate³ × π) / (12 × η × L_gate² × A_gate)  [Poiseuille]
            → 实际由压力和黏度隐式决定

简化：保压速度的工程作用是限制最大流量
    v_hold ≤ γ̇_critical × h_gate × (A_gate / A_screw)  [剪切约束]
    v_hold ≤ max_hold_velo × safety_factor  [机器约束]
    v_hold ≥ Q_min / A_screw  [补缩下限]
```

**核心物理量**：
- γ̇_critical：材料临界剪切速率（PP 10000 s⁻¹, PET 3000 s⁻¹, ...）
- h_gate：浇口间隙（thin 0.8 / medium 1.5 / thick 3.0 mm）
- A_gate：浇口截面积（来自 gate_radius）
- A_screw：螺杆截面积（π × D² / 4）
- max_hold_velo：机器 HMI 设定上限

---

## 3. 三维修正维度

### 3.1 维度 1：材料家族黏度等级（family_velo_ratio）

**物理依据**：高黏度材料（PC/PA/PET）分子链长、缠结密度高，临界剪切速率低；低黏度（PP/PE）流动性好，临界剪切速率高。

| 家族 | velo_ratio | γ̇_critical [s⁻¹] | 物理依据 |
|------|------------|------------------|----------|
| **PP** | 0.30 | 10000 | MFI 高（10~20 g/10min），流动性好，可偏高 |
| **PE** | 0.30 | 10000 | 同 PP，结晶快流动性好 |
| **PS** | 0.25 | 8000 | 流动性中等，脆性需偏低 |
| **ABS** | 0.20 | 6000 | 黏度中等，剪切敏感 |
| **AS** | 0.20 | 6000 | 同 ABS |
| **PMMA** | 0.18 | 5500 | 黏度较高，易剪切发黄 |
| **PA** | 0.15 | 5000 | 高黏度（PA66+GF30 更甚），含水扩散敏感 |
| **POM** | 0.15 | 5000 | 高黏度，易甲醛释放 |
| **PC** | 0.12 | 4000 | 高黏度，剪切降解敏感 |
| **PBT** | 0.12 | 4000 | 同 PC |
| **PET** | 0.10 | 3000 | **高黏度 + 半结晶，剪切降解 + 结晶窗口敏感** |
| **未知 family** | 0.15 | 5000 | 兜底保守值 |

### 3.2 维度 2：浇口尺寸 / 壁厚档（gate_velo_factor）

**物理依据**：浇口间隙 h_gate 越小，相同螺杆速度下浇口处流速越高、剪切速率越大。

```
γ̇ = v_jet / h_gate = v × (A_screw / A_gate) / h_gate
```

- **薄壁（thin, t ≤ 1.5mm）**：典型点浇口，h_gate ≈ 0.8mm，A_gate 小
  - v_jet 极大 → γ̇ 极易超临界 → 速度需偏低
  - 但薄壁冻得快 → 实际补缩时间短 → 偏低也 OK
  - **gate_factor = 0.90**（中位偏低 10%）
- **中壁（medium, 1.5 < t ≤ 3.0mm）**：标准结构件，h_gate ≈ 1.5mm
  - 中位场景
  - **gate_factor = 1.00**（中位不修正）
- **厚壁（thick, t > 3.0mm）**：直浇口/大浇口，h_gate ≈ 3.0mm
  - 流速温和 → 可偏高
  - 厚壁补缩需求高 → 应偏快
  - **gate_factor = 1.10**（偏高 10%）

| bucket | gate_factor | h_gate [mm] | 物理含义 |
|--------|-------------|-------------|----------|
| thin | 0.90 | 0.8 | 浇口薄 → 剪切敏感 → 偏低 |
| medium | 1.00 | 1.5 | 中位 |
| thick | 1.10 | 3.0 | 浇口厚 → 流速温和 → 偏高防凹陷 |

### 3.3 维度 3：机器上限钳制（max_safe_hold_velo_ratio）

**物理依据**：保压阶段螺杆推进速度远低于注射速度（避免剪切过热）。行业共识保压速度通常 ≤ 机器 HMI 上限的 30%。

```
max_safe_hold_velo_ratio = 0.30
hold_velo = min(hold_velo_raw, max_hold_velo × max_safe_hold_velo_ratio)
```

**为什么是 0.30？**
- 注射速度典型：50~100 mm/s（高速填充）
- 保压速度典型：5~30 mm/s（低速补缩，避免剪切过热）
- 比值：保压 / 注射 ≈ 0.10~0.30
- 取 0.30 是行业共识上限（海天/震雄/Fanuc 工艺手册）

**机器类型差异**（未来扩展）：
- 液压机：max_safe = 0.30（典型）
- 全电机：max_safe = 0.40（响应快，可偏高）
- 电动-液压混合：max_safe = 0.35

---

## 4. 推导公式

### 4.1 核心公式

```python
# 三维修正
hold_velo_raw = max_hold_velo × family_velo_ratio[family] × gate_factor[bucket]

# 双钳制保护
hold_velo = min(
    hold_velo_raw,                                              # 物理修正
    max_hold_velo × max_safe_hold_velo_ratio                    # 机器安全上限（30%）
)
```

### 4.2 公式等价性证明（与 #6 / #8 协同）

| 维度 | 保压压力（#6） | 保压速度（#7） | 保压时间（#8） |
|------|--------------|--------------|--------------|
| 物理 | 流变学（P = Q × R） | 运动学（v = Q / A） | 热力学（t = h² / α） |
| 主变量 | 压力 P | 速度 v | 时间 t |
| 流量关系 | Q = ΔP / R | Q = v × A | Q_total = v × t |
| 守恒 | - | - | v × t ≥ replenish_len × A_screw |
| 主导因素 | 材料黏度 | 剪切速率约束 | 浇口凝固时间 |
| 维度数 | 4 维（材料 × 壁厚 × 浇口 × 流道） | **3 维（材料 × 浇口 × 机器上限）** | 5 维（材料 × 壁厚 × 浇口 × 流道 × 模温 + 结晶） |

**关键洞察**：保压速度的"维度数比保压压力少 1（流道）、比保压时间少 2（壁厚、模温、结晶）"，因为：
- 流道对保压速度影响小（保压时流道已凝固，不参与流动）
- 壁厚已通过浇口尺寸隐式表达（薄壁 → 薄浇口）
- 模温/结晶是热力学问题（保压时间已覆盖）

### 4.3 物理守恒检验

**理论**：v × t ≥ replenish_len × A_screw（A_screw 是补缩体积 → 螺杆推进距离的转换系数）

实际上：
- replenish_len 已经是螺杆推进距离（mm）
- v × t 给出的是"如果 v 恒定，t 时间螺杆能走多远"
- 但实际保压过程中，v 早期较高、后期逐渐降低（随凝固加剧）
- 所以 v × t ≥ replenish_len 是 **必要条件**（不满足意味着物理上不可能完成补缩）

**实施位置**：在 smoke test 中作为断言（不作为硬约束），用于算法一致性自检。

---

## 5. 3 级兜底策略

### 5.1 兜底链

| 优先级 | 数据源 | 物理含义 |
|--------|--------|----------|
| **第 1 级** | `Polymer.recommend_hold_velo` 字段 | 制品级精确值（数据库精确值） |
| **第 2 级** | `family_velo_ratio[family]` × `gate_factor[bucket]` | 物理推导（family × bucket 二维查表） |
| **第 3 级** | `default_velo_ratio = 0.15` × `default_gate_factor` | 兜底保守值（未知 family / 缺数据） |

### 5.2 level 字段（用于日志审计）

```python
(level ∈ {'precise', 'family_bucket', 'default'})
```

**审计意义**：
- `precise`：制品级数据已覆盖，直接使用（质量最高）
- `family_bucket`：物理推导（质量中位，推荐长期补充数据升 precise）
- `default`：兜底使用（质量最低，需后续补充数据）

---

## 6. 关键创新：与 #6/#8 的正交拆分

### 6.1 历史痛点：保压参数耦合的"黑盒"问题

原算法（2026-07 之前）的保压压力、保压时间、保压速度通过经验公式混合推导（`_calc_hold_time` 一锅炖），三个参数的物理逻辑纠缠在一起，难以独立优化与替换。

### 6.2 重构原则：保压参数三维正交

| 物理维度 | 算法 | 推导链起点 | 主要数据源 |
|---------|------|----------|----------|
| 流变学（压力） | #6 | 材料黏度等级 | family_hold_ratio × thickness × gate × runner |
| 运动学（速度） | #7（本设计） | 剪切速率约束 | family_velo_ratio × gate × machine_cap |
| 热力学（时间） | #8 | 浇口凝固时间 | freeze_time × gate × runner × mold_temp × cryst |

**优势**：
1. 每个算法独立可优化（替换一个不影响其他）
2. 数据源清晰（每个算法有独立 family 表 + 独立兜底）
3. 守恒可校验（v × t ≥ replenish_len 是必要条件）
4. 渐进式物理化（每个算法可独立升级到更严格的物理推导）

### 6.3 共享数据约定

| 共享字段 | 复用自 | 用途 |
|---------|--------|------|
| `runner_factor` | #6 | 冷流道 → 流道压力损失 → 速度需偏高（但权重小于 #6） |
| `thickness_bucket` | #5 / #6 | 薄/中/厚 → 浇口尺寸 → 速度修正 |
| `gate_thickness[bucket]` | #8 | 物理同源，thin 0.8 / medium 1.5 / thick 3.0 mm |
| `family` | #6 / #8 | 11 family + 兜底 |

**不共享**：
- `hold_pres_ratio`（保压压力专属，不影响速度）
- `hold_time`（保压时间专属，不影响速度推导）
- `mold_temp_factor`（模温影响热力学，不影响运动学）

---

## 7. 算法实施

### 7.1 代码位置

**主调用**：`initializer.py:_derive_process`（保压参数段，#6 之后）

```python
# ========== 保压速度参数 ==========
# 【重构】保压速度 = 材料黏度等级 × 浇口尺寸修正 × 机器上限钳制
# 推导链：剪切速率约束 γ̇ = v × (A_screw / A_gate) / h_gate → 防剪切降解上限
# 数据源：3 级兜底（精确值 / family×bucket 查表 / 默认）
# 物理详见 _dev_refs/2026-07-05-holding-velocity-physics-design.md
family_velo_ratio, velo_level = self._get_family_hold_velo_ratio(family, c_hold)
gate_factor_velo = self._get_gate_factor_for_hold_velo(bucket, c_hold)

hold_velo_raw = max_hold_velo * family_velo_ratio * gate_factor_velo
hold_velo = min(
    hold_velo_raw,
    max_hold_velo * c_hold.get('max_safe_hold_velo_ratio', 0.30),  # 机器安全上限
)

logger.debug(
    f"保压速度: family={family or 'unknown'} (level={velo_level}), "
    f"family_velo_ratio={family_velo_ratio:.3f}, "
    f"bucket={bucket}, gate_factor_velo={gate_factor_velo:.3f}, "
    f"hold_velo_raw={hold_velo_raw:.2f}mm/s → clamp to {max_hold_velo * c_hold.get('max_safe_hold_velo_ratio', 0.30):.2f}mm/s = {hold_velo:.2f}mm/s"
)
```

### 7.2 辅助函数

```python
def _get_family_hold_velo_ratio(
    self, family: str, c_hold: Dict[str, Any]
) -> Tuple[float, str]:
    """
    获取材料保压速度相对比例（3 级兜底）

    优先级：
    1. 第 1 级 - Polymer.recommend_hold_velo_ratio 字段（精确值）
    2. 第 2 级 - family_velo_ratio[family]（大类黏度等级查表）
    3. 第 3 级 - default_velo_ratio（兜底）

    物理依据：
    - 比例反映材料黏度等级 → 临界剪切速率 → 速度上限
    - 高黏度（PC/PA/PET）→ velo_ratio 偏低（防剪切降解）
    - 低黏度（PP/PE）→ velo_ratio 偏高（流动性好）

    Args:
        family: 材料大类（来自 _parse_family）
        c_hold: holding 分组合并系数

    Returns:
        (family_velo_ratio, level) 元组
        level ∈ {'precise', 'family', 'default'}
    """
    # 第 1 级：精确值
    precise_ratio = self.material.get('recommend_hold_velo_ratio')
    if precise_ratio is not None:
        return precise_ratio, 'precise'

    # 第 2 级：按大类查表
    ratio_map = c_hold.get('family_velo_ratio', {})
    if family and family in ratio_map:
        return ratio_map[family], 'family'

    # 第 3 级：默认值（兜底）
    return c_hold.get('default_velo_ratio', 0.15), 'default'


def _get_gate_factor_for_hold_velo(
    self, bucket: str, c_hold: Dict[str, Any]
) -> float:
    """
    获取保压速度场景的浇口尺寸修正因子（3 桶 + 默认）

    物理依据：浇口间隙 h_gate 越小 → 相同螺杆速度下浇口处流速越高 → 剪切速率约束越紧
    - thin 桶（h=0.8mm）→ 浇口薄 → 偏低（防剪切降解）
    - medium 桶（h=1.5mm）→ 中位
    - thick 桶（h=3.0mm）→ 浇口厚 → 偏高（防凹陷）

    Args:
        bucket: 壁厚档（'thin' / 'medium' / 'thick'）
        c_hold: holding 分组合并系数

    Returns:
        gate_factor_velo ∈ {0.90, 1.00, 1.10, 1.00}
    """
    gate_factor_map = c_hold.get('gate_factor_hold_velo', {
        'thin': 0.90,
        'medium': 1.00,
        'thick': 1.10,
    })
    return gate_factor_map.get(bucket, 1.00)
```

### 7.3 数据流

```
mold_info (max_thickness)
    ↓
machine_info (max_set_holding_velocity)
    ↓
material (abbreviation → family)
    ↓
rule_matcher.match() → c_hold (含 family_velo_ratio / gate_factor_hold_velo / max_safe_hold_velo_ratio)
    ↓
_derive_process():
    ├─ #6 保压压力（先算，已落地）
    ├─ #7 保压速度（本设计）
    └─ #8 保压时间（已落地）
    ↓
proc.hold_spd_steps = [hold_velo]  →  后续 _apply_multi_holding 拆分多段
```

---

## 8. 数据源配置

### 8.1 init_rules.json DEFAULT.holding 新增字段

```json
{
  "holding": {
    // ... 已有字段 ...
    "family_velo_ratio": {
      "PP": 0.30, "PE": 0.30,
      "PS": 0.25,
      "ABS": 0.20, "AS": 0.20,
      "PMMA": 0.18,
      "PA": 0.15, "POM": 0.15,
      "PC": 0.12, "PBT": 0.12,
      "PET": 0.10
    },
    "default_velo_ratio": 0.15,
    "gate_factor_hold_velo": {
      "thin": 0.90,
      "medium": 1.00,
      "thick": 1.10
    },
    "max_safe_hold_velo_ratio": 0.30
  }
}
```

### 8.2 rule_matcher.py _BUILTIN_DEFAULTS 同步

同步添加相同字段（与 init_rules.json DEFAULT 保持完全一致），确保 JSON 缺失时仍有兜底。

### 8.3 数据合理性检查

| 场景 | 推导链 | 期望值 | 实际范围 |
|------|--------|--------|----------|
| **PP thin 薄壁点浇口** | 100 × 0.30 × 0.90 = 27.0, 钳到 30 | 27 mm/s | 5~30 mm/s ✓ |
| **ABS medium 标准件** | 100 × 0.20 × 1.00 = 20.0, 钳到 30 | 20 mm/s | 10~25 mm/s ✓ |
| **PC medium 高黏度** | 100 × 0.12 × 1.00 = 12.0, 钳到 30 | 12 mm/s | 5~15 mm/s ✓ |
| **PET thick 长保压** | 100 × 0.10 × 1.10 = 11.0, 钳到 30 | 11 mm/s | 5~15 mm/s ✓ |
| **未知 family 兜底** | 100 × 0.15 × 1.00 = 15.0, 钳到 30 | 15 mm/s | 5~20 mm/s ✓ |
| **极端 max_hold_velo=200** | 200 × 0.15 × 1.00 = 30, 钳到 60 | 30 mm/s | 防止机器能力浪费 ✓ |

---

## 9. 测试用例

### 9.1 场景 A：PET 瓶盖（与 #8 长保压协同）

- max_thickness=5.0, gate_type=直浇口, runner_weight=0
- material=PET, mold_temp=130℃
- max_hold_velo=100

推导链：
- family=PET, bucket=thick
- family_velo_ratio[PET] = 0.10
- gate_factor_hold_velo[thick] = 1.10
- raw = 100 × 0.10 × 1.10 = 11.0 mm/s
- cap = 100 × 0.30 = 30 mm/s
- **hold_velo = 11.0 mm/s** ✓ 符合 PET 长保压场景（10~15 mm/s）

### 9.2 场景 B：PP 薄壁（高流动性，防冻结）

- max_thickness=1.0, gate_type=点浇口
- material=PP
- max_hold_velo=100

推导链：
- family=PP, bucket=thin
- family_velo_ratio[PP] = 0.30
- gate_factor_hold_velo[thin] = 0.90
- raw = 100 × 0.30 × 0.90 = 27.0 mm/s
- cap = 30 mm/s
- **hold_velo = 27.0 mm/s** ✓ PP 流动性好 + 薄壁快冻 → 偏高补缩

### 9.3 场景 C：PC 高黏度（防剪切降解）

- max_thickness=2.0, gate_type=侧浇口
- material=PC
- max_hold_velo=100

推导链：
- family=PC, bucket=medium
- family_velo_ratio[PC] = 0.12
- gate_factor_hold_velo[medium] = 1.00
- raw = 100 × 0.12 × 1.00 = 12.0 mm/s
- cap = 30 mm/s
- **hold_velo = 12.0 mm/s** ✓ PC 高黏度 → 偏低防剪切降解

### 9.4 场景 D：未知材料兜底

- max_thickness=2.0
- material=UNKNOWN_MATERIAL
- max_hold_velo=100

推导链：
- family='', bucket=medium
- family_velo_ratio 不命中 → default_velo_ratio = 0.15
- gate_factor_hold_velo[medium] = 1.00
- raw = 100 × 0.15 × 1.00 = 15.0 mm/s
- cap = 30 mm/s
- **hold_velo = 15.0 mm/s** ✓ 兜底保守值

### 9.5 场景 E：机器能力钳制（max_hold_velo=200）

- max_thickness=2.0
- material=ABS
- max_hold_velo=200

推导链：
- family=ABS, bucket=medium
- family_velo_ratio[ABS] = 0.20
- raw = 200 × 0.20 × 1.00 = 40 mm/s
- cap = 200 × 0.30 = 60 mm/s
- **hold_velo = 40 mm/s** ✓ 物理修正未超 30% 上限（40 < 60）

### 9.6 场景 F：薄壁高黏度极端组合

- max_thickness=1.0, material=PET
- max_hold_velo=100

推导链：
- family=PET, bucket=thin
- raw = 100 × 0.10 × 0.90 = 9.0 mm/s
- cap = 30 mm/s
- **hold_velo = 9.0 mm/s** ✓ PET + 薄壁双重抑制（保守）

### 9.7 守恒检验（与 #8 保压时间协同）

**PET 瓶盖场景**：
- hold_velo = 11.0 mm/s
- hold_time (来自 #8) ≈ 295.48s（2 段 × 147.74s）
- replenish_len（来自 #1）≈ 0.84mm（基于 50g 产品 + 收缩率 0.020 + 密度 0.95）
- 守恒：v × t = 11.0 × 295.48 = 3250 mm >> 0.84mm ✓ 满足
- 物理含义：保压时间大部分是等待浇口冷却凝固，真正补缩时间短（前期），所以 v × t ≫ replenish_len 是合理的（早期 v 满速，后期 v 趋于 0）

### 9.8 smoke test 断言清单

| # | 场景 | 期望 hold_velo [mm/s] | 期望 level |
|---|------|---------------------|-----------|
| 1 | PET 瓶盖 thick + ultra_high | 11.0 | family |
| 2 | PP 薄壁 thin | 27.0 | family |
| 3 | PC 中壁 medium | 12.0 | family |
| 4 | 未知 family 兜底 | 15.0 | default |
| 5 | ABS max_hold_velo=200（钳制未触发） | 40.0 | family |
| 6 | PET + thin 极端组合 | 9.0 | family |
| 7 | 守恒检验：v × t ≫ replenish_len | 通过 | - |

---

## 10. 局限性诚实声明

### 10.1 当前阶段的方法论定位

**半经验三维物理方法**（定性物理正确 + 定量行业共识查表），不是严格物理推导。

具体局限：
1. **gate_factor 简化为 3 桶**：实际浇口间隙与壁厚的物理关系更复杂（不同浇口类型/材料组合下比例不同）
2. **runner_factor 不参与保压速度修正**：保压时流道基本已凝固，影响是次要的
3. **机器类型差异未细分**：全电机/液压机/电动-液压混合的 max_safe 比例未差异化
4. **Poiseuille 流动假设**：实际保压阶段的流动更复杂（非牛顿流体、非稳态）

### 10.2 与 #6 / #8 的一致性局限

| 维度 | #6 保压压力 | #7 保压速度 | #8 保压时间 |
|------|------------|------------|------------|
| 维度数 | 4 | 3 | 5 |
| 主要物理 | 流变学 | 运动学 | 热力学 |
| 物理严格性 | 半经验 | **半经验（依赖工程共识）** | 半经验 |

保压速度的物理严格性比保压压力/保压时间更低，因为：
- 工业实践中**保压速度往往是 HMI 设定上限**，物理推导的可调空间小
- **真实起作用的是压力**（压力反馈控制模式），速度是限速
- 但**速度上限不能拍脑袋**（剪切降解风险），仍需 family 区分

### 10.3 数据缺口

| 字段 | 当前来源 | 数据缺口 |
|------|----------|----------|
| `γ̇_critical[family]` | 行业共识中位值 | 11 family 全部缺精确值 |
| `gate_factor_hold_velo[bucket]` | 物理推导 + 经验 | 3 桶简化（实际更细） |
| `max_safe_hold_velo_ratio` | 行业共识 0.30 | 机器类型细分缺数据 |

### 10.4 渐进式物理化演进路径

**阶段 1（当前）**：半经验三维查表（family × bucket × machine_cap）

**阶段 2（中期）**：
- 引入 Poiseuille 流动显式公式：v_hold = γ̇ × h_gate × A_gate / A_screw
- 需要补全：γ̇_critical[family] 精确值 + gate_radius 字段（已存在于 mold_info）

**阶段 3（长期）**：
- 引入材料黏度-温度-剪切速率的本构方程（Cross-WLF 或 Carreau）
- 与 #6 保压压力真正耦合（v_hold = f(P, η, T) 的反解）
- 机器类型自适应（液压/全电机/混合）

---

## 11. 与 #6 / #8 协同验证

### 11.1 数据一致性

| 检查项 | 期望 | 实际 |
|--------|------|------|
| 复用 `thickness_bucket_thresholds` | [1.5, 3.0] | ✓ 与 #5/#6/#8 一致 |
| 复用 `runner_factor` | 不复用（保压速度对流道不敏感） | 决策：不复用，避免过度耦合 |
| family 表完整性 | 11 family 全部覆盖 | ✓ PP/PE/PS/ABS/AS/PMMA/PA/POM/PC/PBT/PET |
| 兜底策略 | 3 级（precise / family / default） | ✓ 与 #6/#8 一致 |

### 11.2 物理协同

| 协同点 | 物理含义 | 协同方式 |
|--------|---------|----------|
| **守恒校验** | v × t ≥ replenish_len | smoke test 断言 |
| **数据共享** | family / bucket / runner_factor | 通过 c_hold 共享 |
| **量纲一致性** | v [mm/s] × t [s] = 距离 [mm] | 自然成立 |
| **边界兼容** | 默认值（0.15）与现状一致 | 平滑迁移无破坏 |

### 11.3 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| **数据驱动偏差** | family_velo_ratio 偏差导致速度不合理 | level 字段审计 + smoke test 边界断言 |
| **过度工程化** | 3 维公式可能比现状复杂 | 物理约束清晰（剪切速率 + 机器上限） |
| **历史兼容** | 旧数据无 family_velo_ratio 字段 | 兜底 default_velo_ratio = 0.15（与原值一致） |

---

## 12. 后续扩展

### 12.1 短期（1~2 周）

- [ ] smoke test 7 个场景全过
- [ ] 同步 rule_matcher.py _BUILTIN_DEFAULTS
- [ ] 同步 init_rules.json DEFAULT.holding
- [ ] roadmap #7 状态 ⏳ → ✅
- [ ] smoke test 加入守恒校验

### 12.2 中期（1~2 月）

- [ ] 引入 `gate_radius` 字段精确计算 A_gate（替代 bucket 简化）
- [ ] 引入 Poiseuille 流动显式公式
- [ ] 补全 γ̇_critical[family] 实验数据
- [ ] 机器类型细分（液压/全电机/混合）

### 12.3 长期（季度级）

- [ ] 引入 Cross-WLF 本构方程，与 #6 保压压力真正耦合
- [ ] 实测反馈闭环（实际生产数据 → 修正 family_velo_ratio）
- [ ] 与 #8 保压时间协同自适应（v × t 守恒动态调整）

---

## 13. 相关文件

| 文件 | 角色 |
|------|------|
| `process/engines/expert/initializer.py` | 算法主体（_derive_process 保压参数段）|
| `process/engines/expert/expert_rules/init_rules.json` | 规则配置（DEFAULT.holding 新增 4 字段）|
| `process/engines/expert/rule_matcher.py` | _BUILTIN_DEFAULTS 同步 |
| `process/engines/expert/tests/test_hold_velo_smoke.py` | smoke test（待创建，7 断言）|
| `_dev_refs/2026-07-05-holding-velocity-physics-design.md` | 本文档 |
| `_dev_refs/2026-07-05-holding-pressure-physics-design.md` | #6 文档（runner_factor 来源）|
| `_dev_refs/2026-07-05-holding-time-physics-design.md` | #8 文档（gate_thickness + 守恒校验）|
| `_dev_refs/2026-07-04-algorithm-refactor-roadmap.md` | roadmap 同步 |

---

## 14. 更新日志

| 日期 | 进度 | 备注 |
|------|------|------|
| 2026-07-05 | #7 保压速度设计文档 v1.0 | ✅ 本文档。三维半经验物理方法：材料黏度 × 浇口尺寸 × 机器上限。3 级兜底 + 守恒检验。 |

---

*最后更新时间：2026-07-05（#7 保压速度设计文档 v1.0 完稿）*
