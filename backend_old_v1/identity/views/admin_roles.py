from django.utils.decorators import method_decorator
from extensions.decorators import validate_parameters
from extensions.views import BaseView, PaginationResponse
from extensions.schemas import BatchDeleteSchema
from identity.schemas import (
    RoleSchema, 
    RoleListSchema, 
)
from identity.services import role_service
from identity.decorators import require_login


class AdminRoleDetailView(BaseView):
    """管理员操作角色"""
    
    @method_decorator(require_login)
    def get(self, request, role_id):
        return role_service.get_role_info(request.user, role_id)
    
    @method_decorator(require_login)
    @method_decorator(validate_parameters(RoleSchema))
    def put(self, request, role_id, cleaned_data):
        role_service.update_role_info(request.user, role_id, **cleaned_data)
    
    @method_decorator(require_login)
    def delete(self, request, role_id):
        role_service.delete_role(request.user, role_id)
        

class AdminRoleListView(BaseView):
    """管理员获取角色列表"""
    
    @method_decorator(require_login)
    @method_decorator(validate_parameters(RoleListSchema))
    def get(self, request, cleaned_data):
        total, items = role_service.get_role_list(request.user, **cleaned_data)
        return PaginationResponse(total, items)
    """管理员创建角色"""
    
    @method_decorator(require_login)
    @method_decorator(validate_parameters(RoleSchema))
    def post(self, request, cleaned_data):
        role_service.create_role(request.user, **cleaned_data)

    """管理员批量删除角色"""
    
    @method_decorator(require_login)
    @method_decorator(validate_parameters(BatchDeleteSchema))
    def delete(self, request, cleaned_data):
        role_service.batch_delete_role(request.user, **cleaned_data)


class AdminRoleEnableView(BaseView):
    
    @method_decorator(require_login)
    def put(self, request, role_id):
        """启用角色"""
        role_service.enable_role(request.user, role_id)


class AdminRoleDisableView(BaseView):
    
    @method_decorator(require_login)
    def put(self, request, role_id):
        """禁用角色"""
        role_service.disable_role(request.user, role_id)


class AdminRolePermissionTreeView(BaseView):
    
    @method_decorator(require_login)
    def get(self, request):
        """获取角色权限树"""
        return role_service.get_permission_tree(request.user)