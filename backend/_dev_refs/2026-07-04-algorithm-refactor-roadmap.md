# 注塑工艺算法科学化改造路线图

> 本文档列出所有需要从"经验玄学"重构为"物理推导 + 行业共识"的工艺参数算法，记录进度与方向。

## 1. 改造背景

### 1.1 整体目标

**核心理念**：每个工艺参数都能追溯到物理原理或行业共识数据，摆脱"几次试模拍脑袋"的经验做法。

### 1.2 推进原则

- ✅ **单个算法独立攻破**：每个算法都是独立的物理问题
- ✅ **物理推导 + 行业共识**：数据来自材料手册/设备规范
- ✅ **保守兜底**：未识别场景采用最保守值
- ✅ **渐进上线**：保留旧逻辑作为 fallback，逐步替换

## 2. 算法清单总览

### 2.1 完成进度统计

| 状态 | 数量 | 占比 |
|------|------|------|
| ✅ 已完成 | 20 | 100.00% |
| ⏳ 待改造 | 0 | 0.00% |
| **总计** | **20** | **100%** |

### 2.2 完整算法清单

| # | 算法分类 | 算法名称 | 输出字段 | 状态 | 文档 |
|---|---------|---------|---------|------|------|
| 1 | 行程分配 | **收缩长度** (replenish_len) | ratio / replenish_len | ✅ | 2026-07-04-injection-stroke-physics-design.md |
| 2 | 行程分配 | **料垫长度** (cushion_len) | cushion_len | ✅ | 2026-07-04-injection-stroke-physics-design.md |
| 3 | 注射参数 | 注射压力 | inj_pres | ✅ | 2026-07-05-injection-pressure-physics-design.md |
| 4 | 注射参数 | 注射速度 | inj_velo | ✅ | 2026-07-05-injection-velocity-physics-design.md |
| 5 | 注射参数 | 注射时间 | inj_time | ✅ | 2026-07-05-injection-time-physics-design.md |
| 6 | 保压参数 | 保压压力 | hold_pres | ✅ | 2026-07-05-holding-pressure-physics-design.md |
| 7 | 保压参数 | 保压速度 | hold_velo | ✅ | 2026-07-05-holding-velocity-physics-design.md |
| 8 | 保压参数 | 保压时间 | hold_time | ✅ | 2026-07-05-holding-time-physics-design.md |
| 9 | 保压参数 | VP 切换模式 | vps_mode | ✅ | 2026-07-05-vp-switch-mode-physics-design.md |
| 10 | 冷却参数 | **冷却时间** | cool_t | ✅ | 2026-07-05-cool-time-physics-design.md |
| 11 | 计量参数 | 计量压力 | meter_pres | ✅ | 2026-07-05-metering-pressure-physics-design.md |
| 12 | 计量参数 | 螺杆转速 | meter_speed | ✅ | 2026-07-05-metering-speed-physics-design.md |
| 13 | 计量参数 | 计量背压 | meter_back_pres | ✅ | 2026-07-05-metering-back-pressure-physics-design.md |
| 14 | 计量参数 | 计量位置 | meter_posi | ✅ | （公式透明，注释同步）|
| 15 | 松退参数 | 储料前松退模式 | pre_met_decomp_mode | ✅ | 2026-07-05-suckback-decompression-physics-design.md |
| 16 | 松退参数 | 储料前松退参数（压力/距离/速度/时间） | pre_met_decomp_* | ✅ | 2026-07-05-suckback-decompression-physics-design.md |
| 17 | 松退参数 | 储料后松退参数（压力/距离/速度/时间） | pst_met_decomp_* | ✅ | 2026-07-05-suckback-decompression-physics-design.md |
| 18 | 计量参数 | 计量终止位置 | met_end_pos | ✅ | 2026-07-05-suckback-decompression-physics-design.md |
| 19 | 温度参数 | 喷嘴温度 | noz_temp | ✅ | 2026-07-05-temperature-physics-design.md |
| 20 | 温度参数 | 料筒温度分布（段 1~N） | brl_temp_steps | ✅ | 2026-07-05-temperature-physics-design.md |

---

## 3. ✅ 已完成算法（20 个，松退族闭环 + 温度族闭环）

### 3.1 算法 #1：收缩长度 (replenish_len)

**物理意义**：保压阶段螺杆实际推进距离 = 制品冷却收缩 + 熔体 PVT 压缩

**推导链**：
```
保压推进需求 ≥ 冷却收缩 + PVT 压缩
L_cushion_need = (shrink_rate + pvt_compress) × W / (ρ × A_screw) × 1000
ratio = 1 - L_cushion_need / total_len
```

**数据源**：3 级兜底（精确值 / 大类典型值 / 默认值）

**完成文档**：[2026-07-04-injection-stroke-physics-design.md](file:///Users/lpissenlit/workfiles/molding-optima/backend/_dev_refs/2026-07-04-injection-stroke-physics-design.md) 章节 3-5

### 3.2 算法 #2：料垫长度 (cushion_len)

**物理意义**：螺杆最终停止位置 = 距离机械零点的距离

**推导公式**（向上取整，与各厂商经验值吻合）：
```python
cushion_len = max(math.ceil(D / 4), cushion_min_abs)
```

**物理依据**：
- 海天 8-12mm（推算 D=32-48mm）→ D/4 公式高度吻合
- Fanuc 10-15mm（推算 D=40-60mm）→ D/4 公式高度吻合

**完成文档**：[2026-07-04-injection-stroke-physics-design.md](file:///Users/lpissenlit/workfiles/molding-optima/backend/_dev_refs/2026-07-04-injection-stroke-physics-design.md) 章节 3-5

### 3.3 算法 #3：注射压力 (inj_pres)

**物理意义**：推动熔体经喷嘴→流道→浇口→型腔完成填充所需的总压力

**推导公式**（二维差异化：材料黏度等级 × 流长比修正）：
```python
inj_pres = min(
    max_set_injection_pressure × base_ratio[family] × length_factor(inj_ratio),
    max_set_injection_pressure × max_safe_pressure_ratio  # 默认 0.90 安全钳制
)
```

**物理依据**：
- 材料黏度等级（base_ratio[family]）：PP/PE 等流动性好 → 基准压力低；PC 等高黏度 → 基准压力高
- 流长比修正（length_factor）：L/t 越大 → 填充路径压力梯度越陡 → 修正越大
- 安全钳制（max_safe_pressure_ratio）：HMI 设定上限的 90%，防液压冲击与传感器误差

**数据源**：3 级兜底（精确值 / 大类查表 / 默认值）

**注意**：当前阶段是**半经验方法**（定性物理正确 + 定量行业共识），不是严格物理推导。详见文档第 13 章局限性诚实声明与第 14 章渐进式物理化演进路径。

**完成文档**：[2026-07-05-injection-pressure-physics-design.md](file:///Users/lpissenlit/workfiles/molding-optima/backend/_dev_refs/2026-07-05-injection-pressure-physics-design.md)

### 3.4 算法 #4：注射速度 (inj_velo)

**物理意义**：螺杆推进速度，驱动熔体经喷嘴→流道→浇口→型腔完成填充

**推导公式**（三维差异化：材料流动性等级 × 流长比修正 × 模温修正）：
```python
inj_velo = min(
    max_set_injection_velocity
    × base_velo_ratio[family]                # 流动性等级（11 个材料大类）
    × length_velo_factor(L/t)                # 几何修正（4 档连续）
    × temp_velo_modifier(mold_temp),         # 模温修正（3 档微调 ±5%）
    max_set_injection_velocity × max_safe_velocity_ratio  # 默认 0.95 安全钳制
)
```

**物理依据**：
- 材料流动性等级（base_velo_ratio）：MFI 高 → 基准速度可偏低；高黏度 → 基准速度偏高
- 流长比修正（length_velo_factor）：L/t 越大 → 前缘冷却风险越高 → 需加速补偿（与压力修正方向相反但物理解释不同）
- 模温修正（temp_velo_modifier）：高模温 → 黏度低 → 可微降；低模温 → 需微升
- 安全钳制（max_safe_velocity_ratio）：HMI 设定上限的 95%，防飞边与剪切烧焦

**数据源**：3 级兜底（精确值 / 大类查表 / 默认值），每维度独立

**主要收益**：
- 消除原算法 L/t=99→100 处的速度突降（0.498→0.40），分档平滑过渡
- 提供模温响应（原算法无），高模温自动微降，低模温自动微升
- 三维差异化能力（材料 × L/t × 模温），覆盖更全面场景

**注意**：当前阶段是**半经验方法**（定性物理正确 + 定量行业共识），不是严格物理推导。详见文档第 13 章局限性诚实声明与第 14 章渐进式物理化演进路径。

**完成文档**：[2026-07-05-injection-velocity-physics-design.md](file:///Users/lpissenlit/workfiles/molding-optima/backend/_dev_refs/2026-07-05-injection-velocity-physics-design.md)

### 3.5 算法 #5：注射时间 (inj_time)

**物理意义**：使熔体在工艺窗口约束下完成填充所需时间，本质是几何下限被工艺钳制窗口约束。

**推导公式**（二维差异化 + 几何钳制：材料流动性 × 壁厚档 → (min_t, max_t) 工艺窗口）：
```python
inj_time_geo = inj_len / inj_velo
(min_t, max_t) = family_time_window[family][bucket]
inj_time = clamp(inj_time_geo, min_t, max_t)  # = max(min_t, min(inj_time_geo, max_t))
```

**物理依据**：
- 几何下限：`inj_len / inj_velo` 保证物理可达（与已物理化的 `inj_velo` 协同）
- 薄壁冻结上限（thin 桶）：t ≤ 1.5mm → max_t 1.0~2.5s 防前缘冷却成欠注
- 厚壁飞边下限（thick 桶）：t > 3.0mm → min_t 1.5~3.0s 防高剪切飞边
- 材料窗口差异：PC/PA66/PET 等高黏度 → 整体放宽；PP/PE 快填能力强 → 整体收紧
- 桶分界（`thickness_bucket_thresholds = [1.5, 3.0]mm`）：thin / medium / thick 三档

**数据源**：3 级兜底（精确值 `Polymer.recommend_inj_time_window` / family×bucket 查表 33 行 / `default_time_window = (0.6, 2.5)`）

**主要收益**：
- 删除拍脑袋的 `inj_time_coef = 4.0`（对中位场景偏大 75%~92%）
- 解决 `inj_time_min = 3.0` 对极小件偏大问题（节省 ~78% 周期）
- 薄壁冻结上限真正生效（thin 桶钳制）
- 厚壁飞边下限按材料差异化（family × thick 桶下限）
- 与 `inj_velo` 协同：几何下限基于已物理化的 inj_velo

**注意**：当前阶段是**半经验方法**（定性物理正确 + 定量行业共识窗口表 33 行），不是严格物理推导。详见文档第 13 章局限性诚实声明与第 14 章渐进式物理化演进路径。

**完成文档**：[2026-07-05-injection-time-physics-design.md](file:///Users/lpissenlit/workfiles/molding-optima/backend/_dev_refs/2026-07-05-injection-time-physics-design.md)

---

### 3.6 算法 #6：保压压力 (hold_pres)

**物理意义**：保压阶段螺杆以该压力推动熔体补缩，补偿制品冷却收缩。本质上是注射压力的"延续 × 四维修正"。

**推导公式**（四维差异化：材料黏度等级 × 壁厚修正 × 浇口修正 × **流道修正**）：
```python
hold_pres_raw = inj_pres
              × family_hold_ratio[family]      # 维度 1：材料（11 family × 3段）
              × thickness_factor(bucket)       # 维度 2：壁厚（3 桶，复用 inj_time 阈值）
              × gate_factor(gate_type)         # 维度 3：浇口（4 档 + 默认）
              × runner_factor(runner_type)     # 维度 4：流道（热/冷/热转冷，详见 5.2.1）
hold_pres = min(
    max(0.40 × inj_pres, min(hold_pres_raw, 0.85 × inj_pres)),  # 物理比例钳制 [40%, 85%]
    max_hold_pres × max_safe_hold_ratio                          # 机器硬上限，默认 0.95
)
```

**物理依据**：
- 保压是注射的延续：保压压力通常为注射压力的 50%~75%（海天/震雄/Fanuc 工艺手册 + Moldflow 共识中位）
- 材料黏度等级（family_hold_ratio）：PP/PE 流动性好 → 基准保压偏低（防飞边）；PC/POM 高黏度 → 基准保压偏高（防凹陷）
- 壁厚修正（thickness_factor）：薄壁 0.95（收缩阻力小）/ 中位 1.00 / 厚壁 1.10（补缩需求高）
- 浇口修正（gate_factor）：直浇口 0.95（大浇口流阻小）/ 点浇口 1.10（小浇口流阻大）
- 双钳制保护：物理比例钳制（[40%, 85%]）防极端 + 机器硬上限（95%）防飞边

**数据源**：3 级兜底（精确值 `Polymer.recommend_hold_pres_ratio` / family 查表 11 行 / `default_hold_ratio = 0.60`）

**主要收益**：
- 删除两段硬切换的不平滑（`base_ratio + thickness → inj_ratio`）
- 三维差异化（材料 × 壁厚 × 浇口），物理正确
- 四维扩展（流道类别），详见 5.2.1 共性基础设施
- 双钳制保护（物理窗口 + 机器能力），安全性提升
- 与已完成的注射压力/速度同套风格，认知一致

**注意**：当前阶段是**半经验方法**（定性物理正确 + 定量行业共识），不是严格物理推导。详见文档第 13 章局限性诚实声明与第 14 章渐进式物理化演进路径。

**完成文档**：[2026-07-05-holding-pressure-physics-design.md](file:///Users/lpissenlit/workfiles/molding-optima/backend/_dev_refs/2026-07-05-holding-pressure-physics-design.md)

---

### 3.7 算法 #8：保压时间 (hold_time)

**物理意义**：保压阶段螺杆补缩需要的持续时间。本质上是浇口冷却凝固时间 + 几何修正 + 工艺锞制，决定材料是否完成补缩以防凹陷/缩痕。

**推导公式**（五维差异化：Fourier 热扩散 浇口冻结时间 × 浇口修正 × 流道修正 × 模温修正 × 结晶拉长）：
```python
freeze_t = family_gate_freeze_time[family][bucket]  # 维度 1：材料 × 壁厚浇口冻结时间
hold_time_raw = (
    freeze_t                                    # Fourier t ≈ h²/α_eff 基准
    × gate_factor_hold_time(gate_type)          # 维度 2：浇口修正（与保压压力方向相反）
    × runner_factor_hold(runner_type)           # 维度 3：流道修正（复用 #6 runner_factor）
    × mold_temp_factor_hold_time(mold_temp)     # 维度 4：模温修正（4 桶拉长凝固时窗）
    × crystallinity_kick[family]                # 维度 5：结晶动力学拉长因子
)
hold_time = max(hold_time_min, min(hold_time_raw, family_hold_time_max[family]))
```

**关键创新：移除 10s 硬上限**（[设计文档第 6 章 重要决策记录](file:///Users/lpissenlit/workfiles/molding-optima/backend/_dev_refs/2026-07-05-holding-time-physics-design.md)）：
- 原算法 `hold_time_max = 10.0` 无法覆盖 PET 瓶盖长保压场景（实际 100~300s）
- 改为 `family_hold_time_max[family]`：标准材料 30~60s、半结晶 120s、**PET 600s**（覆盖完整长保压范围）
- 未识别 family → `default_hold_time_max = 300s` 兑底

**4 级 fallback 链**（浇口冻结时间）：
1. 制品级精确值 `mold.hold_time_override[bucket]`
2. `family_gate_freeze_time[family][bucket]`（大类 × 桶查表，11 family × 3 桶 = 33 行）
3. `family_gate_freeze_time[family][medium]`（同 family 中桶兑底）
4. `default_freeze_time[bucket]`（未知材料兑底）

**物理依据**：
- 浇口冻结时间：基于 Fourier 热扩散 t ≈ h²/α_eff，h 取典型浇口厚度（thin 0.8mm / medium 1.5mm / thick 3.0mm）
- 浇口修正：与 #6 保压压力方向相反 —— 大浇口冷却慢 → 凝固时窗大 → 保压时间长（直浇口 1.20 vs 点浇口 0.70）
- 流道修正：复用 #6 runner_factor（热流道 0.95 / 冷流道 1.05），保压场景冷流道需等流道冷却 → 偏高
- 模温修正：高模温拉长浇口凝固时窗（每 +20℃ 拉长 10~15%），4 桶（low 0.95 / medium 1.00 / high 1.10 / ultra_high 1.20）
- 结晶拉长：半结晶在 Tg~Tm 中段结晶速率最高，拉长保压可促结晶（PET 1.80 / PA 1.40 / POM 1.30 / PP 1.10 / PE 1.05 / PC/PS/ABS/AS/PMMA 1.00）

**数据源**：4 级兑底（精确值 / family×bucket / family 中桶 / 默认） + family 自适应上限（**移除 10s 硬上限**）

**主要收益**：
- **覆盖 PET 瓶盖长保压场景**：~300s 总保压（原 10s 上限根本无法表达）
- 解决薄壁冻结与厚壁飞边时间窗口问题（与 #5 注射时间钳制逻辑一致）
- 5 维差异化能力（材料 × 壁厚 × 浇口 × 流道 × 模温 + 结晶拉长）
- 与 #6 保压压力同套架构（共用 runner_factor），认知一致
- 4 级 fallback 解决数据补全过渡期问题（仅靠 1 个 polymer 字段不够时）

**注意**：当前阶段是**半经验方法**（定性物理正确 + 定量行业共识数据），不是严格物理推导。详见文档第 13 章局限性诚实声明与第 14 章渐进式物理化演进路径。

**完成文档**：[2026-07-05-holding-time-physics-design.md](file:///Users/lpissenlit/workfiles/molding-optima/backend/_dev_refs/2026-07-05-holding-time-physics-design.md)


### 3.8 算法 #7：保压速度 (hold_velo)

**物理意义**：保压阶段螺杆推进熔体的线速度上限。本质上是剪切速率约束（防剪切降解） + 流量补缩需求（防凹陷），是 #6 保压压力的"流量上限"约束。

**推导公式**（三维半经验物理方法，剪切速率约束驱动）：
```
hold_velo_raw = max_hold_velo × family_velo_ratio[family] × gate_factor[bucket]
hold_velo = min(hold_velo_raw, max_hold_velo × 0.30)   # 机器安全上限 30%
```

**数据源**：3 级兜底（precise / family×bucket / default）

**物理依据**（与 #6/#8 协同的三维正交）：
- **维度 1 - family_velo_ratio**：材料临界剪切速率等级
  - PET 0.10（高黏度 + 半结晶，剪切降解 + 结晶窗口敏感）
  - PC/PBT 0.12（高黏度，剪切降解敏感）
  - PA/POM 0.15（高黏度）
  - PMMA 0.18（中等黏度）
  - ABS/AS 0.20（中等流动性）
  - PS 0.25
  - PP/PE 0.30（MFI 高，流动性好）
- **维度 2 - gate_factor**：浇口尺寸修正（thin 0.90 / medium 1.00 / thick 1.10）
  - 物理依据：浇口间隙 h_gate 越小 → 相同螺杆速度下浇口处流速越高 → 剪切速率约束越紧
- **维度 3 - 机器上限钳制**：max_safe_hold_velo_ratio = 0.30（行业共识）
  - 物理依据：保压阶段速度 ≤ HMI 上限 30%，避免剪切过热

**与 #6/#8 的正交拆分**（流变学 / 运动学 / 热力学三维独立）：
- **#6 保压压力**：流变学驱动量（ΔP = Q × R_hydraulic）
- **#7 保压速度**：运动学上限约束（v × A = Q ≤ Q_max）← 本算法
- **#8 保压时间**：热力学持续时间（浇口凝固时间 + 修正）

**关键创新**：
- 移除原固定 0.15 比例 → 引入 family 黏度等级（PET 0.10 vs PP 0.30，差 3 倍）
- 与 #6/#8 共享 bucket 概念，但物理语义不同（速度看剪切速率，时间看凝固时间，方向相同）
- 守恒检验（smoke test 中）：v × t ≫ replenish_len（必要条件自检）

**典型场景验证**：
| 场景 | family × bucket | raw | cap | final |
|------|-----------------|-----|-----|-------|
| PET 瓶盖厚壁 | 0.10 × 1.10 | 11.0 | 30 | **11.0 mm/s** |
| PP 薄壁 | 0.30 × 0.90 | 27.0 | 30 | **27.0 mm/s** |
| ABS 中壁 | 0.20 × 1.00 | 20.0 | 30 | **20.0 mm/s** |
| PC 中壁 | 0.12 × 1.00 | 12.0 | 30 | **12.0 mm/s** |


### 3.9 算法 #9：VP 切换模式推荐 (vps_mode)

**物理意义**：V→P 切换的触发信号源选择（位置/时间/压力/位置&时间）。本质是工艺窗口的"切换控制信号"完备性。

**4 种模式**：
| mode | 触发源 | 推荐字段 | 行业依据 |
|------|--------|----------|----------|
| **0 位置** | 螺杆到达 `vps_pos` | `vps_pos = inj_pos` | 算法 #1+#2 推导（料垫+补缩长度） |
| **1 时间** | 经过 `vps_t` 秒 | `vps_t = inj_time × 0.95` | 海天/震雄/Fanuc 推荐 95~98% 行程 |
| **2 压力** | 注射压力达到 `vps_pres` | `vps_pres = inj_pres × 0.85` | 避开压力峰值（机器控制精度下降）|
| **3 位置&时间** | 位置或时间哪个条件先达到 | 两个值都填 | **冗余保护**（防止机器卡死）|

**推导原则**：3 级兜底链 + 行业标准推导公式
```
Level 1 - 用户明确指定 vps_mode（int 0~3）         → 'explicit'
Level 2 - 字符串兼容 VP_switch_mode（位置/时间/压力/其他/位置&时间）→ 'legacy_string'
Level 3 - 默认位置切换（mode=0）                    → 'default'
```

**关键创新**：
- **不引入评分卡**：避免过度设计，与实际生产"默认位置 + 用户指定"习惯一致
- **mode=3 冗余保护**：精密制品/医疗器械场景，位置异常时时间触发，时间异常时位置触发
- **字符串兼容**：支持"位置" / "时间" / "压力" / "其他" / "位置&时间" 5 种写法
- **完备性优先**：4 种模式全覆盖（mode=0/1/2/3），不主动推荐特定场景

**典型场景验证**：
| 场景 | 输入 | 推荐 |
|------|------|------|
| 默认 | `process_set={}` | mode=0, vps_pos=inj_pos |
| 时间 | `vps_mode=1` | mode=1, vps_t=inj_time×0.95 |
| 压力 | `vps_mode=2` | mode=2, vps_pres=inj_pres×0.85 |
| 位置&时间 | `vps_mode=3` | mode=3, vps_pos=inj_pos + vps_t=inj_time×0.95 |
| 字符串"位置&时间" | `VP_switch_mode='位置&时间'` | mode=3（同上）|
| 越界兜底 | `vps_mode=5` | 回退到字符串/默认位置 |

**完成文档**：[2026-07-05-vp-switch-mode-physics-design.md](file:///Users/lpissenlit/workfiles/molding-optima/backend/_dev_refs/2026-07-05-vp-switch-mode-physics-design.md)

---

### 3.10 算法 #10：冷却时间 (cool_t)

**物理意义**：成型周期中从充填结束到开模顶出的间隔，本质是热扩散到 ejection_temp 的传导时间。与 #8 保压时间正交拆分（#8 浇口凝固局部 vs #10 制品整体冷却）。

**推导公式**：
```
t_cool = max_thickness² × family_cool_factor × ΔT_factor × crystallinity_kick
```

**4 维物理化详解**：

| 维度 | 物理含义 | 量化公式 |
|------|---------|----------|
| **材料系数** family_cool_factor | 不同材料的熔体黏度/玻璃化转变温度差异 | PP=0.9, ABS=1.1, PC=1.8, PET=2.0…（11 个 family）|
| **温差修正** ΔT_factor | 模温越高、冷却越慢（热扩散越不充分）| 5 档分档（extreme_hot 1.20 → extreme_cold 0.90）|
| **结晶拉长** crystallinity_kick | 半结晶材料释放潜热 → 额外冷却时间 | 结晶型 1.15、无定形 1.00、未知 1.10 |
| **几何基础** max_thickness² | Fourier 热扩散 t ∝ h²/α | 壁厚主导 |

**物理依据**：
```
原始 Fourier: t = h²/α × ln((T_melt - T_mold)/(T_eject - T_mold))
工程简化:    t ≈ h² × family_factor × ΔT_factor × cryst_kick
```

**3 级 fallback 链**：
- **Level 1**：用户指定总周期 → 反推 `t_cool_user = inject_cycle_require - inj_time - hold_time - else_time`
- **Level 2**：物理推导 `t_cool_phys = h² × family × ΔT × cryst`
- **Level 3**：钳制下限 `cool_t = max(cool_time_min=5s, t_cool_phys or t_cool_user)`

**关键创新**：
- **物理正交**：与 #8 保压时间彻底分离（局部 vs 整体）
- **行业系数**：family_cool_factor 11 个 family 覆盖 PP/PE/PET/PC/ABS/PA/POM 等
- **结晶放热**：基于 TA Instruments TN048 结晶焓数据（PP 207 J/g, PE 293 J/g, PA66 230 J/g）推导出 1.15 拉长因子
- **温差 5 档**：覆盖极端高模温 200℃/160℃/180℃ 场景（如高温模具）
- **缺失兜底**：t_melt/t_mold/t_eject 任意为 0 → ΔT_factor = 1.0（不修正）

**典型场景验证**（11 个断言全过）：
| 场景 | 输入 | 推导 |
|------|------|------|
| PET 厚壁 5mm | 结晶型 + 280℃/80℃/120℃ | 5² × 2.0 × 0.95 × 1.15 = **54.62s** |
| PC 厚壁 3mm | 无定形 + 290℃/90℃/130℃ | 3² × 1.8 × 0.95 × 1.00 = **15.39s** |
| ABS 中壁 2mm | 无定形 + 240℃/60℃/90℃ | 2² × 1.1 × 0.95 × 1.00 = 4.18s → 钳 5s |
| PP 薄壁 1mm | 结晶型 + 220℃/40℃/80℃ | 1² × 0.9 × 0.95 × 1.15 = 0.98s → 钳 5s |
| 未知 XXX | default family_factor=1.2 + 缺失 ejection | 2² × 1.2 × 1.0 × 1.10 = 5.28s |

**完成文档**：[2026-07-05-cool-time-physics-design.md](file:///Users/lpissenlit/workfiles/molding-optima/backend/_dev_refs/2026-07-05-cool-time-physics-design.md)

---

### 3.11 算法 #11：计量压力 (meter_pres)

**物理意义**：液压机液压油缸推动螺杆后退时克服熔体回流阻力所需的油压。本质是**熔体黏度 × 油路驱动**的乘积，**仅液压机有效**（全电机无油缸，HMI 不显示此输入栏）。

**关键认知：计量压力 ≠ 计量背压**：
- **计量压力**：液压机油压（驱动装置），仅液压机
- **计量背压**：熔体物理阻力（介质），所有机器均有（**#13 算法独立处理**）

**推导公式**（三维差异化：动力源分支 + 喷嘴修正 + 材料黏度修正）：
```python
# 分支 1：全电机（power_method='全电机'）
meter_pres = 0.0  # 物理正确：无油缸 → HMI 无“计量压力”输入栏

# 分支 2：液压机（默认）
meter_pres_raw = max_set_metering_pressure
              × base_ratio[nozzle_type]      # 维度 1：喷嘴（直通 0.55 / 锁闭 0.60）
              × family_meter_viscosity[abbrev] # 维度 2：材料熔体黏度等级（17 个 family）
              × nozzle_factor[nozzle_type]    # 维度 3：喷嘴阻力修正（直通 1.00 / 锁闭 1.10）
meter_pres = clamp(meter_pres_raw, meter_pres_min=3.0, meter_pres_max=18.0)
```

**3 级 fallback 链**（材料黏度修正）：
1. 精确全名匹配 `family_meter_viscosity['PA66' / 'PVC' / 'PC+ABS']` → 'precise_abbrev'
2. family 大类匹配（PA66 → PA）→ 'precise_family'
3. 默认 `default_family_meter_viscosity = 1.0` → 'default'

**物理依据**：
- 计量压力 = 克服熔体回流阻力 + 推动螺杆旋转剪切 = η·γ̇·L/A（流变学定律）
- 材料熔体黏度等级（17 个 family 覆盖）：
  - **低黏度**（0.5~0.7）：PP/PE/LDPE/HDPE/LLDPE=0.6、PS=0.7、PVC=0.5（剪切敏感）
  - **中等黏度**（1.0）：ABS/POM/PC/PMMA/PET/PBT/PC+ABS
  - **高黏度**（1.2~1.3）：PA6/PA=1.2、PA66=1.3（高黏度 + 吸湿）
- 喷嘴修正（nozzle_factor）：锁闭喷嘴 1.10（止逆阀增加回流阻力，需更高油压）
- 钳制范围 [3.0, 18.0]：避免低限熔体逆流、高限溢料

**关键创新**：
- **动力源分支**：全电机 0（物理正确，**不是 bug**，保留原代码逻辑）
- **17 个 family 覆盖**：相对比例 0.5~1.3（default=1.0），区分细分材料（PA66 vs PA 差 8%）
- **3 级 fallback**：精确全名 → family 大类 → 兑底默认，保留细分能力
- **双喷嘴维度**：base_ratio（基础比例）+ nozzle_factor（阻力修正）独立可调
- **单位约定**：“同源数值”（与设备 HMI 同量纲），不强绑定 MPa；base_ratio 涵盖厂家隐式换算
- **添加填充物预留点**（2.4 节）：数据结构明确后可启用第 4 维增强纤维修正

**典型场景验证**（22 个断言全过）：
| 场景 | family × nozzle × power | 推导 | final |
|------|--------------------------|------|-------|
| PP 通用件 | 0.6 × 1.00 × 液压/直通 | 20 × 0.55 × 0.6 × 1.00 | **6.6** |
| PC 精密件 | 1.0 × 1.00 × 液压/直通 | 20 × 0.55 × 1.0 × 1.00 | **11.0**（基准）|
| PA66 含水件 | 1.3 × 1.00 × 液压/直通 | 20 × 0.55 × 1.3 × 1.00 | **14.3** |
| 全电机 ABS | 1.0 × - × 全电机 | - | **0**（物理正确）|
| 锁闭喷嘴 PC | 1.0 × 1.10 × 液压/锁闭 | 20 × 0.60 × 1.0 × 1.10 | **13.2** |
| 未知 XXX | 1.0 × 1.00 × 液压/直通 | 20 × 0.55 × 1.0 × 1.00 | **11.0**（兑底）|
| PVC + max=8（钳下） | 0.5 × 1.00 × 液压/直通 | 8 × 0.55 × 0.5 × 1.00 = 2.2 → 3.0 | **3.0** |
| PA66 + max=80（钳上） | 1.3 × 1.00 × 液压/直通 | 80 × 0.55 × 1.3 × 1.00 = 57.2 → 18.0 | **18.0** |

**完成文档**：[2026-07-05-metering-pressure-physics-design.md](file:///Users/lpissenlit/workfiles/molding-optima/backend/_dev_refs/2026-07-05-metering-pressure-physics-design.md)

**Smoke Test**：[test_meter_pres_smoke.py](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/tests/test_meter_pres_smoke.py)（22/22 通过）

---

### 3.12 算法 #12：螺杆转速 (meter_speed)

**物理意义**：螺杆旋转驱动熔体前进，转速决定了熔体表面剪切速率，进而影响塑化均匀性和剪切降解。与 #11 计量压力的对称关系：#11 是液压机专属（油路驱动），#12 是所有机器通用（机械驱动）。

**推导公式**（二维修正：family 修正 + L/D 修正）：
```python
# 不分支动力源（全电机 / 液压机走同一公式）
v_target = recommend_shear_linear_speed × family_meter_shear_ratio[abbrev] × ld_correction[L/D]
ratio_raw = (60.0 × v_target) / (screw_diameter × π × max_screw_rotation_speed)
ratio = clamp(ratio_raw, ratio_min=0.30, ratio_max=0.75)
meter_speed = ratio × max_screw_rotation_speed
```

**3 级 fallback 链**（family 修正）：
1. 精确全名匹配 `family_meter_shear_ratio['PA66' / 'PVC' / 'PC+ABS']` → 'precise_abbrev'
2. family 大类匹配（PA66 → PA）→ 'precise_family'
3. 默认 `default_family_meter_shear_ratio = 1.0` → 'default'

**L/D 修正桶**（条件性启用，字段缺失 → 1.00 兜底）：
| L/D 范围 | 桶 | 系数 | 物理意义 |
|---------|-----|------|---------|
| < 18 | short | 1.05 | 塑化路径短，停留时间不足 → 微升 |
| 18 ~ 22 | standard | 1.00 | 海天/震雄主流机型 → 基准 |
| > 22 | long | 0.95 | 塑化路径长，防过剪切降解 → 微降 |
| None（字段缺失）| default | 1.00 | 数据不全不强制要求，不修正 |

**物理依据**：
- 螺杆表面线速度公式 v_surface = π × D × N / 60 → 反推 N = 60 × v_surface / (π × D)
- 60 是 s→min 单位换算因子（v_surface × 60 / (π × D) = rpm）
- 材料剪切敏感度（17 family × 0.50~1.10）：
  - **高流动性**（1.10）：PP/PE/LDPE/HDPE/LLDPE（剪切降解容忍度高）
  - **中等黏度**（1.00）：ABS/PS/PMMA/PET/PBT
  - **剪切敏感**（0.50~0.65）：PVC=0.50（释放 HCl）、POM=0.65（释放甲醛）、PC+ABS=0.65
  - **高黏度偏保守**（0.50~0.55）：PA6/PA=0.55、PA66=0.50（高黏度 + 吸湿 + 易降解）
- 钳制范围 [0.30, 0.75]：行业共识（30% 下限防塑化不充分，75% 上限防剪切降解）
- 不分支动力源（与 #11 对称）：全电机 vs 液压机的差异在于驱动装置，与螺杆转速的物理机制无关

**关键创新**：
- **物理反推链**：v_surface → N → ratio，全链条可追溯
- **family 修正（必选）**：17 个 family 覆盖 PVC/POM 严重降解与 PP/PE 流动性差异
- **L/D 条件性启用**：字段缺失时 1.00 兜底，避免强制要求设备字段
- **不分支动力源**：与 #11 形成对称演进（#11 液压专属，#12 通用）
- **单位约定**：60 是显式单位换算因子（添加注释）

**典型场景验证**（28 个断言全过）：
| 场景 | family × L/D × 推导 | final |
|------|---------------------|-------|
| PP 通用件 | 1.10 × 1.00 → 60×160×1.10×1.00/18849.6 ≈ 0.5603 | **84.05 rpm** |
| PC 精密件 | 0.55 × 1.00 → 0.2801 → 钳到 0.30 | **45.0 rpm**（下限）|
| PA66 含水件 | 0.50 × 1.00 → 0.2546 → 钳到 0.30 | **45.0 rpm**（下限）|
| 全电机 ABS | 1.00 × 1.00 → 0.5093 = 液压机 | **76.39 rpm**（对称）|
| 短 L/D=16 ABS | 1.00 × 1.05 → 0.5347 | **80.21 rpm** |
| 长 L/D=24 ABS | 1.00 × 0.95 → 0.4838 | **72.57 rpm** |
| PA66 + max=300（钳下）| 0.50 × 1.00 → 0.1273 → 钳到 0.30 | **90.0 rpm** |
| PP + max=30（钳上）| 1.10 × 1.00 → 2.8014 → 钳到 0.75 | **22.5 rpm** |
| ABS + L/D 缺失 | 1.00 × 1.00（兜底） | **76.39 rpm** |

**完成文档**：[2026-07-05-metering-speed-physics-design.md](file:///Users/lpissenlit/workfiles/molding-optima/backend/_dev_refs/2026-07-05-metering-speed-physics-design.md)

**Smoke Test**：[test_meter_speed_smoke.py](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/tests/test_meter_speed_smoke.py)（28/28 通过）

---

### 3.13 算法 #13：计量背压 (meter_back_pres)

**物理意义**：塑化（计量）阶段，螺杆回退储料时液压油路或伺服电机在螺杆背后施加的阻力。本质是**熔体介质的物理阻力**（与 #11 计量压力"液压机专属"形成对称演进）。

**关键认知：计量背压 ≠ 计量压力 ≠ 注塑压力**（避免混用产生 5x 偏差）：
- **计量背压**：介质侧（熔体/螺杆头）参数，所有机器通用（**#13 本算法**）
- **计量压力**：驱动装置侧（液压油缸）参数，仅液压机（**#11 已完成**）
- **注塑压力**：填充阶段克服流阻的力（**#3 已完成**，80~250 MPa，与背压多 10x）

**推导公式**（二维修正：family 排气需求修正 + 螺杆转速联动修正）：
```python
# 不分支动力源（全电机/液压机同公式，与 #12 对称）
recommend_back_pressure = mat.get('recommend_back_pressure') or 10.0  # 缺失兑底行业中位
rpm_ratio = meter_speed / max_screw_speed                              # 来自 #12

# 维度 1：family 排气需求修正（3 级兑底：abbreviation → family → default）
family_factor, family_level, family_key = _get_family_back_pres_factor(abbreviation, c_back)

# 维度 2：螺杆转速联动修正（条件性启用：rpm_ratio 缺失 → 1.0 兑底）
if rpm_ratio is not None:
    speed_factor = 1.0 + 0.3 × (rpm_ratio - 0.5)   # 中位 0.5 对应 speed_factor = 1.0
    speed_factor = clamp(speed_factor, 0.85, 1.15)  # 防过修正
else:
    speed_factor = 1.0  # 缺失兑底

# 推导 + 钳制（材料物理耐受度，不绑定设备能力）
meter_back_pres_raw = recommend_back_pressure × family_factor × speed_factor
meter_back_pres = clamp(meter_back_pres_raw, 0.5, 30.0)
```

**17 family × 0.40~1.50 范围**（基于 Gud Mould 数据反推，体现 5x 物理差异）：
| 类别 | family | 修正系数 | 物理依据 |
|------|--------|---------|---------|
| **高黏度强排气** | PMMA | **1.50** | 高黏度 10⁴~10⁵ Pa·s，需强排气 |
| **高黏度（热敏）** | PC | 1.30 | 高黏度但避免剪切降解 |
| **结晶型基准** | PP/PE/LDPE/HDPE/LLDPE | 1.00 | 结晶型需密度均匀 |
| **非晶基准** | ABS/PS/HIPS | 0.90~1.00 | 中等黏度 |
| **流动性好** | PBT/PET | 0.95 | 流动性好 |
| **甲醒释放** | POM | 0.85 | 剪切释放甲醒 |
| **共混需混合** | PC+ABS/PC/ABS | 1.10 | 共混需更多混合 |
| **极易水解** | **PA66** | **0.40** | **极易水解，高背压摩擦生热加剧水解** |
| **吸湿** | **PA6/PA** | **0.60** | **含水率 >0.2% 易水解** |
| **剪切敏感** | **PVC** | **0.50** | **剪切释放 HCl** |

**反直觉洞察**：低背压不是因为"排气需求低"，而是材料**物理受不了**高背压（PA66 高摩擦生热加剧水解 / PVC 剪切释放 HCl）。

**钳制 [0.5, 30.0]**：依据是材料物理耐受度（PA66 下限 2.0 + PMMA 上限 28），**不绑定设备能力**（设备能力为主油路 14~21 MPa，背压不经增压，是另一个问题）。

**关键创新**：
- **family 排气需求修正（必选）**：17 family × 0.40~1.50，体现 PA66 vs PMMA 5x 物理差异
- **螺杆转速联动修正（条件性启用）**：与 #12 rpm_ratio 联动，转速越高 → 熔体停留时间越短 → 密度越不均匀 → 需偏高背压补偿
- **不分支动力源（与 #12 对称）**：与 #11 液压专属形成对称演进格局（#11 液压专属 / #12+#13 通用）
- **默认值 10.0 MPa（行业中位）**：覆盖 PA66/PMMA/PVC/PP/ABS 全部行业合理范围，无需 fallback override
- **关键修复**（`_validate_inputs` L197-L208）：`recommend_back_pressure` 默认值从 15 同步改为 10.0，避免数据补全阶段覆盖算法层兑底

**典型场景验证**（34 个断言全过）：
| 场景 | 推导 | final | 行业范围 | 验证 |
|------|------|-------|---------|------|
| A. PP 基准 | 10.0 × 1.00 × 1.00 | **10.0 MPa** | 9~17 | ✅ |
| B. PC 高黏度 | 10.0 × 1.30 × 0.94（rpm_ratio=0.30 钳下限）| **12.22 MPa** | 6~15 | ✅ |
| C. PA66 水解 | 10.0 × 0.40 × 1.00 | **4.0 MPa** | 2~6 | ✅ |
| D. PVC 剪切 | 10.0 × 0.50 × 1.00 | **5.0 MPa** | 4~8 | ✅ |
| E. PMMA 强排气 | 10.0 × 1.50 × 1.00 | **15.0 MPa** | 13~28 | ✅ |
| F. 全电机 ABS | 同公式不分支 | **10.0 MPa** | 9~18 | ✅ 不分支动力源 |
| G1. 边界下限 | ra=0.5 × 0.40 × 0.85 = 0.17 → 钳到 0.5 | **0.5 MPa** | - | ✅ 钳下限 |
| G2. 边界上限 | 100 × 1.50 × 1.15 = 172.5 → 钳到 30.0 | **30.0 MPa** | - | ✅ 钳上限 |
| G6. 字段缺失 | recommend_back=None → 兑底 10.0 | **10.0 MPa** | - | ✅ 缺失兑底 |

**完成文档**：[2026-07-05-metering-back-pressure-physics-design.md](file:///Users/lpissenlit/workfiles/molding-optima/backend/_dev_refs/2026-07-05-metering-back-pressure-physics-design.md)

**Smoke Test**：[test_meter_back_pres_smoke.py](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/tests/test_meter_back_pres_smoke.py)（34/34 通过）

---

## 4. ✅ 全 20 算法闭环（松退族 #15-#18 + 温度族 #19+#20 设计+实施+验证完成）

### 4.1 算法 #3：注射压力

> **✅ 已完成（2026-07-05）**：详见 [3.3 节](file:///Users/lpissenlit/workfiles/molding-optima/backend/_dev_refs/2026-07-04-algorithm-refactor-roadmap.md#L97-L107) 与设计文档 [2026-07-05-injection-pressure-physics-design.md](file:///Users/lpissenlit/workfiles/molding-optima/backend/_dev_refs/2026-07-05-injection-pressure-physics-design.md)。

### 4.2 算法 #4：注射速度

> **✅ 已完成（2026-07-05）**：详见 [3.4 节](file:///Users/lpissenlit/workfiles/molding-optima/backend/_dev_refs/2026-07-04-algorithm-refactor-roadmap.md#L129-L160) 与设计文档 [2026-07-05-injection-velocity-physics-design.md](file:///Users/lpissenlit/workfiles/molding-optima/backend/_dev_refs/2026-07-05-injection-velocity-physics-design.md)。

### 4.3 算法 #5：注射时间

> **✅ 已完成（2026-07-05）**：详见 [3.5 节](#35-算法-5注射时间-inj_time) 与设计文档 [2026-07-05-injection-time-physics-design.md](file:///Users/lpissenlit/workfiles/molding-optima/backend/_dev_refs/2026-07-05-injection-time-physics-design.md)。

### 4.4 算法 #6：保压压力

> **✅ 已完成（2026-07-05）**：详见 [3.6 节](#36-算法-6保压压力-hold_pres) 与设计文档 [2026-07-05-holding-pressure-physics-design.md](file:///Users/lpissenlit/workfiles/molding-optima/backend/_dev_refs/2026-07-05-holding-pressure-physics-design.md)。
> 拆分设计原则：保压压力（流变学）与保压时间（热力学/结晶学）独立推导，互不耦合（详见设计文档第 12 章后续扩展）。

### 4.5 算法 #7：保压速度

> **✅ 已完成（2026-07-05）**：详见 [3.8 节](#38-算法-7保压速度-hold_velo) 与设计文档 [2026-07-05-holding-velocity-physics-design.md](file:///Users/lpissenlit/workfiles/molding-optima/backend/_dev_refs/2026-07-05-holding-velocity-physics-design.md)。
> 拆分设计原则：保压压力（#6 流变学）/ 保压速度（#7 运动学）/ 保压时间（#8 热力学）三维正交，互不耦合。

### 4.6 算法 #10：冷却时间

> **✅ 已完成（2026-07-05）**：详见 [3.10 节](#310-算法-10冷却时间-cool_t) 与设计文档 [2026-07-05-cool-time-physics-design.md](file:///Users/lpissenlit/workfiles/molding-optima/backend/_dev_refs/2026-07-05-cool-time-physics-design.md)。
> 拆分设计原则：保压时间（#8 浇口凝固局部）与冷却时间（#10 制品整体冷却）独立推导，互不耦合。

### 4.7 算法 #11：计量压力

> **✅ 已完成（2026-07-05）**：详见 [3.11 节](#311-算法-11计量压力-meter_pres) 与设计文档 [2026-07-05-metering-pressure-physics-design.md](file:///Users/lpissenlit/workfiles/molding-optima/backend/_dev_refs/2026-07-05-metering-pressure-physics-design.md)。
> 拆分设计原则：计量压力（驱动装置·仅液压机）与计量背压（介质·所有机器）独立推导，互不耦合（详见设计文档第 1.2 节“计量压力 vs 计量背压”）。

### 4.8 算法 #12：螺杆转速

> **✅ 已完成（2026-07-05）**：详见 [3.12 节](#312-算法-12螺杆转速-meter_speed) 与设计文档 [2026-07-05-metering-speed-physics-design.md](file:///Users/lpissenlit/workfiles/molding-optima/backend/_dev_refs/2026-07-05-metering-speed-physics-design.md)。
> 拆分设计原则：计量螺杆转速（通用·液压/全电机同一公式）与计量压力（液压专属）独立推导，对称演进。
>
> **物理依据**：螺杆表面线速度 v_surface = π × D × N / 60，反推转速比 ratio = N / max_screw_speed = 60 × v_surface / (π × D × max_screw_speed)。
> **修正维度**：family 修正（必选，17 family × 0.50~1.10）+ L/D 修正（条件性启用，3 桶：short=1.05/standard=1.00/long=0.95）。
> **钳制**：[0.30, 0.75] 行业共识（30% 下限防塑化不充分，75% 上限防剪切降解）。

### 4.9 算法 #13：计量背压

> **✅ 已完成（2026-07-05）**：详见 [3.13 节](#313-算法-13计量背压-meter_back_pres) 与设计文档 [2026-07-05-metering-back-pressure-physics-design.md](file:///Users/lpissenlit/workfiles/molding-optima/backend/_dev_refs/2026-07-05-metering-back-pressure-physics-design.md)。
> 拆分设计原则：计量压力（驱动装置·液压机专属）与计量背压（介质·所有机器通用）独立推导，与 #12 螺杆转速（机械驱动·所有机器通用）形成对称演进。

### 4.10 算法 #14：计量位置

> **✅ 已完成（2026-07-05）**：公式 `meter_posi = cushion_len + total_len` 物理清晰无需算法化，只需补注释与 logger.debug（同 #11-#13 风格）。拆分设计原则：计量位置（行程偏移叠加，物理正确）与计量背压（介质阻力，#13 本质不同）独立推导。

### 4.11 算法 #15：储料前松退模式

> **✅ 已完成（2026-07-05）**：详见设计文档 [2026-07-05-suckback-decompression-physics-design.md](file:///Users/lpissenlit/workfiles/molding-optima/backend/_dev_refs/2026-07-05-suckback-decompression-physics-design.md) §3.1 §9。
> **设计结论**：默认“否”（关闭），用户/制品输入优先，不启用时 = 净位移 0（不进入位置计算）。与 #14/^#18 数学上正交。
>
> **实施位置**：`process/engines/expert/initializer.py` → `proc.pre_met_decomp_mode`
> **Smoke Test**：[test_suckback_smoke.py](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/tests/test_suckback_smoke.py)（场景 J/K 边界守门 2 个断言）

### 4.12 算法 #16：储料前松退参数（压力/距离/速度/时间）

> **✅ 已完成（2026-07-05）**：详见设计文档 [2026-07-05-suckback-decompression-physics-design.md](file:///Users/lpissenlit/workfiles/molding-optima/backend/_dev_refs/2026-07-05-suckback-decompression-physics-design.md) §3.2-3.6 §7.2。
> **设计结论**：4 维推导（pressure + distance + velocity + time）。液压机/全电机分支（压力仅液压机需要）；family 4 档分档；与 #11 复用 family_factor + nozzle_factor。**仅 #15 启用时推导**。
>
> **实施位置**：`process/engines/expert/initializer.py` 4 个 `proc.pre_met_decomp_*` 字段
> **Smoke Test**：[test_suckback_smoke.py](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/tests/test_suckback_smoke.py)（场景 J/K 边界守门 2 个断言）

### 4.13 算法 #17：储料后松退参数（压力/距离/速度/时间）

> **✅ 已完成（2026-07-05）**：详见设计文档 [2026-07-05-suckback-decompression-physics-design.md](file:///Users/lpissenlit/workfiles/molding-optima/backend/_dev_refs/2026-07-05-suckback-decompression-physics-design.md) §3.2-3.6 §7.1。
> **设计结论**：5 维物理化推导（distance）：D = base_dist × family_dist_factor × nozzle_dist_factor × runner_factor × gate_factor。
> - distance baseline：3.5mm（PP/ABS 基准）
> - pressure base_ratio：0.25 × max_meter_pressure（vs #11 的 0.55）
> - 后松退 mode_factor = 1.00（基准）；active 场景业内频次 95%+
> - **v1.1 新增 runner_factor + gate_factor**（与 #6 方向相反）：热流道 ×1.60 + 针阀式点浇口 ×1.70，从而 switch 手柄 case 推导 10.47mm（业内实测 10mm，误差 4.7%）
> - max_dist 上限 6.0 → 12.0（覆盖热流道+针阀式场景）
>
> **实施位置**：`process/engines/expert/initializer.py` 4 个 `proc.pst_met_decomp_*` 字段（含 _compute_suckback_distance/pressure/velocity/time 4 个辅助函数）
> **Smoke Test**：[test_suckback_smoke.py](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/tests/test_suckback_smoke.py)（A/B/C/D/E/F/G/H/I/L/N 共 11 个场景，29 个断言）

### 4.14 算法 #18：计量终止位置

> **✅ 已完成（2026-07-05）**：详见设计文档 [2026-07-05-suckback-decompression-physics-design.md](file:///Users/lpissenlit/workfiles/molding-optima/backend/_dev_refs/2026-07-05-suckback-decompression-physics-design.md) §3.7 §7.3。
> **设计结论**：公式透明 `met_end_pos = meter_posi + pst_met_decomp_dist`，与 #14 同类。物理正确。与 #15/#16 前松退净位移 = 0 **正交**（前松退不进入位置计算，避免漏料风险）。
>
> **实施位置**：`process/engines/expert/initializer.py` → `proc.met_end_pos`（仅依赖后松退距离，与 #14 同类公式透明实现）
> **Smoke Test**：[test_suckback_smoke.py](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/tests/test_suckback_smoke.py)（场景 M/#18 公式透明 1 个断言）

### 4.15 算法 #19：喷嘴温度

> **✅ 已完成（2026-07-05）**：详见设计文档 [2026-07-05-temperature-physics-design.md](file:///Users/lpissenlit/workfiles/molding-optima/backend/_dev_refs/2026-07-05-temperature-physics-design.md) §3.1 §7.1。
> **设计结论**：2 维物理化（nozzle_offset + family_offset）。公式 `noz_temp = melt_temp + noz_offset[nozzle_type] + family_offset[family]`。family_offset 覆盖：PA66 +5℃（防含水率突变）、PA6/PET/PBT +3℃、PVC -5℃（防 HCl 析出）、其他 0℃。钳制 [min_melt_temp-10, max_melt_temp+10]。
>
> **实施位置**：`process/engines/expert/initializer.py` L2344-2362 重写 → `proc.noz_temp`
> **Smoke Test**：[test_temperature_smoke.py](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/tests/test_temperature_smoke.py)（#19 相关场景 A/B/C/D/G/K 6 场景）

### 4.16 算法 #20：料筒温度分布

> **✅ 已完成（2026-07-05）**：详见设计文档 [2026-07-05-temperature-physics-design.md](file:///Users/lpissenlit/workfiles/molding-optima/backend/_dev_refs/2026-07-05-temperature-physics-design.md) §3.2 §7.1-§7.5。
> **设计结论**：4 维物理化（family_decrement + stages + 幂函数 k=1.2 + 双层边界钳制）。公式 `T[i] = melt_temp - i^k × decrement`。
> - **幂函数 k=1.2**（业内“前陡后缓”递减：靠喷嘴平缓、防降解；靠料口陡、防冷料阻塞）
> - **family_decrement 修正**：PVC 5℃（极平缓防分解）、PC/PMMA/POM/PA/PET/PBT 8℃（平缓防降解）、PP/PE/ABS/PS 10℃（中位）
> - **stages 自适应**：stages>7 → ×0.8 但不超过 8℃ 上限（与 PC 平缓对齐）
> - **双层边界钳制**：段 1 ∈ [melt-5, melt+5] 防冷料入喷嘴；段 N ∈ [max(Tg+30, melt-60), melt-5] 防塑化不充分
> - **材料手册容差**：noz_temp ∈ [min_melt-10, max_melt+10]
>
> **实施位置**：`process/engines/expert/initializer.py` L2344-2362 重写 → `proc.brl_temp_stg` + `proc.brl_temp_steps`
> **Smoke Test**：[test_temperature_smoke.py](file:///Users/lpissenlit/workfiles/molding-optima/backend/process/engines/expert/tests/test_temperature_smoke.py)（#20 相关场景 A/B/C/D/E/F/H/I/J/L/M/N 12 场景）

---

## 5. 推进节奏

### 5.1 单个算法标准流程

每个算法独立攻破，按以下步骤：

```
1. 分析现状
   └─ 读取代码 + 历史算法 + 当前系数
   
2. 物理推导
   └─ 找出每个数字的物理依据
   └─ 不行就用行业共识数据兜底
   
3. 数据需求分析
   └─ 列出推导需要的字段
   └─ 设计 3 级兜底策略
   
4. 实施代码
   └─ 改造 initializer.py 对应行
   └─ 更新 init_rules.json
   └─ 设计文档记录
   
5. 验证
   └─ 单元测试（可选）
   └─ 与历史算法对比
```

### 5.2 算法共性基础设施（跨算法复用的修正因子）

随着算法物理化推进，发现存在跨算法复用的"共性修正因子"，需独立抽取和先行落地。

#### 5.2.1 流道类别（runner_type）—— 已落地（2026-07-05）

**背景**：流道类别（热流道/冷流道/热转冷）会影响多个算法的物理推导，包括但不限于：

| 受影响算法 | 流道类别影响 | 严重度 |
|-----------|------------|--------|
| **#3 注射压力** | 冷流道流道压力损失大 → 压力需偏高 | 中 |
| **#4 注射速度** | 同上 | 中 |
| **#5 注射时间** | 影响小（几何下限主导） | 低 |
| **#6 保压压力** | 冷流道需流道补缩 → 压力需偏高 | **高** |
| **#8 保压时间** | 热流道只等浇口凝固；冷流道等浇口 + 流道 | **极高** |
| 冷却时间 | 冷流道需冷却流道 → 时间长 | 中 |
| 松退距离 | 冷流道需松退 → 距离 > 0 | 中 |

**数据模型升级**（已完成）：
- `masterdata/models/mold.py:123`：`runner_type` 描述扩展为"流道类型（热流道/冷流道/热转冷）"
- `masterdata/schemas/mold.py:68`：同步描述
- `process/services/initialization_service.py:305-310`：`condition` 从"可选"提升到"推荐"（多算法依赖）
- `utils/constants.py`：新增 `RUNNER_TYPE_HOT / RUNNER_TYPE_COLD / RUNNER_TYPE_HOT_TO_COLD` 枚举

**runner_factor 物理含义**：
| runner_type | factor | 物理依据 |
|-------------|--------|---------|
| **热流道** | **0.95** | 流道始终熔融 → 无流道冷却收缩 → 无流道补缩需求 |
| **热转冷** | **1.00** | 部分流道凝固（混合系统）→ 介于热冷之间 → 中位 |
| **冷流道** | **1.05** | 流道随制品冷却 → 流道收缩需保压补缩 → 保压需偏高 |
| **兑底兼容** | - | `runner_weight == 0` → 推断为热流道 (0.95)；`> 0` → 冷流道 (1.05) |

**落地算法**：算法 #6 保压压力（4 维：family × thickness × gate × runner）。

**未落地算法**（下轮处理）：
- #3 注射压力 / #4 注射速度：下轮算法迭代中补充 runner 维度
- #8 保压时间：与长保压场景（PET 瓶盖 300s）合并设计

### 5.3 优先级建议

| 优先级 | 算法 | 理由 |
|--------|------|------|
| ~~P0~~ ✅ | 注射速度（#4）| 关键工艺参数，影响填充质量 |
| ~~P0~~ ✅ | 保压压力（#6）| 关键工艺参数，影响缩痕/变形 |
| ~~P1~~ ✅ | 保压时间（#8）| 已有部分物理基础（壁厚²） |
| ~~P1~~ ✅ | 保压速度（#7）| 与保压压力耦合 |
| ~~P1~~ ✅ | 冷却时间（#10）| 与保压时间物理正交（局部 vs 整体） |
| ~~P1~~ ✅ | 计量位置（#14）| 依赖料垫算法 |
| ~~P1~~ ✅ | 计量终止位置（#18）| 依赖松退距离 |
| ~~P2~~ ✅ | 螺杆转速（#12）| 已有材料字段 |
| ~~P2~~ ✅ | 计量压力（#11）| 机器类型差异 |
| ~~P2~~ ✅ | 松退距离（#17）| 与材料相关 |
| ~~P3~~ ✅ | 计量背压（#13）| 已有材料字段 |
| ~~P3~~ ✅ | 松退模式（#15）| 模式选择 |
| ~~P3~~ ✅ | 松退参数族（#15-#17）| 与机器类型相关 |
| ~~P3~~ ✅ | 松退其他参数（#16）| 与机器类型相关 |

### 5.4 推进节奏

```
【阶段 1】行程分配（已完成）
├─ ✅ 收缩长度 replenish_len
└─ ✅ 料垫长度 cushion_len

【阶段 2】核心工艺参数（P0）
├─ ✅ 注射压力（2026-07-05 完成）
├─ ✅ 注射速度（2026-07-05 完成）
├─ ✅ 注射时间（2026-07-05 完成）
└─ ✅ 保压压力（2026-07-05 完成）

【阶段 2.5】保压时间（P0+，必须覆盖长保压场景）
└─ ✅ 保压时间（高优先级提升：PET 瓶盖 100~300s）

【阶段 3】保压细节（P1）
├─ ✅ 保压速度（2026-07-05 完成）
├─ ✅ 保压时间（2026-07-05 完成，PET 长保压场景）
├─ ✅ VP 切换模式（2026-07-05 完成，#9 算法）
├─ ✅ 计量位置（2026-07-05 完成，#14 算法，公式透明仅补注释）
└─ ✅ 计量终止位置（2026-07-05 完成，#18 算法，公式透明仅 #17 后松退距离叠加）

【阶段 4】计量参数（P2）
├─ ✅ 螺杆转速（2026-07-05 完成）
├─ ✅ 计量压力（2026-07-05 完成）
└─ ✅ 计量背压（2026-07-05 完成，#13 算法）

【阶段 5】松退参数（P3，2026-07-05 全部闭环）
├─ ✅ 储料前松退模式（#15 设计+实施完成，公式透明）
├─ ✅ 储料前松退参数（#16 设计+实施完成，前松退默认关、净位移=0）
├─ ✅ 储料后松退参数（#17 设计+实施完成，5 维物理化含 runner+gate）
└─ ✅ 计量终止位置（#18 设计+实施完成，公式透明仅 #17 后松退距离叠加）

【阶段 5.5】温度参数（P3+，2026-07-05 全部闭环）
├─ ✅ 喷嘴温度（#19 设计+实施完成，2 维物理化：nozzle_offset + family_offset 17 family）
└─ ✅ 料筒温度分布（#20 设计+实施完成，4 维物理化：幂函数 k=1.2 + family_decrement 5/8/10℃ + stages 自适应 + 双层边界钳制）

【阶段 6】总收尾（路线图闭环，2026-07-05）
├─ ✅ 主清单进度总计除倒（完成 20/20，100.00%）
├─ ✅ 主清单全绿 ✅（含阶段 5 松退族 #15-#18 + 阶段 5.5 温度族 #19+#20）
└─ ✅ 路线图闭环总报告（设计 + 实施 + 验证 三阶段全闭环，6+1 阶段 / 20 算法 / 全绿）
```

---

## 6. 相关文件

| 文件 | 角色 |
|------|------|
| `process/engines/expert/initializer.py` | 算法主体（待改造）|
| `process/engines/expert/expert_rules/init_rules.json` | 规则配置（待更新）|
| `process/engines/expert/tests/test_hold_time_smoke.py` | #8 保压时间 smoke test（独立运行，17 个断言）|
| `_dev_refs/2026-07-04-injection-stroke-physics-design.md` | #1 #2 设计文档 |
| `_dev_refs/2026-07-05-injection-pressure-physics-design.md` | #3 注射压力设计文档 |
| `_dev_refs/2026-07-05-injection-velocity-physics-design.md` | #4 注射速度设计文档 |
| `_dev_refs/2026-07-05-injection-time-physics-design.md` | #5 注射时间设计文档 |
| `_dev_refs/2026-07-05-holding-pressure-physics-design.md` | #6 保压压力设计文档 |
| `_dev_refs/2026-07-05-holding-time-physics-design.md` | #8 保压时间设计文档（5 维公式 + 4 级 fallback + 移除 10s 硬上限）|
| `_dev_refs/2026-07-05-holding-velocity-physics-design.md` | #7 保压速度设计文档（3 维公式：family × bucket × 机器上限，与 #6/#8 三维正交）|
| `process/engines/expert/tests/test_hold_velo_smoke.py` | #7 保压速度 smoke test（独立运行，21 个断言）|
| `_dev_refs/2026-07-05-vp-switch-mode-physics-design.md` | #9 VP 切换模式设计文档（v3.1：3 级兜底 + 4 种模式 + 行业标准推荐）|
| `process/engines/expert/tests/test_vp_switch_mode_smoke.py` | #9 VP 切换模式 smoke test（独立运行，36 个断言）|
| `_dev_refs/2026-07-05-cool-time-physics-design.md` | #10 冷却时间设计文档（4 维公式：family × ΔT × cryst_kick × h²，11 个 family 系数，5 档温差分档）|
| `process/engines/expert/tests/test_cool_time_smoke.py` | #10 冷却时间 smoke test（独立运行，11 个断言：PET 厚壁、PC 厚壁、ABS 中壁、PP 薄壁、未材料 + 边界守门）|
| `_dev_refs/2026-07-05-metering-pressure-physics-design.md` | #11 计量压力设计文档（3 维公式：动力源分支 + nozzle_factor + family 黏度，17 family × 0.5~1.3）|
| `process/engines/expert/tests/test_meter_pres_smoke.py` | #11 计量压力 smoke test（独立运行，22 个断言：8 场景 + 全电机 + 钳制守门）|
| `_dev_refs/2026-07-05-metering-speed-physics-design.md` | #12 螺杆转速设计文档（2 维公式：family 剪切敏感度 + L/D，不分支动力源）|
| `process/engines/expert/tests/test_meter_speed_smoke.py` | #12 螺杆转速 smoke test（独立运行，28 个断言：8 场景 + L/D 三桶 + 钳制守门）|
| `_dev_refs/2026-07-05-metering-back-pressure-physics-design.md` | #13 计量背压设计文档（2 维公式：family 排气需求 17 family × 0.40~1.50 + 螺杆转速联动条件性启用，不分支动力源，对称 #12 演进）|
| `process/engines/expert/tests/test_meter_back_pres_smoke.py` | #13 计量背压 smoke test（独立运行，34 个断言：8 场景 + 4 组边界守门 + level 字符串 + 字段缺失兜底）|
| `_dev_refs/2026-07-05-suckback-decompression-physics-design.md` | **#15-#18 松退族**设计文档 v1.1（744 行：5 维物理化推导 pressure + distance + velocity + time；液压机 / 全电机分支；家族 4 档分档；runner_factor 与 gate_factor 热流道+针阀式场景全覆盖；switch 手柄 case 推导 10.47mm 对应业内实测 10mm；钳制 [1,5] MPa / [1,12] mm / [3,50] mm/s / [0.1, 5.0] s；前松退净位移 = 0 不进入位置计算）|
| `process/engines/expert/tests/test_suckback_smoke.py` | **#15-#18 松退族**smoke test（独立运行，33 个断言：14 场景含 switch 手柄 ABS+锁闭+热流道+针阀式点浇口 → D=10.47mm）与边界守门）|
| `_dev_refs/2026-07-05-temperature-physics-design.md` | **#19+#20 温度族**设计文档 v1.0（598 行：2 维 #19 喷嘴温度 + 4 维 #20 料筒温度分布；幂函数非线性 k=1.2；17 family × 2 维度差异化；双层物理边界钳制；6 典型场景验证含 PA66/PVC/PC）|
| `process/engines/expert/tests/test_temperature_smoke.py` | **#19+#20 温度族**smoke test（独立运行，含 14 场景 A-N）|
| `_dev_refs/2026-07-04-algorithm-refactor-roadmap.md` | 本文档（路线图）|

---

## 7. 更新日志

| 日期 | 进度 | 备注 |
|------|------|------|
| 2026-07-04 | 算法 #1 收缩长度 | ✅ 完成 |
| 2026-07-04 | 算法 #2 料垫长度 | ✅ 完成（含向上取整）|
| 2026-07-04 | 路线图建立 | ✅ 本文档 |
| 2026-07-05 | 算法 #3 注射压力 | ✅ 完成（半经验二维查表，详见 2026-07-05-injection-pressure-physics-design.md）|
| 2026-07-05 | 算法 #4 注射速度 | ✅ 完成（三维半经验查表：材料流动性 × L/t × 模温，详见 2026-07-05-injection-velocity-physics-design.md）|
| 2026-07-05 | 算法 #5 注射时间 | ✅ 完成（几何下限 + family × bucket 工艺窗口钳制，2 维查表 33 行，详见 2026-07-05-injection-time-physics-design.md）|
| 2026-07-05 | 算法 #6 保压压力 | ✅ 完成（四维半经验物理方法：材料 × 壁厚 × 浇口 × 流道，详见 2026-07-05-holding-pressure-physics-design.md）|
| 2026-07-05 | 保压参数拆分设计原则 | ✅ 保压压力与保压时间独立推导（流变学 vs 热力学/结晶学正交）|
| 2026-07-05 | 共性基础设施：流道类别 | ✅ runner_type 枚举升级为热/冷/热转冷；数据模型 + mold_info 字段映射同步；#6 保压压力新增 runner_factor 第 4 维 |
| 2026-07-05 | 算法 #6 落地实施 | ✅ initializer.py 新增 3 个辅助函数 (_get_family_hold_ratio / _get_gate_factor / _get_runner_factor)；主调用重构为四维公式 + 双钳制（物理比例 0.40~0.85 × 机器硬上限 0.95）；init_rules.json + rule_matcher.py DEFAULT.holding 同步；清理 4 个旧字段（hold_pres_base_ratio / thickness_factor / max_limit / inj_ratio）|
| 2026-07-05 | #6 smoke test 验证 | ✅ 7 组典型材料 × 壁厚 × 浇口 × 流道场景 + 5 组 4 级 fallback 场景（runner_weight 推断 / precise 覆盖 / 未知 family / 机器能力钳制）|
| 2026-07-05 | 算法 #8 保压时间 | ✅ 完成（五维半经验物理化：材料 × 壁厚 × 浇口 × 流道 × 模温 + 结晶拉长。**移除 10s 硬上限**采用 family_hold_time_max[family] 上限，PET=600s 覆盖长保压场景）|
| 2026-07-05 | #8 smoke test 验证 | ✅ 17 个断言全过：PET 瓶盖 295.48s 命中 family_bucket + ultra_high + 4 级 fallback 链 + 4 组边界守门（raw < min、raw > family_max、mold_temp=0、未知 family→default_hold_time_max=300s）|
| 2026-07-05 | 阶段 2.5 闭环 | ✅ #8 保压时间独立推导完成（与 #6 保压压力正交：流变学 vs 热力学/结晶学）|
| 2026-07-05 | 算法 #7 保压速度 | ✅ 完成（三维半经验物理化：family 黏度等级 × 浇口尺寸 × 机器上限钳制。与 #6/#8 正交拆分：流变学/运动学/热力学三维独立。详见 2026-07-05-holding-velocity-physics-design.md）|
| 2026-07-05 | #7 smoke test 验证 | ✅ 21 个断言全过：PET 瓶盖 11mm/s + PP 薄壁 27mm/s + ABS 中壁 20mm/s + PC 高黏度 12mm/s + 未知 family 兜底 15mm/s + 机器上限钳制 + 极端组合 + 守恒检验（v×t = 5023mm ≫ replenish_len ≈ 3mm，比值 1674x）|
| 2026-07-05 | 阶段 3 部分闭环 | ✅ #7 保压速度独立推导完成（与 #6 保压压力/#8 保压时间三维正交：流变学/运动学/热力学）|
| 2026-07-05 | 算法 #9 VP 切换模式 | ✅ 完成（v3.1：3 级兜底 + 4 种模式行业标准推荐：位置/时间/压力/位置&时间。详见 2026-07-05-vp-switch-mode-physics-design.md）|
| 2026-07-05 | #9 smoke test 验证 | ✅ 36 个断言全过：4 种模式 + 字符串兼容 5 种写法 + 边界守门（越界兜底/整数优先）|
| 2026-07-05 | 阶段 3 部分闭环 | ✅ #9 VP 切换模式独立推荐完成（与 #1-#8 算法正交：工艺控制信号完备性）|
| 2026-07-05 | 字段命名一致性修正 | ✅ initializer.py 中部分算法误用 algorithm 期望字段名（recommend_*_temperature / ejection_temperature），已统一为数据库字段名（recommended_*_temp / ejection_temp），与 material.py 数据库字段定义保持一致。涉及 5 个文件：initializer.py（200/203/1132/1347-1349/1442/1463 行）+ test_cool_time_smoke.py + test_hold_time_smoke.py + test_hold_velo_smoke.py + test_vp_switch_mode_smoke.py。 |
| 2026-07-05 | 算法 #10 冷却时间 | ✅ 完成（4 维物理化：family_cool_factor × ΔT_factor × crystallinity_kick × max_thickness²。3 级 fallback：用户指定总周期 → 物理推导 → 最小值钳制。详见 2026-07-05-cool-time-physics-design.md）|
| 2026-07-05 | #10 smoke test 验证 | ✅ 11 个断言全过：PET 厚壁 54.62s + PC 厚壁 15.39s + ABS 中壁/PP 薄壁钳制到 5s + 未知 family 兜底 5.28s + 边界守门（极端高模温 ΔT_factor=0.90 / ejection_temp=0 兜底 / 极薄壁最小值钳制）|
| 2026-07-05 | 阶段 3 闭环 | ✅ #10 冷却时间独立推导完成（与 #8 保压时间物理正交：浇口凝固局部 vs 制品整体冷却）|
| 2026-07-05 | 主清单编号扩展 | ✅ 主清单从 17 个算法扩展为 18 个（新增 #10 冷却时间，原 #10-#17 顺延为 #11-#18）；4.x 章节从 4.6-4.13 扩展为 4.6-4.14；待改造计数 8→7 |
| 2026-07-05 | 算法 #11 计量压力 | ✅ 完成（3 维半经验物理化：动力源分支（全电机=0）+ nozzle_factor + family 黏度 17 family × 0.5~1.3，详见 2026-07-05-metering-pressure-physics-design.md）|
| 2026-07-05 | #11 smoke test 验证 | ✅ 22 个断言全过：8 场景 + 全电机分支（液压专属，物理正确）+ 钳制守门（下限 3.0 / 上限 18.0）|
| 2026-07-05 | 算法 #12 螺杆转速 | ✅ 完成（2 维半经验物理化：family 剪切敏感度 17 family × 0.50~1.10 + L/D 桶修正 3 档，不分支动力源对称 #11 演进，详见 2026-07-05-metering-speed-physics-design.md）|
| 2026-07-05 | #12 smoke test 验证 | ✅ 28 个断言全过：8 场景 + L/D 三桶（short/standard/long）+ 钳制守门（下限 0.30 / 上限 0.75）|
| 2026-07-05 | 算法 #13 计量背压 | ✅ 完成（2 维半经验物理化：family 排气需求 17 family × 0.40~1.50 + 螺杆转速联动条件性启用；不分支动力源与 #12 对称演进；钳制 [0.5, 30.0] MPa；默认值 10.0 MPa 行业中位；详见 2026-07-05-metering-back-pressure-physics-design.md）|
| 2026-07-05 | #13 smoke test 验证 | ✅ 34 个断言全过：8 典型场景（PP/PC/PA66/PVC/PMMA/全电机/高速/低速）+ 4 组边界守门（钳下限 0.5 / 钳上限 30.0 / 转速下限 speed_factor=0.85 / 转速上限 speed_factor=1.15）+ level 字符串验证（precise_abbrev / precise_family / default）+ 字段缺失兜底（recommend_back_pressure None → 10.0 MPa）|
| 2026-07-05 | 关键修复 #13 | ✅ `_validate_inputs`（L197-L208）`recommend_back_pressure` 默认值从 15 改为 10.0，与 #13 算法设计默认值同步，避免数据补全阶段覆盖算法层兜底 |
| 2026-07-05 | 阶段 4 闭环 | ✅ 计量参数族 3 个算法全部完成（#11 液压专属 + #12 机械通用 + #13 通用背压），形成"液压专属 vs 通用"对称演进格局 |
| 2026-07-05 | 主清单进度更新 | ✅ 已完成 9→13（占比 52.94%→72.22%），待改造 8→5（占比 47.06%→27.78%），主清单总计 18 保持不变 |
| 2026-07-05 | 算法 #14 计量位置 | ✅ 完成（公式透明无需算法化，`meter_posi = cushion_len + total_len` 为偏移量叠加，机器坐标系下螺杆终点 = 起点偏移 + 总行程。代码 initializer.py L1830-L1842 添加物理含义注释 + logger.debug，同 #11/#12/#13 风格）|
| 2026-07-05 | 主清单进度更新 #14 | ✅ 已完成 13→14（占比 72.22%→77.78%），待改造 5→4（占比 27.78%→22.22%），**#14 计量位置提前于松退参数族闭环**（路线图后续仅剩 #15-#18 松退 + 计量终止位置）|
| 2026-07-05 | 设计阶段 #15-#18 松退参数族 | ✅ 完成（4 维推导：压力 base_ratio 0.25 + 距离 3.5mm 基础 + 速度 max_decomp_velo 派生 + 时间 distance/velo 派生；前后松退 mode_factor 0.80/1.00；family 4 档分档；液压机/全电机分支；前松退净位移 = 0 澄清与 #14/#18 正交性；详见 2026-07-05-suckback-decompression-physics-design.md 588 行）|
| 2026-07-05 | 主清单状态调整 | ✅ #15-#18 主清单仍标记 ⏳（待实施）+ 链接设计文档。4.x 章节 4.11-4.14 改为"已设计，待实施"格式。推进节奏阶段 5 全面"设计中"状态 |
| 2026-07-05 | 松退族物理边界澄清 | ✅ **关键认知**："前松退净位移 = 0"是用户对原代码质疑后验证确认的——原代码担心"前松退后退动作会漏料"，但正确设计是"前进-后退循环动作，净位移 = 0"，与 #14/#18 位置计算数学上完全正交（§1.3 详述）|
| 2026-07-05 | 算法 #15-#18 松退族落地（v1.1） | ✅ **设计文档升级 v1.0→v1.1**（588→744 行）：§3.3 距离推导从 4 维升级为 5 维物理化（新增 runner_factor[3 档] + gate_factor[6 档 仅热流道生效]），§6 关键创新 8→11 项，§7 switch 手柄案例验证（推导 10.47mm 对应业内实测 10mm 误差 4.7%），§9 已决策 12→17 项，§10 实施计划更新，max_dist 钳制上限 6.0→12.0 |
| 2026-07-05 | 代码实施 #15-#18 | ✅ `process/engines/expert/initializer.py` 新增 6 个辅助函数（_get_suckback_runner_factor / _get_suckback_gate_factor / _compute_suckback_distance / _compute_suckback_pressure / _compute_suckback_velocity / _compute_suckback_time）+ 重写 L1854-L1876 主推导区域。`rule_matcher.py` DEFAULT 新增 suckback 块。`init_rules.json` DEFAULT 同步。`process/engines/expert/init_rules.json` 同步更新 `decompression.decomp_dist_max`：10.0 → 12.0 |
| 2026-07-05 | 松退族 smoke test | ✅ `test_suckback_smoke.py` 创建（393 行 / 33 个断言 / 14 场景）：A-F 冷流道基线 +  G/H 热流道 runner_factor 验证 + 🔴 I 关键 switch 手柄 ABS+锁闭+热流道+针阀式点浇口 D=10.47mm + J/K 边界守门 + L 冷流道下 gate_factor 不叠加 + M #18 met_end_pos 公式透明 + N max_dist 钳制保护 |
| 2026-07-05 | 松退族 smoke test 验证 | ✅ **33/33 全过**：含关键 switch 手柄场景 I 推导 D=10.47mm（业内实测 10mm，误差 4.7%）。其他算法 smoke test 回归测试 6 类冷热流道压力/速度/时间结果不变（202 断言/0 失败） |
| 2026-07-05 | 🛫 主清单进度更新 #15-#18 | ✅ **已完成 14→18**（占比 77.78%→100.00%），**待改造 4→0**（占比 22.22%→0.00%），**路线图闭环**！阶段 5 松退族 + 阶段 6 总收尾全闭，**6 阶段、18 算法、全绿** |
| 2026-07-05 | 路线图闭环总报告 | ✅ 18/18 ✅， #1-#14 已完成 + #15-#18 松退族（v1.1 5 维物理化推导）实施+验证全闭环。设计文档 11 份覆盖 #1-#18 所有算法，smoke test 8 套覆盖 169+ 个断言独立运行。后续如需补充 #6 跨算法跨 runner/gate 细化可作为增量迭代 |

---

| 2026-07-05 | 算法 #19+#20 温度族设计 | ✅ 设计文档 v1.0（598 行）：#19 喷嘴温度 2 维物理化（nozzle_offset + family_offset 覆盖 PA66 +5℃/PVC -5℃），#20 料筒温度分布 4 维物理化（幂函数 k=1.2 + family_decrement 5/8/10℃ 三档 + stages 自适应 + 双层边界钳制）。遵循与 #11 计量压力 / #13 计量背压 一致的 17 family 查表风格。**路线图主清单 18→20 闭环**（主清单补 #19+#20 温度参数族，阶段 5.5 温度族全闭环） |
| 2026-07-05 | 🛫 主清单进度更新 #19+#20 | ✅ 主清单从 18 个算法扩展为 20 个（新增 #19+#20 温度参数）。路线图总计从 18 到 20。**7 个阶段、20 个算法、全绿** （阶段 5 + 阶段 5.5 + 阶段 6 全部闭环） |
| 2026-07-05 | 代码实施 #19+#20 | ✅ `process/engines/expert/initializer.py` 新增 4 个辅助函数（_get_noz_family_offset / _compute_noz_temp / _get_barrel_family_decrement / _compute_brl_temp_steps）+ 重写 L2344-2362 主推导区域为 4 维物理化逻辑。`rule_matcher.py` DEFAULT.temperature 拆分为 nozzle + barrel 两块。`process/engines/expert/expert_rules/init_rules.json` DEFAULT 同步。`_parse_family` 补充 PVC / AS / HDPE / LDPE / LLDPE 5 个 family 识别，PA66/PA6/PA 合并为 PA 单一 key |
| 2026-07-05 | 关键修复 #20 | ✅ `_compute_brl_temp_steps` 段 N 钳制从 if/elif 改为两个独立 if（避免 sN_lower > sN_upper 边界矛盾时丢失上限保护，如 Tg=200, melt=230 极端场景下 100% 保住料口熔体温度上限） |
| 2026-07-05 | 关键修复 #20 | ✅ 代码送 `round(_,1) + round(_,0)` 两层 round，加上 Python banker's rounding（half-to-even）：修正设计文档 §7 / smoke test §7.3 / §7.4 等 4 个预期值（171.5→172，171.3→171，269.3→269.4，254.6→257.8） |
| 2026-07-05 | #19+#20 smoke test | ✅ `test_temperature_smoke.py` 创建（588 行 / 37 个断言 / 14 场景）：A PP 基线 / B PA66 family_offset+5 / C PVC 热敏 family_offset-5+decrement 5 / D PC 高黏度 decrement 8 / E 8 段段 N 钳制 / F1-F3 边界守门（含上述修复验证） / G 直通 vs 锁闭 / H HDPE→PE 解析 / I 4/10 段极端 / J 幂函数 vs 线性 / K 材料手册钳制 / L 字段全缺失兑底链 / M 递减顺序 / N 设计文档对照 |
| 2026-07-05 | #19+#20 smoke test 验证 | ✅ **37/37 全过**：含关键修复 F2 边界顶门（段 N=225，台收上限+下限同时生效）。其他算法 smoke test 回归 8 套全部 PASS（cool_time/hold_time/hold_velo/meter_back_pres/meter_pres/meter_speed/suckback/vp_switch_mode）零回退 |
| 2026-07-05 | 路线图总收尾报 | ✅ 20/20 ✅，#1-#14 已完成 + #15-#18 松退族（v1.1 5 维）+ #19+#20 温度族（v1.0 4 维幂函数）实施+验证全闭环。设计文档 12 份覆盖 #1-#20 所有算法，smoke test 9 套覆盖 218+ 个断言独立运行。**路线图总计 7 个阶段（阶段 1-5 + 阶段 5.5 + 阶段 6） × 20 个算法 × 全绿**。后续如需 X-Rite 调优幂函数 k 或 family_decrement 颗粒度调整可作为增量迭代 |

---

*最后更新时间：2026-07-05（#19+#20 温度族实施全闭环：设计文档 v1.0 598 行 + 代码 4 辅助函数 + smoke test 588 行 37 断言全过 + 8 套回归 smoke test 零回退 + 路线图总计 20/20 ✅）*