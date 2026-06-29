from typing import Type
from marshmallow import Schema, ValidationError, EXCLUDE
from django.http import HttpRequest, QueryDict
import json

from utils.http import querydict_to_dict, parse_get_params, querydict_to_dict_with_type_convert
from extensions.exceptions import BizException, ERROR_ILLEGAL_ARGUMENT

def validate_parameters(schema: Type[Schema]):
    """参数验证装饰器"""
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
                # print("get input: ", request.GET)
                body = parse_get_params(request)
                # print("get output: ", body)
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
                # print("input: ", body)
                cleaned_data = schema().load(body, unknown=EXCLUDE)
                # print("output: ", cleaned_data)
            except ValidationError as e:
                raise BizException(ERROR_ILLEGAL_ARGUMENT, e.messages)
            
            return func(*args, **kwargs, cleaned_data=cleaned_data)

        return wrapper

    return decorator