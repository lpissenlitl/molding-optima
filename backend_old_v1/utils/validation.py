from extensions.exceptions import BizException, ERROR_ILLEGAL_ARGUMENT
from typing import Any
import re
from identity.exceptions import(
    ERROR_USER_PERMISSION_CODES_INVALID
)


def validate_pk(
    value: int,
    field_name: str,
    message: str = None
) -> int:
    """主键参数校验"""
    if isinstance(value, int) == False or value <= 0:
        raise BizException(
            ERROR_ILLEGAL_ARGUMENT, 
            message or f"{field_name} 必须为正整数"
        )
    return value


def validate_id_list(
    ids: list,
    field_name: str = None,
    message: str = None
) -> list:
    # if not ids:
    #     return 0
    if not isinstance(ids, list):
        raise BizException(ERROR_ILLEGAL_ARGUMENT, "ids 必须是 list 类型")
    if not all(isinstance(id, int) for id in ids):
        raise BizException(ERROR_ILLEGAL_ARGUMENT, "ids 中元素必须是 int 类型")
    return ids

def validate_required(
    value: Any,
    field_name: str,
    message: str = None
) -> Any:
    """必填参数校验"""
    if value is None:
        raise BizException(
            ERROR_ILLEGAL_ARGUMENT, 
            message or f"{field_name} 不能为空"
        )
    
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            raise BizException(
                ERROR_ILLEGAL_ARGUMENT, 
                message or f"{field_name} 不能为空"
            )
        return stripped
    
    return value


def validate_code(
    value: str,
    field_name: str,
    message: str = None
) -> str:
    """编码参数校验"""
    value = validate_required(value, field_name, message)
    value = value.lower()
    if not re.match(r"^[a-z0-9]([a-z0-9_-]*[a-z0-9])?$", value, re.ASCII):
        raise BizException(
            ERROR_ILLEGAL_ARGUMENT, 
            message or f"{field_name}只能包含字母、数字、- 或 _，且不能以 - 或 _ 开头/结尾"
        )
    return value


def validate_permission_codes(
    permission_codes: list,
    field_name: str,
    message: str = None
) -> list:
    """权限编码参数校验"""
    if not isinstance(permission_codes, list):
        raise BizException(
            ERROR_USER_PERMISSION_CODES_INVALID, 
            message or f"{field_name} 必须为列表"
        )
    cleaned_codes = []
    for code in permission_codes:
        if not isinstance(code, str):
            raise BizException(
                ERROR_USER_PERMISSION_CODES_INVALID, 
                message or f"{field_name} 必须为字符串"
            )
        stripped = code.strip()
        if not stripped:
            raise BizException(
                ERROR_USER_PERMISSION_CODES_INVALID, 
                message or f"{field_name} 不能为空字符"
            )
        cleaned_codes.append(stripped)
    return cleaned_codes