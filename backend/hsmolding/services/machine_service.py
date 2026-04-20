"""
机器服务
"""
from django.db import transaction
from gis.admin.services import admin_service

from gis.common.django_ext.models import paginate
from gis.common.exceptions import BizException

from hsmolding.exceptions import (
    ERROR_DATA_NOT_EXIST,
    ERROR_DATA_EXIST,
    ERROR_INPUT_IS_NULL,
)
from hsmolding.models import Machine, MachineInjector
# from hsmolding.services.machine_trial_service import get_list_of_machine_trial,get_machine_trial_dict_by_machine_trial_id


error_message = ""


# 添加注塑机信息
def _add_machine(params: dict):
    # 机器部件
    machine = Machine()
    for name in params:
        if hasattr(Machine, name):
            setattr(machine, name, params[name])
    machine.save()
    # 注射部件
    injectors_info = params["injectors_info"]
    if injectors_info and len(injectors_info):
        for injector_info in injectors_info:
            injector = MachineInjector()
            injector.machine = machine
            if injector_info.get("machine_id"):
                injector_info["machine_id"] = machine.id
            for name in injector_info:
                if hasattr(injector, name):
                    setattr(injector, name, injector_info[name])
            injector.save()
    return machine


# 添加注塑机信息接口
def add_machine(params):
    trademark = params.get("trademark")
    asset_no = params.get("asset_no")
    company_id = params.get("company_id")
    serial_no = params.get("serial_no")
    internal_id = params.get("internal_id")
    data_source = params.get("data_source")
    # 如果注塑机型号为空，则提示：需要填写注塑机型号
    if trademark is None:
        raise BizException(ERROR_INPUT_IS_NULL, "请填写注塑机型号")
    machines = Machine.objects.all()
    error_message = ""
    # if company_id:
    #     machines = machines.filter(company_id=company_id)
    # if data_source:
    #     machines = machines.filter(data_source=data_source)
    #     error_message += "相同注塑机来源,"
    # if asset_no:
    #     machines = machines.filter(asset_no=asset_no)
    #     error_message += "相同资产编号,"
    # if trademark:
    #     machines = machines.filter(trademark=trademark)
    #     error_message += "相同注塑机型号,"
    # if internal_id:
    #     machines = machines.filter(internal_id=internal_id)   
    #     error_message += "相同注塑机ID,"
    if serial_no:
        machines = machines.filter(serial_no=serial_no)
        error_message += "相同设备编码,"   
    if len(machines) == 0:
        with transaction.atomic():
            if "data_source" not in params:
                params["data_source"] = 0
            machine = _add_machine(params)
            return machine.to_dict()
    else:
        raise BizException(ERROR_DATA_EXIST, error_message[:-1])


# 获取注塑机信息
def _get_machine(machine_id):
    if machine_id:
        machine = Machine.objects.filter(pk=machine_id).first()
        if not machine:
            raise BizException(ERROR_DATA_NOT_EXIST, "该注塑机不存在")
        # 注塑机信息
        machine_info = machine.to_dict()
        # 注射部件信息
        injectors = MachineInjector.objects.filter(machine_id=machine_id)

        machine_info.update({ "injectors_info": [ e.to_dict() for e in injectors ] })
        return machine_info


# 读取注塑机信息接口
def get_machine(machine_id):
    if machine_id:
        return _get_machine(machine_id)


# 更新注塑机信息
def _update_machine(machine_id, params):
    if not (params and machine_id):
        return
    
    with transaction.atomic():
        machine = Machine.objects.filter(pk=machine_id).first()
        if not machine:
            raise BizException(ERROR_DATA_NOT_EXIST, "该注塑机不存在")
        
        # 更新机器信息
        for key, value in params.items():
            if hasattr(machine, key):
                setattr(machine, key, value)
        machine.save()

        injectors = list(MachineInjector.objects.filter(machine_id=machine_id))
        injectors_info = params.get("injectors_info", [])
        
        # 更新现有注塑部件的信息
        for num in range(min(len(injectors), len(injectors_info))):
            injector = injectors[num]
            injector_info = injectors_info[num]
            for name, value in injector_info.items():
                if hasattr(injector, name):
                    setattr(injector, name, value)
            injector.save()

        # 增加新的注塑部件
        for injector_info in injectors_info[len(injectors):]:
            injector = MachineInjector(machine=machine, **{k: v for k, v in injector_info.items() if hasattr(MachineInjector, k)})
            injector.save()

        # 删除多余的注塑部件
        if len(injectors) > len(injectors_info):
            to_delete_ids = [injectors[num].id for num in range(len(injectors_info), len(injectors))]
            MachineInjector.objects.filter(id__in=to_delete_ids).delete()


# 更新注塑机信息接口
def update_machine(machine_id, params):
    # 更新时,如果serial_no已存在,且不属于当前注塑机,那么给出提示
    new_serial_no = params.get('serial_no')
    if new_serial_no is not None:
        if Machine.objects.exclude(pk=machine_id).filter(serial_no=new_serial_no).exists():
            raise BizException(ERROR_DATA_EXIST, "相同设备编码")  
    if machine_id:
        _update_machine(machine_id, params)
    return get_machine(machine_id)


# 删除注塑机接口
def delete_machine(machine_id):
    if machine_id:
        machine = Machine.objects.filter(pk=machine_id).first()
        if machine:
            machine.delete()
            injectors = MachineInjector.objects.filter(machine_id=machine_id)
            for num in range(0, len(injectors)):
                injectors[num].delete()
        else:
            raise BizException(ERROR_DATA_NOT_EXIST, "该注塑机不存在")


# 获取机器列表
def get_list_of_machine(
    data_source=None,
    trademark=None,
    machine_type=None,
    power_method=None,
    propulsion_axis=None,
    asset_no=None,
    serial_no=None,
    manufacturer=None,
    max_clamping_force=None,
    machine_id_list=None,
    page_no=None,
    page_size=None,
    company_id=None,
    user_id=None,
    internal_id=None,

    min_mold_size_horizon=None,
    min_mold_size_vertical=None,
    min_mold_thickness=None,
    min_mold_open_stroke=None,
    min_clamping_force=None,
):
    query = Machine.objects.all().order_by("id")
    user_group = admin_service.get_user_group(user_id)
    if trademark:
        query = query.filter(trademark__icontains=trademark)
    if machine_type:
        query = query.filter(machine_type__icontains=machine_type)
    if power_method:
        query = query.filter(power_method__icontains=power_method)
    if propulsion_axis:
        query = query.filter(propulsion_axis__icontains=propulsion_axis)
    if asset_no:
        query = query.filter(asset_no__icontains=asset_no)
    if serial_no:
        query = query.filter(serial_no__icontains=serial_no)
    if manufacturer:
        query = query.filter(manufacturer__icontains=manufacturer)
    if data_source:
        query = query.filter(data_source__icontains=data_source)
    if max_clamping_force:
        query = query.filter(max_clamping_force=max_clamping_force)
    if user_group:
        query = query.filter(company_id__in=user_group)
    elif company_id:
        allow_ids = [ -1, company_id ]
        query = query.filter(company_id__in=allow_ids)
    if machine_id_list:
        query = query.filter(pk__in=machine_id_list)
    if internal_id:
        query = query.filter(internal_id=internal_id)

    # 以下需求为对应模具的注塑机适配
    # 如果该字段的值为空,那么被过滤掉
    if min_mold_size_horizon:
        query = query.filter(min_mold_size_horizon__lte=min_mold_size_horizon,max_mold_size_horizon__gte=min_mold_size_horizon,min_mold_size_horizon__isnull=False,max_mold_size_horizon__isnull=False)
    if min_mold_size_vertical:
        query = query.filter(min_mold_size_vertical__lte=min_mold_size_vertical,max_mold_size_vertical__gte=min_mold_size_vertical,min_mold_size_vertical__isnull=False,max_mold_size_vertical__isnull=False)
    if min_mold_thickness:
        query = query.filter(min_mold_thickness__lte=min_mold_thickness,max_mold_thickness__gte=min_mold_thickness,min_mold_thickness__isnull=False,max_mold_thickness__isnull=False)
    if min_mold_open_stroke:
        query = query.filter(max_mold_open_stroke__gte=min_mold_open_stroke,max_mold_open_stroke__isnull=False)
    if min_clamping_force:
        query = query.filter(max_clamping_force__gte=min_clamping_force,max_clamping_force__isnull=False)
    
    total_count = query.count()
    if page_no and page_size:
        query = paginate(query, page_no, page_size)

    return total_count, [e.to_dict() for e in query]


# 删除多条机器
def delete_multiple_machine(machine_id_list: list):
    for machine_id in machine_id_list:
        delete_machine(machine_id)


# 读取机器和注塑部件的全部字段
def list_machine_injector_view(cleaned_data):
    total, machines = get_list_of_machine(**cleaned_data)

    machine_list = []
    for item in machines:
        machine_list.append(get_machine(item.get("id")))

    return total, machine_list


# 读取机器和注塑部件的前端需要的字段  excel导出
def list_machine_view(cleaned_data,user_id=None):
    total, machines = get_list_of_machine(**cleaned_data,user_id=user_id)

    machine_list = []
    for item in machines:
        machine_part = dict()
        machine_info = get_machine(item.get("id"))
        injectors_info = machine_info.get("injectors_info")

        if machine_info:
            machine_part["id"] = machine_info.get("id")
            machine_part["manufacturer"] = machine_info.get("manufacturer")
            machine_part["trademark"] = machine_info.get("trademark")
            machine_part["asset_no"] = machine_info.get("asset_no")
            machine_part["serial_no"] = machine_info.get("serial_no")
            machine_part["manufacture_date"] = machine_info.get("manufacture_date")
            machine_part["updated_at"] = machine_info.get("updated_at")
            
        if injectors_info:
            machine_part.update(
                {
                    "max_injection_weight": "/".join(
                        str(injector.get("max_injection_weight")) if injector.get("max_injection_weight") else ""
                        for injector in injectors_info
                    )
                }
            )
            machine_part.update(
                {
                    "max_injection_velocity": "/".join(
                        str(injector.get("max_injection_velocity")) if injector.get("max_injection_velocity") else ""
                        for injector in injectors_info
                    )
                }
            )
            machine_part.update(
                {
                    "max_injection_stroke": "/".join(
                        str(injector.get("max_injection_stroke")) if injector.get("max_injection_stroke") else ""
                        for injector in injectors_info
                    )
                }
            )
            machine_part.update(
                {
                    "max_injection_pressure": "/".join(
                        str(injector.get("max_injection_pressure")) if injector.get("max_injection_pressure") else ""
                        for injector in injectors_info
                    )
                }
            )
            machine_part.update(
                {
                    "max_holding_pressure": "/".join(
                        str(injector.get("max_holding_pressure")) if injector.get("max_holding_pressure") else ""
                        for injector in injectors_info
                    )
                }
            )
            machine_part.update(
                {
                    "max_screw_rotation_speed": "/".join(
                        str(injector.get("max_screw_rotation_speed")) if injector.get("max_screw_rotation_speed") else ""
                        for injector in injectors_info
                    )
                }
            )
            machine_part.update(
                {
                    "plasticizing_capacity": "/".join(
                        str(injector.get("plasticizing_capacity")) if injector.get("plasticizing_capacity") else ""
                        for injector in injectors_info
                    )
                }
            )
            machine_part.update(
                {
                    "screw_diameter": "/".join(
                        str(injector.get("screw_diameter")) if injector.get("screw_diameter") else "" 
                        for injector in injectors_info
                    )
                }
            )
        machine_list.append(machine_part)

    return total, machine_list


# 注塑机数据来源 options
def list_machine_data_source(company_id=None):
    query = Machine.objects.filter(company_id=company_id).values("data_source").distinct()
    source_list: list = [{ "value": item.get("data_source") } for item in query ]
    source_list.append({ "value": "系统" })
    return source_list


def list_machine_manufacturer(
        company_id=None, 
        data_source=None, 
        manufacturer=None
    ):
    query = Machine.objects.filter(company_id__in=[ -1, company_id ]).filter(deleted=0).all()
    if data_source:
        query = query.filter(data_source=data_source)
    if manufacturer:
        query = query.filter(manufacturer__icontains=manufacturer)
    query = query.values_list("manufacturer", flat=True).order_by("manufacturer").distinct()
    return list(query)


# 注塑机种类列表 options
def list_machine_trademark(
        company_id=None, 
        data_source=None, 
        trademark=None,
        manufacturer=None,
        serial_no=None,
        asset_no=None,
    ):
    query = Machine.objects.filter(company_id__in=[ -1, company_id ]).filter(deleted=0).all()
    if data_source:
        query = query.filter(data_source=data_source)
    if trademark:
        query = query.filter(trademark__icontains=trademark)
    if manufacturer:
        query = query.filter(manufacturer__contains=manufacturer)
    if serial_no:
        query = query.filter(serial_no__contains=serial_no)
    if asset_no:
        query = query.filter(asset_no__contains=asset_no)
    query = query.values("id", "data_source", "trademark", "asset_no", "serial_no", "manufacturer").order_by("data_source")
    
    # 返回相应螺杆的参数
    injector_map = get_injector_map([ e.get("id") for e in query ])
    ret_data = []
    for ret_item in query:
        ret_item.update({ "injectors": injector_map.get(ret_item.get("id"), []) })
        ret_data.append(ret_item)

    return ret_data


def get_injector_map(list_of_machine_id: list):
    injector_map = {}
    query = MachineInjector.objects.filter(machine_id__in=list_of_machine_id)
    query = query.values("id", "machine_id", "screw_diameter", "max_injection_stroke", "serial_no")
    for item in query:
        injector_map.setdefault(item.get("machine_id"), []).append(item)
    return injector_map


def list_machine_summary(company_id=None):
    # list_machine_status()调用这个方法时,根据序号取值
    query = (
        Machine.objects.filter(company_id=company_id)
        .values_list("id", "trademark", "asset_no", "serial_no", "manufacture_date")
        .order_by("data_source")
    )
    return list(query)


# 根据列头获取下拉提示
def get_prompt_list_of_column(column: str, input_str: str, company_id: int = None):
    items = []
    if company_id:
        query = Machine.objects.filter(company_id__in=[-1, company_id]).filter(deleted=0) # 过滤公司&已删除
    else:
        query = Machine.objects.all()
    if column == "data_source":
        items = query.filter(data_source__icontains=input_str).values_list("data_source", flat=True).order_by("data_source").distinct()
    if column == "trademark":
        items = query.filter(trademark__icontains=input_str).values_list("trademark", flat=True).order_by("trademark").distinct()
    if column == "serial_no":
        items = query.filter(serial_no__icontains=input_str).values_list("serial_no", flat=True).order_by("serial_no").distinct()
    if column == "asset_no":
        items = query.filter(asset_no__icontains=input_str).values_list("asset_no", flat=True).order_by("asset_no").distinct()
    if column == "manufacturer":
        items = query.filter(manufacturer__icontains=input_str).values_list("manufacturer", flat=True).order_by("manufacturer").distinct()
    return list(items)