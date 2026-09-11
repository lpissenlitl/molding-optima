<!--
  SettingProcess - 工艺参数设定卡

  业务含义：
    - 注射（6 段：压力/速度/位置）+ VP 切换 + 保压（5 段：压力/速度/时间）
    - 熔胶（4 段：压力/螺杆转速/背压/位置）+ 松退（储前/储后）
    - 料筒温度（10 段：喷嘴 + 9 段料筒温度）

  数据结构（与后端 process/services/process_transformer.py 严格对应）：
    setting_process = {
      injection: { stage, max_stage, table_data: [...], injection_time, delay_time, cooling_time },
      vp_switch:  { mode, position, time, pressure, velocity },
      holding:    { stage, max_stage, table_data: [...] },
      metering:   { stage, max_stage, table_data: [...], decompress_table_data: [...], ... },
      barrel_temperature: { stage, max_stage, table_data: [...] }
    }

  模式：
    - 0 位置 / 1 时间 / 2 时间&位置 / 3 压力 / 4 速度（VP 切换）
    - 0 否 / 1 距离 / 2 时间（松退）

  单位系统（machine_info 传入）：
    - pressure_unit / speed_unit / screw_rotation_unit / back_pressure_unit
-->
<template>
  <el-row>
    <!-- 左列：注射 + VP + 保压 -->
    <el-col :xs="24" :lg="13" :xl="13">
      <el-card class="box-card" style="min-height: 750px">
        <!-- 注射段 -->
        <el-table
          class="simple-table"
          size="small"
          :data="injection.table_data"
          :key="`injection_${injection.stage}`"
        >
          <el-table-column
            label="工艺参数"
            width="120"
            align="left"
          >
            <template #header>
              <div>注射段数</div>
              <el-select
                v-model="injection.stage"
                size="small"
                style="width: 100%;"
              >
                <el-option
                  v-for="option in injection.max_stage"
                  :key="option"
                  :label="option"
                  :value="option"
                />
              </el-select>
            </template>
            <template #default="scope">
              {{ scope.row.label }} [{{ scope.row.unit }}]
            </template>
          </el-table-column>
          <el-table-column
            v-for="(col, col_idx) in injection.max_stage"
            :key="`inj_${col_idx}`"
            min-width="80"
            align="center"
            :label="STG_HEADER[col]"
          >
            <template #default="scope">
              <el-input
                v-model="scope.row.sections[col_idx]"
                v-number
                size="small"
                style="width: 100%;"
                :disabled="col > injection.stage"
              />
            </template>
          </el-table-column>
        </el-table>

        <br />

        <!-- 注射时间/延时/冷却 -->
        <el-form size="small" :model="injection" :inline="true">
          <el-form-item label="注射时间" prop="injection_time">
            <el-input
              style="width: 8rem;"
              v-model="injection.injection_time"
              v-number
            >
              <template #suffix>s</template>
            </el-input>
          </el-form-item>
          <el-form-item label="注射延迟" prop="delay_time">
            <el-input
              style="width: 8rem;"
              v-model="injection.delay_time"
              v-number
            >
              <template #suffix>s</template>
            </el-input>
          </el-form-item>
          <el-form-item label="冷却时间" prop="cooling_time">
            <el-input
              style="width: 8rem;"
              v-model="injection.cooling_time"
              v-number
            >
              <template #suffix>s</template>
            </el-input>
          </el-form-item>
        </el-form>

        <!-- VP 切换 -->
        <el-form size="small" :model="vp_switch" :inline="true">
          <el-divider content-position="center">
            <span>VP切换</span>
          </el-divider>
          <el-form-item label="切换方式" prop="mode">
            <el-select
              style="width: 8rem;"
              v-model="vp_switch.mode"
              placeholder="请选择"
            >
              <el-option
                v-for="option in VPS_MODE_OPTIONS"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
          </el-form-item>
          <br />
          <el-form-item label="切换位置" prop="position">
            <el-input
              v-number
              v-model="vp_switch.position"
              style="width: 8rem;"
              :disabled="isSwitchModeDisabled('position')"
            >
              <template #suffix>mm</template>
            </el-input>
          </el-form-item>
          <el-form-item label="切换时间" prop="time">
            <el-input
              v-number
              v-model="vp_switch.time"
              style="width: 8rem;"
              :disabled="isSwitchModeDisabled('time')"
            >
              <template #suffix>s</template>
            </el-input>
          </el-form-item>
          <el-form-item label="切换压力" prop="pressure">
            <el-input
              v-number
              v-model="vp_switch.pressure"
              style="width: 8rem;"
              :disabled="isSwitchModeDisabled('pressure')"
            >
              <template #suffix>{{ pressure_unit }}</template>
            </el-input>
          </el-form-item>
          <el-form-item label="切换速度" prop="velocity">
            <el-input
              v-number
              v-model="vp_switch.velocity"
              style="width: 8rem;"
              :disabled="isSwitchModeDisabled('velocity')"
            >
              <template #suffix>{{ speed_unit }}</template>
            </el-input>
          </el-form-item>
        </el-form>

        <!-- 保压段 -->
        <el-table
          class="simple-table"
          size="small"
          :data="holding.table_data"
          :key="`holding_${holding.stage}`"
        >
          <el-table-column
            label="工艺参数"
            width="120"
            align="left"
          >
            <template #header>
              <div>保压段数</div>
              <el-select
                v-model="holding.stage"
                size="small"
                style="width: 100%;"
              >
                <el-option
                  v-for="option in holding.max_stage"
                  :key="option"
                  :label="option"
                  :value="option"
                />
              </el-select>
            </template>
            <template #default="scope">
              {{ scope.row.label }} [{{ scope.row.unit }}]
            </template>
          </el-table-column>
          <el-table-column
            v-for="(col, col_idx) in holding.max_stage"
            :key="`hold_${col_idx}`"
            :label="HOLD_STG_HEADER[col]"
            min-width="80"
            align="center"
          >
            <template #default="scope">
              <el-input
                v-number
                v-model="scope.row.sections[col_idx]"
                size="small"
                style="width: 100%;"
                :disabled="col > holding.stage"
              />
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </el-col>

    <!-- 右列：熔胶 + 松退 + 终止位置 -->
    <el-col :xs="24" :lg="11" :xl="11">
      <el-card class="box-card" style="min-height: 750px">
        <!-- 熔胶段 -->
        <el-table
          class="simple-table"
          size="small"
          :data="metering.table_data"
          :key="`metering_${metering.stage}`"
        >
          <el-table-column
            label="工艺参数"
            width="140"
            align="left"
          >
            <template #header>
              <div>计量段数</div>
              <el-select
                v-model="metering.stage"
                size="small"
                style="width: 100%;"
              >
                <el-option
                  v-for="option in metering.max_stage"
                  :key="option"
                  :label="option"
                  :value="option"
                />
              </el-select>
            </template>
            <template #default="scope">
              {{ scope.row.label }} [{{ scope.row.unit }}]
            </template>
          </el-table-column>
          <el-table-column
            v-for="(col, col_idx) in metering.max_stage"
            :key="`met_${col_idx}`"
            :label="MET_STG_HEADER[col]"
            min-width="80"
            align="center"
          >
            <template #default="scope">
              <el-input
                v-model="scope.row.sections[col_idx]"
                v-number
                :disabled="col > metering.stage"
                size="small"
                style="width: 100%;"
              />
            </template>
          </el-table-column>
        </el-table>

        <br />

        <!-- 松退模式选择 -->
        <el-form size="small" :model="metering">
          <el-form-item label="储前松退模式" prop="pre_decompress_mode">
            <el-select
              v-model="metering.pre_decompress_mode"
              style="width: 8rem"
            >
              <el-option
                v-for="(option, idx) in DECOMP_MODE_OPTIONS"
                :key="idx"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="储后松退模式" prop="post_decompress_mode">
            <el-select
              v-model="metering.post_decompress_mode"
              style="width: 8rem"
            >
              <el-option
                v-for="(option, idx) in DECOMP_MODE_OPTIONS"
                :key="idx"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
          </el-form-item>
        </el-form>

        <!-- 松退参数表 -->
        <el-table
          class="simple-table"
          size="small"
          :data="metering.decompress_table_data"
        >
          <el-table-column label="段数" width="60" align="center">
            <template #default="scope">
              {{ scope.row.label }}
            </template>
          </el-table-column>
          <el-table-column label="压力" min-width="80" align="center">
            <template #header>
              <div>压力</div>
              <div>[MPa]</div>
            </template>
            <template #default="scope">
              <el-input
                v-model="scope.row.pressure"
                v-number
                size="small"
                style="width: 100%;"
                :disabled="isDecompressDisabled(scope.$index, 'pressure')"
              />
            </template>
          </el-table-column>
          <el-table-column label="速度" min-width="80" align="center">
            <template #header>
              <div>速度</div>
              <div>[mm/s]</div>
            </template>
            <template #default="scope">
              <el-input
                v-number
                v-model="scope.row.velocity"
                size="small"
                style="width: 100%;"
                :disabled="isDecompressDisabled(scope.$index, 'velocity')"
              />
            </template>
          </el-table-column>
          <el-table-column label="距离" min-width="80" align="center">
            <template #header>
              <div>距离</div>
              <div>[mm]</div>
            </template>
            <template #default="scope">
              <el-input
                v-number
                v-model="scope.row.distance"
                size="small"
                style="width: 100%;"
                :disabled="isDecompressDisabled(scope.$index, 'distance')"
              />
            </template>
          </el-table-column>
          <el-table-column label="时间" min-width="80" align="center">
            <template #header>
              <div>时间</div>
              <div>[s]</div>
            </template>
            <template #default="scope">
              <el-input
                v-number
                v-model="scope.row.time"
                size="small"
                style="width: 100%;"
                :disabled="isDecompressDisabled(scope.$index, 'time')"
              />
            </template>
          </el-table-column>
        </el-table>

        <br />

        <!-- 储料延迟 + 终止位置 -->
        <el-form size="small" :model="metering">
          <el-form-item label="储料延迟" prop="delay_time">
            <el-input
              v-model="metering.delay_time"
              v-number
              style="width: 8rem"
            >
              <template #suffix>s</template>
            </el-input>
          </el-form-item>
          <el-form-item label="终止位置" prop="ending_position">
            <el-input
              v-model="metering.ending_position"
              v-number
              style="width: 8rem"
            >
              <template #suffix>mm</template>
            </el-input>
          </el-form-item>
        </el-form>
      </el-card>
    </el-col>

    <!-- 底行：料筒温度 -->
    <el-col :xs="24" :lg="24" :xl="24">
      <el-card class="box-card">
        <el-table
          class="simple-table"
          size="small"
          :data="barrel_temperature.table_data"
          :key="`barrel_temperature_${barrel_temperature.stage}`"
        >
          <el-table-column
            label="工艺参数"
            width="90"
            align="center"
          >
            <template #header>
              <div>温度段数</div>
              <el-select
                v-model="barrel_temperature.stage"
                size="small"
                style="width: 100%;"
              >
                <el-option
                  v-for="option in barrel_temperature.max_stage"
                  :key="option"
                  :label="option"
                  :value="option"
                />
              </el-select>
            </template>
            <template #default="scope">
              {{ scope.row.label }} [{{ scope.row.unit }}]
            </template>
          </el-table-column>
          <el-table-column
            v-for="(col, col_idx) in barrel_temperature.max_stage"
            :key="`brl_${col_idx}`"
            :label="TEMP_STG_HEADER[col]"
            min-width="80"
            align="center"
          >
            <template #default="scope">
              <el-input
                v-number
                v-model="scope.row.sections[col_idx]"
                size="small"
                style="width: 100%;"
                :disabled="col > barrel_temperature.stage"
              />
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup lang="ts">
/**
 * SettingProcess 工艺参数设定卡（Vue 3 Composition API 版）
 *
 * - props.settingProcess: 嵌套结构的工艺参数（与后端 _construct_setting_process_frontend 对应）
 * - props.machineInfo: 设备信息（用于单位系统）
 * - 单位系统同步：watch props.machineInfo → 更新 injection/holding/metering 的 table_data 单位
 */
import { ref, computed, watch, reactive } from 'vue'
import { settingProcessForm } from '@/constants/process-const'

// ============================================================================
// 常量
// ============================================================================

const STG_HEADER: Record<number, string> = {
  1: '一段', 2: '二段', 3: '三段', 4: '四段', 5: '五段', 6: '六段',
}
const HOLD_STG_HEADER: Record<number, string> = {
  1: '一段', 2: '二段', 3: '三段', 4: '四段', 5: '五段',
}
const MET_STG_HEADER: Record<number, string> = {
  1: '一段', 2: '二段', 3: '三段', 4: '四段',
}
const TEMP_STG_HEADER: Record<number, string> = {
  1: '喷嘴', 2: '一段', 3: '二段', 4: '三段', 5: '四段', 6: '五段', 7: '六段', 8: '七段', 9: '八段', 10: '九段',
}

const VPS_MODE_OPTIONS = [
  { label: '位置', value: 0 },
  { label: '时间', value: 1 },
  { label: '时间&位置', value: 2 },
  { label: '压力', value: 3 },
  { label: '速度', value: 4 },
]

const DECOMP_MODE_OPTIONS = [
  { label: '否', value: 0 },
  { label: '距离', value: 1 },
  { label: '时间', value: 2 },
]

// ============================================================================
// Props
// ============================================================================

const props = defineProps<{
  settingProcess: any
  machineInfo?: any
}>()

// ============================================================================
// 响应式状态
// ============================================================================

const setting_process = reactive<any>(props.settingProcess ?? structuredClone(settingProcessForm))
const machine_info = reactive<any>(props.machineInfo ?? {})

const injection = computed(() => setting_process.injection)
const vp_switch = computed(() => setting_process.vp_switch)
const holding = computed(() => setting_process.holding)
const metering = computed(() => setting_process.metering)
const barrel_temperature = computed(() => setting_process.barrel_temperature)

const pressure_unit = computed(() => machine_info.pressure_unit || 'MPa')
const speed_unit = computed(() => machine_info.speed_unit || 'mm/s')

// ============================================================================
// 工具：判断输入是否禁用
// ============================================================================

/**
 * VP 切换：哪些字段在当前模式下不可用
 * - 0 位置：只有 position 可用
 * - 1 时间：只有 time 可用
 * - 2 时间&位置：position + time 可用
 * - 3 压力：只有 pressure 可用
 * - 4 速度：只有 velocity 可用
 */
function isSwitchModeDisabled(keyword: string): boolean {
  const mode = vp_switch.value.mode
  if ((mode === 0 || mode === 2) && keyword === 'position') return false
  if ((mode === 1 || mode === 2) && keyword === 'time') return false
  if (mode === 3 && keyword === 'pressure') return false
  if (mode === 4 && keyword === 'velocity') return false
  return true
}

/**
 * 松退：哪些字段在当前模式下不可用
 * - 0 否：所有都不可用
 * - 1 距离：distance 可用，time 不可用
 * - 2 时间：time 可用，distance 不可用
 */
function isDecompressDisabled(index: number, type: string): boolean {
  const before = metering.value.pre_decompress_mode
  if (index === 0) {
    if (before === 1 && type === 'distance') return false
    if (before === 2 && type === 'time') return false
  }
  const after = metering.value.post_decompress_mode
  if (index === 1) {
    if (after === 1 && type === 'distance') return false
    if (after === 2 && type === 'time') return false
  }
  return true
}

// ============================================================================
// 单位同步
// ============================================================================

function syncMachineUnit() {
  if (!machine_info) return
  const pressure_unit = machine_info.pressure_unit
  const speed_unit = machine_info.speed_unit
  const screw_rotation_unit = machine_info.screw_rotation_unit
  const back_pressure_unit = machine_info.back_pressure_unit

  // 注射：压力 / 速度 / 位置
  if (injection.value.table_data) {
    injection.value.table_data[0].unit = pressure_unit
    injection.value.table_data[1].unit = speed_unit
    injection.value.table_data[2].unit = 'mm'
  }
  // 保压：压力 / 速度 / 时间
  if (holding.value.table_data) {
    holding.value.table_data[0].unit = pressure_unit
    holding.value.table_data[1].unit = speed_unit
    holding.value.table_data[2].unit = 's'
  }
  // 熔胶：压力 / 螺杆转速 / 背压 / 位置
  if (metering.value.table_data) {
    metering.value.table_data[0].unit = pressure_unit
    metering.value.table_data[1].unit = screw_rotation_unit
    metering.value.table_data[2].unit = back_pressure_unit
    metering.value.table_data[3].unit = 'mm'
  }
}

// ============================================================================
// Watch
// ============================================================================

watch(
  () => props.machineInfo,
  (val) => {
    Object.assign(machine_info, val ?? {})
    syncMachineUnit()
  },
  { deep: true, immediate: true },
)

watch(
  () => props.settingProcess,
  (val) => {
    Object.assign(setting_process, val ?? structuredClone(settingProcessForm))
  },
  { deep: true, immediate: true },
)
</script>

<style scoped>
.simple-table {
  width: 100%;
}
</style>
