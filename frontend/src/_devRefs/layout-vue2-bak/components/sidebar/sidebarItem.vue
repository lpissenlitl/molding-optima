<template>
  <div
    v-if="item.meta && !item.meta.hidden" 
    :class="['menu-wrapper', collapse ? 'simple-mode' : 'full-mode', {'first-level': !isNest}]"
  >
    <!-- 跳转链接 -->
    <template v-if="showingChild(item.children, item)">
      <app-link v-if="$hasPermission(lastShowingChild.meta.perm)" :to="resolvePath(lastShowingChild.path)">
        <el-menu-item 
          :index="resolvePath(lastShowingChild.path)" 
          :class="{'submenu-title-noDropdown': !isNest}"
        >
          <app-icon 
            v-if="lastShowingChild.meta && lastShowingChild.meta.icon" 
            :icon="lastShowingChild.meta.icon" 
            class="sidebar-menu-icon"
          />
          <span 
            v-if="lastShowingChild.meta && lastShowingChild.meta.title" 
            slot="title"
          >
            {{ lastShowingChild.meta.title }}
          </span>
        </el-menu-item>
      </app-link>
    </template>
    <!-- 子菜单 -->
    <el-submenu
      v-else-if="$hasPermission(item.meta.perm)"
      :index="resolvePath(item.path)" 
      popper-append-to-body
    >
      <template slot="title">
        <app-icon 
          v-if="item.meta && item.meta.icon" 
          :icon="item.meta.icon" 
          class="sidebar-menu-icon"
        />        
        <span 
          v-if="item.meta && item.meta.title" 
          slot="title"
        >
          {{ item.meta.title }}
        </span>
      </template>
      <template v-for="(route, index) in item.children">
        <sidebar-item        
          v-if="$hasPermission(route.meta.perm)"
          :key="index" 
          :item="route" 
          :base-path="item.path" 
          :collapse="collapse" 
        />
      </template>
    </el-submenu>
  </div>
</template>

<script lang="ts">
import path from "path"
import { Route } from "vue-router"
import { isExternal } from "@/utils/validate"
import { Component, Vue, Prop } from "vue-property-decorator"
import AppLink from "./link.vue"

@Component({
  // Set 'name' here to prevent uglifyjs from causing recursive component not work
  // See https://medium.com/haiiro-io/element-component-name-with-vue-class-component-f3b435656561 for detail
  name: "SidebarItem",
  components: {
    AppLink,
  },
})
export default class SidebarItem extends Vue {
  @Prop({ required: true }) private item!: Route
  @Prop({ default: false }) private isNest!: boolean
  @Prop({ default: false }) private collapse!: boolean
  @Prop({ default: "" }) private basePath!: string

  private lastShowingChild: Route | null = null

  private showingChild(children: Route[], parent: Route) {
    let showingChildren: Route[] = []
    if (children) {
      showingChildren = children.filter((item: Route) => {
        if (item.meta && item.meta.hidden) {
          return false
        } else {
          return true
        }
      })

      if (showingChildren.length === 0) {
        this.lastShowingChild = parent
        return true
      } else if (showingChildren.length === 1) {
        this.lastShowingChild = showingChildren[0]
        return true
      } else if (showingChildren.length > 1) {
        this.lastShowingChild = null
        return false
      }

    } else {
      this.lastShowingChild = parent
      return true
    }
  }

  private resolvePath(routePath: string) {
    if (isExternal(routePath)) {
      return routePath
    }
    return path.resolve(this.basePath, routePath)
  }
}
</script>

<style lang="scss">
@import "src/styles/variables.scss";

.el-submenu.is-active > .el-submenu__title {
  color: var(--submenu-active-text) !important;
}
.el-submenu__title:hover {
  background-color: var(--submenu-hover) !important;
}

.el-submenu .el-submenu__title {
  font-family: "Source Han Serif SC";
  font-size: var(--submenu-title-font-size); 
}

.full-mode {
  .el-submenu {
    .el-menu-item {
      background-color: var(--submenu-bg) !important;
      font-family: "Source Han Serif SC";
      font-size: var(--menu-font-size); 
      // text-indent: -5px;
      &:hover {
        background-color: var(--submenu-hover) !important;
      }
    }
  } 
  .el-menu-item {
    font-family: "Source Han Serif SC";
    font-size: var(--submenu-title-font-size); 
    &:hover {
      background-color: var(--submenu-hover) !important;
    }
  }
}

.simple-mode {
  &.first-level {
    .submenu-title-noDropdown {
      padding-left: 10px !important;
      position: relative;

      .el-tooltip {
        padding: 0 10px !important;
      }
    }
  }
  .el-submenu {
    .el-menu-item {
      background-color: var(--submenu-bg) !important;
      font-family: "Source Han Serif SC";
      font-size: var(--menu-font-size); 
      &:hover {
        background-color: var(--submenu-hover) !important;
      }
    }
    .el-submenu__title {
      padding-left: 8px !important;
    }
    .el-submenu__icon-arrow {
      display: none;
    }
  }
  .el-menu-item {
    font-family: "Source Han Serif SC";
    text-indent: -2px;
    font-size: var(--submenu-title-font-size); 
    &:hover {
      background-color: var(--submenu-hover) !important;
    }
  }
}
</style>

<style lang="scss" scoped>
.svg-icon {
  margin-right: 10px;
}

.sidebar-menu-icon {
  margin-right: 8px;
  width: 16px;
  height: 16px;
}
</style>
