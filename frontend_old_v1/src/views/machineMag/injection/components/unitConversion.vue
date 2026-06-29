<template>
  <div>
    <el-form
      size="mini"
      label-width="8rem"
      label-position="right"
      :model="form_info"
      :inline="true"
    >
      <el-form-item label="注塑机型号">
        <el-input v-model="mac_trademark" readonly></el-input>
      </el-form-item>
      <el-form-item label="螺杆直径">
        <el-input v-model="injectors_info.screw_diameter" readonly></el-input>
      </el-form-item>
      <br />
      <el-form-item label="转换类型">
        <el-select v-model="form_info.unit_type" clearable default-first-option>
          <el-option label="压力" value="压力"></el-option>
          <el-option label="速度" value="速度"></el-option>
          <el-option label="位置" value="位置"></el-option>
        </el-select>
      </el-form-item>
      <br />
      <el-form-item label="" style="margin-left: 20px">
        <el-input
          v-model="form_info.original_value"
          placeholder="请输入数值"
          clearable
          default-first-option
        ></el-input>
        <el-select
          v-model="form_info.original_unit"
          clearable
          default-first-option
          style="width: 7rem"
        >
          <el-option
            v-for="item in unitList"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          >
          </el-option>
        </el-select>
        <span>&nbsp;⇆&nbsp;</span>
        <el-input
          readonly
          clearable
          default-first-option
          v-model="form_info.transform_value"
        ></el-input>
        <el-select
          v-model="form_info.transform_unit"
          clearable
          default-first-option
          style="width: 7rem"
        >
          <el-option
            v-for="item in unitList"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          >
          </el-option>
        </el-select>
      </el-form-item>
    </el-form>
  </div>
</template>

<script>
import * as unit_change from "@/utils/unit-change";
export default {
  name: "UnitConversion",
  props: {
    macTrademark: null,
    injectorInfo: {
      type: Object,
      default: () => {},
    },
  },
  data() {
    return {
      mac_trademark: this.macTrademark,
      injectors_info: this.injectorInfo,
      form_info: {
        unit_type: null,
        original_value: null,
        original_unit: null,
        transform_value: null,
        transform_unit: null,
      },
      unitList: null,
    };
  },
  methods: {},
  watch: {
    macTrademark() {
      this.mac_trademark = this.macTrademark;
    },
    injectorInfo: {
      handler() {
        this.injectors_info = this.injectorInfo;
      },
      deep: true,
    },
    "form_info.unit_type": function () {
      this.form_info.original_value = null;
      this.form_info.original_unit = null;
      this.form_info.transform_value = null;
      this.form_info.transform_unit = null;
      if (this.form_info.unit_type == "压力") {
        this.unitList = [
          { value: "MPa", label: "MPa" },
          { value: "kgf/cm²", label: "kgf/cm²" },
          { value: "bar", label: "bar" },
          { value: "PSI", label: "PSI" },
        ];
      } else if (this.form_info.unit_type == "速度") {
        this.unitList = [
          { value: "mm/s", label: "mm/s" },
          { value: "inch/s", label: "inch/s" },
          { value: "cm³/s", label: "cm³/s" },
          { value: "inch³/s", label: "inch³/s" },
        ];
      } else if (this.form_info.unit_type == "位置") {
        this.unitList = [
          { value: "mm", label: "mm" },
          { value: "inch", label: "inch" },
          { value: "cm³", label: "cm³" },
          { value: "inch³", label: "inch³" },
        ];
      } else {
        this.unitList = [];
      }
    },
    form_info: {
      handler() {
        if ( this.form_info.unit_type && this.form_info.original_value && this.form_info.original_unit && this.form_info.transform_unit ) {
          this.form_info.transform_value = unit_change.conversion(
            this.form_info.original_unit,
            this.form_info.transform_unit,
            this.form_info.original_value,
            this.injectors_info
          );
          if (!this.form_info.transform_value) {
            this.$message({ message: "没有合适的转换!", type: "warning"});
          }
        }
      },
      deep: true,
      immediate: true,
    },
  },
};
</script>

<style scoped>
.el-input {
  width: 8rem;
}
.el-select {
  width: 6rem;
}
</style>