from django.utils.decorators import method_decorator
from gis.common.django_ext.views import BaseView
from gis.admin.decorators import require_login
from hsmolding.services import machine_service, polymer_service, project_service, \
option_service, moldflow_report_service
from gis.admin.services import admin_service, company_service, department_service
from mdprocess.services import rule_service
from gis.common.django_ext.decorators import validate_parameters
from hsmolding.views.option_forms import OptionSchema, OptionsSchema
import logging

_LOGGER = logging.getLogger(__name__)


class SelectOptionView(BaseView):
    @method_decorator(require_login)
    @method_decorator(validate_parameters(OptionSchema))
    def get(self, request, option_name, cleaned_data):
        if option_name == "company_option":
            return company_service.get_company_option()

        if option_name == "department_option":
            if cleaned_data.get("company_id"):
                return department_service.get_department_option(cleaned_data.get("company_id"))
            elif cleaned_data.get("company_id") == 0:
                return department_service.get_department_option(company_id=None)
            else:
                return department_service.get_department_option(request.user.get("company_id"))

        if option_name == "department_tree":
            if cleaned_data.get("parent_id"):
                return department_service.get_department_tree(cleaned_data.get("parent_id"))
        if option_name == "group_tree":
            if cleaned_data.get("parent_id"):
                return company_service.get_group_tree(parent_id=cleaned_data.get("parent_id"), company_id=request.user.get("company_id"), is_super=request.user.get("is_super"))

        if option_name == "role_option":
            if cleaned_data.get("company_id"):
                return admin_service.get_role_option(cleaned_data.get("company_id"))
            elif cleaned_data.get("company_id") == 0:
                return admin_service.get_role_option(company_id=None)
            else:
                return admin_service.get_role_option(request.user.get("company_id"))

        if cleaned_data.get("db_table") == "mold" and option_name in [ "mold_no", "customer", "mold_name", "mold_type", "product_name", 
        "product_type", "project_engineer", "design_engineer",  "production_engineer", "product_small_type" ]:
            # 模具信息中需要的下拉选项
            return project_service.get_prompt_list_of_column(option_name, cleaned_data["form_input"], request.user.get("company_id"))
        
        if cleaned_data.get("db_table") == "product" and option_name in [ "gate_type" ]:
            return project_service.get_product_prompt_list_of_column(option_name, cleaned_data["form_input"], request.user.get("project_id"))

        if cleaned_data.get("db_table") == "machine" and option_name in [ "data_source", "trademark", "manufacturer"]:
            return machine_service.get_prompt_list_of_column(option_name, cleaned_data["form_input"], request.user.get("company_id"))
        
        if cleaned_data.get("db_table") == "polymer" and option_name in [ "abbreviation", "trademark" ]:
            return polymer_service.get_prompt_list_of_column(option_name, cleaned_data["form_input"], request.user.get("company_id"))

        if cleaned_data.get("db_table") == "rule_keyword" and option_name in [ "name" ]:
            return rule_service.get_prompt_list_of_keyword_column(option_name, cleaned_data["form_input"])

        if cleaned_data.get("db_table") == "rule_method" and option_name in [ "polymer_abbreviation", "product_small_type", "defect_name" ]:
            return rule_service.get_prompt_list_of_method_column(option_name, cleaned_data["form_input"])

        if option_name == "machine_data_source":
            return machine_service.list_machine_data_source(request.user.get("company_id"))
        
        if option_name == "manufacturer":
            return machine_service.list_machine_manufacturer(
                company_id=request.user.get("company_id"), 
                data_source=cleaned_data.get("data_source"), 
                manufacturer=cleaned_data.get("manufacturer")
            )

        if option_name == "machine_trademark":
            return machine_service.list_machine_trademark(
                company_id=request.user.get("company_id"), 
                data_source=cleaned_data.get("data_source"), 
                manufacturer=cleaned_data.get("manufacturer"), 
                trademark=cleaned_data.get("trademark"),
                serial_no=cleaned_data.get("serial_no"),
                asset_no=cleaned_data.get("asset_no"),
            )

        if option_name == "machines_summary":
            return machine_service.list_machine_summary(request.user.get("company_id"))

        if option_name == "polymer_abbreviation":
            return polymer_service.list_polymer_abbreviation(request.user.get("company_id"))

        if option_name == "polymer_trademark":
            return polymer_service.list_polymer_trademark(
                request.user.get("company_id"),
                cleaned_data.get("abbreviation"), 
                cleaned_data.get("trademark") 
            )

        # 新增和修改约机时，读取用户姓名和联系方式，供输入框提示使用
        if option_name == "user_list":
            return admin_service.list_user_name_phone(request.user.get("company_id"))

        if option_name == "custom_option":
            return option_service.get_list_of_option(**cleaned_data)

        if option_name == "interface_view":
            return option_service.get_list_of_interface_view(request.user.get("company_id"))

        if option_name == "interface_select":
            return option_service.get_list_of_interface_select(**cleaned_data)

        if option_name == "init":
            return option_service.init_data(**cleaned_data)
        
        if cleaned_data.get("db_table") == "moldflow" and option_name in [ "mold_flow_no", "analytical_sequence", "mold_flow_machine_trademark",
        "poly_trademark", "upload_date" ]:
            return moldflow_report_service.get_prompt_list_of_column(option_name, cleaned_data["form_input"], cleaned_data["project_id"])

        if option_name == "machine_adaption" and cleaned_data.get("form_input") and cleaned_data.get("machine_id_list"):
            return project_service.machine_list(cleaned_data.get("form_input"),cleaned_data.get("machine_id_list"))
  
        if cleaned_data.get("db_table") == "rule_flow" and option_name in ["rule_library", "rule_type", "polymer_abbreviation", "product_small_type"]:
            return rule_service.get_prompt_list_of_column(
                option_name, 
                cleaned_data.get("form_input"), 
                cleaned_data.get("polymer_abbreviation"),
                cleaned_data.get("product_small_type")
                )
        if option_name == "defect_list":
            return rule_service.get_defect_list()
        if option_name == "keyword_dict":
            return rule_service.get_keyword_dict()


    @method_decorator(require_login)
    @method_decorator(validate_parameters(OptionsSchema))
    def post(self, request, cleaned_data):
        return option_service.add_option(cleaned_data)
