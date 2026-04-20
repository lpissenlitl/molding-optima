import logging
from math import log

from django.utils.decorators import method_decorator

from gis.admin.decorators import require_login, check_permission
from gis.common.django_ext.decorators import validate_parameters
from gis.common.django_ext.views import BaseView
from mdprocess.views.inovance_forms import ProjectSchema, PolymerSchema, InitializeProcessSchema, OptimizeProcessSchema
from mdprocess.services import inovance_service
import time


class ProjectDetailView(BaseView):
    # 新增工程
    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProjectSchema))
    def post(self, request, cleaned_data):
        return inovance_service.add_project(cleaned_data)

    # 查看工程详情
    @method_decorator(require_login)
    def get(self, request, project_id):
        return inovance_service.get_project(project_id)

    # 更新工程内容
    @method_decorator(require_login)
    @method_decorator(validate_parameters(ProjectSchema))
    def put(self, request, project_id, cleaned_data):
        return inovance_service.update_project(project_id, cleaned_data)
    
    # 删除工程
    @method_decorator(require_login)
    def delete(self, request, project_id):
        inovance_service.delete_project(project_id)


class PolymerDetailView(BaseView):
    
    @method_decorator(require_login)
    @method_decorator(validate_parameters(PolymerSchema))
    def post(self, request, cleaned_data):
        return inovance_service.add_polymer(cleaned_data)

    # 获取胶料信息
    @method_decorator(require_login)
    def get(self, request, polymer_id):
        return inovance_service.get_polymer(polymer_id)

    # 更新胶料信息
    @method_decorator(require_login)
    @method_decorator(validate_parameters(PolymerSchema))
    def put(self, request, polymer_id, cleaned_data):
        return inovance_service.update_polymer(polymer_id, cleaned_data)

    # 删除胶料信息
    @method_decorator(require_login)
    def delete(self, request, polymer_id):
        inovance_service.delete_polymer(polymer_id)



# 算法 工艺参数初始化
class ProcessInitialAlgorithmView(BaseView):

    # 初始化工艺参数记录
    @method_decorator(require_login)
    @method_decorator(validate_parameters(InitializeProcessSchema))
    def post(self, request, cleaned_data):
        logging.info("开始初始化算法")
        start = time.perf_counter()
        data = inovance_service.initialize_process(request.user, cleaned_data)
        end = time.perf_counter()
        elapsed_ms = (end - start) * 1000  # 转换为毫秒
        logging.info("算法运行结果：%s" % data)
        logging.info("算法初始化耗时：%s ms" % (elapsed_ms))
        return data


# 算法 工艺参数优化
class ProcessOptimizeAlgorithmView(BaseView):

    # 优化工艺参数记录
    @method_decorator(require_login)
    @method_decorator(validate_parameters(OptimizeProcessSchema))
    def post(self, request, cleaned_data):
        return inovance_service.optimize_process(cleaned_data)
