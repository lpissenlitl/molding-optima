<!-- 主布局：Sidebar + Navbar + AppMain：经典三段式布局，支持 hamburger 折叠（桌面端 ≥992px 缩窄到 60px，移动端 <992px 抽屉化默认隐藏），布局专用色硬编码在组件内（不在全局 tokens），详见 architecture.md §ADR-004 -->

<template>
  <div :class="['layout', { 'layout--drawer-open': isMobile && !collapsed }]">
    <!-- 移动端遮罩（仅在抽屉打开时显示）-->
    <div
      v-if="isMobile && !collapsed"
      class="layout__mask"
      @click="collapsed = true"
    ></div>

    <aside
      :class="[
        'layout__sidebar',
        {
          'is-collapsed-desktop': collapsed && !isMobile,  // 桌面端：60px
          'is-drawer-open': !collapsed,                    // 移动端：抽屉显隐（仅移动端 CSS 生效）
        }
      ]"
    >
      <SidebarLogo :collapsed="collapsed && !isMobile" />
      <Sidebar :collapsed="collapsed && !isMobile" />
    </aside>

    <div class="layout__main">
      <header class="layout__navbar">
        <Navbar :collapsed="collapsed && !isMobile" @toggle-sidebar="toggleSidebar" />
      </header>
      <main class="layout__content">
        <AppMain />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import SidebarLogo from './components/sidebar/sidebarLogo.vue'
import Sidebar from './components/sidebar/index.vue'
import Navbar from './components/navbar/index.vue'
import AppMain from './components/appMain.vue'

const settingsStore = useSettingsStore()

// 折叠状态（true = 收起；移动端表示抽屉关闭）
const collapsed = ref(settingsStore.sidebarDefaultCollapsed)
// 移动端判断（< 992px = 抽屉模式）
const isMobile = ref(false)
const MOBILE_BREAKPOINT = 992

const checkMobile = () => {
  const wasMobile = isMobile.value
  isMobile.value = window.innerWidth < MOBILE_BREAKPOINT

  // 桌面 → 移动：强制收起（抽屉默认隐藏）
  if (!wasMobile && isMobile.value) {
    collapsed.value = true
  }
  // 移动 → 桌面：恢复展开
  else if (wasMobile && !isMobile.value) {
    collapsed.value = false
  }
}

const toggleSidebar = () => {
  collapsed.value = !collapsed.value
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', checkMobile)
})
</script>

<style scoped lang="scss">
.layout {
  display: flex;
  /* 锁死 100vh（不是 min-height） + overflow: hidden：min-height 会让 layout 被内容撑高，表单超长时 body 出现滚动条、侧边栏跟着一起滚；锁死后 layout 恒等于视窗高度，侧边栏与主内容区各自内部滚动 */

  height: 100vh;
  overflow: hidden;
  background: var(--color-bg-page);
  /* 工业软件后台：最低 1024px 宽度。 */
  min-width: 1024px;
  /* 侧边栏宽度变量（供子组件 fixed 元素定位）：默认 220px（桌面端展开）、折叠态 60px（is-collapsed-desktop）、移动端 0px（抽屉化不占主内容空间），子组件可用 left: var(--sidebar-width, 220px) */

  --sidebar-width: 220px;

  &__mask {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.4);
    z-index: 999;
  }

  // Sidebar：桌面端默认 220px，可折叠到 60px

  &__sidebar {
    width: 220px;
    background: var(--menu-bgcolor);  // 主题切换
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    transition: width 0.28s ease;

    // 桌面端折叠态：缩窄到 60px（仅桌面端 CSS 生效）
    &.is-collapsed-desktop {
      width: 60px;
      // 同步侧边栏宽度变量，供 fixed 元素重新计算位置
      --sidebar-width: 60px;
    }
  }

  &__main {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-width: 0;
    /* min-height: 0：flex 子项默认 min-height: auto，会被内容撑开 */
    min-height: 0;
  }

  &__navbar {
    height: 56px;
    background: var(--color-bg-base);  // 跟随主题
    box-shadow: 0 1px 4px rgba(0, 21, 41, 0.06);
    flex-shrink: 0;
  }

  &__content {
    flex: 1;
    padding: 12px;
    overflow: auto;
    /* min-height: 0：同上，flex 子项必须允许收缩 */
    min-height: 0;
  }

  // 移动端：sidebar 抽屉化（默认 translateX(-100%) 隐藏，.is-drawer-open 显示；移动端覆盖桌面端折叠，恒 220px）

  @media (max-width: 991px) {
    &__sidebar {
      position: fixed;
      top: 0;
      bottom: 0;
      left: 0;
      z-index: 1000;
      width: 220px;                  // 移动端始终 220px 全宽
      height: 100vh;
      transform: translateX(-100%);  // 默认隐藏
      transition: transform 0.28s ease;
      // 移动端 sidebar 抽屉化，不占主内容空间
      --sidebar-width: 0px;

      // 覆盖桌面端折叠（移动端不需要 60px 折叠态）
      &.is-collapsed-desktop {
        width: 220px;
      }

      // 抽屉打开
      &.is-drawer-open {
        transform: translateX(0);
      }
    }
  }
}
</style>