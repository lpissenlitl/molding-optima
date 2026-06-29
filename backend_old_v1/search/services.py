from extensions.exceptions import BizException, ERROR_ILLEGAL_ARGUMENT
from masterdata.models import (
    Project,
    Mold,
    Polymer,
    Filler,
    InjectionMoldingMachine,
    AuxiliaryEquipment
)
from schedule.models import (
    Reservation,
    MasterSchedule
)
from identity.models import (
    User,
    Company,
    Role
)
from inventory.models import (
    Material,
    MaterialStock,
    MaterialRequisition,
    MaterialRequisitionLine,
    MaterialPurchaseLine,
    MaterialStockHistory
)
from identity.permissions import (
    CompanyPermission,
    UserPermission,
    RolePermission,
    OrganizationPermission,
)
from moldflow.models import MoldflowResult
from notice.models import NoticeTemplate, NoticeRecord

MODEL_CLS_MAP = {
    "project": Project,
    "mold": Mold,
    "polymer": Polymer,
    "filler": Filler,
    "injection_molding_machine": InjectionMoldingMachine,
    "auxiliary_equipment": AuxiliaryEquipment,
    "reservation": Reservation,
    "schedule": MasterSchedule,
    "company": Company,
    "user": User,
    "role": Role,
    "material": Material,
    "material_stock": MaterialStock,
    "material_requisition": MaterialRequisition,
    "material_requisition_line": MaterialRequisitionLine,
    "material_purchase_line": MaterialPurchaseLine,
    "material_stock_history": MaterialStockHistory,
    "moldflow_result": MoldflowResult,
    "notice_template": NoticeTemplate,
    "notice_record": NoticeRecord,
}


def get_doc_cls_by_name(cls_name):
    """根据模型名获取对应的模型类"""
    if cls_name not in MODEL_CLS_MAP.keys():
        raise BizException(ERROR_ILLEGAL_ARGUMENT, f"Invalid model name: {cls_name}, please check search configuration")
    return MODEL_CLS_MAP.get(cls_name)

PERM_CLS_MAP = {
    "user": {
        "permission_class": UserPermission,
        "method_name": '_can_read_user_list',
        "method_kwargs": {
            "permission_code": 'review_user'
        },
    },
    "role": {
        "permission_class": RolePermission,
        "method_name": '_can_get_role',
        "method_kwargs": {
        },
    },
}

def get_perm_dic_by_name(cls_name):
    """根据模型名获取对应的权限类"""
    if cls_name not in PERM_CLS_MAP.keys():
        # raise BizException(ERROR_ILLEGAL_ARGUMENT, f"Invalid model name: {cls_name}, please check search configuration")
        return None # 暂时
    return PERM_CLS_MAP.get(cls_name)


def get_prompt_list_of_column(user: User, **params) -> list[dict[str, object]]:
    """
    通用下拉提示服务，支持多租户隔离，可处理子表查找主表company_id。
    
    Args:
        user: 当前用户
        table: 目标模型名（字符串）
        via: 可选，Django 风格的关联路径，用于反向过滤（如 "product" 或 "category__product"）,找到子表对应的company_id
        其他参数透传给模型的 get_prompt_list_of_column

    示例:
    # 场景1：直接有 company_id
    get_prompt_list_of_column(user, table="Product", column="name", input="手机")

    # 场景2：通过一层外键查找company_id（Category ← Product）
    get_prompt_list_of_column(user, table="Category", column="name", input="电", via="product")

    # 场景3：通过两层外键查找company_id（Brand ← Category ← Product）
    get_prompt_list_of_column(user, table="Brand", column="name", input="苹", via="category__product")
    """
    table_name: str = params.pop("table")
    via: str | None = params.pop("via", None)

    cls = get_doc_cls_by_name(table_name)

    # 白名单：公共表，无需租户隔离
    PUBLIC_TABLES = {"company"}

    if table_name in PUBLIC_TABLES:
        extra_filters = {}
    elif hasattr(cls, "company_id"):
        extra_filters = {"company_id": user.company_id}
    elif via:
        extra_filters = {f"{via}__company_id": user.company_id}
    else:
        raise PermissionError(
            f"Access denied: Table '{table_name}' is not tenant-aware "
            f"and not in public whitelist. Provide 'via' or add to PUBLIC_TABLES."
        )

    perm_dic = get_perm_dic_by_name(table_name)
    
    if perm_dic:
        perm_cls = perm_dic.get("permission_class")
        permMethod = getattr(perm_cls(user), perm_dic.get("method_name"))
        method_kwargs = perm_dic.get("method_kwargs")
        if not permMethod(company_id=user.company_id, **method_kwargs):
            return []
    return cls.get_prompt_list_of_column(
        extra_filters=extra_filters,
        **params,
    )