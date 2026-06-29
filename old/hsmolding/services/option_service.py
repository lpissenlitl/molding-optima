from hsmolding.models import CustomOption


"""
func: 根据条件获取自定义的下拉选项
interface_view: 界面
interface_select: 应用组件
"""
def get_list_of_option(
    interface_view: str = None, 
    interface_select: str = None,
    company_id: int = None,
):
    if interface_view:
        query = CustomOption.objects.filter(interface_view=interface_view).all()
        if interface_select:
            query = query.filter(interface_select=interface_select)
        if company_id:
            query = query.filter(company_id=company_id) 
        return [ { "company_id": row.company_id,"interface_view": row.interface_view,"interface_select": row.interface_select, "label": row.label, "value": row.value , "key":row.key, "view_desc":row.view_desc, "select_desc":row.select_desc} for row in query ]
    else:
        return []
    

def get_list_of_interface_view(company_id):
    query = CustomOption.objects.filter(company_id=company_id).values_list("interface_view", "view_desc").distinct()
    return [{"value":item[0],"label":item[1]} for item in query]


def get_list_of_interface_select(
    interface_view: str = None, 
    company_id: int = None,
):
    query = CustomOption.objects.filter(company_id=company_id, interface_view=interface_view).values_list("interface_select", "select_desc").distinct()
    return [{"value":item[0],"label":item[1]} for item in query]


def add_option(params):
    new_options = params.get("options")
    custom_options = None
    if new_options:
        if type(new_options[0]) == object:
            custom_options = CustomOption.objects.filter(company_id=new_options[0].company_id, interface_view=new_options[0].interface_view, interface_select=new_options[0].interface_select)
        elif type(new_options[0]) == dict:
            custom_options = CustomOption.objects.filter(company_id=new_options[0].get("company_id"), interface_view=new_options[0].get("interface_view"), interface_select=new_options[0].get("interface_select"))
        # 下拉框选项的更新分为三种情况：
        # 1.下拉框选项的个数保持不变
        if custom_options:
            for num in range(0, min(len(custom_options), len(new_options))):
                custom_option = custom_options[num]
                new_option = new_options[num]
                for name in new_option:
                    if hasattr(CustomOption, name):
                        setattr(custom_option, name, new_option[name])
                custom_option.save()
            # 2.下拉框选项的个数增多，多出来的部分要增加
            if len(custom_options) < len(new_options):
                for new_option in new_options[len(custom_options) :]:
                    custom_option = CustomOption()
                    for name in new_option:
                        if hasattr(CustomOption, name):
                            setattr(custom_option, name, new_option[name])
                    custom_option.save()
            # 3.下拉框选项的个数减少，减少的部分要删除
            elif len(custom_options) > len(new_options):
                for num in range(len(new_options), len(custom_options)):
                    custom_option = custom_options[num]
                    custom_option.delete()


def init_data(interface_view=None, interface_select=None, company_id=None):
    custom_options = CustomOption.objects.filter(company_id=0).all()
    if interface_view:
        custom_options = custom_options.filter(interface_view=interface_view)
    if interface_select:
        custom_options = custom_options.filter(interface_select=interface_select)        
    for option in custom_options:
        option.id = None
        option.company_id = company_id
        custom_option = CustomOption()
        option = option.to_dict()
        for name in option:
            if hasattr(CustomOption, name):
                setattr(custom_option, name, option[name])
        custom_option.save()
