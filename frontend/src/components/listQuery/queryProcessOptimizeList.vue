<template>
  <div class="search">
    <el-form
      :inline="true"
      :model="query"
      size="mini"
      label-width="6rem"
    >
      <el-form-item label="制品名称">
        <el-autocomplete
          v-model="query.product_name" 
          :fetch-suggestions="queryProductName"
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
      <el-form-item label="浇口类别">
        <el-autocomplete
          v-model="query.gate_type" 
          :fetch-suggestions="queryGateType"
          placeholder="请输入内容"
          suffix-icon="el-icon-search"
        > 
        </el-autocomplete>
      </el-form-item>
      <el-form-item label="优化日期">
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
import { UserModule } from '@/store/modules/user';
import { dateToday } from '@/utils/datetime';

export default {
  name: "QueryProductsList",
  props: {
    queryDetail: {
      type: Object,
      default: () => ({
        product_name: null,
        product_type: null,
        gate_type: null,
        start_date: dateToday(),
        end_date: dateToday(),
        company_id: UserModule.company_id,
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
      let results = this.queryOptions(str, "product_name")
      cb(results)
    },
    queryProductType(str, cb) {
      let results = this.queryOptions(str, "product_type")
      cb(results)
    },
    queryGateType(str, cb) {
      let results = this.queryOptions(str, "gate_type")
      cb(results)
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
      this.query.product_serial = "";
      this.query.product_name = null;
      this.query.start_date = null;
      this.query.end_date = null;
      this.query.product_type = "";
      this.query.gate_type = "";
      this.queryListData(true);
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
