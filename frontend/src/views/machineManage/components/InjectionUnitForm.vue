<template>
  <el-form 
    ref="formData" 
    size="mini" 
    label-width="10rem" 
    label-position="right"
    :model="injection_unit" 
    :rules="rules"
    :inline="true"
  >
    <el-alert
      title="射台标识说明：当注塑机配备多个注射单元时，请为每个射台分配唯一编号，以便在工艺参数、模具配置和生产记录中准确区分各注射单元。"
      type="info"
      show-icon
      :closable="false"
      style="margin-bottom: 10px;"
    />

    <template v-for="(item, index) in unit_form_items">
      <el-divider 
        v-if="item.type=='divider'" 
        :key="`divider_${index}`"
        content-position="center"
      >
        {{ item.label }}
      </el-divider>
          
      <el-form-item 
        v-else 
        :key="`form_item_${index}`"
        :label="item.label" 
        :prop="item.prop"
      >
        <el-input 
          v-if="item.type=='input'"
          v-model="injection_unit[item.prop]"
          :placeholder="item.placeholder || `请输入${item.label}`"
        >
          <span slot="suffix" v-if="item.unit">{{ item.unit }}</span>
          <span slot="suffix" v-else-if="item.dynamic_unit"> {{ injection_unit[item.dynamic_unit] }} </span>
        </el-input>

        <el-input 
          v-if="item.type=='number'"
          v-model="injection_unit[item.prop]"
          v-number="item.fixed || 2"
          :placeholder="item.placeholder || `请输入${item.label}`"
        >
          <span slot="suffix" v-if="item.unit">{{ item.unit }}</span>
        </el-input>

        <el-select
          v-else-if="item.type === 'select'"
          v-model="injection_unit[item.prop]"
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
        
        <el-select
          v-else-if="item.type === 'number-select'"
          v-model="injection_unit[item.prop]"
          v-number="item.fixed"
          clearable
          filterable 
          allow-create
          @clear="() => injection_unit[item.prop] = null"
        >
          <el-option
            v-for="(option, opt_idx) in item.options"
            :key="opt_idx"
            :label="option.label"
            :value="option.value"
          />
        </el-select>
            
        <el-autocomplete
          v-if="item.type=='autocomplete'"
          v-model.trim="injection_unit[item.prop]" 
          :placeholder="item.placeholder || '请输入内容'"
          clearable
          @clear="query[item.prop]=null"
          :debounce="0"
          :fetch-suggestions="$querySuggestions({
            table: item.table,
            column: item.column,
          })"
        > 
        </el-autocomplete>
            
        <el-date-picker
          v-else-if="item.type=='date'"
          v-model="injection_unit[item.prop]"
          type="date"
          placeholder="选择日期"
          value-format="yyyy-MM-dd"
        ></el-date-picker>
      </el-form-item>
    </template>
  </el-form>
</template>

<script>
import * as machine_const from "@/constants/machine-const"
import { createValidateAndFocus } from "@/utils/form-helper"

export default {
  name: "InjectionUnitForm",
  props: {
    injectionUnit: {
      type: Object,
      default: () => { return structuredClone(machine_const.injectionUnitForm) }
    }
  },
  data() {
    return {
      injection_unit: this.injectionUnit,
      unit_form_items: [
        // --- 射台标识 ---
        { label: "射台编号", prop: "unit_code", type: "input", placeholder: "射台标识（内部识别）" },

        // --- 喷嘴参数 ---
        { label: "喷嘴参数", type: "divider" },
        { label: "喷嘴类型", prop: "nozzle_type", type: "select", options: machine_const.nozzleTypeOptions },
        { label: "喷嘴伸出量", prop: "nozzle_protrusion", type: "number", unit: "mm", fixed: 2, placeholder: "常见默认值：15mm / 20mm" },
        { label: "喷嘴孔直径", prop: "nozzle_hole_diameter", type: "number-select", unit: "mm", fixed: 2, options: machine_const.nozzleHoleDiameterOptions },
        { label: "喷嘴球半径", prop: "nozzle_sphere_radius", type: "number-select", unit: "mm", fixed: 2, options: machine_const.nozzleSphereRadiusOptions },
        { label: "喷嘴接触力", prop: "nozzle_contact_force", type: "number", unit: "kN", fixed: 2 },

        // --- 螺杆参数 ---
        { label: "螺杆参数", type: "divider" },
        { label: "螺杆类型", prop: "screw_type", type: "select", options: machine_const.screwTypeOptions },
        { label: "螺杆直径", prop: "screw_diameter", type: "number", unit: "mm", fixed: 2, placeholder: "螺杆横截面积 mm² / 周长 mm" },
        { label: "长径比L/D", prop: "screw_length_to_diameter_ratio", type: "number", fixed: 2 },
        { label: "压缩比", prop: "screw_compression_ratio", type: "number", fixed: 2 },
        { label: "增强比", prop: "screw_enhancement_ratio", type: "number", fixed: 2 },

        // --- 塑化与注射能力 ---
        { label: "塑化与注射能力", type: "divider" },
        { label: "塑化能力", prop: "plasticizing_capacity", type: "number", unit: "g/h", fixed: 2 },
        { label: "最大注射行程", prop: "max_injection_stroke", type: "number", unit: "mm", fixed: 2 },
        { label: "最大注射体积", prop: "max_injection_volume", type: "number", unit: "cm³", fixed: 2 },
        { label: "最大注射重量", prop: "max_injection_weight", type: "number", unit: "g", fixed: 2 },
        { label: "料筒加热功率", prop: "barrel_heating_power", type: "number", unit: "kW", fixed: 2 },

        // --- 界面单位信息（射台级覆盖）---
        { label: "界面单位信息", type: "divider" },
        { label: "压力单位", prop: "pressure_unit", type: "select", options: machine_const.pressureUnitOptions },
        { label: "速度单位", prop: "speed_unit", type: "select", options: machine_const.speedUnitOptions },
        { label: "位置单位", prop: "position_unit", type: "select", options: machine_const.positionUnitOptions },
        { label: "时间单位", prop: "time_unit", type: "select", options: machine_const.timeUnitOptions },
        { label: "背压单位", prop: "back_pressure_unit", type: "select", options: machine_const.pressureUnitOptions },
        { label: "螺杆转速单位", prop: "screw_rotation_unit", type: "select", options: machine_const.screwRotationUnitOptions },
        { label: "温度单位", prop: "temperature_unit", type: "select", options: machine_const.temperatureUnitOptions },

        // --- 控制系统能力（最大段数） ---
        { label: "控制系统能力（最大段数）", type: "divider" },
        { label: "最大注射段数", prop: "max_injection_stages", type: "number-select", fixed: 0, options: machine_const.maxInjectionStagesOptions },
        { label: "最大保压段数", prop: "max_holding_stages", type: "number-select", fixed: 0, options: machine_const.maxHoldingStagesOptions },
        { label: "最大计量段数", prop: "max_metering_stages", type: "number-select", fixed: 0, options: machine_const.maxMeteringStagesOptions },
        { label: "最大温控区域", prop: "max_temperature_control_zones", type: "number-select", fixed: 0, options: machine_const.maxTempZonesOptions },
        
        // --- 成型能力（设备极限）---
        { label: "成型能力（设备极限）", type: "divider" },
        { label: "最大注射压力", prop: "max_injection_pressure", type: "number", unit: "MPa", fixed: 2, placeholder: "标准值" },
        { label: "最大注射速度", prop: "max_injection_speed", type: "number", unit: "mm/s", fixed: 2, placeholder: "标准值" },
        { label: "最大保压压力", prop: "max_holding_pressure", type: "number", unit: "MPa", fixed: 2, placeholder: "标准值" },
        { label: "最大保压速度", prop: "max_holding_speed", type: "number", unit: "mm/s", fixed: 2, placeholder: "标准值" },
        { label: "最大计量压力", prop: "max_metering_pressure", type: "number", unit: "MPa", fixed: 2, placeholder: "标准值（全电机无）" },
        { label: "最大螺杆转速", prop: "max_screw_rotation_speed", type: "number", unit: "rpm", fixed: 2, placeholder: "标准值" },
        { label: "最大计量背压", prop: "max_metering_back_pressure", type: "number", unit: "MPa", fixed: 2, placeholder: "标准值" },
        { label: "最大松退压力", prop: "max_decompression_pressure", type: "number", unit: "MPa", fixed: 2, placeholder: "标准值" },
        { label: "最大松退速度", prop: "max_decompression_speed", type: "number", unit: "mm/s", fixed: 2, placeholder: "标准值" },

        // --- HMI 可设定范围（界面限制）---
        { label: "HMI 可设定范围（界面限制）", type: "divider" },
        { label: "最大可设定注射压力", prop: "max_set_injection_pressure", type: "number", dynamic_unit: "pressure_unit", fixed: 2, placeholder: "界面值" },
        { label: "最大可设定注射速度", prop: "max_set_injection_speed", type: "number", dynamic_unit: "speed_unit", fixed: 2, placeholder: "界面值" },
        { label: "最大可设定保压压力", prop: "max_set_holding_pressure", type: "number", dynamic_unit: "pressure_unit", fixed: 2, placeholder: "界面值" },
        { label: "最大可设定保压速度", prop: "max_set_holding_speed", type: "number", dynamic_unit: "speed_unit", fixed: 2, placeholder: "界面值" },
        { label: "最大可设定计量压力", prop: "max_set_metering_pressure", type: "number", dynamic_unit: "pressure_unit", fixed: 2, placeholder: "界面值（全电机无）" },
        { label: "最大可设定螺杆转速", prop: "max_set_screw_rotation_speed", type: "number", dynamic_unit: "screw_rotation_unit", fixed: 2, placeholder: "界面值" },
        { label: "最大可设定计量背压", prop: "max_set_metering_back_pressure", type: "number", dynamic_unit: "back_pressure_unit", fixed: 2, placeholder: "界面值" },
        { label: "最大可设定松退压力", prop: "max_set_decompression_pressure", type: "number", dynamic_unit: "pressure_unit", fixed: 2, placeholder: "界面值" },
        { label: "最大可设定松退速度", prop: "max_set_decompression_speed", type: "number", dynamic_unit: "speed_unit", fixed: 2, placeholder: "界面值" }
      ],
      rules: {
        unit_code: [
          { required: true, message: "射台编号不能为空!" }
        ],
        nozzle_type: [
          { required: true, message: "喷嘴类型不能为空!" }
        ],
      },
    }
  },
  watch: {
    injectionUnit: {
      handler() {
        this.injection_unit = this.injectionUnit
      },
      deep: true,
      immediated: true
    }
  },
  mounted() {

  },
  methods: {
    async checkFormDataValid() { 
      const validate = createValidateAndFocus(this)

      const access = await validate(this.$refs.formData)
      if (!access) return false
      return true
    },
  }
}
</script>

<style lang="scss" scoped>

</style>
