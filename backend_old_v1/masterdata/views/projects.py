from extensions.views import BaseView, PaginationResponse
from extensions.schemas import BatchDeleteSchema
from django.utils.decorators import method_decorator
from extensions.decorators import validate_parameters
from identity.decorators import require_login
from masterdata.schemas.project import ProjectSchema, ProjectListSchema
from masterdata.services import project_service


class ProjectDetailView(BaseView):
    
    @method_decorator(require_login)
    def get(self, request, project_id):
        """获取项目信息"""
        return project_service.get_project_info(request.user, project_id)
    
    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProjectSchema))
    def put(self, request, project_id, cleaned_data):
        """修改项目信息"""
        return project_service.update_project_info(request.user, project_id, **cleaned_data)
    
    @method_decorator(require_login)
    def delete(self, request, project_id):
        """删除项目"""
        return project_service.delete_project(request.user, project_id)


class ProjectListView(BaseView):
    
    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProjectSchema))
    def post(self, request, cleaned_data):
        """创建项目"""
        return project_service.create_project(request.user, **cleaned_data)

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProjectListSchema))
    def get(self, request, cleaned_data):
        """获取项目列表"""
        total, results = project_service.get_project_list(request.user, **cleaned_data)
        return PaginationResponse(total, results)

    @method_decorator(require_login)
    @method_decorator(validate_parameters(BatchDeleteSchema))
    def delete(self, request, cleaned_data):
        """批量删除项目"""
        return project_service.batch_delete_project(request.user, **cleaned_data)
