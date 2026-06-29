<template>
  <div ref="processOtimize">
    <el-row>
      <el-form 
        size="mini" 
        label-width="6rem"
        label-position="right"
        :inline="true"
      >
        <el-col :xs="24" :lg="13" :xl="13">
          <el-card class="box-card" style="min-height:240px">
            <el-table 
              size="mini"
              :data="optimize_detail.process_detail.inject_para.table_data" 
              :key="optimize_detail.process_detail.inject_para.injection_stage + 20 + String(viewIndex)"
            >
              <el-table-column 
                label="工艺参数"
                width="80" 
                align="center"
              >
                <template slot="header">
                  <div>注射段数</div>
                  <el-select 
                    v-model="optimize_detail.process_detail.inject_para.injection_stage" 
                    size="mini"
                  >
                    <el-option
                      v-for="option, idx in optimize_detail.process_detail.inject_para.max_injection_stage_option"
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
                v-for="(col, colidx) in optimize_detail.process_detail.inject_para.max_injection_stage_option"
              >
                <el-table-column
                  min-width="80"
                  align="center"
                  :key="colidx"
                  :label="injection_stage_header[col]"
                >
                  <template slot-scope="scope">
                    <el-input
                      :id="components_view_id.inject_para.table[scope.$index][colidx] + viewIndex"
                      v-model="optimize_detail.process_detail.inject_para.table_data[scope.$index].sections[colidx]" 
                      type="number" 
                      min="0" 
                      size="mini"
                      :disabled="colidx >=optimize_detail.process_detail.inject_para.injection_stage"
                      @input="optimize_detail.process_detail.inject_para.table_data[scope.$index].sections[colidx]=checkNumberFormat(optimize_detail.process_detail.inject_para.table_data[scope.$index].sections[colidx])"
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
                  {{ optimize_detail.process_detail.inject_para.table_data[scope.$index].unit }}
                </template>
              </el-table-column>
            </el-table>
          </el-card>
          <el-card class="box-card" style="min-height:240px">
            <el-form-item label="注射时间">
              <el-input
                :id="components_view_id.inject_para.inj_time + viewIndex"
                type="text"
                v-model="optimize_detail.process_detail.inject_para.injection_time"
                style="width: 7rem"
                @input="optimize_detail.process_detail.inject_para.injection_time=checkNumberFormat(optimize_detail.process_detail.inject_para.injection_time)"
              >
                <span slot="suffix">{{ mac_unit.time_unit }}</span>
              </el-input>
            </el-form-item>
            <el-form-item label="注射延迟">
              <el-input
                :id="components_view_id.inject_para.inj_delay + viewIndex"
                type="text"
                v-model="optimize_detail.process_detail.inject_para.injection_delay_time"
                style="width: 7rem"
                @input="optimize_detail.process_detail.inject_para.injection_delay_time=checkNumberFormat(optimize_detail.process_detail.inject_para.injection_delay_time)"
              >
                <span slot="suffix">{{ mac_unit.time_unit }}</span>
              </el-input>
            </el-form-item>
            <el-form-item label="冷却时间">
              <el-input
                :id="components_view_id.inject_para.cool_time + viewIndex"
                type="text"
                v-model="optimize_detail.process_detail.inject_para.cooling_time"
                style="width: 7rem"
                @input="optimize_detail.process_detail.inject_para.cooling_time=checkNumberFormat(optimize_detail.process_detail.inject_para.cooling_time)"
              >
                <span slot="suffix">{{ mac_unit.time_unit }}</span>
              </el-input>
            </el-form-item>
            <el-divider content-position="center"><span style="color:blue">VP切换</span></el-divider>
            <el-form-item label="切换方式">
              <el-select
                :id="components_view_id.VP_switch.mode + viewIndex"
                v-model="optimize_detail.process_detail.VP_switch.VP_switch_mode"
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
                :id="components_view_id.VP_switch.time + viewIndex"
                type="text"
                v-model="optimize_detail.process_detail.VP_switch.VP_switch_time" 
                style="width: 7rem"
                :disabled="optimize_detail.process_detail.VP_switch.VP_switch_mode == null
                  ||optimize_detail.process_detail.VP_switch.VP_switch_mode.indexOf('时间') == -1"
                @input="optimize_detail.process_detail.VP_switch.VP_switch_time=checkNumberFormat(optimize_detail.process_detail.VP_switch.VP_switch_time)"
              >
                <span slot="suffix">{{ mac_unit.time_unit }}</span>
              </el-input>
            </el-form-item>
            <el-form-item label="切换位置">
              <el-input
                :id="components_view_id.VP_switch.position + viewIndex"
                type="text"
                v-model="optimize_detail.process_detail.VP_switch.VP_switch_position" 
                style="width: 7rem"
                :disabled="optimize_detail.process_detail.VP_switch.VP_switch_mode == null
                  ||optimize_detail.process_detail.VP_switch.VP_switch_mode.indexOf('位置') == -1"
                @input="optimize_detail.process_detail.VP_switch.VP_switch_position=checkNumberFormat(optimize_detail.process_detail.VP_switch.VP_switch_position)"
              >
                <span slot="suffix">{{ mac_unit.position_unit }}</span>
              </el-input>
            </el-form-item>
            <el-form-item label="切换压力">
              <el-input
                :id="components_view_id.VP_switch.pressure + viewIndex"
                type="text"
                v-model="optimize_detail.process_detail.VP_switch.VP_switch_pressure" 
                style="width: 7rem"
                :disabled="optimize_detail.process_detail.VP_switch.VP_switch_mode == null
                  ||optimize_detail.process_detail.VP_switch.VP_switch_mode.indexOf('压力') == -1"
                @input="optimize_detail.process_detail.VP_switch.VP_switch_pressure=checkNumberFormat(optimize_detail.process_detail.VP_switch.VP_switch_pressure)"
              >
                <span slot="suffix">{{ mac_unit.pressure_unit }}</span>
              </el-input>
            </el-form-item>
            <el-form-item label="切换速度">
              <el-input
                :id="components_view_id.VP_switch.velocity + viewIndex"
                type="text"
                v-model="optimize_detail.process_detail.VP_switch.VP_switch_velocity" 
                style="width: 7rem"
                :disabled="optimize_detail.process_detail.VP_switch.VP_switch_mode == null
                  ||optimize_detail.process_detail.VP_switch.VP_switch_mode.indexOf('速度') == -1"
                @input="optimize_detail.process_detail.VP_switch.VP_switch_velocity=checkNumberFormat(optimize_detail.process_detail.VP_switch.VP_switch_velocity)"
              >
                <span slot="suffix">{{ mac_unit.velocity_unit }}</span>
              </el-input>
            </el-form-item>
          </el-card>
          <el-card class="box-card" style="min-height:240px">
            <el-table 
              size="mini"
              :data="optimize_detail.process_detail.holding_para.table_data" 
              :key="optimize_detail.process_detail.holding_para.holding_stage + 40 + String(viewIndex)"
            >
              <el-table-column 
                label="工艺参数"
                width="80" 
                align="center"
              >
                <template slot="header">
                  <div>保压段数</div>
                  <el-select 
                    v-model="optimize_detail.process_detail.holding_para.holding_stage" 
                    size="mini"
                  >
                    <el-option
                      v-for="option, idx in optimize_detail.process_detail.holding_para.max_holding_stage_option"
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
              <template v-for="(col, colidx) in optimize_detail.process_detail.holding_para.max_holding_stage_option">
                <el-table-column
                  :key="colidx"
                  :label="holding_stage_header[col]"
                  min-width="80"
                  align="center"
                >
                  <template slot-scope="scope">
                    <el-input
                      :id="components_view_id.holding_para.table[scope.$index][colidx] + viewIndex"
                      v-model="optimize_detail.process_detail.holding_para.table_data[scope.$index].sections[colidx]" 
                      :disabled="colidx >=optimize_detail.process_detail.holding_para.holding_stage"
                      type="number" 
                      min="0" 
                      size="mini"
                      @input="optimize_detail.process_detail.holding_para.table_data[scope.$index].sections[colidx]=checkNumberFormat(optimize_detail.process_detail.holding_para.table_data[scope.$index].sections[colidx])"
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
                  {{ optimize_detail.process_detail.holding_para.table_data[scope.$index].unit }}
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-col>
        <el-col :xs="24" :lg="11" :xl="11">
          <el-card class="box-card" style="min-height:720px">
            <el-table 
              size="mini"
              :data="optimize_detail.process_detail.metering_para.table_data"
              :key="optimize_detail.process_detail.metering_para.metering_stage + 60 + String(viewIndex)"
            >
              <el-table-column 
                label="工艺参数"
                width="80" 
                align="center"
              >
                <template slot="header">
                  <div>计量段数</div>
                  <el-select 
                    v-model="optimize_detail.process_detail.metering_para.metering_stage" 
                    size="mini"
                  >
                    <el-option
                      v-for="option, idx in optimize_detail.process_detail.metering_para.max_metering_stage_option"
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
              <template v-for="(col, colidx) in optimize_detail.process_detail.metering_para.max_metering_stage_option">
                <el-table-column
                  :key="colidx"
                  :label="metering_stage_header[col]"
                  min-width="80"
                  align="center"
                >
                  <template slot-scope="scope">
                    <el-input 
                      :id="components_view_id.metering_para.table[scope.$index][colidx] + viewIndex"
                      v-model="optimize_detail.process_detail.metering_para.table_data[scope.$index].sections[colidx]" 
                      :disabled="colidx >=optimize_detail.process_detail.metering_para.metering_stage"
                      type="number" 
                      min="0" 
                      size="mini"
                      @input="optimize_detail.process_detail.metering_para.table_data[scope.$index].sections[colidx]=checkNumberFormat(optimize_detail.process_detail.metering_para.table_data[scope.$index].sections[colidx])"
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
                  {{ optimize_detail.process_detail.metering_para.table_data[scope.$index].unit }}
                </template>
              </el-table-column>
            </el-table>
            <div style="height:15px" />
            <el-form-item label="储前松退模式">
              <el-select 
                :id="components_view_id.metering_para.dec_mode_bef + viewIndex"
                v-model="optimize_detail.process_detail.metering_para.decompressure_mode_before_metering"
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
                :id="components_view_id.metering_para.dec_mode_aft + viewIndex"
                v-model="optimize_detail.process_detail.metering_para.decompressure_mode_after_metering"
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
              :data="optimize_detail.process_detail.metering_para.decompressure_paras"
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
                  <div>{{ mac_unit.pressure_unit }}</div>
                </template>
                <template slot-scope="scope">
                  <el-input
                    :id="components_view_id.metering_para.deco_table[scope.$index][0] + viewIndex"
                    :disabled="((scope.$index === 0 &&optimize_detail.process_detail.metering_para.decompressure_mode_before_metering === '否')
                      || (scope.$index === 1 &&optimize_detail.process_detail.metering_para.decompressure_mode_after_metering === '否'))"
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
                  <div>{{ mac_unit.velocity_unit }}</div>
                </template>
                <template slot-scope="scope">
                  <el-input
                    :id="components_view_id.metering_para.deco_table[scope.$index][1] + viewIndex"
                    :disabled="((scope.$index === 0 &&optimize_detail.process_detail.metering_para.decompressure_mode_before_metering === '否')
                      || (scope.$index === 1 &&optimize_detail.process_detail.metering_para.decompressure_mode_after_metering === '否'))"
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
                  <div>{{ mac_unit.position_unit }}</div>
                </template>
                <template slot-scope="scope">
                  <el-input
                    :id="components_view_id.metering_para.deco_table[scope.$index][2] + viewIndex"
                    :disabled="((scope.$index === 0 &&optimize_detail.process_detail.metering_para.decompressure_mode_before_metering != '距离')
                      || (scope.$index === 1 &&optimize_detail.process_detail.metering_para.decompressure_mode_after_metering != '距离'))"
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
                  <div>{{ mac_unit.time_unit }}</div>
                </template>
                <template slot-scope="scope">
                  <el-input
                    :id="components_view_id.metering_para.deco_table[scope.$index][3] + viewIndex"
                    :disabled="((scope.$index === 0 &&optimize_detail.process_detail.metering_para.decompressure_mode_before_metering != '时间')
                      || (scope.$index === 1 &&optimize_detail.process_detail.metering_para.decompressure_mode_after_metering != '时间'))"
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
                :id="components_view_id.metering_para.measureDelay + viewIndex"
                type="number"
                v-model="optimize_detail.process_detail.metering_para.metering_delay_time"
                style="width: 8rem"
                @input="optimize_detail.process_detail.metering_para.metering_delay_time=checkNumberFormat(optimize_detail.process_detail.metering_para.metering_delay_time)"
              >
                <span slot="suffix">{{ mac_unit.time_unit }}</span>
              </el-input>
            </el-form-item>
            <br>
            <el-form-item label="终止位置">
              <el-input
                :id="components_view_id.metering_para.stopPos + viewIndex"
                type="number"
                v-model="optimize_detail.process_detail.metering_para.metering_ending_position"
                style="width: 8rem"
                @input="optimize_detail.process_detail.metering_para.metering_ending_position=checkNumberFormat(optimize_detail.process_detail.metering_para.metering_ending_position)"
              >
                <span slot="suffix">{{ mac_unit.position_unit }}</span>
              </el-input>
            </el-form-item>
          </el-card>
        </el-col>
        <el-col :xs="24" :lg="24" :xl="24">
          <el-card class="box-card">
            <el-table 
              size="mini"
              :data="optimize_detail.process_detail.temp_para.table_data"
              :key="optimize_detail.process_detail.temp_para.barrel_temperature_stage + 80 + String(viewIndex)"
            >
              <el-table-column 
                label="工艺参数"
                width="80" 
                align="center"
              >
                <template slot="header">
                  <div>温度段数</div>
                  <el-select 
                    v-model="optimize_detail.process_detail.temp_para.barrel_temperature_stage" 
                    size="mini"
                  >
                    <el-option
                      v-for="option, idx in optimize_detail.process_detail.temp_para.max_barrel_temperature_stage_option"
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
              <template v-for="(col, colidx) in optimize_detail.process_detail.temp_para.max_barrel_temperature_stage_option">
                <el-table-column
                  :key="colidx"
                  :label="temp_stage_header[col]"
                  min-width="80"
                  align="center"
                >
                  <template slot-scope="scope">
                    <el-input 
                      :id="components_view_id.temp_para.table[scope.$index][colidx] + viewIndex"
                      v-model="optimize_detail.process_detail.temp_para.table_data[scope.$index].sections[colidx]" 
                      :disabled="colidx >=optimize_detail.process_detail.temp_para.barrel_temperature_stage"
                      type="number" 
                      min="0" 
                      size="mini"
                      @input="optimize_detail.process_detail.temp_para.table_data[scope.$index].sections[colidx]=checkNumberFormat(optimize_detail.process_detail.temp_para.table_data[scope.$index].sections[colidx])"
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
                  {{ optimize_detail.process_detail.temp_para.table_data[scope.$index].unit }}
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-col>
      </el-form>
    </el-row>

    <el-row v-if="precondition_detail.runner_type=='热流道' && precondition_detail.hot_runner_num">
      <el-card class="box-card">
        <div slot="header" class="clearfix">
          <span>热流道温度</span>
        </div>        
        <el-form
          class="defect-feedback"
          :inline="true"  
          :model="optimize_detail.auxiliary_detail" 
          size="mini" 
          label-width="6rem"
        >
          <el-form-item
            v-for="(item, index) in Number(precondition_detail.hot_runner_num)"
            :key="index"
            :label="'R' + item"
          >
            <el-input
              :id="components_view_id.auxiliary_detail.hot_runner_temps[index] + viewIndex"
              type="number"
              v-model="optimize_detail.auxiliary_detail.hot_runner_temperatures[index]"
              @input="
                optimize_detail.auxiliary_detail.hot_runner_temperatures[index] = checkNumberFormat(
                  optimize_detail.auxiliary_detail.hot_runner_temperatures[index]
                )
              "
            >
              <span slot="suffix">℃</span>
            </el-input>
          </el-form-item>
        </el-form>
      </el-card>
    </el-row>
    <el-row v-if="precondition_detail.valve_num && precondition_detail.valve_num > 1 && false">
      <el-card class="box-card">
        <div slot="header" class="clearfix">
          <span>热流道时序控制</span>
        </div>
        
        <el-form
          class="defect-feedback"
          :inline="true" 
          :model="optimize_detail.auxiliary_detail" 
          size="mini" 
          label-width="6rem"
        >
          <el-form-item 
            v-for="idx in precondition_detail.valve_num"
            :key="idx"
            :label="'阀口' + String(idx)" 
            label-width="6rem"
          >
            <el-input 
            :id="components_view_id.auxiliary_detail.hot_runner_times[Number(idx)-1] + viewIndex"
              v-model="optimize_detail.auxiliary_detail.hot_runner.sequential_ctrl_time[Number(idx)-1]" 
              style="width:8rem"
              @input="optimize_detail.auxiliary_detail.hot_runner.sequential_ctrl_time[Number(idx)-1]=checkNumberFormat(optimize_detail.auxiliary_detail.hot_runner.sequential_ctrl_time[Number(idx)-1])"
            >
              <span slot="suffix">s</span>
            </el-input>
          </el-form-item>
        </el-form>
      </el-card>
    </el-row>

    <el-row>
      <el-card class="box-card">
        <div slot="header" class="clearfix">
          <span>模温机控制</span>
        </div>
        
        <el-form
          class="defect-feedback"
          :inline="true" 
          :model="optimize_detail.auxiliary_detail" 
          size="mini" 
          label-width="6rem"
        >
          <el-form-item label="模温机个数" prop="mold_temp_num">
            <el-select v-model="optimize_detail.auxiliary_detail.mold_temp.mold_temp_num">
              <el-option
                v-for="(option, index) in 20"
                :key="index"
                :label="option"
                :value="option"
              >
              </el-option>
            </el-select>
          </el-form-item>
          <br>

          <el-form-item
            v-for="(temp, idx) in moldTempList"
            :key="idx"
            :label="'模温机' + String(idx + 1)"
            label-width="6rem"
          >
            <el-input
              :id="components_view_id.auxiliary_detail.mold_temp_list[idx] + viewIndex"
              v-model="optimize_detail.auxiliary_detail.mold_temp.mold_temp_list[idx]" 
              @input="optimize_detail.auxiliary_detail.mold_temp.mold_temp_list[idx]=checkNumberFormat(optimize_detail.auxiliary_detail.mold_temp.mold_temp_list[idx])"
              style="width:8rem"
            >
              <span slot="suffix">℃</span>
            </el-input>
          </el-form-item> 
        </el-form>
      </el-card>
    </el-row>

    <el-row>
      <el-card class="box-card">
        <div slot="header" class="clearfix">
          <span>缺陷反馈</span>
        </div>

        <el-form
          class="defect-feedback"
          :inline="true" 
          :model="optimize_detail.feedback_detail" 
          size="mini" 
          label-width="6rem"
        >
          <el-form-item 
            label="制品实际重量" 
            label-width="6rem"
          >
            <el-input 
              v-model="optimize_detail.feedback_detail.actual_product_weight" style="width:8rem"
              @input="optimize_detail.feedback_detail.actual_product_weight=checkNumberFormat(optimize_detail.feedback_detail.actual_product_weight)"
            >
              <span slot="suffix">g</span>
            </el-input>
          </el-form-item>

          <br>

          <template v-for="(defect, index) in optimize_detail.feedback_detail.defect_info">
            <el-form-item :label="defect.label" :prop="defect.prop" :key="index">
              <el-select
                v-model="defect.level"
                placeholder="请选择"
              >
                <el-option
                  v-for="item in defect_level_options"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                ></el-option>
              </el-select>

              <el-select
                v-model="defect.position"
                placeholder="请选择"
                :disabled="defect.level === '无缺陷'"
              >
                <el-option
                  v-for="item in defect_position_options"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                ></el-option>
              </el-select>
              <el-select
                v-if="optimize_detail.name !== '0' && defect.feedback !== null"
                v-model="defect.feedback"
                placeholder="请选择"
              >
                <el-option
                  v-for="item in feedback_options"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                ></el-option>
              </el-select>

            </el-form-item>
          </template>
        </el-form>
      </el-card>
    </el-row>
  </div>
</template>

<script>
import { createOptimizeList } from '@/utils/process_const';

export default {
  name: "ProcessOptimizeForm",
  components: {},
  props: {
    macUnit: {
      type: Object,
      default: () => ({ 
        pressure_unit: "MPa",
        position_unit: "mm",
        power_unit: "KW",
        temperature_unit: "℃",
        velocity_unit: "mm/s",
        time_unit: "s",
        clamping_force_unit: "Ton",
        screw_rotation_unit: "rpm",
      })
    },
    optimizeDetail: {
      type: Object,
      default: () => createOptimizeList("0")
    },
    viewIndex: {
      type: Number,
      default: null
    },
    preconditionDetail: {
      type: Object,
      default: () => ({})
    }
  },
  data() {
    return {
      precondition_detail: this.preconditionDetail,
      optimize_detail: this.optimizeDetail,
      mac_unit: this.macUnit,
      injection_stage_header: [ "注射段数", "一段", "二段", "三段", "四段", "五段", "六段" ],
      holding_stage_header: [ "保压段数", "一段", "二段", "三段", "四段", "五段" ],
      metering_stage_header: [ "计量段数", "一段", "二段", "三段", "四段" ],
      temp_stage_header: [ "温度段数", "喷嘴", "一段", "二段", "三段", "四段", "五段", "六段", "七段", "八段", "九段" ],
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
        auxiliary_detail:{
          hot_runner_temps:Array.from({ length: 50 }, (_, index) => `HRT${index}`),
          hot_runner_times:Array.from({ length: 10 }, (_, index) => `SCT${index}`),
          mold_temp_list:Array.from({ length: 20 }, (_, index) => `MT${index}`),
          mold_temp: "MT"
        }
      },
      defect_level_options: [
        { label: "无缺陷", value: "无缺陷" },
        { label: "轻微", value: "轻微" },
        { label: "中等", value: "中等" },
        { label: "严重", value: "严重" },
        { label: "非常严重", value: "非常严重" },
      ],
      defect_position_options: [
        { label: "缺陷位置不指定", value: "缺陷位置不指定" },
        { label: "缺陷位置在1段", value: "缺陷位置在1段" },
        { label: "缺陷位置在2段", value: "缺陷位置在2段" },
        { label: "缺陷位置在3段", value: "缺陷位置在3段" },
        { label: "缺陷位置在4段", value: "缺陷位置在4段" },
      ],
      valve_position_options: [
        { label: "缺陷位置不指定", value: "缺陷位置不指定" },
        { label: "缺陷位置在1段", value: "缺陷位置在1段" },
        { label: "缺陷位置在2段", value: "缺陷位置在2段" },
        { label: "缺陷位置在3段", value: "缺陷位置在3段" },
        { label: "缺陷位置在4段", value: "缺陷位置在4段" },
        { label: "在第1、2个阀口间", value: "在第1、2个阀口间" },
        { label: "在第2、3个阀口间", value: "在第2、3个阀口间" },
        { label: "在第3、4个阀口间", value: "在第3、4个阀口间" },
        { label: "在第4、5个阀口间", value: "在第4、5个阀口间" },
      ],
      feedback_options: [
        { label: "上一模修正效果佳", value: "上一模修正效果佳" },
        { label: "上一模修正效果不佳", value: "上一模修正效果不佳" },
      ],
    }
  },
  created() {

  },
  mounted() {
    this.updateValvePositionOptions()
  },
  methods: {

    updateValvePositionOptions() {
      
      // 下拉框
      this.valve_position_options = []

      let defect_position = [
        { label: "缺陷位置不指定", value: "缺陷位置不指定" },
        { label: "缺陷位置在1段", value: "缺陷位置在1段" },
        { label: "缺陷位置在2段", value: "缺陷位置在2段" },
        { label: "缺陷位置在3段", value: "缺陷位置在3段" },
        { label: "缺陷位置在4段", value: "缺陷位置在4段" },
        { label: "缺陷位置在5段", value: "缺陷位置在5段" },
        { label: "缺陷位置在6段", value: "缺陷位置在6段" },
      ]

      for (let i = 0; i <= this.optimize_detail.process_detail.inject_para.injection_stage; ++i) {
        this.valve_position_options.push(defect_position[i])
      }

      if (this.precondition_detail.valve_num && this.precondition_detail.valve_num > 1) {

        for (let i = 1; i < this.precondition_detail.valve_num; ++i) {
          let val = "在第" + String(i) + "、" + String(i + 1) + "个阀口间"
          this.valve_position_options.push({
            label: val, value: val
          })
        }
      }
    },
  },
  computed: {
    // 动态生成模温机温度设定列表
    moldTempList() {
      return Array.from({ length: this.optimize_detail.auxiliary_detail.mold_temp.mold_temp_num }, (_, i) => ({
        value: ''
      }));
    }
  },
  watch: {
    optimizeDetail: {
      handler(){
        this.optimize_detail = this.optimizeDetail
        // this.setParamDetail()
      },
      deep:true,
      immediate:true
    },
    "optimize_detail.feedback_detail.defect_info": {
      handler: function () {
        for ( let i=0;i< this.optimize_detail.feedback_detail.defect_info.length;i++) {
            if (this.optimize_detail.feedback_detail.defect_info[i].level == "无缺陷") {
              this.optimize_detail.feedback_detail.defect_info[i].position = "缺陷位置不指定"
            }

            if (this.optimize_detail.feedback_detail.defect_info[i].feedback == "上一模修正效果佳") {
              this.optimize_detail.feedback_detail.optimize_export.rule_valid = 0
              this.optimize_detail.feedback_detail.optimize_export.defect_feedback = "上一模修正效果佳"
            } else if (this.optimize_detail.feedback_detail.defect_info[i].feedback == "上一模修正效果不佳") {
              this.optimize_detail.feedback_detail.optimize_export.rule_valid = 1
              this.optimize_detail.feedback_detail.optimize_export.defect_feedback = "上一模修正效果不佳"
            }
        }
      },
      deep: true
    },
    "optimize_detail.process_detail.inject_para.injection_stage": function() {
      for (let i = this.optimize_detail.process_detail.inject_para.injection_stage; i < 6; ++i) {
        this.optimize_detail.process_detail.inject_para.table_data[0].sections[i] = null
        this.optimize_detail.process_detail.inject_para.table_data[1].sections[i] = null
        this.optimize_detail.process_detail.inject_para.table_data[2].sections[i] = null
      }
      let defect_position = [
        { label: "缺陷位置不指定", value: "缺陷位置不指定" },
        { label: "缺陷位置在1段", value: "缺陷位置在1段" },
        { label: "缺陷位置在2段", value: "缺陷位置在2段" },
        { label: "缺陷位置在3段", value: "缺陷位置在3段" },
        { label: "缺陷位置在4段", value: "缺陷位置在4段" },
        { label: "缺陷位置在5段", value: "缺陷位置在5段" },
        { label: "缺陷位置在6段", value: "缺陷位置在6段" },
      ]
      this.defect_position_options.length = 0
      for (let i = 0; i <= this.optimize_detail.process_detail.inject_para.injection_stage; ++i) {
        this.defect_position_options.push(defect_position[i])
      }

      this.updateValvePositionOptions()
    },
    "optimize_detail.process_detail.holding_para.holding_stage": function() {
      for (let i = this.optimize_detail.process_detail.holding_para.holding_stage; i < 5; ++i) {
        this.optimize_detail.process_detail.holding_para.table_data[0].sections[i] = null
        this.optimize_detail.process_detail.holding_para.table_data[1].sections[i] = null
        this.optimize_detail.process_detail.holding_para.table_data[2].sections[i] = null
      }
    },
    "optimize_detail.process_detail.metering_para.metering_stage": function() {
      for (let i = this.optimize_detail.process_detail.metering_para.metering_stage; i < 4; ++i) {
        this.optimize_detail.process_detail.metering_para.table_data[0].sections[i] = null
        this.optimize_detail.process_detail.metering_para.table_data[1].sections[i] = null
        this.optimize_detail.process_detail.metering_para.table_data[2].sections[i] = null
        this.optimize_detail.process_detail.metering_para.table_data[3].sections[i] = null
      }
    },
    "optimize_detail.process_detail.temp_para.barrel_temperature_stage": function() {
      for (let i = this.optimize_detail.process_detail.temp_para.barrel_temperature_stage; i < 10; ++i) {
        this.optimize_detail.process_detail.temp_para.table_data[0].sections[i] = null
      }
    },
    preconditionDetail() {
      this.precondition_detail = this.preconditionDetail
      this.updateValvePositionOptions()
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
  .defect-feedback {
    .el-select {
      width: 10rem;
    }
  }
  .highlight-input>>>.el-input__inner {
    background-color: red;
  }
  .normal>>>.el-input__inner {
    background-color: white;
  }
  .box-card {
    .el-input {
      border: 0;
      margin: 0;
    }
  }

</style>
