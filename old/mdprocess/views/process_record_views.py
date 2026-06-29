import logging

from django.utils.decorators import method_decorator
from gis.admin.decorators import require_login, check_permission
from gis.common.django_ext.decorators import validate_parameters
from gis.common.django_ext.views import BaseView

from mdprocess.views.process_record_forms import ProcessRecordSchema
from mdprocess.services import process_record_service
from hsmolding.services import media_service

_LOGGER = logging.getLogger(__name__)


# 操作mongo 完整的工艺参数document
class ProcessRecordDetailView(BaseView):
    @method_decorator(require_login)
    def get(self, request, process_index_id):
        return process_record_service.get_process_record(process_index_id)

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessRecordSchema))
    def post(self, request, cleaned_data):
        return process_record_service.add_process_record(cleaned_data)
        
    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessRecordSchema))
    def put(self, request, process_index_id, cleaned_data):
        process_record_service.update_process_record(cleaned_data)

    @method_decorator(require_login)
    def delete(self, request, process_index_id):
        process_record_service.delete_process_record(process_index_id)


class ProcessRecordView(BaseView):

    @method_decorator(require_login)
    def post(self, request):
        process_record_dict = media_service.import_process_record(request)
        return process_record_dict
