from extensions.views import BaseView, PaginationResponse
from extensions.schemas import BatchDeleteSchema
from django.utils.decorators import method_decorator
from extensions.decorators import validate_parameters
from identity.decorators import require_login
from masterdata.schemas.auxiliary import AuxiliaryEquipmentSchema, AuxiliaryEquipmentListSchema
from masterdata.services import auxiliary_service


class AuxiliaryEquipmentDetailView(BaseView):
    
    @method_decorator(require_login)
    def get(self, request, auxiliary_equipment_id):
        """获取辅助装置详情"""
        return auxiliary_service.get_auxiliary_equipment_info(request.user, auxiliary_equipment_id)
    
    @method_decorator(require_login)
    @method_decorator(validate_parameters(AuxiliaryEquipmentSchema))
    def put(self, request, auxiliary_equipment_id, cleaned_data):
        """更新辅助装置信息"""
        return auxiliary_service.update_auxiliary_equipment(request.user, auxiliary_equipment_id, **cleaned_data)
    
    @method_decorator(require_login)
    def delete(self, request, auxiliary_equipment_id):
        """删除辅助装置"""
        return auxiliary_service.delete_auxiliary_equipment(request.user, auxiliary_equipment_id)


class AuxiliaryEquipmentListView(BaseView, PaginationResponse):
    
    @method_decorator(require_login)
    @method_decorator(validate_parameters(AuxiliaryEquipmentSchema))
    def post(self, request, cleaned_data):
        """创建辅助装置"""
        return auxiliary_service.create_auxiliary_equipment(request.user, **cleaned_data)

    @method_decorator(require_login)
    @method_decorator(validate_parameters(AuxiliaryEquipmentListSchema))
    def get(self, request, cleaned_data):
        """获取辅助装置列表"""
        total, items = auxiliary_service.get_auxiliary_equipment_list(request.user, **cleaned_data)
        return PaginationResponse(total, items)
    
    @method_decorator(require_login)
    @method_decorator(validate_parameters(BatchDeleteSchema))
    def delete(self, request, cleaned_data):
        """批量删除辅助装置"""
        return auxiliary_service.batch_delete_auxiliary_equipment(request.user, **cleaned_data)

