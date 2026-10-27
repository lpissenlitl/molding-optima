"""正向映射「旧实现 vs 新契约」逐条对拍（2026-10-23）

回答一个问题：把 ``parameter_optimize._normalize_field_name_by_spec``
换成 ``field_names.to_algo_params`` 之后，**接口入参 → 算法 context** 这条路上的
字段名翻译结果有没有变？

参照系（独立于新实现）：
    legacy_normalize() —— 旧实现**原样冻结**在本文件里（含合并表查表口径），
    不从生产代码 import，避免"改了源头就没得比"。

只读脚本：不写库、不改数据。Django 只用于枚举 ProcessParameter 的字段名
（走 ``_meta``，不查库）。

运行：cd backend; ../.venv/Scripts/python.exe _dev_refs/_verify_naming_forward_parity.py
"""

import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

import django

django.setup()

from process.algorithms.fuzzy import field_names
from process.models import ProcessParameter


# ---------------------------------------------------------------------------
# 参照系：旧实现原样冻结（2026-10-23 之前 parameter_optimize 里的那份）
# ---------------------------------------------------------------------------
def legacy_normalize(params, field_spec, index_offset=None):
    """旧实现冻结版：完整字段名查合并表 + 前缀 + 数字后缀偏移。"""
    if not field_spec:
        return dict(params)

    index_offset = index_offset or {}

    normalized = {}
    for key, value in params.items():
        prefix, sep, suffix = key.rpartition('_')

        # 1) 完整字段名：noz_temp → NT
        if key in field_spec:
            normalized[field_spec[key]] = value
            continue

        # 2) 分段前缀 + 序号偏移：inj_spd_1 → IV0
        if sep and suffix.isdigit() and prefix in field_spec:
            offset = index_offset.get(prefix, 0)
            normalized[f"{field_spec[prefix]}{int(suffix) + offset}"] = value
            continue

        normalized[key] = value
    return normalized


def hr(title):
    print()
    print("=" * 92)
    print(title)
    print("=" * 92)


# ---------------------------------------------------------------------------
# 输入集合
# ---------------------------------------------------------------------------
def model_numeric_fields():
    """ProcessParameter 的数值字段名（走 _meta，不查库）。"""
    names = []
    for f in ProcessParameter._meta.get_fields():
        if f.get_internal_type() in ("FloatField", "IntegerField", "DecimalField"):
            names.append(f.name)
    return sorted(names)


def edge_cases():
    """边界输入：裸前缀 / 未知名 / 越界段号 / 空白 / 非字符串键。"""
    bare_prefixes = sorted(field_names.PREFIX_FIELD_ALIAS.keys())
    unknown = [
        "inj_stg", "hold_stg", "met_stg", "seq_idx", "parameter_no",
        "pre_met_decomp_1", "pst_met_decomp_1", "met_lim_t", "brl_temp_stg",
        "foo_bar", "inj_spd", "IV0",
    ]
    out_of_range = ["inj_spd_0", "inj_spd_10", "inj_spd_007", "brl_temp_10", "hold_t_0"]
    blanks = ["", "   ", " inj_spd_1 ", "inj_spd_1 ", "noz_temp"]
    return {
        "裸前缀(合并表命中)": bare_prefixes,
        "未知/业务控制字段": unknown,
        "越界段号": out_of_range,
        "空白与前后空格": blanks,
    }


# ---------------------------------------------------------------------------
# 对拍
# ---------------------------------------------------------------------------
def compare(label, keys):
    """逐键对拍：返回 (差异列表, 统计)。

    ⚠️ 比对方式：输入值即键名，所以按**值**反查输出键 ——
    直接用 old.get(k) 会把「改名」误判成「丢值」（旧实现把 inj_spd 改名成 IV，
    old.get('inj_spd') 必然是 None）。
    """
    params = {k: k for k in keys}
    old = legacy_normalize(
        params, field_names.FIELD_NAME_ALIAS, field_names.FIELD_INDEX_OFFSET
    )
    new = field_names.to_algo_params(params)

    def inverse(mapping):
        """值 → 输出键（值即原键名，故反查即得该键被改名成了什么）。"""
        return {v: k for k, v in mapping.items()}

    old_inv = inverse(old)
    new_inv = inverse(new)

    diffs = []
    for k in keys:
        o = old_inv.get(k)
        n = new_inv.get(k)
        if o != n:
            diffs.append((k, o, n))

    # 键集合差异（丢键 / 改名）
    old_only = sorted(set(old) - set(new))
    new_only = sorted(set(new) - set(old))

    return diffs, old_only, new_only


def main():
    hr("0. 对拍口径")
    print("  参照系：legacy_normalize()（旧实现冻结在本文件，用合并表 FIELD_NAME_ALIAS）")
    print("  被测对象：field_names.to_algo_params()（契约层新实现，用拆分表）")
    print(f"  合并表 {len(field_names.FIELD_NAME_ALIAS)} 条"
          f"（前缀 {len(field_names.PREFIX_FIELD_ALIAS)} + 完整 {len(field_names.FULL_FIELD_ALIAS)}）")

    total_diff = 0

    # --- 1) 模型全部数值字段 ---
    hr("1. ProcessParameter 全部数值字段（真实入参集合）")
    fields = model_numeric_fields()
    print(f"  字段数：{len(fields)}")
    diffs, old_only, new_only = compare("model", fields)
    print(f"  逐键差异：{len(diffs)}")
    for k, o, n in diffs:
        print(f"    {k:<28} 旧={o!s:<14} 新={n}")
    print(f"  仅旧实现有的键：{old_only or '无'}")
    print(f"  仅新实现有的键：{new_only or '无'}")
    total_diff += len(diffs) + len(old_only) + len(new_only)

    # --- 2) 边界输入 ---
    for label, keys in edge_cases().items():
        hr(f"2. 边界输入：{label}")
        diffs, old_only, new_only = compare(label, keys)
        print(f"  逐键差异：{len(diffs)}")
        for k, o, n in diffs:
            print(f"    {k:<28} 旧={o!s:<14} 新={n}")
        print(f"  仅旧实现有的键：{old_only or '无'}")
        print(f"  仅新实现有的键：{new_only or '无'}")
        total_diff += len(diffs) + len(old_only) + len(new_only)

    # --- 3) 非字符串键 ---
    hr("3. 非字符串键（健壮性）")
    for key in (None, 123, 4.5):
        try:
            old = legacy_normalize({key: "v"}, field_names.FIELD_NAME_ALIAS,
                                   field_names.FIELD_INDEX_OFFSET)
            old_res = f"OK -> {list(old)}"
        except Exception as e:
            old_res = f"抛错 {type(e).__name__}: {e}"
        try:
            new = field_names.to_algo_params({key: "v"})
            new_res = f"OK -> {list(new)}"
        except Exception as e:
            new_res = f"抛错 {type(e).__name__}: {e}"
        print(f"  key={key!r:<8} 旧={old_res:<44} 新={new_res}")

    # --- 4) 往返闭合（新契约自带的性质，旧实现没有） ---
    hr("4. 新契约往返闭合（正向 → 反向）")
    not_closed = []
    for k in model_numeric_fields():
        algo = field_names.to_algo_name(k)
        if not algo:
            continue
        back = field_names.to_business_name(algo)
        if back != k:
            not_closed.append((k, algo, back))
    print(f"  翻译字段数：{sum(1 for k in model_numeric_fields() if field_names.to_algo_name(k))}")
    print(f"  往返不闭合：{len(not_closed)}")
    for k, a, b in not_closed:
        print(f"    {k:<28} → {a:<10} → {b}")

    hr("结论")
    if total_diff == 0:
        print("  ✅ 真实入参集合与全部边界输入上，新旧实现逐键结果完全一致")
    else:
        print(f"  ⚠️ 共 {total_diff} 处差异（详见上方逐项）")
    print()


if __name__ == "__main__":
    main()
