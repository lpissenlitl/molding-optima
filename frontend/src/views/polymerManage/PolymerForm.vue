<template>
  <div>
    <el-form 
      ref="polymerForm" 
      size="mini" 
      label-width="10rem" 
      label-position="right" 
      :model="polymer_info" 
      :rules="rules"
      :inline="true"
    >
      <el-card>
        <div slot="header" class="clearfix">
          基本信息
        </div>
        <el-form-item
          v-for="(item, index) in basic_form_items"
          :key="`basic_${index}`"
          :label="item.label"
          :prop="item.prop"
        >
          <el-input 
            v-if="item.type=='input'"
            v-model.trim="polymer_info[item.prop]"
            :placeholder="item.placeholder || `请输入${item.label}`"
          >
            <span slot="suffix" v-if="item.unit">{{ item.unit }}</span>
          </el-input>
          <el-select 
            v-else-if="item.type==='select'"
            v-model="polymer_info[item.prop]"
            filterable
            :clearable="item.clearable"
            :allow-create="item.allow_create"
          >
            <el-option 
              v-for="option, opt_idx in item.options"
              :key="opt_idx"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
          <el-autocomplete
            v-else-if="item.type==='autocomplete'"
            v-model="polymer_info[item.prop]"
            placeholder="请输入内容"
            clearable
            :debounce="0"
            :fetch-suggestions="$querySuggestions(item.query)"
          />
        </el-form-item>
      </el-card>
      <el-card>
        <div slot="header" class="clearfix">
          推荐工艺参数
        </div>

        <template v-for="(item, index) in process_form_items">
          <el-divider 
            v-if="item.type=='divider'" 
            :key="`divider_${index}`"
            content-position="center"
          >
            {{ item.label }}
          </el-divider>
          
          <el-form-item 
            v-else 
            :key="`process_item_${index}`"
            :label="item.label" 
            :prop="item.prop"
          >
            <el-input 
              v-if="item.type=='number'"
              v-model="polymer_info[item.prop]"
              v-number="item.fixed || 2"
              :placeholder="item.placeholder || `请输入${item.label}`"
            >
              <span slot="suffix" v-if="item.unit">{{ item.unit }}</span>
            </el-input>

            <el-select
              v-else-if="item.type === 'select'"
              v-model="polymer_info[item.prop]"
              filterable 
              :allow-create="item.allow_create"
              :clearable="item.clearable"
            >
              <el-option
                v-for="(option, opt_idx) in item.options"
                :key="opt_idx"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
          </el-form-item>
        </template>
      </el-card>

      <el-card>
        <div slot="header" class="clearfix">
          PVT属性
        </div>
        <el-form-item
          v-for="(item, index) in pvt_form_items"
          :key="`pvt_${index}`"
          :label="item.label"
          :prop="item.prop"
        > 
          <el-input 
            v-model="pvt[item.prop]"
            v-number="item.fixed || 2"
            :placeholder="item.placeholder || `请输入${item.label}`"
          >
            <span slot="suffix" v-if="item.unit">{{ item.unit }}</span>
          </el-input>
        </el-form-item>
      </el-card>

      <el-card>
        <div slot="header" class="clearfix">
          流变属性
        </div>
        <template v-for="(item, index) in rheology_form_items">
          <el-divider 
            v-if="item.type=='divider'" 
            :key="`divider_${index}`"
            content-position="center"
          >
            {{ item.label }}
          </el-divider>
          
          <el-form-item 
            v-else 
            :key="`rheology_${index}`"
            :label="item.label"
            :prop="item.prop"
          > 
            <el-input 
              v-if="item.type==='number'"
              v-model="pvt[item.prop]"
              v-number="item.fixed || 2"
              :placeholder="item.placeholder || `请输入${item.label}`"
            >
              <span slot="suffix" v-if="item.unit">{{ item.unit }}</span>
            </el-input>
            <el-select 
              v-else-if="item.type==='select'"
              v-model="polymer_info[item.prop]"
              filterable
              :clearable="item.clearable"
              :allow-create="item.allow_create"
            >
              <el-option 
                v-for="option, opt_idx in item.options"
                :key="opt_idx"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
          </el-form-item>
        </template>
      </el-card>

      <el-card>
        <div slot="header" class="clearfix">
          机械属性
        </div>
        <template v-for="(item, index) in mechanical_form_items">
          <el-divider 
            v-if="item.type=='divider'" 
            :key="`divider_${index}`"
            content-position="center"
          >
            {{ item.label }}
          </el-divider>
          
          <el-form-item 
            v-else 
            :key="`mechanical_${index}`"
            :label="item.label"
            :prop="item.prop"
          > 
            <el-input 
              v-model="pvt[item.prop]"
              v-number="item.fixed || 2"
              :placeholder="item.placeholder || `请输入${item.label}`"
            >
              <span slot="suffix" v-if="item.unit">{{ item.unit }}</span>
            </el-input>
          </el-form-item>
        </template>
      </el-card>

      <el-card>
        <div slot="header" class="clearfix">
          收缩属性
        </div>
        <template v-for="(item, index) in shrinkage_form_items">
          <el-divider 
            v-if="item.type=='divider'" 
            :key="`divider_${index}`"
            content-position="center"
          >
            {{ item.label }}
          </el-divider>
          
          <el-form-item 
            v-else 
            :key="`shrinkage_${index}`"
            :label="item.label"
            :prop="item.prop"
          > 
            <el-input 
              v-model="pvt[item.prop]"
              v-number="item.fixed || 2"
              :placeholder="item.placeholder || `请输入${item.label}`"
            >
              <span slot="suffix" v-if="item.unit">{{ item.unit }}</span>
            </el-input>
          </el-form-item>
        </template>
      </el-card>

      <!-- <el-card>
        <div slot="header" class="clearfix">
          附件
        </div>
        <upload-polymer-file
          :search-id="polymer_info.id"
          search-type="polymer"
          :file-list="polymer_file_info"
          @file-update="onFileUpdate"
        >
        </upload-polymer-file>
      </el-card> -->
    </el-form>

    <div class="floating-actions fixed right">
      <el-button
        v-if="polymer_info.id" 
        type="success" 
        size="small"
        :loading="export_loading" 
        @click="exportPolymerToExcel" 
      >
        导  出
      </el-button>
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
        v-if="polymer_info.id"
        type="primary" 
        size="small"
        :loading="save_loading"
        @click="savePolymerDetail" 
      >
        更  新
      </el-button>
      <el-button 
        v-else
        type="primary" 
        size="small"
        :loading="save_loading" 
        @click="savePolymerDetail"
      >
        保  存
      </el-button>
    </div>
  </div>
</template>

<script>
import * as polymer_const from "@/constants/polymer-const"
import { polymerMethod } from "@/api"
import { getFullFileUrl } from "@/utils/assert"
import { createValidateAndFocus } from "@/utils/form-helper"

export default {
  name: "PolymerForm",
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
      view_context: this.viewContext,
      polymer_info: structuredClone(polymer_const.polymerInfoForm),// 聚合物基本信息表单配置
      basic_form_items: [
        // --- 基础识别信息 ---
        { label: "塑料简称", prop: "abbreviation", type: "select", allow_create: true, clearable: true, options: polymer_const.polymerAbbreivationOptions },
        { label: "牌号", prop: "grade", type: "input", placeholder: "厂商具体牌号，如：PA6-GF30" },
        { label: "塑料类别", prop: "category", type: "select", options: polymer_const.polymerCategoryOptions },
        { label: "塑料厂商", prop: "manufacturer", type: "autocomplete", query: { table: "polymer", column: "manufacturer" }, placeholder: "如：BASF, SABIC, 金发科技" },
        { label: "系列", prop: "series", type: "input", placeholder: "可选，如：Ultradur®, Luran®" },  
        
        // --- 管理与编码信息 ---
        { label: "数据来源", prop: "data_source", type: "select", clearable: true, allow_create: true, options: polymer_const.polymerDataSourceOptions },
        { label: "内部编号", prop: "internal_id", type: "input", placeholder: "企业内部材料编码" },
        { label: "等级代码", prop: "level_code", type: "input", placeholder: "如：A级、工程级、回收料等" },
        { label: "供应商代码", prop: "vendor_code", type: "input", placeholder: "对应采购系统的供应商编码" },
        // { label: "数据状态", prop: "data_status", type: "input", placeholder: "如：已验证、待测试、草稿" }
      ],
      process_form_items: [
        // --- 熔体与固体密度 ---
        { label: "熔体与固体密度", type: "divider" },
        { label: "熔体密度", prop: "melt_density", type: "number", unit: "g/cm³", fixed: 4 },
        { label: "固体密度", prop: "solid_density", type: "number", unit: "g/cm³", fixed: 4 },

        // --- 熔体温度 ---
        { label: "熔体温度", type: "divider" },
        { label: "最小熔体温度", prop: "min_melt_temp", type: "number", unit: "℃" },
        { label: "最大熔体温度", prop: "max_melt_temp", type: "number", unit: "℃" },
        { label: "推荐熔体温度", prop: "recommended_melt_temp", type: "number", unit: "℃" },

        // --- 模具温度 ---
        { label: "模具温度", type: "divider" },
        { label: "最小模具温度", prop: "min_mold_temp", type: "number", unit: "℃" },
        { label: "最大模具温度", prop: "max_mold_temp", type: "number", unit: "℃" },
        { label: "推荐模具温度", prop: "recommended_mold_temp", type: "number", unit: "℃" },

        // --- 剪切线速度 ---
        { label: "剪切线速度", type: "divider" },
        { label: "最小剪切线速度", prop: "min_shear_line_speed", type: "number", unit: "mm/s" },
        { label: "最大剪切线速度", prop: "max_shear_line_speed", type: "number", unit: "mm/s" },
        { label: "推荐剪切线速度", prop: "recommended_shear_line_speed", type: "number", unit: "mm/s" },

        // --- 其他工艺参数 ---
        { label: "其他工艺参数", type: "divider" },
        { label: "降解温度", prop: "degradation_temp", type: "number", unit: "℃" },
        { label: "顶出温度", prop: "ejection_temp", type: "number", unit: "℃" },
        { label: "料筒停留时间", prop: "barrel_residence_time", type: "number", unit: "min" },
        { label: "最大剪切速率", prop: "max_shear_rate", type: "number", unit: "1/s" },
        { label: "最大剪切应力", prop: "max_shear_stress", type: "number", unit: "MPa" },
        { label: "推荐注射速率", prop: "recommend_injection_rate", type: "number", unit: "cm³/s" },
        { label: "推荐背压", prop: "recommend_back_pressure", type: "number", unit: "MPa" },

        // --- 塑料干燥信息 ---
        { label: "塑料干燥信息", type: "divider" },
        { label: "干燥方式", prop: "drying_method", type: "select", options: polymer_const.dryingMethodOptions },
        { label: "干燥温度下限", prop: "drying_temp_min", type: "number", unit: "℃" },
        { label: "干燥温度上限", prop: "drying_temp_max", type: "number", unit: "℃" },
        { label: "干燥时间下限", prop: "drying_time_min", type: "number", unit: "h" },
        { label: "干燥时间上限", prop: "drying_time_max", type: "number", unit: "h" },
      ],
      pvt_form_items: [
        { label: "Tait b5", prop: "tait_b5", type: "number", unit: "K", fixed: 8 },
        { label: "Tait b6", prop: "tait_b6", type: "number", unit: "K/Pa", fixed: 8 },
        { label: "Tait b1m", prop: "tait_b1m", type: "number", unit: "m³/kg", fixed: 8 },
        { label: "Tait b2m", prop: "tait_b2m", type: "number", unit: "m³/kg-K", fixed: 8 },
        { label: "Tait b3m", prop: "tait_b3m", type: "number", unit: "Pa", fixed: 8 },
        { label: "Tait b4m", prop: "tait_b4m", type: "number", unit: "1/K", fixed: 8 },
        { label: "Tait b1s", prop: "tait_b1s", type: "number", unit: "m³/kg", fixed: 8 },
        { label: "Tait b2s", prop: "tait_b2s", type: "number", unit: "m³/kg·K", fixed: 8 },
        { label: "Tait b3s", prop: "tait_b3s", type: "number", unit: "Pa", fixed: 8 },
        { label: "Tait b4s", prop: "tait_b4s", type: "number", unit: "1/K", fixed: 8 },
        { label: "Tait b7", prop: "tait_b7", type: "number", unit: "m³/kg", fixed: 8 },
        { label: "Tait b8", prop: "tait_b8", type: "number", unit: "1/K", fixed: 8 },
        { label: "Tait b9", prop: "tait_b9", type: "number", unit: "1/Pa", fixed: 8 }
      ],
      rheology_form_items: [ 
        { label: "粘度模型", type: "divider" },
        { label: "粘度模型", prop: "model_type", type: "select", options: [{ label: "Cross-WLF", value: "cross_wlf" }] },

        { label: "Cross-WLF 参数", type: "divider" },
        { label: "Cross-WLF n", prop: "cross_wlf_n", type: "number", unit: null, fixed: 8 },
        { label: "Cross-WLF tau", prop: "cross_wlf_tau", type: "number", unit: "Pa", fixed: 8 },
        { label: "Cross-WLF D1", prop: "cross_wlf_d1", type: "number", unit: "Pa·s", fixed: 8 },
        { label: "Cross-WLF D2", prop: "cross_wlf_d2", type: "number", unit: "K", fixed: 8 },
        { label: "Cross-WLF D3", prop: "cross_wlf_d3", type: "number", unit: "K/Pa", fixed: 8 },
        { label: "Cross-WLF A1", prop: "cross_wlf_a1", type: "number", unit: null, fixed: 8 },
        { label: "Cross-WLF A2", prop: "cross_wlf_a2", type: "number", unit: "K", fixed: 8 },

        { label: "接合点损失法", type: "divider" },
        { label: "接合点损失法c1", prop: "c1", type: "number", unit: "Pa^(1-c2)", fixed: 8 },
        { label: "接合点损失法c2", prop: "c2", type: "number", unit: null, fixed: 8 },

        { label: "其他流变参数", type: "divider" },
        { label: "转换温度", prop: "transition_temp", type: "number", unit: "℃", fixed: 8 },
        { label: "粘度指数", prop: "viscosity_index", type: "number", unit: null, fixed: 8 },

        { label: "MFR 测试条件", type: "divider" },
        { label: "MFR测试温度", prop: "mfr_temp", type: "number", unit: "℃", fixed: 2 },
        { label: "MFR载荷", prop: "mfr_load", type: "number", unit: "kg", fixed: 2 },
        { label: "MFR值", prop: "mfr_value", type: "number", unit: "g/10min", fixed: 2 }
      ],
      mechanical_form_items: [
        { label: "弹性性能", type: "divider" },
        { label: "弹性模量E1", prop: "elastic_modulus_1", type: "number", unit: "MPa", fixed: 4 },
        { label: "弹性模量E2", prop: "elastic_modulus_2", type: "number", unit: "MPa", fixed: 4 },
        { label: "泊松比v12", prop: "poisson_v12", type: "number", unit: null, fixed: 4 },
        { label: "泊松比v23", prop: "poisson_v23", type: "number", unit: null, fixed: 4 },
        { label: "剪切模量G12", prop: "shear_modulus_g12", type: "number", unit: "MPa", fixed: 4 },

        { label: "热膨胀性能", type: "divider" },
        { label: "热膨胀系数α1", prop: "thermal_expansion_1", type: "number", unit: "1/℃", fixed: 4 },
        { label: "热膨胀系数α2", prop: "thermal_expansion_2", type: "number", unit: "1/℃", fixed: 4 }
      ],
      shrinkage_form_items: [
        { label: "平均收缩率", type: "divider" },
        { label: "平行收缩率", prop: "ave_h_shrink", type: "number", unit: "%", fixed: 4 },
        { label: "垂直收缩率", prop: "ave_v_shrink", type: "number", unit: "%", fixed: 4 },

        { label: "平行方向收缩范围", type: "divider" },
        { label: "最小平行收缩率", prop: "min_h_shrink", type: "number", unit: "%", fixed: 4 },
        { label: "最大平行收缩率", prop: "max_h_shrink", type: "number", unit: "%", fixed: 4 },

        { label: "垂直方向收缩范围", type: "divider" },
        { label: "最小垂直收缩率", prop: "min_v_shrink", type: "number", unit: "%", fixed: 4 },
        { label: "最大垂直收缩率", prop: "max_v_shrink", type: "number", unit: "%", fixed: 4 }
      ],
      rules: {
        abbreviation: [
          { required: true, message: "材料名称缩写为空!" }
        ],
        grade: [
          { required: true, message: "材料牌号为空!" }
        ],
        // max_melt_temp: [
        //   { required: true, message: '最大熔体温度为空!' }
        // ],
        // min_melt_temp: [
        //   { required: true, message: '最小熔体温度为空!' }
        // ],
        // recommended_melt_temp: [
        //   { required: true, message: '推荐熔体温度为空!' }
        // ],
        // degradation_temp: [
        //   { required: true, message: '塑料降解温度为空!' }
        // ],
        // max_mold_temp: [
        //   { required: true, message: '最大模具温度为空!' }
        // ],
        // min_mold_temp: [
        //   { required: true, message: '最小模具温度为空!' }
        // ],
        // recommended_mold_temp: [
        //   { required: true, message: '推荐模具温度为空!' }
        // ],
        // ejection_temp: [
        //   { required: true, message: '顶出温度为空!' }
        // ],
        // max_shear_line_speed: [
        //   { required: true, message: '最大剪切线速度为空!' }
        // ],
        // min_shear_line_speed: [
        //   { required: true, message: '最小剪切线速度为空!' }
        // ],
        // recommended_shear_line_speed: [
        //   { required: true, message: '推荐剪切线速度为空!' }
        // ],
        // recommend_injection_rate: [
        //   { required: true, message: '推荐注射速率为空!' }
        // ],
        // recommend_back_pressure: [
        //   { required: true, message: '推荐背压为空!' }
        // ],
      },
      polymer_file_info: [],
      export_loading: false,
      save_loading: false,
    }
  },
  computed: {
    pvt: function() {
      return this.polymer_info.pvt
    },
    rheology: function() {
      return this.polymer_info.rheology
    },
    mechanical: function() {
      return this.polymer_info.mechanical
    },  
    shrinkage: function() {
      return this.polymer_info.shrinkage
    },
  },
  watch: {
    viewContext: {
      handler: function() {
        this.view_context = this.viewContext
        this.initializeView()
      },
      deep: true,
      immediate: true
    }
  },
  mounted() {
    this.initializeView()
  },
  methods: {
    initializeView() {
      // 分多种情况进入当前界面，默认情况下不带材料id
      this.polymer_info.id = null
      if (this.view_context.id) {
        // 通过弹出窗口进入界面
        this.polymer_info.id = this.view_context.id
      } else if (this.$route.query.id) {
        // 通过跳转进入界面
        this.polymer_info.id = Number(this.$route.query.id)
      }

      if (this.polymer_info.id) {
        // 如果材料id存在，读取材料参数
        this.getPolymerDetail(this.polymer_info.id)
      } else {
        // 从文件导入
        if (this.view_context.mode == "import") {
          this.polymer_info = this.view_context.excel_data
        }
      }
    },
    async getPolymerDetail(id) {
      // 从数据库读取模具参数
      if (!id) return

      // 读取材料参数
      const res = await polymerMethod.getDetail(id)
      if (res.status === 0) {
        this.polymer_info = res.data
      }

      if (this.view_context.mode == "copy") {
        this.polymer_info.id = null
        this.polymer_info.grade = null
      }
    },
    async savePolymerDetail() {
      if (!this.$hasPermission("update_polymer")) {
        return this.$message("无材料的编辑权限")
      }
      const validate = createValidateAndFocus(this)
      let access = true

      // 校验材料参数
      access = await validate(this.$refs.polymerForm)
      if (!access) return

      // 根据是否有材料 id 分别执行新增/更新服务
      if (this.polymer_info.id) {
        // 更新材料信息
        const res = await polymerMethod.edit(this.polymer_info, this.polymer_info.id)
        if (res.status === 0) {
          this.$message({ message: "材料信息编辑成功！", type: "success" })
          this.$emit("close")
          this.$router.push("/polymer/list")
        }
      } else {
        // 新增材料信息
        const res = await polymerMethod.add(this.polymer_info)
        if (res.status === 0) {
          this.$message({ message: "材料信息新增成功！", type: "success" })
          this.$emit("close")
          this.$router.push("/polymer/list")
        }
      }
    },
    exportPolymerToExcel() {
      // exportReport({
      //   "resource": "polymer_info",
      //   "polymer_info": this.polymer_info
      // }).then(res => {
      //   if (res.status === 0 && res.data.url) {
      //     this.$message({ message: "导出成功。", type: "success" })
      //     this.$emit("close")
      //     window.location.href = getFullFileUrl(res.data.url)
      //   }
      // })
    },
    // onFileUpdate(file_infos) {
    //   let file_list = []
    //   for (let i = 0; i < file_infos.length; ++i) {
    //     let file_info = file_infos[i]
    //     file_list.push({
    //       "id": file_info.id,
    //       "search_id": file_info.search_id,
    //       "search_type": file_info.search_type,
    //       "name": file_info.name,
    //       "url": file_info.url,
    //     })
    //   }
    //   this.polymer_file_info = file_list
    // },
    resetView() {
      this.polymer_info = structuredClone(polymer_const.polymerInfoForm)
    }
  }
}
</script>

<style lang="scss" scoped>

</style>
