import logging
from math import log
from mdprocess.utils.process_initialization.process_para_type import InjectionParamSet, VPSwitchParamSet, HoldingParamSet, CoolingParamSet,\
    MeteringParamSet, DecompressionParamSet, TemperatureParamSet, ValveParamSet, MoldParamSet
from mdprocess.utils.process_initialization.macros import *
from gis.common.exceptions import BizException
from hsmolding.exceptions import ERROR_MACHINE, ERROR_POLYMER, ERROR_PRODUCT


def check_machine_info(machine_info: dict):

    print("-------------开始注塑机字段核查---------------")
    check_fields = {
        "nozzle_type": "喷嘴类型",
        "screw_diameter": "螺杆直径",
        "max_injection_stroke": "最大注射行程",
        
        "max_injection_pressure": "最大注射压力",
        "max_injection_velocity": "最大注射速度",
        "max_holding_pressure": "最大保压压力",
        "max_holding_velocity": "最大保压速度",
        "max_screw_rotation_speed": "最大螺杆转速",
        "max_metering_back_pressure": "最大计量背压",
        "max_decompression_velocity": "最大松退速度",

        "max_set_injection_pressure": "最大可设定注射压力",
        "max_set_injection_velocity": "最大可设定注射速度",
        "max_set_holding_pressure": "最大可设定保压压力",
        "max_set_holding_velocity": "最大可设定保压速度",
        "max_set_screw_rotation_speed": "最大可设定螺杆转速",
        "max_set_metering_back_pressure": "最大可设定计量背压",
        "max_set_decompression_velocity": "最大可设定松退速度"
    }
    if machine_info.get("power_method") == '液压机':
        # 液压机有计量压力和松退压力，需要校验
        check_fields = {
            **check_fields,
            "max_metering_pressure": "最大计量压力",
            "max_decompression_pressure": "最大松退压力",
            "max_set_metering_pressure": "最大可设定计量压力",
            "max_set_decompression_pressure": "最大可设定松退压力",
        }

    for key, filed_name in check_fields.items():
        if key not in machine_info.keys():
            raise BizException(ERROR_MACHINE, message='检验参数参数：{} 不存在，请联系系统管理员！'.format(filed_name))
        if not machine_info.get(key):
            raise BizException(ERROR_MACHINE, message='注塑机 {} 数据无效, 请检查并补充相关信息！'.format(filed_name))
        print("注塑机参数: {}，核查成功！".format(filed_name))
    print("-------------完成注塑机字段核查---------------")


def check_polymer_info(polymer_info: dict):
    print("-------------开始胶料字段核查---------------")
    check_fields = {
        "abbreviation": { "label": "材料名称缩写", "default": "ABS" },
        "category": { "label": "材料类型", "default": "结晶型" },
        "recommend_melt_temperature": { "label": "推荐成型温度", "default": 250 },
        "recommend_shear_linear_speed": { "label": "推荐剪切线速度", "default": 160 },
        "recommend_back_pressure": { "label": "推荐背压", "default": 15 },
        "recommend_mold_temperature": { "label": "推荐模具温度", "default": 0 },
        "ejection_temperature": {  "label": " 顶出温度", "default": 106 },
        "melt_density": { "label": "熔体密度", "default": 0.95 },
    }
    for key, item in check_fields.items():
        if key not in polymer_info.keys() or not polymer_info.get(key):
            polymer_info[key] = item.get("default")
            # raise BizException(ERROR_MACHINE, message='检验参数参数：{} 不存在，请联系系统管理员！'.format(item.get("label")))
        if not polymer_info.get(key):
            polymer_info[key] = item.get("default")
            # raise BizException(ERROR_MACHINE, message='注塑机 {} 数据无效, 请检查并补充相关信息！'.format(item.get("label")))
        print("胶料参数: {}，核查成功！".format(item.get("label")))
    print("-------------完成胶料字段核查---------------")


def check_initialization_info(init_info: dict):
    print("-------------开始制品字段核查---------------")
    check_fields = {
        "runner_weight": "流道重量",
        "gate_type": "浇口类别",
        "product_type": "制品类型",
        "product_weight": "制品总重量",
        "max_thickness": "制品最大壁厚",
        "ave_thickness": "制品平均壁厚",
        "max_length": "制品最大流长",
        "injection_stage": "注射段数",
        "holding_stage": "保压段数",
        "metering_stage": "计量段数",
        "barrel_temperature_stage": "料筒温度段数",
        "VP_switch_mode": "VP切换模式",
        "decompressure_mode_before_metering": "储前松退模式",
        "decompressure_mode_after_metering": "储后松退模式",
    }
    if init_info.get("gate_type") == "侧浇口" and init_info.get("gate_shape") == "圆形":
        check_fields = {
            **check_fields,
            "gate_shape": "浇口形状",
            "gate_radius": "浇口半径(圆)",
        }
    elif init_info.get("gate_type") == "侧浇口" and init_info.get("gate_shape") == "矩形":
        check_fields = {
            **check_fields,
            "gate_shape": "浇口形状",
            "gate_length": "浇口长(矩形)",
            "gate_width": "浇口宽(矩形)",
        }
    
    for key, filed_name in check_fields.items():
        if key not in init_info.keys() or not init_info.get(key):
            raise BizException(ERROR_PRODUCT, message='检验参数参数：{} 不存在，请联系系统管理员！'.format(filed_name))
        if init_info.get(key, None) is None:
            raise BizException(ERROR_PRODUCT, message='制品 {} 数据无效, 请检查并补充相关信息！'.format(filed_name))
        print("制品参数: {}，核查成功！".format(filed_name))
    print("-------------完成制品字段核查---------------")


def deduce_holding_time(params: dict):
    # 保压时间
    # hold_time = HSO_GATE_TYPE[product['gate_type']](product['ave_thickness'])
    if params['gate_type'] == "直浇口" or params['gate_type'] == "护耳式浇口" or params['gate_type'] == "点浇口":
        hold_time = 0.5 + 0.1 * params['ave_thickness']
    # elif product['gate_type'] == "点浇口":
    #     # hold_time = 0.1
    #     if product['gate_shape'] == "圆形":
    #         gate_area = HSO_PI * (product['gate_radius'] ** 2)
    #     elif product['gate_shape'] == "矩形":
    #         gate_area = product['gate_length'] * product['gate_width']
    #     else:
    #         return -1
    #     hold_time = 0.1 + gate_area / 0.01 * 2
    elif params['gate_type'] == "侧浇口":
        if params['gate_shape'] == "圆形":
            gate_area = HSO_PI * (params['gate_radius'] ** 2)
        elif params['gate_shape'] == "矩形":
            gate_area = params['gate_length'] * params['gate_width']
        else:
            return -1
        hold_time = 2 * gate_area
    else:  # 其他浇口
        hold_time = 0.3 + 0.6 * (params['ave_thickness'] ** 2)
    hold_time = max(2, min(hold_time, 10))
    
    if params['holding_stage'] > 1:  # 保压段数大于1
        # 多级保压dict
        multi_stage_holding_dict = {
            2: [0.5, 0.5],
            3: [0.3, 0.4, 0.3],
            4: [0.25, 0.25, 0.25, 0.25],
            5: [0.2, 0.2, 0.2, 0.2, 0.2]
        }

        # 提取对应段数的list
        holding_list = multi_stage_holding_dict.get(params['holding_stage'])
        
        return [ coef * hold_time for coef in holding_list ]
    else:
        return [ hold_time ]


# 工艺初始化
class ProcessInitializer:
    """
    工艺初始化器
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, machine_info, polymer_info):
        """
        工艺初始化依赖于材料和机器信息
        Parameters
        ----------
        machine_id：dict, 初始化使用的机器信息
        material_id：dict, 初始化使用的材料信息
        """
        # 检查信息是否为空
        if not machine_info:
            raise ValueError("机器信息不能为空！")
        if not polymer_info:
            raise ValueError("材料信息不能为空！")

        # 检查信息是否具备用于计算的key
        # Todo
        check_machine_info(machine_info)
        check_polymer_info(polymer_info)
        # 保留信息
        self.machine = machine_info
        self.material = polymer_info

        # 初始化工艺参数信息
        self.params = {
            "injection_param": InjectionParamSet(),
            "vp_switch_param": VPSwitchParamSet(),
            "holding_param": HoldingParamSet(),
            "cooling_param": CoolingParamSet(),
            "metering_param": MeteringParamSet(),
            "decompression_param": DecompressionParamSet(),
            "temperature_param": TemperatureParamSet(),
            "valve_param": ValveParamSet(),
            "mold_param": MoldParamSet()
        }

    def deduce(self, init_info: dict):
        """
        通过制品信息和机器、材料信息推断初始工艺参数

        Parameters
        ----------
        init_info dict,  制品信息

        Returns
        -------
        Params : dict, 对应制品的生成的初始工艺参数
        """
        product = init_info  # 制品信息
        self.product = product
        check_initialization_info(product)  # 检查制品输入信息

        """
        注射参数推断, 默认一段，包括：射胶延迟、注射时间、注射压力、注射速度、注射位置
        Returns  0: 成功, -1:失败
        """
        injection_param: InjectionParamSet = self.params['injection_param']

        # 注射压力
        inj_ratio = product['max_length'] / product['ave_thickness']  # 最大流长与平均壁厚比值
        inj_pres = self.machine['max_set_injection_pressure'] * 0.65
        # injection_param.inj_ratio = inj_ratio
        # if inj_ratio > 350:
        #     inj_pres = 0.94 * inj_pres
        # else:
        #     for ratio, proportion in HSO_RATIO_PRESSURE_MAP.items():
        #         if inj_ratio < ratio:
        #             inj_pres = proportion * inj_pres
        #             break

        # 注射速度
        max_inj_velo = self.machine['max_set_injection_velocity']  # 机器最大注射速度
        poly_type = self.material['abbreviation']  # 材料所属大类
        poly_types = [
            "PVC", "POM", "PMMA", "ABS", "AS",
            "PE", "HDPE", "LDPE", "LLDPE", "PP"
        ]
        if poly_type in poly_types:
            inj_velo = max_inj_velo * (0.3 + inj_ratio / 500.0) if (inj_ratio < 100) else 0.4 * max_inj_velo
        elif poly_type == "PC+ABS":
            inj_velo = max_inj_velo * (0.215 + inj_ratio / 800.0) if (inj_ratio < 100) else 0.34 * max_inj_velo
        else:
            inj_velo = max_inj_velo * (0.35 + inj_ratio / 500.0) if (inj_ratio < 100) else 0.42 * max_inj_velo

        # 计算注射行程
        total_weight = product['product_weight']
        runner_weight = product['runner_weight']
        product_weight = total_weight - runner_weight
        print("total_weight: {}, runner_weight: {}, product_weight: {}".format(total_weight, runner_weight, product_weight))
        if total_weight <= 0:
            raise BizException(ERROR_PRODUCT, message="制品重量加流道重量小于等于零,请修改！")
        elif total_weight <= 50:
            # length_ratio = 0.97
            length_ratio = 0.85
        elif 50 < total_weight <= 100:
            # length_ratio = 0.93
            length_ratio = 0.90
        else:
            # length_ratio = 0.88
            length_ratio = 0.95
        injection_volume = total_weight / self.material['melt_density']  # 单位为cm³
        injection_length = injection_volume * 1000.0 / (HSO_PI * (self.machine['screw_diameter'] ** 2) / 4)
        injection_param.fInjectLen = injection_length * length_ratio
        inj_posi = 0 # 一段注射时，注射位置为切换位置，默认为0

        # 计算注射时间
        # inj_time = 5.00  # 最大值
        # # for weight, time in HSO_WEIGHT_TIME_MAP.items():
        # #     if total_weight < weight:
        # #         inj_time = time
        # #         break
        # # 注射时间与注射速度建立关系
        # inj_time = inj_time * (80 / inj_velo)
        inj_time = 4 * injection_param.fInjectLen/inj_velo
        if inj_time < 3:
            inj_time = 3
        injection_param.fInjectTime = inj_time

        # 注射延迟时间
        injection_param.fInjectDelay = HSO_INJ_START_DELAY_TIME

        # 数组参数填充
        injection_param.fInjectPresSteps = [ inj_pres ]
        injection_param.fInjectVelocitySteps = [ inj_velo ]
        injection_param.fInjectPositionSteps = [ inj_posi ]
        
        """
        VP切换参数推断,包括VP切换模式、VP切换时间、VP切换位置、VP切换压力、VP切换速度
        Returns 0: 成功, -1:失败
        """
        VP_switch_param: VPSwitchParamSet = self.params['vp_switch_param']

        # 计算VP位置, 与制品类型相关,目前只有位置生效
        base_posi = 15
        VP_swit_posi = base_posi + (1 - length_ratio) * injection_length
        VP_swit_mode = product['VP_switch_mode']
        VP_switch_param.sVPSwitchMode = VP_swit_mode
        if VP_swit_mode == "位置":
            if product_weight >= 120:
                base_posi = 15
            else:
                base_posi = 10
            VP_swit_posi = base_posi + (1 - length_ratio) * injection_length
            VP_switch_param.fVPPos = VP_swit_posi
        elif VP_swit_mode == "时间":
            VP_swit_time = 0
            VP_switch_param.fVPTime = VP_swit_time
        elif VP_swit_mode == "时间&位置":
            VP_swit_time = 0
            VP_switch_param.fVPTime = VP_swit_time
        elif VP_swit_mode == "压力":
            VP_swit_pres = 0
            VP_switch_param.fVPPres = VP_swit_pres
        elif VP_swit_mode == "速度":
            VP_swit_velo = 0
            VP_switch_param.fVPVelo = VP_swit_velo
        # VP切换位置确定，更新一段注射位置
        injection_param.fInjectPositionSteps = [ VP_swit_posi ]
        
        """
        保压参数推断，默认一段，包括保压压力、保压速度、保压时间
        Returns 0: 成功, -1:失败
        """
        holding_param: HoldingParamSet = self.params['holding_param']


        # 保压压力(给的过于笼统，需要根据材料进一步区分)
        # PP料收缩率小，凝固时间短，保压压力一般为50-100MPa，保压时间一般为2-5秒
        # ABS的收缩率较大，PC的凝固时间较长，需要较大的保压压力和时间，保压压力一般为60-150MPa，保压时间一般为3-7秒
        # hold_pres = 0.1 * self.machine['max_set_holding_pressure'] + 10 * product['ave_thickness']  # 旧算法
        hold_pres = 0.25 * self.machine['max_set_holding_pressure'] + 10 * product['ave_thickness']  # 4.6-4.8试模修正
        if hold_pres >= 120:
            hold_pres = 0.65 * inj_pres

        # 保压速度
        # hold_velo = 0.3 * self.machine["max_set_holding_velocity"]
        hold_velo = 0.15 * self.machine["max_set_holding_velocity"]
        
        # 保压时间
        # hold_time = HSO_GATE_TYPE[product['gate_type']](product['ave_thickness'])
        if product['gate_type'] == "直浇口" or product['gate_type'] == "护耳式浇口" or product['gate_type'] == "点浇口":
            hold_time = 0.5 + 0.1 * product['ave_thickness']
        # elif product['gate_type'] == "点浇口":
        #     # hold_time = 0.1
        #     if product['gate_shape'] == "圆形":
        #         gate_area = HSO_PI * (product['gate_radius'] ** 2)
        #     elif product['gate_shape'] == "矩形":
        #         gate_area = product['gate_length'] * product['gate_width']
        #     else:
        #         return -1
        #     hold_time = 0.1 + gate_area / 0.01 * 2
        elif product['gate_type'] == "侧浇口":
            if product['gate_shape'] == "圆形":
                gate_area = HSO_PI * (product['gate_radius'] ** 2)
            elif product['gate_shape'] == "矩形":
                gate_area = product['gate_length'] * product['gate_width']
            else:
                return -1
            hold_time = 2 * gate_area
        else:  # 其他浇口
            hold_time = 0.3 + 0.6 * (product['ave_thickness'] ** 2)
        hold_time = max(2, min(hold_time, 10))

        # 保压限速
        holding_param.fPackLimitVelocity = HSO_PACK_VELOCITY

        # 数组数据填充 (初始化默认不加保压)
        holding_param.fPackPresSteps = [ hold_pres ]
        holding_param.fPackVeloSteps = [ hold_velo ]
        holding_param.fPackTimeSteps = [ hold_time ]
        
        """
        冷却参数推断，包括冷却时间
        Returns 0: 成功, -1:失败
        """
        cooling_param: CoolingParamSet = self.params['cooling_param']
        
        # 冷却时间 简化版算法，影响因素：最大壁厚、产品重量
        k_weight = 1
        if product_weight >= 100:
            k_weight = (product_weight / 100) ** 0.5

        cool_time = 5 * product['max_thickness'] * k_weight
        cooling_param.fCoolTime = round(cool_time)  # 冷却时间
        if product.get("inject_cycle_require", None) is not None:
            # 缩减冷却时间，与推荐周期时间相对应
            inject_cycle_require = product["inject_cycle_require"]
            else_time = 1.5
            cooling_param.fCoolTime = int(inject_cycle_require - inj_time - hold_time - else_time)

        # 复杂版算法，影响因素：最大壁厚、平均壁厚、推荐熔体温度、顶出温度、模温
        # # 提取计算所需信息
        # category = self.material['category']
        # rec_melt_temp = self.material['recommend_melt_temperature']
        # ejec_temp = self.material['ejection_temperature']
        # ave_thickness = product['ave_thickness']
        # mold_temp = product['mold_temperature']
        # a = 1
        #
        # # 冷却时间计算
        # if category == "无定形":
        #     if self.params['injection_param'].inj_ratio > 100:  # 薄壁制品
        #         tmp1 = ave_thickness**2 / (a * HSO_PI**2)
        #         tmp2 = 4 / HSO_PI * (rec_melt_temp - mold_temp) / (ejec_temp - mold_temp)
        #         cool_time = tmp1 * log(tmp2)
        #     else:
        #         tmp1 = (ave_thickness**2) / (a * HSO_PI**2)
        #         tmp2 = 8 * (rec_melt_temp - mold_temp) / ((ejec_temp - mold_temp) * HSO_PI**2)
        #         cool_time = tmp1 * log(tmp2)
        #
        #
        # # 冷却时间
        # crys_mor = "结晶型"
        # ther_dif = self.material['thermal_diffusity']  # 材料热扩散系数，需在材料数据库添加并提取
        # rec_melt_temp = self.material['recommend_melt_temperature']
        # eje_temp = self.material['ejection_temperature']  # 材料顶出温度，需要从数据库提取
        # max_thick = product['max_thickness']
        # ave_thick = product['ave_thickness']
        # mold_temp = product['mold_temp']  # 模具温度，需提取
        # if crys_mor == "无定型":
        #     if self.params['injection_param'].inj_ratio > 100:  # 薄壁制品
        #         tmp1 = (max_thick**2) / (HSO_PI**2) / ther_dif
        #         tmp2 = 4 * (rec_melt_temp - mold_temp) / HSO_PI / (eje_temp - mold_temp)
        #         cool_time = tmp1 * math.log(tmp2)
        #     else:
        #         tmp1 = (max_thick ** 2) / (HSO_PI ** 2) / ther_dif
        #         tmp2 = 8 * (rec_melt_temp - mold_temp) / (HSO_PI**2) / (eje_temp - mold_temp)
        #         cool_time = tmp1 * math.log(tmp2)
        # else:
        #     if self.material['abbreviation'] == "PE":
        #         cool_time = 79.98 * (ave_thick**2) * (rec_melt_temp + 28.9)/(185.6 - mold_temp)
        #     elif self.material['abbreviation'] == "PP":
        #         cool_time = 37.85 * (ave_thick ** 2) * (rec_melt_temp + 490) / (223.9 - mold_temp)
        #     elif self.material['abbreviation'] == "POM":
        #         cool_time = 36.27 * (ave_thick ** 2) * (rec_melt_temp + 157.8) / (157.8 - mold_temp)
        #     else:
        #         tmp1 = (max_thick ** 2) / (HSO_PI ** 2) / ther_dif
        #         tmp2 = 4 * (rec_melt_temp - mold_temp) / HSO_PI / (eje_temp - mold_temp)
        #         cool_time = tmp1 * math.log(tmp2)

        # 参数填充
        cooling_param.fCoolTime = cool_time  # 冷却时间
        
        """
        计量参数推断,包括计量压力、螺杆转速、背压、位置
        Returns 0: 成功, -1:失败
        """
        metering_param: MeteringParamSet = self.params['metering_param']


        # 储料延迟时间
        metering_param.fStartDelay = HSO_METER_START_DELAY_TIME

        # 计量压力 (全电机没有计量压力)
        meter_pres = 0
        if self.machine['power_method'] == '液压机':
            if self.machine['nozzle_type'] == "直通型":
                meter_pres = 0.55 * float(self.machine['max_set_metering_pressure'])
            elif self.machine['nozzle_type'] == "锁闭型":
                meter_pres = 0.6 * float(self.machine['max_set_metering_pressure'])

        # 计量螺杆转速
        temp_ratio = 60.0 * self.material['recommend_shear_linear_speed'] / (self.machine['screw_diameter'] * HSO_PI) \
                    / self.machine['max_set_screw_rotation_speed']
        temp_ratio = max(0.3, min(temp_ratio, 0.75)) # 约束取值范围
        meter_scw_rot_speed = temp_ratio * self.machine['max_set_screw_rotation_speed']

        # 计量背压
        meter_back_pres = self.material['recommend_back_pressure']

        # 计量位置
        meter_posi = base_posi + injection_length

        # 数组数据填充
        metering_param.fPressure = [ meter_pres ]
        metering_param.fVelocity = [ meter_scw_rot_speed ]
        metering_param.fBackPressure = [ meter_back_pres ]
        metering_param.fMeteringPos = [ meter_posi ]
        
        """
        松退参数推断
        Returns 0: 成功, -1:失败
        """
        decom_param: DecompressionParamSet = self.params['decompression_param']
        
        # 推断前松退参数 (全电机没有松退压力)
        decompres_pres_bef_meter = 0 # 计量前松退压力
        if self.machine['power_method'] == '液压机':
            decompres_pres_bef_meter = 0.4 * float(self.machine['max_set_metering_pressure'])
        decompres_velo_bef_meter = HSO_SUCKBACK_VELO_BEFORE_METER  # 计量前松退速度
        decompres_dist_bef_meter = HSO_SUCKBACK_DIS_BEFORE_METER  # 计量前松退距离
        decompres_time_bef_meter = 0  # 计量前松退时间

        # 推断后松退参数 (全电机没有松退压力)
        decompres_pres_aft_meter = 0 # 计量前松退压力
        if self.machine['power_method'] == '液压机':
            decompres_pres_aft_meter = 0.4 * float(self.machine['max_set_metering_pressure'])
        # 计量后松退速度设定原则：设定时与螺杆转速、背压相适应
        decompres_velo_aft_meter = HSO_SUCKBACK_VELO_AFTER_METER  # 计量后松退速度
        # 计量后松退距离
        decompres_dist_aft_meter = 0.1 * injection_length
        decompres_dist_aft_meter = max(2, min(decompres_dist_aft_meter, 10))  # 约束取值范围
        decompres_time_aft_meter = 0  # 获取计量后松退时间

        # 前松退参数
        # decom_param.sBeforeSuckMode = product["decompressure_mode_before_metering"]  # 前松退模式
        decom_param.sBeforeSuckMode = '否'  # 前松退模式固定为’否’
        decom_param.fBeforeBackPressure = decompres_pres_bef_meter  # 计量前松退压力
        decom_param.fBeforeMeasureVel = decompres_velo_bef_meter  # 计量前松退速度
        decom_param.fBeforeMeasureDis = decompres_dist_bef_meter  # 计量前松退距离
        decom_param.fBeforeTime = decompres_time_bef_meter  # 计量前松退时间
        
        # 后松退参数
        decom_param.sAfterSuckMode = product["decompressure_mode_after_metering"]  # 后松退模式
        decom_param.sAfterSuckMode = '距离'  # 后松退模式固定为‘距离’
        decom_param.fAfterBackPressure = decompres_pres_aft_meter  # 计量后松退压力
        decom_param.fAfterMeasureVel = decompres_velo_aft_meter  # 计量后松退速度
        decom_param.fAfterMeasureDis = decompres_dist_aft_meter  # 计量后松退距离
        decom_param.fAfterTime = decompres_time_aft_meter  # 计后前松退时间

        # 获取计量终止位置
        meter_end_posi = meter_posi + decompres_dist_aft_meter
        decom_param.fStopPos = meter_end_posi  # 储料终止位置
        
        """
        温度参数推断, 直接使用材料信息中的推荐温度进行初始化
        Returns 0: 成功, -1:失败
        """
        temperature_param: TemperatureParamSet = self.params['temperature_param']
        
        # 喷嘴温度，防流涎：材料推荐成型温度，不防流涎：材料推荐成型温度-5.0
        temperature_param.nozzle_temp = self.material['recommend_melt_temperature'] - 5.0
        if self.machine['nozzle_type'] == "直通型":
            temperature_param.nozzle_temp = self.material['recommend_melt_temperature'] - 5.0
        elif self.machine['nozzle_type'] == "锁闭型":
            temperature_param.nozzle_temp = self.material['recommend_melt_temperature']

        # 料筒段数
        if product.get('barrel_temperature_stage'):
            temperature_param.barrel_temperature_stage = product['barrel_temperature_stage']
        else:
            temperature_param.barrel_temperature_stage = 5

        # 料筒各段温度
        temperature_param.fTemperature = []
        if temperature_param.barrel_temperature_stage < 7:
            for i in range(temperature_param.barrel_temperature_stage - 1):
                temperature_param.fTemperature.append(self.material['recommend_melt_temperature'] - 10 * i)
        else:
            for i in range(temperature_param.barrel_temperature_stage - 1):
                temperature_param.fTemperature.append(self.material['recommend_melt_temperature'] - 8 * i)

        """
        模温初始参数推荐
        Returns 0: 成功, -1:失败
        """
        mold_param: MoldParamSet = self.params['mold_param']
        
        mold_tmp_dic = {
            "PP": 40,
            "PC": 80,
            "ABS": 50,
            "PC+ABS": 70,
            "PC/ABS": 70,
            "PS": 40,
            "PE": 40,
            "LDPE": 40,
            "HDPE": 40,
            "LLDPE":40,
            "PVC": 40,
            "PA6": 60,
            "PA66": 70,
            "PA": 60,
            "PET": 90,
        }

        mold_temp = 50
        if self.material['recommend_mold_temperature'] != 0:
            mold_temp = self.material['recommend_mold_temperature']
        else:
            mold_temp = mold_tmp_dic.get(self.material['abbreviation'], 50)
        mold_param.mold_temp = mold_temp

        """
        热流道参数推断, 使用模具信息中的阀口数量
        Returns 0: 成功, -1:失败
        """
        valve_param: ValveParamSet = self.params['valve_param']
        
        # 热流道阀口数量
        valve_num = product['valve_num']
        valve_param.fTime = []
        if valve_num:
            valve_param.fTime = [ i for i in range(1, int(valve_num) + 1)]

        # # 注射段数，默认一段注射成型
        # injection_param.injection_stage = product['injection_stage']
        # # 保压段数, 默认1段
        # holding_param.holding_stage = product['holding_stage']
        # # 计量段数
        # metering_param.metering_stage = product['metering_stage']

        # 注射段数改为自动推荐
        if injection_param.fInjectLen >= 40:
            injection_param.injection_stage = 4
        elif injection_param.fInjectLen <= 40 and injection_param.fInjectLen > 20:
            injection_param.injection_stage = 3
        elif injection_param.fInjectLen <= 20 and injection_param.fInjectLen > 10:
            injection_param.injection_stage = 2
        else:
            injection_param.injection_stage = 1

        # 保压段数改为自动推荐
        holding_param.holding_stage = 2

        # 计量段数默认为1段
        metering_param.metering_stage = 1
        
        # 多级注射，多级保压，多级计量
        if injection_param.injection_stage > 1:
            if runner_weight <= 0.01:
                # 热流道
                multi_stage_injection_dict = {
                    2: [[1, 1.05], [0.78, 1], [0.9, 0]],
                    3: [[1, 1.05, 1], [0.78, 1, 0.45], [0.9, 0.3, 0]],
                    4: [[1, 1, 1.05, 1], [0.78, 0.9, 1, 0.45], [0.9, 0.4, 0.15, 0]],
                    5: [[1, 1, 1.05, 1.03, 1], [0.78, 1, 1.2, 1.5, 0.45], [0.9, 0.65, 0.4, 0.15, 0]],
                    6: [[1, 1, 1.05, 1.05, 1.03, 1], [0.78, 1, 1.2, 1.5, 1.3, 0.45], [0.9, 0.7, 0.4, 0.25, 0.1, 0]]
                }
            else:
                # 冷流道
                multi_stage_injection_dict = {
                    2: [[1, 1.05], [1, 0.8]],
                    3: [[1, 1.05, 1], [0.78, 1, 0.45]],
                    4: [[1, 1, 1.05, 1], [0.7, 0.36, 1, 0.45]],
                    5: [[1, 1, 1.05, 1.03, 1], [0.7, 0.36, 1, 1.2, 0.45]],
                    6: [[1, 1, 1.05, 1.05, 1.03, 1], [0.7, 0.3, 1, 1.2, 1.1, 0.45]]
                }
            
            if self.material['abbreviation'] == "ABS":
                if runner_weight <= 0.01:
                    # 热流道
                    multi_stage_injection_dict = {
                        2: [[1, 1.05], [0.78, 1], [0.9, 0]],
                        3: [[1, 1.05, 0.75], [0.78, 1, 0.5], [0.9, 0.3, 0]],
                        4: [[1, 1, 1.05, 0.75], [0.78, 1, 1.3, 0.5], [0.9, 0.4, 0.15, 0]],
                        5: [[1, 1, 1.05, 1.03, 0.75], [0.78, 1, 1.2, 1.5, 0.5], [0.9, 0.65, 0.4, 0.15, 0]],
                        6: [[1, 1, 1.05, 1.05, 1.03, 0.75], [0.78, 1, 1.2, 1.5, 1.3, 0.5], [0.9, 0.7, 0.4, 0.25, 0.1, 0]]
                    }
                else:
                    # 冷流道
                    multi_stage_injection_dict = {
                        2: [[1, 1.05], [0.36, 1]],
                        3: [[1, 1.05, 0.75], [0.45, 1, 0.4]],
                        4: [[1, 1, 1.05, 0.75], [0.7, 0.4, 1, 0.5]],
                        5: [[1, 1, 1.05, 1.03, 0.75], [0.7, 0.4, 1, 1.2, 0.5]],
                        6: [[1, 1, 1.05, 1.05, 1.03, 0.75], [0.7, 0.3, 1, 1.2, 1.1, 0.4]]
                    }


            # 多级注射系数
            injection_list = multi_stage_injection_dict.get(injection_param.injection_stage)

            # 计算多级注射压力
            injection_param.fInjectPresSteps = [ coef * inj_pres for coef in injection_list[0]]                

            # 计算多级注射速度
            injection_param.fInjectVelocitySteps = [ coef * inj_velo for coef in injection_list[1]]                
            
            # 计算多级注射位置
            if runner_weight <= 0.01:
                injection_param.fInjectPositionSteps = [ VP_swit_posi + coef * (injection_param.fInjectLen + decompres_dist_aft_meter) for coef in injection_list[2] ]
            else:
                part_percent = product_weight / total_weight
                runner_percent = runner_weight / total_weight

                if injection_param.injection_stage == 2:
                    inj_posi_1 = meter_end_posi - 1.05 * runner_percent * injection_param.fInjectLen  # 注射一段位置
                    inj_posi_2 = VP_swit_posi # 注射二段位置，即VP切换位置
                    injection_param.fInjectPositionSteps = [inj_posi_1, inj_posi_2]

                elif injection_param.injection_stage == 3:
                    inj_posi_1 = meter_end_posi - 1.05 * runner_percent * injection_param.fInjectLen  # 注射一段位置
                    inj_posi_2 = VP_swit_posi + 0.09 * injection_param.fInjectLen  # 注射二段位置
                    inj_posi_3 = VP_swit_posi  # 注射三段位置
                    injection_param.fInjectPositionSteps = [inj_posi_1, inj_posi_2, inj_posi_3]

                elif injection_param.injection_stage == 4:
                    inj_posi_1 = meter_end_posi - 0.98 * runner_percent * injection_param.fInjectLen
                    inj_posi_2 = meter_end_posi - (runner_percent + 0.05 * part_percent) * injection_param.fInjectLen
                    inj_posi_3 = VP_swit_posi + 0.09 * injection_param.fInjectLen
                    inj_posi_4 = VP_swit_posi
                    injection_param.fInjectPositionSteps = [inj_posi_1, inj_posi_2, inj_posi_3, inj_posi_4]

                elif injection_param.injection_stage == 5:
                    inj_posi_1 = meter_end_posi - 0.98 * runner_percent * injection_param.fInjectLen
                    inj_posi_2 = meter_end_posi - (runner_percent + 0.05 * part_percent) * injection_param.fInjectLen
                    inj_posi_3 = meter_end_posi - (runner_percent + 0.5 * part_percent) * injection_param.fInjectLen
                    inj_posi_4 = VP_swit_posi + 0.09 * injection_param.fInjectLen
                    inj_posi_5 = VP_swit_posi
                    injection_param.fInjectPositionSteps = [inj_posi_1, inj_posi_2, inj_posi_3, inj_posi_4, inj_posi_5]

                elif injection_param.injection_stage == 6:
                    inj_posi_1 = meter_end_posi - 0.98 * runner_percent * injection_param.fInjectLen
                    inj_posi_2 = meter_end_posi - (runner_percent + 0.05 * part_percent) * injection_param.fInjectLen
                    inj_posi_3 = meter_end_posi - (runner_percent + 0.4 * part_percent) * injection_param.fInjectLen
                    inj_posi_4 = meter_end_posi - (runner_percent + 0.7 * part_percent) * injection_param.fInjectLen
                    inj_posi_5 = VP_swit_posi + 0.09 * injection_param.fInjectLen
                    inj_posi_6 = VP_swit_posi
                    injection_param.fInjectPositionSteps = [inj_posi_1, inj_posi_2, inj_posi_3, inj_posi_4,
                                                            inj_posi_5, inj_posi_6]
                
        if holding_param.holding_stage > 1:
            # 多级保压dict
            multi_stage_holding_dict = {
                2: [[1, 0.5], [1, 0.5], [0.5, 0.5]],
                3: [[1, 0.7, 0.4], [1, 0.7, 0.4], [0.3, 0.4, 0.3]],
                4: [[1, 0.75, 0.5, 0.25], [1, 0.75, 0.5, 0.25], [0.25, 0.25, 0.25, 0.25]],
                5: [[1, 0.8, 0.6, 0.4, 0.2], [1, 0.8, 0.6, 0.4, 0.2], [0.2, 0.2, 0.2, 0.2, 0.2]]
            }
                
            # 提取对应段数的list
            holding_list = multi_stage_holding_dict.get(holding_param.holding_stage)

            # 计算多级保压压力
            holding_param.fPackPresSteps = [ coef * hold_pres for coef in holding_list[0] ]

            # 计算多级保压速度
            holding_param.fPackVeloSteps = [ coef * hold_velo for coef in holding_list[1] ]

            # 计算多级保压时间
            holding_param.fPackTimeSteps = [ coef * hold_time for coef in holding_list[2] ]
        
        if metering_param.metering_stage > 1:
            #多级计量dict
            multi_stage_metering_dict = {
                2: [[1, 1], [1, 0.8], [0.8, 1], [0.5, 1]],
                3: [[1, 1, 1], [0.75, 1, 0.75], [0.5, 0.75, 1], [0.3, 0.7, 1]],
                4: [[1, 1, 1, 1], [0.75, 1, 1, 0.75], [0.25, 0.5, 0.75, 1], [0.2, 0.5, 0.8, 1]],
            }
            
            # 提取对应段数的list
            metering_list = multi_stage_metering_dict.get(metering_param.metering_stage)
            
            # 计算多级计量压力
            metering_param.fPressure = [ coef * meter_pres for coef in metering_list[0] ]

            # 计算多级计量螺杆转速
            metering_param.fVelocity = [ coef * meter_scw_rot_speed for coef in metering_list[1] ]

            # 计算多级计量背压
            metering_param.fBackPressure = [ coef * meter_back_pres for coef in metering_list[2] ]

            # 计算多级计量位置
            metering_param.fMeteringPos = [ base_posi + coef * injection_length for coef in metering_list[3] ]


        """
        对输出数据进行格式化
        """
        # 提取对象信息
        injection_param: InjectionParamSet = self.params['injection_param']
        vp_switch_param: VPSwitchParamSet = self.params['vp_switch_param']
        holding_param: HoldingParamSet = self.params['holding_param']
        cooling_param: CoolingParamSet = self.params['cooling_param']
        metering_param: MeteringParamSet = self.params['metering_param']
        decompression_param: DecompressionParamSet = self.params['decompression_param']
        temperature_param: TemperatureParamSet = self.params['temperature_param']

        # 注射参数
        for i in range(injection_param.injection_stage):
            injection_param.fInjectPresSteps[i] = round(injection_param.fInjectPresSteps[i], 0)
            injection_param.fInjectVelocitySteps[i] = round(injection_param.fInjectVelocitySteps[i], 0)
            injection_param.fInjectPositionSteps[i] = round(injection_param.fInjectPositionSteps[i], 2)

        # 注射时间
        injection_param.fInjectTime = round(injection_param.fInjectTime, 2)
        # 注射延时
        injection_param.fInjectDelay = round(injection_param.fInjectDelay, 2)

        # VP切换参数
        vp_switch_param.fVPPres = round(vp_switch_param.fVPPres, 0)
        vp_switch_param.fVPPos = round(vp_switch_param.fVPPos, 2)
        vp_switch_param.fVPTime = round(vp_switch_param.fVPTime, 2)

        # 保压参数
        for i in range(holding_param.holding_stage):
            holding_param.fPackPresSteps[i] = round(holding_param.fPackPresSteps[i], 0)
            holding_param.fPackVeloSteps[i] = round(holding_param.fPackVeloSteps[i], 0)
            holding_param.fPackTimeSteps[i] = round(holding_param.fPackTimeSteps[i], 2)

        # 冷却参数
        cooling_param.fCoolTime = round(cooling_param.fCoolTime, 2)

        # 计量参数
        for i in range(metering_param.metering_stage):
            metering_param.fPressure[i] = round(metering_param.fPressure[i], 0)
            metering_param.fVelocity[i] = round(metering_param.fVelocity[i], 0)
            metering_param.fBackPressure[i] = round(metering_param.fBackPressure[i], 0)
            metering_param.fMeteringPos[i] = round(metering_param.fMeteringPos[i], 2)

        # 计量延时
        metering_param.fStartDelay = round(metering_param.fStartDelay, 2)

        # 松退参数
        decompression_param.fBeforeBackPressure = round(decompression_param.fBeforeBackPressure, 0)
        decompression_param.fBeforeMeasureVel = round(decompression_param.fBeforeMeasureVel, 0)
        decompression_param.fBeforeMeasureDis = round(decompression_param.fBeforeMeasureDis, 2)
        decompression_param.fBeforeTime = round(decompression_param.fBeforeTime, 2)

        decompression_param.fAfterBackPressure = round(decompression_param.fAfterBackPressure, 0)
        decompression_param.fAfterMeasureVel = round(decompression_param.fAfterMeasureVel, 0)
        decompression_param.fAfterMeasureDis = round(decompression_param.fAfterMeasureDis, 2)
        decompression_param.fAfterTime = round(decompression_param.fAfterTime, 2)

        # 终止位置
        decompression_param.fStopPos = round(decompression_param.fStopPos, 2)

        # 温度参数
        temperature_param.nozzle_temp = round(temperature_param.nozzle_temp, 0)
        for i in range(temperature_param.barrel_temperature_stage - 1):
            temperature_param.fTemperature[i] = round(temperature_param.fTemperature[i], 0)
                    
        return self.params
    