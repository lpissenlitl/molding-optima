import logging

from django.utils.decorators import method_decorator
from gis.admin.decorators import require_login, check_permission
from gis.common.django_ext.decorators import validate_parameters
from gis.common.django_ext.views import BaseView, PaginationResponse

from mdprocess.views.process_index_forms import GetProcessIndexListSchema, ProcessIndexSchema, HandleMultipleProcessSchema
from mdprocess.services import process_index_service
from hsmolding.services import export_report_service

_LOGGER = logging.getLogger(__name__)

#  工艺参数记录列表
class ProcessIndexListView(BaseView):
    # 新增工艺记录索引
    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessIndexSchema))
    def post(self, request, cleaned_data):
        return process_index_service.add_process_index(cleaned_data)

    @method_decorator(require_login)
    @method_decorator(validate_parameters(GetProcessIndexListSchema))
    def get(self, request, cleaned_data):
        total, processs = process_index_service.get_list_of_process_index(**cleaned_data)
        return PaginationResponse(total, processs)

    #导出多条工艺记录
    @method_decorator(require_login)
    @method_decorator(validate_parameters(HandleMultipleProcessSchema))
    def put(self, request, cleaned_data):
        if cleaned_data.get("flag") == "export_list":
            return process_index_service.export_process_index(cleaned_data)
        if cleaned_data.get("flag") == "export_report" and cleaned_data.get("process_id_list") and len(cleaned_data.get("process_id_list")) == 1: 
            return export_report_service.export_optimize(cleaned_data.get("process_id_list")[0])

    # 删除多条工艺记录
    @method_decorator(require_login)
    @method_decorator(validate_parameters(HandleMultipleProcessSchema))
    def delete(self, request, cleaned_data):
        process_index_service.delete_multiple_process_index(cleaned_data.get("process_id_list"))


# 操作mysql数据库中的工艺索引
class ProcessIndexDetailView(BaseView):
    # 获取工艺记录索引
    @method_decorator(require_login)
    def get(self, request, process_index_id):
        return process_index_service.get_process_index(process_index_id)

    # 更新工艺记录索引
    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessIndexSchema))
    def put(self, request, process_index_id, cleaned_data):
        process_index_service.update_process_index(process_index_id, cleaned_data)

    # 删除工艺记录索引
    @method_decorator(require_login)
    def delete(self, request, process_index_id):
        process_index_service.delete_process_index(process_index_id)
