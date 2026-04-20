from functools import wraps
import json
import re
import logging

from django.http import HttpRequest, QueryDict
from marshmallow import ValidationError, EXCLUDE

from gis.common.exceptions import BizException, ERROR_ILLEGAL_PARAMETER

from hsmolding.views.machine_trial_forms import (
    GetMachineTrialSchema,
    LoadSensitivityTrialSchema,
    CheckRingDynamicTrialSchema,
    CheckRingStaticTrialSchema,
    InjectVelocityLinearityTrialSchema,
    StabilityAssessmentTrialSchema,
    MouldBoardDeflectionTrialSchema,
    ScrewWearSchema
)

_LOGGER = logging.getLogger(__name__)

_GET_SCHEMA_CLS_MAP = {
    "machine_trials": GetMachineTrialSchema
}

_ADD_SCHEMA_CLS_MAP = {
    "load_sensitivity": LoadSensitivityTrialSchema,
    "check_ring_dynamic": CheckRingDynamicTrialSchema,
    "check_ring_static": CheckRingStaticTrialSchema,
    "inject_velocity_linearity": InjectVelocityLinearityTrialSchema,
    "stability_assessment": StabilityAssessmentTrialSchema,
    "mould_board_deflection": MouldBoardDeflectionTrialSchema,
    "screw_wear": ScrewWearSchema,
}


def get_schema_cls_by_name(cls_name):
    assert cls_name in _GET_SCHEMA_CLS_MAP
    return _GET_SCHEMA_CLS_MAP.get(cls_name)


def get_add_schema_cls_by_name(cls_name):
    assert cls_name in _ADD_SCHEMA_CLS_MAP
    return _ADD_SCHEMA_CLS_MAP.get(cls_name)


def get_dict_from_query_dict(query_dict):
    return {
        k[:-2]
        if k.endswith("[]")
        else k: v[0]
        if len(v) == 1 and k.find("list") == -1 and k.find("polymer_info_ids") == -1 and k.find("testing_material") == -1
        else v
        for k, v in query_dict.lists()
    }


def validate_parameters(schema: object) -> object:
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            request = args[0]
            if not isinstance(request, HttpRequest):
                raise Exception(
                    "the first parameter must be request, "
                    "you must use @method_decorator(validate_parameters) if you use the class-based View."
                )
            content_type = request.META.get("CONTENT_TYPE")
            if request.method == "GET":
                body = get_dict_from_query_dict(QueryDict(request.META["QUERY_STRING"]))
                body = json.loads(body.get("p")) if body.get("p") else body
            else:
                body = request.body.decode()
                if content_type.startswith("application/json"):
                    body = json.loads(body) if body else dict()
                elif content_type == "application/x-www-form-urlencoded":
                    body = QueryDict(body)
                else:
                    raise BizException(
                        ERROR_ILLEGAL_PARAMETER,
                        "content-type must be application/json or application/x-www-form-urlencoded",
                    )
            try:
                cleaned_data = schema().load(body, unknown=EXCLUDE)
            except ValidationError as err:
                raise BizException(ERROR_ILLEGAL_PARAMETER, err.messages)

            return func(*args, **kwargs, cleaned_data=cleaned_data)

        return wrapper

    return decorator


# 根据url和request method，选择合适的schema进行验证
def validate_schema():
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            request = args[0]
            if not isinstance(request, HttpRequest):
                raise Exception(
                    "the first parameter must be request, "
                    "you must use @method_decorator(validate_parameters) if you use the class-based View."
                )

            content_type = request.META.get("CONTENT_TYPE")
            if request.method == "GET":
                body = QueryDict(request.META["QUERY_STRING"])
                body = json.loads(body.get("p")) if body.get("p") else body

                # 举例，解析'/hsmolding/pre_trial/info_state/',取中间两个//之间的pre_trial
                pattern = re.compile(r"(?<=/)(\w+)(?=/)")
                cls_name = pattern.findall(request.META.get("PATH_INFO"))[-2]
                schema = get_schema_cls_by_name(cls_name)
            else:
                body = request.body.decode()
                if content_type.startswith("application/json"):
                    body = json.loads(body) if body else dict()
                elif content_type == "application/x-www-form-urlencoded":
                    body = QueryDict(body)
                else:
                    raise BizException(
                        ERROR_ILLEGAL_PARAMETER,
                        "content-type must be application/json or application/x-www-form-urlencoded",
                    )

                # 举例，解析'/hsmolding/pre_trial/info_state/',取最后两个//之间的info_state
                # ['hsmolding', 'effective_viscosity', '0']
                pattern = re.compile(r"/(\w+)")
                cls_name = pattern.findall(request.META.get("PATH_INFO"))[-1]
                schema = get_add_schema_cls_by_name(cls_name)
            try:
                cleaned_data = schema().load(body, unknown=EXCLUDE)
            except ValidationError as err:
                raise BizException(ERROR_ILLEGAL_PARAMETER, err.messages)

            return func(*args, **kwargs, cleaned_data=cleaned_data)

        return wrapper

    return decorator
