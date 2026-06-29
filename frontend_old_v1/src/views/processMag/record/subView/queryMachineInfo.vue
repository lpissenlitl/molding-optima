<template>
  <el-form 
    size="mini" 
    label-position="right" 
    label-width="10rem"
    :inline="true"
  >
    <el-form-item 
      label="注塑机来源" 
      prop="data_source"
    >
      <el-autocomplete
        v-model="machine_info.data_source"
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
        v-model="machine_info.trademark"
        placeholder="注塑机型号"
        clearable
        :fetch-suggestions="queryTrademarkOptions"
        @select="handleTrademarkSelect"
        suffix-icon="el-icon-search"
      >
        <template slot-scope="{ item }">
          <el-tooltip
            effect="dark"
            :content="'设备编码: ' + [item.serial_no? item.serial_no: '未知']"
            placement="right-end"
          >
            <div style="width:auto;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
              {{ item.value }}
            </div>
          </el-tooltip>
        </template>
      </el-autocomplete>
    </el-form-item>

    <el-divider content-position="center">
      <span style="color:blue">注塑机参数</span>
    </el-divider>

    <el-form-item 
      label="最大注射体积"
      prop="max_injection_volume"
    >
      <el-input
        readonly
        v-model="machine_info.max_injection_volume"
      >
        <span slot="suffix">cm<sup>3</sup></span>
      </el-input>
    </el-form-item>

    <el-form-item 
      label="螺杆最大计量位置"
      prop="max_injection_stroke"
    >
      <el-input 
        readonly
        v-model="machine_info.max_injection_stroke"
      >
        <span slot="suffix">mm</span>
      </el-input>
    </el-form-item>

    <el-form-item 
      label="螺杆直径"
      prop="screw_diameter"
    >
      <el-input 
        readonly
        v-model="machine_info.screw_diameter"
      >
        <span slot="suffix">mm</span>
      </el-input>
    </el-form-item>

    <el-form-item 
      label="螺杆前进1mm体积"
      prop="screw_unit_volume"
    >
      <el-input 
        readonly
        v-model="machine_info.screw_unit_volume"
      >
        <span slot="suffix">cm<sup>3</sup>/mm</span>
      </el-input>
    </el-form-item>
  </el-form>
</template>

<script>
import { getOptions, machineMethod } from "@/api";
import suggestionOptions from "@/mixins/suggestionOptions.vue";

export default {
  name: "QueryMachineInfo",
  mixins: [suggestionOptions],
  props: {
    machineInfo: {
      type: Object,
      default: () => ({})
    },
  },
  data() {
    return {
      machine_info: this.machineInfo,
    };
  },
  methods: {
    queryDataSourceOptions(queryString, cb) {
      cb(this.queryOptions(queryString, "data_source", "machine"))
    },
    queryTrademarkOptions(queryString, cb) {
      queryString = queryString == null ? "" : queryString

      if (!this.machine_info.data_source) {
        return []
      }

      let promptList = []
      getOptions("machine_trademark", {
        "data_source": this.machine_info.data_source,
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
      this.machine_info.id = item.id
    },
    getMachineInfo() {
      if (this.machine_info.id) {
        machineMethod.getDetail(this.machine_info.id)
        .then(res => {
          if (res.status === 0) {
            this.machine_info.data_source = res.data.data_source
            this.machine_info.trademark = res.data.trademark
            this.machine_info.serial_no = res.data.serial_no
            this.machine_info.power_method = res.data.power_method

            this.machine_info.pressure_unit = res.data.pressure_unit
            this.machine_info.backpressure_unit = res.data.backpressure_unit
            this.machine_info.oc_pressure_unit = res.data.oc_pressure_unit
            this.machine_info.oc_velocity_unit = res.data.oc_velocity_unit
            this.machine_info.position_unit = res.data.position_unit
            this.machine_info.power_unit = res.data.power_unit
            this.machine_info.temperature_unit = res.data.temperature_unit
            this.machine_info.velocity_unit = res.data.velocity_unit
            this.machine_info.time_unit = res.data.time_unit
            this.machine_info.clamping_force_unit = res.data.clamping_force_unit
            this.machine_info.screw_rotation_unit = res.data.screw_rotation_unit

            this.machine_info.max_injection_volume = res.data.injectors_info[0].max_injection_volume
            this.machine_info.max_injection_stroke = res.data.injectors_info[0].max_injection_stroke
            this.machine_info.screw_diameter = res.data.injectors_info[0].screw_diameter
            let sdia = this.machine_info.screw_diameter
            this.machine_info.screw_unit_volume = ((sdia**2 * 3.14)/4000).toFixed(4)

            this.machine_info.max_injection_pressure = res.data.injectors_info[0].max_injection_pressure
            this.machine_info.max_injection_velocity = res.data.injectors_info[0].max_injection_velocity
            this.machine_info.max_holding_pressure = res.data.injectors_info[0].max_holding_pressure
            this.machine_info.max_holding_velocity = res.data.injectors_info[0].max_holding_velocity
            this.machine_info.max_metering_pressure = res.data.injectors_info[0].max_metering_pressure
            this.machine_info.max_screw_rotation_speed = res.data.injectors_info[0].max_screw_rotation_speed
            this.machine_info.max_metering_back_pressure = res.data.injectors_info[0].max_metering_back_pressure
            this.machine_info.max_decompression_pressure = res.data.injectors_info[0].max_decompression_pressure
            this.machine_info.max_decompression_velocity = res.data.injectors_info[0].max_decompression_velocity
            this.machine_info.max_ejector_forward_velocity = res.data.injectors_info[0].max_ejector_forward_velocity
            this.machine_info.max_ejector_backward_velocity = res.data.injectors_info[0].max_ejector_backward_velocity
            this.machine_info.max_mold_opening_velocity = res.data.injectors_info[0].max_mold_opening_velocity
            this.machine_info.max_mold_clamping_velocity = res.data.injectors_info[0].max_mold_clamping_velocity

            this.machine_info.max_set_ejector_forward_velocity = res.data.injectors_info[0].max_set_ejector_forward_velocity
            this.machine_info.max_set_ejector_backward_velocity = res.data.injectors_info[0].max_set_ejector_backward_velocity
            this.machine_info.max_set_mold_opening_velocity = res.data.injectors_info[0].max_set_mold_opening_velocity
            this.machine_info.max_set_mold_clamping_velocity = res.data.injectors_info[0].max_set_mold_clamping_velocity
            this.machine_info.max_set_injection_pressure = res.data.injectors_info[0].max_set_injection_pressure
            this.machine_info.max_set_injection_velocity = res.data.injectors_info[0].max_set_injection_velocity
            this.machine_info.max_set_holding_pressure = res.data.injectors_info[0].max_set_holding_pressure
            this.machine_info.max_set_holding_velocity = res.data.injectors_info[0].max_set_holding_velocity
            this.machine_info.max_set_metering_pressure = res.data.injectors_info[0].max_set_metering_pressure
            this.machine_info.max_set_screw_rotation_speed = res.data.injectors_info[0].max_set_screw_rotation_speed
            this.machine_info.max_set_metering_back_pressure = res.data.injectors_info[0].max_set_metering_back_pressure
            this.machine_info.max_set_decompression_pressure = res.data.injectors_info[0].max_set_decompression_pressure
            this.machine_info.max_set_decompression_velocity = res.data.injectors_info[0].max_set_decompression_velocity

            this.machine_info.max_injection_rate = res.data.injectors_info[0].max_injection_rate
            this.machine_info.max_holding_rate = res.data.injectors_info[0].max_holding_rate
            this.machine_info.max_decompression_rate = res.data.injectors_info[0].max_decompression_rate
            this.machine_info.max_screw_linear_velocity = res.data.injectors_info[0].max_screw_linear_velocity
  
            this.machine_info.max_mold_open_stroke = res.data.injectors_info[0].max_mold_open_stroke
            this.machine_info.max_ejection_stroke = res.data.injectors_info[0].max_ejection_stroke

            this.machine_info.screw_area = res.data.injectors_info[0].screw_area
            this.machine_info.screw_circumference = res.data.injectors_info[0].screw_circumference
          }
        })
      }
    }
  },
  watch: {
    machineInfo() {
      this.machine_info = this.machineInfo
    },
    "machine_info.id": function() {
      this.getMachineInfo()
    }
  }
}
</script>

<style lang="scss" scoped>
  .el-autocomplete {
    width: 10rem;
  }
  .el-input {
    width: 10rem;
  }
</style>