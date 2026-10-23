"""verify_user_parameter_sync.py
验证「用户手改的工艺参数 → 写回父记录」的时序（B 方案，2026-10-22）。

业务不变式：**DB 里的记录必须等于用户实际在用的参数**。
用户在前端改了工艺参数、不点【保存试模结果】直接点【获取优化工艺】时，
只有 infer 路径能把改动落库（tuning-feedback 不写 ProcessParameter）。

本次改造（Step 1 装配上下文 + Step 3 落库）：
- Step 1 只读：_resolve_baseline 不再 save，只改内存并吐出 changed_fields
- Step 3 事务内：_sync_user_modified_parameter 精确写回父记录

覆盖：
1. _resolve_baseline 只改内存、不落库；changed_fields 只含**值真的变了**的字段
2. _sync_user_modified_parameter 把改动落库
3. infer 推理失败（fail-fast）→ 父记录**未被改**（写回在落库阶段，不进 Step 3）
4. infer 推理成功 → 父记录被改成用户改后的值，且新轮次已创建

策略：真实 DB fixture（condition + parameter）；_extract_* 与 _call_algorithms 用 mock
（无真实规则库数据），保证测试只聚焦「写回时序」这一件事。
"""

import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")

import django

django.setup()

from unittest.mock import patch

from extensions.exceptions import BizException
from masterdata.models import Mold, Polymer
from process.models import ProcessCondition, ProcessParameter
from process.services import parameter_optimize as _opt_mod
from process.services.parameter_optimize import ParameterOptimizeService

print("=" * 70)
print("用户手改参数 → 写回父记录：时序验证（B 方案）")
print("=" * 70)

FAILURES = []


def check(cond, ok_msg, fail_msg):
    if cond:
        print(f"  [PASS] {ok_msg}")
    else:
        print(f"  [FAIL] {fail_msg}")
        FAILURES.append(fail_msg)


# ---------------------------------------------------------------------------
# Fixture：mold + polymer + condition + 2 个 parameter
#   p_unit  —— 给「helper 级」用例（用例 1、2）用
#   p_infer —— 给「infer 级」用例（用例 3、4）用
# ---------------------------------------------------------------------------
mold = polymer = condition = None
p_unit = p_infer = None


def setup_fixtures():
    global mold, polymer, condition, p_unit, p_infer

    mold = Mold.objects.create(
        mold_no=f"TEST-MOLD-SYNC-{os.getpid()}",
        mold_name="测试模具-参数同步",
        cavity_count=2,
    )
    polymer = Polymer.objects.create(
        abbreviation="TEST-ABS",
        grade="TEST-GRADE",
        manufacturer="TEST-MFR",
    )
    condition = ProcessCondition.objects.create(
        status="active",
        condition_no=f"TEST-PC-SYNC-{os.getpid()}",
        origin_type="manual_creation",
        mold=mold,
        polymer=polymer,
    )
    p_unit = ProcessParameter.objects.create(
        process_condition=condition,
        parent_param=None,
        param_source="algorithm_init",
        inj_spd_1=50.0,
        inj_pres_1=80.0,
    )
    p_infer = ProcessParameter.objects.create(
        process_condition=condition,
        parent_param=None,
        param_source="algorithm_init",
        inj_spd_1=50.0,
        inj_pres_1=80.0,
    )


def cleanup_fixtures():
    if condition is not None:
        ProcessParameter.objects.filter(process_condition=condition).delete()
        ProcessCondition.objects.filter(id=condition.id).delete()
    if mold is not None:
        Mold.objects.filter(id=mold.id).delete()
    if polymer is not None:
        Polymer.objects.filter(id=polymer.id).delete()


# ---------------------------------------------------------------------------
# 用例 1：_resolve_baseline 只改内存，不落库
# ---------------------------------------------------------------------------
def case_1_resolve_baseline_no_write():
    print("\n[用例1] _resolve_baseline：只改内存、不落库，changed_fields 只含真变化")
    target = ProcessParameter.objects.get(id=p_unit.id)

    # inj_spd_1 改成 99.0（真变化）；inj_pres_1 传 80.0（与库中原值相同 → 不算改动）
    baseline, changed = _opt_mod._resolve_baseline(
        user_parameter={"inj_spd_1": 99.0, "inj_pres_1": 80.0},
        base_param_orm=target,
    )

    check(
        changed == {"inj_spd_1": 99.0},
        f"changed_fields 只含真变化字段: {changed}",
        f"changed_fields 应只含 inj_spd_1，实际 {changed}",
    )
    check(
        baseline.get("inj_spd_1") == 99.0,
        "baseline 已用用户改后的值（推理起点 = 用户实际在用的参数）",
        f"baseline.inj_spd_1 应为 99.0，实际 {baseline.get('inj_spd_1')}",
    )
    check(
        target.inj_spd_1 == 99.0,
        "ORM 内存对象已被 setattr",
        f"内存对象 inj_spd_1 应为 99.0，实际 {target.inj_spd_1}",
    )

    # 关键：DB 里还没变
    db_value = ProcessParameter.objects.get(id=p_unit.id).inj_spd_1
    check(
        db_value == 50.0,
        "DB 中该记录**未被修改**（Step 1 只读）",
        f"DB 中 inj_spd_1 应仍为 50.0，实际 {db_value}",
    )


# ---------------------------------------------------------------------------
# 用例 2：_sync_user_modified_parameter 精确写回
# ---------------------------------------------------------------------------
def case_2_sync_writes_back():
    print("\n[用例2] _sync_user_modified_parameter：把改动落库")
    target = ProcessParameter.objects.get(id=p_unit.id)

    _opt_mod._sync_user_modified_parameter(
        parent_param=target,
        changed_fields={"inj_spd_1": 99.0},
    )

    fresh = ProcessParameter.objects.get(id=p_unit.id)
    check(
        fresh.inj_spd_1 == 99.0,
        "改动已落库（DB 与用户实际在用的参数一致）",
        f"DB 中 inj_spd_1 应为 99.0，实际 {fresh.inj_spd_1}",
    )
    check(
        fresh.inj_pres_1 == 80.0,
        "未改动的字段值不变",
        f"inj_pres_1 应仍为 80.0，实际 {fresh.inj_pres_1}",
    )


# ---------------------------------------------------------------------------
# 用例 3：infer 推理失败 → 父记录未被改
# ---------------------------------------------------------------------------
def case_3_infer_fail_keeps_db_unchanged():
    print("\n[用例3] infer 推理失败（fail-fast）→ 父记录未被改")
    before = ProcessParameter.objects.get(id=p_infer.id)
    before_spd = before.inj_spd_1
    before_param_count = ProcessParameter.objects.filter(process_condition=condition).count()

    service = ParameterOptimizeService()
    empty_result = {
        "recommendations": [],
        "algorithm_sources": {},
        "algorithm_names": {},
        "best_recommendation": None,
    }

    with patch.object(_opt_mod, "_extract_machine_info", return_value={}), \
         patch.object(_opt_mod, "_extract_polymer_info", return_value={}), \
         patch.object(_opt_mod, "_extract_mold_info", return_value={}), \
         patch.object(_opt_mod, "_call_algorithms", return_value=empty_result):
        try:
            service.infer(
                condition_id=condition.id,
                parent_seq_idx=p_infer.seq_idx,
                parameter={"inj_spd_1": 77.0},
                feedback={"defect": [{"keyword_name": "DEFECTFREE"}]},
            )
            check(False, "", "推理失败场景：期望抛 BizException，实际无异常")
        except BizException:
            print("  [PASS] 推理失败抛 BizException（fail-fast 生效）")

    after_spd = ProcessParameter.objects.get(id=p_infer.id).inj_spd_1
    after_param_count = ProcessParameter.objects.filter(process_condition=condition).count()

    check(
        after_spd == before_spd,
        f"父记录未被改写（仍是 {before_spd}）—— 写回在落库阶段，失败不进 Step 3",
        f"推理失败时父记录不应被改，实际 inj_spd_1={after_spd}（期望 {before_spd}）",
    )
    check(
        after_param_count == before_param_count,
        "未创建新轮次",
        f"轮次数应不变，实际 {before_param_count}→{after_param_count}",
    )


# ---------------------------------------------------------------------------
# 用例 4：infer 推理成功 → 父记录被改 + 新轮次创建
# ---------------------------------------------------------------------------
def case_4_infer_success_syncs_db():
    print("\n[用例4] infer 推理成功 → 父记录被改成用户改后的值 + 新轮次创建")
    before_param_count = ProcessParameter.objects.filter(process_condition=condition).count()

    service = ParameterOptimizeService()
    algo_result = {
        "recommendations": [
            {
                "param": "inj_pres_1",
                "current_value": 80.0,
                "recommended_value": 88.0,
                "direction": "increase",
                "confidence": 0.9,
            }
        ],
        "algorithm_sources": {"fuzzy": []},
        "algorithm_names": {"fuzzy": "模糊推理"},
        "best_recommendation": None,
    }

    with patch.object(_opt_mod, "_extract_machine_info", return_value={}), \
         patch.object(_opt_mod, "_extract_polymer_info", return_value={}), \
         patch.object(_opt_mod, "_extract_mold_info", return_value={}), \
         patch.object(_opt_mod, "_call_algorithms", return_value=algo_result):
        result = service.infer(
            condition_id=condition.id,
            parent_seq_idx=p_infer.seq_idx,
            parameter={"inj_spd_1": 77.0},
            feedback={"defect": [{"keyword_name": "DEFECTFREE"}]},
        )

    fresh_parent = ProcessParameter.objects.get(id=p_infer.id)
    check(
        fresh_parent.inj_spd_1 == 77.0,
        "父记录已写回用户改后的值（DB = 用户实际在用的参数）",
        f"父记录 inj_spd_1 应为 77.0，实际 {fresh_parent.inj_spd_1}",
    )
    check(
        fresh_parent.inj_pres_1 == 80.0,
        "父记录未被算法推荐值污染（推荐只作用在新轮次）",
        f"父记录 inj_pres_1 应仍为 80.0，实际 {fresh_parent.inj_pres_1}",
    )

    after_param_count = ProcessParameter.objects.filter(process_condition=condition).count()
    check(
        after_param_count == before_param_count + 1,
        "新轮次已创建",
        f"轮次数应 +1，实际 {before_param_count}→{after_param_count}",
    )

    new_param_id = result.get("new_parameter", {}).get("parameter_id")
    new_param = ProcessParameter.objects.get(id=new_param_id)
    check(
        new_param.inj_spd_1 == 77.0,
        "新轮次带上了用户手改后的值（历史不丢用户调整）",
        f"新轮次 inj_spd_1 应为 77.0，实际 {new_param.inj_spd_1}",
    )
    check(
        new_param.inj_pres_1 == 88.0,
        "新轮次带上了算法推荐值",
        f"新轮次 inj_pres_1 应为 88.0，实际 {new_param.inj_pres_1}",
    )


# ===========================================================================
def main():
    setup_fixtures()
    try:
        case_1_resolve_baseline_no_write()
        case_2_sync_writes_back()
        case_3_infer_fail_keeps_db_unchanged()
        case_4_infer_success_syncs_db()
    finally:
        cleanup_fixtures()
        print("\n[fixture 清理完成]")

    print()
    print("=" * 70)
    if FAILURES:
        print(f"FAILED（{len(FAILURES)} 项）:")
        for f in FAILURES:
            print(f"  - {f}")
    else:
        print("ALL PASSED")
    print("=" * 70)
    return 0 if not FAILURES else 1


if __name__ == "__main__":
    sys.exit(main())
