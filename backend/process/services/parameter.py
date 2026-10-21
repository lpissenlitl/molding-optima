"""
工艺参数服务（parameter service）

业务核心实体：ProcessParameter（工艺参数 / 调机轮次）
依附实体：ProcessCondition（工艺条件）

业务模型：
- parameter 是 condition 的子资源，必须依附 condition（ForeignKey）
- parameter 之间通过 parent_param 自关联，构成版本树
- seq_idx 在同一父节点下递增（全局自增也保留语义：condition 内创建顺序）

软删管理器约定（extensions.models.BaseModel）：
- objects        = SoftDeleteManager，get_queryset() 已自动过滤 is_deleted=False
- all_objects    = 普通 Manager，不过滤软删记录
因此：
- 查未删除记录 → 用 .objects，无需再显式写 is_deleted=False
- 需跨越软删边界（如查“已删记录本身”）→ 用 .all_objects，此时才需显式加 is_deleted 条件
- 例外：跨表 join 过滤（filter(related__field=...)）走 _base_manager（普通 Manager），
  不会自动排除软删，需显式写 related__is_deleted=False（见 condition.py 的用法）

应用场景 (B 方案简化后, 2026-10-10):
- 单段 GET 详情       按 parameter_id 查单条 (供前端只读使用)
- 按 condition_id 查树  查 condition 下所有 parameter 的版本树
- 双段写操作          update_parameter_in_condition / delete_parameter_in_condition
                     (URL 含 condition_id + parameter_id, 校验 belongs_to)

已删函数 (2026-10-10):
- update_parameter / delete_parameter / batch_delete_parameter
  (写操作必须走双段 + belongs_to 校验)

设计原则：
- 写操作 (update/delete) 统一走双段 service (XXX_parameter_in_condition)
- 单段 API 只提供 GET 详情 (无副作用)
- 关系字段（process_condition / parent_param / seq_idx）不允许通过本服务修改
- 版本树查询不影响数据（只读）
"""
import logging
from datetime import date, datetime, time
from typing import Dict, Any, List, Tuple

from django.db import transaction
from django.db.models import Max, Q

from extensions.exceptions import (
    BizException, ERROR_DATA_NOT_FOUND, ERROR_ILLEGAL_ARGUMENT,
)
from process.models import ProcessParameter, ProcessCondition
from utils.db import build_filters, parse_ordering, paginate_queryset

_logger = logging.getLogger(__name__)


# ============================================================================
# 业务身份锁：不允许通过 update_parameter 修改的字段
# ============================================================================
# 与 condition.py 的 CONDITION_LOCKED_FIELDS 同一范式（白名单式 allow_fields 扣除）。
#
# 分类依据：
# - 主关联：参数归属的工艺条件，改挂等于换业务对象
# - 调机树：parent_param 父链 + seq_idx 版本序号（由 model.save() 自动分配）
# - 系统生成：parameter_no 编号
# - 来源标记：param_source 记录本轮参数的产生方式，字段编辑不应改变它
# - 软删标记：走 delete_parameter 专用路径
PARAMETER_LOCKED_FIELDS = frozenset({
    # 主键
    "id",
    # 主关联
    "process_condition",
    "process_condition_id",
    # 调机树结构
    "parent_param",
    "parent_param_id",
    "seq_idx",
    # 系统生成
    "parameter_no",
    # 来源标记
    "param_source",
    # 软删标记
    "is_deleted",
    "deleted_at",
})


# ============================================================================
# 私有工具函数
# ============================================================================

def _get_parameter_by_id(parameter_id: int) -> ProcessParameter:
    """获取工艺参数对象（带 condition + parent 预加载）

    Raises:
        BizException: 工艺参数不存在
    """
    try:
        return ProcessParameter.all_objects.select_related(
            "process_condition",
            "parent_param",
        ).get(id=parameter_id, is_deleted=False)
    except ProcessParameter.DoesNotExist:
        raise BizException(ERROR_DATA_NOT_FOUND, f"工艺参数不存在: id={parameter_id}")


def _serializable_parameter_dict(parameter: ProcessParameter) -> dict:
    """构造返回的 parameter 字典

    注：to_dict() 已处理主字段；这里补上 parent_param_id（FK 转 _id）。
    """
    data = parameter.to_dict()
    # to_dict() 已经把 process_condition_id 暴露为 process_condition_id
    # 但 parent_param 可能被 to_dict() 排除（反向关系）；手动补
    if "parent_param_id" not in data:
        data["parent_param_id"] = parameter.parent_param_id
    return data


# ============================================================================
# 单条 CRUD（按 parameter_id）
# ============================================================================


# ============================================================================
# 版本树查询（只读）
# ============================================================================

def get_parameter_tree(condition_id: int = None) -> List[dict]:
    """获取版本树（树形结构） - 2026-10-12 URL 拆除双段嵌套

    业务: 工艺优化页 / 工艺详情页展示调机历史树。

    2026-10-12 改造:
    - 旧: get_parameter_tree(condition_id) (condition 必填)
    - 新: get_parameter_tree(condition_id=None) (condition 退化为可选过滤)
      - condition_id 传 -> 过滤该 condition 下的 parameter 构造树
      - condition_id 不传 -> 查全表构造树 (后台 / 集成 API 场景)

    Args:
        condition_id: 工艺条件 ID (可选)

    Returns:
        list: 根节点列表（每个节点含 children 字段递归子树）
            [
                {
                    "id": 1,
                    "seq_idx": 1,
                    "parent_param_id": None,
                    "param_source": "algorithm_init",
                    "created_at": "2026-10-09 ...",
                    "updated_at": "2026-10-09 ...",
                    "children": [...]
                }
            ]
    """
    # condition_id 仅在传时才校验存在 (过滤前预检, 避免空结果歧义)
    if condition_id is not None and not ProcessCondition.objects.filter(
        id=condition_id
    ).exists():
        raise BizException(ERROR_DATA_NOT_FOUND, f"工艺条件不存在: id={condition_id}")

    # 一次性查出所有 parameter（按 seq_idx, id 排序——便于稳定遍历）
    qs = ProcessParameter.objects.all()
    if condition_id is not None:
        qs = qs.filter(process_condition_id=condition_id)
    parameters = qs.order_by("seq_idx", "id").values(
        "id", "seq_idx", "parent_param_id", "param_source",
        "created_at", "updated_at",
    )

    # 构造节点字典
    nodes = {}
    for param in parameters:
        nodes[param["id"]] = {
            "id": param["id"],
            "seq_idx": param["seq_idx"],
            "parent_param_id": param["parent_param_id"],
            "param_source": param["param_source"],
            "created_at": param["created_at"],
            "updated_at": param["updated_at"],
            "children": [],
        }

    # 构造树（O(N) 单次遍历）
    roots = []
    for node in nodes.values():
        parent_id = node["parent_param_id"]
        if parent_id and parent_id in nodes:
            nodes[parent_id]["children"].append(node)
        else:
            # parent 不存在（已删除或孤立）→ 作为 root
            roots.append(node)

    return roots


# ============================================================================
# parameter 独立服务 (2026-10-12 URL 拆除双段嵌套)
# parameter 是独立业务对象, URL 不再嵌套在 /conditions/<id>/parameters/ 之下
# - service 函数一律不带 _in_condition 后缀
# - condition_id 退化为可选过滤条件 (列查询 / 树查询 场景)
# - 单条 CRUD 仅凭 parameter_id 定位, 不需 condition_id
# ============================================================================


def list_parameters(
    condition_id: int = None,
    parent_seq_idx: int = None,
    seq_idx: int = None,
    param_code: str = None,
    param_source: str = None,
    created_after: date = None,
    created_before: date = None,
    sort: str = None,
    page_no: int = None,
    page_size: int = None,
) -> Tuple[int, List[dict]]:
    """列出 parameter (B 方案 GET 端点用, 2026-10-12 加过滤+分页)

    2026-10-12 改造:
    - 旧: list_parameters_by_condition(condition_id) (condition 必填)
    - 新: list_parameters(condition_id=None) (condition 退化为过滤条件, 可选)
      - condition_id 传 -> 过滤该 condition 下的 parameter
      - condition_id 不传 -> 查全表 (后台 / 集成 API 场景)

    与 get_parameter_tree 的区别:
    - 本函数返回平铺列表 (用于参数详情页列出全部版本)
    - get_parameter_tree 返回树形结构 (用于调机树展示)

    与 records list 风格一致: 过滤 (param_source / seq_idx / time range) + 分页。

    Args:
        condition_id:   工艺条件 ID (可选, 不传 = 查全表)
        parent_seq_idx: 按父参数业务编号过滤 (调机树定位场景)
        seq_idx:        按序列序号过滤 (找特定版本)
        param_code:     工艺参数编号 (icontains 模糊匹配)
        param_source:   参数来源 (manual / algorithm_init / system_inferred / ...)
        created_after:  创建起始日期
        created_before: 创建结束日期
        sort:           排序规则 (+字段 升 / -字段 降, 多字段逗号分隔, 默认 -id)
        page_no:        页码 (默认 1)
        page_size:      每页数量 (默认 30, max 1000)

    Returns:
        (total, items) 元组, 由 view 包装为 PaginationResponse

    Raises:
        BizException: condition_id 存在但 condition 不存在
    """
    # condition_id 仅在传时才校验存在 (过滤前预检, 避免返回空结果歧义)
    if condition_id is not None and not ProcessCondition.objects.filter(
        id=condition_id, is_deleted=False
    ).exists():
        raise BizException(ERROR_DATA_NOT_FOUND, f"工艺条件不存在: id={condition_id}")

    # 过滤映射
    filter_map = {
        "parent_seq_idx": {"input": parent_seq_idx, "column": "parent_seq_idx", "lookup": "exact"},
        "seq_idx":        {"input": seq_idx,        "column": "seq_idx",        "lookup": "exact"},
        "param_code":     {"input": param_code,     "column": "param_code",     "lookup": "icontains"},
        "param_source":   {"input": param_source,   "column": "param_source",   "lookup": "exact"},
    }
    filter_kwargs = build_filters(filter_map)

    # 只列未删除记录：objects 是 SoftDeleteManager（自动过滤 is_deleted=False）；
    # all_objects 是普通 Manager，会把已删版本一并返回
    qs = ProcessParameter.objects.filter(**filter_kwargs)
    if condition_id is not None:
        qs = qs.filter(process_condition_id=condition_id)

    # 创建时间区间
    if created_after is not None or created_before is not None:
        date_filters = Q()
        if created_after is not None:
            date_filters &= Q(created_at__gte=datetime.combine(created_after, time.min))
        if created_before is not None:
            date_filters &= Q(created_at__lte=datetime.combine(created_before, time.max))
        qs = qs.filter(date_filters)

    # 排序
    ordering = parse_ordering(sort or "-id")
    qs = qs.order_by(*ordering)

    # 分页
    pagination = paginate_queryset(qs, page_no, page_size)
    return (
        pagination["total_count"],
        [_serializable_parameter_dict(p) for p in pagination["items"]],
    )


def get_parameter(parameter_id: int) -> dict:
    """获取指定 parameter (B 方案 GET 详情端点用)

    2026-10-12 改造:
    - 旧: get_parameter_in_condition(condition_id, parameter_id) (双段强校验)
    - 新: get_parameter(parameter_id) (仅凭 ID 定位, parameter.process_condition_id 自带)

    区别于 condition.get_condition(condition_id)：
    - condition.get_condition 返回 condition + 最新 parameter
    - 本函数返回**具体某一条** parameter（任意版本）

    Returns:
        dict: parameter 序列化字典（含 process_condition_id / parent_param_id / seq_idx 等）

    Raises:
        BizException: parameter 不存在或已软删
    """
    parameter_obj = _get_parameter_by_id(parameter_id)
    return _serializable_parameter_dict(parameter_obj)


def update_parameter(parameter_id: int, parameter: dict) -> dict:
    """更新指定 parameter (B 方案 PUT 端点用)

    2026-10-12 改造:
    - 旧: update_parameter_in_condition(condition_id, parameter_id, parameter)
    - 新: update_parameter(parameter_id, parameter)

    parameter 自适应两种格式, 由本函数智能识别:
    - 含 'setting_process' key → NEST (前端 UI 格式), 调 _frontend_to_condition_dict 转 FLAT
    - 否则 → FLAT 92 字段 (算法/移植直传), 透传给 parameter.update_info

    两者都经 PARAMETER_LOCKED_FIELDS 过滤：关系字段 / 版本序号 / 来源标记
    不允许通过本服务修改（见模块 docstring 设计原则）。

    Returns:
        dict: 更新后的 parameter 序列化字典

    Raises:
        BizException: parameter 不存在 / parameter.setting_process 为空
    """
    parameter_obj = ProcessParameter.all_objects.filter(id=parameter_id).first()
    if not parameter_obj:
        raise BizException(
            ERROR_DATA_NOT_FOUND,
            f"parameter 不存在: id={parameter_id}",
        )

    if not parameter:
        raise BizException(ERROR_ILLEGAL_ARGUMENT, "parameter 不能为空")

    # 智能识别: 有 setting_process → NEST, 否则 → FLAT
    if "setting_process" in parameter:
        setting_process = parameter["setting_process"]
        if not setting_process:
            raise BizException(
                ERROR_ILLEGAL_ARGUMENT,
                "parameter.setting_process 不能为空 (NEST 透传需含 5 段设置)",
            )
        # 局部 import 避免循环引用
        from process.services.condition import _frontend_to_condition_dict
        parameter_kwargs = _frontend_to_condition_dict(setting_process)
    else:
        parameter_kwargs = parameter

    # 业务身份锁：白名单式扣除受保护字段
    allowed_fields = ProcessParameter.get_allowed_fields() - PARAMETER_LOCKED_FIELDS
    parameter_obj.update_info(allow_fields=allowed_fields, **parameter_kwargs)
    return _serializable_parameter_dict(parameter_obj)


def delete_parameter(parameter_id: int) -> None:
    """软删指定 parameter (B 方案 DELETE 端点用)

    2026-10-12 改造:
    - 旧: delete_parameter_in_condition(condition_id, parameter_id)
    - 新: delete_parameter(parameter_id)

    调机树完整性：存在未删除子节点时拒绝删除——否则子节点会被 get_parameter_tree
    当作孤儿“提根”，丢失其版本归属。需先删子节点。
    """
    parameter_obj = ProcessParameter.all_objects.filter(id=parameter_id).first()
    if not parameter_obj:
        raise BizException(
            ERROR_DATA_NOT_FOUND,
            f"parameter 不存在: id={parameter_id}",
        )

    has_children = ProcessParameter.objects.filter(
        parent_param_id=parameter_id,
    ).exists()
    if has_children:
        raise BizException(
            ERROR_ILLEGAL_ARGUMENT,
            f"该工艺参数存在子版本，请先删除子版本: id={parameter_id}",
        )

    parameter_obj.soft_delete()
