<template>
  <el-dialog 
    v-el-drag-dialog
    width="80%"
    center
    :visible.sync="show_dialog" 
    :show-update="show_dialog"
    :modal="true"
    :append-to-body="true"
    :close-on-click-modal="false"
    :lock-scroll="true"
    @close="closeDialog"
  >
    <div slot="title" class="header-title">
      <div>{{ view_context.title }}</div>
    </div>
    <component 
      ref="componentView"
      :is="compoment_type"
      :view-context="viewContext"
      @close="closeDialog"
    ></component>
  </el-dialog>
</template>
    
<script>
import MoldCreate from "@/views/moldManage/MoldForm.vue"
import MachineCreate from "@/views/machineManage/InjectionMachineForm.vue"
import PolymerCreate from "@/views/polymerManage/PolymerForm.vue"
// import ReservationCreate from "@/views/scheduleManage/ReservationForm.vue"
import FillerCreate from "@/views/fillerManage/FillerCreate.vue"
import UserCreate from "@/views/superManage/UserCreate.vue"
export default {
  name: "DragDialog",
  components: { 
    MoldCreate,
    PolymerCreate,
    MachineCreate,
    // ReservationCreate,
    FillerCreate,
    UserCreate,
  },
  props: {
    componentType:  {
      type: String,
      default: null
    },
    viewContext: {
      type: Object,
      default: () => {}
    },
    showUpdate: {
      type: Boolean,
      default: false,
    }
  },
  data() {
    return {
      compoment_type: this.componentType,
      view_context: this.viewContext,
      show_dialog: this.showUpdate,
    }
  },
  watch: {
    componentType() {
      this.compoment_type = this.compomentType
    },
    viewContext: {
      handler: function() {
        this.view_context = this.viewContext
      },
      deep: true
    },
    showUpdate() {
      this.show_dialog = this.showUpdate
    },
  },
  methods: {
    closeDialog() {
      this.$refs["componentView"].resetView()
      this.$emit("close")
    }
  }
}
</script>

<style lang="scss" scoped>

</style>