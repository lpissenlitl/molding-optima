import logging

from django.utils.decorators import method_decorator

from gis.admin.decorators import require_login, check_permission
from gis.common.django_ext.decorators import validate_parameters
from gis.common.django_ext.views import BaseView

from mdprocess.views.process_index_forms import ProcessIndexSchema
from mdprocess.views.process_optimize_forms import OptimizeProcessSchema, ProcessOptimizationSchema
from mdprocess.services import process_optimize_service

_LOGGER = logging.getLogger(__name__)


# 操作mongo 工艺参数优化过程的参数记录
class ProcessOptimizeDetailView(BaseView):
    @method_decorator(require_login)
    def get(self, request, process_index_id):
        return process_optimize_service.get_process_optimization(process_index_id)

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessOptimizationSchema))
    def post(self, request, cleaned_data):
        return process_optimize_service.add_process_optimization(cleaned_data)

    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessOptimizationSchema))
    def put(self, request, process_index_id, cleaned_data):
        process_optimize_service.update_process_optimization(cleaned_data)

    @method_decorator(require_login)
    def delete(self, request, process_index_id):
        process_optimize_service.delete_process_optimization(process_index_id)


# 算法 工艺参数初始化
class ProcessInitialAlgorithmView(BaseView):

    # 初始化工艺参数记录
    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProcessIndexSchema))
    def post(self, request, cleaned_data):
        return process_optimize_service.initialize_process(cleaned_data)


# 算法 工艺参数优化
class ProcessOptimizeAlgorithmView(BaseView):

    # 优化工艺参数记录
    @method_decorator(require_login)
    @method_decorator(validate_parameters(OptimizeProcessSchema))
    def post(self, request, cleaned_data):
        return process_optimize_service.optimize_process(cleaned_data)

