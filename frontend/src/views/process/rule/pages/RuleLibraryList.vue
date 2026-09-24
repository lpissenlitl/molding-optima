<!--
  RuleLibraryList.vue - 规则管理主页（父容器）

  职责：
  - 顶部 tabs 框架（胶囊 segmented control + 滑动 indicator）
  - URL 同步（?tab=libraries | ?tab=keywords）
  - 计算 isSuperuser（从 user store 读取）
  - 提供共享样式（unscoped）：.tab-panel / .card-grid / .table-wrapper / .pagination / .mono
    - 搜索表单类名（.search-container / .search-form / .search-actions）用全局 custom-form.scss

  子组件：
  - RuleLibraryTab.vue：规则库 tab（搜索 + 卡片网格 + 分页 + 弹窗）
  - RuleKeywordTab.vue：关键词 tab（搜索 + 表格 + 分页 + 弹窗）

  共享状态：
  - 通过 props 传 activeTab + isSuperuser 给子组件
  - 子组件 watch activeTab 决定是否加载数据
-->
<template>
  <div class="rule-library-list">
    <!-- ============= Tabs（胶囊 Segmented Control）============= -->
    <div class="tab-bar" :style="{ '--tab-count': TABS.length }">
      <!--
        width 用 calc((100% - 8px) / tab-count) 减去 tab-bar 左右 padding（4px*2）
        translateX(index * 100%) 基于 indicator 自身宽度滑动（GPU 加速）
      -->
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

// ============================================================================
// 角色判断
// ============================================================================
//
// 专家规则（ExpertRule）属于平台级内部规则（工艺参数初始化系数），
// 不向租户展示，只有超级管理员才能查看/编辑。
// 后端 ExpertRuleListByLibraryView / ExpertRuleDetailView 已加 require_superuser 装饰器做二次防护。
const userStore = useUserStore()
const isSuperuser = computed(() => userStore.is_superuser)

// ============================================================================
// Tab 切换 + URL 同步
// ============================================================================
//
// 设计说明：
// - 上下布局信息密度过高，规则库多时易产生滚动问题
// - 改为顶部 tabs（div + button 自实现，比 el-tabs 样式更可控）
// - URL 同步：?tab=libraries | ?tab=keywords，刷新保留选中
// - 仅显示名称（不带计数 badge，极简风）

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

<!--
  ============================================================================
  共享样式（unscoped）
  ============================================================================
  说明：以下样式被 RuleLibraryTab.vue 和 RuleKeywordTab.vue 共同使用
  - 因为子组件不写 scoped，本组件的 unscoped 样式天然作用于子组件 template
  - 修改此处样式时，子组件也会跟随变化（单一来源）
  ============================================================================ -->
<style lang="scss">
.rule-library-list {
  padding: 16px;
  /* flex column 撑满父容器（layout__content 已有 overflow: auto）*/
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

/* ==========================================================================
   Tab Panel（共享给两个子组件）
   - flex column 布局：搜索卡片不压缩，卡片网格独立滚动
   - min-height: 0 是 flex 子项滚动生效的关键
   ========================================================================== */
.tab-panel {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  /* 底部 padding：避开 fixed 分页器（高度约 48px + 安全边距）*/
  padding-bottom: 60px;
}

/* ==========================================================================
   搜索卡片样式（统一使用全局 .search-container / .search-form / .search-actions）
   - 定义位置：frontend/src/styles/utilities/custom-form.scss
   - 其他页面（CompanyList / UserList / RoleList）同样使用
   - 本组件不重复定义，避免不一致
   ========================================================================== */

/* ==========================================================================
   卡片网格（规则库 tab 使用）
   - flex: 1 撑满搜索卡片下方的剩余空间，独立滚动
   ========================================================================== */
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

/* ==========================================================================
   表格包装层（关键词 tab 使用）
   - flex: 1 撑满搜索卡片下方的剩余空间
   - min-height: 0 关键：允许 flex 子项收缩，撑高才能生效
   - overflow: hidden 让 el-table 内部独立滚动
   ========================================================================== */
.table-wrapper {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ==========================================================================
   分页器（fixed 贴视窗底部，水平居中）
   - 嵌套在 .rule-library-list 内，避免污染其他页面的同名类
     （例如 ExpertRuleSection / RuleMethodSection 也用了 class="pagination"）
   - left 使用 layout 暴露的 --sidebar-width 变量，避免覆盖侧边栏
   - 桌面端展开 220px / 折叠 60px / 移动端 0px（响应式自动适配）
   ========================================================================== */
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

/* ==========================================================================
   工具样式
   ========================================================================== */
.mono {
  font-family: 'Courier New', Consolas, monospace;
  color: #303133;
}
</style>

<!--
  ============================================================================
  本组件专用样式（scoped）
  ============================================================================
  tabs / indicator 等仅本组件使用的样式
  ============================================================================ -->
<style scoped lang="scss">
/* ==========================================================================
   Tab Bar（胶囊 Segmented Control，自定义 div + button）
   设计：参考 Apple iOS Segmented Control
        - 底层灰色胶囊背景
        - 选中态：白色凸起 + 阴影 + 蓝色文字
        - 滑动 indicator（用 transform 动画，GPU 加速）
   ========================================================================== */
.tab-bar {
  position: relative;
  display: inline-flex;
  background: #f5f7fa;
  border-radius: 10px;
  padding: 4px;
  margin-bottom: 24px;
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.03);
}

/* 滑动 indicator：白色凸起 + 阴影
   width 由 inline-style 动态控制（calc((100% - 8px) / tab-count)）
   left: 4px 对应 tab-bar 的 padding-left，保证从第一个 button 位置开始 */
.tab-indicator {
  position: absolute;
  top: 4px;
  bottom: 4px;
  left: 4px;
  /* 淡主题色背景：上 8% 透明度 → 下 20% 透明度，下深上浅
   * light:     浅蓝白 #f4f6f9 → 较深蓝白 #dde4ee
   * dark:      近黑 #202428 → 深灰蓝 #3b4756
   * high-contrast: 近黑 #1c1a08 → 深棕黑 #383107
   */
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