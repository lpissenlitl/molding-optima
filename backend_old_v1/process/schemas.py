from extensions.schemas import BaseSchema, PaginationBaseSchema
from marshmallow import fields, Schema


class ProcessConditionSchema(BaseSchema):
    """工艺条件"""
    status = fields.String(allow_none=True, required=False)
    origin_type = fields.String(allow_none=True, required=False)

    mold_id = fields.Integer(allow_none=True, required=False)
    shot_index = fields.Integer(allow_none=True, required=False)

    injection_machine_id = fields.Integer(allow_none=True, required=False)
    injection_index = fields.Integer(allow_none=True, required=False)
    
    polymer_id = fields.Integer(allow_none=True, required=False)
    

class ProcessParameterSchema(ProcessConditionSchema):
    """工艺参数记录"""

    # --- 基本信息 ---
    parameter_code = fields.String(allow_none=True, required=False)
    parameter_source = fields.String(allow_none=True, required=False)
    parent_parameter_id = fields.Integer(allow_none=True, required=False)
    
    # --- 注射参数 ---
    injection_stages = fields.Integer(allow_none=True, required=False)
    IV0 = fields.Float(allow_none=True, required=False)
    IP0 = fields.Float(allow_none=True, required=False)
    IL0 = fields.Float(allow_none=True, required=False)
    IV1 = fields.Float(allow_none=True, required=False)
    IP1 = fields.Float(allow_none=True, required=False)
    IL1 = fields.Float(allow_none=True, required=False)
    IV2 = fields.Float(allow_none=True, required=False)
    IP2 = fields.Float(allow_none=True, required=False)
    IL2 = fields.Float(allow_none=True, required=False)
    IV3 = fields.Float(allow_none=True, required=False)
    IP3 = fields.Float(allow_none=True, required=False)
    IL3 = fields.Float(allow_none=True, required=False)
    IV4 = fields.Float(allow_none=True, required=False)
    IP4 = fields.Float(allow_none=True, required=False)
    IL4 = fields.Float(allow_none=True, required=False)
    IV5 = fields.Float(allow_none=True, required=False)
    IP5 = fields.Float(allow_none=True, required=False)
    IL5 = fields.Float(allow_none=True, required=False)
    IT = fields.Float(allow_none=True, required=False)
    IDT = fields.Float(allow_none=True, required=False)
    
    # --- VP 切换参数 ---
    VPTM = fields.Integer(allow_none=True, required=False)
    VPTL = fields.Float(allow_none=True, required=False)
    VPTT = fields.Float(allow_none=True, required=False)
    VPTP = fields.Float(allow_none=True, required=False)
    VPTV = fields.Float(allow_none=True, required=False)
    
    # --- 保压参数 ---
    holding_stages = fields.Integer(allow_none=True, required=False)
    PP0 = fields.Float(allow_none=True, required=False)
    PV0 = fields.Float(allow_none=True, required=False)
    PT0 = fields.Float(allow_none=True, required=False)
    PP1 = fields.Float(allow_none=True, required=False)
    PV1 = fields.Float(allow_none=True, required=False)
    PT1 = fields.Float(allow_none=True, required=False)
    PP2 = fields.Float(allow_none=True, required=False)
    PV2 = fields.Float(allow_none=True, required=False)
    PT2 = fields.Float(allow_none=True, required=False)
    PP3 = fields.Float(allow_none=True, required=False)
    PV3 = fields.Float(allow_none=True, required=False)
    PT3 = fields.Float(allow_none=True, required=False)
    PP4 = fields.Float(allow_none=True, required=False)
    PV4 = fields.Float(allow_none=True, required=False)
    PT4 = fields.Float(allow_none=True, required=False)
    
    # --- 冷却参数 ---
    CT = fields.Float(allow_none=True, required=False)
    
    # --- 熔胶参数 ---
    metering_stages = fields.Integer(allow_none=True, required=False)
    MP0 = fields.Float(allow_none=True, required=False)
    MSR0 = fields.Float(allow_none=True, required=False)
    MBP0 = fields.Float(allow_none=True, required=False)
    ML0 = fields.Float(allow_none=True, required=False)
    MP1 = fields.Float(allow_none=True, required=False)
    MSR1 = fields.Float(allow_none=True, required=False)
    MBP1 = fields.Float(allow_none=True, required=False)
    ML1 = fields.Float(allow_none=True, required=False)
    MP2 = fields.Float(allow_none=True, required=False)
    MSR2 = fields.Float(allow_none=True, required=False)
    MBP2 = fields.Float(allow_none=True, required=False)
    ML2 = fields.Float(allow_none=True, required=False)
    MP3 = fields.Float(allow_none=True, required=False)
    MSR3 = fields.Float(allow_none=True, required=False)
    MBP3 = fields.Float(allow_none=True, required=False)
    ML3 = fields.Float(allow_none=True, required=False)
    
    DMBM = fields.Integer(allow_none=True, required=False)
    DPBM = fields.Float(allow_none=True, required=False)
    DVBM = fields.Float(allow_none=True, required=False)
    DTBM = fields.Float(allow_none=True, required=False)
    DDBM = fields.Float(allow_none=True, required=False)

    DMAM = fields.Integer(allow_none=True, required=False)
    DPAM = fields.Float(allow_none=True, required=False)
    DVAM = fields.Float(allow_none=True, required=False)
    DTAM = fields.Float(allow_none=True, required=False)
    DDAM = fields.Float(allow_none=True, required=False)
    
    MDT = fields.Float(allow_none=True, required=False)
    MEL = fields.Float(allow_none=True, required=False)
    
    # --- 料筒温度参数 ---
    barrel_temperature_stages = fields.Integer(allow_none=True, required=False)
    NT = fields.Float(allow_none=True, required=False)
    BT1 = fields.Float(allow_none=True, required=False)
    BT2 = fields.Float(allow_none=True, required=False)
    BT3 = fields.Float(allow_none=True, required=False)
    BT4 = fields.Float(allow_none=True, required=False)
    BT5 = fields.Float(allow_none=True, required=False)
    BT6 = fields.Float(allow_none=True, required=False)
    BT7 = fields.Float(allow_none=True, required=False)
    BT8 = fields.Float(allow_none=True, required=False)
    BT9 = fields.Float(allow_none=True, required=False)


class ProcessConditionAndParameterSchema(Schema):
    """工艺条件及参数"""
    
    condition = fields.Nested(ProcessConditionSchema)
    parameter = fields.Nested(ProcessParameterSchema)
    

class ProcessParameterListSchema(PaginationBaseSchema):
    """工艺参数列表"""
    status = fields.String(allow_none=True, required=False)
    origin_type = fields.String(allow_none=True, required=False)
    mold_no = fields.String(allow_none=True, required=False)
    machine_model = fields.String(allow_none=True, required=False)
    polymer_abbreviation = fields.String(allow_none=True, required=False)    
    start_date = fields.Date(allow_none=True, required=False)
    end_date = fields.Date(allow_none=True, required=False)
