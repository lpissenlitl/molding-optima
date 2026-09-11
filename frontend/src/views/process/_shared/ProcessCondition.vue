<!--
  ProcessCondition - 工艺条件卡（可折叠）

  父组件通过 :process-condition="..." 传入条件对象，
  通过 ref 暴露 checkFormDataValid() 给父组件做提交前校验。

  ┌────────────────────────────────────────────────────────────────┐
  │ ▼ 工艺条件                              [收起 ▲]               │  ← 展开态 header
  │ ────────────────────────────────────────────────────────────  │
  │  模具 / 注塑机 / 材料 三个 area                              │
  │   · 每个 area 顶部是主选（模具编号/工艺射次 等）                       │
  │   · 下面是子 subsection 容器（块状白底 + 边框）                │
  │   · 父子嵌套用 .subsection-block--nested / --deep-nested      │
  └────────────────────────────────────────────────────────────────┘

  ┌────────────────────────────────────────────────────────────────┐
  │ ▶ 工艺条件  📋 PC2025-001 [使用中]  模具:M001/射1  ...     [展开编辑 ▼] │  ← 折叠态 header
  └────────────────────────────────────────────────────────────────┘

  字段来源（后端 ProcessCondition 模型）：
    - mold_id / shot_index                模具 + 第几射
    - injection_machine_id / injection_index  注塑机 + 第几个注射单元
    - polymer_id                          材料
    - condition_no / status               展示用（由后端生成）

  架构（2026-09-11 重构 v3）：
    - 可折叠能力：展开=表单 / 折叠=简要信息（条件号+状态+模具/机器/材料）
    - view mode：强制折叠（不可展开）
    - new/edit/transplant mode：可折叠，defaultExpanded 控制默认状态
    - 单大卡（el-card），不分子卡
    - 三个 area（模具/注塑机/材料）用 .area-section 平铺分隔，不用边框容器
    - 主选字段在 area 顶部 el-row，派生字段下沉到子 subsection-block
    - 父子嵌套：subsection-block（白底）→ --nested（左边线）→ --deep-nested（更浅边线）
    - 派生字段 v-if 显示，仅在选了主数据后才出现
    - 数字字段用 v-number 指令（不用 el-input-number）
    - 复用全局 .custom-form 响应式布局

  校验：
    - 父组件通过 ref 调 checkFormDataValid() 触发 el-form 的 validate
    - 必填 5 项：mold_id / shot_index / injection_machine_id / injection_index / polymer_id
-->
<template>
  <el-card
    class="process-condition-card"
    :class="{ 'is-collapsed': !expanded, 'is-readonly': isReadOnly }"
    shadow="never"
  >
    <!-- 卡片 header：可点击切换（仅在可折叠时） -->
    <template #header>
      <div
        class="process-condition-card__header"
        :class="{ 'is-clickable': !isReadOnly }"
        @click="toggle"
      >
        <!-- 左侧：折叠图标 + 标题 -->
        <div class="process-condition-card__header-left">
          <AppIcon
            :icon="expanded ? 'mdi:chevron-down' : 'mdi:chevron-right'"
            class="process-condition-card__toggle-icon"
          />
          <span class="custom-form__title">工艺条件</span>
        </div>

        <!-- 折叠态：显示简要信息 -->
        <div v-show="!expanded" class="process-condition-card__summary">
          <span class="summary-item">
            <AppIcon icon="mdi:identifier" class="summary-item__icon" />
            <span class="summary-item__value">
              {{ condition.condition_no || '/' }}
            </span>
          </span>
          <el-tag
            v-if="condition.status"
            size="small"
            :type="STATUS_TAG_TYPE[condition.status]"
          >
            {{ STATUS_MAP[condition.status] }}
          </el-tag>
          <template v-if="hasMold">
            <el-divider direction="vertical" />
            <span class="summary-item">
              <AppIcon icon="mdi:cube-outline" class="summary-item__icon" />
              <span class="summary-item__label">模具</span>
              <span class="summary-item__value">
                {{ condition.mold_info?.mold_no }}
                <span class="summary-item__sep">/</span>
                射{{ shotIndexDisplay }}
              </span>
            </span>
          </template>
          <template v-if="hasMachine">
            <el-divider direction="vertical" />
            <span class="summary-item">
              <AppIcon icon="mdi:server-outline" class="summary-item__icon" />
              <span class="summary-item__label">机器</span>
              <span class="summary-item__value">
                {{ condition.machine_info?.brand }}
                {{ condition.machine_info?.model }}
                <span class="summary-item__sep">/</span>
                射台{{ injectionIndexDisplay }}
              </span>
            </span>
          </template>
          <template v-if="hasPolymer">
            <el-divider direction="vertical" />
            <span class="summary-item">
              <AppIcon icon="mdi:flask-outline" class="summary-item__icon" />
              <span class="summary-item__label">材料</span>
              <span class="summary-item__value">
                {{ condition.polymer_info?.abbreviation }}
              </span>
            </span>
          </template>
        </div>

        <!-- 右侧：展开/收起按钮（仅在可折叠时显示） -->
        <div v-if="!isReadOnly" class="process-condition-card__header-right">
          <el-button text size="small" @click.stop="toggle">
            {{ expanded ? '收起' : '展开编辑' }}
          </el-button>
        </div>
      </div>
    </template>

    <!-- 卡片 body：可折叠 -->
    <transition name="process-condition-collapse">
      <div v-show="expanded" class="process-condition-card__body">
        <el-form
          ref="formRef"
          :model="condition"
          :rules="rules"
          class="custom-form"
          label-width="120px"
        >
          <!-- ════════════════════════════════════════════════════════════════
               1. 模具
               ════════════════════════════════════════════════════════════════ -->
          <div class="area-section">
            <span class="custom-form__title">模具</span>
            <el-row :gutter="24">
              <!-- 主选字段（2 个：模具编号 / 射次；制品属于浇注系统下的内容，在下方浇注系统 subsection 内部选择） -->
              <el-col :xs="24" :sm="12" :md="12">
                <el-form-item label="模具编号" prop="mold_id" label-width="auto">
                  <el-autocomplete
                    v-model="moldQuery"
                    :fetch-suggestions="fetchMoldSuggestions"
                    :debounce="300"
                    placeholder="输入或选择模具"
                    clearable
                    :disabled="disabled"
                    @select="onMoldSelect"
                    @clear="onMoldClear"
                  >
                    <template #prefix>
                      <AppIcon icon="mdi:cube-outline" />
                    </template>
                  </el-autocomplete>
                </el-form-item>
              </el-col>
            </el-row>

            <!-- ============ 基本信息 subsection(模具主选后跟随的模具派生字段)
                 名称用“基本信息”而不是“模具信息”：
                 · 同一命名也适用于注塑机/材料(都可用"基本信息"包装主选后的派生字段)
                 · 不限于模具,语义上中立、便于复用 -->
            <div class="subsection-block">
              <div class="subsection-block__header">
                <span class="subsection-block__title">
                  <AppIcon icon="mdi:information-outline" />
                  基本信息
                </span>
              </div>
              <el-row :gutter="24" class="subsection-block__content">
                <el-col :xs="24" :sm="12" :md="6">
                  <DerivedField label="模具名称" :value="condition.mold_info?.mold_name" />
                </el-col>
                <el-col :xs="24" :sm="12" :md="6">
                  <DerivedField label="产品大类" :value="condition.mold_info?.product_category" />
                </el-col>
                <el-col :xs="24" :sm="12" :md="6">
                  <DerivedField label="注射次数" :value="shotCount" unit="射" />
                </el-col>
                <el-col :xs="24" :sm="12" :md="6">
                  <DerivedField
                    label="型腔布局"
                    :value="condition.mold_info?.cavity_layout"
                    :tooltip="CAVITY_LAYOUT_TOOLTIP"
                  />
                </el-col>
              </el-row>
            </div>

            <!-- 主选:工艺射次(与浇注系统 subsection 紧邻,语义上“选第几射 → 查看该射浇注系统”)
                 label-width=auto,避免该行只有一个字段时 label-width=120px 带来的大量空白 -->
            <el-row :gutter="24" style="margin-top: 16px;">
              <el-col :xs="24" :sm="12" :md="12">
                <el-form-item label="工艺射次" prop="shot_index" label-width="auto">
                  <el-select
                    v-if="hasMultipleShots"
                    v-model="shotIndexStr"
                    :disabled="disabled"
                    placeholder="选择第几射"
                    style="width: 100%;"
                  >
                    <el-option
                      v-for="i in shotCount"
                      :key="i"
                      :label="`第 ${i} 射`"
                      :value="String(i)"
                    />
                  </el-select>
                  <el-input
                    v-else
                    v-model="shotIndexStr"
                    v-number="0"
                    placeholder="1（单射默认）"
                    :disabled="true"
                  >
                    <template #suffix>射</template>
                  </el-input>
                </el-form-item>
              </el-col>
            </el-row>

            <!-- ============ 浇注系统 subsection(当前射的浇注系统 + 浇注级派生 + 制品平铺 + 浇口平铺) ============ -->
            <!-- 依存：选中模具 + 当前射存在 gating_system 才显示(随射次切换) -->
            <div v-if="gatingDerived" class="subsection-block">
              <div class="subsection-block__header">
                <span class="subsection-block__title">
                  <AppIcon icon="mdi:pipe" />
                  浇注系统
                  <template v-if="hasMultipleShots">
                    <span class="subsection-block__shot">（第 {{ shotIndexDisplay }} 射）</span>
                  </template>
                </span>
              </div>

              <!-- 浇注系统级字段（不属于任何 cavity,是整个 gating_system 共享的） -->
              <el-row :gutter="24" class="subsection-block__content">
                <el-col :xs="24" :sm="12" :md="6">
                  <DerivedField label="流道类别" :value="gatingDerived?.runner_type" />
                </el-col>
                <el-col :xs="24" :sm="12" :md="6">
                  <DerivedField
                    label="制品总重量"
                    :value="gatingDerived?.total_product_weight"
                    unit="g"
                  />
                </el-col>
                <template v-if="gatingDerived?.runner_type === '冷流道' || gatingDerived?.runner_type === '热转冷'">
                  <el-col :xs="24" :sm="12" :md="6">
                    <DerivedField
                      label="流道重量"
                      :value="gatingDerived?.runner_weight"
                      unit="g"
                    />
                  </el-col>
                </template>
                <template v-if="gatingDerived?.runner_type === '热流道' || gatingDerived?.runner_type === '热转冷'">
                  <el-col :xs="24" :sm="12" :md="6">
                    <DerivedField
                      label="热喷嘴数量"
                      :value="gatingDerived?.hot_runner_nozzle_count"
                      unit="个"
                    />
                  </el-col>
                  <el-col v-if="gatingDerived?.hot_runner_supplier" :xs="24" :sm="12" :md="6">
                    <DerivedField
                      label="热流道供应商"
                      :value="gatingDerived.hot_runner_supplier"
                    />
                  </el-col>
                </template>
              </el-row>

              <!-- 派生信息：浇注系统下的所有制品(cavity)平铺展示。
                  一次注射成型对应浇注下所有腔体同时成型，
                  所以不提供“切第几件”的主选、每个 cavity 都作为一个完整于区块展开 -->
              <div
                v-for="(cavity, cIdx) in cavities"
                v-show="cavities.length"
                :key="`cavity_${cIdx}`"
                class="subsection-block subsection-block--nested"
              >
                <div class="subsection-block__header">
                  <span class="subsection-block__title">
                    <AppIcon icon="mdi:package-variant-closed" />
                    制品 #{{ cIdx + 1 }}
                    <template v-if="cavity.product_name">
                      <span class="subsection-block__shot">（{{ cavity.product_name }}）</span>
                    </template>
                  </span>
                </div>
                <el-row :gutter="24" class="subsection-block__content">
                  <el-col :xs="24" :sm="12" :md="6">
                    <DerivedField label="制品编号" :value="cavity.product_code" />
                  </el-col>
                  <el-col :xs="24" :sm="12" :md="6">
                    <DerivedField label="制品名称" :value="cavity.product_name" />
                  </el-col>
                  <el-col :xs="24" :sm="12" :md="6">
                    <DerivedField
                      label="单腔重量"
                      :value="cavity.estimated_weight_per_cavity"
                      unit="g"
                    />
                  </el-col>
                  <el-col :xs="24" :sm="12" :md="6">
                    <DerivedField label="型腔数" :value="cavity.cavity_count_per_shot" unit="个" />
                  </el-col>
                  <el-col :xs="24" :sm="12" :md="6">
                    <DerivedField
                      label="平均壁厚"
                      :value="cavity.ave_wall_thickness"
                      unit="mm"
                    />
                  </el-col>
                  <el-col :xs="24" :sm="12" :md="6">
                    <DerivedField
                      label="最大壁厚"
                      :value="cavity.max_wall_thickness"
                      unit="mm"
                    />
                  </el-col>
                  <el-col :xs="24" :sm="12" :md="6">
                    <DerivedField
                      label="最大流长"
                      :value="cavity.max_flow_length"
                      unit="mm"
                    />
                  </el-col>
                </el-row>

                <!-- 浇口列表（每个 cavity 下 1:N 个浇口,平铺展示） -->
                <div
                  v-for="(gate, gIdx) in cavity.gates"
                  v-show="cavity.gates && cavity.gates.length"
                  :key="`gate_${cIdx}_${gIdx}`"
                  class="subsection-block subsection-block--deep-nested"
                >
                  <div class="subsection-block__header">
                    <span class="subsection-block__title">
                      <AppIcon icon="mdi:flash-triangle-outline" />
                      浇口 #{{ gIdx + 1 }}
                      <template v-if="gate.gate_shape">
                        <span class="subsection-block__shot">（{{ gate.gate_shape }}）</span>
                      </template>
                    </span>
                  </div>
                  <el-row :gutter="24" class="subsection-block__content">
                    <el-col :xs="24" :sm="12" :md="6">
                      <DerivedField label="浇口类别" :value="gate.gate_type" />
                    </el-col>
                    <el-col :xs="24" :sm="12" :md="6">
                      <DerivedField label="浇口数量" :value="gate.gate_count" unit="个" />
                    </el-col>
                    <el-col :xs="24" :sm="12" :md="6">
                      <DerivedField label="浇口形状" :value="gate.gate_shape" />
                    </el-col>
                    <el-col :xs="24" :sm="12" :md="6">
                      <DerivedField label="浇口位置" :value="gate.location_description" />
                    </el-col>
                    <!-- 条件渲染：圆 / 矩 -->
                    <template v-if="gate.gate_shape === '圆形'">
                      <el-col :xs="24" :sm="12" :md="6">
                        <DerivedField label="浇口直径" :value="gate.diameter" unit="mm" />
                      </el-col>
                    </template>
                    <template v-else-if="gate.gate_shape === '矩形'">
                      <el-col :xs="24" :sm="12" :md="6">
                        <DerivedField label="浇口长" :value="gate.length" unit="mm" />
                      </el-col>
                      <el-col :xs="24" :sm="12" :md="6">
                        <DerivedField label="浇口宽" :value="gate.width" unit="mm" />
                      </el-col>
                    </template>
                  </el-row>
                </div>
              </div>
            </div>
          </div>

          <!-- ════════════════════════════════════════════════════════════════
               2. 注塑机
               ════════════════════════════════════════════════════════════════ -->
          <div class="area-section">
            <span class="custom-form__title">注塑机</span>
          <el-row :gutter="24">
            <!-- 注塑机（主选） -->
            <el-col :xs="24" :sm="12" :md="6">
              <el-form-item label="注塑机" prop="injection_machine_id">
                <el-autocomplete
                  v-model="machineQuery"
                  :fetch-suggestions="fetchMachineSuggestions"
                  :debounce="300"
                  placeholder="输入或选择注塑机"
                  clearable
                  :disabled="disabled"
                  @select="onMachineSelect"
                  @clear="onMachineClear"
                >
                  <template #prefix>
                    <AppIcon icon="mdi:server-outline" />
                  </template>
                </el-autocomplete>
              </el-form-item>
            </el-col>

            <!-- 射台（主选，多射台下拉；单射台时禁用显示 1） -->
            <el-col :xs="24" :sm="12" :md="6">
              <el-form-item label="射台" prop="injection_index">
                <el-select
                  v-if="hasMultipleUnits"
                  v-model="injectionIndexStr"
                  :disabled="disabled"
                  placeholder="选择第几射台"
                  style="width: 100%;"
                >
                  <el-option
                    v-for="i in unitCount"
                    :key="i"
                    :label="`第 ${i} 射台`"
                    :value="String(i)"
                  />
                </el-select>
                <el-input
                  v-else
                  v-model="injectionIndexStr"
                  v-number="0"
                  placeholder="1（单射台默认）"
                  :disabled="true"
                >
                  <template #suffix>射台</template>
                </el-input>
              </el-form-item>
            </el-col>

            <!-- 派生信息：选中注塑机后显示 -->
            <el-col v-if="condition.machine_info" :xs="24" :sm="12" :md="6">
              <DerivedField label="品牌" :value="condition.machine_info.brand" />
            </el-col>
            <el-col v-if="condition.machine_info" :xs="24" :sm="12" :md="6">
              <DerivedField label="设备编号" :value="condition.machine_info.device_no" />
            </el-col>

            <!-- 关键工艺属性：射台数量 -->
            <el-col v-if="condition.machine_info" :xs="24" :sm="12" :md="6">
              <DerivedField label="射台数量" :value="unitCount" unit="个" />
            </el-col>
            <el-col v-if="condition.machine_info" :xs="24" :sm="12" :md="6">
              <DerivedField
                label="锁模力"
                :value="condition.machine_info.max_clamping_force"
                unit="kN"
              />
            </el-col>
          </el-row>

          <!-- ============ 射台信息子 section（当前射台的射台字段）============ -->
            <div v-if="condition.machine_info" class="subsection-block">
              <div class="subsection-block__header">
                <span class="subsection-block__title">
                  <AppIcon icon="mdi:water-pump" />
                  射台信息
                  <template v-if="hasMultipleUnits">
                    <span class="subsection-block__shot">（第 {{ injectionIndexDisplay }} 射台）</span>
                  </template>
                </span>
              </div>
              <el-row :gutter="24" class="subsection-block__content">
                <el-col :xs="24" :sm="12" :md="6">
                  <DerivedField label="射台编码" :value="injectionUnitDerived?.unit_code" />
                </el-col>
                <el-col :xs="24" :sm="12" :md="6">
                  <DerivedField
                    label="最大注射行程"
                    :value="injectionUnitDerived?.max_injection_stroke"
                    unit="mm"
                  />
                </el-col>
                <el-col :xs="24" :sm="12" :md="6">
                  <DerivedField
                    label="最大注射重量"
                    :value="injectionUnitDerived?.max_injection_weight"
                    unit="g"
                  />
                </el-col>
                <el-col :xs="24" :sm="12" :md="6">
                  <DerivedField
                    label="螺杆直径"
                    :value="injectionUnitDerived?.screw_diameter"
                    unit="mm"
                  />
                </el-col>
              </el-row>
            </div>
          </div>

          <!-- ════════════════════════════════════════════════════════════════
               3. 材料
               ════════════════════════════════════════════════════════════════ -->
          <div class="area-section">
            <span class="custom-form__title">材料</span>
          <el-row :gutter="24">
            <el-col :xs="24" :sm="12" :md="6">
              <el-form-item label="塑料" prop="polymer_id">
                <el-autocomplete
                  v-model="polymerQuery"
                  :fetch-suggestions="fetchPolymerSuggestions"
                  :debounce="300"
                  placeholder="输入或选择塑料"
                  clearable
                  :disabled="disabled"
                  @select="onPolymerSelect"
                  @clear="onPolymerClear"
                >
                  <template #prefix>
                    <AppIcon icon="mdi:flask-outline" />
                  </template>
                </el-autocomplete>
              </el-form-item>
            </el-col>

            <el-col v-if="condition.polymer_info" :xs="24" :sm="12" :md="6">
              <DerivedField label="塑料牌号" :value="condition.polymer_info.grade" />
            </el-col>
            <el-col v-if="condition.polymer_info?.manufacturer" :xs="24" :sm="12" :md="6">
              <DerivedField label="生产厂家" :value="condition.polymer_info.manufacturer" />
            </el-col>
            <el-col v-if="condition.polymer_info?.recommend_melt_temperature" :xs="24" :sm="12" :md="6">
              <DerivedField
                label="推荐熔体温度"
                :value="condition.polymer_info.recommend_melt_temperature"
                unit="℃"
              />
            </el-col>
          </el-row>
          </div>
        </el-form>
      </div>
    </transition>
  </el-card>
</template>

<script setup lang="ts">
/**
 * 工艺条件卡组件（可折叠）
 *
 * 校验：父组件通过 ref 调 checkFormDataValid() 触发 el-form 的 validate
 * 选择：autocomplete 远程拉取，主数据选择后回填 *_info（to_dict 缓存）
 * 折叠：mode='view' 强制折叠，其他 mode 受 defaultExpanded 控制
 *
 * 索引说明（2026-09-11 重构）：
 * - 后端 shot_index / injection_index 是 0 索引（0 表示第 1 射/射台）
 * - UI 显示 1 索引（用户友好），内部自动转换
 *   - 显示层：射次 1 = 后端 0，射次 2 = 后端 1
 *   - 提交时：UI 字符串 → Number() 转数字 → 存 0 索引
 */
import { ref, reactive, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { moldList, injectionMachineList, polymerList, moldDetail } from '@/api'
import type { FormInstance, FormRules } from 'element-plus'
import DerivedField from './DerivedField.vue'
import { useConditionDerived } from './composables/useConditionDerived'

// ============================================================================
// 状态枚举映射（与后端 STATUS_CHOICES 保持一致，禁止臆造）
// ============================================================================

const STATUS_MAP: Record<string, string> = {
  active: '使用中',
  archived: '已归档',
}

const STATUS_TAG_TYPE: Record<string, 'success' | 'info' | 'warning'> = {
  active: 'success',
  archived: 'info',
}

/**
 * 型腔布局 tooltip（领域知识）
 * 1: 单色模具, 单腔, 共1个制品
 * 1+1: 单色模具, 两腔, 共2个制品, 制品参数不同
 * 1*2: 单色模具, 两腔, 共2个制品, 制品参数相同
 * 1&1: 双色模具, 1射单腔, 成型1个制品, 2射单腔, 成型1个制品
 * 1&1+1: 双色模具, 1射单腔, 成型1个制品, 2射双腔, 成型2个制品, 制品参数不同
 */
const CAVITY_LAYOUT_TOOLTIP = [
  '1: 单色模具, 单腔, 共1个制品',
  '1+1: 单色模具, 两腔, 共2个制品, 制品参数不同',
  '1*2: 单色模具, 两腔, 共2个制品, 制品参数相同',
  '1&1: 双色模具, 1射单腔, 成型1个制品, 2射单腔, 成型1个制品',
  '1&1+1: 双色模具, 1射单腔, 成型1个制品, 2射双腔, 成型2个制品, 制品参数不同',
].join('\n')

// ============================================================================
// 类型定义（export 以支持 Options API 引用，解决 declaration emit 私有类型错误）
// ============================================================================

/**
 * 浇口特征（对应后端 Gate 模型）
 * - 与 preconditionForm gate_* 字段对齐
 * - 字段语义: 圆形/矩形 不同字段；通过 gate_shape 区分渲染
 */
export interface GateSummary {
  id?: number
  /** 浇口形状：圆形 / 矩形 / 梯形 / 环形 */
  gate_shape?: string
  /** 浇口类型：针阀式 / 直浇口 / 点浇口 / ... */
  gate_type?: string
  /** 浇口数量 */
  gate_count?: number | null
  /** 浇口位置描述 */
  location_description?: string
  // 矩形类尺寸
  length?: number | null
  width?: number | null
  // 圆形类尺寸
  diameter?: number | null
  // 梯形类尺寸
  top_length?: number | null
  bottom_length?: number | null
  height?: number | null
  // 环形类尺寸
  outer_diameter?: number | null
  inner_diameter?: number | null
  gap?: number | null
}

/**
 * 型腔摘要（对应后端 Cavity 模型）
 * - 每个 cavity 对应"一类制品",product 字段描述制品信息
 * - gates 是反向关联的浇口列表（1:N）
 */
export interface CavitySummary {
  id?: number
  cavity_count_per_shot?: number | null
  // 制品信息
  product_name?: string
  product_code?: string
  // 制品关键工艺参数
  max_flow_length?: number | null
  ave_wall_thickness?: number | null
  min_wall_thickness?: number | null
  max_wall_thickness?: number | null
  projected_area_per_cavity?: number | null
  estimated_weight_per_cavity?: number | null
  // 可计算特征
  flow_ratio?: number | null
  thickness_variation?: number | null
  // 浇口(1:N,通过反向关联获取)
  gates?: Array<GateSummary>
}

/**
 * 浇注系统摘要（对应后端 GatingSystem 模型）
 * - 每个 GatingSystem 对应一次注射(shot_index)
 * - 包含 cavities（1:N）→ 制品 + 浇口
 */
export interface GatingSystemSummary {
  id?: number
  runner_type?: string
  estimated_shot_weight?: number | null
  estimated_runner_weight?: number | null
  runner_weight?: number | null
  runner_length?: number | null
  projected_area?: number | null
  total_product_weight?: number | null
  // 热流道细节（仅热流道/热转冷时使用）
  hot_runner_supplier?: string
  hot_runner_system_type?: string
  hot_runner_manifold_zones?: number | null
  hot_runner_nozzle_count?: number | null
  has_sequencing_control?: boolean | null
  valve_actuation_type?: string
  // 型腔列表
  cavities?: Array<CavitySummary>
}

/**
 * 注塑机射台摘要（对应后端 InjectionUnit 模型）
 * - 每个 InjectionUnit 对应一个射台(injection_index)
 * - 新增 unit_code 字段（对应 preconditionForm machine_serial_no）
 */
export interface InjectionUnitSummary {
  /** 射台编号 */
  unit_code?: string
  pressure_unit?: string
  nozzle_type?: string
  screw_type?: string
  screw_diameter?: number | null
  max_injection_stroke?: number | null
  max_injection_volume?: number | null
  max_injection_weight?: number | null
}

export interface MoldInfo {
  id: number
  mold_no: string
  mold_name?: string
  product_category?: string
  product_subcategory?: string
  cavity_layout?: string
  shot_count?: number
  gating_systems?: Array<GatingSystemSummary>
  [key: string]: any
}

export interface MachineInfo {
  id: number
  model: string
  brand?: string
  device_no?: string
  location?: string
  unit_count?: number
  max_clamping_force?: number | null
  injection_units?: Array<InjectionUnitSummary>
  [key: string]: any
}

export interface PolymerInfo {
  id: number
  abbreviation: string
  grade?: string
  manufacturer?: string
  /** 推荐熔体温度（℃），对齐 preconditionForm recommend_melt_temperature */
  recommend_melt_temperature?: number | null
  [key: string]: any
}

export interface Condition {
  id?: number | null
  condition_no?: string | null
  status?: string | null
  origin_type?: string | null
  mold_id?: number | null
  shot_index?: number | null
  /** 制品索引(0 索引,多 cavity 时用于切换显示哪个制品)
   * 注意:ProcessCondition 已不再使用此字段（所有 cavity 平铺展示）,
   *       此处保留仅为兼容后端 schema / 旧数据 */
  product_index?: number | null
  injection_machine_id?: number | null
  injection_index?: number | null
  polymer_id?: number | null
  process_context?: Record<string, any>
  mold_info?: MoldInfo | null
  machine_info?: MachineInfo | null
  polymer_info?: PolymerInfo | null
  [key: string]: any
}

// ============================================================================
// Props
// ============================================================================

const props = withDefaults(
  defineProps<{
    processCondition: Condition
    /** 模式：new/edit/transplant 可编辑，view 强制折叠（只读） */
    mode?: 'new' | 'edit' | 'view' | 'transplant'
    /** 默认展开状态（仅在非 view 模式生效） */
    defaultExpanded?: boolean
    /** 禁用所有输入（与 mode='view' 区别：保留折叠切换能力） */
    disabled?: boolean
  }>(),
  {
    mode: 'edit',
    defaultExpanded: true,
    disabled: false,
  },
)

const formRef = ref<FormInstance>()

// ============================================================================
// 折叠状态
// ============================================================================

/** 只读模式：mode='view' 或 disabled=true 时强制折叠 */
const isReadOnly = computed(() => props.mode === 'view' || props.disabled)

/** 是否展开（受 mode / defaultExpanded 控制） */
const expanded = ref<boolean>(
  isReadOnly.value ? false : props.defaultExpanded,
)

/** 切换展开/折叠（非只读时生效） */
function toggle() {
  if (isReadOnly.value) return
  expanded.value = !expanded.value
}

// ============================================================================
// 响应式状态
// ============================================================================

const condition = reactive<Condition>(props.processCondition ?? {})

// 三个 autocomplete 的输入文本
const moldQuery = ref<string>(condition.mold_info?.mold_no ?? '')
const machineQuery = ref<string>(condition.machine_info?.model ?? '')
const polymerQuery = ref<string>(condition.polymer_info?.abbreviation ?? '')

/**
 * 射次 / 射台 / 制品 字符串中间值（v-number 指令 + el-input 内部用 string）
 * - 显示层：用 1 索引（更友好）
 * - watch 自动同步到 condition.shot_index（0 索引）
 */
const shotIndexStr = ref<string>(
  condition.shot_index != null ? String(condition.shot_index + 1) : '',
)
const injectionIndexStr = ref<string>(
  condition.injection_index != null ? String(condition.injection_index + 1) : '',
)

// ============================================================================
// 派生计算（从 composable 复用）
// ============================================================================
//
// useConditionDerived 负责：
//   - 索引（shot / injection / product，0 索引）
//   - 计数（shot_count / unit_count / cavity_count）
//   - 多射/多腔判断
//   - 实体存在性（hasMold / hasMachine / hasPolymer）
//   - 派生对象（gatingDerived / currentCavity / currentGate / injectionUnitDerived）
//   - 1 索引显示
//
// 模板仍可直接使用这些 computed 名（按原本名字引入），保持与原代码一致。

const {
  shotIndex,
  injectionIndex,
  shotCount,
  unitCount,
  hasMultipleShots,
  hasMultipleUnits,
  hasMold,
  hasMachine,
  hasPolymer,
  gatingDerived,
  cavities,
  injectionUnitDerived,
  shotIndexDisplay,
  injectionIndexDisplay,
} = useConditionDerived(condition)

// 派生字段格式化由 DerivedField 组件统一处理（unit / numberFormat / null 占位）
// 旧 formatWeight / formatStroke / formatDiameter / formatClampingForce 已移除

// ============================================================================
// 折叠态简要信息（已由 composable 提供 hasMold / hasMachine / hasPolymer /
// shotIndexDisplay / injectionIndexDisplay / productIndexDisplay）

// ============================================================================
// 校验规则
// ============================================================================

const rules: FormRules = {
  mold_id: [{ required: true, message: '请选择模具', trigger: 'change' }],
  shot_index: [{ required: true, message: '请选择工艺射次', trigger: 'change' }],
  injection_machine_id: [{ required: true, message: '请选择注塑机', trigger: 'change' }],
  injection_index: [{ required: true, message: '请选择射台', trigger: 'change' }],
  polymer_id: [{ required: true, message: '请选择塑料', trigger: 'change' }],
}

// ============================================================================
// 父组件钩子
// ============================================================================

defineExpose({
  /**
   * 触发 el-form 校验。
   * 校验通过：返回 true，父组件继续保存
   * 校验失败：返回 false，父组件应提示用户
   */
  async checkFormDataValid(): Promise<boolean> {
    if (!formRef.value) return false
    // 折叠态时强制展开（让用户能看到/修改不通过校验的字段）
    if (!expanded.value) {
      expanded.value = true
    }
    try {
      await formRef.value.validate()
    } catch {
      ElMessage.error('工艺条件填写不完整，请检查')
      return false
    }
    // 同步射次 / 射台字符串 → 数字（0 索引）
    syncIndexStringsToCondition()
    return true
  },
  /** 切换展开/折叠（供父组件主动控制） */
  toggle,
  /** 强制展开（供父组件主动控制） */
  expand: () => {
    if (!isReadOnly.value) expanded.value = true
  },
  /** 强制折叠（供父组件主动控制） */
  collapse: () => {
    expanded.value = false
  },
})

/**
 * 把 UI 显示的射次/射台/制品字符串（1 索引）转为后端字段（0 索引）
 * - 空字符串 → null（未填写）
 * - 数字字符串 → Number() - 1（1 索引转 0 索引）
 */
function syncIndexStringsToCondition() {
  const shotNum = Number(shotIndexStr.value)
  condition.shot_index =
    shotIndexStr.value === '' || isNaN(shotNum) ? null : Math.max(0, shotNum - 1)

  const injNum = Number(injectionIndexStr.value)
  condition.injection_index =
    injectionIndexStr.value === '' || isNaN(injNum) ? null : Math.max(0, injNum - 1)
}

// ============================================================================
// 监听：prop 变化时同步内部状态（编辑模式初始化 / 外部切换 condition）
// ============================================================================

watch(
  () => props.processCondition,
  (val) => {
    Object.assign(condition, val ?? {})
    moldQuery.value = val?.mold_info?.mold_no ?? ''
    machineQuery.value = val?.machine_info?.model ?? ''
    polymerQuery.value = val?.polymer_info?.abbreviation ?? ''
    shotIndexStr.value = val?.shot_index != null ? String(val.shot_index + 1) : ''
    injectionIndexStr.value =
      val?.injection_index != null ? String(val.injection_index + 1) : ''
  },
  { deep: true, immediate: true },
)

// ============================================================================
// 主数据远程拉取（autocomplete suggestions）
// ============================================================================

async function fetchMoldSuggestions(queryString: string, cb: (results: any[]) => void) {
  try {
    const res: any = await moldList({
      page_no: 1,
      page_size: 30,
      mold_no: queryString || undefined,
    })
    if (res?.status === 0) {
      const items = (res.data?.items ?? []).map((it: any) => ({
        value: it.mold_no,
        item: it,
      }))
      cb(items)
    } else {
      cb([])
    }
  } catch {
    cb([])
  }
}

async function fetchMachineSuggestions(queryString: string, cb: (results: any[]) => void) {
  try {
    const res: any = await injectionMachineList({
      page_no: 1,
      page_size: 30,
      model: queryString || undefined,
    })
    if (res?.status === 0) {
      const items = (res.data?.items ?? []).map((it: any) => ({
        value: it.model,
        item: it,
      }))
      cb(items)
    } else {
      cb([])
    }
  } catch {
    cb([])
  }
}

async function fetchPolymerSuggestions(queryString: string, cb: (results: any[]) => void) {
  try {
    const res: any = await polymerList({
      page_no: 1,
      page_size: 30,
      abbreviation: queryString || undefined,
    })
    if (res?.status === 0) {
      const items = (res.data?.items ?? []).map((it: any) => ({
        value: it.abbreviation,
        item: it,
      }))
      cb(items)
    } else {
      cb([])
    }
  } catch {
    cb([])
  }
}

// ============================================================================
// 选择回调
// ============================================================================

async function onMoldSelect(item: any) {
  const mold = item?.item ?? null
  if (!mold) return
  condition.mold_id = mold.id
  // 列表 API(to_dict() 不带 include_rvs=True)不返回反向关联
  // 必须调详情 API 获取完整的 gating_systems / cavities / gates
  try {
    const detail: any = await moldDetail(mold.id)
    if (detail?.status === 0 && detail.data) {
      condition.mold_info = detail.data
    } else {
      // 详情失败,退回到列表项(基本信息可显示,浇注系统不会显示)
      condition.mold_info = mold
    }
  } catch {
    condition.mold_info = mold
  }
}

function onMoldClear() {
  condition.mold_id = null
  condition.mold_info = null
}

function onMachineSelect(item: any) {
  const m = item?.item ?? null
  if (!m) return
  condition.injection_machine_id = m.id
  condition.machine_info = m
}

function onMachineClear() {
  condition.injection_machine_id = null
  condition.machine_info = null
}

function onPolymerSelect(item: any) {
  const p = item?.item ?? null
  if (!p) return
  condition.polymer_id = p.id
  condition.polymer_info = p
}

function onPolymerClear() {
  condition.polymer_id = null
  condition.polymer_info = null
}
</script>

<style lang="scss" scoped>
/*
 * 自定义类 .process-condition-card-*：本组件特有的折叠 / 简要信息样式
 *
 * 全局类（不定义）：
 * - .custom-form / .custom-form__section / .custom-form__title / .custom-form__divider
 *   均来自全局 styles/utilities/custom-form.scss
 *
 * 本组件私有：.summary-item*（折叠态简要信息使用）
 */
.process-condition-card {
  &__header {
    display: flex;
    align-items: center;
    gap: 12px;
    min-height: 32px;
    padding: 4px 0;

    &.is-clickable {
      cursor: pointer;
      user-select: none;

      &:hover .process-condition-card__toggle-icon {
        color: var(--el-color-primary);
      }
    }
  }

  &__header-left {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
  }

  &__toggle-icon {
    width: 18px;
    height: 18px;
    flex-shrink: 0;
    color: #606266;
    vertical-align: middle;
    transition: transform 0.3s ease, color 0.2s ease;
  }

  &__summary {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
    flex: 1;
    min-width: 0;
    margin-left: 8px;
    font-size: 13px;
    color: #303133;
  }

  &__header-right {
    flex-shrink: 0;
    margin-left: auto;
  }

  &__body {
    /* 正常 padding 由 .custom-form 提供 */
  }
}

/* 折叠态简要信息项（本组件私有） */
.summary-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  line-height: 1;

  &__icon {
    // AppIcon (Iconify Icon) 渲染为 <svg>，用 width/height 控制大小（font-size 对 svg 无效）
    width: 14px;
    height: 14px;
    flex-shrink: 0;
    color: #909399;
    vertical-align: middle;
  }

  &__label {
    color: #909399;
  }

  &__value {
    color: #303133;
    font-weight: 500;
  }

  &__sep {
    margin: 0 4px;
    color: #c0c4cc;
  }
}

/* 折叠态下的内容过渡（max-height + opacity） */
.process-condition-collapse-enter-active,
.process-condition-collapse-leave-active {
  transition: opacity 0.25s ease, max-height 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.process-condition-collapse-enter-from,
.process-condition-collapse-leave-to {
  opacity: 0;
  max-height: 0;
}

.process-condition-collapse-enter-to,
.process-condition-collapse-leave-from {
  opacity: 1;
  max-height: 2400px;
}

/* 折叠态微调 */
.is-collapsed :deep(.el-card__body) {
  padding-top: 0;
  padding-bottom: 0;
}

/*
* 主 area 之间的间距（首个 area 不需要上方间距）
* - 主 area 不再使用背景/边框容器
* - 标题用全局 .custom-form__title（3px 主题色左竖条 + 16px/700）
* - 主 area 内部区块（如浇注系统/制品信息/浇口/射台信息）用 .subsection-block 块状容器
*/
.area-section + .area-section {
  margin-top: 24px;
}

/*
* 子 subsection 容器（block-area 浅色背景块）
* - 主 area 内部进一步分组的视觉容器
* - 白底 + 边框 + 圆角，与主 area 平铺背景形成层次
* - 嵌套变体（--nested / --deep-nested）用于父子层级场景：
*   · L3 subsection-block：模具信息/浇注系统/射台信息等一级子区块
*   · L4 subsection-block--nested：制品信息（嵌套于浇注系统内）
*   · L5 subsection-block--deep-nested：浇口（嵌套于制品信息内）
*/
.subsection-block {
  border: 1px solid var(--color-border-light, #e4e7ed);
  border-radius: 6px;
  padding: 16px;
  background-color: #ffffff;

  &__header {
    display: flex;
    align-items: center;
    margin-bottom: 12px;
  }

  &__title {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 14px;
    font-weight: 600;
    color: var(--el-text-color-primary, #303133);
  }

  &__shot {
    font-size: 12px;
    font-weight: 400;
    color: var(--el-text-color-regular, #606266);
    margin-left: 4px;
  }

  &__content {
    background-color: transparent;
  }

  &__divider {
    margin: 14px 0;
    background-color: var(--color-border-extra-light, #ebeef5);
  }

  /*
  * L4 嵌套变体：左缩进 + 左边线，区别于 L3 的边框容器
  * - 用于“制品信息”嵌套于“浇注系统”内（制品是浇注系统下的子选择）
  * - 无背景 / 无边框 / 只保留左侧 3px 主题色竖条
  * - 视觉上看起来像 “在父容器内的内嵌区域”，与 L3 的“独立卡片”形成层次
  */
  &--nested {
    margin-top: 16px;
    margin-left: 16px;
    padding: 12px 16px;
    background-color: transparent;
    border: none;
    border-left: 3px solid var(--el-color-primary-light-5, #c0d8f0);
    border-radius: 0;

    .subsection-block__header {
      margin-bottom: 8px;
    }

    .subsection-block__title {
      font-size: 13px;
      font-weight: 600;
    }
  }

  /*
  * L5 深嵌套变体：更深缩进 + 更细左边线
  * - 用于“浇口”嵌套于“制品信息”内（浇口是制品下的子详情）
  * - 进一步缩进 + 左边线变细，表达“再下一级”关系
  */
  &--deep-nested {
    margin-top: 12px;
    margin-left: 32px;
    padding: 10px 16px;
    border-left: 2px solid var(--el-color-primary-light-7, #d8e8f8);
  }
}
</style>
