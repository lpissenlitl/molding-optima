from django.views import View
from django.http import JsonResponse, HttpResponse
from dataclasses import dataclass, field, is_dataclass, asdict
from datetime import datetime
import typing


class BaseView(View):
    """
    自定义基础视图类，统一处理返回值
    子类的处理方法（如 get、post）若返回 None，这自动返回成功相应

    统一返回格式（与 ApiMiddleware 保持一致）：
    {
        "status": 0,
        "msg": "OK",
        "timestamp": <epoch_seconds>,
        "data": <view 返回值>
    }
    """
    # 默认成功响应（不可变，避免子类共享同一对象时被意外修改）
    SUCCESS_RESPONSE_DATA = {"status": 0, "msg": "OK", "data": {}}

    def dispatch(self, request, *args, **kwargs):
        # print(request)
        response = super().dispatch(request, *args, **kwargs)
        return self._wrap_response(response)

    @classmethod
    def _wrap_response(cls, response, status: int = 200):
        """统一包装 view 返回值为 HttpResponse（与 ApiMiddleware 格式一致）

        支持：
        - HttpResponse            原样返回
        - None                    → 默认成功响应
        - dataclass               → asdict() 转换后包装
        - dict / list / str / int / float / bool → JSON 包装

        注意：不处理 tuple。Tuple 表示分页结果时，view 应用
        `PaginationResponse(total, items)` 包装为 dataclass。
        """
        # 已经是 HttpResponse 直接返回
        if isinstance(response, HttpResponse):
            return response
        # dataclass → asdict（主用于 PaginationResponse）
        if is_dataclass(response):
            response = asdict(response)
        # dict / list / str / int / float / bool / None → JSON
        wrapped = {
            "status": 0 if status == 200 else status,
            "msg": "OK" if status == 200 else "Error",
            "timestamp": datetime.now().timestamp(),
            "data": response,
        }
        return JsonResponse(wrapped, status=status, safe=False)


@dataclass
class PaginationResponse:
    """
    分页响应数据结构
    用于 API 接口返回分页数据，如：{ "total": 100, "items": [ ... ] }
    """
    total: int = 0
    items: typing.List[typing.Any] = field(default_factory=list)