from extensions.exceptions import BizErrorCode

"""
统一业务错误码定义
格式：6 位数字 = A + MM + CCCC
A: 应用类型（1=Web/API）
MM: 模块编号
CCCC: 错误序号
"""

# =============================
# 应用类型
# =============================
APP_WEB = 1  # Web

# =============================
# 模块编号
# =============================
MOD_AUTH       = "01"  # 认证与用户
MOD_COMPANY    = "02"  # 公司
MOD_ORG        = "03"  # 组织
MOD_PERMISSION = "04"  # 权限
MOD_ROLE       = "05"  # 角色


# =============================
# 01. 用户认证模块
# =============================
ERROR_USER_TOKEN_NOT_EXISTS = BizErrorCode.create(MOD_AUTH, 1, "请重新登录")
ERROR_USER_USERNAME_EMPTY   = BizErrorCode.create(MOD_AUTH, 2, "用户名不能为空")
ERROR_USER_USERNAME_EXISTS  = BizErrorCode.create(MOD_AUTH, 3, "用户名已存在")
ERROR_USER_USERNAME_NOT_EXISTS = BizErrorCode.create(MOD_AUTH, 4, "用户名不存在")
ERROR_USER_PASSWORD_EMPTY   = BizErrorCode.create(MOD_AUTH, 5, "密码不能为空")
ERROR_USER_PASSWORD_STRENGTH = BizErrorCode.create(MOD_AUTH, 6, "密码强度不够")
ERROR_USER_NOT_FOUND        = BizErrorCode.create(MOD_AUTH, 7, "用户不存在")
ERROR_USER_PASSWORD_WRONG   = BizErrorCode.create(MOD_AUTH, 8, "密码错误")
ERROR_USER_AUTH_FAILED      = BizErrorCode.create(MOD_AUTH, 9, "用户名或密码错误")
ERROR_USER_NOT_ACTIVE       = BizErrorCode.create(MOD_AUTH, 10, "用户未激活")

# =============================
# 02. 公司模块
# =============================
ERROR_COMPANY_NOT_ACCESSIBLE = BizErrorCode.create(MOD_COMPANY, 1, "公司不可访问")
ERROR_COMPANY_NAME_EMPTY     = BizErrorCode.create(MOD_COMPANY, 2, "公司名称不能为空")
ERROR_COMPANY_NAME_EXISTS    = BizErrorCode.create(MOD_COMPANY, 3, "公司名称已存在")
ERROR_COMPANY_CODE_EMPTY     = BizErrorCode.create(MOD_COMPANY, 4, "公司编码不能为空")
ERROR_COMPANY_CODE_EXISTS    = BizErrorCode.create(MOD_COMPANY, 5, "公司编码已存在")
ERROR_COMPANY_CODE_FORMAT    = BizErrorCode.create(MOD_COMPANY, 6, "公司编码格式不正确")
ERROR_COMPANY_NOT_FOUND      = BizErrorCode.create(MOD_COMPANY, 7, "公司不存在")

# =============================
# 03. 组织模块
# =============================
ERROR_ORGANIZATION_NAME_EXISTS      = BizErrorCode.create(MOD_ORG, 1, "组织名称已存在")
ERROR_ORGANIZATION_CODE_EXISTS    = BizErrorCode.create(MOD_ORG, 2, "组织编码已存在")
ERROR_ORGANIZATION_PARENT_NOT_EXISTS = BizErrorCode.create(MOD_ORG, 3, "父级组织不存在")
ERROR_ORGANIZATION_NOT_FOUND      = BizErrorCode.create(MOD_ORG, 4, "组织不存在")
ERROR_ORGANIZATION_LIST           = BizErrorCode.create(MOD_ORG, 5, "组织列表信息错误")
ERROR_ORGANIZATION_TREE           = BizErrorCode.create(MOD_ORG, 6, "组织树信息错误")

# =============================
# 04. 权限模块
# =============================
ERROR_USER_PERMISSION_DENIED = BizErrorCode.create(MOD_PERMISSION, 1, "用户无权限")
ERROR_USER_PERMISSION_CODES_INVALID = BizErrorCode.create(MOD_PERMISSION, 2, "权限编码无效")

# =============================
# 05. 角色模块
# =============================
ERROR_ROLE_CODE_EXISTS = BizErrorCode.create(MOD_ROLE, 1, "角色编码已存在")
ERROR_ROLE_NOT_FOUND   = BizErrorCode.create(MOD_ROLE, 2, "角色不存在")