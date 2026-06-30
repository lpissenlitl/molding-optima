<template>
  <el-form
    ref="formData"
    size="mini"
    :inline="true"
    :model="ejection_system"
    label-width="8rem"
  >
    <el-form-item 
      v-for="item, idx in ejection_form_items"
      :key="item.prop+String(idx)"
      :label="item.label"
      :prop="item.prop"
    >
      <el-input
        v-if="item.type === 'text'"
        v-model="ejection_system[item.prop]"
        :placeholder="item.placeholder || `请输入${item.label}`"
      />
      <el-input
        v-else-if="item.type === 'number'"
        v-model="ejection_system[item.prop]"
        v-number
        :placeholder="item.placeholder || `请输入${item.label}`"
      >
        <span slot="suffix" v-if="item.unit">{{ item.unit }}</span>
      </el-input>
      <el-input
        v-else-if="item.type === 'integer'"
        v-model="ejection_system[item.prop]"
        v-number="0"
        :placeholder="item.placeholder || `请输入${item.label}`"
      >
        <span slot="suffix" v-if="item.unit">{{ item.unit }}</span>
      </el-input>
      <el-select 
        v-else-if="item.type === 'select'"
        v-model="ejection_system[item.prop]"
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
      <el-radio-group 
        v-else-if="item.prop === 'has_pre_ejection'"
        v-model="ejection_system.has_pre_ejection"
      >
        <el-radio-button :label="true">
          是
        </el-radio-button>
        <el-radio-button :label="false">
          否
        </el-radio-button>
      </el-radio-group>
    </el-form-item>
  </el-form>
</template>

<script>
import { ejectionSystemForm, ejectionTypeOptions, resetMethodOptions } from "@/constants/mold-const"

export default {
  name : "EjectionSystemForm",
  props: {
    ejectionSystem: {
      type: Object,
      default: () => (structuredClone(ejectionSystemForm))
    }
  },
  data() { 
    return { 
      ejection_system: this.ejectionSystem,
      ejection_form_items:  [
        { label: "顶出类型", prop: "ejection_type", type: "select", options: ejectionTypeOptions },
        { label: "复位方式", prop: "reset_method", type: "select", options: resetMethodOptions },
        // { label: "顶棍孔类型", prop: "ejector_rod_hole_type", type: "text" },
        { label: "顶棍孔直径", prop: "ejector_rod_hole_diameter", type: "number", unit: "mm" },
        // { label: "顶棍孔深度", prop: "ejector_rod_hole_depth", type: "number", unit: "mm" },
        { label: "顶棍孔X向间距", prop: "ejector_rod_hole_spacing_x", type: "number", unit: "mm", placeholder: "顶棍孔X向间距" },
        { label: "顶棍孔Y向间距", prop: "ejector_rod_hole_spacing_y", type: "number", unit: "mm", placeholder: "顶棍孔Y向间距" },
        { label: "顶出行程", prop: "ejection_stroke", type: "number", unit: "mm" },
        // { label: "是否有预顶出", prop: "has_pre_ejection", type: "radio" },
        // { label: "预顶出行程", prop: "pre_ejection_stroke", type: "integer", unit: "mm" },
        // { label: "推荐顶出力", prop: "estimated_ejection_force", type: "integer", unit: "kN" },
      ]
    }
  },
  watch: { 
    ejectionSystem: {
      handler: function() {
        this.ejection_system = this.ejectionSystem
      },
      deep: true,
      immediate: true
    }
  },
}
</script>

<style lang="scss" scoped>

</style>