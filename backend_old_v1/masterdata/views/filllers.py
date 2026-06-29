from extensions.views import BaseView, PaginationResponse
from extensions.schemas import BatchDeleteSchema
from django.utils.decorators import method_decorator
from extensions.decorators import validate_parameters
from identity.decorators import require_login
from masterdata.schemas.material import FillerSchema, FillerListSchema
from masterdata.services import filler_service


class FillerDetailView(BaseView):
    
    @method_decorator(require_login)
    def get(self, request, filler_id):
        """获取填充物详情"""
        return filler_service.get_filler_info(request.user, filler_id)

    @method_decorator(require_login)
    @method_decorator(validate_parameters(FillerSchema))
    def put(self, request, filler_id, cleaned_data):
        """修改填充物信息"""
        return filler_service.update_filler_info(request.user, filler_id, **cleaned_data)

    @method_decorator(require_login)
    @method_decorator(validate_parameters(FillerSchema))
    def delete(self, request, filler_id):
        """删除填充物信息"""
        return filler_service.delete_filler(request.user, filler_id)


class FillerListView(BaseView):
    
    @method_decorator(require_login)
    @method_decorator(validate_parameters(FillerSchema))
    def post(self, request, cleaned_data):
        """创建填充物"""
        return filler_service.create_filler(request.user, **cleaned_data)

    @method_decorator(require_login)
    @method_decorator(validate_parameters(FillerListSchema))
    def get(self, request, cleaned_data):
        """获取填充物列表"""
        total, results =  filler_service.get_filler_list(request.user, **cleaned_data)
        return PaginationResponse(total, results)

    @method_decorator(require_login)
    @method_decorator(validate_parameters(BatchDeleteSchema))
    def delete(self, request, cleaned_data):
        """批量删除填充物"""
        return filler_service.batch_delete_filler(request.user, **cleaned_data)