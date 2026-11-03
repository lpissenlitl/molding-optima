"""
molding-optima reporting app 工具函数（精简）
保留 build_export_list_path；移除 mold_trial 相关函数（molding-optima 不引入试模）。
"""
import os
import re
from django.conf import settings
from extensions.exceptions import BizException, ERROR_DATA_NOT_FOUND, ERROR_ILLEGAL_ARGUMENT

# 导出文件存放子目录（相对 {STORE_PATH}/{tenant_slug}）
EXPORT_LIST_DIR = "archives/export_lists"


def build_export_list_path(
    tenant_slug: str,
    template_name: str,
    ext: str = "xlsx",
):
    """
    构建导出文件的存储路径：
        {STORE_PATH}/{tenant_slug}/archives/export_lists/{template_name}.{ext}
    """
    if not tenant_slug or not template_name or not ext:
        raise BizException(ERROR_ILLEGAL_ARGUMENT, "tenant_slug, template_name, ext are required")

    if not re.fullmatch(r"[a-zA-Z0-9_-]+", tenant_slug):
        raise BizException(ERROR_ILLEGAL_ARGUMENT, f"Invalid tenant_slug: {tenant_slug!r}")

    relative_path = f"{EXPORT_LIST_DIR}/{template_name}.{ext}"
    full_path = os.path.join(settings.STORE_PATH, tenant_slug, relative_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    return full_path, relative_path


def resolve_export_list_file(tenant_slug: str, relative_path: str) -> str:
    """
    解析导出文件的绝对路径（防目录穿越）

    仅允许访问 ``{STORE_PATH}/{tenant_slug}/archives/export_lists/`` 目录下的文件，
    且归一化后必须仍位于该目录内。

    Args:
        tenant_slug: 租户标识
        relative_path: 相对路径，如 ``archives/export_lists/xxx.xlsx``

    Returns:
        str: 文件绝对路径

    Raises:
        BizException: 路径非法（ERROR_ILLEGAL_ARGUMENT）或文件不存在（ERROR_DATA_NOT_FOUND）
    """
    if not tenant_slug or not re.fullmatch(r"[a-zA-Z0-9_-]+", tenant_slug):
        raise BizException(ERROR_ILLEGAL_ARGUMENT, f"Invalid tenant_slug: {tenant_slug!r}")

    path = (relative_path or "").strip().replace("\\", "/").lstrip("/")
    if not path:
        raise BizException(ERROR_ILLEGAL_ARGUMENT, "文件路径不能为空")

    # 仅允许导出目录下的文件
    if not path.startswith(f"{EXPORT_LIST_DIR}/"):
        raise BizException(ERROR_ILLEGAL_ARGUMENT, "非法的文件路径")

    # 禁止路径穿越片段（..）与空片段（连续斜杠）
    if any(segment in ("..", "") for segment in path.split("/")):
        raise BizException(ERROR_ILLEGAL_ARGUMENT, "非法的文件路径")

    tenant_root = os.path.abspath(os.path.join(str(settings.STORE_PATH), tenant_slug))
    export_root = os.path.abspath(os.path.join(tenant_root, *EXPORT_LIST_DIR.split("/")))
    file_path = os.path.abspath(os.path.join(tenant_root, *path.split("/")))

    # 归一化后必须仍位于导出目录内
    try:
        inside = os.path.commonpath([export_root, file_path]) == export_root
    except ValueError:
        inside = False
    if not inside:
        raise BizException(ERROR_ILLEGAL_ARGUMENT, "非法的文件路径")

    if not os.path.isfile(file_path):
        raise BizException(ERROR_DATA_NOT_FOUND, "文件不存在")

    return file_path