# DefectFeedback DEFECTFREE Keyword 设计

> 日期：2026-09-20
> 关联：工艺优化 → 缺陷反馈模块
> 决策等级：项目级（影响数据库主数据初始化命令）

## 背景

工艺优化详情区有缺陷反馈模块，DefectFeedback 让用户录入"本轮试模的缺陷"。存在一类业务场景：

> **产品已经没有缺陷了，但工艺参数还可以优化**（如减少整体周期时间、提产能、降能耗）

这类场景下，用户**无法跳过**缺陷录入：算法需要"无缺陷"作为有效反馈输入，才能继续做工艺优化（而非仅做缺陷修复）。

## 关键决策

**DEFECTFREE 是 keyword，不特殊值。**

| 候选方案 | 结论 |
|----------|------|
| A. 缺陷反馈表单用单选切换"有缺陷 / 无缺陷"两种模式 | 驳回——切换模式让 UI 变复杂，且"无缺陷"在数据上与具体缺陷等价 |
| B. type 下拉里硬编码 `null` 当作"无缺陷"哨兵值 | 驳回——需要后端特殊接口、前端特殊处理、序列化/反序列化复杂 |
| **C. 把 DEFECTFREE 当作普通 RuleKeyword 录入数据库（keyword_name='DEFECTFREE'）** | **采纳**——所有缺陷走统一字段，算法、业务、UI 都按统一路径处理 |

## 字段语义

DEFECTFREE keyword 的字段设置：

| 字段 | 值 | 说明 |
|------|----|------|
| `keyword_name` | `'DEFECTFREE'` | **前哨标记**，DefectFeedback 通过该名称识别 |
| `keyword_alias` | `'无缺陷'` | 用户可见的别名 |
| `category` | `'defect'` | 与其他缺陷同一类，走统一 if-then 规则路径 |
| `parameter_kind` | `'enum'` | 缺陷类不需要区分设定/实际（migration 0009 的 `enum` 选项） |
| `fuzzy_level` | `3` | 与其他 defect 一致（前端选用该项时隐藏 level/position） |
| `keyword_type` | `'position'` | 缺陷类兜底（rules.py 的 `infer_keyword_type` 对 defect 类返回 position） |
| `unit` | `''` | 缺陷类无物理单位 |
| `range_min/max` | `0 / 1` | 占位（缺陷无连续范围） |
| `description` | `'无缺陷（产品本轮试模无缺陷，工艺仍可优化：减少周期时间、提产能、降能耗等）'` | |

## 排序策略

**前端处理**：拿到 keywords 后，把 `keyword_name === 'DEFECTFREE'` 的项排到第一，其他按 `keyword_alias` 排序。

理由：
- 后端保持数据干净（无特殊 sort 字段）
- 排序属于展示层职责
- 与"默认选中第一个" 的 el-select 行为无缝衔接

## 数据流

```
用户进入 DefectFeedback
  ↓
加载 defect keywords（含 DEFECTFREE）
  ↓
DEFECTFREE 排到第一，其他按别名排序
  ↓
默认选中 DEFECTFREE
  ↓
检测到 DEFECTFREE → 隐藏 level/position 字段
  ↓
用户提交 feedback：defect = { keyword_id: DEFECTFREE_ID, level: null, position: '' }
  ↓
后端正常存储
  ↓
触发"获取优化工艺"：算法针对 DEFECTFREE 返工艺优化建议（产能方向）
```

## 业务流：何时触发算法优化？

| 反馈 | 是否触发优化 | 算法响应 |
|------|------------|---------|
| defect=null（跳过录入） | ✅ | 基于历史工艺优化 |
| defect={DEFECTFREE} | ✅ | 优化产能/周期时间（"无缺陷 → 提效"） |
| defect={飞边, 严重} | ✅ | 降低注射压力等针对性调整 |

**关键洞察**：DEFECTFREE 不是"跳过"，是"有效反馈"。和"不填"语义不同。

## 修改文件

### 后端

- `backend/bootstrap/management/commands/init_rule_keyword.py`
  - 在 JSON 导入循环后增加"步骤 4：确保 DEFECTFREE 存在"
  - 已存在则跳过（幂等），不存在则创建
  - 支持 `--dry-run` 模式

**执行命令**（开发环境）：
```bash
python manage.py init_rule_keyword
```

### 前端（待实施）

- `frontend/src/types/rule.ts`：定义/导出 `FuzzyLevel`、`LEVEL_WORDS`、`DEFECT_LEVEL_LABELS`
- `frontend/src/views/process/optimization/components/PreviousAdjustment.vue`：新建多模态卡片
- `frontend/src/views/process/optimization/components/DefectFeedback.vue`：重写
  - type select 按 keywords 渲染，DEFECTFREE 排第一
  - 选中 DEFECTFREE 时隐藏 level/position 字段
  - level 按 fuzzy_level 动态生成
- `frontend/src/views/process/optimization/pages/OptimizationCreate.vue`：传递数据

## 拒绝的方案（备查）

### A. 单选切换模式
```vue
<el-radio-group v-model="feedbackMode">
  <el-radio value="defect">有缺陷（填写下方）</el-radio>
  <el-radio value="none">无缺陷（试模成功）</el-radio>
</el-radio-group>
```
驳回：用户反馈"无缺陷放在缺陷类型中就可以了，默认无缺陷"。

### B. type 下拉第一个特殊选项
```vue
<el-option label="无缺陷" :value="null" />
<el-option v-for="kw in keywords" :label="kw.alias" :value="kw.id" />
```
驳回：需要后端特殊处理 null、序列化复杂、用户认为应该按 keyword 处理。

### C. 把"无缺陷"做成 fuzzy_level=1
驳回：`FuzzyLevel = 3 | 5 | 7`，扩展类型会污染类型定义。直接用 DEFECTFREE 标识更干净。

## 相关上下文

- `process/migrations/0009_rulekeyword_parameter_kind_enum.py`：`parameter_kind` 增加 `enum` 选项
- `process/models/rules.py`：RuleKeyword 的字段定义
- 工艺优化详情区模块顺序：参数 → 过程反馈 → 缺陷反馈（缺陷永远在最后）
- 反馈类组件不自带 title/header，统一由父级 `round-detail-block__title` 提供

## 后续 TODO

- [ ] 后端：开发环境执行 `python manage.py init_rule_keyword` 录入 DEFECTFREE
- [ ] 前端：按上述修改清单实施
- [ ] 前端：开发阶段 mock `previousAdjustment` 数据调试多模态卡片
- [ ] 后续：等算法侧确认针对 DEFECTFREE 的响应策略
