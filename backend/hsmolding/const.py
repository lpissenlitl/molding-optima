from enum import IntEnum, unique, Enum, EnumMeta


class LabelEnumMeta(EnumMeta):
    def __new__(mcs, name, bases, attrs):
        obj = super().__new__(mcs, name, bases, attrs)
        obj._value2member_map_ = {}
        for m in obj:
            value, label = m.value
            m._value_ = value
            m.label = label
            obj._value2member_map_[value] = m

        return obj


FILE_TYPE_EXCEL = "xlsx"


class TrailStatus(Enum, metaclass=LabelEnumMeta):
    WAITING = 0, "等待确认"
    CANCELED = 1, "已取消"
    CONFIRMED = 2, "已确认"
    OVERDUE = 3, "已过期"
    USED = 4, "转入测试"

    @classmethod
    def get_label(cls, value):
        for item in cls:
            if value == item.value:
                return item.label


class DeleteStatus(Enum, metaclass=LabelEnumMeta):
    NOT_DELETED = 0, "未删除"
    DELETED = 1, "已删除"


@unique
class SliceStatus(IntEnum):
    FILE = 0  # 是文件，非切割
    SLICE = 1  # 是切割后文件


@unique
class ExportStatus(IntEnum):
    PROCESSING = 1  # 处理中
    FINISH = 2  # 导出完成
    FAILED = 3  # 导出失败


ANALYZE_DATA={
    "1610":"filling_time",
    "1760":"vp_switch",
    "1150":"clamping_force",
    "1430":"injection_pressure",
    "1180":"pressure",
    "7112":"cavity_weight",
    "1192":"filling_end_pressure"
}


MOLDFLOW_RESULT = {
    "流动":{
    1610 : "Fill time",
    1760 : "Pressure at V/P switchover",
    1770 : "Temperature at flow front",
    1430 : "Pressure at injection location:XY 图",
    1150 : "Clamp force:XY 图",
    1600 : "Density",
    1900 : "Extension rate",
    1450 : "Flow rate beams",
    1630 : "Time to reach ejection temperature",
    1612 : "Grow from",
    1180 : "Pressure",
    1140 : "Ram speed recommended:XY 图",
    1584 : "Shear rate",
    1597 : "Shear rate maximum",
    7050 : "Shear stress at wall",
    1540 : "Temperature",
    1790 : "Throughput",
    1750 : "Velocity",
    1595 : "Viscosity",
    1151 : "Ram position:XY 图",
    1192 : "Pressure at end of fill",
    1233 : "Frozen layer fraction at end of fill",
    1311 : "Sink marks estimate",
    1312 : "Sink marks shaded",
    1491 : "Frozen layer fraction",
    1620 : "Volumetric shrinkage",
    1622 : "Air traps",
    1629 : "Average volumetric shrinkage",
    1650 : "Polymer fill region",
    1651 : "Weld surface movement (3D)",
    1653 : "Weld surface formation (3D)",
    1722 : "Weld lines",
    1753 : "Pathlines",
    7112 : "Cavity weight",
    },
    "Cool|Flow|Warp":{
    1610:"Fill time",
    1760:"Pressure at V/P switchover",
    1770:"Temperature at flow front",
    1430:"Pressure at injection location:XY 图",
    1150:"Clamp force:XY 图",
    1600:"Density",
    1900:"Extension rate",
    1450:"Flow rate, beams",
    1630:"Time to reach ejection temperature",
    1612:"Grow from",
    1180:"Pressure",
    1140:"Ram speed, recommended:XY 图",
    1584:"Shear rate",
    1597:"Shear rate, maximum",
    7050:"Shear stress at wall",
    1540:"Temperature",
    1790:"Throughput",
    5021:"Circuit coolant temperature",
    5030:"Circuit flow rate",
    5040:"Circuit Reynolds number",
    5050:"Circuit metal temperature",
    5600:"Temperature, part",
    5610:"Time to reach ejection temperature, part",
    5620:"Percentage frozen layer",
    5630:"Percentage molten layer",
    6250:"Deflection, all effects:Deflection",
    6250:"Deflection, all effects:X Component",
    6250:"Deflection, all effects:Y Component",
    6250:"Deflection, all effects:Z Component",
    1750:"Velocity",
    1595:"Viscosity",
    1151:"Ram position:XY 图",
    1192:"Pressure at end of fill",
    1233:"Frozen layer fraction at end of fill",
    1311:"Sink marks estimate",
    1312:"Sink marks shaded",
    1491:"Frozen layer fraction",
    1620:"Volumetric shrinkage",
    1622:"Air traps",
    1629:"Average volumetric shrinkage",
    1650:"Polymer fill region",
    1651:"Weld surface movement (3D)",
    1653:"Weld surface formation (3D)",
    1722:"Weld lines",
    1753:"Pathlines",
    5011:"Circuit pressure",
    }
}

MOLDFLOW_RESULT_CH = {
    1610 : "注射时间",
    1760 : "VP切换压力",
    1770 : "流动前沿温度",
    1430 : "注射位置处压力:XY 图",
    1150 : "锁模力:XY 图",
    1600 : "密度",
    1900 : "拉伸速率",
    1450 : "拉伸速率,柱体",
    1630 : "达到顶出温度的时间",
    1612 : "充填区域",
    1180 : "压力",
    1140 : "推荐的螺杆速度:XY 图",
    1584 : "剪切速率",
    1597 : "剪切速率,最大值",
    7050 : "壁上剪切应力",
    1540 : "温度",
    1790 : "料流量",
    1750 : "速度",
    1595 : "粘度",
    1151 : "螺杆位置:XY 图",
    1192 : "填充末端压力",
    1233 : "填充末端冻结层因子",
    1311 : "缩痕估算",
    1312 : "缩痕阴影",
    1491 : "冻结层因子",
    1620 : "体积收缩率",
    1622 : "气穴",
    1629 : "平均体积收缩率",
    1650 : "聚合物填充物区域",
    1651 : "熔接面移动 (3D)",
    1653 : "熔接面分布 (3D)",
    1722 : "熔接痕",
    1753 : "路径线",
    7112 : "型腔重量",

    5011:"回路压力",
    5021:"回路冷却液温度",
    5030:"回路流动速率",
    5040:"回路雷诺数",
    5050:"回路管壁温度",
    5600:"温度,零件",
    5610:"达到顶出温度的时间,零件",
    5620:"冻结层百分比",
    5630:"融化层百分比",

    5060:"回路热去除效率",
    5702:"模具,温度",
    5081:"回路次要损失系数",
    5082:"回路摩擦系数",
    5960:"流动前沿温度,型腔",

    62500:"翘曲变形",
    62501:"翘曲变形:X Component",
    62502:"翘曲变形:Y Component",
    62503:"翘曲变形:Z Component",

}

MOLDFLOW_RESULT_DESC = {
1610 :"Fill time",
1760 :"Pressure at V/P switchover",              
1770 :"Temperature at flow front",               
1430 :"Pressure at injection location:XY 图",    
1150 :"Clamp force:XY 图",                       
1600 :"Density",                                 
1900 :"Extension rate",                          
1450 :"Flow rate beams",                         
1630 :"Time to reach ejection temperature",      
1612 :"Grow from",                               
1180 :"Pressure",                                
1140 :"Ram speed recommended:XY 图",             
1584 :"Shear rate",                              
1597 :"Shear rate maximum",                      
7050 :"Shear stress at wall",                    
1540 :"Temperature",                             
1790 :"Throughput",                              
1750 :"Velocity",                                
1595 :"Viscosity",                               
1151 :"Ram position:XY 图",                      
1192 :"Pressure at end of fill",                 
1233 :"Frozen layer fraction at end of fill",    
1311 :"Sink marks estimate",                     
1312 :"Sink marks shaded",                       
1491 :"Frozen layer fraction",                   
1620 :"Volumetric shrinkage",                    
1622 :"Air traps",                               
1629 :"Average volumetric shrinkage",            
1650 :"Polymer fill region",                     
1651 :"Weld surface movement (3D)",              
1653 :"Weld surface formation (3D)",             
1722 :"Weld lines",                              
1753 :"Pathlines",                               
7112 :"Cavity weight",                           

5011:"Circuit pressure",						
5021:"Circuit coolant temperature",              
5030:  "Circuit flow rate",                      
5040:  "Circuit Reynolds number",                
5050:  "Circuit metal temperature",              
5600:  "Temperature, part",                      
5610:  "Time to reach ejection temperature, part",
5620:  "Percentage frozen layer",                
5630:  "Percentage molten layer",                

5060:"Circuit heat removal efficiency",									
5702: "Temperature, mold",									
5081: "Circuit minor loss coefficient",									
5082: "Circuit friction factor",	
5960:"Flow front temperature, mold-cavity",								

62500:"Deflection, all effects:Deflection", 
62501:"Deflection, all effects:X Component",
62502:"Deflection, all effects:Y Component",
62503:"Deflection, all effects:Z Component",

}

MOLDFLOW_RESULT_GROUP= {
    1610 :"流动",
    1760 : "流动",
    1770 : "流动",
    1430 : "流动",
    1150 : "流动",
    1600 : "流动",
    1900 : "流动",
    1450 : "流动",
    1630 : "流动",
    1612 : "流动",
    1180 : "流动",
    1140 : "流动",
    1584 : "流动",
    1597 : "流动",
    7050 : "流动",
    1540 : "流动",
    1790 : "流动",
    1750 : "流动",
    1595 : "流动",
    1151 : "流动",
    1192 : "流动",
    1233 : "流动",
    1311 : "流动",
    1312 : "流动",
    1491 : "流动",
    1620 : "流动",
    1622 : "流动",
    1629 : "流动",
    1650 : "流动",
    1651 : "流动",
    1653 : "流动",
    1722 : "流动",
    1753 : "流动",
    7112 : "流动",

    5011:	"冷却",
    5021: "冷却",
    5030:   "冷却",
    5040:   "冷却",
    5050:   "冷却",
    5600:   "冷却",
    5610: "冷却",
    5620:   "冷却",
    5630:   "冷却",

    5060:	"冷却",	
    5702:	"冷却",
    5081:	"冷却",
    5082:	"冷却",
    5960:	"流动",

    62500:"翘曲",
    62501:"翘曲",
    62502:"翘曲",
    62503:"翘曲",
}

MOLDFLOW_RESULT_UNIT= {
    1610 :"s",
    1760 : "MPa",
    1770 : "℃",
    1430 : "MPa",
    1150 : "Ton",
    1600 : "g/cm³",
    1900 : "1/s",
    1450 : "cm³/s",
    1630 : "s",
    1612 : "",
    1180 : "MPa",
    1140 : "%",
    1584 : "1/s",
    1597 : "1/s",
    7050 : "MPa",
    1540 : "℃",
    1790 : "cm³",
    1750 : "cm/s",
    1595 : "Pa-s",
    1151 : "",
    1192 : "MPa",
    1233 : "",
    1311 : "mm",
    1312 : "",
    1491 : "",
    1620 : "%",
    1622 : "",
    1629 : "%",
    1650 : "",
    1651 : "",
    1653 : "",
    1722 : "度",
    1753 : "cm/s",
    7112 : "g",

    5011:	"MPa",
    5021: "℃",
    5030:   "lit/min",
    5040:   "",
    5050:   "℃",
    5600:   "℃",
    5610: "s",
    5620:   "%",
    5630:   "%",

    5060:	"",	
    5702:	"℃",
    5081:	"",
    5082:	"",
    5960:	"℃",

    62500:"mm",
    62501:"mm",
    62502:"mm",
    62503:"mm",
}


TEST_LIST=[
        1610,
        1760,
        1770,
        1430,
        1150,
        1600,
        1900,
        1450,
        1630,
        1612,
        1180,
        1140,
        1584,
        1597,
        7050,
        1540,
        1790,
        1750,
        1595,
        1151,
        1192,
        1233,
        1311,
        1312,
        1491,
        1620,
        1622,
        1629,
        1650,
        1651,
        1653,
        1722,
        1753,
        7112,
    ]

ANALYTICAL_SEQUENCE = {
    "Fill": "填充",
    "流动": "填充+保压",
    "冷却": "冷却",
    "Flow|Warp": "填充+保压+翘曲",
    "Cool|Flow|Warp": "冷却+填充+保压+翘曲",
    "Cool (FEM)": "冷却(FEM)",
    "Cool (FEM)|Flow|Warp": "冷却(FEM)+填充+保压+翘曲"
}

# 注射控制
INJECT_CONTROL = {
    "5": 10602,
    "6": 10603
}

# 注射相对 10602
INJECT_REL = {
    "1": 10618,
    "2": 10605
}

# 注射绝对 10603
INJECT_ABS = {
    "3": 10604,
    "5": 10628,
    "4": 10606,
    "7": 10614,
    "9": 10620,
    "8": 10616,
}

# 保压 10704
HOLDING_SET ={
    "4":10702,
    "2":10707,
    "1":10706,
    "3":10705
}

VELOCITY_UNIT_SET = {
    10604:"mm/s",
    10628:"cm³/s",
    10606:"%",
    10614:"mm/s",
    10620:"cm³/s",
    10616:"%"
}

POSITION_UNIT_SET = {
    10604:"mm",
    10628:"mm",
    10606:"mm",
    10614:"s",
    10620:"s",
    10616:"s"
}

# 注射绝对 10603
INJECT_ABS_LABEL = {
    10604:"位置" ,
    10628:"位置" ,
    10606:"位置" ,
    10614:"时间" ,
    10620:"时间" ,
    10616:"时间" ,
}

# 多射台
MACHINE_TYPE = {
    "单色注塑机":1,
    "双色注塑机":2,
    "三色注塑机":3,
    "四色注塑机":4,
    "五色注塑机":5,
    "六色注塑机":6,
    "七色注塑机":7,
}

MOLD_TYPE = {
    "单色模":1,
    "双色模":2,
    "三色模":3,
    "四色模":4,
    "五色模":5,
    "六色模":6,
    "七色模":7,
}