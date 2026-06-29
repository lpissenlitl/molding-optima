<template>
  <div class="search">
    <el-form
      :inline="true"
      :model="query"
      size="mini"
      label-width="8rem"
    >
      <el-form-item label="模具编号">
        <el-autocomplete
          v-model="query.mold_no" 
          :fetch-suggestions="((str, cb)=>{querySuggestionOptions(str, cb, 'mold_no')})"
          placeholder="请输入内容"
          suffix-icon="el-icon-search"
        > 
        </el-autocomplete>
      </el-form-item>

      <el-form-item label="浇口类别">
        <el-autocomplete
          v-model="query.gate_type" 
          :fetch-suggestions="((str, cb)=>{querySuggestionOptions(str, cb, 'gate_type')})"
          placeholder="请输入内容"
          suffix-icon="el-icon-search"
        > 
        </el-autocomplete>
      </el-form-item>

      <el-form-item label="制品类别">
        <el-autocomplete
          v-model="query.product_type" 
          :fetch-suggestions="((str, cb)=>{querySuggestionOptions(str, cb, 'product_type')})"
          placeholder="请输入内容"
          suffix-icon="el-icon-search"
        > 
        </el-autocomplete>
      </el-form-item>

      <el-form-item label="制品名称">
        <el-autocomplete
          v-model="query.product_name" 
          :fetch-suggestions="((str, cb)=>{querySuggestionOptions(str, cb, 'product_name')})"
          placeholder="请输入内容"
          suffix-icon="el-icon-search"
        > 
        </el-autocomplete>
      </el-form-item>

      <el-form-item label="注塑机来源">
        <el-autocomplete
          v-model="query.machine_data_source"
          placeholder="注塑机来源"
          clearable
          :fetch-suggestions="((str, cb)=>{querySuggestionOptions(str, cb, 'data_source')})"
          suffix-icon="el-icon-search"
        >
        </el-autocomplete>
      </el-form-item>

      <el-form-item label="注塑机型号">
        <el-autocomplete
          v-model="query.machine_trademark"
          placeholder="注塑机型号"
          clearable
          :fetch-suggestions="queryMacTrademarkOptions"
          suffix-icon="el-icon-search"
        >
        </el-autocomplete>
      </el-form-item>

      <el-form-item label="专家记录日期">
        <el-date-picker
          v-model="query.start_date"
          type="date"
          placeholder="选择日期"
          format="yyyy-MM-dd"
          value-format="yyyy-MM-dd"
          style="width:10rem"
        >
        </el-date-picker>
        -
        <el-date-picker
          v-model="query.end_date"
          type="date"
          placeholder="选择日期"
          format="yyyy-MM-dd"
          value-format="yyyy-MM-dd"
          style="width:10rem"
        >
        </el-date-picker>
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
import { processIndexMethod, getOptions } from "@/api";
import suggestionOptions from "@/mixins/suggestionOptions.vue"

export default {
  name: "QueryOptimizeList",
  mixins: [suggestionOptions],
  props: {
    queryDetail: {
      type: Object,
      default: () => ({
        mold_no: null,
        gate_type: null,
        product_type: null,
        product_name: null,
        machine_data_source: null,
        machine_trademark: null,
        start_date: null,
        end_date: null,
      })
    }
  },
  data() {
    return {
      query: this.queryDetail,
      listData: {
        items: [],
        total: 0
      },
    }
  },
  created() {

  },
  methods: {
    querySuggestionOptions(input, cb, column) {
      if (["data_source"].includes(column)) {
        cb(this.queryOptions(input, column, "machine"))
      } else if (["mold_no"].includes(column)) {
        input = input == null ? "" : input
        let promptList = []
        getOptions("mold_no", {
          "form_input": input,
          "db_table": "mold"
        }).then(res => {
          if (res.status == 0) {
            res.data.forEach(element => {
              promptList.push(element)
            })
          }
        })
        cb(promptList)
      } else if (["product_type", "product_name"].includes(column)) {
        cb(this.queryOptions(input, column, "mold"))
      } else if (["gate_type"].includes(column)) {
        cb(this.queryOptions(input, column, "product"))
      }
    },
    queryMacTrademarkOptions(queryString, cb) {
      queryString = queryString == null ? "" : queryString 

      if (!this.query.machine_data_source) {
        return []
      }

      let promptList = []
      getOptions("machine_trademark", {
        "data_source": this.query.machine_data_source,
        "trademark": queryString
      }).then(res => {
        if (res.status == 0) {
          for (let i = 0; i < res.data.length; ++i) {
            promptList.push({
              id: res.data[i].id,
              value: res.data[i].trademark,
              serial_no: res.data[i].serial_no
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
      processIndexMethod.get(this.query)
      .then((res) => {
        if (res.status === 0) {
          this.listData = Object.assign({}, res.data)
          this.$emit("queryFinish", this.listData)
        }
      });
    },
    reloadListData() {
      this.query.mold_no = null
      this.query.gate_type = null
      this.query.product_type = null
      this.query.product_name = null
      this.query.machine_data_source = null
      this.query.machine_trademark = null
      this.query.start_date = null
      this.query.end_date = null
      this.query.status = 4 // 专家记录
      this.query.data_sourcees = "专家调优"
      this.queryListData(true)
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
