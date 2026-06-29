import logging

from django.utils.decorators import method_decorator

from gis.admin.decorators import require_login, check_permission
from gis.common.django_ext.decorators import validate_parameters
from gis.common.django_ext.views import BaseView, PaginationResponse

from hsmolding.views.auxiliary_forms import (
    AuxiliaryMachineSchema,
    AuxiliaryListSchema,
    HandleMultipleAuxiliarySchema
)
from hsmolding.services import auxiliary_service

_LOGGER = logging.getLogger(__name__)

class AuxiliaryListView(BaseView):
    # 获取辅机列表
    @method_decorator(require_login)
    @method_decorator(validate_parameters(AuxiliaryListSchema))
    def get(self, request, cleaned_data):
        total, auxiliaries = auxiliary_service.get_list_of_auxiliary(**cleaned_data)
        return PaginationResponse(total, auxiliaries)


    # 新增辅机信息
    @method_decorator(require_login)
    @method_decorator(validate_parameters(AuxiliaryMachineSchema))
    def post(self, request, cleaned_data):
        auxiliary_service.add_auxiliary(cleaned_data)


    # 删除多条辅机
    @method_decorator(require_login)
    @method_decorator(validate_parameters(HandleMultipleAuxiliarySchema))
    def delete(self, request, cleaned_data):
        auxiliary_service.delete_multiple_auxiliary(cleaned_data.get("auxiliary_id_list"))


class AuxiliaryDetailView(BaseView):
    # 获取辅机信息
    @method_decorator(require_login)
    def get(self, request, auxiliary_id):
        return auxiliary_service.get_auxiliary(auxiliary_id)


    # 更新辅机信息
    @method_decorator(require_login)
    @method_decorator(validate_parameters(AuxiliaryMachineSchema))
    def put(self, request, auxiliary_id, cleaned_data):
        auxiliary_service.update_auxiliary(auxiliary_id, cleaned_data)


    # 删除辅机信息
    @method_decorator(require_login)
    def delete(self, request, auxiliary_id):
        auxiliary_service.delete_auxiliary(auxiliary_id)