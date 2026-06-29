import logging

from django.utils.decorators import method_decorator

from gis.admin.decorators import require_login, check_permission
from gis.common.django_ext.decorators import validate_parameters
from gis.common.django_ext.views import BaseView, PaginationResponse

from hsmolding.views.polymer_forms import (
    PolymerSchema,
    PolymerListSchema,
    HandleMultiplePolymerSchema,
)
from hsmolding.services import polymer_service, export_service, media_service

_LOGGER = logging.getLogger(__name__)


class PolymerListView(BaseView):

    # 获取胶料列表
    @method_decorator(require_login)
    @method_decorator(validate_parameters(PolymerListSchema))
    def get(self, request, cleaned_data):
        total, polymers = polymer_service.get_list_of_polymer(**cleaned_data)
        return PaginationResponse(total, polymers)


    # 新增胶料信息
    @method_decorator(require_login)
    @method_decorator(validate_parameters(PolymerSchema))
    def post(self, request, cleaned_data):
        return polymer_service.add_polymer(cleaned_data)


    # 导出胶料信息
    @method_decorator(require_login)
    @method_decorator(validate_parameters(HandleMultiplePolymerSchema))
    def put(self, request, cleaned_data):
        return export_service.export_polymer_table(cleaned_data)


    # 删除多条胶料
    @method_decorator(require_login)
    @method_decorator(validate_parameters(HandleMultiplePolymerSchema))
    def delete(self, request, cleaned_data):
        # if (cleaned_data.get["flag"] == "delete"):
        polymer_service.delete_multiple_polymer(cleaned_data.get("polymer_id_list"))


class PolymerDetailView(BaseView):

    # 获取胶料信息
    @method_decorator(require_login)
    def get(self, request, polymer_id):
        return polymer_service.get_polymer(polymer_id)


    # 更新胶料信息
    @method_decorator(require_login)
    @method_decorator(validate_parameters(PolymerSchema))
    def put(self, request, polymer_id, cleaned_data):
        return polymer_service.update_polymer(polymer_id, cleaned_data)


    # 删除胶料信息
    @method_decorator(require_login)
    def delete(self, request, polymer_id):
        polymer_service.delete_polymer(polymer_id)


    # 从EXCEL上传胶料    
    @method_decorator(require_login)
    def post(self, request):
        return media_service.import_polymer(request)
