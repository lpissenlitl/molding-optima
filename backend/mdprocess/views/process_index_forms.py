from marshmallow import fields

from gis.common.django_ext.forms import BaseSchema, PaginationBaseSchema, CNDatetimeField

# 工艺初始化 form
class ProcessIndexSchema(BaseSchema):

    id = fields.Integer(required=False, allow_none=True)  # 工艺记录id
    company_id = fields.Integer(required=False, allow_none=True)  # 所属公司

    optimize_type = fields.Integer(Required=False, allow_none=True, default=0) # 初始化 0: 不考虑保压，1：考虑保压
    status = fields.Integer(required=False, allow_none=True)  # 状态: 优化 1, 工艺存储 2, 优化&存储 3, 专家记录 4
    process_no = fields.String(required=False, allow_none=True)  # 工艺编号
    data_sources = fields.String(required=False, allow_none=True)  # 数据来源
    mold_trials_no = fields.String(required=False, allow_none=True)  # 试模次数

    mold_id = fields.Integer(required=False, allow_none=True)  # 模具id
    mold_no = fields.String(required=False, allow_none=True)  # 模具编号
    cavity_num = fields.String(required=False, allow_none=True)  # 型腔数量
    runner_length = fields.Float(required=False, allow_none=True)  # 流道长度
    runner_weight = fields.Float(required=False, allow_none=True)  # 流道重量
    gate_type = fields.String(required=False, allow_none=True)  # 浇口类别
    gate_num = fields.Integer(required=False, allow_none=True)  # 浇口个数
    gate_shape = fields.String(required=False, allow_none=True)  # 浇口形状
    gate_area = fields.Float(required=False, allow_none=True)  # 浇口横截面积
    gate_radius = fields.Float(required=False, allow_none=True)  # 浇口半径(圆)
    gate_length = fields.Float(required=False, allow_none=True)  # 浇口长(矩形)
    gate_width = fields.Float(required=False, allow_none=True)  # 浇口宽(矩形)

    valve_num = fields.Integer(required=False, allow_none=True)
    inject_cycle_require = fields.Float(required=False, allow_none=True)
    subrule_no = fields.String(required=False, allow_none=True)

    inject_part = fields.String(required=False, allow_none=True)  # 射台
    product_no = fields.String(required=False, allow_none=True)  # 制品编号
    product_category = fields.String(required=False, allow_none=True)  # 制品品类

    product_type = fields.String(required=False, allow_none=True)  # 制品类别:精密型,节料型,外观型,透明型
    product_name = fields.String(required=False, allow_none=True)  # 制品名称
    product_total_weight = fields.Float(required=False, allow_none=True)  # 总重量
    product_ave_thickness = fields.Float(required=False, allow_none=True)  # 制品平均厚度
    product_max_thickness = fields.Float(required=False, allow_none=True)  # 制品最大厚度
    product_max_length = fields.Float(required=False, allow_none=True)  # 制品最大长度

    machine_id = fields.Integer(required=False, allow_none=True)  # 塑料id
    machine_data_source = fields.String(required=False, allow_none=True)  # 注塑机来源
    machine_trademark = fields.String(required=False, allow_none=True)  # 注塑机类别
    machine_serial_no = fields.String(required=False, allow_none=True)  # 注塑机设备编码

    polymer_id = fields.Integer(required=False, allow_none=True)  # 胶料id
    polymer_abbreviation = fields.String(required=False, allow_none=True)  # 塑料简称
    polymer_trademark = fields.String(required=False, allow_none=True)  # 塑料牌号

    injection_stage = fields.Integer(required=False, allow_none=True)  # 注射段数
    holding_stage = fields.Integer(required=False, allow_none=True)  # 计量段数
    VP_switch_mode = fields.String(required=False, allow_none=True)  # VP切换模式
    metering_stage = fields.Integer(required=False, allow_none=True)  # 计量段数
    decompressure_mode_before_metering = fields.String(required=False, allow_none=True)  # 储前松退模式
    decompressure_mode_after_metering = fields.String(required=False, allow_none=True)  # 储后松退模式
    barrel_temperature_stage = fields.Integer(required=False, allow_none=True)  # 料筒温度段数

    created_at = CNDatetimeField()
    updated_at = CNDatetimeField()
    deleted = fields.Integer(required=False, allow_none=True)


# 获取工艺参数录入信息列表
class GetProcessIndexListSchema(PaginationBaseSchema):
    company_id = fields.Integer(required=False, allow_none=True)
    status = fields.Integer(required=False, allow_none=True)
    process_no = fields.String(required=False, allow_none=True)
    mold_no = fields.String(required=False, allow_none=True)
    gate_type = fields.String(required=False, allow_none=True)
    product_type = fields.String(required=False, allow_none=True)
    product_name = fields.String(required=False, allow_none=True)
    machine_data_source = fields.String(required=False, allow_none=True)
    machine_trademark = fields.String(required=False, allow_none=True)
    polymer_abbreviation = fields.String(required=False, allow_none=True)
    polymer_trademark = fields.String(required=False, allow_none=True)
    start_date = fields.Date(required=False, allow_none=True)
    end_date = fields.Date(required=False, allow_none=True)
    data_sources = fields.String(required=False, allow_none=True)


# 处理多个工程状态(form)--handle_multiple_process_schema
class HandleMultipleProcessSchema(BaseSchema):
    process_id_list = fields.List(fields.Integer())
    flag = fields.String(default="default") # 标记处理方式
