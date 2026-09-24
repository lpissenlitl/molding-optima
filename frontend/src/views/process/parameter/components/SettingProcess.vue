<!--
  SettingProcess - 工艺参数设定卡

  业务含义：
    - 注射（6 段：压力/速度/位置）+ VP 切换 + 保压（5 段：压力/速度/时间）
    - 储料参数：熔胶（4 段：压力/螺杆转速/背压/位置）+ 松退（储前/储后）+ 终止位置
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
  <!--
    外层 el-card：与 ProcessCondition 视觉对齐
    - shadow="never" 与上方工艺条件卡一致（无阴影）
    - header 明确标识"工艺参数"区块
    - 内部 box-card 保留作为左右列子分组
  -->
  <el-card class="setting-process-card" shadow="never">
    <template #header>
      <div class="setting-process-card__header">
        <AppIcon icon="mdi:tune-variant" class="setting-process-card__icon" />
        <span class="custom-form__title">工艺参数</span>
      </div>
    </template>

    <el-row :gutter="0">
      <!-- 左列：注射 + VP + 保压 -->
      <el-col :xs="24" :lg="13" :xl="13">
        <el-card class="box-card" style="min-height: 750px">
          <!-- 区域 1：注射参数 -->
          <div class="section-header">注射参数</div>

          <!-- 注射段 -->
          <el-table
            class="simple-table"
            size="small"
            :data="injection.table_data"
            :key="`injection_${injection.stage}`"
          >
            <el-table-column label="工艺参数" width="120" align="left">
              <template #header>
                <div class="simple-table__stage-title">注射段数</div>
                <el-select
                  v-model="injection.stage"
                  size="small"
                  style="width: 100%"
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
                  style="width: 100%"
                  :disabled="col > injection.stage"
                />
              </template>
            </el-table-column>
          </el-table>

          <!-- 注射时间/延时/冷却 -->
          <el-form size="small" :model="injection" :inline="true">
            <el-form-item label="注射时间" prop="injection_time">
              <el-input
                style="width: 8rem"
                v-model="injection.injection_time"
                v-number
              >
                <template #suffix>s</template>
              </el-input>
            </el-form-item>
            <el-form-item label="注射延迟" prop="delay_time">
              <el-input
                style="width: 8rem"
                v-model="injection.delay_time"
                v-number
              >
                <template #suffix>s</template>
              </el-input>
            </el-form-item>
            <el-form-item label="冷却时间" prop="cooling_time">
              <el-input
                style="width: 8rem"
                v-model="injection.cooling_time"
                v-number
              >
                <template #suffix>s</template>
              </el-input>
            </el-form-item>
          </el-form>

          <!-- 区域 2：VP 切换 -->
          <div class="section-header">VP 切换</div>

          <!--
            VP 切换字段：5 个 inline 聚拢在一起
            - 切换方式：模式选择器，决定后续字段启用状态
            - 切换位置 / 切换时间 / 切换压力 / 切换速度：根据 mode 动态启用
            - 不要硬换行（会让字段分散），让 inline 聚拢随容器宽度自动换行
          -->
          <el-form size="small" :model="vp_switch" :inline="true">
            <el-form-item label="切换方式" prop="mode">
              <el-select
                style="width: 8rem"
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
            <el-form-item label="切换位置" prop="position">
              <el-input
                v-number
                v-model="vp_switch.position"
                style="width: 8rem"
                :disabled="isSwitchModeDisabled('position')"
              >
                <template #suffix>mm</template>
              </el-input>
            </el-form-item>
            <el-form-item label="切换时间" prop="time">
              <el-input
                v-number
                v-model="vp_switch.time"
                style="width: 8rem"
                :disabled="isSwitchModeDisabled('time')"
              >
                <template #suffix>s</template>
              </el-input>
            </el-form-item>
            <el-form-item label="切换压力" prop="pressure">
              <el-input
                v-number
                v-model="vp_switch.pressure"
                style="width: 8rem"
                :disabled="isSwitchModeDisabled('pressure')"
              >
                <template #suffix>{{ pressure_unit }}</template>
              </el-input>
            </el-form-item>
            <el-form-item label="切换速度" prop="velocity">
              <el-input
                v-number
                v-model="vp_switch.velocity"
                style="width: 8rem"
                :disabled="isSwitchModeDisabled('velocity')"
              >
                <template #suffix>{{ speed_unit }}</template>
              </el-input>
            </el-form-item>
          </el-form>

          <!-- 区域 3：保压参数 -->
          <div class="section-header">保压参数</div>

          <!-- 保压段 -->
          <el-table
            class="simple-table"
            size="small"
            :data="holding.table_data"
            :key="`holding_${holding.stage}`"
          >
            <el-table-column label="工艺参数" width="120" align="left">
              <template #header>
                <div class="simple-table__stage-title">保压段数</div>
                <el-select
                  v-model="holding.stage"
                  size="small"
                  style="width: 100%"
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
                  style="width: 100%"
                  :disabled="col > holding.stage"
                />
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- 右列：储料参数（熔胶 + 储料松退 + 终止位置） -->
      <el-col :xs="24" :lg="11" :xl="11">
        <el-card class="box-card" style="min-height: 750px">
          <!-- 区域 1：储料参数（合并：熔胶 + 储料松退 + 终止位置） -->
          <div class="section-header">储料参数</div>

          <!-- 熔胶段 -->
          <el-table
            class="simple-table"
            size="small"
            :data="metering.table_data"
            :key="`metering_${metering.stage}`"
          >
            <el-table-column label="工艺参数" width="140" align="left">
              <template #header>
                <div class="simple-table__stage-title">计量段数</div>
                <el-select
                  v-model="metering.stage"
                  size="small"
                  style="width: 100%"
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
                  style="width: 100%"
                />
              </template>
            </el-table-column>
          </el-table>

          <!-- 松退模式选择（属于储料参数的子段） -->
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
                  style="width: 100%"
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
                  style="width: 100%"
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
                  style="width: 100%"
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
                  style="width: 100%"
                  :disabled="isDecompressDisabled(scope.$index, 'time')"
                />
              </template>
            </el-table-column>
          </el-table>

          <!-- 储料延迟 + 终止位置（属于储料松退区域的延续） -->
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
          <!-- 区域 1：料筒温度 -->
          <div class="section-header">料筒温度</div>

          <el-table
            class="simple-table"
            size="small"
            :data="barrel_temperature.table_data"
            :key="`barrel_temperature_${barrel_temperature.stage}`"
          >
            <el-table-column label="工艺参数" width="90" align="center">
              <template #header>
                <div class="simple-table__stage-title">温度段数</div>
                <el-select
                  v-model="barrel_temperature.stage"
                  size="small"
                  style="width: 100%"
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
                  style="width: 100%"
                  :disabled="col > barrel_temperature.stage"
                />
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </el-card>
</template>

<script setup lang="ts">
/**
 * SettingProcess 工艺参数设定卡（Vue 3 Composition API 版）
 *
 * - props.settingProcess: 嵌套结构的工艺参数（与后端 _construct_setting_process_frontend 对应）
 * - props.machineInfo: 设备信息（用于单位系统）
 * - 单位系统同步：watch props.machineInfo → 更新 injection/holding/metering 的 table_data 单位
 */
import { ref, computed, watch, reactive } from "vue";
import { settingProcessForm } from "@/constants/process-const";

// ============================================================================
// 常量
// ============================================================================

const STG_HEADER: Record<number, string> = {
  1: "一段",
  2: "二段",
  3: "三段",
  4: "四段",
  5: "五段",
  6: "六段",
};
const HOLD_STG_HEADER: Record<number, string> = {
  1: "一段",
  2: "二段",
  3: "三段",
  4: "四段",
  5: "五段",
};
const MET_STG_HEADER: Record<number, string> = {
  1: "一段",
  2: "二段",
  3: "三段",
  4: "四段",
};
const TEMP_STG_HEADER: Record<number, string> = {
  1: "喷嘴",
  2: "一段",
  3: "二段",
  4: "三段",
  5: "四段",
  6: "五段",
  7: "六段",
  8: "七段",
  9: "八段",
  10: "九段",
};

const VPS_MODE_OPTIONS = [
  { label: "位置", value: 0 },
  { label: "时间", value: 1 },
  { label: "时间&位置", value: 2 },
  { label: "压力", value: 3 },
  { label: "速度", value: 4 },
];

const DECOMP_MODE_OPTIONS = [
  { label: "否", value: 0 },
  { label: "距离", value: 1 },
  { label: "时间", value: 2 },
];

// ============================================================================
// Props
// ============================================================================

const props = defineProps<{
  settingProcess: any;
  machineInfo?: any;
}>();

// ============================================================================
// 响应式状态
// ============================================================================

const setting_process = reactive<any>(
  props.settingProcess ?? structuredClone(settingProcessForm),
);
const machine_info = reactive<any>(props.machineInfo ?? {});

const injection = computed(() => setting_process.injection);
const vp_switch = computed(() => setting_process.vp_switch);
const holding = computed(() => setting_process.holding);
const metering = computed(() => setting_process.metering);
const barrel_temperature = computed(() => setting_process.barrel_temperature);

const pressure_unit = computed(() => machine_info.pressure_unit || "MPa");
const speed_unit = computed(() => machine_info.speed_unit || "mm/s");

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
  const mode = vp_switch.value.mode;
  if ((mode === 0 || mode === 2) && keyword === "position") return false;
  if ((mode === 1 || mode === 2) && keyword === "time") return false;
  if (mode === 3 && keyword === "pressure") return false;
  if (mode === 4 && keyword === "velocity") return false;
  return true;
}

/**
 * 松退：哪些字段在当前模式下不可用
 * - 0 否：所有都不可用
 * - 1 距离：distance 可用，time 不可用
 * - 2 时间：time 可用，distance 不可用
 */
function isDecompressDisabled(index: number, type: string): boolean {
  const before = metering.value.pre_decompress_mode;
  if (index === 0) {
    if (before === 1 && type === "distance") return false;
    if (before === 2 && type === "time") return false;
  }
  const after = metering.value.post_decompress_mode;
  if (index === 1) {
    if (after === 1 && type === "distance") return false;
    if (after === 2 && type === "time") return false;
  }
  return true;
}

// ============================================================================
// 单位同步
// ============================================================================

function syncMachineUnit() {
  if (!machine_info) return;
  const pressure_unit = machine_info.pressure_unit;
  const speed_unit = machine_info.speed_unit;
  const screw_rotation_unit = machine_info.screw_rotation_unit;
  const back_pressure_unit = machine_info.back_pressure_unit;

  // 注射：压力 / 速度 / 位置
  if (injection.value.table_data) {
    injection.value.table_data[0].unit = pressure_unit;
    injection.value.table_data[1].unit = speed_unit;
    injection.value.table_data[2].unit = "mm";
  }
  // 保压：压力 / 速度 / 时间
  if (holding.value.table_data) {
    holding.value.table_data[0].unit = pressure_unit;
    holding.value.table_data[1].unit = speed_unit;
    holding.value.table_data[2].unit = "s";
  }
  // 熔胶：压力 / 螺杆转速 / 背压 / 位置
  if (metering.value.table_data) {
    metering.value.table_data[0].unit = pressure_unit;
    metering.value.table_data[1].unit = screw_rotation_unit;
    metering.value.table_data[2].unit = back_pressure_unit;
    metering.value.table_data[3].unit = "mm";
  }
}

// ============================================================================
// Watch
// ============================================================================

watch(
  () => props.machineInfo,
  (val) => {
    Object.assign(machine_info, val ?? {});
    syncMachineUnit();
  },
  { deep: true, immediate: true },
);

watch(
  () => props.settingProcess,
  (val) => {
    Object.assign(setting_process, val ?? structuredClone(settingProcessForm));
  },
  { deep: true, immediate: true },
);
</script>

<style scoped>
/* ===== 表格 ===== */
/*
 * 参考 shared/SettingProcess.vue 里的 .simple-table 样式
 * - 表格整体 12px（紧凑）
 * - 表头 8px padding + 600 字重（与其他表头一致）
 * - 表体 6px padding（让输入框紧凑）
 */
.simple-table {
  width: 100%;
  font-size: 12px;
}

.simple-table :deep(.el-table__header th) {
  padding: 8px 0;
  font-size: 12px;
  font-weight: 600;
}

.simple-table :deep(.el-table__body td) {
  padding: 6px 0;
  font-size: 12px;
}

/*
 * el-table 后面紧跟 el-form 时的间距
 * - 问题：之前清理 <br /> 后，注射表 / 松退表与下方的 form 紧贴在一起
 * - 解决：用相邻兄弟选择器只对“上一个兄弟元素是 .simple-table”的 form 生效
 * - 不影响其他场景：
 *   - 烙胶表后是 section-header（不是 form，不生效）
 *   - 保压表后无 form（不生效）
 */
.simple-table + .el-form {
  margin-top: 16px;
}

/*
 * section-header 后面紧跟 el-form 时的间距（VP 切换场景专用）
 * - 问题：VP 切换区域里 section-header 后面直接是 form，没有间距
 * - 解决：用相邻兄弟选择器只对“上一个兄弟元素是 .section-header”的 form 生效
 * - section-header 本身有 padding: 12px 16px 8px（下 8px），再加 4px 达 12px 总间距
 * - 不会影响其他场景：
 *   - 注射参数 / 储料参数 / 保压参数 / 料筒温度 后面都是 el-table，不是 form
 */
.section-header + .el-form {
  margin-top: 4px;
}

/*
 * 表头中的“段数”标题（如注射段数 / 保压段数 / 计量段数 / 温度段数）
 * - 原状是裸 div，无视觉重点
 * - 加上主题色 + 600 字重 + 4px 下边距，与下面的 el-select 拉开间距
 * - 字号 12px 与表头一致
 */
.simple-table__stage-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
  line-height: 1.2;
}

/*
 * ===== 区域分组标题 =====
 *
 * 用于 box-card 内部区分不同区域（注射参数 / VP切换 / 保压参数 等）
 * - 参考 shared/SettingProcess.vue 的 .section-header 写法
 * - 与 shared/SettingProcess 一致：主题色竖条 + 浅灰背景 + 600 字重
 *
 * 响应式：
 * - 默认桌面：padding 12px 16px 8px（上下多一点以分隔区块）
 * - 移动端 (<=768px)：padding 8px 12px 6px（紧凑，避免窄屏占用过多空间）
 */
.section-header {
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-primary, #303133);
  padding: 12px 16px 8px;
  margin: 0;
  border-left: 3px solid var(--el-color-primary, #409eff);
  background-color: var(--el-fill-color-light, #f5f7fa);
}

@media (max-width: 768px) {
  .section-header {
    padding: 8px 12px 6px;
    font-size: 12px;
  }
}

/*
 * 外层 card 样式
 * - header 用左对齐的图标 + 标题，与 ProcessCondition 的折叠 header 视觉一致
 * - 与 ProcessCondition 一样用 shadow="never"（border 而非阴影）
 *
 * 参考 molding-expert 旧版布局：
 * - 旧版无 el-row gutter、box-card 直接嵌入页面
 * - 新版保留外层 card 以匹配 ProcessCondition（用户上次明确要求），但去掉 gutter
 * - box-card 仍保留自身边框 + 阴影与旧版一致，保持“卡片嵌套”视觉
 */
.setting-process-card {
  &__header {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  &__icon {
    width: 18px;
    height: 18px;
    color: var(--el-color-primary);
    flex-shrink: 0;
  }

  /*
   * 在 card header 上下文内覆盖全局 .custom-form__title
   * - 原样式有 padding-left: 10px + border-left: 3px 主题色竖条
   * - 问题：在 card header 中竖条颜色与 icon 同色（都是主题色），视觉上连成一体
   *   让人误以为 icon 和文字“贴在一起”，但物理距离实际有 18px
   * - 解决：去掉 padding-left + border-left（icon 已作为视觉标识，不需要重复主题色）
   * - 顺手调整字号：card header 不需要 16px/700，改 15px/600 更轻量
   */
  :deep(.custom-form__title) {
    padding-left: 0;
    border-left: none;
    font-size: 15px;
    font-weight: 600;
  }

  /*
   * 内部 box-card：去掉自身 margin-bottom
   * - box-card 仍保留边框 + 阴影 + 自身 padding（参考旧版 box-card 样式）
   * - 这样视觉上保留“卡片嵌套”的层次感，与旧版 box-card 一致
   */
  :deep(.box-card) {
    margin-bottom: 0;
  }
}
</style>
