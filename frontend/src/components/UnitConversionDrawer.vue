<!--
  UnitConversionDrawer - 单位换算抽屉（命令式工具）

  路由：无（命令式调用）

  设计要点：
  - 旧 UnitConversion.vue（Options API、无引用）已废弃
  - 本组件改用 el-drawer + Vue 3 script setup + TS + 响应式 API
  - 通过 utils/unit-conversion-drawer.ts 导出 openUnitConversionDrawer() 命令式调用
  - 支持类目：压力 / 速度 / 位置 / 温度 / 时间 / 转速
  - 数据预填：macTrademark（机器型号）+ injectorInfo（当前激活 tab 的注射单元）
  - 顶部显著显示"当前射台"标识（如"注射部件-#1"），让用户随时知道引用了哪部分数据
  - 螺杆直径可手动修改（覆盖预填值）
  - 源/目标单位支持一键互换
  - velocity / position / rotation 类目需螺杆直径（按类目级判断，
    保守提示用户填写，避免按"单位组合"判断时遗漏需场景）
-->
<template>
  <el-drawer
    v-model="visible"
    title="单位换算"
    direction="rtl"
    size="480px"
    :with-header="true"
    :close-on-click-modal="false"
    @closed="handleClosed"
  >
    <div class="unit-conversion">
      <!-- 当前射台提示（让用户知道引用的是哪部分数据） -->
      <div v-if="injectorLabel" class="unit-conversion__context">
        <AppIcon icon="mdi:information-outline" class="unit-conversion__context-icon" />
        <span>当前射台：<strong>{{ injectorLabel }}</strong></span>
      </div>

      <!-- 机器信息（预填 + 可编辑螺杆直径） -->
      <section class="unit-conversion__info">
        <el-form
          label-width="7rem"
          size="default"
          class="unit-conversion__info-form"
        >
          <el-form-item label="机器型号">
            <el-input
              v-model="mac_trademark"
              placeholder="如：HTF300W"
              clearable
            />
          </el-form-item>
          <el-form-item label="螺杆直径">
            <el-input
              v-model.number="screw_diameter"
              placeholder="影响速度/位置与体积的换算"
              clearable
            >
              <template #suffix>mm</template>
            </el-input>
          </el-form-item>
        </el-form>
      </section>

      <!-- 换算主体 -->
      <section class="unit-conversion__body">
        <el-form label-width="6rem" size="default">
          <el-form-item label="换算类别">
            <el-select
              v-model="category"
              placeholder="请选择类别"
              style="width: 100%"
            >
              <el-option
                v-for="c in CATEGORIES"
                :key="c.value"
                :label="c.label"
                :value="c.value"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="源">
            <div class="unit-conversion__pair">
              <el-input
                v-model.number="source_value"
                placeholder="输入数值"
                clearable
                class="unit-conversion__value"
              />
              <el-select
                v-model="source_unit"
                placeholder="源单位"
                class="unit-conversion__unit"
              >
                <el-option
                  v-for="u in unitOptions"
                  :key="u.value"
                  :label="u.label"
                  :value="u.value"
                />
              </el-select>
            </div>
          </el-form-item>

          <div class="unit-conversion__swap">
            <el-button
              text
              :icon="ArrowDown"
              @click="swapDirection"
              title="互换源与目标"
            />
          </div>

          <el-form-item label="目标">
            <div class="unit-conversion__pair">
              <el-input
                v-model="target_value"
                placeholder="自动计算"
                readonly
                class="unit-conversion__value"
              />
              <el-select
                v-model="target_unit"
                placeholder="目标单位"
                class="unit-conversion__unit"
              >
                <el-option
                  v-for="u in unitOptions"
                  :key="u.value"
                  :label="u.label"
                  :value="u.value"
                />
              </el-select>
            </div>
          </el-form-item>

          <el-alert
            v-if="hint_message"
            :title="hint_message"
            :type="hint_type"
            :closable="false"
            show-icon
            class="unit-conversion__hint"
          />
        </el-form>
      </section>
    </div>

    <template #footer>
      <div class="unit-conversion__footer">
        <el-button @click="handleReset">重置</el-button>
        <el-button type="primary" @click="handleClose">关闭</el-button>
      </div>
    </template>
  </el-drawer>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'
import { conversion, pressureConversion } from '@/utils/unit-change'

/**
 * 类目定义（与 unit-change.ts 的 capability 对齐）
 * - 压力：MPa / kgf/cm² / bar / PSI（专用 pressureConversion，支持 % 转换）
 * - 速度/位置/温度/时间/转速：统一走 conversion()
 */
const CATEGORIES = [
  { value: 'pressure', label: '压力' },
  { value: 'velocity', label: '速度' },
  { value: 'position', label: '位置' },
  { value: 'temperature', label: '温度' },
  { value: 'time', label: '时间' },
  { value: 'rotation', label: '转速' },
] as const

type CategoryValue = (typeof CATEGORIES)[number]['value']

/**
 * 单位映射表
 * - 数据来源：unit-change.ts 中 conversion() / pressureConversion() 的能力清单
 * - 命名规范：单位符号（国际通用，无歧义时保留原文）
 */
const UNIT_MAP: Record<CategoryValue, { value: string; label: string }[]> = {
  pressure: [
    { value: 'MPa', label: 'MPa' },
    { value: 'kgf/cm²', label: 'kgf/cm²' },
    { value: 'bar', label: 'bar' },
    { value: 'PSI', label: 'PSI' },
  ],
  velocity: [
    { value: 'mm/s', label: 'mm/s（线速度）' },
    { value: 'inch/s', label: 'inch/s（线速度）' },
    { value: 'cm³/s', label: 'cm³/s（体积流速）' },
    { value: 'inch³/s', label: 'inch³/s（体积流速）' },
  ],
  position: [
    { value: 'mm', label: 'mm（线性位置）' },
    { value: 'inch', label: 'inch（线性位置）' },
    { value: 'cm³', label: 'cm³（体积）' },
    { value: 'inch³', label: 'inch³（体积）' },
  ],
  temperature: [
    { value: '℃', label: '℃' },
    { value: '℉', label: '℉' },
  ],
  time: [
    { value: 's', label: 's' },
    { value: 'μs', label: 'μs' },
  ],
  rotation: [
    { value: 'rpm', label: 'rpm（转每分）' },
    { value: 'cm/s', label: 'cm/s（螺杆线速度）' },
    { value: 'mm/s', label: 'mm/s（螺杆线速度）' },
    { value: 'm/s', label: 'm/s（螺杆线速度）' },
    { value: 'inch/s', label: 'inch/s（螺杆线速度）' },
  ],
}

const props = defineProps<{
  /** 机器型号（可选预填） */
  macTrademark?: string | null
  /**
   * 注射单元信息（当前激活 tab 的注射单元对象）
   * - 取 screw_diameter 作为默认螺杆直径
   * - 用户在 drawer 内可手动覆盖
   */
  injectorInfo?: Record<string, any> | null
  /**
   * 当前射台的显示标签（如 "注射部件-#1（射台编号 A）"）
   * - 仅用于顶部提示，不参与换算逻辑
   * - 不传则不显示提示条
   */
  injectorLabel?: string
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

// ============================================================================
// 可见性（drawer 本体）
// ============================================================================

const visible = defineModel<boolean>('visible', { default: true })

function handleClose() {
  visible.value = false
}

function handleClosed() {
  // 等待 drawer 关闭动画结束（默认 300ms）后通知父级卸载
  emit('close')
}

// ============================================================================
// 表单状态
// ============================================================================

const category = ref<CategoryValue>('pressure')
const source_value = ref<number | null>(null)
const source_unit = ref<string | null>(null)
const target_unit = ref<string | null>(null)
const target_value = ref<string>('')
const hint_message = ref<string>('')
const hint_type = ref<'success' | 'info' | 'warning' | 'error'>('info')

// 机器信息（可由用户编辑覆盖预填）
const mac_trademark = ref<string>('')
const screw_diameter = ref<number | null>(null)

// ============================================================================
// 派生
// ============================================================================

const unitOptions = computed(() => UNIT_MAP[category.value] ?? [])

// ============================================================================
// 初始化 / 重置
// ============================================================================

function init() {
  mac_trademark.value = props.macTrademark ?? ''
  screw_diameter.value = props.injectorInfo?.screw_diameter ?? null
  resetForm()
}

function handleReset() {
  // 重置换算表单（不重置机器型号与螺杆直径，保持上下文）
  resetForm()
}

function resetForm() {
  source_value.value = null
  target_value.value = ''
  hint_message.value = ''
  const units = UNIT_MAP[category.value]
  source_unit.value = units[0]?.value ?? null
  target_unit.value = units[1]?.value ?? null
}

// ============================================================================
// 类目/单位变化：重置源/目标单位（避免非法组合）
// ============================================================================

watch(category, () => {
  // 切换类目时，重置源/目标单位（避免保留上一次的单位导致组合无效）
  const units = UNIT_MAP[category.value]
  source_unit.value = units[0]?.value ?? null
  target_unit.value = units[1]?.value ?? units[0]?.value ?? null
  source_value.value = null
  target_value.value = ''
  hint_message.value = ''
})

// ============================================================================
// 互换方向
// ============================================================================

function swapDirection() {
  const old_src_unit = source_unit.value
  const old_tgt_unit = target_unit.value
  const old_src_value = source_value.value

  source_unit.value = old_tgt_unit
  target_unit.value = old_src_unit
  // 反向计算：把当前目标值作为新的源值
  if (target_value.value !== '' && target_value.value !== null) {
    source_value.value = Number(target_value.value)
  } else if (old_src_value !== null) {
    // 兜底：若目标值为空但源值有，用源值
    source_value.value = old_src_value
  }
  recompute()
}

// ============================================================================
// 换算计算
// ============================================================================

const injector_info_proxy = computed(() => ({
  screw_diameter: screw_diameter.value,
}))

function recompute() {
  hint_message.value = ''

  if (source_value.value === null || source_value.value === undefined) {
    target_value.value = ''
    return
  }
  if (!source_unit.value || !target_unit.value) {
    target_value.value = ''
    return
  }
  if (source_unit.value === target_unit.value) {
    target_value.value = String(source_value.value)
    return
  }

  // velocity / position / rotation 类目下的换算都需螺杆直径
  // （保守按类目级检查，避免按"单位组合"检查时遗漏需场景）
  if (
    needsScrewDiameter(category.value)
    && !(screw_diameter.value && screw_diameter.value > 0)
  ) {
    hint_message.value = '当前换算需提供螺杆直径，请在上方填写。'
    hint_type.value = 'warning'
    target_value.value = ''
    return
  }

  const fn = category.value === 'pressure' ? pressureConversion : conversion
  const result = fn(
    source_unit.value,
    target_unit.value,
    Number(source_value.value),
    injector_info_proxy.value,
  )

  if (result === null || result === undefined || result === '') {
    hint_message.value = `暂不支持 ${source_unit.value} 到 ${target_unit.value} 的直接换算。`
    hint_type.value = 'warning'
    target_value.value = ''
    return
  }

  target_value.value = String(result)
  hint_message.value = `转换完成：${source_value.value} ${source_unit.value} = ${result} ${target_unit.value}`
  hint_type.value = 'success'
}

/**
 * 类目级判断：该类目下的换算是否需要螺杆直径
 * - velocity / position / rotation：需要（velocity 涉及线速度↔体积流速；position 涉及线性↔体积；rotation 依赖周长）
 * - pressure / temperature / time：不需要
 * 按类目级而非"单位组合"判断，更保守稳健，避免遗漏场景
 */
function needsScrewDiameter(cat: CategoryValue): boolean {
  return cat === 'velocity' || cat === 'position' || cat === 'rotation'
}

// 监听源值/源单位/目标单位/螺杆直径变化，自动重算
watch(
  [source_value, source_unit, target_unit, screw_diameter],
  () => {
    recompute()
  },
)

// ============================================================================
// 生命周期
// ============================================================================

init()
</script>

<style scoped lang="scss">
.unit-conversion {
  display: flex;
  flex-direction: column;
  gap: 20px;

  // 当前射台提示条（让用户清楚引用的是哪部分数据）
  &__context {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 12px;
    background-color: var(--el-color-primary-light-9, #ecf5ff);
    border: 1px solid var(--el-color-primary-light-5, #d9ecff);
    border-radius: 4px;
    color: var(--el-color-primary, #409eff);
    font-size: 13px;

    strong {
      font-weight: 600;
    }
  }

  &__context-icon {
    font-size: 16px;
    flex-shrink: 0;
  }

  &__info {
    padding: 14px 16px;
    background-color: var(--color-bg-overlay, #f5f7fa);
    border: 1px solid var(--color-border-light, #e4e7ed);
    border-radius: 6px;

    &-form {
      .el-form-item {
        margin-bottom: 8px;

        &:last-child {
          margin-bottom: 0;
        }
      }
    }
  }

  &__body {
    .el-form-item {
      margin-bottom: 16px;
    }
  }

  &__pair {
    display: flex;
    gap: 8px;
    width: 100%;
  }

  &__value {
    flex: 1;
  }

  &__unit {
    width: 140px;
  }

  &__swap {
    text-align: center;
    margin: -4px 0 8px;

    .el-button {
      transform: rotate(90deg);
    }
  }

  &__hint {
    margin-top: 4px;
  }

  &__footer {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
  }
}
</style>
