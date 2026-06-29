from django.utils.decorators import method_decorator
from extensions.decorators import validate_parameters
from extensions.views import BaseView, PaginationResponse
from extensions.schemas import BatchDeleteSchema
from identity.schemas import (
    RoleSchema, 
    RoleListSchema, 
)
from identity.services import role_service
from identity.decorators import require_admin


class AdminRoleDetailView(BaseView):
    """管理员操作角色"""
    
    @method_decorator(require_admin)
    def get(self, request, role_id):
        return role_service.get_role_info(role_id=role_id)
    
    @method_decorator(require_admin)
    @method_decorator(validate_parameters(RoleSchema))
    def put(self, request, role_id, cleaned_data):
        return role_service.update_role_info(role_id=role_id, **cleaned_data)
    
    @method_decorator(require_admin)
    def delete(self, request, role_id):
        return role_service.delete_role(role_id=role_id)
        

class AdminRoleListView(BaseView):
    """管理员获取角色列表"""
    
    @method_decorator(require_admin)
    @method_decorator(validate_parameters(RoleListSchema))
    def get(self, request, cleaned_data):
        total, items = role_service.get_role_list(
            company_id=request.user.company_id,
            **cleaned_data
        )
        return PaginationResponse(total, items)
    
    @method_decorator(require_admin)
    @method_decorator(validate_parameters(RoleSchema))
    def post(self, request, cleaned_data):
        """管理员创建角色"""
        return role_service.create_role(
            operator=request.user,
            **cleaned_data
        )
    
    @method_decorator(require_admin)
    @method_decorator(validate_parameters(BatchDeleteSchema))
    def delete(self, request, cleaned_data):
        """管理员批量删除角色"""
        return role_service.batch_delete_role(**cleaned_data)


class AdminRoleEnableView(BaseView):
    
    @method_decorator(require_admin)
    def put(self, request, role_id):
        """启用角色"""
        return role_service.enable_role(role_id=role_id)


class AdminRoleDisableView(BaseView):
    
    @method_decorator(require_admin)
    def put(self, request, role_id):
        """禁用角色"""
        return role_service.disable_role(role_id=role_id)


class AdminRolePermissionTreeView(BaseView):
    
    @method_decorator(require_admin)
    def get(self, request):
        """获取角色权限树"""
        return role_service.get_permission_tree(
            company_id=request.user.company_id,
            tier_level=request.user.company.tier_level,
            user_permissions=request.user.get_permissions()
        )