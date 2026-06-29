<template>
  <el-dialog 
    v-el-drag-dialog
    width="75%"
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
    <mold-create
      ref="moldCreate"
      :id="id"
      :dialog="true"
      :view-type="viewType"
      :excel-data="excelData"
      @close="closeDialog"
    >
    </mold-create>
  </el-dialog>
</template>

<script>
import MoldCreate from '@/views/moldMag/create.vue'

export default {
  name: "MoldDetail",
  components: { MoldCreate },
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
    excelData: {
      type: Object,
      default: () => ({ 

      })
    }
  },
  data() {
    return {
      title: "新增模具",
      showDialog: this.showUpdate,
    }
  },
  methods: {
    closeDialog() {
      this.$refs["moldCreate"].resetView()
      this.$emit('close')
    }
  },
  watch: {
    showUpdate() {
      this.showDialog = this.showUpdate
    },
    viewType() {
      if (this.viewType == "add") {
        this.title = "新增模具"
      } else if (this.viewType == "edit") {
        this.title = "编辑模具"
      } else if (this.viewType == "copy") {
        this.title = "复制模具"
      } else if (this.viewType == "upload") {
        this.title = "导入模具"
      }
    }
  }
}
</script>

<style lang="scss" scoped>

</style>