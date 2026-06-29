from marshmallow import fields
from gis.common.django_ext.forms import BaseSchema, PaginationBaseSchema, CNDatetimeField



# 产品(form)--product_schema
class ProductSchema(BaseSchema):
    id = fields.Integer(required=False, allow_none=True)
    project_id = fields.Integer(required=False, allow_none=True)

    mold_type = fields.String(required=False, allow_none=True)
    inject_part = fields.String(required=True, allow_none=False)
    # product_no = fields.String(required=False, allow_none=True)
    # product_name = fields.String(required=False, allow_none=True)

    ave_thickness = fields.Float(required=False, allow_none=True)
    max_thickness = fields.Float(required=True, allow_none=False)
    min_thickness = fields.Float(required=False, allow_none=True)
    flow_length = fields.Float(required=True, allow_none=False)
    single_volume = fields.Float(required=False, allow_none=True)
    single_weight = fields.Float(required=False, allow_none=True)

    locate_ring_diameter = fields.Float(required=False, allow_none=True)  # 定位圈直径
    sprue_hole_diameter = fields.Float(required=False, allow_none=True)  # 喷嘴孔直径
    sprue_sphere_radius = fields.Float(required=False, allow_none=True)  # 喷嘴球半径
    runner_type = fields.String(required=True, allow_none=False)  # 流道类型
    hot_runner_num = fields.Integer(required=False, allow_none=True)
    valve_num = fields.Integer(required=False, allow_none=True)  # 热流道控制阀数量
    runner_length = fields.Float(required=True, allow_none=False)  # 流道长度
    runner_weight = fields.Float(required=True, allow_none=False)  # 流道重量
    # hot_runner_volume = fields.Float(required=False, allow_none=True)  # 热流道总体积
    gate_type = fields.String(required=True, allow_none=False)  # 浇口类别
    gate_num = fields.Integer(required=True, allow_none=False)  # 浇口数量
    gate_shape = fields.String(required=True, allow_none=False)  # 浇口形状
    gate_area = fields.Float(required=False, allow_none=True)  # 浇口横截面积
    gate_radius = fields.Float(required=False, allow_none=True)  # 浇口半径(圆)
    gate_length = fields.Float(required=False, allow_none=True)  # 浇口长(矩形)
    gate_width = fields.Float(required=False, allow_none=True)  # 浇口宽(矩形)
    

# 工程(form)--project_index_schema
class ProjectIndexSchema(BaseSchema):
    '''
    注塑模具信息表单
    '''

    id = fields.Integer(required=False, allow_none=True)
    company_id = fields.Integer(required=True, allow_none=False)
    created_at = CNDatetimeField(required=False, allow_none=True)
    updated_at = CNDatetimeField(required=False, allow_none=True)
    deleted = fields.Integer(required=False, allow_none=True)

    status = fields.Integer(required=False, allow_none=True)  # 模具当前状态
    mold_no = fields.String(required=True, allow_none=False)  # 模具编号
    mold_name = fields.String(required=False, allow_none=True)  # 模具名称
    mold_type = fields.String(required=False, allow_none=True)  # 模具类别
    cavity_num = fields.String(required=True, allow_none=False)  # 型腔数量

    product_no = fields.String(required=False, allow_none=True)  # 制品编号
    product_name = fields.String(required=True, allow_none=False)  # 制品名称
    product_type = fields.String(required=False, allow_none=True)  # 制品类别
    product_category = fields.String(required=False, allow_none=True)  # 制品品类
    product_small_type = fields.String(required=True, allow_none=False)
    # product_ave_thickness = fields.Float(required=False, allow_none=True)  # 平均壁厚
    # product_max_thickness = fields.Float(required=False, allow_none=True)  # 最大壁厚
    # product_min_thickness = fields.Float(required=False, allow_none=True)  # 最小壁厚
    # product_max_length = fields.Float(required=False, allow_none=True)  # 制品流长
    # product_single_volume = fields.Float(required=False, allow_none=True)  # 单件体积
    # product_single_weight = fields.Float(required=False, allow_none=True)  # 单件重量
    product_total_weight = fields.Float(required=True, allow_none=False)  # 总重量
    product_projected_area = fields.Float(required=False, allow_none=True)  # 总投射面积

    product_infos = fields.Nested(ProductSchema, many=True)

    locate_ring_diameter = fields.Float(required=False, allow_none=True)  # 定位圈直径
    # sprue_hole_diameter = fields.Float(required=False, allow_none=True)  # 喷嘴孔直径
    # sprue_sphere_radius = fields.Float(required=False, allow_none=True)  # 喷嘴球半径
    # runner_type = fields.String(required=False, allow_none=True)  # 流道类型
    # valve_num = fields.Integer(required=False, allow_none=True)  # 热流道控制阀数量
    # runner_length = fields.Float(required=False, allow_none=True)  # 流道长度
    # runner_weight = fields.Float(required=False, allow_none=True)  # 流道重量
    # hot_runner_volume = fields.Float(required=False, allow_none=True)  # 热流道总体积
    # gate_type = fields.String(required=False, allow_none=True)  # 浇口类别
    # gate_num = fields.Integer(required=False, allow_none=True)  # 浇口数量
    # gate_shape = fields.String(required=False, allow_none=True)  # 浇口形状
    # gate_area = fields.Float(required=False, allow_none=True)  # 浇口横截面积
    # gate_radius = fields.Float(required=False, allow_none=True)  # 浇口半径(圆)
    # gate_length = fields.Float(required=False, allow_none=True)  # 浇口长(矩形)
    # gate_width = fields.Float(required=False, allow_none=True)  # 浇口宽(矩形)

    cavity_cooling_water_diameter = fields.Float(required=False, allow_none=True)  # 前模冷却水直径
    cavity_cooling_circuit_number = fields.Integer(required=False, allow_none=True)  # 前模冷却回路组数
    cavity_water_nozzle_specification = fields.Float(required=False, allow_none=True)  # 前模水嘴安装规格
    core_cooling_water_diameter = fields.Float(required=False, allow_none=True)  # 后模冷却水直径
    core_cooling_circuit_number = fields.Integer(required=False, allow_none=True)  # 后模冷却回路组数
    core_water_nozzle_specification = fields.Float(required=False, allow_none=True)  # 后模水嘴安装规格
    circuit_picture_url = fields.String(required=False, allow_none=True)  # 冷却回路附件
    
    ejector_stroke = fields.Float(required=False, allow_none=True)  # 顶出行程
    ejector_rod_hole_diameter = fields.Float(required=False, allow_none=True)  # 顶棍孔直径
    # ejector_rod_hole_distribute = fields.String(required=False, allow_none=True)  # 顶棍孔分布
    ejector_rod_hole_spacing = fields.Float(required=False, allow_none=True)  # 顶棍孔间距
    ejector_rod_number = fields.Integer(required=False, allow_none=True)  # 顶棍数量
    ejector_force = fields.Float(required=False, allow_none=True)  # 顶出力
    ejector_times = fields.Integer(required=False, allow_none=True)  # 顶出次数
    reset_method = fields.String(required=False, allow_none=True)  # 复位方式
    ejection_method = fields.String(required=False, allow_none=True)  # 顶出方式
    ejector_position_length = fields.Float(required=False, allow_none=True)  # 顶出孔位置
    ejector_position_width = fields.Float(required=False, allow_none=True)  # 顶出孔位置

    mold_weight = fields.Float(required=False, allow_none=True)  # 模具重量
    hanging_mold_hole_specification = fields.String(required=False, allow_none=True)  # 吊模孔规格

    size_horizon = fields.Float(required=False, allow_none=True)  # 模具尺寸（横）
    size_vertical = fields.Float(required=False, allow_none=True)  # 模板尺寸（竖）
    size_thickness = fields.Float(required=False, allow_none=True)  # 模具厚度
    min_clamping_force = fields.Float(required=False, allow_none=True)  # 最小锁模力
    drain_distance = fields.Float(required=False, allow_none=True)  # 取流道距离
    mold_opening_stroke = fields.Float(required=False, allow_none=True)  # 开模行程
    inject_cycle_require = fields.Float(required=False, allow_none=True)  # 注塑周期要求
    subrule_no = fields.String(required=False, allow_none=True)  # 模具绑定的子规则库
    
    assisting_equipments = fields.String(required=False, allow_none=True)  # 辅助装置信息

    customer = fields.String(required=False, allow_none=True)  # 客户
    project_engineer = fields.String(required=False, allow_none=True)  # 项目工程师
    design_engineer = fields.String(required=False, allow_none=True)  # 设计工程师
    production_engineer = fields.String(required=False, allow_none=True)  # 制作工程师
    mold_engineer = fields.String(required=False, allow_none=True)  # 模具工程师
    product_engineer = fields.String(required=False, allow_none=True)  # 产品工程师
    junior_product_engineer = fields.String(required=False, allow_none=True)  # 初级产品工程师
    injection_engineer = fields.String(required=False, allow_none=True)  # 注塑工程师
    senior_injection_engineer = fields.String(required=False, allow_none=True)  # 高级注塑工程师
    order_date = fields.Date(required=False, allow_none=True)  # 订单日期
    entry_date = fields.Date(required=False, allow_none=True)  # 信息录入日期


# 工程信息(from)--project_schema
class ProjectSchema(BaseSchema):
    mold_info = fields.Nested(ProjectIndexSchema)


class ProjectIdSchema(BaseSchema):
    id = fields.Integer(required=False, allow_none=True)


# 获取工程列表(form)--get_project_list_schema
class GetProjectListSchema(PaginationBaseSchema):
    company_id = fields.Integer(required=False, allow_none=True)
    mold_no = fields.String(required=False, allow_none=True)
    mold_type = fields.String(required=False, allow_none=True)
    mold_name = fields.String(required=False, allow_none=True)
    product_type = fields.String(required=False, allow_none=True)
    product_name = fields.String(required=False, allow_none=True)
    customer = fields.String(required=False, allow_none=True)
    project_engineer = fields.String(required=False, allow_none=True)
    design_engineer = fields.String(required=False, allow_none=True)
    production_engineer = fields.String(required=False, allow_none=True)
    order_date = fields.Date(required=False, allow_none=True)
    
    project_id_list = fields.List(fields.Integer())
    mold_no_list = fields.List(fields.String())


# 同时处理多个工程(form)--handle_multiple_project_schema
class HandleMultipleProjectSchema(BaseSchema):
    project_id_list = fields.List(fields.Integer(required=False, allow_none=True))
    flag = fields.String(required=False, allow_none=True)
