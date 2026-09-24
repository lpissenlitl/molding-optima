# 规则库模型设计讨论记录

> 日期：2026-09-10
> 讨论范围：`backend/process/models/rules.py` 中的基础表设计
> 目标：重写 RuleKeyword + RuleMethod 字段模型

---

## ✅ 已确认的设计决策

### 1. 基础表范围（3 张 → 2 张）

```
基础表（不可轻易改动）：
- RuleKeyword（参数元数据层）
- RuleMethod（规则层）

业务层（基于基础扩展）：
- RuleLibrary（分组层/多租户）
- TenantKeywordOverride（租户定制）
- MinedRule（挖掘引擎）
- ExpertRule（专家规则）
```

### 2. RuleKeyword 的 3 个分类维度字段（112-116）—— ❌ **确认删除**

```python
subrule_no           # ❌ 删除 - keyword 不该有
product_small_type   # ❌ 删除 - keyword 不该有
polymer_abbreviation # ❌ 删除 - keyword 不该有
```

**理由**：keyword 应该是全局的，没必要区分材料/产品/子规则。匹配条件应该放在 RuleMethod 上。

### 3. fuzzy_level 是按 keyword 独立设计（业界标准）

- ✅ **设计正确**：每个 keyword 独立 fuzzy_level
- ⚠️ **代码有局限**：当前 `FUZZY_LEVELS = [(3, '3级'), (5, '5级')]` 只有两档

**业界做法**（基于 PMC10600427 等文献）：
- 每个变量独立 partition（**业界标准**）
- 典型范围：3 / 5 / 7 / 9（4 档）
- 简单变量用 3 个（精度低），中等精度用 5 个，高精度用 7 个

**认知升级**：代码里有 hardcoded 3 不代表标准就是 3；代码可能有局限。

### 4. range_min/max / unit 是模板值

```python
range_min = FloatField()
range_max = FloatField()
unit = CharField()
```

- **语义边界**：这些是"实验参考值/默认起点"
- **实际推理**：设备 max_set_* ∩ RuleKeyword.range_*（设备真实范围）
- **设计判断**：保持现状即可，不必纠结 nullable 或精确命名

### 5. step 字段处理

```python
step = FloatField(null=True, blank=True)
```

- **现状**：init_fuzzy_ranges.py 写入数据，但 fuzzy 引擎有兜底（range/3）
- **决策**：暂不处理，作为现状保留

### 6. RuleMethod 的核心定位

```python
polymer_category / product_category  # 匹配条件（if 部分）
rule_content                         # 调整内容（then 部分，纯粹）
subrule_no                           # 规则标识（如 'packaging/shortshot'）
```

- **设计原则**：RuleMethod 保持纯粹——只关心"怎么调整"
- **匹配条件**：放在 RuleMethod 上，**不放在 RuleKeyword 上**

### 7. is_auto 与 enable 字段重叠

- **现状**：`is_auto` + `enable` 两个字段语义重叠
- **业界做法**：Drools / BRMS 用单一 activation 字段
- **建议合并**：只保留 `enable`，删除 `is_auto`

---

## 🤔 待决策的问题（用户未明确表态）

### Q1: PARAM_GROUPS 是否扩展？

当前 5 个：
```
injection（注射）/ holding（保压）/ cooling（冷却）/
metering（熔胶）/ temperature（温度）
```

ProcessParameter 中有但**没分组**的字段：
- `pre_met_decomp_*` / `pst_met_decomp_*` —— **松退参数**
- `vps_mode` / `vps_pos` / `vps_t` / `vps_pres` / `vps_spd` —— **VP切换**

**选项**：
- A. 保持 5 个，把松退/VP 塞到邻近分组
- B. 扩展到 7 个（+ suckback / vp_switch）
- C. 扩展到 8 个（独立细分）

### Q2: keyword_type 是否加 choices？

当前是 CharField 无 choices：
```python
keyword_type = CharField(max_length=45)
# 示例: 'pressure', 'speed', 'time', 'temperature'
```

**业界物理量分类**：
```
pressure / speed / time / temperature / position / force / length / weight
```

**选项**：
- A. 保持现状（字符串）
- B. 改 choices 强制 8 种物理类型

### Q3: fuzzy_level 默认值

当前：`default=3`
业界主流：5

**选项**：default=3 / default=5 / 用户指定

### Q4: 是否新增字段？

可能值得加的：
- `description`（参数说明文档）—— 当前缺失
- `is_active`（启用开关）—— RuleKeyword 没有启用/停用
- `version`（版本号）—— 参数定义本身需要演进

---

## ❌ 我之前的错误认知（用户已纠正）

### 错误 1：6 张表混为一谈
- ❌ 一开始讨论 RuleLibrary / MinedRule / ExpertRule 是否冗余
- ✅ 实际只有 RuleKeyword + RuleMethod 是基础表

### 错误 2：RuleKeyword 3 个字段是"死字段"
- ❌ "字段没人用，所以应该删除"
- ✅ 实际是**职责错位**——分类维度不应该在 RuleKeyword 上
- ✅ 删除的理由是"keyword 应该是全局的"，不是"没人用"

### 错误 3：用代码论证字段设计
- ❌ "代码里 hardcoded 3，所以字段设计是对的"
- ✅ 代码可能有局限，应该从**业界实践**出发
- ✅ 业界标准：每个变量独立 partition（3-9）

### 错误 4：反复跑偏到 RuleLibrary 业务逻辑
- ❌ 反复纠结 RuleLibrary 的 owner_type / priority / version / parent_library
- ✅ 这些是业务扩展层，不属于基础表设计范围

### 错误 5：自上而下给方案
- ❌ 看到字段就立刻说"删除/重构"
- ✅ 应该先理解设计意图，再判断哪些保留/优化

---

## 📚 业界参考

| 维度 | 参考依据 |
|------|---------|
| 模糊推理 partition | PMC10600427（呼吸机参数模糊推理文献）|
| 专家系统规则表示 | Drools DRL / CLIPS / OMG PRR |
| 工业参数元数据 | ISO 14617 / VDI 3682 / OPC UA |
| 业务规则管理 | BRMS / Drools KieBase |
| 模糊推理模型 | Mamdani（直觉）/ Sugeno（计算高效）|

---

## 🎯 下一步

聚焦 RuleKeyword 字段重写，等待用户对 Q1-Q4 的决策。

具体可执行步骤（待用户确认后）：
1. 删除 3 个分类维度字段
2. 扩展 FUZZY_LEVELS 到 3/5/7/9 四档（如果用户确认）
3. 修改/新增其他字段
4. 生成 migration（数据迁移分析）
5. 验证 makemigrations 干净

然后再讨论 RuleMethod 字段重写。