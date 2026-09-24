<!--
  ProcessParameterForm - 工艺参数表单（new / edit / detail 三模式共用）

  路由：
    - /process/parameter/new              新建
    - /process/parameter/:id/edit         编辑
    - /process/parameter/:id/detail       详情（只读）

  业务说明：
    - ProcessCondition 是"试模上下文"的通用载体（见 shared/ProcessCondition.vue）
    - 本页是"工艺参数"业务视图，操作的是 Condition + Parameter 两块数据

  架构（2026-09-11 重构 v2）：
    - 顶部 page-header（返回列表）
    - ProcessCondition（可折叠卡）：默认展开（new/edit）或强制折叠（detail）
      - 展开：显示完整条件表单
      - 折叠：显示简要信息（条件号 + 状态 + 模具/机器/材料）
    - SettingProcess（始终展开）：工艺参数主体
    - 底部 form-actions：取消 / 保存（new）/ 撤销修改（edit）/ 更新

  模式行为：
    - new    → ProcessCondition 默认展开（用户填条件）
    - edit   → ProcessCondition 默认展开（用户可能改条件）
    - detail → ProcessCondition 强制折叠（只读）

  数据流：
    - 加载：根据 mode 调用 getProcessParameterFrontend(id) 或 初始化空 form
    - 提交（new）：saveProcessParameterFrontend → 成功后保存返回的 id → 切到 edit
    - 提交（edit）：updateProcessParameterFrontend(id, payload) → 提示成功

  样式规范：
    - 容器遵守全局表单规范（padding 16 16 96 / max-width 1400）
    - 复用全局 .form-actions / .page-header / .custom-form
    - 本文件无任何自定义 SCSS（工艺条件卡的折叠 / 简要信息样式在 shared/ProcessCondition.vue 内）
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
/**
 * 工艺参数表单（Vue 3 Composition API 版）
 *
 * 关键设计：
 * 1. 三模式（new / edit / detail）由 route 切换
 * 2. 工艺条件卡自带折叠能力（shared/ProcessCondition 内部实现）
 * 3. 工艺条件和工艺参数解耦：独立校验、独立 ref
 * 4. 提交时构造后端需要的 payload
 * 5. 详情模式：禁用底部操作条 + ProcessCondition 强制折叠
 */
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

/** 用于"撤销修改"——保存编辑前的快照 */
let formSnapshot: any = null

// ============================================================================
// 数据加载
// ============================================================================

async function loadForm() {
  loaded.value = false
  try {
    if (mode.value === 'new') {
      // 新建：重置为空表单
      Object.assign(form, structuredClone(injectionProcessForm))
      formSnapshot = null
    } else {
      // 编辑 / 详情：拉取后端数据
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
        // 编辑模式快照用于"撤销修改"
        if (mode.value === 'edit') {
          formSnapshot = JSON.parse(JSON.stringify(form))
        }
      } else {
        ElMessage.error(res?.msg || '加载失败')
        goBack()
        return
      }
    }
  } catch (err) {
    console.error('[ProcessParameterForm] loadForm failed:', err)
    ElMessage.error('加载失败')
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
    // 撤销到原始快照
    Object.assign(form, JSON.parse(JSON.stringify(formSnapshot)))
  }
}

// ============================================================================
// 提交
// ============================================================================

async function onSubmit() {
  // 1. 校验工艺条件（必填 5 项：模具 / 工艺射次 / 注塑机 / 射台 / 材料）
  //    业务说明（2026-09-17 澄清）：
  //    - 这 5 项是「工艺记录」的外键（指向模具 / 注塑机 / 材料等基础表）
  //    - 不填则工艺记录无意义（不知道用什么模具 / 机器 / 材料打的）
  //    - 但这 5 项指向的基础表（模具 / 注塑机 / 材料）内部的字段完整性不管
  //      · 例如模具表里的型腔数 / 浇口类型 / 产品类别等字段，由模具模块自己负责
  //      · 工艺录入只需要「选中」哪个模具，不用填完模具表所有字段
  //    - ProcessCondition.checkFormDataValid() 内部会自动展开折叠态，让用户修改
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
  } catch (err) {
    console.error('[ProcessParameterForm] onSubmit failed:', err)
    ElMessage.error('保存失败')
  } finally {
    save_loading.value = false
  }
}

/**
 * 构造后端需要的 payload
 *
 * 后端 (main_service.create_process_parameter_frontend / update_process_parameter_frontend)：
 *   condition_kwargs = kwargs.get("condition")
 *   setting_process = kwargs.get("parameter", {}).get("setting_process")
 *
 * 注：condition 只需要后端可识别的字段（id、mold_id、shot_index、
 *     injection_machine_id、injection_index、polymer_id、process_context），
 *     *_info 是给前端用的缓存，不需要回传。
 */
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
/*
 * 容器遵守全局表单规范（padding 16 16 96）
 * 不要自定义背景色 / display: flex / gap
 * 复用全局 .form-actions / .page-header
 *
 * 工艺条件卡的折叠 / 简要信息样式在 shared/ProcessCondition.vue 内部
 */
.process-condition-form {
  padding: 16px 16px 96px;
  box-sizing: border-box;
}

.loading-placeholder {
  height: 400px;
}
</style>
