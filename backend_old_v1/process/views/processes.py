from django.utils.decorators import method_decorator
from identity.decorators import require_login
from extensions.decorators import validate_parameters
from extensions.views import BaseView, PaginationResponse
from extensions.schemas import BatchDeleteSchema
from process.schemas import ProcessParameterListSchema, ProcessConditionAndParameterSchema
from process.services import process_service


class ProcessParameterDetailView(BaseView):
    
    @method_decorator(require_login)
    def get(self, request, condition_id):
        """获取工艺参数记录"""
        return process_service.get_process_parameter(request.user, condition_id)
    
    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessConditionAndParameterSchema))
    def put(self, request, condition_id, cleaned_data):
        """更新工艺参数记录"""
        return process_service.update_process_parameter(request.user, condition_id, **cleaned_data)
        
    @method_decorator(require_login)
    def delete(self, request, condition_id):
        """删除工艺参数记录"""
        return process_service.delete_process_parameter(request.user, condition_id)


class ProcessParameterListView(BaseView):
    
    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessParameterListSchema))
    def get(self, request, cleaned_data):
        """获取合格工艺参数列表"""
        total, items = process_service.get_process_parameter_list(request.user, **cleaned_data)
        return PaginationResponse(total, items)
    
    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessConditionAndParameterSchema))
    def post(self, request, cleaned_data):
        """创建合格工艺参数"""
        return process_service.create_process_parameter(request.user, **cleaned_data)
    
    @method_decorator(require_login)
    @method_decorator(validate_parameters(BatchDeleteSchema))
    def delete(self, request, cleaned_data):
        """批量删除合格工艺参数"""
        return process_service.batch_delete_process_parameter(request.user, **cleaned_data)