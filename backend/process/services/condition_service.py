"""
工艺基础服务

提供 ProcessCondition 和 ProcessParameter 的基础 CRUD 操作
"""

from typing import Optional

from django.db import transaction

from process.models import ProcessCondition, ProcessParameter


class ProcessService:
    """工艺基础服务"""

    @staticmethod
    def create_condition(
        mold_id: int = None,
        injection_machine_id: int = None,
        polymer_id: int = None,
        shot_index: int = None,
        injection_index: int = None,
        condition_code: str = None,
        origin_type: str = 'manual_creation',
        status: str = 'draft',
    ) -> ProcessCondition:
        """创建工艺条件"""
        condition = ProcessCondition.objects.create(
            mold_id=mold_id,
            injection_machine_id=injection_machine_id,
            polymer_id=polymer_id,
            shot_index=shot_index,
            injection_index=injection_index,
            condition_code=condition_code,
            origin_type=origin_type,
            status=status,
        )
        return condition

    @staticmethod
    def get_condition(condition_id: int) -> Optional[ProcessCondition]:
        """获取工艺条件"""
        try:
            return ProcessCondition.objects.get(id=condition_id)
        except ProcessCondition.DoesNotExist:
            return None

    @staticmethod
    def create_parameter(
        condition: ProcessCondition,
        parent_param: ProcessParameter = None,
        param_source: str = 'manual',
        **kwargs
    ) -> ProcessParameter:
        """创建工艺参数"""
        with transaction.atomic():
            parameter = ProcessParameter.objects.create(
                process_condition=condition,
                parent_param=parent_param,
                param_source=param_source,
                **kwargs
            )
        return parameter

    @staticmethod
    def get_latest_parameter(condition: ProcessCondition) -> Optional[ProcessParameter]:
        """获取最新版本的工艺参数"""
        return ProcessParameter.objects.filter(
            process_condition=condition,
            is_deleted=False
        ).order_by('-seq_idx').first()

    @staticmethod
    def get_parameter_tree(parameter: ProcessParameter) -> dict:
        """
        获取参数版本树

        返回格式：
        {
            "current": {...},
            "parent": {...},
            "children": [...]
        }
        """
        return {
            'current': parameter,
            'parent': parameter.parent_param,
            'children': list(parameter.children.filter(is_deleted=False)),
        }

    @staticmethod
    def create_child_parameter(
        parent: ProcessParameter,
        param_source: str = 'manual_adjusted',
        **kwargs
    ) -> ProcessParameter:
        """创建子版本参数"""
        return ProcessService.create_parameter(
            condition=parent.process_condition,
            parent_param=parent,
            param_source=param_source,
            **kwargs
        )

    @staticmethod
    def get_parameter_version_path(parameter: ProcessParameter) -> list:
        """
        获取参数版本路径（从根到当前）

        例如: [v1, v1.1, v1.1.2]
        """
        path = []
        current = parameter
        while current is not None:
            path.insert(0, current)
            current = current.parent_param
        return path
