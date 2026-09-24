# FuzzyEngine 参考文档

> 本文档是模糊推理引擎（FuzzyEngine）的**完整参考手册**，融合项目历史背景、架构设计、数据模型、算法核心、规则组织与冲突消解策略，是后续开发的"工作手册"。
>
> 文档生成时间：2026-07-02
>
> 适用范围：`backend/process/engines/fuzzy/` 模块与 `RuleMethod` / `RuleKeyword` / `RuleLibrary` 规则相关业务

## 0. 阅读指引

| 角色 | 推荐阅读顺序 |
|------|------------|
| **新成员快速理解** | §1 (历史) → §2 (架构) → §3 (数据模型) → §9 (典型场景) |
| **算法迁移开发** | §2 (架构) → §4 (算法核心) → §5 (JSON Schema) → §10 (实施清单) |
| **规则治理 / 业务配置** | §5 (JSON Schema) → §6 (规则组织) → §7 (冲突消解) → §9 (典型场景) |
| **代码审查 / Bug 排查** | §1.2 (命名混乱识别) → §7 (冲突消解) → §4.6 (常见 bug) |

---

## 1. 项目历史背景

### 1.1 真实演化路径

```
阶段 A (Mamdani 时代, 用户接手早期)
├── 规则源：Rule.dat 文件 (273 条全模糊规则)
├── 形式：IF X_low AND Y_high THEN Z_add_low (条件模糊+结论模糊)
├── 网络：FuzzyRuleNet (Mamdani, 含反模糊化)
└── 调用：utils/fuzzykit/new_test.py (测试 demo)

阶段 B (数据库时代, 用户未参与的中期重构)
├── 规则源：数据库 (RuleMethod.rule_content JSON)
├── 形式：IF X_low THEN Z_add_10 或 Z_add_5% (条件模糊+结论数值)
├── 网络：NumTskRuleNet (零阶 TSK, 直接数值)
├── 函数名沿用 tsk_algorithm() (命名误导)
└── 调用：production paths (process_optimize_service, inovance_service)

旁支：TskRuleNet (一阶代数式, 从未启用)
├── 实现存在 nets.py L521-814, 但被显式注释
└── 命名误导：让人以为项目用过标准 TSK
```

### 1.2 历史教训：项目原始设计的命名混乱

> **重要**：下文涉及的"网络"指的是 fuzzykit 三套实现；下文涉及的"启用"指是否在生产路径被实际调用。

| 混乱维度 | 具体表现 | 影响 |
|---------|---------|------|
| 函数名 vs 实际网络 | `tsk_algorithm()` 函数名误导，主体跑的是 NumTskRuleNet（零阶 TSK）| 阅读源码时容易误解 |
| 类名 vs 实际启用 | `TskRuleNet` 类有实现但被显式注释 | 误以为有代数式规则，其实没有 |
| 开发者主观归类 | 早期项目把模糊推理整套叫"TSK"（实际跑 Mamdani）| 命名误导 |
| 规则形态变化 | `add_low` (模糊) → `add_10` (数值) → `add_5%` (百分比) | 不同数据库条目形态不一致 |
| 输出多类型 | 数值调整 + 弹窗/提示（`adjust`/`popup` 关键字）| 输出 schema 含 `candidate_rules` + `adjust_rules` |

### 1.3 真实使用情况（基于代码证据）

| 实现类 | 文件位置 | 生产路径使用 | 状态 |
|--------|----------|------------|------|
| `FuzzyRuleNet` (Mamdani) | `nets.py` L132-427 | ❌（仅 new_test.py demo）| 兼容历史 |
| `NumTskRuleNet` (零阶 TSK) | `nets.py` L959-1281 | ✅ 主生产路径 | **生产主路径** |
| `ParticularRules` (弹窗规则) | `nets.py` L817-866 | ✅ 配合 `adjust_array` | 提示类规则 |
| `TskRuleNet` (一阶代数式) | `nets.py` L521-814 | ❌ 注释掉 | **死代码，不迁** |

---

## 2. 架构总览

### 2.1 核心设计哲学：双层并行架构（工厂级 + 兜底层）

```
          ┌─────────────────────────────────────────┐
          │        FuzzyEngine 双层并行               │
          ├─────────────────────────────────────────┤
          │                                         │
          │   ┌──────────┐         ┌──────────┐      │
          │   │ 工厂级    │         │ 兜底层    │      │
          │   │ NumTsk    │         │ FuzzyRule │    │
          │   │ RuleNet   │         │ Net       │    │
          │   │          │         │ (Mamdani) │    │
          │   │ 精确规则  │         │ 模糊级别  │    │
          │   └────┬─────┘         └────┬─────┘      │
          │        │                    │             │
          │   priority_array          centroid       │
          │     加权求和              反模糊化         │
          │        │                    │             │
          │        └────────┬───────────┘             │
          │                 │                         │
          │     ┌───────────▼────────────┐            │
          │     │ 合并：同层聚合 + 跨层覆盖 │            │
          │     │ 工厂级胜出兜底层         │            │
          │     └─────────┬──────────────┘            │
          │               │                          │
          │               ▼                          │
          │       List[Recommendation]                 │
          │       (含 sources: factory/fallback)      │
          └─────────────────────────────────────────┘
```

### 2.2 关键架构决策

| 决策点 | 选择 | 理由 |
|--------|------|------|
| **算法核心范围** | FuzzyRuleNet + NumTskRuleNet + ParticularRules | 涵盖历史兼容 + 生产 + 弹窗 |
| **TskRuleNet 命运** | **不迁** | 死代码（命名误导），无代数式规则 |
| **规则来源** | RuleMethod DB + `engines/fuzzy/rules/` 目录 | DB 是主源；文件做种子样本与导入导出 |
| **双层架构** | NumTskRuleNet（工厂级）+ FuzzyRuleNet（兜底层） | 工厂级是已知场景精确解；兜底层覆盖新场景 |
| **规则组织** | 多规则库（RuleLibrary 隔离大类）+ 库内条件匹配 | 与现有模型字段匹配 |
| **冲突消解** | 方案 B：同层聚合 + 跨层覆盖 | 集成 fuzzykit `priority_array` 自然加权 |
| **priority 协议** | 手动 4 级（L1=10 / L2=5 / L3=4 / L4=1）| 简单可控 |
| **分类维度位置** | polymer_category / product_category 留在字段层 | 离散值路由层 vs 连续值推理层不混 |
| **跨聚合复用** | `RuleLibrary.parent_library` 继承（不写 OR）| 库层级继承天然支持 |
| **step 字段填充** | 扫描 `range_test.csv` 迁移 | 老数据是事实标准 |

### 2.3 模块职责边界（明确）

**FuzzyEngine 内部**（本次实施）：
- fuzzy_core 算法实现
- RuleMethod JSON Schema 定义与序列化
- FuzzyEngine.recommend() 串联
- RuleKeyword.step 字段补全

**FuzzyEngine 外部**（不属于本次）：
- ProcessRecommendationService 业务编排
- defect_degree → w 调整系数
- iteration_trend 调整因子
- opt_nums 迭代反馈
- IDT1~6 / HOLDEXIST / VALVEEXIST 派生字段

---

## 3. 数据模型

### 3.1 模型概览（已存在）

```
RuleLibrary             ← 顶层：产品大类隔离 + 层级继承
  ├── RuleMethod        ← 规则本体（带 polymer/product 分类）
  ├── MinedRule         ← 规则挖掘结果（待审核）
  └── ExpertRule        ← 专家规则（初始化工艺）

RuleKeyword             ← 参数元数据（系统级）
TenantKeywordOverride   ← 租户关键词覆盖
```

### 3.2 RuleLibrary

```python
class RuleLibrary(BusinessBaseModel):
    library_code = CharField(unique=True)  # 'general' / 'packaging' / 'PE_bottle'
    library_name = CharField(max_length=100)
    owner_type = CharField(choices=[('system', '系统级'), ('tenant', '租户级'), ('user', '用户级')])
    priority = IntegerField(default=0)        # 高优先级覆盖低优先级
    is_active = BooleanField(default=True)
    version = IntegerField(default=1)
    parent_library = ForeignKey('self', null=True)  # 支持库层级继承
```

**关键字段**：`library_code`（编码）/ `priority`（覆盖优先级）/ `parent_library`（复用）。

### 3.3 RuleMethod（规则核心）

```python
class RuleMethod(BusinessBaseModel):
    rule_library = ForeignKey(RuleLibrary, related_name='rule_methods')
    subrule_no = CharField(max_length=45)         # 子规则编号
    rule_code = CharField(max_length=50)

    # 路由维度（不写进 rule_content.conditions）
    polymer_category = CharField(null=True, blank=True, max_length=45)
    product_category = CharField(null=True, blank=True, max_length=45)

    # 缺陷信息
    defect_name = CharField(max_length=45)
    defect_desc = CharField(null=True, blank=True, max_length=200)

    # 规则内容
    rule_description = TextField()
    rule_explanation = TextField(null=True, blank=True)
    rule_content = JSONField()                    # 详见 §5

    # 规则元数据
    rule_type = CharField(max_length=45)
    priority = FloatField(default=1.0)            # 用于加权求和
    confidence = FloatField(default=1.0)

    # 启用控制
    is_auto = BooleanField(default=True)
    enable = BooleanField(default=True)

    # 规则来源
    source = CharField(choices=[('expert', '专家经验'), ('rule_miner', '规则挖掘'), ('llm', '大模型生成')])

    class Meta:
        unique_together = ['rule_library', 'rule_code']
```

**需新增字段**（本次迁移）：
- `rule_level`：`'factory' | 'fallback'`，标识工厂级 vs 兜底层
- 详见 §6.3

### 3.4 RuleKeyword

```python
class RuleKeyword(BusinessBaseModel):
    keyword_name = CharField(unique=True)        # 'inj_pres_1'
    keyword_alias = CharField(max_length=100)    # '注射压力1'
    param_group = CharField(choices=PARAM_GROUPS)

    # 取值范围
    range_min = FloatField()
    range_max = FloatField()

    # 调整参数
    action_range_min = FloatField(null=True, blank=True)
    action_range_max = FloatField(null=True, blank=True)
    action_max_val = FloatField(null=True, blank=True)

    # 模糊参数
    fuzzy_level = IntegerField(choices=[(3, '3级'), (5, '5级')], default=3)
    keyword_type = CharField(max_length=45)      # 'pressure' / 'speed' / 'time' / 'temperature'
    unit = CharField(max_length=20)              # 'MPa' / 'mm/s' / 's'

    # 分类维度（参数层）
    subrule_no = CharField(null=True, blank=True)
    product_small_type = CharField(null=True, blank=True)
    polymer_abbreviation = CharField(null=True, blank=True)
```

**需新增字段**（本次迁移）：
- `step = FloatField(null=True, blank=True)` —— 单次调整步长

---

## 4. 算法核心

### 4.1 三套网络与规则形式映射

| 网络 | 处理的规则形式 | solution_matrix 内容 | 输出方式 |
|------|---------------|---------------------|---------|
| **FuzzyRuleNet (Mamdani)** | `IF X_low AND Y_high THEN Z_add_low`（结论**模糊级别**）| 标记 `±1` 在特定 level 列 | centroid 反模糊化 |
| **NumTskRuleNet (零阶 TSK)** | `IF X_low THEN Z_add_10` 或 `Z_add_50%`（结论**数字/百分比**）| `level值 × action` 数字 | 加权求和（百分比乘当前值）|
| **ParticularRules** | 含 `adjust`/`popup` 关键字的弹窗规则 | — | 收集 r_extra 文本 |

### 4.2 FuzzyFeature：参数模糊化

```python
class FuzzyFeature:
    """把一个连续值参数模糊化为多个级别的隶属度"""
    def __init__(self, f_name, f_interval, f_membership_type='gauss', f_level=3):
        # f_interval: 参数取值范围
        # f_membership_type: 'gauss' 高斯 / 'tri' 三角
        # f_level: 模糊级数 (3 或 5)

    def get_value_by_level(self, x, level):
        """返回 x 对该 level 的隶属度（0~1）"""
```

**示例**：参数 `inj_pres_1 ∈ [0, 200]`，3 级高斯：
- `inj_pres_1 = 50` → `[low=0.6, mid=0.4, high=0.0]`（同时属于多个级别）

### 4.3 FuzzyRule：单条规则字符串解析

规则字符串示例：
```
IF inj_pres_1_low AND 短射_high THEN inj_pres_1_add_10
```

解析为：
- `r_preconditions = {"inj_pres_1": {"level": "low"}, "短射": {"level": "high"}}`
- `r_solutions = {"inj_pres_1": {"action": +1, "value": 10, "value_type": "absolute"}}`

### 4.4 NumTskRuleNet：生产主路径

```python
class NumTskRuleNet:
    """
    零阶 TSK 推理网络（生产主路径）
    处理'条件模糊 + 结论数值/百分比'规则
    """

    def __init__(self, rule_array, keyword_array, priority_array):
        # 1. 解析每条规则
        # 2. 把 _add_10 转成 solution_matrix=10.0; _add_50% 转成 0.5
        # 3. rule_classify: 0=绝对值, 1=百分比

    def tsk_inference(self, x, priority_array):
        """
        四层推理：
        1. 隶属度层（gauss_mf）
        2. 规则激活（prod 连接）
        3. 归一化 + priority 加权
        4. 结论层（sol_matrix * cur_params，百分比规则乘当前值）
        """
        # 返回 [(rule_desc, activation, {param: value}), ...]
```

**关键约束**：`rule_content.conditions` 的 `level` 字段必须是数字（如 `low` 不能直接用，要么换数字，要么走 FuzzyRuleNet）。

### 4.5 FuzzyRuleNet：兜底兼容

```python
class FuzzyRuleNet:
    """
    Mamdani 推理网络（兜底层）
    处理'条件模糊 + 结论模糊级别'规则
    """

    def __init__(self, rule_array, keyword_array):
        # 规则解析：solution_matrix 在 level 列标记 ±1

    def inference(self, x):
        """
        四层推理：
        1. 隶属度层
        2. 规则激活（min 连接，弱连接语义）
        3. 输出聚合（max 合成）
        4. centroid 反模糊化
        """
        # 返回 [(param, value, (activation, rule)), ...]
```

### 4.6 TskRuleNet（一阶代数式）—— **不迁**

```python
class TskRuleNet:
    """
    一阶代数式 TSK（如 Y=2*X+5）
    【状态】死代码，从未启用，命名误导，**不在本次迁移范围**
    """
    pass  # 占位类即可
```

### 4.7 ParticularRules：弹窗/提示规则

```python
class ParticularRules:
    """
    弹窗/提示类规则解析
    处理含 'adjust'/'popup' 关键字的特殊规则
    """

    def __init__(self, adjust_array):
        # adjust_array: RuleMethod 中含 'adjust' 关键字的规则
        # 解析后保存到 self.adjust_rule_list
```

**输出字段**：每条提示规则含 `rule_defect` / `rule_description` / `rule_output` 三元组。

### 4.8 常见 Bug 与识别

| Bug 现象 | 根因 | 排查路径 |
|---------|------|---------|
| `float('low')` 报错 | NumTskRuleNet 处理了 `_add_low` 形式规则 | 应路由到 FuzzyRuleNet 而非 NumTskRuleNet |
| 所有规则 activation=0 | FuzzyFeature.min_val/max_val 错位 | 检查 range_min/range_max 是否对应 |
| 推理结果全是 step 满量 | priority_array 全相同 | 检查 RuleMethod.priority 字段 |
| 兜底级 + 工厂级结果差距大 | 优先线路由错 | 检查 `_resolve_libraries` 加载顺序 |
| 百分比规则输出恒为 0 | rule_classify 误判 | 检查 level 字段是否含 '%' |

---

## 5. RuleMethod JSON Schema

### 5.1 完整 Schema 定义

```python
{
    "conditions": [
        # === 类型 A：工艺参数条件（推荐）===
        {
            "param": "inj_pres_1",           # 参数名（必填）
            "fuzzy_level": "low",            # 模糊级别 'low'/'mid'/'high'
                                            # 或数字字符串 '50'
            # 【注意】fuzzy_level 与下面的 operator/value 互斥
        },

        # === 类型 B：精确条件（数字阈值）===
        {
            "param": "inj_pres_1",
            "operator": "lt",                # 'lt' / 'lte' / 'gt' / 'gte' / 'eq'
            "value": 60
        },

        # === 类型 C：缺陷条件 ===
        {
            "defect": "SHORTSHOT",
            "fuzzy_level": "high"
        }
    ],

    "adjustments": [
        # === 类型 A：参数调整 ===
        {
            "type": "param",
            "param": "inj_pres_1",
            "action": "add",                # 'add' / 'reduce'
            "value": 10,                     # 绝对值（value_type='absolute'）
            "value_type": "absolute"        # 或 'percent'
        },
        # 或百分比：
        {
            "type": "param",
            "param": "mel",
            "action": "add_pct",             # 'add_pct' / 'reduce_pct'
            "value": 5,                      # 5 表示 5%
            "value_type": "percent"
        },
        # === 类型 B：Mamdani 模糊级别结论（兜底层）===
        {
            "type": "param",
            "param": "hold_time",
            "action": "add",
            "level": "mid"                   # 由 step 决定数值大小
        },

        # === 类型 C：弹窗/提示（ParticularRules 处理）===
        {
            "type": "tip",
            "defect_name": "SHORTSHOT",
            "severity": "warning",           # 'info'/'warning'/'error'
            "text": "短射缺陷：建议检查模温",
            "trigger_param": "inj_pres_1"
        }
    ]
}
```

### 5.2 字段约束

| 字段 | 工厂级（factory）| 兜底层（fallback）|
|------|-----------------|-------------------|
| `adjustments.action` | `add` / `add_pct` / `reduce` / `reduce_pct`（明确数值）| `add` / `reduce` + `level: low/mid/high` |
| `adjustments.value` | 必须有（数值或百分比）| 可省略（由 level + step 决定）|
| `adjustments.value_type` | `absolute` / `percent` | 通常不填 |

### 5.3 RuleLevel 字段（需新增）

```python
class RuleMethod(models.Model):
    # ... 已有字段 ...

    RULE_LEVELS = [
        ('factory', '工厂级'),     # NumTskRuleNet 处理，精确数值/百分比
        ('fallback', '兜底层'),    # FuzzyRuleNet 处理，模糊级别
    ]
    rule_level = models.CharField(
        max_length=20,
        choices=RULE_LEVELS,
        default='factory',
        verbose_name="规则层级"
    )
```

**路由规则**：
- `rule_level='factory'` → NumTskRuleNet
- `rule_level='fallback'` → FuzzyRuleNet

### 5.4 完整示例：PE 酒瓶短射规则

```python
# === 工厂级（PE 酒瓶精确规则）===
RuleMethod(
    rule_library=packaging_lib,
    polymer_category='PE', product_category='酒瓶',  # 三级特异性：精确
    defect_name='SHORTSHOT',
    rule_level='factory',                              # 工厂级
    priority=10.0,                                     # L1 特异性
    rule_content={
        "conditions": [
            {"param": "hold_time", "fuzzy_level": "low"}
        ],
        "adjustments": [
            {"type": "param", "param": "hold_time",
             "action": "add", "value": 4, "value_type": "absolute"}  # +4s（大调整量）
        ]
    }
)

# === 兜底层（默认规则，跨产品生效）===
RuleMethod(
    rule_library=general_lib,
    defect_name='SHORTSHOT',                           # 无 polymer/product：默认
    rule_level='fallback',                             # 兜底层
    priority=1.0,                                      # L4 默认
    rule_content={
        "conditions": [
            {"param": "hold_time", "fuzzy_level": "low"}
        ],
        "adjustments": [
            {"type": "param", "param": "hold_time",
             "action": "add", "level": "low"}          # 模糊级别，由 step × 隶属度决定
        ]
    }
)
```

---

## 6. 规则组织

### 6.1 多规则库 + 库内条件匹配

```
[ RuleLibrary 顶层隔离 ]
        ↓
[ RuleLibrary.parent_library 继承复用 ]
        ↓
[ RuleMethod.polymer_category × product_category 三级特异性 ]
        ↓
[ rule_content.conditions 工艺参数 ]
        ↓
[ fuzzy 算法 ]
```

### 6.2 三级特异性匹配

匹配优先级（高 → 低）：

| 特异性 | 规则条件 | 命中条件 |
|--------|---------|---------|
| **L1 精确** | `polymer='PE' AND product='酒瓶'` | 当前聚合物 = PE 且产品 = 酒瓶 |
| **L2 部分-聚合物** | `polymer='PE' AND product=NULL` | 当前聚合物 = PE（任意产品）|
| **L3 部分-产品** | `polymer=NULL AND product='酒瓶'` | 当前产品 = 酒瓶（任意材料）|
| **L4 默认** | `polymer=NULL AND product=NULL` | 任意情况 |

**加载顺序**：先 L1 → L2 → L3 → L4。

### 6.3 双层并行：工厂级 vs 兜底层

```
[FuzzyEngine.recommend]
    │
    ├── 按 defect + polymer/product 拉规则
    │
    ├── 分流
    │   ├── factory_rules → NumTskRuleNet (主)
    │   └── fallback_rules → FuzzyRuleNet (兜底)
    │
    ├── 双网络并行推理
    │
    └── 合并：同层聚合 + 跨层覆盖
        ├── 同层：priority + 激活度加权和
        └── 跨层：工厂级胜出兜底
```

### 6.4 库层级继承

```python
# 顶层：包装容器大类
RuleLibrary(code='packaging', parent=None, priority=10)

# 第二层：PE 材料通用（继承 packaging）
RuleLibrary(code='PE', parent=packaging, priority=20)

# 第三层：PE 酒瓶（继承 PE）
RuleLibrary(code='PE_bottle', parent=PE, priority=30)
```

**复用方式**：
- 放在 `packaging` 的规则：所有包装容器可见
- 放在 `PE` 的规则：所有 PE 材料制品可见
- 放在 `PE_bottle` 的规则：仅 PE 酒瓶可见

### 6.5 路由服务：RuleQueryService

```python
class RuleQueryService:
    """规则查询与路由服务"""

    @staticmethod
    def get_rules(context: dict, defect_name: str) -> List[dict]:
        """
        按上下文（产品/材料/缺陷）拉规则
        返回三级特异性排序后的全部规则（含 fallback）
        """
        target_libs = RuleQueryService._resolve_libraries(context)
        all_rules = []
        for lib in target_libs:
            rules = RuleMethod.objects.filter(
                rule_library=lib,
                defect_name=defect_name,
                enable=True,
            ).order_by('-priority')
            all_rules.extend(rules)
        return all_rules

    @staticmethod
    def _resolve_libraries(context: dict) -> List[RuleLibrary]:
        """根据上下文解析目标规则库（按优先级排序）"""
        libraries = []

        # 1. 用户指定库
        if context.get('rule_library_code'):
            libraries.append(
                RuleLibrary.objects.get(library_code=context['rule_library_code'])
            )

        # 2. 产品大类专用库（业务路由逻辑）
        product_class = context.get('product_class')
        if product_class:
            lib = RuleLibrary.objects.filter(
                library_code=product_class, is_active=True
            ).first()
            if lib:
                libraries.append(lib)

        # 3. 通用兜底库
        general = RuleLibrary.objects.filter(
            library_code='general', is_active=True
        ).first()
        if general:
            libraries.append(general)

        return libraries
```

---

## 7. 冲突消解

### 7.1 冲突三大场景

| 场景 | 示例 | 表现 |
|------|------|------|
| **同参不同量** | 通用"加 5" vs 酒瓶"加 15" | 同参数输出不同调整量 |
| **同参反向** | 通用"加 5" vs 酒瓶"减 5" | 同参数方向相反 |
| **覆盖范围冲突** | 通用覆盖 IP0-IP5 vs 酒瓶 IP0-IP2 | 参数覆盖范围不同 |

### 7.2 方案 B 消解策略（推荐）

| 层级 | 消解策略 |
|------|---------|
| **跨层**（工厂 vs 兜底）| **工厂级胜出**，兜底层作为辅助参考 |
| **同层层内** | priority + 激活度加权求和（fuzzykit `priority_array` 已支持）|
| **同名参数** | 多规则激活度加权求和 |
| **同参反向** | 不直接抵消，按各自激活度贡献 |

### 7.3 priority 协议（4 级手动分级）

| 优先级 | 特异性 | 适用场景 | priority 值 |
|--------|--------|---------|-----------|
| L1 | 精确（polymer+product）| 某产品+某材料专有的精确规则 | 10 |
| L2 | 部分-聚合物 | 某材料通用的规则 | 5 |
| L3 | 部分-产品 | 某产品通用的规则 | 4 |
| L4 | 默认（都不指定）| 跨产品的通用兜底 | 1 |

**注意**：priority 字段由人工或迁移脚本设定，**不引入自动计算逻辑**。

### 7.4 合并算法

```python
def merge_recommendations(factory_recs, fallback_recs):
    """
    双层推理结果合并
    - 同名参数：工厂级与兜底层各自处理
    - 工厂级未覆盖的参数：兜底层补充
    - sources 列表说明来源
    """
    merged = {}

    # 工厂级先处理
    for rec in factory_recs:
        merged[rec.param] = rec
        merged[rec.param].sources = ['factory']

    # 兜底层补充未覆盖的参数
    for rec in fallback_recs:
        if rec.param in merged:
            merged[rec.param].sources.append('fallback')
            # fallback 调整量仅作参考标注，不覆盖
            merged[rec.param].fallback_reference = rec.recommended_value
        else:
            merged[rec.param] = rec
            merged[rec.param].sources = ['fallback']

    return list(merged.values())
```

### 7.5 典型执行流程（PE 酒瓶短射场景）

```
[1] FuzzyEngine 加载规则（context = PE, 酒瓶, SHORTSHOT）
    packaging 库：(L1) PE 酒瓶精确规则, priority=10
    general 库：(L4) 默认规则, priority=1

[2] 分流
    factory_rules = [L1 精确规则]
    fallback_rules = [L4 默认规则]

[3] NumTskRuleNet 推理（L1）
    假设 hold_time=3.5s, 隶属度 low=0.85
    sol_matrix: 激活度 0.85 × 4 = 3.4
    归一化后激活度 ≈ 0.567 (10/(10+5)) ... wait, 只有 1 条规则
    
[4] FuzzyRuleNet 推理（L4）
    hold_time=3.5, 隶属度 low=0.85
    模糊级 add_low + step=4 → centroid ≈ 1.6

[5] 合并
    工厂级胜出：hold_time +3.4s (recommended_value = 3.5+3.4)
    兜底层标记：fallback_reference = +1.6
    
[6] 返回
    Recommendation(
        param_name='hold_time',
        current_value=3.5,
        recommended_value=6.9,
        confidence=0.85,
        reason='PE 酒瓶精确规则',
        source='factory',
        sources=['factory', 'fallback'],
        fallback_reference=1.6
    )
```

---

## 8. Adapters 适配层

### 8.1 RuleMethodAdapter：JSON ↔ 规则字符串

```python
class RuleMethodAdapter:
    """RuleMethod.rule_content JSON ↔ RuleNet 字符串"""

    @staticmethod
    def to_rule_string(rule_method: dict) -> str:
        """
        JSON → 'IF X_low THEN Z_add_10'
        用于 fuzzkit fuzzykit 解析
        """
        conditions = rule_method.get('conditions', [])
        adjustments = rule_method.get('adjustments', [])

        # 构造条件部分（兼容 fuzzy_level / operator-value / defect）
        cond_parts = []
        for cond in conditions:
            if cond.get('fuzzy_level'):
                cond_parts.append(f"{cond['param']}_{cond['fuzzy_level']}")
            elif cond.get('defect'):
                cond_parts.append(f"{cond['defect']}_{cond['fuzzy_level']}")
            elif cond.get('operator'):
                # 数值比较转化为模糊级别
                cond_parts.append(f"{cond['param']}_{_value_to_fuzzy_level(cond['value'])}")
        cond_str = ' AND '.join(cond_parts)

        # 构造结论部分
        adj_parts = []
        for adj in adjustments:
            if adj.get('type') == 'tip':
                continue  # 弹窗规则走 ParticularRules
            action = adj['action']
            if adj.get('value_type') == 'percent':
                adj_parts.append(f"{adj['param']}_{_action_to_str(action)}__{adj['value']}%")
            elif 'level' in adj:
                adj_parts.append(f"{adj['param']}_{_action_to_str(action)}_{adj['level']}")
            else:
                adj_parts.append(f"{adj['param']}_{_action_to_str(action)}_{adj['value']}")
        adj_str = ' AND '.join(adj_parts)

        return f"IF {cond_str} THEN {adj_str}"

    @staticmethod
    def from_rule_string(rule_str: str) -> dict:
        """反向：字符串 → JSON（用于 Rule.dat 导入）"""
        # 逆向解析
        ...
```

### 8.2 RuleKeywordAdapter：RuleKeyword → FuzzyFeature dict

```python
class RuleKeywordAdapter:
    """RuleKeyword 模型 → FuzzyFeature 输入 dict"""

    @staticmethod
    def to_fuzzy_dict(keyword: dict) -> dict:
        """
        RuleKeyword (Django Model) → FuzzyFeature dict
        """
        return {
            'keyword': keyword['keyword_name'],
            'lvl': keyword['fuzzy_level'],        # 3 或 5
            'min_val': keyword['range_min'],
            'max_val': keyword['range_max'],
            'step': keyword.get('step') or 1,    # 新增字段，迁移期可能为空
        }

    @staticmethod
    def get_keywords_by_names(names: List[str]) -> List[dict]:
        """按变量名查询 RuleKeyword"""
        keywords = RuleKeyword.objects.filter(
            keyword_name__in=names
        ).values('keyword_name', 'fuzzy_level', 'range_min', 'range_max', 'step', 'unit')

        return [RuleKeywordAdapter.to_fuzzy_dict(kw) for kw in keywords]
```

---

## 9. 典型场景示例

### 9.1 PE 酒瓶短射（最复杂场景）

**数据库配置**：
```python
RuleLibrary(code='packaging', owner_type='system', priority=10)
RuleLibrary(code='general', owner_type='system', priority=0)

RuleMethod(
    rule_library=packaging_lib,
    polymer_category='PE', product_category='酒瓶',  # L1 精确
    defect_name='SHORTSHOT',
    rule_level='factory',                              # 工厂级
    priority=10.0,
    rule_content={
        "conditions": [{"param": "hold_time", "fuzzy_level": "low"}],
        "adjustments": [{
            "type": "param", "param": "hold_time",
            "action": "add", "value": 4, "value_type": "absolute"
        }]
    }
)

RuleMethod(
    rule_library=general_lib,
    defect_name='SHORTSHOT',
    rule_level='fallback',
    priority=1.0,
    rule_content={
        "conditions": [{"param": "hold_time", "fuzzy_level": "low"}],
        "adjustments": [{
            "type": "param", "param": "hold_time",
            "action": "add", "level": "low"             # 模糊级别
        }]
    }
)
```

**推理执行**：
```
1. FuzzyEngine.recommend({polymer='PE', product='酒瓶', defect='SHORTSHOT'})
2. _resolve_libraries() → [packaging, general]
3. packaging 命中: 1 条工厂规则 (priority=10)
4. general 命中: 1 条兜底规则 (priority=1)
5. NumTskRuleNet 推理工厂级 → hold_time +3.4s
6. FuzzyRuleNet 推理兜底层 → hold_time +1.6s
7. 合并: 工厂级胜出 → 输出 hold_time 从 3.5→6.9
   sources = ['factory', 'fallback']
```

### 9.2 新机型无特定规则（兜底层单独生效）

**数据库配置**：
```python
# 只有通用规则库
RuleLibrary(code='general', owner_type='system', priority=0)

RuleMethod(
    rule_library=general,
    defect_name='SHRINKAGE',
    rule_level='fallback',
    priority=1.0,
    rule_content={
        "conditions": [{"param": "mold_temp", "fuzzy_level": "low"}],
        "adjustments": [{
            "type": "param", "param": "mold_temp",
            "action": "add", "level": "mid"
        }]
    }
)
```

**推理执行**：
```
1. FuzzyEngine 加载规则（无特定库）
2. 工厂级规则 = [] → 跳过 NumTskRuleNet
3. FuzzyRuleNet 推理兜底 → mold_temp +模糊级 mid
4. sources = ['fallback']  ← 仅兜底层
```

---

## 10. 实施清单

### 10.1 阶段 1：数据模型补全

- [ ] **RuleKeyword 加 `step` 字段**（FloatField, null=True）
- [ ] **RuleMethod 加 `rule_level` 字段**（factory/fallback）
- [ ] **写 migration 文件**（`0001_add_fuzzy_fields.py`）
- [ ] **数据迁移命令 `init_fuzzy_ranges`**
  - 从 `old/mdprocess/utils/fuzzykit/range_test.csv` 读
  - 通过字段名映射匹配 RuleKeyword
  - 填充 step 字段
  - 支持 `--dry-run` 与 `--force`
- [ ] **数据迁移命令 `init_rule_level`**
  - 给现有规则设置 rule_level
  - 建议 default='factory'

### 10.2 阶段 2：fuzzy_core 算法层

- [ ] **macros.py**：追加 HS_MAPPING_DICT、HS_DEFECT_DICT、ADJUST_ACTIONS
- [ ] **functional.py**：追加 gauss_mf / tri_mf / trap_mf
- [ ] **models/nets.py**：迁移
  - FuzzyFeature（含 gauss/tri 模式）
  - FuzzyRule（字符串规则解析）
  - NumTskRule（结论数值/百分比解析）
  - FuzzyRuleNet (Mamdani, ~295 行)
  - NumTskRuleNet (~322 行)
  - ParticularRules (~50 行)
  - TskRuleNet：占位类即可（不实现）
- [ ] **utils/translate.py**：迁 defect_translate / rule_standard

### 10.3 阶段 3：适配层

- [ ] **adapters.py**：RuleMethodAdapter（JSON ↔ 字符串）
- [ ] **adapters.py**：RuleKeywordAdapter（模型 ↔ FuzzyFeature）
- [ ] **rules/ 目录**：fuzzy_rules.txt 初始样本
  - 短射、飞边各 2-3 条典型规则
- [ ] **RuleQueryService**：路由层实现（三级特异性 + 库层级继承）

### 10.4 阶段 4：FuzzyEngine.recommend 串联

- [ ] **fuzzy_engine.py**：recommend() 实现
  - 按上下文拉规则（双层分流）
  - 构造 NumTskRuleNet + FuzzyRuleNet
  - 并行推理
  - 合并（方案 B 消解策略）
- [ ] **单测**：demo 数据跑通两条规则

### 10.5 阶段 5：种子数据与文档

- [ ] **种子 RuleMethod**：2-3 条样例规则
  - 1 条工厂级（PE 酒瓶精确）
  - 1 条兜底层（默认规则）
- [ ] **更新设计文档**：标记完成情况

---

## 11. FAQ（开发中常见疑问）

### Q1: NumTskRuleNet 能处理 `_add_low`（模糊级别）形式的规则吗？

**答：不能。** NumTskRuleNet 在构造期做 `float(value_level) * action`，无法解析 `low/mid/high` 字符串。需要做：
- 选项 A：路由到 FuzzyRuleNet（推荐）
- 选项 B：在 RuleMethodAdapter 里把模糊级转成 step 倍数（如 `low → 0.33*step`, `mid → 0.66*step`, `high → 1.0*step`）

### Q2: 工厂级和兜底级的激活度都很低，怎么处理？

**答**：触发"无有效规则"分支，recommend() 返回 `[]`。调用方 `ProcessRecommendationService` 用兜底逻辑处理。

### Q3: priority 字段是百分比还是绝对值？

**答**：FloatField，默认 1.0。在 NumTskRuleNet 内部用作 `priority_array`，与激活度加权求和。所以 priority 越大，规则权重越高。

### Q4: 调整量是数值（add_10）和百分比（add_5%）能共存吗？

**答**：能。NumTskRuleNet 通过 `rule_classify` 字段区分（0=绝对值, 1=百分比）。推理时：
- 绝对值：直接用
- 百分比：`sol_matrix * cur_params`

### Q5: 弹窗规则（adjust/popup）什么时候触发？

**答**：通过 ParticularRules 类特殊处理。ParticularRules 不做 fuzzy 计算，只识别关联的 defect、收集输出文本。调用方在 UI 层展示。

### Q6: TskRuleNet 真的不迁吗？

**答**：**不迁**。它是死代码（命名误导），项目从未真实用过代数式规则。`nets.py` 里只保留占位类即可。

### Q7: 库层级继承怎么使用？

**答**：通过 `RuleLibrary.parent_library` 字段。具体：
```python
# 顶层：包装容器大类
RuleLibrary(code='packaging', parent_library=None, priority=10)
# 子库：PE 材料（继承 packaging）
RuleLibrary(code='PE', parent_library=packaging, priority=20)
# 孙子库：PE 酒瓶（继承 PE）
RuleLibrary(code='PE_bottle', parent_library=PE, priority=30)
```
加载规则时把当前库的 parent chain 全拉下来。

### Q8: 跨 polymer 复用不想用库继承怎么办？

**答**：可以在 RuleMethod 上把 polymer_category 留空（None），这样所有 PE、PP 材料都会匹配。但要小心：用默认规则比精确规则优先级低（按 priority 协议）。

### Q9: 测试时怎么构造 demo 数据？

**答**：
```python
# 1 条工厂规则 + 1 条兜底规则 + 2 个 RuleKeyword
from process.engines.fuzzy.fuzzy_core.models import FuzzyRuleNet, NumTskRuleNet

net = NumTskRuleNet(
    rule_array=[
        {"rule_description": "IF inj_pres_1_low THEN inj_pres_1_add_10",
         "rule_code": "test1"}
    ],
    keyword_array=[
        {"keyword": "inj_pres_1", "lvl": 3, "min_val": 0, "max_val": 200, "step": 20}
    ],
    priority_array=[1.0]
)
results, _ = net.predict({"inj_pres_1": 30}, top_k=1)
# 期待: 结果中含 inj_pres_1 的调整建议
```

---

## 附录 A：迁移文件清单

| 操作 | 路径 | 状态 |
|------|------|------|
| 修改 | `process/models/rules.py` | RuleKeyword 加 step、RuleMethod 加 rule_level |
| 新增 | `bootstrap/management/commands/init_fuzzy_ranges.py` | 迁移 step |
| 新增 | `bootstrap/management/commands/init_rule_level.py` | 初始化 rule_level |
| 修改 | `process/engines/fuzzy/fuzzy_core/macros.py` | 加 HS_MAPPING_DICT 等 |
| 修改 | `process/engines/fuzzy/fuzzy_core/functional.py` | 加 gauss/tri/trap MF |
| 修改 | `process/engines/fuzzy/fuzzy_core/models/nets.py` | 完整重写 |
| 新增 | `process/engines/fuzzy/fuzzy_core/utils/translate.py` | defect_translate 等 |
| 新增 | `process/engines/fuzzy/adapters.py` | RuleMethodAdapter / RuleKeywordAdapter |
| 新增 | `process/engines/fuzzy/services/rule_query_service.py` | 路由服务 |
| 新增 | `process/engines/fuzzy/rules/fuzzy_rules.txt` | 初始规则样本 |
| 修改 | `process/engines/fuzzy/fuzzy_engine.py` | recommend() 重写 |

---

## 附录 B：参考资料

- 迁移实施方案：[`fuzzy-engine-migration-design.md`](./fuzzy-engine-migration-design.md)
- 老 fuzzykit 源码：`old/mdprocess/utils/fuzzykit/fuzzy_core/`
- 老 fuzzykit 调用：`old/mdprocess/services/process_optimize_service.py` L447-815
- Rule.dat 样本：`old/mdprocess/utils/fuzzykit/fuzzy_core/dataset/Rule.dat`（273 条全模糊规则）
- Range 数据：`old/mdprocess/utils/fuzzykit/range_test.csv`

---

*最后更新：2026-07-02*
