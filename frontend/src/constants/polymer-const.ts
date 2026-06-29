export const polymerInfoForm = {
  id: null,
  // 基本信息
  abbreviation: null,
  grade: null,
  manufacturer: null,
  data_source: null,
  category: null,
  series: null,
  data_status: null,
  internal_id: null,
  level_code: null,
  vendor_code: null,
  melt_density: null,
  solid_density: null,
  // 推荐工艺
  max_melt_temp: null,
  min_melt_temp: null,
  recommended_melt_temp: null,
  max_mold_temp: null,
  min_mold_temp: null,
  recommended_mold_temp: null,
  max_shear_line_speed: null,
  min_shear_line_speed: null,
  recommended_shear_line_speed: null,

  degradation_temp: null,
  ejection_temp: null,
  barrel_residence_time: null,
  max_shear_rate: null,
  max_shear_stress: null,

  recommend_injection_rate: null,    
  recommend_back_pressure: null,

  drying_method: null,
  drying_temp_min: null,
  drying_temp_max: null,
  drying_time_min: null,
  drying_time_max: null,
  // 流变属性
  rheology: {
    model_type: null,
    cross_wlf_n: null,
    cross_wlf_tau: null,
    cross_wlf_d1: null,
    cross_wlf_d2: null,
    cross_wlf_d3: null,
    cross_wlf_a1: null,
    cross_wlf_a2: null,
    c1: null,
    c2: null,
    transition_temp: null,
    viscosity_index: null,
    mfr_temp: null,
    mfr_load: null,
    mfr_value: null,
  },
  // PVT属性
  pvt: {
    tait_b5: null,
    tait_b6: null,
    tait_b1m: null,
    tait_b2m: null,
    tait_b3m: null,
    tait_b4m: null,
    tait_b1s: null,
    tait_b2s: null,
    tait_b3s: null,
    tait_b4s: null,
    tait_b7: null,
    tait_b8: null,
    tait_b9: null,
  },
  // 机械属性
  mechanical: {
    elastic_modulus_1: null,
    elastic_modulus_2: null,
    poisson_v12: null,
    poisson_v23: null,
    shear_modulus_g12: null,
    thermal_expansion_1: null,
    thermal_expansion_2: null,
  },
  // 收缩属性
  shrinkage: {
    ave_h_shrink: null,
    ave_v_shrink: null,
    min_h_shrink: null,
    max_h_shrink: null,
    min_v_shrink: null,
    max_v_shrink: null,
  },
}

export const initialFillerInfo = {
  // 基本信息
  name: null,
  abbreviation: null,
  category: null,
  shape: null,

  // 关键工艺相关参数
  particle_size_d50: null,
  aspect_ratio: null,
  moisture_content: null,
  surface_treatment: null,

  // 关键物理性能 
  density: null,
  thermal_stability_temp: null,
  color: null
}

export const polymerAbbreivationOptions = [
  { label: "ABS", value: "ABS", desc: "丙烯腈-丁二烯-苯乙烯" },
  { label: "CA", value: "CA", desc: "醋酸纤维素（软性塑胶）" },
  { label: "EP", value: "EP", desc: "环氧树脂（万能胶）" },
  { label: "ERP", value: "ERP", desc: "玻璃增强塑料" },
  { label: "GF", value: "GF", desc: "玻璃纤维" },
  { label: "PA", value: "PA", desc: "聚酰胺（尼龙）" },
  { label: "PC", value: "PC", desc: "聚碳酸酯" },
  { label: "PE", value: "PE", desc: "聚乙烯" },
  { label: "PES", value: "PES", desc: "聚酯" },
  { label: "PF", value: "PF", desc: "酚醛塑料（电木）" },
  { label: "PI", value: "PI", desc: "聚酰亚胺" },
  { label: "PMMA", value: "PMMA", desc: "聚甲基丙烯酸甲酯（有机玻璃）" },
  { label: "POM", value: "POM", desc: "聚甲醛" },
  { label: "PP", value: "PP", desc: "聚丙烯" },
  { label: "PS", value: "PS", desc: "聚苯乙烯" },
  { label: "PSB", value: "PSB", desc: "聚乙烯-丙烯腈共聚物" },
  { label: "PVC", value: "PVC", desc: "聚氯乙烯" },
  { label: "RP", value: "RP", desc: "增强塑料" },
  { label: "SAN", value: "SAN", desc: "苯乙烯-丙烯腈" },
  { label: "SI", value: "SI", desc: "硅树脂" },
  { label: "UF", value: "UF", desc: "脲甲醛树脂" },
  { label: "UP", value: "UP", desc: "不饱和聚酯" }
]

// 塑料常见厂商列表（按字母/拼音排序，便于查找）
export const polymerManufacturerOptions = [
  { label: "巴斯夫", value: "巴斯夫" },
  { label: "科思创", value: "科思创" },
  { label: "沙特基础工业公司（SABIC）", value: "沙特基础工业公司（SABIC）" },
  { label: "杜邦", value: "杜邦" },
  { label: "陶氏化学", value: "陶氏化学" },
  { label: "利安德巴塞尔", value: "利安德巴塞尔" },
  { label: "英力士", value: "英力士" },
  { label: "三菱化学", value: "三菱化学" },
  { label: "住友化学", value: "住友化学" },
  { label: "东丽", value: "东丽" },
  { label: "帝人", value: "帝人" },
  { label: "LG化学", value: "LG化学" },
  { label: "韩华", value: "韩华" },
  { label: "台塑", value: "台塑" },
  { label: "奇美实业", value: "奇美实业" },
  { label: "长春化工", value: "长春化工" },
  { label: "金发科技", value: "金发科技" },
  { label: "普利特", value: "普利特" },
  { label: "道恩股份", value: "道恩股份" },
  { label: "国恩股份", value: "国恩股份" },
  { label: "银禧科技", value: "银禧科技" },
  { label: "中石化", value: "中石化" },
  { label: "中石油", value: "中石油" },
  { label: "万华化学", value: "万华化学" },
  { label: "其他", value: "其他" }
]

export const polymerCategoryOptions = [
  { label: "结晶型", value: "结晶型" }, // en: semi_crystalline
  { label: "无定形", value: "无定形" } // en: amorphous
]

// 塑料数据来源选项（label 和 value 均为中文）
export const polymerDataSourceOptions = [
  { label: "Moldflow 官方数据库", value: "Moldflow 官方数据库" },
  { label: "厂商技术资料（TDS/SDS）", value: "厂商技术资料（TDS/SDS）" },
  { label: "实验室实测", value: "实验室实测" },
  { label: "第三方数据库", value: "第三方数据库" },
  { label: "历史生产经验", value: "历史生产经验" },
  { label: "用户自定义", value: "用户自定义" },
  { label: "其他", value: "其他" }
]

// 塑料干燥方法选项
export const dryingMethodOptions = [
  { label: "无需干燥", value: "无需干燥" },     // en: No drying required
  { label: "除湿干燥", value: "除湿干燥" },     // en: Desiccant drying
  { label: "热风干燥", value: "热风干燥" },     // en: Hot air drying
  { label: "真空干燥", value: "真空干燥" },     // en: Vacuum drying
  { label: "其他", value: "其他" }               // en: Other
]

export const fillerTypeOptions = [
  { value: "GF", label: "GF（玻璃纤维，Glass Fiber）" },
  { value: "CF", label: "CF（碳纤维，Carbon Fiber）" },
  { value: "MF", label: "MF（矿物纤维，Mineral Fiber）" },
  { value: "Talc", label: "滑石粉（Talc）" },
  { value: "CaCO₃", label: "碳酸钙（Calcium Carbonate）" },
  { value: "Wollastonite", label: "硅灰石（Wollastonite）" },
  { value: "Mica", label: "云母（Mica）" },
  { value: "Al(OH)₃", label: "氢氧化铝（Aluminum Hydroxide）" },
  { value: "SiO₂", label: "二氧化硅（Silica）" },
  { value: "BaSO₄", label: "硫酸钡（Barium Sulfate）" },
  { value: "WoodFlour", label: "木粉（Wood Flour）" },
  { value: "PTFE", label: "聚四氟乙烯（PTFE）" },
  { value: "AramidFiber", label: "芳纶纤维（Aramid Fiber）" },
  { value: "NanoClay", label: "纳米黏土（Nano Clay）" },
  { value: "Graphite", label: "石墨（Graphite）" }
]

export const fillerPercentageOptions = [
  { value: "10%", label: "10%" },
  { value: "15%", label: "15%" },
  { value: "20%", label: "20%" },
  { value: "30%", label: "30%" },
  { value: "40%", label: "40%" },
  { value: "50%", label: "50%" },
  { value: "60%", label: "60%" },
]

export const colorOptions = [
  { value: "黑色", label: "黑色" },
  { value: "白色", label: "白色" },
  { value: "透明", label: "透明" },
  { value: "灰色", label: "灰色" },
  { value: "蓝色", label: "蓝色" },
  { value: "红色", label: "红色" },
  { value: "黄色", label: "黄色" },
  { value: "紫色", label: "紫色" },
]

export const shapeOptions = [
  { value: "fibrous", label: "纤维状" },
  { value: "platelet", label: "片状" },
  { value: "spherical", label: "颗粒状" }
]

export const fillerCategoryOptions = [
  { value: "无机填充剂",      label: "无机填充剂" },
  { value: "增强纤维", label: "增强纤维" },
  { value: "有机填充剂",        label: "有机填充剂" },
  { value: "功能性填充剂",     label: "功能性填充剂" },
  { value: "再生/环保填充剂",       label: "再生/环保填充剂" }
]