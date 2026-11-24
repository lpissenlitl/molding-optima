r"""经验推理 `current_value` 的「参数不存在 ≠ 当前值 0」语义测试

背景：
- 经验推理按缺陷查表推荐参数，但**工艺单上未必每个参数都有值**
- 旧实现参数缺失时报 ``0.0`` —— 把「压根没这个参数」伪装成「当前值是 0」，
  下游会把它当真实数值展示（看起来像「该参数被调到 0」），还会参与数值比较
- 现在参数缺失一律留 ``None`` ⇒ 「值是 0」与「没这个参数」必须能区分开

覆盖：
1. 参数存在 ⇒ ``current_value`` 是该参数的真实数值
2. 参数**不存在** ⇒ ``current_value is None``（**不是 0.0**）
3. 真实值恰好是 ``0.0`` ⇒ ``current_value == 0.0``（**不是 None**）
4. increase / decrease 两个方向同一语义
5. 参数缺失**不丢方向**（经验推理的价值就是方向）
6. 参数名用**业务字段名**（经验库命名空间，不泄漏算法名）
7. 下游归一化 + 文案生成遇 ``None`` 不退化（仍只给方向不给数值）

【注意】A 组是纯算法层用例；B 组测 service 层归一化，需要 ``django.setup()``
（离线，不连 DB）。

运行：
  cd backend
  ..\.venv\Scripts\python.exe -m pytest tests/test_empirical_current_value.py -q
"""
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")
django.setup()

from process.algorithms.empirical.empirical_algorithm import (  # noqa: E402
    EmpiricalReasoning,
)
from process.algorithms.empirical.hints import EMPIRICAL_HINTS  # noqa: E402
from process.services.parameter_optimize import (  # noqa: E402
    _normalize_recommendations,
)
from process.services.shared.param_naming import param_label  # noqa: E402

#: 注入用经验表（可控）：一段注射压力 / 注射时间 / 冷却时间
HINTS = {
    'SHORTSHOT': {'increase': ['inj_pres_1', 'inj_t'], 'decrease': []},
    'FLASH': {'increase': [], 'decrease': ['cool_t']},
}

#: 经验库若混入的**算法名**（模糊规则库内部命名）—— 不该出现在经验推理输出里
ALGO_CODES = {
    'IP0', 'IV0', 'IT', 'PP0', 'PV0', 'PT0', 'CT', 'BT1', 'BT2', 'BT3', 'VPTL',
}


def _ctx(params, defect='SHORTSHOT'):
    """构造经验推理 context（缺陷 + 工艺参数）。"""
    return {
        'feedback': {'defects': [{'keyword_name': defect, 'level': 'high'}]},
        'process_parameter': params,
    }


def _by_name(recs):
    """推荐列表 → {参数名: 推荐}。"""
    return {r.param_name: r for r in recs}


# =============================================================================
# A 组：经验推理自身的 current_value 语义
# =============================================================================


def test_existing_param_keeps_real_value():
    """参数存在 ⇒ current_value 是真实数值。"""
    recs = EmpiricalReasoning(hints=HINTS).recommend(_ctx({'inj_pres_1': 35.0}))
    by_name = _by_name(recs)
    assert by_name['inj_pres_1'].current_value == 35.0


def test_missing_param_is_none_not_zero():
    """参数不存在 ⇒ current_value is None（**不是 0.0**）。"""
    recs = EmpiricalReasoning(hints=HINTS).recommend(_ctx({'inj_pres_1': 35.0}))
    by_name = _by_name(recs)
    assert by_name['inj_t'].current_value is None, \
        '参数不存在时必须留空，不能伪装成 0.0'


def test_real_zero_is_kept_as_zero():
    """真实值就是 0.0 ⇒ 保持 0.0（**不是 None**）—— 两者必须能区分。"""
    recs = EmpiricalReasoning(hints=HINTS).recommend(_ctx({'inj_t': 0.0}))
    by_name = _by_name(recs)
    assert by_name['inj_t'].current_value == 0.0
    assert by_name['inj_t'].current_value is not None


def test_missing_param_in_decrease_direction():
    """decrease 方向同样留空（两个方向同一语义）。"""
    recs = EmpiricalReasoning(hints=HINTS).recommend(
        _ctx({}, defect='FLASH'))
    by_name = _by_name(recs)
    assert by_name['cool_t'].current_value is None


def test_direction_survives_missing_current_value():
    """参数缺失**不丢方向** —— 经验推理的价值就是方向。"""
    recs = EmpiricalReasoning(hints=HINTS).recommend(_ctx({}))
    by_name = _by_name(recs)
    assert by_name['inj_pres_1'].direction == 'increase'
    assert by_name['inj_t'].direction == 'increase'


def test_param_names_are_business_names():
    """参数名是**业务字段名** —— 算法名不进经验库。"""
    recs = EmpiricalReasoning().recommend(_ctx({'inj_pres_1': 35.0}))
    assert recs, '经验库应给出推荐'
    for r in recs:
        assert r.param_name not in ALGO_CODES, r.param_name
        assert '_' in r.param_name, r.param_name


def test_to_dict_passes_none_through():
    """to_dict() 原样透传 None（下游 API 契约允许 null）。"""
    recs = EmpiricalReasoning(hints=HINTS).recommend(_ctx({'inj_pres_1': 35.0}))
    by_name = {r.to_dict()['param']: r.to_dict() for r in recs}
    assert by_name['inj_t']['current_value'] is None
    assert by_name['inj_pres_1']['current_value'] == 35.0


def test_all_hints_leave_none_when_no_params():
    """全经验库兜底：空参数表 ⇒ 每条推荐的 current_value 都是 None。"""
    engine = EmpiricalReasoning()
    for defect in sorted(EMPIRICAL_HINTS):
        recs = engine.recommend(_ctx({}, defect=defect))
        assert recs, defect
        for r in recs:
            assert r.current_value is None, '%s / %s' % (defect, r.param_name)


# =============================================================================
# B 组：下游（service 层）遇 None 不退化
# =============================================================================


def test_normalize_keeps_none_and_description_gives_direction_only():
    """归一化 + 文案：current_value 缺失时不崩，且仍只说方向不给数值。"""
    recs = EmpiricalReasoning(hints=HINTS).recommend(_ctx({'inj_pres_1': 35.0}))
    raw = [r.to_dict() for r in recs]
    normalized = _normalize_recommendations(raw)
    by_name = {rec['param']: rec for rec in normalized}

    assert by_name['inj_t']['current_value'] is None
    assert by_name['inj_pres_1']['current_value'] == 35.0

    # 文案：经验推理本就没有推荐值 ⇒ 只说方向，不带数值
    assert by_name['inj_t']['reason'] == \
        '经验推理建议提高' + param_label('inj_t')
    assert by_name['inj_pres_1']['reason'] == \
        '经验推理建议提高' + param_label('inj_pres_1')
