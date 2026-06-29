from extensions.views import BaseView, PaginationResponse
from extensions.schemas import BatchDeleteSchema
from django.utils.decorators import method_decorator
from extensions.decorators import validate_parameters
from identity.decorators import require_login
from masterdata.schemas.mold import MoldSchema, MoldListSchema
from masterdata.services import mold_service


class MoldDetailView(BaseView):
    
    @method_decorator(require_login)
    def get(self, request, mold_id):
        """获取模具信息"""
        return mold_service.get_mold_info(request.user, mold_id)
    
    @method_decorator(require_login)
    @method_decorator(validate_parameters(MoldSchema))
    def put(self, request, mold_id, cleaned_data):
        """修改模具信息"""
        return mold_service.update_mold_info(request.user, mold_id, **cleaned_data)
    
    @method_decorator(require_login)
    def delete(self, request, mold_id):
        """删除模具信息"""
        return mold_service.delete_mold(request.user, mold_id)
    

class MoldListView(BaseView):

    @method_decorator(require_login)
    @method_decorator(validate_parameters(MoldSchema))
    def post(self, request, cleaned_data):
        """创建模具"""
        return mold_service.create_mold(request.user, **cleaned_data)
    
    @method_decorator(require_login)
    @method_decorator(validate_parameters(MoldListSchema))
    def get(self, request, cleaned_data):
        """获取模具列表"""
        #print(cleaned_data)
        total, results = mold_service.get_mold_list(request.user, **cleaned_data)
        return PaginationResponse(total, results)

    @method_decorator(require_login)
    @method_decorator(validate_parameters(BatchDeleteSchema))
    def delete(self, request, cleaned_data):
        """批量删除模具"""
        return mold_service.batch_delete_mold(request.user, cleaned_data['ids'])