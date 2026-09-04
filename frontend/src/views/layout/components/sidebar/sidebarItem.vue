<!--
  SidebarItem：递归菜单项
  - 始终渲染为叶子节点（支持任意嵌套层级）
  - alwaysShow=false + 单子菜单 → 自动收敛（父级被隐藏，子菜单提升为顶级）
  - alwaysShow=true → 始终保留父级

  折叠态（collapsed=true）：
  - 叶子节点：title 隐藏，icon 居中显示（icon-only 模式）
  - 父级节点：title + arrow 隐藏，整体作为 popover trigger
    - 点击触发 popover，在右侧弹出子菜单列表（标准展开模式）

  展开态（collapsed=false）：
  - 完整渲染 title + arrow + 子菜单 inline 展开/折叠
  - 动效：
    - 箭头：单 icon (chevron-down) + transform rotate 切换方向
    - 子菜单：<Transition> + max-height 展开/折叠
    - 激活态：左侧色条 scaleY 动画 + 背景淡入
    - hover：背景 + 文字淡入
-->
<template>
  <!-- 叶子节点（无子菜单） -->
  <li v-if="!item.children || item.children.length === 0" class="sidebar-item">
    <router-link
      :to="item.path"
      :class="[
        'sidebar-item__link',
        {
          'sidebar-item__link--active': isActive,
          'sidebar-item__link--collapsed': collapsed,
        },
      ]"
    >
      <AppIcon v-if="item.icon" :icon="item.icon" class="sidebar-item__icon" />
      <span v-if="!collapsed" class="sidebar-item__title">{{ item.title }}</span>
    </router-link>
  </li>

  <!-- 有子菜单的父级（alwaysShow=true 才显示） -->
  <li v-else class="sidebar-item sidebar-item--parent">
    <!-- ───────── 展开态：inline 展开 ───────── -->
    <template v-if="!collapsed">
      <div
        :class="['sidebar-item__link', 'sidebar-item__link--parent', { 'sidebar-item__link--active': isActive }]"
        :title="isActive && !isOpen ? `当前页面在 ${item.title} 下` : ''"
        @click="toggleOpen"
      >
        <AppIcon v-if="item.icon" :icon="item.icon" class="sidebar-item__icon" />
        <span class="sidebar-item__title">{{ item.title }}</span>
        <!-- 折叠状态下，箭头本身高亮提示"内有激活项" -->
        <AppIcon
          icon="mdi:chevron-down"
          :class="[
            'sidebar-item__arrow',
            { 'is-open': isOpen, 'has-active-child': isActive && !isOpen },
          ]"
        />
      </div>
      <Transition name="submenu">
        <ul v-show="isOpen" class="sidebar-item__children">
          <SidebarItem
            v-for="child in item.children"
            :key="child.path"
            :item="child"
          />
        </ul>
      </Transition>
    </template>

    <!-- ───────── 折叠态：popover 弹子菜单 ───────── -->
    <el-popover
      v-else
      placement="right-start"
      :width="200"
      trigger="click"
      popper-class="sidebar-submenu-popover"
      :show-arrow="false"
    >
      <template #reference>
        <div
          :class="[
            'sidebar-item__link',
            'sidebar-item__link--parent',
            'sidebar-item__link--collapsed',
            {
              'sidebar-item__link--active': isActive,
              'sidebar-item__link--has-active-child': isActive,
            },
          ]"
          :title="item.title"
        >
          <AppIcon v-if="item.icon" :icon="item.icon" class="sidebar-item__icon" />
        </div>
      </template>

      <!-- popover 内容：父级标题 + 子菜单列表 -->
      <div class="sidebar-submenu">
        <div class="sidebar-submenu__title">{{ item.title }}</div>
        <ul class="sidebar-submenu__list">
          <li
            v-for="child in item.children"
            :key="child.path"
            class="sidebar-submenu__item"
          >
            <router-link
              :to="child.path"
              :class="[
                'sidebar-submenu__link',
                {
                  'sidebar-submenu__link--active':
                    route.path === child.path ||
                    route.path.startsWith(child.path + '/'),
                },
              ]"
            >
              <AppIcon v-if="child.icon" :icon="child.icon" class="sidebar-submenu__icon" />
              <span>{{ child.title }}</span>
            </router-link>
          </li>
        </ul>
      </div>
    </el-popover>
  </li>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

interface MenuItem {
  path: string
  title: string
  icon?: string
  children?: MenuItem[]
}

const props = withDefaults(
  defineProps<{
    item: MenuItem
    collapsed?: boolean
  }>(),
  { collapsed: false }
)

const route = useRoute()

// 当前路由匹配：激活态判断（自身或子路由匹配都算激活）
const isActive = computed(() => {
  return (
    route.path === props.item.path ||
    route.path.startsWith(props.item.path + '/')
  )
})

// 展开状态：默认展开（当路由匹配到子路由时展开）
const isOpen = ref(isActive.value)

// 路由变化时，若当前菜单激活 → 自动展开父级
// 这样用户即使之前手动折叠了父级，路由变化后也会自动展开
watch(isActive, (val) => {
  if (val) isOpen.value = true
})

// 用户主动 toggle：完全自由（不受激活态限制）
// 激活状态通过小圆点提示，不强制折叠状态
const toggleOpen = () => {
  isOpen.value = !isOpen.value
}
</script>

<style scoped lang="scss">
// ──────────────────────────────────────
// 子菜单展开/折叠过渡（柔和版）
// - duration 0.5s + Standard 缓和曲线 = "全在柔和地带"
//  - 只过渡 max-height + opacity，不动位移（减少视觉噪声）
// - max-height 上限设大一些，确保动画时长始终饱满
// ──────────────────────────────────────
.submenu-enter-active,
.submenu-leave-active {
  transition: max-height 0.5s cubic-bezier(0.32, 0.72, 0, 1),
              opacity 0.35s ease;
  overflow: hidden;
}
.submenu-enter-from,
.submenu-leave-to {
  max-height: 0;
  opacity: 0;
}
.submenu-enter-to,
.submenu-leave-from {
  max-height: 1200px;
  opacity: 1;
}

.sidebar-item {
  list-style: none;
  user-select: none;

  &__link {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 0 20px;
    height: 44px;
    color: #bfcbd9;
    text-decoration: none;
    cursor: pointer;
    position: relative;       // 锚定 ::before 伪元素色条
    font-size: 14px;
    transition: background 0.2s ease, color 0.2s ease;

    // 左侧色条（激活态显示）
    &::before {
      content: '';
      position: absolute;
      left: 0;
      top: 6px;
      bottom: 6px;
      width: 3px;
      border-radius: 0 2px 2px 0;
      background: #fff;
      transform: scaleY(0);
      transform-origin: center;
      transition: transform 0.4s cubic-bezier(0.32, 0.72, 0, 1);
    }

    &:hover {
      background: rgba(255, 255, 255, 0.06);
      color: #fff;
    }

    &--active {
      color: #fff;
      background: var(--theme-primary);

      &::before {
        transform: scaleY(1);  // 激活：色条展开
      }
    }

    // 父级激活态：仅色条高亮，不重复背景（避免双重高亮）
    &--parent {
      &.sidebar-item__link--active {
        background: transparent;
        color: #fff;

        &::before {
          background: var(--theme-primary);
        }
      }
    }

    // 折叠态：去掉左右 padding，icon 居中
    &--collapsed {
      padding: 0;
      justify-content: center;

      &.sidebar-item__link--parent {
        // 折叠态的父级：背景轻微区分（hover/active 提示）
        &.sidebar-item__link--has-active-child {
          // 不加背景，只用色条——保持视觉简洁
          color: #fff;

          &::before {
            background: var(--theme-primary);
            transform: scaleY(1);
          }
        }
      }
    }
  }

  &__icon {
    font-size: 18px;
    flex-shrink: 0;
    transition: transform 0.3s cubic-bezier(0.32, 0.72, 0, 1);
  }

  &__link:hover &__icon {
    transform: scale(1.08);
  }

  &__title {
    flex: 1;
    line-height: 1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  // 箭头：单 icon (chevron-down) + rotate
  // 收起态：rotate(-90deg) → 视觉朝右
  // 展开态：rotate(0deg)    → 视觉朝下
  // 高亮态：isActive && !isOpen → 变亮白色 + 三层 drop-shadow 光晕（提示内有激活子项）
  &__arrow {
    font-size: 16px;
    color: rgba(255, 255, 255, 0.5);  // 默认浅灰色
    transform: rotate(-90deg);
    transform-origin: center;
    transition: transform 0.45s cubic-bezier(0.32, 0.72, 0, 1),
                color 0.4s ease,
                font-size 0.4s ease,
                filter 0.4s ease;

    // 折叠 + 激活：箭头变成亮白色 + 三层明显光晕
    // 内圈锐利 → 中圈明显扩散 → 外圈远扩散，效果温润醒目
    &.has-active-child {
      color: #fff;
      font-size: 18px;  // 轻微放大（更醒目）
      filter: drop-shadow(0 0 3px rgba(255, 255, 255, 1))
              drop-shadow(0 0 10px rgba(255, 255, 255, 0.85))
              drop-shadow(0 0 16px rgba(255, 255, 255, 0.55));
    }

    // 展开：朝下 + 浅色高亮
    &.is-open {
      transform: rotate(0deg);
      color: rgba(255, 255, 255, 0.85);
    }
  }

  &__children {
    list-style: none;
    margin: 0;
    padding: 0;
    background: rgba(0, 0, 0, 0.15);

    .sidebar-item__link {
      padding-left: 48px;
      height: 38px;
      font-size: 13px;
    }
  }
}

// ──────────────────────────────────────
// 折叠态 popover 子菜单样式（默认主题：白底黑字）
// ──────────────────────────────────────
.sidebar-submenu {
  &__title {
    font-size: 13px;
    font-weight: 600;
    color: #303133;
    padding: 4px 12px 8px;
    border-bottom: 1px solid #ebeef5;
    margin-bottom: 4px;
  }

  &__list {
    list-style: none;
    margin: 0;
    padding: 0;
  }

  &__item {
    list-style: none;
  }

  &__link {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 12px;
    border-radius: 4px;
    color: #606266;
    text-decoration: none;
    font-size: 14px;
    transition: background 0.15s ease, color 0.15s ease;

    &:hover {
      background: #f5f7fa;
      color: var(--theme-primary);
    }

    &--active {
      background: var(--theme-primary);
      color: #fff;

      &:hover {
        background: var(--theme-primary);
        color: #fff;
      }
    }
  }

  &__icon {
    font-size: 16px;
    flex-shrink: 0;
  }
}
</style>

<!--
  Popover 内容被 teleport 到 body，scoped 样式不生效，需 unscoped 块定义
  选择器限定在 .sidebar-submenu-popover 内，避免污染全局
-->
<style lang="scss">
.sidebar-submenu-popover {
  padding: 8px 4px !important;
  border: none !important;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15) !important;
}

.sidebar-submenu-popover .sidebar-submenu {
  &__title {
    font-size: 13px;
    font-weight: 600;
    color: #303133;
    padding: 4px 12px 8px;
    border-bottom: 1px solid #ebeef5;
    margin-bottom: 4px;
  }

  &__list {
    list-style: none;
    margin: 0;
    padding: 0;
  }

  &__item {
    list-style: none;
  }

  &__link {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 12px;
    border-radius: 4px;
    color: #606266;
    text-decoration: none;
    font-size: 14px;
    transition: background 0.15s ease, color 0.15s ease;

    &:hover {
      background: #f5f7fa;
      color: var(--theme-primary);
    }

    &--active {
      background: var(--theme-primary);
      color: #fff;

      &:hover {
        background: var(--theme-primary);
        color: #fff;
      }
    }
  }

  &__icon {
    font-size: 16px;
    flex-shrink: 0;
  }
}
</style>