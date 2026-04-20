<template>
  <div 
    v-if="item.meta && !item.meta.hidden" 
    :class="['menu-wrapper', collapse ? 'simple-mode' : 'full-mode', {'first-level': !isNest}]"
  >
    <template v-if="showingChild(item.children, item)">
      <app-link :to="resolvePath(lastShowingChild.path)">
        <el-menu-item 
          :index="resolvePath(lastShowingChild.path)" 
          :class="{'submenu-title-noDropdown': !isNest}"
        >
          <svg-icon 
            v-if="lastShowingChild.meta && lastShowingChild.meta.icon" 
            :name="lastShowingChild.meta.icon"
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
    <el-submenu
      v-else-if="$store.state.user.userinfo.permissions.includes(item.meta.perm)"
      :index="resolvePath(item.path)" 
      popper-append-to-body
    >
      <template slot="title">
        <svg-icon 
          v-if="item.meta && item.meta.icon" 
          :name="item.meta.icon"
        />
        <span 
          v-if="item.meta && item.meta.title" slot="title"
        >{{ item.meta.title }}</span>
      </template>
      <template v-for="(route, index) in item.children">
        <sidebar-item        
          v-if="$store.state.user.userinfo.permissions.includes(route.meta.perm)"
          :key="index" 
          :item="route" 
          :base-path="item.path" 
          :collapse="collapse" 
          class="nest-menu"
        />
      </template>
    </el-submenu>
  </div>
</template>

<script lang="ts">
import path from 'path';
import { Route } from 'vue-router';
import { isExternal } from '@/utils/validate';
import { Component, Vue, Prop } from 'vue-property-decorator';
import AppLink from './link.vue';

@Component({
  // Set 'name' here to prevent uglifyjs from causing recursive component not work
  // See https://medium.com/haiiro-io/element-component-name-with-vue-class-component-f3b435656561 for detail
  name: 'SidebarItem',
  components: {
    AppLink,
  },
})
export default class SidebarItem extends Vue {
  @Prop({ required: true }) private item!: Route;
  @Prop({ default: false }) private isNest!: boolean;
  @Prop({ default: false }) private collapse!: boolean;
  @Prop({ default: '' }) private basePath!: string;

  private lastShowingChild: Route | null = null;

  private showingChild(children: Route[], parent: Route) {
    let showingChildren: Route[] = [];
    if (children) {
      showingChildren = children.filter((item: Route) => {
        if (item.meta && item.meta.hidden) {
          return false;
        } else {
          return true;
        }
      });

      if (showingChildren.length === 0) {
        this.lastShowingChild = parent
        return true;
      } else if (showingChildren.length === 1) {
        this.lastShowingChild = showingChildren[0]
        return true;
      } else if (showingChildren.length > 1) {
        this.lastShowingChild = null;
        return false;
      }

    } else {
      this.lastShowingChild = parent
      return true
    }
  }

  private resolvePath(routePath: string) {
    if (isExternal(routePath)) {
      return routePath;
    }
    return path.resolve(this.basePath, routePath);
  }
}
</script>

<style lang="scss">
@import "src/styles/variables.scss";

.el-submenu.is-active > .el-submenu__title {
  color: $subMenuActiveText !important;
}

.full-mode {
  .nest-menu .el-submenu>.el-submenu__title,
  .el-submenu .el-menu-item {
    background-color: $subMenuBg !important;

    &:hover {
      background-color: $subMenuHover !important;
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

    .el-submenu {
      overflow: hidden;

      &>.el-submenu__title {
        padding-left: 10px !important;

        .el-submenu__icon-arrow {
          display: none;
        }
      }
    }
  }
}
</style>

<style lang="scss" scoped>
.svg-icon {
  margin-right: 16px;
}
</style>
