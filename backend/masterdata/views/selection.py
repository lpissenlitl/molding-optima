from django.utils.decorators import method_decorator

from extensions.decorators import validate_parameters
from extensions.views import BaseView
from identity.decorators import require_login
from masterdata.schemas.selection import SelectionOptionsSchema
from masterdata.services import selection_service


class SelectionOptionsView(BaseView):
    """远程搜索建议（GET /api/selection-options/）

    供前端 autocomplete 取候选值：
    - table / column 由前端 FormItem.query 指定，均受白名单校验
    - 结果按当前用户所属公司隔离
    """

    @method_decorator(require_login)
    @method_decorator(validate_parameters(SelectionOptionsSchema))
    def get(self, request, cleaned_data):
        """按 table + column 返回候选值列表"""
        return selection_service.get_selection_options(
            company_id=request.user.company_id,
            table=cleaned_data.get("table"),
            column=cleaned_data.get("column"),
            input_text=cleaned_data.get("input", ""),
            limit=cleaned_data.get("limit"),
        )
