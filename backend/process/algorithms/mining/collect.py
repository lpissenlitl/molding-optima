"""数据库来源的样本采集器 —— 从调机流水提炼训练样本。

与 `samples.py::FileSampleRepository`（文件来源）实现同一个
`MiningSampleRepository` 协议 ⇒ 两个来源可互换，挖掘内核无感知。

⚠️ **源侧数据与样本的映射**
    `TuningRecord.adjustments` 本就是「规范化训练样本」（见模型注释），
    结构与 `SampleRecord` 几乎一一对应：

    | adjustments             | SampleRecord |
    |-------------------------|--------------|
    | `defects`               | `defects`    |
    | `changes[]`             | `changes[]`  |
    | `result`（模型字段）     | `label`      |

⚠️ **只收「已出结果 + 有变更」的样本**
    - `result` 为 pending 的轮次没有结论 ⇒ 不构成证据
    - 无变更的轮次没有可学习的动作 ⇒ 挖不出任何规则
    这两个判定统一由 `SampleRecord.is_usable()` 承担 ⇒ 语料里不掺不可用样本。

    ⚠️ **不要求有缺陷**：合格态的产品没有缺陷（业务规则会清空缺陷反馈），
    若强制「有缺陷」，所有合格样本都会被丢弃 ⇒ 语料只剩不合格样本。

⚠️ **模型 import 放在方法内**
    本模块被 `mining/__init__.py` 导出，若在模块顶层 import `process.models`，
    未 `setup()` 的离线 runner 会因 AppRegistryNotReady 崩掉 ⇒ 模型延迟导入。
"""

from typing import Dict, List, Optional

from .contracts import VALID_LABELS, SampleRecord
from .samples import format_sample_id, parse_sample_id


#: 样本 id 前缀（调机记录）
SAMPLE_PREFIX = 'tr'


class TuningRecordCollector:
    """从调机流水采集训练样本（数据库来源）。

    满足 `MiningSampleRepository` 协议 ⇒ 可与文件来源互换。
    """

    def __init__(self, company_id: Optional[int] = None):
        """
        Args:
            company_id: 公司 id；None 表示不按公司过滤（仅本地排查用）。
        """
        self.company_id = company_id

    # --- 取用契约 ---

    def get_samples(self, since: Optional[str] = None) -> List[SampleRecord]:
        """取训练样本列表（按 `sample_id` 升序）。

        Args:
            since: 增量游标 —— 只返回 `sample_id` 严格大于该值的样本。

        Returns:
            可用样本列表（`is_usable()` 为真的那些）。
        """
        from process.models.tuning_record import TuningRecord

        queryset = TuningRecord.objects.filter(result__in=VALID_LABELS)
        if self.company_id is not None:
            queryset = queryset.filter(company_id=self.company_id)

        since_id = parse_sample_id(since)
        if since_id is not None:
            queryset = queryset.filter(id__gt=since_id)

        queryset = queryset.select_related(
            'process_parameter__process_condition__polymer',
        ).order_by('id')

        samples: List[SampleRecord] = []
        for record in queryset:
            sample = self._to_sample(record)
            if sample.is_usable():
                samples.append(sample)
        return samples

    # --- 内部 ---

    def _to_sample(self, record) -> SampleRecord:
        """调机记录 → 样本档案。"""
        adjustments = record.adjustments or {}

        # ⚠️ **缺陷与等级同源于 `defect_feedbacks`**
        #    （每项 = ``keyword_name`` + ``level``）⇒ 合成一项取，天然不会错配。
        #    ⚠️ 不取 `adjustments['defects']` 作名单：那是缺陷名的**快照**
        #       （`build_adjustments` 只投影名字、丢掉了 level），
        #       且 `TuningService.add_defect_feedback` 直接追写缺陷反馈时
        #       **不重算 adjustments** ⇒ 两者会滞后不一致。
        #    ⚠️ 合格态的样本没有缺陷 ⇒ 该列表为空，属正常。
        defects: List[Dict] = []
        for feedback in (record.defect_feedbacks or []):
            if not isinstance(feedback, dict):
                continue
            name = feedback.get('keyword_name')
            if not name:
                continue
            defects.append({
                'name': str(name),
                'level': str(feedback.get('level') or ''),
            })

        changes: List[Dict] = []
        for raw in adjustments.get('changes') or []:
            if not isinstance(raw, dict):
                continue
            changes.append({
                'param': raw.get('param'),
                'direction': raw.get('direction'),
                'before': raw.get('before'),
                'after': raw.get('after'),
            })

        parameter = record.process_parameter
        condition = parameter.process_condition if parameter else None
        context = {
            'polymer': (
                condition.polymer.abbreviation
                if condition and condition.polymer else ''
            ),
            'condition_no': condition.condition_no if condition else '',
            'parameter_no': parameter.parameter_no if parameter else '',
            'iteration': (
                (adjustments.get('tuning_context') or {}).get('iteration')
            ),
        }

        return SampleRecord(
            sample_id=format_sample_id(SAMPLE_PREFIX, record.id),
            defects=defects,
            changes=changes,
            label=record.result,
            context=context,
            source_ref=f'tuning_record:{record.id}',
        )


__all__ = [
    'TuningRecordCollector',
    'SAMPLE_PREFIX',
]
