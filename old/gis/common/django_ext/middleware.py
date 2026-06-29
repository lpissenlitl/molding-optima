import json
import logging
from dataclasses import is_dataclass
from datetime import datetime

from django.http import JsonResponse, HttpResponse, QueryDict
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

from gis.admin.const import ACTION
from gis.common.django_ext.json import JsonEncoder
from gis.common.exceptions import BizException
from gis.common.django_ext.decorators import get_dict_from_query_dict
from gis.common.utils import get_request_ip, shorten_user_agent, get_request_user_agent


_LOGGER = logging.getLogger(__name__)


class ApiMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.incoming_ts = int(timezone.now().timestamp() * 1000)
        request.DATA = None
        if request.method == "DELETE":
            return
        if request.method == "GET":
            request.DATA = get_dict_from_query_dict(request.GET)
        else:
            if request.META.get("CONTENT_TYPE") and request.META.get("CONTENT_TYPE").startswith("application/json"):
                body = request.body.decode()
                request.DATA = json.loads(body) if body else dict()
            elif request.POST:
                request.DATA = get_dict_from_query_dict(request.POST)

    def process_exception(self, request, exception):
        if isinstance(exception, BizException):
            response = dict(
                status=exception.error_code.code,
                msg=exception.detail_message,
                timestamp=datetime.now(),
            )
            logging.warning(
                "biz error: %s ,path: %s, uid: %s",
                exception,
                request.path,
                request.user_id if hasattr(request, "user_id") else None,
            )
            return JsonResponse(response, encoder=JsonEncoder, status=400)
        else:
            response = dict(status=-1, msg="内部错误，请联系管理员", timestamp=timezone.now())
            logging.exception(
                "catched error %s in %s, uid:%s",
                exception.__class__.__name__,
                request.path,
                request.user_id if hasattr(request, "user_id") else None,
            )
            return JsonResponse(response, encoder=JsonEncoder, status=500)

    def process_response(self, request, response):
        request.finish_ts = int(timezone.now().timestamp() * 1000)
        delta_ts = request.finish_ts - request.incoming_ts
        if request.DATA and request.DATA != "{}":
            pass
            # _LOGGER.info(f"URL: {request.method.upper()}:{request.path}, Duration:{delta_ts}ms, params:{request.DATA}")
        if isinstance(response, (dict, list)) or is_dataclass(response):
            wrap_data = dict(status=0, msg="OK", timestamp=timezone.now())
            wrap_data["data"] = response
            return JsonResponse(wrap_data, encoder=JsonEncoder)
        elif isinstance(response, str):
            return HttpResponse(response)
        elif response is None:
            return HttpResponse("")
        else:
            return response


class OperationLogMiddleware(MiddlewareMixin):
    def process_request(self, request):
        pass

    def process_exception(self, request, exception):
        pass

    def process_response(self, request, response):
        try:
            if isinstance(response, dict):
                handle_oper_record(request, response)
        except Exception:
            logging.info("OperationLogMiddleware  exception", exc_info=True)
        return response


def handle_oper_record(req, resp):
    if req.method not in ACTION:
        return

    # 新增导出事件记录
    if req.method == "GET":
        if not req.GET.get("export"):
            return
        # 导出没有数据的记录,resource_id设置为0
        resp["id"] = 0

    try:
        resource_id = resp.get("id", 0)
        action = ACTION[req.method]
        content_type = req.META.get("CONTENT_TYPE")
        if content_type and content_type.startswith("multipart/form-data"):
            content = ""
        else:
            content = req.body.decode() if req.body else ""

        temp = dict()
        if content_type:
            if content_type.startswith("application/json"):
                temp = json.loads(content) if content else dict()
            elif content_type == "application/x-www-form-urlencoded":
                temp = QueryDict(content).copy()
        resource = req.permission_code if hasattr(req, "permission_code") else None
        operator = req.user_id if hasattr(req, "user_id") else None
        ip = get_request_ip(req)
        user_agent = shorten_user_agent(get_request_user_agent(req))
        if req.path == "/admin/login/":  # 登录时去除密码明文
            resource = "admin_login"
            operator = resp["id"]

        from gis.admin.services import admin_service

        if not resource:
            return
        if isinstance(resource, list):
            resource = resource[0]
        admin_service.insert_record(
            resource,
            resource_id,
            action,
            json.dumps(temp),
            operator,
            ip,
            user_agent,
        )
    except Exception as e:
        _LOGGER.exception("insert record exception {}".format(e))
