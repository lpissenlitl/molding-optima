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
              :key="Math.random()"
            >
              <el-table-column 
                label="工艺参数"
                width="90" 
                align="center"
              >
                <template #header>
                  <div>注射段数</div>
                  <el-select 
                    v-model="optimize_detail.process_detail.inject_para.stage" 
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
                <template #default="scope">
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
                  <template #default="scope">
                    <el-input
                      :id="components_view_id.inject_para.table[scope.$index][colidx] + viewIndex"
                      v-model="optimize_detail.process_detail.inject_para.table_data[scope.$index].sections[colidx]" 
                      type="number" 
                      min="0" 
                      size="mini"
                      :disabled="colidx >=optimize_detail.process_detail.inject_para.stage"
                      @input="optimize_detail.process_detail.inject_para.table_data[scope.$index].sections[colidx]=$formatNumber(optimize_detail.process_detail.inject_para.table_data[scope.$index].sections[colidx])"
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
                <template #default="scope">
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
                @input="optimize_detail.process_detail.inject_para.injection_time=$formatNumber(optimize_detail.process_detail.inject_para.injection_time)"
              >
                <span slot="suffix">{{ mac_unit.time_unit }}</span>
              </el-input>
            </el-form-item>
            <el-form-item label="注射延迟">
              <el-input
                :id="components_view_id.inject_para.inj_delay + viewIndex"
                type="text"
                v-model="optimize_detail.process_detail.inject_para.delay_time"
                style="width: 7rem"
                @input="optimize_detail.process_detail.inject_para.delay_time=$formatNumber(optimize_detail.process_detail.inject_para.delay_time)"
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
                @input="optimize_detail.process_detail.inject_para.cooling_time=$formatNumber(optimize_detail.process_detail.inject_para.cooling_time)"
              >
                <span slot="suffix">{{ mac_unit.time_unit }}</span>
              </el-input>
            </el-form-item>
            <el-divider content-position="center">
              <span>VP切换</span>
            </el-divider>
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
                @input="optimize_detail.process_detail.VP_switch.VP_switch_time=$formatNumber(optimize_detail.process_detail.VP_switch.VP_switch_time)"
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
                @input="optimize_detail.process_detail.VP_switch.VP_switch_position=$formatNumber(optimize_detail.process_detail.VP_switch.VP_switch_position)"
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
                @input="optimize_detail.process_detail.VP_switch.VP_switch_pressure=$formatNumber(optimize_detail.process_detail.VP_switch.VP_switch_pressure)"
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
                @input="optimize_detail.process_detail.VP_switch.VP_switch_velocity=$formatNumber(optimize_detail.process_detail.VP_switch.VP_switch_velocity)"
              >
                <span slot="suffix">{{ mac_unit.velocity_unit }}</span>
              </el-input>
            </el-form-item>
          </el-card>
          <el-card class="box-card" style="min-height:240px">
            <el-table 
              size="mini"
              :data="optimize_detail.process_detail.holding.table_data" 
              :key="Math.random()"
            >
              <el-table-column 
                label="工艺参数"
                width="90" 
                align="center"
              >
                <template #header>
                  <div>保压段数</div>
                  <el-select 
                    v-model="optimize_detail.process_detail.holding.stage" 
                    size="mini"
                  >
                    <el-option
                      v-for="option, idx in optimize_detail.process_detail.holding.max_holding_stage_option"
                      :key="idx"
                      :label="option"
                      :value="option"
                    >
                    </el-option>
                  </el-select>
                </template>
                <template #default="scope">
                  {{ scope.row.label }}
                </template>
              </el-table-column>
              <template v-for="(col, colidx) in optimize_detail.process_detail.holding.max_holding_stage_option">
                <el-table-column
                  :key="colidx"
                  :label="holding_stage_header[col]"
                  min-width="80"
                  align="center"
                >
                  <template #default="scope">
                    <el-input
                      :id="components_view_id.holding.table[scope.$index][colidx] + viewIndex"
                      v-model="optimize_detail.process_detail.holding.table_data[scope.$index].sections[colidx]" 
                      :disabled="colidx >=optimize_detail.process_detail.holding.stage"
                      type="number" 
                      min="0" 
                      size="mini"
                      @input="optimize_detail.process_detail.holding.table_data[scope.$index].sections[colidx]=$formatNumber(optimize_detail.process_detail.holding.table_data[scope.$index].sections[colidx])"
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
                <template #default="scope">
                  {{ optimize_detail.process_detail.holding.table_data[scope.$index].unit }}
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-col>
        <el-col :xs="24" :lg="11" :xl="11">
          <el-card class="box-card" style="min-height:720px">
            <el-table 
              size="mini"
              :data="optimize_detail.process_detail.metering.table_data"
              :key="Math.random()"
            >
              <el-table-column 
                label="工艺参数"
                width="90" 
                align="center"
              >
                <template #header>
                  <div>计量段数</div>
                  <el-select 
                    v-model="optimize_detail.process_detail.metering.stage" 
                    size="mini"
                  >
                    <el-option
                      v-for="option, idx in optimize_detail.process_detail.metering.max_metering_stage_option"
                      :key="idx"
                      :label="option"
                      :value="option"
                    >
                    </el-option>
                  </el-select>
                </template>
                <template #default="scope">
                  {{ scope.row.label }}
                </template>
              </el-table-column>
              <template v-for="(col, colidx) in optimize_detail.process_detail.metering.max_metering_stage_option">
                <el-table-column
                  :key="colidx"
                  :label="metering_stage_header[col]"
                  min-width="80"
                  align="center"
                >
                  <template #default="scope">
                    <el-input 
                      :id="components_view_id.metering.table[scope.$index][colidx] + viewIndex"
                      v-model="optimize_detail.process_detail.metering.table_data[scope.$index].sections[colidx]" 
                      :disabled="colidx >=optimize_detail.process_detail.metering.stage"
                      type="number" 
                      min="0" 
                      size="mini"
                      @input="optimize_detail.process_detail.metering.table_data[scope.$index].sections[colidx]=$formatNumber(optimize_detail.process_detail.metering.table_data[scope.$index].sections[colidx])"
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
                <template #default="scope">
                  {{ optimize_detail.process_detail.metering.table_data[scope.$index].unit }}
                </template>
              </el-table-column>
            </el-table>
            <div style="height:15px" />
            <el-form-item label="储前松退模式">
              <el-select 
                :id="components_view_id.metering.dec_mode_bef + viewIndex"
                v-model="optimize_detail.process_detail.metering.pre_decompress_mode"
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
                :id="components_view_id.metering.dec_mode_aft + viewIndex"
                v-model="optimize_detail.process_detail.metering.post_decompress_mode"
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
              :data="optimize_detail.process_detail.metering.decompressure_paras"
              :key="Math.random()"
            >
              <el-table-column
                label=""
                width="45"
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
                  <div>{{ mac_unit.pressure_unit }}</div>
                </template>
                <template #default="scope">
                  <el-input
                    :id="components_view_id.metering.deco_table[scope.$index][0] + viewIndex"
                    :disabled="((scope.$index === 0 &&optimize_detail.process_detail.metering.pre_decompress_mode === '否')
                      || (scope.$index === 1 &&optimize_detail.process_detail.metering.post_decompress_mode === '否'))"
                    v-model="scope.row.pressure"
                    size="mini"
                    @input="scope.row.pressure=$formatNumber(scope.row.pressure)"
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
                  <div>{{ mac_unit.velocity_unit }}</div>
                </template>
                <template #default="scope">
                  <el-input
                    :id="components_view_id.metering.deco_table[scope.$index][1] + viewIndex"
                    :disabled="((scope.$index === 0 &&optimize_detail.process_detail.metering.pre_decompress_mode === '否')
                      || (scope.$index === 1 &&optimize_detail.process_detail.metering.post_decompress_mode === '否'))"
                    v-model="scope.row.velocity"
                    size="mini"
                    @input="scope.row.velocity=$formatNumber(scope.row.velocity)"
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
                  <div>{{ mac_unit.position_unit }}</div>
                </template>
                <template #default="scope">
                  <el-input
                    :id="components_view_id.metering.deco_table[scope.$index][2] + viewIndex"
                    :disabled="((scope.$index === 0 &&optimize_detail.process_detail.metering.pre_decompress_mode != '距离')
                      || (scope.$index === 1 &&optimize_detail.process_detail.metering.post_decompress_mode != '距离'))"
                    v-model="scope.row.distance"
                    size="mini"
                    @input="scope.row.distance=$formatNumber(scope.row.distance)"
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
                  <div>{{ mac_unit.time_unit }}</div>
                </template>
                <template #default="scope">
                  <el-input
                    :id="components_view_id.metering.deco_table[scope.$index][3] + viewIndex"
                    :disabled="((scope.$index === 0 &&optimize_detail.process_detail.metering.pre_decompress_mode != '时间')
                      || (scope.$index === 1 &&optimize_detail.process_detail.metering.post_decompress_mode != '时间'))"
                    v-model="scope.row.time"
                    size="mini"
                    @input="scope.row.time=$formatNumber(scope.row.time)"
                  >
                  </el-input>
                </template>
              </el-table-column>
            </el-table>
            <div style="height:15px" />
            <el-form-item label="储料延迟">
              <el-input
                :id="components_view_id.metering.measureDelay + viewIndex"
                type="number"
                v-model="optimize_detail.process_detail.metering.delay_time"
                style="width: 8rem"
                @input="optimize_detail.process_detail.metering.delay_time=$formatNumber(optimize_detail.process_detail.metering.delay_time)"
              >
                <span slot="suffix">{{ mac_unit.time_unit }}</span>
              </el-input>
            </el-form-item>
            <br>
            <el-form-item label="终止位置">
              <el-input
                :id="components_view_id.metering.stopPos + viewIndex"
                type="number"
                v-model="optimize_detail.process_detail.metering.ending_position"
                style="width: 8rem"
                @input="optimize_detail.process_detail.metering.ending_position=$formatNumber(optimize_detail.process_detail.metering.ending_position)"
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
              :key="Math.random()"
            >
              <el-table-column 
                label="工艺参数"
                width="90" 
                align="center"
              >
                <template #header>
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
                <template #default="scope">
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
                  <template #default="scope">
                    <el-input 
                      :id="components_view_id.temp_para.table[scope.$index][colidx] + viewIndex"
                      v-model="optimize_detail.process_detail.temp_para.table_data[scope.$index].sections[colidx]" 
                      :disabled="colidx >=optimize_detail.process_detail.temp_para.barrel_temperature_stage"
                      type="number" 
                      min="0" 
                      size="mini"
                      @input="optimize_detail.process_detail.temp_para.table_data[scope.$index].sections[colidx]=$formatNumber(optimize_detail.process_detail.temp_para.table_data[scope.$index].sections[colidx])"
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
                <template #default="scope">
                  {{ optimize_detail.process_detail.temp_para.table_data[scope.$index].unit }}
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-col>
      </el-form>
    </el-row>

    <el-row v-if="valveNum && valveNum > 1">
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
            v-for="idx in valveNum"
            :key="idx"
            :label="'阀口' + String(idx)" 
            label-width="6rem"
          >
            <el-input 
              v-model="optimize_detail.auxiliary_detail.hot_runner.sequential_ctrl_time[Number(idx)-1]" 
              style="width:8rem"
              @input="optimize_detail.auxiliary_detail.hot_runner.sequential_ctrl_time[Number(idx)-1]=$formatNumber(optimize_detail.auxiliary_detail.hot_runner.sequential_ctrl_time[Number(idx)-1])"
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
          <el-form-item
            label="设定温度"
            label-width="6rem"
          >
            <el-input 
              v-model="optimize_detail.auxiliary_detail.mold_temp.setting_temp" 
              @input="optimize_detail.auxiliary_detail.mold_temp.setting_temp=$formatNumber(optimize_detail.auxiliary_detail.mold_temp.setting_temp)"
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
          <span style="color:red"> 当前规则：{{ optimize_detail.feedback_detail.optimize_export.rule_in_use }} </span>
        </div>

        <el-form
          class="defect-feedback"
          :inline="true" 
          :model="optimize_detail.feedback_detail.defect_info" 
          size="mini" 
          label-width="6rem"
        >
          <el-form-item 
            label="实际重量" 
            label-width="6rem"
          >
            <el-input 
              v-model="optimize_detail.feedback_detail.actual_product_weight" style="width:8rem"
              @input="optimize_detail.feedback_detail.actual_product_weight=$formatNumber(optimize_detail.feedback_detail.actual_product_weight)"
            >
              <span slot="suffix">g</span>
            </el-input>
          </el-form-item>

          <br>

          <el-form-item 
            label="短射"
            prop="short_shot"
          >
            <el-select
              v-model="optimize_detail.feedback_detail.defect_info.short_shot.level"
              placeholder="请选择"
            >
              <el-option
                v-for="item in defect_level_options"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              >
              </el-option>
            </el-select>

            <el-select
              v-model="optimize_detail.feedback_detail.defect_info.short_shot.position"
              placeholder="请选择"
              :disabled="optimize_detail.feedback_detail.defect_info.short_shot.level == '无缺陷'"
            >
              <el-option
                v-for="item in defect_position_options"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              >
              </el-option>
            </el-select>

            <el-select
              v-if="optimize_detail.name != '0' && optimize_detail.feedback_detail.defect_info.short_shot.feedback != null"
              v-model="optimize_detail.feedback_detail.defect_info.short_shot.feedback"
              placeholder="请选择"
            >
              <el-option
                v-for="item in feedback_options"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              >
              </el-option>
            </el-select>
          </el-form-item>

          <el-form-item 
            label="飞边"
            prop="flash"
          >
            <el-select
              v-model="optimize_detail.feedback_detail.defect_info.flash.level"
              placeholder="请选择"
            >
              <el-option
                v-for="item in defect_level_options"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              >
              </el-option>
            </el-select>

            <el-select
              v-model="optimize_detail.feedback_detail.defect_info.flash.position"
              placeholder="请选择"
              :disabled="optimize_detail.feedback_detail.defect_info.flash.level == '无缺陷'"
            >
              <el-option
                v-for="item in defect_position_options"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              >
              </el-option>
            </el-select>

            <el-select
              v-if="optimize_detail.name != '0' && optimize_detail.feedback_detail.defect_info.flash.feedback != null"
              v-model="optimize_detail.feedback_detail.defect_info.flash.feedback"
              placeholder="请选择"
            >
              <el-option
                v-for="item in feedback_options"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              >
              </el-option>
            </el-select>
          </el-form-item>

          <el-form-item 
            label="缩水"
            prop="shrinkage"
          >
            <el-select
              v-model="optimize_detail.feedback_detail.defect_info.shrinkage.level"
              placeholder="请选择"
            >
              <el-option
                v-for="item in defect_level_options"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              >
              </el-option>
            </el-select>

            <el-select
              v-model="optimize_detail.feedback_detail.defect_info.shrinkage.position"
              placeholder="请选择"
              :disabled="optimize_detail.feedback_detail.defect_info.shrinkage.level == '无缺陷'"
            >
              <el-option
                v-for="item in defect_position_options"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              >
              </el-option>
            </el-select>

            <el-select
              v-if="optimize_detail.name != '0' && optimize_detail.feedback_detail.defect_info.shrinkage.feedback != null"
              v-model="optimize_detail.feedback_detail.defect_info.shrinkage.feedback"
              placeholder="请选择"
            >
              <el-option
                v-for="item in feedback_options"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              >
              </el-option>
            </el-select>
          </el-form-item>

          <el-form-item 
            label="熔接线"
            prop="weld_line"
          >
            <el-select
              v-model="optimize_detail.feedback_detail.defect_info.weld_line.level"
              placeholder="请选择"
            >
              <el-option
                v-for="item in defect_level_options"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              >
              </el-option>
            </el-select>

            <el-select
              v-model="optimize_detail.feedback_detail.defect_info.weld_line.position"
              placeholder="请选择"
              :disabled="optimize_detail.feedback_detail.defect_info.weld_line.level == '无缺陷'"
            >
              <el-option
                v-for="item in valve_position_options"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              >
              </el-option>
            </el-select>

            <el-select
              v-if="optimize_detail.name != '0' && optimize_detail.feedback_detail.defect_info.weld_line.feedback != null"
              v-model="optimize_detail.feedback_detail.defect_info.weld_line.feedback"
              placeholder="请选择"
            >
              <el-option
                v-for="item in feedback_options"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              >
              </el-option>
            </el-select>
          </el-form-item>

          <el-form-item 
            label="色差"
            prop="aberration"
          >
            <el-select
              v-model="optimize_detail.feedback_detail.defect_info.aberration.level"
              placeholder="请选择"
            >
              <el-option
                v-for="item in defect_level_options"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              >
              </el-option>
            </el-select>

            <el-select
              v-model="optimize_detail.feedback_detail.defect_info.aberration.position"
              placeholder="请选择"
              :disabled="optimize_detail.feedback_detail.defect_info.aberration.level == '无缺陷'"
            >
              <el-option
                v-for="item in defect_position_options"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              >
              </el-option>
            </el-select>

            <el-select
              v-if="optimize_detail.name != '0' && optimize_detail.feedback_detail.defect_info.aberration.feedback != null"
              v-model="optimize_detail.feedback_detail.defect_info.aberration.feedback"
              placeholder="请选择"
            >
              <el-option
                v-for="item in feedback_options"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              >
              </el-option>
            </el-select>
          </el-form-item>

          <el-form-item 
            label="困气"
            prop="air_trap"
          >
            <el-select
              v-model="optimize_detail.feedback_detail.defect_info.air_trap.level"
              placeholder="请选择"
            >
              <el-option
                v-for="item in defect_level_options"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              >
              </el-option>
            </el-select>

            <el-select
              v-model="optimize_detail.feedback_detail.defect_info.air_trap.position"
              placeholder="请选择"
              :disabled="optimize_detail.feedback_detail.defect_info.air_trap.level == '无缺陷'"
            >
              <el-option
                v-for="item in defect_position_options"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              >
              </el-option>
            </el-select>

            <el-select
              v-if="optimize_detail.name != '0' && optimize_detail.feedback_detail.defect_info.air_trap.feedback != null"
              v-model="optimize_detail.feedback_detail.defect_info.air_trap.feedback"
              placeholder="请选择"
            >
              <el-option
                v-for="item in feedback_options"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              >
              </el-option>
            </el-select>
          </el-form-item>

          <el-form-item 
            label="气纹"
            prop="gas_veins"
          >
            <el-select
              v-model="optimize_detail.feedback_detail.defect_info.gas_veins.level"
              placeholder="请选择"
            >
              <el-option
                v-for="item in defect_level_options"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              >
              </el-option>
            </el-select>

            <el-select
              v-model="optimize_detail.feedback_detail.defect_info.gas_veins.position"
              placeholder="请选择"
              :disabled="optimize_detail.feedback_detail.defect_info.gas_veins.level == '无缺陷'"
            >
              <el-option
                v-for="item in defect_position_options"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              >
              </el-option>
            </el-select>

            <el-select
              v-if="optimize_detail.name != '0' && optimize_detail.feedback_detail.defect_info.gas_veins.feedback != null"
              v-model="optimize_detail.feedback_detail.defect_info.gas_veins.feedback"
              placeholder="请选择"
            >
              <el-option
                v-for="item in feedback_options"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              >
              </el-option>
            </el-select>
          </el-form-item>

          <el-form-item 
            label="料花"
            prop="material_flower"
          >
            <el-select
              v-model="optimize_detail.feedback_detail.defect_info.material_flower.level"
              placeholder="请选择"
            >
              <el-option
                v-for="item in defect_level_options"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              >
              </el-option>
            </el-select>

            <el-select
              v-model="optimize_detail.feedback_detail.defect_info.material_flower.position"
              placeholder="请选择"
              :disabled="optimize_detail.feedback_detail.defect_info.material_flower.level == '无缺陷'"
            >
              <el-option
                v-for="item in defect_position_options"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              >
              </el-option>
            </el-select>

            <el-select
              v-if="optimize_detail.name != '0' && optimize_detail.feedback_detail.defect_info.material_flower.feedback != null"
              v-model="optimize_detail.feedback_detail.defect_info.material_flower.feedback"
              placeholder="请选择"
            >
              <el-option
                v-for="item in feedback_options"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              >
              </el-option>
            </el-select>
          </el-form-item>
        </el-form>
      </el-card>
    </el-row>
  </div>
</template>

<script>
import { initArray } from "@/utils/array-utils"

export default {
  name: "ProcessOptimizeForm",
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
      default: () => ({
        title: "init", 
        name: "0",
        process_detail: {
          title: "射台 #1",
          name: "0",
          inject_para: {
            stage: 1,
            max_injection_stage_option: 6,
            table_data: [
              { label: "压力", unit: "kgf/cm²", sections: initArray(6, null) },
              { label: "速度", unit: "mm/s", sections: initArray(6, null) },
              { label: "位置", unit: "mm", sections: initArray(6, null) }
            ],
            injection_time: null,
            delay_time: null,
            cooling_time: null
          },
          holding: {
            stage: 1,
            max_holding_stage_option: 5,
            table_data: [
              { label: "压力", unit: "kgf/cm²", sections: initArray(5, null) },
              { label: "速度", unit: "mm/s", sections: initArray(5, null) },
              { label: "时间", unit: "s", sections: initArray(5, null) }
            ]
          },
          VP_switch: {
            VP_switch_mode: "位置",
            VP_switch_position: null,
            VP_switch_time: null,
            VP_switch_pressure: null,
            VP_switch_velocity: null,
          },
          metering: {
            stage: 1,
            max_metering_stage_option: 4,
            table_data: [
              { label: "压力", unit: "kgf/cm²", sections: initArray(4, null) },
              { label: "螺杆转速", unit: "rpm", sections: initArray(4, null) },
              { label: "背压", unit: "kgf/cm²", sections: initArray(4, null) },
              { label: "位置", unit: "mm", sections: initArray(4, null) }
            ],
            pre_decompress_mode: "否",
            post_decompress_mode: "距离",
            decompressure_paras: [
              { label: "储前", pressure: null, velocity: null, time: null, distance: null },
              { label: "储后", pressure: null, velocity: null, time: null, distance: null }
            ],
            delay_time: null,
            ending_position: null
          },
          temp_para: {
            barrel_temperature_stage: 5,
            max_barrel_temperature_stage_option: 10,
            table_data: [
              { label: "温度", unit: "℃", sections: initArray(10, null) },
            ],
          },
        },
        auxiliary_detail: {
          hot_runner: {
            valve_num: null,
            sequential_ctrl_time: []
          },
          mold_temp: {
            setting_temp: null
          }
        },
        feedback_detail: {
          actual_product_weight: null,
          defect_info: {
            short_shot: { level: "无缺陷", position: "缺陷位置不指定", count: 0, feedback: null, remarks: null },
            flash: { level: "无缺陷", position: "缺陷位置不指定", count: 0, feedback: null, remarks: null },
            shrinkage: { level: "无缺陷", position: "缺陷位置不指定", count: 0, feedback: null, remarks: null },
            weld_line: { level: "无缺陷", position: "缺陷位置不指定", count: 0, feedback: null, remarks: null },
            aberration: { level: "无缺陷", position: "缺陷位置不指定", count: 0, feedback: null, remarks: null },
            air_trap: { level: "无缺陷", position: "缺陷位置不指定", count: 0, feedback: null, remarks: null },
            gas_veins: { level: "无缺陷", position: "缺陷位置不指定", count: 0, feedback: null, remarks: null },
            material_flower: { level: "无缺陷", position: "缺陷位置不指定", count: 0, feedback: null, remarks: null },
          },
          optimize_export:  {
            defect_name: null,
            defect_position: null,
            defect_level: null,
            adjust_name: null,
            adjust_direction: null,
            adjust_value: null,
            rule_in_use: null,
            rule_valid: null,

            candidate_rules: [],
          }
        }
      })
    },
    viewIndex: {
      type: Number,
      default: null
    },
    valveNum: {
      type: Number,
      default: null
    }
  },
  data() {
    return {
      optimize_detail: this.optimizeDetail,
      mac_unit: this.macUnit,
      injection_stage_header: ["注射段数", "一段", "二段", "三段", "四段", "五段", "六段"],
      holding_stage_header: ["保压段数", "一段", "二段", "三段", "四段", "五段"],
      metering_stage_header: ["计量段数", "一段", "二段", "三段", "四段"],
      temp_stage_header: ["温度段数", "喷嘴", "一段", "二段", "三段", "四段", "五段", "六段", "七段", "八段", "九段"],
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
            ["IP0", "IP1", "IP2", "IP3", "IP4", "IP5"],
            ["IV0", "IV1", "IV2", "IV3", "IV4", "IV5"],
            ["IL0", "IL1", "IL2", "IL3", "IL4", "IL5"]
          ],
          inj_time: "IT",
          inj_delay: "ID",
          cool_time: "CT"
        },
        holding: {
          table: [
            ["PP0", "PP1", "PP2", "PP3", "PP4"],
            ["PV0", "PV1", "PV2", "PV3", "PV4"],
            ["PT0", "PT1", "PT2", "PT3", "PT4"]
          ]
        },
        VP_switch: {
          mode: "VPTM",
          time: "VPTT",
          position: "VPTL",
          pressure: "VPTP",
          velocity: "VPTV",
        },
        metering: {
          table: [
            ["MP0", "MP1", "MP2", "MP3"],
            ["MSR0", "MSR1", "MSR2", "MSR3"],
            ["MBP0", "MBP1", "MBP2", "MBP3"],
            ["ML0", "ML1", "ML2", "ML3"]
          ],
          dec_mode_bef: "DMBM",
          dec_mode_aft: "DMAM",
          deco_table: [
            ["DPBM", "DVBM", "DDBM", "DTBM"],
            ["DPAM", "DVAM", "DDAM", "DTAM"]
          ],
          measureDelay: "MD",
          stopPos: "MEL"
        },
        temp_para: {
          table: [
            ["NT", "BT1", "BT2", "BT3", "BT4", "BT5", "BT6", "BT7", "BT8", "BT9"]
          ]
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
  watch: {
    optimizeDetail() {
      this.optimize_detail = this.optimizeDetail
    },
    valveNum() {
      this.updateValvePositionOptions()
    },
    "optimize_detail.feedback_detail.defect_info": {
      handler: function () {
        for ( let defect in this.optimize_detail.feedback_detail.defect_info) {
          if (this.optimize_detail.feedback_detail.defect_info[defect].level == "无缺陷") {
            this.optimize_detail.feedback_detail.defect_info[defect].position = "缺陷位置不指定"
          }

          if (this.optimize_detail.feedback_detail.defect_info[defect].feedback == "上一模修正效果佳") {
            this.optimize_detail.feedback_detail.optimize_export.rule_valid = 0
          } else if (this.optimize_detail.feedback_detail.defect_info[defect].feedback == "上一模修正效果不佳") {
            this.optimize_detail.feedback_detail.optimize_export.rule_valid = 1
          }
        }
      },
      deep: true
    },
    "optimize_detail.process_detail.inject_para.stage": function() {
      for (let i = this.optimize_detail.process_detail.inject_para.stage; i < 6; ++i) {
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
      for (let i = 0; i <= this.optimize_detail.process_detail.inject_para.stage; ++i) {
        this.defect_position_options.push(defect_position[i])
      }

      this.updateValvePositionOptions()
    },
    "optimize_detail.process_detail.holding.stage": function() {
      for (let i = this.optimize_detail.process_detail.holding.stage; i < 5; ++i) {
        this.optimize_detail.process_detail.holding.table_data[0].sections[i] = null
        this.optimize_detail.process_detail.holding.table_data[1].sections[i] = null
        this.optimize_detail.process_detail.holding.table_data[2].sections[i] = null
      }
    },
    "optimize_detail.process_detail.metering.stage": function() {
      for (let i = this.optimize_detail.process_detail.metering.stage; i < 4; ++i) {
        this.optimize_detail.process_detail.metering.table_data[0].sections[i] = null
        this.optimize_detail.process_detail.metering.table_data[1].sections[i] = null
        this.optimize_detail.process_detail.metering.table_data[2].sections[i] = null
        this.optimize_detail.process_detail.metering.table_data[3].sections[i] = null
      }
    },
    "optimize_detail.process_detail.temp_para.barrel_temperature_stage": function() {
      for (let i = this.optimize_detail.process_detail.temp_para.barrel_temperature_stage; i < 10; ++i) {
        this.optimize_detail.process_detail.temp_para.table_data[0].sections[i] = null
      }
    },
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

      for (let i = 0; i <= this.optimize_detail.process_detail.inject_para.stage; ++i) {
        this.valve_position_options.push(defect_position[i])
      }

      if (this.valveNum && this.valveNum > 1) {
        // // 辅机参数
        // this.optimize_detail.auxiliary_detail.hot_runner.valve_num = this.valveNum
        // for (let i = 0; i < this.valveNum; ++i) {
        //   this.optimize_detail.auxiliary_detail.hot_runner.sequential_ctrl_time[i] = i + 1
        // }  

        for (let i = 1; i < this.valveNum; ++i) {
          let val = "在第" + String(i) + "、" + String(i + 1) + "个阀口间"
          this.valve_position_options.push({
            label: val, value: val
          })
        }
      }
    }
  }
}
</script>

<style lang="scss" scoped>
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
