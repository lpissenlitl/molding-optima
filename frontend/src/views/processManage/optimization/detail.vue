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
    <optimize-view
      ref="optimizeView"
      :view-context="viewContext"
      @close="closeDialog"
    >
    </optimize-view>
  </el-dialog>
</template>

<script>
import OptimizeView from './create.vue'

export default {
  name: "ProcessOptimizeDetail",
  components: { OptimizeView },
  props: {
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
      view_context: this.viewContext,
      show_dialog: this.showUpdate,
    }
  },
  methods: {
    closeDialog() {
      this.$refs["optimizeView"].resetView()
      this.$emit('close')
    }
  },
  watch: {
    viewContext: {
      handler: function() {
        this.view_context = this.viewContext;
      },
      deep: true
    },
    showUpdate() {
      this.show_dialog = this.showUpdate;
    },
  }
}
</script>

<style lang="scss" scoped>

</style>
