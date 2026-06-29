"""
molding-optima reporting app 工具函数（精简）
保留 build_export_list_path；移除 mold_trial 相关函数（molding-optima 不引入试模）。
"""
import os
import re
from django.conf import settings
from extensions.exceptions import BizException, ERROR_ILLEGAL_ARGUMENT


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

    relative_path = f"archives/export_lists/{template_name}.{ext}"
    full_path = os.path.join(settings.STORE_PATH, tenant_slug, relative_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    return full_path, relative_path