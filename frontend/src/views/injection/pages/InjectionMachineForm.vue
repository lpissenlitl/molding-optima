<!--
  InjectionMachineForm - 注塑机表单（new / edit / copy 三模式共用）

  路由：
    - /equipment/injection/new         新建
    - /equipment/injection/:id/edit    编辑
    - /equipment/injection/:id/copy    复制（清空 id + unit_code）

  架构（2026-09-09 重写）：
    - 5 个 section：机器描述 / 注射单元（el-tabs）/ 锁模单元 / 顶出单元 / 配套参数
    - 4 列布局（el-row + el-col + gutter:24），divider 占满一行
    - 顶部 page-header（返回列表）+ 底部 form-actions（取消 / 保存）
    - 单位系统（7 个）从机器顶层同步到所有注射单元（InjectionUnitForm）
    - InjectionUnitForm 子组件用 Vue3 script setup，通过 ref.checkFormDataValid() 校验
-->
<template>
  <div class="injection-machine-form">
    <!-- 顶部 page-header（仅返回按钮，与 PolymerForm 风格一致） -->
    <div class="page-header">
      <el-button text @click="goBack">
        <AppIcon icon="mdi:arrow-left" style="margin-right: 4px; font-size: 14px;" />
        返回列表
      </el-button>
    </div>

    <div v-if="!loaded" v-loading="true" class="loading-placeholder"></div>

    <el-form
      v-else
      ref="formRef"
      :model="injection_machine"
      :rules="rules"
      class="custom-form"
      label-width="120px"
    >
      <!-- 1. 机器描述 -->
      <el-card class="custom-form__section" shadow="never">
        <template #header>
          <span class="custom-form__title">机器描述</span>
        </template>

        <el-row
          v-for="(row, rIdx) in machineDescRows"
          :key="`desc_${rIdx}`"
          :gutter="24"
        >
          <el-col
            v-for="(item, iIdx) in row"
            :key="`desc_${rIdx}_${iIdx}`"
            :span="item.span"
          >
            <el-divider
              v-if="item.type === 'divider'"
              content-position="left"
              class="custom-form__divider"
            >
              {{ item.label }}
            </el-divider>

            <el-form-item
              v-else-if="item.prop"
              :label="item.label"
              :prop="item.prop"
              :required="item.required"
            >
              <el-input
                v-if="item.type === 'input'"
                v-model.trim="injection_machine[item.prop!]"
                :placeholder="item.placeholder || `请输入${item.label}`"
                clearable
              >
                <template #suffix v-if="item.unit">{{ item.unit }}</template>
                <template #suffix v-else-if="item.dynamic_unit">{{ injection_machine[item.dynamic_unit] }}</template>
              </el-input>

              <el-select
                v-else-if="item.type === 'select'"
                v-model="injection_machine[item.prop!]"
                :placeholder="item.placeholder || `请选择${item.label}`"
                clearable
                filterable
                :allow-create="item.allowCreate !== false"
                @change="(val: any) => item.onChange && item.onChange(val)"
              >
                <el-option
                  v-for="(opt, oIdx) in item.options"
                  :key="oIdx"
                  :label="opt.label"
                  :value="opt.value"
                />
              </el-select>

              <el-autocomplete
                v-else-if="item.type === 'autocomplete'"
                v-model="injection_machine[item.prop!]"
                :placeholder="item.placeholder || `请输入${item.label}`"
                clearable
                :debounce="0"
                :fetch-suggestions="querySuggestions(item.query)"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-card>

      <!-- 2. 注射单元（el-tabs，按射台数量动态渲染） -->
      <el-card class="custom-form__section" shadow="never">
        <template #header>
          <div class="injection-unit-card-header">
            <span class="custom-form__title">注射单元</span>
            <el-button text @click="openUnitConverter">
              <AppIcon icon="mdi:calculator-variant" style="margin-right: 4px; font-size: 14px;" />
              单位换算
            </el-button>
          </div>
        </template>

        <el-tabs v-model="active_tab_index" class="molding-tabs">
          <el-tab-pane
            v-for="(unit, idx) in injection_machine.injection_units"
            :key="`unit_${idx}`"
            :label="`注射部件-#${Number(idx) + 1}`"
            :name="String(idx)"
          >
            <InjectionUnitForm
              :ref="(el: any) => setUnitRef(el, Number(idx))"
              :injection-unit="unit"
            />
          </el-tab-pane>
        </el-tabs>
      </el-card>

      <!-- 3. 锁模单元 -->
      <el-card class="custom-form__section" shadow="never">
        <template #header>
          <span class="custom-form__title">锁模单元</span>
        </template>

        <el-row
          v-for="(row, rIdx) in clampingRows"
          :key="`clamp_${rIdx}`"
          :gutter="24"
        >
          <el-col
            v-for="(item, iIdx) in row"
            :key="`clamp_${rIdx}_${iIdx}`"
            :span="item.span"
          >
            <el-divider
              v-if="item.type === 'divider'"
              content-position="left"
              class="custom-form__divider"
            >
              {{ item.label }}
            </el-divider>

            <el-form-item
              v-else-if="item.prop"
              :label="item.label"
              :prop="item.prop"
            >
              <el-input
                v-if="item.type === 'number'"
                v-model="injection_machine[item.prop!]"
                v-number="item.precision ?? 2"
                :placeholder="item.placeholder || `请输入${item.label}`"
                clearable
              >
                <template #suffix v-if="item.unit">{{ item.unit }}</template>
                <template #suffix v-else-if="item.dynamic_unit">{{ injection_machine[item.dynamic_unit] }}</template>
              </el-input>

              <el-select
                v-else-if="item.type === 'select'"
                v-model="injection_machine[item.prop!]"
                :placeholder="item.placeholder || `请选择${item.label}`"
                clearable
                filterable
                :allow-create="item.allowCreate !== false"
              >
                <el-option
                  v-for="(opt, oIdx) in item.options"
                  :key="oIdx"
                  :label="opt.label"
                  :value="opt.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-card>

      <!-- 4. 顶出单元 -->
      <el-card class="custom-form__section" shadow="never">
        <template #header>
          <span class="custom-form__title">顶出单元</span>
        </template>

        <el-row
          v-for="(row, rIdx) in ejectionRows"
          :key="`eject_${rIdx}`"
          :gutter="24"
        >
          <el-col
            v-for="(item, iIdx) in row"
            :key="`eject_${rIdx}_${iIdx}`"
            :span="item.span"
          >
            <el-form-item
              :label="item.label"
              :prop="item.prop"
            >
              <el-input
                v-if="item.type === 'number'"
                v-model="injection_machine[item.prop!]"
                v-number="item.precision ?? 2"
                :placeholder="item.placeholder || `请输入${item.label}`"
                clearable
              >
                <template #suffix v-if="item.unit">{{ item.unit }}</template>
                <template #suffix v-else-if="item.dynamic_unit">{{ injection_machine[item.dynamic_unit] }}</template>
              </el-input>

              <el-select
                v-else-if="item.type === 'select'"
                v-model="injection_machine[item.prop!]"
                :placeholder="`请选择${item.label}`"
                clearable
                filterable
                :allow-create="item.allowCreate !== false"
              >
                <el-option
                  v-for="(opt, oIdx) in item.options"
                  :key="oIdx"
                  :label="opt.label"
                  :value="opt.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-card>

      <!-- 5. 配套参数 -->
      <el-card class="custom-form__section" shadow="never">
        <template #header>
          <span class="custom-form__title">配套参数</span>
        </template>

        <el-row
          v-for="(row, rIdx) in supportingRows"
          :key="`supp_${rIdx}`"
          :gutter="24"
        >
          <el-col
            v-for="(item, iIdx) in row"
            :key="`supp_${rIdx}_${iIdx}`"
            :span="item.span"
          >
            <el-divider
              v-if="item.type === 'divider'"
              content-position="left"
              class="custom-form__divider"
            >
              {{ item.label }}
            </el-divider>

            <el-form-item
              v-else-if="item.prop"
              :label="item.label"
              :prop="item.prop"
            >
              <el-input
                v-if="item.type === 'number'"
                v-model="injection_machine[item.prop!]"
                v-number="item.precision ?? 2"
                :placeholder="item.placeholder || `请输入${item.label}`"
                clearable
              >
                <template #suffix v-if="item.unit">{{ item.unit }}</template>
                <template #suffix v-else-if="item.dynamic_unit">{{ injection_machine[item.dynamic_unit] }}</template>
              </el-input>

              <el-date-picker
                v-else-if="item.type === 'date'"
                v-model="injection_machine[item.prop!]"
                type="date"
                placeholder="选择日期"
                value-format="yyyy-MM-dd"
                style="width: 100%;"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-card>
    </el-form>

    <!-- 底部 form-actions（全局统一样式：src/styles/utilities/custom-form.scss） -->
    <div v-if="loaded" class="form-actions">
      <el-button @click="goBack">取消</el-button>
      <el-button
        type="primary"
        :loading="submitting"
        :disabled="!hasPermission('update_machine')"
        @click="handleSave"
      >
        {{ is_copy ? '保存为新条目' : (is_edit ? '保存' : '创建') }}
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, getCurrentInstance } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import {
  machineInfoForm,
  injectionUnitForm,
  injectionMachineBrandOptions,
  injectionMachineManufacturerOptions,
  machineTypeOptions,
  injectionUnitCountOptions,
  driveSystemOptions,
  controllerModelOptions,
  controllerVersionOptions,
  commAbilityOptions,
  communicationProtocolOptions,
  pressureUnitOptions,
  speedUnitOptions,
  positionUnitOptions,
  timeUnitOptions,
  screwRotationUnitOptions,
  temperatureUnitOptions,
  clampingForceUnitOptions,
  clampingTypeOptions,
  ejectionTypeOptions,
  ejectionModeOptions,
} from '@/constants/machine-const'
import { machineMethod } from '@/api'
import { groupIntoRows } from '@/utils/form-layout'
import { createValidateAndFocus, querySuggestions } from '@/utils/form-helper'
import { hasPermission } from '@/utils/permission'
import { openUnitConversionDrawer } from '@/utils/unit-conversion-drawer'
import InjectionUnitForm from '../components/InjectionUnitForm.vue'

const route = useRoute()
const router = useRouter()
const instance = getCurrentInstance()

// ============================================================================
// 路由 / 模式
// ============================================================================

const is_edit = computed(() => !!route.params.id && route.name !== 'equipment-injection-copy')
const is_copy = computed(() => route.name === 'equipment-injection-copy')
const machine_id = computed(() => {
  const id = route.params.id
  return id ? Number(id) : null
})

// ============================================================================
// 状态
// ============================================================================

const formRef = ref<FormInstance>()
const submitting = ref(false)
const loaded = ref(false)
const active_tab_index = ref('0')
const injection_machine = ref<any>(structuredClone(machineInfoForm))

// 注射单元 refs（用函数式 ref 收集，详见模板 setUnitRef）
const injectionUnits = ref<any[]>([])
function setUnitRef(el: any, idx: number) {
  if (el) {
    injectionUnits.value[idx] = el
  }
}

// ============================================================================
// 字段定义
// ============================================================================

// 字段定义（onChange 为本表单特有的 select 钩子，未在 FormItem 中定义，所以不用 FormItem 类型）
type FieldItem = any

const machineDescItems: FieldItem[] = [
  // --- 基础信息 ---
  { label: '设备编号', prop: 'device_no', type: 'input', placeholder: '设备唯一标识', required: true },
  { label: '品牌', prop: 'brand', type: 'select', options: injectionMachineBrandOptions, allowCreate: true },
  { label: '制造商', prop: 'manufacturer', type: 'select', options: injectionMachineManufacturerOptions, allowCreate: true },
  { label: '设备型号', prop: 'model', type: 'autocomplete', query: { table: 'injection_molding_machine', column: 'model' }, placeholder: '请输入设备型号', required: true },
  { label: '设备位置', prop: 'location', type: 'autocomplete', query: { table: 'injection_molding_machine', column: 'location' }, placeholder: '格式：xx工厂-xx车间-xx区' },
  { label: '设备类型', prop: 'machine_type', type: 'select', options: machineTypeOptions, allowCreate: false },
  { label: '射台数量', prop: 'unit_count', type: 'select', options: injectionUnitCountOptions, onChange: onUnitCountChanged, allowCreate: false },
  { label: '驱动系统', prop: 'drive_system', type: 'select', options: driveSystemOptions, allowCreate: false },
  { label: '资产编号', prop: 'asset_no', type: 'input', placeholder: '内部资产编号' },

  // --- 控制器信息 ---
  { label: '控制器信息', type: 'divider' },
  { label: '控制器型号', prop: 'controller_model', type: 'select', options: controllerModelOptions, allowCreate: true },
  { label: '控制器版本', prop: 'controller_version', type: 'select', options: controllerVersionOptions, allowCreate: true },
  { label: '通讯接口', prop: 'is_comm_enabled', type: 'select', options: commAbilityOptions, allowCreate: false },
  { label: '通讯协议', prop: 'communication_protocol', type: 'select', options: communicationProtocolOptions, allowCreate: false },
  { label: '通讯 IP', prop: 'communication_ip', type: 'input', placeholder: '格式：192.168.1.1' },

  // --- 默认单位系统 ---
  { label: '默认单位系统', type: 'divider' },
  { label: '压力单位', prop: 'pressure_unit', type: 'select', options: pressureUnitOptions, allowCreate: false },
  { label: '速度单位', prop: 'speed_unit', type: 'select', options: speedUnitOptions, allowCreate: false },
  { label: '位置单位', prop: 'position_unit', type: 'select', options: positionUnitOptions, allowCreate: false },
  { label: '时间单位', prop: 'time_unit', type: 'select', options: timeUnitOptions, allowCreate: false },
  { label: '背压单位', prop: 'back_pressure_unit', type: 'select', options: pressureUnitOptions, allowCreate: false },
  { label: '螺杆转速单位', prop: 'screw_rotation_unit', type: 'select', options: screwRotationUnitOptions, allowCreate: false },
  { label: '温度单位', prop: 'temperature_unit', type: 'select', options: temperatureUnitOptions, allowCreate: false },
  { label: '锁模力单位', prop: 'clamping_force_unit', type: 'select', options: clampingForceUnitOptions, allowCreate: false },
]

const clampingItems: FieldItem[] = [
  // 锁模性能指标（section 顶部，无 divider 包装）
  { label: '锁模类型', prop: 'clamping_type', type: 'select', options: clampingTypeOptions, allowCreate: false },
  { label: '最大锁模力', prop: 'max_clamping_force', type: 'number', dynamic_unit: 'clamping_force_unit', precision: 0, placeholder: '数值即可，如：1500', required: true },

  // --- 模板与结构参数 ---
  { label: '模板与结构参数', type: 'divider' },
  { label: '定模板宽度', prop: 'fixed_platen_width', type: 'number', unit: 'mm', precision: 2, placeholder: '水平方向尺寸（左右）' },
  { label: '定模板高度', prop: 'fixed_platen_height', type: 'number', unit: 'mm', precision: 2, placeholder: '垂直方向尺寸（上下）' },
  { label: '定模板厚度', prop: 'fixed_platen_thickness', type: 'number', unit: 'mm', precision: 2, placeholder: '定模板本体厚度' },
  { label: '动模板宽度', prop: 'moving_platen_width', type: 'number', unit: 'mm', precision: 2, placeholder: '水平方向尺寸（左右）' },
  { label: '动模板高度', prop: 'moving_platen_height', type: 'number', unit: 'mm', precision: 2, placeholder: '垂直方向尺寸（上下）' },
  { label: '动模板厚度', prop: 'moving_platen_thickness', type: 'number', unit: 'mm', precision: 2, placeholder: '动模板本体厚度' },

  // --- 拉杆（格林柱）参数 ---
  { label: '拉杆参数', type: 'divider' },
  { label: '拉杆间距（宽）', prop: 'tie_bar_spacing_width', type: 'number', unit: 'mm', precision: 2, placeholder: '拉杆内侧水平净距' },
  { label: '拉杆间距（高）', prop: 'tie_bar_spacing_height', type: 'number', unit: 'mm', precision: 2, placeholder: '拉杆内侧垂直净距' },
  { label: '拉杆直径', prop: 'tie_bar_diameter', type: 'number', unit: 'mm', precision: 2, placeholder: '单根拉杆直径' },
  { label: '拉杆数量', prop: 'tie_bar_count', type: 'number', unit: '个', precision: 0, placeholder: '通常为4根' },

  // --- 容模能力 ---
  { label: '容模能力', type: 'divider' },
  { label: '最小模板间距', prop: 'min_platen_spacing', type: 'number', unit: 'mm', precision: 2, placeholder: '模板可闭合的最小距离' },
  { label: '最大模板间距', prop: 'max_platen_spacing', type: 'number', unit: 'mm', precision: 2, placeholder: '模板可打开的最大距离' },
  { label: '最小容模宽度', prop: 'min_mold_length', type: 'number', unit: 'mm', precision: 2, placeholder: '可安装模具最小长度' },
  { label: '最大容模宽度', prop: 'max_mold_length', type: 'number', unit: 'mm', precision: 2, placeholder: '可安装模具最大长度' },
  { label: '最小容模高度', prop: 'min_mold_width', type: 'number', unit: 'mm', precision: 2, placeholder: '可安装模具最小宽度' },
  { label: '最大容模高度', prop: 'max_mold_width', type: 'number', unit: 'mm', precision: 2, placeholder: '可安装模具最大宽度' },
  { label: '最小容模厚度', prop: 'min_mold_thickness', type: 'number', unit: 'mm', precision: 2, placeholder: '可安装模具最小总厚' },
  { label: '最大容模厚度', prop: 'max_mold_thickness', type: 'number', unit: 'mm', precision: 2, placeholder: '可安装模具最大总厚' },
  { label: '最大开模行程', prop: 'max_opening_stroke', type: 'number', unit: 'mm', precision: 2, placeholder: '最大开模距离' },
]

const ejectionItems: FieldItem[] = [
  { label: '顶出类型', prop: 'ejection_type', type: 'select', options: ejectionTypeOptions, allowCreate: true },
  { label: '顶出模式', prop: 'ejection_mode', type: 'select', options: ejectionModeOptions, allowCreate: true },
  { label: '顶出行程', prop: 'ejection_stroke', type: 'number', unit: 'mm', precision: 2 },
  { label: '顶出力', prop: 'ejection_force', type: 'number', unit: 'kN', precision: 2 },
]

const supportingItems: FieldItem[] = [
  { label: '机台长度', prop: 'size_length', type: 'number', unit: 'mm', precision: 2, placeholder: '含油箱、电柜等突出部分' },
  { label: '机台宽度', prop: 'size_width', type: 'number', unit: 'mm', precision: 2, placeholder: '含操作面板或侧向附件' },
  { label: '机台高度', prop: 'size_height', type: 'number', unit: 'mm', precision: 2, placeholder: '至最高点，含料斗/报警灯' },
  { label: '机台重量', prop: 'machine_weight', type: 'number', unit: 'kg', precision: 0, placeholder: '整机干重' },

  { label: '电机功率', prop: 'motor_power', type: 'number', unit: 'kW', precision: 1, placeholder: '主驱动电机额定功率' },
  { label: '电热功率', prop: 'heater_power', type: 'number', unit: 'kW', precision: 1, placeholder: '总加热功率' },
  { label: '额定功率', prop: 'rated_power', type: 'number', unit: 'kW', precision: 1, placeholder: '整机最大输入功率' },

  { label: '制造日期', prop: 'manufacture_date', type: 'date', placeholder: '设备出厂日期' },
  { label: '投产日期', prop: 'commissioning_date', type: 'date', placeholder: '首次正式投入生产日期' },
]

// ============================================================================
// 4 列布局行分组（divider 自动占满 24，span 4 字段默认）
// ============================================================================

const machineDescRows = computed(() => groupIntoRows(machineDescItems, { columns: 4 }))
const clampingRows = computed(() => groupIntoRows(clampingItems, { columns: 4 }))
const ejectionRows = computed(() => groupIntoRows(ejectionItems, { columns: 4 }))
const supportingRows = computed(() => groupIntoRows(supportingItems, { columns: 4 }))

// ============================================================================
// 验证规则
// ============================================================================

const rules: FormRules = {
  model: [{ required: true, message: '设备型号不能为空!', trigger: 'blur' }],
  device_no: [{ required: true, message: '设备编号不能为空!', trigger: 'blur' }],
  max_clamping_force: [{ required: true, message: '最大锁模力不能为空!', trigger: 'blur' }],
}

// ============================================================================
// 单位系统同步（机器顶层 → 所有注射单元）
// ============================================================================

const UNIT_FIELDS = [
  'pressure_unit',
  'speed_unit',
  'position_unit',
  'back_pressure_unit',
  'screw_rotation_unit',
  'time_unit',
  'temperature_unit',
] as const

for (const field of UNIT_FIELDS) {
  watch(
    () => injection_machine.value[field],
    (val) => {
      const units = injection_machine.value.injection_units || []
      for (const u of units) {
        u[field] = val
      }
    },
  )
}

// ============================================================================
// 射台数量变化 → 动态增删注射单元
// ============================================================================

function onUnitCountChanged(val: number | string) {
  const target = Number(val) || 1
  const list: any[] = injection_machine.value.injection_units
  const bef = list.length
  if (bef < target) {
    for (let i = bef; i < target; i++) {
      list.push(structuredClone(injectionUnitForm))
    }
  } else if (bef > target) {
    list.splice(target, bef - target)
  }
  active_tab_index.value = String(Math.max(0, target - 1))
}

// ============================================================================
// 加载详情 / 保存 / 返回 / 重置
// ============================================================================

async function loadDetail(id: number) {
  try {
    const res: any = await machineMethod.getDetail(id)
    if (res.status === 0) {
      injection_machine.value = res.data
      // 确保注射单元数组至少 1 个
      if (!Array.isArray(injection_machine.value.injection_units) || injection_machine.value.injection_units.length === 0) {
        injection_machine.value.injection_units = [structuredClone(injectionUnitForm)]
      }
      if (is_copy.value) {
        // 复制模式：清空 id（后端主键） + 各射台编号（业务标识）
        injection_machine.value.id = null
        for (const u of injection_machine.value.injection_units) {
          u.id = null
          u.unit_code = null
        }
      }
    } else {
      ElMessage.error(res.msg || '未读取到注塑机信息')
      router.push('/equipment/injection/list')
    }
  } catch (err: any) {
    console.error('[InjectionMachineForm] loadDetail failed:', err)
    ElMessage.error(err?.message || '加载注塑机异常')
    router.push('/equipment/injection/list')
  }
}

function goBack() {
  router.push('/equipment/injection/list')
}

/**
 * 打开单位换算抽屉
 * - 预填当前机器型号 + 当前激活 tab 对应的注射单元信息（螺杆直径等）
 * - drawer 顶部会显示"当前射台：注射部件-#N（射台编号 X）"，让用户清晰知道引用的是哪部分数据
 * - 用户在 drawer 内可手动覆盖螺杆直径
 */
function openUnitConverter() {
  const idx = Number(active_tab_index.value) || 0
  const active_unit = injection_machine.value.injection_units?.[idx]
  const unit_code = active_unit?.unit_code
  const label = unit_code
    ? `注射部件-#${idx + 1}（射台编号 ${unit_code}）`
    : `注射部件-#${idx + 1}`
  openUnitConversionDrawer({
    macTrademark: injection_machine.value.model,
    injectorInfo: active_unit ?? null,
    injectorLabel: label,
  })
}

async function handleSave() {
  if (!hasPermission('update_machine')) {
    ElMessage.warning('无机器信息的编辑权限')
    return
  }

  // 校验机器顶层表单
  const validate = createValidateAndFocus(instance?.proxy)
  const okTop = await validate(formRef.value)
  if (!okTop) {
    ElMessage.warning('请检查机器信息必填项')
    return
  }

  // 校验所有注射单元（逐个调用 InjectionUnitForm.checkFormDataValid）
  for (let i = 0; i < injectionUnits.value.length; i++) {
    const component = injectionUnits.value[i]
    if (!component) continue
    const ok = await component.checkFormDataValid()
    if (!ok) {
      active_tab_index.value = String(i)
      ElMessage.warning(`请检查注射部件 #${i + 1} 必填项`)
      return
    }
  }

  submitting.value = true
  try {
    const res: any = injection_machine.value.id
      ? await machineMethod.edit(injection_machine.value, injection_machine.value.id)
      : await machineMethod.add(injection_machine.value)

    if (res.status === 0) {
      ElMessage.success(injection_machine.value.id ? '编辑成功！' : '新增成功！')
      goBack()
    } else {
      ElMessage.error(res.msg || '保存失败')
    }
  } catch (err: any) {
    console.error('[InjectionMachineForm] save failed:', err)
    ElMessage.error(err?.message || '提交异常')
  } finally {
    submitting.value = false
  }
}

// ============================================================================
// 生命周期
// ============================================================================

onMounted(async () => {
  if (machine_id.value !== null) {
    await loadDetail(machine_id.value)
  }
  loaded.value = true
})
</script>

<style lang="scss" scoped>
/*
 * 页面样式（与 PolymerForm 对齐）
 * - 表单内部样式（.custom-form / .custom-form__title / .custom-form__divider 等）
 *   全部依赖全局统一样式：src/styles/utilities/custom-form.scss
 * - 本页仅保留页面容器 / page-header / loading-placeholder / 项目专属 tabs 样式
 */
.injection-machine-form {
  padding: 16px 16px 96px;
  max-width: 1400px;
  margin: 0 auto;
  box-sizing: border-box;
}

.page-header {
  margin-bottom: 16px;
}

.loading-placeholder {
  height: 400px;
}

// 注射单元 tabs 样式（项目自定义）
:deep(.molding-tabs) {
  .el-tabs__header {
    margin-bottom: 12px;
  }

  .el-tab-pane {
    padding-top: 8px;
  }
}

// 注射单元卡片标题栏：标题在左，操作按钮在右
.injection-unit-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
</style>