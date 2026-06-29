from hsmolding.models import MachineTrial
import datetime
from gis.common.django_ext.models import paginate
from django.db import transaction

from hsmolding.dao.machine_trial_model import (
    LoadSensitivityTrialDoc,
    CheckRingDynamicTrialDoc,
    CheckRingStaticTrialDoc,
    InjectVelocityLinearityTrialDoc,
    StabilityAssessmentTrialDoc,
    MouldBoardDeflectionTrialDoc,
    ScrewWearDoc
)
from hsmolding.utils.fitting.fitting_method import calculate_one
import numpy as np


Machine_Trial_CLS_MAP = {
    "load_sensitivity": LoadSensitivityTrialDoc,
    "check_ring_dynamic": CheckRingDynamicTrialDoc,
    "check_ring_static": CheckRingStaticTrialDoc,
    "inject_velocity_linearity": InjectVelocityLinearityTrialDoc,
    "stability_assessment": StabilityAssessmentTrialDoc,
    "mould_board_deflection": MouldBoardDeflectionTrialDoc,
    "screw_wear": ScrewWearDoc,
}


# 获取机器性能测试列表
def get_list_of_machine_trial(
    company_id=None,
    machine_trademark=None,
    machine_trial_type=None,
    machine_id=None,
    trial_start_date=None,
    trial_end_date=None,
    page_no=None,
    page_size=None,
):
    query = MachineTrial.objects.all().order_by("-id")
    if company_id:
        query = query.filter(company_id=company_id)
    if machine_trademark:
        query = query.filter(machine_trademark__icontains=machine_trademark)
    if machine_trial_type:
        query = query.filter(machine_trial_type=machine_trial_type)
    if machine_id:
        query = query.filter(machine_id=machine_id)
    if trial_start_date:
        query = query.filter(created_at__gte=datetime.datetime.combine(trial_start_date, datetime.datetime.min.time()))
    if trial_end_date:
        query = query.filter(created_at__lte=datetime.datetime.combine(trial_end_date, datetime.datetime.max.time()))
    total_count = query.count()
    if page_no and page_size:
        query = paginate(query, page_no, page_size)

    return total_count, [e.to_dict() for e in query]


# 删除多条测试记录
def delete_multiple_machine_trial(machine_trial_id_list: list):
    for machine_trial_id in machine_trial_id_list:
        delete_machine_trial_index(machine_trial_id)
        for machine_trial_type in [
            "load_sensitivity",
            "check_ring_dynamic",
            "check_ring_static",
            "inject_velocity_linearity",
            "stability_assessment",
            "mould_board_deflection"
        ]:
            delete_machine_trial(machine_trial_type,machine_trial_id)


# 添加注塑机性能测试
def _add_machine_trial_index(params: dict):
    machine_trial = MachineTrial()
    for name in params:
        if hasattr(MachineTrial, name):
            setattr(machine_trial, name, params[name])
    machine_trial.save()
    return machine_trial


# 添加注塑机性能测试
def add_machine_trial_index(params: dict):
    with transaction.atomic():
        # if "data_source" not in params:
        #     params["data_source"] = 0
        machine_trial = _add_machine_trial_index(params)
        return machine_trial.to_dict()


# 螺杆损失测试,拟合获得系数
def get_fitting_value(params:dict):
    if not(not params.get("table_data")[1].get("sections") is None and not params.get("table_data")[4].get("sections") is None):
        x = np.array(params.get("table_data")[1].get("sections"))
        # 计算的是螺杆前进的行程和体积之间的关系
        y = np.array(params.get("table_data")[4].get("sections"))
        slope,intercept = calculate_one(x,y)
        params["slope"] = slope
        params["intercept"] = intercept
    return params


# 获取注塑机性能测试信息
def _get_machine_trial_index(machine_trial_id):
    if machine_trial_id:
        machine_trial = MachineTrial.objects.filter(pk=machine_trial_id).first()
        return machine_trial


# 读取注塑机性能测试信息接口
def get_machine_trial_index(machine_trial_id):
    if machine_trial_id:
        return _get_machine_trial_index(machine_trial_id).to_dict()

# 更新注塑机性能测试
def update_machine_trial_index(machine_trial_id, params):
    if machine_trial_id:
        _update_machine_trial_index(machine_trial_id, params)
    return get_machine_trial_index(machine_trial_id)


# 更新注塑机性能测试
def _update_machine_trial_index(machine_trial_id, params):
    if params and machine_trial_id:
        machine_trial = MachineTrial.objects.filter(pk=machine_trial_id).first()
        for key, value in params.items():
            setattr(machine_trial, key, value)
        machine_trial.save()


# 删除注塑机性能测试
def delete_machine_trial_index(machine_trial_id):
    if machine_trial_id:
        machine_trial = MachineTrial.objects.filter(pk=machine_trial_id).first()
        if machine_trial:
            machine_trial.delete()


# 根据名称获取数据库对象
def get_doc_cls_by_name(cls_name):
    assert cls_name in Machine_Trial_CLS_MAP
    return Machine_Trial_CLS_MAP.get(cls_name)


# 获取机器性能测试页面数据 dict
def get_machine_trial_dict_by_machine_trial_id(machine_trial_type, machine_trial_id):
    doc = get_doc_cls_by_name(machine_trial_type)
    machine_trial = doc.objects(machine_trial_id=machine_trial_id).first()
    return machine_trial.to_dict() if machine_trial else None

# 获取机器性能测试页面数据 obj
def get_machine_trial_by_machine_trial_id(doc, machine_trial_id):
    machine_trial = doc.objects.filter(machine_trial_id=machine_trial_id).order_by("-updated_at").first()
    return machine_trial if machine_trial else None


# 添加机器性能测试数据
def add_machine_trial(machine_trial_type, params):
    doc = get_doc_cls_by_name(machine_trial_type)
    machine_trial = update_machine_trial(machine_trial_type, params)
    if not machine_trial:
        # 如果是螺杆损失测试,那么根据线性回归,计算系数
        if machine_trial_type == "screw_wear":
            params = get_fitting_value(params)
        machine_trial = doc(**params)
        machine_trial.save()
    return machine_trial.to_dict() if machine_trial else None


# 更新机器性能测试数据
def update_machine_trial(machine_trial_type, params):
    doc = get_doc_cls_by_name(machine_trial_type)
    machine_trial_id = params.get("machine_trial_id")
    machine_trial = get_machine_trial_by_machine_trial_id(doc, machine_trial_id)
    # 如果是螺杆损失测试,那么根据线性回归,计算系数
    if machine_trial_type == "screw_wear":
        params = get_fitting_value(params)
    if machine_trial:
        machine_trial.update(**params)
    return machine_trial


# 删除机器性能测试数据
def delete_machine_trial(machine_trial_type, machine_trial_id):
    doc = get_doc_cls_by_name(machine_trial_type)
    if machine_trial_id:
        machine_trial = get_machine_trial_by_machine_trial_id(doc,machine_trial_id)
        if machine_trial:
            machine_trial.delete()
