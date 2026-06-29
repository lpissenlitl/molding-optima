import logging
from typing import Union
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin
from dataclasses import is_dataclass

from utils.http import querydict_to_dict
from extensions.json import JsonEncoder
from extensions.exceptions import BizException
from datetime import datetime
import json

_LOGGER = logging.getLogger(__name__)

class ApiMiddleware(MiddlewareMixin):
    """
    统一 API 中间件，处理请求参数
    - 解析请求参数到 request.DATA 中
    """
    def process_request(self, request: HttpRequest):
        # 记录请求开始时间（毫秒）
        request.incoming_ts = int(datetime.now().timestamp() * 1000)
        request.DATA = {}

        method = request.method.upper()

        if method in ("GET", "DELETE"):
            request.DATA = querydict_to_dict(request.GET)

        elif method in ("POST", "PUT", "PATCH"):
            content_type = request.META.get("CONTENT_TYPE", "").lower()

            if content_type.startswith("application/json"):
                try:
                    body = request.body.decode("utf-8") if request.body else "{}"
                    request.DATA = json.loads(body)
                except (UnicodeDecodeError, json.JSONDecodeError):
                    request.DATA = {}  # 或抛出异常

            elif content_type.startswith("application/x-www-form-urlencoded"):
                # Django 已解析到 request.POST
                request.DATA = querydict_to_dict(request.POST)

            elif content_type.startswith("multipart/form-data"):
                # 文件上传：表单字段在 request.POST，文件在 request.FILES
                request.DATA = querydict_to_dict(request.POST)

            else:
                # 未知类型，默认尝试当表单处理（可选）
                request.DATA = querydict_to_dict(request.POST)

        return None
    
    def process_response(
        self, 
        request: HttpRequest, 
        response: Union[ HttpResponse, dict, list, str, int, float, bool, None ]
    ):
        """记录请求结束时间，封装响应数据"""
        # 获取请求结束时间（毫秒）
        request.outgoing_ts = int(datetime.now().timestamp() * 1000)
        
        if request.DATA and request.DATA != {}:
            delta_ts = request.outgoing_ts - request.incoming_ts
            _LOGGER.info(f"URL: {request.method.upper()}:{request.path}, Duration:{delta_ts}ms, params:{request.DATA}")

        if isinstance(response, (dict, list, str)) or is_dataclass(response):
            return JsonResponse({
                "status": 0,
                "msg": "OK",
                "timestamp": datetime.now().timestamp(),
                "data": response
            }, encoder=JsonEncoder)
        elif response is None:
            return HttpResponse("")
        else:
            return response
    
    def process_exception(self, request: HttpRequest, exception: Exception):
        """处理异常"""
        if isinstance(exception, BizException):
            response = {
                "status": exception.code,
                "msg": exception.detail_message,
                "timestamp": datetime.now(),
            }
            logging.warning(
                "biz error: %s, path: %s, uid: %s",
                exception,
                request.path,
                request.user_id if hasattr(request, "user_id") else None
            )
            return JsonResponse(response, encoder=JsonEncoder, status=400)
        else:
            response = {
                "status": -1,
                "msg": "内部错误，请联系管理员.",
                "timestamp": datetime.now(),
            }
            logging.exception(
                "catched error %s in %s, uid: %s",
                exception.__class__.__name__,
                request.path,
                request.user_id if hasattr(request, "user_id") else None
            )
            return JsonResponse(response, encoder=JsonEncoder, status=500)