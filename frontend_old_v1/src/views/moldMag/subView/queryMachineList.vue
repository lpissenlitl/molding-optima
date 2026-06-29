<template>
  <div class="search">
    <el-form :inline="true" :model="query" size="mini" label-width="9.5rem">
      <el-form-item label="注塑机来源">
        <el-autocomplete
          v-model="query.data_source"
          placeholder="注塑机来源"
          clearable
          style="width: 10rem"
          :fetch-suggestions="
            (str, cb) => {
              querySuggestionOptions(str, cb, 'data_source');
            }
          "
        >
        </el-autocomplete>
      </el-form-item>

      <el-form-item 
        label="注塑机品牌"
        prop="manufacturer"
      >
        <el-autocomplete
          v-model="query.manufacturer"
          placeholder="注塑机品牌"
          clearable
          style="width: 10rem"
          :fetch-suggestions="queryManufacturerOptions"
        >
        </el-autocomplete>
      </el-form-item>

      <el-form-item label="注塑机型号">
        <el-autocomplete
          v-model="query.trademark"
          placeholder="注塑机型号"
          clearable
          style="width: 10rem"
          :fetch-suggestions="queryMacTrademarkOptions"
        >
        </el-autocomplete>
      </el-form-item>

      <el-form-item label="注塑机类型(射台数)">
        <el-select v-model="query.machine_type">
          <el-option 
            v-for="item in machineTypeOptions"
            :key="item.value"
            :label="item.label"
            :value="item.label"
          >
          </el-option>
        </el-select>
      </el-form-item>

      <el-form-item label="注塑机类型(驱动方式)">
        <el-select v-model="query.power_method">
          <el-option label="电动机" value="电动机"></el-option>
          <el-option label="液压机" value="液压机"></el-option>
        </el-select>
      </el-form-item>

      <el-form-item label="注塑机类型(推进轴线)">
        <el-select v-model="query.propulsion_axis">
          <el-option label="卧式" value="卧式"></el-option>
          <el-option label="立式" value="立式"></el-option>
          <el-option label="角式" value="角式"></el-option>
        </el-select>
      </el-form-item>

      <!-- <el-form-item label="最小容模尺寸(横)">
        <el-input v-model="query.min_mold_size_horizon">
          <span slot="suffix">mm</span>
        </el-input>
      </el-form-item>

      <el-form-item label="最小容模尺寸(竖)">
        <el-input v-model="query.min_mold_size_vertical">
          <span slot="suffix">mm</span>
        </el-input>
      </el-form-item>

      <el-form-item label="最小容模厚度">
        <el-input v-model="query.min_mold_thickness">
          <span slot="suffix">mm</span>
        </el-input>
      </el-form-item>

      <el-form-item label="最小开模行程">
        <el-input v-model="query.min_mold_open_stroke">
          <span slot="suffix">mm</span>
        </el-input>
      </el-form-item>

      <el-form-item label="最小锁模力">
        <el-input v-model="query.min_clamping_force">
          <span slot="suffix">mm</span>
        </el-input>
      </el-form-item> -->

      <el-form-item style="float:right">
        <el-button
          type="primary"
          style="width: 6rem; margin-left:10px"
          @click="queryListData(true)"
        >
          搜索
        </el-button>
        <el-button 
          type="danger" 
          style="width: 6rem"
          @click="reloadListData" 
        >
          重置
        </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script>
import { machineManufacturerOptions } from "@/utils/machine-const"
import { getOptions, machineMethod } from "@/api";
import suggestionOptions from "@/mixins/suggestionOptions.vue";

export default {
  name: "QueryMachineList",
  mixins: [suggestionOptions],
  props: {
    queryDetail: {
      type: Object,
      default: () => ({}),
    },
  },
  data() {
    return {
      query: this.queryDetail,
      machineManuOptions: machineManufacturerOptions,
      listData: {
        items: [],
        total: 0
      },
      machineTypeOptions: [
        { value: "1", label: "单色注塑机" },
        { value: "2", label: "双色注塑机" },
        { value: "3", label: "三色注塑机" },
        { value: "4", label: "四色注塑机" },
        { value: "5", label: "五色注塑机" },
        { value: "6", label: "六色注塑机" },
        { value: "7", label: "七色注塑机" }
      ],
    };
  },
  created() {},
  methods: {
    querySuggestionOptions(input, cb, column) {
      if (["data_source"].includes(column)) {
        cb(this.queryOptions(input, column, "machine"))
      } else if (["min_mold_size_horizon", "min_mold_size_vertical", "min_mold_thickness",
      "max_mold_open_stroke", "max_clamping_force"].includes(column)) {
        cb(this.queryOptions(input, column, "machine"))
      }
    },
    queryManufacturerOptions(queryString, cb) {
      queryString = queryString == null ? "" : queryString

      let promptList = []
      getOptions("manufacturer", {
        "data_source": this.query.data_source,
      }).then(res => {
        if (res.status === 0) {
          for (let i = 0; i < res.data.length; i++) {
            promptList.push({
              value: res.data[i]
            })
          }
          cb(promptList)
        }
      })
    },
    queryMacTrademarkOptions(queryString, cb) {
      queryString = queryString == null ? "" : queryString

      let promptList = []
      getOptions("machine_trademark", {
        "data_source": this.query.data_source,
        "trademark": queryString,
        "manufacturer": this.query.manufacturer,
      }).then(res => {
        if (res.status == 0) {
          for (let i =0; i < res.data.length; i++) {
            promptList.push({
              id: res.data[i].id,
              value: res.data[i].trademark,
            })
          }
          cb(promptList)
        }
      })
    },
    queryListData(reset=false) {
      if(reset){
        this.query.page_no = 1
      }
      this.$emit("queryStart")
      machineMethod.get(this.query)
      .then((res) => {
        if (res.status === 0) {
          this.listData = Object.assign({}, res.data)
        }
      })
      .finally(() => {
        this.$emit("queryFinish", this.listData)
      })
    },
    reloadListData() {
      this.query.data_source = null
      this.query.trademark = null
      this.query.manufacturer = null
      this.query.machine_type = null
      this.query.power_method = null
      this.query.propulsion_axis = null
      this.queryListData(true)
    }
  },
  watch:{
    "queryDetail": {
      handler: function(){
        this.query= this.queryDetail
        if(this.query.min_mold_size_horizon || this.query.min_mold_size_vertical || this.query.min_mold_thickness || this.query.min_mold_open_stroke || this.query.min_clamping_force){
          this.queryListData()
        }
      },
      deep: true,
      immediate:true
    }
  }
};
</script>

<style lang="scss" scoped>
.el-input {
  width: 10rem;
}
.el-select {
  width: 10rem
}
</style>>