from identity.models import User
from masterdata.models import Project
from utils.validation import validate_pk, validate_id_list
from utils.db import build_filters, parse_ordering, paginate_queryset
from utils.code_generator import generate_unique_code
from utils.object_utils import safe_get
from extensions.exceptions import BizException, ERROR_DATA_NOT_FOUND


def create_project(company_id: int, organization_id: int, operator: User = None, **kwargs):
    """
    创建项目
    operator: 操作人（审计字段 created_by），可选
    """
    kwargs.setdefault("project_code", generate_unique_code("PRJ"))
    kwargs.setdefault("source", "manual")
    kwargs.setdefault("created_by", operator)
    kwargs["company_id"] = company_id
    kwargs["organization_id"] = organization_id
    project = Project.create_with_check(**kwargs)
    return project.to_dict()


def _get_project_by_id(project_id: int) -> Project:
    """根据项目ID获取项目对象"""
    project_id = validate_pk(project_id, "项目ID")
    project = Project.objects.filter(pk=project_id).first()
    if not project:
        raise BizException(ERROR_DATA_NOT_FOUND, "项目信息不存在")
    return project


def get_project_info(project_id: int) -> dict:
    """获取项目信息"""
    project = _get_project_by_id(project_id)
    return project.to_dict()


def update_project_info(project_id: int, **kwargs) -> dict:
    """更新项目信息"""
    project = _get_project_by_id(project_id)
    project.update_info(**kwargs)
    return project.to_dict()


def delete_project(project_id: int) -> None:
    """删除项目"""
    project = _get_project_by_id(project_id)
    project.soft_delete()


def get_project_list(
    company_id: int,
    project_code: str = None,
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
) -> tuple:
    """获取项目列表"""
    filter_map = {
        "company_id": {"input": company_id, "column": "company_id", "lookup": "exact"},
        "project_code": {"input": project_code, "column": "project_code", "lookup": "icontains"},
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

    # 排序
    ordering = parse_ordering(sort or "-id")
    qs = qs.order_by(*ordering)

    # 分页
    pagination = paginate_queryset(qs, page_no, page_size)
    results = []
    for item in pagination["items"]:
        mold = item.molds.first()
        results.append({
            **item.to_dict(),
            "mold_id": safe_get(mold, "id", None),
            "mold_no": safe_get(mold, "mold_no"),
        })
    return pagination["total_count"], results


def batch_delete_project(ids: list) -> None:
    """批量删除项目"""
    ids = validate_id_list(ids, "项目ID")
    Project.batch_soft_delete(ids)