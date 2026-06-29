from masterdata.models import AuxiliaryEquipment
from utils.validation import validate_id_list, validate_pk
from utils.db import build_filters, parse_ordering, paginate_queryset
from extensions.exceptions import BizException, ERROR_DATA_NOT_FOUND


def create_auxiliary_equipment(company_id: int, organization_id: int, **kwargs):
    """创建辅助设备"""
    kwargs["company_id"] = company_id
    kwargs["organization_id"] = organization_id
    auxiliary_equipment = AuxiliaryEquipment.create_with_check(**kwargs)
    return auxiliary_equipment.to_dict()


def _get_auxiliary_equipment(auxiliary_equipment_id: int) -> AuxiliaryEquipment:
    """获取辅助设备对象"""
    auxiliary_equipment_id = validate_pk(auxiliary_equipment_id, "辅助设备ID")
    auxiliary_equipment = AuxiliaryEquipment.objects.filter(id=auxiliary_equipment_id).first()
    if not auxiliary_equipment:
        raise BizException(ERROR_DATA_NOT_FOUND, "辅助设备不存在")
    return auxiliary_equipment


def get_auxiliary_equipment_info(auxiliary_equipment_id: int) -> dict:
    """获取辅助设备信息"""
    auxiliary_equipment = _get_auxiliary_equipment(auxiliary_equipment_id)
    return auxiliary_equipment.to_dict()


def update_auxiliary_equipment(auxiliary_equipment_id: int, **kwargs) -> dict:
    """更新辅助设备信息"""
    auxiliary_equipment = _get_auxiliary_equipment(auxiliary_equipment_id)
    auxiliary_equipment.update_info(**kwargs)
    return auxiliary_equipment.to_dict()


def delete_auxiliary_equipment(auxiliary_equipment_id: int) -> None:
    """删除辅助设备"""
    auxiliary_equipment = _get_auxiliary_equipment(auxiliary_equipment_id)
    auxiliary_equipment.soft_delete()


def get_auxiliary_equipment_list(
    company_id: int,
    name: str = None,
    equipment_name: str = None,
    equipment_type: str = None,
    page_no: int = None,
    page_size: int = None,
    sort: str = None
) -> tuple:
    """获取辅助设备列表"""
    filter_map = {
        "company_id": {"input": company_id, "column": "company_id", "lookup": "exact"},
        "name": {"input": name, "column": "name", "lookup": "icontains"},
        "equipment_name": {"input": equipment_name, "column": "equipment_name", "lookup": "icontains"},
        "equipment_type": {"input": equipment_type, "column": "equipment_type", "lookup": "icontains"},
    }
    filters = build_filters(filter_map)
    qs = AuxiliaryEquipment.objects.filter(**filters)

    # 排序
    ordering = parse_ordering(sort or "-id")
    qs = qs.order_by(*ordering)

    # 分页
    pagination = paginate_queryset(qs, page_no, page_size)
    results = [item.to_dict() for item in pagination["items"]]
    return pagination["total_count"], results


def batch_delete_auxiliary_equipment(ids: list):
    """批量删除辅助设备"""
    ids = validate_id_list(ids, "辅助设备ID")
    AuxiliaryEquipment.batch_soft_delete(ids)

