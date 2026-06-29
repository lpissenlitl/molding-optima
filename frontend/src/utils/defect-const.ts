// 缺陷类型
export const defectTypeOptions = [
  { label: "短射", value: "短射" },
  { label: "飞边", value: "飞边" },
  { label: "缩水", value: "缩水" },
  { label: "气纹", value: "气纹" },
  { label: "熔接痕", value: "熔接痕" },
  { label: "料花", value: "料花" },
  { label: "困气", value: "困气" },
  { label: "色差", value: "色差" },
  { label: "烧焦", value: "烧焦" },
  { label: "水波纹", value: "水波纹" },
  { label: "脱模不良", value: "脱模不良" },
  { label: "顶白", value: "顶白" },
  { label: "变形", value: "变形" },
  { label: "尺寸偏大", value: "尺寸偏大" },
  { label: "尺寸偏小", value: "尺寸偏小" }
]

// 缺陷排除分析对象
export const defectAnalysisTarget = [
  { label: "成型工艺", value: "成型工艺" },
  { label: "模具", value: "模具" },
  { label: "注塑机", value: "注塑机" },
  { label: "材料", value: "材料" },
  { label: "制品", value: "制品" }
]

// 缺陷位置
export const defectPositionOptions = [
  { lable: "缺陷位置不指定", value: "缺陷位置不指定" },
  { lable: "缺陷位置在1段", value: "缺陷位置在1段" },
  { lable: "缺陷位置在2段", value: "缺陷位置在2段" },
  { lable: "缺陷位置在3段", value: "缺陷位置在3段" },
  { lable: "缺陷位置在4段", value: "缺陷位置在4段" },
]
// 缺陷程度
export const defectDegreeOptions = [
  { lable: "轻微", value: "轻微" },
  { lable: "中等", value: "中等" },
  { lable: "严重", value: "严重" },
  { lable: "非常严重", value: "非常严重" },
]

// 飞边解决方案
export const flashSolutionOptions = [
  { 
    type: "成型工艺", 
    reason: "保压压力过大", 
    resolve: "降低保压压力" 
  },
  {
    type: "成型工艺",
    reason: "过度填充",
    resolve: "增加切换位置，减少在注射阶段塑料的填充量",
  },
  {
    type: "成型工艺",
    reason: "锁模力不足",
    resolve: "调整模具厚度以确保锁紧状态",
  },
  {
    type: "成型工艺",
    reason: "熔体温度高",
    resolve: "需要更高的压力来填充型腔",
  },
  { 
    type: "成型工艺", 
    reason: "保压切换不当", 
    resolve: "调整注射量" 
  },
  { 
    type: "模具", 
    reason: "分型面损坏", 
    resolve: "激光焊接" 
  },
  { 
    type: "模具", 
    reason: "排气深度大", 
    resolve: "调整模具排气深度" 
  },
  { 
    type: "模具", 
    reason: "塑料残留", 
    resolve: "清洁模具，合理设定工艺" 
  },
  {
    type: "模具",
    reason: "模具支撑",
    resolve: "模具必须进行例常支撑柱检查，以防出现压塌现象",
  },
  { 
    type: "模具", 
    reason: "腐蚀", 
    resolve: "加强模具排气" 
  },
  {
    type: "模具",
    reason: "滑块变形",
    resolve: "将作用在移动型芯上的型腔压力与作用在油缸端面的压力进行比较，液压移动型芯也可以由带锁定角的楔紧块协助锁定。型芯在模具关闭前由液压推到位，然后由楔紧块完成预紧并锁定",
  },
  {
    type: "模具",
    reason: "段差",
    resolve: "段差是无法通过调整注塑机或工艺参数来解决，靠近分型面附近的抛光须格外小心",
  },
  {
    type: "模具",
    reason: "型腔不平衡",
    resolve: "检查模具设计，平衡型腔",
  },
  {
    type: "注塑机",
    reason: "锁模力不足",
    resolve: "注塑机是否达到了预期的锁模力？更换模具在注塑机中的位置。如果模具旋转180°，飞边并没有发生变化，那么大概率缺陷和注塑机有关",
  },
  {
    type: "注塑机",
    reason: "锁模单元平行度",
    resolve: "定期检查注塑机模板，保持各配合表面清洁",
  },
  {
    type: "注塑机",
    reason: "抽芯压力",
    resolve: "正确设置液压抽芯管路中的液压压力",
  },
  {
    type: "注塑机",
    reason: "模具尺寸",
    resolve: "检查注塑机最小模具尺寸，尺寸过小会产生飞边，如果模具非要在超大注塑机上生产，可使用外延式支撑柱避免模具损坏",
  },
  {
    type: "注塑机",
    reason: "合模曲轴磨损",
    resolve: "曲臂系统长时间运行后应该对零部件的磨损状况进行评估。如果锁模单元动作缓慢或发出异样噪音，说明已发生了过度磨损。应更换锁模单元",
  },
  { 
    type: "材料", 
    reason: "黏度降低", 
    resolve: "更换另一批次的塑料" 
  },
  { 
    type: "材料", 
    reason: "含水率", 
    resolve: "注塑之前，检查一下含水量" 
  },
  {
    type: "材料",
    reason: "回料",
    resolve: "保持回料清洁，必要时进行干燥，回料应尽量做到尺寸一致，避免灰尘污染，而且必须尽快投入使用",
  },
]

// 短射解决方案
export const shortShotSolutionOptions = [
  {
    type: "成型工艺",
    reason: "注射填充重量不足",
    resolve: "确定塑料不会发生泄漏后，调整注射量或保压切换位置",
  },
  {
    type: "成型工艺",
    reason: "压力受限",
    resolve: "设定的注射压力必须高于模具填充所需峰值压力（至少高出 10%）",
  },
  {
    type: "成型工艺",
    reason: "注射速度过低",
    resolve: "检查注塑机到达保压切换点所需的填充时间。如果填充时间太长，表示注射阶段的实际速度偏慢。如果实际填充时间比设定填充时间长，应提高填充速度设定值，使实际填充时间与设定填充时间一致",
  },
  {
    type: "成型工艺",
    reason: "保压压力过低",
    resolve: "调整保压压力，检查保压时间，检查保压阶段切换",
  },
  {
    type: "成型工艺",
    reason: "保压切换不当",
    resolve: "调整保压阶段切换参数，优化保压阶段控制",
  },
  {
    type: "成型工艺",
    reason: "无料垫",
    resolve: "检查螺杆前端是否存有料垫。如出现料垫为零的现象，说明注射量太小，或者有漏料发生。如果注塑机没有料垫，也不存在漏料，那么应核验“仅填充”产品重量，然后调整注射量和切换位置",
  },
  {
    type: "成型工艺",
    reason: "无背压",
    resolve: "使用减压（即松退）而不是降低背压来将螺杆拉回到原来的注射量位置",
  },
  { type: "成型工艺", reason: "熔体温度过低", resolve: "提高熔体温度" },

  {
    type: "模具",
    reason: "排气不良",
    resolve: "保证型腔表面清洁，排气道通畅",
  },
  {
    type: "模具",
    reason: "型腔不平衡",
    resolve: "多型腔模具的填充不平衡度应小于 3%",
  },
  { type: "模具", reason: "浇口或热嘴堵塞", resolve: "清理热流道的热嘴" },
  { type: "模具", reason: "塑料卡顿", resolve: "清理模垢并增加排气" },
  {
    type: "模具",
    reason: "热流道温度过低",
    resolve: "确认所有热流道加热区都设置正确，并确保所有加热区的电流数及热电偶读数正确",
  },
  {
    type: "模具",
    reason: "热流道分流板漏料",
    resolve: "清除分流板中的塑料。塑料被射入型腔前，热流道必须充分均匀加热，并达到一定温度，确保分流板中的所有塑料都已融化",
  },

  {
    type: "注塑机",
    reason: "止逆环损坏",
    resolve: "延长保压时间，观察到螺杆是停止前移，还是继续前移直到触底",
  },
  {
    type: "注塑机",
    reason: "喷嘴不匹配",
    resolve: "确认喷嘴长度、孔径和类型",
  },
  {
    type: "注塑机",
    reason: "料筒磨损",
    resolve: "选用料筒时，应先确定塑料型号，随后选用硬度匹配的料筒",
  },
  {
    type: "注塑机",
    reason: "注塑机性能不良",
    resolve: "注塑机必须拥有实现所有参数设定值的能力",
  },
  {
    type: "注塑机",
    reason: "喷嘴漏料",
    resolve: "容易泄漏区域可能在喷嘴头与喷嘴之间、喷嘴与接头之间、接头与端盖之间以及端盖与料筒之间。安装其中任何一个组件时，都应确保安装表面清洁干净",
  },

  { type: "材料", reason: "黏度变化", resolve: "更换另一批材料" },
  {
    type: "材料",
    reason: "含水率过低",
    resolve: "故加工尼龙时应确保含水率合理并保持一致。",
  },
  {
    type: "材料",
    reason: "进料不稳定",
    resolve: "确保输送软管持续畅通。调整注塑机的加料时间，使供料系统中的所有注塑机有足够时间持续加料。经常检查料斗，确保加料时间跟上注塑机的熔料节奏",
  },
  {
    type: "材料",
    reason: "未完全塑化",
    resolve: "优化回料比例，加强塑料干燥处理",
  },
  {
    type: "材料",
    reason: "污染",
    resolve: "原料筛选，加强原料存储管理，定期清洁设备",
  },
]