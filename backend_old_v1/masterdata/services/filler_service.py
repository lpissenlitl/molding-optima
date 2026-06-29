from identity.models import User
from masterdata.models import Filler
from utils.validation import validate_id_list, validate_pk
from utils.db import build_filters, parse_ordering, paginate_queryset
from extensions.exceptions import BizException, ERROR_DATA_NOT_FOUND


def create_filler(user: User, **kwargs):
    """创建填充物"""
    # TODO: 验证 user 操作权限
    kwargs = {
        "company_id": user.company_id,
        "organization_id": user.organization_id,
        **kwargs
    }
    # 创建填充物信息
    filler = Filler.create_with_check(**kwargs)
    return filler.to_dict()


def _get_filler_by_id(filler_id: int) -> Filler:
    """通过 id 获取填充物对象"""
    filler_id = validate_pk(filler_id, "填充物ID")
    filler = Filler.objects.filter(id=filler_id).first()
    if not filler:
        raise BizException(ERROR_DATA_NOT_FOUND, "填充物不存在") # TODO: 抛出异常，补充错误码
    return filler


def get_filler_info(user: User, filler_id: int) -> dict:
    """获取填充物信息"""
    # TODO: 验证 user 操作权限
    
    filler = _get_filler_by_id(filler_id)
    return filler.to_dict()


def update_filler_info(user: User, filler_id: int, **kwargs) -> dict:
    """更新填充物信息"""
    # TODO: 验证 user 操作权限
    
    filler = _get_filler_by_id(filler_id)
    filler.update_info(**kwargs)


def delete_filler(user: User, filler_id: int) -> None:
    """删除填充物"""
    # TODO: 验证 user 操作权限
    
    filler = _get_filler_by_id(filler_id)
    filler.soft_delete()


def get_filler_list(
    user: User, 
    name: str = None,
    category: str = None,
    shape: str = None,
    color: str = None,
    abbreviation: str = None,
    page_no: int = None,
    page_size: int = None,
    sort: str = None
):
    """获取填充物成材列表"""
    # TODO: 验证 user 操作权限
    company_id = user.company_id
    # 构建查询参数
    filter_map = {
        "company_id": {"input": company_id, "column": "company_id", "lookup": "exact"},
        "name": {"input": name, "column": "name", "lookup": "icontains"},
        "category": {"input": category, "column": "category", "lookup": "icontains"},
        "shape": {"input": shape, "column": "shape", "lookup": "icontains"},
        "color": {"input": color, "column": "color", "lookup": "icontains"},
        "abbreviation": {"input": abbreviation, "column": "abbreviation", "lookup": "icontains"},
    }
    filters = build_filters(filter_map)
    qs = Filler.objects.filter(**filters)
    
    # 排序需求
    sort = sort or "-id"
    ordering = parse_ordering(sort)
    qs = qs.order_by(*ordering)
    
    # 数据分页
    pagination = paginate_queryset(qs, page_no, page_size)
    result = [item.to_dict() for item in pagination["items"]]
    total = pagination["total_count"]
    
    return total, result


def batch_delete_filler(user: User, ids: list) -> int:
    """批量删除填充物"""
    # TODO: 验证 user 操作权限
    
    ids = validate_id_list(ids)
    Filler.batch_soft_delete(ids)