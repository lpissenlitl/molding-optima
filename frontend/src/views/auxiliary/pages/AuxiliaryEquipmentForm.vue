<!--
  AuxiliaryEquipmentForm - 辅助装置表单（new / edit / copy 三模式共用）

  路由：
    - /equipment/auxiliary/new         新建
    - /equipment/auxiliary/:id/edit    编辑
    - /equipment/auxiliary/:id/copy    复制（清空 id）

  架构（对齐 InjectionMachineForm）：
    - 顶部 page-header（仅返回按钮）
    - 1 个 section：辅助装置信息（el-card）
    - el-row + el-col + gutter:24 两列布局（与项目内表单一致）
    - 底部 form-actions（全局统一样式：fixed bottom）
    - 所有 .custom-form / .custom-form__section / .custom-form__title / .form-actions
      均复用全局样式（src/styles/utilities/custom-form.scss）
-->
<template>
  <div class="auxiliary-form">
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
      :model="auxiliary"
      :rules="rules"
      class="custom-form"
      label-width="120px"
    >
      <el-card class="custom-form__section" shadow="never">
        <template #header>
          <span class="custom-form__title">辅助装置信息</span>
        </template>

        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="装置名称" prop="equipment_name">
              <el-input
                v-model.trim="auxiliary.equipment_name"
                placeholder="例如：模温机-水式"
                clearable
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="装置类型" prop="equipment_type">
              <el-input
                v-model.trim="auxiliary.equipment_type"
                placeholder="例如：模温机、干燥机"
                clearable
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="24">
          <el-col :span="24">
            <el-form-item label="规格参数" prop="specification">
              <el-input
                v-model.trim="auxiliary.specification"
                placeholder="例如：油式, 120℃ 或 M12×1.5"
                clearable
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="总数量" prop="total_count">
              <el-input-number
                v-model="auxiliary.total_count"
                :min="0"
                :precision="0"
                controls-position="right"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="可用数量" prop="available_count">
              <el-input-number
                v-model="auxiliary.available_count"
                :min="0"
                :max="auxiliary.total_count"
                :precision="0"
                controls-position="right"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="24">
          <el-col :span="24">
            <el-form-item label="备注" prop="remarks">
              <el-input
                v-model="auxiliary.remarks"
                type="textarea"
                placeholder="可填写适用场景、维护要求、品牌建议等"
                :autosize="{ minRows: 2, maxRows: 10 }"
                maxlength="500"
                show-word-limit
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
        :disabled="!hasUpdatePermission"
        @click="handleSave"
      >
        {{ is_copy ? '保存为新条目' : (is_edit ? '保存' : '创建') }}
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { auxiliaryMethod } from '@/api'

const route = useRoute()
const router = useRouter()

// 路由参数：id → 编辑 / 复制模式
const auxiliary_id = computed(() => {
  const id = route.params.id
  return id ? Number(id) : null
})

const is_edit = computed(() => auxiliary_id.value !== null && route.name === 'equipment-auxiliary-edit')
const is_copy = computed(() => auxiliary_id.value !== null && route.name === 'equipment-auxiliary-copy')

const formRef = ref()
const loaded = ref(false)
const submitting = ref(false)

const auxiliary = ref({
  id: null as number | null,
  equipment_name: '',
  equipment_type: '',
  specification: '',
  total_count: 0,
  available_count: 0,
  remarks: '',
})

const rules = {
  equipment_name: [
    { required: true, message: '请输入装置名称', trigger: 'blur' },
  ],
  equipment_type: [
    { required: true, message: '请输入装置类型', trigger: 'blur' },
  ],
  total_count: [
    { required: true, message: '请输入总数量', trigger: 'blur' },
  ],
  available_count: [
    { required: true, message: '请输入可用数量', trigger: 'blur' },
  ],
}

const hasUpdatePermission = computed(() => {
  // 简单占位：与 InjectionMachineForm 保持一致风格
  return true
})

function goBack() {
  router.push('/equipment/auxiliary/list')
}

async function handleSave() {
  try {
    await formRef.value?.validate()
  } catch {
    ElMessage.warning('请检查必填项')
    return
  }

  submitting.value = true
  try {
    // 清理空字符串为 null（保留 0 等有效数值）
    const payload: any = {}
    for (const [k, v] of Object.entries(auxiliary.value)) {
      if (v === '' || v === undefined) {
        payload[k] = null
      } else {
        payload[k] = v
      }
    }

    let res: any
    if (is_edit.value && auxiliary.value.id) {
      res = await auxiliaryMethod.edit(payload, auxiliary.value.id)
    } else {
      // 新建 / 复制：都走 add（payload.id 已为 null）
      res = await auxiliaryMethod.add(payload)
    }

    if (res.status === 0) {
      ElMessage.success(is_edit.value ? '更新成功' : '创建成功')
      goBack()
    } else {
      ElMessage.error(res.msg || '保存失败')
    }
  } catch (err: any) {
    console.error('[AuxiliaryEquipmentForm] save failed:', err)
    ElMessage.error(err?.message || '提交异常')
  } finally {
    submitting.value = false
  }
}

async function loadDetail(id: number) {
  try {
    const res: any = await auxiliaryMethod.getDetail(id)
    if (res.status === 0) {
      Object.assign(auxiliary.value, res.data)
      // 复制模式：清空 id，让保存时走"新增"分支
      if (is_copy.value) {
        auxiliary.value.id = null
      }
      loaded.value = true
    } else {
      ElMessage.error(res.msg || '未读取到相关辅助装置信息')
      goBack()
    }
  } catch (err: any) {
    console.error('[AuxiliaryEquipmentForm] loadDetail failed:', err)
    ElMessage.error(err?.message || '加载辅助装置详情异常')
    goBack()
  }
}

onMounted(async () => {
  if (auxiliary_id.value !== null) {
    await loadDetail(auxiliary_id.value)
  } else {
    loaded.value = true
  }
})
</script>

<style scoped lang="scss">
/*
 * 页面样式（与 InjectionMachineForm 对齐）
 * - .custom-form / .custom-form__section / .custom-form__title / .form-actions
 *   均复用全局统一样式：src/styles/utilities/custom-form.scss
 * - 本页仅保留页面容器 / page-header / loading-placeholder 最小化样式
 */
.auxiliary-form {
  padding: 16px 16px 96px;
  box-sizing: border-box;
}

.page-header {
  margin-bottom: 16px;
}

.loading-placeholder {
  height: 400px;
}
</style>
