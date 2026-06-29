from extensions.views import BaseView, PaginationResponse
from extensions.schemas import BatchDeleteSchema
from django.utils.decorators import method_decorator
from extensions.decorators import validate_parameters
from identity.decorators import require_login
from filecenter.schemas import FileListSchema
from filecenter.services import file_service


class FileDetailView(BaseView):
    
    @method_decorator(require_login)
    def get(self, request, uuid):
        """获取文件信息"""
        return file_service.get_file_info(uuid=uuid)
    
    @method_decorator(require_login)
    def delete(self, request, uuid):
        """删除文件"""
        return file_service.delete_file(uuid=uuid)


class FileListView(BaseView):
    
    @method_decorator(require_login)
    def post(self, request):
        """上传文件"""
        return file_service.upload_file(request)
    
    @method_decorator(require_login)
    @method_decorator(validate_parameters(FileListSchema))
    def get(self, request, cleaned_data):
        """根据业务信息获取文件列表"""
        return file_service.get_file_list_by_business(
            company_id=request.user.company_id,
            **cleaned_data
        )


class FileDownloadView(BaseView):
    
    @method_decorator(require_login)
    def get(self, request, uuid):
        """下载文件（用户认证 - 需要登录）"""
        return file_service.download_file(
            company_id=request.user.company_id,
            tenant_slug=request.user.company.tenant_slug,
            uuid=uuid,
            dispose_type="attachment"
        )


class FilePreviewView(BaseView):
    
    @method_decorator(require_login)
    def get(self, request, uuid):
        """预览文件（用户认证 - 需要登录）"""
        return file_service.download_file(
            company_id=request.user.company_id,
            tenant_slug=request.user.company.tenant_slug,
            uuid=uuid,
            dispose_type="inline"
        )


# ==================== 租户认证文件接口（无需登录，使用 Token）====================

class TenantFileDownloadView(BaseView):
    """文件下载（租户认证 - 通过 Token 验证，无需登录）"""
    
    def get(self, request, uuid):
        """
        下载文件
        
        Headers:
            X-Tenant-Token: <encrypted_uuid_token>
        
        Query Parameters:
            uuid: 文件 UUID
        """
        try:
            from utils.tenant_token_crypto import TenantTokenCrypto
            from extensions.exceptions import BizException, ERROR_ILLEGAL_ARGUMENT
            
            # 验证租户 Token
            token = request.META.get('HTTP_X_TENANT_TOKEN')
            if not token:
                raise BizException(ERROR_ILLEGAL_ARGUMENT, "缺少租户 Token")
            
            # 解密获取 tenant_slug
            try:
                tenant_slug = TenantTokenCrypto.decrypt_tenant_slug(token)
            except ValueError as e:
                raise BizException(ERROR_ILLEGAL_ARGUMENT, f"无效的租户 Token: {str(e)}")
            
            # 调用 Service 层下载文件
            return file_service.download_file_by_token(
                tenant_slug=tenant_slug,
                uuid=uuid,
                dispose_type="attachment"
            )
            
        except BizException as e:
            return self.error_response(e.message, code=e.code)
        except Exception as e:
            return self.error_response(str(e))


class TenantFilePreviewView(BaseView):
    """文件预览（租户认证 - 通过 Token 验证，无需登录）"""
    
    def get(self, request, uuid):
        """
        预览文件
        
        Headers:
            X-Tenant-Token: <encrypted_uuid_token>
        
        Query Parameters:
            uuid: 文件 UUID
        """
        try:
            from utils.tenant_token_crypto import TenantTokenCrypto
            from extensions.exceptions import BizException, ERROR_ILLEGAL_ARGUMENT
            
            # 验证租户 Token
            token = request.META.get('HTTP_X_TENANT_TOKEN')
            if not token:
                raise BizException(ERROR_ILLEGAL_ARGUMENT, "缺少租户 Token")
            
            # 解密获取 tenant_slug
            try:
                tenant_slug = TenantTokenCrypto.decrypt_tenant_slug(token)
            except ValueError as e:
                raise BizException(ERROR_ILLEGAL_ARGUMENT, f"无效的租户 Token: {str(e)}")
            
            # 调用 Service 层预览文件
            return file_service.download_file_by_token(
                tenant_slug=tenant_slug,
                uuid=uuid,
                dispose_type="inline"
            )
            
        except BizException as e:
            return self.error_response(e.message, code=e.code)
        except Exception as e:
            return self.error_response(str(e))