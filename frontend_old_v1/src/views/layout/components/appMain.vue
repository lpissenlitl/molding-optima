<template>
  <section :class="specialStype?'app-main-special':'app-main'">
    <transition name="fade-transform" mode="out-in">
      <!-- or name="fade" -->
      <!-- <router-view :key="key"></router-view> -->
      <router-view />
    </transition>
  </section>
</template>

<script lang="ts">
import { Vue, Component , Watch} from 'vue-property-decorator';
import { Route } from 'vue-router';
@Component
export default class AppMain extends Vue {

  private specialStype: boolean = false

  @Watch('$route')
  private onRouteChange(route: Route) {
    this.changeStyle(route)
  }

  created() {
    this.changeStyle(this.$route)
  }

  private changeStyle(route: Route) {
    if (route.path.startsWith('/testing/view')) {
      this.specialStype = true
    } else {
      this.specialStype = false
    }
  }
}
</script>

<style lang="scss" scoped>
.app-main {
  overflow: hidden;
  padding: 20px;
  padding-top:0;
}

.app-main-special {
  overflow: hidden;
  padding: 0px;
}
</style>
