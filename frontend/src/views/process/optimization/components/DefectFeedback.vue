<!--
  DefectFeedback - 缺陷反馈表单
  - 默认显示 1 个缺陷卡；只有>1的卡显示"移除"按钮
  - 无缺陷（DEFECTFREE）作为合法缺陷之一
  - 数据：DefectFeedbackData[]
-->
<template>
  <div class="defect-feedback">
    <div
      v-for="(defect, idx) in defectList"
      :key="defect.__local_id"
      class="defect-feedback__item"
    >
      <div class="defect-feedback__item-header">
        <span class="defect-feedback__item-title">
          <el-tag
            v-if="getKeyword(defect)"
            :type="isDefectFree(defect) ? 'success' : 'warning'"
            size="small"
            effect="light"
            class="defect-feedback__title-tag"
          >
            <AppIcon
              :icon="isDefectFree(defect) ? 'mdi:check-circle' : 'mdi:alert-circle'"
              style="margin-right: 2px;"
            />
            {{ getItemTitle(defect, idx) }}
          </el-tag>
          <span v-else class="defect-feedback__title-pending">
            {{ getItemTitle(defect, idx) }}
          </span>
        </span>
        <el-button
          v-if="defectList.length > 1"
          type="text"
          size="small"
          @click="removeDefect(idx)"
        >
          <AppIcon icon="mdi:close" />
          移除
        </el-button>
      </div>

      <el-form
        :model="defect"
        label-width="80px"
        size="small"
        class="defect-feedback__form"
      >
        <el-form-item label="缺陷类型">
          <el-select
            :model-value="defect.keyword_id"
            :disabled="!keywordsLoaded"
            :loading="!keywordsLoaded"
            placeholder="请选择缺陷类型"
            style="width: 100%;"
            filterable
            @change="(val: number | null) => onKeywordChange(idx, val)"
          >
            <el-option
              v-for="kw in sortedKeywords"
              :key="kw.id"
              :label="kw.keyword_alias"
              :value="kw.id"
            />
          </el-select>
          <div
            v-if="keywordsLoaded && !sortedKeywords.length"
            class="defect-feedback__hint"
          >
            暂无可用缺陷类型，请联系管理员添加
          </div>
        </el-form-item>

        <el-form-item
          v-if="!isDefectFree(defect)"
          label="缺陷程度"
        >
          <span
            v-if="!getKeyword(defect)"
            class="defect-feedback__hint"
          >
            请先选择缺陷类型
          </span>
          <template v-else>
            <el-radio-group v-model="defect.level">
              <el-radio-button
                v-for="opt in getLevelOptions(defect)"
                :key="opt.value"
                :value="opt.value"
              >
                {{ opt.label }}
              </el-radio-button>
            </el-radio-group>
            <div
              v-if="!getLevelOptions(defect).length"
              class="defect-feedback__hint"
            >
              该缺陷类型暂未配置程度选项，请联系管理员
            </div>
          </template>
        </el-form-item>

        <el-form-item
          v-if="!isDefectFree(defect) && getKeyword(defect)"
          label="缺陷位置"
        >
          <el-select
            v-model="defect.position"
            filterable
            allow-create
            default-first-option
            clearable
            placeholder="选择预设位置或输入自定义位置"
            style="width: 100%;"
          >
            <el-option
              v-for="opt in getPositionOptions(defect)"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>
      </el-form>

      <div
        v-if="isDefectFree(defect)"
        class="defect-feedback__ok-hint"
      >
        <AppIcon icon="mdi:check-circle-outline" />
        <span>已标记无缺陷，工艺仍可继续优化（提产能、降周期、降能耗）</span>
      </div>

      <div
        v-if="!isDefectFree(defect)"
        class="defect-feedback__evidence"
      >
        <el-tabs
          v-model="evidenceTabMap[defect.__local_id]"
          class="defect-feedback__tabs"
        >
          <el-tab-pane label="上传图片" name="image">
            <el-upload
              :file-list="imageMap[defect.__local_id] || []"
              action="#"
              :auto-upload="false"
              list-type="picture-card"
              :limit="5"
              :on-exceed="uploadHandlers.onExceed"
              :on-preview="uploadHandlers.onPreview"
              :on-remove="uploadHandlers.onRemove"
              accept="image/*"
            >
              <AppIcon icon="mdi:image-plus" class="defect-feedback__upload-icon" />
              <div class="defect-feedback__upload-label">添加图片</div>
            </el-upload>
            <div class="defect-feedback__tip">
              支持 jpg / png，单张 ≤ 20MB，最多 5 张（提交时统一上传）
            </div>
          </el-tab-pane>

          <el-tab-pane label="模型选点" name="model">
            <ModelPicker
              :value="defect.position_3d ?? null"
              @update:value="makeModelPickerHandler(defect)"
            />
            <div class="defect-feedback__tip">
              可选：上传 STL 模型后在表面点击选点，作为缺陷位置的精细化补充（不取代缺陷位置字段）
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>

    <!--
      添加缺陷按钮区：暂不开放多缺陷（需求未明确），隐藏保留备将来恢复
      - 打开方式：把 v-if 改为 true，或改为某个可控 prop
      - 同时需恢复：MAX_DEFECT_COUNT、canAddDefect、addDefect() 的实际使用
    -->
    <div v-if="false" class="add-button-wrapper">
      <el-button
        v-if="canAddDefect"
        text
        type="primary"
        size="small"
        @click="addDefect"
      >
        <AppIcon icon="mdi:plus" style="margin-right: 4px;" />
        添加缺陷
      </el-button>
      <div
        v-else
        class="defect-feedback__limit-hint"
      >
        最多添加 {{ MAX_DEFECT_COUNT }} 个缺陷
      </div>
    </div>

    <el-dialog
      v-model="previewVisible"
      :title="previewTitle"
      width="60%"
      append-to-body
    >
      <img :src="previewUrl" alt="预览" style="width: 100%;" />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { UploadUserFile } from 'element-plus'
import type { RuleKeyword } from '@/types/rule'
import type { DefectFeedbackData } from '@/types/optimization'
import { LEVEL_WORDS, DEFECT_LEVEL_LABELS } from '@/constants/rule-const'
import { DEFECTFREE_KEYWORD_NAME } from '@/constants/special-keywords'
import { sortDefectsByCommon } from '@/constants/defect-order'
import ModelPicker from '@/components/three/ModelPicker.vue'

const MAX_DEFECT_COUNT = 5

/** 内部缺陷项：业务数据 + 本地 __local_id（用于 v-for key 与证据区映射） */
type DefectItem = DefectFeedbackData & { __local_id: string }

const props = defineProps<{
  modelValue?: DefectFeedbackData[]
  defectKeywords?: RuleKeyword[]
  positionKeywords?: RuleKeyword[]
  /** 缺陷 keyword 是否已加载完成（控制 select 的 loading/disabled） */
  keywordsLoaded?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: DefectFeedbackData[]): void
}>()

const defectList = ref<DefectItem[]>([])

/** 每个缺陷的 evidence tab 状态（独立维护，key=__local_id，默认值 'image'） */
const evidenceTabMap = reactive<Record<string, 'image' | 'model'>>({})
const imageMap = reactive<Record<string, UploadUserFile[]>>({})

/**
 * 从 modelValue 重建本地列表
 * - 传入 [] → 默认显示 1 个空缺陷卡
 * - 传入 ≥1 → 按传入重建
 * - 不立即 emit 到父级（保持父级 modelValue 与本地可能存在的 1 个空卡的"分歧"）
 * - 同步初始化 evidenceTabMap[__local_id] = 'image'（默认激活"上传图片"）
 */
function rebuildFromProps(val: DefectFeedbackData[] | undefined) {
  const incoming = val ?? []
  if (incoming.length === 0) {
    const item = makeEmptyDefect()
    evidenceTabMap[item.__local_id] = 'image'
    defectList.value = [item]
    return
  }
  defectList.value = incoming.map((d, i) => {
    const localId = d.position || `__empty_${i}_${d.keyword_id ?? 'null'}`
    if (!evidenceTabMap[localId]) evidenceTabMap[localId] = 'image'
    return { ...d, __local_id: localId }
  })
}

/** 空缺陷项（默认显示 1 个 / "添加缺陷" 时复用） */
function makeEmptyDefect(): DefectItem {
  return {
    __local_id: `__new_${Math.random().toString(36).slice(2, 10)}`,
    keyword_id: null,
    keyword_name: null,
    level: null,
    position: '',
    position_3d: null,
  }
}

// 首次同步
rebuildFromProps(props.modelValue)

watch(
  () => props.modelValue,
  (val) => rebuildFromProps(val),
  { deep: true },
)

/** 本地变化 → emit 到父级 */
function syncToParent() {
  emit(
    'update:modelValue',
    defectList.value.map(({ __local_id, ...rest }) => rest),
  )
}

const sortedKeywords = computed<RuleKeyword[]>(() => {
  const sorted = sortDefectsByCommon(props.defectKeywords ?? [])
  sorted.sort((a, b) => {
    if (a.keyword_name === DEFECTFREE_KEYWORD_NAME) return -1
    if (b.keyword_name === DEFECTFREE_KEYWORD_NAME) return 1
    return 0
  })
  return sorted
})

function getKeyword(defect: DefectItem): RuleKeyword | null {
  return props.defectKeywords?.find(k => k.id === defect.keyword_id) ?? null
}

function isDefectFree(defect: DefectItem): boolean {
  return getKeyword(defect)?.keyword_name === DEFECTFREE_KEYWORD_NAME
}

function getItemTitle(defect: DefectItem, idx: number): string {
  const kw = getKeyword(defect)
  if (!kw) return `缺陷 #${idx + 1}（未选）`
  if (kw.keyword_name === DEFECTFREE_KEYWORD_NAME) return `缺陷 #${idx + 1}（无缺陷）`
  return `缺陷 #${idx + 1}：${kw.keyword_alias || kw.keyword_name}`
}

function onKeywordChange(idx: number, val: number | null) {
  const defect = defectList.value[idx]
  if (!defect) return
  const kw = val === null ? null : props.defectKeywords?.find(k => k.id === val)
  if (val !== null && !kw) return

  // 切换 keyword：val=null 表示主动清空；val=number 表示选中
  defect.keyword_id = val
  defect.keyword_name = kw ? kw.keyword_name : null
  defect.level = null
  defect.position = ''
  defect.position_3d = null

  syncToParent()
}

function getLevelOptions(defect: DefectItem): Array<{ value: string; label: string }> {
  const kw = getKeyword(defect)
  if (!kw || isDefectFree(defect)) return []
  const words = LEVEL_WORDS[kw.fuzzy_level] || []
  return words.map(w => ({ value: w, label: DEFECT_LEVEL_LABELS[w] || w }))
}

/** 按 defect 类型联动过滤 position options（命名：DL + defect 名 + 段号） */
function getPositionOptions(defect: DefectItem): Array<{ value: string; label: string }> {
  const kw = getKeyword(defect)
  if (!kw || isDefectFree(defect)) return []
  const prefix = `DL${kw.keyword_name}`
  const indexed = (props.positionKeywords ?? [])
    .filter(p => p.keyword_name.startsWith(prefix))
    .map((p, originalIdx) => {
      const m = p.keyword_name.match(/(\d+)$/)
      return { p, originalIdx, segment: m ? Number(m[1]) : Infinity }
    })
  indexed.sort((a, b) => a.segment - b.segment || a.originalIdx - b.originalIdx)
  return indexed.map(({ p }) => ({
    value: p.keyword_name,
    label: p.keyword_alias || p.keyword_name,
  }))
}

const canAddDefect = computed(() => defectList.value.length < MAX_DEFECT_COUNT)

function addDefect() {
  if (!canAddDefect.value) return
  const item = makeEmptyDefect()
  evidenceTabMap[item.__local_id] = 'image'
  defectList.value.push(item)
  syncToParent()
}

function removeDefect(idx: number) {
  defectList.value.splice(idx, 1)
  syncToParent()
}

const previewVisible = ref(false)
const previewUrl = ref('')
const previewTitle = ref('预览')

const uploadHandlers = {
  onExceed: () => ElMessage.warning('最多上传 5 张图片'),
  onPreview: (file: UploadUserFile) => {
    previewUrl.value = file.url || ''
    previewTitle.value = file.name || '预览'
    previewVisible.value = true
  },
  onRemove: () => {
    // 仅前端预览，删除即同步；后续接入上传时再调后端
  },
}

/** v-for 中每个 defect 都需要独立的 handler（更新自己的 position_3d 后 emit 到父级） */
function makeModelPickerHandler(defect: DefectItem) {
  return (val: { x: number; y: number; z: number } | null) => {
    defect.position_3d = val
    syncToParent()
  }
}
</script>

<style lang="scss" scoped>
/*
 * 类层级 ≤ 2：.defect-feedback > __item / __hint 等
 * 不带 title（由父级 round-detail-block__title 提供）
 * 每个缺陷独立卡片（__item），可堆叠多个
 */
.defect-feedback {
  &__item {
    margin-bottom: 16px;
    padding: 12px 16px;
    border: 1px solid #ebeef5;
    border-radius: 4px;
    background: #fff;

    &:last-child {
      margin-bottom: 0;
    }
  }

  &__item-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px dashed #ebeef5;
  }

  &__item-title {
    font-size: 13px;
    font-weight: 500;
    color: #303133;
  }

  // tag 包裹的标题：行内高度对齐，让 el-tag 与右侧按钮基线对齐
  &__title-tag {
    display: inline-flex;
    align-items: center;
    height: 22px;
    padding: 0 8px;
    font-size: 12px;
    font-weight: 500;
    line-height: 1;

    // 穿透：el-tag 内部 .el-tag__content 也是 inline-flex，让 svg 图标与文字基线对齐
    :deep(.el-tag__content) {
      display: inline-flex;
      align-items: center;
      gap: 2px;
      height: 100%;
    }
  }

  // 未选时退化为灰色提示
  &__title-pending {
    font-size: 13px;
    font-weight: 500;
    color: #909399;
  }

  &__evidence {
    margin-top: 16px;
    border: 1px solid #ebeef5;
    border-radius: 4px;
    background: #fafbfc;
    padding: 4px 12px 12px;
  }

  // tabs 头部紧凑一些
  &__tabs :deep(.el-tabs__header) {
    margin-bottom: 8px;
  }
  &__tabs :deep(.el-tabs__nav-wrap::after) {
    height: 1px;
  }

  &__upload-icon {
    font-size: 22px;
    color: #909399;
  }
  &__upload-label {
    margin-top: 4px;
    font-size: 12px;
    color: #606266;
  }

  &__tip {
    margin-top: 8px;
    font-size: 12px;
    color: #909399;
    line-height: 1.5;
  }

  // 提示文案（warning 色，::before 绘制小圆点）
  &__hint {
    position: relative;
    padding-left: 12px;
    font-size: 12px;
    color: #e6a23c;
    line-height: 1.5;

    &::before {
      content: '';
      position: absolute;
      left: 0;
      top: 50%;
      width: 6px;
      height: 6px;
      margin-top: -3px;
      background: #e6a23c;
      border-radius: 50%;
    }
  }

  // DEFECTFREE 选中时的友好提示
  &__ok-hint {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 10px 12px;
    margin-top: 4px;
    font-size: 13px;
    color: #67c23a;
    background: #f0f9eb;
    border-radius: 4px;
  }

  &__limit-hint {
    font-size: 12px;
    color: #909399;
  }
}

.add-button-wrapper {
  display: flex;
  justify-content: flex-start;
  margin: 8px 0 0;
  padding: 0;
}
</style>