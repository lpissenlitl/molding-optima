from extensions.views import BaseView, PaginationResponse
from extensions.schemas import BatchDeleteSchema
from django.utils.decorators import method_decorator
from extensions.decorators import validate_parameters
from identity.decorators import require_login
from masterdata.schemas.injection import InjectionMoldingMachineSchema, InjectionMachineListSchema
from masterdata.services import injection_service


class InjectionMachineDetailView(BaseView):
    
    @method_decorator(require_login)
    def get(self, request, injection_machine_id):
        """获取注塑机详情"""
        return injection_service.get_injection_machine_info(request.user, injection_machine_id)

    @method_decorator(require_login)
    @method_decorator(validate_parameters(InjectionMoldingMachineSchema))
    def put(self, request, injection_machine_id, cleaned_data):
        """更新注塑机"""
        return injection_service.update_injection_machine(request.user, injection_machine_id, **cleaned_data)
    
    @method_decorator(require_login)
    def delete(self, request, injection_machine_id):
        """删除注塑机"""
        return injection_service.delete_injection_machine(request.user, injection_machine_id)


class InjectionMachineListView(BaseView):
    
    @method_decorator(require_login)
    @method_decorator(validate_parameters(InjectionMoldingMachineSchema))
    def post(self, request, cleaned_data):
        """创建注塑机"""
        return injection_service.create_injection_machine(request.user, **cleaned_data)
    
    @method_decorator(require_login)
    @method_decorator(validate_parameters(InjectionMachineListSchema))
    def get(self, request, cleaned_data):
        """获取注塑机列表"""
        total, items = injection_service.get_injection_machine_list(request.user, **cleaned_data)
        return PaginationResponse(total, items)
    
    @method_decorator(require_login)
    @method_decorator(validate_parameters(BatchDeleteSchema))
    def delete(self, request, cleaned_data):
        """批量删除注塑机"""
        return injection_service.batch_delete_injection_machine(request.user, **cleaned_data)
