import logging

from django.utils.decorators import method_decorator

from gis.admin.decorators import require_login, check_permission
from gis.common.django_ext.decorators import validate_parameters
from gis.common.django_ext.views import BaseView, PaginationResponse

from hsmolding.views.machine_forms import GetMachineListSchema, MachineInfoSchema, HandleMultipleMachineSchema
from hsmolding.services import machine_service, export_service, media_service

_LOGGER = logging.getLogger(__name__)


class MachineListView(BaseView):

    # 获取机器列表
    @method_decorator(require_login)
    @method_decorator(validate_parameters(GetMachineListSchema))
    def get(self, request, cleaned_data):
        total, machines = machine_service.list_machine_view(cleaned_data,user_id=request.user.get("id"))
        return PaginationResponse(total, machines)


    # 新增机器信息
    @method_decorator(require_login)
    @method_decorator(validate_parameters(MachineInfoSchema))
    def post(self, request, cleaned_data):
        machine_service.add_machine(cleaned_data)


    # 导出全部机器信息
    @method_decorator(require_login)
    @method_decorator(validate_parameters(HandleMultipleMachineSchema))
    def put(self, request, cleaned_data):
        return export_service.export_machine_table(cleaned_data)


    # 删除多条机器
    @method_decorator(require_login)
    @method_decorator(validate_parameters(HandleMultipleMachineSchema))
    def delete(self, request, cleaned_data):
        machine_service.delete_multiple_machine(cleaned_data.get("machine_id_list"))


class MachineDetailView(BaseView):

    # 获取机器信息
    @method_decorator(require_login)
    def get(self, request, machine_id):
        return machine_service.get_machine(machine_id)


    # 更新机器信息
    @method_decorator(require_login)
    @method_decorator(validate_parameters(MachineInfoSchema))
    def put(self, request, machine_id, cleaned_data):
        return machine_service.update_machine(machine_id, cleaned_data)


    # 删除机器信息
    @method_decorator(require_login)
    def delete(self, request, machine_id):
        machine_service.delete_machine(machine_id)


    # 从EXCEL上传机器   
    @method_decorator(require_login)
    def post(self, request):
        return media_service.import_machine(request)
