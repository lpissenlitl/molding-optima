from identity.models import User
from masterdata.models import AuxiliaryEquipment
from utils.validation import validate_id_list, validate_pk
from utils.db import build_filters, parse_ordering, paginate_queryset
from extensions.exceptions import BizException, ERROR_DATA_NOT_FOUND


def create_auxiliary_equipment(user: User, **kwargs):
    """创建辅助设备"""
    # TODO: 验证 user 操作权限
    
    # 创建辅助设备信息
    auxiliary_equipment = AuxiliaryEquipment.create_with_check(
        company_id=user.company_id,
        organization_id=user.organization_id,
        **kwargs
    )
    return auxiliary_equipment.to_dict()


def _get_auxiliary_equipment(auxiliary_equipment_id: int) -> AuxiliaryEquipment:
    """获取辅助设备对象"""
    auxiliary_equipment_id = validate_pk(auxiliary_equipment_id, "辅助设备ID")
    auxiliary_equipment = AuxiliaryEquipment.objects.filter(id=auxiliary_equipment_id).first()
    if not auxiliary_equipment:
        raise BizException(ERROR_DATA_NOT_FOUND, "辅助设备不存在") # TODO: 抛出异常，补充错误码
    return auxiliary_equipment


def get_auxiliary_equipment_info(user: User, auxiliary_equipment_id: int) -> dict:
    """获取辅助设备信息"""
    # TODO: 验证 user 操作权限
    
    auxiliary_equipment = _get_auxiliary_equipment(auxiliary_equipment_id)
    return auxiliary_equipment.to_dict()


def update_auxiliary_equipment(user: User, auxiliary_equipment_id: int, **kwargs) -> dict:
    """更新辅助设备信息"""
    # TODO: 验证 user 操作权限
    
    # 更新辅助设备信息
    auxiliary_equipment = _get_auxiliary_equipment(auxiliary_equipment_id)
    auxiliary_equipment.update_info(**kwargs)        


def delete_auxiliary_equipment(user: User, auxiliary_equipment_id: int) -> None:
    """删除辅助设备"""
    # TODO: 验证 user 操作权限
    
    auxiliary_equipment = _get_auxiliary_equipment(auxiliary_equipment_id)
    auxiliary_equipment.soft_delete()
    

def get_auxiliary_equipment_list(
    user: User, 
    name: str = None,
    equipment_name: str = None,
    equipment_type: str = None,
    page_no: int = None,
    page_size: int = None,
    sort: str = None
) -> dict:
    """获取辅助设备列表"""
    # TODO: 验证 user 操作权限
    company_id = user.company_id
    
    filter_map = {
        "company_id": {"input": company_id, "column": "company_id", "lookup": "exact"},
        "name": {"input": name, "column": "name", "lookup": "icontains"},
        "equipment_name": {"input": equipment_name, "column": "equipment_name", "lookup": "icontains"},
        "equipment_type": {"input": equipment_type, "column": "equipment_type", "lookup": "icontains"},
    }
    filters = build_filters(filter_map)
    qs = AuxiliaryEquipment.objects.filter(**filters)
    
    # 排序需求
    sort = sort or "-id"
    ordering = parse_ordering(sort)
    qs = qs.order_by(*ordering)
    
    # 数据分页
    pagination = paginate_queryset(qs, page_no, page_size)
    results = [item.to_dict() for item in pagination["items"]]
    total = pagination["total_count"]
    
    return total, results


def batch_delete_auxiliary_equipment(user: User, ids: list):
    """批量删除辅助设备"""
    # TODO: 验证 user 操作权限
    ids = validate_id_list(ids, "辅助设备ID")
    AuxiliaryEquipment.batch_soft_delete(ids)

