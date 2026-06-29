from identity.models import User
from masterdata.models import Project
from utils.validation import validate_pk, validate_id_list
from utils.db import build_filters, parse_ordering, paginate_queryset
from utils.code_generator import generate_unique_code
from utils.object_utils import safe_get
from extensions.exceptions import BizException, ERROR_DATA_NOT_FOUND


def create_project(user: User, **kwargs):
    """创建项目"""
    # TODO: 验证 user 操作权限
    kwargs = {
        **kwargs,
        "company_id": user.company_id,
        "organization_id": user.organization_id,
        "project_code": generate_unique_code("PRJ"),
        "source": "manual",
        "created_by": user,
    }
    project = Project.create_with_check(**kwargs)
    return project.to_dict()


def _get_project_by_id(project_id: int) -> Project:
    """根据项目ID获取项目对象"""
    project_id = validate_pk(project_id, "项目ID")
    project = Project.objects.filter(pk=project_id).first()
    if not project:
        raise BizException(ERROR_DATA_NOT_FOUND, "项目信息") # TODO: 抛出异常，补充错误码
    return project


def get_project_info(user: User, project_id: int) -> dict:
    """获取项目信息"""
    # TODO: 验证 user 操作权限

    project = _get_project_by_id(project_id)
    return project.to_dict()


def update_project_info(user: User, project_id: int, **kwargs):
    """更新项目信息"""
    # TODO: 验证 user 操作权限

    project = _get_project_by_id(project_id)
    project.update_info(**kwargs)


def delete_project(user: User, project_id: int):
    """删除项目"""
    # TODO: 验证 user 操作权限
    
    project = _get_project_by_id(project_id)
    project.soft_delete()


def get_project_list(
    user: User,
    project_name: str = None,
    mold_no: str = None,
    initiator: str = None,
    application_industry: str = None,
    initiation_reference: str = None,
    status: str = None,
    importance_level: str = None,
    project_manager: str = None,
    page_no: int = None, 
    page_size: int = None, 
    sort: str = None
):
    """获取项目列表"""
    # TODO: 验证 user 访问权限
    company_id = user.company_id
    
    # 构建查询参数
    filter_map = {
        "company_id": {"input": company_id, "column": "company_id", "lookup": "exact"},
        "project_name": {"input": project_name, "column": "project_name", "lookup": "icontains"},
        "mold_no": {"input": mold_no, "column": "molds__mold_no", "lookup": "icontains"},
        "initiator": {"input": initiator, "column": "initiator", "lookup": "icontains"},
        "initiation_reference": {"input": initiation_reference, "column": "initiation_reference", "lookup": "icontains"},
        "application_industry": {"input": application_industry, "column": "application_industry", "lookup": "icontains"},
        "status": {"input": status, "column": "status", "lookup": "icontains"},
        "importance_level": {"input": importance_level, "column": "importance_level", "lookup": "icontains"},
        "project_manager": {"input": project_manager, "column": "project_manager", "lookup": "icontains"}
    }
    filters = build_filters(filter_map)
    qs = Project.objects.filter(**filters).prefetch_related("molds")
    
    # 排序需求
    sort = sort or "-id"
    ordering = parse_ordering(sort)
    qs = qs.order_by(*ordering)
    
    # 数据分页
    pagination = paginate_queryset(qs, page_no, page_size)
    results = []
    for item in pagination["items"]:
        mold = item.molds.first()
        results.append({
            **item.to_dict(),
            "mold_id": safe_get(mold, "id", None),
            "mold_no": safe_get(mold, "mold_no"),
        })
    total = pagination["total_count"]
    
    return total, results


def batch_delete_project(user: User, ids: list):
    """批量删除项目"""
    ids = validate_id_list(ids, "项目ID列表")
    Project.batch_soft_delete(ids)