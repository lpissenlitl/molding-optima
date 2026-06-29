
from django.utils.decorators import method_decorator

from identity.decorators import require_login
from extensions.decorators import validate_parameters
from extensions.views import BaseView

from search.services import get_prompt_list_of_column
from search.schemas import SearchConditionSchema


class SelectOptionView(BaseView):
    @method_decorator(require_login)
    @method_decorator(validate_parameters(SearchConditionSchema))
    def post(self, request, cleaned_data):
        return get_prompt_list_of_column(request.user, **cleaned_data)
