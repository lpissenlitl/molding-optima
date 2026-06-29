<template>
  <div>
    <el-divider content-position="center">
      <span>设定工艺参数</span>
    </el-divider>
    <setting-process 
      :setting-process="process_parameter.setting_process"
      :machine-info="machine_info"
    />
  </div>
</template>

<script>
import { processParameterForm } from "@/constants/process-const"
import { machineInfoForm } from "@/constants/machine-const"
import SettingProcess from "./SettingProcess.vue"


export default {
  name: "ProcessParameter",
  components: { SettingProcess },
  props: {
    processParameter: {
      type: Object,
      default: () => { return structuredClone(processParameterForm) }
    },
    machineInfo: {
      type: Object,
      default: () => { return structuredClone(machineInfoForm) }
    },
  },
  data() {
    return {
      process_parameter: this.processParameter,
      machine_info: this.machineInfo,
    }
  },
  computed: {
  },
  watch: {
    processParameter: {
      handler: function() {
        this.process_parameter = this.processParameter
      },
      deep: true,
      immediate: true
    },
    machineInfo: {
      handler: function() {
        this.machine_info = this.machineInfo
      },
      deep: true,
      immediate: true
    }
  },
}
</script>

<style lang="scss" scoped>

</style>