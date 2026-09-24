"""文件中心模块（FileCenter）业务错误码定义

模块编号：09（与 extensions/exceptions.py 中的 MOD_COMMON 同级）

错误码分段规划：
    01-09  文件夹名 / 路径校验（FOLDER_NAME_* / FILE_PATH_* / TENANT_SLUG_* / FILE_MD5_* / FILE_EXT_* / FILE_TYPE_*）
    10-19  文件上传（UPLOAD_*）—— 预留段位
    20-29  文件下载 / 读取（DOWNLOAD_* / READ_*）—— 预留段位
    30-39  文件删除（DELETE_*）—— 预留段位
    40-49  文件查询 / 列表（QUERY_* / LIST_*）—— 预留段位
    50-59  业务关联（ASSOCIATION_*）—— 预留段位
    60+    未来扩展
"""
from extensions.exceptions import BizErrorCode


# ============================================================
# 模块编号
# ============================================================
MOD_FILECENTER = "09"


# ============================================================
# 01-09 文件夹名 / 路径校验
# ============================================================
ERROR_FOLDER_NAME_NOT_ALLOWED  = BizErrorCode.create(MOD_FILECENTER, 1, "文件夹名非法")
ERROR_FILE_PATH_INVALID        = BizErrorCode.create(MOD_FILECENTER, 2, "文件路径非法")
ERROR_TENANT_SLUG_INVALID      = BizErrorCode.create(MOD_FILECENTER, 3, "租户标识非法")
ERROR_FILE_MD5_INVALID         = BizErrorCode.create(MOD_FILECENTER, 4, "文件 MD5 非法")
ERROR_FILE_EXT_INVALID         = BizErrorCode.create(MOD_FILECENTER, 5, "文件扩展名非法")
ERROR_FILE_TYPE_NOT_SUPPORTED  = BizErrorCode.create(MOD_FILECENTER, 6, "文件用途类型不支持")
