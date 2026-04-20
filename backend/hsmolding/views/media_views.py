import logging

from django.utils.decorators import method_decorator

from gis.admin.decorators import require_login, check_permission
from gis.common.django_ext.views import BaseView
from gis.common.django_ext.decorators import validate_parameters

from hsmolding.views.media_form import ListMediaUrlSchema
from hsmolding.services import media_service

_LOGGER = logging.getLogger(__name__)


class FileServiceView(BaseView):

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ListMediaUrlSchema))
    def get(self, request, cleaned_data):
        # 根据search_id 获取所属文件
        return media_service.get_list_of_file(**cleaned_data)

    @method_decorator(require_login)
    def post(self, request):
        # 上传照片,视频,大视频
        return media_service.upload_file(request)

    @method_decorator(require_login)
    def delete(self, request, file_id):
        # 上传照片,视频,大视频
        return media_service.delete_file(file_id)