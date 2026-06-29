<template>
  <div class="createFiller">
    <el-form 
      ref="filler_info" 
      size="mini" 
      label-width="10rem" 
      label-position="right" 
      :model="filler_info" 
      :inline="true"
      :rules="rules"
    >
      <el-card class="box-card" style="margin-top: 4px;">
        <div slot="header" class="clearfix">
          <span>填充物信息</span>
        </div>
        <div
          v-for="(group, groupIndex) in formGroups"
          :key="group.title"
          class="box-card"
          style="margin-top: 4px;"
        >
          <el-divider content-position="center">
            <span style="color:blue">{{ group.title }}</span>
          </el-divider>
          <el-form-item
            v-for="field in group.fields"
            :key="field.key"
            :label="field.label"
            :prop="field.key"
            :required="field.required" 
          >
            <el-select
              v-if="field.type=='select'"
              v-model="filler_info[field.prop]"
              placeholder="请选择"
              clearable
              allow-create
              filterable
              @clear="filler_info[field.prop]=null"
            >
              <el-option 
                v-for="option in field.options"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
            <template v-if="!field.type || field.type === 'text' || field.type === 'number'">
              <el-input
                v-model="filler_info[field.key]"
                :type="field.type === 'number' ? 'number' : 'text'"
                @input="handleInput(field)"
              >
                <span slot="suffix">
                  {{ field.unit }}
                </span>
              </el-input>
            </template>   
          </el-form-item>
        </div>
      </el-card>
    </el-form>
    <div style="height:25px" />
    <div class="floating-actions fixed right">
      <el-button 
        v-if="view_context.is_dialog"
        type="danger"
        size="small"
        @click="$emit('close')" 
      >
        返  回
      </el-button>
      <el-button 
        v-else
        type="danger"
        size="small"
        @click="resetView" 
      >
        重  置
      </el-button>
      <el-button 
        v-if="filler_info.id"
        type="primary" 
        size="small"
        :loading="update_loading"
        @click="updateFillerDetail" 
      >
        更  新
      </el-button>
      <el-button 
        v-else
        type="primary" 
        size="small"
        :loading="save_loading" 
        @click="saveFillerDetail"
      >
        保  存
      </el-button>
    </div>
  </div>
</template>

<script>
import { fillerMethod } from "@/api"
import { initialFillerInfo, fillerTypeOptions, colorOptions, shapeOptions, fillerCategoryOptions } from "@/constants/polymer-const"

export default {
  name: "FillerCreate",
  props: {
    viewContext: {
      type: Object,
      default: () => ({
        id: null,
        is_dialog: false,
        mode: null,
        excel_data: null
      })
    },
    id: {
      type: Number,
      default: null
    },
  },
  data() {
    return {
      filler_info: structuredClone(initialFillerInfo),
      view_context: this.viewContext,
      formGroups: [
        {
          title: "填充物属性",
          fields: [
            { prop:"name", key: "name", label: "名称", type: "text", required: false, placeholder: "如：玻璃纤维、碳酸钙" },
            { prop:"abbreviation", key: "abbreviation", label: "缩写", type: "select",required: false,placeholder: "如：GF, TALC, CaCO₃",
              options: fillerTypeOptions },    
            { prop:"category", key: "category", label: "类别", type: "select",required: false,placeholder: "如：无机填充、增强纤维", options: fillerCategoryOptions },
            { prop:"shape", key: "shape",label: "形状",type: "select",required: false,placeholder: "如：球形、针状、片状", options: shapeOptions },
          ]
        },

        {
          title: "关键工艺相关参数",
          fields: [
            { prop:"particle_size_d50", key: "particle_size_d50",label: "中位粒径(ρ)",type: "number",unit: "μm" },
            { prop:"aspect_ratio", key: "aspect_ratio",label: "长径比",type: "number",unit: "" },
            { prop:"moisture_content", key: "moisture_content",label: "含水率",type: "number",unit: "%" },
            { prop:"surface_treatment", key: "surface_treatment",label: "表面处理",type: "text",unit: "" },
          ]
        },

        {
          title: "关键物理性能",
          fields: [
            { prop:"density", key: "density",label: "密度", type: "number", unit: "g/cm³", required: false },
            { prop:"thermal_stability_temp", key: "thermal_stability_temp",label: "热稳定温度", type: "number", unit: "℃", required: false },
            { prop:"color", key: "color",label: "颜色", type: "select", unit: "", required: false, options: colorOptions }
          ]
        }
      ],
      update_loading: false,
      save_loading: false,
    }
  },
  computed: {
    rules() {
      const rules = {}
      this.formGroups.forEach(group => {
        group.fields.forEach(field => {
          const key = field.key

          // 如果是必填字段，生成校验规则
          if (field.required) {
            rules[key] = [
              {
                required: true,
                message: `${field.label}不能为空`,
                trigger: "blur"
              }
            ]
          }
        })
      })
      return rules
    }
  },
  watch: {
    viewContext: {
      handler: function() {
        this.view_context = this.viewContext
        this.initializeView()
      },
      deep: true
    }
  },
  mounted() {
    this.initializeView()
  },
  methods: {
    initializeView() {
      // 分多种情况进入当前界面，默认情况下不带材料id
      this.filler_info.id = null
      if (this.view_context.id) {
        // 通过弹出窗口进入界面
        this.filler_info.id = this.view_context.id
      } else if (this.$route.query.id) {
        // 通过跳转进入界面
        this.filler_info.id = Number(this.$route.query.id)
      }

      if (this.filler_info.id) {
        // 如果id存在，读取参数
        this.getFillerDetail(this.filler_info.id)
      } else {
        // 从文件导入
        if (this.view_context.mode == "import") {
          this.filler_info = this.view_context.excel_data
        }
      }
    },
    handleInput(field) {
      const value = this.filler_info[field.key]
      if (field.type === "number") {
        this.filler_info[field.key] = this.$formatNumber(value, field.decimal)
      }
    },
    getFillerDetail(filler_id) {
      if (!filler_id) {
        return
      }  
      fillerMethod.getDetail(filler_id)
        .then((res) => {
          if (res.status === 0) {
            this.filler_info = structuredClone(res.data)
            if (this.view_context.mode == "copy") {
              this.filler_info.id = null
              this.filler_info.grade = ""
            }
          }
        }) 
    },
    saveFillerDetail() {
      this.$refs["filler_info"].validate((valid) => {
        if (valid) {
          this.saveFiller()
        }
      })
    },
    saveFiller() {
      fillerMethod.add(this.filler_info)
        .then((res) => {
          if (res.status === 0) {
            this.$message({ message: "填充物信息新增成功！", type: "success" })
            this.$emit("close")
            this.$router.push("/polymer/filler/list")
          }
        })
    },
    updateFillerDetail() {
      this.$refs["filler_info"].validate((valid) => {
        if (valid) {
          fillerMethod.edit(this.filler_info, this.filler_info.id)
            .then((res) => {
              if (res.status === 0) {
                this.$message({ message: "填充物信息编辑成功！", type: "success" })
                this.$emit("close")
              }
            })
        }
      })
    },
    resetView() {
      this.filler_info = structuredClone(initialFillerInfo)
    },
    addFiller() {
      if (!this.filler_info.fillers) {
        this.$set(this.filler_info, "fillers", [])
      }
      this.filler_info.fillers.push({ ...initialFillerInfo })
    },
    removeFiller(index) {
      this.filler_info.fillers.splice(index, 1)

      if (this.filler_info.fillers.length === 0) {
        this.$delete(this.filler_info, "fillers")
      }
    },
  }
}
</script>

<style lang="scss" scoped>
  .button {
    position: fixed;
    // left: auto;
    right: 20px;
    bottom: 8px;
    // _position:absolute;
    z-index: 1000;
    font-size: 11px;
    line-height: 32px;
    height: 34px;
    // padding: 0px 15px 0px 15px;
    // width:666px;
    margin: 0px;
    .el-button {
      width: 8rem;
    }
  }
  .el-autocomplete {
    width: 10rem;
  }
  .el-input {
    width: 10rem;
  }
  .el-select {
    width: 10rem;
  }
</style>
