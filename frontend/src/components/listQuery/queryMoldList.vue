<template>
  <div class="search">
    <el-form
      :inline="true"
      :model="query"
      size="mini"
      label-width="6rem"
    >
      <el-form-item label="模具编号:">
        <el-autocomplete
          v-model="query.mold_no" 
          :fetch-suggestions="queryMoldNo"
          placeholder="请输入内容"
          suffix-icon="el-icon-search"
        > 
        </el-autocomplete>
      </el-form-item>
      <el-form-item label="客户:">
        <el-autocomplete
          v-model="query.customer" 
          :fetch-suggestions="queryCustomer"
          placeholder="请输入内容"
          suffix-icon="el-icon-search"
        > 
        </el-autocomplete>
      </el-form-item>
      <el-form-item label="模具名称:">
        <el-autocomplete
          v-model="query.mold_name" 
          :fetch-suggestions="queryMoldName"
          placeholder="请输入内容"
          suffix-icon="el-icon-search"
        > 
        </el-autocomplete>
      </el-form-item>
      <el-form-item label="模具类别:">
        <el-autocomplete
          v-model="query.mold_type" 
          :fetch-suggestions="queryMoldType"
          placeholder="请输入内容"
          suffix-icon="el-icon-search"
        > 
        </el-autocomplete>
      </el-form-item>
      <el-form-item label="制品名称:">
        <el-autocomplete
          v-model="query.product_name" 
          :fetch-suggestions="queryProductName"
          placeholder="请输入内容"
          suffix-icon="el-icon-search"
        > 
        </el-autocomplete>
      </el-form-item>
      <el-form-item label="项目工程师:">
        <el-autocomplete
          v-model="query.project_engineer" 
          :fetch-suggestions="queryProjectEngineer"
          placeholder="请输入内容"
          suffix-icon="el-icon-search"
        > 
        </el-autocomplete>
      </el-form-item>
      <el-form-item label="制作工程师:">
        <el-autocomplete
          v-model="query.production_engineer" 
          :fetch-suggestions="queryManufactureEngineer"
          placeholder="请输入内容"
          suffix-icon="el-icon-search"
        > 
        </el-autocomplete>
      </el-form-item>
      <el-form-item label="落单日期:">
        <el-date-picker
          v-model="query.order_date"
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
import { UserModule } from '@/store/modules/user';
import { getOptions } from "@/api";
import { projectMethod } from "@/api"

export default {
  name: "QueryMoldList",
  props: {
    queryDetail: {
      type: Object,
      default: () => ({
        mold_no: null,
        customer: null,
        mold_name: null,
        mold_type: null,
        product_name: null,
        project_engineer: null,
        production_engineer: null,
        order_date: null,
        page_size: 100,
        page_no: 1 ,
        company_id : UserModule.company_id,
      })
    }
  },
  data() {
    return {
      query: this.queryDetail,
      listData: {}
    }
  },
  methods: {
    queryOptions(str, column) {
      str = str == null ? "" : str 
      let promptList = []
      if (column) {
        getOptions(column, { "form_input": str, "db_table": "mold" })
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
    queryMoldNo(str, cb) {
      str = str == null ? "" : str 
      let promptList = []
      getOptions("mold_no", { "form_input": str, "db_table": "mold" })
      .then( res => {
        if(res.status == 0) {
          for(let i = 0; i < res.data.length; i++) {
            promptList.push(res.data[i])
          }
        }
      })
      cb(promptList)
    },
    queryCustomer(str, cb) {
      let results = this.queryOptions(str, "customer")
      cb(results)
    },
    queryMoldName(str, cb) {
      let results = this.queryOptions(str, "mold_name")
      cb(results)
    },
    queryMoldType(str, cb) {
      let results = this.queryOptions(str, "mold_type")
      cb(results)
    },
    queryProductName(str, cb) {
      let results = this.queryOptions(str, "product_name")
      cb(results)
    },
    queryProjectEngineer(str, cb) {
      let results = this.queryOptions(str, "project_engineer")
      cb(results)
    },
    queryManufactureEngineer(str, cb) {
      let results = this.queryOptions(str, "production_engineer")
      cb(results)
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
      this.query.mold_no = null;
      this.query.customer = null;
      this.query.mold_name = null;
      this.query.mold_type = null;
      this.query.product_name = null;
      this.query.project_engineer = null;
      this.query.production_engineer = null;
      this.query.order_date = null;
      this.queryListData(true);
    }
  }
}
</script>

<style lang="scss" scoped>
  .el-autocomplete {
    width: 10rem;
  }
</style>
