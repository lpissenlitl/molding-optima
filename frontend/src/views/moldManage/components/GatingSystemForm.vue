<template>
  <el-form
    ref="formData"
    size="mini"
    :inline="true"
    :model="gating_system"
    label-width="8rem"
  >
    <el-alert
      :title="getRunnerTypeHint"
      type="info"
      show-icon
      style="margin-bottom: 16px"
      :closable="false"
    />

    <el-form-item 
      v-for="item, index in basic_form_items"
      :key="`runner_${index}`"
      :label="item.label"
      :prop="item.prop"
    >
      <el-input
        v-if="item.type === 'number'"
        v-model="gating_system[item.prop]"
        v-number
        :placeholder="item.placeholder || `请输入${item.label}`"
      >
        <span slot="suffix" v-if="item.unit">{{ item.unit }}</span>
      </el-input>
      <el-select 
        v-else-if="item.type === 'select'"
        v-model="gating_system[item.prop]"
      >
        <el-option 
          v-for="(option, opt_idx) in item.options"
          :key="opt_idx"
          :label="option.label" 
          :value="option.value"
        />
      </el-select>
    </el-form-item>
    
    <template v-if="showHotRunner">
      <el-divider content-position="center">
        热流道结构
      </el-divider>
      <el-form-item 
        v-for="item, index in hotrunner_form_items"
        :key="`hotrunner_${index}`"
        :label="item.label"
        :prop="item.prop"
      >
        <el-input
          v-if="item.type === 'input'"
          v-model="gating_system[item.prop]"
          :placeholder="item.placeholder || `请输入${item.label}`"
          :disabled="isInputDisabled(item.prop)"
        />
        <el-input
          v-else-if="item.type === 'integer'"
          v-model="gating_system[item.prop]"
          v-number="0"
          :placeholder="item.placeholder || `请输入${item.label}`"
        >
          <span slot="suffix" v-if="item.unit">{{ item.unit }}</span>
        </el-input>
        <el-select 
          v-else-if="item.type === 'select'"
          v-model="gating_system[item.prop]"
          clearable
          filterable 
          allow-create
          :placeholder="item.placeholder || `请选择${item.label}`"
          :disabled="isInputDisabled(item.prop)"
        >
          <el-option 
            v-for="(option, opt_idx) in item.options"
            :key="opt_idx"
            :label="option.label" 
            :value="option.value"
          />
        </el-select>
        <el-radio-group 
          v-else-if="item.prop === 'has_sequencing_control'"
          v-model="gating_system.has_sequencing_control"
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

    <template v-if="showColdRunner">
      <el-divider content-position="center">
        冷流道结构
      </el-divider>
      <el-form-item 
        v-for="item, index in coldrunner_form_items"
        :key="`coldrunner${index}`"
        :label="item.label"
        :prop="item.prop"
      >
        <el-input
          v-if="item.type === 'input'"
          v-model="gating_system[item.prop]"
          :placeholder="item.placeholder || `请输入${item.label}`"
        />
        <el-input
          v-else-if="item.type === 'number'"
          v-model="gating_system[item.prop]"
          v-number
          :placeholder="item.placeholder || `请输入${item.label}`"
        >
          <span slot="suffix" v-if="item.unit">{{ item.unit }}</span>
        </el-input>
        <el-select 
          v-else-if="item.type === 'select'"
          v-model="gating_system[item.prop]"
          v-number
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
      </el-form-item>
    </template>

    <el-tabs
      v-model="active_cavity"
      @tab-click="onAddCavityForm"
      @tab-remove="onRemoveCavityForm"
    >
      <el-tab-pane 
        v-for="(cavity, cavi_idx) in gating_system.cavities"
        :key="cavi_idx"
        :label="'型腔 #'+String(cavi_idx+1)"
        :name="String(cavi_idx)"
        :closable="cavi_idx >= 1"
      >
        <el-form-item
          v-for="item, idx in cavity_form_items"
          :key="`cavity_${idx}`"
          :label="item.label"
          :prop="item.prop"
        >
          <el-input
            v-if="item.type === 'input'"
            v-model="cavity[item.prop]"
            :placeholder="item.placeholder || `请输入${item.label}`"
          />
          <el-input
            v-else-if="item.type === 'number'"
            v-model="cavity[item.prop]"
            v-number
            :placeholder="item.placeholder || `请输入${item.label}`"
          >
            <span slot="suffix" v-if="item.unit">{{ item.unit }}</span>
          </el-input>
          <el-input
            v-else-if="item.type === 'integer'"
            v-model="cavity[item.prop]"
            v-number="0"
            :placeholder="item.placeholder || `请输入${item.label}`"
          >
            <span slot="suffix" v-if="item.unit">{{ item.unit }}</span>
          </el-input>
        </el-form-item>

        <el-tabs 
          v-model="active_gate"
          @tab-click="onAddGateForm" 
          @tab-remove="onRemoveGateForm"
        >
          <el-tab-pane 
            v-for="(gate, gate_idx) in cavity.gates"
            :key="gate_idx"
            :label="'浇口 #'+String(gate_idx+1)"
            :name="String(gate_idx)"
            :closable="gate_idx >= 1"
          >
            <el-form-item
              v-for="item, idx in gate_form_items"
              :key="`gate_${idx}`"
              :label="item.label"
              :prop="item.prop"
            >
              <el-input
                v-if="item.type === 'input'"
                v-model="gate[item.prop]"
                :placeholder="item.placeholder || `请输入${item.label}`"
              />
              <el-input
                v-else-if="item.type === 'number'"
                v-model="gate[item.prop]"
                v-number
                :placeholder="item.placeholder || `请输入${item.label}`"
              >
                <span slot="suffix" v-if="item.unit">{{ item.unit }}</span>
              </el-input>
              <el-input
                v-else-if="item.type === 'integer'"
                v-model="gate[item.prop]"
                v-number="0"
                :placeholder="item.placeholder || `请输入${item.label}`"
              >
                <span slot="suffix" v-if="item.unit">{{ item.unit }}</span>
              </el-input>
              <el-select 
                v-else-if="item.type === 'select'"
                v-model="gate[item.prop]"
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
            </el-form-item>

            <template v-if="showGateShapeRect(gate)">
              <!-- 矩形类 -->
              <el-form-item
                v-for="item, idx in rect_form_items"
                :key="`rect_${idx}`"
                :label="item.label"
                :prop="item.prop"
              >
                <el-input
                  v-model="gate[item.prop]"
                  v-number
                  :placeholder="item.placeholder || `请输入${item.label}`"
                >
                  <span slot="suffix" v-if="item.unit">{{ item.unit }}</span>
                </el-input>
              </el-form-item>
            </template>

            <template v-if="showGateShapeCircle(gate)">
              <!-- 圆形类 -->
              <el-form-item
                v-for="item, idx in circle_form_items"
                :key="`circle_${idx}`"
                :label="item.label"
                :prop="item.prop"
              >
                <el-input
                  v-model="gate[item.prop]"
                  v-number
                  :placeholder="item.placeholder || `请输入${item.label}`"
                >
                  <span slot="suffix" v-if="item.unit">{{ item.unit }}</span>
                </el-input>
              </el-form-item>
            </template>

            <template v-if="showGateShapeAnnulus(gate)">
              <!-- 环形类 -->
              <el-form-item
                v-for="item, idx in annulus_form_items"
                :key="`annulus_${idx}`"
                :label="item.label"
                :prop="item.prop"
              >
                <el-input
                  v-model="gate[item.prop]"
                  v-number
                  :placeholder="item.placeholder || `请输入${item.label}`"
                >
                  <span slot="suffix" v-if="item.unit">{{ item.unit }}</span>
                </el-input>
              </el-form-item>
            </template>
          </el-tab-pane>
          <el-tab-pane label="+" name="add" key="add" />
        </el-tabs>
      </el-tab-pane>
      <el-tab-pane label="+" name="add" key="add" />
    </el-tabs>
  </el-form>
</template>

<script>
import { gateForm, cavityForm, gatingSystemForm, 
  runnerTypeOptions, hotNozzleTypeOptions, sequencingControlMethodOptions,
  sprueBushingOuterDiaOptions, sprueBushingBoreDiaOptions, sprueBushingRadiusOptions,
  gateTypeOptions, gateShapeOptions
} from "@/constants/mold-const"

export default {
  name: "GatingSystemForm",
  props: {
    gatingSystem: {
      type: Object,
      default: () => (structuredClone(gatingSystemForm))
    }
  },
  data() {
    return {
      gating_system: this.gatingSystem,
      active_cavity: "0",
      active_gate: "0",
      basic_form_items: [
        { label: "流道类别", prop: "runner_type", type: "select", options: runnerTypeOptions },
        { label: "制品总重量", prop: "total_product_weight", type: "number", unit: "g" },
      ],
      hotrunner_form_items: [
        { label: "热流道供应商", prop: "hot_runner_supplier", type: "input" },
        { label: "热流道类型", prop: "hot_runner_system_type", type: "select", options: hotNozzleTypeOptions },
        // —— 针阀相关字段（仅当类型=针阀式时有效）——
        { label: "针阀驱动方式", prop: "valve_actuation_type", type: "input" },
        { label: "分流板温控区数", prop: "hot_runner_manifold_zones", type: "integer", unit: "组" },
        { label: "热喷嘴数量", prop: "hot_runner_nozzle_count", type: "integer", unit: "个" },
        // —— 时序控制主开关 ——
        { label: "是否序流控制", prop: "has_sequencing_control", type: "radio" },
        { label: "时序控制方式", prop: "sequencing_control_method", type: "select", options: sequencingControlMethodOptions },
      ],
      coldrunner_form_items: [
        { label: "料把重量", prop: "runner_weight", type: "number", unit: "kg" },
        { label: "料把长度", prop: "runner_length", type: "number", unit: "mm" },
        { label: "浇口套外径 D1", prop: "sprue_bushing_outer_dia", type: "select", options: sprueBushingOuterDiaOptions, unit: "mm" },
        { label: "浇口套孔径 D2", prop: "sprue_bushing_bore_dia", type: "select", options: sprueBushingBoreDiaOptions, unit: "mm" },
        { label: "球面半径 R", prop: "sprue_bushing_radius", type: "select", options: sprueBushingRadiusOptions, unit: "mm" },
        // { label: "密封锥角 θ", prop: "sprue_bushing_angle", type: "number", unit: "°" },
        // { label: "主流道衬套材质", prop: "sprue_bushing_material", type: "input" },
        // { label: "主流道衬套标准", prop: "sprue_bushing_standard", type: "input" },
      ],
      cavity_form_items: [
        { label: "每射成型腔数", prop: "cavity_count_per_shot", type: "integer", unit: "腔", placeholder: "默认 1" },
        { label: "制品名称", prop: "product_name", type: "input" },
        { label: "制品编号", prop: "product_code", type: "input" },
        { label: "最大流动长度", prop: "max_flow_length", type: "number", unit: "mm" },
        { label: "平均壁厚", prop: "ave_wall_thickness", type: "number", unit: "mm" },
        { label: "最小壁厚", prop: "min_wall_thickness", type: "number", unit: "mm" },
        { label: "最大壁厚", prop: "max_wall_thickness", type: "number", unit: "mm" },
        { label: "单腔注射重量", prop: "estimated_weight_per_cavity", type: "number", unit: "g" },
        { label: "单腔投影面积", prop: "projected_area_per_cavity", type: "number", unit: "mm²" },
      ],
      gate_form_items: [
        { label: "浇口类型", prop: "gate_type", type: "select", options: gateTypeOptions },
        { label: "浇口数量", prop: "gate_count", type: "integer", unit: "个" },
        { label: "位置描述", prop: "location_description", type: "input" },
        { label: "浇口形状", prop: "gate_shape", type: "select", options: gateShapeOptions },
      ],
      rect_form_items: [
        { label: "长", prop: "length", type: "number", unit: "mm", placeholder: "浇口尺寸 长" },
        { label: "宽", prop: "width", type: "number", unit: "mm", placeholder: "浇口尺寸 宽" },
      ],
      circle_form_items: [
        { label: "直径", prop: "diameter", type: "number", unit: "mm", placeholder: "浇口尺寸 直径" },
      ],
      annulus_form_items:  [
        { label: "外径", prop: "outer_diameter", type: "number", unit: "mm", placeholder: "浇口尺寸 外径" },
        { label: "内径", prop: "inner_diameter", type: "number", unit: "mm", placeholder: "浇口尺寸 内径" },
        { label: "间距", prop: "gap", type: "number", unit: "mm", placeholder: "浇口尺寸 间隔" },
      ],
      runner_type_options: runnerTypeOptions,
    }
  },
  computed: {
    getRunnerTypeHint() {
      const type = this.gating_system.runner_type
      if (type === "热流道") return "仅显示热流道相关参数"
      if (type === "冷流道") return "仅显示冷流道相关参数"
      if (type === "热转冷") return "同时显示热流道与冷流道参数"
      return "请选择流道类别以显示对应配置项"
    },
    showHotRunner() {
      return this.gating_system.runner_type === "热流道" || this.gating_system.runner_type === "热转冷"
    },
    showColdRunner() {
      return this.gating_system.runner_type === "冷流道" || this.gating_system.runner_type === "热转冷"
    },
  },
  watch: {
    gatingSystem: {
      handler: function() {
        this.gating_system = this.gatingSystem
      },
      deep: true,
      immediate: true
    }
  },
  methods: {
    isInputDisabled(prop) {
      switch (prop) {
        case "valve_actuation_type":
          return this.gating_system.hot_runner_system_type !== "针阀式"
        case "sequencing_control_method":
          return this.gating_system.has_sequencing_control !== true
        default:
          return false
      }
    },
    showGateShapeRect(gate) {
      return gate.gate_shape === "矩形"
    },
    showGateShapeCircle(gate) {
      return gate.gate_shape === "圆形"
    },
    showGateShapeAnnulus(gate) {
      return gate.gate_shape === "环形"
    },
    onAddCavityForm(tab) {
      if (tab.name === "add") {
        this.gating_system.cavities.push(structuredClone(cavityForm))
        this.active_cavity = String(this.gating_system.cavities.length - 1)
      }
    },
    onRemoveCavityForm(target_name) {
      this.gating_system.cavities.splice(Number(target_name), 1)
      this.active_cavity = String(this.gating_system.cavities.length - 1)
    },
    onAddGateForm(tab) {
      if (tab.name === "add") {
        this.gating_system.cavities[Number(this.active_cavity)].gates.push(structuredClone(gateForm))
        this.active_gate = String(this.gating_system.cavities[this.active_cavity].gates.length - 1)
      }
    },
    onRemoveGateForm(target_name) {
      this.gating_system.cavities[Number(this.active_cavity)].gates.splice(Number(target_name), 1)
      this.active_gate = String(this.gating_system.cavities[this.active_cavity].gates.length - 1)
    },
  }
}
</script>

<style lang="scss" scoped>

</style>