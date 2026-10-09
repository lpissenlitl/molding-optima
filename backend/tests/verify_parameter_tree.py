"""parameter.py 服务验证：CRUD + 版本树查询 + 手动版本管理

覆盖：
- get_parameter：按 ID 取具体某一条
- update_parameter：白名单字段更新 + forbidden 字段保护
- delete_parameter：删除叶节点 OK + 有 children 拒绝
- get_parameter_tree：树形结构（嵌套 children）
- get_parameter_lineage：祖先链（root → 当前）
- get_parameter_descendants：后代 BFS 平铺
- create_adjustment_version：手动版本创建（seq_idx + parent + param_source）
- revert_parameter：基于历史版本创建新 parameter

设计意图：
- 真实 DB fixture（mold + polymer + condition + 6 个 parameter 构成版本树）
- 顶部清理 + 底部清理（test 期间数据不影响其他测试）
- 注：ProcessParameter.save() 自动分配 seq_idx（max+1），测试需用实际 seq_idx 断言
- 8 个测试场景，每个都用 [PASS]/[FAIL] 风格
"""

import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")

import django

django.setup()

from django.db.models import Max
from extensions.exceptions import BizException, ERROR_DATA_NOT_FOUND, ERROR_ILLEGAL_ARGUMENT
from masterdata.models import Mold, Polymer
from process.models import ProcessCondition, ProcessParameter
from process.services.parameter import (
    get_parameter,
    update_parameter,
    delete_parameter,
    get_parameter_tree,
    get_parameter_lineage,
    get_parameter_descendants,
    create_adjustment_version,
    revert_parameter,
)


print("=" * 70)
print("parameter.py 服务验证：CRUD + 版本树查询 + 手动版本管理")
print("=" * 70)


# ============================================================================
# Fixture 准备（真实 DB 操作，try/finally 保证清理）
# ============================================================================

mold = polymer = condition = None
created_parameter_ids = []  # 测试结束时统一软删


def setup_fixtures():
    """创建测试 fixture：mold + polymer + condition + 6 个 parameter（树形结构）

    注：ProcessParameter.save() 自动分配 seq_idx（max+1），
    故 fixture 创建顺序决定 seq_idx 严格递增：1, 2, 3, 4, 5, 6

    树形结构：
        P1 (seq=1, parent=None)
          ├── P2 (seq=2, parent=P1)
          │     └── P3 (seq=3, parent=P2)  [测试中会被软删]
          └── P4 (seq=4, parent=P1)
        P5 (seq=5, parent=None)             [算法初始化，无 children]
        P6 (seq=6, parent=None)             [孤立 root]
    """
    global mold, polymer, condition

    # 1. Mold（mold_no 必填）
    mold = Mold.objects.create(
        mold_no=f"TEST-MOLD-{os.getpid()}",
        mold_name="测试模具",
        cavity_count=2,
    )

    # 2. Polymer（所有字段 null=True）
    polymer = Polymer.objects.create(
        abbreviation="TEST-ABS",
        grade="TEST-GRADE",
        manufacturer="TEST-MFR",
    )

    # 3. ProcessCondition
    condition = ProcessCondition.objects.create(
        status="active",
        condition_no=f"TEST-PC-{os.getpid()}",
        origin_type="manual_creation",
        mold=mold,
        polymer=polymer,
    )

    # 4. 创建 parameter（save() 自动分配 seq_idx = max+1）
    p1 = ProcessParameter.objects.create(
        process_condition=condition,
        parent_param=None,
        param_source="algorithm_init",
        inj_spd_1=50.0,
        inj_pres_1=80.0,
    )
    p2 = ProcessParameter.objects.create(
        process_condition=condition,
        parent_param=p1,
        param_source="ai_recommended",
        inj_spd_1=55.0,
        inj_pres_1=85.0,
    )
    p3 = ProcessParameter.objects.create(
        process_condition=condition,
        parent_param=p2,
        param_source="ai_recommended",
        inj_spd_1=60.0,
        inj_pres_1=90.0,
    )
    p4 = ProcessParameter.objects.create(
        process_condition=condition,
        parent_param=p1,
        param_source="manual_adjusted",
        inj_spd_1=52.0,
        inj_pres_1=82.0,
    )
    p5 = ProcessParameter.objects.create(
        process_condition=condition,
        parent_param=None,
        param_source="algorithm_init",
        inj_spd_1=48.0,
        inj_pres_1=78.0,
    )
    p6 = ProcessParameter.objects.create(
        process_condition=condition,
        parent_param=None,  # 孤立 root（视为 root）
        param_source="manual",
        inj_spd_1=70.0,
        inj_pres_1=95.0,
    )

    created_parameter_ids.extend([p1.id, p2.id, p3.id, p4.id, p5.id, p6.id])
    return p1, p2, p3, p4, p5, p6


def cleanup_fixtures():
    """清理 fixture：所有 parameter 软删 + condition + mold + polymer 软删"""
    # 软删 parameter（按 seq_idx 降序删，先删 children 再删 parent，避开 has_children 保护）
    if created_parameter_ids:
        ProcessParameter.all_objects.filter(id__in=created_parameter_ids).delete()
    if condition:
        condition.delete()
    if mold:
        mold.delete()
    if polymer:
        polymer.delete()


# 准备 fixture
p1, p2, p3, p4, p5, p6 = setup_fixtures()


try:
    # ============================================================================
    # Test 1: get_parameter（按 ID 取具体某一条）
    # ============================================================================
    print("\n[1] get_parameter 验证:")
    data = get_parameter(p3.id)
    assert data["id"] == p3.id, f"id mismatch: {data['id']} vs {p3.id}"
    assert data["parent_param_id"] == p2.id, "parent_param_id 错误"
    assert data["process_condition_id"] == condition.id, "process_condition_id 错误"
    assert data["seq_idx"] == p3.seq_idx, f"seq_idx 错误: {data['seq_idx']} vs {p3.seq_idx}"
    assert data["param_source"] == "ai_recommended", "param_source 错误"
    print(f"    [OK] get_parameter({p3.id}) 返回正确字段 (seq_idx={data['seq_idx']})")

    # 测试不存在的 ID
    try:
        get_parameter(999999999)
        print(f"    [FAIL] 不存在的 id 应抛 BizException")
        sys.exit(1)
    except BizException as e:
        assert e.error_code == ERROR_DATA_NOT_FOUND, f"错误码不对: {e.error_code}"
        print(f"    [OK] 不存在的 id 抛 BizException(DATA_NOT_FOUND): {e}")

    # ============================================================================
    # Test 2: update_parameter（白名单 + 保护）
    # ============================================================================
    print("\n[2] update_parameter 验证:")
    # 合法字段更新
    original_inj_pres_1 = p3.inj_pres_1
    updated = update_parameter(
        p3.id,
        inj_pres_1=original_inj_pres_1 + 5,
        inj_spd_1=original_inj_pres_1 + 10,
    )
    assert updated["inj_pres_1"] == original_inj_pres_1 + 5, "inj_pres_1 未更新"
    print(f"    [OK] 合法字段更新成功: inj_pres_1={original_inj_pres_1} -> {updated['inj_pres_1']}")

    # forbidden 字段被过滤
    p3_fresh = ProcessParameter.objects.get(id=p3.id)
    original_parent = p3_fresh.parent_param_id
    original_seq = p3_fresh.seq_idx
    original_cond_id = p3_fresh.process_condition_id
    original_no = p3_fresh.parameter_no

    update_parameter(
        p3.id,
        inj_pres_1=99.0,
        # 试图篡改关系/主键字段（应被过滤）：
        id=999999,
        process_condition_id=999999,
        parent_param_id=999999,
        seq_idx=999,
        parameter_no="HACK",
        created_at="2000-01-01",
        is_deleted=True,
    )
    p3_after = ProcessParameter.objects.get(id=p3.id)
    assert p3_after.parent_param_id == original_parent, "parent_param_id 被篡改!"
    assert p3_after.seq_idx == original_seq, "seq_idx 被篡改!"
    assert p3_after.process_condition_id == original_cond_id, "process_condition_id 被篡改!"
    assert p3_after.parameter_no == original_no, "parameter_no 被篡改!"
    assert p3_after.is_deleted is False, "is_deleted 被篡改!"
    assert p3_after.inj_pres_1 == 99.0, "合法字段未更新"
    print(f"    [OK] forbidden 字段被正确过滤（parent/seq/cond_id/no/is_deleted 未变）")

    # 空 kwargs 应抛 BizException
    try:
        update_parameter(p3.id)
        print(f"    [FAIL] 空 kwargs 应抛 BizException")
        sys.exit(1)
    except BizException as e:
        assert e.error_code == ERROR_ILLEGAL_ARGUMENT, f"错误码不对: {e.error_code}"
        print(f"    [OK] 空 kwargs 抛 BizException(ILLEGAL_ARGUMENT)")

    # ============================================================================
    # Test 3: delete_parameter（叶节点 OK + 中间节点拒绝）
    # ============================================================================
    print("\n[3] delete_parameter 验证:")
    # P3 在树中无 children（p4 是 P1 的子，不是 P3 的子）
    p3_children = ProcessParameter.objects.filter(
        parent_param_id=p3.id, is_deleted=False
    ).count()
    assert p3_children == 0, f"P3 不应有 children，但有 {p3_children}"

    delete_parameter(p3.id)
    p3_deleted = ProcessParameter.all_objects.get(id=p3.id)
    assert p3_deleted.is_deleted is True, "软删标志未设置"
    print(f"    [OK] 删除叶节点 P3 成功（is_deleted=True）")

    # P1 有 children（P2, P4）—— 删除应被拒绝
    try:
        delete_parameter(p1.id)
        print(f"    [FAIL] 有 children 的 P1 应被拒绝删除")
        sys.exit(1)
    except BizException as e:
        assert e.error_code == ERROR_ILLEGAL_ARGUMENT, f"错误码不对: {e.error_code}"
        print(f"    [OK] 有 children 的 P1 删除被拒绝: {e}")

    # 不存在 ID
    try:
        delete_parameter(999999999)
        print(f"    [FAIL] 不存在的 id 应抛 BizException")
        sys.exit(1)
    except BizException as e:
        print(f"    [OK] 不存在 id 抛 BizException: {e}")

    # ============================================================================
    # Test 4: get_parameter_tree（树形结构）
    # ============================================================================
    print("\n[4] get_parameter_tree 验证:")
    # 注：P3 已被软删，不应在树中
    tree = get_parameter_tree(condition.id)
    # 应有 3 个 root：P1, P5, P6（都是 parent=None）
    root_ids = sorted([r["id"] for r in tree])
    expected_roots = sorted([p1.id, p5.id, p6.id])
    assert root_ids == expected_roots, f"roots 错误: {root_ids} vs {expected_roots}"
    print(f"    [OK] 返回 {len(tree)} 个 root: {root_ids}")

    # 验证 P1 的 children
    p1_node = next(r for r in tree if r["id"] == p1.id)
    p1_child_ids = sorted([c["id"] for c in p1_node["children"]])
    # P1 的 children：P2, P4（P3 已被软删，所以 P2 无 children）
    assert p1_child_ids == sorted([p2.id, p4.id]), f"P1 children 错误: {p1_child_ids}"
    print(f"    [OK] P1.children = {p1_child_ids}")

    # 验证 P2 的 children 应为 []（因为 P3 已删）
    p2_node = next(c for c in p1_node["children"] if c["id"] == p2.id)
    assert p2_node["children"] == [], f"P2.children 应为空: {p2_node['children']}"
    print(f"    [OK] P2.children = []（P3 已被软删）")

    # 不存在的 condition_id
    try:
        get_parameter_tree(999999999)
        print(f"    [FAIL] 不存在的 condition_id 应抛 BizException")
        sys.exit(1)
    except BizException as e:
        assert e.error_code == ERROR_DATA_NOT_FOUND, f"错误码不对: {e.error_code}"
        print(f"    [OK] 不存在 condition_id 抛 BizException: {e}")

    # ============================================================================
    # Test 5: get_parameter_lineage（祖先链）
    # ============================================================================
    print("\n[5] get_parameter_lineage 验证:")
    # 从 P4 查：root=P1, current=P4
    lineage_p4 = get_parameter_lineage(p4.id)
    lineage_p4_ids = [n["id"] for n in lineage_p4]
    assert lineage_p4_ids == [p1.id, p4.id], f"P4 lineage 错误: {lineage_p4_ids}"
    print(f"    [OK] P4 lineage = {lineage_p4_ids}")

    # 从 P2 查（P2.parent=P1，P3 已删不影响 P2 自身链）
    lineage_p2 = get_parameter_lineage(p2.id)
    lineage_p2_ids = [n["id"] for n in lineage_p2]
    assert lineage_p2_ids == [p1.id, p2.id], f"P2 lineage 错误: {lineage_p2_ids}"
    print(f"    [OK] P2 lineage = {lineage_p2_ids}")

    # 从 root P1 查：lineage = [P1]
    lineage_p1 = get_parameter_lineage(p1.id)
    lineage_p1_ids = [n["id"] for n in lineage_p1]
    assert lineage_p1_ids == [p1.id], f"P1 lineage 错误: {lineage_p1_ids}"
    print(f"    [OK] P1 (root) lineage = {lineage_p1_ids}")

    # 从 isolated P6 查：lineage = [P6]
    lineage_p6 = get_parameter_lineage(p6.id)
    lineage_p6_ids = [n["id"] for n in lineage_p6]
    assert lineage_p6_ids == [p6.id], f"P6 lineage 错误: {lineage_p6_ids}"
    print(f"    [OK] P6 (isolated) lineage = {lineage_p6_ids}")

    # ============================================================================
    # Test 6: get_parameter_descendants（后代 BFS）
    # ============================================================================
    print("\n[6] get_parameter_descendants 验证:")
    # P1 的后代（不含 P3 因已删）：P2, P4（按 seq_idx 排序：P2.seq < P4.seq）
    descendants_p1 = get_parameter_descendants(p1.id)
    descendant_ids_p1 = [d["id"] for d in descendants_p1]
    assert descendant_ids_p1 == [p2.id, p4.id], (
        f"P1 descendants 错误: {descendant_ids_p1}（应为 [{p2.id}, {p4.id}]）"
    )
    print(f"    [OK] P1 descendants = {descendant_ids_p1}")

    # P2 的后代：[]（P3 已删）
    descendants_p2 = get_parameter_descendants(p2.id)
    descendant_ids_p2 = [d["id"] for d in descendants_p2]
    assert descendant_ids_p2 == [], f"P2 descendants 错误: {descendant_ids_p2}"
    print(f"    [OK] P2 descendants = []（P3 已删）")

    # root P5（无 children）
    descendants_p5 = get_parameter_descendants(p5.id)
    assert descendants_p5 == [], f"P5 descendants 错误: {descendants_p5}"
    print(f"    [OK] P5 (leaf) descendants = []")

    # ============================================================================
    # Test 7: create_adjustment_version（手动版本）
    # ============================================================================
    print("\n[7] create_adjustment_version 验证:")
    # 当前 condition 内 parameter：P1(seq=1), P2(seq=2), P3(seq=3,已删), P4(seq=4), P5(seq=5), P6(seq=6)
    # 下一个 seq_idx = 6 + 1 = 7（model.save() 自动分配）
    condition_max_before = (
        ProcessParameter.objects.filter(
            process_condition_id=condition.id, is_deleted=False
        ).aggregate(Max("seq_idx"))["seq_idx__max"] or 0
    )

    new_p = create_adjustment_version(
        parent_param_id=p4.id,
        params={
            "inj_spd_1": 53.0,
            "inj_pres_1": 53.0,
            "param_source": "should_be_overwritten",  # 应被覆盖为 manual_adjusted
        },
        adjustment_note="测试手动调整",
    )
    assert new_p["parent_param_id"] == p4.id, f"parent_param_id 错误: {new_p['parent_param_id']}"
    assert new_p["process_condition_id"] == condition.id, "process_condition_id 错误"
    # seq_idx 由 model.save() 自动分配（condition 内 max + 1）
    assert new_p["seq_idx"] == condition_max_before + 1, (
        f"seq_idx 错误: {new_p['seq_idx']}（应为 {condition_max_before + 1}）"
    )
    assert new_p["param_source"] == "manual_adjusted", f"param_source 被覆盖: {new_p['param_source']}"
    assert new_p["inj_spd_1"] == 53.0, "inj_spd_1 未写入"
    print(
        f"    [OK] 创建新版本: id={new_p['id']}, parent={new_p['parent_param_id']}, "
        f"seq_idx={new_p['seq_idx']}, param_source={new_p['param_source']}"
    )

    # forbidden 字段过滤 + seq_idx 自动续号（model.save() 分配 max+1）
    new_p2 = create_adjustment_version(
        parent_param_id=p4.id,
        params={
            "inj_spd_1": 54.0,
            "parent_param_id": 999999,  # 应被过滤
            "process_condition_id": 999999,  # 应被过滤
            "seq_idx": 999,  # 应被过滤
            "id": 999999,  # 应被过滤
        },
    )
    assert new_p2["parent_param_id"] == p4.id, "parent_param_id 被篡改!"
    assert new_p2["process_condition_id"] == condition.id, "process_condition_id 被篡改!"
    # seq_idx 应是 condition_max_before + 2（new_p 已占用 +1）
    assert new_p2["seq_idx"] == condition_max_before + 2, (
        f"seq_idx 错误: {new_p2['seq_idx']}（应为 {condition_max_before + 2}）"
    )
    print(f"    [OK] forbidden 字段过滤 + seq_idx 自动续号: parent={new_p2['parent_param_id']}, seq_idx={new_p2['seq_idx']}")

    # 记录 id 用于清理
    created_parameter_ids.append(new_p["id"])
    created_parameter_ids.append(new_p2["id"])

    # ============================================================================
    # Test 8: revert_parameter（回退到历史版本）
    # ============================================================================
    print("\n[8] revert_parameter 验证:")
    # 回退到 P4（基于 P4 字段创建新版本，parent = condition 内当前最新）
    # 调用 revert 之前查 latest（new_p2），作为 service 应该采用的 parent
    expected_latest_id = (
        ProcessParameter.objects.filter(
            process_condition_id=condition.id, is_deleted=False
        ).order_by("-seq_idx", "-id").first().id
    )
    condition_max_before_revert = (
        ProcessParameter.objects.filter(
            process_condition_id=condition.id, is_deleted=False
        ).aggregate(Max("seq_idx"))["seq_idx__max"] or 0
    )
    reverted_p = revert_parameter(
        parameter_id=p4.id,
        note="回退到 P4",
    )
    assert reverted_p["process_condition_id"] == condition.id, "process_condition_id 错误"
    # parent 应是 condition 内当前最新 parameter（按 -seq_idx, -id 排序），
    # 即调用 revert 之前的最新（new_p2），不是 revert 自己生成的新 parameter
    assert reverted_p["parent_param_id"] == expected_latest_id, (
        f"parent_param_id 错误: {reverted_p['parent_param_id']}（应为 {expected_latest_id}）"
    )
    # seq_idx 由 model.save() 分配（condition 内 max + 1）
    assert reverted_p["seq_idx"] == condition_max_before_revert + 1, (
        f"seq_idx 错误: {reverted_p['seq_idx']}（应为 {condition_max_before_revert + 1}）"
    )
    assert reverted_p["param_source"] == "manual_adjusted", "param_source 错误"
    # 字段值应复制自 P4
    assert reverted_p["inj_spd_1"] == p4.inj_spd_1, f"inj_spd_1 应复制 P4: {reverted_p['inj_spd_1']} vs {p4.inj_spd_1}"
    assert reverted_p["inj_pres_1"] == p4.inj_pres_1, "inj_pres_1 应复制 P4"
    print(
        f"    [OK] revert_parameter: new_id={reverted_p['id']}, "
        f"parent={reverted_p['parent_param_id']}, seq_idx={reverted_p['seq_idx']}"
    )

    created_parameter_ids.append(reverted_p["id"])

    print("\n" + "=" * 70)
    print("All tests passed")
    print(f"parameter.py 暴露 8 个函数，全部行为符合预期")
    print("=" * 70)

finally:
    # ============================================================================
    # 清理 fixture
    # ============================================================================
    cleanup_fixtures()
    print("\n[fixture 清理完成]")