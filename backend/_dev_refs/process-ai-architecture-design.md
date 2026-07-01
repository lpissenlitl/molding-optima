# 工艺智能系统 - 完整架构设计文档

> 本文档描述了 molding-optima 工艺智能系统的完整数据流和 AI 模块架构设计。

## 1. 设计理念

### 1.1 核心理念

1. **数据锚点稳定**：以 `ProcessCondition + ProcessParameter` 为核心锚点，所有扩展基于此结构插拔式扩展
2. **结构化数据**：尽可能将工艺相关数据结构化存储，使数据具有完整上下文意义
3. **可插拔 AI 引擎**：不同 AI 算法（模糊推理、规则挖掘、大模型）通过统一接口接入
4. **自学习闭环**：系统随数据积累自动学习成长，越用越智能

### 1.2 与 molding-expert 的关系

- molding-optima 是注塑工艺智能优化系统的重构项目
- molding-expert 是当前最新设计，是本次重构的设计源头
- 本架构设计遵循"同步对齐"原则：相同功能保持一致，差异只在 molding-optima 独有模块

## 2. 完整数据流

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           工艺智能系统 - 完整数据流                            │
└─────────────────────────────────────────────────────────────────────────────┘

                                数据层
    ┌──────────────────────────────────────────────────────────────────┐
    │                     ProcessCondition                              │
    │              (模具+机台+材料+注射单元+状态)                         │
    └─────────────────────────┬────────────────────────────────────────┘
                              │
                              ▼
    ┌──────────────────────────────────────────────────────────────────┐
    │                     ProcessParameter                              │
    │  (工艺参数 + parent_param 版本树 + param_source 标记来源)           │
    │                                                                       │
    │  版本树自动记录调整历史，版本差异 = 调整策略                          │
    └──────┬─────────────────────────┬─────────────────────┬────────────┘
           │                         │                     │
           ▼                         ▼                     ▼
    ┌─────────────┐         ┌─────────────┐       ┌─────────────┐
    │ TuningRecord│         │   AI-REC    │       │  (扩展插槽)  │
    │  调试记录    │         │  AI推荐     │       │             │
    │  - 缺陷反馈  │         │  - fuzzy    │       │             │
    │  - 试模结果  │         │  - llm      │       │             │
    └─────────────┘         └──────┬──────┘       └─────────────┘
           │                       │
           │                       ▼
           │              ┌─────────────────┐
           │              │   规则学习模块   │
           │              │ (自学习闭环核心) │
           │              └────────┬────────┘
           │                       │
           ▼                       ▼
    ┌─────────────────────────────────────┐
    │            规则库                    │
    │  ┌─────────────┬─────────────┐      │
    │  │ 初始化规则库 │ 优化规则库    │      │
    │  │ (材料+机台   │ (缺陷→参数   │      │
    │  │  →初始参数)  │  调整策略)   │      │
    │  └─────────────┴─────────────┘      │
    └─────────────────────────────────────┘
```

## 3. 数据模型设计

### 3.1 分层结构

| 场景 | 组合方式 | 说明 |
|------|----------|------|
| **1. 基础工艺存储** | `Condition + Parameter` | 仅保存工艺参数，方便调用 |
| **2. 调参过程追踪** | `Condition + Parameter + TuningRecord` | 记录调试历史、缺陷反馈 |
| **3. 工艺模板/引导** | `Condition + Parameter` | 作为模板引导用户 |
| **4. AI 推荐** | `Condition + Parameter + AI-REC` | 基于缺陷反馈的智能推荐 |
| **5. (未来扩展)** | `Condition + Parameter + XXX` | 可插拔的扩展模块 |

### 3.2 现有模型支持

**ProcessCondition** - 工艺条件（某一射）

```python
class ProcessCondition(BusinessBaseModel):
    # 状态信息
    status = CharField()  # draft/testing/approved/rejected/obsolete
    
    # 基本信息
    condition_code = CharField()
    origin_type = CharField()  # manual_creation/template_based/ai_recommendation...
    process_context_snapshot = JSONField()  # 工艺快照
    
    # 模具信息
    mold = ForeignKey("masterdata.Mold")
    shot_index = IntegerField()  # 注射次数（多射）
    
    # 设备信息
    injection_machine = ForeignKey("masterdata.InjectionMoldingMachine")
    injection_index = IntegerField()  # 注射单元
    
    # 材料信息
    polymer = ForeignKey("masterdata.Polymer")
```

**ProcessParameter** - 工艺参数

```python
class ProcessParameter(BusinessBaseModel):
    process_condition = ForeignKey("ProcessCondition")
    
    # 版本关系（支持树形结构）
    parent_param = ForeignKey("self", null=True)  # 父版本
    seq_idx = IntegerField()  # 序列号
    
    # 参数来源
    param_source = CharField()  # manual/algorithm_init/manual_adjusted...
    
    # 工艺参数字段（60+ 个）
    inj_pres_1, inj_spd_1, hold_pres_1, ...
```

### 3.3 新增模型

**TuningRecord** - 调试记录

```python
class TuningRecord(BusinessBaseModel):
    """
    工艺调参记录 - 记录一次调参与试模结果
    """
    
    process_parameter = ForeignKey("ProcessParameter")
    
    # 缺陷反馈（JSON数组）
    defect_feedbacks = JSONField(default=list)
    """
    [
        {
            "defect_type": "短射",
            "level": "medium",
            "position": "产品边缘",
            "image_url": "..."
        }
    ]
    """
    
    # 调参备注
    note = CharField(max_length=500)
    
    # 结果：pending / qualified / unqualified
    result = CharField(max_length=20)
    
    # 当次参数快照（冗余存储）
    parameter_snapshot = JSONField()
```

**AIRecommendation** - AI 推荐方案

```python
class AIRecommendation(BusinessBaseModel):
    """
    AI 推荐方案 - 可扩展的 AI 推荐插槽
    """
    
    process_parameter = ForeignKey("ProcessParameter")
    
    # 推荐来源类型
    SOURCE_TYPES = [
        ('fuzzy_rule', '模糊规则推理'),
        ('rule_miner', '规则挖掘学习'),
        ('llm', '大语言模型'),
        ('doe', '实验设计优化'),
    ]
    source_type = CharField(max_length=20, choices=SOURCE_TYPES)
    
    # 推荐方案（JSON 存储）
    recommendations = JSONField(default=list)
    """
    [
        {
            "defect": "短射",
            "param": "inj_pres_1",
            "action": "increase",
            "confidence": 0.85
        }
    ]
    """
    
    # 是否已采纳
    is_adopted = BooleanField(default=False)
    adopted_param = ForeignKey("ProcessParameter", null=True)
```

## 4. 智能模块架构

### 4.1 模块划分

```
backend/process/
├── models/
│   ├── process_condition.py
│   ├── process_parameter.py
│   ├── tuning_record.py           # 新增
│   ├── recommendation.py         # 新增：存储推荐结果（关联 ProcessParameter）
│   └── rules.py                   # 新增：规则库模型（RuleLibrary/RuleKeyword/RuleMethod/MinedRule/ExpertRule）
│
├── services/                          # 业务服务层
│   ├── process_service.py             # 基础 CRUD
│   ├── process_tuning_service.py      # 调试记录服务
│   └── process_recommendation_service.py  # 对外推荐服务接口（HTTP接口层）
│
├── engines/                           # 算法引擎层（与 services 同级）
│   ├── __init__.py
│   ├── base_engine.py                 # 引擎基类（策略模式）
│   │
│   ├── expert/                        # 专家系统引擎（基于专家规则推导初始工艺）
│   │   ├── __init__.py
│   │   ├── expert_engine.py            # 专家系统推理主逻辑
│   │   └── expert_rules/               # 专家规则库
│   │       ├── rule_loader.py          # 规则加载器
│   │       └── material_machine_rules.py  # 材料-机台-产品规则
│   │
│   ├── fuzzy/                         # 模糊推理引擎（缺陷修正）
│   │   ├── __init__.py
│   │   ├── fuzzy_engine.py            # 模糊推理主逻辑
│   │   └── fuzzy_core/                # 迁移自 old/mdprocess/utils/fuzzykit
│   │       ├── functional.py
│   │       ├── macros.py
│   │       └── models/
│   │           ├── __init__.py
│   │           └── nets.py
│   │
│   ├── llm/                          # 大模型推理引擎
│   │   ├── __init__.py
│   │   └── llm_engine.py
│   │
│   └── rule_miner/                   # 规则挖掘引擎（自学习核心）
│       ├── __init__.py
│       └── rule_miner_engine.py
│
│   # === 以下引擎预留扩展 ===
│   ├── doe/                          # 实验设计引擎（预留）
│   ├── ga/                           # 遗传算法引擎（预留）
│   └── neural/                        # 神经网络引擎（预留）
│
└── views/
    └── ...
```

**目录说明：**

| 目录 | 说明 |
|------|------|
| `models/` | 数据模型 |
| `models/rules.py` | 规则库模型（RuleLibrary/RuleKeyword/RuleMethod/MinedRule/ExpertRule） |
| `models/recommendation.py` | 推荐结果（关联 ProcessParameter） |
| `services/` | 业务服务层，提供对外 HTTP 接口 |
| `engines/` | 算法引擎层，提供推理能力（对 services 透明） |
| `engines/expert/` | 专家系统引擎，根据模具/材料/产品/机台推理初始工艺参数 |
| `engines/fuzzy/` | 模糊推理引擎，包含主逻辑和 fuzzy_core 子模块 |
| `engines/llm/` | 大模型推理引擎 |
| `engines/rule_miner/` | 规则挖掘引擎 |

**模型区分：**

| 文件 | 模型 | 归属 | 说明 |
|------|------|------|------|
| `recommendation.py` | Recommendation | Process 模块 | 存储推荐结果，关联 ProcessParameter |
| `rules.py` | RuleLibrary/RuleKeyword/RuleMethod/MinedRule/ExpertRule | AI 推理模块 | 规则库定义，供 engines 调用 |

### 4.2 可插拔引擎设计

#### 4.2.1 引擎基类

```python
# backend/process/services/ai/base_engine.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Recommendation:
    """推荐结果"""
    param_name: str
    current_value: float
    recommended_value: float
    confidence: float
    reason: str
    source: str  # 'fuzzy' / 'rule_miner' / 'llm'

class AIEngineBase(ABC):
    """AI 算法引擎基类"""
    
    engine_name: str
    engine_type: str  # 'initialization' / 'optimization'
    
    @abstractmethod
    def recommend(self, context: dict) -> List[Recommendation]:
        """
        根据上下文返回推荐结果
        context = {
            'process_condition': {...},
            'process_parameter': {...},
            'defect_feedbacks': [...],
            'tuning_history': [...],
        }
        """
        pass
    
    @abstractmethod
    def is_available(self, context: dict) -> bool:
        """判断当前引擎是否适用于此场景"""
        pass


class EngineRegistry:
    """引擎注册中心（支持策略模式动态切换）"""
    
    _engines: dict[str, AIEngineBase] = {}
    
    @classmethod
    def register(cls, engine_type: str, engine: AIEngineBase):
        cls._engines[engine_type] = engine
    
    @classmethod
    def get_engine(cls, engine_type: str) -> Optional[AIEngineBase]:
        return cls._engines.get(engine_type)
    
    @classmethod
    def get_available_engines(cls, context: dict) -> List[AIEngineBase]:
        return [e for e in cls._engines.values() if e.is_available(context)]
```

#### 4.2.2 专家系统引擎

基于专家规则，根据模具/材料/产品/机台信息推理初始工艺参数。当前 `process_generate.py` 是硬编码实现，未来应升级为规则驱动、数据可学习的专家系统引擎：

```python
class ExpertEngine(AIEngineBase):
    """专家系统引擎 - 基于专家规则推理初始工艺参数"""
    
    engine_name = "专家系统"
    engine_type = "initialization"
    
    def __init__(self):
        self.rule_loader = RuleLoader()
    
    def recommend(self, context: dict) -> dict:
        """
        根据上下文推理初始工艺参数
        
        context = {
            'mold': {...},           # 模具信息（浇口类型、流道重量、产品壁厚等）
            'machine': {...},         # 机台信息（驱动类型、螺杆直径、最大压力等）
            'polymer': {...},         # 材料信息（类别、推荐温度、密度等）
            'product': {...},         # 产品信息（重量、壁厚、流长等）
        }
        
        Returns:
            {
                'injection_params': {...},
                'holding_params': {...},
                'cooling_params': {...},
                'metering_params': {...},
                'temperature_params': {...},
            }
        """
        # 1. 根据产品类型和材料类型选择推理策略
        polymer_category = context['polymer'].get('category')
        product_type = context['product'].get('type')
        drive_system = context['machine'].get('drive_system')
        
        # 2. 加载对应规则
        rules = self.rule_loader.load_expert_rules(
            polymer_category=polymer_category,
            product_type=product_type,
            drive_system=drive_system
        )
        
        # 3. 执行推理
        result = self._infer(context, rules)
        
        return result
    
    def is_available(self, context: dict) -> bool:
        return all([
            context.get('mold'),
            context.get('machine'),
            context.get('polymer'),
            context.get('product'),
        ])
```

**专家规则示例：**

```
IF polymer.category = '结晶型' AND product.max_thickness > 2.0
THEN hold_pressure = max_pressure * 0.7
     cooling_time = 5 * max_thickness

IF machine.drive_system = '电动机' AND polymer.category = '无定形'
THEN injection_speed = max_speed * 0.4
     metering_back_pressure = recommend_back_pressure

IF product.gate_type = '点浇口'
THEN hold_time = 0.5 + 0.1 * product.ave_thickness
```

**规则存储方式：**

规则支持两种存储方式，可互补并不冲突：

| 存储方式 | 适用场景 | 优点 | 缺点 |
|----------|----------|------|------|
| **文件存储** (`expert_rules/*.json`) | 初始规则、通用规则 | 易于版本管理、可静态加载 | 不便于动态编辑 |
| **数据库存储** (ExpertRule 表) | 企业定制规则、动态规则 | 支持可视化编辑、运行时修改 | 需要配套管理界面 |

**存储结构示例（数据库）：**

```python
class ExpertRule(BusinessBaseModel):
    """专家规则表"""
    
    # 规则标识
    rule_code = CharField(max_length=50, unique=True)
    rule_name = CharField(max_length=100)
    
    # 规则条件
    condition = JSONField()  # 触发条件
    """
    {
        "polymer.category": "结晶型",
        "product.max_thickness": {">": 2.0}
    }
    """
    
    # 规则结论
    conclusion = JSONField()  # 参数推理结论
    """
    {
        "hold_pressure": {"formula": "max_pressure * 0.7"},
        "cooling_time": {"formula": "5 * max_thickness"}
    }
    """
    
    # 规则元数据
    priority = IntegerField(default=0)  # 优先级
    confidence = FloatField(default=1.0)  # 置信度
    source = CharField(max_length=20)  # 'expert' / 'rule_miner' / 'llm'
    is_active = BooleanField(default=True)
    
    # 版本管理
    version = IntegerField(default=1)
    parent_rule = ForeignKey('self', null=True)  # 规则版本树
```

**规则加载器设计：**

```python
class RuleLoader:
    """规则加载器 - 支持文件和数据库双源加载"""
    
    def __init__(self):
        self._file_rules = {}
        self._db_rules = []
    
    def load_rules(self):
        # 1. 加载文件规则（优先级高）
        self._load_file_rules()
        
        # 2. 加载数据库规则（可覆盖文件规则）
        self._load_db_rules()
    
    def _load_file_rules(self):
        """从 expert_rules/ 目录加载 JSON 规则文件"""
        rules_dir = Path(__file__).parent / 'expert_rules'
        for rule_file in rules_dir.glob('*.json'):
            with open(rule_file, encoding='utf-8') as f:
                rules = json.load(f)
                self._file_rules.update({r['rule_code']: r for r in rules})
    
    def _load_db_rules(self):
        """从数据库加载活动规则"""
        db_rules = ExpertRule.objects.filter(is_active=True).order_by('-priority')
        self._db_rules = list(db_rules)
    
    def get_rule(self, rule_code: str) -> dict:
        """获取规则，数据库规则优先于文件规则"""
        return self._db_rules.get(rule_code) or self._file_rules.get(rule_code)
    
    def get_matching_rules(self, context: dict) -> List[dict]:
        """获取匹配当前上下文的规则列表"""
        matched = []
        for rule in itertools.chain(self._db_rules, self._file_rules.values()):
            if self._match_condition(rule['condition'], context):
                matched.append(rule)
        return sorted(matched, key=lambda r: -r.get('priority', 0))
```

**规则来源演进：**
1. **阶段一**：专家总结的固定规则（当前状态）
2. **阶段二**：规则入库，支持可视化编辑
3. **阶段三**：基于历史成功工艺数据学习新规则
4. **阶段四**：与 RuleMiner 联动，自动优化专家规则

#### 4.2.3 模糊推理引擎

迁移现有 `nets.py` 实现：

```python
class FuzzyEngine(AIEngineBase):
    """模糊推理引擎 - 适用于已知规则的场景"""
    
    engine_name = "模糊推理"
    engine_type = "optimization"
    
    def __init__(self):
        self.rule_net = None
        self._load_rules()
    
    def _load_rules(self):
        # 从数据库/文件加载规则
        rules = rule_service.load_defect_rules()
        keywords = rule_service.load_keyword_ranges()
        self.rule_net = NumTskRuleNet(rules, keywords)
    
    def recommend(self, context: dict) -> List[Recommendation]:
        defects = context.get('defect_feedbacks', [])
        if not defects:
            return []
        
        # 转换为模糊推理输入格式
        x = self._build_fuzzy_input(context)
        results, _ = self.rule_net.predict(x, top_k=10)
        
        return [
            Recommendation(
                param_name=param,
                current_value=x.get(param, 0),
                recommended_value=value,
                confidence=activation,
                reason=rule_desc,
                source='fuzzy'
            )
            for rule_desc, activation, adjustments in results
            for param, value in adjustments.items()
        ]
    
    def is_available(self, context: dict) -> bool:
        return len(context.get('defect_feedbacks', [])) > 0
```

#### 4.2.3 规则挖掘引擎（自学习核心）

```python
class RuleMinerEngine(AIEngineBase):
    """规则挖掘引擎 - 从历史数据中学习规则"""
    
    engine_name = "规则挖掘"
    engine_type = "optimization"
    
    def __init__(self):
        self.min_confidence = 0.7
        self.min_support = 0.05
    
    def recommend(self, context: dict) -> List[Recommendation]:
        # 获取历史成功案例
        tuning_records = context.get('tuning_history', [])
        successful_cases = [r for r in tuning_records if r['result'] == 'qualified']
        
        if len(successful_cases) < 10:
            return []  # 数据不足
        
        # 使用关联规则学习提取规则
        rules = self._mine_rules(successful_cases)
        
        recommendations = []
        for rule in rules:
            if rule.confidence >= self.min_confidence:
                recommendations.append(Recommendation(
                    param_name=rule.param,
                    current_value=context['process_parameter'].get(rule.param),
                    recommended_value=rule.recommended_value,
                    confidence=rule.confidence,
                    reason=f"基于 {rule.support} 条成功案例学习",
                    source='rule_miner'
                ))
        
        return recommendations
    
    def _mine_rules(self, cases: list) -> List[MinedRule]:
        """
        使用 FP-Growth 或 Apriori 算法从成功案例中挖掘规则
        
        输入: [(缺陷类型, 参数值, 试模结果), ...]
        输出: [{param, condition, recommended_value, confidence, support}, ...]
        """
        pass
    
    def is_available(self, context: dict) -> bool:
        return len(context.get('tuning_history', [])) >= 10
```

**规则挖掘触发机制：**

规则挖掘支持两种触发模式，不冲突可并存：

| 触发模式 | 说明 | 使用场景 |
|----------|------|----------|
| **定时任务** | 周期性自动执行（如每天凌晨） | 系统性规则学习、持续优化 |
| **手动触发** | 用户/管理员按需触发 | 特定缺陷规则急需优化、特定产品线规则补充 |

**触发机制实现：**

```python
# 定时任务触发
class RuleMinerScheduler:
    """规则挖掘定时任务"""
    
    @staticmethod
    @scheduled_task(cron='0 2 * * *')  # 每天凌晨 2 点
    def run_daily_mining():
        """每日规则挖掘"""
        engine = RuleMinerEngine()
        engine.run_full_mine()


# 手动触发接口
class RuleMinerService:
    """规则挖掘服务 - 支持手动触发"""
    
    def trigger_mining(
        self,
        polymer_category: str = None,
        defect_type: str = None,
        min_records: int = 10
    ) -> dict:
        """
        手动触发规则挖掘
        
        Args:
            polymer_category: 仅挖掘特定材料类别规则
            defect_type: 仅挖掘特定缺陷类型规则
            min_records: 最少记录数
        
        Returns:
            {'mined_rules': [...], 'pending_review': [...]}
        """
        # 1. 查询符合条件的 TuningRecord
        records = self._query_records(polymer_category, defect_type, min_records)
        
        # 2. 执行规则挖掘
        engine = RuleMinerEngine()
        rules = engine.mine_rules(records)
        
        # 3. 规则评估
        reviewed_rules = self._evaluate_rules(rules)
        
        return {
            'mined_rules': reviewed_rules['high_confidence'],
            'pending_review': reviewed_rules['needs_review']
        }
    
    def approve_rule(self, rule_id: int):
        """专家审核通过后入库"""
        rule = MinedRule.objects.get(id=rule_id)
        rule.status = 'approved'
        rule.save()
        
        # 同步到 ExpertRule 表
        self._sync_to_expert_rule(rule)
```

#### 4.2.4 大模型推理引擎（未来扩展）

```python
class LLMEngine(AIEngineBase):
    """大模型推理引擎"""
    
    engine_name = "大模型推理"
    engine_type = "optimization"
    
    def __init__(self, model_name: str = "gpt-4"):
        self.model_name = model_name
    
    def recommend(self, context: dict) -> List[Recommendation]:
        # RAG: 从 TuningRecord 中检索相似案例
        similar_cases = self._retrieve_similar_cases(context)
        
        # 构建 prompt
        prompt = self._build_prompt(context, similar_cases)
        
        # 调用 LLM
        response = self._call_llm(prompt)
        
        # 解析结果
        return self._parse_llm_response(response)
    
    def _retrieve_similar_cases(self, context: dict) -> list:
        """向量检索相似历史案例"""
        pass
    
    def _build_prompt(self, context: dict, similar_cases: list) -> str:
        """构建 LLM prompt"""
        pass
    
    def _parse_llm_response(self, response: str) -> List[Recommendation]:
        """解析 LLM 输出"""
        pass
    
    def is_available(self, context: dict) -> bool:
        # 需要配置 LLM API
        return bool(settings.LLM_API_KEY)
```

#### 4.2.5 其他引擎预留

系统预留以下引擎扩展点，可根据需要逐步实现：

| 引擎 | 类型 | 说明 | 适用场景 |
|------|------|------|----------|
| `DoeEngine` | optimization | 实验设计引擎（DOE） | 参数范围探索、最优参数组合搜索 |
| `GaEngine` | optimization | 遗传算法引擎 | 多参数全局优化 |
| `RbfEngine` | optimization | 径向基函数网络 | 复杂非线性工艺建模 |
| `NeuralEngine` | optimization | 神经网络预测 | 大数据量下的参数预测 |

**扩展方式：**

所有新引擎只需继承 `AIEngineBase` 并实现对应接口，即可通过 `EngineRegistry.register()` 接入系统。

```python
class DoeEngine(AIEngineBase):
    """实验设计引擎 - 预留扩展"""
    
    engine_name = "实验设计"
    engine_type = "optimization"
    engine_subtype = "doe"  # 子类型标识
    
    def recommend(self, context: dict) -> List[Recommendation]:
        # 实现 DOE 算法
        pass
    
    def is_available(self, context: dict) -> bool:
        return settings.DOE_ENABLED and len(context.get('tuning_history', [])) >= 5
```

### 4.3 推荐服务（统一入口）

```python
# backend/process/services/ai/recommendation_service.py

class RecommendationService:
    """推荐服务 - 统一入口"""
    
    def __init__(self):
        # 注册引擎（按优先级排序）
        EngineRegistry.register('fuzzy', FuzzyEngine())
        EngineRegistry.register('rule_miner', RuleMinerEngine())
        EngineRegistry.register('llm', LLMEngine())
    
    def get_recommendations(
        self,
        process_condition_id: int,
        defect_feedbacks: list,
        engine_types: list = None
    ) -> dict:
        """
        获取推荐结果
        
        Args:
            process_condition_id: 工艺条件 ID
            defect_feedbacks: 缺陷反馈列表
            engine_types: 指定使用的引擎类型，None 表示使用所有可用引擎
        
        Returns:
            {
                'recommendations': [...],
                'engine_sources': {'模糊推理': [...], '规则挖掘': [...]},
                'best_recommendation': {...}
            }
        """
        # 构建上下文
        context = self._build_context(process_condition_id, defect_feedbacks)
        
        # 获取可用引擎
        if engine_types:
            engines = [EngineRegistry.get_engine(t) for t in engine_types]
        else:
            engines = EngineRegistry.get_available_engines(context)
        
        # 并行调用各引擎
        all_recommendations = []
        engine_results = {}
        
        for engine in engines:
            if engine and engine.is_available(context):
                recs = engine.recommend(context)
                engine_results[engine.engine_name] = recs
                all_recommendations.extend(recs)
        
        # 合并去重（同一参数保留最高置信度）
        merged = self._merge_recommendations(all_recommendations)
        
        return {
            'recommendations': merged,
            'engine_sources': engine_results,
            'best_recommendation': merged[0] if merged else None
        }
    
    def _build_context(self, condition_id: int, defect_feedbacks: list) -> dict:
        """构建推理上下文"""
        condition = ProcessCondition.objects.get(id=condition_id)
        parameter = condition.process_parameters.filter(is_deleted=False).first()
        tuning_history = TuningRecord.objects.filter(
            process_parameter=parameter
        ).order_by('-created_at')[:50]
        
        return {
            'process_condition': condition.to_dict(),
            'process_parameter': parameter.to_dict() if parameter else {},
            'defect_feedbacks': defect_feedbacks,
            'tuning_history': [t.to_dict() for t in tuning_history],
        }
    
    def _merge_recommendations(self, recommendations: List[Recommendation]) -> List[Recommendation]:
        """合并同一参数的多个推荐，保留最高置信度"""
        merged_dict = {}
        for rec in recommendations:
            key = rec.param_name
            if key not in merged_dict or rec.confidence > merged_dict[key].confidence:
                merged_dict[key] = rec
        return sorted(merged_dict.values(), key=lambda x: -x.confidence)


**引擎选择策略：**

系统支持灵活的引擎选择策略，优先使用经过验证的引擎：

| 引擎 | 优先级 | 适用条件 | 说明 |
|------|--------|----------|------|
| **FuzzyEngine** | 🥇 最高 | 有缺陷反馈 + 存在匹配规则 | **优先实现**，已验证的模糊推理方案，复用现有 nets.py |
| **RuleMinerEngine** | 🥈 次高 | 成功案例 >= 10 | 数据驱动的规则学习，需积累数据 |
| **LLMEngine** | 🥉 可选 | 已配置 LLM API | 大模型推理，适合复杂场景 |
| **其他引擎** | 待扩展 | 根据配置启用 | DOE、遗传算法等预留 |

**引擎选择逻辑：**

```python
class EngineSelector:
    """引擎选择器 - 决定使用哪些引擎"""
    
    # 引擎优先级配置（数字越小优先级越高）
    ENGINE_PRIORITY = {
        'fuzzy': 1,           # 模糊推理 - 优先
        'rule_miner': 2,     # 规则挖掘 - 次优
        'llm': 3,             # 大模型 - 补充
        'doe': 4,             # 实验设计 - 探索
        'ga': 5,              # 遗传算法 - 优化
    }
    
    @classmethod
    def select_engines(
        cls,
        context: dict,
        prefer_engines: list = None,
        exclude_engines: list = None
    ) -> List[AIEngineBase]:
        """
        选择适用的引擎
        
        Args:
            context: 推理上下文
            prefer_engines: 优先使用的引擎列表（如 ['fuzzy']）
            exclude_engines: 排除的引擎列表
        
        Returns:
            按优先级排序的可用引擎列表
        """
        # 1. 获取所有可用引擎
        available = EngineRegistry.get_available_engines(context)
        
        # 2. 过滤排除的引擎
        if exclude_engines:
            available = [e for e in available if e.engine_name not in exclude_engines]
        
        # 3. 按优先级排序
        available.sort(key=lambda e: cls.ENGINE_PRIORITY.get(e.engine_name, 99))
        
        # 4. 如果指定了优先引擎，只返回优先引擎
        if prefer_engines:
            available = [e for e in available if e.engine_name in prefer_engines]
        
        return available
```

**推荐策略配置示例：**

```python
# settings.py
RECOMMENDATION_CONFIG = {
    'default_mode': 'fuzzy_first',  # 默认模式：优先 fuzzy
    'fallback_to_rule_miner': True,  # fuzzy 无结果时 fallback 到 rule_miner
    'enable_llm': False,  # 默认关闭 LLM
    'fuzzy_priority': 1,
    'rule_miner_priority': 2,
}
```

## 5. 自学习闭环设计

```
┌─────────────────────────────────────────────────────────────────┐
│                        自学习闭环                                 │
└─────────────────────────────────────────────────────────────────┘

    1. 规则初始化
    ┌─────────────────────────────────────────────────────────┐
    │  初始规则库（专家经验）                                    │
    │  - 模糊推理规则（现有 nets.py）                           │
    │  - 初始化参数规则（现有 process_generate.py）              │
    └─────────────────────────────────────────────────────────┘
                              │
                              ▼
    2. 推荐 → 用户采纳
    ┌─────────────────────────────────────────────────────────┐
    │  用户根据推荐调参 → 试模 → 记录 TuningRecord              │
    │  - 记录缺陷反馈                                           │
    │  - 记录参数快照                                           │
    │  - 记录试模结果（qualified/unqualified）                   │
    └─────────────────────────────────────────────────────────┘
                              │
                              ▼
    3. 规则学习
    ┌─────────────────────────────────────────────────────────┐
    │  定时任务 / 按需触发                                       │
    │  RuleMinerEngine._mine_rules()                           │
    │                                                           │
    │  输入: TuningRecord (result='qualified')                 │
    │  输出: 新发现的规则                                        │
    │  IF 缺陷类型='短射' AND inj_pres_1 < 60 THEN +10          │
    └─────────────────────────────────────────────────────────┘
                              │
                              ▼
    4. 规则评估与入库
    ┌─────────────────────────────────────────────────────────┐
    │  - 计算规则置信度、覆盖率                                  │
    │  - 专家审核（可选）                                        │
    │  - 入库到规则库                                           │
    └─────────────────────────────────────────────────────────┘
                              │
                              ▼
    5. 规则更新 → 回到步骤 2
    ┌─────────────────────────────────────────────────────────┐
    │  规则库更新后，下一次推荐使用新规则                         │
    │  系统越用越智能                                            │
    └─────────────────────────────────────────────────────────┘
```

## 6. 模块现状与改进方向

| 模块 | 现状 | 改进方向 |
|------|------|----------|
| **工艺初始化** | 硬编码规则 (`process_generate.py`)，固定公式 | 升级为 `ExpertEngine`，规则入库，支持数据学习优化 |
| **工艺优化** | 模糊推理 (`nets.py`) | 迁移为 `FuzzyEngine`，保留核心算法 |
| **规则来源** | 专家总结 | 专家 + 数据学习（RuleMiner）+ LLM |
| **系统成长** | 规则固定 | 随 TuningRecord 数据积累自动学习 |

**引擎演进路径：**

| 引擎 | 现状 | 短期目标 | 长期目标 |
|------|------|----------|----------|
| `ExpertEngine` | 硬编码 | 规则入库可配置 | 数据驱动自动学习 |
| `FuzzyEngine` | 固定规则库 | 迁移框架 | 与 RuleMiner 联动 |
| `LLMEngine` | 无 | 设计 RAG 架构 | 接入门控知识 |
| `RuleMinerEngine` | 无 | 基础实现 | 持续优化 |

## 7. 核心优势

1. **可插拔**：新算法只需实现 `AIEngineBase` 接口即可接入
2. **自学习**：规则库随 TuningRecord 数据积累自动成长
3. **可追溯**：每个推荐都可追溯到来源（模糊/规则挖掘/LLM）
4. **统一入口**：前端只需调用 `RecommendationService`，无需关心底层算法
5. **数据闭环**：从数据到知识，从知识到智能的完整闭环

## 8. 待实施事项

### 阶段零：专家系统引擎（ExpertEngine）
- [ ] 设计 `ExpertEngine` 引擎架构
- [ ] 将 `process_generate.py` 规则迁移为结构化专家规则
- [ ] 实现 `RuleLoader` 规则加载器
- [ ] 设计 `expert_rules/` 专家规则库结构

### 阶段一：基础模型扩展
- [ ] 设计并实现 `TuningRecord` 模型
- [ ] 设计并实现 `AIRecommendation` 模型
- [ ] 设计 `TuningRecord` 的 API 接口

### 阶段二：AI 引擎框架
- [ ] 实现 `AIEngineBase` 基类和 `EngineRegistry`
- [ ] 迁移现有 `nets.py` 为 `FuzzyEngine`
- [ ] 实现 `RecommendationService` 统一入口

### 阶段三：自学习能力
- [ ] 实现 `RuleMinerEngine` 规则挖掘引擎
- [ ] 设计规则评估与入库流程
- [ ] 实现定时任务触发规则学习

### 阶段四：LLM 扩展
- [ ] 实现 `LLMEngine` 大模型推理引擎
- [ ] 设计 RAG 相似案例检索
- [ ] 配置 LLM API 集成

---

*文档生成时间：2026-06-29*
*最后更新：2026-06-29*