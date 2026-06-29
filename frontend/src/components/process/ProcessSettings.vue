<template>
  <div class="process-settings-wrapper">
    <!-- 两列布局 -->
    <div class="two-column-layout">
      <!-- 左侧卡片：注射 + VP切换 + 保压 -->
      <el-card class="process-card injection-card">
        <!-- 1. 注射段 -->
        <div class="section-header">
          注射参数
        </div>
        <el-table 
          class="simple-table"
          size="mini"
          :data="injection.table_data" 
          :key="`injection_${injection.stage}`"
        >
          <el-table-column 
            label="工艺参数"
            width="120" 
            align="left"
          >
            <template #header>
              <el-select 
                v-model="injection.stage" 
                size="mini"
                style="width: 80%;"
                :disabled="readonly"
              >
                <el-option
                  v-for="(option, idx) in injection.max_stage"
                  :key="idx" :label="`${option}段`" :value="option"
                >
                </el-option>
              </el-select>
            </template>
            <template #default="scope">
              {{ scope.row.label }} [{{ scope.row.unit }}]
            </template>
          </el-table-column>
          <el-table-column
            v-for="(col, col_idx) in stageHeader('injection', injection.max_stage)"
            min-width="80"
            align="center"
            :key="col_idx"
            :label="col"
          >
            <template #header>
              <div>{{ col }}</div>
            </template>
            <template #default="scope">
              <el-input 
                v-if="!readonly"
                v-model="scope.row.sections[col_idx]"
                v-number
                size="mini"
                style="width: 100%;"
                :class="{ 
                  'field-changed': isFieldChanged(
                    `injection.table_data[${scope.$index}].sections[${col_idx}]`
                  ) 
                }"
                :disabled="col_idx >= injection.stage"
              >
              </el-input>
              <span 
                v-else 
                class="readonly-value"
                :class="{ 
                  'field-changed-text': isFieldChanged(
                    `injection.table_data[${scope.$index}].sections[${col_idx}]`
                  ) 
                }"
              >
                {{ scope.row.sections[col_idx] || '-' }}
              </span>
            </template>
          </el-table-column>
        </el-table>

        <!-- 注射时间参数 -->
        <el-form
          size="mini"
          :model="injection"
          :inline="true"
          class="form-inline"
        >
          <el-form-item label="注射时间">
            <el-input
              v-if="!readonly"
              style="width: 8rem;"
              v-model="injection.injection_time"
              v-number
              :class="{ 'field-changed': isFieldChanged('injection.injection_time') }"
            >
              <span slot="suffix">s</span>
            </el-input>
            <span v-else class="readonly-value-with-unit" :class="{ 'field-changed-text': isFieldChanged('injection.injection_time') }">
              {{ injection.injection_time }} <small>s</small>
            </span>
          </el-form-item>
          <el-form-item label="注射延迟">
            <el-input
              v-if="!readonly"
              style="width: 8rem;"
              v-model="injection.delay_time"
              v-number
              :class="{ 'field-changed': isFieldChanged('injection.delay_time') }"
            >
              <span slot="suffix">s</span>
            </el-input>
            <span v-else class="readonly-value-with-unit" :class="{ 'field-changed-text': isFieldChanged('injection.delay_time') }">
              {{ injection.delay_time }} <small>s</small>
            </span>
          </el-form-item>
          <el-form-item label="冷却时间">
            <el-input
              v-if="!readonly"
              style="width: 8rem;"
              v-model="injection.cooling_time"
              v-number
              :class="{ 'field-changed': isFieldChanged('injection.cooling_time') }"
            >
              <span slot="suffix">s</span>
            </el-input>
            <span v-else class="readonly-value-with-unit" :class="{ 'field-changed-text': isFieldChanged('injection.cooling_time') }">
              {{ injection.cooling_time }} <small>s</small>
            </span>
          </el-form-item>
        </el-form>

        <!-- VP切换参数 -->
        <div class="section-header">
          VP切换参数
        </div>
        <el-form
          size="mini"
          :model="vp_switch"
          :inline="true"
          class="form-inline"
        >
          <el-form-item label="切换方式">
            <el-select
              v-if="!readonly"
              style="width: 8rem;"
              v-model="vp_switch.mode"
              placeholder="请选择"
              @change="vpSwitchModeChange"
            >
              <el-option
                v-for="option in vp_switch_mode_options"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              >
              </el-option>
            </el-select>
            <span v-else class="readonly-value">
              {{ getVpSwitchModeLabel(vp_switch.mode) }}
            </span>
          </el-form-item>
          <el-form-item label="切换位置">
            <el-input
              v-if="!readonly"
              v-number
              v-model="vp_switch.position" 
              style="width: 8rem;"
              :disabled="isSwitchModeDisabled('position')"
            >
              <span slot="suffix">mm</span>
            </el-input>
            <span v-else class="readonly-value-with-unit">
              {{ vp_switch.position }} <small>mm</small>
            </span>
          </el-form-item>
          <el-form-item label="切换时间">
            <el-input
              v-if="!readonly"
              v-number
              v-model="vp_switch.time" 
              style="width: 8rem;"
              :disabled="isSwitchModeDisabled('time')"
            >
              <span slot="suffix">s</span>
            </el-input>
            <span v-else class="readonly-value-with-unit">
              {{ vp_switch.time }} <small>s</small>
            </span>
          </el-form-item>
          <el-form-item label="切换压力">
            <el-input
              v-if="!readonly"
              v-number
              v-model="vp_switch.pressure" 
              style="width: 8rem;"
              :disabled="isSwitchModeDisabled('pressure')"
            >
              <span slot="suffix">{{ pressure_unit }}</span>
            </el-input>
            <span v-else class="readonly-value-with-unit">
              {{ vp_switch.pressure }} <small>{{ pressure_unit }}</small>
            </span>
          </el-form-item>
          <el-form-item label="切换速度">
            <el-input
              v-if="!readonly"
              v-number
              v-model="vp_switch.velocity" 
              style="width: 8rem;"
              :disabled="isSwitchModeDisabled('velocity')"
            >
              <span slot="suffix">{{ speed_unit }}</span>
            </el-input>
            <span v-else class="readonly-value-with-unit">
              {{ vp_switch.velocity }} <small>{{ speed_unit }}</small>
            </span>
          </el-form-item>
        </el-form>

        <!-- 保压参数 -->
        <div class="section-header">
          保压参数
        </div>
        <el-table 
          class="simple-table"
          size="mini"
          :data="holding.table_data" 
          :key="`holding_${holding.stage}`"
        >
          <el-table-column 
            label="工艺参数"
            width="120" 
            align="left"
          >
            <template #header>
              <el-select 
                v-model="holding.stage" 
                size="mini"
                style="width: 80%;"
                :disabled="readonly"
              >
                <el-option
                  v-for="(option, idx) in holding.max_stage"
                  :key="idx"
                  :label="`${option}段`"
                  :value="option"
                >
                </el-option>
              </el-select>
            </template>
            <template #default="scope">
              {{ scope.row.label }} [{{ scope.row.unit }}]
            </template>
          </el-table-column>
          <el-table-column
            v-for="(col, col_idx) in stageHeader('holding', holding.max_stage)"
            :key="col_idx"
            :label="col"
            min-width="80"
            align="center"
          >
            <template #default="scope">
              <el-input 
                v-if="!readonly"
                v-number
                v-model="scope.row.sections[col_idx]" 
                size="mini"
                style="width: 100%;"
                :disabled="col_idx >= holding.stage"
              >
              </el-input>
              <span v-else class="readonly-value">{{ scope.row.sections[col_idx] || '-' }}</span>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 右侧卡片：储料/计量 -->
      <el-card class="process-card metering-card">
        <!-- 4. 储料/计量段 -->
        <div class="section-header">
          计量参数
        </div>
        <el-table 
          class="simple-table"
          size="mini"
          :data="metering.table_data"
          :key="`metering_${metering.stage}`"
        >
          <el-table-column 
            label="工艺参数"
            width="120" 
            align="left"
          >
            <template #header>
              <el-select 
                v-model="metering.stage" 
                size="mini"
                style="width: 80%;"
                :disabled="readonly"
              >
                <el-option
                  v-for="(option, idx) in metering.max_stage"
                  :key="idx"
                  :label="`${option}段`"
                  :value="option"
                >
                </el-option>
              </el-select>
            </template>
            <template #default="scope">
              {{ scope.row.label }} [{{ scope.row.unit }}]
            </template>
          </el-table-column>
          <el-table-column
            v-for="(col, col_idx) in stageHeader('metering', metering.max_stage)"
            :key="col_idx"
            :label="col"
            min-width="80"
            align="center"
          >
            <template #default="scope">
              <el-input 
                v-if="!readonly"
                v-model="scope.row.sections[col_idx]" 
                v-number
                :disabled="col_idx >= metering.stage"
                size="mini"
                style="width: 100%;"
              >
              </el-input>
              <span v-else class="readonly-value">{{ scope.row.sections[col_idx] || '-' }}</span>
            </template>
          </el-table-column>
        </el-table>

        <!-- 储料松退参数 -->
        <div class="section-header">
          储料松退参数
        </div>
        <el-form
          size="mini"
          :model="setting_process"
          class="form-inline"
        >
          <el-form-item label="储前松退模式">
            <el-select 
              v-if="!readonly"
              v-model="metering.pre_decompress_mode"
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
            <span v-else class="readonly-value">
              {{ getDecompressModeLabel(metering.pre_decompress_mode) }}
            </span>
          </el-form-item>
          <el-form-item label="储后松退模式">
            <el-select 
              v-if="!readonly"
              v-model="metering.post_decompress_mode"
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
            <span v-else class="readonly-value">
              {{ getDecompressModeLabel(metering.post_decompress_mode) }}
            </span>
          </el-form-item>
        </el-form>

        <!-- 松退参数表 -->
        <el-table
          class="simple-table"
          size="mini"
          :data="metering.decompress_table_data"
        >
          <el-table-column
            label=""
            width="120"
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
              <div>压力 [MPa]</div>
            </template>
            <template #default="scope">
              <el-input
                v-if="!readonly"
                v-model="scope.row.pressure"
                v-number
                size="mini"
                style="width: 100%;"
                :disabled="isDecompressDisabled(scope.$index, 'pressure')"
              >
              </el-input>
              <span v-else class="readonly-value">{{ scope.row.pressure || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column
            label="速度"
            min-width="80"
            align="center"
          >
            <template #header>
              <div>速度 [mm/s]</div>
            </template>
            <template #default="scope">
              <el-input
                v-if="!readonly"
                v-number
                v-model="scope.row.velocity"
                size="mini"
                style="width: 100%;"
                :disabled="isDecompressDisabled(scope.$index, 'velocity')"
              >
              </el-input>
              <span v-else class="readonly-value">{{ scope.row.velocity || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column
            label="距离"
            min-width="80"
            align="center"
          >
            <template #header>
              <div>距离 [mm]</div>
            </template>
            <template #default="scope">
              <el-input
                v-if="!readonly"
                v-number
                v-model="scope.row.distance"
                size="mini"
                style="width: 100%;"
                :disabled="isDecompressDisabled(scope.$index, 'distance')"
              >
              </el-input>
              <span v-else class="readonly-value">{{ scope.row.distance || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column
            label="时间"
            min-width="80"
            align="center"
          >
            <template #header>
              <div>时间 [s]</div>
            </template>
            <template #default="scope">
              <el-input
                v-if="!readonly"
                v-number
                v-model="scope.row.time"
                size="mini"
                style="width: 100%;"
                :disabled="isDecompressDisabled(scope.$index, 'time')"
              >
              </el-input>
              <span v-else class="readonly-value">{{ scope.row.time || '-' }}</span>
            </template>
          </el-table-column>
        </el-table>

        <!-- 储料延迟和终止位置 -->
        <el-form
          size="mini"
          :model="setting_process"
          class="form-inline"
        >
          <el-form-item label="储料延迟">
            <el-input
              v-if="!readonly"
              v-model="metering.delay_time"
              v-number
              style="width: 8rem"
            >
              <span slot="suffix">s</span>
            </el-input>
            <span v-else class="readonly-value-with-unit">
              {{ metering.delay_time }} <small>s</small>
            </span>
          </el-form-item>
          <el-form-item label="终止位置">
            <el-input
              v-if="!readonly"
              v-model="metering.ending_position"
              v-number
              style="width: 8rem"
            >
              <span slot="suffix">mm</span>
            </el-input>
            <span v-else class="readonly-value-with-unit">
              {{ metering.ending_position }} <small>mm</small>
            </span>
          </el-form-item>
        </el-form>
      </el-card>
    </div>

    <!-- 底部全宽：料筒温度 -->
    <el-card class="process-card temperature-card">
      <div class="section-header">
        料筒温度
      </div>
      <el-table 
        class="simple-table"
        size="mini"
        :data="barrel_temperature.table_data"
        :key="`barrel_temperature_${barrel_temperature.stage}`"
      >
        <el-table-column 
          label="工艺参数"
          width="120" 
          align="center"
        >
          <template #header>
            <el-select 
              v-model="barrel_temperature.stage" 
              size="mini"
              style="width: 80%;"
              :disabled="readonly"
            >
              <el-option
                v-for="(option, idx) in barrel_temperature.max_stage"
                :key="idx"
                :label="`${option}段`"
                :value="option"
              >
              </el-option>
            </el-select>
          </template>
          <template #default="scope">
            {{ scope.row.label }} [{{ scope.row.unit }}]
          </template>
        </el-table-column>
        <el-table-column
          v-for="(col, col_idx) in stageHeader('barrel_temperature', barrel_temperature.max_stage)"
          :key="col_idx"
          :label="col"
          min-width="80"
          align="center"
        >
          <template #default="scope">
            <el-input 
              v-if="!readonly"
              v-number
              v-model="scope.row.sections[col_idx]" 
              size="mini"
              style="width: 100%;"
              :disabled="col_idx >= barrel_temperature.stage"
            >
            </el-input>
            <span v-else class="readonly-value">{{ scope.row.sections[col_idx] || '-' }}</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script>
import { settingProcessForm } from "@/constants/process-const"
import { machineInfoForm } from "@/constants/machine-const"

export default {
  name: "ProcessSettings",
  props: {
    // 原始数据（用于变更检测）
    originalProcess: {
      type: Object,
      default: () => structuredClone(settingProcessForm)
    },
    // 当前工艺数据
    settingProcess: {
      type: Object,
      required: true
    },
    // 机器信息
    machineInfo: {
      type: Object,
      default: () => structuredClone(machineInfoForm)
    },
    // 只读模式
    readonly: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      setting_process: null,
      original_process: null,
      machine_info: null,
      vp_switch_mode_options: [
        { label: "位置", value: 0 },
        { label: "时间", value: 1 },
        { label: "时间&位置", value: 2 },
        { label: "压力", value: 3 },
        { label: "速度", value: 4 }
      ],
      decompressure_mode_options: [
        { label: "否", value: 0 },
        { label: "距离", value: 1 },
        { label: "时间", value: 2 },
      ],
    }
  },
  computed: {
    injection() {
      return this.setting_process?.injection
    },
    vp_switch() {
      return this.setting_process?.vp_switch
    },
    holding() {
      return this.setting_process?.holding
    },
    metering() {
      return this.setting_process?.metering
    },
    barrel_temperature() {
      return this.setting_process?.barrel_temperature
    },
    pressure_unit() {
      return this.machine_info?.pressure_unit || "MPa"
    },
    speed_unit() { 
      return this.machine_info?.speed_unit || "mm/s"
    },
    temperature_unit() { 
      return this.machine_info?.temperature_unit || "℃"
    },
  },
  watch: { 
    settingProcess: {
      handler(val) {
        this.setting_process = val
      },
      immediate: true
    },
    machineInfo: {
      handler(val) {
        this.machine_info = val
        this.setMachineUnit()
      },
      immediate: true
    },
    originalProcess: {
      handler(val) {
        this.original_process = val
      },
      immediate: true
    },
    // 监听注射段数变化
    "setting_process.injection.stage"() {
      this.adjustTableData("injection")
    },
    // 监听保压段数变化
    "setting_process.holding.stage"() {
      this.adjustTableData("holding")
    },
    // 监听计量段数变化
    "setting_process.metering.stage"() {
      this.adjustTableData("metering")
    },
    // 监听料筒温度段数变化
    "setting_process.barrel_temperature.stage"() {
      this.adjustTableData("barrel_temperature")
    }
  },
  mounted() {
    this.$nextTick(() => {
      this.saveOriginalSnapshot()
    })
  },
  methods: {
    /**
     * 根据路径字符串获取嵌套对象的值
     * 支持格式：
     * - 'vp_switch.position'
     * - 'injection.table_data[0].sections[1]'
     * - 'metering.decompress_table_data[10].pressure' (支持多位数索引)
     */
    getNestedValue(obj, path) {
      if (!obj || !path) return undefined
      
      const parts = path.match(/[^[\].]+|\[\d+\]/g) || []
      
      return parts.reduce((acc, part) => {
        if (acc === undefined || acc === null) {
          return undefined
        }
        
        const index_match = part.match(/^\[(\d+)\]$/)
        if (index_match) {
          const index = parseInt(index_match[1], 10)
          return Array.isArray(acc) ? acc[index] : undefined
        }
        
        return acc[part]
      }, obj)
    },
    
    /**
     * 判断指定路径的字段是否发生变更
     * @param {string} path - 字段路径
     * @returns {boolean} - 是否变更
     */
    isFieldChanged(path) {
      if (!this.original_process) return false
      
      const current_value = this.getNestedValue(this.setting_process, path)
      const original_value = this.getNestedValue(this.original_process, path)
      
      if (current_value === null && original_value === null) return false
      if (current_value === undefined && original_value === undefined) return false
      if (current_value === null && original_value !== null) return true
      if (current_value !== null && original_value === null) return true
      if (current_value === undefined && original_value !== undefined) return true
      if (current_value !== undefined && original_value === undefined) return true
      
      if (typeof current_value === "number" && typeof original_value === "number") {
        if (isNaN(current_value) && isNaN(original_value)) return false
        return Math.abs(current_value - original_value) > 0.0001
      }
      
      return current_value !== original_value
    },
    
    /**
     * 保存原始数据快照
     */
    saveOriginalSnapshot() {
      if (this.setting_process) {
        this.original_process = JSON.parse(JSON.stringify(this.setting_process))
      }
    },
    
    /**
     * 重置快照（保存成功后调用）
     */
    resetSnapshot() {
      this.saveOriginalSnapshot()
    },
    
    stageHeader(type = "injection", max_stage = 6) {
      const label_arr = []
      if (type === "barrel_temperature") {
        label_arr.push("喷嘴")
        max_stage -= 1
      }
      return [...label_arr, ...Array.from({ length: max_stage }, (_, i) => `${i + 1}段`)]
    },

    isSwitchModeDisabled(keyword) {
      const mode = this.vp_switch?.mode
      if (keyword === "position" && (mode === 0 || mode === 2)) return false
      if (keyword === "time" && (mode === 1 || mode === 2)) return false
      if (keyword === "pressure" && mode === 3) return false
      if (keyword === "velocity" && mode === 4) return false
      return true
    },

    isDecompressDisabled(index, type) {
      const before = this.metering?.pre_decompress_mode
      if (index === 0 && before === 1 && type !== "time") return false
      if (index === 0 && before === 2 && type !== "distance") return false

      const after = this.metering?.post_decompress_mode
      if (index === 1 && after === 1 && type !== "time") return false
      if (index === 1 && after === 2 && type !== "distance") return false

      return true
    },

    setMachineUnit() {
      if (!this.machine_info) return
      
      const pressure_unit = this.machine_info.pressure_unit
      const speed_unit = this.machine_info.speed_unit
      const screw_rotation_unit = this.machine_info.screw_rotation_unit
      const back_pressure_unit = this.machine_info.back_pressure_unit

      if (this.injection) {
        this.injection.table_data[0].unit = pressure_unit
        this.injection.table_data[1].unit = speed_unit
        this.injection.table_data[2].unit = "mm"
      }

      if (this.holding) {
        this.holding.table_data[0].unit = pressure_unit
        this.holding.table_data[1].unit = speed_unit
        this.holding.table_data[2].unit = "s"
      }

      if (this.metering) {
        this.metering.table_data[0].unit = pressure_unit
        this.metering.table_data[1].unit = screw_rotation_unit
        this.metering.table_data[2].unit = back_pressure_unit
        this.metering.table_data[3].unit = "mm"
      }
    },

    vpSwitchModeChange(mode) {
      console.log(mode)
    },
    
    getVpSwitchModeLabel(mode) {
      const mode_map = new Map(this.vp_switch_mode_options.map(item => [item.value, item.label]))
      return mode_map.get(mode) || "-"
    },

    getDecompressModeLabel(mode) {
      const mode_map = new Map(this.decompressure_mode_options.map(item => [item.value, item.label]))
      return mode_map.get(mode) || "-"
    },

    /**
     * 根据段数调整表格数据长度
     * @param {string} sectionKey - 数据段key
     */
    adjustTableData(sectionKey) {
      const section = this.setting_process?.[sectionKey]
      if (!section || !section.table_data) return
      
      const max_stage = section.max_stage
      
      section.table_data.forEach(row => {
        if (row.sections) {
          while (row.sections.length < max_stage) {
            row.sections.push(null)
          }
          if (row.sections.length > max_stage) {
            row.sections = row.sections.slice(0, max_stage)
          }
        }
      })
    },
  }
}
</script>

<style scoped>
/* ===== 布局 ===== */
.process-settings-wrapper {
  background-color: white;
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  gap: 0px;
  padding: 24px;
}

.two-column-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0px;
}

/* 响应式：当屏幕宽度小于1200px时，切换为单列布局 */
@media (max-width: 1200px) {
  .two-column-layout {
    grid-template-columns: 1fr;
  }
}

/* ===== 卡片 ===== */
.process-card {
  border-radius: 8px;
  min-height: 600px;
}

.temperature-card {
  min-height: auto;
}

.process-card >>> .el-card__header {
  padding: 12px 16px;
  background-color: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
}

/* ===== 区域标题 ===== */
.section-header {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  padding: 12px 16px 8px;
  margin: 0;
  border-left: 3px solid #409EFF;
  background-color: #f5f7fa;
}

/* ===== 表格 ===== */
.simple-table {
  font-size: 12px;
}

.simple-table >>> .el-table__header th {
  padding: 8px 0;
  font-size: 12px;
  font-weight: 600;
}

.simple-table >>> .el-table__body td {
  padding: 6px 0;
  font-size: 12px;
}

/* ===== 表单 ===== */
.form-inline {
  margin-top: 8px;
}

.form-inline >>> .el-form-item {
  margin-bottom: 8px;
  font-size: 12px;
}

.form-inline >>> .el-form-item__label {
  font-size: 12px;
  padding: 0 4px 0 0;
}

.form-inline >>> .el-input__inner {
  font-size: 12px;
}

.form-inline >>> .el-select {
  font-size: 12px;
}

/* ===== 只读值 ===== */
.readonly-value {
  display: inline-block;
  font-size: 12px;
  color: #606266;
  padding: 0 4px;
}

.readonly-value-with-unit {
  display: inline-flex;
  align-items: baseline;
  gap: 2px;
  font-size: 12px;
  color: #606266;
}

.readonly-value-with-unit small {
  font-size: 11px;
  color: #909399;
  margin-left: 2px;
}

/* ===== 变更高亮 ===== */
.field-changed >>> .el-input__inner {
  background-color: #fff7e6;
  border-color: #ffa940;
  box-shadow: 0 0 0 2px rgba(255, 169, 64, 0.2);
  animation: highlight-pulse 2s ease-in-out;
  transition: all 0.3s ease;
}

.field-changed-text {
  color: #fa8c16;
  font-weight: 600;
  position: relative;
  padding: 2px 4px;
  background-color: #fff7e6;
  border-radius: 2px;
}

.field-changed-text::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(to right, #ffa940, #fa8c16);
  animation: underline-expand 0.5s ease-out;
}

/* 脉冲动画 */
@keyframes highlight-pulse {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(255, 169, 64, 0.4);
  }
  50% {
    box-shadow: 0 0 0 4px rgba(255, 169, 64, 0.2);
  }
}

/* 下划线动画 */
@keyframes underline-expand {
  from {
    transform: scaleX(0);
  }
  to {
    transform: scaleX(1);
  }
}
</style>
