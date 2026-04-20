import logging

from django.utils.decorators import method_decorator

from gis.admin.decorators import require_login, check_permission
from gis.common.django_ext.decorators import validate_parameters
from gis.common.django_ext.views import BaseView

from mdprocess.views.process_expert_forms import ExpertProcessSchema
from mdprocess.services import process_expert_service, process_optimize_service


class ProcessExpertDetailView(BaseView):
    # @method_decorator(require_login)
    def get(self, request, process_index_id):
        return process_optimize_service.get_process_optimization(process_index_id)

    # @method_decorator(require_login)
    @method_decorator(validate_parameters(ExpertProcessSchema))
    def post(self, request, cleaned_data):
        return process_expert_service.add_expert_process(cleaned_data)

    # @method_decorator(require_login)
    def delete(self, request, process_index_id):
        process_optimize_service.delete_process_optimization(process_index_id)
