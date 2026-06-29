import logging

# from core_mch import mch_service
from gis.admin.exceptions import ERROR_USER_NOT_EXISTS, ERROR_ROLE_NOT_EXISTS
from gis.admin.services import admin_service
from gis.common.exceptions import BizException

_LOGGER = logging.getLogger(__name__)


def wrapper_record_info(record_items):
    resp_items = []
    for record_item in record_items:
        record = admin_service.get_user_by_id(
            record_item["operator"], check_enable=False, check_deleted=False
        )
        record_item["operator_name"] = record["name"]
        permission = admin_service.get_permission_by_code(record_item["resource"])
        record_item["resource_name"] = permission["name"]
        resp_items.append(record_item)
    return resp_items
