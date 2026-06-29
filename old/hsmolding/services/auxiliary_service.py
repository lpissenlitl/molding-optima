
from gis.common.exceptions import BizException
from gis.common.django_ext.models import paginate

from hsmolding.models import AuxiliaryMachine
from hsmolding.exceptions import ERROR_DATA_NOT_EXIST, ERROR_DATA_EXIST

# 添加辅机信息
def _add_auxiliary(params: dict):
    auxiliary = AuxiliaryMachine()
    for name in params:
        if hasattr(AuxiliaryMachine, name):
            setattr(auxiliary, name, params[name])
    auxiliary.save()
    return auxiliary


# 添加辅机信息接口
def add_auxiliary(params: dict):
    # 先检查是否存在,按照辅机编号唯一
    auxiliary = AuxiliaryMachine.objects.all()
    serial_num = params.get("serial_num")
    if serial_num:
        auxiliary = AuxiliaryMachine.objects.filter(serial_num=serial_num)
    if len(auxiliary) == 0:
        _add_auxiliary(params)
    else:
        raise BizException(ERROR_DATA_EXIST, "相同辅机编号")


# 获取辅机信息
def _get_auxiliary(auxiliary_id: int):
    if auxiliary_id:
        auxiliary = AuxiliaryMachine.objects.filter(id=auxiliary_id).first()
        if not auxiliary:
            raise BizException(ERROR_DATA_NOT_EXIST, message="该辅机不存在")
        auxiliary_dict = auxiliary.to_dict()
        return auxiliary_dict
        

# 获取辅机信息接口
def get_auxiliary(auxiliary_id: int):
    if auxiliary_id:
        return _get_auxiliary(auxiliary_id)


# 更新辅机信息
def _update_auxiliary(auxiliary_id: int, params: dict):
    if auxiliary_id and params:
        auxiliary = AuxiliaryMachine.objects.filter(id=auxiliary_id).first()
        if not auxiliary:
            raise BizException(ERROR_DATA_NOT_EXIST, message="该辅机不存在")
        # 更新时,如果serial_num已存在,且不属于当前辅机,那么给出提示
        new_serial_no = params.get('serial_num')
        if new_serial_no is not None:
            if AuxiliaryMachine.objects.exclude(pk=auxiliary_id).filter(serial_num=new_serial_no).exists():
                raise BizException(ERROR_DATA_EXIST, "相同辅机编号")
        if auxiliary:
            for key, value in params.items():
                setattr(auxiliary, key, value)
            auxiliary.save()


# 更新辅机信息接口
def update_auxiliary(auxiliary_id: int, params: dict):
    if auxiliary_id:
        _update_auxiliary(auxiliary_id, params)
    return get_auxiliary(auxiliary_id)


# 删除辅机接口
def delete_auxiliary(auxiliary_id: int):
    if auxiliary_id:
        auxiliary = AuxiliaryMachine.objects.filter(id=auxiliary_id).first()
        if auxiliary:
            auxiliary.delete()
        else:
            raise BizException(ERROR_DATA_NOT_EXIST, message="该辅机不存在")


# 获取辅机列表
def get_list_of_auxiliary(
    machine_id = None,
    auxiliary_type = None,
    serial_num = None,
    manufacture = None,
    auxiliary_id_list = None,
    page_no=None,
    page_size=None
):
    query = AuxiliaryMachine.objects.all()

    if machine_id:
        query = query.filter(machine_id=machine_id)
    if serial_num:
        query = query.filter(serial_num__icontains=serial_num)
    if auxiliary_type:
        query = query.filter(auxiliary_type__icontains=auxiliary_type)
    if manufacture:
        query = query.filter(manufacture__icontains=manufacture)
    if auxiliary_id_list:
        query = query.filter(pk__in=auxiliary_id_list)
    total_count = query.count()
    if page_no and page_size:
        query = paginate(query, page_no, page_size)
    
    return total_count, [ e.to_dict() for e in query ]


# 删除多条辅机
def delete_multiple_auxiliary(auxiliary_id_list: list):
    for auxiliary_id in auxiliary_id_list:
        delete_auxiliary(auxiliary_id)
    