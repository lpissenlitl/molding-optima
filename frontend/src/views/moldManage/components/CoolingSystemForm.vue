<template>
  <el-form
    ref="formData"
    size="mini"
    :inline="true"
    :model="cooling_system"
    label-width="8rem"
  > 
    <template 
      v-for="item, idx in form_items"
    >
      <el-divider 
        :key="`divider_${idx}`"
        v-if="item.type=='divider'" 
        content-position="center"
      >
        <span>{{ item.label }}</span>
      </el-divider>
      <el-form-item 
        v-else
        :key="`form_item_${idx}`"
        :label="item.label"
        :prop="item.prop"
      >
        <el-input
          v-if="item.type === 'input'"
          v-model="cooling_system[item.prop]"
          :placeholder="item.placeholder || `请输入${item.label}`"
        />
        <el-input
          v-else-if="item.type === 'number'"
          v-model="cooling_system[item.prop]"
          v-number
          :placeholder="item.placeholder || `请输入${item.label}`"
        >
          <span slot="suffix" v-if="item.unit">{{ item.unit }}</span>
        </el-input>
        <el-input
          v-else-if="item.type === 'integer'"
          v-model="cooling_system[item.prop]"
          v-number="0"
          :placeholder="item.placeholder || `请输入${item.label}`"
        >
          <span slot="suffix" v-if="item.unit">{{ item.unit }}</span>
        </el-input>
        <el-select 
          v-else-if="item.type === 'select'"
          v-model="cooling_system[item.prop]"
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
          v-model="cooling_system[item.prop]"
          v-number
          clearable
          filterable 
          allow-create
          @clear="() => cooling_system[item.prop] = null"
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
  </el-form>
</template>

<script>
import { coolingSystemForm, coolingTypeOptions, 
  coolingChannelDiameterOptions, coolingFittingTypeOptions } from "@/constants/mold-const"

export default {
  name: "CoolingSystemForm",
  props: {
    coolingSystem: {
      type: Object,
      default: () => (structuredClone(coolingSystemForm))
    }
  },
  data() {
    return { 
      cooling_system: this.coolingSystem,
      form_items: [
        { label: "前模（定模）", type: "divider" },
        { label: "型腔冷却类型", prop: "cooling_cavity_type", type: "select", options: coolingTypeOptions },
        { label: "冷却回路数量", prop: "cooling_cavity_circuit_count", type: "integer", unit: "组", placeholder: "型腔冷却回路数量" },
        // { label: "冷却布局", prop: "cooling_cavity_layout", type: "input" },
        { label: "冷却管道直径", prop: "cooling_cavity_pipe_diameter", type: "number-select", unit: "mm", options: coolingChannelDiameterOptions },
        { label: "水路接口类型", prop: "cooling_cavity_fitting_type", type: "select", options: coolingFittingTypeOptions },
        { label: "水路接口数量", prop: "cooling_cavity_fitting_count", type: "integer", unit: "个", placeholder: "型腔水路接口数量" },
        // { label: "冷却管连接器标签", prop: "cooling_cavity_fitting_labels", type: "input" },
        // { label: "水嘴密封方式", prop: "cooling_cavity_fitting_seal_method", type: "input" },
        { label: "后模（动模）", type: "divider" },
        { label: "型芯冷却类型", prop: "cooling_core_type", type: "select", options: coolingTypeOptions },
        { label: "冷却回路数量", prop: "cooling_core_circuit_count", type: "integer", unit: "组", placeholder: "型芯冷却回路数量" },
        // { label: "型芯冷却布局", prop: "cooling_core_layout", type: "input" },
        { label: "冷却管道直径", prop: "cooling_core_pipe_diameter", type: "number-select", unit: "mm", options: coolingChannelDiameterOptions },
        { label: "水路接口类型", prop: "cooling_core_fitting_type", type: "select", options: coolingFittingTypeOptions },
        { label: "水路接口数量", prop: "cooling_core_fitting_count", type: "integer", unit: "个", placeholder: "型芯水路接口数量" },
        // { label: "冷却管连接器标签", prop: "cooling_core_fitting_labels", type: "input" },
        // { label: "水嘴密封方式", prop: "cooling_core_fitting_seal_method", type: "input" },
      ],
    }
  },
  watch: {
    coolingSystem: {
      handler: function() {
        this.cooling_system = this.coolingSystem
      },
      deep: true,
      immediate: true
    }
  }
}
</script>

<style lang="scss" scoped>
</style>