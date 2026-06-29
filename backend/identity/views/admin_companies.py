from extensions.views import BaseView, PaginationResponse
from django.utils.decorators import method_decorator
from extensions.decorators import validate_parameters
from identity.schemas import (
    CompanySchema,
    CompanyListSchema,
    OrganizationSchema,
    OrganizationListSchema,
    OrganizationBatchUpdateSchema
)
from identity.decorators import require_admin
from identity.services import company_service
from extensions.schemas import BatchDeleteSchema


class AdminCompanyDetailView(BaseView):
    """管理员获取公司详情"""
    
    @method_decorator(require_admin)
    def get(self, request, company_id):
        return company_service.get_company_info(company_id=company_id)
    
    @method_decorator(require_admin)
    @method_decorator(validate_parameters(CompanySchema))
    def put(self, request, company_id, cleaned_data):
        return company_service.update_company_info(company_id=company_id, **cleaned_data)

    @method_decorator(require_admin)
    def delete(self, request, company_id):
        return company_service.delete_company(company_id=company_id)


class AdminCompanyListView(BaseView):
    """管理员公司列表"""
    
    @method_decorator(require_admin)
    @method_decorator(validate_parameters(CompanyListSchema))
    def get(self, request, cleaned_data):
        """管理员获取公司列表"""
        total, items = company_service.get_list_of_company(**cleaned_data)
        return PaginationResponse(total, items)
    
    @method_decorator(require_admin)
    @method_decorator(validate_parameters(CompanySchema))
    def post(self, request, cleaned_data):
        """管理员创建公司"""
        return company_service.create_company(operator=request.user, **cleaned_data)
        
    @method_decorator(require_admin)
    @method_decorator(validate_parameters(BatchDeleteSchema))
    def delete(self, request, cleaned_data):
        """批量删除公司"""
        return company_service.batch_delete_company(**cleaned_data)


class AdminCompanyEnableView(BaseView):
    
    @method_decorator(require_admin)
    def put(self, request, company_id):
        """管理员启用公司"""
        return company_service.enable_company(company_id=company_id)


class AdminCompanyDisableView(BaseView):
    
    @method_decorator(require_admin)
    def put(self, request, company_id):
        """管理员禁用公司"""
        return company_service.disable_company(company_id=company_id)


class AdminAssumeCompanyView(BaseView):
    
    @method_decorator(require_admin)
    def put(self, request, company_id):
        """管理员开始接管公司"""
        return company_service.assume_company(user=request.user, company_id=company_id)


class AdminReleaseCompanyView(BaseView):
    
    @method_decorator(require_admin)
    def put(self, request, company_id):
        """管理员放弃公司"""
        return company_service.release_company(user=request.user, company_id=company_id)

        
class AdminOrganizationListView(BaseView):
    
    @method_decorator(require_admin)
    @method_decorator(validate_parameters(OrganizationListSchema))
    def get(self, request, cleaned_data):
        """管理员获取组织列表"""
        total, groups = company_service.get_list_of_organization(
            company_id=request.user.company_id,
            **cleaned_data
        )
        return PaginationResponse(total, groups)
    
    @method_decorator(require_admin)
    @method_decorator(validate_parameters(OrganizationSchema))
    def post(self, request, cleaned_data):
        """管理员创建组织"""
        return company_service.create_organization(
            operator=request.user,
            company_id=request.user.company_id,
            **cleaned_data
        )
    
    @method_decorator(require_admin)
    @method_decorator(validate_parameters(OrganizationBatchUpdateSchema))
    def put(self, request, cleaned_data):
        """管理员批量更新组织"""
        return company_service.batch_update_organization_structure(**cleaned_data)
    
    @method_decorator(require_admin)
    @method_decorator(validate_parameters(BatchDeleteSchema))
    def delete(self, request, cleaned_data):
        """管理员批量删除组织"""
        return company_service.batch_delete_organization(**cleaned_data)


class AdminOrganizationDetailView(BaseView):
    
    @method_decorator(require_admin)
    def get(self, request, organization_id):
        """管理员获取组织详情"""
        return company_service.get_organization_info(organization_id=organization_id)
    
    @method_decorator(require_admin)
    @method_decorator(validate_parameters(OrganizationSchema))
    def put(self, request, organization_id, cleaned_data):
        """管理员更新组织信息"""
        return company_service.update_organization_info(organization_id=organization_id, **cleaned_data)
    
    @method_decorator(require_admin)
    def delete(self, request, organization_id):
        """管理员删除组织信息"""
        return company_service.delete_organization(organization_id=organization_id)
