<!--
  InjectionUnitForm - 注射单元子表单（被 InjectionMachineForm 引用）

  路由：无（子组件）

  设计要点：
  - 数据通过 props.injectionUnit 直接双向绑定（修改 reactive 对象属性即可同步到父级 injection_machine.injection_units）
  - 字段定义：flat items 数组 + groupIntoRows 自动分行（4 列布局）
  - 单位系统（压力/速度/位置/时间/背压/螺杆转速/温度）从机器顶层同步，9 个 HMI 面板参数联动对应单位
  - 暴露 formRef 给父组件统一验证（通过 expose 替代原 Options API 的 this.$refs）
  - 自实现渲染分支（不引入 mold 模块的 FormFieldRenderer）
  - divider 支持 notice（独立 div 包裹，整组带背景）+ description（说明 alert）扩展属性（详见 form-types.ts）
-->
<template>
  <el-form
    ref="formRef"
    :model="injectionUnit"
    :rules="rules"
    class="custom-form"
    label-width="120px"
  >
    <!-- 常规分组渲染（不含 notice section） -->
    <el-row
      v-for="(row, rIdx) in normalRows"
      :key="`row_${rIdx}`"
      :gutter="24"
    >
      <el-col
        v-for="(item, iIdx) in row"
        :key="`field_${rIdx}_${iIdx}`"
        :span="item.span"
      >
        <!-- divider 分组标题 -->
        <el-divider
          v-if="item.type === 'divider'"
          content-position="left"
          class="custom-form__divider"
        >
          {{ item.label }}
        </el-divider>

        <!-- divider 下的说明 alert（带 description 字段才渲染） -->
        <el-alert
          v-if="item.type === 'divider' && item.description"
          :title="item.description"
          type="info"
          :closable="false"
          show-icon
          class="custom-form__divider-alert"
        />

        <!-- 文本输入 -->
        <el-form-item
          v-else-if="item.type === 'input'"
          :label="item.label"
          :prop="item.prop"
          :required="item.required"
        >
          <el-input
            v-model.trim="(injectionUnit as any)[item.prop!]"
            :placeholder="item.placeholder || `请输入${item.label}`"
            clearable
          >
            <template #suffix v-if="item.unit">{{ item.unit }}</template>
            <template #suffix v-else-if="item.dynamicUnit">{{ injectionUnit[item.dynamicUnit] }}</template>
          </el-input>
        </el-form-item>

        <!-- 数值输入（含整数 / 小数） -->
        <el-form-item
          v-else-if="item.type === 'number'"
          :label="item.label"
          :prop="item.prop"
          :required="item.required"
        >
          <el-input
            v-model="(injectionUnit as any)[item.prop!]"
            v-number="item.precision ?? 2"
            :placeholder="item.placeholder || `请输入${item.label}`"
            clearable
          >
            <template #suffix v-if="item.unit">{{ item.unit }}</template>
            <template #suffix v-else-if="item.dynamicUnit">{{ injectionUnit[item.dynamicUnit] }}</template>
          </el-input>
        </el-form-item>

        <!-- 下拉选择（系统字典） -->
        <el-form-item
          v-else-if="item.type === 'select'"
          :label="item.label"
          :prop="item.prop"
        >
          <el-select
            v-model="(injectionUnit as any)[item.prop!]"
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

        <!-- 数值 + 下拉混合（喷嘴孔直径等选项带单位的字段） -->
        <el-form-item
          v-else-if="item.type === 'number-select'"
          :label="item.label"
          :prop="item.prop"
        >
          <el-select
            v-model="(injectionUnit as any)[item.prop!]"
            v-number="item.precision"
            :placeholder="item.placeholder || `请选择${item.label}`"
            clearable
            filterable
            :allow-create="item.allowCreate !== false"
            @clear="() => ((injectionUnit as any)[item.prop!] = null)"
          >
            <el-option
              v-for="(opt, oIdx) in item.options"
              :key="oIdx"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>

        <!-- 自动补全（联想输入） -->
        <el-form-item
          v-else-if="item.type === 'autocomplete'"
          :label="item.label"
          :prop="item.prop"
        >
          <el-autocomplete
            v-model.trim="(injectionUnit as any)[item.prop!]"
            :placeholder="item.placeholder || '请输入内容'"
            clearable
            :debounce="0"
            :fetch-suggestions="(queryString: string, cb: any) => buildQuerySuggestions(item.query!)(queryString, cb)"
          />
        </el-form-item>

        <!-- 日期选择 -->
        <el-form-item
          v-else-if="item.type === 'date'"
          :label="item.label"
          :prop="item.prop"
        >
          <el-date-picker
            v-model="(injectionUnit as any)[item.prop!]"
            type="date"
            placeholder="选择日期"
            value-format="yyyy-MM-dd"
          />
        </el-form-item>
      </el-col>
    </el-row>

    <!-- notice section 独立渲染（整组背景） -->
    <div
      v-if="noticeSection"
      class="custom-form__notice-section"
    >
      <el-divider content-position="left" class="custom-form__divider">
        <span class="custom-form__divider-icon" aria-hidden="true">★</span>
        {{ noticeSection.divider.label }}
      </el-divider>

      <el-alert
        v-if="noticeSection.divider.description"
        :title="noticeSection.divider.description"
        type="info"
        :closable="false"
        show-icon
        class="custom-form__divider-alert"
      />

      <div class="custom-form__notice-grid">
        <el-form-item
          v-for="(field, fIdx) in noticeSection.fields"
          :key="`notice_${fIdx}`"
          :label="field.label"
          :prop="field.prop"
          :required="field.required"
        >
          <el-input
            v-model="(injectionUnit as any)[field.prop!]"
            v-number="field.precision ?? 2"
            :placeholder="field.placeholder || `请输入${field.label}`"
            clearable
          >
            <template #suffix v-if="field.unit">{{ field.unit }}</template>
          </el-input>
        </el-form-item>
      </div>
    </div>
  </el-form>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { querySuggestions as buildQuerySuggestions } from '@/utils/form-helper'
import { groupIntoRows } from '@/utils/form-layout'
import type { FormItem } from '@/utils/form-types'
import {
  nozzleTypeOptions,
  screwTypeOptions,
  pressureUnitOptions,
  speedUnitOptions,
  positionUnitOptions,
  timeUnitOptions,
  screwRotationUnitOptions,
  temperatureUnitOptions,
  maxInjectionStagesOptions,
  maxHoldingStagesOptions,
  maxMeteringStagesOptions,
  maxTempZonesOptions,
  nozzleHoleDiameterOptions,
  nozzleSphereRadiusOptions,
} from '@/constants/machine-const'

/**
 * props 数据双向绑定说明：
 * - props.injectionUnit 是 InjectionMachineForm.injection_machine.injection_units[i] 的引用（reactive 对象）
 * - 直接修改属性会同步到父级（v-model="(injectionUnit as any)[prop]" 生效）
 * - 子组件不创建本地 ref，保持单向数据流
 */
const props = defineProps<{
  injectionUnit: Record<string, any>
}>()

/**
 * 验证规则（与 InjectionMachineForm 一致：required 字段才校验）
 */
const rules: FormRules = {
  unit_code: [
    { required: true, message: '射台编号不能为空!', trigger: 'blur' },
  ],
  nozzle_type: [
    { required: true, message: '喷嘴类型不能为空!', trigger: 'change' },
  ],
}

const formRef = ref<FormInstance>()

/**
 * 字段定义（flat items，45 字段，4 列布局 → 自动分行 12 行）
 *
 * 5 个 divider 分组（全部 ≥ 4 字段，符合 3+ 规则）：
 *   - 喷嘴螺杆组件（10）
 *   - 控制系统能力（4）/ 界面单位信息（7）
 *   - 操作面板参数（界面显示上限）（9）/ 设备出厂参数（真实极限）（9，notice=true）
 *
 * 顶部 6 字段（无 divider 包装，作为开篇基础信息，射台编号 + 塑化/注射能力高频关注）：
 *   射台编号 / 塑化能力 / 最大注射行程 / 最大注射体积 / 最大注射重量 / 料筒加热功率
 *
 * 设备出厂参数 vs 操作面板参数（顺序逻辑：先易后难）：
 * - 操作面板参数（界面显示上限）：HMI 控制面板允许设定的最大值，从面板直接读取（90% 场景够用）
 * - 设备出厂参数（真实极限）：来自设备铭牌或厂家技术规格书（铭牌不一定有），单位固定为国际单位（工艺计算场景需要）
 */
const formItems: FormItem[] = [
  // 顶部：射台基础信息（6 字段平铺，高频关注：射台编号 + 塑化与注射能力）
  { label: '射台编号', prop: 'unit_code', type: 'input', placeholder: '射台标识（多射台时用于区分各注射部件）', required: true },
  { label: '塑化能力', prop: 'plasticizing_capacity', type: 'number', unit: 'g/h', precision: 2 },
  { label: '最大注射行程', prop: 'max_injection_stroke', type: 'number', dynamicUnit: 'position_unit', precision: 2 },
  { label: '最大注射体积', prop: 'max_injection_volume', type: 'number', unit: 'cm³', precision: 2 },
  { label: '最大注射重量', prop: 'max_injection_weight', type: 'number', unit: 'g', precision: 2 },
  { label: '料筒加热功率', prop: 'barrel_heating_power', type: 'number', unit: 'kW', precision: 2 },

  // --- 喷嘴螺杆组件（机械结构参数）---
  { label: '喷嘴螺杆组件', type: 'divider' },
  { label: '喷嘴类型', prop: 'nozzle_type', type: 'select', options: nozzleTypeOptions, allowCreate: false, required: true },
  { label: '喷嘴伸出量', prop: 'nozzle_protrusion', type: 'number', unit: 'mm', precision: 2, placeholder: '常见默认值：15mm / 20mm' },
  { label: '喷嘴孔直径', prop: 'nozzle_hole_diameter', type: 'number-select', unit: 'mm', precision: 2, options: nozzleHoleDiameterOptions, allowCreate: false },
  { label: '喷嘴球半径', prop: 'nozzle_sphere_radius', type: 'number-select', unit: 'mm', precision: 2, options: nozzleSphereRadiusOptions, allowCreate: false },
  { label: '喷嘴接触力', prop: 'nozzle_contact_force', type: 'number', unit: 'kN', precision: 2 },
  { label: '螺杆类型', prop: 'screw_type', type: 'select', options: screwTypeOptions, allowCreate: false },
  { label: '螺杆直径', prop: 'screw_diameter', type: 'number', unit: 'mm', precision: 2, placeholder: '螺杆横截面积 mm² / 周长 mm' },
  { label: '长径比L/D', prop: 'screw_length_to_diameter_ratio', type: 'number', precision: 2 },
  { label: '压缩比', prop: 'screw_compression_ratio', type: 'number', precision: 2 },
  { label: '增强比', prop: 'screw_enhancement_ratio', type: 'number', precision: 2 },

  // --- 控制系统能力（最大段数） ---
  // 业务数据而非系统字典：允许创建超过 options 的值（后端 PositiveSmallIntegerField 无上限）
  { label: '控制系统能力（最大段数）', type: 'divider' },
  { label: '最大注射段数', prop: 'max_injection_stages', type: 'number-select', precision: 0, options: maxInjectionStagesOptions, allowCreate: true },
  { label: '最大保压段数', prop: 'max_holding_stages', type: 'number-select', precision: 0, options: maxHoldingStagesOptions, allowCreate: true },
  { label: '最大计量段数', prop: 'max_metering_stages', type: 'number-select', precision: 0, options: maxMeteringStagesOptions, allowCreate: true },
  { label: '最大温控区域', prop: 'max_temperature_control_zones', type: 'number-select', precision: 0, options: maxTempZonesOptions, allowCreate: true },

  // --- 界面单位信息（射台级覆盖）---
  { label: '界面单位信息', type: 'divider' },
  { label: '压力单位', prop: 'pressure_unit', type: 'select', options: pressureUnitOptions, allowCreate: false },
  { label: '速度单位', prop: 'speed_unit', type: 'select', options: speedUnitOptions, allowCreate: false },
  { label: '位置单位', prop: 'position_unit', type: 'select', options: positionUnitOptions, allowCreate: false },
  { label: '时间单位', prop: 'time_unit', type: 'select', options: timeUnitOptions, allowCreate: false },
  { label: '背压单位', prop: 'back_pressure_unit', type: 'select', options: pressureUnitOptions, allowCreate: false },
  { label: '螺杆转速单位', prop: 'screw_rotation_unit', type: 'select', options: screwRotationUnitOptions, allowCreate: false },
  { label: '温度单位', prop: 'temperature_unit', type: 'select', options: temperatureUnitOptions, allowCreate: false },

  // --- 操作面板参数（界面显示上限）---
  // HMI 控制面板允许设定的最大值，从面板直接读取（90% 场景够用，先放前面）
  { label: '操作面板参数（界面显示上限）', type: 'divider', description: 'HMI 控制面板允许设定的最大值，从面板直接读取。可能用 bar/%/Hz 等非标准单位，与设备真实极限不一定一致。' },
  { label: '最大注射压力', prop: 'max_set_injection_pressure', type: 'number', dynamicUnit: 'pressure_unit', precision: 2, placeholder: '面板显示上限' },
  { label: '最大注射速度', prop: 'max_set_injection_speed', type: 'number', dynamicUnit: 'speed_unit', precision: 2, placeholder: '面板显示上限' },
  { label: '最大保压压力', prop: 'max_set_holding_pressure', type: 'number', dynamicUnit: 'pressure_unit', precision: 2, placeholder: '面板显示上限' },
  { label: '最大保压速度', prop: 'max_set_holding_speed', type: 'number', dynamicUnit: 'speed_unit', precision: 2, placeholder: '面板显示上限' },
  { label: '最大计量压力', prop: 'max_set_metering_pressure', type: 'number', dynamicUnit: 'pressure_unit', precision: 2, placeholder: '面板显示上限（全电机无）' },
  { label: '最大螺杆转速', prop: 'max_set_screw_rotation_speed', type: 'number', dynamicUnit: 'screw_rotation_unit', precision: 2, placeholder: '面板显示上限' },
  { label: '最大计量背压', prop: 'max_set_metering_back_pressure', type: 'number', dynamicUnit: 'back_pressure_unit', precision: 2, placeholder: '面板显示上限' },
  { label: '最大松退压力', prop: 'max_set_decompression_pressure', type: 'number', dynamicUnit: 'pressure_unit', precision: 2, placeholder: '面板显示上限' },
  { label: '最大松退速度', prop: 'max_set_decompression_speed', type: 'number', dynamicUnit: 'speed_unit', precision: 2, placeholder: '面板显示上限' },

  // --- 设备出厂参数（真实物理极限）---
  // 来自设备铭牌或厂家技术规格书（铭牌不一定有），单位固定为国际单位（MPa/rpm/mm/s）
  // notice=true：整组独立 div 包裹，加背景 + 左边框
  { label: '设备出厂参数（真实物理极限）', type: 'divider', notice: true, description: '设备出厂的真实物理极限，需联系厂家或查看技术规格书获取。单位固定为国际单位（MPa/rpm/mm/s）。' },
  { label: '最大注射压力', prop: 'max_injection_pressure', type: 'number', unit: 'MPa', precision: 2, placeholder: '实际值' },
  { label: '最大注射速度', prop: 'max_injection_speed', type: 'number', unit: 'mm/s', precision: 2, placeholder: '实际值' },
  { label: '最大保压压力', prop: 'max_holding_pressure', type: 'number', unit: 'MPa', precision: 2, placeholder: '实际值' },
  { label: '最大保压速度', prop: 'max_holding_speed', type: 'number', unit: 'mm/s', precision: 2, placeholder: '实际值' },
  { label: '最大计量压力', prop: 'max_metering_pressure', type: 'number', unit: 'MPa', precision: 2, placeholder: '实际值（全电机无）' },
  { label: '最大螺杆转速', prop: 'max_screw_rotation_speed', type: 'number', unit: 'rpm', precision: 2, placeholder: '实际值' },
  { label: '最大计量背压', prop: 'max_metering_back_pressure', type: 'number', unit: 'MPa', precision: 2, placeholder: '实际值' },
  { label: '最大松退压力', prop: 'max_decompression_pressure', type: 'number', unit: 'MPa', precision: 2, placeholder: '实际值' },
  { label: '最大松退速度', prop: 'max_decompression_speed', type: 'number', unit: 'mm/s', precision: 2, placeholder: '实际值' },
]

/**
 * 拆分 formItems 为"普通段" + "notice 段"
 *
 * 设计要点（2026-09-09 简化）：
 * - 业务方仍按 flat items 顺序定义所有字段（含 notice 段）
 * - 渲染时自动拆分：notice=true 的 divider + 其后续所有字段 → noticeSection
 * - 普通段走原 el-row/el-col 网格，notice 段走独立 div（整组带背景）
 * - 相比之前用 :has() CSS 选择器，逻辑更直观，无需重构 grid 算法
 */
const normalItems = computed<FormItem[]>(() => {
  const result: FormItem[] = []
  let inNotice = false
  for (const item of formItems) {
    if (item.type === 'divider') {
      inNotice = !!item.notice
    }
    if (!inNotice) {
      result.push(item)
    }
  }
  return result
})

const noticeSection = computed<{ divider: FormItem; fields: FormItem[] } | null>(() => {
  let divider: FormItem | null = null
  const fields: FormItem[] = []
  let inNotice = false

  for (const item of formItems) {
    if (item.type === 'divider') {
      if (item.notice) {
        inNotice = true
        divider = item
      } else {
        inNotice = false
      }
    } else if (inNotice) {
      fields.push(item)
    }
  }
  return divider ? { divider, fields } : null
})

// 自动分行（4 列布局：normalItems 36 字段 ÷ 4 列 ≈ 9 行）
const normalRows = computed(() => groupIntoRows(normalItems.value, { columns: 4 }))

/**
 * 暴露给父组件 InjectionMachineForm 统一验证
 * - 父组件通过 ref.checkFormDataValid() 调用
 * - 与 EjectionSystemForm / CoolingSystemForm 风格一致
 */
defineExpose({
  formRef,
  /** 兼容旧调用：父组件可能调用 checkFormDataValid() */
  async checkFormDataValid(): Promise<boolean> {
    try {
      await formRef.value?.validate()
      return true
    } catch {
      return false
    }
  },
})
</script>

<style scoped lang="scss">
/* 子组件无特有样式，复用 custom-form 全局样式 */
</style>
