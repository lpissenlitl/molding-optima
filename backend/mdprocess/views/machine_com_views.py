import logging

from django.utils.decorators import method_decorator

from gis.admin.decorators import require_login, check_permission
from gis.common.django_ext.decorators import validate_parameters
from gis.common.django_ext.views import BaseView

from mdprocess.services import mes_service
from mdprocess.views.machine_com_forms import (
    YizumiMesTransfer,
)
from mdprocess.views.process_record_forms import ProcessRecordSchema


# 通过伊之密MES读写接口
class MachineMesView(BaseView):
    @method_decorator(require_login)
    @method_decorator(validate_parameters(YizumiMesTransfer))
    def get(self, request, cleaned_data):
        return mes_service.getProcessTech(**cleaned_data)

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessRecordSchema))
    def post(self, request, cleaned_data):
        return mes_service.setProcessTech(**cleaned_data)
