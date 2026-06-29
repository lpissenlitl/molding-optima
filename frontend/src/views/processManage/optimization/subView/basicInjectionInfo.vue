<template>
  <el-form
    ref="detail_info"
    :inline="true"
    :model="detail_info"
    size="mini"
    label-width="10rem"
  >
    <el-divider class="precondition-divider" content-position="center">
      <span>注塑机</span>
    </el-divider>
    <el-form-item 
      label="注塑机品牌" 
      prop="manufacturer"
    >
      <el-autocomplete
        v-model="detail_info.manufacturer"
        placeholder="请输入内容"
        clearable
        :debounce="0"
        :fetch-suggestions="((str, cb)=>{querySuggestionOptions(str, cb, 'manufacturer')})"
        @select="detail_info.trademark = null, detail_info.serial_no = null"
      >
      </el-autocomplete>
    </el-form-item>
    <el-form-item 
      label="注塑机型号" 
      prop="trademark"
    >
      <el-autocomplete
        v-model="detail_info.trademark"
        placeholder="请输入内容"
        clearable
        :debounce="0"
        :fetch-suggestions="((str, cb)=>{querySuggestionOptions(str, cb, 'trademark')})"
        @select="detail_info.serial_no = null"
      >
      </el-autocomplete>
    </el-form-item>
    <el-form-item
      label="注塑机编号"
      prop="serial_no"
    >
      <el-autocomplete
        v-model="detail_info.serial_no"
        placeholder="请输入内容"
        clearable
        :debounce="0"
        :fetch-suggestions="((str, cb)=>{querySuggestionOptions(str, cb, 'serial_no')})"
        @select="onMachineSelected"
      >
      </el-autocomplete>
    </el-form-item>
    <el-form-item 
      label="注塑机位置" 
      prop="data_source"
    >
      <!-- <el-autocomplete
        v-model="detail_info.data_source"
        placeholder="请输入内容"
        clearable
        :debounce="0"
        :fetch-suggestions="((str, cb)=>{querySuggestionOptions(str, cb, 'data_source')})"
      >
      </el-autocomplete> -->
      <el-input
        v-model="detail_info.data_source"
        readonly
      >
      </el-input>
    </el-form-item>
    <el-form-item
      label="注塑机类型"
      prop="machine_type"
    >
      <el-input
        v-model="detail_info.machine_type"
        readonly
      >
      </el-input>
    </el-form-item>
    <el-form-item 
      label="驱动方式" 
      prop="drive_system"
    >
      <el-input
        v-model="detail_info.drive_system"
        readonly
      >
      </el-input>
    </el-form-item>
    <!-- <el-form-item 
      label="推进轴线" 
      prop="propulsion_axis"
    >
      <el-input
        v-model="detail_info.propulsion_axis"
        readonly
      >
      </el-input>
    </el-form-item> -->
  </el-form>
</template>

<script>
import SuggestionOptions from "@/mixins/suggestionOptions.vue";

export default {
  name: "BasicInjectionInfo",
  mixins: [ SuggestionOptions ],
  props: {
    basicInjectionInfo: {
      type: Object,
      default: () => ({})
    }
  },
  data() {
    return {
      detail_info: this.basicInjectionInfo,
    }
  },
  methods: {
    async querySuggestionOptions(input_str, cb, db_column) {
      let selections = [];
      if ("data_source" == db_column) {
        selections = await this.queryOptions(input_str, "machine", "data_source");
      } else if ("manufacturer" == db_column) {
        selections = await this.queryOptions(input_str, "machine", "manufacturer");
      } else if ("trademark" == db_column) {
        selections = await this.queryOptions(input_str, "machine", "trademark", {
          "manufacturer": this.detail_info.manufacturer
        });
      } else if ("serial_no" == db_column) {
        selections = await this.queryOptions(input_str, "machine", "serial_no", {
          "manufacturer": this.detail_info.manufacturer,
          "trademark": this.detail_info.trademark
        });
      }
      cb(selections);
    },
    onMachineSelected(item) {
      this.detail_info.id = item.id;
    },
  },
  watch: {
    basicInjectionInfo: {
      handler: function() {
        this.detail_info = this.basicInjectionInfo;
      },
      deep: true
    }
  }
}
</script>

<style lang="scss" scoped>
  .el-input,
  .el-select,
  .el-autocomplete {
    width: 10rem;
  }
</style>