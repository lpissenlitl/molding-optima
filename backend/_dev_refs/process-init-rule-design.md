# 工艺参数初始化规则引擎设计文档

> 本文档描述了 molding-optima 工艺参数初始化规则引擎的设计方案。

## 1. 设计背景

### 1.1 当前问题

当前 `ProcessInitializer` 使用硬编码的专家规则：

```python
# initializer.py - 硬编码示例
inj_pres = max_inj_pres * 0.65           # 固定系数，无法灵活调整
hold_pres = 0.25 * max_hold_pres + 10 * avg_thickness  # 固定公式
```

**问题**：
- 系数固定，无法针对不同材料/产品类型调整
- 新增材料规则需要修改代码
- 系数调整需要开发人员介入

### 1.2 优化目标

1. **规则结构化**：将硬编码规则改为数据库存储
2. **可配置**：通过管理界面调整规则系数
3. **可扩展**：支持按材料、产品类型等维度细化规则
4. **向下兼容**：保持现有功能不变

## 2. 数据模型设计

### 2.1 简化设计

将条件和系数统一存储在一张表中：

```python
class InitRule(BusinessBaseModel):
    """初始化规则"""
    
    # 基本信息
    rule_code = CharField(max_length=50, unique=True, verbose_name="规则编码")
    rule_name = CharField(max_length=100, verbose_name="规则名称")
    description = TextField(null=True, blank=True, verbose_name="规则描述")
    
    # 优先级（数字越小优先级越高）
    priority = IntegerField(default=100, verbose_name="优先级")
    
    # 状态
    is_active = BooleanField(default=True, verbose_name="是否启用")
    
    # 适用范围
    scope = CharField(max_length=20, default='global', verbose_name="适用范围")
    """
    - global: 全局规则
    - tenant: 租户规则
    """
    
    # 条件（JSON数组）
    conditions = JSONField(default=list, verbose_name="匹配条件")
    """
    支持的条件格式：
    [
        {'field': 'polymer_type', 'operator': 'in', 'value': ['ABS', 'PC']},
        {'field': 'wall_thickness', 'operator': 'in', 'value': ['normal', 'thick']}
    ]
    
    支持的 operator：
    - in: 值在列表中
    - exact: 精确匹配
    - gte: 大于等于
    - lte: 小于等于
    - gt: 大于
    - lt: 小于
    """
    
    # 系数（JSON对象）
    coefficients = JSONField(default=dict, verbose_name="规则系数")
    """
    系数格式：
    {
        'inj_pres_ratio': 0.65,                    # 注射压力比例
        'hold_pres_base': 0.25,                    # 保压压力基数
        'hold_pres_thickness_factor': 10,          # 保压压力厚度系数
        'hold_velo_ratio': 0.15,                   # 保压速度比例
        'inj_velo_ratio': 0.40,                    # 注射速度比例
        'cool_time_factor': 1.0,                   # 冷却时间系数
        'meter_back_pres_ratio': 0.10,             # 计量背压比例
    }
    """
    
    # 元信息
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'process_init_rule'
        ordering = ['priority']
        verbose_name = '初始化规则'
        verbose_name_plural = '初始化规则'
```

### 2.2 规则示例

| rule_code | conditions | coefficients | 说明 |
|-----------|------------|--------------|------|
| `ABS_DEFAULT` | `[{'field': 'polymer_type', 'operator': 'in', 'value': ['ABS']}]` | `{'inj_pres_ratio': 0.65, ...}` | ABS材料默认规则 |
| `PC_DEFAULT` | `[{'field': 'polymer_type', 'operator': 'in', 'value': ['PC']}]` | `{'inj_pres_ratio': 0.60, ...}` | PC材料默认规则 |
| `THIN_WALL` | `[{'field': 'wall_thickness', 'operator': 'in', 'value': ['thin']}]` | `{'inj_velo_ratio': 0.50, ...}` | 薄壁件规则 |
| `DEFAULT` | `[]` | `{'inj_pres_ratio': 0.65, ...}` | 全局默认规则 |

## 3. 匹配逻辑设计

### 3.1 匹配流程

```
用户输入：产品信息（材料、壁厚、浇口...）
              │
              ▼
    ┌─────────────────────┐
    │   InitRuleMatcher   │
    │   规则匹配器        │
    └──────────┬──────────┘
               │
    ┌──────────┴──────────┐
    │ 1. 查询所有活动规则 │
    │ 2. 按 priority 排序 │
    └──────────┬──────────┘
               │
    ┌──────────┴──────────┐
    │ 3. 遍历匹配条件     │
    │    条件全部满足     │
    │    则匹配成功       │
    └──────────┬──────────┘
               │
    ┌──────────┴──────────┐
    │ 4. 返回匹配的规则   │
    │    或 DEFAULT 兜底  │
    └─────────────────────┘
```

### 3.2 匹配器实现

```python
class InitRuleMatcher:
    """规则匹配器"""
    
    def match(self, context: dict) -> dict:
        """
        匹配规则并返回系数
        
        context = {
            'polymer_type': 'ABS',
            'wall_thickness': 'normal',  # thin / normal / thick
            'gate_type': '点浇口',
            'avg_thickness': 2.5,
            'max_inj_pres': 150,
            ...
        }
        
        Returns:
            coefficients (dict): 匹配的规则系数
        """
        # 1. 查询所有活动规则，按优先级排序
        rules = InitRule.objects.filter(
            is_active=True
        ).order_by('priority')
        
        # 2. 遍历匹配
        for rule in rules:
            if self._match_conditions(rule.conditions, context):
                return rule.coefficients
        
        # 3. 理论上 DEFAULT 规则会匹配到
        raise ValueError("无可用初始化规则，请检查 DEFAULT 规则是否存在")
    
    def _match_conditions(self, conditions: list, context: dict) -> bool:
        """匹配所有条件（AND 关系）"""
        if not conditions:
            return True  # 空条件表示默认规则
        
        for cond in conditions:
            if not self._match_single_condition(cond, context):
                return False
        return True
    
    def _match_single_condition(self, cond: dict, context: dict) -> bool:
        """匹配单个条件"""
        field = cond['field']
        operator = cond['operator']
        value = cond['value']
        
        # 获取上下文中的值
        context_value = self._get_nested_value(context, field)
        
        if operator == 'in':
            return context_value in value
        elif operator == 'exact':
            return context_value == value
        elif operator == 'gte':
            return context_value >= value
        elif operator == 'lte':
            return context_value <= value
        elif operator == 'gt':
            return context_value > value
        elif operator == 'lt':
            return context_value < value
        
        return False
    
    def _get_nested_value(self, data: dict, field: str):
        """获取嵌套字段值"""
        keys = field.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        return value
```

## 4. 规则系数说明

### 4.1 支持的系数

| 系数名 | 说明 | 公式示例 |
|--------|------|----------|
| `inj_pres_ratio` | 注射压力比例 | `inj_pres = max_inj_pres * inj_pres_ratio` |
| `hold_pres_base` | 保压压力基数 | `hold_pres = hold_pres_base * max_hold_pres + hold_pres_thickness_factor * avg_thickness` |
| `hold_pres_thickness_factor` | 保压压力厚度系数 | 同上 |
| `hold_velo_ratio` | 保压速度比例 | `hold_velo = max_hold_velo * hold_velo_ratio` |
| `inj_velo_ratio` | 注射速度比例 | `inj_velo = max_inj_velo * inj_velo_ratio` |
| `cool_time_factor` | 冷却时间系数 | `cool_time = base_cool_time * cool_time_factor` |
| `meter_back_pres_ratio` | 计量背压比例 | `meter_back_pres = max_back_pres * meter_back_pres_ratio` |

### 4.2 默认规则数据

```python
# 种子数据
DEFAULT_RULE = {
    'rule_code': 'DEFAULT',
    'rule_name': '全局默认规则',
    'description': '无可用特定规则时的兜底规则',
    'priority': 9999,
    'is_active': True,
    'scope': 'global',
    'conditions': [],  # 无条件
    'coefficients': {
        'inj_pres_ratio': 0.65,
        'hold_pres_base': 0.25,
        'hold_pres_thickness_factor': 10,
        'hold_velo_ratio': 0.15,
        'inj_velo_ratio': 0.40,
        'cool_time_factor': 1.0,
        'meter_back_pres_ratio': 0.10,
    }
}
```

## 5. 与现有代码的集成

### 5.1 修改 ProcessInitializer

```python
class ProcessInitializer:
    """工艺参数初始化器"""
    
    def __init__(self, machine_info: Dict[str, Any], polymer_info: Dict[str, Any]):
        # ... 现有初始化代码 ...
        
        # 新增：初始化规则匹配器
        self.rule_matcher = InitRuleMatcher()
    
    def _derive_process(self, params: ProductionParams):
        # ... 现有基础计算代码 ...
        
        # 新增：从规则获取系数
        context = {
            'polymer_type': mat.get('abbreviation', 'ABS'),
            'wall_thickness': self._classify_wall_thickness(avg_thickness),
            'gate_type': prod.get('gate_type', '直浇口'),
            'avg_thickness': avg_thickness,
        }
        
        # 获取匹配的规则系数
        coeffs = self.rule_matcher.match(context)
        
        # 使用系数计算参数
        inj_pres = max_inj_pres * coeffs.get('inj_pres_ratio', 0.65)
        hold_pres = coeffs.get('hold_pres_base', 0.25) * max_hold_pres + \
                    coeffs.get('hold_pres_thickness_factor', 10) * avg_thickness
        hold_velo = max_hold_velo * coeffs.get('hold_velo_ratio', 0.15)
    
    def _classify_wall_thickness(self, avg_thickness: float) -> str:
        """分类壁厚"""
        if avg_thickness < 2:
            return 'thin'
        elif avg_thickness > 4:
            return 'thick'
        else:
            return 'normal'
```

### 5.2 向下兼容

如果数据库中不存在规则记录，仍使用硬编码的默认值：

```python
def _get_coefficients(self, context: dict) -> dict:
    """获取系数，优先从数据库，兜底用硬编码"""
    try:
        return self.rule_matcher.match(context)
    except Exception:
        # 数据库无可用规则，使用硬编码默认值
        return {
            'inj_pres_ratio': 0.65,
            'hold_pres_base': 0.25,
            'hold_pres_thickness_factor': 10,
            'hold_velo_ratio': 0.15,
            'inj_velo_ratio': 0.40,
            'cool_time_factor': 1.0,
            'meter_back_pres_ratio': 0.10,
        }
```

## 6. 管理界面（后续扩展）

### 6.1 规则管理

| 功能 | 说明 |
|------|------|
| 规则列表 | 展示所有规则，支持筛选 |
| 规则详情 | 查看规则的条件和系数 |
| 规则编辑 | 修改规则系数 |
| 规则新增 | 添加新规则 |
| 规则测试 | 输入产品信息，测试匹配结果 |

### 6.2 规则导入导出

支持 JSON 格式导入导出，便于批量配置。

## 7. 演进方向

### 7.1 短期（当前实现）

- 规则存储到数据库
- 支持按材料类型匹配
- 提供管理界面

### 7.2 中期

- 支持更多匹配维度（壁厚、浇口、产品类型）
- 规则学习：从成功案例学习最优系数
- 规则版本管理

### 7.3 长期

- 规则自动生成
- 规则效果评估
- 多规则组合匹配

## 8. 文件结构

```
backend/process/
├── models/
│   ├── __init__.py
│   └── init_rule.py          # 新增：InitRule 模型
│
├── engines/
│   └── expert/
│       ├── __init__.py
│       ├── expert_engine.py
│       ├── macros.py          # 保留宏定义常量
│       ├── param_types.py     # 保留参数类型定义
│       ├── initializer.py     # 修改：使用规则匹配器
│       └── rule_matcher.py    # 新增：规则匹配器
```

## 9. 实施计划

| 步骤 | 内容 | 优先级 |
|------|------|--------|
| 1 | 创建 InitRule 模型 | P0 |
| 2 | 创建种子数据迁移 | P0 |
| 3 | 实现 InitRuleMatcher | P0 |
| 4 | 修改 ProcessInitializer 使用规则匹配 | P0 |
| 5 | 测试验证功能 | P0 |
| 6 | 添加管理接口 | P1 |

---

*文档生成时间：2026-07-01*