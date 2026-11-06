<!-- MiningRuleList.vue - 候选规则审核台：规则挖掘产出的候选规则列表（通过 / 驳回入口）
     仅管理员可见（前端 adminOnly 过滤 + 后端 require_admin 二次防护） -->
<template>
  <div class="mining-rule-list">
    <!-- 搜索卡片 -->
    <div class="search-container">
      <el-form :inline="true" class="search-form">
        <el-form-item label="规则编号">
          <el-input
            v-model="query.keyword"
            placeholder="如 MR-202611-00001"
            clearable
            style="width: 200px"
            @keyup.enter="loadRules"
          />
        </el-form-item>
        <el-form-item label="审核状态">
          <el-select v-model="query.status" clearable placeholder="全部" style="width: 140px">
            <el-option label="待审核" value="pending" />
            <el-option label="已通过" value="approved" />
            <el-option label="已驳回" value="rejected" />
          </el-select>
        </el-form-item>
        <el-form-item label="后件">
          <el-select v-model="query.consequent" clearable placeholder="全部" style="width: 140px">
            <el-option label="合格" value="qualified" />
            <el-option label="不合格" value="unqualified" />
            <el-option label="有改善" value="improved" />
            <el-option label="变差" value="worse" />
          </el-select>
        </el-form-item>
        <el-form-item class="search-actions">
          <el-button type="primary" @click="search">
            <AppIcon icon="mdi:magnify" :size="14" style="margin-right: 4px;" />
            搜索
          </el-button>
          <el-button @click="resetQuery">
            <AppIcon icon="mdi:refresh" :size="14" style="margin-right: 4px;" />
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 候选规则表格 -->
    <div class="table-wrapper">
      <el-table
        v-loading="loading"
        :data="rules"
        border
        stripe
        height="100%"
      >
        <el-table-column type="index" label="#" width="60" align="center" fixed="left" />
        <el-table-column label="规则编号" prop="rule_code" min-width="170" fixed="left">
          <template #default="{ row }">
            <el-link type="primary" @click="goDetail(row)">{{ row.rule_code }}</el-link>
          </template>
        </el-table-column>
        <el-table-column label="前件缺陷" prop="defect_text" min-width="180">
          <template #default="{ row }">
            <span class="mono">{{ row.defect_text || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="参数变更" min-width="220">
          <template #default="{ row }">
            <span class="mono">{{ changeText(row) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="后件" prop="consequent" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="consequentTagType(row.consequent)" effect="plain">
              {{ consequentLabel(row.consequent) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="支持度" prop="support" width="100" align="right">
          <template #default="{ row }">{{ percent(row.support) }}</template>
        </el-table-column>
        <el-table-column label="置信度" prop="confidence" width="100" align="right">
          <template #default="{ row }">{{ (row.confidence ?? 0).toFixed(3) }}</template>
        </el-table-column>
        <el-table-column label="提升度" prop="lift" width="100" align="right">
          <template #default="{ row }">{{ (row.lift ?? 0).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="证据" prop="sample_count" width="80" align="center" />
        <el-table-column label="状态" prop="status" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="text" @click="goDetail(row)">详情</el-button>
            <template v-if="row.status === 'pending'">
              <el-button type="text" @click="handleApprove(row)">通过</el-button>
              <el-button type="text" class="text-danger" @click="handleReject(row)">驳回</el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 分页器：始终显示（无数据时保留「共 0 条」占位）-->
    <el-pagination
      class="pagination"
      layout="total, prev, pager, next"
      :current-page="query.page_no"
      :page-size="query.page_size"
      :total="total"
      @current-change="onPageChange"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listMiningRules, approveMiningRule, rejectMiningRule } from '@/api/mining'
import type { MiningRule, MiningRuleStatus, MiningConsequent } from '@/types/mining'

const router = useRouter()

// 状态
const rules = ref<MiningRule[]>([])
const total = ref(0)
const loading = ref(false)
const query = reactive({
  keyword: '',
  status: '' as '' | MiningRuleStatus,
  consequent: '' as '' | MiningConsequent,
  page_no: 1,
  page_size: 20,
})

// 文案映射
const STATUS_LABELS: Record<MiningRuleStatus, string> = {
  pending: '待审核',
  approved: '已通过',
  rejected: '已驳回',
}
function statusLabel(s: string) {
  return STATUS_LABELS[s as MiningRuleStatus] || s
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
  return CONSEQUENT_LABELS[c as MiningConsequent] || c
}
function consequentTagType(c: string): 'success' | 'danger' | 'warning' | 'info' {
  if (c === 'qualified') return 'success'
  if (c === 'unqualified') return 'danger'
  if (c === 'improved') return 'warning'
  return 'info'
}

/** 参数变更文本（inj_pres_1:increase 50→60） */
function changeText(row: MiningRule) {
  const changes = row.changes || []
  if (!changes.length) return '-'
  return changes
    .map(c => {
      const dir = c.direction === 'increase' ? '调高' : '调低'
      const range =
        c.before !== null && c.before !== undefined && c.after !== null && c.after !== undefined
          ? ` ${c.before}→${c.after}`
          : ''
      return `${c.param}(${dir})${range}`
    })
    .join('、')
}

function percent(v?: number) {
  return `${((v ?? 0) * 100).toFixed(1)}%`
}

// 数据加载
async function loadRules() {
  loading.value = true
  try {
    const res: any = await listMiningRules({
      page_no: query.page_no,
      page_size: query.page_size,
      status: query.status || undefined,
      consequent: query.consequent || undefined,
      keyword: query.keyword || undefined,
    })
    rules.value = res.data?.items || res.items || []
    total.value = res.data?.total ?? res.total ?? 0
  } catch (e) {
    rules.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function search() {
  query.page_no = 1
  loadRules()
}

function resetQuery() {
  query.keyword = ''
  query.status = ''
  query.consequent = ''
  query.page_no = 1
  loadRules()
}

function onPageChange(p: number) {
  query.page_no = p
  loadRules()
}

function goDetail(row: MiningRule) {
  router.push(`/process/mining-rules/${row.id}`)
}

/** 通过 ⇒ 落地为生效规则 */
async function handleApprove(row: MiningRule) {
  try {
    await ElMessageBox.confirm(
      `通过后该规则将落地为生效规则并参与试模推荐，确认通过？\n${row.rule_code}`,
      '通过候选规则',
      { type: 'warning' },
    )
  } catch {
    return
  }
  try {
    await approveMiningRule(row.id)
    ElMessage.success('已通过并落地为生效规则')
    loadRules()
  } catch {
    // 拦截器已统一提示（不可落地 / 已审核等）
  }
}

/** 驳回（必须填意见） */
async function handleReject(row: MiningRule) {
  let note = ''
  try {
    const { value } = await ElMessageBox.prompt(
      '请填写驳回原因（将记录在候选规则上）',
      '驳回候选规则',
      {
        type: 'warning',
        inputPlaceholder: '如：证据样本不足，暂不采纳',
        inputValidator: (val: string) => {
          if (!val || !val.trim()) return '驳回原因不能为空'
          return true
        },
      },
    )
    note = value
  } catch {
    return
  }
  try {
    await rejectMiningRule(row.id, { note })
    ElMessage.success('已驳回')
    loadRules()
  } catch {
    // 拦截器已统一提示
  }
}

onMounted(() => {
  loadRules()
})
</script>

<style lang="scss" scoped>
/* 页面容器：flex column 撑满父容器（layout__content 已有 overflow: auto）*/
.mining-rule-list {
  padding: 16px;
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  /* 底部 padding：避开 fixed 分页器 */
  padding-bottom: 60px;
}

/* 表格包装层：flex: 1 撑满剩余空间；overflow: hidden 让 el-table 内部独立滚动 */
.table-wrapper {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 分页器（fixed 贴视窗底部）*/
.pagination {
  display: flex;
  justify-content: center;
  position: fixed;
  left: var(--sidebar-width, 220px);
  right: 0;
  bottom: 0;
  z-index: 100;
  padding: 12px 0;
  border-top: 1px solid #ebeef5;
}

/* 等宽字体（规则编号 / 指纹 / 缺陷名）*/
.mono {
  font-family: 'Courier New', Consolas, monospace;
  color: #303133;
}

/* 危险操作按钮 */
.text-danger {
  color: var(--el-color-danger, #f56c6c);
}
</style>
