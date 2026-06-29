export const moldflowForm = {
  // 模具参数
  mold_id: null,
  mold_no: null,
  mold_type: null,
  // 基本信息
  moldflow_no: null,
  analysis_software: null,
  analysis_version: null,
  analysis_engineer: null,
  analysis_date: null,
  analysis_result: null,
  // 上传文件信息
  txt_uuid: null,
  ppt_uuid: null,
  // 解析后的信息
  analysis_log: {
    // 模型细节
    total_volume: null,  // 总体积
    tetrahedral_elements_volume: null,  // 四面体单元的体积
    sprue_runner_gate_elements_volume: null,  // 主流道/流道/浇口单元的体积
    hot_sprue_runner_gate_elements_volume: null,  // 热主流道/流道/浇口单元的体积
    initial_filled_volume: null,  // 最初充填的体积
    filled_volume: null,  // 要充填的体积
    filled_part_volume: null,  // 要充填的零件体积
    filled_sprue_runner_gate_volume: null,  // 要充填的主流道/流道/浇口体积
    total_projected_area: null,  // 总投影面积  
    
    // 型腔温度结果摘要
    surface_temperature_maximum: null,  // 零件表面温度 - 最大值
    surface_temperature_minimum: null,  // 零件表面温度 - 最小值
    surface_temperature_average: null,  // 零件表面温度 - 平均值
    cavity_surface_temperature_maximum: null,  // 型腔表面温度 - 最大值
    cavity_surface_temperature_minimum: null,  // 型腔表面温度 - 最小值
    cavity_surface_temperature_average: null,  // 型腔表面温度 - 平均值
    average_mold_external_temperature: null,  // 平均模具外部温度
    heat_removal_through_external_boundaries: null,  // 通过外边界的热量排除
    cycle_time: null,  // 周期时间
    maximum_temperature: null,  // 最高温度
    minimum_temperature: null,  // 最低温度

    // 材料数据
    polymer_manufacturer: null,  // 制造商
    polymer_trademark: null,  // 牌号
    polymer_abbreviation: null,  // 系列
    specific_heat: null,  // 比热(Cp)
    thermal_conductivity: null,  // 热传导率
    transition_temperature: null,  // 转换温度
    melt_density: null,  // 熔体密度
    solid_density: null,  // 固体密度
    recommend_melt_temperature: null,  // 推荐熔体温度
    ejection_temperature: null,  // 顶出温度
    max_shear_stress: null,  // 最大剪切应力
    max_shear_rate: null,  // 最大剪切速率
    
    // 工艺设置--注塑机参数
    machine_manufacturer: null,  // 注塑机制造商
    machine_trademark: null,  // 注塑机牌号
    max_injection_pressure: null,  // 最大注射压力
    max_clamping_force: null,  // 最大注塑机锁模力
    max_injection_rate: null,  // 最大注射机注射率
    response_time: null,  // 注塑机液压响应时间
    enhancement_ratio: null,  // 增强比
    hydraulic_pressure: null,  // 液压压力
    
    // 工艺设置--温度控制
    melt_temperature: null,  // 熔体温度
    mold_temperature: null,  // 模具温度
    atmospheric_temperature: null,  // 大气温度
    // 工艺设置--充填控制
    fill_control_type: null,  // 充填控制类型
    stroke_volume_determination: null,  // 射出体积确定
    injection_time: null,  // 充填时间
    flow_rate: null,  // 流动速率
    ram_speed_profile_control_method: null,  // 螺杆速度曲线控制方式
    ram_speed_profile: [],  // 螺杆速度曲线
    filling_profile_scale_type: null,  // 充填曲线比例类型
    nominal_injection_time: null,  // 名义注射时间
    nominal_flow_rate: null,  // 名义流动速率
    starting_ram_position: null,  // 启动螺杆位置
    cushion_size: null,  // 垫料尺寸
    // 工艺设置--速度/压力切换控制
    vp_switch_mode: null,  // 速度/压力切换控制类型
    fill_volume_percentage: null,  // 零件体积百分比
    specified_ram_position: null,  // 指定的螺杆位置
    specified_injection_pressure: null,  // 指定的注射压力
    specified_hydraulic_pressure: null,  // 指定的液压压力
    specified_clamp_force: null,  // 指定的锁模力
    specified_pressure_control_point: null,  // 指定的压力控制点
    specified_control_point_pressure: null,  // 指定的控制点压力
    specified_injection_time: null,  // 注射时间
    // 工艺设置--保压控制
    holding_control_type: null,  // 保压控制类型
    holding_time: null,  // 保压时间
    pressure_profile: [],  // 压力曲线
    // 工艺设置--冷却时间
    cooling_time_determination: null,  // 冷却时间确定
    cooling_time: null,  // 冷却时间
    injection_holding_cooling_time: null,  // 注射 + 保压 + 冷却时间
    
    // 充填阶段结束的结果摘要
    eof_current_time_from_cycle_start: null,  // 从循环开始的当前时间
    eof_total_mass: null,  // 总体积
    eof_frozen_volume: null,  // 冻结体积
    eof_injection_pressure: null,  // 注射压力
    maximum_clamping_force_during_filling: null,  // 最大锁模力 - 在充填期间  
    vp_switch_time: null,  // 速度/压力切换的时间      
    vp_switch_pressure: null,  // 速度/压力切换时的注射压力
    vp_switch_volume: null,  // 速度/压力切换时充填的体积
    
    // 保压阶段结束的结果摘要
    eop_current_time_from_cycle_start: null,  // 从循环开始的当前时间
    eop_total_mass: null,  // 总体积
    eop_frozen_volume: null,  // 冻结体积
    eop_injection_pressure: null,  // 注射压力
    maximum_volumetric_shrinkage: null,  // 体积收缩率 - 最大值
    minimum_volumetric_shrinkage: null,  // 体积收缩率 - 最小值  
    average_volumetric_shrinkage: null,  // 体积收缩率 - 平均值
    standard_deviation_of_volumetric_shrinkage: null,  // 体积收缩率 - 标准差
  },
  // 解析后的图片
  picture_infos: []
}

//分析序列
export const moldFlowAnalyticalSequenceOptions = [
  { label: "填充", value: "填充" },
  { label: "填充+保压", value: "填充+保压" },
  { label: "冷却", value: "冷却" },
  { label: "填充+保压+翘曲", value: "填充+保压+翘曲" },
  { label: "冷却+填充+保压+翘曲", value: "冷却+填充+保压+翘曲" },
  { label: "冷却(FEM)", value: "冷却(FEM)" },
  { label: "冷却(FEM)+填充+保压+翘曲", value: "冷却(FEM)+填充+保压+翘曲" },
]

//充填控制
export const moldFlowFillControlOptions = [
  { label: "自动", value: "1" },
  { label: "注射时间", value: "2" },
  { label: "流动速率", value: "3" },
  { label: "相对螺杆速度曲线", value: "5" },
  { label: "绝对螺杆速度曲线", value: "6" },
  { label: "原有螺杆速度曲线(旧版本)", value: "4" },
]

//速度/压力切换
export const moldFlowSpeedSwitchingOptions = [
  { label: "自动", value: "0" },
  { label: "由%充填体积", value: "1" },
  { label: "由螺杆位置", value: "8" },
  { label: "由注射压力", value: "2" },
  { label: "由液压压力", value: "3" },
  { label: "由锁模力", value: "4" },
  { label: "由压力控制点", value: "5" },
  { label: "由注射时间", value: "6" },
  { label: "由任一条件满足时", value: "7" },
]

//保压控制
export const moldFlowPressureHoldingControlOptions = [
  { label: "自动", value: "5" },
  { label: "由%填充压力与时间", value: "4" },
  { label: "保压压力与时间", value: "2" },
  { label: "液压压力与时间", value: "1" },
  { label: "%最大注塑机压力与时间", value: "3" },
]

//相对螺杆速度曲线
export const moldFlowRelativeOptions = [
  { label: "%流动速率与%射出体积", value: "1" },
  { label: "%螺杆速度与%行程", value: "2" },
]

//绝对螺杆速度曲线
export const moldFlowAbsoluteOptions = [
  { label: "螺杆速度与螺杆位置", value: "3" },
  { label: "流动速率与螺杆位置", value: "5" },
  { label: "%最大螺杆速度与螺杆位置", value: "4" },
  { label: "螺杆速度与时间", value: "7" },
  { label: "流动速率与时间", value: "9" },
  { label: "%最大螺杆速度与时间", value: "8" },
]

//原有螺杆速度曲线
export const moldFlowOriginalOptions = [
  { label: "%流动速率与%射出体积", value: "%流动速率与%射出体积" },
  { label: "%螺杆速度与%行程", value: "%螺杆速度与%行程" },
  { label: "螺杆速度与螺杆位置", value: "螺杆速度与螺杆位置" },
  { label: "%最大螺杆速度与螺杆位置", value: "%最大螺杆速度与螺杆位置" },
  { label: "流动速率与螺杆位置", value: "流动速率与螺杆位置" },
  { label: "%最大流动速率与螺杆位置", value: "%最大流动速率与螺杆位置" },
  { label: "螺杆速度与时间", value: "螺杆速度与时间" },
  { label: "%最大螺杆速度与时间", value: "%最大螺杆速度与时间" },
  { label: "流动速率与时间", value: "流动速率与时间" },
  { label: "%最大流动速率与时间", value: "%最大流动速率与时间" },
]

export const productMap = new Map([[0,"1ST"],[1,"2ND"],[2,"3RD"],[3,"4TH"],[4,"5TH"],[5,"6TH"],[6,"7TH"]])