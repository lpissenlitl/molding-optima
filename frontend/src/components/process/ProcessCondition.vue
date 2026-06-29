<template>
  <div>
    <el-divider class="precondition-divider" content-position="center">
      <span>模具信息</span>
    </el-divider>

    <el-form
      ref="moldInfo"
      :inline="true"
      :model="condition"
      size="mini"
      label-width="10rem"
      :rules="mold_rules"
    >
      <el-form-item 
        label="模具编号" 
        prop="mold_info.mold_no" 
      >
        <el-autocomplete 
          v-model="mold_info.mold_no"
          clearable
          placeholder="请输入内容"
          :debounce="0"
          :fetch-suggestions="$querySuggestions({
            table: 'mold', 
            column: 'mold_no', 
            with_id: true
          })"
          :disabled="isMoldDisabled"
          @select="((item) => {mold_info.id = item.id})"
        >
        </el-autocomplete>
      </el-form-item>

      <el-form-item
        v-for="item, index in mold_form_items"
        :key="index"
        :label="item.label"
        :prop="`mold_info.${item.prop}`"
      >
        <el-input 
          v-model="mold_info[item.prop]"
          readonly
        ></el-input>
      </el-form-item>

      <el-form-item 
        v-if="mold_info.shot_count >= 1"
        label="注射次序" 
        prop="shot_index"
      >
        <el-select
          v-model="condition.shot_index"
          placeholder="请选择当前注射次数"
          :disabled="isMoldDisabled"
        >
          <el-option
            v-for="item, index in mold_info.shot_count"
            :key="item"
            :label="`第${item}次 注射`"
            :value="index"
          ></el-option>
        </el-select>
      </el-form-item>
    </el-form>
    
    <el-divider class="precondition-divider" content-position="center">
      <span>注塑机信息</span>
    </el-divider>

    <el-form
      ref="machineInfo"
      :inline="true"
      :model="condition"
      size="mini"
      label-width="10rem"
      :rules="machine_rules"
    >
      <el-form-item 
        label="注塑机品牌" 
        prop="machine_info.brand"
      >
        <el-autocomplete
          v-model="machine_info.brand"
          placeholder="请输入内容"
          clearable
          :debounce="0"
          :fetch-suggestions="$querySuggestions({
            table: 'injection_molding_machine', 
            column: 'brand'
          })"
          :disabled="isMachineDisabled"
        >
        </el-autocomplete>
      </el-form-item>

      <el-form-item 
        label="注塑机型号" 
        prop="machine_info.model"
      >
        <el-autocomplete
          v-model="machine_info.model"
          placeholder="注塑机型号"
          clearable
          :debounce="0"
          :fetch-suggestions="{ 
            table: 'injection_molding_machine', 
            column: 'model',
            with_id: true,
            sub_column: 'device_no',
            filter_columns: {
              'brand': machine_info.brand ? machine_info.brand : ''
            }
          }"
          :disabled="isMachineDisabled"
          @select="((item) => {machine_info.id = item.id})"
        >
        </el-autocomplete>
      </el-form-item>

      <el-form-item
        v-for="item, index in machine_form_items"
        :key="index"
        :label="item.label"
        :prop="`machine_info.${item.prop}`"
      >
        <el-input 
          v-model="machine_info[item.prop]"
          readonly
        ></el-input>
      </el-form-item>

      <el-form-item 
        v-if="machine_info.injection_units?.length >= 1"
        label="注射单元" 
        prop="injection_index"
      >
        <el-select
          v-model="condition.injection_index"
          placeholder="请选择当前注射次数"
          :disabled="isMachineDisabled"
        >
          <el-option
            v-for="item, index in machine_info.injection_units?.length"
            :key="item"
            :label="`注射单元 ${item}`"
            :value="index"
          ></el-option>
        </el-select>
      </el-form-item>
    </el-form>

    <el-divider class="precondition-divider" content-position="center">
      <span>材料信息</span>
    </el-divider>

    <el-form 
      ref="polymerInfo"
      size="mini" 
      label-width="10rem" 
      :model="polymer_info" 
      :inline="true"
      :rules="polymer_rules"
    >
      <el-form-item 
        label="塑料简称" 
        prop="abbreviation" 
      >
        <el-autocomplete
          v-model="polymer_info.abbreviation"
          placeholder="塑料简称"
          clearable
          :debounce="0"
          :fetch-suggestions="$querySuggestions({
            table: 'polymer', 
            column: 'abbreviation'
          })"
          :disabled="isPolymerDisabled"
        >
        </el-autocomplete>
      </el-form-item>

      <el-form-item 
        label="塑料牌号" 
        prop="grade"
      >
        <el-autocomplete
          v-model="polymer_info.grade"
          placeholder="塑料牌号"
          clearable
          :debounce="0"
          :fetch-suggestions="$querySuggestions({
            table: 'polymer',
            column: 'grade',
            with_id: true,
            filter_columns: {
              'abbreviation': polymer_info.abbreviation || ''
            }
          })"
          :disabled="isPolymerDisabled"
          @select="((item) => {polymer_info.id = item.id})"
        >
        </el-autocomplete>
      </el-form-item>

      <el-form-item
        v-for="item, idx in polymer_form_items"
        :key="idx"
        :label="item.label"
        :prop="item.prop"
      >
        <el-input
          v-model="polymer_info[item.prop]"
          readonly
        >
          <span slot="suffix" v-if="item.unit">{{ item.unit }}</span>
        </el-input>
      </el-form-item>
    </el-form>
  </div>
</template>

<script>
import { processConditionForm } from "@/constants/process-const"
import { moldMethod, machineMethod, polymerMethod } from "@/api"
import { createValidateAndFocus } from "@/utils/form-helper"

export default {
  name: "ProcessCondition",
  props: {
    processCondition: {
      type: Object,
      default: () => structuredClone(processConditionForm)
    },
    mode: {
      type: String,
      default: "add"  // add | edit | transplant
    }
  },
  data() {
    return {
      condition: this.processCondition,
      mold_rules: {
        "mold_info.mold_no": [
          { required: true, message: "请选择模具信息", trigger: "blur" }
        ],
        "shot_index": [
          { required: true, message: "请确定当前注射次序", trigger: "blur" }
        ],
      },
      machine_rules: {
        "machine_info.brand": [
          { required: true, message: "请选择注塑机品牌", trigger: "blur" }
        ],
        "machine_info.model": [
          { required: true, message: "请选择注塑机型号", trigger: "blur" }
        ],
        "injection_index": [
          { required: true, message: "请确定当前注射单元", trigger: "blur" }
        ],
      },
      polymer_rules: {
        "abbreviation": [
          { required: true, message: "请选择塑料简称", trigger: "blur" }
        ],
        "grade": [
          { required: true, message: "请选择塑料牌号", trigger: "blur" }
        ]
      },
      mold_form_items: [
        { label: "模具名称", prop: "mold_name", type: "text" },
        { label: "模具类型", prop: "mold_type", type: "text" },
        { label: "注射次数", prop: "shot_count", type: "text" },
        { label: "模腔布局", prop: "cavity_layout", type: "text" },
      ],
      machine_form_items: [
        { label: "注塑机编号", prop: "device_no", type: "text" },
        { label: "注塑机类型", prop: "machine_type", type: "text" },
        { label: "驱动系统", prop: "drive_system", type: "text" }
      ],
      polymer_form_items: [
        { label: "固态密度", prop: "solid_density", type: "number", unit: "g/cm³" },
        { label: "熔融密度", prop: "melt_density", type: "number", unit: "g/cm³" },
        { label: "推荐熔胶温度", prop: "recommended_melt_temp", type: "number", unit: "℃" },
        { label: "推荐模具温度", prop: "recommended_mold_temp", type: "number", unit: "℃" },
      ]
    }
  },
  computed: {
    mold_info() {
      return this.condition.mold_info
    },
    machine_info() {
      return this.condition.machine_info
    },
    polymer_info() {
      return this.condition.polymer_info
    },
    isMoldDisabled() {
      if (this.mode === "transplant") return true
      return this.condition.id !== null
    },
    isMachineDisabled() {
      if (this.mode === "transplant") return false
      return this.condition.id !== null
    },
    isPolymerDisabled() {
      if (this.mode === "transplant") return true
      return this.condition.id !== null
    }
  },
  watch: {
    processCondition: {
      handler: function() {
        this.condition = this.processCondition
      },
      deep: true,
      immediate: true
    },
    "condition.mold_info.id": function(val) {
      this.getMoldInfo(val)
    },
    "condition.machine_info.id": function(val) {
      this.getMachineInfo(val)
    },
    "condition.polymer_info.id": function(val) {
      this.getPolymerInfo(val)
    },
    "condition.shot_index": function(val) {
      this.condition.gating_system = this.condition.mold_info.gating_systems[val]
    },
    "condition.injection_index": function(val) {
      this.condition.injection_unit = this.condition.machine_info.injection_units[val]
    }
  },
  methods: {
    async getMoldInfo(id) {
      if (!id) return

      const res = await moldMethod.getDetail(id)
      if (res.status === 0) {
        Object.assign(this.condition.mold_info, res.data)
        if (this.condition.shot_index >= 0) {
          this.condition.gating_system = this.condition.mold_info.gating_systems[this.condition.shot_index]
        }
      } else {
        this.$message({ message: res.message, type: "error" })
      }
    },
    async getMachineInfo(id) {
      if (!id) return

      const res = await machineMethod.getDetail(id)
      if (res.status === 0) {
        Object.assign(this.condition.machine_info, res.data)
        if (this.condition.injection_index >= 0) {
          this.condition.injection_unit = this.condition.machine_info.injection_units[this.condition.injection_index]
        }
      } else {
        this.$message({ message: res.message, type: "error" })
      }
    },
    async getPolymerInfo(id) {
      if (!id) return

      const res = await polymerMethod.getDetail(id)
      if (res.status === 0) {
        Object.assign(this.condition.polymer_info, res.data)
      } else {
        this.$message({ message: res.message, type: "error" })
      }
    },
    async checkFormDataValid() { 
      const validate = createValidateAndFocus(this)

      const mold_access = await validate(this.$refs.moldInfo)
      if (!mold_access) return false

      const machine_access = await validate(this.$refs.machineInfo)
      if (!machine_access) return false

      const polymer_access = await validate(this.$refs.polymerInfo)
      if (!polymer_access) return false

      return true
    },
  }
}
</script>

<style lang="scss" scoped>

</style>
