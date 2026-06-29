<template>
  <div>
    <div style="height: 15px"></div>
    <el-form>
      <el-form-item
        label="模流TXT"
      >

        <span>
          <el-upload
            style="display: inline-block"
            action=""
            :show-file-list="false"
            :http-request="uploadMoldFromTxt"
          >
            <el-button type="primary" size="mini" icon="el-icon-folder-opened">
              导入新的模流数据
            </el-button>
          </el-upload>
        </span>
      </el-form-item>
   
    </el-form>
    <mold-flow-list 
      @getTheMoldflow=getMoldflow 
      ref="moldflowList"
      @upload-file-info="onFileUploaded"
      :mold-flow-no="mold_flow_data.mold_flow_no"
    >
    </mold-flow-list>

    <div style="height:20px"></div>

    <el-tabs v-model="activeName">
      <el-tab-pane label="模流" name="first">
        <el-card shadow="hover">
          <el-form
            size="mini"
            label-position="right"
            label-width="9rem"
            :inline="true"
          >
            <el-form-item label="模流分析编号" prop="mold_flow_no">
              <el-input v-model="mold_flow_data.mold_flow_no" readonly></el-input>
            </el-form-item>
            <el-divider content-position="center"><span style="color: blue">机器</span></el-divider>
            <el-form-item label="注塑机型号" prop="trademark">
              <el-autocomplete
                v-model="mold_flow_data.machine.trademark"
                placeholder="注塑机型号"
                clearable
                style="width:10rem"
                :fetch-suggestions="queryMacTrademarkList"
                @select="handleTrademarkOptions"
              >
              </el-autocomplete>
            </el-form-item>
            <br>

            <el-divider content-position="center"><span style="color: blue">材料</span></el-divider>

            <el-form-item label="塑料牌号" prop="poly_trademark">
              <el-autocomplete
                v-model="mold_flow_data.polymer.poly_trademark"
                placeholder="材料牌号"
                clearable
                style="width:10rem"
                :fetch-suggestions="queryPolyTrademarkList"
                @select="handelePolyTrademarkListOption"
              >
              </el-autocomplete>
            </el-form-item>
            <br>

            <el-divider content-position="center"><span style="color: blue">工艺</span></el-divider>

            <el-form-item label="分析序列" prop="analytical_sequence">
              <el-select v-model="mold_flow_data.technology.analytical_sequence" style="width:13rem">
                <el-option
                  v-for="item, index in AnalyticalSequenceOptions"
                  :key="index"
                  :label="item.label"
                  :value="item.value"
                >
                </el-option>
              </el-select>
            </el-form-item>
            <br>
            <div v-show="isShowOne">
              <fill
                :technology-data="mold_flow_data.technology.fill"
                :process-data="mold_flow_data.technology.process_data"
              >
              </fill>
            </div>

            <div v-show="isShowTwo">
              <fill-and-holding
                :technology-data="mold_flow_data.technology.fill_holding"
                :process-data="mold_flow_data.technology.process_data"
              >
              </fill-and-holding>
            </div>

            <div v-show="isShowThree">
              <cooling
                :technology-data="mold_flow_data.technology.cooling"
              >
              </cooling>
            </div>

            <div v-show="isShowFour">
              <fill-and-holding-and-warping
                :technology-data="mold_flow_data.technology.fill_holding_warping"
                :process-data="mold_flow_data.technology.process_data"
              >
              </fill-and-holding-and-warping>
            </div>

            <div v-show="isShowFive">
              <cooling-and-fill-and-holding-and-warping
                :technology-data="mold_flow_data.technology.cooling_fill_holding_warping"
                :process-data="mold_flow_data.technology.process_data"
              >
              </cooling-and-fill-and-holding-and-warping>
            </div>

            <div v-show="isShowSix">
              <cooling-fem
                :technology-data="mold_flow_data.technology.cooling_fem"
              >
              </cooling-fem>
            </div>

            <div v-show="isShowSeven">
              <cooling-fem-and-fill-and-holding-and-warping
                :technology-data="mold_flow_data.technology.cooling_fem_fill_holding_warping"
                :process-data="mold_flow_data.technology.process_data"
              >
              </cooling-fem-and-fill-and-holding-and-warping>
            </div>

            <el-divider content-position="center"><span style="color: blue">分析数据</span></el-divider>
            <el-form-item label="注射时间" prop="filling_time">
              <el-input v-model="mold_flow_data.analyze_data.filling_time">
                <span slot="suffix">s</span>
              </el-input>
            </el-form-item>
            <el-form-item label="VP切换压力" prop="vp_switch">
              <el-input v-model="mold_flow_data.analyze_data.vp_switch">
                <span slot="suffix">MPa</span>
              </el-input>
            </el-form-item>
            <el-form-item label="最大锁模力" prop="clamping_force">
              <el-input v-model="mold_flow_data.analyze_data.clamping_force">
                <span slot="suffix">Ton</span>
              </el-input>
            </el-form-item>

            <el-form-item label="型腔重量" prop="cavity_weight">
              <el-input v-model="mold_flow_data.analyze_data.cavity_weight">
                <span slot="suffix">g</span>
              </el-input>
            </el-form-item>

            <el-divider content-position="center"><span style="color: blue">分析结果</span></el-divider>
            <div class="menu" v-show="mold_flow_data.ppt_link">
              <el-tree :data="mold_flow_data.result" :props="defaultProps" @node-click="handleNodeClick"></el-tree>
            </div>
            <div class="content" v-show="mold_flow_data.ppt_link">
              <div v-for="item,idx in mold_flow_data.result" :key="idx">
                <div v-for="img,index in item.children" :key="index">
                  <div v-if="status == img.name">
                    <el-form-item style="margin-left: 20px">{{img.name}}</el-form-item>
                    <el-form-item label="最大值">
                      <el-input size="mini" v-model="img.max_value">
                        <span slot="suffix">{{img.unit}}</span>
                      </el-input>
                    </el-form-item>
                    <el-form-item label="视频格式" prop="format">
                      <el-select v-model="format" style="width:13rem" @change="changeFormat">
                        <el-option label="gif" value="gif"></el-option>
                        <el-option label="mp4" value="mp4"></el-option>
                      </el-select>
                    </el-form-item>
                  </div>
                  <img :src="getImage(img.animation_url)" v-if="status == img.name&&format=='gif'">
                  <video :src="getImage(img.animation_url)" v-if="status == img.name&&format=='mp4'" class="avatar video-avatar" controls="controls"></video>
                </div>
              </div>
            </div>
          </el-form>
        </el-card>
      </el-tab-pane>
      <el-tab-pane label="日志" name="second" v-if=false>
        <el-card shadow="hover">
          <div slot="header" class="clearfix">日志</div>

          <el-form
            size="mini"
            label-width="8rem"
            label-position="right"
            :inline="true"
          >
            <el-divider content-position="center"><span style="color: blue">材料</span></el-divider>

            <el-form-item label="材料牌号" prop="polymer_trademark">
              <el-input v-model="process.monitor_item.polymer_trademark" >
              </el-input>
            </el-form-item>

            <br/>
            <el-divider content-position="center"><span style="color: blue">时间</span></el-divider>

            <el-form-item label="周期时间" prop="cycle_time">
              <el-input
                v-model="process.monitor_item.cycle_time"
                type="number"
                min="0"
                @input="
                  process.monitor_item.cycle_time = checkNumberFormat(
                    process.monitor_item.cycle_time
                  )
                "
              >
                <span slot="suffix">s</span>
              </el-input>
            </el-form-item>

            <el-form-item label="注射时间">
              <el-input
                type="text"
                v-model="process.monitor_item.injection_time"
                @input="
                  process.monitor_item.injection_time = checkNumberFormat(
                    process.monitor_item.injection_time
                  )
                "
              >
                <span slot="suffix">s</span>
              </el-input>
            </el-form-item>

            <el-form-item label="冷却时间">
              <el-input
                type="text"
                v-model="process.monitor_item.cooling_time"
                @input="
                  process.monitor_item.cooling_time = checkNumberFormat(
                    process.monitor_item.cooling_time
                  )
                "
              >
                <span slot="suffix">s</span>
              </el-input>
            </el-form-item>

            <el-form-item label="保压时间">
              <el-input
                type="text"
                v-model="process.monitor_item.holding_time"
                @input="
                  process.monitor_item.holding_time = checkNumberFormat(
                    process.monitor_item.holding_time
                  )
                "
              >
                <span slot="suffix">s</span>
              </el-input>
            </el-form-item>

            <br>
            <el-divider content-position="center"><span style="color: blue">制品</span></el-divider>

            <el-form-item label="总投射面积" prop="product_projected_area">
              <el-input
                v-model.trim="process.monitor_item.product_projected_area"
                type="number"
                @input="
                  process.monitor_item.product_projected_area = checkNumberFormat(
                    process.monitor_item.product_projected_area
                  )
                "
              >
                <span slot="suffix">cm<sup>2</sup></span>
              </el-input>
            </el-form-item>

            <el-form-item label="总体积" prop="single_volume">
              <el-input
                v-model.trim="process.monitor_item.single_volume"
                type="number"
                @input="
                  process.monitor_item.single_volume = checkNumberFormat(
                    process.monitor_item.single_volume
                  )
                "
              >
                <span slot="suffix">cm<sup>3</sup></span>
              </el-input>
            </el-form-item>

            <el-form-item label="壁厚" prop="thickness">
              <el-input
                v-model.trim="process.monitor_item.thickness"
                type="number"
                @input="
                  process.monitor_item.thickness = checkNumberFormat(
                    process.monitor_item.thickness
                  )
                "
              >
                <span slot="suffix">mm</span>
              </el-input>
            </el-form-item>

            <el-form-item label="克重" prop="product_weight">
              <el-input
                v-model.trim="process.monitor_item.product_weight"
                type="number"
                @input="
                  process.monitor_item.product_weight = checkNumberFormat(
                    process.monitor_item.product_weight
                  )
                "
              >
                <span slot="suffix">g</span>
              </el-input>
            </el-form-item>

            <br>
            <el-divider content-position="center"><span style="color: blue">温度</span></el-divider>

            <el-form-item label="料温">
              <el-input
                type="number"
                v-model="process.monitor_item.melt_temp"
                @input="
                  process.monitor_item.melt_temp = checkNumberFormat(
                    process.monitor_item.melt_temp
                  )
                "
              >
                <span slot="suffix">℃</span>
              </el-input>
            </el-form-item>

            <el-form-item label="前模模温">
              <el-input
                type="number"
                v-model="process.monitor_item.cavity_temp"
                @input="
                  process.monitor_item.cavity_temp = checkNumberFormat(
                    process.monitor_item.cavity_temp
                  )
                "
              >
                <span slot="suffix">℃</span>
              </el-input>
            </el-form-item>

            <el-form-item label="后模模温">
              <el-input
                type="number"
                v-model="process.monitor_item.core_temp"
                @input="
                  process.monitor_item.core_temp = checkNumberFormat(
                    process.monitor_item.core_temp
                  )
                "
              >
                <span slot="suffix">℃</span>
              </el-input>
            </el-form-item>

            <el-form-item label="浇口温度">
              <el-input
                type="number"
                v-model="process.monitor_item.gate_temperature"
                @input="
                  process.monitor_item.gate_temperature = checkNumberFormat(
                    process.monitor_item.gate_temperature
                  )
                "
              >
                <span slot="suffix">℃</span>
              </el-input>
            </el-form-item>

            <el-form-item label="斜顶温度">
              <el-input
                type="number"
                v-model="process.monitor_item.pentroof_temperature"
                @input="
                  process.monitor_item.pentroof_temperature = checkNumberFormat(
                    process.monitor_item.pentroof_temperature
                  )
                "
              >
                <span slot="suffix">℃</span>
              </el-input>
            </el-form-item>

            <el-form-item label="弹块滑块温度">
              <el-input
                type="number"
                v-model="process.monitor_item.slug_temperature"
                @input="
                  process.monitor_item.slug_temperature = checkNumberFormat(
                    process.monitor_item.slug_temperature
                  )
                "
              >
                <span slot="suffix">℃</span>
              </el-input>
            </el-form-item>

            <el-form-item label="内抽温度">
              <el-input
                type="number"
                v-model="process.monitor_item.lifters_temperature"
                @input="
                  process.monitor_item.lifters_temperature = checkNumberFormat(
                    process.monitor_item.lifters_temperature
                  )
                "
              >
                <span slot="suffix">℃</span>
              </el-input>
            </el-form-item>

            <br>
            <el-divider content-position="center"><span style="color: blue">压力损耗</span></el-divider>

            <el-form-item label="最大注射压力">
              <el-input
                type="number"
                v-model="process.monitor_item.injection_pressure"
                @input="
                  process.monitor_item.injection_pressure = checkNumberFormat(
                    process.monitor_item.injection_pressure
                  )
                "
              >
                <span slot="suffix">MPa</span>
              </el-input>
            </el-form-item>

            <el-form-item label="最大锁模力">
              <el-input
                type="number"
                v-model="process.monitor_item.max_clamping_force"
                @input="
                  process.monitor_item.max_clamping_force = checkNumberFormat(
                    process.monitor_item.max_clamping_force
                  )
                "
              >
                <span slot="suffix">tonne</span>
              </el-input>
            </el-form-item>
            <br />

            <el-form-item label="注塑机">
              <el-input
                type="number"
                v-model="process.monitor_item.injection"
                @input="
                  process.monitor_item.injection = checkNumberFormat(
                    process.monitor_item.injection
                  )
                "
              >
                <span slot="suffix">MPa</span>
              </el-input>
            </el-form-item>

            <el-form-item label="热流道">
              <el-input
                type="number"
                v-model="process.monitor_item.hot_runner_pressure"
                @input="
                  process.monitor_item.hot_runner_pressure = checkNumberFormat(
                    process.monitor_item.hot_runner_pressure
                  )
                "
              >
                <span slot="suffix">MPa</span>
              </el-input>
            </el-form-item>

            <el-form-item label="浇口">
              <el-input
                type="number"
                v-model="process.monitor_item.gate_pressure"
                @input="
                  process.monitor_item.gate_pressure = checkNumberFormat(
                    process.monitor_item.gate_pressure
                  )
                "
              >
                <span slot="suffix">MPa</span>
              </el-input>
            </el-form-item>
          </el-form>

          <div style="height:30px"></div>
          <el-row>
            <el-col :xs="24" :lg="11" :xl="11">
              <el-table
                size="mini"
                :data="process.monitor_item.inject_para" 
                :key="Math.random()"
              >
                <el-table-column width="80" align="center">
                  <template slot="header">注射段数</template>
                  <template slot-scope="scope">
                    {{ scope.row.label }}
                  </template>
                </el-table-column>
                <template v-for="(col, colidx) in 5">
                  <el-table-column
                    min-width="80"
                    align="center"
                    :key="colidx"
                    :label="injection_stage_header[col]"
                  >
                    <template slot-scope="scope">
                      <el-input
                        style="width:6rem"
                        v-model="process.monitor_item.inject_para[scope.$index].sections[colidx]" 
                        type="number" 
                        min="0" 
                        size="mini"
                        @input="process.monitor_item.inject_para[scope.$index].sections[colidx]=checkNumberFormat(process.monitor_item.inject_para[scope.$index].sections[colidx])"
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
                    {{ process.monitor_item.inject_para[scope.$index].unit }}
                  </template>
                </el-table-column>
              </el-table>
            </el-col>
            <el-col :xs="24" :lg="11" :xl="11">
              <el-table
                size="mini"
                :data="process.monitor_item.holding_para" 
                :key="Math.random()"
              >
                <el-table-column width="80" align="center">
                  <template slot="header">保压段数</template>
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
                        style="width:6rem"
                        v-model="process.monitor_item.holding_para[scope.$index].sections[colidx]" 
                        type="number" 
                        min="0" 
                        size="mini"
                        @input="process.monitor_item.holding_para[scope.$index].sections[colidx]=checkNumberFormat(process.monitor_item.holding_para[scope.$index].sections[colidx])"
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
                    {{ process.monitor_item.holding_para[scope.$index].unit }}
                  </template>
                </el-table-column>
              </el-table>
            </el-col>
          </el-row>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <div class="nextButton">
      <el-button type="danger" size="small" @click="resetView">
        重 置
      </el-button>
      <el-button
        v-if="process.id"
        type="primary"
        size="small"
        :loading="update_loading"
        @click="updateMoldData"
      >
        更 新
      </el-button>
      <el-button
        v-else
        type="primary"
        size="small"
        :loading="save_loading"
        @click="saveMoldData"
      >
        保 存
      </el-button>
    </div>
  </div>
</template>

<script>
import * as mold_const from '@/utils/mold-const';
import { importMoldflow,getMoldflowMethod, moldflowMethod, downloadFile, getOptions, machineMethod, polymerMethod } from "@/api";
import { ProjectsInfoModule } from "@/store/modules/projects";
import { getFullReportUrl, getFullImageUrl } from '@/utils/assert';
import { initArray } from "@/utils/array-help";
import UploadSingleFile from '@/components/uploadSingleFile'
import FillAndHolding from './subView/fillAndHolding.vue';
import Fill from './subView/fill.vue';
import Cooling from './subView/cooling.vue';
import FillAndHoldingAndWarping from './subView/fillAndHoldingAndWarping.vue';
import CoolingAndFillAndHoldingAndWarping from './subView/coolingAndFillAndHoldingAndWarping.vue';
import CoolingFem from './subView/coolingFem.vue';
import CoolingFemAndFillAndHoldingAndWarping from './subView/coolingFemAndFillAndHoldingAndWarping.vue';
import MoldFlowList from './subView/moldFlowList.vue';
import { datetimeTodayStr } from "@/utils/datetime";

export default {
  name: "MoldData",
  components: {
    UploadSingleFile,
    FillAndHolding,
    Fill,
    Cooling,
    FillAndHoldingAndWarping,
    CoolingAndFillAndHoldingAndWarping,
    CoolingFem,
    CoolingFemAndFillAndHoldingAndWarping,
    MoldFlowList
  },
  data() {
    return {
      activeName: "first",
      format: "gif",
      process: {
        project_id: null,
        mold_no: null,
        doc_link: null,
        ppt_link: null,
        pdf_link: null,
        monitor_item: {
          cycle_time: null,
          injection_time: null,
          cooling_time:null,
          holding_time:null,

          product_projected_area: null,
          single_volume: null,

          melt_temp:null,
          cavity_temp:null,
          core_temp:null,

          injection_pressure:null,
          max_clamping_force:null,

          polymer_trademark: null,
          thickness: null,
          product_weight: null,
          gate_temperature: null,
          pentroof_temperature: null,
          slug_temperature: null,
          lifters_temperature: null,

          inject_para: [
            { label: "压力", unit: "MPa", sections: initArray(5, null) },
            { label: "速度", unit: "cm³/s", sections: initArray(5, null) },
          ],
          holding_para:[
            { label: "压力", unit: "MPa", sections: initArray(5, null) },
            { label: "时间", unit: "s", sections: initArray(5, null) },
          ],

          injection: null,
          hot_runner_pressure: null,
          gate_pressure: null,
        },
      },
      injection_stage_header: [ "注射段数", "一段", "二段", "三段", "四段", "五段" ],
      holding_stage_header: [ "保压段数", "一段", "二段", "三段", "四段", "五段" ],
      update_loading: false,
      save_loading: false,
      moldflow_ppt_info: {
        id: ProjectsInfoModule.selectedProject.mold_info.id,
        name: null,
        url: null,
        mold_flow_no:null
      },
      mold_flow_data: {
        project_id: null,
        mold_flow_no: null,
        deleted: null,
        mold_no: null,
        doc_link: null,
        ppt_link: null,
        machine: {
          id: null,
          trademark: null,
          data_source: null,
          manufacturer: null,
          machine_type: null,
        },
        polymer: {
          id : null,
          poly_trademark: null,
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
          degradation_temperature: null,
          ejection_temperature: null,
          max_sheer_rate: null,
          max_sheer_stress: null,
          recommend_back_pressure: null,
          barrel_residence_time: null,
        },
        technology: {
          analytical_sequence: null,
          fill_holding: {
            surface_temperature: null,
            melt_temperature: null,
            fill_control: null,
            inject_time: null,
            flow_rate: null,
            control_options: null,
            reference: null,
            nominal_injection_time: null,
            nominal_rate: null,
            injection_volume: null,
            screw_diameter: null,
            start_screw_diameter: null,
            packing_warning_limit: null,
            starting_screw_position: null,
            speed_switching: null,
            fill_volume: null,
            screw_position: null,
            injection_pressure: null,
            hydraulic_pressure: null,
            clamping_force: null,
            injection_time: null,
            node: null,
            pressure: null,
            pressure_holding_control: null,
            cooling_time: null,
            cool_time: null,
          },
          fill: {
            surface_temperature: null,
            melt_temperature: null,
            fill_control: null,
            inject_time: null,
            flow_rate: null,
            control_options: null,
            reference: null,
            nominal_injection_time: null,
            nominal_rate: null,
            injection_volume: null,
            screw_diameter: null,
            start_screw_diameter: null,
            packing_warning_limit: null,
            starting_screw_position: null,
            speed_switching: null,
            fill_volume: null,
            screw_position: null,
            injection_pressure: null,
            hydraulic_pressure: null,
            clamping_force: null,
            injection_time: null,
            node: null,
            pressure: null,
            pressure_holding_control: null,
          },
          cooling: {
            melt_temperature: null,
            mold_open_time: null,
            injection_holding_cooling_time: null,
            injection_holding_cool_time: null,
          },
          fill_holding_warping: {
            surface_temperature: null,
            melt_temperature: null,
            fill_control: null,
            inject_time: null,
            flow_rate: null,
            control_options: null,
            reference: null,
            nominal_injection_time: null,
            nominal_rate: null,
            injection_volume: null,
            screw_diameter: null,
            start_screw_diameter: null,
            packing_warning_limit: null,
            starting_screw_position: null,
            speed_switching: null,
            fill_volume: null,
            screw_position: null,
            injection_pressure: null,
            hydraulic_pressure: null,
            clamping_force: null,
            injection_time: null,
            node: null,
            pressure: null,
            pressure_holding_control: null,
            cooling_time: null,
            cool_time: null,

            warping_analysis_type: null,
            parallel_thread: null,
            amg_select: null,
            thread_count: null,
          },
          cooling_fill_holding_warping: {
            melt_temperature: null,
            mold_open_time: null,
            injection_holding_cooling_time: null,
            injection_holding_cool_time: null,

            fill_control: null,
            inject_time: null,
            flow_rate: null,
            control_options: null,
            reference: null,
            nominal_injection_time: null,
            nominal_rate: null,
            injection_volume: null,
            screw_diameter: null,
            start_screw_diameter: null,
            packing_warning_limit: null,
            starting_screw_position: null,
            speed_switching: null,
            fill_volume: null,
            screw_position: null,
            injection_pressure: null,
            hydraulic_pressure: null,
            clamping_force: null,
            injection_time: null,
            node: null,
            pressure: null,
            pressure_holding_control: null,

            warping_analysis_type: null,
            parallel_thread: null,
            amg_select: null,
            thread_count: null,
          },
          cooling_fem: {
            melt_temperature: null,
            mold_open_time: null,
            mold_close_time: null,
            injection_holding_cooling_time: null,
            injection_holding_cool_time: null,
            mold_temperature: null,
          },
          cooling_fem_fill_holding_warping: {
            melt_temperature: null,
            mold_open_time: null,
            mold_close_time: null,
            injection_holding_cooling_time: null,
            injection_holding_cool_time: null,
            mold_temperature: null,

            fill_control: null,
            inject_time: null,
            flow_rate: null,
            control_options: null,
            reference: null,
            nominal_injection_time: null,
            nominal_rate: null,
            injection_volume: null,
            screw_diameter: null,
            start_screw_diameter: null,
            packing_warning_limit: null,
            starting_screw_position: null,
            speed_switching: null,
            fill_volume: null,
            screw_position: null,
            injection_pressure: null,
            hydraulic_pressure: null,
            clamping_force: null,
            injection_time: null,
            node: null,
            pressure: null,
            pressure_holding_control: null,

            warping_analysis_type: null,
            parallel_thread: null,
            amg_select: null,
            thread_count: null,
          },
          process_data: {
            inject_stage: 4,
            holding_stage: 4,
            max_inject_stage_option: 5,
            max_holding_stage_option: 5,
            inject_para: [
              { label: "压力", unit: "MPa", sections: initArray(5, null) },
              { label: "速度", unit: "cm³/s", sections: initArray(5, null) },
              { label: "位置", unit: "mm", sections: initArray(5, null) },
            ],
            holding_para:[
              { label: "压力", unit: "MPa", sections: initArray(5, null) },
              { label: "时间", unit: "s", sections: initArray(5, null) },
            ],
          },
        },
        result: [
          {
            name: null,
            children: [
              {
                name: null,
                id: null,
                desc: null,
                animation_url: null,
                max_value: null,
                unit: null,
              }
            ]
          }
        ],
        analyze_data: {
          filling_time: null,
          vp_switch: null,
          clamping_force: null,
          injection_pressure: null,
          pressure: null,
          cavity_weight: null,
          filling_end_pressure: null,
        }
      },
      defaultProps: {
        children: 'children',
        label: 'name'
      },
      AnalyticalSequenceOptions: mold_const.moldFlowAnalyticalSequenceOptions,
      isShowOne: false,
      isShowTwo: false,
      isShowThree: false,
      isShowFour: false,
      isShowFive: false,
      isShowSix: false,
      isShowSeven: false,
      status: null,
    };
  },
  mounted() {
    // this.getMoldflow()
  },
  methods: {
    handleNodeClick(data) {
      this.status = data.name
    },
    queryMacTrademarkList(str, cb) {
      str = (str == null ? "" : str)
      let promptList = []
      getOptions("machine_trademark")
      .then(res => {
        if (res.status === 0) {
          for (let i = 0; i < res.data.length; i++) {
            promptList.push({ 
              id: res.data[i].id,
              value: res.data[i].trademark 
            })
          }
        }
      })
      cb(promptList)
    },
    queryPolyTrademarkList(str, cb) {
      str = (str == null ? "" : str)
      let promptList = []
      getOptions("polymer_trademark")
      .then(res => {
        if (res.status === 0) {
          for (let i = 0; i < res.data.length; i++) {
            promptList.push({
              id: res.data[i].id,
              value: res.data[i].trademark
            })
          }
        }
      })
      cb(promptList)
    },
    handleTrademarkOptions(item) {
      if (item.id) {
        machineMethod.getDetail(item.id)
        .then(res => {
          if (res.status === 0) {
            let machine_info = res.data
            this.mold_flow_data.machine.id = machine_info.id
            this.mold_flow_data.machine.data_source = machine_info.data_source
            this.mold_flow_data.machine.manufacturer = machine_info.manufacturer
            this.mold_flow_data.machine.machine_type = machine_info.machine_type
          }
        })
      }
    },
    handelePolyTrademarkListOption(item) {
      if (item.id) {
        polymerMethod.getDetail(item.id)
        .then( res => {
          if (res.status === 0) {
            let poly_info = res.data
            this.mold_flow_data.polymer.id = poly_info.id
            this.mold_flow_data.polymer.max_melt_temperature = poly_info.max_melt_temperature
            this.mold_flow_data.polymer.min_melt_temperature = poly_info.min_melt_temperature
            this.mold_flow_data.polymer.recommend_melt_temperature = poly_info.recommend_melt_temperature
            this.mold_flow_data.polymer.max_mold_temperature = poly_info.max_mold_temperature
            this.mold_flow_data.polymer.min_mold_temperature = poly_info.min_mold_temperature
            this.mold_flow_data.polymer.recommend_mold_temperature = poly_info.recommend_mold_temperature
            this.mold_flow_data.polymer.max_shear_linear_speed = poly_info.max_shear_linear_speed
            this.mold_flow_data.polymer.min_shear_linear_speed = poly_info.min_shear_linear_speed
            this.mold_flow_data.polymer.recommend_shear_linear_speed = poly_info.recommend_shear_linear_speed
            this.mold_flow_data.polymer.recommend_injection_rate = poly_info.recommend_injection_rate
            this.mold_flow_data.polymer.degradation_temperature = poly_info.degradation_temperature
            this.mold_flow_data.polymer.ejection_temperature = poly_info.ejection_temperature
            this.mold_flow_data.polymer.max_sheer_rate = poly_info.max_sheer_rate
            this.mold_flow_data.polymer.max_sheer_stress = poly_info.max_sheer_stress
            this.mold_flow_data.polymer.recommend_back_pressure = poly_info.recommend_back_pressure
            this.mold_flow_data.polymer.barrel_residence_time = poly_info.barrel_residence_time
          }
        })
      }
    },
    getMoldflow(row){
      // 用当前行的mold_flow_no参与查询
      if (!row.mold_flow_no) {
        location.reload()
      } else {
        getMoldflowMethod({"project_id":ProjectsInfoModule.selectedProject.mold_info.id, "mold_flow_no":row.mold_flow_no})
          .then((res)=>{
            if(res.status === 0 && JSON.stringify(res.data)!=="{}"){
              this.mold_flow_data = res.data

            }
          })
      }
    },
    uploadMoldFromTxt(data) {
      let params = new FormData();
      params.append("file", data.file);
      let mold_no = ProjectsInfoModule.selectedProject.mold_info.mold_no;
      let project_id = ProjectsInfoModule.selectedProject.mold_info.id;
      importMoldflow(params, mold_no, project_id)
        .then((res) => {
          if (res.status === 0) {
            if (res.data) {
              this.mold_flow_data = res.data.mold_flow_data
            }
            this.$message({ message: "上传成功", type: "success" });
            this.$refs.moldflowList.getListData()
          } else {
            this.$message({ message: "上传失败", type: "error" });
          }
        })
        .finally(() => (this.uploadingID = null));
      return 0;
    },
    setProcess(temp_moldflow) {
      if(temp_moldflow){
        this.process.monitor_item.polymer_trademark = temp_moldflow.polymer_trademark
        this.process.monitor_item.cycle_time = temp_moldflow.cycle_time;
        this.process.monitor_item.melt_temp = temp_moldflow.melt_temp;
        this.process.monitor_item.cavity_temp = temp_moldflow.cavity_temp;
        this.process.monitor_item.core_temp = temp_moldflow.core_temp;

        this.process.monitor_item.injection_time = temp_moldflow.injection_time;
        this.process.monitor_item.injection_pressure = temp_moldflow.injection_pressure;
        this.process.monitor_item.holding_time = temp_moldflow.holding_time[0];
        this.process.monitor_item.mold_open_clamp_time =
          temp_moldflow.mold_open_clamp_time;
        this.process.monitor_item.cooling_time = temp_moldflow.cooling_time;
        this.process.monitor_item.max_clamping_force =
          temp_moldflow.max_clamping_force;
        this.process.monitor_item.product_projected_area =
          temp_moldflow.product_projected_area;
        this.process.monitor_item.single_volume = temp_moldflow.single_volume;

        this.process.monitor_item.inject_para = temp_moldflow.inject_para
        this.process.monitor_item.holding_para = temp_moldflow.holding_para
      }
    },
    saveMoldData() {
      this.mold_flow_data.mold_no = ProjectsInfoModule.selectedProject.mold_info.mold_no;
      this.mold_flow_data.project_id = ProjectsInfoModule.selectedProject.mold_info.id;
      moldflowMethod.add(this.mold_flow_data)
      .then(res => {
        if (res.status === 0) {
          this.$message({ message: '新增成功！', type: 'success'})
        }
      })
    },
    updateMoldData() {},
    resetView() {
      this.process = {
        id: null,
        mold_no: null,
        doc_link: null,
        ppt_link: null,
        pdf_link: null,
        monitor_item: {
          cycle_time: null,
          injection_time: null,
          cooling_time:null,
          holding_time:null,

          product_projected_area: null,
          single_volume: null,

          melt_temp:null,
          cavity_temp:null,
          core_temp:null,

          injection_pressure:null,
          max_clamping_force:null,

          polymer_trademark: null,
          thickness: null,
          product_weight: null,
          gate_temperature: null,
          pentroof_temperature: null,
          slug_temperature: null,
          lifters_temperature: null,

          inject_para: [
            { label: "压力", unit: "MPa", sections: initArray(5, null) },
            { label: "速度", unit: "cm³/s", sections: initArray(5, null) },
          ],
          holding_para:[
            { label: "压力", unit: "MPa", sections: initArray(5, null) },
            { label: "时间", unit: "s", sections: initArray(5, null) },
          ],

          injection: null,
          hot_runner_pressure: null,
          gate_pressure: null,
        },
      };
      this.mold_flow_data = {
        machine: {
          id: null,
          trademark: null,
          data_source: null,
          manufacturer: null,
          machine_type: null,
        },
        polymer: {
          id : null,
          poly_trademark: null,
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
          degradation_temperature: null,
          ejection_temperature: null,
          max_sheer_rate: null,
          max_sheer_stress: null,
          recommend_back_pressure: null,
          barrel_residence_time: null,
        },
        technology: {
          analytical_sequence: null,
          fill_holding: {
            surface_temperature: null,
            melt_temperature: null,
            fill_control: null,
            inject_time: null,
            flow_rate: null,
            control_options: null,
            reference: null,
            nominal_injection_time: null,
            nominal_rate: null,
            injection_volume: null,
            screw_diameter: null,
            start_screw_diameter: null,
            packing_warning_limit: null,
            starting_screw_position: null,
            speed_switching: null,
            fill_volume: null,
            screw_position: null,
            injection_pressure: null,
            hydraulic_pressure: null,
            clamping_force: null,
            injection_time: null,
            node: null,
            pressure: null,
            pressure_holding_control: null,
            cooling_time: null,
            cool_time: null,
          },
          fill: {
            surface_temperature: null,
            melt_temperature: null,
            fill_control: null,
            inject_time: null,
            flow_rate: null,
            control_options: null,
            reference: null,
            nominal_injection_time: null,
            nominal_rate: null,
            injection_volume: null,
            screw_diameter: null,
            start_screw_diameter: null,
            packing_warning_limit: null,
            starting_screw_position: null,
            speed_switching: null,
            fill_volume: null,
            screw_position: null,
            injection_pressure: null,
            hydraulic_pressure: null,
            clamping_force: null,
            injection_time: null,
            node: null,
            pressure: null,
            pressure_holding_control: null,
          },
          cooling: {
            melt_temperature: null,
            mold_open_time: null,
            injection_holding_cooling_time: null,
            injection_holding_cool_time: null,
          },
          fill_holding_warping: {
            surface_temperature: null,
            melt_temperature: null,
            fill_control: null,
            inject_time: null,
            flow_rate: null,
            control_options: null,
            reference: null,
            nominal_injection_time: null,
            nominal_rate: null,
            injection_volume: null,
            screw_diameter: null,
            start_screw_diameter: null,
            packing_warning_limit: null,
            starting_screw_position: null,
            speed_switching: null,
            fill_volume: null,
            screw_position: null,
            injection_pressure: null,
            hydraulic_pressure: null,
            clamping_force: null,
            injection_time: null,
            node: null,
            pressure: null,
            pressure_holding_control: null,
            cooling_time: null,
            cool_time: null,

            warping_analysis_type: null,
            parallel_thread: null,
            amg_select: null,
            thread_count: null,
          },
          cooling_fill_holding_warping: {
            melt_temperature: null,
            mold_open_time: null,
            injection_holding_cooling_time: null,
            injection_holding_cool_time: null,

            fill_control: null,
            inject_time: null,
            flow_rate: null,
            control_options: null,
            reference: null,
            nominal_injection_time: null,
            nominal_rate: null,
            injection_volume: null,
            screw_diameter: null,
            start_screw_diameter: null,
            packing_warning_limit: null,
            starting_screw_position: null,
            speed_switching: null,
            fill_volume: null,
            screw_position: null,
            injection_pressure: null,
            hydraulic_pressure: null,
            clamping_force: null,
            injection_time: null,
            node: null,
            pressure: null,
            pressure_holding_control: null,

            warping_analysis_type: null,
            parallel_thread: null,
            amg_select: null,
            thread_count: null,
          },
          cooling_fem: {
            melt_temperature: null,
            mold_open_time: null,
            mold_close_time: null,
            injection_holding_cooling_time: null,
            injection_holding_cool_time: null,
            mold_temperature: null,
          },
          cooling_fem_fill_holding_warping: {
            melt_temperature: null,
            mold_open_time: null,
            mold_close_time: null,
            injection_holding_cooling_time: null,
            injection_holding_cool_time: null,
            mold_temperature: null,

            fill_control: null,
            inject_time: null,
            flow_rate: null,
            control_options: null,
            reference: null,
            nominal_injection_time: null,
            nominal_rate: null,
            injection_volume: null,
            screw_diameter: null,
            start_screw_diameter: null,
            packing_warning_limit: null,
            starting_screw_position: null,
            speed_switching: null,
            fill_volume: null,
            screw_position: null,
            injection_pressure: null,
            hydraulic_pressure: null,
            clamping_force: null,
            injection_time: null,
            node: null,
            pressure: null,
            pressure_holding_control: null,

            warping_analysis_type: null,
            parallel_thread: null,
            amg_select: null,
            thread_count: null,
          },
          process_data: {
            inject_stage: 4,
            holding_stage: 4,
            max_inject_stage_option: 5,
            max_holding_stage_option: 5,
            inject_para: [
              { label: "压力", unit: "MPa", sections: initArray(5, null) },
              { label: "速度", unit: "cm³/s", sections: initArray(5, null) },
              { label: "位置", unit: "mm", sections: initArray(5, null) },
            ],
            holding_para:[
              { label: "压力", unit: "MPa", sections: initArray(5, null) },
              { label: "时间", unit: "s", sections: initArray(5, null) },
            ],
          },
        },
        result: [
          {
            name: null,
            children: [
              {
                name: null,
                id: null,
                desc: null,
                animation_url: null,
                max_value: null,
              }
            ]
          }
        ],
        analyze_data: {
          filling_time: null,
          vp_switch: null,
          clamping_force: null,
          injection_pressure: null,
          pressure: null,
          cavity_weight: null,
          filling_end_pressure: null,
        }
      }
    },
    onFileUploaded(fileInfo) {
      if (fileInfo) {
        this.mold_flow_data = fileInfo
      } else {
        this.mold_flow_data.result = null
        this.mold_flow_data.ppt_link = null
      }
      this.$refs.moldflowList.getListData()
    },
    changeImg(index) {
      this.status = index
    },
    getImage(img) {
      return getFullImageUrl(img)
    },
    changeFormat(item){
      for(let i=0;i<this.mold_flow_data.result.length;i++){
        for(let j=0;j<this.mold_flow_data.result[i].children.length;j++){
          let point_position = this.mold_flow_data.result[i].children[j].animation_url.indexOf(".")
          this.mold_flow_data.result[i].children[j].animation_url = this.mold_flow_data.result[i].children[j].animation_url.slice(0,point_position)+"."+item
        }
      }
    }
  },
  watch: {
    "mold_flow_data.technology.analytical_sequence": {
      handler(val) {
        if (val == "填充") {
          this.isShowOne = true
          this.isShowTwo = false
          this.isShowThree = false
          this.isShowFour = false
          this.isShowFive = false
          this.isShowSix = false
          this.isShowSeven = false
        } else if (val == "填充+保压") {
          this.isShowOne = false
          this.isShowTwo = true
          this.isShowThree = false
          this.isShowFour = false
          this.isShowFive = false
          this.isShowSix = false
          this.isShowSeven = false
        } else if (val == "冷却") {
          this.isShowOne = false
          this.isShowTwo = false
          this.isShowThree = true
          this.isShowFour = false
          this.isShowFive = false
          this.isShowSix = false
          this.isShowSeven = false
        } else if (val == "填充+保压+翘曲") {
          this.isShowOne = false
          this.isShowTwo = false
          this.isShowThree = false
          this.isShowFour = true
          this.isShowFive = false
          this.isShowSix = false
          this.isShowSeven = false
        } else if (val == "冷却+填充+保压+翘曲") {
          this.isShowOne = false
          this.isShowTwo = false
          this.isShowThree = false
          this.isShowFour = false
          this.isShowFive = true
          this.isShowSix = false
          this.isShowSeven = false
        } else if (val == "冷却(FEM)") {
          this.isShowOne = false
          this.isShowTwo = false
          this.isShowThree = false
          this.isShowFour = false
          this.isShowFive = false
          this.isShowSix = true
          this.isShowSeven = false
        } else if (val == "冷却(FEM)+填充+保压+翘曲") {
          this.isShowOne = false
          this.isShowTwo = false
          this.isShowThree = false
          this.isShowFour = false
          this.isShowFive = false
          this.isShowSix = false
          this.isShowSeven = true
        } else {
          this.isShowOne = false
          this.isShowTwo = false
          this.isShowThree = false
          this.isShowFour = false
          this.isShowFive = false
          this.isShowSix = false
          this.isShowSeven = false
        }
      },
      immediate: true,
      deep: true,
    }
  },
};
</script>

<style lang="scss" scoped>
.el-autocomplete {
  width: 10rem;
}
.el-input {
  width: 10rem;
}
.el-select {
  width: 10rem;
}
.menu {
  width: 20%;
  height: 750px;
  float: left;
  overflow-y: scroll;
}
.menu li {
  list-style: none;
  margin-top: 10px;
}
.content {
  width: 80%;
  height: 750px;
  float: right;
}
.content img {
  width: 100%;
  height: 705px;
}
.content video {
  width: 80%;
  height: 705px;
}
</style>