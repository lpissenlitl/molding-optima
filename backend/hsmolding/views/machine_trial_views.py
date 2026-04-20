import logging

from django.utils.decorators import method_decorator

from gis.admin.decorators import require_login
from gis.common.django_ext.decorators import validate_parameters
from gis.common.django_ext.views import BaseView, PaginationResponse

from hsmolding.views.machine_trial_forms import MachineTrialSchema, GetMachineTrialListSchema, HandleMultipleTrialSchema
from hsmolding.services import machine_trial_service
from gis.common.django_ext.decorators import validate_schema

_LOGGER = logging.getLogger(__name__)


# 机器性能测试索引
class MachineTrialListView(BaseView):
    # 新增机器性能测试信息
    @method_decorator(require_login)
    @method_decorator(validate_parameters(MachineTrialSchema))
    def post(self, request, cleaned_data):
        return  machine_trial_service.add_machine_trial_index(cleaned_data)

    # 获取机器性能测试列表
    @method_decorator(require_login)
    @method_decorator(validate_parameters(GetMachineTrialListSchema))
    def get(self, request, cleaned_data):
        total, machine_trials = machine_trial_service.get_list_of_machine_trial(**cleaned_data)
        return PaginationResponse(total, machine_trials)

    # 更新机器性能测试信息
    @method_decorator(require_login)
    @method_decorator(validate_parameters(MachineTrialSchema))
    def put(self, request, machine_trial_id, cleaned_data):
        machine_trial_service.update_machine_trial_index(machine_trial_id, cleaned_data)
        
    #　删除多条机器性能测试
    @method_decorator(require_login)
    @method_decorator(validate_parameters(HandleMultipleTrialSchema))
    def delete(self, request, cleaned_data):
        machine_trial_service.delete_multiple_machine_trial(**cleaned_data)


# 机器性能测试
class MachineTrialDetailView(BaseView):
    """
    machine_trial_type
    # 载荷敏感度测试
    "machine_trial_type/load_sensitivity/"
    # 动态止逆环重复性测试
    "machine_trial_type/check_ring_dynamic/"
    # 静态止逆环重复性测试
    "machine_trial_type/check_ring_static/"
    # 注射速度线性测试
    "machine_trial_type/inject_velocity_linearity/"
    # 稳定性评估测试
    "machine_trial_type/stability_assessment/"
    # 模板变形测试
    "machine_trial_type/mould_board_deflection/"
    # 螺杆磨损测试
    "machine_trial_type/screw_wear/"
    """
    # 添加机器性能测试信息
    @method_decorator(require_login)
    @method_decorator(validate_schema())
    def post(self, request, machine_trial_type, cleaned_data):
        return machine_trial_service.add_machine_trial(machine_trial_type, cleaned_data)

    # 获取机器性能测试信息
    @method_decorator(require_login)
    @method_decorator(validate_schema())
    def get(self, request, machine_trial_type, cleaned_data):
        return machine_trial_service.get_machine_trial_dict_by_machine_trial_id(machine_trial_type, **cleaned_data)

    # 更新机器性能测试信息
    @method_decorator(require_login)
    @method_decorator(validate_schema())
    def put(self, request, machine_trial_type, cleaned_data):
        machine_trial_service.update_machine_trial(machine_trial_type, cleaned_data)

    # 删除机器性能测试信息
    @method_decorator(require_login)
    def delete(self, request, machine_trial_type, cleaned_data):
        machine_trial_service.delete_machine_trial(**cleaned_data)
