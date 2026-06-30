<template>
  <div>
    <el-card class="box-card">
      <div slot="header" class="clearfix">
        <span>基本信息</span>
      </div>
      <el-form
        ref="basicForm" 
        size="mini"
        label-width="8rem"
        :inline="true" 
        :model="mold_info" 
        :rules="rules"
      >
        <template v-for="item, idx in basic_form_items">
          <el-divider
            v-if="item.type === 'divider'"
            :key="`divider_${idx}`"
            content-position="center"
          >
            {{ item.label }}
          </el-divider>
          <el-form-item
            v-else-if="item.prop=='product_description'"
            :key="`product_description_${idx}`"
            :label="item.label"
            :prop="item.prop"
            class="full-width"
          >
            <el-input
              type="textarea"
              rows="2"
              placeholder="请输入产品描述"
              v-model.trim="mold_info[item.prop]"
            >
            </el-input>
          </el-form-item>
          <el-form-item
            v-else
            :key="`basic_${idx}`"
            :label="item.label"
            :prop="item.prop"
          >
            <el-tooltip 
              v-if="item.prop=='cavity_layout'"
              effect="dark" 
              placement="top"
            >
              <div slot="content">
                1: 表示单色模具, 单腔, 共1个制品<br>
                1+1: 表示单色模具, 两腔, 共2个制品, 制品参数不同<br>
                1*2: 表示单色模具, 两腔, 共2个制品, 制品参数相同<br>
                1&1: 表示双色模具, 1射单腔, 成型1个制品, 2射单腔, 成型1个制品<br>
                1&1+1: 表示双色模具, 1射单腔, 成型1个制品, 2射双腔, 成型2个制品, 制品参数不同<br>
                规则以此类推
              </div>
              <el-input 
                v-model.trim="mold_info[item.prop]"
                placeholder="示例：1*2、1+1"
              >
                <span slot="suffix" v-if="item.unit">{{ item.unit }}</span>
              </el-input>
            </el-tooltip>
            <el-input 
              v-else-if="item.type=='input'"
              v-model.trim="mold_info[item.prop]"
              :placeholder="item.placeholder || `请输入${item.label}`"
            >
              <span slot="suffix" v-if="item.unit">{{ item.unit }}</span>
            </el-input>
            <el-input 
              v-else-if="item.type=='number'"
              v-model.trim="mold_info[item.prop]"
              v-number="item.fixed"
              :placeholder="item.placeholder || `请输入${item.label}`"
            >
              <span slot="suffix" v-if="item.unit">{{ item.unit }}</span>
            </el-input>
            <el-select 
              v-else-if="item.type=='select'"
              v-model="mold_info[item.prop]"
              filterable
              default-first-option
              :placeholder="item.placeholder || `请选择${item.label}`"
              @change="(val) => item.onChange && item.onChange(val)"
            >
              <el-option 
                v-for="option, opt_idx in item.options"
                :key="opt_idx"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
            <el-autocomplete
              v-else-if="item.prop=='recommended_tonnage'"
              :value="String(mold_info[item.prop] || '')"
              @input="val => mold_info[item.prop] = val"
              clearable
              :placeholder="item.placeholder || `请输入${item.label}`"
              :debounce="0"
              :fetch-suggestions="$querySuggestions(item.query)"
            >
              <span slot="suffix" v-if="item.unit">{{ item.unit }}</span>
            </el-autocomplete>
          </el-form-item>
        </template>
      </el-form>
    </el-card>

    <el-card class="box-card">
      <div slot="header" class="clearfix">
        <span>浇注系统</span>
      </div>
      <el-tabs v-model="active_gating">
        <el-tab-pane 
          v-for="(gating_system, index) in mold_info.gating_systems"
          :key="index"
          :label="'浇注 #'+String(index+1)"
          :name="String(index)"
        >
          <gating-system-form
            ref="gatingSystem" 
            :gating-system="gating_system"
          />
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-card class="box-card">
      <div slot="header" class="clearfix">
        <span>冷却系统</span>
      </div>
      <cooling-system-form
        ref="coolingSystem"
        :cooling-system="cooling_system"
      />
    </el-card>

    <el-card class="box-card">
      <div slot="header" class="clearfix">
        <span>顶出系统</span>
      </div>
      <ejection-system-form
        ref="ejectionSystem"
        :ejection-system="ejection_system"
      />
    </el-card>

    <el-card class="box-card">
      <div slot="header" class="clearfix">
        <span>其他参数</span>
      </div>
      <el-form
        ref="structureForm" 
        label-width="8rem"
        size="mini"
        :model="mold_info" 
        :inline="true"
      >
        <template v-for="item, idx in structure_form_items">
          <el-divider
            v-if="item.type === 'divider'"
            :key="`struct_${idx}`"
            content-position="center"
          >
            {{ item.label }}
          </el-divider>
          <el-form-item
            v-else
            :key="`struct_${item.prop}`"
            :label="item.label"
            :prop="item.prop"
          >
            <el-input
              v-if="item.type === 'number'"
              v-number
              v-model="mold_info[item.prop]"
              :placeholder="item.placeholder || `请输入${item.label}`"
            >
              <span slot="suffix" v-if="item.unit">{{ item.unit }}</span>
            </el-input>
            <el-input
              v-else-if="item.type === 'integer'"
              v-number="0"
              v-model="mold_info[item.prop]"
              :placeholder="item.placeholder || `请输入${item.label}`"
            >
              <span slot="suffix" v-if="item.unit">{{ item.unit }}</span>
            </el-input>
            <el-select
              v-else-if="item.type === 'select'"
              v-model="mold_info[item.prop]"
              clearable
              filterable 
              allow-create
            >
              <el-option
                v-for="(option, opt_idx) in item.options"
                :key="opt_idx"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
            <el-select
              v-else-if="item.type === 'number-select'"
              v-model="mold_info[item.prop]"
              v-number
              clearable
              filterable 
              allow-create
              @clear="() => mold_info[item.prop] = null"
            >
              <el-option
                v-for="(option, opt_idx) in item.options"
                :key="opt_idx"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
            <el-input
              v-else-if="item.type === 'text'"
              v-model="mold_info[item.prop]"
              :placeholder="item.placeholder || `请输入${item.label}`"
            />
            <el-radio-group 
              v-else-if="item.type === 'radio'"
              v-model="mold_info[item.prop]"
            >
              <el-radio-button :label="true">
                是
              </el-radio-button>
              <el-radio-button :label="false">
                否
              </el-radio-button>
            </el-radio-group>
          </el-form-item>
        </template>
        <el-divider content-position="center">
          辅助装置
        </el-divider>
        <el-alert
          title="辅助装置指安装在模具上的功能性附加设备，例如：液压抽芯油缸、气动阀、热流道温控箱、模内传感器等。可从下拉中选择，或直接输入自定义名称。"
          type="info"
          show-icon
          :closable="false"
          style="margin-bottom: 12px;"
        />
        <el-select
          class="assist-select"
          v-model="checked_assist_equipments"
          multiple
          filterable
          allow-create
          default-first-option
          placeholder="请选择或输入辅助装置"
          style="width: 100%"
        >
          <el-option
            v-for="item in assist_equipment_options"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
      </el-form>
    </el-card>

    <div style="height: 30px;"></div>

    <div class="floating-actions-right">
      <el-button
        v-if="isModuleVisible('export_button')"
        type="success" 
        size="small"
        :loading="export_loading" 
        @click="exportMoldToExcel" 
      >
        导  出
      </el-button>
      <el-button 
        v-if="isModuleVisible('return_button')"
        type="danger"
        size="small"
        @click="$emit('close')" 
      >
        返  回
      </el-button>
      <el-button 
        v-if="isModuleVisible('reset_button')"
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
        @click="saveMoldInfo"
        :disabled="!$hasPermission('update_mold')"
      >
        {{ mold_info.id ? "更  新" : "保  存" }}
      </el-button>
    </div>
  </div>
</template>

<script>
import { moldMethod } from "@/api"
import { 
  moldInfoForm, gatingSystemForm, moldTypeOptions, moldCategoryOptions,
  moldStructureOptions, shotCountOptions, partRemovalActionOptions,
  liftingTypeOptions, liftingEyeBoltOptions, locatorTypeOptions,
  locatingRingOuterDiaOptions, movingLocatingRingOuterDiaOptions,
  assistEquipmentOptions, recommendedTonnageOptions,
} from "@/constants/mold-const"
import {
  productMajorOptions, mediumOptionsMap, minorOptionsMap
} from "@/utils/product-category.ts"
import { createValidateAndFocus } from "@/utils/form-helper"
import GatingSystemForm from "./components/GatingSystemForm.vue"
import CoolingSystemForm from "./components/CoolingSystemForm.vue"
import EjectionSystemForm from "./components/EjectionSystemForm.vue"

export default {
  name: "MoldForm",
  components: { 
    GatingSystemForm, 
    CoolingSystemForm, 
    EjectionSystemForm 
  },
  props: {
    viewContext: {
      type: Object,
      default: () => ({
        id: null,
        title: null,
        mode: "add",
        excel_data: null
      })
    }
  },
  data() {
    return { 
      view_context: this.viewContext,
      mold_info: structuredClone(moldInfoForm),
      basic_form_items: [
        { label: "模具编号", prop: "mold_no", type: "input", placeholder: "模具唯一标识" },
        { label: "模具名称", prop: "mold_name", type: "input", placeholder: "请输入模具名称" },
        { label: "模具类型", prop: "mold_type", type: "select", options: [] },
        { label: "模具类别", prop: "category", type: "select", options: [] },
        { label: "模具结构", prop: "structure", type: "select", options: [] },
        { label: "注射次数", prop: "shot_count", type: "select", options: [], onChange: this.onShotCountChange },
        { label: "模腔布局", prop: "cavity_layout", type: "input" },
        // { label: "型腔数量", prop: "cavity_count", type: "number", fixed: 0 },
        { label: "目标成型周期", prop: "target_cycle_time", type: "number", fixed: 2, unit: "s" },
        { 
          label: "客户机吨位", 
          prop: "recommended_tonnage", 
          type: "autocomplete", 
          fixed: 0, 
          unit: "Ton", 
          query: { 
            table: "injection_molding_machine", 
            column:"max_clamping_force" 
          } 
        },
        { label: "总注射重量", prop: "total_injection_weight", type: "number", fixed: 2, unit: "g" },
        // --- 产品分类信息 ---
        { label: "产品分类", type: "divider" },
        { label: "产品大类", prop: "product_category", type: "select", options: [] },
        { label: "产品中类", prop: "product_subcategory", type: "select", options: [] },
        { label: "产品小类", prop: "product_model", type: "select", options: [] },
        { label: "产品描述", prop: "product_description", type: "textarea" },
      ],
      structure_form_items: [
        { label: "尺寸结构", type: "divider" },
        { label: "模具长度", prop: "mold_length", type: "number", unit: "mm" },
        { label: "模具宽度", prop: "mold_width", type: "number", unit: "mm" },
        { label: "模具厚度", prop: "mold_thickness", type: "number", unit: "mm" },
        { label: "模具重量", prop: "mold_weight", type: "number", unit: "kg" },
        { label: "模具吊装", type: "divider" },
        { label: "吊装类型", prop: "handling_type", type: "select", options: [] },
        { label: "吊环规格", prop: "handling_thread_size", type: "select", options: [] },
        // { label: "吊装螺纹深度", prop: "handling_thread_depth", type: "number", unit: "mm" },
        { label: "吊装点数量", prop: "handling_point_count", type: "integer", unit: "个" },
        // { label: "吊装点位置", prop: "handling_position", type: "text", unit: null },
        { label: "模具定位", type: "divider" },
        { label: "定模定位圈外径", prop: "locating_ring_outer_dia", type: "number-select", options: [] },
        { label: "定模定位圈内径", prop: "locating_ring_inner_dia", type: "number", unit: "mm" },
        { label: "定模定位圈高度", prop: "locating_ring_height", type: "number", unit: "mm" },
        // { label: "定位圈材质", prop: "locating_ring_material", type: "text", unit: null },
        // { label: "定位圈标准", prop: "locating_ring_standard", type: "text", unit: null },
        { label: "动模定位圈外径", prop: "mov_half_locating_ring_outer_dia", type: "number-select", options: [] },
        { label: "动模定位圈内径", prop: "mov_half_locating_ring_inner_dia", type: "number", unit: "mm" },
        { label: "动模定位圈高度", prop: "mov_half_locating_ring_height", type: "number", unit: "mm" },
        // { label: "导柱直径", prop: "guide_pin_diameter", type: "number", unit: "mm" },
        // { label: "导柱数量", prop: "guide_pin_count", type: "integer", unit: "个" },
        // { label: "是否有精定位", prop: "has_precision_locator", type: "radio", unit: null },
        // { label: "精定位类型", prop: "locator_type", type: "select", options: [] },
        // { label: "精定位位置", prop: "locator_position", type: "text", unit: null },
        { label: "开合模与取件", type: "divider" },
        { label: "取件方式", prop: "part_removal_action", type: "select", options: [] },
        { label: "开模行程", prop: "recommended_opening_stroke", type: "number", unit: "mm" },
        { label: "流道分离距离", prop: "runner_separation_distance", type: "number", unit: "mm" },
        { label: "最小锁模力", prop: "min_clamping_force", type: "number", unit: "Ton" },
      ],
      rules: {
        "mold_no": [
          { required: true, message: "模具编号不能为空", trigger: "blur" },
        ],
      },
      active_gating: "0",
      // --- 下拉菜单项 ---
      select_options: {
        "mold_type": moldTypeOptions,
        "category": moldCategoryOptions,
        "structure": moldStructureOptions,
        "shot_count": shotCountOptions,
        "product_category": productMajorOptions,
        "product_subcategory": [],
        "product_model": [],
        "recommended_tonnage": recommendedTonnageOptions,
        "part_removal_action": partRemovalActionOptions,
        "handling_type": liftingTypeOptions,
        "handling_thread_size": liftingEyeBoltOptions,
        "locator_type": locatorTypeOptions,
        "locating_ring_outer_dia": locatingRingOuterDiaOptions,
        "mov_half_locating_ring_outer_dia": movingLocatingRingOuterDiaOptions,
      },
      assist_equipment_options: assistEquipmentOptions,
      save_loading: false,
      export_loading: false,
    }
  },
  computed: {
    cooling_system: function() {
      return this.mold_info.cooling_system
    },
    ejection_system: function() {
      return this.mold_info.ejection_system
    },
    checked_assist_equipments: {
      get: function() {
        if (this.mold_info.mechanism) {
          return this.mold_info.mechanism.split("|")
        }
        return []
      },
      set: function(value) {
        if (value) {
          this.mold_info.mechanism = value.join("|")
        }
      }
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
    },
    "mold_info.product_category"() {
      this.select_options.product_subcategory.length = 0
      this.select_options.product_subcategory.push(...(mediumOptionsMap[this.mold_info.product_category] || [])) 
    },
    "mold_info.product_subcategory"() {
      this.select_options.product_model.length = 0
      this.select_options.product_model.push(...(minorOptionsMap[this.mold_info.product_subcategory] || []))
    },
  },
  mounted() {
    this.initFormOptions()
  },
  methods: {
    initFormOptions() {
      const keys = Object.keys(this.select_options)
      for (const item of this.basic_form_items) {
        if (item.type === "select" && keys.includes(item.prop)) {
          item.options = this.select_options[item.prop]
        }
      }
      for (const item of this.structure_form_items) {
        if (item.type.indexOf("select") != -1 && keys.includes(item.prop)) {
          item.options = this.select_options[item.prop]
        }
      }
    },
    isModuleVisible(module) {
      switch (module) {
        case "export_button":
          return false
        case "return_button":
          return this.view_context.mode == "edit"
        case "reset_button":
          return this.view_context.mode == "add"
        default:
          return true
      }
    },
    async initializeView() {
      // 重置界面
      this.resetView()
      if (this.view_context.id) {
        // 通过弹出窗口进入界面
        this.mold_info.id = this.view_context.id
      } else if (this.$route.query.id) {
        // 通过跳转传参进入界面
        this.mold_info.id = this.$route.query.id
      } else if (this.$route.query.project_id) {
        this.mold_info.project_id = this.$route.query.project_id
      }

      if (this.mold_info.id) {
        // 如果模具id存在，读取模具参数
        this.getMoldInfo(this.mold_info.id)
      } else {
        // 从文件导入
        if (this.view_context.mode == "import") {
          this.mold_info = this.view_context.excel_data
        }
      }
    },
    async getMoldInfo(id) {
      if (!id) return
      // 读取模具参数
      const res = await moldMethod.getDetail(id)
      if (res.status === 0) {
        Object.assign(this.mold_info, res.data)
      } else {
        this.$message({ message: "未读取到相关模具信息！", type: "warning" }) 
      }
    },
    async saveMoldInfo() {
      // 验证数据完整性
      const validate = createValidateAndFocus(this)

      const acccess = await validate(this.$refs.basicForm)
      if (!acccess) return

      // 根据是否有模具 id 分别执行新增/更新服务
      if (this.mold_info.id) {
        // 更新模具信息
        const res = await moldMethod.edit(this.mold_info, this.mold_info.id)
        if (res.status === 0) {
          this.$message({ message: "模具信息编辑成功！", type: "success" })
        }
      } else {
        // 新增模具信息
        const res = await moldMethod.add(this.mold_info)
        if (res.status === 0) {
          this.$message({ message: "模具信息新增成功！", type: "success" })
        }
      }

      // 数据提交完成切换到模具列表 
      this.$emit("close")
      this.$router.push("/mold/list")
    },
    onShotCountChange(val) {
      const gs_count = this.mold_info.gating_systems.length
      if (val < gs_count) {
        this.mold_info.gating_systems.splice(val - 1, gs_count - val)
      } else if (val > gs_count) {
        for (let i = gs_count; i < val; i++) {
          this.mold_info.gating_systems.push(structuredClone(gatingSystemForm))
        }
      }
    },
    resetView() {
      this.mold_info = structuredClone(moldInfoForm)
      this.active_gating = "0"
    },
  }
}
</script>

<style lang="scss" scoped>

</style>
