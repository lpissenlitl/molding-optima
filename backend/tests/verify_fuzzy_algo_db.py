"""
verify_fuzzy_algo_db.py

L2 层：连真实 DB 的 optimize 链路端到端验证
（模拟输入 → 跑真实算法 → 拿到可判定输出 → 断言业务落地性）

与 L1（verify_fuzzy_algo_offline.py）的分工：

| 层 | 依赖 | 钉住什么 |
|----|------|----------|
| L1 | 零 DB / 零 Django ORM / 零前端 | 「算法输入可模拟、算法理论可脱离前端独立运行」 |
| L2 | 真实规则库 + 真实 ORM | 「接上真数据后，产出仍满足业务落地性契约」 |

断言口径：**业务口径**（与前端消费方的契约一致），不引用被测实现内部函数。
参照系来源：frontend/src/views/process/optimization/components/parameterTransform.ts
（前端唯一的 flat → nested 翻译器）。

不落库：走 infer_from_provided（纯推理入口），DB 只读。
"""

import json
import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")
django.setup()

from process.models.condition import ProcessCondition  # noqa: E402
from process.services import parameter_optimize as opt  # noqa: E402
from process.services.parameter_optimize import (  # noqa: E402
    ParameterOptimizeService,
    _to_full_dict,
)

# 缺陷输入（业务口径：缺陷类型 + 程度 + 位置）
DEFECT_NAME = os.environ.get("MOULD_DEFECT", "SHORTSHOT")
DEFECT_LEVEL = os.environ.get("MOULD_LEVEL", "very_low")
DEFECT_POSITION = os.environ.get("MOULD_POSITION", "DLSHORTSHOT1")

# 前端表格的段位字段（parameterFromFlat 按这些 key 还原表格）
SEGMENT_FIELDS = (
    "inj_spd_1", "inj_spd_2", "inj_spd_3", "inj_spd_4", "inj_spd_5", "inj_spd_6",
    "inj_pres_1", "inj_pres_2", "inj_pres_3", "inj_pres_4", "inj_pres_5", "inj_pres_6",
    "inj_pos_1", "inj_pos_2", "inj_pos_3", "inj_pos_4", "inj_pos_5", "inj_pos_6",
    "hold_pres_1", "hold_spd_1", "hold_t_1",
    "met_pres_1", "met_rot_spd_1", "met_back_pres_1", "met_pos_1",
    "brl_temp_1", "brl_temp_2",
)

# nested 形态的数组字段名（flat 契约下**不应**出现）
NESTED_ARRAY_KEYS = (
    "inj_spd_steps", "inj_pres_steps", "inj_pos_steps",
    "hold_pres_steps", "hold_spd_steps", "hold_time_steps",
    "met_pres_steps", "met_rot_spd_steps", "met_back_pres_steps", "met_pos_steps",
    "brl_temp_steps",
)


def _pick_context():
    """挑一个可用的工艺条件：优先 MOULD_CONDITION_ID，否则取最新的有参数的 condition"""
    cid = os.environ.get("MOULD_CONDITION_ID")
    queryset = ProcessCondition.objects.select_related(
        "injection_machine", "polymer", "mold"
    )
    if cid:
        condition = queryset.filter(id=int(cid)).first()
    else:
        condition = queryset.filter(process_parameters__isnull=False).order_by("-id").first()
    if condition is None:
        raise SystemExit("找不到可用的工艺条件（DB 无 process_parameters）")
    parent = condition.process_parameters.order_by("-seq_idx").first()
    if parent is None:
        raise SystemExit(f"condition id={condition.id} 下没有 process_parameters")
    return condition, parent


def _run(condition, parent, position):
    """走一遍 optimize 纯推理（不落库），返回 (result, baseline)"""
    feedback = {
        "defect": [
            {
                "keyword_name": DEFECT_NAME,
                "level": DEFECT_LEVEL,
                "position": position,
            }
        ]
    }
    baseline = _to_full_dict(parent)
    result = ParameterOptimizeService().infer_from_provided(
        parameter=baseline,
        feedback=feedback,
        mold_info=opt._extract_mold_info(condition),
        machine_info=opt._extract_machine_info(condition),
        polymer_info=opt._extract_polymer_info(condition),
    )
    return result, baseline


def main():
    print("=" * 70)
    print("optimize 链路端到端验证（L2：连真实 DB，不落库）")
    print("=" * 70)

    condition, parent = _pick_context()
    print(f"上下文: condition_id={condition.id} parent_seq_idx={parent.seq_idx} "
          f"defect={DEFECT_NAME}/{DEFECT_LEVEL}/{DEFECT_POSITION}")

    result, baseline = _run(condition, parent, DEFECT_POSITION)

    # ---- D1 真实规则库能产出推荐 ----
    groups = (result.get("suggestion") or {}).get("groups") or []
    items = [it for g in groups for it in (g.get("items") or [])]
    assert items, "真实规则库未产出任何推荐（suggestion.groups 为空）"
    print(f"[D1] 产出推荐 {len(items)} 条 OK")

    # ---- D2 推荐真的落地到 baseline 的业务字段 ----
    new_parameter = result.get("new_parameter") or {}
    changed = {
        k: (baseline.get(k), new_parameter.get(k))
        for k in baseline
        if k in new_parameter and baseline.get(k) != new_parameter.get(k)
    }
    assert changed, "推荐未改变 baseline 的任何字段 ⇒ 推荐没落地到可写回的业务字段"
    for key, (old, new) in changed.items():
        print(f"       · {key}: {old} → {new}")
    print(f"[D2] 推荐落地 {len(changed)} 个 baseline 业务字段 OK")

    # ---- D3 new_parameter 是 flat 形态 ----
    for nested_key in NESTED_ARRAY_KEYS:
        assert nested_key not in new_parameter, f"new_parameter 不应含 nested 数组字段 {nested_key}"
    missing = [f for f in SEGMENT_FIELDS if f not in new_parameter]
    assert not missing, f"new_parameter 缺段位字段（前端表格无法还原）: {missing}"
    print(f"[D3] new_parameter 为 flat 且含 {len(SEGMENT_FIELDS)} 个段位字段 OK")

    # ---- D4 表格关键格子有值（前端空白问题的直接判据） ----
    inj_spd_1 = new_parameter.get("inj_spd_1")
    assert inj_spd_1 is not None, "inj_spd_1 无值 ⇒ 前端「注射速度 一段」格子会是空的"
    print(f"[D4] 注射速度一段 inj_spd_1 = {inj_spd_1}（前端表格该格非空）OK")

    # ---- D5 置信度域 ----
    for it in items:
        conf = it.get("confidence")
        if conf is None:
            continue
        assert 0 < float(conf) <= 1.0, f"置信度越界: {conf}"
    print("[D5] 置信度均在 (0, 1] OK")

    # ---- D6 位置条件不影响产出（已知实现现状，钉住不漂移） ----
    result_alt, _ = _run(condition, parent, "浇口附近")
    np_alt = result_alt.get("new_parameter") or {}
    assert np_alt == new_parameter, "不同 position 产出的 new_parameter 不一致（位置条件已生效？）"
    print("[D6] 不同 position 产出逐位相同（位置条件无效 —— 已知现状，已钉住）")

    # ---- D7 落盘 flat 供前端真代码验证 ----
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_flat_out.json")
    with open(out_path, "w", encoding="utf-8") as fp:
        json.dump(new_parameter, fp, ensure_ascii=False, indent=2, default=str)
    print(f"[D7] flat 已写出 {out_path}（供前端 parameterFromFlat 验证）")

    print("\n=== verify_fuzzy_algo_db PASSED ===")
    return True


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
