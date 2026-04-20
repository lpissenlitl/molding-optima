<template>
  <el-card>
    <!-- <h3>冷却fem+填充+保压+翘曲</h3> -->
    <div>
      <cooling-fem :technology-data="technology"> </cooling-fem>
    </div>
    <div style="height:20px"></div>
    <div>
      <el-form-item label="填充控制" prop="fill_control">
        <el-select v-model="technology.fill_control" @change="changeFillControl">
          <el-option
            v-for="(item, index) in FillControlOptions"
            :key="index"
            :label="item.label"
            :value="item.value"
          >
          </el-option>
        </el-select>
      </el-form-item>

      <el-form-item v-if="isShowTime">
        <el-input
          type="number"
          min="0"
          v-model="technology.inject_time"
          @input="
            technology.inject_time = checkNumberFormat(technology.inject_time)
          "
        >
          <span slot="suffix">s</span>
        </el-input>
      </el-form-item>
      <el-form-item v-if="isShowRate">
        <el-input
          type="number"
          min="0"
          v-model="technology.flow_rate"
          @input="
            technology.flow_rate = checkNumberFormat(technology.flow_rate)
          "
        >
          <span slot="suffix">cm³/s</span>
        </el-input>
      </el-form-item>
      <el-form-item label="由" v-if="isShowFillControl">
        <el-select v-model="technology.control_options">
          <el-option
            v-for="(item, index) in moldFlowOptions"
            :key="index"
            :label="item.label"
            :value="item.value"
          >
          </el-option>
        </el-select>
      </el-form-item>
      <el-row v-if="isShowFillControl">
        <el-col :xs="24" :lg="11" :xl="11">
          <el-table
            size="mini"
            :data="process.inject_para" 
            :key="Math.random()"
          >
            <el-table-column label="工艺参数" width="80" align="center">
              <template slot="header">
                注射段数
                <el-select 
                  v-model="process.inject_stage" 
                  size="mini"
                >
                  <el-option
                    v-for="option, idx in process.max_inject_stage_option"
                    :key="idx"
                    :label="option"
                    :value="option"
                  >
                  </el-option>
                </el-select>
              </template>
              <template slot-scope="scope">
                {{ scope.row.label }}
              </template>
            </el-table-column>
            <template v-for="(col, colidx) in process.max_inject_stage_option">
              <el-table-column
                min-width="80"
                align="center"
                :key="colidx"
                :label="injection_stage_header[col]"
              >
                <template slot-scope="scope">
                  <el-input
                    style="width:5rem"
                    v-model="process.inject_para[scope.$index].sections[colidx]" 
                    :disabled="colidx >= process.inject_stage"
                    type="number" 
                    min="0" 
                    size="mini"
                    @input="process.inject_para[scope.$index].sections[colidx]=checkNumberFormat(process.inject_para[scope.$index].sections[colidx])"
                  >
                  </el-input>
                </template>
              </el-table-column>
            </template>
            <el-table-column
              label="单位"
              width="80"
              align="center"
            >
              <template slot-scope="scope">
                {{ process.inject_para[scope.$index].unit }}
              </template>
            </el-table-column>
          </el-table>
        </el-col>
        <div v-show="isShowReference">
          <el-form-item label="参考">
            <el-select v-model="technology.reference">
              <el-option label="名义注射时间" value="1"></el-option>
              <el-option label="名义流动速率" value="2"></el-option>
            </el-select>
          </el-form-item>
          <el-form-item v-if="isShowNominalInjectionTime">
            <el-input
              type="number"
              min="0"
              v-model="technology.nominal_injection_time"
              @input="
                technology.nominal_injection_time = checkNumberFormat(
                  technology.nominal_injection_time
                )
              "
            >
              <span slot="suffix">s</span>
            </el-input>
          </el-form-item>
          <el-form-item v-if="isShowNominalRate">
            <el-input
              type="number"
              min="0"
              v-model="technology.nominal_rate"
              @input="
                technology.nominal_rate = checkNumberFormat(
                  technology.nominal_rate
                )
              "
            >
              <span slot="suffix">cm³/s</span>
            </el-input>
          </el-form-item>
          <el-form-item label="射出体积">
            <el-select v-model="technology.injection_volume">
              <el-option label="自动" value="0"></el-option>
              <el-option label="指定" value="1"></el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="注塑机螺杆直径" v-if="isShowScrewDiameter">
            <el-input
              type="number"
              min="0"
              v-model="technology.screw_diameter"
              @input="
                technology.screw_diameter = checkNumberFormat(
                  technology.screw_diameter
                )
              "
            >
              <span slot="suffix">mm</span>
            </el-input>
          </el-form-item>
          <el-form-item label="启动螺杆直径" v-if="isShowScrewDiameter">
            <el-input
              type="number"
              min="0"
              v-model="technology.start_screw_diameter"
              @input="
                technology.start_screw_diameter = checkNumberFormat(
                  technology.start_screw_diameter
                )
              "
            >
              <span slot="suffix">cm³/s</span>
            </el-input>
          </el-form-item>
        </div>
        <div v-show="isShowLimit">
          <el-form-item label="垫料警告限制">
            <el-input
              type="number"
              min="0"
              v-model="technology.packing_warning_limit"
              @input="
                technology.packing_warning_limit = checkNumberFormat(
                  technology.packing_warning_limit
                )
              "
            >
              <span slot="suffix">mm</span>
            </el-input>
          </el-form-item>
          <el-form-item label="启动螺杆位置">
            <el-input
              type="number"
              min="0"
              v-model="technology.starting_screw_position"
              @input="
                technology.starting_screw_position = checkNumberFormat(
                  technology.starting_screw_position
                )
              "
            >
              <span slot="suffix">mm</span>
            </el-input>
          </el-form-item>
        </div>
      </el-row>
      <br />

      <el-form-item label="速度/压力切换" prop="speed_switching">
        <el-select v-model="technology.speed_switching">
          <el-option
            v-for="(item, index) in SpeedSwitchingOptions"
            :key="index"
            :label="item.label"
            :value="item.value"
          >
          </el-option>
        </el-select>
      </el-form-item>

      <el-form-item v-if="isShowFillVolume">
        <el-input
          type="number"
          min="0"
          v-model="technology.fill_volume"
          @input="
            technology.fill_volume = checkNumberFormat(technology.fill_volume)
          "
        >
          <span slot="suffix">%</span>
        </el-input>
      </el-form-item>
      <el-form-item v-if="isShowScrewPosition">
        <el-input
          type="number"
          min="0"
          v-model="technology.screw_position"
          @input="
            technology.screw_position = checkNumberFormat(
              technology.screw_position
            )
          "
        >
          <span slot="suffix">mm</span>
        </el-input>
      </el-form-item>
      <el-form-item v-if="isShowInjectionPressure">
        <el-input
          type="number"
          min="0"
          v-model="technology.injection_pressure"
          @input="
            technology.injection_pressure = checkNumberFormat(
              technology.injection_pressure
            )
          "
        >
          <span slot="suffix">MPa</span>
        </el-input>
      </el-form-item>
      <el-form-item v-if="isShowHydraulicPressure">
        <el-input
          type="number"
          min="0"
          v-model="technology.hydraulic_pressure"
          @input="
            technology.hydraulic_pressure = checkNumberFormat(
              technology.hydraulic_pressure
            )
          "
        >
          <span slot="suffix">MP</span>
        </el-input>
      </el-form-item>
      <el-form-item v-if="isShowClampingForce">
        <el-input
          type="number"
          min="0"
          v-model="technology.clamping_force"
          @input="
            technology.clamping_force = checkNumberFormat(
              technology.clamping_force
            )
          "
        >
          <span slot="suffix">Ton</span>
        </el-input>
      </el-form-item>
      <el-form-item v-if="isShowInjectionTime">
        <el-input
          type="number"
          min="0"
          v-model="technology.injection_time"
          @input="
            technology.injection_time = checkNumberFormat(
              technology.injection_time
            )
          "
        >
          <span slot="suffix">s</span>
        </el-input>
      </el-form-item>
      <el-form-item label="节点" v-if="isShowControlPoint">
        <el-input v-model="technology.node">
        </el-input>
      </el-form-item>
      <el-form-item label="压力" v-if="isShowControlPoint">
        <el-input
          type="number"
          min="0"
          v-model="technology.pressure"
          @input="
            technology.pressure = checkNumberFormat(
              technology.pressure
            )
          "
        >
          <span slot="suffix">MPa</span>
        </el-input>
      </el-form-item>
      <br />

      <el-form-item label="保压控制" prop="pressure_holding_control">
        <el-select v-model="technology.pressure_holding_control">
          <el-option
            v-for="(item, index) in PressureHoldingControlOptions"
            :key="index"
            :label="item.label"
            :value="item.value"
          >
          </el-option>
        </el-select>
      </el-form-item>
      <el-row v-if="isShowHolding">
        <el-col :xs="24" :lg="11" :xl="11">
          <el-table
            size="mini"
            :data="process.holding_para" 
            :key="Math.random()"
          >
            <el-table-column width="80" align="center">
              <template slot="header">
                保压段数
                <el-select 
                  v-model="process.holding_stage" 
                  size="mini"
                >
                  <el-option
                    v-for="option, idx in process.max_holding_stage_option"
                    :key="idx"
                    :label="option"
                    :value="option"
                  >
                  </el-option>
                </el-select>
              </template>
              <template slot-scope="scope">
                {{ scope.row.label }}
              </template>
            </el-table-column>
            <template v-for="(col, colidx) in 5">
              <el-table-column
                min-width="80"
                align="center"
                :key="colidx"
                :label="holding_stage_header[col]"
              >
                <template slot-scope="scope">
                  <el-input
                    style="width:5rem"
                    v-model="process.holding_para[scope.$index].sections[colidx]" 
                    :disabled="colidx >= process.holding_stage"
                    type="number" 
                    min="0" 
                    size="mini"
                    @input="process.holding_para[scope.$index].sections[colidx]=checkNumberFormat(process.holding_para[scope.$index].sections[colidx])"
                  >
                  </el-input>
                </template>
              </el-table-column>
            </template>
            <el-table-column
              label="单位"
              width="80"
              align="center"
            >
              <template slot-scope="scope">
                {{ process.holding_para[scope.$index].unit }}
              </template>
            </el-table-column>
          </el-table>
        </el-col>
      </el-row>
    </div>
    <div style="height:20px"></div>
    <div> 
      <el-form-item label="翘曲分析类型" prop="warping_analysis_type">
        <el-select v-model="technology.warping_analysis_type">
          <el-option label="小变形" value="1"></el-option>
          <el-option label="大变形" value="2"></el-option>
          <el-option label="挫曲" value="3"></el-option>
        </el-select>
      </el-form-item>

      <el-form-item label="并行的线程数" prop="parallel_thread">
        <el-select v-model="technology.parallel_thread">
          <el-option label="自动" value="1"></el-option>
          <el-option
            label="单一线程(无并行)"
            value="4"
          ></el-option>
          <el-option label="最大值" value="2"></el-option>
          <el-option label="指定线程数" value="3"></el-option>
        </el-select>
      </el-form-item>

      <el-form-item
        label="AMG矩阵求解器选择"
        prop="amg_select"
        v-if="isShowAmg"
      >
        <el-select v-model="technology.amg_select">
          <el-option label="开" value="1"></el-option>
          <el-option label="关" value="0"></el-option>
        </el-select>
      </el-form-item>

      <el-form-item label="线程数" prop="thread_count" v-if="isShowThread">
        <el-input v-model="technology.thread_count"></el-input>
      </el-form-item>
    </div>
    <!-- <el-button
      size="mini"
      type="primary"
      class="but"
      @click="next(isShowOne, isShowTwo, isShowThree)"
      v-if="!isShowThree"
      >下一步</el-button
    >
    <el-button
      size="mini"
      type="primary"
      class="but"
      @click="last(isShowOne, isShowTwo, isShowThree)"
      v-if="!isShowOne"
      >上一步</el-button
    > -->
  </el-card>
</template>

<script>
import coolingFem from "./coolingFem.vue";
import * as mold_const from "@/utils/mold-const";

export default {
  name: "CoolingFemAndFillAndHoldingAndWarping",
  components: { coolingFem },
  props: {
    technologyData: {
      type: Object,
      default: () => ({}),
    },
    processData: {
      type: Object,
      default: () => ({})
    }
  },
  data() {
    return {
      technology: this.technologyData,
      process: this.processData,
      isShowOne: true,
      isShowTwo: false,
      isShowThree: false,
      moldFlowOptions: null,
      FillControlOptions: mold_const.moldFlowFillControlOptions,
      SpeedSwitchingOptions: mold_const.moldFlowSpeedSwitchingOptions,
      PressureHoldingControlOptions:
        mold_const.moldFlowPressureHoldingControlOptions,
      moldFlowRelativeOptions: mold_const.moldFlowRelativeOptions,
      moldFlowAbsoluteOptions: mold_const.moldFlowAbsoluteOptions,
      moldFlowOriginalOptions: mold_const.moldFlowOriginalOptions,
      isShowTime: false,
      isShowRate: false,
      isShowFillControl: false,
      isShowFillVolume: false,
      isShowScrewPosition: false,
      isShowInjectionPressure: false,
      isShowHydraulicPressure: false,
      isShowClampingForce: false,
      isShowInjectionTime: false,
      isShowControlPoint: false,
      isShowNominalInjectionTime: false,
      isShowNominalRate: false,
      isShowScrewDiameter: false,
      isShowAmg: false,
      isShowThread: false,
      isShowHolding: false,
      isShowReference: false,
      isShowLimit: false,
      injection_stage_header: [ "注射段数", "一段", "二段", "三段", "四段", "五段" ],
      holding_stage_header: [ "保压段数", "一段", "二段", "三段", "四段", "五段" ],
    };
  },
  methods: {
    next(isShowOne, isShowTwo, isShowThree) {
      if (isShowOne && !isShowTwo && !isShowThree) {
        this.isShowOne = false;
        this.isShowTwo = true;
        this.isShowThree = false;
      } else if (
        (!isShowOne && isShowTwo && !isShowThree) ||
        (!isShowOne && !isShowTwo && isShowThree)
      ) {
        this.isShowOne = false;
        this.isShowTwo = false;
        this.isShowThree = true;
      }
    },
    last(isShowOne, isShowTwo, isShowThree) {
      if (
        (isShowOne && !isShowTwo && !isShowThree) ||
        (!isShowOne && isShowTwo && !isShowThree)
      ) {
        this.isShowOne = true;
        this.isShowTwo = false;
        this.isShowThree = false;
      } else if (!isShowOne && !isShowTwo && isShowThree) {
        this.isShowOne = false;
        this.isShowTwo = true;
        this.isShowThree = false;
      }
    },
    changeFillControl(val) {
      if (val == "1" || !val) {
        this.isShowFillControl = false;
        this.isShowRate = false;
        this.isShowTime = false;
      } else if (val == "2") {
        this.isShowFillControl = false;
        this.isShowRate = false;
        this.isShowTime = true;
      } else if (val == "3") {
        this.isShowFillControl = false;
        this.isShowRate = true;
        this.isShowTime = false;
      } else if (val) {
        this.isShowFillControl = true;
        this.isShowRate = false;
        this.isShowTime = false;
        if (val == "5") {
          this.moldFlowOptions = this.moldFlowRelativeOptions;
          this.technology.control_options = null
          this.isShowLimit = false
          this.isShowReference = true
        } else if (val == "6") {
          this.moldFlowOptions = this.moldFlowAbsoluteOptions;
          this.technology.control_options = null
          this.isShowLimit = true
          this.isShowReference = false
        } else if (val == "4") {
          this.moldFlowOptions = this.moldFlowOriginalOptions;
          this.technology.control_options = null
          this.isShowLimit = false
          this.isShowReference = true
        }
      }
    }
  },
  watch: {
    technologyData: {
      handler() {
        this.technology = this.technologyData;
      },
      immediate: true,
      deep: true,
    },
    processData: {
      handler() {
        this.process = this.processData
      },
      immediate: true,
      deep: true,
    },
    "technology.speed_switching"(val) {
      if (val == "0") {
        this.isShowFillVolume = false;
        this.isShowScrewPosition = false;
        this.isShowInjectionPressure = false;
        this.isShowHydraulicPressure = false;
        this.isShowClampingForce = false;
        this.isShowInjectionTime = false;
        this.isShowControlPoint  = false;
      } else if (val == "1") {
        this.isShowFillVolume = true;
        this.isShowScrewPosition = false;
        this.isShowInjectionPressure = false;
        this.isShowHydraulicPressure = false;
        this.isShowClampingForce = false;
        this.isShowInjectionTime = false;
        this.isShowControlPoint  = false;
      } else if (val == "8") {
        this.isShowFillVolume = false;
        this.isShowScrewPosition = true;
        this.isShowInjectionPressure = false;
        this.isShowHydraulicPressure = false;
        this.isShowClampingForce = false;
        this.isShowInjectionTime = false;
        this.isShowControlPoint  = false;
      } else if (val == "2") {
        this.isShowFillVolume = false;
        this.isShowScrewPosition = false;
        this.isShowInjectionPressure = true;
        this.isShowHydraulicPressure = false;
        this.isShowClampingForce = false;
        this.isShowInjectionTime = false;
        this.isShowControlPoint  = false;
      } else if (val == "3") {
        this.isShowFillVolume = false;
        this.isShowScrewPosition = false;
        this.isShowInjectionPressure = false;
        this.isShowHydraulicPressure = true;
        this.isShowClampingForce = false;
        this.isShowInjectionTime = false;
        this.isShowControlPoint  = false;
      } else if (val == "4") {
        this.isShowFillVolume = false;
        this.isShowScrewPosition = false;
        this.isShowInjectionPressure = false;
        this.isShowHydraulicPressure = false;
        this.isShowClampingForce = true;
        this.isShowInjectionTime = false;
        this.isShowControlPoint  = false;
      } else if (val == "6") {
        this.isShowFillVolume = false;
        this.isShowScrewPosition = false;
        this.isShowInjectionPressure = false;
        this.isShowHydraulicPressure = false;
        this.isShowClampingForce = false;
        this.isShowInjectionTime = true;
        this.isShowControlPoint  = false;
      } else if (val == "5") {
        this.isShowFillVolume = false;
        this.isShowScrewPosition = false;
        this.isShowInjectionPressure = false;
        this.isShowHydraulicPressure = false;
        this.isShowClampingForce = false;
        this.isShowInjectionTime = false;
        this.isShowControlPoint  = true;
      } else {
        this.isShowFillVolume = false;
        this.isShowScrewPosition = false;
        this.isShowInjectionPressure = false;
        this.isShowHydraulicPressure = false;
        this.isShowClampingForce = false;
        this.isShowInjectionTime = false;
      }
    },
    "technology.parallel_thread"(val) {
      if (val == "1" || val == "2" || !val) {
        this.isShowAmg = false;
        this.isShowThread = false;
      } else if (val == "4") {
        this.isShowAmg = true;
        this.isShowThread = false;
      } else if (val == "3") {
        this.isShowAmg = false;
        this.isShowThread = true;
      }
    },
    "technology.pressure_holding_control"(val) {
      if (val == "5" || !val) {
        this.isShowHolding = false
      } else {
        this.isShowHolding = true
      }
    },
    "technology.reference"(val) {
      if (val == "1") {
        this.isShowNominalInjectionTime = true
        this.isShowNominalRate = false
      } else if (val == "2") {
        this.isShowNominalInjectionTime = false
        this.isShowNominalRate = true
      } else {
        this.isShowNominalInjectionTime = false
        this.isShowNominalRate = false
      }
    },
    "technology.injection_volume"(val) {
      if (val == "1") {
        this.isShowScrewDiameter = true
      } else {
        this.isShowScrewDiameter = false
      }
    }
  },
};
</script>

<style lang="scss" scoped>
.but {
  float: right;
  margin: 10px 20px 10px 0;
}
</style>