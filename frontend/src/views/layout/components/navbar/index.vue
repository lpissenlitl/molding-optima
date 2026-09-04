<!--
  Navbar：顶部栏
  - 左侧：sidebar 折叠/展开按钮 + 面包屑
  - 右侧：用户区（占位）
  - sidebar 按钮用 Element Plus 的 Fold / Expand icon，语义直接
  - 面包屑从 route.matched 自动生成
-->
<template>
  <div class="navbar">
    <div class="navbar__left">
      <button
        class="navbar__hamburger"
        :aria-label="collapsed ? '展开侧边栏' : '折叠侧边栏'"
        @click="$emit('toggle-sidebar')"
      >
        <el-icon :size="22">
          <AppIcon v-if="!collapsed" icon="mdi:chevron-left" style="font-size: 22px;" />
          <AppIcon v-else icon="mdi:chevron-right" style="font-size: 22px;" />
        </el-icon>
      </button>

      <nav class="navbar__breadcrumbs">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item
            v-for="(item, idx) in breadcrumbs"
            :key="item.path"
            :to="idx < breadcrumbs.length - 1 ? { path: item.path } : undefined"
          >
            {{ item.title }}
          </el-breadcrumb-item>
        </el-breadcrumb>
      </nav>
    </div>

    <div class="navbar__right">
      <!-- 设置入口（点击弹出系统设置抽屉）-->
      <button
        class="navbar__action"
        aria-label="系统设置"
        @click="settingsOpen = true"
      >
        <AppIcon icon="mdi:cog-outline" />
      </button>

      <!-- 用户区 -->
      <el-dropdown trigger="click">
        <span class="navbar__user" :title="userStore.display_name">
          <AppIcon
            :icon="userStore.is_admin ? 'mdi:shield-account' : 'mdi:account-circle'"
            class="navbar__user-icon"
          />
          <span>{{ userStore.display_name }}</span>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item @click="settingsOpen = true">
              <AppIcon icon="mdi:cog-outline" class="navbar__menu-icon" />
              系统设置
            </el-dropdown-item>
            <el-dropdown-item divided @click="handleLogout">
              <AppIcon icon="mdi:logout" class="navbar__menu-icon" />
              退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <!-- 系统设置抽屉 -->
      <SettingsDrawer v-model="settingsOpen" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import SettingsDrawer from '@/components/SettingsDrawer.vue'

defineProps<{
  collapsed?: boolean
}>()

defineEmits<{
  (e: 'toggle-sidebar'): void
}>()

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 系统设置抽屉状态
const settingsOpen = ref(false)

const handleLogout = () => {
  userStore.clear()
  router.push('/login')
}

// 面包屑：从 route.matched 提取有 title 的层级
const breadcrumbs = computed(() =>
  route.matched
    .filter(r => r.meta?.title && r.path !== '/')
    .map(r => ({
      path: r.path,
      title: r.meta?.title as string,
    }))
)
</script>

<style scoped lang="scss">
.navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  // 左侧 padding 缩小，让 hamburger 离 sidebar 更近
  padding: 0 20px 0 6px;

  &__left {
    display: flex;
    align-items: center;
    // 缩小 hamburger 与 breadcrumb 之间的间距
    gap: 4px;
    min-width: 0;
    flex: 1;
  }

  // ──────────────────────────────────────
  // sidebar 折叠/展开按钮（用 Element Plus <Fold> / <Expand> icon）
  // ──────────────────────────────────────
  &__hamburger {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    padding: 0;
    border: none;
    background: transparent;
    border-radius: 6px;
    cursor: pointer;
    color: var(--color-text-regular);
    transition: background 0.2s, color 0.2s;

    &:hover {
      background: var(--color-bg-page);
      color: var(--theme-primary);
    }

    &:active {
      background: var(--color-bg-mask, rgba(0, 0, 0, 0.05));
    }
  }

  // ──────────────────────────────────────
  // 面包屑
  // ──────────────────────────────────────
  // ─────────────────────────────────────
// 面包屑（Element Plus el-breadcrumb）
// - 当前页（最后一级）：主色 + 加粗
// - 中间路径：常规色 + hover 变主题色
// - 分隔符：次要色 + 50% 透明
// ─────────────────────────────────────
&__breadcrumbs {
    :deep(.el-breadcrumb) {
      font-size: 14px;
    }

    // 当前页（最后一级）：主色 + 加粗
    :deep(.el-breadcrumb__item:last-child .el-breadcrumb__inner) {
      color: var(--color-text-primary);
      font-weight: 600;
      cursor: default;
    }

    // 中间路径 hover：变主题色，传达可点击
    :deep(.el-breadcrumb__item:not(:last-child) .el-breadcrumb__inner:hover) {
      color: var(--theme-primary);
    }

    // 分隔符：浅灰半透明
    :deep(.el-breadcrumb__separator) {
      color: var(--color-text-secondary);
      opacity: 0.5;
    }
  }

  &__right {
    display: flex;
    align-items: center;
    gap: 16px;
    flex-shrink: 0;
  }

  // 设置按钮（齿轮）
  &__action {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    padding: 0;
    border: none;
    background: transparent;
    border-radius: 6px;
    cursor: pointer;
    color: var(--color-text-regular);
    font-size: 20px;
    transition: background 0.2s, color 0.2s;

    &:hover {
      background: var(--color-bg-page);
      color: var(--theme-primary);
    }
  }

  &__menu-icon {
    margin-right: 8px;
    font-size: 16px;
    vertical-align: middle;
  }

  &__user {
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--color-text-regular);
    font-size: 14px;
    cursor: pointer;
    padding: 4px 8px;
    border-radius: 4px;
    transition: background 0.2s;

    &:hover {
      background: var(--color-bg-page);
    }

    &-icon {
      font-size: 20px;
    }

    // 头像首字母（avatar 缺失时使用）
    &-avatar {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 24px;
      height: 24px;
      border-radius: 50%;
      background: var(--theme-primary);
      color: #fff;
      font-size: 12px;
      font-weight: 600;
    }
  }
}
</style>