<!--
  主布局：Sidebar + Navbar + AppMain
  - 经典三段式布局（现代化包装）
  - 支持 hamburger 折叠
    - 桌面端（≥992px）：sidebar 缩窄到 60px
    - 移动端（<992px）：sidebar 抽屉化（默认隐藏）
  - 布局专用色硬编码在组件内（不在全局 tokens）
  - 详见 architecture.md §ADR-004
-->
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
// 初始化时读取用户偏好（仅桌面端生效）
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
  /*
   * 锁死 100vh（不是 min-height） + overflow: hidden
   *
   * 原因：
   * - 之前用 min-height: 100vh，layout 会被内容撑高
   * - 当表单超长时，layout 超过视窗 → body 出现滚动条
   * - 侧边栏作为 layout 的子元素，跟着页面一起滚
   *   → 出现"下拉侧边栏菜单也被滚动"的 bug
   *
   * 修复后：
   * - layout 始终 = 视窗高度，body 不可能滚动
   * - 侧边栏和主内容区都在 layout 内部独立滚动
   *   （侧边栏的 .sidebar overflow-y: auto 处理菜单过长）
   *   （主内容区的 .layout__content overflow: auto 处理表单过长）
   */
  height: 100vh;
  overflow: hidden;
  background: var(--color-bg-page);
  /*
   * 工业软件后台：最低 1024px 宽度。
   * 低于此值出现水平滚动条，不重排。
   * 这样表格/列筛选/批量操作不会在手机上被压缩错位。
   */
  min-width: 1024px;

  &__mask {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.4);
    z-index: 999;
  }

  // ──────────────────────────────────────
  // Sidebar：桌面端默认 220px，可折叠到 60px
  // ──────────────────────────────────────
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
    }
  }

  &__main {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-width: 0;
    /*
     * min-height: 0：flex 子项默认 min-height: auto，会被内容撑开
     * 设为 0 后，子项可以收缩到比内容更小，overflow:auto 才会触发
     */
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
    /*
     * min-height: 0：同上，flex 子项必须允许收缩
     * overflow:auto 才会在内容超过可视区时出现滚动条
     */
    min-height: 0;
  }

  // ──────────────────────────────────────
  // 移动端：sidebar 抽屉化
  // - 默认 transform: translateX(-100%) 隐藏在屏幕左侧
  // - .is-drawer-open 时 transform: translateX(0) 显示
  // - 桌面端折叠（is-collapsed-desktop）在移动端被覆盖（始终 220px）
  // ──────────────────────────────────────
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