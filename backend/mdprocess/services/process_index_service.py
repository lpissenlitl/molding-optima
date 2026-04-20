from gis.common.django_ext.models import paginate

from mdprocess.models import ProcessIndex
from gis.common.exceptions import BizException
from hsmolding.exceptions import ERROR_DATA_NOT_EXIST

import os
import datetime
import logging
import time

from django.conf import settings
from openpyxl import load_workbook

# 新增制品工艺参数
def _add_process_index(params: dict):
    process = ProcessIndex()
    for name in params:
        if hasattr(ProcessIndex, name):
            setattr(process, name, params[name])
    process.save()
    return process


# 新增制品工艺参数接口
def add_process_index(params: dict):
    if params.get("process_no"):
        process = ProcessIndex.objects.filter(process_no=params.get("process_no")).first()
        if process:
            update_process_index(process.id, params)
            return process.to_dict()
        else:
            process = _add_process_index(params)
            return process.to_dict()


# 获取工艺参数对象
def _get_process_index(process_index_id):
    if process_index_id:
        process = ProcessIndex.objects.filter(id=process_index_id).first()
        if not process:
            raise BizException(ERROR_DATA_NOT_EXIST, message="该工艺记录不存在")
        return process


# 获取制品工艺参数接口
def get_process_index(process_index_id):
    process = _get_process_index(process_index_id)
    return process.to_dict()


# 更新制品工艺参数接口
def update_process_index(process_index_id, params: dict):    
    process = _get_process_index(process_index_id)
    if process:
        if params:
            for key, value in params.items():
                setattr(process, key, value)
        process.save()
    else:
        raise BizException(ERROR_DATA_NOT_EXIST, message="该工艺记录不存在")


# 删除制品工艺参数
def delete_process_index(process_index_id):
    process = _get_process_index(process_index_id)
    if process:
        process.delete()
    else:
        raise BizException(ERROR_DATA_NOT_EXIST, message="该工艺记录不存在")


# 删除多条工艺优化记录
def delete_multiple_process_index(process_id_list: list):
    for process_index_id in process_id_list:
        delete_process_index(process_index_id)


# 获取制品工艺参数列表
def get_list_of_process_index(
    company_id=None,
    status=None,
    page_no=None,
    page_size=None,
    mold_no=None,
    gate_type=None,
    product_type=None,
    product_name=None,
    machine_id=None,
    machine_data_source=None,
    machine_trademark=None,
    start_date=None,
    end_date=None,
    process_id_list=None,
    data_sources=None,
    mold_trials_no=None,
):
    query = ProcessIndex.objects.all().order_by("-created_at")
    if company_id:
        query = query.filter(company_id=company_id)
    if status:
        query = query.filter(status=status)
    if mold_no:
        query = query.filter(mold_no__icontains=mold_no)
    if gate_type:
        query = query.filter(gate_type=gate_type)
    if product_type:
        query = query.filter(product_type=product_type)
    if product_name:
        query = query.filter(product_name__icontains=product_name)
    if machine_id:
        query = query.filter(machine_id=machine_id)
    if machine_data_source:
        query = query.filter(machine_data_source=machine_data_source)
    if machine_trademark:
        query = query.filter(machine_trademark=machine_trademark)
    if start_date:
        query = query.filter(created_at__gte=datetime.datetime.combine(start_date, datetime.datetime.min.time()))
    if end_date:
        query = query.filter(created_at__lte=datetime.datetime.combine(end_date, datetime.datetime.max.time()))
    if process_id_list:
        query = query.filter(pk__in=process_id_list)
    if data_sources:
        query = query.filter(data_sources=data_sources)
    if mold_trials_no:
        query = query.filter(mold_trials_no=mold_trials_no)
    query = query.filter(deleted=0)
    total_count = query.count()
    if page_no and page_size:
        query = paginate(query, page_no, page_size)

    transfer_map = get_transfer_map([ e.id for e in query ])
    ret_data = []
    for item in query:
        ret_item = item.to_dict()
        ret_item.update({"machine_adaption":transfer_map.get(item.id, [])})
        ret_data.append(ret_item)
    return total_count, ret_data
    # return total_count, [e.to_dict() for e in query]


# 查看当前工艺是否移植过
def get_transfer_map(list_of_process_id):
    transfer_map = {}
    process_list = ProcessIndex.objects.filter(data_sources="工艺移植", mold_trials_no__in=list_of_process_id)
    for transfer_process in process_list:
        transfer_map.setdefault(int(transfer_process.mold_trials_no), []).append(transfer_process.to_dict())
    return transfer_map


def export_process_index(params):
    total, process_list = get_list_of_process_index(process_id_list=params.get("process_id_list"))
    # 读取文件
    wb = load_workbook(settings.TEMPLATE_PATH + "standard/teplt_process_index.xlsx")
    if not wb:
        return { "url": "" }
    sheet = wb["Sheet1"]
    row = 2
    if total > 0:
        for index, testing in enumerate(process_list):
            sheet["A"+str(index+2)] = str(index+1)
            sheet["B"+str(index+2)] = testing["mold_no"]
            sheet["C"+str(index+2)] = testing["cavity_num"]
            sheet["D"+str(index+2)] = testing["product_no"]
            sheet["E"+str(index+2)] = testing["product_type"]
            sheet["F"+str(index+2)] = testing["product_name"]
            sheet["G"+str(index+2)] = testing["machine_trademark"]
            sheet["H"+str(index+2)] = testing["machine_serial_no"]
            sheet["I"+str(index+2)] = testing["polymer_trademark"]
            sheet["J"+str(index+2)] = testing["runner_length"]
            sheet["K"+str(index+2)] = testing["runner_weight"]
            sheet["L"+str(index+2)] = testing["gate_type"]
            sheet["M"+str(index+2)] = testing["gate_num"]
            sheet["N"+str(index+2)] = testing["gate_shape"]
            sheet["O"+str(index+2)] = testing["product_total_weight"]
            sheet["P"+str(index+2)] = testing["product_max_thickness"]
            sheet["Q"+str(index+2)] = testing["product_ave_thickness"]
            sheet["R"+str(index+2)] = testing["product_max_length"]
            sheet["S"+str(index+2)] = datetime.datetime.strftime(testing["created_at"], "%Y%m%d")

    date = time.strftime("%Y%m%d%H%M%S", time.localtime())
    folder_relative_path = f"temp/"
    file_name = str("process_index_list") + date + ".xlsx"
    file_relative_path = f"{folder_relative_path}{file_name}"
    file_absolute_path = f"{settings.FILE_STORAGE_PATH}{file_relative_path}"

    if not os.path.exists(f"{settings.FILE_STORAGE_PATH}{folder_relative_path}"):
        os.makedirs(f"{settings.FILE_STORAGE_PATH}{folder_relative_path}")
    wb.save(file_absolute_path)
    
    return { "url": file_relative_path }
