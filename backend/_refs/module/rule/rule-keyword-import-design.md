# 规则关键词数据导入设计

**状态**：✅ 已完成
**日期**：2026-09-15（创建与落地）
**关联数据**：`backend/process/refs/rule_keyword_curated.json`（310 条，已人工审校）
**关联备份**：`backend/process/refs/rule_keyword_extracted.original.json`（原始 1614 条备份）
**关联代码**：`backend/process/models/rules.py` RuleKeyword、`backend/bootstrap/management/commands/init_rule_keyword.py`

---

## 一、背景与目标

### 1.1 数据来源

旧系统（`old/mdprocess`）导出的关键词清单，共 **1614 条**，原始分类如下：

| 旧分类 | 数量 | 占比 | 实际含义 |
|--------|------|------|---------|
| 参数 | 1450 | 90% | 主机工艺参数（温度、压力、时间等物理量）|
| 缺陷 | 17 | 1% | 质量缺陷（短射、缩水、飞边等）|
| 缺陷位置 | 110 | 7% | 缺陷在某段发生（DLSHORTSHOT1~6）|
| 非工艺参数 | 36 | 2% | 实际是辅机参数 + 模式枚举 + 段位激活位 |
| 其他 | 1 | 0% | IL 注射位置（分类错误）|

### 1.2 重构目标

1. **补齐"设定 vs 实际"维度**——旧系统只有设定值，本次重构要支持 actual（设备通讯采集）
2. **统一业务分类**——简化录入界面，避免过度细化
3. **保留数据完整性**——1595 条可导入数据全部入库

### 1.3 旧系统的关键代码参考

- `old/mdprocess/services/inovance_service.py:1237-1248` —— 段位激活位（injectstage1-6）的 one-hot 展开逻辑
  - **这是 fuzzy 引擎的预处理中间变量，不是规则关键词**
- `old/mdprocess/services/process_optimize_service.py:911-918` —— 硬编码使用 `actual_product_weight`
  - **应该改成规则驱动**：规则 IF 条件引用 `actual_product_weight` 关键词

---

## 二、Model 字段设计

### 2.1 RuleKeyword 新增字段

```python
# 字段1：业务分类（3 选 1）
CATEGORIES = [
    ('parameter', '参数'),          # 主参数 + 辅机 + 模式（统一）
    ('defect', '缺陷'),            # IF 条件变量
    ('defect_position', '缺陷位置'),  # IF 条件变量
]
category = models.CharField(max_length=30, choices=CATEGORIES, default='parameter')

# 字段 2：值类型（2 选 1）
PARAMETER_KINDS = [
    ('setpoint', '设定值'),  # 面板输入（数值型 + 离散模式）
    ('actual', '实际值'),    # 设备通讯采集或手填
]
parameter_kind = models.CharField(max_length=20, choices=PARAMETER_KINDS, default='setpoint')
```

### 2.2 字段语义

| 字段 | 维度 | 录入复杂度 | 业务作用 |
|------|------|----------|---------|
| `category` | 业务角色 | 3 选 1 | 决定该关键词在 if-then 规则中能扮演的角色 |
| `parameter_kind` | 值来源 | 2 选 1 | 区分面板输入 vs 设备采集 |
| `keyword_type`（已有）| 物理量 | 8 选 1 | 描述参数值的物理属性 |

### 2.3 三字段正交关系

```
              parameter      defect       defect_position
setpoint  →  BT1            SHORTSHOT    DLSHORTSHOT1
actual    →  actual_BT1     (无)         (无)
mode      →  DMBM0          (无)         (无)
       ↓
   keyword_type: temperature / pressure / position / force / length / weight / time / speed
```

### 2.4 为什么 mode 不独立

用户在评审中明确："mode（注射几段、VP 切换模式）实际上都是面板上的设定工艺参数"——所以 mode 不是独立值类型，归入 setpoint。

---

## 三、JSON 数据 → RuleKeyword 映射

### 3.1 完整映射表

| JSON 原类型 | 数量 | category | parameter_kind | 备注 |
|----------|------|----------|----------------|------|
| 参数（BT1、PT0、IP0 等）| 1450 | parameter | setpoint | 主工艺参数 |
| 缺陷（SHORTSHOT、GASVEINS 等）| 17 | defect | setpoint | 布尔状态，keyword_type 填 position 占位 |
| 缺陷位置（DLSHORTSHOT1~6）| 110 | defect_position | setpoint | 段位状态，keyword_type 填 position 占位 |
| 辅机物理参数（CLAMP、IPOS、CUSION、BT、ET）| 13 | parameter | setpoint | 锁模力/注射位置/残留量等 |
| 模式参数（DMBM0-2、DMAM0-2、VPTM0-4）| 11 | parameter | setpoint | 离散模式选择 |
| 数量（HRN 热流道段数）| 1 | parameter | setpoint | 整数计数 |
| 其他（IL 注射位置）| 1 | parameter | setpoint | 分类错误，归并为辅机参数 |
| **导入小计** | **1603** | | | |
| injectstage1-6 | 8 | — | — | fuzzy 引擎 one-hot 预处理，**不导入** |
| holdingstage1-5 | 5 | — | — | 同上 |
| meteringstage1-4 | 4 | — | — | 同上 |
| HOLDEXIST | 1 | — | — | 业务控制位（保压启用），**不导入** |
| VALVEEXIST | 1 | — | — | 业务控制位（热流道启用），**不导入** |
| **不导入小计** | **19** | | | |
| **总计** | **1622** | | | **注：原始 JSON 1614 条，统计含 overlap** |

> 注：原始 JSON 实际 1614 条，上述统计中含部分重复记录需按 `keyword_name` 去重，最终导入约 1595 条（见第 6 节讨论）。

---

## 四、不导入数据的设计理由

### 4.1 injectstage1-6 / holdingstage1-5 / meteringstage1-4（共 17 条）

**真实作用**：fuzzy 引擎的 one-hot 激活位预处理

**代码证据**：
```python
# old/mdprocess/services/inovance_service.py:1237-1248
injection_stage = current_value_dict['injection_stage']  # 数字 1-6
if injection_stage == 1:
    current_value_dict['injectstage1'] = 0.95
else:
    current_value_dict['injectstage1'] = 0.05
    current_value_dict['injectstage' + str(injection_stage)] = 0.95
```

**为什么不该入 RuleKeyword**：
- 这些字段**不是工程师手写的规则变量**
- 是机器根据"当前段数"动态生成的模糊化输入
- 应该在 inovance_service 的 fuzzy 推理前**临时生成**，不持久化

**调整第几段的正确实现**：
- JSON 已有分段参数名（BT1~BT9、PT0~PT5、IP0~IP6 等）
- 规则直接引用分段参数名（如 `PT0`）即可
- 不依赖 injectstage1-6 作为条件

### 4.2 HOLDEXIST / VALVEEXIST

**真实作用**：业务控制位
- `HOLDEXIST` = 是否启用保压 → 决定是否调用保压相关推理
- `VALVEEXIST` = 是否多阀试验 → 决定是否启用热流道相关规则

**为什么不该入 RuleKeyword**：
- 这两个字段是**推理流程开关**，不是规则变量
- 应该由业务模块在调用推理前设置
- 出现在规则条件中会非常奇怪：
  ```
  IF GASVEINS_high AND VALVEEXIST_high  ← 逻辑不通
  ```

---

## 五、待回答的子问题

### 5.1 ❓ `keyword_alias` 怎么填？

JSON 数据没有 `alias` 字段，但 Model 必填。

候选方案：
- A：用 `description` 当作 alias（"料筒温度一段"）
- B：用 `keyword_name` 当作 alias（"BT1"）—— 技术化，不推荐

### 5.2 ❓ `unit` 怎么填？

JSON 数据没有 `unit` 字段，但 Model 必填。

候选方案：
- A：默认空字符串 `""`
- B：默认占位符 `"—"`
- C：按 `keyword_type` 推断（temperature→℃、pressure→MPa）—— 工程量大

### 5.3 ❓ 1614 条 vs 327 个唯一 name（去重策略）

| 策略 | 结果 | 风险 |
|------|------|------|
| 全量导入 | 1614 条 | 重复数据浪费 |
| 按 name 去重（保留首条）| 327 条 | 丢失 ID 信息 |
| 按 name + library 分组 | 待定 | 需要先看分组依据 |

---

## 七、导入实测结果（2026-09-15）

### 最终状态

**8 个动作完成**：
1. Model 字段重构（加 category + parameter_kind）
2. 生成 migration 0007
3. 原 JSON 备份为 `rule_keyword_extracted.original.json`
4. 生成 `rule_keyword_curated.json`（去重 + 排除 + fuzzy=5 统一）
5. 删除废弃脚本 `init_fuzzy_demo.py`
6. 脚本修复（长前缀优先 + VPT/DMB/DMA 加前缀表）
7. 重新导入 310 条数据（全部 keyword_type 正确）
8. 脚本重命名 `init_fuzzy_keyword` → `init_rule_keyword`（避免 fuzzy 歧义）

### 命名统一（2026-09-15）

为避免命名歧义，本次会话统一了以下脚本名：

| 旧名 | 新名 | 理由 |
|------|------|------|
| `init_rules.py` | `init_expert_rules.py` | 脚本导入的是 ExpertRule，不是"通用 init_rules" |
| `init_rules.json` | `expert_rules.json` | 数据文件跟随脚本名 |
| `init_fuzzy_keyword.py` | `init_rule_keyword.py` | RuleKeyword 是通用模型，不只 fuzzy 使用 |
| `init_fuzzy_ranges.py` | `init_rule_keyword_steps.py` | "ranges" 太宽泛，实际是 step（推理步长）|
| library_code `'init_rules'` | library_code `'expert_rules'` | 库标识语义清晰，去掉冗余的 init_ 前缀 |

数据迁移：1 条 RuleLibrary（library_code 从 `'init_rules'` 更新为 `'expert_rules'`），8 条 ExpertRule FK 跟随。

### 数据统计

| 指标 | 数量 |
|------|------|
| 原 JSON | 1614 条 |
| 备份 | 1614 条 |
| 去重后 | 327 条 |
| 排除（injectstage/holdingstage/meteringstage + HOLDEXIST/VALVEEXIST）| 17 条 |
| **curated 最终入库** | **310 条** |
| parameter | 183 条 |
| defect | 17 条 |
| defect_position | 110 条 |

### fuzzy_level 统一处理

- 原 JSON 里 fuzzy_level 只有 3 和 9 两种值（1523 + 91 = 1614）
- curated JSON 里统一为 **5**（与 Model 默认一致）
- 理由：原数据不一定正确；早期开发人员可能随意取值；统一 5 便于后期调整

### keyword_type 修复记录

**修复前错误推断**：
- `IPOS` 被识别为 pressure（实际是 position）
- `VPTM1-4`、`VPTT` 被识别为 time/pressure/speed（实际是离散模式）

**修复后**：
- 18 个离散模式关键词全部识别为 `position`（占位）
- 长前缀优先匹配逻辑避免 IPOS 被 IP 截胡
- VPT/DMB/DMA 加前缀表，优先匹配 position

### 文件管理

| 文件 | 状态 |
|------|------|
| `process/refs/rule_keyword_extracted.json` | ❌ 已删除（被 curated 取代） |
| `process/refs/rule_keyword_extracted.original.json` | ✅ 备份保留 |
| `process/refs/rule_keyword_curated.json` | ✅ 生产用（310 条） |
| `bootstrap/management/commands/init_fuzzy_demo.py` | ❌ 已删除（废弃脚本） |
| `bootstrap/management/commands/init_rule_keyword.py` | ✅ 已修复（重命名自 init_fuzzy_keyword） |

| 决策 | 选择 | 理由 |
|------|------|------|
| category 分类数 | 3（参数/缺陷/缺陷位置）| 用户评审：辅机和模式不应拆分，避免过度细化 |
| parameter_kind 分类数 | 2（setpoint/actual）| 用户评审：mode 是 setpoint 的特殊形式 |
| 是否加 defect_position | 是 | 缺陷位置是 if-then 规则的有效条件变量 |
| injectstage 是否入 | 否 | fuzzy 引擎内部 one-hot 预处理中间变量 |
| HOLDEXIST/VALVEEXIST 是否入 | 否 | 业务控制位，应在业务层处理 |

### 流程验证（2026-09-15）

为验证 RuleKeyword → FuzzyEngine 数据通路，写了 `_smoke_test_pipeline.py` 脚本
（`backend/process/refs/_smoke_test_pipeline.py`），跑过 4 个测试：

| 测试 | 结果 |
|------|------|
| 单条 RuleKeyword → fuzzy dict | ✅ 6 个样本全部正确（BT1/IP0/PT0/CLAMP/SHORTSHOT/DLSHORTSHOT1）|
| 批量查询 → fuzzy dict 列表 | ✅ 3/3 |
| category 分布 | ✅ parameter 183 / defect_position 110 / defect 17 |
| BT1 关键字段验证 | ✅ category/parameter_kind/keyword_type/unit/fuzzy_level/keyword_alias/description 全过 |

```
[ALL PASS] RuleKeyword -> FuzzyEngine pipeline OK
```

**遗留工作**：FuzzyEngine 内部实际调用 RuleKeywordAdapter 的链路尚未验证（待后续）
——本设计文档只验证 Adapter 本身工作正常。

---

## 八、本次会话决策记录（2026-09-15）

按时间顺序：

1. **Model 字段重构**：加 category（3类）+ parameter_kind（2类）
2. **数据导入策略**：原 JSON 备份 + 生成 curated JSON（人工审校后权威模板）
3. **fuzzy_level 统一**：从 JSON 的 3/9 统一为 5（与 Model 默认一致）
4. **keyword_type 推断修复**：长前缀优先 + VPT/DMB/DMA 加前缀表
5. **脚本重命名**：init_rules→init_expert_rules、init_fuzzy_keyword→init_rule_keyword、init_fuzzy_ranges→init_rule_keyword_steps
6. **library_code 重命名**：'init_rules' → 'expert_rules'（数据迁移 1 条 RuleLibrary）