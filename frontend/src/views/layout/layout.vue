<template>
  <div :class="classObj" class="app-wrapper">
    <div
      v-if="classObj.mobile && sidebar.opened" 
      class="drawer-bg" 
      @click="handleClickOutside"
    ></div>
    <sidebar 
      class="sidebar-container" 
      :collapse="classObj.hideSidebar"
    ></sidebar>
    <div class="main-container">
      <div :class="{ 'fixed-header': fixedHeader }">
        <navbar />
      </div>
      <div v-if="fixedHeader" style="height:40px"></div>
      <app-main />
      <right-panel v-if="showSettings">
        <settings />
      </right-panel>
      <!-- <div class="copyright-notice">
        <a 
          target="_blank" 
          style="color: #5c6b77" 
          href="https://beian.miit.gov.cn/"
        >
          鄂ICP备2021009988号-1
        </a>&nbsp;
        <span style="color: #5c6b77">@2020-2030 武汉模鼎科技有限公司 版权所有 保留一切权利</span>
      </div> -->
    </div>
  </div>
</template>

<script lang="ts">
import { Component, Vue } from "vue-property-decorator"
import { mixins } from "vue-class-component"
import ResizeMixin from "./mixin/ResizeHandler"
import { DeviceType, AppModule } from "@/store/modules/app"
import { SettingsModule } from "@/store/modules/settings"
import { Sidebar, Navbar, AppMain } from "./components"
import RightPanel from "@/components/rightPanel/index.vue"
import Settings from "./components/settings/index.vue"

@Component({
  components: {
    Sidebar,
    Navbar,
    AppMain,
    RightPanel,
    Settings
  },
})
export default class Layout extends mixins(ResizeMixin) {
  get classObj() {
    return {
      hideSidebar: !this.sidebar.opened,
      openSidebar: this.sidebar.opened,
      withoutAnimation: this.sidebar.withoutAnimation,
      mobile: this.device === DeviceType.Mobile,
    }
  }

  get fixedHeader() {
    return SettingsModule.fixedHeader
  }

  get showSettings() {
    return SettingsModule.showSettings
  }

  private handleClickOutside() {
    AppModule.CloseSideBar(false)
  }
}
</script>

<style lang="scss" scoped>
  @import "src/styles/mixin.scss";
  @import "src/styles/variables.scss";

  .app-wrapper {
    @include clearfix;
    position: relative;
    height: 100%;
    width: 100%;
  }

  .drawer-bg {
    background: #000;
    opacity: 0.3;
    width: 100%;
    top: 0;
    height: 100%;
    position: absolute;
    z-index: 999;
  }

  .sidebar-container {
    transition: width 0.28s;
    width: $sideBarWidth !important;
    height: 100%;
    position: fixed;
    font-size: 0px;
    top: 0;
    bottom: 0;
    left: 0;
    z-index: 1001;
    overflow: hidden;
  }

  .main-container {
    min-height: 100%;
    transition: margin-left .28s;
    margin-left: $sideBarWidth;
    position: relative;
  }

  .fixed-header {
    position: fixed;
    top: 0;
    right: 0;
    z-index: 9;
    width: calc(100% - #{$sideBarWidth});
    transition: width 0.28s;
  }

  /* 隐藏sidebar */
  .hideSidebar {
    
    .sidebar-container {
      width: $sideBarHideWidth !important;
    }

    .main-container {
      margin-left: $sideBarHideWidth;
    }

    .fixed-header {
      width: calc(100% - #{$sideBarHideWidth});
    }
  }

  /* for mobile response 适配移动端 */
  .mobile {
    .main-container {
      margin-left: 0px;
    }

    .fixed-header {
      width: 100%;
    }

    .sidebar-container {
      transition: transform .28s;
      width: $sideBarWidth !important;
    }

    &.openSidebar {
      position: fixed;
      top: 0;
    }

    &.hideSidebar {
      .sidebar-container {
        transition-duration: 0.3s;
        transform: translate3d(-$sideBarWidth, 0, 0);
      }
    }
  }

  .withoutAnimation {
    .main-container,
    .sidebar-container {
      transition: none;
    }
  }

  .copyright-notice {
    text-align: center; 
    position: fixed; 
    width: 100%; 
    bottom: 0px;
  }
</style>
