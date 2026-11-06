"""候选规则审核流视图 —— 列表 / 详情 / 通过 / 驳回。

URL 段:
- processes/mining-rules/                        候选规则列表（审核台）
- processes/mining-rules/<id>/                   候选规则详情（含落地预览）
- processes/mining-rules/<id>/approve/           通过 ⇒ 落地为生效规则
- processes/mining-rules/<id>/reject/            驳回

⚠️ **四个端点全部要求管理员**（`require_admin`：超管 || 租户管理员）
    —— 候选规则是**统计关联**，未经人工确认就写进生效规则库等于把
    「相关性」当成「工艺因果」使用；驳回/通过会直接改变试模推荐行为，
    因此这条业务线**整体不对普通用户开放**。
"""

from django.utils.decorators import method_decorator

from extensions.decorators import validate_parameters
from extensions.schemas import PaginationBaseSchema
from extensions.views import BaseView, PaginationResponse
from identity.decorators import require_admin

from process.services import mining_review


def _reviewer_name(request) -> str:
    """审核人姓名（优先工程师姓名，其次用户名）。"""
    user = getattr(request, 'user', None)
    if user is None:
        return ''
    return (
        getattr(user, 'engineer_name', None)
        or getattr(user, 'username', '')
        or ''
    )


# ----- 候选规则 (mining-rules) -----

@method_decorator(require_admin, name="dispatch")
class MiningRuleListView(BaseView):
    """候选规则列表（审核台）

    GET 可选 query:
    - status       按审核态过滤（pending / approved / rejected）
    - consequent  按后件过滤（qualified / unqualified / improved / worse）
    - keyword      规则编号模糊搜索
    - 其余分页参数 page_no / page_size / sort
    """

    @method_decorator(validate_parameters(PaginationBaseSchema))
    def get(self, request, cleaned_data):
        result = mining_review.get_mining_rule_list(
            company_id=getattr(request.user, "company_id", None),
            is_superuser=getattr(request.user, "is_superuser", False),
            status=request.GET.get("status"),
            consequent=request.GET.get("consequent"),
            keyword=request.GET.get("keyword"),
            **cleaned_data,
        )
        return PaginationResponse(total=result["total"], items=result["items"])


@method_decorator(require_admin, name="dispatch")
class MiningRuleDetailView(BaseView):
    """候选规则详情（挖掘指标 + 证据样本 + 落地预览）"""

    def get(self, request, mining_rule_id):
        return mining_review.get_mining_rule_detail(
            mining_rule_id,
            company_id=getattr(request.user, "company_id", None),
            is_superuser=getattr(request.user, "is_superuser", False),
        )


@method_decorator(require_admin, name="dispatch")
class MiningRuleApproveView(BaseView):
    """通过候选规则 ⇒ 落地为生效规则（RuleMethod, source='rule_miner'）

    POST body:
    - note  审核意见（可选）
    """

    def post(self, request, mining_rule_id):
        data = request.DATA or {}
        return mining_review.approve_mining_rule(
            mining_rule_id,
            company_id=getattr(request.user, "company_id", None),
            is_superuser=getattr(request.user, "is_superuser", False),
            reviewer=_reviewer_name(request),
            note=data.get("note") or "",
        )


@method_decorator(require_admin, name="dispatch")
class MiningRuleRejectView(BaseView):
    """驳回候选规则

    POST body:
    - note  审核意见（**必填**）
    """

    def post(self, request, mining_rule_id):
        data = request.DATA or {}
        return mining_review.reject_mining_rule(
            mining_rule_id,
            company_id=getattr(request.user, "company_id", None),
            is_superuser=getattr(request.user, "is_superuser", False),
            reviewer=_reviewer_name(request),
            note=data.get("note") or "",
        )
