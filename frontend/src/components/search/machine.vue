<template>
  <div class="el-form-item el-form-item--mini" style="margin:0px">
    <el-form-item 
      label="注塑机来源" 
      prop="data_source"
    >
      <el-autocomplete
        v-model="machine.data_source"
        placeholder="注塑机来源"
        clearable
        :fetch-suggestions="queryDataSourceOptions"
        suffix-icon="el-icon-search"
      >
      </el-autocomplete>
    </el-form-item>

    <el-form-item 
      label="注塑机型号" 
      prop="trademark"
    >
      <el-autocomplete
        v-model="machine.trademark"
        placeholder="注塑机型号"
        clearable
        :fetch-suggestions="queryTrademarkOptions"
        @select="handleTrademarkSelect"
        suffix-icon="el-icon-search"
      >
        <template slot-scope="{ item }">
          <el-tooltip
            effect="dark"
            :content="'设备编码: ' + [item.serial_no ? item.serial_no : '未知']"
            placement="right-end"
          >
            <div style="width:auto;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
              {{ item.value }}
            </div>
          </el-tooltip>
        </template>
      </el-autocomplete>
    </el-form-item>
  </div>
</template>

<script>
import { getOptions } from "@/api";
import suggestionOptions from "@/mixins/suggestionOptions.vue"

export default {
  name: "SearchMachine",
  mixins: [suggestionOptions],
  props: {
    machineInfo: {
      type: Object,
      default: () => ({})
    },
  },
  data() {
    return {
      machine: this.machineInfo,
    };
  },
  mounted() {

  },
  methods: {
    queryDataSourceOptions(queryString, cb) {
      cb(this.queryOptions(queryString, "data_source", "machine"))
    },
    queryTrademarkOptions(queryString, cb) {
      queryString = queryString == null ? "" : queryString

      if (!this.machine.data_source) {
        return []
      }

      let promptList = []
      getOptions("machine_trademark", {
        "data_source": this.machine.data_source,
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
    handleTrademarkSelect(item) {
      this.machine.id = item.id
      this.$emit("update-machine", item.id)
    },
  },
  watch: {
    machineInfo() {
      this.machine = this.machineInfo
    }
  }
}
</script>

<style lang="scss" scoped>
  .el-autocomplete {
    width: 10rem;
  }
</style>