"""
molding-optima 工艺记录 service

基于 ProcessCondition 的 CRUD 包装。
"""
from django.db import transaction

from extensions.exceptions import BizException, ERROR_DATA_NOT_FOUND
from process.models import ProcessCondition


def get_process_record(condition_id):
    """获取工艺记录详情"""
    record = ProcessCondition.objects.filter(
        id=condition_id,
        is_deleted=False,
    ).first()
    if not record:
        raise BizException(ERROR_DATA_NOT_FOUND, f"工艺记录不存在: id={condition_id}")
    return record.to_dict()


@transaction.atomic
def add_process_record(company_id, organization_id, **params):
    """添加工艺记录"""
    params["company_id"] = company_id
    if organization_id:
        params["organization_id"] = organization_id
    return ProcessCondition.create_with_check(**params).to_dict()


@transaction.atomic
def update_process_record(condition_id, **params):
    """更新工艺记录"""
    record = ProcessCondition.objects.filter(
        id=condition_id,
        is_deleted=False,
    ).first()
    if not record:
        raise BizException(ERROR_DATA_NOT_FOUND, f"工艺记录不存在: id={condition_id}")
    record.update_info(**params)
    return record.to_dict()


@transaction.atomic
def delete_process_record(condition_id):
    """删除工艺记录（软删除）"""
    record = ProcessCondition.objects.filter(
        id=condition_id,
        is_deleted=False,
    ).first()
    if not record:
        raise BizException(ERROR_DATA_NOT_FOUND, f"工艺记录不存在: id={condition_id}")
    record.soft_delete()
    return {"deleted_id": condition_id}