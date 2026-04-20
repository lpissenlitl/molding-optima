"""
工程服务
"""
from datetime import date
from django.db import transaction
from marshmallow.fields import String
from gis.common.django_ext.models import paginate
from gis.common.exceptions import BizException

from hsmolding.exceptions import ERROR_DATA_NOT_EXIST, ERROR_DATA_EXIST
from hsmolding.models import Project, Product
from hsmolding.const import TrailStatus,MACHINE_TYPE, MOLD_TYPE
from hsmolding.services import export_service
from hsmolding.dao.moldflow_report_model import MoldFlowReportDoc
from hsmolding.dao.reservation_model import MachineAdaptionDoc
from hsmolding.services.machine_adaption_service import get_machine_adaption_dict, add_machine_adaption

# 模具的注塑机适配
from hsmolding.services.machine_service import get_machine
import time


table_data = [
        {
          "mold_desc":"模具编号", 
          "mold_info":"",
          "desc": "注塑机型号",
        },
        {
          "desc": "注塑机编号",
        },
        {
          "mold_desc": "是否适配",
        },
        {
           "mold_desc":"模具类型", 
           "mold_info":"", 
          "desc": "注塑机类型",
        },
        {
           "mold_desc":"模具锁模力(Ton)", 
           "mold_info":"",
          "desc": "锁模力",
        },
        {
           "mold_desc":"模具最大重量(g)", 
           "mold_info":"",
          "desc": "最大注射重量",
        },
        # {
        #   "desc": "最大注射行程",
        # },
        # {
        #   "desc": "停留时间(机器)",
        # },
        # {
        #   "desc": "停留时间(热流道)",
        # },
        # {
        #   "desc": "停留时间(总和)",
        # },
        {
           "mold_desc":"模具尺寸(横)(mm)", 
           "mold_info":"",
          "desc": "最小容模尺寸(横)",
        },
        {
           "mold_desc":"模具尺寸(竖)(mm)", 
           "mold_info":"",
          "desc": "最小容模尺寸(竖)",
        },
        {
           "mold_desc":"模具厚度(mm)", 
           "mold_info":"",
          "desc": "最小容模厚度",
        },
        {
           "mold_desc":"模具尺寸(横)(mm)", 
           "mold_info":"",
          "desc": "最大容模尺寸(横)",
        },
        {
           "mold_desc":"模具尺寸(竖)(mm)", 
           "mold_info":"",
          "desc": "最大容模尺寸(竖)",
        },
        {
           "mold_desc":"模具厚度(mm)", 
           "mold_info":"",   
          "desc": "最大容模厚度",
        },
        {
           "mold_desc":"模具定位圈直径(mm)", 
           "mold_info":"",
          "desc": "定位圈直径",
        },
        {
           "mold_desc":"模具顶出力(KN)", 
           "mold_info":"",
          "desc": "顶出力",
        },
        {
             "mold_desc":"模具顶出行程(mm)", 
           "mold_info":"", 
          "desc": "顶出行程",
        },
        {
           "mold_desc":"模具开模行程(mm)", 
           "mold_info":"",
          "desc": "最大开模行程",
        },
        {
           "mold_desc":"模具喷嘴球径(mm)", 
           "mold_info":"",    
          "desc": "喷嘴球径",
        },
        {
           "mold_desc":"模具喷嘴孔径(mm)", 
           "mold_info":"",  
          "desc": "喷嘴孔径",
        },
        {
          "mold_desc":"约机", 
          "mold_info":"",  
          "desc": "",
        },
        {
          "mold_desc":"注塑机id", 
          "mold_info":"",  
          "desc": "",
        },
]
color_data = [
        {
          "mold_desc":"模具编号", 
          "mold_info":"",
          "desc": "注塑机型号",
        },
        {
          "desc": "注塑机编号",
        },
        {
          "mold_desc": "是否适配",
        },
        {
           "mold_desc":"模具类型", 
           "mold_info":"", 
          "desc": "注塑机类型",
        },
        {
           "mold_desc":"模具锁模力", 
           "mold_info":"",
          "desc": "锁模力",
        },
        {
           "mold_desc":"模具最大重量", 
           "mold_info":"",
          "desc": "最大注射重量",
        },
        # {
        #   "desc": "最大注射行程",
        # },
        # {
        #   "desc": "停留时间(机器)",
        # },
        # {
        #   "desc": "停留时间(热流道)",
        # },
        # {
        #   "desc": "停留时间(总和)",
        # },
        {
           "mold_desc":"模具尺寸(横)", 
           "mold_info":"",
          "desc": "最小容模尺寸(横)",
        },
        {
           "mold_desc":"模具尺寸(竖)", 
           "mold_info":"",
          "desc": "最小容模尺寸(竖)",
        },
        {
           "mold_desc":"模具厚度", 
           "mold_info":"",
          "desc": "最小容模厚度",
        },
        {
           "mold_desc":"模具尺寸(横)", 
           "mold_info":"",
          "desc": "最大容模尺寸(横)",
        },
        {
           "mold_desc":"模具尺寸(竖)", 
           "mold_info":"",
          "desc": "最大容模尺寸(竖)",
        },
        {
           "mold_desc":"模具厚度", 
           "mold_info":"",   
          "desc": "最大容模厚度",
        },
        {
           "mold_desc":"模具定位圈直径", 
           "mold_info":"",
          "desc": "定位圈直径",
        },
        {
           "mold_desc":"模具顶出力", 
           "mold_info":"",
          "desc": "顶出力",
        },
        {
             "mold_desc":"模具顶出行程", 
           "mold_info":"", 
          "desc": "顶出行程",
        },
        {
           "mold_desc":"模具开模行程", 
           "mold_info":"",
          "desc": "最大开模行程",
        },
        {
           "mold_desc":"模具喷嘴球径", 
           "mold_info":"",    
          "desc": "喷嘴球径",
        },
        {
           "mold_desc":"模具喷嘴孔径", 
           "mold_info":"",  
          "desc": "喷嘴孔径",
        },
        {
          "mold_desc":"约机", 
          "mold_info":"",  
          "desc": "",
        },
        {
          "mold_desc":"注塑机id", 
          "mold_info":"",  
          "desc": "",
        },
]
machine_no = 1

error_message = ""


# 新增制品参数
def add_product(project: Project, product_info: dict):
    product = Product()
    product_info["project_id"] = project.id
    for name in product_info:
        if hasattr(product, name):
            setattr(product, name, product_info[name])
    product.save()


# 新增模具中的制品参数
def add_mold_product_infos(project: Project, product_infos: list):
    if product_infos and len(product_infos) > 0:
        for product_info in product_infos:
            add_product(project, product_info)


# 新增工程中的模具参数
def _add_mold(params: dict):
    if "mold_no" in params and "company_id" in params:
        project = get_project_obj_by_mold_no(params["mold_no"], params["company_id"])
        # 新建工程的时候，如果该名称已存在，返回已经存在提示
        if project is not None:
            raise BizException(ERROR_DATA_EXIST, "模号为" + params["mold_no"] + "的模具已存在")
    # 保存工程数据
    with transaction.atomic():
        project = Project()
        for key in params:
            if hasattr(Project, key):
                setattr(project, key, params[key])
        project.save()
        add_mold_product_infos(project, params["product_infos"])

    return project


# 新增工程数据
def add_project(params: dict):
    if "mold_info" in params:
        # 模具信息
        project = _add_mold(params.get("mold_info"))
        products = Product.objects.filter(project_id=project.id, deleted=False).all()
        mold_info = project.to_dict()
        mold_info.update({ "product_infos": [ e.to_dict() for e in products ] })

    # return { "mold_info": mold_info }
    return { "id": project.id }


# 查询工程基本信息
def get_project_obj_by_id(project_id: int):
    project = Project.objects.filter(id=project_id).first()
    return project


# 通过模号即工程名 查工程,不同公司下的模号可以重复
def get_project_obj_by_mold_no(mold_no: str, company_id: int):
    project = Project.objects.filter(mold_no=mold_no).filter(company_id=company_id).filter(deleted=0).first()
    return project


# 查询模具信息(包含各制品信息)
def get_mold_dict_by_id(project_id: int):
    project = get_project_obj_by_id(project_id)
    if not project:
        raise BizException(ERROR_DATA_NOT_EXIST)
    
    products = Product.objects.filter(project_id=project.id).all()
    mold_info = project.to_dict()
    mold_info.update({ "product_infos": [ e.to_dict() for e in products ] })
    return mold_info


# 根据id获取模具相关数据
def get_project(project_id: int):
    # 模具相关数据记录
    mold_info = get_mold_dict_by_id(project_id)
    adaption = get_machine_adaption_dict(project_id, "模具")

    return {
        "mold_info": mold_info,
        "adaption":adaption
    }


# 更新制品信息
def update_product(product_id: int, product_info: dict):
    if product_id and product_info:
        product = Product.objects.filter(id=product_id).first()
        if product:
            for key, value in product_info.items():
                setattr(product, key, value)
            product.save()
        else:
            raise BizException(ERROR_DATA_NOT_EXIST, "制品信息不存在")


# 更新模具中的制品信息
def update_mold_product_infos(project: Project, product_infos: list):
    if project and product_infos:
        products = Product.objects.filter(project_id=project.id)
        for i in range(0, max(len(products), len(product_infos))):

            if len(products) < len(product_infos):
                if i < len(products):
                    update_product(products[i].id, product_infos[i])
                else:
                    add_product(project, product_infos[i])
            else:
                if i < len(product_infos):
                    update_product(products[i].id, product_infos[i])
                else:
                    delete_product(products[i].id)


# 更新模具信息
def _update_mold(project_id: int, mold_info: dict):
    # 更新时,如果mold_no已存在,且不属于当前模具,那么给出提示
    mold_no = mold_info.get('mold_no')
    if mold_no is not None:
        if Project.objects.exclude(pk=project_id).filter(mold_no=mold_no, deleted=False).exists():
            raise BizException(ERROR_DATA_EXIST, "相同模具编号")
    if mold_info and project_id:
        project = get_project_obj_by_id(project_id)
        if project:
            for key, value in mold_info.items():
                setattr(project, key, value)
            project.save()

            update_mold_product_infos(project, mold_info["product_infos"])
        else:
            raise BizException(ERROR_DATA_NOT_EXIST)


# 根据id更新模具信息
def update_project(project_id: int, params: dict):
    if "mold_info" in params:
        _update_mold(project_id, params["mold_info"])
        # return get_mold_dict_by_id(project_id)
        return { "id": project_id }


# 删除制品信息
def delete_product(product_id: int):
    product = Product.objects.filter(id=product_id).first()
    if product:
        product.delete()
    else:
        raise BizException(ERROR_DATA_NOT_EXIST, "制品信息不存在")


# 根据id删除模具
def delete_project(project_id: int):
    # 数据软删除, deleted = 1
    project = Project.objects.filter(id=project_id).first()
    if project:
        project.deleted = 1
        project.save()
    else:
        raise BizException(ERROR_DATA_NOT_EXIST)


# 根据工程id匹配模流
def get_moldflow_map(list_of_project_id: list):
    moldflow_map = {}
    query = MoldFlowReportDoc.objects.filter(project_id__in=list_of_project_id)
    for item in query:
        moldflow_map.setdefault(item.project_id, item.to_dict())
    return moldflow_map


# 根据工程id获得注塑机适配
def get_adaption_map(list_of_project_id: list):
    adaption_map = {}
    query = MachineAdaptionDoc.objects.filter(p_id__in=list_of_project_id)
    for item in query:
        adaption_map.setdefault(item.p_id, item.to_dict())
    return adaption_map


# 获取工程列表
def get_list_of_project(
    company_id: int = None,
    user_id: int = None,
    mold_no: String = None,
    mold_type: String = None,
    mold_name: String = None,
    product_type: String = None,
    product_name: String = None,
    customer: String = None,
    project_engineer: String = None,
    design_engineer: String = None,
    production_engineer: String = None,
    order_date: date = None,
    project_id_list: list = None,
    mold_no_list: list = None,
    page_no: int = None,
    page_size: int = None,
):
    query = Project.objects.all()

    if company_id:
        query = query.filter(company_id=company_id)
    if mold_no:
        query = query.filter(mold_no__icontains=mold_no)
    if mold_type:
        query = query.filter(mold_type__icontains=mold_type)
    if mold_name:
        query = query.filter(mold_name__icontains=mold_name)
    if product_type:
        query = query.filter(product_type__icontains=product_type)
    if product_name:
        query = query.filter(product_name__icontains=product_name)
    if customer:
        query = query.filter(customer__icontains=customer)
    if project_engineer:
        query = query.filter(project_engineer__icontains=project_engineer)
    if design_engineer:
        query = query.filter(design_engineer__icontains=design_engineer)
    if production_engineer:
        query = query.filter(production_engineer__icontains=production_engineer)
    if order_date:
        query = query.filter(order_date=order_date)
    if project_id_list:
        query = query.filter(id__in=project_id_list)
    if mold_no_list:
        query = query.filter(mold_no__in=mold_no_list)
        
    query = query.filter(deleted=0) # 已删除的不显示
    query = query.order_by("-created_at") # 根据创建时间排序
    total = query.count()

    if page_no and page_size:
        query = paginate(query, page_no, page_size)

    moldflow_map = get_moldflow_map([ e.id for e in query ])
    adaption_map = get_adaption_map([ e.id for e in query ])
    ret_data = []
    for item in query:
        ret_item = item.to_dict()
        ret_item.update({ "moldflow": moldflow_map.get(item.id) })
        ret_item.update({ "adaption": adaption_map.get(item.id) })
        ret_data.append(ret_item)

    return total, ret_data


# 删除多个工程
def delete_multiple_project(list_of_project: list):
    for project_id in list_of_project:
        delete_project(project_id)


# 处理多个工程
def handle_multiple_project(params: dict):
    project_id_list = params.get("project_id_list")
    flag = params.get("flag")
    if flag == "export_list":
        return export_service.export_project_table(project_id_list)


# 根据列头获取下拉提示
def get_prompt_list_of_column(column: str, input_str: str, company_id: int = None):
    items = []
    if company_id:
        query = Project.objects.filter(company_id=company_id).filter(deleted=0) # 过滤公司&已删除
    else:
        query = Project.objects
    if column == "mold_no":
        # 模具编号列表
        query = query.filter(mold_no__icontains=input_str).values_list("id", "mold_no")
        items = [ {  "mold_id": q[0], "value": q[1] } for q in query ]
    elif column == "customer":
        # 客户列表
        items = query.filter(customer__icontains=input_str).values_list("customer", flat=True).order_by("customer").distinct()
    elif column == "mold_type":
        # 模具类型列表
        items = query.filter(mold_type__icontains=input_str).values_list("mold_type", flat=True).order_by("mold_type").distinct()
    elif column == "mold_name":
        # 模具名称
        items = query.filter(mold_name__icontains=input_str).values_list("mold_name", flat=True).order_by("mold_name").distinct()
    elif column == "product_type":
        # 制品类别列表
        items = query.filter(product_type__icontains=input_str).values_list("product_type", flat=True).order_by("product_type").distinct()
    elif column == "product_small_type":
        # 制品类别列表
        items = query.filter(product_small_type__icontains=input_str).values_list("product_small_type", flat=True).order_by("product_small_type").distinct()
    elif column == "product_name":
        # 制品名称列表
        items = query.filter(product_name__icontains=input_str).values_list("product_name", flat=True).order_by("product_name").distinct()
    elif column == "project_engineer":
        # 项目工程师列表
        items = query.filter(project_engineer__icontains=input_str).values_list("project_engineer", flat=True).order_by("project_engineer").distinct()
    elif column == "design_engineer":
        # 设计工程师列表
        items = query.filter(design_engineer__icontains=input_str).values_list("design_engineer", flat=True).order_by("design_engineer").distinct()
    elif column == "production_engineer":
        # 制作工程师列表
        items = query.filter(production_engineer__icontains=input_str).values_list("production_engineer", flat=True).order_by("production_engineer").distinct()
    elif column == "trial_no":
        # 试模次数
        items = query.filter(trial_no__icontains=input_str).values_list("trial_no", flat=True).order_by("trial_no").distinct()
    return list(items)


def get_product_prompt_list_of_column(column: str, input_str: str, project_id: int = None):
    items = []
    if project_id:
        query = Product.objects.filter(project_id=project_id).filter(deleted=0)
    else:
        query = Product.objects
    if column == "gate_type":
        #浇口类别
        items = query.filter(gate_type__icontains=input_str).values_list("gate_type", flat=True).order_by("gate_type").distinct()
    return list(items)


# 主要考虑:
# 1.锁模力
# 2.注射重量
# 3.单色注塑机 #停留时间
# 4.容模尺寸,长宽,最大和最小
# 5.开模行程
# 6.容模厚度
# 7.顶出行程
def calculate_apation(mold_info, machine_id):
    # 对比每个属性,得出是否满足条件
    # 如果有一个条件不满足,则不适配
    # 如果所有条件都满足,则适配
    global table_data
    global color_data
    global machine_no
    not_adapted = 0
    not_confirmed = 0
    machine_info = get_machine(machine_id)
    injectors_info = machine_info.get("injectors_info")
    
    table_data[0]["values"][machine_no] = machine_info.get("trademark")
    table_data[1]["values"][machine_no] = machine_info.get("serial_no")
    # 1.选对型
    # 单色模具可以用双色机，双色模具不能用单色机，依此类推双色、三色、四色……
    table_data[3]["values"][machine_no] = machine_info.get("machine_type")
    if machine_info.get("machine_type"):
        table_data[3]["values"][machine_no] = str(machine_info.get("machine_type"))
        if mold_info.get("mold_type"):
            if MACHINE_TYPE.get(machine_info.get("machine_type")) < MOLD_TYPE.get(mold_info.get("mold_type")[4:]):
                not_adapted = 1
                color_data[3]["values"][machine_no] = "red"
            else:
                color_data[3]["values"][machine_no] = "rgb(0,201,87)"
        else:
            not_confirmed = 1
    else:
        not_confirmed = 1
        print(f'{machine_id}machine_type: {machine_info.get("machine_type")} {mold_info.get("mold_type")}')     

    # 4.锁得住
    if machine_info.get("max_clamping_force"):
        table_data[4]["mold_desc"] = "模具锁模力("+machine_info.get("clamping_force_unit")+")"
        table_data[4]["values"][machine_no] = str(machine_info.get("max_clamping_force"))
        if mold_info.get("min_clamping_force"):
            if machine_info.get("max_clamping_force") <= mold_info.get("min_clamping_force"):
                not_adapted = 1
                color_data[4]["values"][machine_no] = "red"
            elif float(machine_info.get("max_clamping_force"))*0.85 <= float(mold_info.get("min_clamping_force")):
                color_data[4]["values"][machine_no] = "rgb(255,160,0)"
            else:
                color_data[4]["values"][machine_no] = "rgb(0,201,87)"
        else:
            not_confirmed = 1
    else:
        not_confirmed = 1
        print(f'{machine_id}max_clamping_force: {machine_info.get("max_clamping_force")} {mold_info.get("min_clamping_force")}')
    
    # 6.射得稳:注塑机最大重量 vs 产品重量+流动重量
    # 注塑机最大注射量的25%≤产品总重量（包括所有的制品和流道）≤注塑机最大注射量的75%
    if injectors_info[0].get("max_injection_weight"):
        table_data[5]["values"][machine_no] = str(injectors_info[0].get("max_injection_weight"))
        if mold_info.get("product_total_weight"):
            if injectors_info[0].get("max_injection_weight") <= mold_info.get("product_total_weight"):
                not_adapted = 1
                color_data[5]["values"][machine_no] = "red"
            elif float(injectors_info[0].get("max_injection_weight"))*0.75 <= float(mold_info.get("product_total_weight")):
                color_data[5]["values"][machine_no] = "rgb(255,160,0)"  # 黄色
            elif float(injectors_info[0].get("max_injection_weight"))*0.25 >= float(mold_info.get("product_total_weight")):
                color_data[5]["values"][machine_no] = "rgb(255,160,0)"  # 黄色
            else:
                color_data[5]["values"][machine_no] = "rgb(0,201,87)"  # 绿色
        else:
            not_confirmed = 1
    else:
        not_confirmed = 1
        print(f'{machine_id}max_injection_weight: {machine_info.get("max_injection_weight")} {mold_info.get("product_total_weight")}')
    
    # 模具中的最大注射行程是多少,通过重量算体积,通过螺杆面积算行程

    # 2.放得下:注塑机最小容模尺寸（横）≤模具尺寸（横）≤注塑机最大容模尺寸（横）
    # 注塑机最小容模尺寸（竖）≤模具尺寸（竖）≤注塑机最大容模尺寸（竖）；
    # 注塑机最小容模厚度≤模具厚度≤注塑机最大容模厚度。
    if machine_info.get("min_mold_size_horizon"):
        table_data[6]["values"][machine_no] = str(machine_info.get("min_mold_size_horizon"))
        if mold_info.get("size_horizon"):
            if machine_info.get("min_mold_size_horizon") > mold_info.get("size_horizon"):
                not_adapted = 1
                color_data[6]["values"][machine_no] = "red"
            else:
                color_data[6]["values"][machine_no] = "rgb(0,201,87)"
        else:
            not_confirmed = 1
    else:
        not_confirmed = 1
        print(f'{machine_id}min_mold_size_horizon: {machine_info.get("min_mold_size_horizon")} {mold_info.get("size_horizon")}')
    
    if machine_info.get("min_mold_size_vertical"):
        table_data[7]["values"][machine_no] = str(machine_info.get("min_mold_size_vertical"))
        if mold_info.get("size_vertical"):
            if machine_info.get("min_mold_size_vertical") > mold_info.get("size_vertical"):
                not_adapted = 1
                color_data[7]["values"][machine_no] = "red"
            else:
                color_data[7]["values"][machine_no] = "rgb(0,201,87)"
        else:
            not_confirmed = 1
    else:
        not_confirmed = 1
        print(f'{machine_id}min_mold_size_vertical: {machine_info.get("min_mold_size_vertical")} {mold_info.get("size_vertical")}')        
    
    if machine_info.get("min_mold_thickness"):
        table_data[8]["values"][machine_no] = str(machine_info.get("min_mold_thickness"))
        if mold_info.get("size_thickness"):
            if machine_info.get("min_mold_thickness") > mold_info.get("size_thickness"):
                not_adapted = 1
                color_data[8]["values"][machine_no] = "red"
            else:
                color_data[8]["values"][machine_no] = "rgb(0,201,87)"
        else:
            not_confirmed = 1
    else:
        not_confirmed = 1
        print(f'{machine_id}min_mold_thickness: {machine_info.get("min_mold_thickness")} {mold_info.get("size_thickness")}')
        
    if machine_info.get("max_mold_size_horizon"):
        table_data[9]["values"][machine_no] = str(machine_info.get("max_mold_size_horizon"))
        if mold_info.get("size_horizon"):
            if machine_info.get("max_mold_size_horizon") < mold_info.get("size_horizon"):
                not_adapted = 1
                color_data[9]["values"][machine_no] = "red"
            else:
                color_data[9]["values"][machine_no] = "rgb(0,201,87)"
        else:
            not_confirmed = 1
    else:
        not_confirmed = 1
        print(f'{machine_id}max_mold_size_horizon: {machine_info.get("max_mold_size_horizon")} {mold_info.get("size_horizon")}')
    
    if machine_info.get("max_mold_size_vertical"):
        table_data[10]["values"][machine_no] = str(machine_info.get("max_mold_size_vertical"))
        if mold_info.get("size_vertical"):
            if machine_info.get("max_mold_size_vertical") < mold_info.get("size_vertical"):
                not_adapted = 1
                color_data[10]["values"][machine_no] = "red"
            else:
                color_data[10]["values"][machine_no] = "rgb(0,201,87)"
        else:
            not_confirmed = 1
    else:
        not_confirmed = 1
        print(f'{machine_id}max_mold_size_vertical: {machine_info.get("max_mold_size_vertical")} {mold_info.get("size_vertical")}')
    
    if machine_info.get("max_mold_thickness"):
        table_data[11]["values"][machine_no] = str(machine_info.get("max_mold_thickness"))
        if mold_info.get("size_thickness"):
            if machine_info.get("max_mold_thickness") < mold_info.get("size_thickness"):
                not_adapted = 1
                color_data[11]["values"][machine_no] = "red"
            else:
                color_data[11]["values"][machine_no] = "rgb(0,201,87)"
        else:
            not_confirmed = 1
    else:
        not_confirmed = 1
        print(f'{machine_id}max_mold_thickness: {machine_info.get("max_mold_thickness")} {mold_info.get("size_thickness")}')
    
    # 2.放得下:定位圈直径
    # 考虑多色
    if machine_info.get("locate_ring_diameter"):
        table_data[12]["values"][machine_no] = str(machine_info.get("locate_ring_diameter"))
        if mold_info.get("locate_ring_diameter"):
            if machine_info.get("locate_ring_diameter") != mold_info.get("locate_ring_diameter"):
                not_adapted = 1
                color_data[12]["values"][machine_no] = "red"
            else:
                color_data[12]["values"][machine_no] = "rgb(0,201,87)"  
        else:
            not_confirmed = 1
    else:
        not_confirmed = 1
        print(f'{machine_id}locate_ring_diameter: {machine_info.get("locate_ring_diameter")} {mold_info.get("locate_ring_diameter")}')
     
    # 3.拿得出:顶出力,顶出行程,开模行程
    if machine_info.get("max_ejection_force"):
        table_data[13]["values"][machine_no] = str(machine_info.get("max_ejection_force"))
        if mold_info.get("ejector_force"):
            if machine_info.get("max_ejection_force") < mold_info.get("ejector_force"):
                not_adapted = 1
                color_data[13]["values"][machine_no] = "red"
            else:
                color_data[13]["values"][machine_no] = "rgb(0,201,87)"  
        else:
            not_confirmed = 1
    else:
        not_confirmed = 1
        print(f'{machine_id}ejector_force: {machine_info.get("max_ejection_force")} {mold_info.get("ejector_force")}')
 
    if machine_info.get("max_ejection_stroke"):
        table_data[14]["values"][machine_no] = str(machine_info.get("max_ejection_stroke"))
        if mold_info.get("ejector_stroke"):
            if machine_info.get("max_ejection_stroke") and mold_info.get("ejector_stroke"):    
                if machine_info.get("max_ejection_stroke") < mold_info.get("ejector_stroke"):
                    not_adapted = 1  
                    color_data[14]["values"][machine_no] = "red"
                else:
                    color_data[14]["values"][machine_no] = "rgb(0,201,87)"  
        else:
            not_confirmed = 1
    else:
        not_confirmed = 1
        print(f'{machine_id}max_ejection_stroke: {machine_info.get("max_ejection_stroke")} {mold_info.get("ejector_stroke")}')
        
    # A.对于单分型面模：
    # 塑件顶出行程（mm）+产品厚度（mm）≤最大开模行程（mm）-10；
    # B.对于双分型面：
    # 塑件顶出行程（mm）+产品厚度（mm）+取出浇注系统所需的定模座板与流道板间分离的距离（mm）≤最大开模行程-10。
    if machine_info.get("max_mold_open_stroke"):
        table_data[15]["values"][machine_no] = str(machine_info.get("max_mold_open_stroke"))
        if mold_info.get("mold_opening_stroke"):
            if "两板模" in mold_info.get("mold_type"):
                if float(machine_info.get("max_mold_open_stroke"))-10 < float((mold_info.get("mold_opening_stroke")+mold_info.get("size_thickness"))):
                    not_adapted = 1
                    color_data[15]["values"][machine_no] = "red"
                else:
                    color_data[15]["values"][machine_no] = "rgb(0,201,87)"  
            elif "三板模" in mold_info.get("mold_type") and mold_info.get("drain_distance"):
                if float(machine_info.get("max_mold_open_stroke"))-10 < float(mold_info.get("mold_opening_stroke")+mold_info.get("size_thickness")+mold_info.get("drain_distance")):
                    not_adapted = 1
                    color_data[15]["values"][machine_no] = "red"
                else:
                    color_data[15]["values"][machine_no] = "rgb(0,201,87)"
            else:
                not_confirmed = 1
        else:
            not_confirmed = 1
    else:
        not_confirmed = 1
        print(f'{machine_id}max_opening_stroke: {machine_info.get("max_mold_open_stroke")} {mold_info.get("mold_opening_stroke")}')
    
    # 5.射得好:1)模具浇口衬套球径＞注塑机喷嘴球径；	
    # 2)模具浇口衬套孔径＞注塑机喷嘴孔径。
    # 考虑多色
    if injectors_info[0].get("nozzle_sphere_diameter"):
        table_data[16]["values"][machine_no] = str(injectors_info[0].get("nozzle_sphere_diameter"))
        if mold_info.get("product_infos")[0].get("sprue_sphere_radius"):
            if injectors_info[0].get("nozzle_sphere_diameter") and mold_info.get("product_infos")[0].get("sprue_sphere_radius"):    
                if injectors_info[0].get("nozzle_sphere_diameter") < mold_info.get("product_infos")[0].get("sprue_sphere_radius"):
                    not_adapted = 1  
                    color_data[16]["values"][machine_no] = "red"
                else:
                    color_data[16]["values"][machine_no] = "rgb(0,201,87)"  
        else:
            not_confirmed = 1
    else:
        not_confirmed = 1
        print(f'{machine_id}sprue_sphere_radius: {injectors_info[0].get("nozzle_sphere_diameter")} {mold_info.get("product_infos")[0].get("sprue_sphere_radius")}')
 
    if injectors_info[0].get("nozzle_hole_diameter"):
        table_data[17]["values"][machine_no] = str(injectors_info[0].get("nozzle_hole_diameter"))
        if mold_info.get("product_infos")[0].get("sprue_hole_diameter"):
            if injectors_info[0].get("nozzle_hole_diameter") and mold_info.get("product_infos")[0].get("sprue_hole_diameter"):    
                if injectors_info[0].get("nozzle_hole_diameter") < mold_info.get("product_infos")[0].get("sprue_hole_diameter"):
                    not_adapted = 1  
                    color_data[17]["values"][machine_no] = "red"
                else:
                    color_data[17]["values"][machine_no] = "rgb(0,201,87)"  
        else:
            not_confirmed = 1
    else:
        not_confirmed = 1
        print(f'{machine_id}sprue_hole_diameter: {injectors_info[0].get("nozzle_hole_diameter")} {mold_info.get("product_infos")[0].get("sprue_hole_diameter")}')
        
    # 7.射得好:所需注射压力不超过注塑机最大注射压力的85%。

    # 8.射得快:注塑机最大注射速率10%≤所需注射速率≤注塑机最大注射速率90%
    table_data[2]["values"][machine_no] = "否" if not_adapted == 1 else "-" if not_confirmed == 1 else "是"
    table_data[18]["values"][machine_no] = ""
    table_data[19]["values"][machine_no] = str(machine_id)


def set_mold_info(mold_info):
    global table_data
    table_data[0]["mold_info"] = mold_info.get("mold_no")
    table_data[3]["mold_info"] = mold_info.get("mold_type")
    table_data[4]["mold_info"] = str(mold_info.get("min_clamping_force")) if mold_info.get("min_clamping_force") else None
    table_data[5]["mold_info"] = str(mold_info.get("product_total_weight")) if mold_info.get("product_total_weight") else None
    table_data[6]["mold_info"] = str(mold_info.get("size_horizon")) if mold_info.get("size_horizon") else None
    table_data[7]["mold_info"] = str(mold_info.get("size_vertical")) if mold_info.get("size_vertical") else None
    table_data[8]["mold_info"] = str(mold_info.get("size_thickness")) if mold_info.get("size_thickness") else None
    table_data[9]["mold_info"] = str(mold_info.get("size_horizon")) if mold_info.get("size_horizon") else None
    table_data[10]["mold_info"] = str(mold_info.get("size_vertical")) if mold_info.get("size_vertical") else None
    table_data[11]["mold_info"] = str(mold_info.get("size_thickness")) if mold_info.get("size_thickness") else None
    table_data[12]["mold_info"] = str(mold_info.get("locate_ring_diameter")) if mold_info.get("locate_ring_diameter") else None
    table_data[13]["mold_info"] = str(mold_info.get("ejector_force")) if mold_info.get("ejector_force") else None
    table_data[14]["mold_info"] = str(mold_info.get("ejector_stroke")) if mold_info.get("ejector_stroke") else None
    table_data[15]["mold_info"] = str(mold_info.get("mold_opening_stroke")) if mold_info.get("mold_opening_stroke") else None
    table_data[16]["mold_info"] = str(mold_info.get("product_infos")[0].get("sprue_sphere_radius")) if mold_info.get("product_infos")[0].get("sprue_sphere_radius") else None
    table_data[17]["mold_info"] = str(mold_info.get("product_infos")[0].get("sprue_hole_diameter")) if mold_info.get("product_infos")[0].get("sprue_hole_diameter") else None


def machine_list(project_id, machine_id_list=None):
    global table_data
    global color_data
    global machine_no
    machine_no = 0
    if isinstance(project_id, str):
        project_id = int(project_id)
    mold_info = get_mold_dict_by_id(project_id)
    set_mold_info(mold_info)
    # 根据注塑机的数量初始化values的长度
    for item in table_data:
        values = [None] * len(machine_id_list)
        item["values"] = values
    for item in color_data:
        values = [None] * len(machine_id_list)
        item["values"] = values
    for machine_id in machine_id_list:
        calculate_apation(mold_info, machine_id)
        machine_no += 1
    add_machine_adaption({
        "p_id":project_id,
        "adaption_type":"模具",
        "adaption_no":"A"+time.strftime("%Y%m%d%H%M%S", time.localtime()),
        "machine_id_list":machine_id_list,
        "table_data":table_data,
        "color_data":color_data,
        "machine_num":len(machine_id_list),
        "deleted":0
        })
    return {"mold_info":mold_info, "machine_num":len(machine_id_list),"table_data":table_data, "color_data":color_data}
