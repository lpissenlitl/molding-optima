"""
经验推理数据表

来源：原 process/services/optimization_advice.py 的 DEFECT_OPTIMIZATION_HINTS 字典
      （工程师多年经验沉淀的工艺优化提示）

字段说明：
- 字典的 key 是**英文缺陷码**（SHORTSHOT / SHRINKAGE / ...）
  - 与 RuleMethod.defect_code、RuleKeyword.keyword_name 对齐
  - 与 fuzzy 规则库的前件词完全一致（同是 17 个缺陷）
  - 历史实现用中文缺陷名（短射 / 缩水 / ...），而反馈传进来的是
    `feedback.defect[].keyword_name`（英文码），两者永远匹配不上，
    经验引擎恒定返回空推荐
- 字典的 value 包含两个 list：
  - increase: 推荐调高的参数代码列表
  - decrease: 推荐调低的参数代码列表

命名空间说明：
- 参数代码是**算法命名空间**（与 RuleKeyword.keyword_name 同名同段号），
  不是业务字段名。业务侧是 `inj_pres_1`（1-based），算法侧是 `IP0`（0-based）。
- 原因：编排层（parameter_optimize）把业务参数翻译成算法命名后再喂给算法，
  算法返回值也在算法命名空间；经验引擎若返回业务名，
  `process_parameter.get(param_code)` 永远取不到当前值，current_value 恒为 0。

数据维护：
- 由工艺工程师根据经验持续扩充
- 新增缺陷时直接在这里加 key 即可（key 用英文缺陷码）
- 段号基准：规则库以 0-based 为主（IV0 / PP0 / ...），这里与之保持一致；
  料筒温度例外 —— BT1..BT9 是 1-based（BT1=料筒温度一段），
  与业务 brl_temp_1..9 同构，命名契约里偏移为 0。
"""


# 缺陷码 -> 推荐调高 / 调低的参数代码（算法命名空间）
EMPIRICAL_HINTS: dict = {
    # 短射：整体充填不足 → 提高注射压力 / 速度 / 延长注射时间
    "SHORTSHOT": {"increase": ["IP0", "IV0", "IT"], "decrease": []},
    # 缩水：体积收缩 → 提高保压压力 / 延长保压时间 / 延长冷却时间
    "SHRINKAGE": {"increase": ["PP0", "PT0", "CT"], "decrease": []},
    # 飞边：压力过高溢料 → 降低注射压力 / 速度
    "FLASH": {"increase": [], "decrease": ["IP0", "IV0"]},
    # 熔接痕：料流未熔合 → 提高料筒温度 / 注射速度
    "WELDLINE": {"increase": ["BT1", "BT2", "BT3", "IV0"], "decrease": []},
    # 困气：困气排气不良 → 提高 VP 切换位置 / 降低注射速度
    "AIRTRAP": {"increase": ["VPTL"], "decrease": ["IV0"]},
    # 气纹：气流纹 → 提高冷却时间 / 料筒温度，降低注射速度
    "GASVEINS": {"increase": ["CT", "BT1"], "decrease": ["IV0"]},
    # 烧焦：过热焦烧 → 降低注射速度 / 料筒温度
    "BURN": {"increase": [], "decrease": ["IV0", "BT1", "BT2"]},
    # 料花：料流花纹 → 提高料筒温度，降低注射速度
    "MATERIALFLOWER": {"increase": ["BT1", "BT2"], "decrease": ["IV0"]},
    # 色差：色差 → 提高料筒温度
    "SHADING": {"increase": ["BT1", "BT2", "BT3"], "decrease": []},
    # 水波纹：熔接线波纹 → 提高料筒温度 / 冷却时间
    "WATERRIPPLE": {"increase": ["BT1", "CT"], "decrease": []},
    # 脱模不良：脱模困难 → 延长冷却时间，降低保压压力
    "HARDDEMOLDING": {"increase": ["CT"], "decrease": ["PP0"]},
    # 顶白：顶白 → 降低保压压力 / 保压速度
    "TOPWHITE": {"increase": [], "decrease": ["PP0", "PV0"]},
    # 变形：翘曲变形 → 延长冷却时间，降低保压压力
    "WARPING": {"increase": ["CT"], "decrease": ["PP0"]},
    # 尺寸偏大：尺寸过大 → 降低保压压力 / 缩短保压时间
    "OVERSIZE": {"increase": [], "decrease": ["PP0", "PT0"]},
    # 尺寸偏小：尺寸过小 → 提高保压压力 / 延长保压时间
    "UNDERSIZE": {"increase": ["PP0", "PT0"], "decrease": []},
    # 浇口印：浇口痕明显 → 延长冷却时间，降低保压压力
    "GATEMARK": {"increase": ["CT"], "decrease": ["PP0"]},
    # 阴阳面：阴阳面 → 提高料筒温度 / 注射速度
    "ABERRATION": {"increase": ["BT1", "BT2", "IV0"], "decrease": []},
}
