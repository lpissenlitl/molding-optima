<!-- Sidebar：左侧菜单：数据源 router.options.routes（自动从 router 生成），hidden=true 的路由不显示；alwaysShow=false 且只有 1 个子菜单时父级隐藏、子菜单提升为顶级 -->

<template>
  <nav class="sidebar">
    <ul class="sidebar__menu">
      <SidebarItem
        v-for="item in menuItems"
        :key="item.path"
        :item="item"
        :collapsed="collapsed"
      />
    </ul>
  </nav>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import SidebarItem from './sidebarItem.vue'
import { useUserStore } from '@/stores/user'

interface MenuItem {
  path: string
  title: string
  icon?: string
  children?: MenuItem[]
}

withDefaults(
  defineProps<{
    collapsed?: boolean
  }>(),
  { collapsed: false }
)

const router = useRouter()

/** 管理员标识（超管 || 租户管理员）：与后端 `require_admin` 判定一致 */
const userStore = useUserStore()
const isAdmin = computed(() => userStore.is_admin)

/** 递归解析路由为菜单项：过滤 hidden=true 与 adminOnly（非管理员），按父级 basePath 计算完整路径，alwaysShow=false 且只有 1 个子菜单时返回子菜单（隐藏父级） */

function parseMenu(routes: RouteRecordRaw[], basePath = ''): MenuItem[] {
  const items: MenuItem[] = []

  for (const route of routes) {
    if (route.meta?.hidden) continue
    // ⚠️ **adminOnly 路由对非管理员直接隐藏**
    //    （后端同一批接口也挂了 require_admin，前端隐藏只是避免用户点进去撞 403）
    if (route.meta?.adminOnly === true && !isAdmin.value) continue

    const fullPath = resolvePath(basePath, route.path)
    const item: MenuItem = {
      path: fullPath,
      title: (route.meta?.title as string) || route.path,
      icon: route.meta?.icon as string | undefined,
      children: undefined,
    }

    // 处理子路由
    if (route.children?.length) {
      const children = parseMenu(route.children, fullPath)

      // 收敛规则：alwaysShow=false 且只有 1 个子菜单 → 提升子菜单
      if (!route.meta?.alwaysShow && children.length === 1) {
        const child = children[0]
        // 合并 icon（如果父级有 icon，保留给子菜单）
        if (!child.icon && item.icon) {
          child.icon = item.icon
        }
        items.push(child)
      } else {
        item.children = children
        items.push(item)
      }
    } else {
      items.push(item)
    }
  }

  return items
}

/** 拼接路径（处理 /、:params 等情况） */
function resolvePath(base: string, path: string): string {
  if (!path.startsWith('/')) {
    path = base.replace(/\/$/, '') + '/' + path
  }
  return path.replace(/\/+/g, '/')
}

// 从 router 提取顶级菜单项
const menuItems = computed<MenuItem[]>(() => {
  const layoutRoute = router.options.routes.find(r => r.path === '/')
  if (!layoutRoute?.children) return []
  return parseMenu(layoutRoute.children, '')
})
</script>

<style scoped lang="scss">
.sidebar {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;

  &__menu {
    list-style: none;
    margin: 0;
    padding: 0;
  }
}
</style>