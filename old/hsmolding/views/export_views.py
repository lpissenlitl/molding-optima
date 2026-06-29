import logging

from django.utils.decorators import method_decorator

from gis.admin.decorators import require_login, check_permission
from gis.common.django_ext.decorators import validate_parameters
from gis.common.django_ext.views import BaseView

from hsmolding.services import export_service

from hsmolding.views.project_forms import ProjectIndexSchema
from hsmolding.views.machine_forms import MachineInfoSchema
from hsmolding.views.polymer_forms import PolymerSchema
from mdprocess.views.process_record_forms import ProcessRecordSchema
from mdprocess.views.rule_forms import GetRuleSchema

_LOGGER = logging.getLogger(__name__)


# 导出模具信息
class MoldInfoExportView(BaseView):

    # 根据模具id导出excel文件
    @method_decorator(require_login)
    def get(self, request, project_id):
        return export_service.export_mold_by_id(project_id)


    # 根据模具信息导出excel文件
    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProjectIndexSchema))
    def post(self, request, cleaned_data):
        return export_service.export_mold(cleaned_data)


# 导出机器信息
class MachineExportView(BaseView):

    # 根据机器id导出excel文件
    @method_decorator(require_login)
    def get(self, request, machine_id):
        return export_service.export_machine_by_id(machine_id)


    # 根据机器信息导出excel文件
    @method_decorator(require_login)
    @method_decorator(validate_parameters(MachineInfoSchema))
    def post(self, request, cleaned_data):
        return export_service.export_machine(cleaned_data)


# 导出胶料信息
class PolymerExportView(BaseView):

    # 根据胶料id导出excel文件
    @method_decorator(require_login)
    def get(self, request, polymer_id):
        return export_service.export_polymer_by_id(polymer_id)


    # 根据机器信息导出excel文件
    @method_decorator(require_login)
    @method_decorator(validate_parameters(PolymerSchema))
    def post(self, request, cleaned_data):
        return export_service.export_polymer(cleaned_data)


# 导出工艺信息
class ProcessExportView(BaseView):

    # 根据工艺id导出excel文件
    @method_decorator(require_login)
    def get(self, request, process_id):
        return export_service.export_process_by_id(process_id, request.user.get("company_id"))


    # 根据工艺信息导出excel文件
    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessRecordSchema))
    def post(self, request, cleaned_data):
        return export_service.export_process(cleaned_data, request.user.get("company_id"))


class RuleView(BaseView):

    # 根据subrule导出excel文件
    @method_decorator(require_login)
    @method_decorator(validate_parameters(GetRuleSchema))
    def post(self, request, cleaned_data):
        return export_service.export_rule(cleaned_data, request.user.get("company_id"))