from extensions.views import BaseView, PaginationResponse
from extensions.schemas import BatchDeleteSchema
from django.utils.decorators import method_decorator
from extensions.decorators import validate_parameters
from identity.decorators import require_login
from masterdata.schemas.material import PolymerSchema, PolymerListSchema
from masterdata.services import polymer_service


class PolymerDetailView(BaseView):
    
    @method_decorator(require_login)
    def get(self, request, polymer_id):
        """获取单个聚合物信息"""
        return polymer_service.get_polymer_info(request.user, polymer_id)
    
    @method_decorator(require_login)
    @method_decorator(validate_parameters(PolymerSchema))
    def put(self, request, polymer_id, cleaned_data):
        """更新单个聚合物信息"""
        return polymer_service.update_polymer_info(request.user, polymer_id, **cleaned_data)

    @method_decorator(require_login)
    def delete(self, request, polymer_id):
        """删除单个聚合物"""
        return polymer_service.delete_polymer(request.user, polymer_id)


class PolymerListView(BaseView, PaginationResponse):
    
    @method_decorator(require_login)
    @method_decorator(validate_parameters(PolymerSchema))
    def post(self, request, cleaned_data):
        """创建单个聚合物信息"""
        return polymer_service.create_polymer(request.user, **cleaned_data)

    @method_decorator(require_login)
    @method_decorator(validate_parameters(PolymerListSchema))
    def get(self, request, cleaned_data):
        """获取聚合物列表信息"""
        total, results = polymer_service.get_polymer_list(request.user, **cleaned_data)
        return PaginationResponse(total, results)

    @method_decorator(require_login)
    @method_decorator(validate_parameters(BatchDeleteSchema))
    def delete(self, request, cleaned_data):
        """批量删除聚合物信息"""
        return polymer_service.batch_delete_polymer(request.user, **cleaned_data)
