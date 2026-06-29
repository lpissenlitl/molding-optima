from extensions.exceptions import BizException, ERROR_DATA_NOT_FOUND, ERROR_DATA_FOUND, ERROR_REQUIRED_FIELD
from identity.models import User, company
from masterdata.models import (
    Mold,
    GatingSystem,
    Cavity,
    Gate,
    CoolingSystem,
    EjectionSystem,
)
from django.db import transaction
from utils.validation import validate_pk, validate_id_list
from utils.db import (
    parse_ordering, 
    paginate_queryset, 
    build_filters
)
from masterdata.services.project_service import create_project
from utils.object_utils import safe_get


def check_mold_exist(params: dict, err_msg="模具信息不存在！"):
    filters = {}
    if "mold_id" in params and params["mold_id"]:
        # 如果传递了mold_id，查找mold
        filters["pk"] = params.get("mold_id")
    elif "mold_no" in params:
        # 如果没有传递mold_id，根据模号查是否存在模具信息
        filters["mold_no"] = params.get("mold_no")
    else:
        raise BizException(ERROR_DATA_NOT_FOUND, err_msg)
    # 如果模具信息不存在
    return Mold.objects.filter(**filters).exists()


def create_mold(user: User, **kwargs):
    """创建模具"""
    if "mold_no" not in kwargs or kwargs["mold_no"]== "":
        raise BizException(ERROR_REQUIRED_FIELD, "模具编号必须存在， 且不能为空")
    if Mold.objects.filter(mold_no=kwargs["mold_no"],company=user.company).exists():
        raise BizException(ERROR_DATA_FOUND, f'模具信息 {kwargs["mold_no"]} 已存在，请勿重复添加！')

    #  创建模具信息 TODO：未来可优化，避免深层嵌套
    with transaction.atomic():
        if kwargs.get("project_id", None) is None:
            # 自动创建项目信息，自动补充项目信息
            project_info = create_project(user, is_draft=True)
            kwargs["project_id"] = project_info["id"]
        
        # 创建模具信息
        mold = Mold.create_with_check(
            **kwargs,
            company_id=user.company_id,
            organization_id=user.organization_id,
        )
        
        # 创建浇注系统信息        
        for gating_system_kwargs in kwargs.get("gating_systems", []):
            gating_system = GatingSystem.create_with_check(mold=mold, **gating_system_kwargs)
            for cavity_kwargs in gating_system_kwargs.get("cavities", []):
                cavity = Cavity.create_with_check(gating_system=gating_system, **cavity_kwargs)
                for gate_kwargs in cavity_kwargs.get("gates", []):
                    Gate.create_with_check(cavity=cavity, **gate_kwargs)
        # 创建冷却系统信息
        if "cooling_system" in kwargs:
            CoolingSystem.create_with_check(mold=mold, **kwargs["cooling_system"])
        # 创建顶出系统信息
        if "ejection_system" in kwargs:
            EjectionSystem.create_with_check(mold=mold, **kwargs["ejection_system"])


def _get_mold_by_id(mold_id: int) -> Mold:
    """根据模具ID获取模具对象"""
    mold_id = validate_pk(mold_id, "模具ID")
    mold = Mold.objects.filter(
        pk=mold_id
    ).select_related("project").prefetch_related(
        "gating_systems__cavities__gates",
        "cooling_system", "ejection_system",
    ).first()
    if not mold:
        raise BizException(ERROR_DATA_NOT_FOUND, "模具信息不存在")
    return mold


def get_mold_info(user: User, mold_id: int) -> dict:
    """获取模具信息"""
    # TODO: 验证 user 操作权限
    mold = _get_mold_by_id(mold_id)
    return mold.to_dict(include_rvs=True)


def update_mold_info(user: User, mold_id: int, **kwargs):
    """更新模具信息"""
    # TODO: 验证 user 操作权限
    # TODO: 优化性能：当前为 N+1 查询，未来需改为批量操作 + 预加载
    
    mold = _get_mold_by_id(mold_id)
    
    if Mold.objects.filter(mold_no=kwargs["mold_no"],company=user.company).exclude(id=mold_id).exists():
        raise BizException(ERROR_DATA_FOUND, f'模具信息 {kwargs["mold_no"]} 已存在，请勿重复添加！')

    
    with transaction.atomic():
        mold.update_info(**kwargs)
        # 更新浇注系统信息
        if "gating_systems" in kwargs:
            # 删除不存在的浇注系统
            for gating_system in mold.gating_systems.all():
                if not any(gating_system_kwargs.get("id") == gating_system.id for gating_system_kwargs in kwargs["gating_systems"]):
                    gating_system.delete()
            # 创建/更新浇注系统
            for gating_system_kwargs in kwargs.get("gating_systems", []):
                if "id" in gating_system_kwargs and gating_system_kwargs["id"] is not None:
                    gating_system = GatingSystem.objects.filter(pk=gating_system_kwargs["id"]).first()
                    gating_system.update_info(mold=mold, **gating_system_kwargs)
                else:
                    gating_system = GatingSystem.create_with_check(mold=mold, **gating_system_kwargs)
                # 更新型腔信息
                if "cavities" in gating_system_kwargs:
                    # 删除不存在的型腔
                    for cavity in gating_system.cavities.all():
                        if not any(cavity_kwargs.get("id") == cavity.id for cavity_kwargs in gating_system_kwargs["cavities"]):
                            cavity.delete()
                    # 创建/更新型腔
                    for cavity_kwargs in gating_system_kwargs["cavities"]:
                        if "id" in cavity_kwargs and cavity_kwargs["id"] is not None:
                            cavity = Cavity.objects.filter(pk=cavity_kwargs["id"]).first()
                            cavity.update_info(gating_system=gating_system, **cavity_kwargs)
                        else:
                            cavity = Cavity.create_with_check(gating_system=gating_system, **cavity_kwargs)
                        # 更新浇口信息
                        if "gates" in cavity_kwargs:
                            # 删除不存在的浇口
                            for gate in cavity.gates.all():
                                if not any(gate_kwargs.get("id") == gate.id for gate_kwargs in cavity_kwargs["gates"]):
                                    gate.delete()
                            # 创建/更新浇口
                            for gate_kwargs in cavity_kwargs["gates"]:
                                if "id" in gate_kwargs:
                                    gate = Gate.objects.filter(pk=gate_kwargs["id"]).first()
                                    gate.update_info(cavity=cavity, **gate_kwargs)
                                else:
                                    Gate.create_with_check(cavity=cavity, **gate_kwargs)
            # 更新冷却系统信息
            if "cooling_system" in kwargs:
                CoolingSystem.update_or_create_with_check(mold=mold, **kwargs["cooling_system"])
                
            # 更新顶出系统信息
            if "ejection_system" in kwargs:
                EjectionSystem.update_or_create_with_check(mold=mold, **kwargs["ejection_system"])


def delete_mold(user: User, mold_id: int):
    """删除模具"""
    # TODO: 验证 user 操作权限
    
    mold = _get_mold_by_id(mold_id)
    mold.soft_delete()


def get_mold_list(
    user: User, 
    mold_no: str = None,
    mold_name: str = None,
    category: str = None,
    structure: str = None,
    cavity_layout: str = None,
    status: str = None,
    page_no: int = None, 
    page_size: int = None, 
    sort: str = None,
):
    """获取模具列表"""
    # 构建查询参数
    filter_map = {
        "company_id": {"input": user.company_id, "column": "company_id", "lookup": "exact"},
        "mold_no": {"input": mold_no, "column": "mold_no", "lookup": "icontains"},
        "mold_name": {"input": mold_name, "column": "mold_name", "lookup": "icontains"},
        "category": {"input": category, "column": "category", "lookup": "icontains"},
        "structure": {"input": structure, "column": "structure", "lookup": "exact"},
        "cavity_layout": {"input": cavity_layout, "column": "cavity_layout", "lookup": "exact"},
        "status": {"input": status, "column": "status", "lookup": "exact"},
    }
    
    filters = build_filters(filter_map)
    qs = Mold.objects.filter(**filters)
    
    # 排序需求
    sort = sort or "-id"
    ordering = parse_ordering(sort)
    qs = qs.order_by(*ordering)
    
    # 数据分页
    pagination = paginate_queryset(qs, page_no, page_size)
    results = [item.to_dict() for item in pagination["items"]]
    total = pagination["total_count"]
    
    return total, results
    

def batch_delete_mold(user: User, ids: list):
    """批量删除模具"""
    ids = validate_id_list(ids, "模具ID列表")
    Mold.batch_soft_delete(ids)

                    

    
