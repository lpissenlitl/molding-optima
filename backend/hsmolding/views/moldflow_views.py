
from django.utils.decorators import method_decorator
from gis.common.django_ext.views import BaseView
from gis.admin.decorators import require_login
from hsmolding.services import moldflow_service, moldflow_report_service, media_service
from hsmolding.views.moldflow_forms import MoldFlowSchema
from hsmolding.views.moldflow_report_forms import MoldFlowReportSchema, MoldFlowReportQuerySchema
from gis.common.django_ext.decorators import validate_parameters


class MoldflowLogView(BaseView):
    @method_decorator(require_login)
    @method_decorator(validate_parameters(MoldFlowSchema))
    def post(self, request, cleaned_data):
        # 上传模流日志
        return moldflow_service.add_moldflow(cleaned_data)


    @method_decorator(require_login)
    def get(self, request, project_id):
        # 上传模流日志
        return moldflow_service.get_moldflow_dict(project_id)


    @method_decorator(require_login)
    @method_decorator(validate_parameters(MoldFlowSchema))
    def put(self, request, cleaned_data):
        # 上传模流日志
        return moldflow_service.update_moldflow(cleaned_data)


class ImportMoldflowLogView(BaseView):
    @method_decorator(require_login)
    def post(self, request, mold_no, project_id):
        # 导入moldflow日志
        return media_service.upload_moldflow(request, mold_no, project_id, request.user.get("company_id"))


class MoldflowView(BaseView):
    @method_decorator(require_login)
    @method_decorator(validate_parameters(MoldFlowReportSchema))
    def post(self, request, cleaned_data):
        # 上传模流vbs跑出来的txt
        return moldflow_report_service.add_moldflow(cleaned_data)


    @method_decorator(require_login)
    @method_decorator(validate_parameters(MoldFlowReportSchema))
    def get(self, request, cleaned_data):
        # 上传模流vbs跑出来的txt
        return moldflow_report_service.get_moldflow_dict(cleaned_data.get("project_id"), cleaned_data.get("mold_flow_no"))


    @method_decorator(require_login)
    @method_decorator(validate_parameters(MoldFlowReportSchema))
    def put(self, request, cleaned_data):
        # 上传模流vbs跑出来的txt
        return moldflow_report_service.update_moldflow(cleaned_data).to_dict()


class ImportMoldflowView(BaseView):
    @method_decorator(require_login)
    def post(self, request, mold_no, project_id):
        # 导入moldflow模流vbs跑出来的txt
        return media_service.upload_moldflow(request, mold_no, project_id, request.user.get("company_id"))
        

class MoldflowListView(BaseView):
    @method_decorator(require_login)
    @method_decorator(validate_parameters(MoldFlowReportQuerySchema))
    def get(self, request, cleaned_data):
        #　一个模具对应多个模流分析文件
        return moldflow_report_service.get_moldflow_list(**cleaned_data)
