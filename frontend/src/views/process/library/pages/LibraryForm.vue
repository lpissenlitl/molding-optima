<!--
  ProcessParameterForm - 工艺参数表单（new / edit / detail 三模式共用）

  数据模型：操作 Condition（试模上下文）+ Parameter（工艺参数）两块数据
-->
<template>
  <div class="process-condition-form">
    <div v-if="!loaded" v-loading="true" class="loading-placeholder" />

    <template v-else>
      <!-- 工艺条件卡：编辑/详情模式默认折叠 -->
      <ProcessCondition
        ref="conditionRef"
        :process-condition="form.condition"
        :mode="mode === 'detail' ? 'view' : mode"
        :default-expanded="mode === 'new'"
      />

      <!-- 工艺参数卡：视觉对齐 OptimizationCreate 的“工作台”风格 -->
      <el-card
        v-if="form.parameter.setting_process"
        class="parameter-card"
        shadow="never"
        style="margin-top: 16px"
      >
        <template #header>
          <div class="parameter-card__header">
            <AppIcon icon="mdi:cog-outline" class="parameter-card__header-icon" />
            <span class="custom-form__title">工艺参数</span>
          </div>
        </template>
        <SettingProcess
          ref="parameterRef"
          :setting-process="form.parameter.setting_process"
          :machine-info="form.condition.machine_info ?? {}"
          :disabled="mode === 'detail'"
        />
      </el-card>
    </template>

    <!-- 底部操作（全局 .form-actions） -->
    <div v-if="mode !== 'detail' && loaded" class="form-actions">
      <el-button @click="goBack">
        <AppIcon icon="mdi:close" style="margin-right: 4px; font-size: 14px;" />
        取消
      </el-button>
      <el-button v-if="mode === 'new'" @click="resetForm">
        <AppIcon icon="mdi:refresh" style="margin-right: 4px; font-size: 14px;" />
        重置
      </el-button>
      <el-button
        type="primary"
        :loading="save_loading"
        @click="onSubmit"
      >
        <AppIcon icon="mdi:content-save-outline" style="margin-right: 4px; font-size: 14px;" />
        {{ mode === 'new' ? '保存' : '更新' }}
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
// 工艺条件和工艺参数解耦：独立校验、独立 ref
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import ProcessCondition from '@/views/process/shared/ProcessCondition.vue'
import SettingProcess from '../components/SettingProcess.vue'
import { injectionProcessForm, settingProcessForm } from '@/constants/process-const'
import { processRecordMethod } from '@/api'

// ============================================================================
// 路由
// ============================================================================

const route = useRoute()
const router = useRouter()

/** mode 派生（由 route 决定） */
const mode = computed<'new' | 'edit' | 'detail'>(() => {
  if (route.name === 'process-library-detail') return 'detail'
  if (route.params?.id) return 'edit'
  return 'new'
})

// ============================================================================
// 状态
// ============================================================================

const form = reactive<{
  condition: any
  parameter: any
}>(structuredClone(injectionProcessForm))

const loaded = ref(false)
const save_loading = ref(false)

const conditionRef = ref<InstanceType<typeof ProcessCondition> | null>(null)
const parameterRef = ref<InstanceType<typeof SettingProcess> | null>(null)

// ============================================================================
// 数据加载
// ============================================================================

async function loadForm() {
  loaded.value = false
  try {
    if (mode.value === 'new') {
      Object.assign(form, structuredClone(injectionProcessForm))
    } else {
      const id = Number(route.params.id)
      if (!id) {
        ElMessage.error('无效的工艺 ID')
        goBack()
        return
      }
      const res: any = await processRecordMethod.getDetail(id)
      if (res?.status === 0 && res.data) {
        const { condition, parameter } = res.data
        // condition 字段深合并（保留 form 初始字段）
        // *_info.id 是 id 的唯一来源（嵌套结构，校验规则走 prop="*_info.id"）
        form.condition = { ...form.condition, ...(condition ?? {}) }
        form.parameter = {
          ...form.parameter,
          ...(parameter ?? {}),
          setting_process: parameter?.setting_process ?? structuredClone(settingProcessForm),
        }
      } else {
        ElMessage.error(res?.msg || '加载失败')
        goBack()
        return
      }
    }
  } catch {
    // 拦截器已统一 toast + console
    goBack()
    return
  } finally {
    loaded.value = true
  }
}

function resetForm() {
  if (mode.value === 'new') {
    Object.assign(form, structuredClone(injectionProcessForm))
  }
}

// ============================================================================
// 提交
// ============================================================================

async function onSubmit() {
  // 校验工艺条件 5 项必填外键：模具 / 工艺射次 / 注塑机 / 射台 / 材料
  // 这 5 项选中即可，不用填完各基础表的所有字段——各基础表的字段由基础模块自己负责
  const condValid = await conditionRef.value?.checkFormDataValid()
  if (!condValid) {
    return
  }

  // 2. 构造后端 payload
  const payload = buildPayload()

  save_loading.value = true
  try {
    if (mode.value === 'new') {
      const res: any = await processRecordMethod.add(payload)
      if (res?.status === 0) {
        ElMessage.success('工艺保存成功')
        // 跳转到列表：list 看到刚刚创建的记录
        goBack()
      } else {
        ElMessage.error(res?.msg || '保存失败')
      }
    } else if (mode.value === 'edit') {
      const id = Number(route.params.id)
      const res: any = await processRecordMethod.edit(payload, id)
      if (res?.status === 0) {
        ElMessage.success('工艺更新成功')
        // 跳转到列表：list 看到刚刚更新的记录
        goBack()
      } else {
        ElMessage.error(res?.msg || '更新失败')
      }
    }
  } catch {
    // 拦截器已统一 toast + console
  } finally {
    save_loading.value = false
  }
}

// 仅回传后端可识别的字段；condition.*_info 是前端缓存，不需要回传
// - status / process_context / mold_id / shot_index / injection_machine_id / injection_index / polymer_id / origin_type
//   这些字段后端都能识别，前端发整个 condition 对象方便
// - process_context 由后端管理（前端 form 无此字段，不主动构造空 dict）
// - 业务身份锁字段（mold_id/machine_id/polymer_id/shot_index/injection_index/origin_type）
//   发到后端后由 service.update_condition 静默忽略（业务身份不变）
// - 后端 DTO 要求顶层 *_id（不接 *_info 嵌套），从 *_info.id 推导平铺
function buildPayload() {
  return {
    condition: {
      status: form.condition.status || 'active',
      origin_type: form.condition.origin_type || 'manual_creation',
      mold_id: form.condition.mold_info?.id ?? null,
      shot_index: Number(form.condition.shot_index ?? 0),
      injection_machine_id: form.condition.machine_info?.id ?? null,
      injection_index: Number(form.condition.injection_index ?? 0),
      polymer_id: form.condition.polymer_info?.id ?? null,
    },
    // 后端 service 调 _frontend_to_condition_dict 转平铺 130+ 字段
    parameter: {
      setting_process: form.parameter.setting_process,
    },
  }
}

// ============================================================================
// 导航
// ============================================================================

function goBack() {
  router.push('/process/library')
}

// ============================================================================
// 生命周期
// ============================================================================

onMounted(() => {
  loadForm()
})
</script>

<style lang="scss" scoped>
// 容器遵守全局表单规范（padding 由 .process-condition-form 决定）
// 不要在本文件加 display: flex / gap / 自定义背景色
.process-condition-form {
  padding: 16px 16px 96px;
  box-sizing: border-box;
}

// 工艺参数卡 header：视觉对齐 OptimizationCreate
.parameter-card__header {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 32px;
  padding: 4px 0;

  &-icon {
    width: 18px;
    height: 18px;
    flex-shrink: 0;
    color: #606266;
  }
}
</style>
