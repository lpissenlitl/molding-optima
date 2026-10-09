"""
工艺参数服务（parameter service）

业务核心实体：ProcessParameter（工艺参数 / 调机轮次）
依附实体：ProcessCondition（工艺条件）

业务模型：
- parameter 是 condition 的子资源，必须依附 condition（ForeignKey）
- parameter 之间通过 parent_param 自关联，构成版本树
- seq_idx 在同一父节点下递增（全局自增也保留语义：condition 内创建顺序）

应用场景：
- 单条 parameter CRUD（按 parameter_id）—— 与 condition.py 的"按 condition_id 操作"区分
- 版本树查询（按 condition_id / parameter_id）
- 手动版本管理（用户不走算法，纯手动微调字段创建新版本）

设计原则：
- 本服务专注于"按 parameter_id 操作"具体的某一条 parameter
- 关系字段（process_condition / parent_param / seq_idx）不允许通过本服务修改
- 版本树查询不影响数据（只读）
- 手动版本管理走事务，保证 seq_idx + parent_param 一致性

合并历史：
- 2026-10-09：独立出来。原 parameter.py 的所有函数都按 condition_id 操作（命名误导），
  已合并入 condition.py。本文件专门处理"按 parameter_id 操作"和版本树管理。
"""
import logging
from datetime import datetime
from typing import Dict, Any, List

from django.db import transaction
from django.db.models import Max

from extensions.exceptions import (
    BizException, ERROR_DATA_NOT_FOUND, ERROR_ILLEGAL_ARGUMENT,
)
from process.models import ProcessParameter, ProcessCondition

_logger = logging.getLogger(__name__)


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

def get_parameter(parameter_id: int) -> dict:
    """获取工艺参数详情（按 parameter_id）

    区别于 condition.get_condition(condition_id)：
    - condition.get_condition 返回 condition + 最新 parameter
    - 本函数返回**具体某一条** parameter（任意版本）

    Args:
        parameter_id: 工艺参数 ID

    Returns:
        dict: 工艺参数详情（含 process_condition_id, parent_param_id, seq_idx 等）
    """
    parameter = _get_parameter_by_id(parameter_id)
    return _serializable_parameter_dict(parameter)


@transaction.atomic
def update_parameter(parameter_id: int, **kwargs) -> dict:
    """更新工艺参数字段（不影响 condition 和其他 parameter）

    区别于 condition.update_condition(condition_id, ...):
    - condition.update_condition 修改 condition 字段 + 最新一条 parameter
    - 本函数修改**任意指定** parameter（不影响 condition 字段）

    禁止通过本接口修改关系字段（id / process_condition / parent_param / seq_idx），
    防止破坏版本树结构。

    Args:
        parameter_id: 工艺参数 ID
        **kwargs: 待更新的字段（白名单自动过滤非法字段）

    Returns:
        dict: 更新后的工艺参数
    """
    parameter = _get_parameter_by_id(parameter_id)

    # 过滤禁止字段（防止破坏关系 / 时间戳 / 主键）
    forbidden_fields = {
        "id", "process_condition", "process_condition_id",
        "parent_param", "parent_param_id", "seq_idx",
        "created_at", "updated_at", "is_deleted", "deleted_at",
        "parameter_no",
    }
    clean_kwargs = {k: v for k, v in kwargs.items() if k not in forbidden_fields}

    if not clean_kwargs:
        raise BizException(
            ERROR_ILLEGAL_ARGUMENT,
            "update_parameter: 至少需要一个可更新字段",
        )

    parameter.update_info(**clean_kwargs)
    _logger.info(
        "[parameter] update_parameter: id=%s, fields=%s",
        parameter_id, sorted(clean_kwargs.keys()),
    )
    return _serializable_parameter_dict(parameter)


@transaction.atomic
def delete_parameter(parameter_id: int) -> None:
    """删除单条工艺参数（不影响 condition 和其他 parameter）

    业务场景：删除某个无效的调整版本（保留历史链中的其他版本）。

    Args:
        parameter_id: 工艺参数 ID

    注：若该 parameter 有后代（children），删除后后代的 parent_param_id 仍指向
        已删除的 record。这会造成"孤儿后代"。调用前请确认无 children 或预期承担。
    """
    parameter = _get_parameter_by_id(parameter_id)

    # 防御——有 children 时不允许直接删除（避免孤儿）
    has_children = ProcessParameter.objects.filter(
        parent_param_id=parameter_id,
        is_deleted=False,
    ).exists()
    if has_children:
        raise BizException(
            ERROR_ILLEGAL_ARGUMENT,
            f"工艺参数 id={parameter_id} 有未删除的后代版本，不允许直接删除。"
            f"请先处理后代或使用软删除标记。",
        )

    parameter.soft_delete()
    _logger.info("[parameter] delete_parameter: id=%s", parameter_id)


# ============================================================================
# 版本树查询（只读）
# ============================================================================

def get_parameter_tree(condition_id: int) -> List[dict]:
    """获取工艺条件下的版本树（树形结构）

    业务：工艺优化页 / 工艺详情页展示调机历史树。

    Args:
        condition_id: 工艺条件 ID

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
                    "children": [
                        {
                            "id": 2,
                            "seq_idx": 2,
                            "parent_param_id": 1,
                            "param_source": "ai_recommended",
                            "created_at": "...",
                            "children": [...]
                        }
                    ]
                }
            ]
    """
    if not ProcessCondition.objects.filter(id=condition_id, is_deleted=False).exists():
        raise BizException(ERROR_DATA_NOT_FOUND, f"工艺条件不存在: id={condition_id}")

    # 一次性查出所有 parameter（按 seq_idx, id 排序——便于稳定遍历）
    parameters = ProcessParameter.objects.filter(
        process_condition_id=condition_id,
        is_deleted=False,
    ).order_by("seq_idx", "id").values(
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


