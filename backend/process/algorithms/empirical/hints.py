"""
经验推理数据表

来源：原 process/services/optimization_advice.py 的 DEFECT_OPTIMIZATION_HINTS 字典
      （工程师多年经验沉淀的工艺优化提示）

字段说明：
- 字典的 key 是中文缺陷名（与 FuzzyEngine 输入对齐）
- 字典的 value 包含两个 list：
  - increase: 推荐调高的参数代码列表
  - decrease: 推荐调低的参数代码列表

数据维护：
- 由工艺工程师根据经验持续扩充
- 新增缺陷时直接在这里加 key 即可
- 命名规范：与 RuleMethod.defect_label / RuleKeyword.keyword_name 对齐
"""


# 缺陷 -> 推荐调高 / 调低的参数代码
EMPIRICAL_HINTS: dict = {
    "短射": {"increase": ["inj_pres_1", "inj_spd_1", "inj_t"], "decrease": []},
    "缩水": {"increase": ["hold_pres_1", "hold_t_1", "cool_t"], "decrease": []},
    "飞边": {"increase": [], "decrease": ["inj_pres_1", "inj_spd_1"]},
    "熔接痕": {"increase": ["brl_temp_1", "brl_temp_2", "brl_temp_3", "inj_spd_1"], "decrease": []},
    "困气": {"increase": ["vps_pos"], "decrease": ["inj_spd_1"]},
    "气纹": {"increase": ["cool_t", "brl_temp_1"], "decrease": ["inj_spd_1"]},
    "烧焦": {"increase": [], "decrease": ["inj_spd_1", "brl_temp_1", "brl_temp_2"]},
    "料花": {"increase": ["brl_temp_1", "brl_temp_2"], "decrease": ["inj_spd_1"]},
    "色差": {"increase": ["brl_temp_1", "brl_temp_2", "brl_temp_3"], "decrease": []},
    "水波纹": {"increase": ["brl_temp_1", "cool_t"], "decrease": []},
    "脱模不良": {"increase": ["cool_t"], "decrease": ["hold_pres_1"]},
    "顶白": {"increase": [], "decrease": ["hold_pres_1", "hold_spd_1"]},
    "变形": {"increase": ["cool_t"], "decrease": ["hold_pres_1"]},
    "尺寸偏大": {"increase": [], "decrease": ["hold_pres_1", "hold_t_1"]},
    "尺寸偏小": {"increase": ["hold_pres_1", "hold_t_1"], "decrease": []},
    "浇口印": {"increase": ["cool_t"], "decrease": ["hold_pres_1"]},
    "阴阳面": {"increase": ["brl_temp_1", "brl_temp_2", "inj_spd_1"], "decrease": []},
}
