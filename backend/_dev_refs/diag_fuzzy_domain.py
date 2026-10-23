"""论域体检：RuleKeyword 的 range 与真实工艺参数值对不对得上

2026-10-22

回答：BT/NT 的 range=[0,50] 而真实值 250，是数据问题还是单位问题？
以及「低/高」的基准到底能不能从现有数据里找出来。

运行：cd backend; ../.venv/Scripts/python.exe _dev_refs/diag_fuzzy_domain.py
"""

import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

import django

django.setup()

from django.db.models import Avg, Max, Min
from process.models import ProcessParameter
from process.models.rules import RuleKeyword


def hr(title):
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


# 算法侧参数名 → ProcessParameter 业务字段名（对齐 FuzzyEngine.FIELD_NAME_ALIAS）
ALGO_TO_BIZ = {
    "IV0": "inj_spd_1",
    "IV1": "inj_spd_2",
    "IV2": "inj_spd_3",
    "IP0": "hold_pres_1",
    "PP0": "hold_pres_2",
    "PV0": "hold_pres_3",
    "PV1": "hold_pres_4",
    "BT": "brl_temp_1",
    "NT": "noz_temp",
    "CT": "mold_temp",
    "MEL": "melt_temp",
    "MSR0": "mold_screw_sp",
    "MP0": "mold_press",
    "MBP0": "mold_back_press",
}


def main():
    hr("1. RuleKeyword 定义（前件参数）")
    print(f"  {'参数':<8}{'category':<16}{'lvl':>5}{'range_min':>12}"
          f"{'range_max':>12}{'step':>10}")
    print("  " + "-" * 66)
    for name in ["IV0", "IV1", "IP0", "PP0", "PV0", "BT", "NT", "CT",
                 "MEL", "MSR0", "MP0", "MBP0"]:
        kw = RuleKeyword.objects.filter(keyword_name=name).first()
        if kw is None:
            print(f"  {name:<8}(无 RuleKeyword)")
            continue
        print(f"  {name:<8}{str(getattr(kw, 'category', '')):<16}"
              f"{kw.fuzzy_level:>5}{kw.range_min:>12}{kw.range_max:>12}"
              f"{str(kw.step):>10}")

    hr("2. ProcessParameter 真实值的统计分布")
    print(f"  {'字段':<20}{'n':>6}{'min':>12}{'max':>12}{'avg':>12}")
    print("  " + "-" * 64)
    qs = ProcessParameter.objects.all()
    total = qs.count()
    stats = {}
    for algo, biz in sorted(ALGO_TO_BIZ.items()):
        try:
            agg = qs.aggregate(
                mn=Min(biz), mx=Max(biz), av=Avg(biz),
            )
        except Exception:
            continue
        if agg["mn"] is None:
            print(f"  {biz:<20}{'—':>6}{'（无数据）':>12}")
            continue
        stats[algo] = agg
        print(f"  {biz:<20}{total:>6}{agg['mn']:>12.1f}{agg['mx']:>12.1f}"
              f"{agg['av']:>12.1f}")

    hr("3. 逐参数：真实值 vs 论域")
    print(f"  {'参数':<8}{'业务字段':<18}{'range':>16}{'真实[min,max]':>20}"
          f"{'avg位置':>10}{'判定':>14}")
    print("  " + "-" * 88)
    out_cnt = 0
    check_cnt = 0
    for algo, biz in sorted(ALGO_TO_BIZ.items()):
        kw = RuleKeyword.objects.filter(keyword_name=algo).first()
        if kw is None or algo not in stats:
            continue
        lo, hi = float(kw.range_min), float(kw.range_max)
        mn, mx, av = stats[algo]["mn"], stats[algo]["mx"], stats[algo]["av"]
        if hi <= lo:
            continue
        check_cnt += 1
        pos = (av - lo) / (hi - lo) * 100
        if mx > hi * 1.2:
            verdict = "!! 论域严重偏小"
            out_cnt += 1
        elif mn < lo * 0.8:
            verdict = "!! 论域下界偏大"
            out_cnt += 1
        elif pos < 5 or pos > 95:
            verdict = "!! 平均值贴边"
            out_cnt += 1
        else:
            verdict = ""
        print(f"  {algo:<8}{biz:<18}{f'[{lo:g},{hi:g}]':>16}"
              f"{f'[{mn:g},{mx:g}]':>20}{pos:>9.0f}%{verdict:>14}")
    print("  " + "-" * 88)
    print(f"  论域明显失真的参数 = {out_cnt} / {check_cnt}")

    hr("4. 结论：BT / NT 的 5 倍差异是什么")
    for algo, biz in (("BT", "brl_temp_1"), ("NT", "noz_temp")):
        kw = RuleKeyword.objects.filter(keyword_name=algo).first()
        if kw is None or algo not in stats:
            continue
        lo, hi = float(kw.range_min), float(kw.range_max)
        mn, mx, av = stats[algo]["mn"], stats[algo]["mx"], stats[algo]["av"]
        print(f"  {algo} ({biz}):")
        print(f"    RuleKeyword 论域 = [{lo:g}, {hi:g}]")
        print(f"    真实值           = [{mn:g}, {mx:g}]，平均 {av:g}")
        print(f"    真实最大值 / 论域上界 = {mx / hi:.2f}×")
        if mx > hi * 1.2 and av > hi:
            print(f"    ⇒ 真实值整体在论域**之上**，论域不是『偏小』而是**完全错位**")
            print(f"      （若论域按真实数据重定为 [{mn:g}, {mx:g}]，平均值位置 = "
                  f"{(av - mn) / max(mx - mn, 1e-9) * 100:.0f}%，属正常区间）")
        elif mx > hi * 1.2:
            print(f"    ⇒ 真实最大值超出论域上界 {mx / hi:.1f}×，论域上界偏小")
        print()

    hr("5. 能否用『历史分位数』当基准？")
    print("  若走 Q2(c)『该产品 × 该材料的历史分位数』，需要：")
    print("    - 同一产品 × 材料下的多条工艺记录（分位数才有意义）")
    print("    - 每条记录绑定当时的缺陷反馈（否则分位数无工艺含义）")
    print()
    try:
        from process.models import ProcessParameter as PP
        fields = [f.name for f in PP._meta.get_fields()
                  if f.get_internal_type() in ("CharField", "ForeignKey")]
        print(f"  ProcessParameter 可见字段：{fields[:14]}")
    except Exception as exc:
        print(f"  （字段枚举失败：{exc}）")

    print()
    print("=" * 78)
    print("论域体检结束")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
