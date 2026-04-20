<template>
  <div>
    <el-form 
      ref="formData" 
      size="mini" 
      label-width="10rem" 
      label-position="right"
      :model="machine_info" 
      :rules="rules"
      :inline="true"
    >
      <el-card>
        <div slot="header" class="clearfix">
          机器描述
        </div>
        <el-form-item 
          label="注塑机来源" 
          prop="data_source"
        >
          <el-select 
            v-model.trim="machine_info.data_source"
            clearable
            filterable 
            allow-create
            default-first-option
          >
            <el-option
              v-for="item in machine_datasource_options"
              :key="item.value" 
              :label="item.label" 
              :value="item.value"
            >
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item 
          label="注塑机品牌" 
          prop="manufacturer"
        >
          <el-select 
            v-model="machine_info.manufacturer" 
            placeholder="请选择"
            clearable
            filterable
            allow-create
            default-first-option
          >
            <el-option
              v-for="item in machine_manu_options"
              :key="item.value"
              :label="item.label"
              :value="item.label"
            >
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item 
          label="注塑机型号" 
          prop="trademark" 
        >
          <el-input v-model="machine_info.trademark"></el-input>
        </el-form-item>
        <el-tooltip class="item" effect="dark" content="与注塑机建立通讯的关键字" placement="top-start">
          <el-form-item 
            label="设备编码" 
            prop="serial_no"
          >
            <el-input v-model="machine_info.serial_no"></el-input>
          </el-form-item>
        </el-tooltip>
        <el-form-item 
          label="资产编号" 
          prop="asset_no"
        >
          <el-input v-model="machine_info.asset_no">
          </el-input>
        </el-form-item>
        <el-form-item  
          label="注塑机ID"
          prop="internal_id"
        >
          <el-input 
            v-model="machine_info.internal_id"
            @input="machine_info.internal_id=checkNumberFormat(machine_info.internal_id, 0)"
          ></el-input>
        </el-form-item>
        <el-form-item 
          label="通讯接口" 
          prop="communication_interface"
        >
          <el-select v-model="machine_info.communication_interface">
            <el-option label="开通" :value="1"></el-option>
            <el-option label="未开通" :value="0"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item 
          label="协议" 
          prop="agreement"
        >
          <el-select allow-create filterable v-model="machine_info.agreement">
            <el-option label="keba1175" value="keba1175"></el-option>
            <el-option label="keba映翰通" value="keba映翰通"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item 
          label="注塑机类型(射台数)" 
          prop="mac_inject_type"
        >
          <el-select 
            v-model="machine_info.machine_type" 
            @change="onMachineTypeChanged"
          >
            <el-option
              v-for="item in machine_type_options"
              :key="item.value"
              :label="item.label"
              :value="item.label"
            />
          </el-select>
        </el-form-item>
        <el-form-item 
          label="注塑机类型(驱动方式)" 
          prop="power_method"
        >
          <el-select v-model="machine_info.power_method">
            <el-option label="电动机" value="电动机"></el-option>
            <el-option label="液压机" value="液压机"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item 
          label="注塑机类型(推进轴线)" 
          prop="propulsion_axis"
        >
          <el-select v-model="machine_info.propulsion_axis">
            <el-option label="卧式" value="卧式"></el-option>
            <el-option label="立式" value="立式"></el-option>
            <el-option label="角式" value="角式"></el-option>
          </el-select>
        </el-form-item>
        <el-divider content-position="center">
          <span style="color: blue">操作界面单位</span>
        </el-divider>
        <el-tooltip class="item" effect="dark" content="注射,保压,熔胶,松退" placement="top-start">
          <el-form-item 
            label="压力单位" 
            prop="pressure_unit"
          >
            <el-select v-model="machine_info.pressure_unit">
              <el-option
                v-for="item in pres_unit_options"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              >
              </el-option>
            </el-select>
          </el-form-item>
        </el-tooltip>
        <el-form-item 
          label="背压单位" 
          prop="backpressure_unit"
        >
          <el-select v-model="machine_info.backpressure_unit">
            <el-option
              v-for="item in pres_unit_options"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            >
            </el-option>
          </el-select>
        </el-form-item>
        <el-tooltip class="item" effect="dark" content="注射,保压,熔胶,松退" placement="top-start">
          <el-form-item 
            label="速度单位" 
            prop="velocity_unit"
          >
            <el-select v-model="machine_info.velocity_unit" @change="velocityUnitChange">
              <el-option
                v-for="item in velo_unit_options"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              >
              </el-option>
            </el-select>
          </el-form-item>
        </el-tooltip>
        <el-form-item 
          label="温度单位" 
          prop="temperature_unit"
        >
          <el-select v-model="machine_info.temperature_unit">
            <el-option
              v-for="item in temp_unit_options"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            >
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item 
          label="时间单位" 
          prop="time_unit"
        >
          <el-select v-model="machine_info.time_unit">
            <el-option
              v-for="item in time_unit_options"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            >
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item 
          label="位置单位" 
          prop="position_unit"
        >
          <el-select v-model="machine_info.position_unit">
            <el-option
              v-for="item in posi_unit_options"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            >
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item 
          label="锁模力单位" 
          prop="clamping_force_unit"
        >
          <el-select v-model="machine_info.clamping_force_unit">
            <el-option
              v-for="item in clfc_unit_options"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            >
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item 
          label="螺杆转速单位" 
          prop="screw_rotation_unit"
        >
          <el-select v-model="machine_info.screw_rotation_unit" @change="rotationUnitChange">
            <el-option
              v-for="item in rotation_unit_options"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            >
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item 
          label="功率单位" 
          prop="power_unit"
        >
          <el-select v-model="machine_info.power_unit">
            <el-option
              v-for="item in power_unit_options"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            >
            </el-option>
          </el-select>
        </el-form-item>
      </el-card>
      <div style="height: 4px" />
      <el-card>
        <div slot="header" class="clearfix" id="inject_part">
          注射单元
        </div>
        <el-tabs v-model="actived_index">
          <el-tab-pane
            v-for="item in machine_info.injection_units"
            :label="item.title"
            :key="item.name"
            :name="item.name"
          >
            <injection-unit
              ref="injectionUnit"
              :injector-info="item"
              :pressure-unit="machine_info.pressure_unit"
              :velocity-unit="machine_info.velocity_unit"
              :rotation-unit="machine_info.screw_rotation_unit"
              :ocpressure-unit="machine_info.oc_pressure_unit"
              :ocvelocity-unit="machine_info.oc_velocity_unit"
              :backpressure-unit="machine_info.backpressure_unit"
              :mac-trademark="machine_info.trademark"
              :power-method="machine_info.power_method"
            >
            </injection-unit>
          </el-tab-pane>
        </el-tabs>
      </el-card>
      <div style="height: 4px" />
      <el-card>
        <div slot="header" class="clearfix">
          锁模单元
        </div>
        <el-divider content-position="center">
          <span style="color: blue">模板参数</span>
        </el-divider>         
        <el-form-item 
          label="最小容模尺寸(横)" 
          prop="min_mold_size_horizon"
        >
          <el-input 
            type="number" 
            min="0" 
            v-model="machine_info.min_mold_size_horizon"
            @input="machine_info.min_mold_size_horizon=checkNumberFormat(machine_info.min_mold_size_horizon)"
          >
            <span slot="suffix">
              mm
            </span>
          </el-input>
        </el-form-item>
        <el-form-item 
          label="最小容模尺寸(竖)" 
          prop="min_mold_size_vertical"
        >
          <el-input 
            type="number" 
            min="0" 
            v-model="machine_info.min_mold_size_vertical"
            @input="machine_info.min_mold_size_vertical=checkNumberFormat(machine_info.min_mold_size_vertical)"
          >
            <span slot="suffix">
              mm
            </span>
          </el-input>
        </el-form-item>
        <el-form-item 
          label="最大容模尺寸(横)" 
          prop="max_mold_size_horizon"
        >
          <el-input 
            type="number" 
            min="0" 
            v-model="machine_info.max_mold_size_horizon"
            @input="machine_info.max_mold_size_horizon=checkNumberFormat(machine_info.max_mold_size_horizon)"
          >
            <span slot="suffix">
              mm
            </span>
          </el-input>
        </el-form-item>
        <el-form-item 
          label="最大容模尺寸(竖)" 
          prop="max_mold_size_vertical"
        >
          <el-input 
            type="number" 
            min="0" 
            v-model="machine_info.max_mold_size_vertical"
            @input="machine_info.max_mold_size_vertical=checkNumberFormat(machine_info.max_mold_size_vertical)"
          >
            <span slot="suffix">
              mm
            </span>
          </el-input>
        </el-form-item>
        <el-form-item 
          label="最小容模厚度" 
          prop="min_mold_thickness"
        >
          <el-input 
            type="number" 
            min="0" 
            v-model="machine_info.min_mold_thickness"
            @input="machine_info.min_mold_thickness=checkNumberFormat(machine_info.min_mold_thickness)"
          >
            <span slot="suffix">
              mm
            </span>
          </el-input>
        </el-form-item>
        <el-form-item 
          label="最大容模厚度" 
          prop="max_mold_thickness"
        >
          <el-input 
            type="number" 
            min="0" 
            v-model="machine_info.max_mold_thickness"
            @input="machine_info.max_mold_thickness=checkNumberFormat(machine_info.max_mold_thickness)"
          >
            <span slot="suffix">
              mm
            </span>
          </el-input>
        </el-form-item>
        <el-form-item 
          label="最小模板开距" 
          prop="min_platen_opening"
        >
          <el-input 
            type="number" 
            min="0" 
            v-model="machine_info.min_platen_opening"
            @input="machine_info.min_platen_opening=checkNumberFormat(machine_info.min_platen_opening)"
          >
            <span slot="suffix">
              mm
            </span>
          </el-input>
        </el-form-item>
        <el-form-item 
          label="最大模板开距" 
          prop="max_platen_opening"
        >
          <el-input 
            type="number" 
            min="0" 
            v-model="machine_info.max_platen_opening"
            @input="machine_info.max_platen_opening=checkNumberFormat(machine_info.max_platen_opening)"
          >
            <span slot="suffix">
              mm
            </span>
          </el-input>
        </el-form-item>
        <el-form-item 
          label="定位圈直径" 
          prop="locate_ring_diameter"
        >
          <el-input 
            type="number" 
            min="0" 
            v-model="machine_info.locate_ring_diameter"
            @input="machine_info.locate_ring_diameter=checkNumberFormat(machine_info.locate_ring_diameter)"
          >
            <span slot="suffix">
              mm
            </span>
          </el-input>
        </el-form-item>
        <el-divider content-position="center">
          <span style="color: blue">拉杆参数</span>
        </el-divider>

        <el-form-item 
          label="拉杆连接头尺寸" 
          prop="pull_rod_size"
        >
          <el-input
            type="number" 
            min="0" 
            v-model="machine_info.pull_rod_size"
            @input="machine_info.pull_rod_size=checkNumberFormat(machine_info.pull_rod_size)"
          >
          </el-input>
        </el-form-item>
        <el-form-item 
          label="拉杆直径" 
          prop="pull_rod_diameter"
        >
          <el-input
            type="number" 
            min="0" 
            v-model="machine_info.pull_rod_diameter"
            @input="machine_info.pull_rod_diameter=checkNumberFormat(machine_info.pull_rod_diameter)"
          >
            <span slot="suffix">
              mm
            </span>
          </el-input>
        </el-form-item>
        <el-form-item 
          label="拉杆间距(横)" 
          prop="pull_rod_distance_horizon"
        >
          <el-input 
            type="number" 
            min="0" 
            v-model="machine_info.pull_rod_distance_horizon"
            @input="machine_info.pull_rod_distance_horizon=checkNumberFormat(machine_info.pull_rod_distance_horizon)"
          >
            <span slot="suffix">
              mm
            </span>
          </el-input>
        </el-form-item>
        <el-form-item 
          label="拉杆间距(竖)" 
          prop="pull_rod_distance_vertical"
        >
          <el-input 
            type="number" 
            min="0" 
            v-model="machine_info.pull_rod_distance_vertical"
            @input="machine_info.pull_rod_distance_vertical=checkNumberFormat(machine_info.pull_rod_distance_vertical)"
          >
            <span slot="suffix">
              mm
            </span>
          </el-input>
        </el-form-item>
        <el-divider content-position="center">
          <span style="color: blue">开合模参数</span>
        </el-divider>
        <el-form-item 
          label="锁模方式" 
          prop="clamping_method"
        >
          <el-select v-model="machine_info.clamping_method">
            <el-option label="曲轴式" value="曲轴式"></el-option>
            <el-option label="直压式" value="直压式"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item 
          label="最大锁模力" 
          prop="max_clamping_force"
        >
          <el-input 
            type="number" 
            min="0" 
            v-model="machine_info.max_clamping_force"
            @input="machine_info.max_clamping_force=checkNumberFormat(machine_info.max_clamping_force, fixed=0)"
          >
            <span slot="suffix">
              {{ machine_info.clamping_force_unit }}
            </span>
          </el-input>
        </el-form-item>
        <el-form-item 
          label="最大开模行程" 
          prop="max_mold_open_stroke"
        >
          <el-input 
            type="number" 
            min="0" 
            v-model="machine_info.max_mold_open_stroke"
            @input="machine_info.max_mold_open_stroke=checkNumberFormat(machine_info.max_mold_open_stroke)"
          >
            <span slot="suffix">
              mm
            </span>
          </el-input>
        </el-form-item>        
        <el-divider content-position="center">
          <span style="color: blue">顶出参数</span>
        </el-divider>
        <el-form-item 
          label="最大顶出力" 
          prop="max_ejection_force"
        >
          <el-input 
            type="number" 
            min="0" 
            v-model="machine_info.max_ejection_force"
            @input="machine_info.max_ejection_force=checkNumberFormat(machine_info.max_ejection_force, fixed=0)"
          >
            <span slot="suffix">
              KN
            </span>
          </el-input>
        </el-form-item>
        <el-form-item 
          label="最大顶出行程" 
          prop="max_ejection_stroke"
        >
          <el-input 
            type="number" 
            min="0" 
            v-model="machine_info.max_ejection_stroke"
            @input="machine_info.max_ejection_stroke=checkNumberFormat(machine_info.max_ejection_stroke, fixed=0)"
          >
            <span slot="suffix">
              mm
            </span>
          </el-input>
        </el-form-item>
        <el-form-item 
          label="顶出孔数量" 
          prop="ejection_hole_num"
        >
          <el-input 
            type="number" 
            min="0" 
            v-model="machine_info.ejection_hole_num"
            @input="machine_info.ejection_hole_num=checkNumberFormat(machine_info.ejection_hole_num, fixed=0)"
          >
          </el-input>
        </el-form-item>         
      </el-card>
      <div style="height: 4px" />
      <el-card>
        <div slot="header" class="clearfix">
          动力/电热
        </div>
        <el-form-item 
          label="最大系统压力" 
          prop="hydraulic_system_pressure"
        >
          <el-input 
            type="number" 
            min="0" 
            v-model="machine_info.hydraulic_system_pressure"
            @input="machine_info.hydraulic_system_pressure=checkNumberFormat(machine_info.hydraulic_system_pressure)"
          >
            <span slot="suffix">
              MPa
            </span>
          </el-input>
        </el-form-item>
        <el-form-item 
          label="电机功率" 
          prop="motor_power"
        >
          <el-input 
            type="number" 
            min="0" 
            v-model="machine_info.motor_power"
            @input="machine_info.motor_power=checkNumberFormat(machine_info.motor_power)"
          >
            <span slot="suffix">
              {{ machine_info.power_unit }}
            </span>
          </el-input>
        </el-form-item>
        <el-form-item 
          label="电热功率" 
          prop="heater_power"
        >
          <el-input
            type="number" 
            min="0" 
            v-model="machine_info.heater_power"
            @input="machine_info.heater_power=checkNumberFormat(machine_info.heater_power)"
          >
            <span slot="suffix">
              {{ machine_info.power_unit }}
            </span>
          </el-input>
        </el-form-item>
        <el-form-item 
          label="温度控制区数" 
          prop="temp_control_zone_num"
        >
          <el-input 
            type="number" 
            min="0" 
            v-model="machine_info.temp_control_zone_num"
            @input="machine_info.temp_control_zone_num=checkNumberFormat(machine_info.temp_control_zone_num, 0)"
          >
          </el-input>
        </el-form-item>
        <br />
        <el-form-item label="抽芯" prop="needle_core">
          <el-radio-group 
            v-model="machine_info.needle_core"
          >
            <el-radio v-model="machine_info.needle_core" label="有">
              有
            </el-radio>
            <el-radio v-model="machine_info.needle_core" label="没有">
              没有
            </el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item 
          label="抽芯组数" 
          prop="core_pulling"
        >
          <el-input
            type="number" 
            v-model="machine_info.core_pulling"
            :disabled="machine_info.needle_core === '没有'"
            @input="machine_info.core_pulling=checkNumberFormat(machine_info.core_pulling, fixed=0)"
          >
            <span slot="suffix">
              组
            </span>
          </el-input>
        </el-form-item>
      </el-card>
      <div style="height: 4px" />
      <el-card>
        <div slot="header" class="clearfix">
          其他
        </div>

        <el-form-item 
          label="机器重量" 
          prop="machine_weight"
        >
          <el-input 
            type="number" 
            min="0" 
            v-model="machine_info.machine_weight"
            @input="machine_info.machine_weight=checkNumberFormat(machine_info.machine_weight)"
          >
            <span slot="suffix">
              KG
            </span>
          </el-input>
        </el-form-item>
        <el-form-item 
          label="机台外形尺寸(长)" 
          prop="size"
        >
          <el-input 
            type="number" 
            min="0" 
            v-model="machine_info.size_length"
            @input="machine_info.size_length=checkNumberFormat(machine_info.size_length)"
          >
            <span slot="suffix">
              mm
            </span>
          </el-input>
        </el-form-item>
        <el-form-item 
          label="机台外形尺寸(宽)" 
          prop="size"
        >
          <el-input 
            type="number" 
            min="0" 
            v-model="machine_info.size_width"
            @input="machine_info.size_width=checkNumberFormat(machine_info.size_width)"
          >
            <span slot="suffix">
              mm
            </span>
          </el-input>
        </el-form-item>
        <el-form-item 
          label="机台外形尺寸(高)" 
          prop="size"
        >
          <el-input 
            type="number" 
            min="0" 
            v-model="machine_info.size_height"
            @input="machine_info.size_height=checkNumberFormat(machine_info.size_height)"
          >
            <span slot="suffix">
              mm
            </span>
          </el-input>
        </el-form-item>
        <el-form-item 
          label="响应时间" 
          prop="response_time"
        >
          <el-input 
            type="number" 
            min="0" 
            v-model="machine_info.response_time"
            @input="machine_info.response_time=checkNumberFormat(machine_info.response_time)"
          >
            <span slot="suffix">
              s
            </span>
          </el-input>
        </el-form-item>
        <el-form-item 
          label="增强比" 
          prop="enhancement_ratio"
        >
          <el-input v-model="machine_info.enhancement_ratio"></el-input>
        </el-form-item>

        <el-form-item 
          label="制造日期" 
          prop="manufacturing_date"
        >
          <el-date-picker
            v-model="machine_info.manufacturing_date"
            type="date"
            placeholder="选择时间日期"
            value-format="yyyy-MM-dd"
          >
          </el-date-picker>
        </el-form-item>
        <el-form-item 
          label="出厂日期" 
          prop="manufacture_date"
        >
          <el-date-picker
            v-model="machine_info.manufacture_date"
            type="date"
            placeholder="选择日期"
            value-format="yyyy-MM-dd"
          >
          </el-date-picker>
        </el-form-item>
        <el-form-item 
          label="出厂编码" 
          prop="manufacture_no"
        >
          <el-input v-model="machine_info.manufacture_no"></el-input>
        </el-form-item> 
        <el-form-item 
          label="备注" 
          prop="remark"
        >
          <el-input v-model="machine_info.remark"></el-input>
        </el-form-item>
      </el-card>
    </el-form>
    <div style="height: 25px" />
    <div class="nextButton">
      <el-button
        v-if="machine_info.id"
        type="primary" 
        size="small" 
        :loading="update_loading" 
        @click="updateMachineDetail"
      >
        更  新
      </el-button>
      <el-button
        v-else
        type="primary" 
        size="small" 
        :loading="save_loading" 
        @click="saveMachineInfo"
      >
        保  存
      </el-button>
      <el-button
        v-if="view_type=='edit'" 
        type="success" 
        size="small"
        :loading="export_loading" 
        @click="exportMachineToExcel" 
      >
        导  出
      </el-button>
      <el-button 
        type="danger"
        size="small"
        @click="resetView" 
      >
        重  置
      </el-button>
      <el-button 
        type="warning"
        size="small" 
        @click="$emit('close')" 
      >
        返  回
      </el-button>
    </div>
  </div>
</template>

<script>
import InjectionUnit from "./components/InjectionUnit.vue"
import * as machine_const from "@/utils/machine-const"
import { machineMethod, exportMachine } from "@/api"
import { getFullReportUrl } from "@/utils/assert"

export default {
  name: "CreateInjectionMachine",
  components: { InjectionUnit },
  props: {
    id: {
      type: Number,
      default: null
    },
    viewType: {
      type: String,
      default: null,
    },
    excelData:{
      type: Object,
      default: () => { }
    }
  },
  data() {
    return {
      view_type: this.viewType,
      actived_index: "1",
      machine_info: structuredClone(machine_const.injectionMachineForm),
      rules: {
        trademark: [
          { required: true, message: "注塑机型号为空!" }
        ],
        manufacturer:[
          { required: true, message: "注塑机品牌为空!" }
        ],
        serial_no: [
          { required: true, message: "设备编码为空!" }
        ],
        data_source: [
          { required: true, message: "注塑机来源为空!" }
        ],
        power_method: [
          { required: true, message: "注塑机类型(驱动方式)为空!" }
        ],
        pressure_unit: [
          { required: true, message: "压力单位为空!" }
        ],
        backpressure_unit: [
          { required: true, message: "背压单位为空!" }
        ],
        velocity_unit: [
          { required: true, message: "速度单位为空!" }
        ],
        temperature_unit: [
          { required: true, message: "温度单位为空!" }
        ],
        time_unit: [
          { required: true, message: "时间单位为空!" }
        ],
        position_unit: [
          { required: true, message: "位置单位为空!" }
        ],
        clamping_force_unit: [
          { required: true, message: "锁模力单位为空!" }
        ],  
        screw_rotation_unit: [
          { required: true, message: "螺杆转速单位为空!" }
        ],
        power_unit: [
          { required: true, message: "功率单位为空!" }
        ],    
      },
      machine_datasource_options: machine_const.machineDatasourceOptions,
      machine_type_options: machine_const.machineTypeOptions,
      machine_manu_options: machine_const.machineManufacturerOptions,
      pres_unit_options: machine_const.presUnitOptions,
      velo_unit_options: machine_const.veloUnitOptions,
      temp_unit_options: machine_const.tempUnitOptions,
      time_unit_options: machine_const.timeUnitOptions,
      posi_unit_options: machine_const.posiUnitOptions,
      clfc_unit_options: machine_const.clfcUnitOptions,
      rotation_unit_options: machine_const.rotationUnitOptions,
      power_unit_options: machine_const.powerUnitOptions,
      export_loading: false,
      update_loading: false,
      save_loading: false,
    }
  },
  watch: {
    id() {
      this.machine_info.id = this.id
    },
    viewType() {
      this.view_type = this.viewType
    },
    excelData: {
      handler: function() {
        if (this.excelData) {
          this.machine_info = this.excelData
          for (let i = 0; i < this.machine_info.injection_units.length; i++) {
            this.machine_info.injection_units[i].nozzle_hole_diameter = String(this.machine_info.injection_units[i].nozzle_hole_diameter)
            this.machine_info.injection_units[i].nozzle_sphere_diameter = String(this.machine_info.injection_units[i].nozzle_sphere_diameter)
          }
        }
      },
      deep: true,
      immediate: true  
    }
  },
  created() {
  },
  mounted() {
    this.getMachineInfo()
  },
  methods: {
    onMachineTypeChanged(val) {
      const MachineTypeOptions = {
        "单色注塑机": 1,
        "双色注塑机": 2,
        "三色注塑机": 3,
        "四色注塑机": 4,
        "五色注塑机": 5,
        "六色注塑机": 6,
        "七色注塑机": 7,
      }
      let bef = this.machine_info.injection_units.length
      let cur = MachineTypeOptions[val]
      if (bef < cur) {
        for (let i = bef; i < cur; ++i) {
          let injection_unit = structuredClone(machine_const.injectionUnitForm)
          injection_unit.title = "部件" + String(i + 1)
          injection_unit.name = String(i + 1)
          this.machine_info.injection_units.push(injection_unit)
        }
      } else if (bef > cur) {
        this.machine_info.injection_units = this.machine_info.injection_units.slice(0, cur)
      }
      this.actived_index = String(this.machine_info.injection_units.length)
    },
    async getMachineInfo() {
      // 通过页面跳转传入
      if (this.$route.query.id) {
        this.machine_info.id = this.$route.query.id
      }

      if (this.machine_info.id == null) return

      // 读取注塑机信息
      await machineMethod.getDetail(this.machine_info.id)
        .then(res => {
          if (res.status === 0) {
            this.machine_info = res.data
            for (let i = 0; i < this.machine_info.injection_units.length; ++i) {
              this.machine_info.injection_units[i].title = "部件" + (i + 1)
              this.machine_info.injection_units[i].name = String(i + 1)
            }
          }
        })

      if (this.viewType == "copy") {
        this.machine_info.id = null
        for (let i = 0; i < this.machine_info.injection_units.length; ++i) {
          this.machine_info.injection_units[i].id = null
        }
      }

      // 默认显示第一个注射部件
      this.actived_index = "1"
    },
    async saveMachineInfo() {
      let allValid = true
      // 验证注射单元
      this.refs["injectionUnit"].forEach(component => {
        component.$refs["formData"].validate(valid => {allValid = valid})
      })
      // 验证注塑机信息
      this.$refs["formData"].validate(valid => {allValid = valid})

      if (!allValid) {
        this.$message({ message: "请填写必填项！", type: "error" })
        return
      }

      // 保存注塑机信息
      if (this.machine_info.id) {
        machineMethod.edit(this.machine_info, this.machine_info.id)
          .then(res => {
            if (res.status === 0) {
              this.$message({ message:"保存成功！", type:"success" })
              this.$emit("close")
              this.$router.push("/machine/injection/list")
            }
          })
      } else {
        machineMethod.add(this.machine_info)
          .then(res => {
            if (res.status === 0) {
              this.$message({ message:"保存成功！", type:"success" })
              this.$emit("close")
            }
          })
      }
    },
    exportMachineToExcel() {
      exportMachine(this.machine_info)
        .then(res => {
          if (res.status === 0 && res.data.url) {
            this.$message({ message: "导出成功。", type: "success" })
            this.$emit("close")
            window.location.href = getFullReportUrl(res.data.url)
          }
        })
    },
    resetView() {
      this.machine_info = structuredClone(machine_const.injectionMachineForm)
    },
  }
}
</script>

<style lang="scss" scoped>
  .el-input {
    width: 10rem;
  }

  .el-select {
    width: 10rem;
  }
</style>
