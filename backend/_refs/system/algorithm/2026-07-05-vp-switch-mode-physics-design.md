# 算法 #9：VP 切换模式推荐 (vps_mode) 物理化设计

> **算法编号**：#9（保压切换模式选择）
> **类别**：保压参数 / 工艺控制信号选择
> **版本**：v3.0（4 种模式 + 行业标准推荐）
> **创建日期**：2026-07-05
> **依赖**：算法 #1-#8（replenish_len / cushion_len / inj_time / inj_pres 等）
> **设计原则**：默认位置切换 + 用户输入优先 + 按 mode 填充对应字段

---

## 1. 物理意义

### 1.1 四种切换模式

V/P 切换 = 注塑机从 **速度控制（V）切换到压力控制（P）** 的触发信号。机器支持 4 种触发源：

| mode | 名称 | 触发源 | 信号稳定性 | 物理量类型 | 典型场景 |
|------|------|--------|------------|------------|----------|
| **0** | 位置切换 | 螺杆到达 `vps_pos` | **高** | 几何量（与温度/压力解耦） | 标准制品、标准行程 |
| **1** | 时间切换 | 经过 `vps_t` 秒 | 中 | 时间量（开环控制） | 短注射行程、薄壁冻结 |
| **2** | 压力切换 | 注射压力达到 `vps_pres` | 中 | 力学量（受黏度/温度影响） | 长保压、厚壁、精密件 |
| **3** | 位置&时间 | 位置或时间哪个条件先达到就切换（**冗余保护**） | **高+中** | 几何量或时间量 | 标准制品（防止位置/时间异常卡死）|

### 1.2 为什么默认是位置切换（mode=0）

- **位置信号最稳定**：螺杆位置由位移传感器反馈，与温度/压力波动解耦
- **工业主流**：海天/震雄/Fanuc/Engel 默认都是位置切换
- **与切换位置同源**：`vps_pos = inj_pos = cushion_len + replenish_len`，已由算法 #1+#2 推导

### 1.3 为什么需要"位置&时间"（mode=3）

- **冗余保护机制**：避免位置传感器或时间控制异常导致机器卡死
- **实际工程意义**：
  - 正常情况：按位置切换（位置信号更稳定）
  - 异常情况（位置传感器故障/异常慢速）：时间达到即触发（避免卡死）
- **工业应用**：精密制品、医疗器械等对工艺稳定性要求高的场景

---

## 2. 推荐逻辑（3 级兜底）

### 2.1 优先级链

```
Level 1 - 用户明确指定 vps_mode（int 0~3）         → 'explicit'
Level 2 - 字符串兼容 VP_switch_mode 字段            → 'legacy_string'
Level 3 - 默认位置切换（mode=0）                    → 'default'
```

**关键**：Level 1 永远优先于 Level 2/3，确保用户明确输入不被覆盖。

### 2.2 字符串映射

| `VP_switch_mode` 字符串 | 派生 mode |
|--------------------------|-----------|
| `"位置"` | 0 |
| `"时间"` | 1 |
| `"压力"` | 2（显式映射） |
| `"其他"` | 2（兑底兼容） |
| `"位置&时间"` | 3（**仅此一种写法**） |

> 说明：mode=3 只接受 `"位置&时间"` 作为字符串标识，不接受变体写法（如 `"位置时间"` / `"位置与时间"` / `"位置和时间"`），避免多写法导致语义混淆。

### 2.3 输出参数策略（按 mode 填充行业标准推荐值）

| mode | `vps_pos` | `vps_t` | `vps_pres` | `vps_spd` |
|------|-----------|---------|------------|-----------|
| **0 位置** | **`inj_pos`** ⭐ | 0 | 0 | 0 |
| **1 时间** | 0 | **`inj_time × 0.95`** ⭐ | 0 | 0 |
| **2 压力** | 0 | 0 | **`inj_pres × 0.85`** ⭐ | 0 | 0 |
| **3 位置&时间** | **`inj_pos`** ⭐ | **`inj_time × 0.95`** ⭐ | 0 | 0 |

⭐ 每种填充的工业标准依据：

**mode=0 位置切换**：`vps_pos = inj_pos`
- 来源：算法 #1+#2 推导（`cushion_len + replenish_len`）
- 物理依据：注射完成位置 = 料垫 + 补缩长度（强物理推导）

**mode=1 时间切换**：`vps_t = inj_time × 0.95`
- 物理依据：VP 切换通常发生在注射行程的 95~98%（海天/震雄/Fanuc 工艺手册推荐值）
- 在速度近似线性条件下，时间 95% ≈ 位置 95%（工程容差 ±5%）
- 实际生产中：标准件推荐 95%、精密件推荐 92~95%，本算法取中位 95%

**mode=2 压力切换**：`vps_pres = inj_pres × 0.85`
- 物理依据：避开注射末端的压力峰值（峰值时机器控制精度下降）
- 实际生产中：精密件 70~80%、标准件 85~95%，本算法取中位 85%

**mode=3 位置&时间**：`vps_pos = inj_pos` + `vps_t = inj_time × 0.95`
- 物理依据：冗余保护（位置异常时时间触发，时间异常时位置触发）
- 两个值都按行业标准（位置 100%、时间 95%）独立推导

### 2.4 代码伪代码

```python
# ========== VP 切换参数（v3.1：3 级兜底 + 4 种模式行业标准推荐）==========
# Level 1: 用户明确指定 vps_mode（int 0~3）
# Level 2: 字符串兼容 VP_switch_mode（位置/时间/压力/其他/位置&时间）
# Level 3: 默认位置切换（mode=0）
# 推荐原则：基于行业标准推导公式填充推荐值

# ========== Step 1: 确定 vps_mode ==========
vps_mode_int = ps.get('vps_mode')
if isinstance(vps_mode_int, int) and 0 <= vps_mode_int <= 3:
    # Level 1: 用户明确指定（支持 0~3）
    proc.vps_mode = vps_mode_int
    vps_mode_source = 'explicit'
elif ps.get('VP_switch_mode') is not None:
    # Level 2: 字符串兼容
    vp_mode_str = ps.get('VP_switch_mode')
    if vp_mode_str == '位置':
        proc.vps_mode = 0
    elif vp_mode_str == '时间':
        proc.vps_mode = 1
    elif vp_mode_str == '压力':
        proc.vps_mode = 2  # 显式映射
    elif vp_mode_str == '位置&时间':
        proc.vps_mode = 3  # 仅此一种写法
    else:
        # "其他" 等未知字符串 → 兑底到压力切换
        proc.vps_mode = 2
    vps_mode_source = 'legacy_string'
else:
    # Level 3: 默认位置切换
    proc.vps_mode = 0
    vps_mode_source = 'default'

# ========== Step 2: 按 mode 填充推荐值（行业标准推导）==========
# 初始化（避免遗留字段）
proc.vps_pos = 0
proc.vps_t = 0
proc.vps_pres = 0
proc.vps_spd = 0

# 获取 inj_pres（用于 mode=2）
inj_pres_1st_for_vps = proc.inj_pres_steps[0] if proc.inj_pres_steps else 0.0

if proc.vps_mode == 0:
    # 位置切换：来自算法 #1+#2 推导的 inj_pos
    proc.vps_pos = inj_pos
elif proc.vps_mode == 1:
    # 时间切换：95% 注射时间（行业共识）
    proc.vps_t = inj_time * 0.95
elif proc.vps_mode == 2:
    # 压力切换：85% 注射压力（避开压力峰值）
    proc.vps_pres = inj_pres_1st_for_vps * 0.85
elif proc.vps_mode == 3:
    # 位置&时间（冗余保护）：两个值都填
    proc.vps_pos = inj_pos
    proc.vps_t = inj_time * 0.95

logger.debug(
    f"VP 切换参数: mode={proc.vps_mode} (source={vps_mode_source}) "
    f"vps_pos={proc.vps_pos:.2f}mm vps_t={proc.vps_t:.3f}s "
    f"vps_pres={proc.vps_pres:.2f}MPa (inj_pos={inj_pos:.2f}mm, "
    f"inj_time={inj_time:.3f}s, inj_pres={inj_pres_1st_for_vps:.2f}MPa)"
)
```

---

## 3. 典型场景示例

### 场景 A：标准 ABS 制品（默认位置）

- **输入**：`process_set = {}`（无任何指定）
- **推荐**：`vps_mode = 0`，`vps_pos = inj_pos`（算法 #1+#2 推导），其他 = 0
- **source**：`default`

### 场景 B：用户明确指定时间切换

- **输入**：`process_set = {'vps_mode': 1}` 或 `{'VP_switch_mode': '时间'}`
- **推荐**：`vps_mode = 1`，`vps_t = inj_time × 0.95`（行业标准：95% 注射时间）
- **source**：`explicit` 或 `legacy_string`

### 场景 C：用户明确指定压力切换

- **输入**：`process_set = {'vps_mode': 2}` 或 `{'VP_switch_mode': '其他'}`
- **推荐**：`vps_mode = 2`，`vps_pres = inj_pres × 0.85`（行业标准：避开压力峰值）
- **source**：`explicit` 或 `legacy_string`

### 场景 D：用户明确指定位置&时间（冗余保护）

- **输入**：`process_set = {'vps_mode': 3}` 或 `{'VP_switch_mode': '位置&时间'}`
- **推荐**：`vps_mode = 3`，`vps_pos = inj_pos` + `vps_t = inj_time × 0.95`（两个值都填）
- **source**：`explicit` 或 `legacy_string`
- **物理意义**：位置或时间哪个条件先达到就触发切换（冗余保护）

### 场景 E：无效输入（越界）

- **输入**：`process_set = {'vps_mode': 5}`（越界）
- **行为**：回退到 Level 2（字符串），若无字符串则回退到 Level 3（默认位置）
- **推荐**：`vps_mode = 0`，`vps_pos = inj_pos`

---

## 4. 关键创新点

### 4.1 简洁性

- **不引入评分卡**：避免过度设计，与实际生产中"默认位置 + 用户指定"的工艺习惯一致
- **3 级兜底链**：与算法 #1-#8 的多级兜底风格一致
- **复用现有字段**：`inj_pos`/`inj_time`/`inj_pres` 已在算法 #1-#5 中推导，无需新增数据源

### 4.2 完备性

- **4 种模式全覆盖**：mode=0/1/2/3 都支持识别和输出
- **向后兼容**：保留 `VP_switch_mode` 字符串字段，新增 `位置&时间` 字符串识别
- **冗余保护**：mode=3 提供位置+时间双重触发机制

### 4.3 行业标准

- **mode=0**：`inj_pos`（算法 #1+#2 推导，强物理依据）
- **mode=1**：`inj_time × 0.95`（海天/震雄/Fanuc 工艺手册推荐值）
- **mode=2**：`inj_pres × 0.85`（避开压力峰值，标准件推荐中位）
- **mode=3**：同时填充位置+时间（冗余保护）

### 4.4 物理正确性

- **位置切换 = 工业主流**：符合海天/震雄/Fanuc/Engel 默认行为
- **位置锚点**：与算法 #1+#2 推导的 `inj_pos` 同源，物理一致
- **冗余保护机制**：mode=3 解决了位置/时间异常导致机器卡死的隐患

---

## 5. 局限性

- **不主动推荐 mode=1/2/3 场景**：仅支持用户明确指定，不主动推荐各模式的使用场景
- **×0.95 / ×0.85 是工程近似**：实际生产中切换点取决于材料/制品/机器，需根据实际情况调整
- **mode=3 冗余保护的实际触发逻辑依赖机器实现**：本算法仅设置字段值，不修改机器控制程序
- **未来扩展方向**：可考虑增加 mode=4（压力&时间）等更多冗余组合

---

## 6. 相关文件

### 6.1 代码

- `backend/process/engines/expert/initializer.py` - 修改 VP 切换参数主流程

### 6.2 测试

- `backend/process/engines/expert/tests/test_vp_switch_mode_smoke.py` - 5 场景 smoke test

### 6.3 文档

- `backend/_dev_refs/2026-07-04-algorithm-refactor-roadmap.md` - 同步 #9 状态、3.9 章节
- `backend/_dev_refs/2026-07-05-vp-switch-mode-physics-design.md` - 本文档（v3.0）

### 6.4 关联算法

- **算法 #1+#2**：`inj_pos = cushion_len + replenish_len` → `vps_pos`（mode=0/3）
- **算法 #3**：`inj_pres` → `vps_pres × 0.85`（mode=2）
- **算法 #5**：`inj_time` → `vps_t × 0.95`（mode=1/3）