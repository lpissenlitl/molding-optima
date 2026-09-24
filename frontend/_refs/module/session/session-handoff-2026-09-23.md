# molding-optima 工艺优化模块 —— 2026-09-23 会话交接

> 本文档是新对话的入口上下文，包含：项目背景、本次累积工作、关键 bug 修复、设计决策、待办计划。
> 新对话开启后，请先读这份文档，再决定具体从哪里入手。

---

# 第一部分：会话总结（已完成的工作）

## 1. 项目背景

- **路径**：`f:\items\moldingx\molding-optima`
- **后端**：Python 3.11 + Django（端口 8200，settings 模块 `_moldx.settings`）
- **前端**：Vue 3 + Vite + Element Plus（端口 9527，代理 `/api` → 8200）
- **核心模块**：工艺参数（process）、优化（optimization）、规则（rules）、专家（expert）
- **关键模型**：`ProcessCondition`（工艺条件）+ `ProcessParameter`（工艺参数，含 seq_idx 调机业务编号）

## 2. 本次会话累积工作（按时间顺序）

### Round 1：UI 精修 + 业务流互斥
- `OptimizationCreate.vue` 按钮配色：success（初始）/ warning（优化）/ plain（重置折叠）/ primary（保存）
- 三个 computed：`hasInitialProcess` / `hasAnyProcess` / `hasConditionData`
- `<ProcessCondition :disabled="hasInitialProcess" />` 锁定工艺条件
- 三层校验防御：UI 锁 + 按钮锁 + 函数校验

### Round 2：参数校验与友好错误
- `OptimizationCreate.vue` `getInitialProcess` 调用 `conditionRef.value?.checkFormDataValid()`
- `data_validator.py` 把 `raise ValueError` 改为 `raise BizException(ERROR_PROCESS_INSUFFICIENT_FIELDS, ...)`
- 错误码：`107036 ERROR_PROCESS_INSUFFICIENT_FIELDS`
- 收集所有缺失字段一次性提示（不是只报第一个）
- 前端 `request.ts` 拦截器已 warning，catch 不再重复 toast

### Round 3：API 修复（prefetch 缺失）
- `initialization_service.py:_build_mold_snapshot` 加 `prefetch_related('gating_systems__cavities__gates')`
- 根因：`gating.to_dict(include_rvs=True)` 只在 `_prefetched_objects_cache` 存在时序列化反向关系
- 影响：`gate_type / ave_thickness / max_thickness / product_weight` 等必填字段拿不到

### Round 4：API 修复（datetime JSON 序列化）
- `initialization_service.py:_jsonify` helper 递归把 datetime/date 转 ISO 字符串
- `process_context_snapshot` JSONField 落库前清理
- 根因：ORM `to_dict()` 返回含 `created_at/updated_at` datetime，默认 `json.dumps` 失败

### Round 5：API 修复（seq_idx 缺失）
- `infer_from_masterdata` 响应里补 `result['seq_idx'] = parameter.seq_idx`
- 前端下游 infer 需要 parent_seq_idx（业务编号）

### Round 6：注释简化
- `initialization_service.py` 1454 → 1357 行（-97 行）
- 注释密度：10.5% → 7.8%
- 保留关键 Bug fix 段落（_build_mold_snapshot 27 行 docstring）

### Round 7：前端工艺参数写入
- `process-const.ts` `initArray<number | null>(...)` 显式标注 sections 类型
- `OptimizationCreate.vue` 三个 helper：
  - `padSteps(steps, max)`：数组 padding
  - `mapInferResultToParameter(result)`：后端扁平 → 前端嵌套（injection/holding/metering/barrel_temperature/vp_switch）
  - `applyInferResultToForm(result)`：集中响应处理（原子应用）
- `getInitialProcess` Step 3 改为一次调用 `applyInferResultToForm(result)`

### Round 8：API 响应 bug（必须解 .data 层）
- 后端用 `{status, msg, timestamp, data: ...}` 包裹，axios 拦截器返回 `response.data`（整个 body）
- **所有前端调用必须 `result?.data?.xxx`** —— 不能直接 `result?.xxx`
- 修复 `OptimizationCreate.vue` 中 3 处错误：`result.condition_id` / `result.matched_rules` / `result.new_parameter`
- 失败案例：toast 显示 `condition_id=-` 但后端 terminal 显示 `condition_id=6`

### Round 9：resetForm bug（必须 mutate 不 replace）
- `ProcessCondition.vue` 在 setup 时一次性 `reactive(props.processCondition)` 包装**第一次的**引用
- 父组件 `Object.assign(form, {condition: {}})` 替换整个对象引用 → 子组件内部 proxy 仍指向旧对象 → UI 不更新
- 修复：`for (key of Object.keys(form.condition)) delete form.condition[key]`，保留引用触发 `deleteProperty` 代理

### Round 10：优化记录列表页面（OptimizationList.vue）
- 路由：`/process/optimization-records`（router/index.ts:129-134）
- 复用 `/api/processes/parameter/` API（不新建）
- 后端最小改动：`main_service.py` 加 `Count("process_parameters")` annotation + `parameters_count` 字段
- 前端 list：调机轮次列（warning 黄/ info 灰）+ 调机历史 dialog（el-dialog + el-timeline）

## 3. 关键 bug + 修复一览

| Bug | 触发 | 修复位置 |
|-----|------|----------|
| BizException 500 → 400 友好 | 数据缺字段时 500 错误 | [data_validator.py:122-126](file:///f:/items/moldingx/molding-optima/backend/process/engines/expert/data_validator.py#L122-L126) |
| `gate_type=None` | mold → cavities → gates 字段缺失 | [initialization_service.py:738-755](file:///f:/items/moldingx/molding-optima/backend/process/services/initialization_service.py#L738-L755)（prefetch） |
| `TypeError: datetime is not JSON serializable` | ORM to_dict 含 datetime | [initialization_service.py:660-686](file:///f:/items/moldingx/molding-optima/backend/process/services/initialization_service.py#L660-L686)（_jsonify） |
| toast 显示 `condition_id=-` | 前端没解 .data 层 | [OptimizationCreate.vue](file:///f:/items/moldingx/molding-optima/frontend/src/views/process/optimization/pages/OptimizationCreate.vue) 三处 |
| resetForm 不生效 | 父组件 replace 对象引用 | [OptimizationCreate.vue:521-557](file:///f:/items/moldingx/molding-optima/frontend/src/views/process/optimization/pages/OptimizationCreate.vue#L521-L557)（mutate） |

## 4. 关键设计决策

### 4.1 原子操作
- **后端**：`with transaction.atomic():` 包裹 Condition + Parameter 创建，要么都成功要么都回滚
- **前端**：JS 单线程同步执行，响应处理封装在一个函数（`applyInferResultToForm`）
- 验证：手动 RuntimeError 注入测试，确认 condition 也被回滚 ✓

### 4.2 字段映射策略
- **后端**：`infer_initial_params` 返回扁平 ProcessParams.to_dict（inj_pres_steps[] 等）
- **前端**：`settingProcessForm` 是嵌套结构（injection.table_data[0].sections[] 等）
- **策略**：padding 到 max 长度（注射 6 段 / 保压 5 段 / 熔胶 4 段 / 料筒 10 段），缺的填 null

### 4.3 复用 vs 新建
- 优化记录列表复用 `/api/processes/parameter/` API（与 ProcessParameterList 共用）
- 后端只加 1 个 annotation，2 处改动，4 行新增
- 不为单个视图新建独立 endpoint

### 4.4 字段命名兼容
后端 history 返回 `seq_idx`，前端用 `item.sequence_index ?? item.seq_idx ?? '-'` fallback 链，防止字段重命名破坏。

## 5. 文档清单（本次会话创建）

| 文档 | 内容 |
|------|------|
| [docs/process-data-validator-friendly-error-2026-09-23.md](file:///f:/items/moldingx/molding-optima/docs/process-data-validator-friendly-error-2026-09-23.md) | BizException 友好提示设计 |
| [docs/process-frontend-param-mapping-atomic-2026-09-23.md](file:///f:/items/moldingx/molding-optima/docs/process-frontend-param-mapping-atomic-2026-09-23.md) | 前端字段映射 + 原子操作 |
| [docs/optimization-records-page-2026-09-23.md](file:///f:/items/moldingx/molding-optima/docs/optimization-records-page-2026-09-23.md) | 优化记录列表页面设计 |

## 6. Memory 更新（auto 保存）

| 类别 | 标题 | id |
|------|------|-----|
| common_pitfalls_experience | 前端 API 响应必须解一层 .data 取业务数据 | `3c57acc8-75e1-4e64-962c-3ef7ab260cfc` |
| common_pitfalls_experience | resetForm 必须 mutate 不要 replace | `af2efe33-078c-484a-bc92-08e74c8959ed` |

新对话开启时，可以调用 `SearchMemory` 检索这两条避免重复踩坑。

## 7. 验证脚本（可复用）

后端单 API 验证（PowerShell）：
```powershell
cd F:\items\moldingx\molding-optima\backend
python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', '_moldx.settings')
import django; django.setup()
from process.services.main_service import get_process_parameter_list
total, items = get_process_parameter_list(company_id=None, page_no=1, page_size=3)
for item in items:
    print(f'id={item[\"id\"]}, condition_no={item.get(\"condition_no\")}, parameters_count={item.get(\"parameters_count\")}')
"
```

前端 TypeScript 编译：
```powershell
cd F:\items\moldingx\molding-optima\frontend
npx vue-tsc --noEmit --project tsconfig.app.json
```

---

# 第二部分：下一阶段计划（用户即将开展）

## 总目标
从前往后梳理页面，**逐个排查功能 bug**，处理完后**再攻破算法部分**。

## Phase 1：核心工作台深度验证（OptimizationCreate）

### 1.1 工艺实测（ProcessActualFeedback）接线
**当前状态**：UI 展示组件存在，但**数据未与 activeRound.feedback.observations 双向绑定**
**风险**：用户填写实测数据不会保存 / 调机历史里看不到实测
**检查点**：
- `components/ProcessActualFeedback.vue` 是否双向 v-model 到 `activeRound.feedback.observations`
- infer 接口的 `feedback.observations` 字段是否被填入请求
- 后端 `optimize_service` 是否消费 observations 字段

### 1.2 缺陷反馈（DefectFeedback）接线
**当前状态**：UI 展示组件存在，defectKeywords 已加载，但**实际选择未持久化**
**风险**：用户选择缺陷不会传入 infer 接口
**检查点**：
- `components/DefectFeedback.vue` 是否 v-model 到 `activeRound.feedback.defect`
- infer 接口的 `feedback.defect` 是否被填入请求
- 后端 `optimize_service` 是否消费 defect 字段
- "无缺陷"特殊 keyword 的处理（已有 memory 记录约定）

### 1.3 previousSuggestion 数据流
**当前状态**：之前是 mock 数据
**风险**：infer 响应的 `suggestion.groups` 没填入 previousSuggestion
**检查点**：
- `getOptimizedProcess` 是否调用 `previousSuggestion = inferData.suggestion.groups`
- `PreviousSuggestion.vue` 渲染是否正确

### 1.4 调机树轮次管理
**检查点**：
- activeRound 切换是否同步 parameter 渲染
- 新轮次创建（makeRound('optimized')）时机
- parent_seq_idx 链路是否正确传递

## Phase 2：列表 / 详情页

### 2.1 ProcessParameterList.vue
- 搜索表单（6 维度）功能验证
- 列偏好持久化（view-name="process_parameter_list"）
- 批量删除流程
- 行操作：编辑 / 删除 / 跨模块入口

### 2.2 ProcessParameterForm.vue（新建 / 编辑 / 详情）
- 大文件，潜在 bug 多
- 三种模式（new/edit/transplant）的字段差异
- 提交 / 保存 / 取消流程
- 校验与错误提示

### 2.3 OptimizationList.vue 回归
- 调机历史 dialog 数据完整性
- 字段命名兼容（sequence_index/seq_idx）
- 批量删除级联逻辑

## Phase 3：辅助功能

### 3.1 工艺移植
- `ProcessParameterTransplant.vue`
- 跨模具复用参数
- 字段映射坑

### 3.2 规则中心
- `RuleLibraryList.vue` / `RuleMethodList.vue` / `ExpertRuleList.vue`
- 筛选 / 搜索 / 排序
- Tab 切换数据加载

### 3.3 masterdata 列表
- Mold / InjectionMoldingMachine / Polymer 列表
- 较成熟，但需验证搜索 / 分页

## Phase 4：算法部分（最后攻破）

按用户原话"处理完成后我再回来攻破算法这部分的内容"。

### 4.1 infer_initial_params 算法
- `backend/process/engines/expert/infer_algorithm.py`
- 规则匹配逻辑（`rule_matcher.py`）
- 优先级 / fallback 策略

### 4.2 优化建议生成
- `optimize_service.py`
- suggestion.groups 生成逻辑

### 4.3 规则方法
- RuleMethod / RuleLibrary / ExpertRule
- 规则冲突处理

---

# 第三部分：执行约定

## 工作节奏
1. **每个页面/功能**：用户明确说"看 X" → 我读代码 + 列 bug 清单 → 用户确认优先级 → 修复 → 验证 → 总结
2. **不主动启动新功能**：未经用户确认，不主动改下一个页面
3. **不改算法部分**：除非用户明确说"开始算法"

## 验证工具
- 后端: `python -c "..."` 跑 service 层
- 前端: `vue-tsc` 编译 + Node 模拟 Vue Proxy 行为
- HTTP: `RequestFactory` 模拟请求（如需鉴权绕开）

## Memory 检索
- 开启新对话时调 `SearchMemory` 检索本次保存的两条 pitfall
- 任何新的 bug 发现立即 `UpdateMemory` 记录

## 关键文件位置速查

| 文件 | 作用 |
|------|------|
| [backend/process/services/initialization_service.py](file:///f:/items/moldingx/molding-optima/backend/process/services/initialization_service.py) | 工艺初始化 + 推理编排（本次会话多次修改） |
| [backend/process/services/main_service.py](file:///f:/items/moldingx/molding-optima/backend/process/services/main_service.py) | 通用列表 + 批量操作（加 annotation） |
| [backend/process/engines/expert/data_validator.py](file:///f:/items/moldingx/molding-optima/backend/process/engines/expert/data_validator.py) | BizException 友好提示 |
| [frontend/src/views/process/optimization/pages/OptimizationCreate.vue](file:///f:/items/moldingx/molding-optima/frontend/src/views/process/optimization/pages/OptimizationCreate.vue) | 核心工作台（多次修改） |
| [frontend/src/views/process/optimization/pages/OptimizationList.vue](file:///f:/items/moldingx/molding-optima/frontend/src/views/process/optimization/pages/OptimizationList.vue) | 优化记录列表（刚完成） |
| [frontend/src/views/process/parameter/pages/ProcessParameterForm.vue](file:///f:/items/moldingx/molding-optima/frontend/src/views/process/parameter/pages/ProcessParameterForm.vue) | 新建 / 编辑 / 详情表单（待排查） |
| [frontend/src/constants/process-const.ts](file:///f:/items/moldingx/molding-optima/frontend/src/constants/process-const.ts) | 前端表单结构（initArray 类型修复） |
| [frontend/src/utils/request.ts](file:///f:/items/moldingx/molding-optima/frontend/src/utils/request.ts) | axios 拦截器（返回 response.data 整个 body） |