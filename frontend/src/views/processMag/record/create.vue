<template>
  <div>
    <el-card class="box-card">
      <div slot="header" class="clearfix">
        <span>基本信息</span>
      </div>
      <precondition-form
        :precondition-detail="form_info.precondition"
        :max-inject-part="form_info.mold_info.product_infos.length"
      >
      </precondition-form>
    </el-card>

    <el-card shadow="hover">
      <div slot="header" class="clearfix">
        <span>参数设定</span>
      </div>

      <process-record-form
        :record-detail="form_info.process_detail"
        :machine-info="form_info.mac_unit"
      ></process-record-form>
    </el-card>

    <div style="height: 25px" />

    <div class="nextButton">
      <el-button 
        type="primary" 
        size="small" 
        @click="readMES"
      >
        读取MES
      </el-button>
      <el-button 
        type="primary" 
        size="small" 
        @click="writeMES"
        :disabled="btnisShow"
      >
        写入MES
      </el-button>
      
      <el-button
        v-if="dialog"
        type="danger"
        size="small"
        @click="$emit('close')"
      >
        返 回
      </el-button>
      <el-button 
        v-else 
        type="danger" 
        size="small" 
        @click="resetView"
      >
        重 置
      </el-button>
      <el-button
        v-if="id && viewType !== 'copy'"
        type="primary"
        size="small"
        :loading="update_loading"
        @click="saveProcessRecordDetail"
      >
        更 新
      </el-button>
      <el-button
        v-else
        type="primary"
        size="small"
        :loading="save_loading"
        @click="saveProcessRecordDetail"
      >
        保 存
      </el-button>
    </div>
  </div>
</template>

<script>
import { projectMethod , processRecordMethod, machineMethod, processIndexMethod, 
getYizumiProcess, getMesProcessMethod,setMesProcessMethod } from "@/api";
import { UserModule } from "@/store/modules/user";
import { initArray } from "@/utils/array-help";
import { datetimeTodayStr } from "@/utils/datetime";
import PreconditionForm from "./subView/preconditionForm.vue";
import ProcessRecordForm from "./subView/processRecordForm.vue";

export default {
  name: "CreateProcessRecord",
  components: { PreconditionForm, ProcessRecordForm },
  props: {
    id: {
      type: Number,
      default: null,
    },
    dialog: {
      type: Boolean,
      default: false,
    },
    viewType: {
      type: String,
      default: null,
    },
    excelData: {
      type: Object,
      default: () => ({}),
    },
  },
  data() {
    return {
      form_info: {
        mac_unit: {
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

          max_injection_stroke: null,
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
        },
        mold_info: {
          product_infos: []
        },
        process_index_id: this.id,
        precondition: {
          data_sources: null,
          mold_trials_no: null,
          machine_id: null,
          machine_data_source: null,
          machine_trademark: null,
          machine_serial_no: null,

          polymer_id: null,
          polymer_abbreviation: null,
          polymer_trademark: null,

          mold_id: null,
          mold_no: null,
          cavity_num: null,
          inject_cycle_require:null,
          runner_length: null,
          runner_weight: null,
          gate_type: null,
          gate_num: null,
          gate_shape: null,
          gate_area: null,
          gate_radius: null,
          gate_length: null,
          gate_width: null,
          
          inject_part: null,
          product_type: null,

          product_no: null,
          product_name: null,
          product_ave_thickness: null,
          product_max_thickness: null,
          product_max_length: null,
          product_total_weight: null,
        },
        process_detail: {
          title: "射台 #1",
          name: "1",
          inject_para: {
            injection_stage: 1,
            max_injection_stage_option: 6,
            table_data: [
              { label: "压力", unit: "kgf/cm²", sections: initArray(6, null) },
              { label: "速度", unit: "mm/s", sections: initArray(6, null) },
              { label: "位置", unit: "mm", sections: initArray(6, null) },
            ],
            injection_time: null,
            injection_delay_time: null,
            cooling_time: null,
          },
          holding_para: {
            holding_stage: 1,
            max_holding_stage_option: 5,
            table_data: [
              { label: "压力", unit: "kgf/cm²", sections: initArray(5, null) },
              { label: "速度", unit: "mm/s", sections: initArray(5, null) },
              { label: "时间", unit: "s", sections: initArray(5, null) },
            ],
          },
          VP_switch: {
            VP_switch_mode: "位置",
            VP_switch_position: null,
            VP_switch_time: null,
            VP_switch_pressure: null,
            VP_switch_velocity: null,
          },
          metering_para: {
            metering_stage: 1,
            max_metering_stage_option: 4,
            table_data: [
              { label: "压力", unit: "kgf/cm²", sections: initArray(4, null) },
              { label: "螺杆转速", unit: "rpm", sections: initArray(4, null) },
              { label: "背压", unit: "kgf/cm²", sections: initArray(4, null) },
              { label: "位置", unit: "mm", sections: initArray(4, null) },
            ],
            decompressure_mode_before_metering: "否",
            decompressure_mode_after_metering: "距离",
            decompressure_paras: [
              {
                label: "储前",
                pressure: null,
                velocity: null,
                time: null,
                distance: null,
              },
              {
                label: "储后",
                pressure: null,
                velocity: null,
                time: null,
                distance: null,
              },
            ],
            metering_delay_time: null,
            metering_ending_position: null,
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
        },
      },
      export_loading: false,
      update_loading: false,
      save_loading: false,
      is_valid: true,
      timer: null,
      btnisShow: false
    };
  },
  created() {

  },
  mounted() {
    // sessionStorage
    let checkData = {};
    checkData = sessionStorage.getItem("process_record");
    if (checkData && JSON.stringify(checkData) != "{}") {
      this.form_info = JSON.parse(checkData)
    }

    this.getProcessRecordDetail()
    // setTimeout(this.checkValid, 1000)
  },
  methods: {
    setMoldInfo() {
      if (this.form_info.precondition.mold_id) {
        projectMethod.getDetail(this.form_info.precondition.mold_id)
        .then(res => {
          if (res.status === 0) {
            this.form_info.precondition.mold_id = res.data.mold_info.id
            this.form_info.precondition.mold_no = res.data.mold_info.mold_no
            this.form_info.precondition.cavity_num = res.data.mold_info.cavity_num
            this.form_info.precondition.inject_cycle_require = res.data.mold_info.inject_cycle_require

            this.form_info.precondition.product_type = res.data.mold_info.product_type
            this.form_info.precondition.product_no = res.data.mold_info.product_no
            this.form_info.precondition.product_name = res.data.mold_info.product_name

            this.form_info.precondition.product_ave_thickness = null
            this.form_info.precondition.product_max_thickness = null
            this.form_info.precondition.product_max_length = null  
            this.form_info.precondition.product_total_weight = null

            // 模具参数
            this.form_info.mold_info.product_infos = []

            // 默认选取主射台的制品信息
            if (res.data.mold_info.product_infos && res.data.mold_info.product_infos.length > 0) {
              this.form_info.mold_info.product_infos = res.data.mold_info.product_infos
              this.form_info.precondition.inject_part = "0"
              this.setProductInfo()
            }
          }
        })
      }
    },
    setProductInfo() {

      if (this.form_info.mold_info.product_infos && this.form_info.mold_info.product_infos.length > 0) {

        let index = Number(this.form_info.precondition.inject_part)
        let product_info  = this.form_info.mold_info.product_infos[index]

        this.form_info.precondition.product_ave_thickness = product_info.ave_thickness
        this.form_info.precondition.product_max_thickness = product_info.max_thickness
        this.form_info.precondition.product_max_length = product_info.flow_length
        this.form_info.precondition.product_total_weight = product_info.single_weight

        this.form_info.precondition.runner_length = product_info.runner_length
        this.form_info.precondition.runner_weight = product_info.runner_weight
        this.form_info.precondition.gate_type = product_info.gate_type
        this.form_info.precondition.gate_num = product_info.gate_num
        this.form_info.precondition.gate_shape = product_info.gate_shape
        this.form_info.precondition.gate_area = product_info.gate_area
        this.form_info.precondition.gate_radius = product_info.gate_radius
        this.form_info.precondition.gate_length = product_info.gate_length
        this.form_info.precondition.gate_width = product_info.gate_width
      }
    },
    setViewUnit() {
      if (this.form_info.precondition.machine_id) {
        machineMethod
          .getDetail(this.form_info.precondition.machine_id)
          .then((res) => {
            if (res.status === 0 && res.data) {
              this.form_info.precondition.machine_data_source = res.data.data_source
              this.form_info.precondition.machine_trademark = res.data.trademark
              this.form_info.precondition.machine_serial_no = res.data.serial_no

              this.form_info.mac_unit.pressure_unit = res.data.pressure_unit
              this.form_info.mac_unit.backpressure_unit = res.data.backpressure_unit
              this.form_info.mac_unit.oc_pressure_unit = res.data.oc_pressure_unit
              this.form_info.mac_unit.oc_velocity_unit = res.data.oc_velocity_unit
              this.form_info.mac_unit.position_unit = res.data.position_unit
              this.form_info.mac_unit.power_unit =  res.data.power_unit
              this.form_info.mac_unit.temperature_unit =  res.data.temperature_unit
              this.form_info.mac_unit.velocity_unit =  res.data.velocity_unit
              this.form_info.mac_unit.time_unit =  res.data.time_unit
              this.form_info.mac_unit.clamping_force_unit =  res.data.clamping_force_unit
              this.form_info.mac_unit.screw_rotation_unit = res.data.screw_rotation_unit

              // 获取机器的最大设定值
              this.form_info.mac_unit.max_injection_stroke =
                res.data.injectors_info[0].max_injection_stroke;
              this.form_info.mac_unit.max_set_injection_pressure =
                res.data.injectors_info[0].max_set_injection_pressure;
              this.form_info.mac_unit.max_set_injection_velocity =
                res.data.injectors_info[0].max_set_injection_velocity;

              this.form_info.mac_unit.max_set_holding_pressure =
                res.data.injectors_info[0].max_set_holding_pressure;
              this.form_info.mac_unit.max_set_holding_velocity =
                res.data.injectors_info[0].max_set_holding_velocity;

              this.form_info.mac_unit.max_set_metering_pressure =
                res.data.injectors_info[0].max_set_metering_pressure;                
              this.form_info.mac_unit.max_set_screw_rotation_speed =
                res.data.injectors_info[0].max_set_screw_rotation_speed;
              this.form_info.mac_unit.max_set_metering_back_pressure =
                res.data.injectors_info[0].max_set_metering_back_pressure;

              this.form_info.mac_unit.max_set_decompression_velocity =
                res.data.injectors_info[0].max_set_decompression_velocity;
              this.form_info.mac_unit.max_set_decompression_pressure =
                res.data.injectors_info[0].max_set_decompression_pressure;

              this.form_info.mac_unit.max_mold_open_stroke =
                res.data.max_mold_open_stroke;
              this.form_info.mac_unit.max_ejection_stroke =
                res.data.max_ejection_stroke;
              this.form_info.mac_unit.max_set_ejector_forward_velocity =
                res.data.injectors_info[0].max_set_ejector_forward_velocity;
              this.form_info.mac_unit.max_set_ejector_backward_velocity =
                res.data.injectors_info[0].max_set_ejector_backward_velocity;
              this.form_info.mac_unit.max_set_mold_opening_velocity =
                res.data.injectors_info[0].max_set_mold_opening_velocity;
              this.form_info.mac_unit.max_set_mold_clamping_velocity =
                res.data.injectors_info[0].max_set_mold_clamping_velocity;

              this.form_info.process_detail.inject_para.table_data[0].unit =
                this.form_info.mac_unit.pressure_unit;
              this.form_info.process_detail.inject_para.table_data[1].unit =
                this.form_info.mac_unit.velocity_unit;
              this.form_info.process_detail.inject_para.table_data[2].unit =
                this.form_info.mac_unit.position_unit;

              this.form_info.process_detail.holding_para.table_data[0].unit =
                this.form_info.mac_unit.pressure_unit;
              this.form_info.process_detail.holding_para.table_data[1].unit =
                this.form_info.mac_unit.velocity_unit;
              this.form_info.process_detail.holding_para.table_data[2].unit =
                this.form_info.mac_unit.time_unit;

              this.form_info.process_detail.metering_para.table_data[0].unit =
                this.form_info.mac_unit.pressure_unit;
              this.form_info.process_detail.metering_para.table_data[1].unit =
                this.form_info.mac_unit.screw_rotation_unit;
              this.form_info.process_detail.metering_para.table_data[2].unit =
                this.form_info.mac_unit.backpressure_unit;
              this.form_info.process_detail.metering_para.table_data[3].unit =
                this.form_info.mac_unit.position_unit;

              this.form_info.process_detail.temp_para.table_data[0].unit =
                this.form_info.mac_unit.temperature_unit;
              
              if(this.form_info.process_detail.ejector_setting){

                this.form_info.process_detail.ejector_setting.ejector_backward.table_data[0].unit =
                  this.form_info.mac_unit.oc_pressure_unit;
                this.form_info.process_detail.ejector_setting.ejector_forward.table_data[0].unit =
                  this.form_info.mac_unit.oc_pressure_unit;
                this.form_info.process_detail.ejector_setting.ejector_backward.table_data[1].unit =
                  this.form_info.mac_unit.oc_velocity_unit;
                this.form_info.process_detail.ejector_setting.ejector_forward.table_data[1].unit =
                  this.form_info.mac_unit.oc_velocity_unit;
              }
              if(this.form_info.process_detail.opening_and_clamping_mold_setting){

                this.form_info.process_detail.opening_and_clamping_mold_setting.mold_opening.table_data[0].unit =
                  this.form_info.mac_unit.oc_pressure_unit;
                this.form_info.process_detail.opening_and_clamping_mold_setting.mold_opening.table_data[0].unit =
                  this.form_info.mac_unit.oc_pressure_unit;
                this.form_info.process_detail.opening_and_clamping_mold_setting.mold_clamping.table_data[1].unit =
                  this.form_info.mac_unit.oc_velocity_unit;
                this.form_info.process_detail.opening_and_clamping_mold_setting.mold_clamping.table_data[1].unit =
                  this.form_info.mac_unit.oc_velocity_unit;
              }
            }
          });
      }
    },
    getProcessRecordDetail() {
      if (this.id) {
        processRecordMethod.getDetail(this.id).then((res) => {
          if (
            res.status === 0 &&
            res.data &&
            JSON.stringify(res.data) != "{}"
          ) {
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

            this.form_info.process_index_id = res.data.process_index_id;
            this.form_info.precondition = res.data.precondition;
            this.form_info.process_detail = res.data.process_detail;

            if (this.viewType == "edit") {
            } else if (this.viewType == "copy") {
              this.form_info.process_index_id = null;
            }
          } else {
            this.$message({
              message: "未读取到相关内容！",
              type: "warning",
            });
            this.$emit("close");
          }
        });
      }

      if (this.viewType == "add") {
      } else if (
        this.viewType == "upload" &&
        this.excelData &&
        JSON.stringify(this.excelData) != "{}"
      ) {
      }
    },
    saveProcessRecordDetail() {
      if (!this.is_valid) {
        this.checkValid();
      } else {
        if (this.id && this.viewType !== "copy") {
          // 更新详细工艺记录
          let record_para = {
            process_index_id: this.form_info.process_index_id,
            precondition: this.form_info.precondition,
            process_detail: this.form_info.process_detail,
          };
          processRecordMethod.add(record_para).then((res) => {
            if (res.status === 0) {
              this.$message({
                message: "工艺参数数据已更新！",
                type: "success",
              });
            }
          });
        } else {
          let process_index = {
            company_id: UserModule.company_id,
            status: 2,
            process_no: "P" + datetimeTodayStr(),

            mold_id: this.form_info.precondition.mold_id,
            mold_no: this.form_info.precondition.mold_no,
            cavity_num: this.form_info.precondition.cavity_num,
            inject_cycle_require: this.form_info.precondition.inject_cycle_require,
            runner_length: this.form_info.precondition.runner_length,
            runner_weight: this.form_info.precondition.runner_weight,
            gate_type: this.form_info.precondition.gate_type,
            gate_num: this.form_info.precondition.gate_num,
            gate_shape: this.form_info.precondition.gate_shape,
            gate_area: this.form_info.precondition.gate_area,
            gate_radius: this.form_info.precondition.gate_radius,
            gate_length: this.form_info.precondition.gate_length,
            gate_width: this.form_info.precondition.gate_width,

            inject_part: this.form_info.precondition.inject_part,
            product_no: this.form_info.precondition.product_no,
            product_type: this.form_info.precondition.product_type,
            product_name: this.form_info.precondition.product_name,
            product_total_weight: this.form_info.precondition.product_total_weight,
            product_ave_thickness: this.form_info.precondition.product_ave_thickness,
            product_max_thickness: this.form_info.precondition.product_max_thickness,
            product_max_length: this.form_info.precondition.product_max_length,

            data_sources: this.form_info.precondition.data_sources,
            mold_trials_no: this.form_info.mold_trials_no,
            machine_id: this.form_info.precondition.machine_id,
            machine_data_source: this.form_info.precondition.machine_data_source,
            machine_trademark: this.form_info.precondition.machine_trademark,
            machine_serial_no: this.form_info.precondition.machine_serial_no,

            polymer_id: this.form_info.precondition.polymer_id,
            polymer_abbreviation: this.form_info.precondition.polymer_abbreviation,
            polymer_trademark: this.form_info.precondition.polymer_trademark,
          };
          let form_infos = this.form_info
          processIndexMethod.add(process_index)
          .then((res) => {
            if (res.status === 0) {
              form_infos.process_index_id = res.data.id;
              // 新增详细工艺记录
              let record_para = {
                process_index_id: form_infos.process_index_id,
                precondition: form_infos.precondition,
                process_detail: form_infos.process_detail,
              };
              processRecordMethod.add(record_para).then((res) => {
                if (res.status === 0) {
                  this.$message({
                    message: "工艺参数数据已上传至数据库！",
                    type: "success",
                  });
                }
              });
            }
          });
        }

        this.$emit("close");
        this.$router.push({
          path: "/process/record/list",
        });
      }
    },
    resetView() {
      this.form_info = {
        mac_unit: {
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
          max_injection_stroke: null,
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
        },
        mold_info: {
          product_infos: []
        },
        process_index_id: this.id,
        precondition: {
          data_sources: null,
          mold_trials_no: null,
          machine_id: null,
          machine_data_source: null,
          machine_trademark: null,
          machine_serial_no: null,

          polymer_id: null,
          polymer_abbreviation: null,
          polymer_trademark: null,

          mold_id: null,
          mold_no: null,
          cavity_num: null,
          inject_cycle_require:null,
          runner_length: null,
          runner_weight: null,
          gate_type: null,
          gate_num: null,
          gate_shape: null,
          gate_area: null,
          gate_radius: null,
          gate_length: null,
          gate_width: null,

          inject_part: null,
          product_type: null,

          product_no: null,
          product_name: null,
          product_ave_thickness: null,
          product_max_thickness: null,
          product_max_length: null,
          product_total_weight: null,
        },
        process_detail: {
          title: "射台 #1",
          name: "1",
          inject_para: {
            injection_stage: 1,
            max_injection_stage_option: 6,
            table_data: [
              { label: "压力", unit: "kgf/cm²", sections: initArray(6, null) },
              { label: "速度", unit: "mm/s", sections: initArray(6, null) },
              { label: "位置", unit: "mm", sections: initArray(6, null) },
            ],
            injection_time: null,
            injection_delay_time: null,
            cooling_time: null,
          },
          holding_para: {
            holding_stage: 1,
            max_holding_stage_option: 5,
            table_data: [
              { label: "压力", unit: "kgf/cm²", sections: initArray(5, null) },
              { label: "速度", unit: "mm/s", sections: initArray(5, null) },
              { label: "时间", unit: "s", sections: initArray(5, null) },
            ],
          },
          VP_switch: {
            VP_switch_mode: "位置",
            VP_switch_position: null,
            VP_switch_time: null,
            VP_switch_pressure: null,
            VP_switch_velocity: null,
          },
          metering_para: {
            metering_stage: 1,
            max_metering_stage_option: 4,
            table_data: [
              { label: "压力", unit: "kgf/cm²", sections: initArray(4, null) },
              { label: "螺杆转速", unit: "rpm", sections: initArray(4, null) },
              { label: "背压", unit: "kgf/cm²", sections: initArray(4, null) },
              { label: "位置", unit: "mm", sections: initArray(4, null) },
            ],
            decompressure_mode_before_metering: "否",
            decompressure_mode_after_metering: "距离",
            decompressure_paras: [
              {
                label: "储前",
                pressure: null,
                velocity: null,
                time: null,
                distance: null,
              },
              {
                label: "储后",
                pressure: null,
                velocity: null,
                time: null,
                distance: null,
              },
            ],
            metering_delay_time: null,
            metering_ending_position: null,
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
      }
    },
    readMES() {
      if(this.form_info.precondition.machine_id){
        this.form_info.precondition.data_sources = "读取MES"
        getMesProcessMethod({machine_id: this.form_info.precondition.machine_id}).then((res) => {
          if (res.status === 0) {
            if (res.data.result === "outdated") {
              window.location.href = "https://iiot2.yizumi.com" // "http://kunpeng.yizumi.com:82"
            } else if (res.data.result === "failed") {
                this.$message({
                message: "读取失败",
                type: "warning",
              });
            } else
            {
              this.form_info.process_detail = res.data.process_detail;
              this.form_info.precondition.mold_no = res.data.mold_no
              this.form_info.precondition.product_no = res.data.product_no
            }
          }
        });
      }
      else if (!(this.form_info.precondition.machine_id) && this.form_info.precondition.machine_trademark){
        this.$message({
          message: "请到机器管理中先新增该机器信息！",
          // message: "请选择注塑机来源和型号",
          type: "warning",
        });
      } else if (!(this.form_info.precondition.machine_id) && !(this.form_info.precondition.machine_trademark)){
        this.$message({
          message: "请选择注塑机来源和型号",
          type: "warning",
        })
      }
    },
    writeMES() {
      this.checkValid()
      if(!this.form_info.precondition.machine_serial_no){
        this.$message({
          message: "射台编码为空,请填写注塑机射台编码后,重新选择注塑机和注射单元",
          type: "warning"
        })  
        return
      }
      if(this.is_valid === true){      
        setMesProcessMethod({
          process_detail: this.form_info.process_detail,
          precondition: this.form_info.precondition
        }).then((res) => {
          if (res.status === 0) {
            if (!res.data.result) {
              this.$message({
                message: "未连接注塑机",
                type: "warning"
              })
            }
            if (res.data.result === "success") {
              this.btnisShow = true
              this.intervalShowButton()
              this.$message({
                message: "成功写入",
                type: "success",
              });
            }
            if (res.data.result === "outdated") {
              window.location.href = "https://iiot2.yizumi.com" // "http://kunpeng.yizumi.com:82"
            }
            if (res.data.result === "failed") {
              this.$message({
                message: "写入失败",
                type: "warning",
              });
            }
          }
        });
      }
      else{
        this.$message({
          message: "参数超过注塑机最大可设定,请根据页面提示信息修改相关参数",
          type: "warning",
        });
      }
    },
    //定时器
    intervalShowButton() {
      this.timer = setTimeout(() => {
        this.btnisShow = false
      },5000)
    },
    checkValid() {
      this.is_valid = true

      // 螺杆位置判断
      // 切换位置<注射4段位置<注射3段位置<注射2段位置<注射1段位置<储料位置<储料1段位置<储料2段位置<储料3段位置<储料4段位置<最大注射行程

      // 切换位置<注射4段位置<注射3段位置<注射2段位置<注射1段位置<熔胶终止位置<最大注射行程
      // 储料1段位置<储料2段位置<储料3段位置<储料4段位置<熔胶终止位置<最大注射行程
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
      
      let mac_info = this.form_info.mac_unit
      posi_para_record["最大注射行程"] = { "element_id": "NULL", "value": mac_info.max_injection_stroke }

      let metering_para = this.form_info.process_detail.metering_para
      posi_para_record["螺杆终止位置"] = { "element_id": "MEL", "value": metering_para.metering_ending_position }

      for (let i = 0; i < metering_para.metering_stage; ++i) {
        posi_para_record["储料" + Number(i + 1) + "段位置"] = {
          "element_id": "ML" + i,
          "value": metering_para.table_data[3].sections[i]
        }
      }

      let inject_para = this.form_info.process_detail.inject_para
      for (let i = 0; i < inject_para.injection_stage; ++i) {
        posi_para_record["注射" + Number(i + 1) + "段位置"] = {
          "element_id": "IL" + i,
          "value": inject_para.table_data[2].sections[i]
        }
      }

      let VP_switch = this.form_info.process_detail.VP_switch
      posi_para_record["VP切换位置"] = { "element_id": "VPTL", "value": VP_switch.VP_switch_position }
      if(this.form_info.process_detail.opening_and_clamping_mold_setting){
        let mold_opening = this.form_info.process_detail.opening_and_clamping_mold_setting.mold_opening
        for (let i = 0; i < mold_opening.mold_opening_stage; i++) {
          posi_para_record["开模" + Number(i + 1) + "段位置"] = {
            "element_id": "MOP" + i,
            "value": mold_opening.table_data[2].sections[i]
          }
        }

        let mold_clamping = this.form_info.process_detail.opening_and_clamping_mold_setting.mold_clamping
        for (let i = 0; i < mold_clamping.mold_clamping_stage; i++) {
          posi_para_record["合模" + Number(i + 1) + "段位置"] = {
            "element_id": "MCP" + i,
            "value": mold_clamping.table_data[2].sections[i]
          }
        }
      }

      if(this.form_info.process_detail.ejector_setting){

        let ejector_backward = this.form_info.process_detail.ejector_setting.ejector_backward
        for (let i = 0; i < ejector_backward.ejector_backward_stage; i++) {
          posi_para_record["顶针后退" + Number(i + 1) + "段位置"] = {
            "element_id": "EBP" + i,
            "value": ejector_backward.table_data[2].sections[i]
          }
        }
  
        let ejector_forward = this.form_info.process_detail.ejector_setting.ejector_forward
        for (let i = 0; i < ejector_forward.ejector_forward_stage; i++) {
          posi_para_record["顶针前进" + Number(i + 1) + "段位置"] = {
            "element_id": "EFP" + i,
            "value": ejector_forward.table_data[2].sections[i]
          }
        }
      }

      for (let i = 1; i < screw_positions.length; ++i) {
        let last_item = posi_para_record[screw_positions[i - 1]]
        if (last_item && last_item.value) {
          for (let j = i; j < screw_positions.length; ++j) {
            let curr_item = posi_para_record[screw_positions[j]]
            if (curr_item && curr_item.value ) {
              if (Number(curr_item.value) > Number(last_item.value) && Number(last_item.value) > 0) {
                this.timer = window.setTimeout(() => {
                  this.$notify({
                    title: '提示!',
                    message: this.$createElement('i', { style: 'color: teal'}, screw_positions[j] + "的值大于" + screw_positions[i - 1] + "的值，不符合要求！")
                  })
                })
                // this.$message({
                //   message: screw_positions[j] + "的值大于" + screw_positions[i - 1] + "的值，不符合要求！",
                //   type: "warning",
                //   showClose: true,
                //   duration: 5000,
                // })
                this.setElementStyle(document.getElementById(curr_item.element_id), "#highlight")
                this.is_valid = false
              } else {
                this.setElementStyle(document.getElementById(curr_item.element_id), "#normal")
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
                this.setElementStyle(document.getElementById(curr_item.element_id), "#highlight")
                this.is_valid = false
              } else {
                this.setElementStyle(document.getElementById(curr_item.element_id), "#normal")
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
                this.setElementStyle(document.getElementById(curr_item.element_id), "#highlight")
                this.is_valid = false
              } else {
                this.setElementStyle(document.getElementById(curr_item.element_id), "#normal")
              }
            }
          }
        }
      }
      //合模第一段位置要比开模最后一段位置小
      if(this.form_info.process_detail.opening_and_clamping_mold_setting){
        
        let mc_positions_first = posi_para_record[mold_clamping_positions[1]]
        let a = this.form_info.process_detail.opening_and_clamping_mold_setting.mold_opening.mold_opening_stage
        let ml_positions_last = posi_para_record[mold_opening_positions[9-a]]
        if (mc_positions_first && mc_positions_first.value && ml_positions_last && ml_positions_last.value) {
          if (Number(mc_positions_first.value) > Number(ml_positions_last.value)) {
            this.timer = window.setTimeout(() => {
              this.$notify({
                title: '提示!',
                message: this.$createElement('i', { style: 'color: teal' }, mold_clamping_positions[1] + "的值大于" + mold_opening_positions[9-a] + "的值，不符合要求")
              })
            })
            this.setElementStyle(document.getElementById(mc_positions_first.element_id), "#highlight")
            this.is_valid = false
          } else {
            this.setElementStyle(document.getElementById(mc_positions_first.element_id), '#normal')
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
                  this.setElementStyle(document.getElementById(curr_item.element_id), "#highlight")
                  this.is_valid = false
                } else {
                  this.setElementStyle(document.getElementById(curr_item.element_id), '#normal')
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
                  this.setElementStyle(document.getElementById(curr_item.element_id), "#highlight")
                  this.is_valid = false
                } else {
                  this.setElementStyle(document.getElementById(curr_item.element_id), '#normal')
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
                  this.setElementStyle(document.getElementById(curr_item.element_id), "#highlight")
                  this.is_valid = false
                } else {
                  this.setElementStyle(document.getElementById(curr_item.element_id), '#normal')
                }
              }
            }
          }
        }
      }

      // 校验工艺参数,不能小于0,不能大于机器的最大设定值
      // 注射:

      // 完成: 注射压力<机器最大注射压力
      // 完成: 注射速度<机器最大注射速度

      // 保压:

      // 保压压力<机器最大保压压力
      // 保压速度<机器最大保压速度

      // 熔胶:

      // 熔胶压力<机器最大压力
      // 熔胶螺杆转速<机器最大螺杆转速
      // 熔胶背压<机器最大背压

      // 射退:

      // 最大射退压力<机器最大射退压力
      // 最大射退速度<机器最大射退速度

      // set :注射速度, max:机器最大注射速度, label:注射速度的id
      let compare_list = []
      // 注射参数
      for (let i = 0; i < inject_para.injection_stage; ++i) {
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
      // 保压参数
      let holding_para = this.form_info.process_detail.holding_para
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
      // 储料参数
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
        "set_val_label": "储后松退速度",
        "max_val_label": "机器最大松退速度",
        "element_id": "DVAM"
      })
      // 开模参数
      if(this.form_info.process_detail.opening_and_clamping_mold_setting){

        let mold_opening_para = this.form_info.process_detail.opening_and_clamping_mold_setting.mold_opening
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
        let mold_clamping_para = this.form_info.process_detail.opening_and_clamping_mold_setting.mold_clamping
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
      }
      if(this.form_info.process_detail.ejector_setting){

        // 顶针后退参数
        let ejector_backward_para = this.form_info.process_detail.ejector_setting.ejector_backward
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
        let ejector_forward_para = this.form_info.process_detail.ejector_setting.ejector_forward
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
      }

      for (let i = 0; i < compare_list.length; ++i) {
        let item = compare_list[i]
        if (item.set_val && item.max_val) {
          if (Number(item.set_val) > Number(item.max_val)) {
            this.timer = window.setTimeout(() => {
              this.$notify({
                title: '提示!',
                message: this.$createElement('i', { style: 'color: teal'}, item.set_val_label + "的设定值为: " + item.set_val 
                  + ", 大于" + item.max_val_label + "最大可设定值: " + item.max_val 
                  + ", 不符合要求！")
              })
            })
            // this.$message({
            //   message: item.set_val_label + "的设定值为: " + item.set_val 
            //   + ", 大于" + item.max_val_label + "最大可设定值: " + item.max_val 
            //   + ", 不符合要求！",
            //   type: "warning",
            //   showClose: true,
            //   duration: 5000,
            // });
            this.setElementStyle(document.getElementById(String(item.element_id)), "#highlight");
            this.is_valid = false
          } else {
            this.setElementStyle(document.getElementById(String(item.element_id)), "#normal");  
          }
        }
      }
    },
    setElementStyle(element, style) {
      if (element && style === "#highlight") {
        element.style.backgroundColor = "red";
        element.style.color = "white";
      } else if (element && style === "#normal") {
        element.style.backgroundColor = "white";
        element.style.color = "black";
      }
    },
  },
  watch: {
    id() {
      if (this.id) {
        this.getProcessRecordDetail();
      }
    },
    "form_info.precondition.mold_id" () {
      this.setMoldInfo()
    },
    "form_info.precondition.inject_part" () {
      this.setProductInfo()
    },
    "form_info.precondition.machine_id": function() {
      this.setViewUnit()
    },
    "form_info.process_detail": {
      handler: function () {
        setTimeout(() => {
          this.checkValid()
        },500)
      },
      deep: true,
    },
    form_info: {
      handler: function () {
         sessionStorage.setItem("process_record", JSON.stringify(this.form_info));
      },
      deep: true,
    },
    excelData: {
      handler: function () {
        if (this.excelData && this.excelData !== undefined) {
          this.form_info = this.excelData;
        }
      },
      deep: true,
    },
  },
};
</script>

<style lang="scss" scoped>

</style>