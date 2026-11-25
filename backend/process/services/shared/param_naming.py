"""工艺优化 —— ORM 工艺字段的识别与中文标签。

职责边界：只认**ORM 定义的工艺字段**，不取数、不推理、不做命名空间翻译。

【注意】**算法字段名不进来**：算法名（``IV0`` / ``IP0`` / ``MEL``）只在算法
推理内部使用，跨出算法边界的字段名一律是 ORM 业务字段名 ⇒ 本模块只处理后者。

【注意】**判「是不是工艺量」用静态字段字典**（:data:`PROCESS_FIELDS`）——
那是**字段定义**（静态），不是 baseline（某台机的当前值）⇒ 「本机有没有值」
与「是不是工艺量」是两件事。
"""
from typing import FrozenSet, Optional

from process.schemas.parameter import ProcessParameterSchema


#: 列出**工艺字段字典**，即工艺参数表有哪些列，属于静态契约。
PROCESS_FIELDS: FrozenSet[str] = frozenset(ProcessParameterSchema.model_fields)


def is_process_field(param_name: str) -> bool:
    """判断字段名是不是 ORM 定义的工艺字段。

    规则库专用参数（``IPOS`` / ``CUSION``）在 ORM 里没有对应列 ⇒ 不是工艺字段。
    """
    return bool(param_name) and param_name in PROCESS_FIELDS


def to_process_field_name(param_name: str) -> Optional[str]:
    """业务字段名 → 工艺字段名；不是工艺量则返回 None。

    入参应是**业务字段名**（算法名由算法层在出口译好）⇒ 这里只判
    「是不是 ORM 定义的工艺量」。
    """
    if not param_name or not isinstance(param_name, str):
        return None
    return param_name if param_name in PROCESS_FIELDS else None


def param_label(business_name: str) -> str:
    """业务字段名 → 中文标签（取 ProcessParameter 字段的 verbose_name）。

    例：``inj_pres_1`` → ``一段注射压力``。

    建议文案面向的是工艺员，必须用中文标签而不是 ``inj_pres_1`` / ``IP0``。

    【注意】**入参应是 ORM 定义的工艺字段**（先用 :func:`is_process_field` 判）；
    不是工艺字段时**原样返回**（不臆造中文标签）。

    【注意】**ORM 惰性导入**：本模块在算法层的导入链上
    （``optimize_chain/defect_selection`` → ``decide_adjustment`` →
    本模块）⇒ **导入期不能拉 django**
    （``tests/test_fuzzy_algo_offline.py`` 的
    ``test_algorithm_layer_has_no_django_dependency`` 守着这条红线）
    ⇒ ORM 模型只在**函数调用时**导入。
    """
    if not business_name:
        return business_name
    from process.models import ProcessParameter  # 惰性导入：避免导入期拉 ORM
    try:
        return ProcessParameter._meta.get_field(business_name).verbose_name
    except Exception:  # noqa: BLE001 —— 字段不存在 / 非模型字段
        return business_name


__all__ = [
    "PROCESS_FIELDS",
    "is_process_field",
    "param_label",
    "to_process_field_name",
]
