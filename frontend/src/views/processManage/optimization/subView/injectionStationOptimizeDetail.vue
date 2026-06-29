<template>
  <div>
    <el-row>
      <el-form
        size="mini"
        label-width="8rem"
        :model="detail_info.casting_system"
        :inline="true"
      >
        <el-divider content-position="center">
          <span>浇注</span>
        </el-divider>
        <el-form-item
          label="定位圈直径"
          prop="locate_ring_diameter"
        >
          <el-input 
            v-model="detail_info.casting_system.locate_ring_diameter"
          ></el-input>
        </el-form-item> 
        <el-form-item
          label="流道类别"
          prop="runner_type"
        >
          <el-select 
            v-model="detail_info.casting_system.runner_type"
            clearable
            filterable 
            allow-create
            style="width: 10rem;"
          >
            <el-option label="热流道" value="热流道"></el-option>
            <el-option label="冷流道" value="冷流道"></el-option>
            <el-option label="热转冷" value="热转冷"></el-option>
          </el-select>
        </el-form-item> 
        <template v-if="['热流道', '热转冷'].includes(detail_info.casting_system.runner_type)">
          <el-divider content-position="center">
            <span>热流道</span>
          </el-divider>
          <el-form-item
            label="热嘴类型"
            prop="hot_nozzle_type"
          >
            <el-input v-model="detail_info.casting_system.hot_nozzle_type"></el-input>
          </el-form-item>
          <el-form-item
            label="热嘴数量"
            prop="hot_nozzle_number"
          >
            <el-input v-model="detail_info.casting_system.hot_nozzle_number"></el-input>
          </el-form-item>
          <el-form-item
            label="阀口数量"
            prop="hotrunner_valve_number"
          >
            <el-input v-model="detail_info.casting_system.hotrunner_valve_number"></el-input>
          </el-form-item>
        </template>
        <template v-if="['冷流道', '热转冷'].includes(detail_info.casting_system.runner_type)">
          <el-divider content-position="center">
            <span>冷流道</span>
          </el-divider>
          <el-form-item
            label="流道重量"
            prop="runner_weight"
          >
            <el-input v-model="detail_info.casting_system.runner_weight">
              <span slot="suffix">g</span>
            </el-input>
          </el-form-item>
          <el-form-item
            label="流道长度"
            prop="runner_length"
          >
            <el-input v-model="detail_info.casting_system.runner_length">
              <span slot="suffix">mm</span>
            </el-input>
          </el-form-item>
          <el-form-item
            label="浇口总数量"
            prop="total_gate_number"
          >
            <el-input v-model="detail_info.casting_system.total_gate_number"></el-input>
          </el-form-item>
          <el-divider content-position="center">
            <span>浇口参数</span>
          </el-divider>
          <div 
            v-for="(gate_detail, idx) in detail_info.casting_system.gate_details"
            :key="idx"
          >
            <el-form-item 
              label="浇口类别"
              prop="gate_type"
            >
              <el-input v-model="gate_detail.gate_type"></el-input>
            </el-form-item>
            <el-form-item
              label="浇口形状"
              prop="gate_shape"
            >
              <el-input v-model="gate_detail.gate_shape"></el-input>
            </el-form-item>  
            <el-form-item
              label="浇口数量"
              prop="gate_number"
            >
              <el-input v-model="gate_detail.gate_number"></el-input>
            </el-form-item>
            <el-form-item
              label="横截面积"
              prop="gate_area"
            >
              <el-input v-model="gate_detail.gate_area">
                <span slot="suffix">cm<sup>2</sup></span>
              </el-input>
            </el-form-item>
          </div>
        </template>
        <el-divider content-position="center">
          <span>制品参数</span>
        </el-divider>
        <el-tabs v-if="detail_info.casting_system.product_details.length > 1">
          <el-tab-pane
            v-for="(prod, idx) in detail_info.casting_system.product_details"
            :key="idx"
            :label="'制品-' + (idx + 1)"
          >
            <casting-system-product-detail
              :product-detail="prod"
            ></casting-system-product-detail>
          </el-tab-pane>
        </el-tabs>
        <div v-else-if="detail_info.casting_system.product_details.length == 1">
          <casting-system-product-detail
            :product-detail="detail_info.casting_system.product_details[0]"
          ></casting-system-product-detail>
        </div>
      </el-form>
    </el-row>
    <el-row>
      <el-divider content-position="center">
        <span>材料</span>
      </el-divider>
      <el-form
        size="mini"
        label-width="8rem"
        :model="detail_info.polymer_detail"
        :inline="true"
      >
        <el-form-item 
          label="塑料厂商" 
          prop="manufacturer" 
        >
          <el-autocomplete
            v-model="detail_info.polymer_detail.manufacturer"
            placeholder="请输入内容"
            clearable
            :debounce="0"
            :fetch-suggestions="((str, cb)=>{querySuggestionOptions(str, cb, 'manufacturer')})"
          >
          </el-autocomplete>
        </el-form-item>
        <el-form-item 
          label="塑料简称" 
          prop="abbreviation" 
        >
          <el-autocomplete
            v-model="detail_info.polymer_detail.abbreviation"
            placeholder="请输入内容"
            clearable
            :debounce="0"
            :fetch-suggestions="((str, cb)=>{querySuggestionOptions(str, cb, 'abbreviation')})"
          >
          </el-autocomplete>
        </el-form-item>
        <el-form-item 
          label="塑料牌号" 
          prop="trademark"
        >
          <el-autocomplete
            v-model="detail_info.polymer_detail.trademark"
            placeholder="请输入内容"
            clearable
            :debounce="0"
            :fetch-suggestions="((str, cb)=>{querySuggestionOptions(str, cb, 'trademark')})"
            @select="((item) => {onTrademarkSelected(item)})"
          >
          </el-autocomplete>
        </el-form-item>
        <el-form-item
          label="塑料类别"
          prop="category"
        >
          <el-input 
            v-model="detail_info.polymer_detail.category"
            :readonly="true"
          >
          </el-input>
        </el-form-item>
      </el-form>
    </el-row>
    <el-row>
      <el-divider content-position="center">
        <span>工艺参数优化记录</span>
      </el-divider>
      <el-tabs v-model="actived_tab_index">
        <el-tab-pane 
          v-for="(optimize_detail, index) in detail_info.optimize_list"
          :key="index"
          :label="index == 0 ? '初始工艺' : `优化#${(index)}`"
          :name="String(index)"
        >
          <el-form
            size="mini"
            label-width="6rem"
            :inline="true"
          >
            <el-col :xs="24" :lg="13" :xl="13">
              <el-card class="box-card" style="min-height: 750px">
                <el-table 
                  id="xuanran"
                  size="mini"
                  :data="optimize_detail.setting_process.injection.table_data" 
                  :key="optimize_detail.setting_process.injection.stage + 20 + String(index)"
                >
                  <el-table-column
                    label="工艺参数"
                    width="90" 
                    align="center"
                  >
                    <template #header>
                      <div>注射段数</div>
                      <el-select 
                        v-model="optimize_detail.setting_process.injection.stage" 
                        size="mini"
                        style="width: 100%;"
                      >
                        <el-option
                          v-for="(option, idx) in optimize_detail.setting_process.injection.max_stage"
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
                  <template v-for="(col, col_idx) in optimize_detail.setting_process.injection.max_stage">
                    <el-table-column
                      min-width="80"
                      align="center"
                      :key="col_idx"
                      :label="injection_stage_header[col]"
                    >
                      <template #default="scope">
                        <el-input 
                          :id="custom_id.injection[scope.$index][col_idx] + String(station_index) + String(index)"
                          @change="onValueChanged(custom_id.injection[scope.$index][col_idx] + String(station_index), index)"
                          v-model="scope.row.sections[col_idx]" 
                          :disabled="col > optimize_detail.setting_process.injection.stage"
                          type="number" 
                          size="mini"
                          style="width: 100%;"
                          @input="scope.row.sections[col_idx]=$formatNumber(scope.row.sections[col_idx])"
                        >
                        </el-input>
                      </template>
                    </el-table-column>
                  </template>
                  <el-table-column
                    label="单位"
                    min-width="80"
                    align="center"
                  >
                    <template #default="scope">
                      {{ scope.row.unit }}
                    </template>
                  </el-table-column>
                </el-table>
                <div style="height:15px" />
                <el-form-item 
                  label="注射时间"
                  prop="injection_time"
                >
                  <el-input
                    :id="custom_id.inj_time + String(station_index) + String(index)"
                    @change="onValueChanged(custom_id.inj_time + String(station_index), index)"
                    type="number"
                    style="width: 8rem;"
                    v-model="optimize_detail.setting_process.injection.injection_time"
                    @input="optimize_detail.setting_process.injection.injection_time=$formatNumber(optimize_detail.setting_process.injection.injection_time)"
                  >
                    <span slot="suffix">s</span>
                  </el-input>
                </el-form-item>
                <el-form-item 
                  label="注射延迟"
                  prop="delay_time"
                >
                  <el-input
                    :id="custom_id.inj_delay + String(station_index) + String(index)"
                    @change="onValueChanged(custom_id.inj_delay + String(station_index), index)"
                    type="number"
                    style="width: 8rem;"
                    v-model="optimize_detail.setting_process.injection.delay_time"
                    @input="optimize_detail.setting_process.injection.delay_time=$formatNumber(optimize_detail.setting_process.injection.delay_time)"
                  >
                    <span slot="suffix">s</span>
                  </el-input>
                </el-form-item>
                <el-form-item 
                  label="冷却时间"
                  prop="cooling_time"
                >
                  <el-input
                    :id="custom_id.cool_time + String(station_index) + String(index)"
                    @change="onValueChanged(custom_id.cool_time + String(station_index), index)"
                    type="number"
                    style="width: 8rem;"
                    v-model="optimize_detail.setting_process.injection.cooling_time"
                    @input="optimize_detail.setting_process.injection.cooling_time=$formatNumber(optimize_detail.setting_process.injection.cooling_time)"
                  >
                    <span slot="suffix">s</span>
                  </el-input>
                </el-form-item>
                <el-divider content-position="center">
                  <span>VP切换</span>
                </el-divider>
                <el-form-item 
                  label="切换方式"
                  prop="mode"
                >
                  <el-select
                    :id="custom_id.vp_mode + String(station_index) + String(index)"
                    @change="(value) => onValueChanged(custom_id.vp_mode + String(station_index), index, value)"
                    style="width: 8rem;"
                    v-model="optimize_detail.setting_process.vp_switch.mode"
                    placeholder="请选择"
                  >
                    <el-option
                      v-for="option in VP_switch_mode_option"
                      :key="option.value"
                      :label="option.label"
                      :value="option.value"
                    >
                    </el-option>
                  </el-select>
                </el-form-item>
                <br />
                <el-form-item 
                  label="切换时间"
                  prop="time"
                >
                  <el-input
                    :id="custom_id.vp_time + String(station_index) + String(index)"
                    @change="onValueChanged(custom_id.vp_time + String(station_index), index)"
                    type="number"
                    style="width: 8rem;"
                    v-model="optimize_detail.setting_process.vp_switch.time" 
                    :disabled="optimize_detail.setting_process.vp_switch.mode == null
                      || optimize_detail.setting_process.vp_switch.mode.indexOf('时间') == -1"
                    @input="optimize_detail.setting_process.vp_switch.time=$formatNumber(optimize_detail.setting_process.vp_switch.time)"
                  >
                    <span slot="suffix">s</span>
                  </el-input>
                </el-form-item>
                <el-form-item 
                  label="切换位置"
                  prop="position"
                >
                  <el-input
                    :id="custom_id.vp_posi + String(station_index) + String(index)"
                    @change="onValueChanged(custom_id.vp_posi + String(station_index), index)"
                    type="number"
                    style="width: 8rem;"
                    v-model="optimize_detail.setting_process.vp_switch.position" 
                    :disabled="optimize_detail.setting_process.vp_switch.mode == null
                      || optimize_detail.setting_process.vp_switch.mode.indexOf('位置') == -1"
                    @input="optimize_detail.setting_process.vp_switch.position=$formatNumber(optimize_detail.setting_process.vp_switch.position)"
                  >
                    <span slot="suffix">mm</span>
                  </el-input>
                </el-form-item>
                <el-form-item 
                  label="切换压力"
                  prop="pressure"
                >
                  <el-input
                    :id="custom_id.vp_pres + String(station_index) + String(index)"
                    @change="onValueChanged(custom_id.vp_pres + String(station_index), index)"
                    type="number"
                    style="width: 8rem;"
                    v-model="optimize_detail.setting_process.vp_switch.pressure" 
                    :disabled="optimize_detail.setting_process.vp_switch.mode == null
                      || optimize_detail.setting_process.vp_switch.mode.indexOf('压力') == -1"
                    @input="optimize_detail.setting_process.vp_switch.pressure=$formatNumber(optimize_detail.setting_process.vp_switch.pressure)"
                  >
                    <span slot="suffix">{{ machine_info.pressure_unit }}</span>
                  </el-input>
                </el-form-item>
                <el-form-item 
                  label="切换速度"
                  prop="velocity"
                >
                  <el-input
                    :id="custom_id.vp_velo + String(station_index) + String(index)"
                    @change="onValueChanged(custom_id.vp_velo + String(station_index), index)"
                    type="number"
                    style="width: 8rem;"
                    v-model="optimize_detail.setting_process.vp_switch.velocity" 
                    :disabled="optimize_detail.setting_process.vp_switch.mode == null
                      || optimize_detail.setting_process.vp_switch.mode.indexOf('速度') == -1"
                    @input="optimize_detail.setting_process.vp_switch.velocity=$formatNumber(optimize_detail.setting_process.vp_switch.velocity)"
                  >
                    <span slot="suffix">{{ machine_info.velocity_unit }}</span>
                  </el-input>
                </el-form-item>
                <el-table 
                  size="mini"
                  :data="optimize_detail.setting_process.holding.table_data" 
                  :key="optimize_detail.setting_process.holding.stage + 40 + String(index)"
                >
                  <el-table-column 
                    label="工艺参数"
                    width="90" 
                    align="center"
                  >
                    <template #header>
                      <div>保压段数</div>
                      <el-select 
                        v-model="optimize_detail.setting_process.holding.stage" 
                        size="mini"
                        style="width: 100%;"
                      >
                        <el-option
                          v-for="(option, idx) in optimize_detail.setting_process.holding.max_stage"
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
                  <template v-for="(col, col_idx) in optimize_detail.setting_process.holding.max_stage">
                    <el-table-column
                      :key="col_idx"
                      :label="holding_stage_header[col]"
                      min-width="80"
                      align="center"
                    >
                      <template #default="scope">
                        <el-input 
                          :id="custom_id.holding[scope.$index][col_idx] + String(station_index) + String(index)"
                          @change="onValueChanged(custom_id.holding[scope.$index][col_idx] + String(station_index), index)"
                          v-model="scope.row.sections[col_idx]" 
                          :disabled="col > optimize_detail.setting_process.holding.stage"
                          type="number"
                          size="mini"
                          style="width: 100%;"
                          @input="scope.row.sections[col_idx]=$formatNumber(scope.row.sections[col_idx])"
                        >
                        </el-input>
                      </template>
                    </el-table-column>
                  </template>
                  <el-table-column
                    label="单位"
                    min-width="80"
                    align="center"
                  >
                    <template #default="scope">
                      {{ scope.row.unit }}
                    </template>
                  </el-table-column>
                </el-table>
              </el-card>
            </el-col>
            <el-col :xs="24" :lg="11" :xl="11">
              <el-card class="box-card" style="min-height: 750px">
                <el-table 
                  size="mini"
                  :data="optimize_detail.setting_process.metering.table_data"
                  :key="optimize_detail.setting_process.metering.stage + 60 + String(index)"
                >
                  <el-table-column 
                    label="工艺参数"
                    width="90" 
                    align="center"
                  >
                    <template #header>
                      <div>计量段数</div>
                      <el-select 
                        v-model="optimize_detail.setting_process.metering.stage" 
                        size="mini"
                        style="width: 100%;"
                      >
                        <el-option
                          v-for="(option, idx) in optimize_detail.setting_process.metering.max_stage"
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
                  <template v-for="(col, col_idx) in optimize_detail.setting_process.metering.max_stage">
                    <el-table-column
                      :key="col_idx"
                      :label="metering_stage_header[col]"
                      min-width="80"
                      align="center"
                    >
                      <template #default="scope">
                        <el-input 
                          :id="custom_id.metering[scope.$index][col_idx] + String(station_index) + String(index)"
                          @change="onValueChanged(custom_id.metering[scope.$index][col_idx] + String(station_index), index)"
                          v-model="scope.row.sections[col_idx]" 
                          :disabled="col > optimize_detail.setting_process.metering.stage"
                          type="number"
                          size="mini"
                          style="width: 100%;"
                          @input="scope.row.sections[col_idx]=$formatNumber(scope.row.sections[col_idx])"
                        >
                        </el-input>
                      </template>
                    </el-table-column>
                  </template>
                  <el-table-column
                    label="单位"
                    min-width="80"
                    align="center"
                  >
                    <template #default="scope">
                      {{ scope.row.unit }}
                    </template>
                  </el-table-column>
                </el-table>
                <div style="height:15px" />
                <el-form-item 
                  label="储前松退模式"
                  prop="pre_decompress_mode"
                  label-width="7.2rem"
                >
                  <el-select 
                    :id="custom_id.dec_bef_mode + String(station_index) + String(index)"
                    @change="(value) => onValueChanged(custom_id.dec_bef_mode + String(station_index), index, value)"
                    v-model="optimize_detail.setting_process.metering.pre_decompress_mode"
                    style="width: 8rem"
                  >
                    <el-option
                      v-for="option, idx in decompressure_mode"
                      :key="idx"
                      :label="option.label"
                      :value="option.value"
                    >
                    </el-option>
                  </el-select>
                </el-form-item>
                <br>
                <el-form-item 
                  label="储后松退模式"
                  label-width="7.2rem"
                >
                  <el-select 
                    :id="custom_id.dec_aft_mode + String(station_index) + String(index)"
                    @change="(value) => onValueChanged(custom_id.dec_aft_mode + String(station_index), index, value)"
                    v-model="optimize_detail.setting_process.metering.post_decompress_mode"
                    style="width: 8rem"
                  >
                    <el-option
                      v-for="option, idx in decompressure_mode"
                      :key="idx"
                      :label="option.label"
                      :value="option.value"
                    >
                    </el-option>
                  </el-select>
                </el-form-item>
                <el-table
                  size="mini"
                  :data="optimize_detail.setting_process.metering.decompress_table_data"
                >
                  <el-table-column
                    label="模式"
                    width="60"
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
                    <template #default="scope">
                      <el-input
                        :id="custom_id.dec_pres[scope.$index] + String(station_index) + String(index)"
                        @change="onValueChanged(custom_id.dec_pres[scope.$index] + String(station_index), index)"
                        :disabled="((scope.$index === 0 && optimize_detail.setting_process.metering.pre_decompress_mode === '否')
                          || (scope.$index === 1 && optimize_detail.setting_process.metering.post_decompress_mode === '否'))"
                        v-model="scope.row.pressure"
                        size="mini"
                        style="width: 100%;"
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
                    <template #default="scope">
                      <el-input
                        :id="custom_id.dec_velo[scope.$index] + String(station_index) + String(index)"
                        @change="onValueChanged(custom_id.dec_velo[scope.$index] + String(station_index), index)"
                        :disabled="((scope.$index === 0 && optimize_detail.setting_process.metering.pre_decompress_mode === '否')
                          || (scope.$index === 1 && optimize_detail.setting_process.metering.post_decompress_mode === '否'))"
                        v-model="scope.row.velocity"
                        size="mini"
                        style="width: 100%;"
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
                    <template #default="scope">
                      <el-input
                        :id="custom_id.dec_dist[scope.$index] + String(station_index) + String(index)"
                        @change="onValueChanged(custom_id.dec_dist[scope.$index] + String(station_index), index)"
                        :disabled="((scope.$index === 0 && optimize_detail.setting_process.metering.pre_decompress_mode != '距离')
                          || (scope.$index === 1 && optimize_detail.setting_process.metering.post_decompress_mode != '距离'))"
                        v-model="scope.row.distance"
                        size="mini"
                        style="width: 100%;"
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
                    <template #default="scope">
                      <el-input
                        :id="custom_id.dec_time[scope.$index] + String(station_index) + String(index)"
                        @change="onValueChanged(custom_id.dec_time[scope.$index] + String(station_index), index)"
                        :disabled="((scope.$index === 0 && optimize_detail.setting_process.metering.pre_decompress_mode != '时间')
                          || (scope.$index === 1 && optimize_detail.setting_process.metering.post_decompress_mode != '时间'))"
                        v-model="scope.row.time"
                        size="mini"
                        style="width: 100%;"
                        @input="scope.row.time=$formatNumber(scope.row.time)"
                      >
                      </el-input>
                    </template>
                  </el-table-column>
                </el-table>
                <div style="height:15px" />
                <el-form-item 
                  label="储料延迟"
                  prop="delay_time"
                  label-width="7.2rem"
                >
                  <el-input
                    :id="custom_id.met_delay + String(station_index) + String(index)"
                    @change="onValueChanged(custom_id.met_delay + String(station_index), index)"
                    type="number"
                    v-model="optimize_detail.setting_process.metering.delay_time"
                    style="width: 8rem"
                    @input="optimize_detail.setting_process.metering.delay_time=$formatNumber(optimize_detail.setting_process.metering.delay_time)"
                  >
                    <span slot="suffix">s</span>
                  </el-input>
                </el-form-item>
                <br>
                <el-form-item 
                  label="终止位置"
                  prop="ending_position"
                  label-width="7.2rem"
                >
                  <el-input
                    :id="custom_id.stp_pos + String(station_index) + String(index)"
                    @change="onValueChanged(custom_id.stp_pos + String(station_index), index)"
                    type="number"
                    v-model="optimize_detail.setting_process.metering.ending_position"
                    style="width: 8rem"
                    @input="optimize_detail.setting_process.metering.ending_position=$formatNumber(optimize_detail.setting_process.metering.ending_position)"
                  >
                    <span slot="suffix">mm</span>
                  </el-input>
                </el-form-item>
              </el-card>
            </el-col>
            <el-col :xs="24" :lg="24" :xl="24">
              <el-card class="box-card">
                <el-table 
                  size="mini"
                  :data="optimize_detail.setting_process.barrel_temperature.table_data"
                  :key="optimize_detail.setting_process.barrel_temperature.stage + 80 + String(index)"
                >
                  <el-table-column 
                    label="工艺参数"
                    width="90" 
                    align="center"
                  >
                    <template #header>
                      <div>温度段数</div>
                      <el-select 
                        v-model="optimize_detail.setting_process.barrel_temperature.stage" 
                        size="mini"
                        style="width: 100%;"
                      >
                        <el-option
                          v-for="(option, idx) in optimize_detail.setting_process.barrel_temperature.max_stage"
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
                  <template v-for="(col, col_idx) in optimize_detail.setting_process.barrel_temperature.max_stage">
                    <el-table-column
                      :key="col_idx"
                      :label="temp_stage_header[col]"
                      min-width="80"
                      align="center"
                    >
                      <template #default="scope">
                        <el-input 
                          :id="custom_id.barl_temp[col_idx] + String(station_index) + String(index)"
                          @change="onValueChanged(custom_id.barl_temp[col_idx] + String(station_index), index)"
                          v-model="scope.row.sections[col_idx]" 
                          :disabled="col > optimize_detail.setting_process.barrel_temperature.stage"
                          type="number" 
                          size="mini"
                          style="width: 100%;"
                          @input="scope.row.sections[col_idx]=$formatNumber(scope.row.sections[col_idx])"
                        >
                        </el-input>
                      </template>
                    </el-table-column>
                  </template>
                  <el-table-column
                    label="单位"
                    min-width="80"
                    align="center"
                  >
                    <template #default="scope">
                      {{ scope.row.unit }}
                    </template>
                  </el-table-column>
                </el-table>
              </el-card>
            </el-col>
          </el-form>
          <el-card class="box-card">
            <div slot="header" class="clearfix">
              <span>实时参数</span>
            </div>
            <el-form
              size="mini"
              label-width="6rem"
              :inline="true"
            >
              <el-form-item 
                label="实际重量" 
                prop="actual_product_weight"
              >
                <el-input 
                  v-model="optimize_detail.realtime_info.actual_product_weight" 
                  style="width:8rem"
                  @input="optimize_detail.realtime_info.actual_product_weight=$formatNumber(optimize_detail.feedback_detail.actual_product_weight)"
                >
                  <span slot="suffix">g</span>
                </el-input>
              </el-form-item>
              <el-form-item 
                label="峰值压力" 
                prop="peak_pressure"
              >
                <el-input 
                  v-model="optimize_detail.realtime_info.peak_pressure" 
                  style="width:8rem"
                  @input="optimize_detail.realtime_info.peak_pressure=$formatNumber(optimize_detail.feedback_detail.peak_pressure)"
                >
                  <span slot="suffix">{{ machine_info.pressure_unit }}</span>
                </el-input>
              </el-form-item>
            </el-form>
          </el-card>
          <el-card class="box-card">
            <div slot="header" class="clearfix">
              <span>缺陷反馈</span>
              <span style="color:red"> 当前规则：{{ optimize_detail.optimize_record.rule_description }} </span>
            </div>
            <el-form
              class="defect-feedback"
              :inline="true" 
              :model="optimize_detail.defect_feedback" 
              size="mini" 
              label-width="6rem"
            >
              <el-form-item
                v-for="defect in defect_options"
                :key="defect.value"
                :label="defect.label"
                :prop="defect.value"
              >
                <el-select
                  v-model="optimize_detail.defect_feedback[defect.value].level"
                  placeholder="请选择"
                >
                  <el-option label="无缺陷" value="无缺陷"></el-option>
                  <el-option label="轻微" value="轻微"></el-option>
                  <el-option label="中等" value="中等"></el-option>
                  <el-option label="严重" value="严重"></el-option>
                  <el-option label="非常严重" value="非常严重"></el-option>
                </el-select>
                <el-select
                  v-model="optimize_detail.defect_feedback[defect.value].position"
                  placeholder="请选择"
                  :disabled="optimize_detail.defect_feedback[defect.value].level == '无缺陷'"
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
                  v-if="optimize_detail.name != '0' && optimize_detail.defect_feedback[defect.value].feedback != null"
                  v-model="optimize_detail.defect_feedback[defect.value].feedback"
                  placeholder="请选择"
                >
                  <el-option label="上一模修正效果佳" value="上一模修正效果佳"></el-option>
                  <el-option label="上一模修正效果不佳" value="上一模修正效果不佳"></el-option>
                </el-select>
              </el-form-item>
            </el-form>
          </el-card>
        </el-tab-pane>
      </el-tabs>
    </el-row>
  </div>
</template>

<script>
import { polymerMethod } from "@/api";
import SuggestionOptions from "@/mixins/suggestionOptions.vue";
import CastingSystemProductDetail from "./castingSystemProductDetail.vue";

export default {
  name: "InjectionStationDetail",
  mixins: [ SuggestionOptions ],
  components: { CastingSystemProductDetail },
  props: {
    stationIndex: {
      type: Number,
      default: 0
    },
    injectionStationDetail: {
      type: Object,
      default: () => {}
    },
    machineInfo: {
      type: Object,
      default: () => {}
    }
  },
  data() {
    return {
      detail_info: this.injectionStationDetail,
      machine_info: this.machineInfo,
      station_index: this.stationIndex,
      actived_tab_index: "0",
      injection_stage_header: [ "注射段数", "一段", "二段", "三段", "四段", "五段", "六段" ],
      holding_stage_header: [ "保压段数", "一段", "二段", "三段", "四段", "五段" ],
      metering_stage_header: [ "计量段数", "一段", "二段", "三段", "四段" ],
      temp_stage_header: [ "温度段数", "喷嘴", "一段", "二段", "三段", "四段", "五段", "六段", "七段", "八段", "九段" ],
      VP_switch_mode_option: [
        { label: "位置", value: "位置" },
        { label: "时间", value: "时间" },
        { label: "时间&位置", value: "时间&位置" },
        { label: "压力", value: "压力" },
        { label: "速度", value: "速度" }
      ],
      decompressure_mode: [
        { label: "否", value: "否" },
        { label: "距离", value: "距离" },
        { label: "时间", value: "时间" },
      ],
      defect_options: [ 
        { label: "短射", value: "short_shot" },
        { label: "飞边", value: "flash" },
        { label: "缩水", value: "shrinkage" },
        { label: "熔接线", value: "weld_line" },
        { label: "色差", value: "aberration" },
        { label: "困气", value: "air_trap" },
        { label: "气纹", value: "gas_veins" },
        { label: "料花", value: "material_flower" }
      ],
      defect_position_options: [
        { label: "缺陷位置不指定", value: "缺陷位置不指定" },
        { label: "缺陷位置在1段", value: "缺陷位置在1段" },
        { label: "缺陷位置在2段", value: "缺陷位置在2段" },
        { label: "缺陷位置在3段", value: "缺陷位置在3段" },
        { label: "缺陷位置在4段", value: "缺陷位置在4段" },
      ],
      custom_id: {
        injection: [
          [ "IP0", "IP1", "IP2", "IP3", "IP4", "IP5" ],
          [ "IV0", "IV1", "IV2", "IV3", "IV4", "IV5" ],
          [ "IL0", "IL1", "IL2", "IL3", "IL4", "IL5" ]
        ],
        inj_time: "IT",
        inj_delay: "ID",
        cool_time: "CT",
        vp_mode: "VPTM",
        vp_time: "VPTT",
        vp_posi: "VPTL",
        vp_pres: "VPTP",
        vp_velo: "VPTV",
        holding: [
          [ "PP0", "PP1", "PP2", "PP3", "PP4" ],
          [ "PV0", "PV1", "PV2", "PV3", "PV4" ],
          [ "PT0", "PT1", "PT2", "PT3", "PT4" ]
        ],
        metering: [
          [ "MP0", "MP1", "MP2", "MP3" ],
          [ "MSR0", "MSR1", "MSR2", "MSR3" ],
          [ "MBP0", "MBP1", "MBP2", "MBP3" ],
          [ "ML0", "ML1", "ML2", "ML3" ]
        ],
        dec_bef_mode: "DMBM",
        dec_aft_mode: "DMAM",
        dec_pres: [ "DPBM", "DPAM" ],
        dec_velo: [ "DVBM", "DVAM" ],
        dec_dist: [ "DDBM", "DDAM" ],
        dec_time: [ "DTBM", "DTAM" ],
        met_delay: "MD",
        stp_pos: "MEL",
        barl_temp: [ "NT", "BT1", "BT2", "BT3", "BT4", "BT5", "BT6", "BT7", "BT8", "BT9" ]
      },
    }
  },
  methods: {
    async querySuggestionOptions(input_str, cb, db_column) {
      let selections = [];
      if ("manufacturer" == db_column) {
        selections = await this.queryOptions(input_str, "polymer", "manufacturer");
      } else if ("abbreviation" == db_column) {
        selections = await this.queryOptions(input_str, "polymer", "abbreviation", {
          "manufacturer": this.detail_info.polymer_detail.manufacturer
        });
      } else if ("trademark" == db_column) {
        selections = await this.queryOptions(input_str, "polymer", "trademark", {
          "manufacturer": this.detail_info.polymer_detail.manufacturer,
          "abbreviation": this.detail_info.polymer_detail.abbreviation
        });
      }
      cb(selections);
    },
    onTrademarkSelected(item) {
      polymerMethod.getDetail(item.id)
      .then( res => {
        if (res.status === 0) {
          let polymer_detail = this.detail_info.polymer_detail;
          Object.keys(polymer_detail).forEach((key) => {
            if (Object.keys(res.data).includes(key)) {
              polymer_detail[key] = res.data[key];
            }
          });
        }
      })
    },
    setElementStyle(element, unequal = false) {
      if (unequal) {
        element.style.backgroundColor = "green";
        element.style.color = "white";
      } else {
        element.style.backgroundColor = "white";
        element.style.color = "black";
      }
    },
    onValueChanged(id, tab_idx, value = null) {
      // console.log(value)
      if (tab_idx > 0) {
        let curr_elem = document.getElementById(id + String(tab_idx));
        let last_elem = document.getElementById(id + String(tab_idx - 1));
        if (curr_elem && last_elem) {
          let unequal = false;
          if (value != null) {
            unequal = value != last_elem.value;
          } else {
            unequal = curr_elem.value != last_elem.value;
          }
          this.setElementStyle(curr_elem, unequal);
        }
      }
    },
    compareValueEqual(id, unequal = false) {
      let element = document.getElementById(id);
      if (!element) return;
      this.setElementStyle(element, unequal)
    },
    hightlightChanged(tab_idx) {
      if (tab_idx > 0) {
        let curr_tab = this.detail_info.optimize_list[tab_idx].setting_process;
        let last_tab = this.detail_info.optimize_list[tab_idx - 1].setting_process;

        // 校验界面是否渲染
        if (!document.getElementById(String(this.custom_id.stp_pos + this.station_index + tab_idx))) {
          setTimeout(() => {
            this.hightlightChanged(tab_idx)
          }, 200);
        }

        // 注射参数
        for (let i = 0; i < 3; ++i) {
          for (let j = 0; j < 6; ++j) {
            this.compareValueEqual(String(this.custom_id.injection[i][j] + this.station_index + tab_idx), 
              last_tab.injection.table_data[i].sections[j] != curr_tab.injection.table_data[i].sections[j]);
          }
        }
        // 注射时间
        this.compareValueEqual(String(this.custom_id.inj_time + this.station_index + tab_idx),
          last_tab.injection.injection_time != curr_tab.injection.injection_time);
        // 注射延时
        this.compareValueEqual(String(this.custom_id.inj_delay + this.station_index + tab_idx),
          last_tab.injection.delay_time != curr_tab.injection.delay_time);
        // 冷却时间
        this.compareValueEqual(String(this.custom_id.cool_time + this.station_index + tab_idx),
          last_tab.injection.cooling_time != curr_tab.injection.cooling_time);

        // 切换模式
        this.compareValueEqual(String(this.custom_id.vp_mode + this.station_index + tab_idx),
          last_tab.vp_switch.mode != curr_tab.vp_switch.mode);
        // 切换时间
        this.compareValueEqual(String(this.custom_id.vp_time + this.station_index + tab_idx),
          last_tab.vp_switch.time != curr_tab.vp_switch.time);
        // 切换位置
        this.compareValueEqual(String(this.custom_id.vp_posi + this.station_index + tab_idx),
          last_tab.vp_switch.position != curr_tab.vp_switch.position);
        // 切换压力
        this.compareValueEqual(String(this.custom_id.vp_pres + this.station_index + tab_idx),
          last_tab.vp_switch.pressure != curr_tab.vp_switch.pressure);
        // 切换速度
        this.compareValueEqual(String(this.custom_id.vp_velo + this.station_index + tab_idx),
          last_tab.vp_switch.velocity != curr_tab.vp_switch.velocity);

        // 保压参数
        for (let i = 0; i < 3; ++i) {
          for (let j = 0; j < 5; ++j) {
            this.compareValueEqual(String(this.custom_id.holding[i][j] + this.station_index + tab_idx), 
              last_tab.holding.table_data[i].sections[j] != curr_tab.holding.table_data[i].sections[j]);
          }
        }

        // 计量参数
        for (let i = 0; i < 4; ++i) {
          for (let j = 0; j < 4; ++j) {
            this.compareValueEqual(String(this.custom_id.metering[i][j] + this.station_index + tab_idx), 
              last_tab.metering.table_data[i].sections[j] != curr_tab.metering.table_data[i].sections[j]);
          }
        }
        
        // 储前射退模式
        this.compareValueEqual(String(this.custom_id.dec_bef_mode + this.station_index + tab_idx),
          last_tab.metering.pre_decompress_mode != curr_tab.metering.pre_decompress_mode);
        // 储后射退模式
        this.compareValueEqual(String(this.custom_id.dec_aft_mode + this.station_index + tab_idx),
          last_tab.metering.post_decompress_mode != curr_tab.metering.post_decompress_mode);
        // 松退参数
        for (let i = 0; i < 2; ++i) {
          // 松退压力
          this.compareValueEqual(String(this.custom_id.dec_pres[i] + this.station_index + tab_idx),
            last_tab.metering.decompress_table_data[i].pressure != curr_tab.metering.decompress_table_data[i].pressure);
          // 松退速度
          this.compareValueEqual(String(this.custom_id.dec_velo[i] + this.station_index + tab_idx),
            last_tab.metering.decompress_table_data[i].velocity != curr_tab.metering.decompress_table_data[i].velocity);
          // 松退距离
          this.compareValueEqual(String(this.custom_id.dec_dist[i] + this.station_index + tab_idx),
            last_tab.metering.decompress_table_data[i].distance != curr_tab.metering.decompress_table_data[i].distance);
          // 松退时间
          this.compareValueEqual(String(this.custom_id.dec_time[i] + this.station_index + tab_idx),
            last_tab.metering.decompress_table_data[i].time != curr_tab.metering.decompress_table_data[i].time);
        }
        // 储料延时
        this.compareValueEqual(String(this.custom_id.met_delay + this.station_index + tab_idx),
          last_tab.metering.delay_time != curr_tab.metering.delay_time);
        // 储料终止位置
        this.compareValueEqual(String(this.custom_id.stp_pos + this.station_index + tab_idx),
          last_tab.metering.ending_position != curr_tab.metering.ending_position);
        
        // 温度参数
        for (let j = 0; j < 10; ++j) {
          this.compareValueEqual(String(this.custom_id.barl_temp[j] + this.station_index + tab_idx), 
            last_tab.barrel_temperature.table_data[0].sections[j] != curr_tab.barrel_temperature.table_data[0].sections[j]);
        }
      }
    }
  },
  computed: {

  },
  watch: {
    injectionStationDetail: {
      handler: function() {
        this.detail_info = this.injectionStationDetail;
      },
      deep: true
    },
    machineInfo: {
      handler: function() {
        this.machine_info = this.machineInfo;
      },
      deep: true
    },
    actived_tab_index() {
      this.hightlightChanged(Number(this.actived_tab_index));
    }
  }
}
</script>

<style lang="scss" scoped>
.el-autocomplete {
  width: 10rem;
}
.el-input {
  width: 10rem;
}
</style>