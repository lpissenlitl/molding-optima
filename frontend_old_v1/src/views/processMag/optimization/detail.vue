<template>
  <el-dialog 
    v-el-drag-dialog
    width="80%"
    center
    :visible.sync="showDialog" 
    :show-update="showUpdate"
    :modal="true"
    :append-to-body="true"
    :close-on-click-modal="false"
    :lock-scroll="true"
    @close="closeDialog"
  >
    <div slot="title" class="header-title">
      <div style="font-size:25px; font-weight:bold">{{ title }}</div>
    </div>
    <optimize-view
      ref="optimizeView"
      :id="id"
      :dialog="true"
      :view-type="viewType"
      @close="closeDialog"
    >
    </optimize-view>
  </el-dialog>
</template>

<script>
import OptimizeView from './create.vue';

export default {
  name: "ProcessOptimizeDetail",
  components: { OptimizeView },
  props: {
    showUpdate: {
      type: Boolean,
      default: false,
    },
    id: {
      type: Number,
      default: null,
    },
    viewType: {
      type: String,
      default: null,
    },
  },
  data() {
    return {
      title: "新增优化记录",
      showDialog: this.showUpdate,
    }
  },
  methods: {
    closeDialog() {
      this.$refs["optimizeView"].resetView()
      this.$emit('close')
    }
  },
  watch: {
    showUpdate() {
      this.showDialog = this.showUpdate
    },
    viewType() {
      if (this.viewType == "add") {
        this.title = "新增记录"
      } else if (this.viewType == "edit") {
        this.title = "查看记录"
      } else if (this.viewType == "copy") {
        this.title = "复制记录"
      } else if (this.viewType == "upload") {
        this.title = "新增记录"
      }
    }
  }
}
</script>

<style lang="scss" scoped>

</style>
