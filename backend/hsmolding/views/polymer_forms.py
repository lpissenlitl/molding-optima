from marshmallow import fields

from gis.common.django_ext.forms import BaseSchema, PaginationBaseSchema, CNDatetimeField


class PolymerListSchema(PaginationBaseSchema):
    trademark = fields.String()
    abbreviation = fields.String()
    series = fields.String()
    manufacturer = fields.String()
    company_id = fields.Integer()


class HandleMultiplePolymerSchema(BaseSchema):
    polymer_id_list = fields.List(fields.Integer())
    flag = fields.String(default="default") # 标记处理方式

    
class PolymerSchema(BaseSchema):
    # 增加材料
    company_id = fields.Integer(required=False, allow_none=True)
    series = fields.String(required=False, allow_none=True)
    manufacturer = fields.String(required=False, allow_none=True)
    trademark = fields.String(required=True, allow_none=False)
    abbreviation = fields.String(required=True, allow_none=False)
    category = fields.String(required=False, allow_none=True)  # 材料类型:结晶性,无定形
    data_source = fields.String(required=False, allow_none=True)
    data_status = fields.String(required=False, allow_none=True)
    internal_id = fields.String(required=False, allow_none=True)
    level_code = fields.String(required=False, allow_none=True)
    vendor_code = fields.String(required=False, allow_none=True)

    # 推荐工艺
    max_melt_temperature = fields.Float(required=False, allow_none=True)
    min_melt_temperature = fields.Float(required=False, allow_none=True)
    recommend_melt_temperature = fields.Float(required=True, allow_none=False)
    max_mold_temperature = fields.Float(required=False, allow_none=True)
    min_mold_temperature = fields.Float(required=False, allow_none=True)
    recommend_mold_temperature = fields.Float(required=True, allow_none=False)
    max_shear_linear_speed = fields.Float(required=False, allow_none=True)
    min_shear_linear_speed = fields.Float(required=False, allow_none=True)
    recommend_shear_linear_speed = fields.Float(required=True, allow_none=False)
    recommend_injection_rate = fields.Float(required=False, allow_none=True)
    recommend_back_pressure = fields.Float(required=True, allow_none=False)
    degradation_temperature = fields.Float(required=False, allow_none=True)
    ejection_temperature = fields.Float(required=False, allow_none=True)
    barrel_residence_time = fields.Float(required=False, allow_none=True)
    max_sheer_rate = fields.Float(required=False, allow_none=True)
    max_sheer_stress = fields.Float(required=False, allow_none=True)
    dry_temperature = fields.String(required=False, allow_none=True)
    dry_time = fields.String(required=False, allow_none=True)
    dry_method = fields.String(required=False, allow_none=True)

    # 流变属性
    viscosity_model = fields.String(required=False, allow_none=True)  # 粘度模型:cross_WLF
    cross_WLF_n = fields.String(required=False, allow_none=True)
    cross_WLF_Tau = fields.String(required=False, allow_none=True)  # Pa
    cross_WLF_D1 = fields.String(required=False, allow_none=True)  # Pa-s
    cross_WLF_D2 = fields.String(required=False, allow_none=True)  # k
    cross_WLF_D3 = fields.String(required=False, allow_none=True)  # k/Pa
    cross_WLF_A1 = fields.String(required=False, allow_none=True)
    cross_WLF_A2 = fields.String(required=False, allow_none=True)  # k
    c1 = fields.String(required=False, allow_none=True)  # 接合点损失法系数(Pa^(1-c2))
    c2 = fields.String(required=False, allow_none=True)  # 接合点损失法系数
    switch_temp = fields.String(required=False, allow_none=True)  # 转换温度(℃)
    viscosity_index = fields.String(required=False, allow_none=True)  # 粘度指数
    MFR_temp = fields.String(required=False, allow_none=True)  # 温度（℃）
    MFR_load = fields.String(required=False, allow_none=True)  # 载入（Kg）
    MFR_measure = fields.String(required=False, allow_none=True)  # 测量的MFR（g/10min）

    # pvT属性
    melt_density = fields.Float(required=True, allow_none=False)
    solid_density = fields.Float(required=True, allow_none=False)
    Tait_pvT_b5 = fields.String(required=False, allow_none=True)
    Tait_pvT_b6 = fields.String(required=False, allow_none=True)
    Tait_pvT_b1m = fields.String(required=False, allow_none=True)
    Tait_pvT_b2m = fields.String(required=False, allow_none=True)
    Tait_pvT_b3m = fields.String(required=False, allow_none=True)
    Tait_pvT_b4m = fields.String(required=False, allow_none=True)
    Tait_pvT_b1s = fields.String(required=False, allow_none=True)
    Tait_pvT_b2s = fields.String(required=False, allow_none=True)
    Tait_pvT_b3s = fields.String(required=False, allow_none=True)
    Tait_pvT_b4s = fields.String(required=False, allow_none=True)
    Tait_pvT_b7 = fields.String(required=False, allow_none=True)
    Tait_pvT_b8 = fields.String(required=False, allow_none=True)
    Tait_pvT_b9 = fields.String(required=False, allow_none=True)

    # 机械属性
    E1 = fields.Float(required=False, allow_none=True)
    E2 = fields.Float(required=False, allow_none=True)
    v12 = fields.Float(required=False, allow_none=True)
    v23 = fields.Float(required=False, allow_none=True)
    G12 = fields.Float(required=False, allow_none=True)
    Alpha1 = fields.Float(required=False, allow_none=True)
    Alpha2 = fields.Float(required=False, allow_none=True)

    # 收缩属性
    average_horizontal_shrinkage = fields.Float(required=False, allow_none=True)
    average_vertical_shrinkage = fields.Float(required=False, allow_none=True)
    min_horizontal_shrinkage = fields.Float(required=False, allow_none=True)
    max_horizontal_shrinkage = fields.Float(required=False, allow_none=True)
    min_vertical_shrinkage = fields.Float(required=False, allow_none=True)
    max_vertical_shrinkage = fields.Float(required=False, allow_none=True)

    # 填充物属性
    filler = fields.String(required=False, allow_none=True)
    filler_type = fields.String(required=False, allow_none=True)
    filler_shape = fields.String(required=False, allow_none=True)
    filler_percentage = fields.Float(required=False, allow_none=True)
    filler_density = fields.Float(required=False, allow_none=True)
    filler_specific_heat = fields.Float(required=False, allow_none=True)
    filler_specific_thermal_conductivity = fields.Float(required=False, allow_none=True)
    filler_E1 = fields.Float(required=False, allow_none=True)
    filler_E2 = fields.Float(required=False, allow_none=True)
    filler_v12 = fields.Float(required=False, allow_none=True)
    filler_v23 = fields.Float(required=False, allow_none=True)
    filler_G12 = fields.Float(required=False, allow_none=True)
    filler_Alpha1 = fields.Float(required=False, allow_none=True)
    filler_Alpha2 = fields.Float(required=False, allow_none=True)
    filler_horizontal_tensile_strength = fields.Float(required=False, allow_none=True)
    filler_vertical_tensile_strength = fields.Float(required=False, allow_none=True)
    filler_aspect_ratio = fields.Float(required=False, allow_none=True)
    
    # 修改时要用到的字段
    id = fields.Integer(required=False, allow_none=True)
    created_at = CNDatetimeField()
    updated_at = CNDatetimeField()
    deleted = fields.Integer(default=0)
