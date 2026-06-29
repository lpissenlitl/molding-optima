"""
molding-optima 规则管理 service

提供 RuleKeyword 和 RuleMethod 的 CRUD + 列表查询。
RuleFlowDoc（MongoDB 流程图）相关功能暂不引入。
"""
import logging

from django.db import transaction

from extensions.exceptions import BizException, ERROR_DATA_NOT_FOUND
from process.models import RuleKeyword, RuleMethod
from utils.db import paginate_queryset, parse_ordering

_logger = logging.getLogger(__name__)


# ==================== RuleKeyword ====================

def get_rule_keyword(rule_keyword_id):
    """获取规则关键字详情"""
    rule = RuleKeyword.objects.filter(
        id=rule_keyword_id, is_deleted=False,
    ).first()
    if not rule:
        raise BizException(ERROR_DATA_NOT_FOUND, "该关键字不存在")
    return rule.to_dict()


@transaction.atomic
def add_rule_keyword(company_id, organization_id, **params):
    """新增规则关键字"""
    params["company_id"] = company_id
    if organization_id:
        params["organization_id"] = organization_id
    return RuleKeyword.create_with_check(**params).to_dict()


@transaction.atomic
def update_rule_keyword(rule_keyword_id, **params):
    """更新规则关键字"""
    rule = RuleKeyword.objects.filter(
        id=rule_keyword_id, is_deleted=False,
    ).first()
    if not rule:
        raise BizException(ERROR_DATA_NOT_FOUND, "该关键字不存在")
    rule.update_info(**params)
    return rule.to_dict()


@transaction.atomic
def delete_rule_keyword(rule_keyword_id):
    """删除规则关键字（软删除）"""
    rule = RuleKeyword.objects.filter(
        id=rule_keyword_id, is_deleted=False,
    ).first()
    if not rule:
        raise BizException(ERROR_DATA_NOT_FOUND, "该关键字不存在")
    rule.soft_delete()


def get_list_of_rule_keyword(
    name=None,
    keyword_type=None,
    show_on_page=None,
    subrule_no=None,
    page_no=1,
    page_size=30,
    sort="-id",
):
    """获取规则关键字列表"""
    qs = RuleKeyword.objects.filter(is_deleted=False)

    if name:
        qs = qs.filter(name__icontains=name)
    if keyword_type:
        qs = qs.filter(keyword_type=keyword_type)
    if show_on_page is not None:
        qs = qs.filter(show_on_page=show_on_page)
    if subrule_no:
        qs = qs.filter(subrule_no=subrule_no)

    qs = qs.order_by(*parse_ordering(sort or "-id"))
    pagination = paginate_queryset(qs, page_no, page_size)
    items = [item.to_dict() for item in pagination["items"]]

    return {
        "total": pagination["total_count"],
        "items": items,
    }


# ==================== RuleMethod ====================

def get_rule_method(rule_method_id):
    """获取规则方法详情"""
    rule = RuleMethod.objects.filter(
        id=rule_method_id, is_deleted=False,
    ).first()
    if not rule:
        raise BizException(ERROR_DATA_NOT_FOUND, "该规则方法不存在")
    return rule.to_dict()


@transaction.atomic
def add_rule_method(company_id, organization_id, **params):
    """新增规则方法"""
    params["company_id"] = company_id
    if organization_id:
        params["organization_id"] = organization_id
    return RuleMethod.create_with_check(**params).to_dict()


@transaction.atomic
def update_rule_method(rule_method_id, **params):
    """更新规则方法"""
    rule = RuleMethod.objects.filter(
        id=rule_method_id, is_deleted=False,
    ).first()
    if not rule:
        raise BizException(ERROR_DATA_NOT_FOUND, "该规则方法不存在")
    rule.update_info(**params)
    return rule.to_dict()


@transaction.atomic
def delete_rule_method(rule_method_id):
    """删除规则方法（软删除）"""
    rule = RuleMethod.objects.filter(
        id=rule_method_id, is_deleted=False,
    ).first()
    if not rule:
        raise BizException(ERROR_DATA_NOT_FOUND, "该规则方法不存在")
    rule.soft_delete()


def get_list_of_rule_method(
    defect_name=None,
    subrule_no=None,
    rule_type=None,
    enable=None,
    page_no=1,
    page_size=30,
    sort="-priority",
):
    """获取规则方法列表"""
    qs = RuleMethod.objects.filter(is_deleted=False)

    if defect_name:
        qs = qs.filter(defect_name__icontains=defect_name)
    if subrule_no:
        qs = qs.filter(subrule_no=subrule_no)
    if rule_type:
        qs = qs.filter(rule_type=rule_type)
    if enable is not None:
        qs = qs.filter(enable=enable)

    qs = qs.order_by(*parse_ordering(sort or "-priority"))
    pagination = paginate_queryset(qs, page_no, page_size)
    items = [item.to_dict() for item in pagination["items"]]

    return {
        "total": pagination["total_count"],
        "items": items,
    }


def get_rules_by_defect(defect_name):
    """根据缺陷名获取所有启用的规则（按优先级排序）"""
    rules = RuleMethod.objects.filter(
        defect_name=defect_name,
        enable=1,
        is_deleted=False,
    ).order_by("-priority")
    return [r.to_dict() for r in rules]


def get_keywords_by_subrule(subrule_no, keyword_type=None):
    """根据子规则编号获取所有关键字"""
    qs = RuleKeyword.objects.filter(
        subrule_no=subrule_no,
        is_deleted=False,
    )
    if keyword_type:
        qs = qs.filter(keyword_type=keyword_type)
    return [k.to_dict() for k in qs.order_by("name")]