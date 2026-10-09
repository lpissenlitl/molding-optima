<!--
  ProcessParameterForm - 工艺参数表单（new / edit / detail 三模式共用）

  数据模型：操作 Condition（试模上下文）+ Parameter（工艺参数）两块数据
  样式约束：本文件无任何自定义 SCSS（条件卡折叠样式在 shared/ProcessCondition.vue）
-->
<template>
  <div class="process-condition-form">
    <!-- 顶部 page-header（全局类） -->
    <div class="page-header">
      <el-button text @click="goBack">
        <AppIcon icon="mdi:arrow-left" style="margin-right: 4px; font-size: 14px;" />
        返回列表
      </el-button>
    </div>

    <div v-if="!loaded" v-loading="true" class="loading-placeholder" />

    <template v-else>
      <!-- 工艺条件卡（可折叠：展开=表单 / 折叠=简要信息） -->
      <ProcessCondition
        ref="conditionRef"
        :process-condition="form.condition"
        :mode="mode === 'detail' ? 'view' : mode"
        :default-expanded="true"
      />

      <!-- 工艺参数卡（始终展开） -->
      <SettingProcess
        v-if="form.parameter.setting_process"
        ref="parameterRef"
        :setting-process="form.parameter.setting_process"
        :machine-info="form.condition.machine_info ?? {}"
        :disabled="mode === 'detail'"
      />
    </template>

    <!-- 底部操作（全局 .form-actions） -->
    <div v-if="mode !== 'detail' && loaded" class="form-actions">
      <el-button @click="goBack">取消</el-button>
      <el-button v-if="mode === 'new'" @click="resetForm">重置</el-button>
      <el-button v-else-if="mode === 'edit'" @click="resetForm">
        撤销修改
      </el-button>
      <el-button
        type="primary"
        :loading="save_loading"
        @click="onSubmit"
      >
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
import {
  getProcessParameterFrontend,
  saveProcessParameterFrontend,
  updateProcessParameterFrontend,
} from '@/api'

// ============================================================================
// 路由
// ============================================================================

const route = useRoute()
const router = useRouter()

/** mode 派生（由 route 决定） */
const mode = computed<'new' | 'edit' | 'detail'>(() => {
  if (route.name === 'process-parameter-detail') return 'detail'
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

let formSnapshot: any = null

// ============================================================================
// 数据加载
// ============================================================================

async function loadForm() {
  loaded.value = false
  try {
    if (mode.value === 'new') {
      Object.assign(form, structuredClone(injectionProcessForm))
      formSnapshot = null
    } else {
      const id = Number(route.params.id)
      if (!id) {
        ElMessage.error('无效的工艺 ID')
        goBack()
        return
      }
      const res: any = await getProcessParameterFrontend(id)
      if (res?.status === 0 && res.data) {
        const { condition, parameter } = res.data
        // condition 字段深合并（保留 form 初始字段）
        form.condition = { ...form.condition, ...(condition ?? {}) }
        form.parameter = {
          ...form.parameter,
          ...(parameter ?? {}),
          setting_process: parameter?.setting_process ?? structuredClone(settingProcessForm),
        }
        if (mode.value === 'edit') {
          formSnapshot = JSON.parse(JSON.stringify(form))
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
  } else if (mode.value === 'edit' && formSnapshot) {
    Object.assign(form, JSON.parse(JSON.stringify(formSnapshot)))
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
      const res: any = await saveProcessParameterFrontend(payload)
      if (res?.status === 0) {
        ElMessage.success('工艺保存成功')
        const newId = res.data?.id ?? form.condition.id
        if (newId) {
          router.replace(`/process/parameter/${newId}/edit`)
        } else {
          goBack()
        }
      } else {
        ElMessage.error(res?.msg || '保存失败')
      }
    } else if (mode.value === 'edit') {
      const id = Number(route.params.id)
      const res: any = await updateProcessParameterFrontend(id, payload)
      if (res?.status === 0) {
        ElMessage.success('工艺更新成功')
        // 重新拉取以刷新快照
        await loadForm()
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
function buildPayload() {
  return {
    condition: {
      status: form.condition.status || 'active',
      origin_type: form.condition.origin_type || 'manual_creation',
      mold_id: form.condition.mold_id,
      shot_index: Number(form.condition.shot_index ?? 0),
      injection_machine_id: form.condition.injection_machine_id,
      injection_index: Number(form.condition.injection_index ?? 0),
      polymer_id: form.condition.polymer_id,
      process_context: form.condition.process_context ?? {},
    },
    parameter: {
      setting_process: form.parameter.setting_process,
    },
  }
}

// ============================================================================
// 导航
// ============================================================================

function goBack() {
  router.push('/process/parameter')
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
</style>
