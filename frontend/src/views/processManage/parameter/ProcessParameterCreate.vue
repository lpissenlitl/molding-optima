<template>
  <div class="process-create-wrapper">
    <el-card class="condition-card">
      <div slot="header" class="card-header">
        <span>工艺条件</span>
      </div>
      <process-condition 
        ref="processCondition"
        :process-condition="form_info.condition"
      />
    </el-card>

    <el-card class="settings-card">
      <div slot="header" class="card-header">
        <span>工艺参数</span>
      </div>
      <process-settings
        v-if="setting_process"
        ref="processSettings"
        :setting-process="setting_process"
        :machine-info="form_info.condition.machine_info"
        :original-process="original_process"
      />
    </el-card>

    <div class="floating-actions fixed right">
      <el-button
        v-if="form_info.process_id" 
        type="success" 
        size="small"
        :loading="export_loading" 
        @click="exportProcessToExcel" 
      >
        导  出
      </el-button>
      <el-button
        v-if="view_context.is_dialog"
        type="danger"
        size="small"
        @click="$emit('close')"
      >
        返 回
      </el-button>
      <el-button 
        v-else 
        type="danger" 
        size="small" 
        @click="resetView"
      >
        重 置
      </el-button>
      <el-button
        v-if="form_info.process_id"
        type="primary"
        size="small"
        :loading="update_loading"
        @click="saveProcessParameter"
      >
        更 新
      </el-button>
      <el-button
        v-else
        type="primary"
        size="small"
        :loading="save_loading"
        @click="saveProcessParameter"
      >
        保 存
      </el-button>
    </div>
  </div>
</template>

<script>
import { processParameterMethod } from "@/api"
import { injectionProcessForm, settingProcessForm } from "@/constants/process-const"
import ProcessCondition from "@/components/process/ProcessCondition.vue"
import ProcessSettings from "@/components/process/ProcessSettings.vue"
import { getProcessParameterFrontend, saveProcessParameterFrontend, updateProcessParameterFrontend } from "@/api"

export default {
  name: "ProcessParameterCreate",
  components: { 
    ProcessCondition,
    ProcessSettings
  },
  props: {
    viewContext: {
      type: Object,
      default: () => ({
        id: null,
        is_dialog: false,
        mode: null,
        excel_data: null
      })
    }
  },
  data() {
    return {
      form_info: structuredClone(injectionProcessForm),
      view_context: this.viewContext,
      export_loading: false,
      update_loading: false,
      save_loading: false,
      original_process: null,
    }
  },
  computed: { 
    condition() { 
      return this.form_info.condition
    },
    parameter() { 
      return this.form_info.parameter
    },
    setting_process() {
      return this.form_info.parameter.setting_process
    },
  },
  watch: {
    $data: {
      handler: function () {
        sessionStorage.setItem("injection_process", JSON.stringify(this.$data))
      },
      deep: true,
    },
    viewContext: {
      handler: function () {
        this.view_context = this.viewContext
        this.initializeView()
      },
      deep: true,
    },
  },
  mounted() {
    this.initializeView()
  },
  methods: {
    async initializeView() {
      this.resetView()
      this.condition.id = null
      if (this.view_context.id) {
        this.condition.id = this.view_context.id
      } else if (this.$route.query.id) {
        this.condition.id = this.$route.query.id
      }

      if (this.condition.id) {
        await this.getProcessParameter(this.condition.id)
      } else {
        // 初始化原始数据快照
        this.original_process = structuredClone(settingProcessForm)
      }
    },
    
    async getProcessParameter(id) { 
      if (!id) return
      // 使用前端适配接口，直接返回嵌套结构，无需转换
      const res = await getProcessParameterFrontend(id)
      if (res.status === 0) {
        // 填充条件信息
        const { condition, parameter } = res.data
        Object.assign(this.condition, condition)

        if (parameter?.setting_process) {
          this.form_info.parameter.id = parameter.id
          // 后端已返回前端结构，直接使用
          this.form_info.parameter.setting_process = parameter.setting_process
          // 保存原始数据快照用于变更检测
          this.original_process = JSON.parse(JSON.stringify(this.form_info.parameter.setting_process))
        } else {
          this.$message.error("未读取到工艺参数")
          this.original_process = structuredClone(settingProcessForm)
        }
      }
    },
    
    async saveProcessParameter() {
      // 校验条件表单
      const valid = await this.$refs.processCondition.checkFormDataValid()
      if (!valid) return

      // 构建后端请求数据
      const condition = {
        status: "draft",
        origin_type: "manual_creation",
        mold_id: this.condition.mold_info.id,
        shot_index: this.condition.shot_index,
        injection_machine_id: this.condition.machine_info.id,
        injection_index: this.condition.injection_index,
        polymer_id: this.condition.polymer_info.id,
      }

      const injection_process = {
        condition,
        parameter: {
          setting_process: this.setting_process
        }
      }

      if (this.condition.id) {
        // 更新 - 使用前端嵌套结构格式
        this.update_loading = true
        try {
          const res = await updateProcessParameterFrontend(
            this.condition.id,
            injection_process
          )
          if (res.status === 0) {
            this.$message.success("工艺参数修改成功")
            // 更新原始快照
            this.original_process = JSON.parse(JSON.stringify(this.setting_process))
            // 调用 ProcessSettings 的 resetSnapshot 方法
            if (this.$refs.processSettings?.resetSnapshot) {
              this.$refs.processSettings.resetSnapshot()
            }
            if (!this.view_context.is_dialog) {
              this.$router.push("/process/parameter/list")
            }
          }
        } finally {
          this.update_loading = false
        }
      } else {
        // 新增 - 使用前端嵌套结构格式
        this.save_loading = true
        try {
          const res = await saveProcessParameterFrontend(injection_process)
          if (res.status === 0) {
            this.$message.success("工艺参数添加成功")
            this.condition.id = res.data.id
            this.form_info.parameter.id = res.data.process_parameters?.[0]?.id
            // 更新原始快照
            this.original_process = JSON.parse(JSON.stringify(this.setting_process))
            if (!this.view_context.is_dialog) {
              this.$router.push("/process/parameter/list")
            }
          }
        } finally {
          this.save_loading = false
        }
      }
    },
    
    exportProcessToExcel() {
      // 导出功能待实现
      this.$message.info("导出功能开发中...")
    },
    
    resetView() {
      this.form_info = structuredClone(injectionProcessForm)
      this.original_process = structuredClone(settingProcessForm)
    },
  },
}
</script>

<style lang="scss" scoped>
.process-create-wrapper {
  background-color: #f5f7fa;
  min-height: 100%;
  padding: 16px;
}

.condition-card {
  margin-bottom: 16px;
  
  ::v-deep .el-card__header {
    padding: 12px 16px;
    background-color: #f5f7fa;
  }
}

.settings-card {
  ::v-deep .el-card__header {
    padding: 12px 16px;
    background-color: #f5f7fa;
  }
}

.card-header {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}
</style>
