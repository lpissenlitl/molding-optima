# 初始化规则数据库化

> 本文档记录将初始化规则从硬编码迁移到数据库的过程。

## 1. 完成的工作

### 1.1 模型结构调整

修改 `process/models/rules.py` 中的 `ExpertRule` 模型：

| 原字段 | 新字段 | 说明 |
|--------|--------|------|
| `condition` | `conditions` | 改为数组格式 |
| `conclusion` | `coefficients` | 改为直接系数值 |
| - | `description` | 新增描述字段 |
| `priority` default=0 | `priority` default=100 | 数字越小优先级越高 |

**新结构示例**：

```python
# conditions - 条件数组
conditions = [
    {'field': 'polymer.abbreviation', 'operator': 'in', 'value': ['ABS', 'PC']},
    {'field': 'product.ave_thickness', 'operator': 'gte', 'value': 2.0}
]

# coefficients - 直接系数值
coefficients = {
    'inj_pres_ratio': 0.65,
    'hold_pres_base': 0.25,
    'hold_pres_thickness_factor': 10,
}
```

### 1.2 迁移文件

- 删除旧迁移 `process/migrations/0001_initial.py`
- 生成新迁移（包含完整模型定义）

### 1.3 数据迁移脚本

创建 `bootstrap/scripts/import_init_rules.py`：

**功能**：
- 读取 `expert_rules/init_rules.json` 规则文件
- 创建系统级规则库 `init_rules`
- 导入 8 条初始化规则到数据库
- 支持幂等执行（重复运行会更新而非重复创建）

**运行命令**：
```bash
python manage.py import_init_rules
```

### 1.4 导入的规则

| 规则编码 | 规则名称 | 优先级 | 条件数 |
|----------|----------|--------|--------|
| DEFAULT | 默认规则 | 9999 | 0 |
| MATERIAL_GENERAL | 通用材料注射速度 | 100 | 1 |
| MATERIAL_PC_ABS | PC+ABS材料注射速度 | 100 | 1 |
| MATERIAL_OTHER | 其他材料注射速度 | 200 | 1 |
| GATE_DIRECT | 直浇口/点浇口保压时间 | 100 | 1 |
| GATE_SIDE | 侧浇口保压时间 | 100 | 1 |
| GATE_OTHER | 其他浇口保压时间 | 200 | 1 |
| MOLD_TEMP_DEFAULTS | 模温默认值 | 100 | 0 |

## 2. 规则结构

### 2.1 条件格式

支持的操作符：`exact`, `in`, `not_in`, `gte`, `lte`, `gt`, `lt`

```json
{
  "field": "polymer.abbreviation",
  "operator": "in",
  "value": ["ABS", "PC", "PP"]
}
```

### 2.2 系数结构

```json
{
  "injection": { "inj_pres_ratio": 0.65 },
  "holding": { "hold_pres_base_ratio": 0.25 },
  "cooling": { "cool_time_factor": 5.0 }
}
```

## 3. 后续步骤

- [ ] 修改 `initializer.py` 使用数据库规则而非 JSON 文件
- [ ] 实现 `InitRuleMatcher` 从数据库匹配规则
- [ ] 添加管理界面 CRUD

## 4. 相关文件

| 文件 | 说明 |
|------|------|
| `process/models/rules.py` | ExpertRule 模型定义 |
| `process/migrations/0001_initial.py` | 数据库迁移 |
| `bootstrap/management/commands/import_init_rules.py` | 数据导入命令 |
| `process/engines/expert/expert_rules/init_rules.json` | 规则源文件 |
| `process/engines/expert/rule_loader.py` | JSON 规则加载器 |

---

*文档生成时间：2026-06-29*
