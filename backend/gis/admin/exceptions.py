from gis.common.exceptions import BizErrorCode
from hsmolding.exceptions import ERROR_DATA_EXIST

ERROR_COMPANY_NOT_EXISTS = BizErrorCode(9001, "企业不存在")
ERROR_COMPANY_NOT_PERMISSION = BizErrorCode(9002, "当前用户所在企业无使用权限！请联系管理员！")
ERROR_GROUP_NOT_PERMISSION = BizErrorCode(9004, "当前用户所在组织无使用权限！请联系管理员！")
ERROR_DEPARTMENT_NOT_EXISTS = BizErrorCode(9005, "部门不存在")
ERROR_DEPARTMENT_NOT_PERMISSION = BizErrorCode(9006, "当前用户所在部门无使用权限！请联系管理员！")
ERROR_ROLE_NOT_EXISTS = BizErrorCode(9007, "角色不存在")
ERROR_ROLE_NOT_PERMISSION = BizErrorCode(9008, "当前用户所处角色无使用权限！请联系管理员！")
ERROR_USER_NOT_PERMISSION = BizErrorCode(9009, "当前用户无使用权限！请联系管理员！")

ERROR_USER_NOT_EXISTS = BizErrorCode(1001, "用户不存在")
ERROR_USER_PASSWORD_INCORRECT = BizErrorCode(1002, "密码不正确")
ERROR_USER_PASSWORD_DIFFERENT = BizErrorCode(1003, "新旧密码不能相同")
ERROR_USER_DISABLED = BizErrorCode(1004, "请激活用户")
ERROR_USER_INVALID_TOKEN = BizErrorCode(1005, "未授权用户")
ERROR_USER_NAME_DUPLICATE = BizErrorCode(1006, "用户名已存在")
ERROR_USER_TOKEN_NOT_EXISTS = BizErrorCode(1007, "请重新登录")  # Token不存在
ERROR_USER_ROLES_NOT_EXISTS = BizErrorCode(1008, "用户尚未分配角色")
ERROR_USER_TOKEN_ERROR = BizErrorCode(1009, "Token无效，请重新登录")


ERROR_ROLE_NOT_EXISTS = BizErrorCode(1101, "角色不存在")
ERROR_ROLE_NAME_EXISTS = BizErrorCode(1102, "角色名称重复")
ERROR_ROLE_BIND_ONLY_LEAF_PERMISSION = BizErrorCode(1103, "绑定的权限具有子权限")
ERROR_ROLE_NOT_ALLOW_SET_PERMISSION_ATTR = BizErrorCode(1104, "该权限没有属性可设置")
ERROR_ROLE_CAN_NOT_UPDATE = BizErrorCode(1105, "该角色不允许编辑")

ERROR_GROUP_NOT_EXISTS = BizErrorCode(1201, "组织不存在")
ERROR_GROUP_NAME_EXISTS = BizErrorCode(1202, "组织名称重复")

ERROR_PERMISSION_NOT_EXISTS = BizErrorCode(1301, "权限不存在")
ERROR_PERMISSION_NOT_AUTHORIZED = BizErrorCode(1302, "未授权操作")
ERROR_PERMISSION_EXISTS = BizErrorCode(1303, "权限已存在")

ERROR_LIST_FUNC_MISS_ARGS = BizErrorCode(1401, "list function 缺少参数")

ERROR_VCODE_EMPTY = BizErrorCode(3215, "验证码为空")
ERROR_VCODE_INCORRECT = BizErrorCode(3216, "验证码错误")
