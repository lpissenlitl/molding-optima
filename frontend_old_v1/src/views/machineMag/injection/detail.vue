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
    <machine-create 
      ref="machineCreate"
      :id="id"
      :dialog="true"
      :view-type="viewType"
      :excel-data="excelData"
      @close="closeDialog"
    >
    </machine-create>
  </el-dialog>
</template>

<script>
import MachineCreate from "./CreateInjectionMachine.vue";

export default {
  components: { MachineCreate },
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
    excelData: {
      type: Object,
      default: () => ({ 

      })
    }
  },
  data() {
    return {
      title: "新增机器",
      showDialog: this.showUpdate,
    }
  },
  methods: {
    closeDialog() {
      this.$refs["machineCreate"].resetView()
      this.$emit('close')
    }
  },
  watch: {
    showUpdate() {
      this.showDialog = this.showUpdate
    },
    viewType() {
      if (this.viewType == "add") {
        this.title = "新增机器"
      } else if (this.viewType == "edit") {
        this.title = "编辑机器"
      } else if (this.viewType == "copy") {
        this.title = "复制机器"
      } else if (this.viewType == "upload") {
        this.title = "导入机器"
      }
    }
  }
}
</script>

<style lang="scss" scoped>

</style>
