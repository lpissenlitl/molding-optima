"""
注塑参数按照类型划分为多个数据类
"""


class InjectionParamSet:
    """
    注射参数集合类，参数定义来源于原始C++版本
    """

    def __init__(self):
        """
        注射参数实例化，分为状态量、限制量、中间量

        Notes
        -----
        f_: float n_: int
        """
        # 实际状态量
        self.injection_stage = 1  # 分级注射的实际段数,默认一段
        self.fInjectPresSteps = []  # 分级压力数组
        self.fInjectVelocitySteps = []  # 分级速度数组
        self.fInjectPositionSteps = []  # 分级位置数组
        self.fInjectTime = 0.0  # 注射时间（单位：s）
        self.fInjectDelay = 0.0  # 注射延迟（单位：s）

        # 状态限制量
        self.nInjectMaxCount = 6  # 当前版本最大允许注射段数
        self.fInjectMaxTime = 0.0  # 充填过量控制（单位：s）

        # 不是实际工艺参数，用于计算的中间变量，不用于输出
        self.fInjectLen = 0.0  # 注射行程
        self.inj_ratio = 0.0  # 比率

    def __repr__(self):
        return repr(vars(self))


class VPSwitchParamSet:
    """
    VP切换参数集合类
    """

    def __init__(self):
        """
        VP切换参数实例化，分为状态量、限制量

        Notes
        -----
        f_: float n_: int
        """
        # 状态量
        self.nVPSwitchType = 1  # VP转换类型，默认为位置转换
        self.sVPSwitchMode = "位置"  # VP转换类型
        self.fVPPos = 0.0  # V-P转化的位置设置（单位：mm）
        self.fVPTime = 0.0  # VP切换时间
        self.fVPPres = 0.0  # VP切换压力
        self.fVPVelo = 0.0  # VP切换速度

    def __repr__(self):
        return repr(vars(self))


class HoldingParamSet:
    """
    保压参数集合类
    """

    def __init__(self):
        """
        保压参数实例化，分为状态量、限制量

        Notes
        -----
        f_: float n_: int
        """
        # 状态量
        self.holding_stage = 1  # 分级保压的级数
        self.fPackPresSteps = []  # 分级保压的压力设置,
        self.fPackVeloSteps = []  # 新增 分级保压的速度设置,
        self.fPackTimeSteps = []  # 分级保压的时间设置,

        # 限制量
        self.fPackLimitVelocity = 0.0  # 分级保压的限定速度，（单位：mm / s）
        self.nPackMaxCount = 5

    def __repr__(self):
        return repr(vars(self))


class CoolingParamSet:
    """
        冷却参数类，包含冷却时间
        """

    def __init__(self):
        """
        冷却参数

        Notes
        -----
        f_: float, n_: int
        """
        # 冷却时间
        self.fCoolTime = 0.0  # 冷却时间（单位：s）

    def __repr__(self):
        return repr(vars(self))


class MeteringParamSet:
    """
    计量参数集合类
    """

    def __init__(self):
        """
        计量参数实例化，分为状态量、限制量

        Notes
        -----
        f_: float, n_: int
        """
        # 状态量
        # 计量部分
        self.metering_stage = 1  # 计量段数
        self.fPressure = []  # 压力
        self.fVelocity = []  # 螺杆速度
        self.fBackPressure = []  # 背压
        self.fMeteringPos = []  # 计量位置

        self.fStartDelay = 0.0  # 储料延迟

        # self.fPressure = [1.0, 1.0]  # 未知，直接移植
    
        # 限制量
        self.nMeasureMaxCount = 3

    def __repr__(self):
        return repr(vars(self))


class DecompressionParamSet:
    """
    松退参数类
    """

    def __init__(self):
        """
        松退参数实例化，分为状态量、限制量

        Notes
        -----
        f_: float, n_: int
        """
        # 状态量
        self.fMidTime = 0.0  # 中间时间

        self.sBeforeSuckMode = ""
        self.sAfterSuckMode = ""

        self.fBeforeMode = 0
        self.fBeforeBackPressure = 0.0  # 计量前减压压力
        self.fBeforeMeasureVel = 0.0  # 计量前减压速度（单位：mm/s）
        self.fBeforeMeasureDis = 0.0  # 计量前减压距离 （单位：mm）
        self.fBeforeTime = 0.0  # 计量前减压时间

        self.fAfterMode = 0
        self.fAfterBackPressure = 0.0  # 计量后减压压力
        self.fAfterMeasureVel = 0.0  # 计量后减压速度（单位：mm/s）
        self.fAfterMeasureDis = 0.0  # 计量后减压距离 （单位：mm）
        self.fAfterTime = 0.0  # 计量后减压时间

        self.fStopPos = 0.0  # 储料终止位置

        # 限制量
        self.nMeasureMaxCount = 3

    def __repr__(self):
        return repr(vars(self))


class TemperatureParamSet:
    """
    温度参数，喷嘴和料筒温度
    """

    def __init__(self):
        self.barrel_temperature_stage = 5
        self.nozzle_temp = 0
        self.fTemperature = []

    def __repr__(self):
        return repr(vars(self))


class ValveParamSet:
    """
    热流道参数，阀口开闭时间
    """

    def __init__(self):
        self.valve_num = 6
        self.fTime = []

    def __repr__(self):
        return repr(vars(self))


class MoldParamSet:
    """
    模温机参数，设定温度
    """
    def __init__(self):
        self.mold_temp = 50

    def __repr__(self):
        return repr(vars(self))


class UnitConversionParamSet:
    """
    单位转换比值参数类
    """
    def __init__(self):
        self.injection_pressure_ratio = 1  # 注射压力转换比值
        self.injection_velocity_ratio = 1  # 注射速度转换比值
        self.holding_pressure_ratio = 1  # 保压压力转换比值
        self.holding_velocity_ratio = 1  # 保压速度转换比值
        self.metering_pressure_ratio = 1  # 计量压力转换比值
        self.metering_velocity_ratio = 1  # 螺杆转速转换比值
        self.metering_backpressure_ratio = 1  # 计量背压转换比值
        self.decompression_pressure_ratio = 1  # 松退压力转换比值
        self.decompression_velocity_ratio = 1  # 松退速度转换比值

    def __repr__(self):
        return repr(vars(self))
