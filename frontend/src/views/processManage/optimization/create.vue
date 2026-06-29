<template>
  <div>
    <el-card class="box-card">
      <div slot="header" class="clearfix">
        <span>基本信息</span>
      </div>
      <basic-mold-info
        :basic-mold-info="detail_info.basic_mold_info"
      >
      </basic-mold-info>
      <basic-injection-info
        :basic-injection-info="detail_info.basic_machine_info"
      >
      </basic-injection-info>
      <el-tabs 
        class="molding-tabs"
        v-if="detail_info.injection_station_details.length > 1"
        v-model="actived_tab_index"
      >
        <el-tab-pane
          v-for="(station_info, index) in detail_info.injection_station_details"
          :key="index"
          :label="'射台-#'+(index+1)"
          :name="String(index)"
        >
          <injection-station-detail
            ref="injection_station_detail"
            :class="{ 'disabled-area': station_info.casting_system.inject_part == null }"
            :disabled="true"
            :station-index="index"
            :injection-station-detail="station_info"
            :machine-info="detail_info.basic_machine_info"
          ></injection-station-detail>
        </el-tab-pane>
      </el-tabs>  
      <div v-else-if="detail_info.injection_station_details.length == 1">
        <injection-station-detail
          ref="injection_station_detail"
          :station-index="0"
          :injection-station-detail="detail_info.injection_station_details[0]"
          :machine-info="detail_info.basic_machine_info"
        ></injection-station-detail>
      </div>
    </el-card>
    <el-dialog
      title="提示！"
      :visible.sync="dialog_visible"
      width="30%"
    >
      <el-form size="mini">
        <el-form-item 
          :label="'当前射台为：射台#' + (Number(actived_tab_index) + 1) + '，请选择目标射台'"
        >
          <el-select v-model="switch_station">
            <el-option 
              v-for="(item, index) in detail_info.injection_station_details.length"
              :key="item"
              :label="'射台' + item"
              :value="index"
            ></el-option>
          </el-select>
        </el-form-item>
      </el-form>
      <span slot="footer" class="dialog-footer">
        <el-button 
          size="mini" 
          type="danger" 
          @click="dialog_visible = false"
        >
          取 消
        </el-button>
        <el-button 
          size="mini" 
          type="primary" 
          @click="onStationChanged"
        >
          确 定
        </el-button>
      </span>
    </el-dialog>
    <div 
      v-if="!view_context.is_dialog" 
      class="buttonGroup"
    >
      <el-button-group>
        <el-button
          type="warning"
          size="small"
          @click="resetView"
        >
          重置参数
        </el-button>
        <el-button
          v-if="detail_info.injection_station_details.length > 1"
          type="primary"
          size="small"
          @click="dialog_visible = true"
        >
          切换射台
        </el-button>
        <el-button
          type="success"
          size="small"
          @click="initProcessPara"
        >
          创建首模工艺
        </el-button>
        <el-button
          type="danger"
          size="small"
          @click="optimizeProcessPara"
        >
          缺陷修正
        </el-button>
        <el-button
          type="primary"
          size="small"
          @click="saveCurrentProcess"
          :loading="save_loading"
        >
          保存当前工艺
        </el-button>
      </el-button-group>
    </div>
  </div>
</template>

<script>
import { machineMethod, initialProcessAlgorithm, processOptimizeMethod,
  optimizeProcessAlgorithm, projectMethod, processIndexMethod, 
  processRecordMethod } from "@/api"
import { UserModule } from "@/store/modules/user"
import { initArray } from "@/utils/array-utils"
import { datetimeTodayStr } from "@/utils/datetime"
import { isValidData, updateObjectProperties, syncArray } from "@/utils/function"
import BasicMoldInfo from "./subView/basicMoldInfo.vue"
import BasicInjectionInfo from "./subView/basicInjectionInfo.vue"
import InjectionStationDetail from "./subView/injectionStationOptimizeDetail.vue"

const initialDetailInfo = {
  company_id: null,
  project_id: null,
  process_id: null,
  basic_mold_info: {
    id: null,
    // 基本信息
    mold_no: null,
    mold_type: null,
    mold_name: null,
    cavity_num: null,
    inject_cycle_require: null,
    // 制品信息
    product_industry: null,
    product_category: null,
    product_type: null,
    product_name: null,
    product_no: null,
    product_total_weight: null,
    product_projected_area: null,
    // 结构参数
    mold_weight: null,
    hanging_mold_hole_specification: null,
    size_horizon: null,
    mold_width: null,
    size_thickness: null,
    mold_opening_stroke: null,
    min_clamping_force: null,
    drain_distance: null,
    // 冷却系统
    cavity_cooling_circuit_number: null,
    cavity_water_nozzle_specification: null,
    cavity_cooling_water_diameter: null,
    core_cooling_circuit_number: null,
    core_water_nozzle_specification: null,
    core_cooling_water_diameter: null,
    // 顶出系统
    ejection_method: null,
    ejector_hole_position: null,
    ejector_hole_diameter: null,
    ejector_rod_number: null,
    ejector_rod_hole_distribute: null,
    ejector_rod_hole_spacing: null,
    ejector_rod_hole_diameter: null,
    ejector_times: null,
    ejector_stroke: null,
    ejector_force: null,
    reset_method: null,
  },
  basic_machine_info: {
    id: null,
    // 注塑机描述
    data_source: null,
    manufacturer: null,
    trademark: null,
    serial_no: null,
    asset_no: null,
    machine_type: null,
    drive_system: null,
    // 操作界面单位
    pressure_unit: "MPa",
    velocity_unit: "mm/s",
    position_unit: "mm",
    time_unit: "s",
    back_pressure_unit: "MPa",
    screw_rotation_unit: "rpm",
    temperature_unit: "℃",
    clamping_force_unit: "Ton",
    // 开合模机构
    min_mold_size_horizon: null,
    max_mold_size_horizon: null,
    min_mold_width: null,
    max_mold_width: null,
    min_mold_thickness: null,
    max_mold_thickness: null,
    min_platen_opening: null,
    max_platen_opening: null,
    locate_hole_diameter: null,
    // 拉杆机构
    pull_rod_size: null,
    pull_rod_diameter: null,
    pull_rod_distance_horizon: null,
    pull_rod_distance_vertical: null,
    // 锁模机构
    clamping_method: null,
    max_clamping_force: null,
    max_mold_open_stroke: null,
    // 顶出参数
    max_ejection_force: null,
    max_ejection_stroke: null,
    ejection_hole_num: null,
    core_pulling: null,
    core_pulling_group: null,
  },
  injection_station_details: [{
    // 模具信息
    casting_system: {
      inject_part: null,
      // 结构信息
      locate_ring_diameter: null,
      sprue_sphere_radius: null,
      sprue_hole_diameter: null,
      runner_type: null,
      // 结构信息--热流道
      hot_nozzle_type: null,
      hot_nozzle_number: null,
      need_hotrunner_wiring_adapter: null,
      hotrunner_valve_number: null,
      need_sequence_valve: null,
      valve_needle_drive_mode: null,
      // 结构信息--冷流道
      runner_weight: null,
      runner_length: null,
      total_gate_number: null,
      // 浇口信息
      gate_details: [{
        gate_type: null,
        gate_shape: null,
        gate_number: null,
        gate_length: null,
        gate_width: null,
        gate_radius: null,
        gate_area: null
      }],
      // 制品信息
      product_details: [{
        product_desc: null,
        product_number: null,
        product_flow_length: null,
        product_max_thickness: null,
        product_min_thickness: null,
        product_ave_thickness: null,
        product_single_volume: null,
        product_single_weight: null,
      }]
    },
    injection_detail: {
      id: null,
      title: "注射部件-#1",
      name: "0",
      serial_no: null,
      // 喷嘴参数
      nozzle_type: null,
      nozzle_protrusion: null,
      nozzle_hole_diameter: null,
      nozzle_sphere_radius: null,
      nozzle_contact_force: null,
      // 螺杆、料筒、油缸参数
      screw_type: null,
      screw_diameter: null,
      screw_length_to_diameter_ratio: null,
      screw_cross_sectional_area: null,
      screw_circumference: null,
      screw_compression_ratio: null,
      screw_enhancement_ratio: null,
      plasticizing_capacity: null,
      max_injection_stroke: null,
      max_injection_volume: null,
      max_injection_weight: null,
      barrel_heating_power: null,
      // 注塑机界面最大可设定段数
      max_stage: null,
      max_stage: null,
      max_stage: null,
      max_stage: null,
      // 注塑机界面单位
      pressure_unit: "MPa",
      velocity_unit: "mm/s",
      position_unit: "mm",
      time_unit: "s",
      back_pressure_unit: "MPa",
      screw_rotation_unit: "rpm",
      temperature_unit: "℃",
      // 成型参数（标准单位）
      max_injection_pressure: null,
      max_injection_velocity: null,
      max_holding_pressure: null,
      max_holding_velocity: null,
      max_metering_pressure: null,
      max_screw_rotation_speed: null,
      max_metering_back_pressure: null,
      max_decompression_pressure: null,
      max_decompression_velocity: null,
      // 注塑机界面最大可设定成型参数
      max_set_injection_pressure: null,
      max_set_injection_velocity: null,
      max_set_holding_pressure: null,
      max_set_holding_velocity: null,
      max_set_metering_pressure: null,
      max_set_screw_rotation_speed: null,
      max_set_metering_back_pressure: null,
      max_set_decompression_pressure: null,
      max_set_decompression_velocity: null,
    },
    // 材料信息
    polymer_detail: {
      id: null,
      title: "射台-#1",
      name: "0",
      // 基本信息
      manufacturer: null,
      abbreviation: null,
      trademark: null,
      category: null,
      // PVT属性
      melt_density: null,
      solid_density: null,
      // 推荐工艺
      max_melt_temperature: null,
      min_melt_temperature: null,
      recommend_melt_temperature: null,
      max_mold_temperature: null,
      min_mold_temperature: null,
      recommend_mold_temperature: null,
      max_shear_linear_speed: null,
      min_shear_linear_speed: null,
      recommend_shear_linear_speed: null,
      recommend_injection_rate: null,
      recommend_back_pressure: null,
      degradation_temperature: null,
      ejection_temperature: null,
      barrel_residence_time: null,
      max_shear_rate: null,
      max_shear_stress: null,
      dry_temperature: null,
      dry_time: null,
      dry_method: null,
      // 填充物
      filler: null,
      filler_percentage: null,
    },
    optimize_list: [{
      title: null,
      name: null,
      setting_process: {
        injection: {
          max_stage: 6,
          stage: 1,
          table_data: [
            { label: "压力", unit: "MPa", sections: initArray(6, null) },
            { label: "速度", unit: "mm/s", sections: initArray(6, null) },
            { label: "位置", unit: "mm", sections: initArray(6, null) }
          ],
          injection_time: null,
          delay_time: null,
          cooling_time: null
        },
        vp_switch: {
          mode: "位置",
          position: null,
          time: null,
          pressure: null,
          velocity: null,
        },
        holding: {
          max_stage: 5,
          stage: 1,
          table_data: [
            { label: "压力", unit: "MPa", sections: initArray(5, null) },
            { label: "速度", unit: "mm/s", sections: initArray(5, null) },
            { label: "时间", unit: "s", sections: initArray(5, null) }
          ]
        },
        metering: {
          max_stage: 4,
          stage: 1,
          table_data: [
            { label: "压力", unit: "MPa", sections: initArray(4, null) },
            { label: "螺杆转速", unit: "rpm", sections: initArray(4, null) },
            { label: "背压", unit: "MPa", sections: initArray(4, null) },
            { label: "位置", unit: "mm", sections: initArray(4, null) }
          ],
          pre_decompress_mode: "否",
          post_decompress_mode: "距离",
          decompress_table_data: [
            { label: "储前", pressure: null, velocity: null, time: null, distance: null },
            { label: "储后", pressure: null, velocity: null, time: null, distance: null }
          ],
          delay_time: null,
          ending_position: null
        },
        barrel_temperature: {
          max_stage: 10,
          stage: 5,
          table_data: [
            { label: "温度", unit: "℃", sections: initArray(10, null) },
          ],
        }
      },
      defect_feedback: {
        short_shot: { level: "无缺陷", position: "缺陷位置不指定", count: 0, feedback: null, remarks: null },
        flash: { level: "无缺陷", position: "缺陷位置不指定", count: 0, feedback: null, remarks: null },
        shrinkage: { level: "无缺陷", position: "缺陷位置不指定", count: 0, feedback: null, remarks: null },
        weld_line: { level: "无缺陷", position: "缺陷位置不指定", count: 0, feedback: null, remarks: null },
        aberration: { level: "无缺陷", position: "缺陷位置不指定", count: 0, feedback: null, remarks: null },
        air_trap: { level: "无缺陷", position: "缺陷位置不指定", count: 0, feedback: null, remarks: null },
        gas_veins: { level: "无缺陷", position: "缺陷位置不指定", count: 0, feedback: null, remarks: null },
        material_flower: { level: "无缺陷", position: "缺陷位置不指定", count: 0, feedback: null, remarks: null },
      },
      realtime_info: {
        actual_product_weight: null,
        peak_pressure: null,
      },
      optimize_record: {
        last_defect_name: null,
        last_defect_level: null,
        last_defect_position: null,
        
        rule_id: null,
        rule_description: null,
        rule_activation: null,
        rule_result_key: null,
        rule_result_value: null,

        adjust_name: null,
        adjust_value: null,
      }
    }]
  }]
}

export default {
  name: "CreateProcessOptimize",
  components: { 
    BasicMoldInfo, 
    BasicInjectionInfo, 
    InjectionStationDetail 
  },
  props: {
    viewContext: {
      type: Object,
      default: () => ({
        id: null,
        is_dialog: false,
        mode: null,
        excel_data: null
      })
    }
  },
  data() {
    return {
      detail_info: structuredClone(initialDetailInfo),
      view_context: this.viewContext,
      actived_tab_index: "0",
      save_loading: false,
      dialog_visible: false,
      switch_station: 0,
      default_station_distribute: true
    }
  },
  watch: {
    "detail_info.basic_mold_info.id" () {
      this.updateViewData()
    },
    "detail_info.basic_machine_info.id" () {
      this.updateViewData()
    },
    "detail_info": {
      handler: function() {
        sessionStorage.setItem("process_optimize", JSON.stringify(this.detail_info))
      },
      deep: true
    },
    viewContext: {
      handler: function () {
        this.view_context = this.viewContext
        this.initializeView()
      },
      deep: true,
      immediate: true
    },
  },
  created() {
    // sessionStorage
    let checkData = sessionStorage.getItem("process_optimize")
    if (isValidData(checkData)) {
      this.detail_info = JSON.parse(checkData)
    }
  },
  mounted() {
    this.initializeView()
  },
  methods: {
    async initializeView() {
      this.detail_info.process_id = null
      if (this.view_context.id) {
        // 弹框进入界面
        this.detail_info.process_id = this.view_context.id
      } else if (this.$route.query.id) {
        // 跳转进入界面，读取工艺记录
        const res = await processRecordMethod.get({ "process_id": this.$route.query.id })
        if (res.status === 0 && isValidData(res.data)) {
          this.detail_info.company_id = res.data.company_id
          this.detail_info.project_id = res.data.project_id
          this.detail_info.process_id = res.data.process_id
          this.detail_info.basic_mold_info = res.data.basic_mold_info
          this.detail_info.basic_machine_info = res.data.basic_machine_info
          syncArray(this.detail_info.injection_station_details, res.data.injection_station_details, initialDetailInfo.injection_station_details[0])
          this.detail_info.injection_station_details.forEach((injection_station, index) => {
            updateObjectProperties(injection_station, res.data.injection_station_details[index])
          })
        } else {
          this.$message({ message: "数据丢失，未读取到相关内容！", type: "warning" })
        }
        return
      }

      if (!this.detail_info.process_id) return

      // 读取工艺优化记录
      const res = await processOptimizeMethod.get({ "process_id": this.detail_info.process_id })
      if (res.status === 0 && isValidData(res.data)) {
        updateObjectProperties(this.detail_info, res.data)
      } else {
        this.$message({ message: "数据丢失，未读取到相关内容！", type: "warning" })
        this.$emit("close")
      }
    },
    async updateViewData() {
      // 1. 需要确定机台信息
      if (this.detail_info.basic_machine_info.id) {
        const res = await machineMethod.getDetail(this.detail_info.basic_machine_info.id)
        if (res.status === 0 && res.data) {
          // 读取注塑机基本参数
          updateObjectProperties(this.detail_info.basic_machine_info, res.data)
          // 读取注塑机射台参数
          if (isValidData(res.data.injection_details)) {
            // 根据注塑机信息调整射台数量
            syncArray(this.detail_info.injection_station_details, res.data.injection_details, initialDetailInfo.injection_station_details[0])
            // 更新每个注射部件的参数
            this.detail_info.injection_station_details.forEach((injection_station, index) => {
              updateObjectProperties(injection_station.injection_detail, res.data.injection_details[index])
              // 调整界面的单位
              injection_station.optimize_list.forEach((optimize_detail) => {
                // 注射参数
                optimize_detail.setting_process.injection.table_data[0].unit = res.data.pressure_unit
                optimize_detail.setting_process.injection.table_data[1].unit = res.data.velocity_unit
                // 保压参数
                optimize_detail.setting_process.holding.table_data[0].unit = res.data.pressure_unit
                optimize_detail.setting_process.holding.table_data[1].unit = res.data.velocity_unit
                // 计量参数
                optimize_detail.setting_process.metering.table_data[0].unit = res.data.pressure_unit
                optimize_detail.setting_process.metering.table_data[1].unit = res.data.screw_rotation_unit
                optimize_detail.setting_process.metering.table_data[2].unit = res.data.back_pressure_unit
              })
            })
          }
        }
      }

      // 2. 需要确定模具信息
      if (this.detail_info.basic_mold_info.id) {
        const res = await projectMethod.getDetail(this.detail_info.basic_mold_info.id)
        if (res.status === 0 && res.data) {
          updateObjectProperties(this.detail_info.basic_mold_info, res.data.mold_info)
          if (isValidData(res.data.mold_info.casting_systems)) {
            const casting_systems = res.data.mold_info.casting_systems
            // 更新每个射台对应的模具浇注信息
            this.detail_info.injection_station_details.forEach((injection_station, index) => {
              // 确保数据有效
              if (index < casting_systems.length) {
                updateObjectProperties(injection_station.casting_system, casting_systems[index])
                // 移除浇口信息 id
                injection_station.casting_system.gate_details.forEach(gate => {
                  delete gate.id
                  delete gate.casting_system_id
                })

                // 移除制品信息 id
                injection_station.casting_system.product_details.forEach(product => {
                  delete product.id
                  delete product.casting_system_id
                })
              }
            })
          }
        }
      }

      // // 强制界面渲染
      // this.detail_info.injection_station_details = structuredClone(this.detail_info.injection_station_details);
      // console.log(this.detail_info.injection_station_details)
    },
    showWarningMsg(msg) {      
      this.$message({ type: "warning", message: msg })
    },
    loadProcessPara(setting_process, params) {
      // 注射参数
      setting_process.injection.stage = params["stage"]
      for (let i = 0; i < params["stage"]; i++) {
        setting_process.injection.table_data[0].sections[i] = params["IP" + i]
        setting_process.injection.table_data[1].sections[i] = params["IV" + i]
        setting_process.injection.table_data[2].sections[i] = params["IL" + i]
      }
      setting_process.injection.injection_time = params["IT"]
      setting_process.injection.delay_time = params["ID"]
      setting_process.injection.cooling_time = params["CT"]

      // 切换方式
      setting_process.vp_switch.mode = params["VPTM"]
      setting_process.vp_switch.position = params["VPTL"]
      setting_process.vp_switch.time = params["VPTT"]
      setting_process.vp_switch.pressure = params["VPTP"]
      setting_process.vp_switch.velocity = params["VPTV"]
      
      // 保压参数
      setting_process.holding.stage = params["stage"]
      for (let i = 0; i < params["stage"]; i++) {
        setting_process.holding.table_data[0].sections[i] = params["PP" + i]
        setting_process.holding.table_data[1].sections[i] = params["PV" + i]
        setting_process.holding.table_data[2].sections[i] = params["PT" + i]
      }

      // 计量参数
      setting_process.metering.stage = params["stage"]
      for (let i = 0; i < params["stage"]; i++) {
        setting_process.metering.table_data[0].sections[i] = params["MP" + i]
        setting_process.metering.table_data[1].sections[i] = params["MSR" + i]
        setting_process.metering.table_data[2].sections[i] = params["MBP" + i]
        setting_process.metering.table_data[3].sections[i] = params["ML" + i]
      }

      // 储料切换方式
      setting_process.metering.pre_decompress_mode = params["DMBM"]
      setting_process.metering.post_decompress_mode = params["DMAM"]

      // 储前参数
      setting_process.metering.decompress_table_data[0].pressure = params["DPBM"]
      setting_process.metering.decompress_table_data[0].velocity = params["DVBM"]
      setting_process.metering.decompress_table_data[0].distance = params["DDBM"]
      setting_process.metering.decompress_table_data[0].time = params["DTBM"]

      // 储后参数
      setting_process.metering.decompress_table_data[1].pressure = params["DPAM"]
      setting_process.metering.decompress_table_data[1].velocity = params["DVAM"]
      setting_process.metering.decompress_table_data[1].distance = params["DDAM"]
      setting_process.metering.decompress_table_data[1].time = params["DTAM"]

      setting_process.metering.delay_time = params["MD"]
      setting_process.metering.ending_position = params["MEL"]

      // 料筒温度
      setting_process.barrel_temperature.stage = params["stage"]
      for (let i = 0; i < params["stage"]; i++) {
        if ( i === 0) {
          setting_process.barrel_temperature.table_data[0].sections[i] = params["NT"]
        } else {
          setting_process.barrel_temperature.table_data[0].sections[i] = params["BT" + i]
        }
      }
    },
    checkProcessValid(setting_process) {
      if (!this.detail_info.basic_machine_info.drive_system) {
        return this.showWarningMsg("注塑机信息不完整 - 动力方式为空, 请补充相关信息")
      }
      let injection = setting_process.injection
      for (let i = 0; i < injection.stage; ++i) {
        if (injection.table_data[0].sections[i] == null) {
          return this.showWarningMsg("注射" + (i + 1) + "段压力不能为空")
        }
        if (injection.table_data[1].sections[i] == null) {
          return this.showWarningMsg("注射" + (i + 1) + "段速度不能为空")
        }
        if (injection.table_data[2].sections[i] == null) {
          return this.showWarningMsg("注射" + (i + 1) + "段位置不能为空")
        }
      }
      if (injection.injection_time == null) {
        return this.showWarningMsg("注射时间不能为空")
      }
      if (injection.cooling_time == null) {
        return this.showWarningMsg("冷却时间不能为空")
      }
      let vp_switch = setting_process.vp_switch
      if (vp_switch.mode == null) {
        return this.showWarningMsg("VP切换模式不能为空")
      } else {
        if (vp_switch.mode == "位置" && vp_switch.position == null) {
          return this.showWarningMsg("位置切换模式时，切换位置不能为空")
        }
        if (vp_switch.mode == "时间" && vp_switch.time == null) {
          return this.showWarningMsg("时间切换模式时，切换时间不能为空")
        }
        if (vp_switch.mode == "时间&位置" 
        && vp_switch.position == null && vp_switch.time == null) {
          return this.showWarningMsg("时间&位置切换模式时，切换位置和切换时间不能为空")
        }
        if (vp_switch.mode == "压力" && vp_switch.pressure == null) {
          return this.showWarningMsg("压力切换模式时，切换压力不能为空")
        }
        if (vp_switch.mode == "速度" && vp_switch.velocity == null) {
          return this.showWarningMsg("速度切换模式时，切换速度不能为空")
        }
      }

      let holding = setting_process.holding
      for (let i = 0; i < holding.stage; ++i) {
        if (holding.table_data[0].sections[i] == null) {
          return this.showWarningMsg("保压" + (i + 1) + "段压力不能为空")
        }
        if (holding.table_data[1].sections[i] == null) {
          return this.showWarningMsg("保压" + (i + 1) + "段速度不能为空")
        }
        if (holding.table_data[2].sections[i] == null) {
          return this.showWarningMsg("保压" + (i + 1) + "段时间不能为空")
        }
      }

      let metering = setting_process.metering
      for (let i = 0; i < metering.stage; ++i) {
        if (metering.table_data[0].sections[i] == null) {
          if (this.detail_info.basic_machine_info.drive_system != "电动机")
            return this.showWarningMsg("计量" + (i + 1) + "段压力不能为空")
        }
        if (metering.table_data[1].sections[i] == null) {
          return this.showWarningMsg("计量" + (i + 1) + "段螺杆转速不能为空")
        }
        if (metering.table_data[2].sections[i] == null) {
          return this.showWarningMsg("计量" + (i + 1) + "段背压不能为空")
        }
        if (metering.table_data[3].sections[i] == null) {
          return this.showWarningMsg("计量" + (i + 1) + "段位置不能为空")
        }
      }

      if (metering.post_decompress_mode == "距离") {
        if (metering.decompress_table_data[1].pressure == null) {
          return this.showWarningMsg("储后压力不能为空")
        }
        if (metering.decompress_table_data[1].velocity == null) {
          return this.showWarningMsg("储后速度不能为空")
        }
        if (metering.decompress_table_data[1].distance == null) {
          return this.showWarningMsg("储后距离不能为空")
        }
      } else if (metering.post_decompress_mode == "时间") {
        if (metering.decompress_table_data[1].pressure == null) {
          return this.showWarningMsg("储后压力不能为空")
        }
        if (metering.decompress_table_data[1].velocity == null) {
          return this.showWarningMsg("储后速度不能为空")
        }
        if (metering.decompress_table_data[1].time == null) {
          return this.showWarningMsg("储后时间不能为空")
        }
      }

      if (metering.ending_position == null) {
        return this.showWarningMsg("储料终止位置不能为空") 
      }

      return true
    },
    async saveProcessOptimizeDetail() {
      if (this.detail_info.process_id == null) {
        // 插入工艺索引
        let mold_info = this.detail_info.basic_mold_info
        let machine_info = this.detail_info.basic_machine_info
        let polys_infos = [[], [], [], [], [], []]
        for (let i = 0; i < this.detail_info.injection_station_details.length; ++i) {
          let polymer_detail = this.detail_info.injection_station_details[i].polymer_detail
          polys_infos[0].push(polymer_detail.id)
          polys_infos[1].push(polymer_detail.data_source)
          polys_infos[2].push(polymer_detail.manufacturer)
          polys_infos[3].push(polymer_detail.abbreviation)
          polys_infos[4].push(polymer_detail.trademark)
          polys_infos[5].push(polymer_detail.category)
        }

        await processIndexMethod.add({
          company_id: UserModule.company_id,
          organization_id: UserModule.organization_id,
          project_id: this.detail_info.basic_mold_info.id,
          // 标记信息
          type: "optimize",
          status: 1,
          data_source: "手工录入",
          process_no: "P" + datetimeTodayStr(),
          // 模具信息
          mold_no: mold_info.mold_no,
          mold_type: mold_info.mold_type,
          mold_name: mold_info.mold_name,
          cavity_num: mold_info.cavity_num,
          inject_cycle_require: mold_info.inject_cycle_require,
          product_industry: mold_info.product_industry,
          product_category: mold_info.product_category,
          product_type: mold_info.product_type,
          product_name: mold_info.product_name,
          product_no: mold_info.product_no,
          product_total_weight: mold_info.product_total_weight,
          product_projected_area: mold_info.product_projected_area,
          // 注塑机信息
          mac_id: machine_info.id,
          mac_manufacturer: machine_info.manufacturer,
          mac_trademark: machine_info.trademark,
          mac_serial_no: machine_info.serial_no,
          mac_data_source: machine_info.data_source,
          mac_machine_type: machine_info.machine_type,
          // 材料信息
          polys_id: polys_infos[0].join("&"),
          polys_data_source: polys_infos[1].join("&"),
          polys_manufacturer: polys_infos[2].join("&"),
          polys_abbreviation: polys_infos[3].join("&"),
          polys_trademark: polys_infos[4].join("&"),
          polys_category: polys_infos[5].join("&"),
        }).then(res => {
          if (res.status === 0 && isValidData(res.data)) {
            this.detail_info.process_id = res.data.id
            this.$message({ message: "工艺参数索引新增成功！", type: "success" })
          }
        })
      }
      // 如果有工艺索引，则保存优化记录
      if (!this.detail_info.process_id) return
      await processOptimizeMethod.add({
        company_id: UserModule.company_id,
        organization_id: UserModule.organization_id,
        project_id: this.detail_info.basic_mold_info.id,
        process_id: this.detail_info.process_id,
        basic_mold_info: this.detail_info.basic_mold_info,
        basic_machine_info: this.detail_info.basic_machine_info,
        injection_station_details: this.detail_info.injection_station_details
      }).then(res => {
        if (res.status === 0) {
          this.$message({ message: "工艺优化记录已上传！", type: "success" })
        }
      })
    },
    async initProcessPara() {
      let mold_info = this.detail_info.basic_mold_info
      let machine_info = this.detail_info.basic_machine_info
      let injection_station_detail = this.detail_info.injection_station_details[Number(this.actived_tab_index)]
      let polymer_info = injection_station_detail.polymer_detail
      let casting_system = injection_station_detail.casting_system
      let init_process = injection_station_detail.optimize_list[0].setting_process
      // 查找横截面积最大的浇口信息
      let max_gate_area = 0
      let gate_detail = casting_system.gate_details[0]
      for (let i = 0; i < casting_system.gate_details.length; ++i) {
        if (casting_system.gate_details[i].gate_area > max_gate_area) {
          max_gate_area = casting_system.gate_details[i].gate_area
          gate_detail = casting_system.gate_details[i]
        }
      }
      // 获取制品信息，制品的总质量求和，最大壁厚、平均壁厚取最大值，最小壁厚取最小值
      let product_total_weight = 0
      let product_flow_length = 0
      let product_max_thickness = 0
      let product_min_thickness = 10000
      let product_ave_thickness = 0
      for (let i = 0; i < casting_system.product_details.length; ++i) {
        let product_detail = casting_system.product_details[i]
        product_total_weight += Number(product_detail.product_single_weight)
        if (product_detail.product_flow_length > product_flow_length) {
          product_flow_length = product_detail.product_flow_length
        }
        if (product_detail.product_max_thickness > product_max_thickness) {
          product_max_thickness = product_detail.product_max_thickness
        }
        if (product_detail.product_min_thickness < product_min_thickness) {
          product_min_thickness = product_detail.product_min_thickness
        }
        if (product_detail.product_ave_thickness > product_ave_thickness) {
          product_ave_thickness = product_detail.product_ave_thickness
        }
      }
      // 调用初始工艺算法
      const res = await initialProcessAlgorithm({
        // 模具信息
        mold_id: mold_info.id,
        mold_no: mold_info.mold_no,
        cavity_num: mold_info.cavity_num,
        inject_cycle_require: mold_info.inject_cycle_require,
        // 制品类别
        product_industry: mold_info.product_industry,
        product_category: mold_info.product_category,
        product_type: mold_info.product_type,
        // 流道参数
        runner_type: casting_system.runner_type,
        runner_weight: casting_system.runner_weight,
        runner_length: casting_system.runner_length,
        hot_nozzle_type: casting_system.hot_nozzle_type,
        hot_nozzle_number: casting_system.hot_nozzle_number,
        hotrunner_valve_number: casting_system.hotrunner_valve_number,
        // 浇口参数
        gate_type: gate_detail.gate_type,
        gate_shape: gate_detail.gate_shape,
        gate_number: gate_detail.gate_number,
        gate_area: gate_detail.gate_area,
        // 制品参数
        product_total_weight: product_total_weight,
        product_flow_length: product_flow_length,
        product_max_thickness: product_max_thickness,
        product_min_thickness: product_min_thickness,
        product_ave_thickness: product_ave_thickness,
        // 注塑机信息
        machine_id: machine_info.id,
        mac_manufacturer: machine_info.mac_manufacturer,
        mac_trademark: machine_info.trademark,
        mac_serial_no: machine_info.serial_no,
        mac_data_source: machine_info.data_source,
        mac_machine_type: machine_info.machine_type,
        injection_name: this.actived_tab_index,
        // 塑料信息
        polymer_id: polymer_info.id,
        poly_manufacture: polymer_info.manufacturer,
        poly_abbreviation: polymer_info.abbreviation,
        poly_trademark: polymer_info.trademark,
        poly_category: polymer_info.category,
        // 注塑机初始设定
        stage: init_process.injection.stage,
        VP_switch_mode: init_process.vp_switch.mode,
        stage: init_process.holding.stage,
        stage: init_process.metering.stage,
        pre_decompress_mode: init_process.metering.pre_decompress_mode,
        post_decompress_mode: init_process.metering.post_decompress_mode,
        stage: init_process.barrel_temperature.stage
      })
      // 处理初始化之后的操作
      if (res.status === 0 && isValidData(res.data)) {
        // 读取数据
        this.loadProcessPara(init_process, res.data)
        // 强制界面渲染
        this.detail_info.injection_station_details = structuredClone(this.detail_info.injection_station_details)
        // 由于是初始化工艺
        injection_station_detail.optimize_list.length = 1
        this.detail_info.process_id = null
        // 保存界面数据
        this.saveProcessOptimizeDetail()
      } else {
        this.$message({ message: "工艺参数初始化失败！", type: "error" })
      }
    },
    async optimizeProcessPara() {
      const setCurrentOptimizeTab = (tab_index) => {
        if (this.$refs["injection_station_detail"] instanceof Array) {
          this.$refs["injection_station_detail"][Number(this.actived_tab_index)].actived_tab_index = String(tab_index)
        } else {
          this.$refs["injection_station_detail"].actived_tab_index = String(tab_index)
        }
      }

      // 获取当前界面显示的工艺信息，构建提交给后端的参数信息
      let mold_info = this.detail_info.basic_mold_info
      let machine_info = this.detail_info.basic_machine_info
      let injection_station_detail = this.detail_info.injection_station_details[Number(this.actived_tab_index)]
      let optimize_list = injection_station_detail.optimize_list
      let opt_idx = 0
      if (this.$refs["injection_station_detail"] instanceof Array) {
        opt_idx = Number(this.$refs["injection_station_detail"][Number(this.actived_tab_index)].actived_tab_index)
      } else {
        opt_idx = Number(this.$refs["injection_station_detail"].actived_tab_index)
      }
      let optimize_detail = optimize_list[opt_idx]
      let process_detail = optimize_detail.setting_process

      // 校验工艺参数
      if (this.checkProcessValid(process_detail) != true) return

      // 校验缺陷反馈信息
      let target_defect = null
      for (let defect in optimize_detail.defect_feedback) {
        if (optimize_detail.defect_feedback[defect].level != "无缺陷") {
          target_defect = defect
          break
        }
      }
      if (target_defect == null) {
        return this.showWarningMsg("无缺陷反馈信息，请填写！")
      }

      // 构建注射重量
      let casting_system = injection_station_detail.casting_system
      let product_weight = 0
      if (casting_system.runner_type in ["冷流道", "热转冷"]) {
        product_weight = Number(casting_system.runner_weight)
      }
      for (let i = 0; i < casting_system.product_details.length; ++i) {
        product_weight += Number(casting_system.product_details[i].product_single_weight)
      }
      // 获取材料参数
      let polymer_detail = injection_station_detail.polymer_detail
      // 构建优化数据结构
      let process_params = {
        "opt_idx": opt_idx,
        "process_id": this.detail_info.process_id,
        "machine_id": machine_info.id,
        "injection_name": this.actived_tab_index,
        "polymer_abbreviation": polymer_detail.abbreviation,
        "product_type": mold_info.product_type,
        "product_weight": product_weight
      }
      // 注射参数
      let injection = process_detail.injection
      process_params["stage"] = injection.stage
      for (let i = 0; i < injection.stage; i++) {
        process_params["IP" + i] = injection.table_data[0].sections[i]
        process_params["IV" + i] = injection.table_data[1].sections[i]
        process_params["IL" + i] = injection.table_data[2].sections[i]
      }
      process_params["IT"] = injection.injection_time
      process_params["ID"] = injection.delay_time
      process_params["CT"] = injection.cooling_time
      // VP切换参数
      let vp_switch = process_detail.vp_switch
      process_params["VPTM"] = vp_switch.mode
      process_params["VPTT"] = vp_switch.time
      process_params["VPTL"] = vp_switch.position
      process_params["VPTP"] = vp_switch.pressure
      process_params["VPTV"] = vp_switch.velocity
      // 保压参数
      let holding = process_detail.holding
      process_params["stage"] = holding.stage
      for (let i = 0; i < holding.stage; i++) {
        process_params["PP" + i] = holding.table_data[0].sections[i]
        process_params["PV" + i] = holding.table_data[1].sections[i]
        process_params["PT" + i] = holding.table_data[2].sections[i]
      }
      // 计量参数
      let metering = process_detail.metering
      process_params["stage"] = metering.stage
      for (let i = 0; i < metering.stage; i++) {
        process_params["MP" + i] = metering.table_data[0].sections[i]
        process_params["MSR" + i] = metering.table_data[1].sections[i]
        process_params["MBP" + i] = metering.table_data[2].sections[i]
        process_params["ML" + i] = metering.table_data[3].sections[i]
      }
      // 储前射退参数
      process_params["DMBM"] = metering.pre_decompress_mode
      process_params["DPBM"] = metering.decompress_table_data[0].pressure
      process_params["DVBM"] = metering.decompress_table_data[0].velocity
      process_params["DDBM"] = metering.decompress_table_data[0].distance
      process_params["DTBM"] = metering.decompress_table_data[0].time
      // 储后射退参数
      process_params["DMAM"] = metering.post_decompress_mode
      process_params["DPAM"] = metering.decompress_table_data[1].pressure
      process_params["DVAM"] = metering.decompress_table_data[1].velocity
      process_params["DDAM"] = metering.decompress_table_data[1].distance
      process_params["DTAM"] = metering.decompress_table_data[1].time

      process_params["MD"] = metering.delay_time
      process_params["MEL"] = metering.ending_position

      // 温度参数
      let barrel_temperature = process_detail.barrel_temperature
      process_params["stage"] = barrel_temperature.stage
      for (let i = 0; i < barrel_temperature.stage; i++) {
        if (i === 0) {
          process_params["NT"] = barrel_temperature.table_data[0].sections[i]
        } else {
          process_params["BT" + i] = barrel_temperature.table_data[0].sections[i]
        }
      }
      // 其它参数
      process_params["defect_feedback"] = optimize_detail.defect_feedback
      process_params["realtime_info"] = optimize_detail.realtime_info
      process_params["optimize_record"] = optimize_detail.optimize_record
      // 调用工艺优化算法
      const res = await optimizeProcessAlgorithm(process_params)
      if (res.status === 0 && isValidData(res.data)) {
        let optimize_detail = structuredClone(initialDetailInfo.injection_station_details[0].optimize_list[0])
        // 读取工艺参数
        this.loadProcessPara(optimize_detail.setting_process, res.data)
        // 其它数据
        optimize_detail.optimize_record = res.data.optimize_record
        let last_defect = res.data.optimize_record.last_defect_name
        optimize_detail.defect_feedback[last_defect].feedback = "上一模修正效果佳"
        if (opt_idx < optimize_list.length - 1) {
          // 重新优化参数
          optimize_list[opt_idx + 1] = optimize_detail
          setCurrentOptimizeTab(opt_idx + 1)
        } else {
          // 插入优化参数
          optimize_list.push(optimize_detail)
          setCurrentOptimizeTab(optimize_list.length - 1)
        }
      }

      // 保存界面数据
      this.saveProcessOptimizeDetail()
    },
    async saveCurrentProcess() {
      // 保存当前界面的工艺
      let mold_info = this.detail_info.basic_mold_info
      let machine_info = this.detail_info.basic_machine_info
      let polys_infos = [[], [], [], [], [], []]
      for (let i = 0; i < this.detail_info.injection_station_details.length; ++i) {
        let polymer_detail = this.detail_info.injection_station_details[i].polymer_detail
        polys_infos[0].push(polymer_detail.id)
        polys_infos[1].push(polymer_detail.data_source)
        polys_infos[2].push(polymer_detail.manufacturer)
        polys_infos[3].push(polymer_detail.abbreviation)
        polys_infos[4].push(polymer_detail.trademark)
        polys_infos[5].push(polymer_detail.category)
      }

      let process_id = null
      await processIndexMethod.add({
        company_id: UserModule.company_id,
        organization_id: UserModule.organization_id,
        project_id: this.detail_info.basic_mold_info.id,
        // 标记 信息
        type: "record",
        data_source: "自动生成",
        status: 1,
        process_no: "P" + datetimeTodayStr(),
        // 模具信息
        mold_no: mold_info.mold_no,
        mold_type: mold_info.mold_type,
        mold_name: mold_info.mold_name,
        cavity_num: mold_info.cavity_num,
        inject_cycle_require: mold_info.inject_cycle_require,
        product_industry: mold_info.product_industry,
        product_category: mold_info.product_category,
        product_type: mold_info.product_type,
        product_name: mold_info.product_name,
        product_no: mold_info.product_no,
        product_total_weight: mold_info.product_total_weight,
        product_projected_area: mold_info.product_projected_area,
        // 注塑机信息
        mac_id: machine_info.id,
        mac_data_source: machine_info.data_source,
        mac_manufacturer: machine_info.manufacturer,
        mac_trademark: machine_info.trademark,
        mac_serial_no: machine_info.serial_no,
        mac_machine_type: machine_info.machine_type,
        // 材料信息
        polys_id: polys_infos[0].join("&"),
        polys_data_source: polys_infos[1].join("&"),
        polys_manufacturer: polys_infos[2].join("&"),
        polys_abbreviation: polys_infos[3].join("&"),
        polys_trademark: polys_infos[4].join("&"),
        polys_category: polys_infos[5].join("&"),
      }).then(res => {
        if (res.status === 0 && isValidData(res.data)) {
          process_id = res.data.id
          this.$message({ message: "工艺参数索引新增成功！", type: "success" })
        }
      })
      if (!process_id) return
      // 构建每射台工艺参数
      let injection_station_details = []
      if (this.$refs["injection_station_detail"] instanceof Array) {
        for (let i = 0; i < this.$refs["injection_station_detail"].length; ++i) {
          let select_idx = Number(this.$refs["injection_station_detail"][i].actived_tab_index)
          let station_detail = this.detail_info.injection_station_details[i]
          injection_station_details.push({
            "casting_system": station_detail.casting_system,
            "injection_detail": station_detail.injection_detail,
            "polymer_detail": station_detail.polymer_detail,
            "setting_process": station_detail.optimize_list[select_idx].setting_process
          })
        }
      } else {
        let select_idx = Number(this.$refs["injection_station_detail"].actived_tab_index)
        let station_detail = this.detail_info.injection_station_details[0]
        injection_station_details.push({
          "casting_system": station_detail.casting_system,
          "injection_detail": station_detail.injection_detail,
          "polymer_detail": station_detail.polymer_detail,
          "setting_process": station_detail.optimize_list[select_idx].setting_process
        })
      }
      // 记录详细的工艺参数相关信息
      await processRecordMethod.add({
        "company_id": UserModule.company_id,
        "organization_id": UserModule.organization_id,
        "project_id": mold_info.id,
        "process_id": process_id,
        "basic_mold_info": mold_info,
        "basic_machine_info": machine_info,
        "injection_station_details": injection_station_details
      }).then(res => {
        if (res.status === 0) {
          this.$message({ message: "工艺参数详细数据已保存！", type: "success" })
        }
      })
    },
    onStationChanged() {
      // 交换射台模具参数
      this.dialog_visible = false
      let cur_tab_index = Number(this.actived_tab_index)
      let tar_tab_index = Number(this.switch_station)
      let cur_casting_system = structuredClone(this.detail_info.injection_station_details[cur_tab_index].casting_system)
      this.detail_info.injection_station_details[cur_tab_index].casting_system = structuredClone(this.detail_info.injection_station_details[tar_tab_index].casting_system)
      this.detail_info.injection_station_details[tar_tab_index].casting_system = cur_casting_system
      this.actived_tab_index = String(tar_tab_index)
    },
    resetView() {
      this.detail_info = structuredClone(initialDetailInfo)
      this.actived_tab_index = "0"
    },
  }
}
</script>

<style lang="scss" scoped>
  .el-input {
    width: 10rem;
  }
  .el-select  {
    width: 10rem;
  }
  .el-autocomplete  {
    width: 10rem;
  }
  .buttonGroup {
    z-index: 999;
    position: fixed;
    text-align: center;
    width: 100%;
    bottom: 10px;
    font-size: 11px;
    line-height: 32px;
    margin: 0;
    height: 40px;
    .el-button {
      width: 8rem;
    }
  }
  .disabled-area {
    opacity: 0.6; /* 减少透明度 */
    pointer-events: none; /* 阻止鼠标交互 */
  }

</style>
