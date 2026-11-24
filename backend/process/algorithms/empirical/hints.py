"""经验推理数据表。

来源：原 process/services/optimization_advice.py 的 DEFECT_OPTIMIZATION_HINTS 字典
      （工程师多年经验沉淀的工艺优化提示）

字段说明：
- 字典的 key 是**英文缺陷码**（SHORTSHOT / SHRINKAGE / ...）
  - 与 RuleMethod.defect_code、RuleKeyword.keyword_name 对齐
  - 与 fuzzy 规则库的前件词完全一致（同是 17 个缺陷）
  - 历史实现用中文缺陷名（短射 / 缩水 / ...），而反馈传进来的是
    `feedback.defects[].keyword_name`（英文码），两者永远匹配不上，
    经验引擎恒定返回空推荐
- 字典的 value 包含两个 list：
  - increase: 推荐调高的参数代码列表
  - decrease: 推荐调低的参数代码列表

命名空间说明：
- 参数代码用**业务字段名**（``inj_pres_1`` / ``brl_temp_1``）—— 与 ORM 工艺
  参数表、前端展示、工艺单是同一套名字 ⇒ 工程师写经验时不必心算段号。
- 【注意】**段号是 1-based**（``inj_pres_1`` = 注射压力第 1 段）；模糊规则库那边
  是 0-based（``IP0`` = 注射压力第 1 段）⇒ 两套编号差一位，对照见下表。
- 【注意】**算法名不进来**：算法字段名（``IV0`` / ``IP0`` / ``MEL``）是模糊规则库
  的内部命名，只在 ``algorithms/fuzzy/`` 内成立 ⇒ 经验库不认算法名，
  本引擎也不 import fuzzy 的命名契约。

业务字段名 ↔ 规则库参数码对照（写经验时对照用）
==================================================
==========================================  ======================
业务字段名                                    规则库参数码
==========================================  ======================
``inj_pres_1``                                ``IP0``
``inj_spd_1``                                 ``IV0``
``inj_t``                                     ``IT``
``hold_pres_1``                               ``PP0``
``hold_spd_1``                                ``PV0``
``hold_t_1``                                  ``PT0``
``cool_t``                                    ``CT``
``brl_temp_1`` / ``brl_temp_2`` / ``brl_temp_3``  ``BT1`` / ``BT2`` / ``BT3``
``vps_pos``                                   ``VPTL``
==========================================  ======================

数据维护：
- 由工艺工程师根据经验持续扩充
- 新增缺陷时直接在这里加 key 即可（key 用英文缺陷码）
"""


# 缺陷码 -> 推荐调高 / 调低的参数代码（业务字段名）
EMPIRICAL_HINTS: dict = {
    # 短射：整体充填不足 → 提高注射压力 / 速度 / 延长注射时间
    "SHORTSHOT": {"increase": ["inj_pres_1", "inj_spd_1", "inj_t"], "decrease": []},
    # 缩水：体积收缩 → 提高保压压力 / 延长保压时间 / 延长冷却时间
    "SHRINKAGE": {"increase": ["hold_pres_1", "hold_t_1", "cool_t"], "decrease": []},
    # 飞边：压力过高溢料 → 降低注射压力 / 速度
    "FLASH": {"increase": [], "decrease": ["inj_pres_1", "inj_spd_1"]},
    # 熔接痕：料流未熔合 → 提高料筒温度 / 注射速度
    "WELDLINE": {"increase": ["brl_temp_1", "brl_temp_2", "brl_temp_3", "inj_spd_1"], "decrease": []},
    # 困气：困气排气不良 → 提高 VP 切换位置 / 降低注射速度
    "AIRTRAP": {"increase": ["vps_pos"], "decrease": ["inj_spd_1"]},
    # 气纹：气流纹 → 提高冷却时间 / 料筒温度，降低注射速度
    "GASVEINS": {"increase": ["cool_t", "brl_temp_1"], "decrease": ["inj_spd_1"]},
    # 烧焦：过热焦烧 → 降低注射速度 / 料筒温度
    "BURN": {"increase": [], "decrease": ["inj_spd_1", "brl_temp_1", "brl_temp_2"]},
    # 料花：料流花纹 → 提高料筒温度，降低注射速度
    "MATERIALFLOWER": {"increase": ["brl_temp_1", "brl_temp_2"], "decrease": ["inj_spd_1"]},
    # 色差：色差 → 提高料筒温度
    "SHADING": {"increase": ["brl_temp_1", "brl_temp_2", "brl_temp_3"], "decrease": []},
    # 水波纹：熔接线波纹 → 提高料筒温度 / 冷却时间
    "WATERRIPPLE": {"increase": ["brl_temp_1", "cool_t"], "decrease": []},
    # 脱模不良：脱模困难 → 延长冷却时间，降低保压压力
    "HARDDEMOLDING": {"increase": ["cool_t"], "decrease": ["hold_pres_1"]},
    # 顶白：顶白 → 降低保压压力 / 保压速度
    "TOPWHITE": {"increase": [], "decrease": ["hold_pres_1", "hold_spd_1"]},
    # 变形：翘曲变形 → 延长冷却时间，降低保压压力
    "WARPING": {"increase": ["cool_t"], "decrease": ["hold_pres_1"]},
    # 尺寸偏大：尺寸过大 → 降低保压压力 / 缩短保压时间
    "OVERSIZE": {"increase": [], "decrease": ["hold_pres_1", "hold_t_1"]},
    # 尺寸偏小：尺寸过小 → 提高保压压力 / 延长保压时间
    "UNDERSIZE": {"increase": ["hold_pres_1", "hold_t_1"], "decrease": []},
    # 浇口印：浇口痕明显 → 延长冷却时间，降低保压压力
    "GATEMARK": {"increase": ["cool_t"], "decrease": ["hold_pres_1"]},
    # 阴阳面：阴阳面 → 提高料筒温度 / 注射速度
    "ABERRATION": {"increase": ["brl_temp_1", "brl_temp_2", "inj_spd_1"], "decrease": []},
}
