<template>
  <div class="search">
    <el-form
      :inline="true"
      :model="query"
      size="mini"
      label-width="9.5rem"
    >
      <el-form-item 
        v-for="item, index in form_items"
        :key="index"
        :label="item.label"
        :prop="item.prop"
      >
        <el-autocomplete
          v-if="item.type === 'autocomplete'"
          :v-model="query[item.prop]"
          placeholder="请选择"
          clearable
          style="width:10rem"
          :fetch-suggestions="item.options"
        />
        <el-select 
          v-else-if="item.type === 'select'"
          v-model="query.machine_type"
        >
          <el-option 
            v-for="option in item.options"
            :key="option.value"
            :label="option.label"
            :value="option.value"
          />
        </el-select>
      </el-form-item>
      <el-form-item style="float:right">
        <el-button
          type="primary"
          @click="getListData(reload=false)"
          style="width: 6rem; margin-left:10px"
        >
          搜索
        </el-button>
        <el-button
          type="danger"
          @click="getListData(reload=true)"
          style="width: 6rem"
        >
          重置
        </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script>
import { 
  machineTypeOptions, machinePowerMethodOptions, machinePropulsionAxisOptions 
} from "@/utils/machine-const"
import { getOptions, machineMethod } from "@/api"

export default {
  name: "QueryInjectionMachineList",
  props: {
    queryDetail: {
      type: Object,
      default: () => ({
        data_source: null,
        trademark: null,
        serial_no: null,
        manufacturer: null,
        machine_type: null,
        power_method: null,
        propulsion_axis: null,
      })
    }
  },
  data() {
    return {
      form_items: [
        { label: "注塑机来源", prop: "data_source", type: "autocomplete", options: [] },
        { label: "注塑机品牌", prop: "manufacturer", type: "autocomplete", options: [] },
        { label: "注塑机型号", prop: "trademark", type: "autocomplete", options: [] },
        { label: "设备编码", prop: "serial_no", type: "autocomplete", options: [] },
        { label: "注塑机类型(射台数)", prop: "machine_type", type: "select", options: machineTypeOptions },
        { label: "注塑机类型(驱动方式)", prop: "power_method", type: "select", options: machinePowerMethodOptions },
        { label: "注塑机类型(推进轴线)", prop: "propulsion_axis", type: "select", options: machinePropulsionAxisOptions },
      ],
      query: this.queryDetail,
      list_data: {
        items: [],
        total: 0
      }
    }
  },
  created() {
  },
  methods: {
    async getListData(reload = false) {
      // 重置数据
      this.list_data = {
        items: [],
        total: 0
      }
      // 准备查询条件
      if (reload == true) {
        this.query.data_source = null
        this.query.trademark = null
        this.query.manufacturer = null
        this.query.serial_no = null
        this.query.machine_type = null
        this.query.power_method = null
        this.query.propulsion_axis = null
        this.query.page_no = 1
      }
      // 获取数据
      this.$emit("queryStart")
      await machineMethod.get(this.query)
        .then((res) => {
          if (res.status === 0) {
            this.list_data = Object.assign({}, res.data)
          }
        })
      this.$emit("queryFinish", this.list_data)
    },
  }
}
</script>

<style lang="scss" scoped>
  .el-autocomplete {
    width: 10rem;
  }
  .el-select {
    width: 10rem;
  }
</style>
