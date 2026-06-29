"""
参数验证装饰器 - Pydantic 版本

版本历史：
- v2.0.0 (2026-06-27) - 从 marshmallow 迁移到 Pydantic
"""
from typing import Type
from pydantic import BaseModel, ValidationError
from django.http import HttpRequest, QueryDict
import json

from utils.request_utils import querydict_to_dict, parse_get_params, querydict_to_dict_with_type_convert
from extensions.exceptions import BizException, ERROR_ILLEGAL_ARGUMENT


def validate_parameters(schema: Type[BaseModel]):
    """参数验证装饰器 - Pydantic 版本"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            request = args[0]
            if not isinstance(request, HttpRequest):
                raise Exception(
                    "the first parameter must be request, "
                    "you must use @method_decorator(validate_parameters) if you use the class-based View."
                )
            
            content_type = request.META.get("CONTENT_TYPE", "")
            body = {}
            
            if request.method == "GET":
                body = parse_get_params(request)
            else:
                content_type = request.META.get("CONTENT_TYPE", "").lower()

                if content_type.startswith("application/json"):
                    try:
                        body = json.loads(request.body.decode("utf-8")) if request.body else {}
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        raise BizException(ERROR_ILLEGAL_ARGUMENT, "Invalid JSON")

                elif content_type.startswith("application/x-www-form-urlencoded"):
                    # Django 已解析到 request.POST（QueryDict）
                    body = querydict_to_dict(request.POST)

                elif content_type.startswith("multipart/form-data"):
                    # Django 已解析表单字段到 request.POST（QueryDict）
                    # 注意：文件在 request.FILES，通常不需要放进 schema 验证
                    body = querydict_to_dict_with_type_convert(request.POST)

                else:
                    raise BizException(
                        ERROR_ILLEGAL_ARGUMENT,
                        "content-type must be application/json, application/x-www-form-urlencoded, or multipart/form-data",
                    )
            
            try:
                # Pydantic v2 验证并返回字典
                validated = schema.model_validate(body)
                # 只排除 None 值，保留有默认值的字段
                cleaned_data = validated.model_dump(exclude_none=True, by_alias=True)
            except ValidationError as e:
                # 转换 Pydantic 错误格式为兼容格式
                error_messages = {}
                for err in e.errors():
                    field = ".".join(str(loc) for loc in err["loc"])
                    error_messages[field] = err["msg"]
                raise BizException(ERROR_ILLEGAL_ARGUMENT, error_messages)
            
            return func(*args, **kwargs, cleaned_data=cleaned_data)

        return wrapper

    return decorator