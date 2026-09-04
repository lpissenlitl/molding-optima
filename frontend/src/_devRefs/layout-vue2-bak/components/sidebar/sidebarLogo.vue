<template>
  <div
    class="sidebar-logo-container"
    :class="{'collapse': collapse}"
  >
    <transition name="sidebarLogoFade">
      <router-link
        v-if="collapse"
        key="collapse"
        class="sidebar-logo-link"
        to="/"
      >
        <img src="@/image/md.png" class="sidebar-logo">
      </router-link>
      <router-link
        v-else
        key="expand"
        class="sidebar-logo-link"
        to="/"
      >
        <!-- <img src="@/image/intelligent_injection.png" class="sidebar-logo"> -->
        <h1 class="sidebar-title">
          {{ title }}
        </h1>
      </router-link>
    </transition>
  </div>
</template>

<script lang="ts">
import { Component, Prop, Vue } from "vue-property-decorator"
import settings from "@/settings"

@Component({
  name: "SidebarLogo"
})
export default class extends Vue {
  @Prop({ required: true }) private collapse!: boolean

  get title() {
    return  settings.title
  }
}
</script>

<style lang="scss" scoped>

  .sidebar-logo-container {
    position: relative;
    width: 100%;
    height: 52px;
    line-height: 52px;
    background: var(--sidebar-logo-bg);
    text-align: center;
    overflow: hidden;

    & .sidebar-logo-link {
      height: 100%;
      width: 100%;

      & .sidebar-logo {
        width: 100%;
        height: 100%;
      }

      & .sidebar-title {
        display: inline-block;
        margin: 0;
        color: var(--sidebar-title-color);
        font-weight: 580;
        font-family: "Source Han Serif SC";
        line-height: 50px;
        font-size: var(--sidebar-title-font-size);  
        vertical-align: middle;
      }
    }

    &.collapse {
      .sidebar-logo {
        margin-right: 0px;
      }
    }
  }

  .sidebarLogoFade-enter-active {
    transition: opacity 1.5s;
  }

  .sidebarLogoFade-enter,
  .sidebarLogoFade-leave-to {
    opacity: 0;
  }

</style>
