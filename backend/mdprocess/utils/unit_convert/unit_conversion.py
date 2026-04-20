import logging
import math
"""
注射单位转换

barspec→bar
压力bar=压力barspec（采集值）×螺杆横截面积mm2÷油缸面积mm2
            =压力barspec（采集值）×（π×螺杆直径mm2÷4）÷油缸面积mm2
如果活塞杆位于注射侧=true，那么油缸面积mm2=油缸数×π×油缸直径mm2÷4
如果活塞杆位于注射侧=false，那么油缸面积mm2=油缸数×（（π×油缸直径mm2÷4）-（π×活塞杆直径mm2÷4））
螺杆直径标签：Injection1.sv_rScrewDiameter
油缸数标签：Injection1.sv_CylinderData.iNumCylinders
油缸直径标签：Injection1.sv_CylinderData.rCylinderDiameter
活塞杆直径标签：Injection1.sv_CylinderData.rPistonRodDiameter
活塞杆位于注射侧标签：Injection1.sv_CylinderData.bUseSmallSize

cm³/s→mm/s：
线速度mm/s=体积速度cm³/s（采集值）÷面积mm2×1000.0
                   =体积速度cm³/s（采集值）÷(π×螺杆直径mm2÷4.0)×1000.0
螺杆直径标签：Injection1.sv_rScrewDiameter

cm³/s→%：
速度%=实际速度cm³/s（采集值）÷最大速度cm³/s×100.0
最大速度标签：Injection1.sv_rMaxSpeedFwdSpec

cm³→mm：
位置mm=实际位置cm³（采集值）÷面积mm2×1000.0
             =实际位置cm³（采集值）÷(π×螺杆直径mm2÷4.0)×1000.0
螺杆直径标签：Injection1.sv_rScrewDiameter
"""
# 保留几位有效数字
VALID_NUMBER = 2

def getCylinderArea(injector_info:dict):
    cylinder_area = None
    if injector_info.get("cylinder_numer") and injector_info.get("cylinder_diameter"):
        if injector_info.get("use_small_size"):
            cylinder_area = float(injector_info.get("cylinder_numer"))*math.pi*float(injector_info.get("cylinder_diameter"))*float(injector_info.get("cylinder_diameter"))/4
        else:
            cylinder_area = float(injector_info.get("cylinder_numer"))*(
                math.pi*float(injector_info.get("cylinder_diameter"))*float(injector_info.get("cylinder_diameter"))/4 - math.pi*float(injector_info.get("piston_rod_diameter"))*float(injector_info.get("piston_rod_diameter"))/4)
    else:
        logging.info(f"油缸数为空?{injector_info.get('cylinder_numer') } 油缸直径为空?{injector_info.get('cylinder_diameter')}")
    return cylinder_area


def getScrewArea(injector_info:dict):
    if injector_info.get("screw_diameter"):
        area = math.pi*float(injector_info.get("screw_diameter"))*float(injector_info.get("screw_diameter"))/4
        return area
    else:
        logging.info(f"螺杆直径为空?{injector_info.get('screw_diameter') }")


def getScrewCircumference(injector_info:dict):
    if injector_info.get("screw_diameter"):
        return math.pi*float(injector_info.get("screw_diameter")) 
    else:
        logging.info(f"螺杆直径为空?{injector_info.get('screw_diameter') }")


def changeVelocityToRate(velocity, injector_info):
    volume = conversion(original_unit="mm/s", converted_unit="cm³/s", original_value=velocity, injector_info=injector_info)
    return volume

def caculateRateToPercent(original_value, rate, velocity, injector_info, VALID_NUMBER):
    # 检查最大(注射/保压/射退)速率是否存在
    if rate and rate != 0 :
        return round(original_value / float(rate) * 100, VALID_NUMBER)
    elif velocity and velocity != 0:
        return round(original_value / changeVelocityToRate(velocity, injector_info) * 100, VALID_NUMBER)


def caculatePercentToRate(original_value, rate, velocity, injector_info, VALID_NUMBER):
    # 检查最大(注射/保压/射退)速率是否存在
    print(f"最大速率{rate}  最大速度{velocity}")
    if rate and rate != 0:
        return round(original_value * float(rate) / 100, VALID_NUMBER)
    elif velocity and velocity != 0:
        return round(original_value * changeVelocityToRate(velocity, injector_info) / 100, VALID_NUMBER)


def caculateVelocityToPercent(original_value, velocity, VALID_NUMBER):
    # 检查最大(开模/合模/顶进/顶退)速度是否存在
    if velocity and velocity != 0:
        return round(original_value / float(velocity) * 100, VALID_NUMBER)


def caculatePercentToVelocity(original_value, velocity, VALID_NUMBER):
    # 检查最大(开模/合模/顶进/顶退)速度是否存在
    if velocity and velocity != 0:
        return round(original_value * float(velocity) / 100, VALID_NUMBER)


def getPressureCoefficient(injector_info, convert_type=None):
    # return 10*getScrewArea(injector_info)/float(getCylinderArea(injector_info))
    # 注射压力
    if "injection_pressure" in convert_type:
        return injector_info.get("max_set_injection_pressure")/injector_info.get("max_injection_pressure")
    # 保压压力
    if "holding_pressure" in convert_type:
        return injector_info.get("max_set_holding_pressure")/injector_info.get("max_holding_pressure")
    # 计量压力
    if "metering_pressure" in convert_type:
        return injector_info.get("max_set_metering_pressure")/injector_info.get("max_metering_pressure")
    # 松退压力
    if "decompression_pressure" in convert_type:
        return injector_info.get("max_set_decompression_pressure")/injector_info.get("max_decompression_pressure")


def conversion(original_unit=None, converted_unit=None, original_value=None, injector_info=None, convert_type=None):
    if original_unit and converted_unit and original_unit.lower() == converted_unit.lower():
        logging.info(f"转换前后单位相同{original_unit}")
        return round(original_value, VALID_NUMBER)
    elif not original_value:
        logging.info(f"原始值为空{original_value}")
    elif not injector_info:
        logging.info(f"注射部件为空{injector_info}")
    elif original_value and injector_info:
        if convert_type and "origin_press" in convert_type:
            return pressure_conversion(original_unit, converted_unit, original_value, injector_info)
        # 绝对注射压力/实际注射压力/料管压力MPa :max
        # 界面油压MPa/ bar/ kgf/cm² / psi    :max_set
        # 从max_set(绝对)到max,还是max到max_set(绝对)
        elif convert_type and "_pressure" in convert_type:
            pressure_coefficient = getPressureCoefficient(injector_info)
            # 从MES读取, 从MPa到界面设定, max_to_max_set
            if "read" in convert_type:
                return round(original_value*pressure_coefficient,VALID_NUMBER)
            # 从MES下发, 从界面设定到MPa, max_set_to_max
            if "write" in convert_type:
                return round(original_value/pressure_coefficient,VALID_NUMBER)

        # 速度转换
        elif original_unit == "mm/s" and converted_unit == "inch/s":
            return round(original_value / 25.4, VALID_NUMBER)
        elif original_unit == "inch/s" and converted_unit == "mm/s":
            return round(original_value * 25.4, VALID_NUMBER) 

        elif original_unit == "mm/s" and converted_unit == "inch³/s" and getScrewArea(injector_info):
            return round(original_value*getScrewArea(injector_info)/ 25.4/25.4/25.4,VALID_NUMBER)
        elif original_unit == "inch³/s" and converted_unit == "mm/s" and getScrewArea(injector_info):
            return round(original_value/getScrewArea(injector_info)* 25.4*25.4*25.4,VALID_NUMBER)

        elif original_unit == "cm³/s" and converted_unit == "inch/s" and getScrewArea(injector_info):
            return round(original_value/getScrewArea(injector_info)*1000/ 25.4,VALID_NUMBER)
        elif original_unit == "cm³/s" and converted_unit == "inch³/s" and getScrewArea(injector_info):
            return round(original_value*1000/ 25.4/ 25.4/ 25.4,VALID_NUMBER)

        elif original_unit == "inch/s" and converted_unit == "cm³/s" and getScrewArea(injector_info):
            return round(original_value* 25.4*getScrewArea(injector_info)/1000,VALID_NUMBER)
        elif original_unit == "inch³/s" and converted_unit == "cm³/s" and getScrewArea(injector_info):
            return round(original_value/1000* 25.4* 25.4* 25.4,VALID_NUMBER)

        elif original_unit == "cm³/s" and converted_unit == "mm/s" and getScrewArea(injector_info):
            return round(original_value/getScrewArea(injector_info)*1000,VALID_NUMBER)

        # 最大注射/保压/射退速度 单位是cm³/s
        elif original_unit == "cm³/s" and converted_unit == "%":
            # 在速率转换%时,需要用到最大速率,需要convert_type来区分是保压,注射还是射退, 单位是cm³/s
            if convert_type == "injection":
                return caculateRateToPercent(original_value, injector_info.get("max_injection_rate"), injector_info.get("max_injection_velocity"), injector_info, VALID_NUMBER)
            if convert_type == "holding":
                return caculateRateToPercent(original_value, injector_info.get("max_holding_rate"), injector_info.get("max_holding_velocity"), injector_info, VALID_NUMBER)
            if convert_type == "decompressure":
                return caculateRateToPercent(original_value, injector_info.get("max_decompression_rate"), injector_info.get("max_decompression_velocity"), injector_info, VALID_NUMBER)

        # 最大开合模速度 单位是mm/s        
        elif original_unit == "%" and converted_unit == "mm/s":
            if convert_type == "opening":
                return caculatePercentToVelocity(original_value, injector_info.get("max_mold_opening_velocity"), VALID_NUMBER)
            if convert_type == "clamping":
                return caculatePercentToVelocity(original_value, injector_info.get("max_mold_clamping_velocity"), VALID_NUMBER)
            if convert_type == "forward":
                return caculatePercentToVelocity(original_value, injector_info.get("max_ejector_forward_velocity"), VALID_NUMBER)
            if convert_type == "backward":
                return caculatePercentToVelocity(original_value, injector_info.get("max_ejector_backward_velocity"), VALID_NUMBER)
            if convert_type == "injection":
                return caculatePercentToVelocity(original_value, injector_info.get("max_injection_velocity"), VALID_NUMBER)
            if convert_type == "holding":
                return caculatePercentToVelocity(original_value, injector_info.get("max_holding_velocity"), VALID_NUMBER)
            if convert_type == "decompressure":
                return caculatePercentToVelocity(original_value, injector_info.get("max_decompression_velocity"), VALID_NUMBER)
        elif original_unit == "mm/s" and converted_unit == "%":
            if convert_type == "opening":
                return caculateVelocityToPercent(original_value, injector_info.get("max_mold_opening_velocity"), VALID_NUMBER)
            if convert_type == "clamping":
                return caculateVelocityToPercent(original_value, injector_info.get("max_mold_clamping_velocity"), VALID_NUMBER)
            if convert_type == "forward":
                return caculateVelocityToPercent(original_value, injector_info.get("max_ejector_forward_velocity"), VALID_NUMBER)
            if convert_type == "backward":
                return caculateVelocityToPercent(original_value, injector_info.get("max_ejector_backward_velocity"), VALID_NUMBER)
            if convert_type == "injection":
                return caculateVelocityToPercent(original_value, injector_info.get("max_injection_velocity"), VALID_NUMBER)
            if convert_type == "holding":
                return caculateVelocityToPercent(original_value, injector_info.get("max_holding_velocity"), VALID_NUMBER)
            if convert_type == "decompressure":
                return caculateVelocityToPercent(original_value, injector_info.get("max_decompression_velocity"), VALID_NUMBER)
        elif original_unit == "mm/s" and converted_unit == "cm³/s" and getScrewArea(injector_info):
            return round(original_value*getScrewArea(injector_info)/1000,VALID_NUMBER)
            
        # 最大注射/保压/松退速度 单位是cm³/s
        elif original_unit == "%" and converted_unit == "cm³/s":
            if convert_type == "injection":
                return caculatePercentToRate(original_value, injector_info.get("max_injection_rate"), injector_info.get("max_injection_velocity"), injector_info, VALID_NUMBER)
            if convert_type == "holding":
                return caculatePercentToRate(original_value, injector_info.get("max_holding_rate"), injector_info.get("max_holding_velocity"), injector_info, VALID_NUMBER)
            if convert_type == "decompressure":
                return caculatePercentToRate(original_value, injector_info.get("max_decompression_rate"), injector_info.get("max_decompression_velocity"), injector_info, VALID_NUMBER)
        elif original_unit == "mm" and converted_unit == "inch":
            return round(original_value / 25.4, VALID_NUMBER)
        elif original_unit == "inch" and converted_unit == "mm":
            return round(original_value * 25.4, VALID_NUMBER) 

        elif original_unit == "mm" and converted_unit == "inch³" and getScrewArea(injector_info):
            return round(original_value*getScrewArea(injector_info)/ 25.4/ 25.4/ 25.4,VALID_NUMBER)
        elif original_unit == "inch³" and converted_unit == "mm" and getScrewArea(injector_info):
            return round(original_value/getScrewArea(injector_info)* 25.4* 25.4* 25.4,VALID_NUMBER)

        elif original_unit == "cm³" and converted_unit == "inch³" and getScrewArea(injector_info):
            return round(original_value*1000/ 25.4/ 25.4/ 25.4,VALID_NUMBER)
        elif original_unit == "cm³" and converted_unit == "inch" and getScrewArea(injector_info):
            return round(original_value/getScrewArea(injector_info)*1000 / 25.4/ 25.4/ 25.4,VALID_NUMBER)

        elif original_unit == "inch³" and converted_unit == "cm³" and getScrewArea(injector_info):
            return round(original_value/1000* 25.4* 25.4* 25.4,VALID_NUMBER)
        elif original_unit == "inch" and converted_unit == "cm³" and getScrewArea(injector_info):
            return round(original_value*getScrewArea(injector_info)/1000 * 25.4* 25.4* 25.4,VALID_NUMBER)

        elif original_unit == "cm³" and converted_unit == "mm" and getScrewArea(injector_info):
            return round(original_value/getScrewArea(injector_info)*1000,VALID_NUMBER)
        elif original_unit == "mm" and converted_unit == "cm³" and getScrewArea(injector_info):
            return round(original_value*getScrewArea(injector_info)/1000,VALID_NUMBER)

        # 螺杆转速
        elif original_unit == "cm/s" and converted_unit == "rpm" and getScrewCircumference(injector_info):
            print(f"转前{original_unit} 转后{converted_unit} 转后的数值{round(original_value/getScrewCircumference(injector_info)*10*60,VALID_NUMBER)}")
            return round(original_value/getScrewCircumference(injector_info)*10*60,1)
        # 最大螺杆转速 当前单位 rpm ,转化成cm/s
        elif original_unit == "cm/s" and converted_unit == "%":
            max_set = injector_info.get("max_screw_linear_velocity") if injector_info.get("max_screw_linear_velocity") else conversion('rpm', 'cm/s', float(injector_info.get("max_screw_linear_velocity")), injector_info)
            return round(original_value/float(max_set)*100,VALID_NUMBER)
        elif original_unit == "rpm" and converted_unit == "cm/s" and getScrewCircumference(injector_info):
            return round(original_value*getScrewCircumference(injector_info)/10/60,VALID_NUMBER)
        elif original_unit == "rpm" and converted_unit == "%" and getScrewCircumference(injector_info):
            cms = conversion(original_unit, "cm/s", float(original_value), injector_info, convert_type)
            return conversion("cm/s", converted_unit, cms, injector_info, convert_type)
        elif original_unit == "%" and converted_unit == "rpm" and getScrewCircumference(injector_info):
            cms = conversion(original_unit, "cm/s", float(original_value), injector_info, convert_type)
            return conversion("cm/s", converted_unit, cms, injector_info, convert_type)   
        elif original_unit == "cm/s" and converted_unit == "m/min":
            return round(original_value /100 *60, VALID_NUMBER)
        elif original_unit == "cm/s" and converted_unit == "mm/s":
            return round(original_value *10, VALID_NUMBER)
        elif original_unit == "mm/s" and converted_unit == "cm/s":
            return round(original_value /10, VALID_NUMBER)
        elif original_unit == "cm/s" and converted_unit == "m/s":
            return round(original_value /100, VALID_NUMBER)
        elif original_unit == "cm/s" and converted_unit == "inch/s":
            return round(original_value /2.54, VALID_NUMBER)

        elif original_unit == "m/min" and converted_unit == "cm/s":
            return round(original_value *100 /60, VALID_NUMBER)
        elif original_unit == "m/s" and converted_unit == "cm/s":
            return round(original_value *100, VALID_NUMBER)
        elif original_unit == "inch/s" and converted_unit == "cm/s":
            return round(original_value *2.54, VALID_NUMBER)
        elif original_unit == "%" and converted_unit == "cm/s" and injector_info.get("max_screw_rotation_speed"):
            max_set = conversion('rpm', 'cm/s', float(injector_info.get("max_screw_rotation_speed")), injector_info)
            return round(original_value*float(max_set)/100,VALID_NUMBER)
            
        # 时间转换
        elif original_unit == "μs" and converted_unit == "s":
            return round(original_value/1000000.0,VALID_NUMBER)
        elif original_unit == "s" and converted_unit == "μs":
            return round(original_value*1000000.0,VALID_NUMBER)

        # 温度转换
        elif original_unit == "℃" and converted_unit == "℉":
            return round(original_value *1.8 +32,VALID_NUMBER)
        elif original_unit == "℉" and converted_unit == "℃":
            return round((original_value -32)/1.8,VALID_NUMBER)
        else:
            logging.info(f"没有合适的转换 转之前的单位{original_unit} 转之后的单位{converted_unit} 转换之前的值{original_value}")

def pressure_conversion(original_unit=None, converted_unit=None, original_value=None, injector_info=None):

    # 压力转换
    # 全电 不需要这一条
    # 1kg/cm2 =14.223psi
    # 1bar=14.5psi
    # 1MPa=145psi

    if original_unit == "psi" and converted_unit == "kgf/cm²":
        return round(14.223*original_value,VALID_NUMBER)
    elif original_unit.lower() == "psi" and converted_unit == "bar":
        return round(14.5*original_value,VALID_NUMBER)
    elif original_unit.lower() == "psi" and converted_unit == "MPa":
        return round(145*original_value,VALID_NUMBER)
    elif original_unit == "bar" and converted_unit.lower() == "psi":
        return round(original_value/14.5,VALID_NUMBER)
    elif original_unit == "MPa" and converted_unit.lower() == "psi":
        return round(original_value/145,VALID_NUMBER)

    elif original_unit == "kgf/cm²" and converted_unit == "bar":
        return round(1.01*original_value,VALID_NUMBER)
    elif original_unit == "MPa" and converted_unit == "bar":
        return round(original_value*10,VALID_NUMBER)
    elif original_unit == "bar" and converted_unit == "kgf/cm²":
        return round(0.98*original_value,VALID_NUMBER)
    elif original_unit == "MPa" and converted_unit == "kgf/cm²":
        return round(9.8*original_value,VALID_NUMBER)         
    elif original_unit == "bar" and converted_unit == "MPa":
        return round(original_value/10,VALID_NUMBER)
    elif original_unit == "kgf/cm²" and converted_unit == "MPa":
        return round(0.101*original_value,VALID_NUMBER)
    elif original_unit == "barspec" and converted_unit == "kgf/cm²":
        return conversion("bar", "kgf/cm²",conversion(original_unit, "bar", original_value, injector_info),injector_info)
    elif original_unit == "barspec" and converted_unit == "MPa":
        return conversion("bar", "MPa",conversion(original_unit, "bar", original_value, injector_info),injector_info)

"""
保压单位转换

barspec→bar
压力bar=压力barspec（采集值）×螺杆横截面积mm2÷油缸面积mm2
            =压力barspec（采集值）×（π×螺杆直径mm2÷4）÷油缸面积mm2
如果活塞杆位于注射侧=true，那么油缸面积mm2=油缸数×π×油缸直径mm2÷4
如果活塞杆位于注射侧=false，那么油缸面积mm2=油缸数×（（π×油缸直径mm2÷4）-（π×活塞杆直径mm2÷4））
螺杆直径标签：Injection1.sv_rScrewDiameter
油缸数标签：Injection1.sv_CylinderData.iNumCylinders
油缸直径标签：Injection1.sv_CylinderData.rCylinderDiameter
活塞杆直径标签：Injection1.sv_CylinderData.rPistonRodDiameter
活塞杆位于注射侧标签：Injection1.sv_CylinderData.bUseSmallSize

cm³/s→mm/s：
线速度mm/s=体积速度cm³/s（采集值）÷面积mm2×1000.0
                   =体积速度cm³/s（采集值）÷(π×螺杆直径mm2÷4.0)×1000.0
螺杆直径标签：Injection1.sv_rScrewDiameter

cm³/s→%：
速度%=实际速度cm³/s（采集值）÷最大速度cm³/s×100.0
最大速度标签：Injection1.sv_rMaxSpeedFwdSpec

cm³→mm：
位置mm=实际位置cm³（采集值）÷面积mm2×1000.0
             =实际位置cm³（采集值）÷(π×螺杆直径mm2÷4.0)×1000.0
螺杆直径标签：Injection1.sv_rScrewDiameter
"""

"""
熔胶单位转换

cm/s→rpm
转速rpm=转速cm/s（采集值）÷周长mm×10.0×60.0
             =转速cm/s（采集值）÷（π×螺杆直径mm）×10.0×60.0
螺杆直径标签：Injection1.sv_rScrewDiameter

cm/s→%
转速%=转速cm/s（采集值）÷最大转速cm/s×100.0
最大转速标签：Injection1.sv_rMaxRotationPlast

cm³→mm：
位置mm=实际位置cm³（采集值）÷面积mm2×1000.0
             =实际位置cm³（采集值）÷(π×螺杆直径mm2÷4.0)×1000.0
螺杆直径标签：Injection1.sv_rScrewDiameter

"""


"""
松退单位转换

cm/s→rpm
转速rpm=转速cm/s（采集值）÷周长mm×10.0×60.0
             =转速cm/s（采集值）÷（π×螺杆直径mm）×10.0×60.0
螺杆直径标签：Injection1.sv_rScrewDiameter

cm/s→%
转速%=转速cm/s（采集值）÷最大转速cm/s×100.0
最大转速标签：Injection1.sv_rMaxRotationPlast

cm³→mm：
位置mm=实际位置cm³（采集值）÷面积mm2×1000.0
             =实际位置cm³（采集值）÷(π×螺杆直径mm2÷4.0)×1000.0
螺杆直径标签：Injection1.sv_rScrewDiameter
"""



"""
开合模单位转换

mm/s→%：
速度%=实际速度mm/s（采集值）÷最大速度mm/s×100.0
最大速度标签：Mold1.sv_rMaxSpeedFwd
"""



"""
调模单位转换

kN→bar
压力bar=实际压力kN（采集值）÷面积mm2×10000.0

l/min→%
速度%=实际速度l/min（采集值）÷绝对流量l/min×100.0
"""


"""
顶针进退单位转换

kN→bar （液压顶针）
压力bar=实际压力kN（采集值）÷面积mm2×10000.0
如果活塞杆位于顶针前进侧=false，那么面积mm2=油缸数×π×油缸直径mm2÷4
如果活塞杆位于顶针前进侧=true，那么面积mm2=油缸数×（（π×油缸直径mm2÷4）-（π×活塞杆直径mm2÷4））
电动顶针标签：Ejector1.sv_bElectric
油缸数标签：Ejector1.sv_CylinderData.iNumCylinders
油缸直径标签：Ejector1.sv_CylinderData.rCylinderDiameter
活塞杆直径标签：Ejector1.sv_CylinderData.rPistonRodDiameter
活塞杆位于顶针前进侧标签：Ejector1.sv_CylinderData.bUseSmallSize

mm/s→%
速度%=实际速度mm/s（采集值）÷最大速度mm/s×100.0
最大速度标签：Ejector1.sv_rMaxSpeedFwd
"""


"""
中子单位转换

l/min→%
速度%=实际速度l/min（采集值）÷绝对流量l/min×100.0
中子进绝对流量标签：Core1.sv_HydrMaxValuesIn.rAbsFlow
中子出绝对流量标签：Core1.sv_HydrMaxValuesOut.rAbsFlow

μs→s
时间s=实际时间μs（采集值）÷1000000.0
"""


"""
座进和座退单位转换

kN→bar
压力bar=实际压力kN（采集值）÷面积mm2×10000.0
如果活塞杆位于射台前进侧=false，那么面积mm2=油缸数×π×油缸直径mm2÷4
如果活塞杆位于射台前进侧=true，那么面积mm2=油缸数×（（π×油缸直径mm2÷4）-（π×活塞杆直径mm2÷4））
油缸数标签：Nozzle1.sv_CylinderData.iNumCylinders
油缸直径标签：Nozzle1.sv_CylinderData.rCylinderDiameter
活塞杆直径标签：Nozzle1.sv_CylinderData.rPistonRodDiameter
活塞杆位于射台前进侧标签：Nozzle1.sv_CylinderData.bUseSmallSize

mm/s→%
速度%=实际速度mm/s（采集值）÷最大速度mm/s×100.0
最大速度标签：Nozzle1.sv_rMaxSpeedFwd

μs→s
时间s=实际时间μs（采集值）÷1000000.0
"""


"""
机床实时参数

kN→bar
压力bar=实际压力kN（采集值）÷面积mm2×10000.0
如果活塞杆位于射台前进侧=false，那么面积mm2=油缸数×π×油缸直径mm2÷4
如果活塞杆位于射台前进侧=true，那么面积mm2=油缸数×（（π×油缸直径mm2÷4）-（π×活塞杆直径mm2÷4））
油缸数标签：Nozzle1.sv_CylinderData.iNumCylinders
油缸直径标签：Nozzle1.sv_CylinderData.rCylinderDiameter
活塞杆直径标签：Nozzle1.sv_CylinderData.rPistonRodDiameter
活塞杆位于射台前进侧标签：Nozzle1.sv_CylinderData.bUseSmallSize

mm/s→%
速度%=实际速度mm/s（采集值）÷最大速度mm/s×100.0
最大速度标签：Nozzle1.sv_rMaxSpeedFwd

μs→s
时间s=实际时间μs（采集值）÷1000000.0
"""