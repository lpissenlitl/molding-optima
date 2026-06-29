<template>
  <div class="search">
    <el-form
      :inline="true"
      :model="query"
      size="mini"
      label-width="8rem"
    >
      <el-form-item 
        label="塑料简称" 
        prop="abbreviation"
      >
        <el-autocomplete
          v-model="query.abbreviation"
          placeholder="塑料简称"
          clearable
          style="width:10rem"
          :fetch-suggestions="queryAbbreviationList"
        >
        </el-autocomplete>
      </el-form-item>

      <el-form-item 
        label="塑料牌号" 
        prop="trademark"
      >
        <el-autocomplete
          v-model="query.trademark"
          placeholder="塑料牌号"
          clearable
          style="width:10rem"
          :fetch-suggestions="queryTrademarkList"
        >
        </el-autocomplete>
      </el-form-item>

      <br>

      <el-form-item 
        label="制造厂商"
        prop="manufacturer"
      >
        <el-input 
          style="width:10rem" 
          v-model="query.manufacturer"
        ></el-input>
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
import { getOptions, polymerMethod } from "@/api";

export default {
  name: "QueryPolymerList",
  props: {
    queryDetail: {
      type: Object,
      default: () => ({
        abbreviation: null,
        trademark: null,
        series: null,
        manufacturer: null,
      })
    }
  },
  data() {
    return {
      query: this.queryDetail,
      poly_abbreviation_list: [],
      poly_trademark_dict: [],
      listData: {
        items: [],
        total: 0
      }
    }
  },
  created() {
    getOptions("polymer_abbreviation")
    .then(res => {
      // 塑料简称
      if (res.status === 0 && Array.isArray(res.data)) {
        this.poly_abbreviation_list.length = 0
        for (let i = 0; i < res.data.length; ++i) {
          this.poly_abbreviation_list.push({ "value": res.data[i].value })
        }
      }
    })
  },
  methods: {
    queryAbbreviationList(queryString, cb) {
      var poly_abbreviation_list = this.poly_abbreviation_list;
      var results = queryString ? poly_abbreviation_list.filter(this.createStateFilter(queryString)) : poly_abbreviation_list;
      cb(results)
    },
    queryTrademarkList(queryString, cb) {
      queryString = queryString == null ? "" : queryString

      if (!this.query.abbreviation) {
        return []
      }

      let promptList = []
      getOptions("polymer_trademark", {
        "abbreviation": this.query.abbreviation,
        "trademark": queryString
      }).then(res => {
        if (res.status == 0) {
          for (let i = 0; i < res.data.length; ++i) {
            promptList.push({
              id: res.data[i].id,
              value: res.data[i].trademark,
              category: res.data[i].category
            })
          }
          cb(promptList)
        }
      })
    },
    createStateFilter(queryString) {
      return (state) => {
        return (state.value.toLowerCase().indexOf(queryString.toLowerCase()) === 0);
      }
    },
    queryListData(reset=false) {
      if(reset){
        this.query.page_no = 1
      }
      this.$emit("queryStart")
      polymerMethod.get(this.query)
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
      this.query.abbreviation = null
      this.query.trademark = null
      this.query.series = null
      this.query.manufacturer = null

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
