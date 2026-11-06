<!-- RuleLibraryList.vue - 规则管理主页（父容器）：顶部 tabs + URL 同步（?tab=libraries|keywords），子组件 RuleLibraryTab / RuleKeywordTab 接收 activeTab + isSuperuser 并自行 watch 决定何时加载 -->
<template>
  <div class="rule-library-list">
    <!-- ============= Tabs（胶囊 Segmented Control）============= -->
    <div class="tab-bar" :style="{ '--tab-count': TABS.length }">
      <!-- width 用 calc((100% - 8px) / tab-count) 减去 tab-bar 左右 padding（4px*2） -->
      <div
        class="tab-indicator"
        :style="{
          width: `calc((100% - 8px) / ${TABS.length})`,
          transform: `translateX(${TABS.findIndex(t => t.key === activeTab) * 100}%)`,
        }"
      ></div>
      <button
        v-for="tab in TABS"
        :key="tab.key"
        type="button"
        :class="['tab-btn', { active: activeTab === tab.key }]"
        @click="switchTab(tab.key)"
      >
        <span class="tab-btn-label">{{ tab.label }}</span>
      </button>
    </div>

    <!-- ============= Tab 1: 规则库 ============= -->
    <RuleLibraryTab
      v-show="activeTab === 'libraries'"
      :active-tab="activeTab"
      :is-superuser="isSuperuser"
    />

    <!-- ============= Tab 2: 关键词 ============= -->
    <RuleKeywordTab
      v-show="activeTab === 'keywords'"
      :active-tab="activeTab"
      :is-superuser="isSuperuser"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import RuleLibraryTab from './RuleLibraryTab.vue'
import RuleKeywordTab from './RuleKeywordTab.vue'
import { useUserStore } from '@/stores/user'

// 角色判断：专家规则属平台级内部规则，仅 superadmin 可见（后端已加 require_superuser 二次防护）
const userStore = useUserStore()
const isSuperuser = computed(() => userStore.is_superuser)

// Tab 切换 + URL 同步：?tab=libraries | ?tab=keywords，刷新保留选中

type TabKey = 'libraries' | 'keywords'

const route = useRoute()
const router = useRouter()

const TABS: Array<{ key: TabKey; label: string }> = [
  { key: 'libraries', label: '规则库' },
  { key: 'keywords', label: '关键词' },
]

const activeTab = ref<TabKey>(
  (route.query.tab as TabKey) && TABS.some(t => t.key === route.query.tab)
    ? (route.query.tab as TabKey)
    : 'libraries',
)

function switchTab(key: TabKey) {
  if (activeTab.value === key) return
  activeTab.value = key
}

// tab 变化同步到 URL（replace 不留历史记录，避免浏览器后退时反复触发）
watch(activeTab, (val) => {
  if (route.query.tab !== val) {
    router.replace({ query: { ...route.query, tab: val } })
  }
})

// 路由参数变化（外部链接 / 浏览器后退）反向同步到 tab
watch(
  () => route.query.tab,
  (val) => {
    const target = TABS.find(t => t.key === val)?.key
    if (target && target !== activeTab.value) {
      activeTab.value = target
    }
  },
)
</script>

<!-- 共享样式（unscoped）：供 RuleLibraryTab / RuleKeywordTab 共用，单一来源 -->
<style lang="scss">
.rule-library-list {
  padding: 16px;
  /* flex column 撑满父容器（layout__content 已有 overflow: auto）*/
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

/* Tab Panel（共享给两个子组件）：flex column 布局，搜索卡片不压缩；min-height: 0 是子项滚动生效的关键 */
.tab-panel {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  /* 底部 padding：避开 fixed 分页器（高度约 48px + 安全边距）*/
  padding-bottom: 60px;
}

/* 搜索卡片：统一用全局 .search-container / .search-form / .search-actions，本组件不重复定义 */

/* 卡片网格（规则库 tab）：flex: 1 撑满搜索卡片下方剩余空间，独立滚动 */
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  min-height: 180px;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 4px;
  margin: -4px;
}

/* 自定义滚动条（Webkit / Blink）*/
.card-grid::-webkit-scrollbar {
  width: 8px;
}

.card-grid::-webkit-scrollbar-thumb {
  background: #d4d7dc;
  border-radius: 4px;
}

.card-grid::-webkit-scrollbar-thumb:hover {
  background: #b4b7bc;
}

/* 空态居中：el-empty 占满整行 + 内部 flex 居中 */
.card-grid:has(> .el-empty) {
  display: flex;
  justify-content: center;
  align-items: center;
}

/* 表格包装层（关键词 tab）：flex: 1 撑满剩余空间；min-height: 0 允许 flex 子项收缩（撑高才生效）；overflow: hidden 让 el-table 内部独立滚动 */
.table-wrapper {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 分页器（fixed 贴视窗底部）：嵌套在 .rule-library-list 内避免污染同名类；left 用 --sidebar-width 变量适配侧边栏宽度 */
.rule-library-list {
  .pagination {
    display: flex;
    justify-content: center;
    position: fixed;
    left: var(--sidebar-width, 220px);
    right: 0;
    bottom: 0;
    z-index: 100;
    padding: 12px 0;
    border-top: 1px solid #ebeef5;
  }
}

/* 工具样式 */
.mono {
  font-family: 'Courier New', Consolas, monospace;
  color: #303133;
}
</style>

<!-- 本组件专用样式（scoped）：tabs / indicator 等 -->
<style scoped lang="scss">
/* Tab Bar（胶囊 Segmented Control，自定义 div + button）：参考 Apple iOS 风格，灰色胶囊底 + 选中态白色凸起 + transform 滑动 indicator */
.tab-bar {
  position: relative;
  display: inline-flex;
  background: #f5f7fa;
  border-radius: 10px;
  padding: 4px;
  margin-bottom: 24px;
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.03);
}

/* 滑动 indicator：白色凸起 + 阴影 */
.tab-indicator {
  position: absolute;
  top: 4px;
  bottom: 4px;
  left: 4px;
  /* 淡主题色背景：上 8% 透明度 → 下 20% 透明度，下深上浅 */
  background: linear-gradient(
    to bottom,
    color-mix(in srgb, var(--el-color-primary, #254373) 8%, transparent),
    color-mix(in srgb, var(--el-color-primary, #254373) 20%, transparent)
  );
  border-radius: 8px;
  /* 主题色阴影（10% 透明度，比之前更淡）*/
  box-shadow:
    0 2px 8px color-mix(in srgb, var(--el-color-primary, #254373) 12%, transparent),
    0 1px 3px rgba(0, 0, 0, 0.04);
  /* 滑动动画：cubic-bezier 让过渡更顺滑 */
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  /* indicator 在 button 之下，不拦截点击 */
  pointer-events: none;
  z-index: 0;
}

.tab-btn {
  position: relative;
  z-index: 1;
  flex: 1;
  min-width: 100px;
  padding: 8px 28px;
  border: none;
  background: transparent;
  color: #606266;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border-radius: 8px;
  outline: none;
  appearance: none;
  -webkit-appearance: none;
  /* 多属性过渡：颜色 / 缩放 */
  transition:
    color 0.25s ease,
    transform 0.15s cubic-bezier(0.34, 1.56, 0.64, 1);
}

/* hover 时非选中 tab 文字变主题色（带轻微提示）*/
.tab-btn:hover:not(.active) {
  color: var(--el-color-primary, #254373);
}

/* 激活 tab 文字：主题色实色（indicator 是淡背景，文字足够清晰）*/
.tab-btn.active {
  color: var(--el-color-primary, #254373);
  font-weight: 600;
}

/* high-contrast 主题：金黄背景上黑字才能看清 */
[data-theme='high-contrast'] .tab-btn.active {
  color: #000;
}

/* 按下时轻微缩放（触感反馈）*/
.tab-btn:active:not(.disabled) {
  transform: scale(0.96);
}

/* label 居中 */
.tab-btn-label {
  display: inline-block;
  line-height: 1;
  white-space: nowrap;
}
</style>