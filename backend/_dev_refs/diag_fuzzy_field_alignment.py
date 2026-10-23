"""规则参数 ↔ 引擎取值 ↔ 论域 的端到端对齐体检（2026-10-23）

回答：哪些参数的【论域问题真正在伤规则】。

背景：前面的体检（diag_fuzzy_domain_device.py）只比对了「RuleKeyword 论域 vs 真实值」，
但没有走一遍【规则参数名 → 引擎实际拿到的值 → 判档】这条完整链路。
本脚本跑通全链路，找出「门控恒定失效」的参数。

只读脚本：不写库、不改数据。判级复刻 fuzzy_core 分桶公式（nets.py L93-102）。

运行：cd backend; ../.venv/Scripts/python.exe _dev_refs/diag_fuzzy_field_alignment.py
"""

import collections
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="gbk", errors="replace")
except Exception:
    pass

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

import django

django.setup()

import numpy as np

from process.algorithms.fuzzy.fuzzy_algorithm import FuzzyEngine
from process.models import ProcessParameter
from process.models.rules import RuleKeyword, RuleMethod
from process.services.parameter_optimize import _normalize_field_name_by_spec


def hr(title):
    print()
    print("=" * 100)
    print(title)
    print("=" * 100)


def buckets(lo, hi, lvl):
    if hi <= lo:
        return [lo], 1.0
    step = (hi - lo) / (lvl - 1)
    return [lo + i * step for i in range(lvl)], (hi - lo) / (2 * (lvl - 1))


def dominant(x, lo, hi, lvl):
    means, sigma = buckets(lo, hi, lvl)
    mus = [float(np.exp(-0.5 * ((x - m) / sigma) ** 2)) for m in means]
    return int(np.argmax(mus)), max(mus)


RULE_RE = re.compile(r'^IF\s+(.+?)\s+THEN\s+(.+)$', re.S)


def main():
    rules = list(
        RuleMethod.objects.filter(is_deleted=False).filter(is_active=True)
        .values_list("rule_description", flat=True)
    )
    kws = {kw.keyword_name: kw for kw in RuleKeyword.objects.all()}

    # ---------------------------------------------------- 规则参数使用频次
    pre_cnt = collections.Counter()
    then_cnt = collections.Counter()
    for desc in rules:
        m = RULE_RE.match(desc.strip())
        if not m:
            continue
        for part in m.group(1).split(" AND "):
            t = part.split()
            if t:
                pre_cnt[t[0]] += 1
        for part in m.group(2).split(" AND "):
            t = part.split()
            if t:
                then_cnt[t[0]] += 1

    hr("1. 规则参数使用频次（按参数聚合，IF=前件门控 / THEN=调整对象）")
    usage = collections.Counter()
    for name, c in pre_cnt.items():
        base = re.sub(r'_(low|high|medium|mid|worse|adjust.*)$', '', name)
        usage[base] += c
    for name, c in then_cnt.items():
        base = re.sub(r'_(add|reduce|adjust).*$', '', name)
        usage[base] += c

    print(f"  {'参数':<10}{'IF门控':>8}{'THEN调整':>10}{'合计':>8}  备注")
    print("  " + "-" * 70)
    for base, total in usage.most_common(24):
        p = sum(v for k, v in pre_cnt.items()
                if re.sub(r'_(low|high|medium|mid|worse|adjust.*)$', '', k) == base)
        t = sum(v for k, v in then_cnt.items()
                if re.sub(r'_(add|reduce|adjust).*$', '', k) == base)
        note = ""
        if p + t >= 100:
            note = "★ 高频（论域错则大面积失真）"
        print(f"  {base:<10}{p:>8}{t:>10}{total:>8}  {note}")

    # ---------------------------------------------------- 引擎实际取值
    hr("2. 引擎实际拿到的值（跑一遍 _normalize_field_name_by_spec）")
    pps = list(ProcessParameter.objects.all())
    normalized = []
    for pp in pps:
        raw = {f.name: getattr(pp, f.name, None)
               for f in ProcessParameter._meta.get_fields()
               if f.get_internal_type() in ("FloatField", "IntegerField", "DecimalField")}
        raw = {k: v for k, v in raw.items() if v is not None}
        if not raw:
            continue
        normalized.append(_normalize_field_name_by_spec(
            raw,
            FuzzyEngine.FIELD_NAME_ALIAS,
            FuzzyEngine.FIELD_INDEX_OFFSET,
            FuzzyEngine.FAMILY_FIELD_ALIAS,
        ))

    focus = ["BT", "BT1", "BT2", "CT", "NT", "MEL", "PT0", "PT1", "IL0", "IL2",
             "IV0", "IP0", "PP0", "PV0", "MSR0", "MBP0", "MP0", "IT", "VPTL"]
    print(f"  {'算法名':<8}{'反查业务字段':<20}{'样本数':>7}{'p10':>10}{'p50':>10}"
          f"{'p90':>10}")
    print("  " + "-" * 76)
    real_dist = {}
    for name in focus:
        vals = [rec[name] for rec in normalized if name in rec]
        biz = FuzzyEngine.to_business_name(name) or "（无对应业务字段）"
        if not vals:
            print(f"  {name:<8}{biz:<20}{0:>7}   —— 引擎取不到该参数 ——")
            continue
        arr = np.array(vals, dtype=float)
        p10, p50, p90 = np.percentile(arr, [10, 50, 90])
        real_dist[name] = (arr, biz)
        print(f"  {name:<8}{biz:<20}{len(vals):>7}{p10:>10.1f}{p50:>10.1f}{p90:>10.1f}")

    # ---------------------------------------------------- 门控失效参数
    hr("3. 门控失效体检（真实值 vs 论域 ⇒ 某一档是否恒真）")
    print("  恒定高档 = 真实值恒在上界之上 ⇒ 前件的 low/medium 永不命中")
    print("  恒定低档 = 真实值恒在下界之下 ⇒ 前件的 high 永不命中")
    print()
    print(f"  {'参数':<8}{'论域':>16}{'真实p50':>10}{'越界%':>8}{'判定档':>8}"
          f"{'门控状态':<16}{'IF引用':>8}{'THEN引用':>9}")
    print("  " + "-" * 88)

    broken = []
    for name, (arr, biz) in sorted(real_dist.items()):
        kw = kws.get(name)
        if kw is None or kw.range_max in (None, 0):
            continue
        lo, hi = float(kw.range_min or 0), float(kw.range_max)
        if hi <= lo:
            continue
        lvl = int(kw.fuzzy_level or 3)
        p50 = float(np.percentile(arr, 50))
        out_ratio = float(np.mean((arr < lo) | (arr > hi)) * 100)
        dom, _ = dominant(p50, lo, hi, lvl)

        if out_ratio >= 90:
            state = "★ 恒定越界"
            broken.append((name, "恒定越界", out_ratio))
        elif out_ratio >= 30:
            state = "部分越界"
        else:
            state = "正常"
        p = sum(v for k, v in pre_cnt.items()
                if re.sub(r'_(low|high|medium|mid|worse|adjust.*)$', '', k) == name)
        t = sum(v for k, v in then_cnt.items()
                if re.sub(r'_(add|reduce|adjust).*$', '', k) == name)
        print(f"  {name:<8}{f'[{lo:g},{hi:g}]':>16}{p50:>10.1f}{out_ratio:>7.0f}%"
              f"{f'L{dom}':>8}{state:<16}{p:>8}{t:>9}")

    print("  " + "-" * 88)
    print("  门控恒定失效的参数：")
    for name, kind, ratio in broken:
        p = sum(v for k, v in pre_cnt.items()
                if re.sub(r'_(low|high|medium|mid|worse|adjust.*)$', '', k) == name)
        print(f"    · {name}（{kind} {ratio:.0f}%）→ 影响 {p} 条规则的前件门控")

    hr("4. 结论")
    print(f"  规则总数                 : {len(rules)}")
    print(f"  涉及算法参数             : {len(usage)}")
    print(f"  高频参数（IF+THEN≥100）  : "
          f"{[k for k, v in usage.items() if v >= 100]}")
    print(f"  门控恒定失效的参数       : {[b[0] for b in broken] or '无'}")
    print()
    print("  => 论域问题的实际危害面 = 上面『高频』×『门控失效』的交集")

    print()
    print("=" * 100)
    print("端到端对齐体检结束（只读，未写库）")
    print("=" * 100)
    return 0


if __name__ == "__main__":
    sys.exit(main())
