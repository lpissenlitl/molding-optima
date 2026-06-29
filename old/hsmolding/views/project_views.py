import logging

from django.utils.decorators import method_decorator

from gis.admin.decorators import require_login, check_permission
from gis.common.django_ext.decorators import validate_parameters
from gis.common.django_ext.views import BaseView, PaginationResponse

from hsmolding.views.project_forms import (
    ProjectSchema,
    GetProjectListSchema,
    HandleMultipleProjectSchema,
)
from hsmolding.services import project_service, media_service

_LOGGER = logging.getLogger(__name__)
        

# 多个工程view
class ProjectListView(BaseView):

    # 新增工程
    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProjectSchema))
    def post(self, request, cleaned_data):
        return project_service.add_project(cleaned_data)


    # 获取工程列表
    @method_decorator(require_login)
    @method_decorator(validate_parameters(GetProjectListSchema))
    def get(self, request, cleaned_data):
        total, projects = project_service.get_list_of_project(**cleaned_data,user_id=request.user.get("id"))
        return PaginationResponse(total, projects)


    # 处理多个工程
    @method_decorator(require_login)
    @method_decorator(validate_parameters(HandleMultipleProjectSchema))
    def put(self, request, cleaned_data):
        return project_service.handle_multiple_project(cleaned_data)


    # 删除多个工程
    @method_decorator(require_login)
    @method_decorator(validate_parameters(HandleMultipleProjectSchema))
    def delete(self, request, cleaned_data):
        project_service.delete_multiple_project(cleaned_data.get("project_id_list"))


# 单个工程view
class ProjectDetailView(BaseView):
  
    # 查看工程详情
    @method_decorator(require_login)
    def get(self, request, project_id):
        return project_service.get_project(project_id)


    # 更新工程内容
    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProjectSchema))
    def put(self, request, project_id, cleaned_data):
        return project_service.update_project(project_id, cleaned_data)


    # 删除工程
    @method_decorator(require_login)
    def delete(self, request, project_id):
        project_service.delete_project(project_id)


    # 从EXCEL上传模具    
    @method_decorator(require_login)
    def post(self, request):
        return media_service.import_mold(request)
