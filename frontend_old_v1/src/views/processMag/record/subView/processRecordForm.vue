<template>
  <div ref="processRecord">
    <el-form 
      size="mini" 
      label-width="6rem"
      label-position="right"
      :inline="true"
    >
      <el-collapse v-model="activeNames" class="collapseItemTitle">
        <el-collapse-item title="工艺设定" name="1">
          <el-row>
            <el-col :xs="24" :lg="13" :xl="13">
              <el-card class="box-card" style="min-height:240px">
                <el-table 
                  size="mini"
                  :data="record_detail.inject_para.table_data" 
                  :key="Math.random()"
                >
                  <el-table-column 
                    label="工艺参数"
                    width="80" 
                    align="center"
                  >
                    <template slot="header">
                      <div>注射段数</div>
                      <el-select 
                        v-model="record_detail.inject_para.injection_stage" 
                        size="mini"
                      >
                        <el-option
                          v-for="option, idx in record_detail.inject_para.max_injection_stage_option"
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

                  <template 
                    v-for="(col, colidx) in record_detail.inject_para.max_injection_stage_option"
                  >
                    <el-table-column
                      min-width="80"
                      align="center"
                      :key="colidx"
                      :label="injection_stage_header[col]"
                    >
                      <template slot-scope="scope">
                        <el-input 
                          :id="components_view_id.inject_para.table[scope.$index][colidx]"
                          v-model="record_detail.inject_para.table_data[scope.$index].sections[colidx]" 
                          :disabled="colidx >=record_detail.inject_para.injection_stage"
                          type="number" 
                          min="0" 
                          size="mini"
                          @input="record_detail.inject_para.table_data[scope.$index].sections[colidx]=checkNumberFormat(record_detail.inject_para.table_data[scope.$index].sections[colidx])"
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
                      {{ record_detail.inject_para.table_data[scope.$index].unit }}
                    </template>
                  </el-table-column>
                </el-table>
              </el-card>

              <el-card class="box-card" style="min-height:240px">
                <el-form-item label="注射时间">
                  <el-input
                    :id="components_view_id.inject_para.inj_time"
                    type="text"
                    v-model="record_detail.inject_para.injection_time"
                    style="width: 7rem"
                    @input="record_detail.inject_para.injection_time=checkNumberFormat(record_detail.inject_para.injection_time)"
                  >
                    <span slot="suffix">{{ machine_info.time_unit }}</span>
                  </el-input>
                </el-form-item>

                <el-form-item label="注射延迟">
                  <el-input
                    :id="components_view_id.inject_para.inj_delay"
                    type="text"
                    v-model="record_detail.inject_para.injection_delay_time"
                    style="width: 7rem"
                    @input="record_detail.inject_para.injection_delay_time=checkNumberFormat(record_detail.inject_para.injection_delay_time)"
                  >
                    <span slot="suffix">{{ machine_info.time_unit }}</span>
                  </el-input>
                </el-form-item>

                <el-form-item label="冷却时间">
                  <el-input
                    :id="components_view_id.inject_para.cool_time"
                    type="text"
                    v-model="record_detail.inject_para.cooling_time"
                    style="width: 7rem"
                    @input="record_detail.inject_para.cooling_time=checkNumberFormat(record_detail.inject_para.cooling_time)"
                  >
                    <span slot="suffix">{{ machine_info.time_unit }}</span>
                  </el-input>
                </el-form-item>

                <el-divider content-position="center">
                  <span style="color:blue">VP切换</span>
                </el-divider>

                <el-form-item label="切换方式">
                  <el-select
                    v-model="record_detail.VP_switch.VP_switch_mode"
                    style="width: 7rem"
                    placeholder="请选择"
                  >
                    <el-option
                      v-for="option in VP_switch_mode_options"
                      :key="option.value"
                      :label="option.label"
                      :value="option.value"
                    >
                    </el-option>
                  </el-select>
                </el-form-item>

                <el-form-item label="切换时间">
                  <el-input
                    :id="components_view_id.VP_switch.time"
                    type="text"
                    v-model="record_detail.VP_switch.VP_switch_time" 
                    style="width: 7rem"
                    :disabled="record_detail.VP_switch.VP_switch_mode == null
                      ||record_detail.VP_switch.VP_switch_mode.indexOf('时间') == -1"
                    @input="record_detail.VP_switch.VP_switch_time=checkNumberFormat(record_detail.VP_switch.VP_switch_time)"
                  >
                    <span slot="suffix">{{ machine_info.time_unit }}</span>
                  </el-input>
                </el-form-item>

                <el-form-item label="切换位置">
                  <el-input
                    :id="components_view_id.VP_switch.position"
                    type="text"
                    v-model="record_detail.VP_switch.VP_switch_position" 
                    style="width: 7rem"
                    :disabled="record_detail.VP_switch.VP_switch_mode == null
                      ||record_detail.VP_switch.VP_switch_mode.indexOf('位置') == -1"
                    @input="record_detail.VP_switch.VP_switch_position=checkNumberFormat(record_detail.VP_switch.VP_switch_position)"
                  >
                    <span slot="suffix">{{ machine_info.position_unit }}</span>
                  </el-input>
                </el-form-item>

                <el-form-item label="切换压力">
                  <el-input
                    :id="components_view_id.VP_switch.pressure"
                    type="text"
                    v-model="record_detail.VP_switch.VP_switch_pressure" 
                    style="width: 7rem"
                    :disabled="record_detail.VP_switch.VP_switch_mode == null
                      ||record_detail.VP_switch.VP_switch_mode.indexOf('压力') == -1"
                    @input="record_detail.VP_switch.VP_switch_pressure=checkNumberFormat(record_detail.VP_switch.VP_switch_pressure)"
                  >
                    <span slot="suffix">{{ machine_info.pressure_unit }}</span>
                  </el-input>
                </el-form-item>

                <el-form-item label="切换速度">
                  <el-input
                    :id="components_view_id.VP_switch.velocity"
                    type="text"
                    v-model="record_detail.VP_switch.VP_switch_velocity" 
                    style="width: 7rem"
                    :disabled="record_detail.VP_switch.VP_switch_mode == null
                      ||record_detail.VP_switch.VP_switch_mode.indexOf('速度') == -1"
                    @input="record_detail.VP_switch.VP_switch_velocity=checkNumberFormat(record_detail.VP_switch.VP_switch_velocity)"
                  >
                    <span slot="suffix">{{ machine_info.velocity_unit }}</span>
                  </el-input>
                </el-form-item>
              </el-card>

              <el-card class="box-card" style="min-height:240px">
                <el-table 
                  size="mini"
                  :data="record_detail.holding_para.table_data" 
                  :key="Math.random()"
                >
                  <el-table-column 
                    label="工艺参数"
                    width="80" 
                    align="center"
                  >
                    <template slot="header">
                      <div>保压段数</div>
                      <el-select 
                        v-model="record_detail.holding_para.holding_stage" 
                        size="mini"
                      >
                        <el-option
                          v-for="option, idx in record_detail.holding_para.max_holding_stage_option"
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

                  <template v-for="(col, colidx) in record_detail.holding_para.max_holding_stage_option">
                    <el-table-column
                      :key="colidx"
                      :label="holding_stage_header[col]"
                      min-width="80"
                      align="center"
                    >
                      <template slot-scope="scope">
                        <el-input 
                          :id="components_view_id.holding_para.table[scope.$index][colidx]"
                          v-model="record_detail.holding_para.table_data[scope.$index].sections[colidx]" 
                          :disabled="colidx >=record_detail.holding_para.holding_stage"
                          type="number" 
                          min="0" 
                          size="mini"
                          @input="record_detail.holding_para.table_data[scope.$index].sections[colidx]=checkNumberFormat(record_detail.holding_para.table_data[scope.$index].sections[colidx])"
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
                      {{ record_detail.holding_para.table_data[scope.$index].unit }}
                    </template>
                  </el-table-column>
                </el-table>
              </el-card>
            </el-col>
            
            <el-col :xs="24" :lg="11" :xl="11">
              <el-card class="box-card" style="min-height:720px">
                <el-table 
                  size="mini"
                  :data="record_detail.metering_para.table_data"
                  :key="Math.random()"
                >
                  <el-table-column 
                    label="工艺参数"
                    width="80" 
                    align="center"
                  >
                    <template slot="header">
                      <div>计量段数</div>
                      <el-select 
                        v-model="record_detail.metering_para.metering_stage" 
                        size="mini"
                      >
                        <el-option
                          v-for="option, idx in record_detail.metering_para.max_metering_stage_option"
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

                  <template v-for="(col, colidx) in record_detail.metering_para.max_metering_stage_option">
                    <el-table-column
                      :key="colidx"
                      :label="metering_stage_header[col]"
                      min-width="80"
                      align="center"
                    >
                      <template slot-scope="scope">
                        <el-input 
                          :id="components_view_id.metering_para.table[scope.$index][colidx]"
                          v-model="record_detail.metering_para.table_data[scope.$index].sections[colidx]" 
                          :disabled="colidx >=record_detail.metering_para.metering_stage"
                          type="number" 
                          min="0" 
                          size="mini"
                          @input="record_detail.metering_para.table_data[scope.$index].sections[colidx]=checkNumberFormat(record_detail.metering_para.table_data[scope.$index].sections[colidx])"
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
                      {{ record_detail.metering_para.table_data[scope.$index].unit }}
                    </template>
                  </el-table-column>
                </el-table>

                <div style="height:15px" />

                <el-form-item label="储前松退模式">
                  <el-select 
                    :id="components_view_id.metering_para.dec_mode_bef"
                    v-model="record_detail.metering_para.decompressure_mode_before_metering"
                    style="width: 8rem"
                  >
                    <el-option
                      v-for="option, idx in decompressure_mode_options"
                      :key="idx"
                      :label="option.label"
                      :value="option.value"
                    >
                    </el-option>
                  </el-select>
                </el-form-item>

                <br>

                <el-form-item label="储后松退模式">
                  <el-select 
                    :id="components_view_id.metering_para.dec_mode_aft"
                    v-model="record_detail.metering_para.decompressure_mode_after_metering"
                    style="width: 8rem"
                  >
                    <el-option
                      v-for="option, idx in decompressure_mode_options"
                      :key="idx"
                      :label="option.label"
                      :value="option.value"
                    >
                    </el-option>
                  </el-select>
                </el-form-item>

                <el-table
                  size="mini"
                  :data="record_detail.metering_para.decompressure_paras"
                  :key="Math.random()"
                >
                  <el-table-column
                    label=""
                    width="45"
                    align="center"
                  >
                    <template slot-scope="scope">
                      {{ scope.row.label }}
                    </template>
                  </el-table-column>

                  <el-table-column
                    label="压力"
                    min-width="80"
                    align="center"
                  >
                    <template slot="header">
                      <div>压力</div>
                      <div>{{ machine_info.pressure_unit }}</div>
                    </template>
                    <template slot-scope="scope">
                      <el-input
                        :id="components_view_id.metering_para.deco_table[scope.$index][0]"
                        :disabled="((scope.$index === 0 &&record_detail.metering_para.decompressure_mode_before_metering === '否')
                          || (scope.$index === 1 &&record_detail.metering_para.decompressure_mode_after_metering === '否'))"
                        v-model="scope.row.pressure"
                        size="mini"
                        @input="scope.row.pressure=checkNumberFormat(scope.row.pressure)"
                      >
                      </el-input>
                    </template>
                  </el-table-column>

                  <el-table-column
                    label="速度"
                    min-width="80"
                    align="center"
                  >
                    <template slot="header">
                      <div>速度</div>
                      <div>{{ machine_info.velocity_unit }}</div>
                    </template>
                    <template slot-scope="scope">
                      <el-input
                        :id="components_view_id.metering_para.deco_table[scope.$index][1]"
                        :disabled="((scope.$index === 0 &&record_detail.metering_para.decompressure_mode_before_metering === '否')
                          || (scope.$index === 1 &&record_detail.metering_para.decompressure_mode_after_metering === '否'))"
                        v-model="scope.row.velocity"
                        size="mini"
                        @input="scope.row.velocity=checkNumberFormat(scope.row.velocity)"
                      >
                      </el-input>
                    </template>
                  </el-table-column>

                  <el-table-column
                    label="距离"
                    min-width="80"
                    align="center"
                  >
                    <template slot="header">
                      <div>距离</div>
                      <div>{{ machine_info.position_unit }}</div>
                    </template>
                    <template slot-scope="scope">
                      <el-input
                        :id="components_view_id.metering_para.deco_table[scope.$index][2]"
                        :disabled="((scope.$index === 0 &&record_detail.metering_para.decompressure_mode_before_metering != '距离')
                          || (scope.$index === 1 &&record_detail.metering_para.decompressure_mode_after_metering != '距离'))"
                        v-model="scope.row.distance"
                        size="mini"
                        @input="scope.row.distance=checkNumberFormat(scope.row.distance)"
                      >
                      </el-input>
                    </template>
                  </el-table-column>

                  <el-table-column
                    label="时间"
                    min-width="80"
                    align="center"
                  >
                    <template slot="header">
                      <div>时间</div>
                      <div>{{ machine_info.time_unit }}</div>
                    </template>
                    <template slot-scope="scope">
                      <el-input
                        :id="components_view_id.metering_para.deco_table[scope.$index][3]"
                        :disabled="((scope.$index === 0 &&record_detail.metering_para.decompressure_mode_before_metering != '时间')
                          || (scope.$index === 1 &&record_detail.metering_para.decompressure_mode_after_metering != '时间'))"
                        v-model="scope.row.time"
                        size="mini"
                        @input="scope.row.time=checkNumberFormat(scope.row.time)"
                      >
                      </el-input>
                    </template>
                  </el-table-column>
                </el-table>

                <div style="height:15px" />

                <el-form-item label="储料延迟">
                  <el-input
                    :id="components_view_id.metering_para.measureDelay"
                    type="number"
                    v-model="record_detail.metering_para.metering_delay_time"
                    style="width: 8rem"
                    @input="record_detail.metering_para.metering_delay_time=checkNumberFormat(record_detail.metering_para.metering_delay_time)"
                  >
                    <span slot="suffix">{{ machine_info.time_unit }}</span>
                  </el-input>
                </el-form-item>

                <br>

                <el-form-item label="终止位置">
                  <el-input
                    :id="components_view_id.metering_para.stopPos"
                    type="number"
                    v-model="record_detail.metering_para.metering_ending_position"
                    style="width: 8rem"
                    @input="record_detail.metering_para.metering_ending_position=checkNumberFormat(record_detail.metering_para.metering_ending_position)"
                  >
                    <span slot="suffix">{{ machine_info.position_unit }}</span>
                  </el-input>
                </el-form-item>
              </el-card>
            </el-col>

            <el-col :xs="24" :lg="24" :xl="24">
              <el-card class="box-card">
                <el-table 
                  size="mini"
                  :data="record_detail.temp_para.table_data"
                  :key="Math.random()"
                >
                  <el-table-column 
                    label="工艺参数"
                    width="80" 
                    align="center"
                  >
                    <template slot="header">
                      <div>温度段数</div>
                      <el-select 
                        v-model="record_detail.temp_para.barrel_temperature_stage" 
                        size="mini"
                      >
                        <el-option
                          v-for="option, idx in record_detail.temp_para.max_barrel_temperature_stage_option"
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

                  <template v-for="(col, colidx) in record_detail.temp_para.max_barrel_temperature_stage_option">
                    <el-table-column
                      :key="colidx"
                      :label="temp_stage_header[col]"
                      min-width="80"
                      align="center"
                    >
                      <template slot-scope="scope">
                        <el-input 
                          :id="components_view_id.temp_para.table[scope.$index][colidx]"
                          v-model="record_detail.temp_para.table_data[scope.$index].sections[colidx]" 
                          :disabled="colidx >=record_detail.temp_para.barrel_temperature_stage"
                          type="number" 
                          min="0" 
                          size="mini"
                          @input="record_detail.temp_para.table_data[scope.$index].sections[colidx]=checkNumberFormat(record_detail.temp_para.table_data[scope.$index].sections[colidx])"
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
                      {{ record_detail.temp_para.table_data[scope.$index].unit }}
                    </template>
                  </el-table-column>
                </el-table>
              </el-card>
            </el-col>
          </el-row>
        </el-collapse-item>

        <el-collapse-item title="开合模设定" name="2" v-if="false">
          <el-row>
            <el-col :xs="24" :lg="8" :xl="6">
              <el-card class="box-card" style="min-width:300px">
                <el-form
                  size="mini"
                  label-width="7rem"
                  label-position="right"
                  :inline="true"
                  class="inputClass"
                >
                  <el-form-item 
                    label="锁模力"
                    prop="set_mold_clamping_force"
                  >
                    <el-input
                      v-model="record_detail.opening_and_clamping_mold_setting.set_mold_clamping_force"
                      type="number"
                      @input="record_detail.opening_and_clamping_mold_setting.set_mold_clamping_force=checkNumberFormat(record_detail.opening_and_clamping_mold_setting.set_mold_clamping_force)"
                    >
                      <span slot="suffix">Ton</span>
                    </el-input>
                  </el-form-item>

                  <el-form-item 
                    label="使用机械手"
                    prop="using_robot"
                  >
                    <el-radio
                      v-model="record_detail.opening_and_clamping_mold_setting.using_robot"
                      label="是"
                    >
                      是
                    </el-radio>
                    <el-radio
                      v-model="record_detail.opening_and_clamping_mold_setting.using_robot"
                      label="否"
                    >
                      否
                    </el-radio>
                  </el-form-item>

                  <el-form-item 
                    label="使用夹具"
                    prop="using_tool"
                  >
                    <el-radio
                      v-model="record_detail.opening_and_clamping_mold_setting.using_tool"
                      label="是"
                    >
                      是
                    </el-radio>
                    <el-radio
                      v-model="record_detail.opening_and_clamping_mold_setting.using_tool"
                      label="否"
                    >
                      否
                    </el-radio>
                  </el-form-item>

                  <el-form-item 
                    label="复位方式"
                    prop="reset_method"
                  >
                    <el-select
                      v-model="record_detail.opening_and_clamping_mold_setting.reset_method"
                    >
                      <el-option label="弹弓" value="弹弓"></el-option>
                      <el-option label="强制拉杆" value="强制拉杆"></el-option>
                      <el-option label="抽芯" value="抽芯"></el-option>
                    </el-select>
                  </el-form-item>

                  <el-form-item 
                    label="模保时间"
                    prop="set_mold_protect_time"
                  >
                    <el-input
                      v-model="record_detail.opening_and_clamping_mold_setting.set_mold_protect_time"
                      type="number"
                      @input="record_detail.opening_and_clamping_mold_setting.set_mold_protect_time=checkNumberFormat(record_detail.opening_and_clamping_mold_setting.set_mold_protect_time)"
                    >
                      <span slot="suffix">s</span>
                    </el-input>
                  </el-form-item>

                  <el-form-item 
                    label="模保速度"
                    prop="set_mold_protect_velocity"
                  >
                    <el-input
                      v-model="record_detail.opening_and_clamping_mold_setting.set_mold_protect_velocity"
                      type="number"
                      @input="record_detail.opening_and_clamping_mold_setting.set_mold_protect_velocity=checkNumberFormat(record_detail.opening_and_clamping_mold_setting.set_mold_protect_velocity)"
                    >
                      <span slot="suffix">{{ machine_info.oc_velocity_unit }}</span>
                    </el-input>
                  </el-form-item>

                  <el-form-item 
                    label="模保压力"
                    prop="set_mold_protect_pressure"
                  >
                    <el-input
                      v-model="record_detail.opening_and_clamping_mold_setting.set_mold_protect_pressure"
                      type="number"
                      @input="record_detail.opening_and_clamping_mold_setting.set_mold_protect_pressure=checkNumberFormat(record_detail.opening_and_clamping_mold_setting.set_mold_protect_pressure)"
                    >
                      <span slot="suffix">{{ machine_info.oc_pressure_unit }}</span>
                    </el-input>
                  </el-form-item>
                  <el-form-item 
                    label="模保位置"
                    prop="set_mold_protect_distance"
                  >
                    <el-input
                      v-model="record_detail.opening_and_clamping_mold_setting.set_mold_protect_distance"
                      type="number"
                      @input="record_detail.opening_and_clamping_mold_setting.set_mold_protect_distance=checkNumberFormat(record_detail.opening_and_clamping_mold_setting.set_mold_protect_distance)"
                    >
                      <span slot="suffix">{{ machine_info.position_unit }}</span>
                    </el-input>
                  </el-form-item>
                  <el-form-item 
                    label="允许偏差"
                    prop="opening_position_deviation"
                  >
                    <el-tooltip class="item" effect="dark" content="开模终止位置允许偏差" placement="top">
                      <el-input
                        v-model="record_detail.opening_and_clamping_mold_setting.opening_position_deviation"
                        type="number"
                        @input="record_detail.opening_and_clamping_mold_setting.opening_position_deviation=checkNumberFormat(record_detail.opening_and_clamping_mold_setting.opening_position_deviation)"
                      >
                        <span slot="suffix">mm</span>
                      </el-input>
                    </el-tooltip>
                  </el-form-item>

                  <el-form-item 
                    label="转盘方式"
                    prop="turnable_method"
                  >
                    <el-select
                      v-model="record_detail.opening_and_clamping_mold_setting.turnable_method"
                      type="number"
                    >
                      <el-option label="先转后顶" value="先转后顶"></el-option>
                      <el-option label="先顶后转" value="先顶后转"></el-option>
                    </el-select>
                  </el-form-item>

                  <el-form-item 
                    label="转盘速度"
                    prop="turnable_velocity"
                  >
                    <el-input
                      v-model="record_detail.opening_and_clamping_mold_setting.turnable_velocity"
                      type="number"
                      @input="record_detail.opening_and_clamping_mold_setting.turnable_velocity=checkNumberFormat(record_detail.opening_and_clamping_mold_setting.turnable_velocity)"
                    >
                      <span slot="suffix">{{ machine_info.oc_velocity_unit }}</span>
                    </el-input>
                  </el-form-item>
                </el-form>
              </el-card>
            </el-col>

            <el-col :xs="24" :lg="16" :xl="18">
              <el-card class="boc-card">
                <el-table
                  size="mini"
                  :data="record_detail.opening_and_clamping_mold_setting.mold_opening.table_data"
                  :key="Math.random()"
                >
                  <el-table-column 
                    label="开模参数" 
                    width="80" 
                    align="center"
                  >
                    <template slot="header">
                      <div>开模段数</div>
                      <el-select
                        v-model="record_detail.opening_and_clamping_mold_setting.mold_opening.mold_opening_stage"
                        size="mini"
                      >
                        <el-option
                          v-for="(option, index) in 
                            record_detail.opening_and_clamping_mold_setting.mold_opening.max_mold_opening_stage_option"
                          :key="index"
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

                  <template
                    v-for="(col, colidx) in 
                      record_detail.opening_and_clamping_mold_setting.mold_opening.max_mold_opening_stage_option"
                  >
                    <el-table-column
                      min-width="80"
                      align="center"
                      :key="colidx"
                      :label="mold_opening_stage_header[col]"
                    >
                      <template slot-scope="scope">
                        <el-input
                          :id="components_view_id.mold_opening.table[scope.$index][colidx]"
                          v-model="scope.row.sections[colidx]"
                          :disabled="colidx >= record_detail.opening_and_clamping_mold_setting.mold_opening.mold_opening_stage"
                          type="number"
                          min="0"
                          size="mini"
                          @input="scope.row.sections[colidx]=checkNumberFormat(scope.row.sections[colidx])"
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
                      {{ scope.row.unit }}
                    </template>
                  </el-table-column>
                </el-table>
                    
                <div style="height:50px" />

                <el-table
                  size="mini"
                  :data="record_detail.opening_and_clamping_mold_setting.mold_clamping.table_data"
                  :key="Math.random()"
                >
                  <el-table-column label="合模参数" width="80" align="center">
                    <template slot="header">
                      <div>合模段数</div>
                      <el-select
                        v-model="record_detail.opening_and_clamping_mold_setting.mold_clamping.mold_clamping_stage"
                        size="mini"
                      >
                        <el-option
                          v-for="(option, idx) in 
                            record_detail.opening_and_clamping_mold_setting.mold_clamping.max_mold_clamping_stage_option"
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
                  
                  <template
                    v-for="(col, colidx) in 
                      record_detail.opening_and_clamping_mold_setting.mold_clamping.max_mold_clamping_stage_option"
                  >
                    <el-table-column
                      :key="colidx"
                      :label="mold_clamping_stage_header[col]"
                      min-width="80"
                      align="center"
                    >
                      <template slot-scope="scope">
                        <el-input
                          :id="components_view_id.mold_clamping.table[scope.$index][colidx]"
                          v-model="scope.row.sections[colidx]"
                          :disabled="colidx >= 
                            record_detail.opening_and_clamping_mold_setting.mold_clamping.mold_clamping_stage"
                          type="number"
                          min="0"
                          size="mini"
                          @input="scope.row.sections[colidx]=checkNumberFormat(scope.row.sections[colidx])"
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
                      {{ scope.row.unit }}
                    </template>
                  </el-table-column>
                </el-table>

                <div style="height:36px" />
              </el-card>
            </el-col>
          </el-row>
        </el-collapse-item>

        <el-collapse-item title="顶针设定" name="3" v-if="false">
          <el-row>
            <el-col :xs="24" :lg="8" :xl="6">
              <el-card class="box-card" style="min-width:300px">
                <el-form
                  size="mini"
                  label-width="7rem"
                  label-position="right"
                  :inline="true"
                  class="inputClass"
                >
                  <el-form-item 
                    label="开始位置"
                    prop="ejector_start_point"
                  >
                    <el-input 
                      type="number"
                      v-model="record_detail.ejector_setting.ejector_start_point" 
                      @input="record_detail.ejector_setting.ejector_start_point=checkNumberFormat(record_detail.ejector_setting.ejector_start_point)"
                    >
                      <span slot="suffix">mm</span>
                    </el-input>
                  </el-form-item>

                  <el-form-item 
                    label="顶进延时"
                    prop="ejector_delay"
                  >
                    <el-input 
                      v-model="record_detail.ejector_setting.ejector_delay" 
                      type="number" 
                      @input="record_detail.ejector_setting.ejector_delay=checkNumberFormat(record_detail.ejector_setting.ejector_delay)"
                    >
                      <span slot="suffix">s</span>
                    </el-input>
                  </el-form-item>

                  <el-form-item 
                    label="保持时间"
                    prop="ejector_keep"
                  >
                    <el-input 
                      v-model="record_detail.ejector_setting.ejector_keep" 
                      type="number" 
                      @input="record_detail.ejector_setting.ejector_keep=checkNumberFormat(record_detail.ejector_setting.ejector_keep)"
                    >
                      <span slot="suffix">s</span>
                    </el-input>
                  </el-form-item>

                  <el-form-item 
                    label="中间时间"
                    prop="ejector_pause"
                  >
                    <el-input
                      v-model="record_detail.ejector_setting.ejector_pause"
                      type="number" 
                      @input="record_detail.ejector_setting.ejector_pause=checkNumberFormat(record_detail.ejector_setting.ejector_pause)"
                    >
                      <span slot="suffix">s</span>
                    </el-input>
                  </el-form-item>

                  <el-form-item 
                    label="吹气时间"
                    prop="ejector_blow_time"
                  >
                    <el-input 
                      v-model="record_detail.ejector_setting.ejector_blow_time" 
                      type="number" 
                      @input="record_detail.ejector_setting.ejector_blow_time=checkNumberFormat(record_detail.ejector_setting.ejector_blow_time)"
                    >
                      <span slot="suffix">s</span>
                    </el-input>
                  </el-form-item>
                  
                  <el-form-item 
                    label="顶针模式"
                    prop="ejector_mode"
                  >
                    <el-select v-model="record_detail.ejector_setting.ejector_mode">
                      <el-option label="不用" value="不用"></el-option>
                      <el-option label="连续" value="连续"></el-option>
                      <el-option label="开模完成顶出" value="开模完成顶出"></el-option>
                      <el-option label="中途顶出" value="中途顶出"></el-option>
                      <el-option label="震动" value="震动"></el-option>
                    </el-select>
                  </el-form-item>

                  <el-form-item 
                    label="顶出次数"
                    prop="ejector_times"
                  >
                    <el-input 
                      v-model="record_detail.ejector_setting.ejector_times" 
                      type="number"
                      @input="record_detail.ejector_setting.ejector_times=checkNumberFormat(record_detail.ejector_setting.ejector_times)"
                    >
                      <span slot="suffix">次</span>
                    </el-input>
                  </el-form-item>

                  <el-form-item 
                    label="顶出行程"
                    prop="ejector_stroke"
                  >
                    <el-input 
                      v-model="record_detail.ejector_setting.ejector_stroke" 
                      type="number"
                      @input="record_detail.ejector_setting.ejector_stroke=checkNumberFormat(record_detail.ejector_setting.ejector_stroke)"
                    >
                      <span slot="suffix">mm</span>
                    </el-input>
                  </el-form-item>

                  <el-form-item 
                    label="开模中推顶"
                    prop="ejector_on_opening"
                  >
                    <el-radio v-model="record_detail.ejector_setting.ejector_on_opening" label="开">开</el-radio>
                    <el-radio v-model="record_detail.ejector_setting.ejector_on_opening" label="关">关</el-radio>
                  </el-form-item>

                  <el-form-item 
                    label="推顶力"
                    prop="ejector_force"
                  >
                    <el-input 
                      v-model="record_detail.ejector_setting.ejector_force" 
                      type="number"
                      @input="record_detail.ejector_setting.ejector_force=checkNumberFormat(record_detail.ejector_setting.ejector_force)"
                    >
                      <span slot="suffix">{{ machine_info.oc_pressure_unit }}</span>
                    </el-input>
                  </el-form-item>

                  <el-form-item 
                    label="监视扭矩"
                    prop="set_torque"
                  >
                    <el-input 
                      v-model="record_detail.ejector_setting.set_torque" 
                      type="number"
                      @input="record_detail.ejector_setting.set_torque=checkNumberFormat(record_detail.ejector_setting.set_torque)"
                    >
                      <span slot="suffix">N·m</span>
                    </el-input>
                  </el-form-item>
                </el-form>
              </el-card> 
            </el-col>
            <el-col :xs="24" :lg="16" :xl="18">
              <el-card class="boc-card" style="min-width:800px">
                <el-table
                  size="mini"
                  :data="record_detail.ejector_setting.ejector_backward.table_data"
                  :key="Math.random()"
                >
                  <el-table-column 
                    label="顶针后退" 
                    width="80" 
                    align="center"
                  >
                    <template slot="header">
                      <div>后退段数</div>
                      <el-select
                        v-model="record_detail.ejector_setting.ejector_backward.ejector_backward_stage"
                        size="mini"
                      >
                        <el-option
                          v-for="(option, idx) in record_detail.ejector_setting.ejector_backward.max_ejector_backward_stage_option"
                          :key="idx"
                          :label="option"
                          :value="option"
                        ></el-option>
                      </el-select>
                    </template>
                    <template slot-scope="scope">
                      {{ scope.row.label }}
                    </template>
                  </el-table-column>
                    
                  <template v-for="(col, colidx) in record_detail.ejector_setting.ejector_backward.max_ejector_backward_stage_option">
                    <el-table-column
                      min-width="80"
                      align="center"
                      :key="colidx"
                      :label="ejector_backward_header[col]"
                    >
                      <template slot-scope="scope">
                        <el-input
                          :id="components_view_id.ejector_backward.table[scope.$index][colidx]"
                          v-model="record_detail.ejector_setting.ejector_backward.table_data[scope.$index].sections[colidx]"
                          :disabled="colidx >= record_detail.ejector_setting.ejector_backward.ejector_backward_stage"
                          type="number"
                          min="0"
                          size="mini"
                          @input="record_detail.ejector_setting.ejector_backward.table_data[scope.$index].sections[colidx]=checkNumberFormat(record_detail.ejector_setting.ejector_backward.table_data[scope.$index].sections[colidx])"
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
                      {{ record_detail.ejector_setting.ejector_backward.table_data[scope.$index].unit }}
                    </template>
                  </el-table-column>
                </el-table>

                <div style="height: 60px" />

                <el-table
                  size="mini"
                  :data="record_detail.ejector_setting.ejector_forward.table_data"
                  :key="Math.random()"
                >
                  <el-table-column 
                    label="顶针前进" 
                    width="80" 
                    align="center"
                  >
                    <template slot="header">
                      <div>前进段数</div>
                      <el-select
                        v-model="record_detail.ejector_setting.ejector_forward.ejector_forward_stage"
                        size="mini"
                      >
                        <el-option
                          v-for="(option, idx) in record_detail.ejector_setting.ejector_forward.max_ejector_forward_stage_option"
                          :key="idx"
                          :label="option"
                          :value="option"
                        ></el-option>
                      </el-select>
                    </template>
                    <template slot-scope="scope">
                      {{ scope.row.label }}
                    </template>
                  </el-table-column>

                  <template 
                    v-for="(col, colidx) in record_detail.ejector_setting.ejector_forward.max_ejector_forward_stage_option"
                  >
                    <el-table-column
                      :key="colidx"
                      :label="ejector_forward_header[col]"
                      min-width="80"
                      align="center"
                    >
                      <template slot-scope="scope">
                        <el-input
                          :id="components_view_id.ejector_forward.table[scope.$index][colidx]"
                          v-model="record_detail.ejector_setting.ejector_forward.table_data[scope.$index].sections[colidx]"
                          :disabled="colidx >= record_detail.ejector_setting.ejector_forward.ejector_forward_stage"
                          type="number"
                          min="0"
                          size="mini"
                          @input="record_detail.ejector_setting.ejector_forward.table_data[scope.$index].sections[colidx]=checkNumberFormat(record_detail.ejector_setting.ejector_forward.table_data[scope.$index].sections[colidx])"
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
                      {{ record_detail.ejector_setting.ejector_forward.table_data[scope.$index].unit }}
                    </template>
                  </el-table-column>
                </el-table>
                
                <div style="height: 72px" />
              </el-card>
            </el-col>
          </el-row>
        </el-collapse-item>      
      </el-collapse>
    </el-form>
  </div>
</template>

<script>
import { initArray } from "@/utils/array-help";

export default {
  name: "ProcessRecordForm",
  props: {
    machineInfo: {
      type: Object,
      default: () => ({ 
        pressure_unit: "MPa",
        oc_pressure_unit: "MPa",
        oc_velocity_unit: "mm/s",
        position_unit: "mm",
        power_unit: "KW",
        temperature_unit: "℃",
        velocity_unit: "mm/s",
        time_unit: "s",
        clamping_force_unit: "Ton",
        screw_rotation_unit: "rpm",
      })
    },
    recordDetail: {
      type: Object,
      default: () => ({ 
        title: "射台 #1", 
        name: "1",
        inject_para: {
          injection_stage: 4,
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
          holding_stage: 3,
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
          metering_stage: 1,
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
        // loose_core: {
        //   core_movement_method: null,
        //   table_data: initArray(2, {
        //     core_switch_selection: null,
        //     core_mold_clamping_method: null,
        //     core_mold_opening_method: null,
        //     set_core_in_time: null,
        //     set_core_out_time: null,
        //     core_in_position: null,
        //     core_out_position: null,
        //   })
        // },
      })
    },
    viewIndex: {
      type: Number,
      default: null
    }
  },
  data() {
    return {
      record_detail: this.recordDetail,
      machine_info: this.machineInfo,
      activeNames: ['1'],
      injection_stage_header: [ "注射段数", "一段", "二段", "三段", "四段", "五段", "六段" ],
      holding_stage_header: [ "保压段数", "一段", "二段", "三段", "四段", "五段" ],
      metering_stage_header: [ "计量段数", "一段", "二段", "三段", "四段" ],
      temp_stage_header: [ "温度段数", "喷嘴", "一段", "二段", "三段", "四段", "五段", "六段", "七段", "八段", "九段" ],
      ejector_backward_header: ["顶针后退段数","一段  -->","二段  -->","三段  -->","四段  -->","五段  -->","六段  -->","七段  -->","八段",],
      ejector_forward_header: ["顶针前进段数","一段  -->","二段  -->","三段  -->","四段  -->","五段  -->","六段  -->","七段  -->","八段",],
      mold_opening_stage_header: ["开模段数","一段  -->","二段  -->","三段  -->","四段  -->","五段  -->","六段  -->","七段  -->","八段",],
      mold_clamping_stage_header: ["合模段数","一段  -->","二段  -->","三段  -->","四段  -->","五段  -->","六段  -->","七段  -->","八段",],
      VP_switch_mode_options: [
        { label: "位置", value: "位置" },
        { label: "时间", value: "时间" },
        { label: "时间&位置", value: "时间&位置" },
        { label: "压力", value: "压力" },
        { label: "速度", value: "速度" }
      ],
      decompressure_mode_options: [
        { label: "否", value: "否" },
        { label: "距离", value: "距离" },
        { label: "时间", value: "时间" },
      ],
      components_view_id: {
        inject_para: {
          table: [
            [ "IP0", "IP1", "IP2", "IP3", "IP4", "IP5" ],
            [ "IV0", "IV1", "IV2", "IV3", "IV4", "IV5" ],
            [ "IL0", "IL1", "IL2", "IL3", "IL4", "IL5" ]
          ],
          inj_time: "IT",
          inj_delay: "ID",
          cool_time: "CT"
        },
        holding_para: {
          table: [
            [ "PP0", "PP1", "PP2", "PP3", "PP4" ],
            [ "PV0", "PV1", "PV2", "PV3", "PV4" ],
            [ "PT0", "PT1", "PT2", "PT3", "PT4" ]
          ]
        },
        VP_switch: {
          mode: "VPTM",
          time: "VPTT",
          position: "VPTL",
          pressure: "VPTP",
          velocity: "VPTV",
        },
        metering_para: {
          table: [
            [ "MP0", "MP1", "MP2", "MP3" ],
            [ "MSR0", "MSR1", "MSR2", "MSR3" ],
            [ "MBP0", "MBP1", "MBP2", "MBP3" ],
            [ "ML0", "ML1", "ML2", "ML3" ]
          ],
          dec_mode_bef: "DMBM",
          dec_mode_aft: "DMAM",
          deco_table: [
            [ "DPBM", "DVBM", "DDBM", "DTBM" ],
            [ "DPAM", "DVAM", "DDAM", "DTAM" ]
          ],
          measureDelay: "MD",
          stopPos: "MEL"
        },
        temp_para: {
          table: [
            [ "NT", "BT1", "BT2", "BT3", "BT4", "BT5", "BT6", "BT7", "BT8", "BT9"  ]
          ]
        },
        mold_opening: {
          table: [
            [ "MOPR0", "MOPR1", "MOPR2", "MOPR3", "MOPR4", "MOPR5", "MOPR6", "MOPR7" ],
            [ "MOS0", "MOS1", "MOS2", "MOS3", "MOS4", "MOS5", "MOS6", "MOS7" ],
            [ "MOP0", "MOP1", "MOP2", "MOP3", "MOP4", "MOP5", "MOP6", "MOP7" ],
          ]
        },
        mold_clamping: {
          table: [
            [ "MCPR0", "MCPR1", "MCPR2", "MCPR3", "MCPR4", "MCPR5", "MCPR6", "MCPR7" ],
            [ "MCS0", "MCS1", "MCS2", "MCS3", "MCS4", "MCS5", "MCS6", "MCS7" ],
            [ "MCP0", "MCP1", "MCP2", "MCP3", "MCP4", "MCP5", "MCP6", "MCP7" ],
          ]
        },
        ejector_backward: {
          table: [
            [ "EBPR0", "EBPR1", "EBPR2", "EBPR3", "EBPR4", "EBPR5", "EBPR6", "EBPR7" ],
            [ "EBS0", "EBS1", "EBS2", "EBS3", "EBS4", "EBS5", "EBS6", "EBS7" ],
            [ "EBP0", "EBP1", "EBP2", "EBP3", "EBP4", "EBP5", "EBP6", "EBP7" ],
          ]
        },
        ejector_forward: {
          table: [
            [ "EFPR0", "EFPR1", "EFPR2", "EFPR3", "EFPR4", "EFPR5", "EFPR6", "EFPR7" ],
            [ "EFS0", "EFS1", "EFS2", "EFS3", "EFS4", "EFS5", "EFS6", "EFS7" ],
            [ "EFP0", "EFP1", "EFP2", "EFP3", "EFP4", "EFP5", "EFP6", "EFP7" ],
          ]
        }
      },
    }
  },
  created() {
  },
  mounted() {
  },
  methods: {
    setViewUnit() {
      this.record_detail.inject_para.table_data[0].unit = this.machine_info.pressure_unit
      this.record_detail.inject_para.table_data[1].unit = this.machine_info.velocity_unit
      this.record_detail.inject_para.table_data[2].unit = this.machine_info.position_unit

      this.record_detail.holding_para.table_data[0].unit = this.machine_info.pressure_unit
      this.record_detail.holding_para.table_data[1].unit = this.machine_info.velocity_unit
      this.record_detail.holding_para.table_data[2].unit = this.machine_info.time_unit

      this.record_detail.metering_para.table_data[0].unit = this.machine_info.pressure_unit
      this.record_detail.metering_para.table_data[1].unit = this.machine_info.screw_rotation_unit
      this.record_detail.metering_para.table_data[2].unit = this.machine_info.backpressure_unit
      this.record_detail.metering_para.table_data[3].unit = this.machine_info.position_unit

      this.record_detail.temp_para.table_data[0].unit = this.machine_info.temperature_unit

      // 顶针单位
      if(this.record_detail.ejector_setting){

        this.record_detail.ejector_setting.ejector_backward.table_data[0].unit = this.machine_info.oc_pressure_unit
        this.record_detail.ejector_setting.ejector_forward.table_data[0].unit = this.machine_info.oc_pressure_unit
        this.record_detail.ejector_setting.ejector_backward.table_data[1].unit = this.machine_info.oc_velocity_unit
        this.record_detail.ejector_setting.ejector_forward.table_data[1].unit = this.machine_info.oc_velocity_unit
      }
      if(this.record_detail.opening_and_clamping_mold_setting){

        //开合模单位
        this.record_detail.opening_and_clamping_mold_setting.mold_opening.table_data[0].unit = this.machine_info.oc_pressure_unit
        this.record_detail.opening_and_clamping_mold_setting.mold_clamping.table_data[0].unit = this.machine_info.oc_pressure_unit
        this.record_detail.opening_and_clamping_mold_setting.mold_opening.table_data[1].unit = this.machine_info.oc_velocity_unit
        this.record_detail.opening_and_clamping_mold_setting.mold_clamping.table_data[1].unit = this.machine_info.oc_velocity_unit
      }
    }
  },
  watch: {
    recordDetail: function() {
      this.record_detail = this.recordDetail
    },
    machineInfo: {
      handler: function() {
        this.machine_info = this.machineInfo
        this.setViewUnit()
      },
      deep: true
    },
    "record_detail.inject_para.injection_stage": function() {
      for (let i = this.record_detail.inject_para.injection_stage; i < 6; ++i) {
        this.record_detail.inject_para.table_data[0].sections[i] = null
        this.record_detail.inject_para.table_data[1].sections[i] = null
        this.record_detail.inject_para.table_data[2].sections[i] = null
      }
    },
    "record_detail.holding_para.holding_stage": function() {
      for (let i = this.record_detail.holding_para.holding_stage; i < 5; ++i) {
        this.record_detail.holding_para.table_data[0].sections[i] = null
        this.record_detail.holding_para.table_data[1].sections[i] = null
        this.record_detail.holding_para.table_data[2].sections[i] = null
      }
    },
    "record_detail.metering_para.metering_stage": function() {
      for (let i = this.record_detail.metering_para.metering_stage; i < 4; ++i) {
        this.record_detail.metering_para.table_data[0].sections[i] = null
        this.record_detail.metering_para.table_data[1].sections[i] = null
        this.record_detail.metering_para.table_data[2].sections[i] = null
        this.record_detail.metering_para.table_data[3].sections[i] = null
      }
    },
    "record_detail.temp_para.barrel_temperature_stage": function() {
      for (let i = this.record_detail.temp_para.barrel_temperature_stage; i < 10; ++i) {
        this.record_detail.temp_para.table_data[0].sections[i] = null
      }
    },
    "record_detail.VP_switch.VP_switch_position": function() {
      // 注射最后一段的位置等于VP切换位置
      let inject_stage = this.record_detail.inject_para.injection_stage
      let inject_para_table = this.record_detail.inject_para.table_data
      inject_para_table[2].sections[inject_stage - 1] = this.record_detail.VP_switch.VP_switch_position
    },
    "record_detail.metering_para.metering_ending_position": function() {
      // 螺杆终止位置等于计量最后一段位置+储料射退距离
      let metering_stage = this.record_detail.metering_para.metering_stage
      let metering_para_table = this.record_detail.metering_para.table_data
      let metering_para_deco_table = this.record_detail.metering_para.decompressure_paras
      let deco_mode_bef_metering = this.record_detail.metering_para.decompressure_mode_before_metering
      let deco_mode_aft_metering = this.record_detail.metering_para.decompressure_mode_after_metering

      let metering_end_posi = this.record_detail.metering_para.metering_ending_position
      if (metering_end_posi && deco_mode_bef_metering === "距离") {
        metering_end_posi = (Number(metering_end_posi) - Number(metering_para_deco_table[0].distance)).toFixed(2)
      }
      if (metering_end_posi && deco_mode_aft_metering === "距离") {
        metering_end_posi = (Number(metering_end_posi) - Number(metering_para_deco_table[1].distance)).toFixed(2)
      }
      if (Number(metering_end_posi) > 0) {
        metering_para_table[3].sections[metering_stage - 1] = Number(metering_end_posi).toFixed(2)
      }
    }
  }
}
</script>

<style lang="scss" scoped>
  .el-divider {
    margin: 15px 0 20px 0;
    span {
      color: blue;
      font-size: 15px;
    }
  }
</style>
