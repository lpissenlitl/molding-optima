from django.views import View
from dataclasses import dataclass, field
import typing


class BaseView(View):
    """
    自定义基础视图类，统一处理返回值
    子类的处理方法（如 get、post）若返回 None，这自动返回成功相应
    """
    # 使用不可变默认值
    SUCCESS_RESPONSE_DATA = {}
    
    def dispatch(self, request, *args, **kwargs):
        # print(request)
        response = super().dispatch(request, *args, **kwargs)
        if response is None:
            return BaseView.SUCCESS_RESPONSE_DATA
        return response


@dataclass
class PaginationResponse:
    """
    分页响应数据结构
    用于 API 接口返回分页数据，如：{ "total": 100, "items": [ ... ] }
    """
    total: int = 0
    items: typing.List[typing.Any] = field(default_factory=list)