# 搜索表单统一改造方案

> **版本**: 1.0.0  
> **创建时间**: 2026-06-10  
> **目标**: 将所有搜索表单统一改造为使用 BaseSearchForm 公共组件

---

## 📋 目录

- [1. 改造背景](#1-改造背景)
- [2. 涉及文件清单](#2-涉及文件清单)
- [3. 改造策略](#3-改造策略)
- [4. 实施步骤](#4-实施步骤)
- [5. 风险评估](#5-风险评估)
- [6. 验收标准](#6-验收标准)

---

## 1. 改造背景

### 1.1 现状问题

当前系统中存在 **25 个搜索表单组件**，虽然都使用了统一的 `.search-container` 样式类，但每个组件都是独立实现的，存在以下问题：

1. **代码重复**：每个组件都有类似的模板结构（el-form、el-form-item、按钮等）
2. **维护成本高**：样式调整需要修改多个文件
3. **功能不一致**：重置逻辑、清空处理等细节可能不一致
4. **扩展困难**：新增功能（如展开/收起）需要在每个组件中实现

### 1.2 改造目标

通过引入 `BaseSearchForm` 公共组件，实现：

1. ✅ **代码复用**：减少 70%+ 的重复代码
2. ✅ **统一行为**：搜索、重置、清空等行为完全一致
3. ✅ **易于维护**：样式和逻辑集中在 BaseSearchForm
4. ✅ **灵活扩展**：支持配置化和插槽定制

---

## 2. 涉及文件清单

### 2.1 已使用 search-container 的文件（25个）

#### 模具管理模块（2个）
| 文件路径 | 组件名 | 复杂度 | 优先级 |
|---------|--------|--------|--------|
| `src/views/moldManage/components/MoldSearchForm.vue` | MoldSearchForm | 中 | P0（已完成试点） |
| `src/views/moldManage/components/ProjectSearchForm.vue` | ProjectSearchForm | 低 | P0（已完成试点） |

#### 设备管理模块（3个）
| 文件路径 | 组件名 | 复杂度 | 优先级 |
|---------|--------|--------|--------|
| `src/views/machineManage/components/InjectionSearchForm.vue` | InjectionSearchForm | 低 | P1 |
| `src/views/machineManage/AuxiliaryEquipmentList.vue` | AuxiliaryEquipmentList | 中 | P2 |
| `src/views/machineTest/MachineTestList.vue` | MachineTestList | 中 | P2 |

#### 工艺管理模块（3个）
| 文件路径 | 组件名 | 复杂度 | 优先级 |
|---------|--------|--------|--------|
| `src/views/processManage/parameter/components/ParameterSearchForm.vue` | ParameterSearchForm | 中 | P1 |
| `src/views/processManage/adaptation/components/ProcessSearchForm.vue` | ProcessSearchForm | 中 | P1 |
| `src/views/processManage/optimization/subView/queryOptimizeList.vue` | queryOptimizeList | 低 | P2 |

#### 试模管理模块（3个）
| 文件路径 | 组件名 | 复杂度 | 优先级 |
|---------|--------|--------|--------|
| `src/views/moldTrial/components/TrialSessionSearchForm.vue` | TrialSessionSearchForm | 高 | P1 |
| `src/views/moldTrial/components/TaskSearchForm.vue` | TaskSearchForm | 高 | P1 |
| `src/views/moldTrial/components/TrialReportSearchForm.vue` | TrialReportSearchForm | 高 | P1 |

#### 库存管理模块（5个）
| 文件路径 | 组件名 | 复杂度 | 优先级 |
|---------|--------|--------|--------|
| `src/views/inventoryManage/components/MaterialSearchForm.vue` | MaterialSearchForm | 低 | P1 |
| `src/views/inventoryManage/components/MaterialStockSearchForm.vue` | MaterialStockSearchForm | 低 | P1 |
| `src/views/inventoryManage/components/MaterialRequisitionSearchForm.vue` | MaterialRequisitionSearchForm | 中 | P1 |
| `src/views/inventoryManage/components/PackagingMaterialSearchForm.vue` | PackagingMaterialSearchForm | 中 | P2 |
| `src/views/inventoryManage/MaterialRequisitionCreate.vue` | MaterialRequisitionCreate | 中 | P2 |

#### 排程管理模块（4个）
| 文件路径 | 组件名 | 复杂度 | 优先级 |
|---------|--------|--------|--------|
| `src/views/scheduleManage/schedule/components/ScheduleSearchForm.vue` | ScheduleSearchForm | 中 | P1 |
| `src/views/scheduleManage/reservation/components/ReservationSearchForm.vue` | ReservationSearchForm | 中 | P1 |
| `src/views/scheduleManage/reservation/ReservationForm/components/ReservationSearchForm.vue` | ReservationSearchForm | 中 | P2 |
| `src/views/scheduleManage/readiness/components/ReadinessSearchForm.vue` | ReadinessSearchForm | 低 | P2 |

#### 通知管理模块（2个）
| 文件路径 | 组件名 | 复杂度 | 优先级 |
|---------|--------|--------|--------|
| `src/views/noticeManage/components/NoticeTemplateSearch.vue` | NoticeTemplateSearch | 低 | P2 |
| `src/views/noticeManage/components/NoticeRecordSearch.vue` | NoticeRecordSearch | 低 | P2 |

#### 系统管理模块（3个）
| 文件路径 | 组件名 | 复杂度 | 优先级 |
|---------|--------|--------|--------|
| `src/views/superManage/UserList.vue` | UserList | 中 | P2 |
| `src/views/superManage/RoleList.vue` | RoleList | 中 | P2 |
| `src/views/superManage/CompanyList.vue` | CompanyList | 中 | P2 |

### 2.2 复杂度评估标准

| 等级 | 标准 | 示例特征 |
|------|------|---------|
| **低** | 仅包含 autocomplete/select，无特殊逻辑 | 3-5 个字段，无日期范围 |
| **中** | 包含多种类型，有简单自定义逻辑 | 5-8 个字段，可能有日期选择 |
| **高** | 包含复杂表单项，有大量自定义逻辑 | 8+ 字段，日期范围、级联选择器等 |

---

## 3. 改造策略

### 3.1 分批改造计划

#### 第一批：P0 - 已完成试点（2个）
- ✅ MoldSearchForm.vue
- ✅ ProjectSearchForm.vue

**目的**：验证 BaseSearchForm 的可行性和易用性

#### 第二批：P1 - 核心业务模块（13个）
- InjectionSearchForm.vue
- ParameterSearchForm.vue
- ProcessSearchForm.vue
- TrialSessionSearchForm.vue
- TaskSearchForm.vue
- TrialReportSearchForm.vue
- MaterialSearchForm.vue
- MaterialStockSearchForm.vue
- MaterialRequisitionSearchForm.vue
- ScheduleSearchForm.vue
- ReservationSearchForm.vue（主）
- AuxiliaryEquipmentList.vue
- MachineTestList.vue

**特点**：使用频率高，改造收益大

#### 第三批：P2 - 次要模块（10个）
- queryOptimizeList.vue
- PackagingMaterialSearchForm.vue
- MaterialRequisitionCreate.vue
- ReservationSearchForm.vue（子组件）
- ReadinessSearchForm.vue
- NoticeTemplateSearch.vue
- NoticeRecordSearch.vue
- UserList.vue
- RoleList.vue
- CompanyList.vue

**特点**：使用频率较低，可逐步改造

### 3.2 改造模式

#### 模式A：标准改造（适用于 80% 的场景）

**适用条件**：
- 表单项类型为 autocomplete/select/input/date
- 无复杂自定义表单项
- 无特殊的搜索/重置逻辑

**改造步骤**：
1. 导入 BaseSearchForm
2. 将 `suggestion_items` 或类似配置转换为 `search_items`
3. 简化模板为 `<BaseSearchForm :query="..." :items="..." />`
4. 简化 methods，只保留 `handleSearch()` 和 `handleReset()`
5. 删除冗余的 reset 逻辑

**示例**：参考 ProjectSearchForm.vue 的改造

#### 模式B：混合改造（适用于 15% 的场景）

**适用条件**：
- 大部分表单项可用配置化
- 有 1-2 个特殊表单项（如日期范围、级联选择器）

**改造步骤**：
1. 标准表单项使用配置化
2. 特殊表单项通过插槽实现
3. 在 `search_items` 中使用 `{ slot_name: "xxx" }` 占位

**示例**：
```vue
<BaseSearchForm :query="query_params" :items="search_items">
  <template #date-range="{ query }">
    <el-form-item label="日期范围">
      <el-date-picker v-model="query.dateRange" type="daterange" />
    </el-form-item>
  </template>
</BaseSearchForm>
```

#### 模式C：保持现状（适用于 5% 的场景）

**适用条件**：
- 高度定制的搜索表单
- 复杂的交互逻辑
- 改造成本高于收益

**决策**：暂不改造，保持现有实现

---

## 4. 实施步骤

### 4.1 准备阶段（1天）

**任务**：
1. ✅ 创建 BaseSearchForm 组件（已完成）
2. ✅ 完成 2 个试点改造（已完成）
3. ⏳ 编写改造指南文档（进行中）
4. ⏳ 团队培训（讲解 BaseSearchForm 使用方法）

**产出**：
- BaseSearchForm.vue
- README_BaseSearchForm.md
- MoldSearchForm_Migration_Example.md

### 4.2 第二批改造（3-5天）

**每日计划**：
- **Day 1**：改造 3-4 个设备/工艺模块
- **Day 2**：改造 3-4 个试模模块
- **Day 3**：改造 3-4 个库存模块
- **Day 4**：改造 2-3 个排程模块
- **Day 5**：测试和修复 Bug

**每个组件改造时间**：约 30-60 分钟

### 4.3 第三批改造（2-3天）

**每日计划**：
- **Day 1**：改造 4-5 个次要模块
- **Day 2**：改造剩余模块
- **Day 3**：全面测试

### 4.4 验收阶段（1天）

**任务**：
1. 功能测试：确保所有搜索表单正常工作
2. 样式检查：确认视觉效果一致
3. 性能测试：无明显性能下降
4. 代码审查：确保符合规范

---

## 5. 风险评估

### 5.1 技术风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| BaseSearchForm 不支持某些特殊表单项 | 中 | 中 | 使用插槽扩展机制 |
| 父组件调用方式变化导致错误 | 低 | 高 | 保持 Props/Events 接口不变 |
| 样式不一致 | 低 | 中 | 统一使用全局 .search-container 样式 |
| 性能问题 | 低 | 低 | BaseSearchForm 已优化，性能影响可忽略 |

### 5.2 进度风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| 改造时间超出预期 | 中 | 中 | 分批进行，优先改造高频使用的模块 |
| 发现隐藏的兼容性问题 | 低 | 高 | 充分测试，保留回滚方案 |
| 团队成员不熟悉 BaseSearchForm | 中 | 中 | 提供详细文档和培训 |

### 5.3 回滚方案

如果改造过程中发现重大问题：

1. **Git 分支管理**：每个批次在独立分支上开发
2. **渐进式发布**：改造一个测试一个，不一次性全部上线
3. **保留旧代码**：必要时可以快速回滚到改造前的版本

---

## 6. 验收标准

### 6.1 功能验收

- [ ] 所有搜索表单的搜索功能正常
- [ ] 所有搜索表单的重置功能正常
- [ ] 清空按钮工作正常
- [ ] 展开/收起功能（如有）正常
- [ ] 自动完成建议列表正常显示
- [ ] 下拉选择正常

### 6.2 样式验收

- [ ] 所有搜索表单使用统一的 `.search-container` 样式
- [ ] 悬停效果一致
- [ ] 按钮样式统一
- [ ] 间距和布局一致
- [ ] 响应式布局正常

### 6.3 代码质量验收

- [ ] 无 ESLint 错误
- [ ] 符合项目命名规范（Data 用下划线，Methods 用驼峰）
- [ ] 组件结构清晰
- [ ] 注释完整
- [ ] 无重复代码

### 6.4 性能验收

- [ ] 页面加载时间无明显增加
- [ ] 搜索响应速度无明显下降
- [ ] 内存占用合理

---

## 7. 改造检查清单

### 每个组件改造时需要检查的项目

```markdown
## [组件名] 改造检查清单

### 准备工作
- [ ] 备份原文件
- [ ] 阅读 BaseSearchForm 文档
- [ ] 确认表单项类型

### 代码改造
- [ ] 导入 BaseSearchForm
- [ ] 注册组件
- [ ] 转换配置项（suggestion_items → search_items）
- [ ] 简化模板
- [ ] 简化 methods
- [ ] 更新变量命名（驼峰 → 下划线）

### 功能测试
- [ ] 搜索功能正常
- [ ] 重置功能正常
- [ ] 清空功能正常
- [ ] 自动完成正常
- [ ] 下拉选择正常

### 样式检查
- [ ] 样式与之前一致
- [ ] 响应式正常
- [ ] 无样式污染

### 代码审查
- [ ] 无 ESLint 错误
- [ ] 命名符合规范
- [ ] 注释完整
- [ ] 无冗余代码

### 提交
- [ ] Git 提交信息清晰
- [ ] 关联 Issue（如有）
```

---

## 8. 预计工作量

### 8.1 时间估算

| 阶段 | 工作量 | 说明 |
|------|--------|------|
| 准备阶段 | 1 天 | 文档、培训 |
| 第二批改造 | 3-5 天 | 13 个组件 × 30-60 分钟 |
| 第三批改造 | 2-3 天 | 10 个组件 × 20-40 分钟 |
| 验收阶段 | 1 天 | 测试、修复 |
| **总计** | **7-10 天** | 约 1.5-2 周 |

### 8.2 人力安排

- **主要负责人**：1 人（负责核心模块改造）
- **协助人员**：1-2 人（负责次要模块改造）
- **测试人员**：1 人（负责功能测试）

---

## 9. 后续优化

改造完成后，可以考虑的优化方向：

1. **增强 BaseSearchForm**
   - 支持更多表单项类型（cascader、tree-select 等）
   - 添加表单验证功能
   - 支持动态加载选项

2. **性能优化**
   - 懒加载大型选项列表
   - 缓存自动完成建议

3. **用户体验**
   - 添加搜索历史
   - 支持快捷键（Enter 搜索、Esc 关闭）
   - 智能默认值

---

## 📚 相关文档

- [BaseSearchForm 使用指南](../components/_devRefs/README_BaseSearchForm.md)
- [MoldSearchForm 改造示例](../components/_devRefs/MoldSearchForm_Migration_Example.md)
- [前端代码规范](../../CODING_STANDARDS.md)
- [搜索表单轻量级样式架构](../../styles/devRefs/SEARCH_FORM_OPTIMIZATION.md)

---

**最后更新**: 2026-06-10  
**维护者**: MoldingX Team
