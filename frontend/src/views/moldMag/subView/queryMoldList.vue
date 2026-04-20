<template>
  <div class="search">
    <el-form
      :inline="true"
      :model="query"
      size="mini"
      label-width="8rem"
    >
      <el-form-item 
        label="模具编号"
        prop="mold_no"
      >
        <el-autocomplete
          v-model="query.mold_no" 
          :fetch-suggestions="((str, cb) => {querySuggestionOptions(str,cb,'mold_no')})"
          placeholder="请输入内容"
          suffix-icon="el-icon-search"
        > 
        </el-autocomplete>
      </el-form-item>

      <el-form-item 
        label="模具类别"
        prop="mold_type"
      >
        <el-autocomplete
          v-model="query.mold_type" 
          :fetch-suggestions="((str, cb) => {querySuggestionOptions(str,cb,'mold_type')})"
          placeholder="请输入内容"
          suffix-icon="el-icon-search"
        > 
        </el-autocomplete>
      </el-form-item>

      <el-form-item 
        label="模具名称"
        prop="mold_name"
      >
        <el-autocomplete
          v-model="query.mold_name" 
          :fetch-suggestions="((str, cb) => {querySuggestionOptions(str,cb,'mold_name')})"
          placeholder="请输入内容"
          suffix-icon="el-icon-search"
        > 
        </el-autocomplete>
      </el-form-item>

      <el-form-item 
        label="制品类别"
        prop="product_type"
      >
        <el-autocomplete
          v-model="query.product_type" 
          :fetch-suggestions="((str, cb) => {querySuggestionOptions(str,cb,'product_type')})"
          placeholder="请输入内容"
          suffix-icon="el-icon-search"
        > 
        </el-autocomplete>
      </el-form-item>

      <el-form-item 
        label="制品名称"
        prop="product_name"
      >
        <el-autocomplete
          v-model="query.product_name" 
          :fetch-suggestions="((str, cb) => {querySuggestionOptions(str,cb,'product_name')})"
          placeholder="请输入内容"
          suffix-icon="el-icon-search"
        > 
        </el-autocomplete>
      </el-form-item>

      <el-form-item 
        label="客户"
        prop="customer"
      >
        <el-autocomplete
          v-model="query.customer" 
          :fetch-suggestions="((str, cb) => {querySuggestionOptions(str,cb,'customer')})"
          placeholder="请输入内容"
          suffix-icon="el-icon-search"
        > 
        </el-autocomplete>
      </el-form-item>

      <el-form-item 
        label="项目工程师"
        prop="project_engineer"
      >
        <el-autocomplete
          v-model="query.project_engineer" 
          :fetch-suggestions="((str, cb) => {querySuggestionOptions(str,cb,'project_engineer')})"
          placeholder="请输入内容"
          suffix-icon="el-icon-search"
        > 
        </el-autocomplete>
      </el-form-item>

      <el-form-item 
        label="设计工程师"
        prop="design_engineer"
      >
        <el-autocomplete
          v-model="query.design_engineer" 
          :fetch-suggestions="((str, cb) => {querySuggestionOptions(str,cb,'design_engineer')})"
          placeholder="请输入内容"
          suffix-icon="el-icon-search"
        > 
        </el-autocomplete>
      </el-form-item>

      <el-form-item 
        label="制作工程师"
        prop="production_engineer"
      >
        <el-autocomplete
          v-model="query.production_engineer" 
          :fetch-suggestions="((str, cb) => {querySuggestionOptions(str,cb,'production_engineer')})"
          placeholder="请输入内容"
          suffix-icon="el-icon-search"
        > 
        </el-autocomplete>
      </el-form-item>

      <el-form-item 
        label="落单日期" 
        prop="order_date"
      >
        <el-date-picker
          v-model="query.order_date"
          placeholder="选择日期"
          format="yyyy-MM-dd"
          value-format="yyyy-MM-dd"
          type="date"
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
import { getOptions, projectMethod } from "@/api";
import suggestionOptions from "@/mixins/suggestionOptions.vue"

export default {
  name: "QueryMoldList",
  mixins: [suggestionOptions],
  props: {
    queryDetail: {
      type: Object,
      default: () => ({
        mold_no: null,
        mold_type: null,
        mold_name: null,
        product_type: null,
        product_name: null,
        customer: null,
        project_engineer: null,
        design_engineer: null,
        production_engineer: null,
        order_date: null,
      })
    }
  },
  data() {
    return {
      query: this.queryDetail,
      listData: {
        items: [],
        total: 0
      }
    }
  },
  methods: {
    querySuggestionOptions(input, cb, column) {
      if (["mold_no"].includes(column)) {
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
      } else if (["mold_type", "mold_name", "product_type", 
      "product_name", "customer", "project_engineer", "design_engineer",
      "production_engineer"].includes(column)) {
        cb(this.queryOptions(input, column, "mold"))
      }
    },
    queryListData(reset=false) {
      if(reset){
        this.query.page_no = 1
      }
      this.$emit("queryStart")
      projectMethod.get(this.query)
      .then((res) => {
        if (res.status === 0) {
          this.listData = Object.assign({}, res.data)
          this.$emit("queryFinish", this.listData)
        }
      });
    },
    reloadListData() {
      this.query.mold_no = null
      this.query.mold_type = null
      this.query.mold_name = null
      this.query.product_type = null
      this.query.product_name = null
      this.query.customer = null
      this.query.project_engineer = null
      this.query.design_engineer = null
      this.query.production_engineer = null
      this.query.order_date = null

      this.queryListData(true)
    }
  }
}
</script>

<style lang="scss" scoped>
  .el-form-item {
    .el-autocomplete {
      width: 10rem;
    }

    .el-date-picker {
      width: 10rem;
    }
  }
</style>
