<template>
  <el-row>
    <el-col :xs="24" :lg="13" :xl="13">
      <el-card class="box-card" style="min-height: 750px">
        <el-table 
          class="simple-table"
          size="mini"
          :data="injection.table_data" 
          :key="`injection_${injection.stage}`"
        >
          <el-table-column 
            label="工艺参数"
            width="120" 
            align="left"
          >
            <template #header>
              <div>注射段数</div>
              <el-select 
                v-model="injection.stage" 
                size="mini"
                style="width: 100%;"
              >
                <el-option
                  v-for="(option, idx) in injection.max_stage"
                  :key="idx"
                  :label="option"
                  :value="option"
                >
                </el-option>
              </el-select>
            </template>
            <template #default="scope">
              {{ scope.row.label }} [{{ scope.row.unit }}]
            </template>
          </el-table-column>
          <el-table-column
            v-for="(col, col_idx) in injection.max_stage"
            min-width="80"
            align="center"
            :key="col_idx"
            :label="injection_stage_header[col]"
          >
            <template #header>
              <div>{{ injection_stage_header[col] }}</div>
            </template>
            <template #default="scope">
              <el-input 
                v-model="scope.row.sections[col_idx]"
                v-number
                size="mini"
                style="width: 100%;"
                :disabled="col > injection.stage"
              >
              </el-input>
            </template>
          </el-table-column>
        </el-table>
        <br />
        <el-form
          size="mini"
          :model="injection"
          :inline="true"
        >
          <el-form-item 
            label="注射时间"
            prop="injection_time"
          >
            <el-input
              style="width: 8rem;"
              v-model="injection.injection_time"
              v-number
            >
              <span slot="suffix">s</span>
            </el-input>
          </el-form-item>
          <el-form-item 
            label="注射延迟"
            prop="delay_time"
          >
            <el-input
              style="width: 8rem;"
              v-model="injection.delay_time"
              v-number
            >
              <span slot="suffix">s</span>
            </el-input>
          </el-form-item>
          <el-form-item 
            label="冷却时间"
            prop="cooling_time"
          >
            <el-input
              style="width: 8rem;"
              v-model="injection.cooling_time"
              v-number
            >
              <span slot="suffix">s</span>
            </el-input>
          </el-form-item>
        </el-form>
        <el-form
          size="mini"
          :model="vp_switch"
          :inline="true"
        >
          <el-divider content-position="center">
            <span>VP切换</span>
          </el-divider>
          <el-form-item 
            label="切换方式"
            prop="mode"
          >
            <el-select
              style="width: 8rem;"
              v-model="vp_switch.mode"
              placeholder="请选择"
            >
              <el-option
                v-for="option in vp_switch_mode_options"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              >
              </el-option>
            </el-select>
          </el-form-item>
          <br />
          <el-form-item 
            label="切换位置"
            prop="position"
          >
            <el-input
              v-number
              v-model="vp_switch.position" 
              style="width: 8rem;"
              :disabled="isSwitchModeEnabled('position')"
            >
              <span slot="suffix">mm</span>
            </el-input>
          </el-form-item>
          <el-form-item 
            label="切换时间"
            prop="time"
          >
            <el-input
              v-number
              v-model="vp_switch.time" 
              style="width: 8rem;"
              :disabled="isSwitchModeEnabled('time')"
            >
              <span slot="suffix">s</span>
            </el-input>
          </el-form-item>
          <el-form-item 
            label="切换压力"
            prop="pressure"
          >
            <el-input
              v-number
              v-model="vp_switch.pressure" 
              style="width: 8rem;"
              :disabled="isSwitchModeEnabled('pressure')"
            >
              <span slot="suffix">{{ pressure_unit }}</span>
            </el-input>
          </el-form-item>
          <el-form-item 
            label="切换速度"
            prop="velocity"
          >
            <el-input
              v-number
              v-model="vp_switch.velocity" 
              style="width: 8rem;"
              :disabled="isSwitchModeEnabled('velocity')"
            >
              <span slot="suffix">{{ speed_unit }}</span>
            </el-input>
          </el-form-item>
        </el-form>
        <el-table 
          class="simple-table"
          size="mini"
          :data="holding.table_data" 
          :key="`holding_${holding.stage}`"
        >
          <el-table-column 
            label="工艺参数"
            width="120" 
            align="left"
          >
            <template #header>
              <div>保压段数</div>
              <el-select 
                v-model="holding.stage" 
                size="mini"
                style="width: 100%;"
              >
                <el-option
                  v-for="(option, idx) in holding.max_stage"
                  :key="idx"
                  :label="option"
                  :value="option"
                >
                </el-option>
              </el-select>
            </template>
            <template #default="scope">
              {{ scope.row.label }} [{{ scope.row.unit }}]
            </template>
          </el-table-column>
          <el-table-column
            v-for="(col, col_idx) in holding.max_stage"
            :key="col_idx"
            :label="holding_stage_header[col]"
            min-width="80"
            align="center"
          >
            <template #default="scope">
              <el-input 
                v-number
                v-model="scope.row.sections[col_idx]" 
                size="mini"
                style="width: 100%;"
                :disabled="col > holding.stage"
              >
              </el-input>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </el-col>
    <el-col :xs="24" :lg="11" :xl="11">
      <el-card class="box-card" style="min-height: 750px">
        <el-table 
          class="simple-table"
          size="mini"
          :data="metering.table_data"
          :key="`metering_${metering.stage}`"
        >
          <el-table-column 
            label="工艺参数"
            width="140" 
            align="left"
          >
            <template #header>
              <div>计量段数</div>
              <el-select 
                v-model="metering.stage" 
                size="mini"
                style="width: 100%;"
              >
                <el-option
                  v-for="(option, idx) in metering.max_stage"
                  :key="idx"
                  :label="option"
                  :value="option"
                >
                </el-option>
              </el-select>
            </template>
            <template #default="scope">
              {{ scope.row.label }} [{{ scope.row.unit }}]
            </template>
          </el-table-column>
          <el-table-column
            v-for="(col, col_idx) in metering.max_stage"
            :key="col_idx"
            :label="metering_stage_header[col]"
            min-width="80"
            align="center"
          >
            <template #default="scope">
              <el-input 
                v-model="scope.row.sections[col_idx]" 
                v-number
                :disabled="col > metering.stage"
                size="mini"
                style="width: 100%;"
              >
              </el-input>
            </template>
          </el-table-column>
        </el-table>
        <br />
        <el-form
          size="mini"
          :model="setting_process"
        >
          <el-form-item 
            label="储前松退模式"
            prop="pre_decompress_mode"
          >
            <el-select 
              v-model="metering.pre_decompress_mode"
              style="width: 8rem"
            >
              <el-option
                v-for="option, idx in decompressure_mode"
                :key="idx"
                :label="option.label"
                :value="option.value"
              >
              </el-option>
            </el-select>
          </el-form-item>
          <el-form-item 
            label="储后松退模式"
            prop="post_decompress_mode"
          >
            <el-select 
              v-model="metering.post_decompress_mode"
              style="width: 8rem"
            >
              <el-option
                v-for="option, idx in decompressure_mode"
                :key="idx"
                :label="option.label"
                :value="option.value"
              >
              </el-option>
            </el-select>
          </el-form-item>
        </el-form>
        <el-table
          class="simple-table"
          size="mini"
          :data="metering.decompress_table_data"
        >
          <el-table-column
            label="段数"
            width="60"
            align="center"
          >
            <template #default="scope">
              {{ scope.row.label }}
            </template>
          </el-table-column>
          <el-table-column
            label="压力"
            min-width="80"
            align="center"
          >
            <template #header>
              <div>压力</div>
              <div>[MPa]</div>
            </template>
            <template #default="scope">
              <el-input
                v-model="scope.row.pressure"
                v-number
                size="mini"
                style="width: 100%;"
                :disabled="isDecompressDisabled(scope.$index, 'pressure')"
              >
              </el-input>
            </template>
          </el-table-column>
          <el-table-column
            label="速度"
            min-width="80"
            align="center"
          >
            <template #header>
              <div>速度</div>
              <div>[mm/s]</div>
            </template>
            <template #default="scope">
              <el-input
                v-number
                v-model="scope.row.velocity"
                size="mini"
                style="width: 100%;"
                :disabled="isDecompressDisabled(scope.$index, 'velocity')"
              >
              </el-input>
            </template>
          </el-table-column>
          <el-table-column
            label="距离"
            min-width="80"
            align="center"
          >
            <template #header>
              <div>距离</div>
              <div>[mm]</div>
            </template>
            <template #default="scope">
              <el-input
                v-number
                v-model="scope.row.distance"
                size="mini"
                style="width: 100%;"
                :disabled="isDecompressDisabled(scope.$index, 'distance')"
              >
              </el-input>
            </template>
          </el-table-column>
          <el-table-column
            label="时间"
            min-width="80"
            align="center"
          >
            <template #header>
              <div>时间</div>
              <div>[s]</div>
            </template>
            <template #default="scope">
              <el-input
                v-number
                v-model="scope.row.time"
                size="mini"
                style="width: 100%;"
                :disabled="isDecompressDisabled(scope.$index, 'time')"
              >
              </el-input>
            </template>
          </el-table-column>
        </el-table>
        <br />       
        <el-form
          size="mini"
          :model="setting_process"
        >
          <el-form-item 
            label="储料延迟"
            prop="delay_time"
          >
            <el-input
              v-model="metering.delay_time"
              v-number
              style="width: 8rem"
            >
              <span slot="suffix">s</span>
            </el-input>
          </el-form-item>
          <el-form-item 
            label="终止位置"
            prop="ending_position"
          >
            <el-input
              v-model="metering.ending_position"
              v-number
              style="width: 8rem"
            >
              <span slot="suffix">mm</span>
            </el-input>
          </el-form-item>
        </el-form>
      </el-card>
    </el-col>
    <el-col :xs="24" :lg="24" :xl="24">
      <el-card class="box-card">
        <el-table 
          class="simple-table"
          size="mini"
          :data="barrel_temperature.table_data"
          :key="`barrel_temperature_${barrel_temperature.stage}`"
        >
          <el-table-column 
            label="工艺参数"
            width="90" 
            align="center"
          >
            <template #header>
              <div>温度段数</div>
              <el-select 
                v-model="barrel_temperature.stage" 
                size="mini"
                style="width: 100%;"
              >
                <el-option
                  v-for="(option, idx) in barrel_temperature.max_stage"
                  :key="idx"
                  :label="option"
                  :value="option"
                >
                </el-option>
              </el-select>
            </template>
            <template #default="scope">
              {{ scope.row.label }} [{{ scope.row.unit }}]
            </template>
          </el-table-column>
          <el-table-column
            v-for="(col, col_idx) in barrel_temperature.max_stage"
            :key="col_idx"
            :label="temp_stage_header[col]"
            min-width="80"
            align="center"
          >
            <template #default="scope">
              <el-input 
                v-number
                v-model="scope.row.sections[col_idx]" 
                size="mini"
                style="width: 100%;"
                :disabled="col > barrel_temperature.stage"
              >
              </el-input>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </el-col>
  </el-row>
</template>

<script>
import { settingProcessForm } from "@/constants/process-const"
import { machineInfoForm } from "@/constants/machine-const"

export default {
  name: "SettingProcess",
  props: {
    settingProcess: {
      type: Object,
      default: () => { return structuredClone(settingProcessForm) }
    },
    machineInfo: {
      type: Object,
      default: () => { return structuredClone(machineInfoForm) }
    }
  },
  data() {
    return {
      setting_process: this.settingProcess,
      machine_info: this.machineInfo,
      injection_stage_header: ["注射段数", "一段", "二段", "三段", "四段", "五段", "六段"],
      holding_stage_header: ["保压段数", "一段", "二段", "三段", "四段", "五段"],
      metering_stage_header: ["计量段数", "一段", "二段", "三段", "四段"],
      temp_stage_header: ["温度段数", "喷嘴", "一段", "二段", "三段", "四段", "五段", "六段", "七段", "八段", "九段"],
      vp_switch_mode_options: [
        { label: "位置", value: 0 },
        { label: "时间", value: 1 },
        { label: "时间&位置", value: 2 },
        { label: "压力", value: 3 },
        { label: "速度", value: 4 }
      ],
      decompressure_mode: [
        { label: "否", value: 0 },
        { label: "距离", value: 1 },
        { label: "时间", value: 2 },
      ],
    }
  },
  computed: {
    injection() {
      return this.setting_process.injection
    },
    vp_switch() {
      return this.setting_process.vp_switch
    },
    holding() {
      return this.setting_process.holding
    },
    metering() {
      return this.setting_process.metering
    },
    barrel_temperature() {
      return this.setting_process.barrel_temperature
    },
    pressure_unit() {
      return this.machineInfo.pressure_unit || "MPa"
    },
    speed_unit() { 
      return this.machineInfo.speed_unit || "mm/s"
    },
    temperature_unit() { 
      return this.machineInfo.temperature_unit || "℃"
    },
  },
  watch: { 
    settingProcess: {
      handler() {
        this.setting_process = this.settingProcess
        this.setMachineUnit()
      },
      deep: true,
      immediate: true
    }
  },
  methods: {
    isSwitchModeEnabled(keyword) {
      // VP 切换模式判断
      // 0: 位置, 1: 时间, 2: 时间&位置, 3: 压力, 4: 速度

      const mode = this.vp_switch.mode
      if ((mode === 0 || mode === 2) && keyword === "position") return false
      if ((mode === 1 || mode === 2) && keyword === "time") return false
      if (mode === 3 && keyword === "pressure") return false
      if (mode === 4 && keyword === "velocity") return false

      return true
    },
    isDecompressDisabled(index, type) {
      // 松退是否禁用
      // 0: 否, 1: 距离, 2: 时间

      const before = this.metering.pre_decompress_mode
      if (index === 0 && before === 1 && type !== "time") return false
      if (index === 0 && before === 2 && type !== "distance") return false

      const after = this.metering.post_decompress_mode
      if (index === 1 && after === 1 && type !== "time") return false
      if (index === 1 && after === 2 && type !== "distance") return false

      return true
    },
    setMachineUnit() {
      // 同步机器单位
      const pressure_unit = this.machine_info.pressure_unit
      const speed_unit = this.machine_info.speed_unit
      const screw_rotation_unit = this.machine_info.screw_rotation_unit
      const back_pressure_unit = this.machine_info.back_pressure_unit

      // --- 注射参数 ---
      this.injection.table_data[0].unit = pressure_unit
      this.injection.table_data[1].unit = speed_unit
      this.injection.table_data[2].unit = "mm"

      // --- 保压参数 ---
      this.holding.table_data[0].unit = pressure_unit
      this.holding.table_data[1].unit = speed_unit
      this.holding.table_data[2].unit = "s"

      // --- 计量参数 ---
      this.metering.table_data[0].unit = pressure_unit
      this.metering.table_data[1].unit = screw_rotation_unit
      this.metering.table_data[2].unit = back_pressure_unit
      this.metering.table_data[3].unit = "mm"
    }
  }
}
</script>

<style scoped>

</style>