<!--
  RuleLibraryCard.vue - 单个规则库卡片（Section 1 网格中的一项）

  展示字段（按重要性排序）：
  - 顶部图标 + 库名称
  - 归属标签（系统级/租户级）
  - 库编码 + 描述（截断 2 行）
  - 底部统计：规则方法数 / 专家规则数 / 版本号 / 优先级
  - 状态指示器

  交互：
  - 卡片整体点击 → 触发 @click（进入详情）
  - 右上角编辑/删除按钮 → 触发 @edit / @delete（系统库禁用）
  - 系统库：owner_type=system 时只读，不响应整体点击
-->
<template>
  <div
    class="rule-library-card"
    :class="{
      'is-system': library.owner_type === 'system',
      'is-disabled': !library.is_active,
      'is-readonly': isReadonly,
    }"
    @click="handleClick"
  >
    <!-- 顶部：图标 + 名称 + 归属 + 操作按钮 -->
    <div class="card-header">
      <div class="header-left">
        <el-icon class="library-icon">
          <svg viewBox="0 0 24 24" width="28" height="28">
            <path
              fill="currentColor"
              d="M4 4h12v3h2V4a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10v-2H4V4zm18 6h-8a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2v-8a2 2 0 0 0-2-2zm-8 2h8v8h-8v-8z"
            />
          </svg>
        </el-icon>
        <div class="library-meta">
          <div class="library-name" :title="library.library_name">
            {{ library.library_name }}
          </div>
          <div class="library-code">{{ library.library_code }}</div>
        </div>
      </div>
      <div class="header-right">
        <el-tag
          :type="library.owner_type === 'system' ? 'info' : 'success'"
          effect="light"
        >
          {{ ownerTypeLabel }}
        </el-tag>
        <!-- 右上角操作按钮（hover 时显示）-->
        <div v-if="!isReadonly" class="card-actions" @click.stop>
          <el-button type="text" :title="'编辑 ' + library.library_name" @click="handleEdit">
            <AppIcon icon="mdi:pencil-outline" style="font-size: 14px;" />
          </el-button>
          <el-button type="text" class="text-danger" :title="'删除 ' + library.library_name" @click="handleDelete">
            <AppIcon icon="mdi:delete-outline" style="font-size: 14px;" />
          </el-button>
        </div>
        <el-tooltip v-else placement="top" content="系统库只读，不可编辑/删除">
          <el-icon class="lock-icon"><svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M12 1a5 5 0 0 0-5 5v3H6a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-9a2 2 0 0 0-2-2h-1V6a5 5 0 0 0-5-5zm-3 8V6a3 3 0 1 1 6 0v3H9z"/></svg></el-icon>
        </el-tooltip>
      </div>
    </div>

    <!-- 描述 -->
    <div class="library-desc" :title="library.description || ''">
      {{ library.description || '—' }}
    </div>

    <!-- 底部统计 -->
    <div class="card-stats">
      <div class="stat-item">
        <span class="stat-label">规则方法</span>
        <span class="stat-value">{{ library.method_count ?? 0 }}</span>
      </div>
      <!-- 专家规则数：仅超级管理员可见（平台级内部规则） -->
      <template v-if="isSuperuser">
        <div class="stat-divider"></div>
        <div class="stat-item">
          <span class="stat-label">专家规则</span>
          <span class="stat-value">{{ library.expert_rule_count ?? 0 }}</span>
        </div>
      </template>
      <div class="stat-divider"></div>
      <div class="stat-item">
        <span class="stat-label">版本</span>
        <span class="stat-value">v{{ library.version }}</span>
      </div>
      <div class="stat-divider"></div>
      <div class="stat-item">
        <span class="stat-label">优先级</span>
        <span class="stat-value">{{ library.priority }}</span>
      </div>
    </div>

    <!-- 状态指示 -->
    <div class="card-footer">
      <span class="library-type" :class="library.library_type">
        {{ libraryTypeLabel }}
      </span>
      <div class="status-info">
        <span
          class="status-dot"
          :class="library.is_active ? 'active' : 'inactive'"
        ></span>
        <span class="status-text">
          {{ library.is_active ? '启用' : '禁用' }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { RuleLibrary } from '@/types/rule'

const props = withDefaults(
  defineProps<{
    library: RuleLibrary
    /**
     * 当前用户是否为超级管理员
     * - true：显示「专家规则」统计项（平台级内部数据仅超管可见）
     * - false：隐藏「专家规则」统计项（租户用户不可见）
     */
    isSuperuser?: boolean
    /**
     * 是否只读（系统库 + 非超管 = 只读）
     * - true：卡片只读，禁用编辑/删除按钮，但整体点击仍可进入详情查看
     * - false：正常可编辑/删除
     */
    isReadonly?: boolean
  }>(),
  {
    isSuperuser: false,
    isReadonly: false,
  },
)

const emit = defineEmits<{
  (e: 'click', library: RuleLibrary): void
  (e: 'edit', library: RuleLibrary): void
  (e: 'delete', library: RuleLibrary): void
}>()

const ownerTypeLabel = computed(() =>
  props.library.owner_type === 'system' ? '系统级' : '租户级',
)

const libraryTypeLabel = computed(() =>
  props.library.library_type === 'fuzzy' ? '模糊规则库' : '专家规则库',
)

function handleClick() {
  // 系统库只读，但仍可点击进入详情查看（编辑/删除按钮已禁用）
  emit('click', props.library)
}

function handleEdit() {
  emit('edit', props.library)
}

function handleDelete() {
  emit('delete', props.library)
}
</script>

<style scoped>
.rule-library-card {
  position: relative;
  display: flex;
  flex-direction: column;
  padding: 16px;
  background: var(--el-fill-color-blank, #fff);
  border: 1px solid var(--el-border-color-light, #e4e7ed);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  min-height: 180px;
}

.rule-library-card:hover {
  border-color: var(--el-color-primary, #409eff);
  box-shadow: 0 4px 16px rgba(64, 158, 255, 0.12);
  transform: translateY(-2px);
}

.rule-library-card.is-system {
  background: var(--el-fill-color-light, #fafafa);
}

.rule-library-card.is-disabled {
  opacity: 0.6;
}

.rule-library-card.is-readonly {
  cursor: default;
}

.rule-library-card.is-readonly:hover {
  border-color: var(--el-border-color-light, #e4e7ed);
  box-shadow: none;
  transform: none;
}

/* 顶部 */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 8px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.library-icon {
  color: var(--el-color-primary, #409eff);
  flex-shrink: 0;
}

.is-system .library-icon {
  color: var(--el-text-color-secondary, #909399);
}

.lock-icon {
  color: var(--el-text-color-secondary, #909399);
  flex-shrink: 0;
}

.library-meta {
  flex: 1;
  min-width: 0;
}

.library-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary, #303133);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.4;
}

.is-system .library-name {
  color: var(--el-text-color-regular, #606266);
}

.library-code {
  font-size: 12px;
  color: var(--el-text-color-secondary, #909399);
  font-family: monospace;
  margin-top: 2px;
}

/* 右上角操作按钮：默认半透明，hover 时变亮（避免布局跳动）*/
.card-actions {
  display: flex;
  align-items: center;
  gap: 0;
  opacity: 0.4;
  transition: opacity 0.2s ease;
}

.rule-library-card:hover .card-actions {
  opacity: 1;
}

.card-actions .el-button {
  padding: 4px 0px;
}

.text-danger {
  color: var(--el-color-danger, #f56c6c);
}

/* 描述 */
.library-desc {
  font-size: 13px;
  color: var(--el-text-color-regular, #606266);
  line-height: 1.5;
  height: 40px;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  margin-bottom: 12px;
}

/* 底部统计 */
.card-stats {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 10px 0;
  border-top: 1px dashed var(--el-border-color-light, #e4e7ed);
  border-bottom: 1px dashed var(--el-border-color-light, #e4e7ed);
  margin-bottom: 8px;
}

.stat-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.stat-label {
  font-size: 11px;
  color: var(--el-text-color-secondary, #909399);
}

.stat-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary, #303133);
}

.stat-divider {
  width: 1px;
  height: 24px;
  background: var(--el-border-color-light, #e4e7ed);
}

/* 状态 */
.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
}

.status-info {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: auto;
}

/* 库类型标签（纯文本 + 颜色，与 footer 状态区风格统一）*/
.library-type {
  font-size: 12px;
  font-weight: 500;
}

.library-type.expert {
  color: var(--el-color-primary, #409eff);
}

.library-type.fuzzy {
  color: var(--el-color-warning, #e6a23c);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.active {
  background: var(--el-color-success, #67c23a);
  box-shadow: 0 0 0 3px rgba(103, 194, 58, 0.15);
}

.status-dot.inactive {
  background: var(--el-text-color-placeholder, #c0c4cc);
}

.status-text {
  font-size: 12px;
  color: var(--el-text-color-regular, #606266);
}
</style>
