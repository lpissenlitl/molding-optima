r"""工艺参数调优调用链的冒烟护栏（离线，不连 DB）。

覆盖：
1. 所有 import 可用（schema / service / view / urls）
2. Schema 校验接受合法请求、拒绝非法请求
3. Service 公开入口可调用
4. URL 路由已注册
5. 算法层接口契约（``OptimizeDataValidator``，字段名用 ORM 命名空间）

运行：
  cd backend
  ..\.venv\Scripts\python.exe -m pytest tests/test_optimize_smoke.py -q
"""
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")
django.setup()

from unittest.mock import patch  # noqa: E402

import pytest  # noqa: E402
from pydantic import ValidationError  # noqa: E402

from extensions.exceptions import BizException  # noqa: E402
from process.algorithms.fuzzy.specs import (  # noqa: E402
    OPTIMIZE_MACHINE_INFO_FIELDS,
    OptimizeDataValidator,
)
from process.schemas import (  # noqa: E402
    DefectFeedbackDataSchema,
    ProcessOptimizeFromConditionSchema,
    ProcessOptimizeFromProvidedSchema,
    SuggestionSchema,
)
from process.services import parameter_optimize as _opt_mod  # noqa: E402  模块级函数（service 层无类封装）
from process.urls import urlpatterns  # noqa: E402

#: 一台液压机的完整上限
#: 【注意】``max_injection_stroke``（实测行程）**是必填**：位置类判级论域上界的
#: 唯一权威源（``max_injection_stroke`` 属于必填字段）。
FULL_MACHINE = {
    "drive_system": "hydraulic",
    "max_set_injection_pressure": 180.0,
    "max_set_injection_speed": 300.0,
    "max_set_holding_pressure": 120.0,
    "max_set_holding_speed": 150.0,
    "max_set_screw_rotation_speed": 200.0,
    "max_set_metering_pressure": 100.0,
    "max_set_metering_back_pressure": 15.0,
    "max_set_decompression_pressure": 10.0,
    "max_injection_stroke": 200.0,
}
OK_POLYMER = {"abbreviation": "PP"}
OK_MOLD = {"product_category": "空调"}


# ---------------------------------------------------------------- schema 校验

def test_condition_schema_accepts_valid_request():
    """参照系（业务口径）：合法的调优请求能被解析成结构化对象。"""
    parsed = ProcessOptimizeFromConditionSchema.model_validate({
        "condition_id": 100,
        "parent_seq_idx": 1,
        "parameter": {"inj_spd_1": 50.0, "inj_pres_1": 60.0},
        "feedback": {
            "defects": [
                {"keyword_name": "短射", "level": "high", "position": "DL飞边3"},
                {"keyword_name": "飞边", "level": "medium", "position": "DL飞边2"},
            ],
            "observations": [
                {"param_key": "actual_product_weight", "value": 85.0},
                {"param_key": "peak_pressure", "value": None},
            ],
            "tuning_result": "ineffective",
        },
    })

    assert parsed.condition_id == 100
    assert parsed.parent_seq_idx == 1
    # parameter 是 ProcessParameterSchema 实例（不再是自由 dict），用属性访问
    assert parsed.parameter.inj_spd_1 == 50.0
    assert parsed.parameter.inj_pres_1 == 60.0
    assert len(parsed.feedback.defects) == 2
    assert parsed.feedback.tuning_result == "ineffective"


def test_condition_schema_rejects_missing_condition_id():
    """参照系（业务口径）：缺 condition_id ⇒ 拒（调优对象不明确）。"""
    with pytest.raises(Exception):
        ProcessOptimizeFromConditionSchema.model_validate({"parent_seq_idx": 1})


def test_suggestion_schema_accepts_wellformed_payload():
    """参照系（业务口径）：建议载荷结构被 schema 接受。"""
    suggestion = SuggestionSchema.model_validate({
        "source_type": "fuzzy_rule",
        "recommendation_id": 42,
        "groups": [
            {
                "category": "注射参数",
                "icon": "mdi:speedometer",
                "items": [
                    {
                        "description": "降低一段注射速度 5 mm/s",
                        "direction": "decrease",
                        "rule_refs": ["M001"],
                    }
                ],
            }
        ],
    })

    assert suggestion.source_type == "fuzzy_rule"
    assert len(suggestion.groups) == 1
    assert suggestion.groups[0].items[0].direction == "decrease"


def test_defect_feedback_schema_allows_null_keyword_name():
    """参照系（业务口径）：未选中的缺陷 keyword_name 可以为 null。"""
    empty_defect_schema = DefectFeedbackDataSchema.model_validate({
        "keyword_name": None,
        "level": None,
        "position": "",
    })

    assert empty_defect_schema.keyword_name is None


def test_defect_feedback_schema_defaults_to_none():
    """参照系（业务口径）：缺省时也走默认值 None。"""
    default_defect = DefectFeedbackDataSchema.model_validate({})

    assert default_defect.keyword_name is None


def test_condition_schema_accepts_defect_with_null_keyword_name():
    """参照系（业务口径）：含未选缺陷的完整请求也能通过。"""
    parsed = ProcessOptimizeFromConditionSchema.model_validate({
        "condition_id": 100,
        "parent_seq_idx": 1,
        "feedback": {"defects": [{"keyword_name": None}]},
    })

    assert parsed.feedback.defects[0].keyword_name is None


def test_condition_schema_accepts_parameter_none():
    """参照系（业务口径）：parameter 为 None 合法（用户没改参数 ⇒ service 走 ORM 反查 baseline）。"""
    parsed = ProcessOptimizeFromConditionSchema.model_validate({
        "condition_id": 100,
        "parent_seq_idx": 1,
        "feedback": {"defects": [{"keyword_name": "短射", "level": "high", "position": "DL1"}]},
    })

    assert parsed.parameter is None


def test_condition_schema_rejects_empty_parameter_dict():
    """参照系（业务口径）：parameter={} 应被拒（前端忘翻译 / 误传空 dict 都会落入此情形）。"""
    with pytest.raises(ValidationError) as exc:
        ProcessOptimizeFromConditionSchema.model_validate({
            "condition_id": 100, "parent_seq_idx": 1,
            "parameter": {},
            "feedback": {"defects": [{"keyword_name": "短射", "level": "high", "position": "DL1"}]},
        })

    msg = str(exc.value)
    assert "parameter" in msg or "工艺字段" in msg, f"error message should mention parameter: {msg}"


def test_condition_schema_rejects_business_metadata_only_parameter():
    """参照系（业务口径）：parameter 只含业务元数据（无标量工艺字段）⇒ 拒。"""
    with pytest.raises(ValidationError):
        ProcessOptimizeFromConditionSchema.model_validate({
            "condition_id": 100, "parent_seq_idx": 1,
            "parameter": {"parent_seq_idx": 5, "param_source": "manual"},
            "feedback": {"defects": [{"keyword_name": "短射", "level": "high", "position": "DL1"}]},
        })


def test_condition_schema_accepts_sparse_flat_override():
    """参照系（业务口径）：只覆盖一个标量工艺字段 ⇒ 合法，未覆盖字段保持 None。"""
    parsed = ProcessOptimizeFromConditionSchema.model_validate({
        "condition_id": 100, "parent_seq_idx": 1,
        "parameter": {"inj_spd_1": 50.0},
        "feedback": {"defects": [{"keyword_name": "短射", "level": "high", "position": "DL1"}]},
    })

    assert parsed.parameter.inj_spd_1 == 50.0
    assert parsed.parameter.inj_pres_1 is None


def test_provided_schema_accepts_minimal_context():
    """参照系（业务口径）：三维对象齐、字段可缺（两层设计：对象存在性由 pydantic 拦，
    字段级必填等级由 ``algorithms/fuzzy/specs.py`` 拦）。"""
    parsed = ProcessOptimizeFromProvidedSchema.model_validate({
        "parameter": {"inj_pres_1": 60.0},
        "feedback": {"defects": [{"keyword_name": "短射", "level": "high", "position": "DL1"}]},
        "mold_info": {"product_category": "空调"},
        "machine_info": {"drive_system": "hydraulic"},
        "polymer_info": {"abbreviation": "PP"},
    })

    assert parsed.machine_info.drive_system == "hydraulic"
    assert parsed.machine_info.max_set_injection_pressure is None
    # rule_library_code 已从公共 schema 移除（算法内部资源选择，上游自解）
    assert not hasattr(parsed, "rule_library_code")


@pytest.mark.parametrize("missing_dim", ["machine_info", "polymer_info", "mold_info"])
def test_provided_schema_rejects_missing_context_dimension(missing_dim):
    """参照系（业务口径）：缺任意一个维度对象必须被拒（论域上界无来源 ⇒ 模糊等级不可信）。"""
    provided_min = {
        "parameter": {"inj_pres_1": 60.0},
        "feedback": {"defects": [{"keyword_name": "短射", "level": "high", "position": "DL1"}]},
        "mold_info": {"product_category": "空调"},
        "machine_info": {"drive_system": "hydraulic"},
        "polymer_info": {"abbreviation": "PP"},
    }
    bad = {k: v for k, v in provided_min.items() if k != missing_dim}

    with pytest.raises(ValidationError):
        ProcessOptimizeFromProvidedSchema.model_validate(bad)


def test_provided_schema_accepts_full_context_and_drops_unknown_fields():
    """参照系（业务口径）：三维齐全 ⇒ 接受；未知字段由 BaseSchema 的 extra='ignore' 丢弃。"""
    parsed = ProcessOptimizeFromProvidedSchema.model_validate({
        "parameter": {"inj_pres_1": 60.0, "brl_temp_3": 220.0, "unknown_biz_field": 1},
        "feedback": {"defects": [{"keyword_name": "飞边", "level": "medium", "position": "分型面"}]},
        "mold_info": {"product_category": "空调", "target_cycle_time": 45.0},
        "machine_info": {
            "drive_system": "hydraulic",
            "max_set_injection_pressure": 180.0,
            "max_set_holding_pressure": 120.0,
            "bogus": 9,
        },
        "polymer_info": {"abbreviation": "PP", "min_melt_temp": 200.0, "max_melt_temp": 260.0},
    })

    assert parsed.machine_info.max_set_injection_pressure == 180.0
    assert parsed.polymer_info.max_melt_temp == 260.0
    assert parsed.mold_info.product_category == "空调"
    assert not hasattr(parsed.machine_info, "bogus")


def test_provided_schema_keeps_injection_stroke():
    """参照系（业务口径）：接口层**保留**实测行程字段。

    【注意】``BaseSchema`` 是 ``extra="ignore"`` ⇒ schema 未声明的字段会被
    **静默丢弃** ⇒ 行程若没在 schema 里声明，契约层会误判「缺行程」而拒。
    """
    parsed = ProcessOptimizeFromProvidedSchema.model_validate({
        "parameter": {"inj_pres_1": 60.0},
        "feedback": {"defects": [{"keyword_name": "短射", "level": "high", "position": "DL1"}]},
        "mold_info": {"product_category": "空调"},
        "machine_info": {"drive_system": "hydraulic", "max_injection_stroke": 200.0},
        "polymer_info": {"abbreviation": "PP"},
    })

    assert parsed.machine_info.max_injection_stroke == 200.0


def test_provided_schema_rejects_missing_parameter():
    """参照系（业务口径）：缺 parameter 必须报错（调优作用对象缺失）。"""
    with pytest.raises(Exception):
        ProcessOptimizeFromProvidedSchema.model_validate({"feedback": {}})


# ---------------------------------------------------------------- service 入口

def test_service_exposes_public_entrypoints():
    """参照系（业务口径）：service 层公开入口与纯算法内核都在。"""
    assert hasattr(_opt_mod, "optimize_from_condition")
    assert hasattr(_opt_mod, "optimize_from_provided")
    # 模块顶层 helper
    assert hasattr(_opt_mod, "_resolve_condition")
    assert hasattr(_opt_mod, "_resolve_parent_parameter")
    assert hasattr(_opt_mod, "_resolve_baseline")
    assert hasattr(_opt_mod, "_build_suggestion_payload")
    # 纯算法内核（Step 3+4，两个入口共用，对应 parameter_initialize._infer_kernel 模式）
    assert hasattr(_opt_mod, "_infer_kernel")
    assert hasattr(_opt_mod, "_compose_algorithm_context")


def test_optimize_from_provided_rejects_empty_defect_list():
    """参照系（业务口径）：缺 feedback.defects 必拒（与 optimize_from_condition 同一套约束镜像）。"""
    with pytest.raises(BizException) as exc:
        _opt_mod.optimize_from_provided(
            parameter={"inj_pres_1": 60.0},
            feedback={"defects": []},
            mold_info={"product_category": "空调"},
            machine_info={"drive_system": "hydraulic"},
            polymer_info={"abbreviation": "PP"},
        )

    assert "缺陷" in str(exc.value) or "feedback" in str(exc.value).lower() or "defect" in str(exc.value).lower()


def test_optimize_from_provided_full_path_runs():
    """参照系（业务口径）：完整输入能走通整条链路。

    接受 2 种结果：成功（返回 parameter+suggestion）/ fail-fast（无推荐 BizException）
    —— 只要不是 NameError 就说明链路是通的。

    【注意】``_resolve_visible_libraries`` 是唯一碰 DB 的点 ⇒ 桩成空库列表，
    本用例保持离线可跑。
    """
    try:
        with patch.object(_opt_mod, "_resolve_visible_libraries", return_value=[]):
            result = _opt_mod.optimize_from_provided(
                parameter={"inj_pres_1": 60.0, "brl_temp_3": 220.0},
                feedback={"defects": [{"keyword_name": "短射", "level": "high", "position": "DL1"}]},
                mold_info={"product_category": "空调"},
                machine_info={
                    "drive_system": "hydraulic",
                    "max_set_injection_pressure": 180.0,
                    "max_set_injection_speed": 300.0,
                    "max_set_holding_pressure": 120.0,
                    "max_set_holding_speed": 150.0,
                    "max_set_screw_rotation_speed": 200.0,
                    "max_set_metering_pressure": 100.0,
                    "max_set_metering_back_pressure": 15.0,
                    "max_set_decompression_pressure": 10.0,
                    "max_injection_stroke": 200.0,
                },
                polymer_info={"abbreviation": "PP"},
            )
    except BizException as exc:
        # fail-fast 路径：算法无推荐（规则集不全）/ 零落地（场景裁决后无可落地参数）
        # —— 两种都是链路走通的标志
        assert (
            "推荐算法" in str(exc) or "无法落地" in str(exc)
        ), f"unexpected BizException: {exc}"
        return

    # 成功路径：从 provided 返回的 parameter / suggestion 无落库 ID
    # （入参给的是中文缺陷名「短射」⇒ 转换头把它译成英文码 SHORTSHOT，
    #   规则库按英文码匹配 ⇒ 能查到规则）
    assert "parameter" in result, f"missing parameter: {result.keys()}"
    assert "suggestion" in result, f"missing suggestion: {result.keys()}"
    assert "parameter_id" not in result["parameter"]
    assert "seq_idx" not in result["parameter"]
    assert "recommendation_id" not in result["suggestion"]


def test_optimize_from_provided_chinese_defect_name_reaches_success_path():
    """参照系（业务口径）：中文缺陷名能走通到成功返回（转换头译成英文码）。

    缺陷码词表在算法层公共底座（``algorithms/common/defect_codes.py``）
    ⇒ 中文名与英文码走同一条路径（阶段推导 / 场景裁决也拿同一份英文码）。
    """
    with patch.object(_opt_mod, "_resolve_visible_libraries", return_value=[]):
        result = _opt_mod.optimize_from_provided(
            parameter={"inj_pres_1": 60.0, "brl_temp_3": 220.0},
            feedback={"defects": [{"keyword_name": "缩水", "level": "high", "position": "DL1"}]},
            mold_info=OK_MOLD,
            machine_info=FULL_MACHINE,
            polymer_info=OK_POLYMER,
        )

    assert "parameter" in result, f"missing parameter: {result.keys()}"
    assert "suggestion" in result, f"missing suggestion: {result.keys()}"
    assert "parameter_id" not in result["parameter"]
    assert "seq_idx" not in result["parameter"]
    assert "recommendation_id" not in result["suggestion"]


# ---------------------------------------------------------------- URL 路由

def test_optimize_route_is_registered():
    """参照系（业务口径）：调优入口的 URL 路由已注册且唯一。"""
    optimize_routes = [p for p in urlpatterns if "algorithms/optimize" in str(p.pattern)]

    assert len(optimize_routes) == 1, f"expected 1 optimize route, got {len(optimize_routes)}"


# ---------------------------------------------------------------- 算法层契约

def test_validator_accepts_complete_hydraulic_input():
    """参照系（业务口径）：完整的液压机输入通过算法层契约校验。"""
    OptimizeDataValidator.validate(FULL_MACHINE, OK_POLYMER, OK_MOLD)


def test_validator_rejects_missing_injection_limit():
    """参照系（业务口径）：缺机台上限 ⇒ **必拒**。

    设备实际值是**判级论域上界的必需来源**（从设备读取参数是为了用实际值补全
    参数的论域；设备值没有就报错）⇒ 缺了论域上界无法确定
    ⇒ 模糊等级判错 ⇒ 直接拒，而不是「不拦请求、只不裁剪」。
    """
    missing_pressure = {k: v for k, v in FULL_MACHINE.items()
                        if k != "max_set_injection_pressure"}

    with pytest.raises(ValueError) as exc:
        OptimizeDataValidator.validate(missing_pressure, OK_POLYMER, OK_MOLD)

    assert "max_set_injection_pressure" in str(exc.value), str(exc.value)


def test_validator_rejects_missing_metering_limit_on_hydraulic():
    """参照系（业务口径）：液压机缺计量压力 ⇒ **必拒**（标「液压机必填」）。"""
    missing_metering = {k: v for k, v in FULL_MACHINE.items()
                        if k != "max_set_metering_pressure"}

    with pytest.raises(ValueError) as exc:
        OptimizeDataValidator.validate(missing_metering, OK_POLYMER, OK_MOLD)

    assert "max_set_metering_pressure" in str(exc.value), str(exc.value)


def test_validator_rejects_missing_injection_stroke():
    """参照系（业务口径）：缺实测行程 ⇒ **必拒**。

    行程是位置类判级论域上界的**唯一权威源**（``max_injection_stroke``
    属于必填字段）⇒ 缺失 ⇒ 位置类判级区间没有上界 ⇒ 「充填量第一优先」的那组
    规则失活 ⇒ 直接拒，而不是「回落经验论域」。
    """
    missing_stroke = {k: v for k, v in FULL_MACHINE.items()
                      if k != "max_injection_stroke"}

    with pytest.raises(ValueError) as exc:
        OptimizeDataValidator.validate(missing_stroke, OK_POLYMER, OK_MOLD)

    assert "max_injection_stroke" in str(exc.value), str(exc.value)


def test_validator_tolerates_electric_machine_without_metering_limit():
    """参照系（业务口径）：全电机缺计量压力 ⇒ **不拒**。

    标「液压机必填」⇒ 全电机 HMI 物理上无此栏，缺失属正常，不能当数据缺失拦人。
    """
    electric = {
        **{k: v for k, v in FULL_MACHINE.items() if k != "max_set_metering_pressure"},
        "drive_system": "electric",
    }

    OptimizeDataValidator.validate(electric, OK_POLYMER, OK_MOLD)


def test_validator_tolerates_missing_optional_keys():
    """参照系（业务口径）：规则库筛选键（abbreviation / product_category）都是「可选」
    —— 为精度旋钮，填了命中高特异度规则，不填退到默认规则，算法并不因缺它们而无法运行。"""
    OptimizeDataValidator.validate(FULL_MACHINE, {}, OK_MOLD)
    OptimizeDataValidator.validate(FULL_MACHINE, OK_POLYMER, {})


def test_validator_treats_temperature_bounds_as_recommended():
    """参照系（业务口径）：温度类字段是「推荐」—— 缺失不拦
    （触发条件在本维度外，强拦会挡住纯压力类调优）。"""
    OptimizeDataValidator.validate(FULL_MACHINE, OK_POLYMER, OK_MOLD)  # 未带任何温度字段

    assert OPTIMIZE_MACHINE_INFO_FIELDS["max_set_decompression_speed"]["condition"] == "可选"


def main():
    """独立跑法（不依赖 pytest）：``python -m tests.test_optimize_smoke``。"""
    import inspect

    cases = [
        fn for name, fn in sorted(globals().items())
        if name.startswith('test_') and inspect.isfunction(fn)
    ]
    failed = []
    for fn in cases:
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 - 独立跑法需要汇总全部失败
            print(f'[FAIL] {fn.__name__}: {exc}')
            failed.append(fn.__name__)
    print('\n' + '=' * 60)
    if failed:
        print(f'[FAIL] {len(failed)}/{len(cases)} 个用例失败：{failed}')
        return 1
    print(f'[PASS] {len(cases)}/{len(cases)} 个用例通过')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())