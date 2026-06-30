<template>
  <div>
    <el-card class="box-card">
      <div slot="header" class="clearfix">
        <span>项目信息</span>
      </div>
      <el-form
        ref="formData"
        :model="project_info"
        :rules="rules"
        :inline="true"
        label-width="10rem"
        size="small"
      >
        <template v-for="item, index in form_items">
          <el-divider 
            v-if="item.type === 'divider'" 
            content-position="center"
            :key="`divider_${index}`"
          >
            <span>{{ item.label }}</span>
          </el-divider>
          <el-form-item 
            v-else-if="item.prop=='remarks'"
            class="full-width"
            :label="item.label"
            :prop="item.prop"
            :key="`sub_item_${index}`"
          >
            <el-input
              v-model="project_info.remarks"
              type="textarea"
              :rows="3"
              placeholder="请输入备注"
            />
          </el-form-item>
          <el-form-item
            v-else
            :label="item.label"
            :prop="item.prop"
            :key="`pro_item_${index}`"
          >
            <el-input
              v-if="item.type === 'input' "
              v-model.trim="project_info[item.prop]"
              :placeholder="item.placeholder || `请输入${item.label}`"
            />
            <el-input
              v-else-if="item.type === 'number'"
              v-model="project_info[item.prop]"
              v-number="item.fixed"
              placeholder="请输入"
            >
              <span slot="suffix" v-if="item.unit">{{ item.unit }}</span>
            </el-input>
            <el-select
              v-else-if="item.type === 'select'"
              v-model="project_info[item.prop]"
              filterable
              :placeholder="item.placeholder || `请选择${item.label}`"
            >
              <el-option
                v-for="opt in item.options"
                :key="opt.value"
                :label="opt.label"
                :value="opt.value"
              />
            </el-select>
            <el-date-picker
              v-if="item.type === 'date'"
              v-model="project_info[item.prop]"
              type="date"
              value-format="yyyy-MM-dd"
              placeholder="选择日期"
            />
          </el-form-item>
        </template>
      </el-form>
    </el-card>
    <div class="floating-actions-right">
      <el-button 
        type="danger"
        size="small"
        @click="resetView"
      >
        重  置
      </el-button>
      <el-button 
        type="primary" 
        size="small"
        :loading="save_loading"
        @click="saveProjectInfo"
        :disabled="!$hasPermission('update_project')"
      >
        {{ project_info.id ? "更  新" : "保  存" }}
      </el-button>
    </div>
  </div>
</template>

<script>
import { projectMethod } from "@/api"
import {
  projectInfoForm,
  projectStatusOptions,
  reviewStatusOptions,
  premiumOptions,
  importanceLevelOptions,
  applicationIndustryOptions,
  manufacturingMethodOptions,
} from "@/constants/project-const"
import { createValidateAndFocus } from "@/utils/form-helper"

export default {
  name: "ProjectForm",
  props: {
    viewContext: {
      type: Object,
      default: () => ({
        id: null,
        is_dialog: false,
        title: null,
        mode: null,
        excel_data: null
      })
    }
  },
  data() {
    return {
      view_context: this.viewContext,
      project_info: structuredClone(projectInfoForm),
      form_items: [
        { label: "项目编号", prop: "project_code", type: "input" },
        { label: "项目名称", prop: "project_name", type: "input" },
        { label: "项目状态", prop: "status", type: "select", options: projectStatusOptions },
        { label: "评审结果", prop: "review_status", type: "select", options: reviewStatusOptions },
        { label: "是否高端项目", prop: "is_premium", type: "select", options: premiumOptions },
        { label: "重要程度", prop: "importance_level", type: "select", options: importanceLevelOptions },
        { label: "客户名称", prop: "initiator", type: "input", placeholder: "客户名称等" },
        { label: "量产地", prop: "manufacturing_location", type: "input" },
        { label: "应用行业", prop: "application_industry", type: "select", options: applicationIndustryOptions },
        { label: "制作方式", prop: "manufacturing_method", type: "select", options: manufacturingMethodOptions },
        { label: "备注", prop: "remarks", type: "input" },
        { label: "计划节点", type: "divider" },
        { label: "合同日期", prop: "contract_date", type: "date" },
        { label: "合同T1日期", prop: "contract_t1_date", type: "date" },
        { label: "合同出厂日期", prop: "contract_factory_delivery_date", type: "date" },
        { label: "标准试模次数", prop: "standard_trial_count", type: "number", fixed: 0, unit: "次" },
        { label: "目标新制周期", prop: "target_new_cycle_days", type: "number", fixed: 0, unit: "天" },
        { label: "目标整改周期", prop: "target_rework_cycle_days", type: "number", fixed: 0, unit: "天" },
        { label: "开工日期", prop: "work_start_date", type: "date" },
        { label: "项目启动日期", prop: "project_kickoff_date", type: "date" },
        { label: "试模计划开始时间", prop: "trial_plan_start_date", type: "date" },
        { label: "试模计划结束时间", prop: "trial_plan_end_date", type: "date" },
        { label: "财务结算日期", prop: "financial_settlement_date", type: "date" },
        { label: "成员信息", type: "divider" },
        { label: "项目经理", prop: "project_manager", type: "input" },
        { label: "销售经理", prop: "sales_manager", type: "input" },
        { label: "项目工程师", prop: "project_engineer", type: "input" },
        //{ label: "技术经理", prop: "technical_manager", type: "input" },
        { label: "设计主管", prop: "design_leader", type: "input" },
        { label: "试模工程师", prop: "process_engineer", type: "input" },
        { label: "钳工班组", prop: "fitter", type: "input" },
      ],
      rules: {
        initiator: [{ required: true, message: "客户名称不能为空", trigger: "blur" }],
        application_industry: [{ required: true, message: "请选择应用行业", trigger: "change" }]
      },
      save_loading: false,
    }
  },
  watch: {
    viewContext: {
      handler: function() {
        this.view_context = this.viewContext
        this.initializeView()
      },
      deep: true,
      immediate: true
    },
  },
  methods: {
    async initializeView() {
      this.resetView()
      if (this.view_context.id) {
        // 通过弹出窗口进入界面
        this.project_info.id = this.view_context.id
      }

      if (this.project_info.id) {
        await this.getProjectInfo(this.project_info.id)
      }
    },
    async getProjectInfo(id) {
      if (!id) return
      // 读取模具参数
      const res = await projectMethod.getDetail(id)
      if (res.status === 0) {
        Object.assign(this.project_info, res.data)
      } else {
        this.$message({
          showClose: true,
          message: "未读取到相关项目信息！",
          type: "warning"
        }) 
      }
    },
    async saveProjectInfo() {
      const validate = createValidateAndFocus(this)
      let access = true

      // 校验机器参数
      access = await validate(this.$refs.formData)
      if (!access) return

      // 根据是否有模具 id 分别执行新增/更新服务
      if (this.project_info.id) {
        // 更新模具信息
        const res = await projectMethod.edit(this.project_info, this.project_info.id)
        if (res.status === 0) {
          this.$message({ message: "项目信息编辑成功！", type: "success" })
        }
      } else {
        // 新增模具信息
        const res = await projectMethod.add(this.project_info)
        if (res.status === 0) {
          this.$message({ message: "项目信息新增成功！", type: "success" })
        }
      }

      this.$emit("close")
      this.$router.push("/mold/project/list")
    },
    resetView() {
      this.project_info = structuredClone(projectInfoForm)
    },
  }
}
</script>

<style lang="scss" scoped>

</style>