<template>
  <div>
    <el-collapse 
      v-model="form_info.active_collapse" 
      class="collapseItemTitle"
    >
      <el-collapse-item title="基本信息" name="1">
        <precondition-form
          ref="precondition"
          :precondition-detail="form_info.precondition"
          :max-inject-part="form_info.mold_info.product_infos.length"
        >
        </precondition-form>
      </el-collapse-item>

      <el-collapse-item title="工艺参数优化" name="2">
        <el-tabs 
          v-model="form_info.active_tab_index"
        >
          <el-tab-pane
            v-for="item, index in form_info.optimize_list"
            :key="index"
            :label="item.title"
            :name="item.name"
          >
            <process-optimize-form
              ref="processOptimize"
              :view-index="index"
              :optimize-detail="item"
              :mac-unit="form_info.mac_unit"
              :precondition-detail="form_info.precondition"
            ></process-optimize-form>
          </el-tab-pane>
        </el-tabs>
      </el-collapse-item>
    </el-collapse>

    <el-form>
      <el-form-item label="缺陷图">
        <upload-single-file
          :value="flaw_picture_info"
          search-type="media"
          @upload-file-info="onFileUploaded"
        >
        </upload-single-file>
      </el-form-item>
    </el-form>

    <div v-if="!id" class="buttonGroup">
      <el-button-group>
        <el-button
          type="warning"
          size="small"
          @click="resetView"
        >
          重置参数
        </el-button>
        <el-button
          :disabled="Boolean(form_info.process_index_id)"
          type="success"
          size="small"
          @click="initProcessPara"
        >
          创建首模工艺
        </el-button>
        <el-button
          :disabled="!Boolean(form_info.process_index_id)"
          type="danger"
          size="small"
          @click="constructCommitParams"
        >
          缺陷修正
        </el-button>

        <el-button
          :disabled="!Boolean(form_info.process_index_id)"
          type="primary"
          size="small"
          @click="saveCurrentProcess"
          :loading="loading"
        >
          合格 保存当前工艺
        </el-button>
        <el-tooltip
          effect="dark"
          content="把最新的工艺参数下发到注塑机"
          placement="top-start"
        >
          <el-button 
            type="primary" 
            size="small" 
            @click="writeMES"
            :disabled="btnisShow"
          >
            写入MES
          </el-button>
        </el-tooltip>
      </el-button-group>
    </div>

    <el-dialog
      title=""
      :visible.sync="showDefects"
      width="35%"
      @closeDialog="closeDefectsDialog"
    >
      <serious-defects
        :tab-data="serious_defects_data"
        @close-dialog="closeDefectsDialog"
        @execute="execute"
      >
      </serious-defects>
    </el-dialog>

    <!-- <el-dialog
      title=""
      :visible.sync="showRules"
      width="95%"
      @closeDialog="closeRuleChoicesDialog"
    >
      <rule-choices
        :tab-data="ruleChoicesData"
        @close-dialog="closeRuleChoicesDialog"
        @execute="chosenRule"
      >
      </rule-choices>
    </el-dialog> -->
  </div>
</template>

<script>
import { machineMethod, initialProcessAlgorithm, processOptimizeMethod,
  optimizeProcessAlgorithm, projectMethod, processIndexMethod, 
  processRecordMethod, downloadFile,getMesProcessMethod,setMesProcessMethod, ruleDetailMethod, getOptions } from "@/api"
import { UserModule } from "@/store/modules/user"
import { datetimeTodayStr } from "@/utils/datetime"
import ProcessOptimizeForm from "./subView/processOptimizeForm.vue"
import PreconditionForm from "./subView/preconditionForm.vue"
import UploadSingleFile from "@/components/uploadSingleFile"
import SeriousDefects from "./subView/seriousDefects.vue"
import RuleChoices from "./subView/ruleChoices.vue"
import { createOptimizeList, DEFAULT_FORM_INFO } from "@/utils/process_const"
import { initArray } from "@/utils/array-help"

export default {
  name: "CreateProcessOptimize",
  components: { PreconditionForm, ProcessOptimizeForm, UploadSingleFile, SeriousDefects, RuleChoices },
  props: {
    id: {
      type: Number,
      default: null
    },
    dialog: {
      type: Boolean,
      default: false
    },
    viewType: {
      type: String,
      default: null
    },
  },
  data() {
    return {
      form_info: JSON.parse(JSON.stringify(DEFAULT_FORM_INFO)),
      loading: false,
      interval_mark: null,
      flaw_picture_info: {
        id: null,
        name: null,
        url: null
      },
      showDefects: false,
      // showRules: false,
      // ruleChoicesData:[],
      serious_defects_data: [
        {
          desc: "注射一段",
          original_value: null,
          suggest_value: null,
        },
        {
          desc: "注射二段",
          original_value: null,
          suggest_value: null,
        },
        {
          desc: "注射时间",
          original_value: null,
          suggest_value: null,
        },
      ],
      light_defects: false,
      optimize_para:{},  // 缺陷修正之后,存储从后端返回的原生参数,如IP0
      optimize_detail:{},  // 缺陷修正之后,存储从后端返回的工艺参数,适用于页面
      btnisShow: false,
      is_valid:true,
      defectOptions: [],
      currentSubrule: null,
      general:null,
    }
  },
  watch: {
    id: function() {
      if (this.id) {
        this.getProcessOptimizeDetail()
      }
    },
    "form_info.precondition.mold_id" () {
      this.setMoldInfo()
    },
    "form_info.precondition.inject_part" () {
      this.setProductInfo()
    },
    "form_info.precondition.machine_id" () {
      this.setViewUnit()
    },
    form_info: {
      handler: function() {
        setTimeout(() => {
          this.highlightChange(this.form_info.active_tab_index)
        }, 100)
        sessionStorage.setItem("process_optimization", JSON.stringify(this.form_info))
      },
      deep:true
    },
    active_tab_index () {
      this.highlightChange(this.form_info.active_tab_index)
    }
  },
  created() {

  },
  mounted() {
    this.loadDefectOptions()    
    // sessionStorage
    let checkData = {}
    checkData = sessionStorage.getItem("process_optimization")
    if (checkData && JSON.stringify(checkData) != "{}") {
      this.form_info = JSON.parse(checkData)
    }

    this.getProcessOptimizeDetail()
  },
  methods: {
    async loadDefectOptions() {
      try {
      // 第一步：获取缺陷列表
        const res = await getOptions("defect_list", [])
        const defectsConst = res.data

        // 第二步：生成 defectOptions
        this.defectOptions = defectsConst.map(defect => ({
          ...defect,
          level: "无缺陷",
          position: "缺陷位置不指定",
          count: 0,
          feedback: null,
          remark: null
        }))

        // 第三步：赋值给 form_info.optimize_list[0].feedback_detail.defect_info
        if (this.form_info.optimize_list && this.form_info.optimize_list[0]) {
          this.form_info.optimize_list[0].feedback_detail.defect_info = JSON.parse(JSON.stringify(this.defectOptions))
        } else {
          console.error("form_info.optimize_list[0] is not defined")
        }
      } catch (error) {
        console.error("Error fetching defect list:", error)
      }
    },
    setMoldInfo() {
      if (this.form_info.precondition.mold_id) {
        projectMethod.getDetail(this.form_info.precondition.mold_id)
          .then(res => {
            if (res.status === 0) {
              this.form_info.precondition.mold_id = res.data.mold_info.id
              this.form_info.precondition.mold_no = res.data.mold_info.mold_no
              this.form_info.precondition.cavity_num = res.data.mold_info.cavity_num
              this.form_info.precondition.inject_cycle_require = res.data.mold_info.inject_cycle_require
              this.form_info.precondition.subrule_no = res.data.mold_info.subrule_no

              this.form_info.precondition.product_type = res.data.mold_info.product_small_type

              this.form_info.precondition.product_no = res.data.mold_info.product_no
              this.form_info.precondition.product_name = res.data.mold_info.product_name
              this.form_info.precondition.product_total_weight = res.data.mold_info.product_total_weight
              this.form_info.precondition.product_ave_thickness = null
              this.form_info.precondition.product_max_thickness = null
              this.form_info.precondition.product_max_length = null 

              // 模具参数
              this.form_info.mold_info.product_infos = []


              // 包括制品总重量和流道总重量

              // this.original_total_weight = Number(res.data.mold_info.product_total_weight)
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
        // this.form_info.precondition.product_total_weight = (this.original_total_weight + Number(product_info.runner_weight)).toFixed(2)
        
        this.form_info.precondition.runner_length = product_info.runner_length
        this.form_info.precondition.runner_weight = product_info.runner_weight
        this.form_info.precondition.gate_type = product_info.gate_type
        this.form_info.precondition.gate_num = product_info.gate_num
        this.form_info.precondition.gate_shape = product_info.gate_shape
        this.form_info.precondition.gate_area = product_info.gate_area
        this.form_info.precondition.gate_radius = product_info.gate_radius
        this.form_info.precondition.gate_length = product_info.gate_length
        this.form_info.precondition.gate_width = product_info.gate_width

        this.form_info.precondition.runner_type = product_info.runner_type
        this.form_info.precondition.hot_runner_num = product_info.hot_runner_num
        // 根据阀口数量,显示热流道时序
        this.form_info.precondition.valve_num = product_info.valve_num
        // 根据热流道的段数,初始化温度值,材料的熔体推荐温度
        this.form_info.optimize_list[0].auxiliary_detail.hot_runner_temperatures = initArray(product_info.hot_runner_num, this.form_info.precondition.recommend_melt_temperature)
      }
    },
    setViewUnit() {
      if (this.form_info.precondition.machine_id) {
        machineMethod.getDetail(this.form_info.precondition.machine_id)
          .then(res => {
            if (res.status === 0) {
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
              this.form_info.mac_unit.power_method = res.data.power_method

              for (let i = 0; i < this.form_info.optimize_list.length; ++ i) {
                let optimize_view = this.form_info.optimize_list[i]
                optimize_view.process_detail.inject_para.table_data[0].unit = this.form_info.mac_unit.pressure_unit
                optimize_view.process_detail.inject_para.table_data[1].unit = this.form_info.mac_unit.velocity_unit
                optimize_view.process_detail.inject_para.table_data[2].unit = this.form_info.mac_unit.position_unit

                optimize_view.process_detail.holding_para.table_data[0].unit = this.form_info.mac_unit.pressure_unit
                optimize_view.process_detail.holding_para.table_data[1].unit = this.form_info.mac_unit.velocity_unit
                optimize_view.process_detail.holding_para.table_data[2].unit = this.form_info.mac_unit.time_unit

                optimize_view.process_detail.metering_para.table_data[0].unit = this.form_info.mac_unit.pressure_unit
                optimize_view.process_detail.metering_para.table_data[1].unit = this.form_info.mac_unit.screw_rotation_unit
                optimize_view.process_detail.metering_para.table_data[2].unit = this.form_info.mac_unit.backpressure_unit
                optimize_view.process_detail.metering_para.table_data[3].unit = this.form_info.mac_unit.position_unit

                optimize_view.process_detail.temp_para.table_data[0].unit = this.form_info.mac_unit.temperature_unit
              }
            }
          })
      }
    },
    loadHistoryProcess(process_index_id) {
      this.form_info.process_index_id = process_index_id
      if (this.form_info.process_index_id) {
        processRecordMethod.getDetail(this.form_info.process_index_id)
          .then(res => {
            if (res.status === 0 && JSON.stringify(res.data) != "{}") {
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
              this.form_info.precondition = res.data.precondition
              // 如果是读取MES,那么把来源设置为工艺优化,这样,在下发时,不下发开合模和顶针
              this.form_info.precondition.data_sources = "工艺优化"
              this.form_info.optimize_list[0].process_detail = res.data.process_detail

              // 保压
              if (res.data.process_detail.holding_para.holding_stage === 1) {
                this.form_info.init_holding_para[0].pp = res.data.process_detail.holding_para.table_data[0].sections[0]
                this.form_info.init_holding_para[1].pv = res.data.process_detail.holding_para.table_data[1].sections[0]
                this.form_info.init_holding_para[2].pt = res.data.process_detail.holding_para.table_data[2].sections[0]
              } else if (res.data.process_detail.holding_para.holding_stage > 1) {
                this.form_info.init_holding_para[0].pp = res.data.process_detail.holding_para.table_data[0].sections[1]
                this.form_info.init_holding_para[1].pv = res.data.process_detail.holding_para.table_data[1].sections[0]
                this.form_info.init_holding_para[2].pt = res.data.process_detail.holding_para.table_data[2].sections[0]
              }

              if (this.form_info.optimize_type === 0) {
                let holding_para = this.form_info.optimize_list[0].process_detail.holding_para
                for (let i = 0; i < holding_para.holding_stage; ++i) {

                  this.form_info.init_holding_para[0].sections[i] = holding_para.table_data[0].sections[i]
                  this.form_info.init_holding_para[1].sections[i] = holding_para.table_data[1].sections[i]
                  this.form_info.init_holding_para[2].sections[i] = holding_para.table_data[2].sections[i]

                  holding_para.table_data[0].sections[i] = 0
                  holding_para.table_data[1].sections[i] = 0
                  holding_para.table_data[2].sections[i] = 0
                }
              }
            } else {
              this.$message({
                message: "未读取到相关内容！",
                type: "warning"
              })
            }
          })
      }
    },
    addNewTab(tab_name) {
      let optimize = createOptimizeList(tab_name)
      optimize.feedback_detail.defect_info = JSON.parse(JSON.stringify(this.defectOptions))
      this.form_info.optimize_list.push(optimize)
      this.form_info.active_tab_index = String(tab_name)
      this.setViewUnit()
      this.highlightChange(this.form_info.active_tab_index)      
    },
    setElementStyle(element, style) {
      if (element && style === "#highlight") {
        element.style.backgroundColor = "red"
        element.style.color = "white"
      } else if (element && style === "#normal") {
        element.style.backgroundColor = "white"
        element.style.color = "black"
      }
    },
    highlightChange(tab_idx) {
      if (tab_idx > 0) {
        // 标记修改字段
        let last_idx = tab_idx - 1
        let curr_view = this.form_info.optimize_list[tab_idx].process_detail
        let last_view = this.form_info.optimize_list[last_idx].process_detail
        // 注射
        for (let i = 0; i < 6; ++i) {
          if (last_view.inject_para.table_data[0].sections[i] != curr_view.inject_para.table_data[0].sections[i]) {
            this.setElementStyle(document.getElementById(String("IP" + i + tab_idx)), "#highlight")
          } else {
            this.setElementStyle(document.getElementById(String("IP" + i + tab_idx)), "#normal")
          }
          if (last_view.inject_para.table_data[1].sections[i] != curr_view.inject_para.table_data[1].sections[i]) {
            this.setElementStyle(document.getElementById(String("IV" + i + tab_idx)), "#highlight")
          } else {
            this.setElementStyle(document.getElementById(String("IV" + i + tab_idx)), "#normal")
          }
          if (last_view.inject_para.table_data[2].sections[i] != curr_view.inject_para.table_data[2].sections[i]) {
            this.setElementStyle(document.getElementById(String("IL" + i + tab_idx)), "#highlight")
          } else {
            this.setElementStyle(document.getElementById(String("IL" + i + tab_idx)), "#normal")
          }
        }

        if (last_view.inject_para.injection_time != curr_view.inject_para.injection_time) {
          this.setElementStyle(document.getElementById(String("IT" + tab_idx)), "#highlight")
        } else {
          this.setElementStyle(document.getElementById(String("IT" + tab_idx)), "#normal")
        }
        if (last_view.inject_para.injection_delay_time != curr_view.inject_para.injection_delay_time) {
          this.setElementStyle(document.getElementById(String("ID" + tab_idx)), "#highlight")
        } else {
          this.setElementStyle(document.getElementById(String("ID" + tab_idx)), "#normal")
        }
        if (last_view.inject_para.cooling_time != curr_view.inject_para.cooling_time) {
          this.setElementStyle(document.getElementById(String("CT" + tab_idx)), "#highlight")
        } else {
          this.setElementStyle(document.getElementById(String("CT" + tab_idx)), "#normal")
        }

        // 保压
        for (let i = 0; i < 5; ++i) {
          if (last_view.holding_para.table_data[0].sections[i] != curr_view.holding_para.table_data[0].sections[i]) {
            this.setElementStyle(document.getElementById(String("PP" + i + tab_idx)), "#highlight")
          } else {
            this.setElementStyle(document.getElementById(String("PP" + i + tab_idx)), "#normal")
          }
          if (last_view.holding_para.table_data[1].sections[i] != curr_view.holding_para.table_data[1].sections[i]) {
            this.setElementStyle(document.getElementById(String("PV" + i + tab_idx)), "#highlight")
          } else {
            this.setElementStyle(document.getElementById(String("PV" + i + tab_idx)), "#normal")
          }
          if (last_view.holding_para.table_data[2].sections[i] != curr_view.holding_para.table_data[2].sections[i]) {
            this.setElementStyle(document.getElementById(String("PT" + i + tab_idx)), "#highlight")
          } else {
            this.setElementStyle(document.getElementById(String("PT" + i + tab_idx)), "#normal")
          }
        }

        if (last_view.VP_switch.VP_switch_mode != curr_view.VP_switch.VP_switch_mode) {
          this.setElementStyle(document.getElementById(String("VPTM" + tab_idx)), "#highlight")
        } else {
          this.setElementStyle(document.getElementById(String("VPTM" + tab_idx)), "#normal")
        }
        if (last_view.VP_switch.VP_switch_time != curr_view.VP_switch.VP_switch_time) {
          this.setElementStyle(document.getElementById(String("VPTT" + tab_idx)), "#highlight")
        } else {
          this.setElementStyle(document.getElementById(String("VPTT" + tab_idx)), "#normal")
        }
        if (last_view.VP_switch.VP_switch_position != curr_view.VP_switch.VP_switch_position) {
          this.setElementStyle(document.getElementById(String("VPTL" + tab_idx)), "#highlight")
        } else {
          this.setElementStyle(document.getElementById(String("VPTL" + tab_idx)), "#normal")
        }
        if (last_view.VP_switch.VP_switch_pressure != curr_view.VP_switch.VP_switch_pressure) {
          this.setElementStyle(document.getElementById(String("VPTP" + tab_idx)), "#highlight")
        } else {
          this.setElementStyle(document.getElementById(String("VPTP" + tab_idx)), "#normal")
        }
        if (last_view.VP_switch.VP_switch_velocity != curr_view.VP_switch.VP_switch_velocity) {
          this.setElementStyle(document.getElementById(String("VPTV" + tab_idx)), "#highlight")
        } else {
          this.setElementStyle(document.getElementById(String("VPTV" + tab_idx)), "#normal")
        }

        // 计量
        for (let i = 0; i < 4; ++i) {
          if (last_view.metering_para.table_data[0].sections[i] != curr_view.metering_para.table_data[0].sections[i]) {
            this.setElementStyle(document.getElementById(String("MP" + i + tab_idx)), "#highlight")
          } else {
            this.setElementStyle(document.getElementById(String("MP" + i + tab_idx)), "#normal")
          }
          if (last_view.metering_para.table_data[1].sections[i] != curr_view.metering_para.table_data[1].sections[i]) {
            this.setElementStyle(document.getElementById(String("MSR" + i + tab_idx)), "#highlight")
          } else {
            this.setElementStyle(document.getElementById(String("MSR" + i + tab_idx)), "#normal")
          }
          if (last_view.metering_para.table_data[2].sections[i] != curr_view.metering_para.table_data[2].sections[i]) {
            this.setElementStyle(document.getElementById(String("MBP" + i + tab_idx)), "#highlight")
          } else {
            this.setElementStyle(document.getElementById(String("MBP" + i + tab_idx)), "#normal")
          }
          if (last_view.metering_para.table_data[3].sections[i] != curr_view.metering_para.table_data[3].sections[i]) {
            this.setElementStyle(document.getElementById(String("ML" + i + tab_idx)), "#highlight")
          } else {
            this.setElementStyle(document.getElementById(String("ML" + i + tab_idx)), "#normal")
          }
        }

        if (last_view.metering_para.decompressure_mode_before_metering != curr_view.metering_para.decompressure_mode_before_metering) {
          this.setElementStyle(document.getElementById(String("DMBM" + tab_idx)), "#highlight")
        } else {
          this.setElementStyle(document.getElementById(String("DMBM" + tab_idx)), "#normal")
        }
        if (last_view.metering_para.decompressure_mode_after_metering != curr_view.metering_para.decompressure_mode_after_metering) {
          this.setElementStyle(document.getElementById(String("DMAM" + tab_idx)), "#highlight")
        } else {
          this.setElementStyle(document.getElementById(String("DMAM" + tab_idx)), "#normal")
        }

        if (last_view.metering_para.decompressure_paras[0].pressure != curr_view.metering_para.decompressure_paras[0].pressure) {
          this.setElementStyle(document.getElementById(String("DPBM" + tab_idx)), "#highlight")
        } else {
          this.setElementStyle(document.getElementById(String("DPBM" + tab_idx)), "#normal")
        }
        if (last_view.metering_para.decompressure_paras[0].velocity != curr_view.metering_para.decompressure_paras[0].velocity) {
          this.setElementStyle(document.getElementById(String("DVBM" + tab_idx)), "#highlight")
        } else {
          this.setElementStyle(document.getElementById(String("DVBM" + tab_idx)), "#normal")
        }
        if (last_view.metering_para.decompressure_paras[0].distance != curr_view.metering_para.decompressure_paras[0].distance) {
          this.setElementStyle(document.getElementById(String("DDBM" + tab_idx)), "#highlight")
        } else {
          this.setElementStyle(document.getElementById(String("DDBM" + tab_idx)), "#normal")
        }
        if (last_view.metering_para.decompressure_paras[0].time != curr_view.metering_para.decompressure_paras[0].time) {
          this.setElementStyle(document.getElementById(String("DTBM" + tab_idx)), "#highlight")
        } else {
          this.setElementStyle(document.getElementById(String("DTBM" + tab_idx)), "#normal")
        }

        if (last_view.metering_para.decompressure_paras[1].pressure != curr_view.metering_para.decompressure_paras[1].pressure) {
          this.setElementStyle(document.getElementById(String("DPAM" + tab_idx)), "#highlight")
        } else {
          this.setElementStyle(document.getElementById(String("DPAM" + tab_idx)), "#normal")
        }
        if (last_view.metering_para.decompressure_paras[1].velocity != curr_view.metering_para.decompressure_paras[1].velocity) {
          this.setElementStyle(document.getElementById(String("DVAM" + tab_idx)), "#highlight")
        } else {
          this.setElementStyle(document.getElementById(String("DVAM" + tab_idx)), "#normal")
        }
        if (last_view.metering_para.decompressure_paras[1].distance != curr_view.metering_para.decompressure_paras[1].distance) {
          this.setElementStyle(document.getElementById(String("DDAM" + tab_idx)), "#highlight")
        } else {
          this.setElementStyle(document.getElementById(String("DDAM" + tab_idx)), "#normal")
        }
        if (last_view.metering_para.decompressure_paras[1].time != curr_view.metering_para.decompressure_paras[1].time) {
          this.setElementStyle(document.getElementById(String("DTAM" + tab_idx)), "#highlight")
        } else {
          this.setElementStyle(document.getElementById(String("DTAM" + tab_idx)), "#normal")
        }

        if (last_view.metering_para.metering_delay_time != curr_view.metering_para.metering_delay_time) {
          this.setElementStyle(document.getElementById(String("MD" + tab_idx)), "#highlight")
        } else {
          this.setElementStyle(document.getElementById(String("MD" + tab_idx)), "#normal")
        }
        if (last_view.metering_para.metering_ending_position != curr_view.metering_para.metering_ending_position) {
          this.setElementStyle(document.getElementById(String("MEL" + tab_idx)), "#highlight")
        } else {
          this.setElementStyle(document.getElementById(String("MEL" + tab_idx)), "#normal")
        }

        // 料筒温度
        for (let i = 0; i < 10; ++i) {
          if (last_view.temp_para.table_data[0].sections[i] != curr_view.temp_para.table_data[0].sections[i]) {
            if (i === 0) {
              this.setElementStyle(document.getElementById(String("NT" + tab_idx)), "#highlight")
            } else {
              this.setElementStyle(document.getElementById(String("BT" + i + tab_idx)), "#highlight")
            }
          } else {
            if (i === 0) {
              this.setElementStyle(document.getElementById(String("NT" + tab_idx)), "#normal")
            } else {
              this.setElementStyle(document.getElementById(String("BT" + i + tab_idx)), "#normal")
            }
          }
        }
        let curr_auxiliary_view = this.form_info.optimize_list[tab_idx].auxiliary_detail
        let last_auxiliary_view = this.form_info.optimize_list[last_idx].auxiliary_detail
        // 热流道温度
        if (this.form_info.precondition.hot_runner_num){
          for (let i = 0; i < this.form_info.precondition.hot_runner_num; ++i) {
            if (last_auxiliary_view.hot_runner_temperatures[i] != curr_auxiliary_view.hot_runner_temperatures[i]) {
              this.setElementStyle(document.getElementById(String("HRT" + i + tab_idx)), "#highlight")
            } else {
              this.setElementStyle(document.getElementById(String("HRT" + i + tab_idx)), "#normal")
            }
          }
        }
        // 热流道阀口时序控制
        if (curr_auxiliary_view.hot_runner.valve_num){
          for (let i = 0; i < curr_auxiliary_view.hot_runner.valve_num; ++i) {
            if (last_auxiliary_view.hot_runner.sequential_ctrl_time[i] != curr_auxiliary_view.hot_runner.sequential_ctrl_time[i]) {
              this.setElementStyle(document.getElementById(String("SCT" + i + tab_idx)), "#highlight")
            } else {
              this.setElementStyle(document.getElementById(String("SCT" + i + tab_idx)), "#normal")
            }
          }
        }
        // 模温机
        if (last_auxiliary_view.mold_temp.setting_temp != curr_auxiliary_view.mold_temp.setting_temp) {
          this.setElementStyle(document.getElementById(String("MT" + tab_idx)), "#highlight")
        } else {
          this.setElementStyle(document.getElementById(String("MT" + tab_idx)), "#normal")
        }
        if (curr_auxiliary_view.mold_temp.mold_temp_num){
          for (let i = 0; i < curr_auxiliary_view.mold_temp.mold_temp_num; ++i) {
            if (last_auxiliary_view.mold_temp.mold_temp_list[i] != curr_auxiliary_view.mold_temp.mold_temp_list[i]) {
              this.setElementStyle(document.getElementById(String("MT" + i + tab_idx)), "#highlight")
            } else {
              this.setElementStyle(document.getElementById(String("MT" + i + tab_idx)), "#normal")
            }
          }
        }
      }
    },
    getProcessOptimizeDetail() {
      if (this.id) {
        processOptimizeMethod.getDetail(this.id)
          .then(res => {
            if (res.status === 0 && JSON.stringify(res.data) != "{}") {
              this.form_info.process_index_id = res.data.process_index_id
              this.form_info.precondition = res.data.precondition
              this.form_info.optimize_list = res.data.optimize_list
              if (this.form_info.flaw_picture_url) {
                downloadFile({
                  "search_type": "media",
                  "file_url": this.form_info.flaw_picture_url
                }).then(res => {
                  if (res.status == 0 && res.data.length > 0) {
                    this.flaw_picture_info.id = res.data[0].id
                    this.flaw_picture_info.name = res.data[0].name
                    this.flaw_picture_info.url = res.data[0].url
                  }
                })
              } else {
                this.flaw_picture_info.id = null
                this.flaw_picture_info.name = null
                this.flaw_picture_info.url = null
              }
            } else {
              this.$message({
                message: "未读取到相关内容！",
                type: "warning"
              })
            }
          })
      }

      if (this.$route.query.process_id) {
        this.resetView()
        this.loadHistoryProcess(this.$route.query.process_id)
      }
    },
    saveProcessOptimizeDetail() {
      // 判断初始工艺参数数据来源
      processIndexMethod.getDetail(this.form_info.process_index_id)
        .then(res => {
          if (res.status == 0) {
            if (res.data.status == 1) {
            // 从工艺参数初始化获得初始工艺参数，直接保存工艺优化记录到数据库
              let optimize_para = {
                process_index_id: this.form_info.process_index_id,
                precondition: this.form_info.precondition,
                optimize_list: this.form_info.optimize_list,
                flaw_picture_url: this.form_info.flaw_picture_url
              }
              processOptimizeMethod.add(optimize_para)
                .then(res => {
                  if (res.status === 0) {
                    this.$message({
                      message: "工艺优化数据已上传至数据库！",
                      type: "success"
                    })
                  }
                })
            } else if (res.data.status == 2) {
            // 从工艺参数记录表直接读取初始工艺参数，需要创建优化索引
              let process_index = {
                company_id: UserModule.company_id,
                status: 1, // status 1: 工艺参数索引; 2: 工艺优化索引
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

                machine_id: this.form_info.precondition.machine_id,
                machine_data_source: this.form_info.precondition.machine_data_source,
                machine_trademark: this.form_info.precondition.machine_trademark,
                machine_serial_no: this.form_info.precondition.machine_serial_no,

                polymer_id: this.form_info.precondition.polymer_id,
                polymer_abbreviation: this.form_info.precondition.polymer_abbreviation,
                polymer_trademark: this.form_info.precondition.polymer_trademark,
              }

              // 插入工艺优化索引到数据库
              processIndexMethod.add(process_index)
                .then(res => {
                  if (res.status == 0) {
                    this.form_info.process_index_id = res.data.id
  
                    // 保存工艺优化记录到数据库
                    let optimize_para = {
                      process_index_id: this.form_info.process_index_id,
                      precondition: this.form_info.precondition,
                      optimize_list: this.form_info.optimize_list,
                      flaw_picture_url: this.form_info.flaw_picture_url
                    }
                    processOptimizeMethod.add(optimize_para)
                      .then(res => {
                        if (res.status === 0) {
                          this.$message({
                            message: "工艺优化数据已上传至数据库！",
                            type: "success"
                          })
                        }
                      })
                  }
                })
            }
          }
        })
    },
    async initProcessPara() {
      let init_data = {
        company_id: UserModule.company_id,
        optimize_type: this.form_info.optimize_type,
        status: 1,
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
        valve_num: this.form_info.precondition.valve_num,

        runner_type: this.form_info.precondition.runner_type,
        hot_runner_num: this.form_info.precondition.hot_runner_num,

        inject_part: this.form_info.precondition.inject_part,
        product_no: this.form_info.precondition.product_no,
        product_type: this.form_info.precondition.product_type,
        product_name: this.form_info.precondition.product_name,
        product_total_weight: this.form_info.precondition.product_total_weight,
        product_ave_thickness: this.form_info.precondition.product_ave_thickness,
        product_max_thickness: this.form_info.precondition.product_max_thickness,
        product_max_length: this.form_info.precondition.product_max_length,

        machine_id: this.form_info.precondition.machine_id,
        machine_data_source: this.form_info.precondition.machine_data_source,
        machine_trademark: this.form_info.precondition.machine_trademark,
        machine_serial_no: this.form_info.precondition.machine_serial_no,

        polymer_id: this.form_info.precondition.polymer_id,
        polymer_abbreviation: this.form_info.precondition.polymer_abbreviation,
        polymer_trademark: this.form_info.precondition.polymer_trademark,

        injection_stage: this.form_info.optimize_list[0].process_detail.inject_para.injection_stage,
        holding_stage: this.form_info.optimize_list[0].process_detail.holding_para.holding_stage,
        VP_switch_mode: this.form_info.optimize_list[0].process_detail.VP_switch.VP_switch_mode,
        metering_stage: this.form_info.optimize_list[0].process_detail.metering_para.metering_stage,
        decompressure_mode_before_metering: this.form_info.optimize_list[0].process_detail.metering_para.decompressure_mode_before_metering,
        decompressure_mode_after_metering: this.form_info.optimize_list[0].process_detail.metering_para.decompressure_mode_after_metering,
        barrel_temperature_stage: this.form_info.optimize_list[0].process_detail.temp_para.barrel_temperature_stage,
      }
      let valid = false
      await this.$refs["precondition"].$refs["form"].validate((v) => {valid = v})
      if (!valid){
        return
      }

      await initialProcessAlgorithm(init_data)
        .then(res => {
          if (res.status === 0) {

            let init_para = res.data
            this.form_info.process_index_id = init_para.process_index_id

            let init_process_detail = this.form_info.optimize_list[0].process_detail // 初始化页面
            // 注射
            init_process_detail.inject_para.injection_stage = init_para["injection_stage"]
            for (let i = 0; i < init_para["injection_stage"]; i++) {
              init_process_detail.inject_para.table_data[0].sections[i] = init_para["IP" + i]
              init_process_detail.inject_para.table_data[1].sections[i] = init_para["IV" + i]
              init_process_detail.inject_para.table_data[2].sections[i] = init_para["IL" + i]
            }
            init_process_detail.inject_para.injection_time = init_para["IT"]
            init_process_detail.inject_para.injection_delay_time = init_para["ID"]
            init_process_detail.inject_para.cooling_time = init_para["CT"]

            // 保压
            this.form_info.init_holding_para[0].pp = init_para["PP0"]
            this.form_info.init_holding_para[1].pv = init_para["PV0"]
            this.form_info.init_holding_para[2].pt = init_para["PT0"]
            init_process_detail.holding_para.holding_stage = init_para["holding_stage"]
            for (let i = 0; i < init_para["holding_stage"]; i++) {
            // 缓存初始化的保压参数
              this.form_info.init_holding_para[0].sections[i] = init_para["PP" + i]
              this.form_info.init_holding_para[1].sections[i] = init_para["PV" + i]
              this.form_info.init_holding_para[2].sections[i] = init_para["PT" + i]
              if (this.form_info.optimize_type === 0) {
                init_process_detail.holding_para.table_data[0].sections[i] = 0
                init_process_detail.holding_para.table_data[1].sections[i] = 0
                init_process_detail.holding_para.table_data[2].sections[i] = 0
              } else {
                init_process_detail.holding_para.table_data[0].sections[i] = init_para["PP" + i]
                init_process_detail.holding_para.table_data[1].sections[i] = init_para["PV" + i]
                init_process_detail.holding_para.table_data[2].sections[i] = init_para["PT" + i]
              }
            }
            // 切换方式
            init_process_detail.VP_switch.VP_switch_mode = init_para["VPTM"]
            init_process_detail.VP_switch.VP_switch_position = init_para["VPTL"]
            init_process_detail.VP_switch.VP_switch_time = init_para["VPTT"]
            init_process_detail.VP_switch.VP_switch_pressure = init_para["VPTP"]
            init_process_detail.VP_switch.VP_switch_velocity = init_para["VPTV"]

            // 计量
            init_process_detail.metering_para.metering_stage = init_para["metering_stage"]
            for (let i = 0; i < init_para["metering_stage"]; i++) {
              init_process_detail.metering_para.table_data[0].sections[i] = init_para["MP" + i]
              init_process_detail.metering_para.table_data[1].sections[i] = init_para["MSR" + i]
              init_process_detail.metering_para.table_data[2].sections[i] = init_para["MBP" + i]
              init_process_detail.metering_para.table_data[3].sections[i] = init_para["ML" + i]
            }
            // 储料切换方式
            init_process_detail.metering_para.decompressure_mode_before_metering = init_para["DMBM"]
            init_process_detail.metering_para.decompressure_mode_after_metering = init_para["DMAM"]

            // 储前
            init_process_detail.metering_para.decompressure_paras[0].pressure = init_para["DPBM"]
            init_process_detail.metering_para.decompressure_paras[0].velocity = init_para["DVBM"]
            init_process_detail.metering_para.decompressure_paras[0].distance = init_para["DDBM"]
            init_process_detail.metering_para.decompressure_paras[0].time = init_para["DTBM"]

            // 储后
            init_process_detail.metering_para.decompressure_paras[1].pressure = init_para["DPAM"]
            init_process_detail.metering_para.decompressure_paras[1].velocity = init_para["DVAM"]
            init_process_detail.metering_para.decompressure_paras[1].distance = init_para["DDAM"]
            init_process_detail.metering_para.decompressure_paras[1].time = init_para["DTAM"]

            init_process_detail.metering_para.metering_delay_time = init_para["MD"]
            init_process_detail.metering_para.metering_ending_position = init_para["MEL"]

            // 料筒温度
            init_process_detail.temp_para.barrel_temperature_stage = init_para["barrel_temperature_stage"]
            for (let i = 0; i < init_para["barrel_temperature_stage"]; i++) {
              if ( i === 0) {
                init_process_detail.temp_para.table_data[0].sections[i] = init_para["NT"]
              } else {
                init_process_detail.temp_para.table_data[0].sections[i] = init_para["BT" + i]
              }
            }

            let auxiliary_detail = this.form_info.optimize_list[0].auxiliary_detail
            // 热流道时序控制
            auxiliary_detail.hot_runner.valve_num = this.form_info.precondition.valve_num
            if (auxiliary_detail.hot_runner.valve_num) {
              for (let i = 0; i < auxiliary_detail.hot_runner.valve_num; ++i) {
                auxiliary_detail.hot_runner.sequential_ctrl_time[i] = init_para["SCT" + i]
              }
            }

            // 模温
            auxiliary_detail.mold_temp.setting_temp = init_para["mold_temp"]
            if (auxiliary_detail.mold_temp.mold_temp_num) {
              for (let i = 0; i < auxiliary_detail.mold_temp.mold_temp_num; ++i) {
                auxiliary_detail.mold_temp.mold_temp_list[i] = init_para["mold_temp"]
              }
            }
            // 热流道温度
            auxiliary_detail.hot_runner_temperatures = this.form_info.optimize_list[0].auxiliary_detail.hot_runner_temperatures
            this.$set(this.form_info.optimize_list[0])
            // 初始化之后保存数据到mongo
            this.saveProcessOptimizeDetail()
          }
        })

    },
    async constructCommitParams() {
      // 判断机器动力方式是否为空
      if (!this.form_info.mac_unit.power_method) {
        this.$message({
          type: "warning",
          message: "机器信息不完整 - 动力方式为空, 请补充相关信息"
        })
        return false
      }

      // 判断缺陷修正需要用到的计算参数是否为空
      let optimize_detail = this.form_info.optimize_list[0].process_detail
      if (optimize_detail.inject_para.injection_time == null) {
        this.$message({
          type: "warning",
          message: "注射时间不能为空"
        })
        return false
      } else if (optimize_detail.inject_para.cooling_time == null) {
        this.$message({
          type: "warning",
          message: "冷却时间不能为空"
        })
        return false
      } 
      for (let j = 1; j <= optimize_detail.inject_para.injection_stage; j++) {
        if (optimize_detail.inject_para.table_data[0].sections[j - 1] == null) {
          this.$message({
            type: "warning",
            message: "注射" + j + "段压力不能为空"
          })
          return false
        } else if (optimize_detail.inject_para.table_data[1].sections[j - 1] == null) {
          this.$message({
            type: "warning",
            message: "注射" + j + "段速度不能为空"
          })
          return false
        } else if (optimize_detail.inject_para.table_data[2].sections[j - 1] == null) {
          this.$message({
            type: "warning",
            message: "注射" + j + "段位置不能为空"
          })
          return false
        } 
      }
      for (let j = 1; j <= optimize_detail.holding_para.holding_stage; j++) {
        if (optimize_detail.holding_para.table_data[0].sections[j - 1] == null) {
          this.$message({
            type: "warning",
            message: "保压" + j + "段压力不能为空"
          })
          return false
        } else if (optimize_detail.holding_para.table_data[1].sections[j - 1] == null) {
          this.$message({
            type: "warning",
            message: "保压" + j + "段速度不能为空"
          })
          return false
        } else if (optimize_detail.holding_para.table_data[2].sections[j - 1] == null) {
          this.$message({
            type: "warning",
            message: "保压" + j + "段时间不能为空"
          })
          return false
        } 
      }
      if (optimize_detail.VP_switch.VP_switch_position == null && 
      optimize_detail.VP_switch.VP_switch_time == null &&
      optimize_detail.VP_switch.VP_switch_pressure == null &&
      optimize_detail.VP_switch.VP_switch_velocity == null
      ) {
        this.$message({
          type: "warning",
          message: "VP切换不能为空"
        })
        return false
      } 
      for (let j = 1; j < optimize_detail.temp_para.barrel_temperature_stage; j++) {
        if (optimize_detail.temp_para.table_data[0].sections[0] == null) {
          this.$message({
            type: "warning",
            message: "喷嘴温度不能为空"
          })
          return false
        } else if (optimize_detail.temp_para.table_data[0].sections[j] == null) {
          this.$message({
            type: "warning",
            message: "温度" + j + "段不能为空"
          })
          return false
        }
      }
      for (let j = 1; j <= optimize_detail.metering_para.metering_stage; j++) {
        if (optimize_detail.metering_para.table_data[0].sections[j - 1] == null && this.form_info.mac_unit.power_method !== "电动机") {
          this.$message({
            type: "warning",
            message: "计量" + j + "段压力不能为空"
          })
          return false
        } else if (optimize_detail.metering_para.table_data[1].sections[j - 1] == null) {
          this.$message({
            type: "warning",
            message: "计量" + j + "段螺杆转速不能为空"
          })
          return false
        } else if (optimize_detail.metering_para.table_data[2].sections[j - 1] == null) {
          this.$message({
            type: "warning",
            message: "计量" + j + "段背压不能为空"
          })
          return false
        } else if (optimize_detail.metering_para.table_data[3].sections[j - 1] == null) {
          this.$message({
            type: "warning",
            message: "计量" + j + "段位置不能为空"
          })
          return false
        } 
      }
      if (optimize_detail.metering_para.decompressure_mode_after_metering == "距离") {
        if (optimize_detail.metering_para.decompressure_paras[1].pressure == null && this.form_info.mac_unit.power_method !== "电动机") {
          this.$message({
            type: "warning",
            message: "储后压力不能为空"
          })
          return false
        } else if (optimize_detail.metering_para.decompressure_paras[1].velocity == null) {
          this.$message({
            type: "warning",
            message: "储后速度不能为空"
          })
          return false
        } else if (optimize_detail.metering_para.decompressure_paras[1].distance == null) {
          this.$message({
            type: "warning",
            message: "储后距离不能为空"
          })
          return false
        } 
      } else if (optimize_detail.metering_para.decompressure_mode_after_metering == "时间") {
        if (optimize_detail.metering_para.decompressure_paras[1].pressure == null) {
          this.$message({
            type: "warning",
            message: "储后压力不能为空"
          })
          return false
        } else if (optimize_detail.metering_para.decompressure_paras[1].velocity == null) {
          this.$message({
            type: "warning",
            message: "储后速度不能为空"
          })
          return false
        } else if (optimize_detail.metering_para.decompressure_paras[1].time == null) {
          this.$message({
            type: "warning",
            message: "储后时间不能为空"
          })
          return false
        } 
      } else if (optimize_detail.metering_para.decompressure_mode_after_metering == "否") {
        optimize_detail.metering_para.decompressure_paras[1].pressure = 0
        optimize_detail.metering_para.decompressure_paras[1].velocity = 0
        optimize_detail.metering_para.decompressure_paras[1].time = 0
        optimize_detail.metering_para.decompressure_paras[1].distance = 0
      }
      if (optimize_detail.metering_para.metering_ending_position == null) {
        this.$message({
          type: "warning",
          message: "终止位置不能为空"
        })
        return false
      }

      this.form_info.active_tab_index = String(this.form_info.optimize_list.length - 1)
      let process_optimize = this.form_info.optimize_list[this.form_info.optimize_list.length - 1]      

      let has_defect = false
      let current_defect = null
      this.light_defects = false
      for (let i = 0;i < process_optimize.feedback_detail.defect_info.length; i++) {
        let detect_info = process_optimize.feedback_detail.defect_info[i]
        if (detect_info.level != "无缺陷") {
          process_optimize.feedback_detail.defect_info[i].count += 1
          has_defect = true
          current_defect = detect_info.label
        }
        if (["中等", "严重", "非常严重"].includes(detect_info.level)) {
          this.light_defects = true
        }
      }
      // 如果没有缺陷,则不需要提交
      if (has_defect === false) {
        this.$message({
          type: "warning",
          message: "请填写缺陷反馈!"
        })
      } else {
        const subrule_no = this.form_info.precondition.subrule_no
        // 如果模具已经绑定子规则库,那么查找该规则库对应缺陷是否有规则
        if (subrule_no){
          let query = {
            rule_type: "子规则库",
            subrule_no: subrule_no,
            defect_name: current_defect,  // 查找当前缺陷在子规则中是否有对应
          }
  
          // 检查当前制品的当前缺陷是否有对应的子规则
          let hasProductSubrule = await this.getProductSubrule(query)
          if (hasProductSubrule) {
            // 调用接口获得修正反馈结果
            this.callInterface(current_defect)
          }
          else {
            // 如果绑定规则库中缺陷没有规则,那么调用通用
            this.callGeneral(current_defect)
          }
        }
        else {
          // 如果没有绑定规则库,那么调用通用
          this.callGeneral(current_defect)
        } 
      }
    },
    async callGeneral(current_defect){
      let query = {
        rule_type: "子规则库",
        product_small_type: "通用",
        defect_name: current_defect,  // 查找当前缺陷在子规则中是否有对应
      }

      let hasProductSubrule = await this.getProductSubrule(query)

      if (hasProductSubrule) {
        this.$message({
          message: `模具绑定的规则库中没有缺陷${current_defect}的规则,正在调用通用规则库`,
          type: "success"
        }) 
        this.general = true
        // 调用接口获得修正反馈结果
        this.callInterface(current_defect)
      }
      else {
        this.$message({
          message: `模具绑定的规则库和通用规则库没有当前缺陷${current_defect}的规则,请到规则流程图中增加相应的规则`,
          type: "warning"
        })
      }
    },
    getProductSubrule(query){
      return new Promise((resolve, reject) => {
        ruleDetailMethod.get(query)
          .then(res => {
          // 找对应制品对应缺陷的子规则库,如果没有的话,尝试调用通用子规则库
            if (res.status === 0 && res.data.total === 0) {
              resolve(false)
            } else {
              this.currentSubrule = res.data.items[0].subrule_no
              this.showRules = true
              resolve(true)
            }
          })
      })
    },
    transferParas(optimize_detail, optimize_para){
      optimize_detail.process_detail.inject_para.injection_stage = optimize_para["injection_stage"]
      for (let i = 0; i < optimize_para["injection_stage"]; i++) {
        optimize_detail.process_detail.inject_para.table_data[0].sections[i] = optimize_para["IP" + i]
        optimize_detail.process_detail.inject_para.table_data[1].sections[i] = optimize_para["IV" + i]
        optimize_detail.process_detail.inject_para.table_data[2].sections[i] = optimize_para["IL" + i]
      }

      optimize_detail.process_detail.inject_para.injection_time = optimize_para["IT"]   // 注射时间
      optimize_detail.process_detail.inject_para.injection_delay_time = optimize_para["ID"]
      optimize_detail.process_detail.inject_para.cooling_time = optimize_para["CT"]   // 冷却时间

      // 保压:用返回值确定保压段数
      optimize_detail.process_detail.holding_para.holding_stage = optimize_para["holding_stage"]
      for (let i = 0; i < optimize_para["holding_stage"]; i++) {
        optimize_detail.process_detail.holding_para.table_data[0].sections[i] = optimize_para["PP" + i]
        optimize_detail.process_detail.holding_para.table_data[1].sections[i] = optimize_para["PV" + i]
        optimize_detail.process_detail.holding_para.table_data[2].sections[i] = optimize_para["PT" + i]
      }

      optimize_detail.process_detail.VP_switch.VP_switch_mode = optimize_para["VPTM"]
      optimize_detail.process_detail.VP_switch.VP_switch_position = optimize_para["VPTL"]
      optimize_detail.process_detail.VP_switch.VP_switch_pressure = optimize_para["VPTP"]
      optimize_detail.process_detail.VP_switch.VP_switch_time = optimize_para["VPTT"]
      optimize_detail.process_detail.VP_switch.VP_switch_velocity = optimize_para["VPTV"]

      // 储料
      optimize_detail.process_detail.metering_para.metering_stage = optimize_para["metering_stage"]
      for (let i = 0; i < optimize_para["metering_stage"]; i++) {
        optimize_detail.process_detail.metering_para.table_data[0].sections[i] = optimize_para["MP" + i]
        optimize_detail.process_detail.metering_para.table_data[1].sections[i] = optimize_para["MSR" + i]
        optimize_detail.process_detail.metering_para.table_data[2].sections[i] = optimize_para["MBP" + i]
        optimize_detail.process_detail.metering_para.table_data[3].sections[i] = optimize_para["ML" + i]
      }

      optimize_detail.process_detail.metering_para.decompressure_mode_before_metering = optimize_para["DMBM"]
      optimize_detail.process_detail.metering_para.decompressure_mode_after_metering = optimize_para["DMAM"]

      optimize_detail.process_detail.metering_para.decompressure_paras[0].pressure = optimize_para["DPBM"]
      optimize_detail.process_detail.metering_para.decompressure_paras[0].velocity = optimize_para["DVBM"]
      optimize_detail.process_detail.metering_para.decompressure_paras[0].distance = optimize_para["DDBM"]
      optimize_detail.process_detail.metering_para.decompressure_paras[0].time = optimize_para["DTBM"]

      optimize_detail.process_detail.metering_para.decompressure_paras[1].pressure = optimize_para["DPAM"]
      optimize_detail.process_detail.metering_para.decompressure_paras[1].velocity = optimize_para["DVAM"]
      optimize_detail.process_detail.metering_para.decompressure_paras[1].distance = optimize_para["DDAM"]
      optimize_detail.process_detail.metering_para.decompressure_paras[1].time = optimize_para["DTAM"]

      optimize_detail.process_detail.metering_para.metering_delay_time = optimize_para["MD"]
      optimize_detail.process_detail.metering_para.metering_ending_position = optimize_para["MEL"]

      // 料筒温度
      optimize_detail.process_detail.temp_para.barrel_temperature_stage = optimize_para["barrel_temperature_stage"]
      for (let i = 0; i < optimize_para["barrel_temperature_stage"]; i++) {
        if (i === 0) {
          optimize_detail.process_detail.temp_para.table_data[0].sections[i] = optimize_para["NT"]
        } else {
          optimize_detail.process_detail.temp_para.table_data[0].sections[i] = optimize_para["BT" + i]
        }
      }

      // 热流道时序阀口控制
      this.form_info.precondition.valve_num = optimize_para["SCVN"]
      optimize_detail.auxiliary_detail.hot_runner.valve_num = optimize_para["SCVN"]
      for (let i = 0; i < optimize_para["SCVN"]; ++i) {
        optimize_detail.auxiliary_detail.hot_runner.sequential_ctrl_time[i] = optimize_para["SCT" + i]
      }

      // 模温机设定温度
      optimize_detail.auxiliary_detail.mold_temp.mold_temp_num = optimize_para["MTN"]
      optimize_detail.auxiliary_detail.mold_temp.setting_temp = optimize_para["MT"]
      for (let i = 0; i < optimize_para["MTN"]; ++i) {
        optimize_detail.auxiliary_detail.mold_temp.mold_temp_list[i] = optimize_para["MT" + i]
      }
      // 热流道温度
      for (let i = 0; i < optimize_para["HRN"]; ++i) {
        optimize_detail.auxiliary_detail.hot_runner_temperatures[i] = optimize_para["HRT" + i]
      }
      // 缺陷修正之后,返回的优化,并显示上一模优化效果
      optimize_detail.feedback_detail.optimize_export = optimize_para.optimize_export
      let defect_num = optimize_detail.feedback_detail.optimize_export.defect_num
      console.log("上一模的缺陷编号",defect_num)
      if (defect_num != null && defect_num !== "") {
        optimize_detail.feedback_detail.defect_info[defect_num].feedback = "上一模修正效果佳"
        optimize_detail.feedback_detail.optimize_export.defect_feedback = "上一模修正效果佳"  // 记录上一模的修正效果给后端直接调用
        optimize_detail.feedback_detail.optimize_export.rule_valid = 0
      }

      return optimize_detail
    },
    execute(){
      this.showDefects = false
      let new_tab_name = this.form_info.optimize_list.length
      this.addNewTab(new_tab_name)
      
      let optimize_detail = this.form_info.optimize_list[this.form_info.active_tab_index]
      this.transferParas(optimize_detail, this.optimize_para)

      // 优化之后保存数据到mongo
      this.saveProcessOptimizeDetail()
    },
    callInterface(current_defect){      
      let process_optimize = this.form_info.optimize_list[this.form_info.optimize_list.length - 1]
      console.log("前一个工艺",process_optimize)
      let process_params = {}
      process_params["injection_stage"] = process_optimize.process_detail.inject_para.injection_stage
      for (let i = 0; i < process_optimize.process_detail.inject_para.injection_stage; i++) {
        process_params["IP" + i] = process_optimize.process_detail.inject_para.table_data[0].sections[i]
        process_params["IV" + i] = process_optimize.process_detail.inject_para.table_data[1].sections[i]
        process_params["IL" + i] = process_optimize.process_detail.inject_para.table_data[2].sections[i]
      }

      process_params["IT"] = process_optimize.process_detail.inject_para.injection_time
      process_params["ID"] = process_optimize.process_detail.inject_para.injection_delay_time
      process_params["CT"] = process_optimize.process_detail.inject_para.cooling_time

      process_params["holding_stage"] = process_optimize.process_detail.holding_para.holding_stage
      let start_holding = false
      for (let i = 0; i < process_optimize.process_detail.holding_para.holding_stage; i++) {
        // 第2个是缩水
        if (process_optimize.feedback_detail.defect_info[1].count == 1 && this.form_info.optimize_type == 0) {
          start_holding = true
          // 启用保压参数
          process_params["PP" + i] = this.form_info.init_holding_para[0].sections[i]
          process_params["PV" + i] = this.form_info.init_holding_para[1].sections[i]
          process_params["PT" + i] = this.form_info.init_holding_para[2].sections[i]
        } else {
          process_params["PP" + i] = process_optimize.process_detail.holding_para.table_data[0].sections[i]
          process_params["PV" + i] = process_optimize.process_detail.holding_para.table_data[1].sections[i]
          process_params["PT" + i] = process_optimize.process_detail.holding_para.table_data[2].sections[i]
        }
      }
      if (start_holding){
        this.form_info.optimize_type = 1
      }
      process_params["VPTM"] = process_optimize.process_detail.VP_switch.VP_switch_mode
      process_params["VPTT"] = process_optimize.process_detail.VP_switch.VP_switch_time
      process_params["VPTL"] = process_optimize.process_detail.VP_switch.VP_switch_position
      process_params["VPTP"] = process_optimize.process_detail.VP_switch.VP_switch_pressure
      process_params["VPTV"] = process_optimize.process_detail.VP_switch.VP_switch_velocity

      process_params["metering_stage"] = process_optimize.process_detail.metering_para.metering_stage
      for (let i = 0; i < process_optimize.process_detail.metering_para.metering_stage; i++) {
        process_params["MP" + i] = process_optimize.process_detail.metering_para.table_data[0].sections[i]
        process_params["MSR" + i] = process_optimize.process_detail.metering_para.table_data[1].sections[i]
        process_params["MBP" + i] = process_optimize.process_detail.metering_para.table_data[2].sections[i]
        process_params["ML" + i] = process_optimize.process_detail.metering_para.table_data[3].sections[i]
      }

      process_params["DMBM"] = process_optimize.process_detail.metering_para.decompressure_mode_before_metering
      process_params["DMAM"] = process_optimize.process_detail.metering_para.decompressure_mode_after_metering

      process_params["DPBM"] = process_optimize.process_detail.metering_para.decompressure_paras[0].pressure
      process_params["DVBM"] = process_optimize.process_detail.metering_para.decompressure_paras[0].velocity
      process_params["DDBM"] = process_optimize.process_detail.metering_para.decompressure_paras[0].distance
      process_params["DTBM"] = process_optimize.process_detail.metering_para.decompressure_paras[0].time

      process_params["DPAM"] = process_optimize.process_detail.metering_para.decompressure_paras[1].pressure
      process_params["DVAM"] = process_optimize.process_detail.metering_para.decompressure_paras[1].velocity
      process_params["DDAM"] = process_optimize.process_detail.metering_para.decompressure_paras[1].distance
      process_params["DTAM"] = process_optimize.process_detail.metering_para.decompressure_paras[1].time

      process_params["MD"] = process_optimize.process_detail.metering_para.metering_delay_time
      process_params["MEL"] = process_optimize.process_detail.metering_para.metering_ending_position

      process_params["barrel_temperature_stage"] = process_optimize.process_detail.temp_para.barrel_temperature_stage
      for (let i = 0; i < process_optimize.process_detail.temp_para.barrel_temperature_stage; i++) {
        if (i === 0) {
          process_params["NT"] = process_optimize.process_detail.temp_para.table_data[0].sections[i]
        } else {
          process_params["BT" + i] = process_optimize.process_detail.temp_para.table_data[0].sections[i]
        }
      }

      process_params["SCVN"] = process_optimize.auxiliary_detail.hot_runner.valve_num
      for (let i = 0; i < process_optimize.auxiliary_detail.hot_runner.valve_num; i++) {
        process_params["SCT" + i] = process_optimize.auxiliary_detail.hot_runner.sequential_ctrl_time[i]
      }

      process_params["MT"] = process_optimize.auxiliary_detail.mold_temp.setting_temp
      if (process_optimize.auxiliary_detail.mold_temp.mold_temp_num){
        process_params["MTN"] = process_optimize.auxiliary_detail.mold_temp.mold_temp_num
        for (let i = 0; i < process_optimize.auxiliary_detail.mold_temp.mold_temp_num; i++) {
          process_params["MT" + i] = process_optimize.auxiliary_detail.mold_temp.mold_temp_list[i]
        }
      } 
      // 热流道
      if (this.form_info.precondition.hot_runner_num){
        process_params["HRN"] = this.form_info.precondition.hot_runner_num
        for (let i = 0; i < this.form_info.precondition.hot_runner_num; i++) {
          process_params["HRT" + i] = process_optimize.auxiliary_detail.hot_runner_temperatures[i]
        }
      }

      process_params["actual_product_weight"] = process_optimize.feedback_detail.actual_product_weight
      process_params["defect_info"] = process_optimize.feedback_detail.defect_info
      process_params["optimize_export"] = process_optimize.feedback_detail.optimize_export

      process_params["process_index_id"] = this.form_info.process_index_id
      process_params["machine_id"] = this.form_info.precondition.machine_id
      process_params["product_weight"] = this.form_info.precondition.product_total_weight
      process_params["opt_nums"] = this.form_info.optimize_list.length

      process_params["polymer_abbreviation"] = this.form_info.precondition.polymer_abbreviation
      process_params["product_small_type"] = this.form_info.precondition.product_type

      // 确定要调用的subrule_no
      process_params["subrule_no"] = this.currentSubrule
      process_params["general"] = this.general

      process_params["precondition"] = this.form_info.precondition
      process_params["precondition"]["injection_stage"] = process_optimize.process_detail.inject_para.injection_stage
      process_params["precondition"]["holding_stage"] = process_optimize.process_detail.holding_para.holding_stage
      process_params["precondition"]["VP_switch_mode"] = process_optimize.process_detail.VP_switch.VP_switch_mode
      process_params["precondition"]["metering_stage"] = process_optimize.process_detail.metering_para.metering_stage
      process_params["precondition"]["decompressure_mode_before_metering"] = process_optimize.process_detail.metering_para.decompressure_mode_before_metering
      process_params["precondition"]["decompressure_mode_after_metering"] = process_optimize.process_detail.metering_para.decompressure_mode_after_metering
      process_params["precondition"]["barrel_temperature_stage"] = process_optimize.process_detail.temp_para.barrel_temperature_stage 
      console.log("接下来调用修正", process_params)
      optimizeProcessAlgorithm(process_params)
        .then(res => {
          if (res.status === 0) {
            this.optimize_para = res.data
            // 把热流道的温度原样赋值给新的一模
            this.optimize_para["hot_runner_temperatures"] = process_optimize.auxiliary_detail.hot_runner_temperatures
          }
          // 如果反馈结果有adjust,那么直接弹窗

          // 先提示文字部分
          let instructionDict = {
            "短射":"锁模力是否过大?",
            "飞边":"锁模力是否过小?",
            "顶白":"顶针力、顶针速度是否过大?"
          }
          const defectCount = {}
          let defectDict = { "短射": "SHORTSHOT", "飞边": "FLASH", "顶白": "TOPWHITE" }
          this.form_info.optimize_list.forEach(problem => {
            const defectName = problem.feedback_detail.optimize_export.defect_name
            if (defectName in defectCount) {
              defectCount[defectName] += 1 // 如果已经存在，则数量加1
            } else if (defectName){
              defectCount[defectName] = 1 // 如果不存在，则初始化为1
            }
          })
          if (defectCount[defectDict[current_defect]] === undefined && instructionDict[current_defect] && instructionDict[current_defect] !== undefined){
            console.log("第一次出现", current_defect)
            this.$confirm(`${instructionDict[current_defect]}`,"请检查",{
              confirmButtonText: "已检查",
              type: "warning",
            }).then(() => {
              this.actualExcute()
            })   
          } else {
            console.log("不是第一次出现", current_defect)
            this.actualExcute()
          }
        })
    },
    actualExcute(){
      // 如果缺陷轻微新增页面,或者用户选择执行
      if (this.light_defects === false){
        this.execute()
      }
      if (this.light_defects === true){
        console.log("有严重缺陷")  
        let tab_name = this.form_info.optimize_list.length
        let optimize_detail = createOptimizeList(tab_name)
        optimize_detail.feedback_detail.defect_info = JSON.parse(JSON.stringify(this.defectOptions))
        this.transferParas(optimize_detail, this.optimize_para)
        this.checkChange(this.form_info.active_tab_index, optimize_detail)
        this.showDefects = true
      }
    },
    closeDefectsDialog() {
      this.showDefects = false
    },
    closeRuleChoicesDialog() {
      this.showRules = false
    },
    saveCurrentProcess() {
      this.loading = true
      let process_index = {
        company_id: UserModule.company_id,
        status: 2,
        process_no: "P" + datetimeTodayStr(),
        data_sources: "工艺优化",

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

        runner_type: this.form_info.precondition.runner_type,
        hot_runner_num: this.form_info.precondition.hot_runner_num,

        inject_part: this.form_info.precondition.inject_part,
        product_no: this.form_info.precondition.product_no,
        product_type: this.form_info.precondition.product_type,
        product_name: this.form_info.precondition.product_name,
        product_total_weight: this.form_info.precondition.product_total_weight,
        product_ave_thickness: this.form_info.precondition.product_ave_thickness,
        product_max_thickness: this.form_info.precondition.product_max_thickness,
        product_max_length: this.form_info.precondition.product_max_length,

        machine_id: this.form_info.precondition.machine_id,
        machine_data_source: this.form_info.precondition.machine_data_source,
        machine_trademark: this.form_info.precondition.machine_trademark,
        machine_serial_no: this.form_info.precondition.machine_serial_no,

        polymer_id: this.form_info.precondition.polymer_id,
        polymer_abbreviation: this.form_info.precondition.polymer_abbreviation,
        polymer_trademark: this.form_info.precondition.polymer_trademark,
      }
      processIndexMethod.add(process_index)
        .then(res => {
          if (res.status === 0) {
            let record_para = {
              "process_index_id": res.data.id,
              "precondition": this.form_info.precondition,
              "process_detail": this.form_info.optimize_list[Number(this.form_info.active_tab_index)].process_detail
            }
            processRecordMethod.add(record_para)
              .then(res => {
                if (res.status === 0) {
                  this.$message({
                    message: "工艺参数数据已上传至数据库！",
                    type: "success"
                  })
                }
              })
              .finally(() => {
                this.loading = false
              })
          }
        })
        .finally(() => {
          this.loading = false
        })
    },
    resetView() {
      this.form_info = JSON.parse(JSON.stringify(DEFAULT_FORM_INFO))
      this.form_info.optimize_list[0].feedback_detail.defect_info = JSON.parse(JSON.stringify(this.defectOptions))
    },
    onFileUploaded(fileInfo) {
      if (fileInfo) {
        this.form_info.flaw_picture_url = fileInfo.url
      } else {
        this.form_info.flaw_picture_url = null
      }
    },
    // 缺陷不是轻微,对比返回的工艺和上一模工艺,拿到改变的值
    checkChange (tab_idx, optimize_detail) {
      // 标记修改字段
      this.serious_defects_data = []
      let curr_view = optimize_detail.process_detail
      let last_view = this.form_info.optimize_list[tab_idx].process_detail

      let inject_name = new Map([
        [0,"压力"],
        [1,"速度"],
        [2,"位置"]
      ])
      // 注射
      for (let i = 0; i < 6; ++i) {
        for (let j = 0;j < 3;++j){
          if (last_view.inject_para.table_data[j].sections[i] != curr_view.inject_para.table_data[j].sections[i]) {
            // 压力, 速度, 位置
            this.serious_defects_data.push(
              {
                desc: "注射" + (i + 1) + "段" + inject_name.get(j),
                original_value: last_view.inject_para.table_data[j].sections[i],
                suggest_value: curr_view.inject_para.table_data[j].sections[i],
              }
            )
          }
        }
      }

      if (last_view.inject_para.injection_time != curr_view.inject_para.injection_time) {
        this.serious_defects_data.push(
          {
            desc: "注射时间",
            original_value: last_view.inject_para.injection_time,
            suggest_value: curr_view.inject_para.injection_time,
          }
        )
      } 
      if (last_view.inject_para.injection_delay_time != curr_view.inject_para.injection_delay_time) {
        this.serious_defects_data.push(
          {
            desc: "注射延迟",
            original_value: last_view.inject_para.injection_delay_time,
            suggest_value: curr_view.inject_para.injection_delay_time,
          }
        )
      } 
      if (last_view.inject_para.cooling_time != curr_view.inject_para.cooling_time) {
        this.serious_defects_data.push(
          {
            desc: "冷却时间",
            original_value: last_view.inject_para.cooling_time,
            suggest_value: curr_view.inject_para.cooling_time,
          }
        )
      } 
      let holding_name = new Map([
        [0,"压力"],
        [1,"速度"],
        [2,"时间"]
      ])
      // 保压
      for (let i = 0; i < 5; ++i) {
        for (let j = 0;j < 3;++j){
          if (last_view.holding_para.table_data[j].sections[i] != curr_view.holding_para.table_data[j].sections[i]) {
            // 压力, 速度, 位置
            this.serious_defects_data.push(
              {
                desc: "保压" + (i + 1) + "段" + holding_name.get(j),
                original_value: last_view.holding_para.table_data[j].sections[i],
                suggest_value: curr_view.holding_para.table_data[j].sections[i],
              }
            )
          }
        }
      }

      if (last_view.VP_switch.VP_switch_mode != curr_view.VP_switch.VP_switch_mode) {
        this.serious_defects_data.push(
          {
            desc: "VP切换方式",
            original_value: last_view.VP_switch.VP_switch_mode,
            suggest_value: curr_view.VP_switch.VP_switch_mode,
          }
        )
      } 
      if (last_view.VP_switch.VP_switch_time != curr_view.VP_switch.VP_switch_time) {
        this.serious_defects_data.push(
          {
            desc: "VP切换时间",
            original_value: last_view.VP_switch.VP_switch_time,
            suggest_value: curr_view.VP_switch.VP_switch_time,
          }
        )
      } 
      if (last_view.VP_switch.VP_switch_position != curr_view.VP_switch.VP_switch_position) {
        this.serious_defects_data.push(
          {
            desc: "VP切换位置",
            original_value: last_view.VP_switch.VP_switch_position,
            suggest_value: curr_view.VP_switch.VP_switch_position,
          }
        )
      } 
      if (last_view.VP_switch.VP_switch_pressure != curr_view.VP_switch.VP_switch_pressure) {
        this.serious_defects_data.push(
          {
            desc: "VP切换压力",
            original_value: last_view.VP_switch.VP_switch_pressure,
            suggest_value: curr_view.VP_switch.VP_switch_pressure,
          }
        )
      } 
      if (last_view.VP_switch.VP_switch_velocity != curr_view.VP_switch.VP_switch_velocity) {
        this.serious_defects_data.push(
          {
            desc: "VP切换速度",
            original_value: last_view.VP_switch.VP_switch_velocity,
            suggest_value: curr_view.VP_switch.VP_switch_velocity,
          }
        )
      } 
      let metering_name = new Map([
        [0,"压力"],
        [1,"螺杆转速"],
        [2,"背压"],
        [3,"位置"]
      ])
      // 计量
      for (let i = 0; i < 4; ++i) {
        // 压力,螺杆转速,背压,位置
        for (let j = 0;j < 3;++j){
          if (last_view.metering_para.table_data[j].sections[i] != curr_view.metering_para.table_data[j].sections[i]) {
            this.serious_defects_data.push(
              {
                desc: "计量" + (i + 1) + "段" + metering_name.get(j),
                original_value: last_view.metering_para.table_data[j].sections[i],
                suggest_value: curr_view.metering_para.table_data[j].sections[i],
              }
            )
          } 
        }
      }

      if (last_view.metering_para.decompressure_mode_before_metering != curr_view.metering_para.decompressure_mode_before_metering) {
        this.serious_defects_data.push(
          {
            desc: "储前松退模式",
            original_value: last_view.metering_para.decompressure_mode_before_metering,
            suggest_value: curr_view.metering_para.decompressure_mode_before_metering,
          }
        )
      } 
      if (last_view.metering_para.decompressure_mode_after_metering != curr_view.metering_para.decompressure_mode_after_metering) {
        this.serious_defects_data.push(
          {
            desc: "储后松退模式",
            original_value: last_view.metering_para.decompressure_mode_after_metering,
            suggest_value: curr_view.metering_para.decompressure_mode_after_metering,
          }
        )
      } 

      if (last_view.metering_para.decompressure_paras[0].pressure != curr_view.metering_para.decompressure_paras[0].pressure) {
        this.serious_defects_data.push(
          {
            desc: "储前压力",
            original_value: last_view.metering_para.decompressure_paras[0].pressure,
            suggest_value: curr_view.metering_para.decompressure_paras[0].pressure,
          }
        )
      } 
      if (last_view.metering_para.decompressure_paras[0].velocity != curr_view.metering_para.decompressure_paras[0].velocity) {
        this.serious_defects_data.push(
          {
            desc: "储前速度",
            original_value: last_view.metering_para.decompressure_paras[0].velocity,
            suggest_value: curr_view.metering_para.decompressure_paras[0].velocity,
          }
        )
      } 
      if (last_view.metering_para.decompressure_paras[0].distance != curr_view.metering_para.decompressure_paras[0].distance) {
        this.serious_defects_data.push(
          {
            desc: "储前距离",
            original_value: last_view.metering_para.decompressure_paras[0].distance,
            suggest_value: curr_view.metering_para.decompressure_paras[0].distance,
          }
        )
      } 
      if (last_view.metering_para.decompressure_paras[0].time != curr_view.metering_para.decompressure_paras[0].time) {
        this.serious_defects_data.push(
          {
            desc: "储前时间",
            original_value: last_view.metering_para.decompressure_paras[0].time,
            suggest_value: curr_view.metering_para.decompressure_paras[0].time,
          }
        )
      } 

      if (last_view.metering_para.decompressure_paras[1].pressure != curr_view.metering_para.decompressure_paras[1].pressure) {
        this.serious_defects_data.push(
          {
            desc: "储后压力",
            original_value: last_view.metering_para.decompressure_paras[1].pressure,
            suggest_value: curr_view.metering_para.decompressure_paras[1].pressure,
          }
        )
      } 
      if (last_view.metering_para.decompressure_paras[1].velocity != curr_view.metering_para.decompressure_paras[1].velocity) {
        this.serious_defects_data.push(
          {
            desc: "储后速度",
            original_value: last_view.metering_para.decompressure_paras[1].velocity,
            suggest_value: curr_view.metering_para.decompressure_paras[1].velocity,
          }
        )
      }
      if (last_view.metering_para.decompressure_paras[1].distance != curr_view.metering_para.decompressure_paras[1].distance) {
        this.serious_defects_data.push(
          {
            desc: "储后距离",
            original_value: last_view.metering_para.decompressure_paras[1].distance,
            suggest_value: curr_view.metering_para.decompressure_paras[1].distance,
          }
        )
      } 
      if (last_view.metering_para.decompressure_paras[1].time != curr_view.metering_para.decompressure_paras[1].time) {
        this.serious_defects_data.push(
          {
            desc: "储后时间",
            original_value: last_view.metering_para.decompressure_paras[1].time,
            suggest_value: curr_view.metering_para.decompressure_paras[1].time,
          }
        )
      } 

      if (last_view.metering_para.metering_delay_time != curr_view.metering_para.metering_delay_time) {
        this.serious_defects_data.push(
          {
            desc: "储料延迟",
            original_value: last_view.metering_para.metering_delay_time,
            suggest_value: curr_view.metering_para.metering_delay_time,
          }
        )
      } 
      if (last_view.metering_para.metering_ending_position != curr_view.metering_para.metering_ending_position) {
        this.serious_defects_data.push(
          {
            desc: "终止位置",
            original_value: last_view.metering_para.metering_ending_position,
            suggest_value: curr_view.metering_para.metering_ending_position,
          }
        )
      }

      // 料筒温度
      for (let i = 0; i < 10; ++i) {
        if (last_view.temp_para.table_data[0].sections[i] != curr_view.temp_para.table_data[0].sections[i]) {
          if (i === 0) {
            this.setElementStyle(document.getElementById(String("NT" + tab_idx)), "#highlight")
          } else {
            this.setElementStyle(document.getElementById(String("BT" + i + tab_idx)), "#highlight")
          }
        } 
      }
    },
    //定时器
    intervalShowButton() {
      this.timer = setTimeout(() => {
        this.btnisShow = false
      },5000)
    },
    writeMES() {
      this.checkValid()
      // 把最新的工艺参数下发到注塑机
      let len = this.form_info.optimize_list.length
      if (!this.form_info.precondition.machine_serial_no){
        this.$message({
          message: "射台编码为空,请填写注塑机射台编码后,重新选择注塑机和注射单元",
          type: "warning"
        })  
        return
      }
      if (this.is_valid === true){      
        setMesProcessMethod({
          process_detail: this.form_info.optimize_list[len - 1].process_detail,
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
              })
            }
            if (res.data.result === "outdated") {
              window.location.href = "https://iiot2.yizumi.com" // "http://kunpeng.yizumi.com:82"
            }
            if (res.data.result === "failed") {
              this.$message({
                message: "写入失败",
                type: "warning",
              })
            }
          }
        })
      }
      else {
        this.$message({
          message: "参数超过注塑机最大可设定,请根据页面提示信息修改相关参数",
          type: "warning",
        })
      }
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

	  let process_detail = this.form_info.optimize_list[this.form_info.optimize_list.length - 1].process_detail
      let metering_para = process_detail.metering_para
      posi_para_record["螺杆终止位置"] = { "element_id": "MEL", "value": metering_para.metering_ending_position }

      for (let i = 0; i < metering_para.metering_stage; ++i) {
        posi_para_record["储料" + Number(i + 1) + "段位置"] = {
          "element_id": "ML" + i,
          "value": metering_para.table_data[3].sections[i]
        }
      }

      let inject_para = process_detail.inject_para
      for (let i = 0; i < inject_para.injection_stage; ++i) {
        posi_para_record["注射" + Number(i + 1) + "段位置"] = {
          "element_id": "IL" + i,
          "value": inject_para.table_data[2].sections[i]
        }
      }

      let VP_switch = process_detail.VP_switch
      posi_para_record["VP切换位置"] = { "element_id": "VPTL", "value": VP_switch.VP_switch_position }

    
      for (let i = 1; i < screw_positions.length; ++i) {
        let last_item = posi_para_record[screw_positions[i - 1]]
        if (last_item && last_item.value) {
          for (let j = i; j < screw_positions.length; ++j) {
            let curr_item = posi_para_record[screw_positions[j]]
            if (curr_item && curr_item.value ) {
              if (Number(curr_item.value) > Number(last_item.value) && Number(last_item.value) > 0) {
                this.timer = window.setTimeout(() => {
                  this.$notify({
                    title: "提示!",
                    message: this.$createElement("i", { style: "color: teal" }, screw_positions[j] + "的值大于" + screw_positions[i - 1] + "的值，不符合要求！")
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

      for (let i = 1; i < storing_positions.length; i++) {
        let last_item = posi_para_record[storing_positions[i - 1]]
        if (last_item && last_item.value) {
          for (let j = i; j < storing_positions.length; j++) {
            let curr_item = posi_para_record[storing_positions[j]]
            if (curr_item && curr_item.value) {
              if (Number(curr_item.value) > Number(last_item.value) && Number(last_item.value) > 0) {
                this.timer = window.setTimeout(() => {
                  this.$notify({
                    title: "提示!",
                    message: this.$createElement("i", { style: "color: teal" }, storing_positions[j] + "的值大于" + storing_positions[i - 1] + "的值，不符合要求")
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
      let holding_para = process_detail.holding_para
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
     
      for (let i = 0; i < compare_list.length; ++i) {
        let item = compare_list[i]
        if (item.set_val && item.max_val) {
          if (Number(item.set_val) > Number(item.max_val)) {
            this.timer = window.setTimeout(() => {
              this.$notify({
                title: "提示!",
                message: this.$createElement("i", { style: "color: teal" }, item.set_val_label + "的设定值为: " + item.set_val 
                  + ", 大于" + item.max_val_label + "最大可设定值: " + item.max_val 
                  + ", 不符合要求！")
              })
            })

            this.setElementStyle(document.getElementById(String(item.element_id)), "#highlight")
            this.is_valid = false
          } else {
            this.setElementStyle(document.getElementById(String(item.element_id)), "#normal")  
          }
        }
      }
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
  .precondition-divider {
    margin: 15px 0 20px 0;

    span {
      color: blue;
    }
  }
</style>
