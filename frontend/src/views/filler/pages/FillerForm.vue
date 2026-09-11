<!--
  FillerForm - 填充物表单（new / edit / copy 三模式共用）

  路由：
    - /material/filler/new         新建
    - /material/filler/:id/edit    编辑
    - /material/filler/:id/copy    复制（清空 id 和 name）

  架构（2026-09-08）：
    - 单 card 设计：11 字段平铺，4 列布局，groupIntoRows 自动分行（3 行可见）
-->
<template>
  <div class="filler-form">
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
      :model="filler_info"
      :rules="rules"
      class="custom-form"
      label-width="120px"
    >
      <el-card class="custom-form__section" shadow="never">
        <template #header>
          <span class="custom-form__title">填充物信息</span>
        </template>

        <el-row
          v-for="(row, rIdx) in rows"
          :key="`filler_${rIdx}`"
          :gutter="24"
        >
          <el-col
            v-for="(item, iIdx) in row"
            :key="`field_${rIdx}_${iIdx}`"
            :span="item.span"
          >
            <el-form-item
              v-if="item.prop"
              :label="item.label"
              :prop="item.prop"
            >
              <el-input
                v-if="item.type === 'input'"
                v-model.trim="filler_info[item.prop!]"
                :placeholder="getPlaceholder(item)"
                clearable
              />

              <el-input
                v-else-if="item.type === 'number'"
                v-model.trim="filler_info[item.prop!]"
                v-number="getPrecision(item)"
                :placeholder="getPlaceholder(item)"
                clearable
              >
                <template #suffix v-if="item.unit">{{ item.unit }}</template>
              </el-input>

              <el-select
                v-else-if="item.type === 'select'"
                v-model="filler_info[item.prop!]"
                :placeholder="getPlaceholder(item)"
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
    </el-form>

    <div v-if="loaded" class="form-actions">
      <el-button @click="goBack">取消</el-button>
      <el-button
        type="primary"
        :loading="submitting"
        @click="handleSave"
      >
        {{ is_edit ? '保存' : '创建' }}
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { fillerMethod } from '@/api'
import {
  initialFillerInfo,
  fillerTypeOptions,
  fillerCategoryOptions,
  colorOptions,
  shapeOptions,
} from '@/constants/polymer-const'
import { groupIntoRows } from '@/utils/form-layout'
import { getPlaceholder, getPrecision } from '@/utils/form-helper'
import type { FormItem } from '@/utils/form-types'

const route = useRoute()
const router = useRouter()

const is_edit = computed(() => !!route.params.id && route.name !== 'material-filler-copy')
const is_copy = computed(() => route.name === 'material-filler-copy')
const filler_id = computed(() => {
  const id = route.params.id
  return id ? Number(id) : null
})

const filler_info = ref<any>(structuredClone(initialFillerInfo))
const formRef = ref<FormInstance>()
const submitting = ref(false)
const loaded = ref(false)

// ============================================================================
// 字段定义（11 字段平铺，4 列布局自动分行）
// ============================================================================

const items: FormItem[] = [
  { label: '名称', prop: 'name', type: 'input', required: true, placeholder: '如：玻璃纤维、碳酸钙' },
  { label: '缩写', prop: 'abbreviation', type: 'select', options: fillerTypeOptions, allowCreate: false, placeholder: '如：GF, TALC, CaCO₃' },
  { label: '类别', prop: 'category', type: 'select', options: fillerCategoryOptions, allowCreate: false, placeholder: '如：无机填充、增强纤维' },
  { label: '形状', prop: 'shape', type: 'select', options: shapeOptions, allowCreate: false, placeholder: '如：球形、针状、片状' },
  { label: '中位粒径(ρ)', prop: 'particle_size_d50', type: 'number', unit: 'μm', precision: 2 },
  { label: '长径比', prop: 'aspect_ratio', type: 'number', precision: 2 },
  { label: '含水率', prop: 'moisture_content', type: 'number', unit: '%', precision: 2 },
  { label: '表面处理', prop: 'surface_treatment', type: 'input', placeholder: '如：硅烷偶联剂处理' },
  { label: '密度', prop: 'density', type: 'number', unit: 'g/cm³', precision: 4 },
  { label: '热稳定温度', prop: 'thermal_stability_temp', type: 'number', unit: '℃' },
  { label: '颜色', prop: 'color', type: 'select', options: colorOptions, allowCreate: true },
]

const rows = computed(() => groupIntoRows(items, { columns: 4 }))

const rules: FormRules = {
  name: [
    { required: true, message: '名称不能为空', trigger: 'blur' },
  ],
}

function goBack() {
  router.push('/material/filler/list')
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
    // 清理 null / 空字符串（保留 0 等有效值）
    const payload: any = {}
    for (const [key, val] of Object.entries(filler_info.value)) {
      if (val !== null && val !== '') {
        payload[key] = val
      }
    }

    let res: any
    if (filler_id.value !== null && !is_copy.value) {
      res = await fillerMethod.edit(payload, filler_id.value)
    } else {
      res = await fillerMethod.add(payload)
    }

    if (res.status === 0) {
      ElMessage.success(is_edit ? '填充物编辑成功！' : '填充物新增成功！')
      goBack()
    } else {
      ElMessage.error(res.msg || '保存失败')
    }
  } catch (err: any) {
    console.error('[FillerForm] save failed:', err)
    ElMessage.error(err?.message || '提交异常')
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  if (filler_id.value !== null) {
    await loadDetail(filler_id.value)
  } else {
    loaded.value = true
  }
})

async function loadDetail(id: number) {
  try {
    const res: any = await fillerMethod.getDetail(id)
    if (res.status === 0) {
      filler_info.value = res.data
      if (is_copy.value) {
        filler_info.value.id = null
        filler_info.value.name = null
      }
      loaded.value = true
    } else {
      ElMessage.error(res.msg || '未读取到填充物信息')
      router.push('/material/filler/list')
    }
  } catch (err: any) {
    console.error('[FillerForm] loadDetail failed:', err)
    ElMessage.error(err?.message || '加载填充物详情异常')
    router.push('/material/filler/list')
  }
}
</script>

<style scoped lang="scss">
.filler-form {
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

/* card 标题 */
.custom-form__title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}
</style>