<template>
  <div class="el-form-item el-form-item--mini" style="margin:0px">
    <el-form-item label="塑料简称" prop="abbreviation">
      <el-autocomplete
        v-model="polymer.abbreviation"
        placeholder="塑料简称"
        clearable
        style="width:10rem"
        :fetch-suggestions="queryAbbreviationList"
        @select="handleAbbreviationSelect"
      >
      </el-autocomplete>
    </el-form-item>
    <el-form-item label="塑料牌号" prop="trademark">
      <el-autocomplete
        v-model="polymer.trademark"
        placeholder="塑料牌号"
        clearable
        style="width:10rem"
        :fetch-suggestions="queryTrademarkList"
        @select="handleTrademarkSelect"
      >
      </el-autocomplete>
    </el-form-item>
  </div>
</template>
<script>
import { getOptions } from "@/api";

export default {
  data() {
    return {
      polymer: this.polymerData,
      abbreviation_dict: [],
      trademark_dict: [],
    };
  },
  props: {
    polymerData: {
      type: Object,
      default: () => ({
        id: null,
        abbreviation: null,
        trademark: null,
      })
    }
  },
  mounted() {
    this.getAbbreviationList()
  },
  methods: {
    getAbbreviationList() {
      getOptions("polymer_abbreviation")
      .then(res => {
        // 塑料简称
        if (res.status === 0 && Array.isArray(res.data)) {
          this.abbreviation_dict.length = 0
          for (let i = 0; i < res.data.length; ++i) {
            this.abbreviation_dict.push({ "value": res.data[i].value })
          }
        }
      });
    },
    getTrademarkList(params) {
      // 没有塑料简称的时候，显示全部塑料牌号
      getOptions("polymer_trademark", params)
      .then(res => {
        if (res.status === 0 && Array.isArray(res.data)) {
          this.trademark_dict.length = 0
          for (let i = 0; i < res.data.length; ++i) {
            this.trademark_dict.push({ "id": res.data[i].id, "value": res.data[i].value })
          }
        }
      });
    },
    // 塑料简称和牌号过滤
    queryAbbreviationList(queryString, cb) {
      var abbreviation_dict = this.abbreviation_dict;
      var results = queryString ? abbreviation_dict.filter(this.createStateFilter(queryString)) : abbreviation_dict;
      cb(results);
    },
    queryTrademarkList(queryString, cb) {
      var trademark_dict = this.trademark_dict;
      var results = queryString ? trademark_dict.filter(this.createStateFilter(queryString)) : trademark_dict;
      cb(results);
    },
    createStateFilter(queryString) {
      return (state) => {
        return (state.value.toLowerCase().indexOf(queryString.toLowerCase()) === 0);
      };
    },
    handleAbbreviationSelect(item) {
      this.polymer.abbreviation = item.value
      this.getTrademarkList({ "abbreviation": item.value })
    },
    handleTrademarkSelect(item) {
      this.polymer.id = item.id
      this.polymer.trademark = item.value
    }
  },
  watch: {
    polymerData () {
      this.polymer = this.polymerData
    }
  }
}
</script>