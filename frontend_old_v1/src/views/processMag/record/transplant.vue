<template>
  <div class="MacProcessTransplant">
    <el-backtop 
      target=".MacProcessTransplant" 
      :bottom="200"
    ></el-backtop>

    <el-card shadow="hover" id="origin_machine">
      <div slot="header" class="clearfix">
        <div style="text-align:center">
          <span>工艺检索</span>
        </div>
      </div>
      <select-process-record 
        @select-process="load_origin_process"
      ></select-process-record>
    </el-card>

    <div style="height:20px"></div>
    <el-collapse 
      v-model="active_collapse" 
      class="collapseItemTitle"
    >
      <el-collapse-item title="原始工艺" name="1" class="collapseItemTitle">

        <el-drawer
          title="校验机台参数结果"
          size="650"
          direction="rtl"
          :visible.sync="showDrawer"
          :append-to-body="true"
          > 
          <check-result
            :mold-info="mold_info"
            :mold-result="mold_result"
            :origin-result="origin_result"
            :transplant-result="transplant_result"
            :machine-adaption-result="machine_adaption_result"
            :origin-machine-info="origin_process.machine_info"
            :transplant-machine-info="transplant_process.machine_info"
            :sum="sum"
            @transfer="getClick"
          >
          </check-result>
        </el-drawer>
        
        <el-divider content-position="center">
          <span style="color:blue">试模机台</span>
        </el-divider>

        <query-machine-info
          :machine-info="origin_process.machine_info"
        >
        </query-machine-info>

        <el-divider content-position="center">
          <span style="color:blue">参数设定</span>
        </el-divider>

        <process-record
          ref="originalProcess"
          :machine-info="origin_process.machine_info"
          :record-detail="origin_process.process_detail"
        >
        </process-record>
      </el-collapse-item>

      <div style="height:20px"></div>

      <el-card shadow="hover">
        <div slot="header" class="clearfix">
          <div style="text-align:center; color:green" id="transfer_machine">
            <span>转换工艺</span>
          </div>
        </div>

        <el-divider content-position="center">
          <span style="color:blue">转换机台</span>
        </el-divider>

        <query-machine-info
          :machine-info="transplant_process.machine_info"
        >
        </query-machine-info>


        <el-divider content-position="center">
          <span style="color:blue">参数设定</span>
        </el-divider>

        <process-record
          ref="transplantProcess"
          :machine-info="transplant_process.machine_info"
          :record-detail="transplant_process.process_detail"
        >
        </process-record>
      </el-card>
    </el-collapse>
    <div style="25px" />

    <div class="buttonGroup">
      <el-button-group>
        <el-button 
          type="warning" 
          size="small" 
          @click="resetView"
        >
          重置界面
        </el-button>
        <el-button
          type="primary"
          size="small"
          @click="checkMachine"
        >
          校验机台
        </el-button>
        <el-tooltip
          effect="dark"
          content="请先点击校验机台"
          placement="right-end"
        >
          <el-button 
            type="success" 
            size="small" 
            @click="processTransplant"
            :disabled="isclick"
          >
            转换原始工艺
          </el-button>
        </el-tooltip>
        <el-button 
          type="primary" 
          size="small" 
          @click="saveTransferProcess"
        >
          保存转换工艺
        </el-button>
      </el-button-group>
    </div>
  </div>
</template>

<script>

import QueryMachineInfo from "./subView/queryMachineInfo.vue";
import SelectProcessRecord from "./subView/selectProcessRecord.vue";
import ProcessRecord from "./subView/processRecordForm.vue";
import { processRecordMethod, processIndexMethod, machineMethod,projectMethod } from "@/api";
import { UserModule } from '@/store/modules/user';
import { initArray } from "@/utils/array-help";
import { datetimeTodayStr } from '@/utils/datetime';
import { processTransfer, checkValidTransfer, checkValidMold, checkValidAdaption, checkValidTransferMachine } from "@/utils/process-transfer";
import CheckResult from './subView/checkResult.vue';

export default {
  name: "ParameterTransplant",
  components: { SelectProcessRecord, QueryMachineInfo, ProcessRecord, CheckResult }, 
  data() {
    return {
      active_collapse:["1"],
      showDrawer: false,
      isclick: true,
      origin_process: {
        machine_info: {
          id: null,
          data_source: null,
          trademark: null,
          serial_no: null,
          power_method: null,

          pressure_unit: "MPa",
          backpressure_unit: "MPa",
          oc_pressure_unit: "MPa",
          oc_velocity_unit: "mm/s",
          position_unit: "mm",
          power_unit: "KW",
          temperature_unit: "℃",
          velocity_unit: "mm/s",
          time_unit: "s",
          clamping_force_unit: "Ton",
          screw_rotation_unit: "rpm",

          max_injection_volume: null,
          max_injection_stroke: null,
          screw_diameter: null,
          screw_unit_volume: null,

          cylinder_area: null,
          intensification_ratio: null,

          max_injection_pressure: null,
          max_injection_velocity: null,
          max_holding_pressure: null,
          max_holding_velocity: null,
          max_metering_pressure: null,
          max_screw_rotation_speed: null,
          max_metering_back_pressure: null,
          max_decompression_pressure: null,
          max_decompression_velocity: null,
          max_ejector_forward_velocity: null,
          max_ejector_backward_velocity: null,
          max_mold_opening_velocity: null,
          max_mold_clamping_velocity: null,

          max_set_ejector_forward_velocity: null,
          max_set_ejector_backward_velocity: null,
          max_set_mold_opening_velocity: null,
          max_set_mold_clamping_velocity: null,
          max_set_injection_pressure: null,
          max_set_injection_velocity: null,
          max_set_holding_pressure: null,
          max_set_holding_velocity: null,
          max_mold_open_stroke: null,
          max_ejection_stroke: null,
          max_set_metering_pressure: null,
          max_set_screw_rotation_speed: null,
          max_set_metering_back_pressure: null,
          max_set_decompression_pressure: null,
          max_set_decompression_velocity: null,

          max_injection_rate: null,
          max_holding_rate: null,
          max_decompression_rate: null,

          max_temperature_stage:null,

          screw_wear: null,
          slope: null,
          intercept: null,

          // 模具与注塑机的匹配
          machine_type          : null,
          max_clamping_force    : null,
          max_injection_weight  : null,
          min_mold_size_horizon : null,
          min_mold_size_vertical: null,
          min_mold_thickness    : null,
          max_mold_size_horizon : null,
          max_mold_size_vertical: null,
          max_mold_thickness    : null,
          locate_ring_diameter  : null,
          max_ejection_force    : null,
          max_ejection_stroke   : null,
          max_mold_open_stroke  : null,
          nozzle_sphere_diameter: null,
          nozzle_hole_diameter  : null,
        },
        precondition: {
          mold_id: null,
          mold_no: null,
          cavity_num: null,
          runner_length: null,
          runner_weight: null,
          gate_type: null,
          gate_num: null,
          gate_shape: null,
          gate_area: null,
          gate_radius: null,
          gate_length: null,
          gate_width: null,

          product_no: null,
          product_type: null,
          product_name: null,
          product_total_weight: null,
          product_ave_thickness: null,
          product_max_thickness: null,
          product_max_length: null,

          machine_id: null,
          machine_data_source: null,
          machine_trademark: null,
          machine_serial_no: null,

          polymer_id: null,
          polymer_abbreviation: null,
          polymer_trademark: null,
        },
        process_detail: {
          title: "射台 #1", 
          name: "1",
          inject_para: {
            injection_stage: 6,
            max_injection_stage_option: 6,
            table_data: [
              { label: "压力", unit: "kgf/cm²", sections: initArray(6, null) },
              { label: "速度", unit: "mm/s", sections: initArray(6, null) },
              { label: "位置", unit: "mm", sections: initArray(6, null) }
            ],
            injection_time: null,
            injection_delay_time: null,
            cooling_time: null
          },
          holding_para: {
            holding_stage: 5,
            max_holding_stage_option: 5,
            table_data: [
              { label: "压力", unit: "kgf/cm²", sections: initArray(5, null) },
              { label: "速度", unit: "mm/s", sections: initArray(5, null) },
              { label: "时间", unit: "s", sections: initArray(5, null) }
            ]
          },
          VP_switch: {
            VP_switch_mode: null,
            VP_switch_position: null,
            VP_switch_time: null,
            VP_switch_pressure: null,
            VP_switch_velocity: null,
          },
          metering_para: {
            metering_stage: 4,
            max_metering_stage_option: 4,
            table_data: [
              { label: "压力", unit: "kgf/cm²", sections: initArray(4, null) },
              { label: "螺杆转速", unit: "rpm", sections: initArray(4, null) },
              { label: "背压", unit: "kgf/cm²", sections: initArray(4, null) },
              { label: "位置", unit: "mm", sections: initArray(4, null) }
            ],
            decompressure_mode_before_metering: "否",
            decompressure_mode_after_metering: "距离",
            decompressure_paras: [
              { label: "储前", pressure: null, velocity: null, time: null, distance: null },
              { label: "储后", pressure: null, velocity: null, time: null, distance: null }
            ],
            metering_delay_time: null,
            metering_ending_position: null
          },
          temp_para: {
            barrel_temperature_stage: 5,
            max_barrel_temperature_stage_option: 10,
            table_data: [
              { label: "温度", unit: "℃", sections: initArray(10, null) },
            ],
          },
          ejector_setting: {
            ejector_backward: {
              ejector_backward_stage: 4,
              max_ejector_backward_stage_option: 8,
              table_data: [
                { label: "压力", unit: "kgf/cm²", sections: initArray(8, null) },
                { label: "速度", unit: "mm/s", sections: initArray(8, null) },
                { label: "位置", unit: "mm", sections: initArray(8, null) },
              ]
            },
            ejector_forward: {
              ejector_forward_stage: 4,
              max_ejector_forward_stage_option: 8,
              table_data: [
                { label: "压力", unit: "kgf/cm²", sections: initArray(8, null) },
                { label: "速度", unit: "mm/s", sections: initArray(8, null) },
                { label: "位置", unit: "mm", sections: initArray(8, null) },
              ]
            },
            ejector_start_point: null,
            ejector_delay: null,
            ejector_keep: null,
            ejector_pause: null,
            ejector_blow_time: null,
            ejector_mode: null,
            ejector_times: null,
            ejector_on_opening: "关",
            ejector_stroke: null,
            ejector_force: null,
            set_torque: null,
          },
          opening_and_clamping_mold_setting: {
            mold_opening: {
              mold_opening_stage: 4,
              max_mold_opening_stage_option: 8,
              table_data: [
                { label: "压力", unit: "kgf/cm²", sections: initArray(8, null) },
                { label: "速度", unit: "mm/s", sections: initArray(8, null) },
                { label: "位置", unit: "mm", sections: initArray(8, null) },
              ],
            },
            mold_clamping: {
              mold_clamping_stage: 4,
              max_mold_clamping_stage_option: 8,
              table_data: [
                { label: "压力", unit: "kgf/cm²", sections: initArray(8, null) },
                { label: "速度", unit: "mm/s", sections: initArray(8, null) },
                { label: "位置", unit: "mm", sections: initArray(8, null) }
              ]
            },
            set_mold_clamping_force: null,
            using_robot: "否",
            using_tool: "否",
            reset_method: null,
            set_mold_protect_time: null,
            set_mold_protect_velocity: null,
            set_mold_protect_pressure: null,
            set_mold_protect_distance: null,
            opening_position_deviation: null,
            turnable_method: null,
            turnable_velocity: null,
          },

        }
      },
      transplant_process: {
        machine_info: {
          id: null,
          data_source: null,
          trademark: null,
          serial_no: null,
          power_method: null,

          pressure_unit: "MPa",
          backpressure_unit: "MPa",
          oc_pressure_unit: "MPa",
          oc_velocity_unit: "mm/s",
          position_unit: "mm",
          power_unit: "KW",
          temperature_unit: "℃",
          velocity_unit: "mm/s",
          time_unit: "s",
          clamping_force_unit: "Ton",
          screw_rotation_unit: "rpm",

          max_injection_volume: null,
          max_injection_stroke: null,
          screw_diameter: null,
          screw_unit_volume: null,

          cylinder_area: null,
          intensification_ratio: null,

          max_injection_pressure: null,
          max_injection_velocity: null,
          max_holding_pressure: null,
          max_holding_velocity: null,
          max_metering_pressure: null,
          max_screw_rotation_speed: null,
          max_metering_back_pressure: null,
          max_decompression_pressure: null,
          max_decompression_velocity: null,
          max_ejector_forward_velocity: null,
          max_ejector_backward_velocity: null,
          max_mold_opening_velocity: null,
          max_mold_clamping_velocity: null,

          max_set_injection_pressure: null,
          max_set_injection_velocity: null,
          max_set_holding_pressure: null,
          max_set_holding_velocity: null,
          max_set_metering_pressure: null,
          max_set_screw_rotation_speed: null,
          max_set_metering_back_pressure: null,
          max_set_decompression_pressure: null,
          max_set_decompression_velocity: null,
          max_mold_open_stroke: null,
          max_ejection_stroke: null,
          max_set_ejector_forward_velocity: null,
          max_set_ejector_backward_velocity: null,
          max_set_mold_opening_velocity: null,
          max_set_mold_clamping_velocity: null,

          max_injection_rate: null,
          max_holding_rate: null,
          max_decompression_rate: null,
          max_temperature_stage: null,

          screw_wear: null,
          slope: null,
          intercept: null,

          // 模具与注塑机适配
          machine_type          : null,
          max_clamping_force    : null,
          max_injection_weight  : null,
          min_mold_size_horizon : null,
          min_mold_size_vertical: null,
          min_mold_thickness    : null,
          max_mold_size_horizon : null,
          max_mold_size_vertical: null,
          max_mold_thickness    : null,
          locate_ring_diameter  : null,
          max_ejection_force    : null,
          max_ejection_stroke   : null,
          max_mold_open_stroke  : null,
          nozzle_sphere_diameter: null,
          nozzle_hole_diameter  : null,
        },
        precondition: {
          mold_id: null,
          mold_no: null,
          cavity_num: null,
          runner_length: null,
          runner_weight: null,
          gate_type: null,
          gate_num: null,
          gate_shape: null,
          gate_area: null,
          gate_radius: null,
          gate_length: null,
          gate_width: null,

          product_no: null,
          product_type: null,
          product_name: null,
          product_total_weight: null,
          product_ave_thickness: null,
          product_max_thickness: null,
          product_max_length: null,

          machine_id: null,
          machine_data_source: null,
          machine_trademark: null,
          machine_serial_no: null,

          polymer_id: null,
          polymer_abbreviation: null,
          polymer_trademark: null,
        },
        process_detail: {
          title: "射台 #1", 
          name: "1",
          inject_para: {
            injection_stage: 6,
            max_injection_stage_option: 6,
            table_data: [
              { label: "压力", unit: "kgf/cm²", sections: initArray(6, null) },
              { label: "速度", unit: "mm/s", sections: initArray(6, null) },
              { label: "位置", unit: "mm", sections: initArray(6, null) }
            ],
            injection_time: null,
            injection_delay_time: null,
            cooling_time: null
          },
          holding_para: {
            holding_stage: 5,
            max_holding_stage_option: 5,
            table_data: [
              { label: "压力", unit: "kgf/cm²", sections: initArray(5, null) },
              { label: "速度", unit: "mm/s", sections: initArray(5, null) },
              { label: "时间", unit: "s", sections: initArray(5, null) }
            ]
          },
          VP_switch: {
            VP_switch_mode: null,
            VP_switch_position: null,
            VP_switch_time: null,
            VP_switch_pressure: null,
            VP_switch_velocity: null,
          },
          metering_para: {
            metering_stage: 4,
            max_metering_stage_option: 4,
            table_data: [
              { label: "压力", unit: "kgf/cm²", sections: initArray(4, null) },
              { label: "螺杆转速", unit: "rpm", sections: initArray(4, null) },
              { label: "背压", unit: "kgf/cm²", sections: initArray(4, null) },
              { label: "位置", unit: "mm", sections: initArray(4, null) }
            ],
            decompressure_mode_before_metering: "否",
            decompressure_mode_after_metering: "距离",
            decompressure_paras: [
              { label: "储前", pressure: null, velocity: null, time: null, distance: null },
              { label: "储后", pressure: null, velocity: null, time: null, distance: null }
            ],
            metering_delay_time: null,
            metering_ending_position: null
          },
          temp_para: {
            barrel_temperature_stage: 5,
            max_barrel_temperature_stage_option: 10,
            table_data: [
              { label: "温度", unit: "℃", sections: initArray(10, null) },
            ],
          },
          ejector_setting: {
            ejector_backward: {
              ejector_backward_stage: 4,
              max_ejector_backward_stage_option: 8,
              table_data: [
                { label: "压力", unit: "kgf/cm²", sections: initArray(8, null) },
                { label: "速度", unit: "mm/s", sections: initArray(8, null) },
                { label: "位置", unit: "mm", sections: initArray(8, null) },
              ]
            },
            ejector_forward: {
              ejector_forward_stage: 4,
              max_ejector_forward_stage_option: 8,
              table_data: [
                { label: "压力", unit: "kgf/cm²", sections: initArray(8, null) },
                { label: "速度", unit: "mm/s", sections: initArray(8, null) },
                { label: "位置", unit: "mm", sections: initArray(8, null) },
              ]
            },
            ejector_start_point: null,
            ejector_delay: null,
            ejector_keep: null,
            ejector_pause: null,
            ejector_blow_time: null,
            ejector_mode: null,
            ejector_times: null,
            ejector_on_opening: "关",
            ejector_stroke: null,
            ejector_force: null,
            set_torque: null,
          },
          opening_and_clamping_mold_setting: {
            mold_opening: {
              mold_opening_stage: 4,
              max_mold_opening_stage_option: 8,
              table_data: [
                { label: "压力", unit: "kgf/cm²", sections: initArray(8, null) },
                { label: "速度", unit: "mm/s", sections: initArray(8, null) },
                { label: "位置", unit: "mm", sections: initArray(8, null) },
              ],
            },
            mold_clamping: {
              mold_clamping_stage: 4,
              max_mold_clamping_stage_option: 8,
              table_data: [
                { label: "压力", unit: "kgf/cm²", sections: initArray(8, null) },
                { label: "速度", unit: "mm/s", sections: initArray(8, null) },
                { label: "位置", unit: "mm", sections: initArray(8, null) }
              ]
            },
            set_mold_clamping_force: null,
            using_robot: "否",
            using_tool: "否",
            reset_method: null,
            set_mold_protect_time: null,
            set_mold_protect_velocity: null,
            set_mold_protect_pressure: null,
            set_mold_protect_distance: null,
            opening_position_deviation: null,
            turnable_method: null,
            turnable_velocity: null,
          },
          loose_core: {
            core_movement_method: null,
            table_data: initArray(2, {
              core_switch_selection: null,
              core_mold_clamping_method: null,
              core_mold_opening_method: null,
              set_core_in_time: null,
              set_core_out_time: null,
              core_in_position: null,
              core_out_position: null,
            })
          },
        }
      },
      origin_result: [],
      transplant_result: [],
      mold_result: [],
      machine_adaption_result:[],
      sum: 0,
      origin_process_index_id: null,
      mold_info:null
    }
  },
  mounted() {
    
  },
  methods: {
    load_origin_process(process_index_id) {
      this.origin_process_index_id = String(process_index_id)
      if (process_index_id) {
        processRecordMethod.getDetail(process_index_id)
        .then(res => {
          if (res.status === 0 && JSON.stringify(res.data) != "{}") {
            // 从科学试模工艺条件记录保存过来的有些参数需要转换一下再在页面显示
            if (res.data.process_detail.metering_para.decompressure_mode_after_metering == "distance") {
              res.data.process_detail.metering_para.decompressure_mode_after_metering = "距离"
            } else if (res.data.process_detail.metering_para.decompressure_mode_after_metering == "forbidden") {
              res.data.process_detail.metering_para.decompressure_mode_after_metering = "否"
            } else if (res.data.process_detail.metering_para.decompressure_mode_after_metering == "time") {
              res.data.process_detail.metering_para.decompressure_mode_after_metering = "时间"
            }
            if (res.data.process_detail.metering_para.decompressure_mode_before_metering == "distance") {
              res.data.process_detail.metering_para.decompressure_mode_before_metering = "距离"
            } else if (res.data.process_detail.metering_para.decompressure_mode_before_metering == "forbidden") {
              res.data.process_detail.metering_para.decompressure_mode_before_metering = "否"
            } else if (res.data.process_detail.metering_para.decompressure_mode_before_metering == "time") {
              res.data.process_detail.metering_para.decompressure_mode_before_metering = "时间"
            }
            this.origin_process.precondition = res.data.precondition
            this.origin_process.process_detail = res.data.process_detail

            // 注塑机信息
            this.origin_process.machine_info.id = res.data.precondition.machine_id

            // 获得模具的参数
            if(this.origin_process.precondition.mold_id){
              projectMethod.getDetail(this.origin_process.precondition.mold_id)
              .then(res => {
                if (res.data && JSON.stringify(res.data) != "{}") {
                  this.mold_info = res.data.mold_info
                }
              })
            }

            this.$message({
              message: "工艺参数读取完成!",
              type: "success"
            })
          } else {
            this.$message({
              message: "读取失败, 无工艺参数记录！",
              type: "warning"
            })
          }
        })
      } else {
        this.$message({
          message: "无效id, 读取工艺参数失败!",
          type: "warning"
        })
      }
    },
    resetView() {
      this.showDrawer = false,
      this.isclick = true,
      this.origin_process = {
        machine_info: {
          id: null,
          data_source: null,
          trademark: null,
          serial_no: null,
          power_method: null,

          pressure_unit: "MPa",
          backpressure_unit: "MPa",
          oc_pressure_unit: "MPa",
          oc_velocity_unit: "mm/s",
          position_unit: "mm",
          power_unit: "KW",
          temperature_unit: "℃",
          velocity_unit: "mm/s",
          time_unit: "s",
          clamping_force_unit: "Ton",
          screw_rotation_unit: "rpm",

          max_injection_volume: null,
          max_injection_stroke: null,
          screw_diameter: null,
          screw_unit_volume: null,

          cylinder_area: null,
          intensification_ratio: null,

          max_injection_pressure: null,
          max_injection_velocity: null,
          max_holding_pressure: null,
          max_holding_velocity: null,
          max_metering_pressure: null,
          max_screw_rotation_speed: null,
          max_metering_back_pressure: null,
          max_decompression_pressure: null,
          max_decompression_velocity: null,
          max_ejector_forward_velocity: null,
          max_ejector_backward_velocity: null,
          max_mold_opening_velocity: null,
          max_mold_clamping_velocity: null,

          max_set_ejector_forward_velocity: null,
          max_set_ejector_backward_velocity: null,
          max_set_mold_opening_velocity: null,
          max_set_mold_clamping_velocity: null,
          max_set_injection_pressure: null,
          max_set_injection_velocity: null,
          max_set_holding_pressure: null,
          max_set_holding_velocity: null,
          max_mold_open_stroke: null,
          max_ejection_stroke: null,
          max_set_metering_pressure: null,
          max_set_screw_rotation_speed: null,
          max_set_metering_back_pressure: null,
          max_set_decompression_pressure: null,
          max_set_decompression_velocity: null,

          max_injection_rate: null,
          max_holding_rate: null,
          max_decompression_rate: null,

          max_temperature_stage: null,
        },
        precondition: {
          mold_id: null,
          mold_no: null,
          cavity_num: null,
          runner_length: null,
          runner_weight: null,
          gate_type: null,
          gate_num: null,
          gate_shape: null,
          gate_area: null,
          gate_radius: null,
          gate_length: null,
          gate_width: null,

          product_no: null,
          product_type: null,
          product_name: null,
          product_total_weight: null,
          product_ave_thickness: null,
          product_max_thickness: null,
          product_max_length: null,

          machine_id: null,
          machine_data_source: null,
          machine_trademark: null,
          machine_serial_no: null,

          polymer_id: null,
          polymer_abbreviation: null,
          polymer_trademark: null,
        },
        process_detail: {
          title: "射台 #1", 
          name: "1",
          inject_para: {
            injection_stage: 6,
            max_injection_stage_option: 6,
            table_data: [
              { label: "压力", unit: "kgf/cm²", sections: initArray(6, null) },
              { label: "速度", unit: "mm/s", sections: initArray(6, null) },
              { label: "位置", unit: "mm", sections: initArray(6, null) }
            ],
            injection_time: null,
            injection_delay_time: null,
            cooling_time: null
          },
          holding_para: {
            holding_stage: 5,
            max_holding_stage_option: 5,
            table_data: [
              { label: "压力", unit: "kgf/cm²", sections: initArray(5, null) },
              { label: "速度", unit: "mm/s", sections: initArray(5, null) },
              { label: "时间", unit: "s", sections: initArray(5, null) }
            ]
          },
          VP_switch: {
            VP_switch_mode: null,
            VP_switch_position: null,
            VP_switch_time: null,
            VP_switch_pressure: null,
            VP_switch_velocity: null,
          },
          metering_para: {
            metering_stage: 4,
            max_metering_stage_option: 4,
            table_data: [
              { label: "压力", unit: "kgf/cm²", sections: initArray(4, null) },
              { label: "螺杆转速", unit: "rpm", sections: initArray(4, null) },
              { label: "背压", unit: "kgf/cm²", sections: initArray(4, null) },
              { label: "位置", unit: "mm", sections: initArray(4, null) }
            ],
            decompressure_mode_before_metering: "否",
            decompressure_mode_after_metering: "距离",
            decompressure_paras: [
              { label: "储前", pressure: null, velocity: null, time: null, distance: null },
              { label: "储后", pressure: null, velocity: null, time: null, distance: null }
            ],
            metering_delay_time: null,
            metering_ending_position: null
          },
          temp_para: {
            barrel_temperature_stage: 5,
            max_barrel_temperature_stage_option: 10,
            table_data: [
              { label: "温度", unit: "℃", sections: initArray(10, null) },
            ],
          },
          ejector_setting: {
            ejector_backward: {
              ejector_backward_stage: 4,
              max_ejector_backward_stage_option: 8,
              table_data: [
                { label: "压力", unit: "kgf/cm²", sections: initArray(8, null) },
                { label: "速度", unit: "mm/s", sections: initArray(8, null) },
                { label: "位置", unit: "mm", sections: initArray(8, null) },
              ]
            },
            ejector_forward: {
              ejector_forward_stage: 4,
              max_ejector_forward_stage_option: 8,
              table_data: [
                { label: "压力", unit: "kgf/cm²", sections: initArray(8, null) },
                { label: "速度", unit: "mm/s", sections: initArray(8, null) },
                { label: "位置", unit: "mm", sections: initArray(8, null) },
              ]
            },
            ejector_start_point: null,
            ejector_delay: null,
            ejector_keep: null,
            ejector_pause: null,
            ejector_blow_time: null,
            ejector_mode: null,
            ejector_times: null,
            ejector_on_opening: "关",
            ejector_stroke: null,
            ejector_force: null,
            set_torque: null,
          },
          opening_and_clamping_mold_setting: {
            mold_opening: {
              mold_opening_stage: 4,
              max_mold_opening_stage_option: 8,
              table_data: [
                { label: "压力", unit: "kgf/cm²", sections: initArray(8, null) },
                { label: "速度", unit: "mm/s", sections: initArray(8, null) },
                { label: "位置", unit: "mm", sections: initArray(8, null) },
              ],
            },
            mold_clamping: {
              mold_clamping_stage: 4,
              max_mold_clamping_stage_option: 8,
              table_data: [
                { label: "压力", unit: "kgf/cm²", sections: initArray(8, null) },
                { label: "速度", unit: "mm/s", sections: initArray(8, null) },
                { label: "位置", unit: "mm", sections: initArray(8, null) }
              ]
            },
            set_mold_clamping_force: null,
            using_robot: "否",
            using_tool: "否",
            reset_method: null,
            set_mold_protect_time: null,
            set_mold_protect_velocity: null,
            set_mold_protect_pressure: null,
            set_mold_protect_distance: null,
            opening_position_deviation: null,
            turnable_method: null,
            turnable_velocity: null,
          },
          loose_core: {
            core_movement_method: null,
            table_data: initArray(2, {
              core_switch_selection: null,
              core_mold_clamping_method: null,
              core_mold_opening_method: null,
              set_core_in_time: null,
              set_core_out_time: null,
              core_in_position: null,
              core_out_position: null,
            })
          },
        }
      },
      this.transplant_process = {
        machine_info: {
          id: null,
          data_source: null,
          trademark: null,
          serial_no: null,
          power_method: null,

          pressure_unit: "MPa",
          backpressure_unit: "MPa",
          oc_pressure_unit: "MPa",
          oc_velocity_unit: "mm/s",
          position_unit: "mm",
          power_unit: "KW",
          temperature_unit: "℃",
          velocity_unit: "mm/s",
          time_unit: "s",
          clamping_force_unit: "Ton",
          screw_rotation_unit: "rpm",

          max_injection_volume: null,
          max_injection_stroke: null,
          screw_diameter: null,
          screw_unit_volume: null,

          cylinder_area: null,
          intensification_ratio: null,

          max_injection_pressure: null,
          max_injection_velocity: null,
          max_holding_pressure: null,
          max_holding_velocity: null,
          max_metering_pressure: null,
          max_screw_rotation_speed: null,
          max_metering_back_pressure: null,
          max_decompression_pressure: null,
          max_decompression_velocity: null,
          max_ejector_forward_velocity: null,
          max_ejector_backward_velocity: null,
          max_mold_opening_velocity: null,
          max_mold_clamping_velocity: null,

          max_set_ejector_forward_velocity: null,
          max_set_ejector_backward_velocity: null,
          max_set_mold_opening_velocity: null,
          max_set_mold_clamping_velocity: null,
          max_set_injection_pressure: null,
          max_set_injection_velocity: null,
          max_set_holding_pressure: null,
          max_set_holding_velocity: null,
          max_set_metering_pressure: null,
          max_set_screw_rotation_speed: null,
          max_set_metering_back_pressure: null,
          max_set_decompression_pressure: null,
          max_set_decompression_velocity: null,
          max_mold_open_stroke: null,
          max_ejection_stroke: null,
          max_injection_rate: null,
          max_holding_rate: null,
          max_decompression_rate: null,
          
          max_temperature_stage: null,
        },
        precondition: {
          mold_id: null,
          mold_no: null,
          cavity_num: null,
          runner_length: null,
          runner_weight: null,
          gate_type: null,
          gate_num: null,
          gate_shape: null,
          gate_area: null,
          gate_radius: null,
          gate_length: null,
          gate_width: null,

          product_no: null,
          product_type: null,
          product_name: null,
          product_total_weight: null,
          product_ave_thickness: null,
          product_max_thickness: null,
          product_max_length: null,

          machine_id: null,
          machine_data_source: null,
          machine_trademark: null,
          machine_serial_no: null,

          polymer_id: null,
          polymer_abbreviation: null,
          polymer_trademark: null,
        },
        process_detail: {
          title: "射台 #1", 
          name: "1",
          inject_para: {
            injection_stage: 6,
            max_injection_stage_option: 6,
            table_data: [
              { label: "压力", unit: "kgf/cm²", sections: initArray(6, null) },
              { label: "速度", unit: "mm/s", sections: initArray(6, null) },
              { label: "位置", unit: "mm", sections: initArray(6, null) }
            ],
            injection_time: null,
            injection_delay_time: null,
            cooling_time: null
          },
          holding_para: {
            holding_stage: 5,
            max_holding_stage_option: 5,
            table_data: [
              { label: "压力", unit: "kgf/cm²", sections: initArray(5, null) },
              { label: "速度", unit: "mm/s", sections: initArray(5, null) },
              { label: "时间", unit: "s", sections: initArray(5, null) }
            ]
          },
          VP_switch: {
            VP_switch_mode: null,
            VP_switch_position: null,
            VP_switch_time: null,
            VP_switch_pressure: null,
            VP_switch_velocity: null,
          },
          metering_para: {
            metering_stage: 4,
            max_metering_stage_option: 4,
            table_data: [
              { label: "压力", unit: "kgf/cm²", sections: initArray(4, null) },
              { label: "螺杆转速", unit: "rpm", sections: initArray(4, null) },
              { label: "背压", unit: "kgf/cm²", sections: initArray(4, null) },
              { label: "位置", unit: "mm", sections: initArray(4, null) }
            ],
            decompressure_mode_before_metering: "否",
            decompressure_mode_after_metering: "距离",
            decompressure_paras: [
              { label: "储前", pressure: null, velocity: null, time: null, distance: null },
              { label: "储后", pressure: null, velocity: null, time: null, distance: null }
            ],
            metering_delay_time: null,
            metering_ending_position: null
          },
          temp_para: {
            barrel_temperature_stage: 5,
            max_barrel_temperature_stage_option: 10,
            table_data: [
              { label: "温度", unit: "℃", sections: initArray(10, null) },
            ],
          },
          ejector_setting: {
            ejector_backward: {
              ejector_backward_stage: 4,
              max_ejector_backward_stage_option: 8,
              table_data: [
                { label: "压力", unit: "kgf/cm²", sections: initArray(8, null) },
                { label: "速度", unit: "mm/s", sections: initArray(8, null) },
                { label: "位置", unit: "mm", sections: initArray(8, null) },
              ]
            },
            ejector_forward: {
              ejector_forward_stage: 4,
              max_ejector_forward_stage_option: 8,
              table_data: [
                { label: "压力", unit: "kgf/cm²", sections: initArray(8, null) },
                { label: "速度", unit: "mm/s", sections: initArray(8, null) },
                { label: "位置", unit: "mm", sections: initArray(8, null) },
              ]
            },
            ejector_start_point: null,
            ejector_delay: null,
            ejector_keep: null,
            ejector_pause: null,
            ejector_blow_time: null,
            ejector_mode: null,
            ejector_times: null,
            ejector_on_opening: "关",
            ejector_stroke: null,
            ejector_force: null,
            set_torque: null,
          },
          opening_and_clamping_mold_setting: {
            mold_opening: {
              mold_opening_stage: 4,
              max_mold_opening_stage_option: 8,
              table_data: [
                { label: "压力", unit: "kgf/cm²", sections: initArray(8, null) },
                { label: "速度", unit: "mm/s", sections: initArray(8, null) },
                { label: "位置", unit: "mm", sections: initArray(8, null) },
              ],
            },
            mold_clamping: {
              mold_clamping_stage: 4,
              max_mold_clamping_stage_option: 8,
              table_data: [
                { label: "压力", unit: "kgf/cm²", sections: initArray(8, null) },
                { label: "速度", unit: "mm/s", sections: initArray(8, null) },
                { label: "位置", unit: "mm", sections: initArray(8, null) }
              ]
            },
            set_mold_clamping_force: null,
            using_robot: "否",
            using_tool: "否",
            reset_method: null,
            set_mold_protect_time: null,
            set_mold_protect_velocity: null,
            set_mold_protect_pressure: null,
            set_mold_protect_distance: null,
            opening_position_deviation: null,
            turnable_method: null,
            turnable_velocity: null,
          },
          loose_core: {
            core_movement_method: null,
            table_data: initArray(2, {
              core_switch_selection: null,
              core_mold_clamping_method: null,
              core_mold_opening_method: null,
              set_core_in_time: null,
              set_core_out_time: null,
              core_in_position: null,
              core_out_position: null,
            })
          },
        }
      },
      this.origin_result = [],
      this.transplant_result = [],
      this.sum = 0
    },
    setViewUnit(machine_info) {
      if (machine_info.id) {
        machineMethod
        .getDetail(machine_info.id)
        .then((res) => {
          if (res.status === 0 && res.data) {

            // 获取机器的最大设定值
            machine_info.max_injection_stroke =
              res.data.injectors_info[0].max_injection_stroke;

            machine_info.max_injection_pressure =
              res.data.injectors_info[0].max_injection_pressure;
            machine_info.max_set_injection_pressure =
              res.data.injectors_info[0].max_set_injection_pressure;

            machine_info.max_injection_velocity =
              res.data.injectors_info[0].max_injection_velocity;
            machine_info.max_set_injection_velocity =
              res.data.injectors_info[0].max_set_injection_velocity;

            machine_info.max_holding_pressure =
              res.data.injectors_info[0].max_holding_pressure;
            machine_info.max_set_holding_pressure =
              res.data.injectors_info[0].max_set_holding_pressure;

            machine_info.max_holding_velocity =
              res.data.injectors_info[0].max_holding_velocity;
            machine_info.max_set_holding_velocity =
              res.data.injectors_info[0].max_set_holding_velocity;

            machine_info.max_metering_pressure =
              res.data.injectors_info[0].max_metering_pressure;  
            machine_info.max_set_metering_pressure =
              res.data.injectors_info[0].max_set_metering_pressure;    

            machine_info.max_screw_rotation_speed =
              res.data.injectors_info[0].max_screw_rotation_speed;
            machine_info.max_set_screw_rotation_speed =
              res.data.injectors_info[0].max_set_screw_rotation_speed;

            machine_info.max_metering_back_pressure =
              res.data.injectors_info[0].max_metering_back_pressure;
            machine_info.max_set_metering_back_pressure =
              res.data.injectors_info[0].max_set_metering_back_pressure;

            machine_info.max_decompression_velocity =
              res.data.injectors_info[0].max_decompression_velocity;
            machine_info.max_set_decompression_velocity =
              res.data.injectors_info[0].max_set_decompression_velocity;

            machine_info.max_decompression_pressure =
              res.data.injectors_info[0].max_decompression_pressure;
            machine_info.max_set_decompression_pressure =
              res.data.injectors_info[0].max_set_decompression_pressure;

            machine_info.max_mold_clamping_velocity =
              res.data.injectors_info[0].max_mold_clamping_velocity;
            machine_info.max_set_mold_clamping_velocity =
              res.data.injectors_info[0].max_set_mold_clamping_velocity;
              
            machine_info.max_mold_opening_velocity =
              res.data.injectors_info[0].max_mold_opening_velocity;
            machine_info.max_set_mold_opening_velocity =
              res.data.injectors_info[0].max_set_mold_opening_velocity;

            machine_info.max_ejector_backward_velocity =
              res.data.injectors_info[0].max_ejector_backward_velocity;
            machine_info.max_set_ejector_backward_velocity =
              res.data.injectors_info[0].max_set_ejector_backward_velocity;

            machine_info.max_ejector_forward_velocity =
              res.data.injectors_info[0].max_ejector_forward_velocity;
            machine_info.max_set_ejector_forward_velocity =
              res.data.injectors_info[0].max_set_ejector_forward_velocity;
            
            machine_info.max_mold_open_stroke =
                res.data.max_mold_open_stroke;
            machine_info.max_ejection_stroke =
              res.data.max_ejection_stroke;

            machine_info.max_injection_rate = 
              res.data.injectors_info[0].max_injection_rate;
            machine_info.max_holding_rate = 
              res.data.injectors_info[0].max_holding_rate;
            machine_info.max_decompression_rate = 
              res.data.injectors_info[0].max_decompression_rate;

            machine_info.power_method = res.data.power_method
            machine_info.cylinder_area = res.data.injectors_info[0].cylinder_area
            machine_info.intensification_ratio = res.data.injectors_info[0].intensification_ratio

            // 最大料筒段数
            machine_info.max_temperature_stage = res.data.injectors_info[0].max_temperature_stage

            // 获取螺杆磨损情况
            machine_info.slope = res.data.slope
            machine_info.intercept = res.data.intercept

            // 模具是否匹配注塑机
            machine_info.machine_type = res.data.machine_type
            machine_info.machine_type = res.data.machine_type
            machine_info.max_clamping_force = res.data.max_clamping_force
            machine_info.max_injection_weight = res.data.injectors_info[0].max_injection_weight
            machine_info.min_mold_size_horizon = res.data.min_mold_size_horizon
            machine_info.min_mold_size_vertical = res.data.min_mold_size_vertical
            machine_info.min_mold_thickness = res.data.min_mold_thickness
            machine_info.max_mold_size_horizon = res.data.max_mold_size_horizon
            machine_info.max_mold_size_vertical = res.data.max_mold_size_vertical
            machine_info.max_mold_thickness = res.data.max_mold_thickness
            machine_info.locate_ring_diameter = res.data.locate_ring_diameter
            machine_info.max_ejection_force = res.data.max_ejection_force
            machine_info.max_ejection_stroke = res.data.max_ejection_stroke
            machine_info.max_mold_open_stroke = res.data.max_mold_open_stroke
            machine_info.nozzle_sphere_diameter = res.data.injectors_info[0].nozzle_sphere_diameter
            machine_info.nozzle_hole_diameter = res.data.injectors_info[0].nozzle_hole_diameter
          }
        });
      }
    },
    processTransplant() {
      // 流动性好的塑料：PE、PP、PS、PA6、PBT、LCP等；
      // 流动性中等的塑料：HIPS、ABS、AS、PMMA、POM等 ；
      // 流动性差的塑料：PC、硬PVC、PPO、PSF等 
      let value = 0.2
      if(["PE","PP","PS","PA6","PBT","LCP"].includes(this.origin_process.precondition.polymer_abbreviation)){
        value = 0.15
      }
      if(["HIPS","ABS","AS","PMMA","POM"].includes(this.origin_process.precondition.polymer_abbreviation)){
        value = 0.125
      }
      if(["PC","硬PVC","PPO","PSF","PA66"].includes(this.origin_process.precondition.polymer_abbreviation)){
        value = 0.10
      } 
      let VP_switch_position = (this.transplant_process.machine_info.max_injection_stroke * value).toFixed(2)
      processTransfer(
        this.origin_process.machine_info, 
        this.origin_process.process_detail, 
        this.transplant_process.machine_info,
        this.transplant_process.process_detail,
        VP_switch_position
      )
      // 如果VP切换位置+注射行程(即终止位置)>注塑机最大注射行程，那么提供选项：减少VP切换位置
      if(Number(this.transplant_process.process_detail.metering_para.metering_ending_position) > Number(this.transplant_process.machine_info.max_injection_stroke)){
        let diff = (Number(this.transplant_process.process_detail.metering_para.metering_ending_position) - Number(this.transplant_process.machine_info.max_injection_stroke)).toFixed(0)
        this.$prompt('终止位置超过注塑机最大注射行程'+diff+'mm。是否要调小VP切换位置?输入新的VP切换位置', '提示', {
          confirmButtonText: '确认调整',
          cancelButtonText: '不调整',
          inputValue: `${VP_switch_position}`,
        }).then((value) => {
          processTransfer(
            this.origin_process.machine_info, 
            this.origin_process.process_detail, 
            this.transplant_process.machine_info,
            this.transplant_process.process_detail,
            value.value
          )
          this.$message({ type: "success", message: "已调整VP切换位置" });
          this.checkValid()
        }).catch(() => {
          this.$message({ type: "info", message: "不调整" });
        });
      }

      this.checkValid()
    },
    getClick(msg) {
      if (msg != undefined) {
        this.isclick = msg
      }
    },
    checkMachine() {
      this.setViewUnit(this.transplant_process.machine_info)
      this.setViewUnit(this.origin_process.machine_info)
      if(this.origin_process.precondition.mold_id){
        projectMethod.getDetail(this.origin_process.precondition.mold_id)
        .then(res => {
          if (res.data && JSON.stringify(res.data) != "{}") {
            this.mold_info = res.data.mold_info
          }
        })
      }
      setTimeout(()=> {
        this.checkValidBeforeTransfer()
        this.sum++
      },500)
    },
    checkValidBeforeTransfer(){
      // 检查原始工艺
      if(!this.origin_process.machine_info.id){
        this.$message({
          message: "请读取要转换的原始工艺",
          type: "warning"
        })
        window.scrollTo(0, document.getElementById("origin_machine").offsetTop-40)
        return false
      }
      // 检查转换机台
      if(!this.transplant_process.machine_info.id){
        this.$message({
          message: "请选择转换机台",
          type: "warning"
        })
        window.scrollTo(0, document.getElementById("transfer_machine").offsetTop-40)
        return false
      }
      // 先检查模具参数是否齐全
      let error = [ "模具参数的" ]
      checkValidMold(this.mold_info, error)
      if (error == "模具参数的"){
        error.push("参数合格")
      }
      this.mold_result = error

      error = [ "原始机台的" ]
      checkValidTransfer(this.origin_process.machine_info, error)
      if (error == "原始机台的"){
        error.push("参数合格")
      }
      this.origin_result = error

      error = [ "转换机台的" ]
      checkValidTransfer(this.transplant_process.machine_info, error)
      // 检查转换机台模具类参数是否齐全
      checkValidTransferMachine(this.transplant_process.machine_info, error)
      if (error == "转换机台的"){
        error.push("参数合格")
      }
      this.transplant_result = error

      // 检查转换机台是否适合该模具
      error = [ "模具和转换机台适配的" ]
      let yellow = checkValidAdaption(this.transplant_process.machine_info, error, this.mold_info)
      if (error == "模具和转换机台适配的" || error.length -yellow ==1){
        error.push("参数合格")
      }
      this.machine_adaption_result = error

      this.showDrawer = true
      if (this.origin_result.indexOf("参数合格") != -1 && this.transplant_result.indexOf("参数合格") != -1 && this.mold_result.indexOf("参数合格") != -1 && this.machine_adaption_result.indexOf("参数合格") != -1) {
        this.isclick = false
        return
      } else {
        this.getClick()
      }
    },
    checkValid() {
      //螺杆判断位置
      //切换位置<注射4段位置<注射3段位置<注射2段位置<注射1段位置<储料位置<储料1段位置<储料2段位置<储料3段位置<储料4段位置<最大注射行程
      // let screw_positions = [
      //   "最大注射行程",
      //   "螺杆终止位置",
      //   "储料4段位置",
      //   "储料3段位置",
      //   "储料2段位置",
      //   "储料1段位置",
      //   "注射1段位置",
      //   "注射2段位置",
      //   "注射3段位置",
      //   "注射4段位置",
      //   "注射5段位置",
      //   "注射6段位置",
      //   "VP切换位置",
      // ]

      // 切换位置<注射4段位置<注射3段位置<注射2段位置<注射1段位置<熔胶终止位置<最大注射行程
      // 储料1段位置<储料2段位置<储料3段位置<储料4段位置<熔胶终止位置<最大注射行程
      let screw_positions = [
        "最大注射行程",
        "螺杆终止位置",
        "注射1段位置",
        "注射2段位置",
        "注射3段位置",
        "注射4段位置",
        "注射5段位置",
        "注射6段位置",
        "VP切换位置",
      ]
      let storing_positions = [
        "最大注射行程",
        "螺杆终止位置",
        "储料4段位置",
        "储料3段位置",
        "储料2段位置",
        "储料1段位置",
      ]
      let mold_opening_positions = [
        "最大开模行程",
        "开模8段位置",
        "开模7段位置",
        "开模6段位置",
        "开模5段位置",
        "开模4段位置",
        "开模3段位置",
        "开模2段位置",
        "开模1段位置"
      ]
      let mold_clamping_positions = [
        "最大开模行程",
        "合模1段位置",
        "合模2段位置",
        "合模3段位置",
        "合模4段位置",
        "合模5段位置",
        "合模6段位置",
        "合模7段位置",
        "合模8段位置"
      ]
      let ejector_backward_positions = [
        "最大顶出行程",
        "顶针后退1段位置",
        "顶针后退2段位置",
        "顶针后退3段位置",
        "顶针后退4段位置",
        "顶针后退5段位置",
        "顶针后退6段位置",
        "顶针后退7段位置",
        "顶针后退8段位置",
      ]
      let ejector_forward_positions = [
        "最大顶出行程",
        "顶针前进8段位置",
        "顶针前进7段位置",
        "顶针前进6段位置",
        "顶针前进5段位置",
        "顶针前进4段位置",
        "顶针前进3段位置",
        "顶针前进2段位置",
        "顶针前进1段位置",
      ]
     
      let posi_para_record = {}

      let mac_info = this.transplant_process.machine_info
      posi_para_record["最大注射行程"] = { "element_id": "NULL", "value": mac_info.max_injection_stroke }
    
      let metering_para = this.transplant_process.process_detail.metering_para
      posi_para_record["螺杆终止位置"] = { "element_id": "MEL", "value": metering_para.metering_ending_position }

      for (let i = 0; i < metering_para.metering_stage; i++) {
        posi_para_record["储料" + Number(i+1) + "段位置"] = {
          "element_id": "ML" +i,
          "value": metering_para.table_data[3].sections[i]
        }
      }

      let inject_para = this.transplant_process.process_detail.inject_para
      for (let i = 0; i < inject_para.injection_stage; i++) {
        posi_para_record["注射" + Number(i + 1) + "段位置"] = {
          "element_id": "IL" + i,
          "value": inject_para.table_data[2].sections[i]
        }
      }

      let VP_switch = this.transplant_process.process_detail.VP_switch
      posi_para_record["VP切换位置"] = { "element_id": "VPTL", "value": VP_switch.VP_switch_position }

      let mold_opening = this.transplant_process.process_detail.opening_and_clamping_mold_setting.mold_opening
      for (let i = 0; i < mold_opening.mold_opening_stage; i++) {
        posi_para_record["开模" + Number(i + 1) + "段位置"] = {
          "element_id": "MOP" + i,
          "value": mold_opening.table_data[2].sections[i]
        }
      }

      let mold_clamping = this.transplant_process.process_detail.opening_and_clamping_mold_setting.mold_clamping
      for (let i = 0; i < mold_clamping.mold_clamping_stage; i++) {
        posi_para_record["合模" + Number(i + 1) + "段位置"] = {
          "element_id": "MCP" + i,
          "value": mold_clamping.table_data[2].sections[i]
        }
      }

      let ejector_backward = this.transplant_process.process_detail.ejector_setting.ejector_backward
      for (let i = 0; i < ejector_backward.ejector_backward_stage; i++) {
        posi_para_record["顶针后退" + Number(i + 1) + "段位置"] = {
          "element_id": "EBP" + i,
          "value": ejector_backward.table_data[2].sections[i]
        }
      }

      let ejector_forward = this.transplant_process.process_detail.ejector_setting.ejector_forward
      for (let i = 0; i < ejector_forward.ejector_forward_stage; i++) {
        posi_para_record["顶针前进" + Number(i + 1) + "段位置"] = {
          "element_id": "EFP" + i,
          "value": ejector_forward.table_data[2].sections[i]
        }
      }

      for (let i = 1; i < screw_positions.length; i++) {
        let last_item = posi_para_record[screw_positions[i - 1]]
        if (last_item && last_item.value) {
          for (let j = i; j < screw_positions.length; j++) {
            let curr_item = posi_para_record[screw_positions[j]]
            if (curr_item && curr_item.value ) {
              if (Number(curr_item.value) > Number(last_item.value) && Number(last_item.value) > 0) {
                this.timer = window.setTimeout(() => {
                  this.$notify({
                    title: '提示!',
                    message: this.$createElement('i', { style: 'color: teal'}, screw_positions[j] + "的值大于" + screw_positions[i - 1] + "的值，不符合要求！")
                  })
                })
                // this.setElementStyle(document.getElementById(curr_item.element_id), "#highlight")
              } else {
                // this.setElementStyle(document.getElementById(curr_item.element_id), "#normal")
              }
            }
          }
        }
      }
      for (let i = 1; i < storing_positions.length; i++) {
        let last_item = posi_para_record[storing_positions[i - 1]]
        if (last_item && last_item.value) {
          for (let j = i; j < storing_positions.length; j++) {
            let curr_item = posi_para_record[storing_positions[j]]
            if (curr_item && curr_item.value) {
              if (Number(curr_item.value) > Number(last_item.value) && Number(last_item.value) > 0) {
                this.timer = window.setTimeout(() => {
                  this.$notify({
                    title: '提示!',
                    message: this.$createElement('i', { style: 'color: teal' }, storing_positions[j] + "的值大于" + storing_positions[i - 1] + "的值，不符合要求")
                  })
                })
                // this.setElementStyle(document.getElementById(curr_item.element_id), "#highlight")
              } else {
                // this.setElementStyle(document.getElementById(curr_item.element_id), "#normal")
              }
            }
          }
        }
      }

      for (let i = 1; i < mold_opening_positions.length; i++) {
        let last_item = posi_para_record[mold_opening_positions[i - 1]]
        if (last_item && last_item.value) {
          for (let j = i; j < mold_opening_positions.length; j++) {
            let curr_item = posi_para_record[mold_opening_positions[j]]
            if (curr_item && curr_item.value) {
              if (Number(curr_item.value) > Number(last_item.value) && Number(last_item.value) > 0) {
                this.timer = window.setTimeout(() => {
                  this.$notify({
                    title: '提示!',
                    message: this.$createElement('i', { style: 'color: teal' }, mold_opening_positions[j] + "的值大于" + mold_opening_positions[i - 1] + "的值，不符合要求")
                  })
                })
                // this.setElementStyle(document.getElementById(curr_item.element_id), "#highlight")
              } else {
                // this.setElementStyle(document.getElementById(curr_item.element_id), "#normal")
              }
            }
          }
        }
      }
      //合模第一段位置要比开模最后一段位置小
      let mc_positions_first = posi_para_record[mold_clamping_positions[1]]
      let a = this.transplant_process.process_detail.opening_and_clamping_mold_setting.mold_opening.mold_opening_stage
      let ml_positions_last = posi_para_record[mold_opening_positions[9-a]]
      if (mc_positions_first && mc_positions_first.value && ml_positions_last && ml_positions_last.value) {
        if (Number(mc_positions_first.value) > Number(ml_positions_last.value)) {
          this.timer = window.setTimeout(() => {
            this.$notify({
              title: '提示!',
              message: this.$createElement('i', { style: 'color: teal' }, mold_clamping_positions[1] + "的值大于" + mold_opening_positions[9-a] + "的值，不符合要求")
            })
          })
          // this.setElementStyle(document.getElementById(mc_positions_first.element_id), "#highlight")
        } else {
          // this.setElementStyle(document.getElementById(mc_positions_first.element_id), '#normal')
        }
      }

      for (let i = 1; i < mold_clamping_positions.length; i++) {
        let last_item = posi_para_record[mold_clamping_positions[i - 1]]
        if (last_item && last_item.value) {
          for (let j = i; j < mold_clamping_positions.length; j++) {
            let curr_item = posi_para_record[mold_clamping_positions[j]]
            if (curr_item && curr_item.value) {
              if (Number(curr_item.value) > Number(last_item.value) && Number(last_item.value) > 0) {
                this.timer = window.setTimeout(() => {
                  this.$notify({
                    title: '提示!',
                    message: this.$createElement('i', { style: 'color: teal' }, mold_clamping_positions[j] + "的值大于" + mold_clamping_positions[i - 1] + "的值，不符合要求")
                  })
                })
                // this.setElementStyle(document.getElementById(curr_item.element_id), "#highlight")
              } else {
                // this.setElementStyle(document.getElementById(curr_item.element_id), '#normal')
              }
            }
          }
        }
      }

      for (let i = 1; i < ejector_backward_positions.length; i++) {
        let last_item = posi_para_record[ejector_backward_positions[i - 1]]
        if (last_item && last_item.value) {
          for (let j = i; j < ejector_backward_positions.length; j++) {
            let curr_item = posi_para_record[ejector_backward_positions[j]]
            if (curr_item && curr_item.value) {
              if (Number(curr_item.value) > Number(last_item.value) && Number(last_item.value) > 0) {
                this.timer = window.setTimeout(() => {
                  this.$notify({
                    title: '提示!',
                    message: this.$createElement('i', { style: 'color: teal' }, ejector_backward_positions[j] + "的值大于" + ejector_backward_positions[i - 1] + "的值，不符合要求")
                  })
                })
                // this.setElementStyle(document.getElementById(curr_item.element_id), "#highlight")
              } else {
                // this.setElementStyle(document.getElementById(curr_item.element_id), '#normal')
              }
            }
          }
        }
      }

      for (let i = 1; i < ejector_forward_positions.length; i++) {
        let last_item = posi_para_record[ejector_forward_positions[i - 1]]
        if (last_item && last_item.value) {
          for (let j = i; j < ejector_forward_positions.length; j++) {
            let curr_item = posi_para_record[ejector_forward_positions[j]]
            if (curr_item && curr_item.value) {
              if (Number(curr_item.value) > Number(last_item.value) && Number(last_item.value) > 0) {
                this.timer = window.setTimeout(() => {
                  this.$notify({
                    title: '提示!',
                    message: this.$createElement('i', { style: 'color: teal' }, ejector_forward_positions[j] + "的值大于" + ejector_forward_positions[i - 1] + "的值，不符合要求")
                  })
                })
                // this.setElementStyle(document.getElementById(curr_item.element_id), "#highlight")
              } else {
                // this.setElementStyle(document.getElementById(curr_item.element_id), '#normal')
              }
            }
          }
        }
      }
      let compare_list = []
      //注射参数
      for (let i = 0; i < inject_para.injection_stage; i++) {
        compare_list.push({
          "set_val": inject_para.table_data[0].sections[i],
          "max_val": mac_info.max_set_injection_pressure,
          "set_val_label": "注射" + Number(i + 1) + "段压力",
          "max_val_label": "机器最大注射压力",
          "element_id": "IP" + i
        })
        compare_list.push({
          "set_val": inject_para.table_data[1].sections[i],
          "max_val": mac_info.max_set_injection_velocity,
          "set_val_label": "注射" + Number(i + 1) + "段速度",
          "max_val_label": "机器最大注射速度",
          "element_id": "IV" + i
        })
      }
      //保压参数
      let holding_para = this.transplant_process.process_detail.holding_para
      for (let i = 0; i < holding_para.holding_stage; ++i) {
        compare_list.push({
          "set_val": holding_para.table_data[0].sections[i],
          "max_val": mac_info.max_set_holding_pressure,
          "set_val_label": "保压" + Number(i + 1) + "段压力",
          "max_val_label": "机器最大保压压力",
          "element_id": "PP" + i
        })
        compare_list.push({
          "set_val": holding_para.table_data[1].sections[i],
          "max_val": mac_info.max_set_holding_velocity,
          "set_val_label": "保压" + Number(i + 1) + "段速度",
          "max_val_label": "机器最大保压速度",
          "element_id": "PV" + i
        })
      }
      //储料参数
      for (let i = 0; i < metering_para.metering_stage; ++i) {
        compare_list.push({
          "set_val": metering_para.table_data[0].sections[i],
          "max_val": mac_info.max_set_metering_pressure,
          "set_val_label": "熔胶" + Number(i + 1) + "段压力",
          "max_val_label": "机器最大注射压力",
          "element_id": "MP" + i
        })
        compare_list.push({
          "set_val": metering_para.table_data[1].sections[i],
          "max_val": mac_info.max_set_screw_rotation_speed,
          "set_val_label": "熔胶" + Number(i + 1) + "段螺杆转速",
          "max_val_label": "机器最大注射速度",
          "element_id": "MSR" + i
        })
        compare_list.push({
          "set_val": metering_para.table_data[2].sections[i],
          "max_val": mac_info.max_set_metering_back_pressure,
          "set_val_label": "熔胶" + Number(i + 1) + "段背压",
          "max_val_label": "机器最大熔胶背压",
          "element_id": "MBP" + i
        })
      }
      compare_list.push({
        "set_val": metering_para.decompressure_paras[0].pressure,
        "max_val": mac_info.max_set_decompression_pressure,
        "set_val_label": "储前松退压力",
        "max_val_label": "机器最大松退压力",
        "element_id": "DPBM"
      })
      compare_list.push({
        "set_val": metering_para.decompressure_paras[0].velocity,
        "max_val": mac_info.max_set_decompression_velocity,
        "set_val_label": "储前松退速度",
        "max_val_label": "机器最大松退速度",
        "element_id": "DVBM"
      })
      compare_list.push({
        "set_val": metering_para.decompressure_paras[1].pressure,
        "max_val": mac_info.max_set_decompression_pressure,
        "set_val_label": "储后松退压力",
        "max_val_label": "机器最大松退压力",
        "element_id": "DPAM"
      })
      compare_list.push({
        "set_val": metering_para.decompressure_paras[1].velocity,
        "max_val": mac_info.max_set_decompression_velocity,
        "set_val_label": "储后射退速度",
        "max_val_label": "机器最大射退速度",
        "element_id": "DVAM"
      })
      // 开模参数
      let mold_opening_para = this.transplant_process.process_detail.opening_and_clamping_mold_setting.mold_opening
      for (let i = 0; i < mold_opening_para.mold_opening_stage; i++) {
        compare_list.push({
          "set_val": mold_opening_para.table_data[2].sections[i],
          "max_val": mac_info.max_mold_open_stroke,
          "set_val_label": "开模" + Number(i + 1) + "段位置",
          "max_val_label": "机器最大开模行程",
          "element_id": "MOP" + i
        })
        compare_list.push({
          "set_val": mold_opening_para.table_data[1].sections[i],
          "max_val": mac_info.max_set_mold_opening_velocity,
          "set_val_label": "开模" + Number(i + 1) + "段速度",
          "max_val_label": "机器最大可设定开模速度",
          "element_id": "MOS" + i
        })
      }
      // 合模参数
      let mold_clamping_para = this.transplant_process.process_detail.opening_and_clamping_mold_setting.mold_clamping
      for (let i = 0; i < mold_clamping_para.mold_clamping_stage; i++) {
        compare_list.push({
          "set_val": mold_clamping_para.table_data[2].sections[i],
          "max_val": mac_info.max_mold_open_stroke,
          "set_val_label": "合模" + Number(i + 1) + "段位置",
          "max_val_label": "机器最大开模行程",
          "element_id": "MCP" + i
        })
        compare_list.push({
          "set_val": mold_clamping_para.table_data[1].sections[i],
          "max_val": mac_info.max_set_mold_clamping_velocity,
          "set_val_label": "合模" + Number(i + 1) + "段速度",
          "max_val_label": "机器最大可设定合模速度",
          "element_id": "MCS" + i
        })
      }
      // 顶针后退参数
      let ejector_backward_para = this.transplant_process.process_detail.ejector_setting.ejector_backward
      for (let i = 0; i < ejector_backward_para.ejector_backward_stage; i++) {
        compare_list.push({
          "set_val": ejector_backward_para.table_data[2].sections[i],
          "max_val": mac_info.max_ejection_stroke,
          "set_val_label": "顶针后退" + Number(i + 1) + "段位置",
          "max_val_label": "机器最大顶出行程",
          "element_id": "EBP" + i
        })
        compare_list.push({
          "set_val": ejector_backward_para.table_data[1].sections[i],
          "max_val": mac_info.max_set_ejector_backward_velocity,
          "set_val_label": "顶针后退" + Number(i + 1) + "段速度",
          "max_val_label": "机器最大可设定顶退速度",
          "element_id": "EBS" + i
        })
      }
      // 顶针前进参数
      let ejector_forward_para = this.transplant_process.process_detail.ejector_setting.ejector_forward
      for (let i = 0; i < ejector_forward_para.ejector_forward_stage; i++) {
        compare_list.push({
          "set_val": ejector_forward_para.table_data[2].sections[i],
          "max_val": mac_info.max_ejection_stroke,
          "set_val_label": "顶针前进" + Number(i + 1) + "段位置",
          "max_val_label": "机器最大顶出行程",
          "element_id": "EFP" + i
        })
        compare_list.push({
          "set_val": ejector_forward_para.table_data[1].sections[i],
          "max_val": mac_info.max_set_ejector_forward_velocity,
          "set_val_label": "顶针前进" + Number(i + 1) + "段速度",
          "max_val_label": "机器最大可设定顶进速度",
          "element_id": "EFS" + i
        })
      }
      for (let i = 0; i < compare_list.length; ++i) {
        let item = compare_list[i]
        if (item.set_val && item.max_val && item.set_val !== "Infinity") {
          if (Number(item.set_val) > Number(item.max_val)) {
            this.timer = window.setTimeout(() => {
              this.$notify({
                title: '提示!',
                message: this.$createElement('i', { style: 'color: teal'}, item.set_val_label + "的设定值为: " + item.set_val 
                  + ", 大于" + item.max_val_label + "最大可设定值: " + item.max_val 
                  + ", 不符合要求！"),
              })
            })
            // this.setElementStyle(document.getElementById(String(item.element_id)), "#highlight");
          } else {
            // this.setElementStyle(document.getElementById(String(item.element_id)), "#normal");  
          }
        }
      }
    },
    saveTransferProcess() {
      let process_index = {
        company_id: UserModule.company_id,
        status: 2,
        process_no: "P" + datetimeTodayStr(),
        data_sources: "工艺移植",
        mold_trials_no: this.origin_process_index_id,  // 保存原始工艺id

        mold_id: this.origin_process.precondition.mold_id,
        mold_no: this.origin_process.precondition.mold_no,
        cavity_num: this.origin_process.precondition.cavity_num,
        runner_length: this.origin_process.precondition.runner_length,
        runner_weight: this.origin_process.precondition.runner_weight,
        gate_type: this.origin_process.precondition.gate_type,
        gate_num: this.origin_process.precondition.gate_num,
        gate_shape: this.origin_process.precondition.gate_shape,
        gate_area: this.origin_process.precondition.gate_area,
        gate_radius: this.origin_process.precondition.gate_radius,
        gate_length: this.origin_process.precondition.gate_length,
        gate_width: this.origin_process.precondition.gate_width,

        product_no: this.origin_process.precondition.product_no,
        product_type: this.origin_process.precondition.product_type,
        product_name: this.origin_process.precondition.product_name,
        product_total_weight: this.origin_process.precondition.product_total_weight,
        product_ave_thickness: this.origin_process.precondition.product_ave_thickness,
        product_max_thickness: this.origin_process.precondition.product_max_thickness,
        product_max_length: this.origin_process.precondition.product_max_length,

        machine_id: this.transplant_process.machine_info.id,
        machine_data_source: this.transplant_process.machine_info.data_source,
        machine_trademark: this.transplant_process.machine_info.trademark,
        machine_serial_no: this.transplant_process.machine_info.serial_no,

        polymer_id: this.origin_process.precondition.polymer_id,
        polymer_abbreviation: this.origin_process.precondition.polymer_abbreviation,
        polymer_trademark: this.origin_process.precondition.polymer_trademark,
      }
      processIndexMethod.add(process_index)
      .then(res => {
        if (res.status === 0) {
          let process_index_id = res.data.id

          this.transplant_process.precondition.mold_id = res.data.mold_id
          this.transplant_process.precondition.data_sources = res.data.data_sources
          this.transplant_process.precondition.mold_trials_no = res.data.mold_trials_no
          this.transplant_process.precondition.mold_no = res.data.mold_no
          this.transplant_process.precondition.cavity_num = res.data.cavity_num
          this.transplant_process.precondition.runner_length = res.data.runner_length
          this.transplant_process.precondition.runner_weight = res.data.runner_weight
          this.transplant_process.precondition.gate_type = res.data.gate_type
          this.transplant_process.precondition.gate_num = res.data.gate_num
          this.transplant_process.precondition.gate_shape = res.data.gate_shape
          this.transplant_process.precondition.gate_area = res.data.gate_area
          this.transplant_process.precondition.gate_radius = res.data.gate_radius
          this.transplant_process.precondition.gate_length = res.data.gate_length
          this.transplant_process.precondition.gate_width = res.data.gate_width

          this.transplant_process.precondition.product_no = res.data.product_no
          this.transplant_process.precondition.product_type = res.data.product_type
          this.transplant_process.precondition.product_name = res.data.product_name
          this.transplant_process.precondition.product_total_weight = res.data.product_total_weight
          this.transplant_process.precondition.product_ave_thickness = res.data.product_ave_thickness
          this.transplant_process.precondition.product_max_thickness = res.data.product_max_thickness
          this.transplant_process.precondition.product_max_length = res.data.product_max_length

          this.transplant_process.precondition.machine_id = res.data.machine_id
          this.transplant_process.precondition.machine_data_source = res.data.machine_data_source
          this.transplant_process.precondition.machine_trademark = res.data.machine_trademark

          this.transplant_process.precondition.polymer_id = res.data.polymer_id
          this.transplant_process.precondition.polymer_abbreviation = res.data.polymer_abbreviation
          this.transplant_process.precondition.polymer_trademark = res.data.polymer_trademark

          let precondition = this.transplant_process.precondition

          let process_detail = {
            title: this.transplant_process.process_detail.title,
            name: this.transplant_process.process_detail.name,
            inject_para: this.transplant_process.process_detail.inject_para,
            holding_para: this.transplant_process.process_detail.holding_para,
            VP_switch: this.transplant_process.process_detail.VP_switch,
            metering_para: this.transplant_process.process_detail.metering_para,
            temp_para: this.transplant_process.process_detail.temp_para,
            ejector_setting: this.transplant_process.process_detail.ejector_setting,
            opening_and_clamping_mold_setting: this.transplant_process.process_detail.opening_and_clamping_mold_setting,
            loose_core: this.transplant_process.process_detail.loose_core,
          }

          // 保存工艺记录
          let record_para = {
            "process_index_id": process_index_id,
            "precondition": precondition,
            "process_detail": process_detail
          }
          processRecordMethod.add(record_para)
          .then(res => {
            if (res.status === 0) {
              this.$message({
                message: "工艺参数数据已上传至数据库！",
                type: "success"
              })
              location.reload()
            }
          })
          .finally(() => {
            this.loading = false
          })
        }
      })
    },
    setElementStyle(element, style) {
      if (element && style === "#highlight") {
        element.style.backgroundColor = "red";
        element.style.color = "white";
      } else if (element && style === "#normal") {
        element.style.backgroundColor = "white";
        element.style.color = "black";
      }
    }
  },
  watch: {
    "transplant_process.machine_info.id": function() {
      this.setViewUnit(this.transplant_process.machine_info)
    },
    "origin_process.machine_info.id": function() {
      this.setViewUnit(this.origin_process.machine_info)
    },
  }
};
</script>

<style lang="scss" scoped>
  .el-input {
    width: 10rem;
  }
  .el-autocomplete {
    width: 10rem;
  }
  .buttonGroup {
    z-index: 999;
    position: fixed;
    text-align: center;
    width: 100%;
    bottom: 5px;
    font-size: 11px;
    line-height: 32px;
    margin: 0;
    height: 40px;
    .el-button {
      width: 8rem;
    }
  }
  .MacProcessTransplant {
    overflow: auto;
    height: inherit;
  }
</style>
