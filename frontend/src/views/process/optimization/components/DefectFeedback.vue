<!-- DefectFeedback - 缺陷反馈表单 -->
<template>
  <div class="defect-feedback">
    <!-- 工艺效果评价（整轮一个）：首轮只判合格性，后续轮可判合格性与相较上一轮的变化 -->
    <div class="defect-feedback__tuning-result">
      <span class="defect-feedback__tuning-label">
        {{ hasComparison ? '工艺效果' : '产品是否合格' }}
        <el-tooltip
          placement="top"
          :show-after="200"
          :hide-after="0"
        >
          <template #content>
            <template v-if="hasComparison">
              本轮试模结果：产品是否合格、相较上一轮的变化<br>
              写入本轮调参记录，作为算法的训练标签
            </template>
            <template v-else>
              本轮试模结果：产品是否合格<br>
              写入本轮调参记录，作为算法的训练标签
            </template>
          </template>
          <AppIcon
            icon="mdi:help-circle-outline"
            class="defect-feedback__tuning-help"
          />
        </el-tooltip>
      </span>
      <el-radio-group
        :model-value="tuningResult"
        size="small"
        @update:model-value="onTuningResultChange"
      >
        <el-radio-button value="qualified">合格</el-radio-button>
        <template v-if="hasComparison">
          <el-radio-button value="effective">改善</el-radio-button>
          <el-radio-button value="unchanged">无变化</el-radio-button>
          <el-radio-button value="ineffective">变差</el-radio-button>
        </template>
        <template v-else>
          <el-radio-button value="unqualified">不合格</el-radio-button>
        </template>
      </el-radio-group>
    </div>

    <!-- 合格态：产品没有缺陷 ⇒ 缺陷区整体不渲染（下方缺陷卡片列表为空） -->
    <div v-if="isQualified" class="defect-feedback__hint">
      产品已合格，本轮无需填写缺陷信息
    </div>

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
          <span
            v-if="isDefectFree(defect)"
            class="defect-feedback__hint"
          >
            无缺陷（历史记录，已由「产品是否合格」取代）
          </span>
          <el-select
            v-else
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
            <el-radio-group
              v-model="defect.level"
              @change="syncToParent"
            >
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
            @change="syncToParent"
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

    <!-- 添加缺陷按钮区：多缺陷暂不开放（需求未明确），整块隐藏保留 -->
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
import type { DefectFeedbackData, TuningResult } from '@/types/optimization'
import { LEVEL_WORDS, DEFECT_LEVEL_LABELS } from '@/constants/rule-const'
import { DEFECTFREE_KEYWORD_NAME } from '@/constants/special-keywords'
import { sortDefectsByCommon } from '@/constants/defect-order'
import ModelPicker from '@/components/three/ModelPicker.vue'

const MAX_DEFECT_COUNT = 5

/** 内部缺陷项：业务数据 + 本地 __local_id（用于 v-for key 与证据区映射） */
type DefectItem = DefectFeedbackData & { __local_id: string }

const props = withDefaults(defineProps<{
  modelValue?: DefectFeedbackData[]
  defectKeywords?: RuleKeyword[]
  positionKeywords?: RuleKeyword[]
  /** 缺陷 keyword 是否已加载完成（控制 select 的 loading/disabled） */
  keywordsLoaded?: boolean
  /** 工艺效果评价（整轮一个） */
  tuningResult?: TuningResult
  /** 是否有对比基准（第 2 轮起才有）：true 时在「合格」外另提供「改善/无变化/变差」 */
  hasComparison?: boolean
}>(), {
  hasComparison: true,
})

const emit = defineEmits<{
  (e: 'update:modelValue', val: DefectFeedbackData[]): void
  (e: 'update:tuningResult', val: TuningResult): void
}>()

const defectList = ref<DefectItem[]>([])

/**
 * 是否「合格」：合格态产品没有缺陷 ⇒ 缺陷区整体隐藏并清空。
 * ⚠️ 只隐藏缺陷输入区，上面的「工艺效果评价」单选必须保留（用户靠它切到合格）。
 */
const isQualified = computed(() => props.tuningResult === 'qualified')

/** 每个缺陷的 evidence tab 状态（独立维护，key=__local_id，默认值 'image'） */
const evidenceTabMap = reactive<Record<string, 'image' | 'model'>>({})
const imageMap = reactive<Record<string, UploadUserFile[]>>({})

/** 从 modelValue 重建本地列表（空数组 → 显示 1 个空缺陷卡；重建不立即 emit，保留与父级的"分歧"） */
function rebuildFromProps(val: DefectFeedbackData[] | undefined) {
  // 合格态：缺陷区整体隐藏 ⇒ 不建任何缺陷卡（否则会露出一张空白卡）
  if (isQualified.value) {
    defectList.value = []
    return
  }
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

rebuildFromProps(props.modelValue)

watch(
  () => props.modelValue,
  (val) => rebuildFromProps(val),
  { deep: true },
)

/** 合格态切换：合格 ⇒ 隐藏并清空缺陷区（含父级已填的）；离开合格 ⇒ 按当前值重建 */
watch(
  () => props.tuningResult,
  (val) => {
    if (val === 'qualified') {
      defectList.value = []
      // 后端合格态也会丢弃缺陷，界面上更不该留着
      emit('update:modelValue', [])
    } else {
      rebuildFromProps(props.modelValue)
    }
  },
)

function syncToParent() {
  emit(
    'update:modelValue',
    defectList.value.map(({ __local_id, ...rest }) => rest),
  )
}

const sortedKeywords = computed<RuleKeyword[]>(() =>
  sortDefectsByCommon(props.defectKeywords ?? []),
)

/** 是否「无缺陷」项：读数据自带 keyword_name，不依赖 keyword 列表（该类型已下线，列表里已过滤） */
function isDefectFree(defect: DefectItem): boolean {
  return defect.keyword_name === DEFECTFREE_KEYWORD_NAME
}

function onTuningResultChange(val: TuningResult) {
  emit('update:tuningResult', val)
}

function getKeyword(defect: DefectItem): RuleKeyword | null {
  return props.defectKeywords?.find(k => k.id === defect.keyword_id) ?? null
}

function getItemTitle(defect: DefectItem, idx: number): string {
  if (isDefectFree(defect)) return `缺陷 #${idx + 1}（无缺陷）`
  const kw = getKeyword(defect)
  if (!kw) return `缺陷 #${idx + 1}（未选）`
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
    // 仅前端预览，删除即同步
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
/* 类层级 ≤ 2：.defect-feedback > __item / __hint 等
   不带 title（由父级 round-detail-block__title 提供） */
.defect-feedback {
  &__tuning-result {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 12px;
    padding: 8px 12px;
    background: #f5f7fa;
    border-radius: 4px;
  }

  &__tuning-label {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 13px;
    color: #606266;
  }

  &__tuning-help {
    color: #c0c4cc;
    cursor: help;
  }

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

  // 提示文案：warning 色 + ::before 小圆点
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