import logging
from django.conf import settings
from gis.common.django_ext.models import paginate

from mdprocess.models import RuleKeyword, RuleMethod
from mdprocess.dao.rule_model import RuleFlowDoc

from gis.common.exceptions import BizException
from hsmolding.exceptions import ERROR_DATA_NOT_EXIST, ERROR_RULE_ERROR, ERROR_FILE_TYPE
from mdprocess.const import KeyWord, optimizeKeyWord, LocationKeyWord, Paramkeyword, DEFECT_CONST, DEFECTS_NAME_LIST
import numpy as np
import datetime
from django.db.models import Q
from mdprocess.services.rule_predence_test import rule_predence_test
import chardet
import os
import copy


# 新增关键字
def _add_rule_keyword(params: dict):
    rule_keyword = RuleKeyword()
    for name in params:
        if hasattr(RuleKeyword, name):
            setattr(rule_keyword, name, params[name])
    rule_keyword.save()
    return rule_keyword


# 新增关键字信息接口
def add_rule_keyword(params: dict):
    rule_keyword = _add_rule_keyword(params)
    if rule_keyword:
        return rule_keyword.to_dict()


# 获取关键字信息
def _get_rule_keyword(rule_keyword_id):
    if rule_keyword_id:
        rule_keyword = RuleKeyword.objects.filter(id=rule_keyword_id).first()
        if not rule_keyword:
            raise BizException(ERROR_DATA_NOT_EXIST, message="该关键字不存在")
        return rule_keyword


# 获取关键字信息接口
def get_rule_keyword(rule_keyword_id):
    rule_keyword = _get_rule_keyword(rule_keyword_id)
    return rule_keyword.to_dict()


def _update_rule_keyword(rule_keyword_id, params: dict):
    rule_keyword = _get_rule_keyword(rule_keyword_id)
    if rule_keyword:
        if params:
            for key, value in params.items():
                setattr(rule_keyword, key, value)
        rule_keyword.save()
    else:
        raise BizException(ERROR_DATA_NOT_EXIST, message="该关键字不存在")


# 更新关键字信息接口
def update_rule_keyword(rule_keyword_id, params: dict):
    _update_rule_keyword(rule_keyword_id, params)


# 删除关键字信息
def delete_rule_keyword(rule_keyword_id):
    # rule_keyword = _get_rule_keyword(rule_keyword_id)
    # rule_keyword.delete()
    update_rule_keyword(rule_keyword_id, {"deleted": 1})


# 获取关键字列表
def get_list_of_rule_keyword(
    name=None,
    keyword_type=None,
    show_on_page=None,
    subrule_no=None,
    product_small_type=None,
    polymer_abbreviation=None,
    rule_type=None,
    page_no=None,
    page_size=None,
):
    query = RuleKeyword.objects.all().filter(deleted=0, keyword_type__in=["参数", "缺陷"])
    if name:
        query = query.filter(name__icontains=name)
    if keyword_type:
        query = query.filter(keyword_type=keyword_type)
    if show_on_page:
        query = query.filter(show_on_page=show_on_page)
    if subrule_no:
        query = query.filter(subrule_no__icontains=subrule_no)
    if product_small_type:
        query = query.filter(product_small_type__icontains=product_small_type)
    if polymer_abbreviation:
        query = query.filter(polymer_abbreviation__icontains=polymer_abbreviation)
    if rule_type:
        query = query.filter(rule_type=rule_type)

    total_count = query.count()
    if page_no and page_size:
        query = paginate(query, page_no, page_size)

    return total_count, [e.to_dict() for e in query]


# 新增规则方法
def _add_rule_method(params: dict):
    rule_method = RuleMethod()
    for key, value in params.items():
        if hasattr(RuleMethod, key):
            setattr(rule_method, key, value)
    rule_method.save()
    return rule_method


# 新增规则方法
def add_rule_method(params: dict):
    rule_method = _add_rule_method(params)
    if rule_method:
        return rule_method.to_dict()


# 获取规则库信息
def _get_rule_method(rule_method_id):
    if rule_method_id:
        rule = RuleMethod.objects.filter(id=rule_method_id).first()
        if not rule:
            raise BizException(ERROR_DATA_NOT_EXIST, message="该规则不存在")
        return rule


# 获取规则库信息接口
def get_rule_method(rule_method_id):
    rule_method = _get_rule_method(rule_method_id)
    return rule_method.to_dict()


# 更新规则库信息
def update_rule_method(rule_method_id, params: dict):
    rule_method = _get_rule_method(rule_method_id)
    if params:
        for key, value in params.items():
            setattr(rule_method, key, value)
    rule_method.save()


# 更新规则库信息接口
def _update_rule_method(defect_name, params):
    if params:
        if(params[0].get("rule_type") == "基础库"):
            rule_method_list = RuleMethod.objects.all().filter(rule_type="基础库",defect_name=defect_name)
        else:
            rule_method_list = RuleMethod.objects.all().filter(
                deleted=0,
                subrule_no=params[0].get("subrule_no"),
                polymer_abbreviation=params[0].get("polymer_abbreviation"),
                product_small_type=params[0].get("product_small_type"),
                defect_name=defect_name
                )
        # 更新分为三种情况：
        # 1.个数保持不变
        for num in range(0, min(len(params), len(rule_method_list))):
            rule_method = rule_method_list[num]
            rule_method_info = params[num]
            for name in rule_method_info:
                if hasattr(RuleMethod, name):
                    setattr(rule_method, name, rule_method_info.get(name))
            rule_method.save()
        # 2.个数增多，多出来的部分要增加
        if len(rule_method_list) < len(params):
            for rule_method_info in params[len(rule_method_list) :]:
                rule_method = RuleMethod()
                for name in rule_method_info:
                    if hasattr(RuleMethod, name):
                        setattr(rule_method, name, rule_method_info.get(name))
                rule_method.save()
        # 3.个数减少，减少的部分要删除
        elif len(rule_method_list) > len(params):
            for num in range(len(params), len(rule_method_list)):
                rule_method = rule_method_list[num]
                rule_method.delete()


# 删除规则库信息
def delete_rule_method(rule_method_id):
    # rule = _get_rule_method(rule_method_id)
    # rule.delete()
    update_rule_method(rule_method_id, {"deleted": 1})


# 按照subrule_no删除规则
def delete_rule_method_by_no(subrule_no):
    _, rule_method_list = get_list_of_rule_method(subrule_no=subrule_no)
    for rule_method in rule_method_list:
        delete_rule_method(rule_method.get("id"))
    # 同时把流程图对应子规则禁用
    update_rule_flow({"rule_library": subrule_no, "enable": False})


def get_list_of_rule_method(
    polymer_abbreviation=None,
    product_small_type=None,
    defect_name=None,
    defect_desc=None,
    subrule_no=None,
    rule_type=None,
    is_auto=None,
    enable=None,
    rule_description=None,
    rule_explanation=None,
    page_no=None,
    page_size=None
):
    query = RuleMethod.objects.all().filter(deleted=0)

    if polymer_abbreviation:
        query = query.filter(
            polymer_abbreviation__icontains=polymer_abbreviation)
    if product_small_type:
        query = query.filter(product_small_type__icontains=product_small_type)
    if defect_name:
        query = query.filter(defect_name__icontains=defect_name)
    if defect_desc:
        query = query.filter(defect_desc__icontains=defect_desc)
    if subrule_no:
        query = query.filter(subrule_no__icontains=subrule_no)
    if rule_type:
        query = query.filter(rule_type__icontains=rule_type)
    if is_auto or is_auto == 0:
        query = query.filter(is_auto=is_auto)
    if enable or enable == 0:
        query = query.filter(enable=enable)
    if rule_description:
        if rule_description == 'add':
            query = query.filter(
                    Q(rule_description__icontains='add') | Q(rule_description__icontains='reduce')
            )
        else:
            query = query.filter(rule_description__icontains=rule_description)
    if rule_explanation:
        query = query.filter(rule_explanation__icontains=rule_explanation)
    query = query.order_by("defect_name")
    total_count = query.count()
    if page_no and page_size:
        query = paginate(query, page_no, page_size)

    return total_count, [e.to_dict() for e in query]


def get_prompt_list_of_keyword_column(column: str, input_str: str):
    items = []
    query = RuleKeyword.objects.all()
    if column == "name":
        items = query.filter(name__icontains=input_str, keyword_type__in=["参数", "缺陷"]).values_list(
            "name", flat=True).distinct()

    return list(items)


def get_prompt_list_of_method_column(column: str, input_str: str):
    items = []
    query = RuleMethod.objects.filter(deleted=0,enable=1)
    if column == "product_small_type":
        items = query.filter(product_small_type__icontains=input_str).values_list(
            "product_small_type", flat=True).distinct()
    if column == "polymer_abbreviation":
        items = query.filter(polymer_abbreviation__icontains=input_str).values_list(
            "polymer_abbreviation", flat=True).distinct()
    if column == "defect_name":
        items = query.filter(defect_name__icontains=input_str).values_list(
            "defect_name", flat=True).distinct()

    return list(items)


def read_rule_from_file(rules_path=None, ranges_path=None):
    rule_array = []
    if rules_path:
        with open(rules_path, 'rb') as f:
            encode = chardet.detect((f.read()))
            with open(rules_path, encoding=encode.get("encoding")) as f:
                for line in f.readlines():
                    line = line.strip('\n')
                    if line:
                        if not line.startswith("#"):
                            rule_array.append({"rule_description": line})

    keyword_array = []
    if ranges_path:
        dtype_dict = {'names': ('col1', 'col2', 'col3', 'col4', 'col5', 'col6', 'col7'),
                    'formats': ('U20', 'i4', 'f4', 'f4', 'f4', 'f4', 'f4')}
        records = np.loadtxt(ranges_path, dtype=dtype_dict,
                        encoding='utf-8', delimiter=',')
        for line in records[['col1', 'col2', 'col3', 'col4', 'col7']]:
            keyword_array.append(
                dict(zip(['keyword', 'lvl', 'min_val', 'max_val', 'step'], line)))

    return rule_array, keyword_array


def load_rule_from_database(polymer_abbreviation=None, product_small_type=None, subrule_no=None, rule_id_list=None):
    rule_methods = RuleMethod.objects.all().filter(deleted=0).filter(enable=1)
    if subrule_no:
        rule_methods = rule_methods.filter(subrule_no=subrule_no)
    if rule_id_list:
        rule_methods = rule_methods.filter(
            id__in=rule_id_list)
    # 如果没有匹配制品和材料的规则,那么使用通用规则
    if not rule_methods:
        rule_methods = RuleMethod.objects.all().filter(
            deleted=0).filter(enable=1).filter(product_small_type="通用")
    rule_library = next(iter(rule_method.subrule_no for rule_method in rule_methods if rule_method.subrule_no is not None), None)
    rule_array = [{
        'rule_description': rule_method.rule_description
    } for rule_method in rule_methods]
    rule_priority = []
    for rule_method in rule_methods:
        if rule_method.priority == None:
            rule_method.priority = 1
        rule_priority.append(rule_method.priority)

    rule_keywords = RuleKeyword.objects.all().filter(deleted=0)
    keyword_array = [{
        'keyword': rule_keyword.name,
        'lvl': rule_keyword.level,
        'min_val': rule_keyword.all_range_min,
        'max_val': rule_keyword.all_range_max,
        'step': rule_keyword.action_max_val
    } for rule_keyword in rule_keywords]

    return rule_array, keyword_array, rule_library, rule_priority


def change_rule_to_explanation(rule):
    words_list = rule.strip().split()
    if len(words_list) == 0:
        return -1
    is_pre = False
    preconditions = "如果"
    solutions = "那么"
    for phase in words_list:
        if phase == 'IF':
            is_pre = True
        elif phase in ['Then', 'THEN']:
            is_pre = False
        elif phase == 'AND':
            continue
        else:
            try:
                words = phase.split('_')
                if KeyWord.get(words[0]):
                    if is_pre:
                        if words[0] not in DEFECT_CONST:
                            if words[0][:2] == 'DL':
                                if LocationKeyWord.get(words[1]):
                                    preconditions += KeyWord.get(words[0]) + \
                                        LocationKeyWord.get(words[1]) + ","
                                else:
                                    logging.error(f'{LocationKeyWord.get(words[1])}为空')

                            elif len(words)>1:
                                # 工艺参数条件,键为参数名,值为参数模糊级别、条件类型
                                if Paramkeyword.get(words[1]):
                                    preconditions += KeyWord.get(words[0]) + \
                                        Paramkeyword.get(words[1]) + ","
                                else:
                                    logging.error(f'{Paramkeyword.get(words[1])}为空')
                            else:
                                logging.error(f"{words}")
                        else:
                            # 缺陷类型条件,键为缺陷类型,值为缺陷严重程度、缺陷位置、条件类型
                            if KeyWord.get(words[1]):
                                preconditions += KeyWord.get(words[0]) + \
                                    KeyWord.get(words[1]) + ","
                            else:
                                logging.error(f'{KeyWord.get(words[1])}为空')

                    else:
                        # 工艺参数修正,键为参数名,值为参数调整方向、调整模糊级别、条件类型
                        if words[1] == "adjust":
                            solutions += "弹窗请检查"+KeyWord.get(words[0])+"是否不合理。"
                        else:
                            value = optimizeKeyWord.get(words[2])
                            if not value:  # 表示幅度,用0到100的小数
                                value = words[2]
                            solutions += KeyWord.get(words[0]) + KeyWord.get(
                                words[1]) + value + "。"
                else:
                    logging.error(f'{KeyWord.get(words[0])}为空')
            except Exception as e:
                print(f"当前错误{e.__traceback__.tb_lineno} {e.args}")
                raise BizException(ERROR_RULE_ERROR, message=rule)

    return preconditions + solutions


def get_rule_flow(
    rule_library=None,  # 基础库, 或 R20220609163348
    rule_type=None,  # 基础库, 或 子规则库
    product_small_type=None,  # 制品
    polymer_abbreviation=None,  # 塑料
):
    query = RuleFlowDoc.objects.all()
    if rule_library:
        query = query.filter(rule_library=rule_library)
    if rule_type:
        query = query.filter(rule_type=rule_type)
    if product_small_type:
        query = query.filter(product_small_type=product_small_type)
    if polymer_abbreviation:
        query = query.filter(polymer_abbreviation=polymer_abbreviation)
    query = query.first()
    return query.to_dict() if query else None


# 新增规则流程图
def add_rule_flow(params: dict):
    rule_flow = update_rule_flow(params)
    if not rule_flow:
        rule_flow = RuleFlowDoc(**params)
        rule_flow.save()
        if rule_flow:
            show_dict = change_flow_to_rule(rule_flow.to_dict())

    return rule_flow.to_dict() if rule_flow else None


def update_rule_flow(params: dict):
    rule_library = params.get("rule_library")
    rule_flow = RuleFlowDoc.objects.filter(rule_library=rule_library).first()
    if rule_flow:
        rule_flow.update(**params)
        # 读取修改后最新的流程数据
        rule_flow = RuleFlowDoc.objects.filter(rule_library=rule_library).first()
        if rule_flow:
            # 修改rule_method
            show_dict = change_flow_to_rule(rule_flow.to_dict())
        return rule_flow
    else:
        return None


# 复制规则关键字
def copy_rule_keyword(rule_flow, show_dict):
    # 如果对应子规则库编号,已经存在这一条关键字,那么修改,否则新增
    rule_keyword_list = RuleKeyword.objects.filter(subrule_no=rule_flow.get("rule_library"),deleted=0)
    for rule_keyword in rule_keyword_list: 
        rule_keyword = rule_keyword.to_dict()
        # 根据规则语句，自动选择过滤关键词，修改is_all为1，表示可见。其他关键词,is_all为0
        if show_dict:
            rule_keyword["show_on_page"] = show_dict.get(rule_keyword.get("name"))
            if rule_keyword.get("name") not in show_dict.keys():
                rule_keyword["show_on_page"] = 0
            rule_keyword["updated_at"]=datetime.datetime.now()
            _update_rule_keyword(rule_keyword.get("id"), rule_keyword)
    if not rule_keyword_list:
        rule_keyword_list = RuleKeyword.objects.filter(deleted=-1)
        for rule_keyword in rule_keyword_list:
            rule_keyword = rule_keyword.to_dict()
            del rule_keyword["id"]
            rule_keyword["deleted"] = 0
            rule_keyword["subrule_no"]=rule_flow.get("rule_library")
            rule_keyword["polymer_abbreviation"]=rule_flow.get("polymer_abbreviation")
            rule_keyword["product_small_type"]=rule_flow.get("product_small_type")
            rule_keyword["rule_type"]=rule_flow.get("rule_type")
            rule_keyword["updated_at"]=datetime.datetime.now()
            # 根据规则语句，自动选择过滤关键词，修改is_all为1，表示可见。其他关键词,is_all为0
            if show_dict:
                rule_keyword["show_on_page"] = show_dict.get(rule_keyword.get("name"))
                if rule_keyword.get("name") not in show_dict.keys():
                    rule_keyword["show_on_page"] = 0
            _add_rule_keyword(rule_keyword)


def get_value_by_rule(level, name):
    value = 1 if level == "low" else 1.5 if level == "mid" else 1.9
    # 不同类型的参数，默认初始值不同，暂时全部默认为2
    # 1. 注射时间、保压时间，默认为0.5
    # 2. 背压默认为1
    # 3. 其余均默认为2
    if "IT" in name or "PT" in name:
        return 0.5*value
    if "MBP" in name:
        return 1*value
    else:
        return 2*value
        

# 从流程图到基础规则库
def change_flow_to_rule(rule_flow):
    defects = rule_flow.get("defect_data")
    show_dict = {}

    for defect_data in defects:
        rule_method_list = []
        graph_data = defect_data.get("graph_data")
        nodes = graph_data.get("nodes")
        rule_method = defect_data.get("rule_method")
        solution_ways = rule_method.get("solution_ways")
        defect_name = defect_data.get("defect_name")
        ways_list = []
        # 子规则和基础库要分开生成
        if rule_flow.get("rule_type") == "子规则库":
            for solution_way in solution_ways:
                if solution_way:
                    for level in ["low"]:
                        ways_list.append(generate_rules(nodes, solution_way, level))
            # 根据优先级重写子规则
            rule_description_list = rule_predence_test(defect_data.get("defect_desc"), ways_list)
            for rule_description in rule_description_list:
                rule_method_list = generate_list(nodes, solution_way, rule_method_list, rule_flow, defect_data, show_dict, rule_description)
        else:
            for solution_way in solution_ways:
                if solution_way:
                    for level in ["low", "mid", "high"]:
                        rule_description = generate_rules(nodes, solution_way, level)
                        rule_method_list = generate_list(nodes, solution_way, rule_method_list, rule_flow, defect_data, show_dict, rule_description)
        _update_rule_method(defect_name, rule_method_list)
    return show_dict


def generate_rules(nodes, solution_way, level):
    if nodes[solution_way[2]].get('properties').get('action') == "adjust":
        rule_description = f"IF {nodes[solution_way[0]].get('properties').get('rule_name')}_{level} AND {nodes[solution_way[1]].get('properties').get('rule_name')}_{nodes[solution_way[1]].get('properties').get('action')} THEN {nodes[solution_way[2]].get('properties').get('rule_name')}_{nodes[solution_way[2]].get('properties').get('action')}_请检查{KeyWord.get(nodes[solution_way[2]].get('properties').get('rule_name'))}是否不合理。"
    else:
        rule_description = f"IF {nodes[solution_way[0]].get('properties').get('rule_name')}_{level} AND {nodes[solution_way[1]].get('properties').get('rule_name')}_{nodes[solution_way[1]].get('properties').get('action')} THEN {nodes[solution_way[2]].get('properties').get('rule_name')}_{nodes[solution_way[2]].get('properties').get('action')}_{get_value_by_rule(level, nodes[solution_way[2]].get('properties').get('rule_name'))} "
    return rule_description


def generate_list(nodes, solution_way, rule_method_list, rule_flow, defect_data, show_dict, rule_description):
    # 新增规则到rule_method表中
    rule_method_list.append({
        "polymer_abbreviation":rule_flow.get("polymer_abbreviation"),
        "rule_description": rule_description,
        "rule_explanation":change_rule_to_explanation(rule_description),
        "is_auto":0,
        "enable":1,
        "deleted":0,
        "product_small_type":rule_flow.get("product_small_type"),
        "subrule_no":rule_flow.get("rule_library"),
        "rule_type":rule_flow.get("rule_type"),
        "defect_name":defect_data.get("defect_name"),
        "defect_desc":defect_data.get("defect_desc"),
        "updated_at":datetime.datetime.now()
    })
    show_dict[nodes[solution_way[0]].get('properties').get('rule_name')] = 1
    show_dict[nodes[solution_way[1]].get('properties').get('rule_name')] = 1
    show_dict[nodes[solution_way[2]].get('properties').get('rule_name')] = 1
    return rule_method_list


def get_prompt_list_of_column(column: str, input_str: str, polymer_abbreviation=None, product_small_type=None):
    items = []
    query = RuleFlowDoc.objects.filter(rule_type="子规则库", enable=True).order_by("-created_at")
    if product_small_type:
        query = query.filter(product_small_type__icontains=product_small_type)
    if polymer_abbreviation:
        query = query.filter(polymer_abbreviation__icontains=polymer_abbreviation)
    if column == "product_small_type":
        items = set(query.filter(product_small_type__icontains=input_str).values_list("product_small_type"))
    if column == "polymer_abbreviation":
        items = set(query.filter(polymer_abbreviation__icontains=input_str).values_list("polymer_abbreviation"))
    if column == "rule_library":
        items = set(query.filter(rule_library__icontains=input_str).values_list("rule_library"))
    if column == "rule_type":
        items = set(query.filter(rule_type__icontains=input_str).values_list("rule_type"))
    return list(items)


# 获得缺陷名称列表
def get_defect_list():
    query = RuleKeyword.objects.filter(keyword_type="缺陷", rule_type="基础库").values("name", "comment").distinct()
    defect_list: list = [{ "label": item.get("comment"), "desc": item.get("name") } for item in query ]
    return defect_list


# 获得基础关键字列表
def get_keyword_dict():
    query = RuleKeyword.objects.filter(rule_type="基础库").values("name", "comment").distinct()
    final_result = {}
    for item in query:
        name = item["name"]
        comment = item["comment"]

        final_result[name] = comment

    # 返回最终结果字典
    return final_result


def import_rule(request):
    file = request.FILES.get("file", None)
    if "txt" not in file.name:
        raise BizException(ERROR_FILE_TYPE)
    else:
        absolute_path = settings.FILE_STORAGE_PATH + "gsid_"+str(request.user.get("company_id"))+"/rule/"
        if not os.path.exists(absolute_path):
            os.makedirs(absolute_path)
        model_path = absolute_path + file.name
        with open(model_path, "wb+") as f:
            # 分块写入
            for chunk in file.chunks():
                f.write(chunk)
    subrule_no = request.POST.get("subrule_no")
    product_small_type = request.POST.get("product_small_type")
    polymer_abbreviation = request.POST.get("polymer_abbreviation")
    rule_array, _ = read_rule_from_file(rules_path=model_path)
    defect_dict = {}
    for defect in DEFECTS_NAME_LIST:
        defect_dict[defect] = []
    for row in rule_array:
        defect_desc = get_defect_desc(row.get("rule_description"))
        defect_name = KeyWord.get(defect_desc)
        rule_detail = {
            "rule_type": "子规则库",
            "subrule_no": subrule_no,
            "polymer_abbreviation": polymer_abbreviation if polymer_abbreviation != "null" else None,
            "product_small_type": product_small_type if product_small_type != "null" else None,
            "rule_description": row.get("rule_description"),
            "rule_explanation": change_rule_to_explanation(row.get("rule_description")),
            "defect_name": defect_name,
            "defect_desc": defect_desc, 
            "is_auto": 0,
            "enable": 1,
            "deleted": 0
        }
        defect_dict[defect_name].append(rule_detail)
    message = f"共有规则{len(rule_array)}条<br>"
    for defect_name in DEFECTS_NAME_LIST:
        if defect_dict[defect_name]:
            message += import_rule_method(defect_name, defect_dict[defect_name])
    return {"message": message}


def import_rule_method(defect_name, params):
    if params:
        if(params[0].get("rule_type") == "基础库"):
            rule_method_list = RuleMethod.objects.all().filter(rule_type="基础库",defect_name=defect_name)
        else:
            rule_method_list = RuleMethod.objects.all().filter(
                deleted=0,
                subrule_no=params[0].get("subrule_no"),
                polymer_abbreviation=params[0].get("polymer_abbreviation"),
                product_small_type=params[0].get("product_small_type"),
                defect_name=defect_name
                )
    message = f"{defect_name}规则{len(params)}条,其中"
    # 如果对应缺陷,之前的规则为空,那么直接把导入的写进数据库
    if rule_method_list == []:
        for p in params:
            _add_rule_method(p)
        message += f"新增规则{len(params)}条"
    # 如果对应缺陷,之前有规则,那么新规则,需要一条一条核对,之前是否有完全一样,如果一样,那么略过,如果不同,那么写进数据库
    else:
        existed = 0
        new = 0
        for p in params:
            if p.get("rule_description") in [r.rule_description for r in rule_method_list]:
                existed += 1
            else:
                _add_rule_method(p)
                new += 1
        if existed != 0:
            message += f"{existed}条已存在,"
        if new != 0:
            message += f"新增规则{new}条"
    return message+"<br>"


def get_defect_desc(rule):
    words_list = rule.strip().split()
    if len(words_list) == 0:
        return -1
    for phase in words_list:
        if '_' in phase:
            words = phase.split('_')
            return words[0]


def add_defect(params):
    # 1. 在rule_keyword表中增加缺陷
    # 2. 在mongo中,复制参考的流程图
    # 3. 在rule_keyword中增加缺陷相关关键字
    rule_keyword = params.get("rule_keyword")
    add_rule_keyword(rule_keyword)

    previous_length = params.get("previous_length")
    # 计算DL的ID值 401+ previous_length *6 +8 
    # 预留id最大600,再最多增加15个,也就是缺陷个数最多32个,大于之后,用id自增
    first_id = None
    if previous_length < 32:
        first_id = 401+ previous_length *6 +8 
    for i in range(6):
        inner_keyword = {
            "name": "DL" + rule_keyword.get("name") + str(i+1),
            "level":3,
            "all_range_min": 0,
            "all_range_max": 1,
            "action_max_val": -1,
            "keyword_type": "缺陷位置",
            "deleted": 0,
            "rule_type": "基础库",
            "comment": rule_keyword.get("comment")+"在"+str(i+1)+"段",
            "show_on_page": None
        }
        if previous_length < 32:
            inner_keyword["id"] = first_id + i
        add_rule_keyword(inner_keyword)
    rule_flow = get_rule_flow(
        rule_library="基础库",  # 基础库, 或 R20220609163348
        rule_type="基础库"
    )
    refer_defect_data = None
    defect_data = rule_flow.get("defect_data")
    for defect in defect_data:
        if defect.get("defect_name") == params.get("refer_defect"):
            # 使用深拷贝来创建一个新的缺陷字典
            refer_defect_data = copy.deepcopy(defect)
            
            # 更新defect_name和defect_desc
            refer_defect_data["defect_name"] = rule_keyword.get("comment")
            refer_defect_data["defect_desc"] = rule_keyword.get("name")

            # 更新graph_data中的nodes的第一个节点的text值
            if "graph_data" in refer_defect_data and "nodes" in refer_defect_data["graph_data"]:
                nodes = refer_defect_data["graph_data"]["nodes"]
                if nodes:
                    nodes[0]["text"] = rule_keyword.get("comment")
                    break
    if refer_defect_data:
        rule_flow.get("defect_data").append(refer_defect_data)
        del rule_flow["_id"]
        update_rule_flow(rule_flow)
