"""
调参记录服务

提供 TuningRecord 的 CRUD 操作和趋势分析
"""

from dataclasses import dataclass
from typing import List, Optional
from collections import Counter

from process.models import TuningRecord, ProcessParameter


class ProcessTuningService:
    """调参记录服务"""

    @staticmethod
    def create_tuning_record(
        parameter: ProcessParameter,
        defect_feedbacks: List[dict] = None,
        result: str = 'pending',
        result_detail: str = None,
        previous_parameter: dict = None,
    ) -> TuningRecord:
        """
        创建调参记录

        业务说明：
        - 本方法通常由业务层调用，同步创建 TuningRecord 与 parameter
        - previous_parameter 通常在创建时为空，由 infer/manual-adjust 后续填充

        Args:
            parameter: 工艺参数
            defect_feedbacks: 缺陷反馈列表
            result: 试模结果 (pending/improved/worse/unchanged/qualified/unqualified)
            result_detail: 结果详情，描述具体效果
            previous_parameter: 调整前的参数快照（OLD parameter.parameters）

        Returns:
            TuningRecord 实例
        """
        if defect_feedbacks is None:
            defect_feedbacks = []

        return TuningRecord.objects.create(
            process_parameter=parameter,
            defect_feedbacks=defect_feedbacks,
            result=result,
            result_detail=result_detail,
            previous_parameter=previous_parameter,
        )

    @staticmethod
    def _build_parameter_snapshot(parameter: ProcessParameter) -> dict:
        """
        从 ProcessParameter 构建快照

        Deprecated：
        - 本方法仅作为工具方法保留
        - 创建 TuningRecord 时不再自动调用（previous_parameter 为空）
        - infer/manual-adjust 调用时应直接从 parameter.parameters 获取快照
        """
        snapshot = {}
        for field in parameter._meta.fields:
            field_name = field.name
            if field_name.startswith('_') or field_name in ['id', 'created_at', 'updated_at', 'deleted']:
                continue
            value = getattr(parameter, field_name, None)
            if value is not None:
                snapshot[field_name] = value
        return snapshot

    @staticmethod
    def get_tuning_records(parameter: ProcessParameter) -> List[TuningRecord]:
        """获取参数的所有调参记录"""
        return list(TuningRecord.objects.filter(
            process_parameter=parameter
        ).order_by('-created_at'))

    @staticmethod
    def get_latest_record(parameter: ProcessParameter) -> Optional[TuningRecord]:
        """获取最新的调参记录"""
        return TuningRecord.objects.filter(
            process_parameter=parameter
        ).order_by('-created_at').first()

    @staticmethod
    def update_tuning_result(
        record: TuningRecord,
        result: str,
        result_detail: str = None,
    ) -> TuningRecord:
        """
        更新试模结果

        备注：
        - 原 note 参数已移除（被 adjustments 取代）
        - adjustments 是系统自动生成的，不允许用户手工修改
        """
        record.result = result
        if result_detail:
            record.result_detail = result_detail
        record.save()
        return record

    @staticmethod
    def add_defect_feedback(
        record: TuningRecord,
        defect_feedback: dict
    ) -> TuningRecord:
        """
        添加缺陷反馈

        Args:
            record: 调参记录
            defect_feedback: 缺陷反馈 dict（与前端 DefectFeedbackData 对齐）
                {
                    "keyword_id": 15,
                    "keyword_name": "短射",
                    "level": "high",           # 动态档位（3/5/7 档）
                    "position": "DLWELDLINE3", # DL${defect_name}${segment}
                    "position_3d": null
                }
        """
        feedbacks = record.defect_feedbacks or []
        feedbacks.append(defect_feedback)
        record.defect_feedbacks = feedbacks
        record.save()
        return record

    @staticmethod
    def get_successful_records(
        condition_id: int = None,
        parameter_id: int = None,
        limit: int = None
    ) -> List[TuningRecord]:
        """
        获取成功的调参记录

        用于规则学习
        """
        queryset = TuningRecord.objects.filter(result='qualified')
        if parameter_id:
            queryset = queryset.filter(process_parameter_id=parameter_id)
        if condition_id:
            queryset = queryset.filter(process_parameter__process_condition_id=condition_id)

        queryset = queryset.order_by('-created_at')
        if limit:
            queryset = queryset[:limit]

        return list(queryset)

    @staticmethod
    def get_defect_summary(parameter: ProcessParameter) -> dict:
        """
        获取缺陷汇总

        返回格式：
        {
            "total": 5,
            "defects": {
                "短射": 2,
                "飞边": 3
            },
            "levels": {
                "low": 1,
                "medium": 2,
                "high": 2
            }
        }
        """
        records = ProcessTuningService.get_tuning_records(parameter)

        summary = {
            'total': len(records),
            'defects': {},
            'levels': {},
        }

        for record in records:
            for defect in (record.defect_feedbacks or []):
                # 与前端 DefectFeedbackData 对齐：使用 keyword_name 而非 defect_type
                defect_name = defect.get('keyword_name') or defect.get('defect_type', 'unknown')
                level = defect.get('level', 'unknown')

                summary['defects'][defect_name] = summary['defects'].get(defect_name, 0) + 1
                summary['levels'][level] = summary['levels'].get(level, 0) + 1

        return summary

    @staticmethod
    @dataclass
    class IterationTrend:
        """
        迭代趋势分析结果

        Attributes:
            trend: 趋势方向 (improving/worsening/stable/final)
            improving: 改善次数
            worsening: 恶化次数
            unchanged: 无变化次数
            last_result: 最近一次结果
            recommendation: 策略建议
        """
        trend: str
        improving: int
        worsening: int
        unchanged: int
        last_result: str
        recommendation: str

    @staticmethod
    def analyze_iteration_trend(parameter: ProcessParameter) -> 'ProcessTuningService.IterationTrend':
        """
        分析迭代趋势

        基于历史调参记录分析趋势，用于指导引擎选择策略：
        - improving: 持续改善，继续当前方向
        - worsening: 持续恶化，需回退或换策略
        - stable: 改善/恶化交替，陷入僵局
        - final: 已达终态（qualified/unqualified）

        Returns:
            IterationTrend 对象
        """
        records = ProcessTuningService.get_tuning_records(parameter)

        # 只分析已验证的记录
        validated_records = [r for r in records if r.result != 'pending']

        if not validated_records:
            return ProcessTuningService.IterationTrend(
                trend='unknown',
                improving=0,
                worsening=0,
                unchanged=0,
                last_result='pending',
                recommendation='等待首次试模结果'
            )

        # 统计各类结果
        results = [r.result for r in validated_records]
        counter = Counter(results)

        improving = counter.get('improved', 0)
        worsening = counter.get('worse', 0)
        unchanged = counter.get('unchanged', 0)
        last_result = validated_records[0].result  # 按 -created_at 排序的第一个

        # 判断终态
        if last_result in ('qualified', 'unqualified'):
            trend = 'final'
            recommendation = '已达成终态，无需继续调参' if last_result == 'qualified' else '当前方案无效，需更换策略'
        # 判断趋势
        elif improving > worsening and improving >= 2:
            trend = 'improving'
            recommendation = '趋势向好，继续当前调整方向，可适当加大调整幅度'
        elif worsening > improving and worsening >= 2:
            trend = 'worsening'
            recommendation = '趋势恶化，建议回退参数或更换调整策略'
        elif worsening > 0 and improving == 0:
            trend = 'worsening'
            recommendation = '调整方向错误，建议回退参数并分析原因'
        elif unchanged > improving + worsening:
            trend = 'stable'
            recommendation = '调整效果不明显，建议改变策略或检查设备状态'
        else:
            trend = 'stable'
            recommendation = '趋势不明朗，建议维持当前策略观察'

        return ProcessTuningService.IterationTrend(
            trend=trend,
            improving=improving,
            worsening=worsening,
            unchanged=unchanged,
            last_result=last_result,
            recommendation=recommendation
        )
