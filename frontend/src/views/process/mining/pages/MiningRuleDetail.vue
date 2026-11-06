<!-- MiningRuleDetail.vue - 候选规则详情：挖掘指标 + 证据样本 + 落地预览（这条规则会变成哪几条生效规则）+ 审核操作（通过 / 驳回）；仅管理员可见 -->
<template>
  <div v-loading="loading" class="mining-rule-detail">
    <!-- 顶部：返回 + 规则编号 + 状态 -->
    <div class="detail-header">
      <el-button @click="goBack">
        <AppIcon icon="mdi:arrow-left" :size="14" style="margin-right: 4px;" />
        返回
      </el-button>
      <span class="detail-header__code mono">{{ rule.rule_code }}</span>
      <el-tag :type="statusTagType(rule.status)">{{ statusLabel(rule.status) }}</el-tag>
    </div>

    <!-- 规则内容 -->
    <el-card class="custom-form__section" shadow="never">
      <span class="custom-form__title">规则内容</span>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="前件缺陷">
          <span class="mono">{{ rule.defect_text || '无' }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="后件">
          <el-tag :type="consequentTagType(rule.consequent)" effect="plain">
            {{ consequentLabel(rule.consequent) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="参数变更" :span="2">
          <span v-if="!(rule.changes || []).length">无</span>
          <div v-for="(c, idx) in rule.changes || []" :key="idx" class="change-item">
            <span class="mono">{{ c.param }}</span>
            <span class="change-item__dir">{{ c.direction === 'increase' ? '调高' : '调低' }}</span>
            <span class="mono" v-if="c.before !== null && c.before !== undefined && c.after !== null && c.after !== undefined">
              {{ c.before }} → {{ c.after }}
            </span>
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="支持度">{{ percent(rule.support) }}</el-descriptions-item>
        <el-descriptions-item label="置信度">{{ (rule.confidence ?? 0).toFixed(3) }}</el-descriptions-item>
        <el-descriptions-item label="提升度">{{ (rule.lift ?? 0).toFixed(3) }}</el-descriptions-item>
        <el-descriptions-item label="证据样本数">{{ rule.sample_count }}</el-descriptions-item>
        <el-descriptions-item label="规则指纹">
          <span class="mono">{{ rule.rule_hash }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="语料游标">
          <span class="mono">{{ rule.corpus_cursor || '-' }}</span>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 落地预览 -->
    <el-card class="custom-form__section" shadow="never">
      <span class="custom-form__title">落地预览</span>
      <div class="field-tip">
        通过后，这条候选规则会被翻译成模糊规则并写入「规则挖掘库」，参与试模推荐。
      </div>

      <!-- 可落地项 -->
      <template v-if="preview && preview.rules && preview.rules.length">
        <div v-for="(r, idx) in preview.rules" :key="idx" class="landing-item">
          <div class="landing-item__desc mono">{{ r.rule_description }}</div>
          <div v-if="r.rule_explanation" class="landing-item__exp">{{ r.rule_explanation }}</div>
          <div class="landing-item__meta">
            <span>缺陷：{{ r.defect_label || r.defect_code || '-' }}</span>
            <span>置信度：{{ (r.confidence ?? 0).toFixed(2) }}</span>
            <span>优先级：{{ r.priority }}</span>
          </div>
        </div>
      </template>
      <el-empty v-else description="该规则无法落地为生效规则" :image-size="60" />

      <!-- 跳过项（原因） -->
      <div v-if="preview && preview.skipped && preview.skipped.length" class="skipped">
        <div class="skipped__title">以下内容被剔除</div>
        <div v-for="(s, idx) in preview.skipped" :key="idx" class="skipped__item">
          <el-tag type="warning" size="small" effect="plain">{{ s.reason }}</el-tag>
          <span class="skipped__detail">{{ s.detail }}</span>
        </div>
      </div>
    </el-card>

    <!-- 待审核：审核操作 -->
    <el-card v-if="rule.status === 'pending'" class="custom-form__section" shadow="never">
      <span class="custom-form__title">审核</span>
      <el-form label-width="80px" class="review-form">
        <el-form-item label="审核意见">
          <el-input
            v-model="reviewNote"
            type="textarea"
            :rows="3"
            placeholder="通过时可选填；驳回时必填"
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="success"
            :loading="submitting"
            :disabled="!preview || !preview.landable"
            @click="handleApprove"
          >
            <AppIcon icon="mdi:check" :size="14" style="margin-right: 4px;" />
            通过并落地
          </el-button>
          <el-button type="danger" :loading="submitting" @click="handleReject">
            <AppIcon icon="mdi:close" :size="14" style="margin-right: 4px;" />
            驳回
          </el-button>
          <span v-if="preview && !preview.landable" class="field-tip field-tip--inline">
            该规则无法落地为生效规则（见上方剔除原因），只能驳回
          </span>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 已审核：审核痕迹 -->
    <el-card v-else class="custom-form__section" shadow="never">
      <span class="custom-form__title">审核记录</span>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="状态">
          <el-tag :type="statusTagType(rule.status)">{{ statusLabel(rule.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="审核人">{{ rule.reviewed_by || '-' }}</el-descriptions-item>
        <el-descriptions-item label="审核时间">{{ rule.reviewed_at || '-' }}</el-descriptions-item>
        <el-descriptions-item label="审核意见">{{ rule.review_note || '-' }}</el-descriptions-item>
        <el-descriptions-item label="落地说明" :span="2">
          {{ rule.landing_note || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="生效规则" :span="2">
          <span class="mono">{{ rule.landed_description || '-' }}</span>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 证据样本 -->
    <el-card class="custom-form__section" shadow="never">
      <span class="custom-form__title">证据样本（{{ (rule.evidence || []).length }}）</span>
      <div v-if="(rule.evidence || []).length" class="evidence">
        <el-tag
          v-for="(e, idx) in rule.evidence || []"
          :key="idx"
          size="small"
          effect="plain"
          class="evidence__item mono"
        >
          {{ e }}
        </el-tag>
      </div>
      <el-empty v-else description="无证据样本" :image-size="60" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getMiningRule, approveMiningRule, rejectMiningRule } from '@/api/mining'
import type { MiningRule, MiningRuleStatus, MiningConsequent } from '@/types/mining'

const route = useRoute()
const router = useRouter()

const rule = ref<MiningRule>({} as MiningRule)
const loading = ref(false)
const submitting = ref(false)
const reviewNote = ref('')

const ruleId = computed(() => Number(route.params.id))
const preview = computed(() => rule.value.landing_preview)

// 文案映射
const STATUS_LABELS: Record<MiningRuleStatus, string> = {
  pending: '待审核',
  approved: '已通过',
  rejected: '已驳回',
}
function statusLabel(s: string) {
  return STATUS_LABELS[s as MiningRuleStatus] || s || '-'
}
function statusTagType(s: string): 'warning' | 'success' | 'info' {
  if (s === 'approved') return 'success'
  if (s === 'rejected') return 'info'
  return 'warning'
}

const CONSEQUENT_LABELS: Record<MiningConsequent, string> = {
  qualified: '合格',
  unqualified: '不合格',
  improved: '有改善',
  worse: '变差',
}
function consequentLabel(c: string) {
  return CONSEQUENT_LABELS[c as MiningConsequent] || c || '-'
}
function consequentTagType(c: string): 'success' | 'danger' | 'warning' | 'info' {
  if (c === 'qualified') return 'success'
  if (c === 'unqualified') return 'danger'
  if (c === 'improved') return 'warning'
  return 'info'
}

function percent(v?: number) {
  return `${((v ?? 0) * 100).toFixed(1)}%`
}

async function loadRule() {
  loading.value = true
  try {
    const res: any = await getMiningRule(ruleId.value)
    rule.value = res.data || res
  } catch (e) {
    rule.value = {} as MiningRule
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push('/process/mining-rules')
}

/** 通过 ⇒ 落地为生效规则 */
async function handleApprove() {
  if (!preview.value?.landable) {
    ElMessage.warning('该规则无法落地为生效规则，请查看剔除原因')
    return
  }
  try {
    await ElMessageBox.confirm(
      '通过后该规则将落地为生效规则并参与试模推荐，确认通过？',
      '通过候选规则',
      { type: 'warning' },
    )
  } catch {
    return
  }
  submitting.value = true
  try {
    await approveMiningRule(ruleId.value, { note: reviewNote.value })
    ElMessage.success('已通过并落地为生效规则')
    await loadRule()
  } catch {
    // 拦截器已统一提示
  } finally {
    submitting.value = false
  }
}

/** 驳回（意见必填） */
async function handleReject() {
  const note = reviewNote.value.trim()
  if (!note) {
    ElMessage.warning('请填写驳回原因')
    return
  }
  try {
    await ElMessageBox.confirm(
      `驳回后该候选规则不再进入审核，确认驳回？\n${note}`,
      '驳回候选规则',
      { type: 'warning' },
    )
  } catch {
    return
  }
  submitting.value = true
  try {
    await rejectMiningRule(ruleId.value, { note })
    ElMessage.success('已驳回')
    await loadRule()
  } catch {
    // 拦截器已统一提示
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadRule()
})
</script>

<style lang="scss" scoped>
.mining-rule-detail {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

/* 顶部条 */
.detail-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.detail-header__code {
  font-size: 16px;
  font-weight: 600;
}

/* 变更明细行 */
.change-item {
  line-height: 1.8;
}

.change-item__dir {
  margin: 0 8px;
  color: var(--el-color-primary, #254373);
}

/* 落地预览条目 */
.landing-item {
  border: 1px solid var(--el-border-color-lighter, #ebeef5);
  border-radius: 6px;
  padding: 10px 12px;
  margin-bottom: 8px;
}

.landing-item__desc {
  font-weight: 600;
}

.landing-item__exp {
  margin-top: 4px;
  color: var(--el-text-color-regular, #606266);
  line-height: 1.6;
}

.landing-item__meta {
  margin-top: 6px;
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: var(--el-text-color-secondary, #909399);
}

/* 跳过项 */
.skipped {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px dashed var(--el-border-color-lighter, #ebeef5);
}

.skipped__title {
  font-size: 13px;
  color: var(--el-text-color-regular, #606266);
  margin-bottom: 6px;
}

.skipped__item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 6px;
  line-height: 1.6;
}

.skipped__detail {
  font-size: 13px;
  color: var(--el-text-color-secondary, #909399);
}

/* 证据样本 */
.evidence {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.evidence__item {
  font-family: 'Courier New', Consolas, monospace;
}

/* 表单提示 */
.field-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary, #909399);
  line-height: 1.5;
  margin: 4px 0 10px;
}

.field-tip--inline {
  margin: 0 0 0 12px;
}

/* 等宽字体 */
.mono {
  font-family: 'Courier New', Consolas, monospace;
  color: #303133;
}

/* 审核表单 */
.review-form {
  max-width: 720px;
}
</style>
