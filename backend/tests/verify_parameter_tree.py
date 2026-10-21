"""
verify_parameter_tree.py
验证 process/services/parameter.py 的真实 API：
- get_parameter：按 ID 取具体某一条（软删记录不可见）
- update_parameter：字段更新 + 业务身份锁（关系字段 / 版本序号 / 来源标记不可篡改）
- delete_parameter：删除叶节点 OK + 有子版本时拒绝
- get_parameter_tree：树形结构（嵌套 children）
- list_parameters：过滤 + 分页

2026-10-20 修复说明：
原测试按 backend/_refs/ 里的参考设计稿编写，引用了 4 个从未在服务层实现的函数
（get_parameter_lineage / get_parameter_descendants / create_adjustment_version /
revert_parameter）——它们只有本测试在引用，view / URL / 前端均无调用方。
按既定决策（改写测试对齐现有 API，不新增生产代码），本测试改为覆盖
services.parameter 实际导出的 5 个函数。

另：update_parameter 的调用形式按真实签名 update_parameter(id, {..dict..}) 改写
（原测试用的是 kwargs 形式 update_parameter(id, inj_pres_1=..)，与实现不符）。

fixture 设计：真实 DB（mold + polymer + condition + 6 个 parameter 构成版本树），
顶部清理 + finally 底部清理，测试期间数据不影响其他用例。

树形结构：
    P1 (seq=1, parent=None)
      ├── P2 (seq=2, parent=P1)
      │     └── P3 (seq=3, parent=P2)  [测试中会被软删]
      └── P4 (seq=4, parent=P1)
    P5 (seq=5, parent=None)             [算法初始化，无 children]
    P6 (seq=6, parent=None)             [孤立 root]
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
    list_parameters,
)


print("=" * 70)
print("parameter.py 服务验证：CRUD + 版本树查询")
print("=" * 70)


# ============================================================================
# Fixture 准备（真实 DB 操作，finally 保证清理）
# ============================================================================

mold = polymer = condition = None
created_parameter_ids = []  # 测试结束时统一软删


def setup_fixtures():
    """创建测试 fixture：mold + polymer + condition + 6 个 parameter（树形结构）

    注：ProcessParameter.save() 自动分配 seq_idx（max+1），
    故 fixture 创建顺序决定 seq_idx 严格递增：1, 2, 3, 4, 5, 6
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
        print("    [FAIL] 不存在的 id 应抛 BizException")
        sys.exit(1)
    except BizException as e:
        assert e.error_code == ERROR_DATA_NOT_FOUND, f"错误码不对: {e.error_code}"
        print(f"    [OK] 不存在 id 抛 BizException(DATA_NOT_FOUND): {e}")

    # ============================================================================
    # Test 2: update_parameter（字段更新 + 业务身份锁）
    # ============================================================================
    print("\n[2] update_parameter 验证:")
    # 合法字段更新（真实签名：update_parameter(parameter_id, {..dict..})）
    original_inj_pres_1 = p3.inj_pres_1
    updated = update_parameter(
        p3.id,
        {"inj_pres_1": original_inj_pres_1 + 5, "inj_spd_1": original_inj_pres_1 + 10},
    )
    assert updated["inj_pres_1"] == original_inj_pres_1 + 5, "inj_pres_1 未更新"
    assert updated["inj_spd_1"] == original_inj_pres_1 + 10, "inj_spd_1 未更新"
    print(f"    [OK] 合法字段更新成功: inj_pres_1={original_inj_pres_1} -> {updated['inj_pres_1']}")

    # 业务身份锁：受保护字段必须被拦截
    p3_fresh = ProcessParameter.objects.get(id=p3.id)
    original_parent = p3_fresh.parent_param_id
    original_seq = p3_fresh.seq_idx
    original_cond_id = p3_fresh.process_condition_id
    original_no = p3_fresh.parameter_no
    original_source = p3_fresh.param_source

    update_parameter(
        p3.id,
        {
            "inj_pres_1": 99.0,
            # 试图篡改关系/版本/来源字段（应被过滤）：
            "id": 999999,
            "process_condition_id": 999999,
            "parent_param_id": 999999,
            "seq_idx": 999,
            "parameter_no": "HACK",
            "param_source": "manual",
            "is_deleted": True,
        },
    )
    p3_after = ProcessParameter.objects.get(id=p3.id)
    assert p3_after.parent_param_id == original_parent, "parent_param_id 被篡改!"
    assert p3_after.seq_idx == original_seq, "seq_idx 被篡改!"
    assert p3_after.process_condition_id == original_cond_id, "process_condition_id 被篡改!"
    assert p3_after.parameter_no == original_no, "parameter_no 被篡改!"
    assert p3_after.param_source == original_source, "param_source 被篡改!"
    assert p3_after.is_deleted is False, "is_deleted 被篡改!"
    assert p3_after.inj_pres_1 == 99.0, "合法字段未更新"
    print("    [OK] 业务身份锁生效（parent/seq/cond_id/no/source/is_deleted 未变）")

    # 空 dict 应抛 BizException
    try:
        update_parameter(p3.id, {})
        print("    [FAIL] 空 dict 应抛 BizException")
        sys.exit(1)
    except BizException as e:
        assert e.error_code == ERROR_ILLEGAL_ARGUMENT, f"错误码不对: {e.error_code}"
        print(f"    [OK] 空 dict 抛 BizException(ILLEGAL_ARGUMENT)")

    # ============================================================================
    # Test 3: delete_parameter（叶节点 OK + 有子版本时拒绝）
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
    print("    [OK] 删除叶节点 P3 成功（is_deleted=True）")

    # 软删后 get_parameter 不应再返回该记录
    try:
        get_parameter(p3.id)
        print("    [FAIL] 已软删的 parameter 不应被 get_parameter 返回")
        sys.exit(1)
    except BizException as e:
        assert e.error_code == ERROR_DATA_NOT_FOUND, f"错误码不对: {e.error_code}"
        print("    [OK] 已软删的 parameter 对 get_parameter 不可见")

    # P1 有 children（P2, P4）—— 删除应被拒绝
    try:
        delete_parameter(p1.id)
        print("    [FAIL] 有 children 的 P1 应被拒绝删除")
        sys.exit(1)
    except BizException as e:
        assert e.error_code == ERROR_ILLEGAL_ARGUMENT, f"错误码不对: {e.error_code}"
        print(f"    [OK] 有 children 的 P1 删除被拒绝: {e}")

    # 不存在 ID
    try:
        delete_parameter(999999999)
        print("    [FAIL] 不存在的 id 应抛 BizException")
        sys.exit(1)
    except BizException as e:
        assert e.error_code == ERROR_DATA_NOT_FOUND, f"错误码不对: {e.error_code}"
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
    print("    [OK] P2.children = []（P3 已被软删）")

    # 不存在的 condition_id
    try:
        get_parameter_tree(999999999)
        print("    [FAIL] 不存在的 condition_id 应抛 BizException")
        sys.exit(1)
    except BizException as e:
        assert e.error_code == ERROR_DATA_NOT_FOUND, f"错误码不对: {e.error_code}"
        print(f"    [OK] 不存在 condition_id 抛 BizException: {e}")

    # ============================================================================
    # Test 5: list_parameters（过滤 + 分页）
    # ============================================================================
    print("\n[5] list_parameters 验证:")
    # 按 condition 过滤：应返回 5 条（P3 已软删）
    total, items = list_parameters(condition_id=condition.id)
    assert total == 5, f"total 错误: {total}（应为 5）"
    assert len(items) == 5, f"items 长度错误: {len(items)}"
    assert all(i["process_condition_id"] == condition.id for i in items), "condition 过滤失效"
    print(f"    [OK] 按 condition_id 过滤: total={total}, items={len(items)}")

    # 按 param_source 过滤
    total_src, items_src = list_parameters(
        condition_id=condition.id, param_source="ai_recommended"
    )
    assert total_src == 1, f"param_source 过滤错误: {total_src}（应为 1，仅 P2）"
    assert items_src[0]["id"] == p2.id, f"param_source 过滤结果错误: {items_src[0]['id']}"
    print(f"    [OK] 按 param_source 过滤: total={total_src}（P2）")

    # 分页
    total_pg, items_pg = list_parameters(condition_id=condition.id, page_no=1, page_size=2)
    assert total_pg == 5, f"分页 total 错误: {total_pg}"
    assert len(items_pg) == 2, f"分页 items 长度错误: {len(items_pg)}"
    print(f"    [OK] 分页: total={total_pg}, 本页 items={len(items_pg)}")

    # 不存在的 condition_id
    try:
        list_parameters(condition_id=999999999)
        print("    [FAIL] 不存在的 condition_id 应抛 BizException")
        sys.exit(1)
    except BizException as e:
        assert e.error_code == ERROR_DATA_NOT_FOUND, f"错误码不对: {e.error_code}"
        print(f"    [OK] 不存在 condition_id 抛 BizException: {e}")

    print("\n" + "=" * 70)
    print("All tests passed")
    print("parameter.py 暴露 5 个函数，全部行为符合预期")
    print("=" * 70)

finally:
    # ============================================================================
    # 清理 fixture
    # ============================================================================
    cleanup_fixtures()
    print("\n[fixture 清理完成]")
