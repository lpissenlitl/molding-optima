<template>
  <div class="search">
    <el-form
      :inline="true"
      :model="query"
      size="mini"
      label-width="6rem"
    >
      <el-form-item label="工艺编号">
        <el-autocomplete
          v-model="query.process_no" 
          :fetch-suggestions="queryProcessNo"
          placeholder="请输入内容"
          suffix-icon="el-icon-search"
        > 
        </el-autocomplete>
      </el-form-item>
      <el-form-item label="制品名称">
        <el-autocomplete
          v-model="query.product_name" 
          :fetch-suggestions="queryProductName"
          placeholder="请输入内容"
          suffix-icon="el-icon-search"
        > 
        </el-autocomplete>
      </el-form-item>
      <el-form-item label="制品大类">
        <el-autocomplete
          v-model="query.product_catalog" 
          :fetch-suggestions="queryProduCatelog"
          placeholder="请输入内容"
          suffix-icon="el-icon-search"
        > 
        </el-autocomplete>
      </el-form-item>
      <el-form-item label="制品类别">
        <el-autocomplete
          v-model="query.product_type" 
          :fetch-suggestions="queryProductType"
          placeholder="请输入内容"
          suffix-icon="el-icon-search"
        > 
        </el-autocomplete>
      </el-form-item>
      <el-form-item label="注塑机来源">
        <el-autocomplete
          v-model="query.machine_data_source" 
          :fetch-suggestions="queryMachineDataSource"
          placeholder="请输入内容"
          @select="handleDataSourceSelect"
          suffix-icon="el-icon-search"
        > 
        </el-autocomplete>
      </el-form-item>
      <el-form-item label="注塑机型号">
        <el-autocomplete
          v-model="query.machine_trademark" 
          :fetch-suggestions="queryMachineTrademark"
          placeholder="请输入内容"
          suffix-icon="el-icon-search"
        > 
        </el-autocomplete>
      </el-form-item>
      <el-form-item label="材料类型" prop="polymer_abbreviation">
        <el-autocomplete
          v-model="query.polymer_abbreviation" 
          :fetch-suggestions="queryPolymerAbbreviation"
          placeholder="请输入内容"
          suffix-icon="el-icon-search"
        > 
        </el-autocomplete>
      </el-form-item>
      <el-form-item label="塑料牌号">
        <el-autocomplete
          v-model="query.polymer_trademark" 
          :fetch-suggestions="queryPolymerTrademark"
          placeholder="请输入内容"
          suffix-icon="el-icon-search"
        > 
        </el-autocomplete>
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
import { processMethod, getOptions } from "@/api";
import { UserModule } from '@/store/modules/user';
import machine from '@/components/search/machine';

export default {
  comments: { machine },
  name: "QueryProductsList",
  props: {
    queryDetail: {
      type: Object,
      default: () => ({
        process_no: null,
        product_name: null,
        product_catalog: null,
        product_type: null,
        machine_data_source: null,
        machine_trademark: null,
        polymer_abbreviation: null,
        polymer_trademark: null,
        company_id: UserModule.company_id,
      })
    }
  },
  data() {
    return {
      query: this.queryDetail,
      listData: {},
    }
  },
  methods: {
    queryOptions(str, column) {
      str = str == null ? "" : str 
      let promptList = []
      if (column) {
        getOptions(column, { "form_input": str, "db_table": "process" })
        .then( res => {
          if(res.status == 0) {
            for(let i = 0; i < res.data.length; i++) {
              promptList.push({ value: res.data[i] })
            }
          }
        })
      } 
      return promptList
    },
    queryProductName(str, cb) {
      let results = this.queryOptions(str, "process_product_name")
      cb(results)
    },
    queryProcessNo(str, cb) {
      let results = this.queryOptions(str, "process_no")
      cb(results)
    },
    queryProduCatelog(str, cb) {
      let results = this.queryOptions(str, "process_product_catalog")
      cb(results)
    },
    queryProductType(str, cb) {
      let results = this.queryOptions(str, "process_product_type")
      cb(results)
    },
    queryMachineDataSource(str, cb) {
      let results = this.queryOptions(str, "process_machine_data_source")
      cb(results)
    },
    queryMachineTrademark(str, cb) {
      let results = this.queryOptions(str, "process_machine_trademark")
      cb(results)
    },
    queryPolymerAbbreviation(str, cb) {
      let results = this.queryOptions(str, "process_polymer_abbreviation")
      cb(results)
    },
    queryPolymerTrademark(str, cb) {
      let results = this.queryOptions(str, "process_polymer_trademark")
      cb(results)
    },
    queryListData(reset=false) {
      if(reset){
        this.query.page_no = 1
      }
      this.$emit("queryStart")
      processMethod.get(this.query)
      .then((res) => {
        if (res.status === 0) {
          this.listData = Object.assign({}, res.data)
          this.$emit("queryFinish", this.listData)
        }
      });
    },
    reloadListData() {
      this.query.process_no = null;
      this.query.product_name = "";
      this.query.product_catalog = "";
      this.query.product_type = "";
      this.query.machine_data_source = "";
      this.query.machine_trademark = "";
      this.query.polymer_abbreviation = "";
      this.query.polymer_trademark = ""
      this.queryListData(true);
    },
    handleDataSourceSelect(item) {
      // 选择机器位置之后，根据机器位置过滤注塑机型号
      this.machine.data_source = item.value
      this.getTrademarkList({ "data_source": this.machine.data_source })
    },
  }
}
</script>

<style lang="scss" scoped>
  .el-autocomplete {
    width: 10rem;
  }

  .el-table {
    white-space: pre-wrap;
  }

</style>
