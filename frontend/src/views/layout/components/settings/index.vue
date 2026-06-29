<template>
  <div class="drawer-container">
    <div>
      <h3 class="drawer-title" style="font-size: var(--basic-font-size);">
        系统样式配置
      </h3>
      <div class="drawer-item">
        <span style="font-size: var(--basic-font-size);">主题色</span>
        <div style="height: 20px"></div>
        <el-radio v-model="theme_color" label="深" @input="themeChange">
          深色调
        </el-radio>
        <el-radio v-model="theme_color" label="浅" @input="themeChange">
          浅色调
        </el-radio>
      </div>

      <div class="drawer-item">
        <span style="font-size: var(--basic-font-size);">字体大小</span><br />
        <div style="height: 20px"></div>
        <el-radio v-model="theme_font_size" label="小" @input="themeChange">
          小
        </el-radio>
        <el-radio v-model="theme_font_size" label="中" @input="themeChange">
          中
        </el-radio>
        <el-radio v-model="theme_font_size" label="大" @input="themeChange">
          大
        </el-radio>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "Settings",
  data() {
    return {
      theme_font_size: "中",
      theme_color: "深",
    }
  },
  watch: {
    theme_font_size: {
      handler(val) {
        localStorage.setItem("theme_font_size", val)
      },
    },
    theme_color: {
      handler(val) {
        localStorage.setItem("theme_color", val)
      },
    }
  },
  mounted() {
    const theme_fsize = localStorage.getItem("theme_font_size")
    const theme_col = localStorage.getItem("theme_color")
    if (theme_col) {
      this.theme_color = theme_col
      this.themeChange(this.theme_color)
    }
    if (theme_fsize) {
      this.theme_font_size = theme_fsize
      this.themeChange(this.theme_font_size)
    }
  },
  methods: {
    themeChange(val) {
      if (val === "小") {
        document.documentElement.style.setProperty("--basic-font-size", "14px")
        document.documentElement.style.setProperty("--first-level-font-size", "17px")
        document.documentElement.style.setProperty("--second-level-font-size", "16px")
        document.documentElement.style.setProperty("--three-level-font-size", "15px")
        document.documentElement.style.setProperty("--submenu-title-font-size", "16px")
        document.documentElement.style.setProperty("--menu-font-size", "15px")
        document.documentElement.style.setProperty("--sidebar-title-font-size","24px")

        document.documentElement.style.setProperty("--breadcrumb-font-size", "18px")

        document.documentElement.style.setProperty("--dialog-header-title", "23px")
      } else if (val === "中") {
        document.documentElement.style.setProperty("--basic-font-size", "16px")
        document.documentElement.style.setProperty("--first-level-font-size", "19px")
        document.documentElement.style.setProperty("--second-level-font-size", "18px")
        document.documentElement.style.setProperty("--three-level-font-size", "17px")
        document.documentElement.style.setProperty("--submenu-title-font-size", "21px")
        document.documentElement.style.setProperty("--menu-font-size", "19px")
        document.documentElement.style.setProperty("--sidebar-title-font-size", "27px")

        document.documentElement.style.setProperty("--breadcrumb-font-size", "20px")

        document.documentElement.style.setProperty("--dialog-header-title", "25px")
      } else if (val === "大") {
        document.documentElement.style.setProperty("--basic-font-size", "18px")
        document.documentElement.style.setProperty("--first-level-font-size", "21px")
        document.documentElement.style.setProperty("--second-level-font-size", "20px")
        document.documentElement.style.setProperty("--three-level-font-size", "19px")
        document.documentElement.style.setProperty("--submenu-title-font-size", "23px")
        document.documentElement.style.setProperty("--menu-font-size", "21px")
        document.documentElement.style.setProperty("--sidebar-title-font-size", "30px")

        document.documentElement.style.setProperty("--breadcrumb-font-size", "22px")

        document.documentElement.style.setProperty("--dialog-header-title", "27px")
      } else if (val === "深") {
        document.documentElement.style.setProperty("--menu-bgcolor", "#304156")
        document.documentElement.style.setProperty("--menu-text-color", "#bfcbd9")
        document.documentElement.style.setProperty("--menu-active-text-color", "#409EFF")
        document.documentElement.style.setProperty("--submenu-hover", "#001528")
        document.documentElement.style.setProperty("--submenu-bg", "#1f2d3d")
        document.documentElement.style.setProperty("--submenu-active-text", "#f4f4f5")

        document.documentElement.style.setProperty("--sidebar-logo-bg", "#2b2f3a")
        document.documentElement.style.setProperty("--sidebar-title-color", "#fff")
      } else if (val === "浅") {
        document.documentElement.style.setProperty("--menu-bgcolor", "#ffffff")
        document.documentElement.style.setProperty("--menu-text-color", "rgb(48, 65, 86)")
        document.documentElement.style.setProperty("--menu-active-text-color", "rgb(150, 210, 255)")
        document.documentElement.style.setProperty("--submenu-hover", "rgb(212, 229, 250)")
        document.documentElement.style.setProperty("--submenu-bg", "rgb(237, 245, 255)")
        document.documentElement.style.setProperty("--submenu-active-text", "rgb(25, 36, 49)")

        document.documentElement.style.setProperty("--sidebar-logo-bg", "#fff")
        document.documentElement.style.setProperty("--sidebar-title-color", "rgb(48, 65, 86)")
      }
    },
  }
}
</script>

<style lang="scss" scoped>
.drawer-container {
  padding: 24px;
  font-size: 14px;
  line-height: 1.5;
  word-wrap: break-word;

  .drawer-title {
    margin-bottom: 12px;
    color: rgba(0, 0, 0, 0.85);
    font-size: 14px;
    line-height: 22px;
  }

  .drawer-item {
    color: rgba(0, 0, 0, 0.65);
    font-size: 14px;
    padding: 12px 0;
  }
}
</style>