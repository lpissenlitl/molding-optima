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
    <auxiliary-create 
      ref="auxiliaryCreate"
      :id="id"
      :dialog="true"
      :view-type="viewType"
      @close="closeDialog"
    >
    </auxiliary-create>
  </el-dialog>
</template>

<script>
import AuxiliaryCreate from "./create.vue";

export default {
  components: { AuxiliaryCreate },
  props: {
    showUpdate: {
      type: Boolean,
      default: false
    },
    id: {
      type: Number,
      default: null
    },
    viewType: {
      type: String,
      default: null,
    },
  },
  data() {
    return {
      title: "新增辅机",
      showDialog: this.showUpdate,
    }
  },
  methods: {
    closeDialog() {
      this.$refs["auxiliaryCreate"].resetView()
      this.$emit('close')
    }
  },
  watch: {
    showUpdate() {
      this.showDialog = this.showUpdate
    },
    viewType() {
      if (this.viewType == "add") {
        this.title = "新增辅机"
      } else if (this.viewType == "edit") {
        this.title = "编辑辅机"
      } else if (this.viewType == "copy") {
        this.title = "复制辅机"
      } else if (this.viewType == "upload") {
        this.title = "新增辅机"
      }
    }
  }
}
</script>

<style lang="scss" scoped>
  .el-dialog_body {
    height: 60vh;
    overflow: auto;
  }

</style>
