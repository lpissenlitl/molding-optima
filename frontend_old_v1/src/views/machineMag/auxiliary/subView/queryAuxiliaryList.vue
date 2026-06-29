<template>
  <div class="search">
    <el-form
      :inline="true"
      :model="query"
      size="mini"
      label-width="8rem"
    >
      <el-form-item label="辅机类型">
        <el-select 
          v-model="query.auxiliary_type" 
          style="width: 10rem"
          placeholder="请选择"
          filterable
          allow-create
          default-first-option
          clearable
        >
          <el-option
            v-for="item in AuxiliaryTypeOptions"
            :key="item.value"
            :label="item.label"
            :value="item.label"
          >
          </el-option>
        </el-select>
      </el-form-item>

      <el-form-item label="设备编码">
        <el-input 
          style="width:10rem" 
          v-model="query.serial_num"
        >
        </el-input>
      </el-form-item>
        
      <el-form-item style="float:right">
        <el-button
          type="primary"
          @click="queryListData(true)"
          style="width: 6rem; margin-left:10px"
        >
          搜索
        </el-button>
        <el-button
          type="danger"
          @click="reloadListData"
          style="width: 6rem"
        >
          重置
        </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script>
import { machineManufacturerOptions } from "@/utils/machine-const";
import { getOptions, auxiliaryMethod } from "@/api";

export default {
  name: "QueryAuxiliaryList",
  props: {
    queryDetail: {
      type: Object,
      default: () => ({
        auxiliary_type: "",
        serial_no: "",
      })
    }
  },
  data() {
    return {
      query: this.queryDetail,
      mac_data_source_list: [],
      mac_trademark_list: [],
      machineManuOptions: machineManufacturerOptions,
      listData: {
        items: [],
        total: 0
      },
      AuxiliaryTypeOptions: [
        {value:'0',label:'干燥机'},
        {value:'1',label:'热流道'},
        {value:'2',label:'模温机'},
        {value:'3',label:'色母机'},
      ],
    }
  },
  created() {

  },
  methods: {
    queryListData(reset=false) {
      if(reset){
        this.query.page_no = 1
      }
      this.$emit("queryStart")
      auxiliaryMethod.get(this.query)
      .then((res) => {
        if (res.status === 0) {
          this.listData = Object.assign({}, res.data)
        }
      })
      .finally( () => {
        this.$emit("queryFinish", this.listData)
      })
    },
    reloadListData() {
      this.query.auxiliary_type = null
      this.query.serial_no = null

      this.queryListData(true)
    }
  }
}
</script>

<style lang="scss" scoped>
  .el-autocomplete {
    width: 10rem;
  }
</style>
