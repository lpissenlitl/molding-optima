"""
molding-optima 工艺参数服务

参考 molding-expert 的 service 拆分模式（class-based service），
实现工艺条件的 CRUD、参数移植等基础操作。
第二阶段将从 old/ 提炼工艺优化/初始化/专家调优等核心算法。
"""
from django.db import transaction
from django.db.models import Max
from extensions.exceptions import BizException, ERROR_DATA_NOT_FOUND, ERROR_REQUIRED_FIELD, ERROR_ILLEGAL_ARGUMENT

from process.models import ProcessCondition, ProcessParameter


# ==================== ProcessCondition ====================

def _create_process_condition(company_id, organization_id, **kwargs):
    """
    创建工艺条件
    """
    if not company_id:
        raise BizException(ERROR_REQUIRED_FIELD, "company_id is required")

    # 过滤只允许的字段
    allowed_fields = ProcessCondition.get_allowed_fields()
    cleaned = {k: v for k, v in kwargs.items() if k in allowed_fields}

    cleaned["company_id"] = company_id
    if organization_id:
        cleaned["organization_id"] = organization_id

    return ProcessCondition.create_with_check(**cleaned)


def _get_process_condition_by_id(condition_id):
    """获取工艺条件"""
    if not condition_id:
        raise BizException(ERROR_ILLEGAL_ARGUMENT, "condition_id is required")

    condition = ProcessCondition.objects.filter(
        id=condition_id, is_deleted=False,
    ).first()

    if not condition:
        raise BizException(ERROR_DATA_NOT_FOUND, f"工艺条件不存在: id={condition_id}")

    return condition


def update_process_condition(condition_id, **kwargs):
    """更新工艺条件"""
    condition = _get_process_condition_by_id(condition_id)
    condition.update_info(**kwargs)
    return condition


def soft_delete_process_condition(condition_id):
    """软删除工艺条件（级联删除其参数）"""
    condition = _get_process_condition_by_id(condition_id)
    with transaction.atomic():
        condition.soft_delete()
        ProcessParameter.all_objects.filter(
            process_condition=condition, is_deleted=False,
        ).update(is_deleted=True, updated_at=condition.updated_at, deleted_at=condition.updated_at)


def get_process_condition_list(
    status=None,
    origin_type=None,
    mold_id=None,
    injection_machine_id=None,
    polymer_id=None,
    page_no=1,
    page_size=30,
    sort="-id",
):
    """获取工艺条件列表"""
    qs = ProcessCondition.objects.filter(is_deleted=False)

    if status:
        qs = qs.filter(status=status)
    if origin_type:
        qs = qs.filter(origin_type=origin_type)
    if mold_id:
        qs = qs.filter(mold_id=mold_id)
    if injection_machine_id:
        qs = qs.filter(injection_machine_id=injection_machine_id)
    if polymer_id:
        qs = qs.filter(polymer_id=polymer_id)

    from utils.db import parse_ordering, paginate_queryset
    qs = qs.order_by(*parse_ordering(sort or "-id"))
    pagination = paginate_queryset(qs, page_no, page_size)

    items = [item.to_dict(include_rvs=False) for item in pagination["items"]]
    return {
        "total": pagination["total_count"],
        "items": items,
    }


# ==================== ProcessParameter ====================

def create_process_parameter(company_id, organization_id, **kwargs):
    """
    创建工艺参数
    必须传入 process_condition_id
    """
    if not company_id:
        raise BizException(ERROR_REQUIRED_FIELD, "company_id is required")

    process_condition_id = kwargs.pop("process_condition_id", None)
    if not process_condition_id:
        raise BizException(ERROR_REQUIRED_FIELD, "process_condition_id is required")

    # 校验工艺条件存在
    condition = _get_process_condition_by_id(process_condition_id)

    # 自动计算 seq_idx（如果未指定）
    if not kwargs.get("seq_idx"):
        last_idx = ProcessParameter.all_objects.filter(
            process_condition=condition,
        ).aggregate(Max("seq_idx"))["seq_idx__max"] or 0
        kwargs["seq_idx"] = last_idx + 1

    # 过滤字段
    allowed_fields = ProcessParameter.get_allowed_fields()
    cleaned = {k: v for k, v in kwargs.items() if k in allowed_fields}
    cleaned["process_condition_id"] = condition.id
    cleaned["company_id"] = company_id
    if organization_id:
        cleaned["organization_id"] = organization_id

    return ProcessParameter.create_with_check(**cleaned)


def _construct_return_parameter(condition):
    """构造工艺条件的参数返回结构"""
    params = list(
        condition.process_parameters.filter(is_deleted=False).order_by("seq_idx")
    )
    return {
        "condition": condition.to_dict(),
        "parameters": [p.to_dict() for p in params],
    }


def get_process_parameter(condition_id):
    """获取工艺条件及其参数（树形）"""
    condition = _get_process_condition_by_id(condition_id)
    return _construct_return_parameter(condition)


def update_process_parameter(parameter_id, **kwargs):
    """更新工艺参数"""
    parameter = ProcessParameter.objects.filter(
        id=parameter_id, is_deleted=False,
    ).first()

    if not parameter:
        raise BizException(ERROR_DATA_NOT_FOUND, f"工艺参数不存在: id={parameter_id}")

    parameter.update_info(**kwargs)
    return parameter


def delete_process_parameter(parameter_id):
    """软删除工艺参数"""
    parameter = ProcessParameter.objects.filter(
        id=parameter_id, is_deleted=False,
    ).first()

    if not parameter:
        raise BizException(ERROR_DATA_NOT_FOUND, f"工艺参数不存在: id={parameter_id}")

    parameter.soft_delete()
    return parameter


def get_process_parameter_list(
    status=None,
    origin_type=None,
    mold_id=None,
    injection_machine_id=None,
    polymer_id=None,
    page_no=1,
    page_size=30,
    sort="-id",
):
    """获取工艺参数列表（带条件过滤）"""
    # 先过滤工艺条件
    cond_qs = ProcessCondition.objects.filter(is_deleted=False)
    if status:
        cond_qs = cond_qs.filter(status=status)
    if origin_type:
        cond_qs = cond_qs.filter(origin_type=origin_type)
    if mold_id:
        cond_qs = cond_qs.filter(mold_id=mold_id)
    if injection_machine_id:
        cond_qs = cond_qs.filter(injection_machine_id=injection_machine_id)
    if polymer_id:
        cond_qs = cond_qs.filter(polymer_id=polymer_id)

    condition_ids = list(cond_qs.values_list("id", flat=True))

    qs = ProcessParameter.objects.filter(
        is_deleted=False,
        process_condition_id__in=condition_ids,
    ).select_related("process_condition")

    from utils.db import parse_ordering, paginate_queryset
    qs = qs.order_by(*parse_ordering(sort or "-id"))
    pagination = paginate_queryset(qs, page_no, page_size)

    items = [item.to_dict() for item in pagination["items"]]
    return {
        "total": pagination["total_count"],
        "items": items,
    }


def batch_delete_process_parameter(ids):
    """批量软删除工艺参数"""
    if not ids:
        raise BizException(ERROR_ILLEGAL_ARGUMENT, "ids must not be empty")

    deleted_count = ProcessParameter.batch_soft_delete(list(ids))
    return {"deleted_count": deleted_count}


# ==================== Process Transplant（参数移植占位）====================

def transplant_process_parameter(source_condition_id, target_context):
    """
    工艺参数移植（占位实现）。

    第二阶段将从 old/ 提炼机台适配算法（machine_adaption_service），
    当前仅返回基本结构。
    """
    source = _get_process_condition_by_id(source_condition_id)
    source_params = list(
        source.process_parameters.filter(is_deleted=False).order_by("seq_idx")
    )

    # 阶段 1 占位：直接复制参数
    return {
        "source_condition_id": source_condition_id,
        "target_context": target_context,
        "parameters_count": len(source_params),
        "message": "阶段 1 占位实现；算法将在第二阶段实现",
    }


# ==================== Frontend / Flat 视图（迁移自 molding-expert）====================
from process.services.process_transformer import (
    _transform_frontend_to_flat,
    _construct_setting_process_frontend,
)


def get_process_parameter_flat(condition_id):
    """获取工艺参数（扁平格式，对齐 molding-expert）"""
    condition = _get_process_condition_by_id(condition_id)
    parameter = condition.process_parameters.filter(is_deleted=False).first()
    if not parameter:
        raise BizException(ERROR_DATA_NOT_FOUND, "工艺参数不存在")
    return parameter.to_dict()


def get_process_parameter_frontend(condition_id):
    """获取工艺参数（前端嵌套格式，对齐 molding-expert）"""
    condition = _get_process_condition_by_id(condition_id)
    parameter = condition.process_parameters.filter(is_deleted=False).first()
    if not parameter:
        raise BizException(ERROR_DATA_NOT_FOUND, "工艺参数不存在")

    injection_unit = None
    if getattr(condition, "injection_unit_id", None):
        try:
            from masterdata.models import InjectionUnit
            injection_unit = InjectionUnit.objects.get(id=condition.injection_unit_id)
        except Exception:
            pass

    return {
        "condition": {
            "id": condition.id,
            "mold_info": condition.mold.to_dict(include_rvs=True) if condition.mold else None,
            "shot_index": condition.shot_index,
            "machine_info": condition.injection_machine.to_dict(include_rvs=True) if condition.injection_machine else None,
            "injection_index": condition.injection_index,
            "injection_unit": injection_unit.to_dict() if injection_unit else None,
            "polymer_info": condition.polymer.to_dict(include_rvs=True) if condition.polymer else None,
        },
        "parameter": {
            "setting_process": _construct_setting_process_frontend(parameter, injection_unit),
        },
    }


def create_process_parameter_frontend(company_id, organization_id, **kwargs):
    """创建工艺参数（前端嵌套结构，对齐 molding-expert /parameter/frontend/）"""
    condition_kwargs = kwargs.get("condition")
    parameter_nested = kwargs.get("parameter", {})
    setting_process = parameter_nested.get("setting_process")

    if not condition_kwargs:
        raise BizException(ERROR_ILLEGAL_ARGUMENT, "请确定工艺条件信息存在")
    if not setting_process:
        raise BizException(ERROR_ILLEGAL_ARGUMENT, "请确定工艺参数信息存在")

    # 转换前端嵌套结构为扁平字段
    flat = _transform_frontend_to_flat(setting_process)

    # 过滤 ProcessParameter 允许的字段
    allowed = ProcessParameter.get_allowed_fields()
    cleaned = {k: v for k, v in flat.items() if k in allowed}

    condition = _create_process_condition(company_id, organization_id, **condition_kwargs)
    cleaned["process_condition_id"] = condition.id
    cleaned["company_id"] = company_id
    if organization_id:
        cleaned["organization_id"] = organization_id

    ProcessParameter.create_with_check(**cleaned)
    return get_process_parameter_frontend(condition.id)


def update_process_parameter_frontend(condition_id, **kwargs):
    """更新工艺参数（前端嵌套结构，对齐 molding-expert /parameter/<id>/frontend/）"""
    condition = _get_process_condition_by_id(condition_id)

    if "condition" in kwargs:
        condition.update_info(**kwargs["condition"])

    if "parameter" in kwargs:
        parameter_nested = kwargs["parameter"]
        setting_process = parameter_nested.get("setting_process")
        if setting_process:
            flat = _transform_frontend_to_flat(setting_process)
            allowed = ProcessParameter.get_allowed_fields()
            parameter_kwargs = {k: v for k, v in flat.items() if k in allowed}
            parameter = condition.process_parameters.filter(is_deleted=False).first()
            if parameter:
                parameter.update_info(**parameter_kwargs)

    return get_process_parameter_frontend(condition_id)