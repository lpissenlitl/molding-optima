"""可分档性体检：参数到底能不能区分「低/中/高」（2026-10-23）

回答用户的判断——「这几个参数也很难区分低中高」——到底成立不成立。

关键区分两种退化：
  (i)  样本退化：取值本身就集中在极少的几个值  ⇒ 数据问题
  (ii) 论域退化：取值分布正常，但被论域钳在一侧 ⇒ 论域问题

只读脚本：不写库、不改数据。判档复刻 fuzzy_core 分桶公式（nets.py L93-102）。

运行：cd backend; ../.venv/Scripts/python.exe _dev_refs/diag_fuzzy_separability.py
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


def bucket_of(x, lo, hi, lvl):
    """返回该值所属桶的下标（按最近的桶中心判定，与 argmax 隶属度等价）。"""
    means, _ = buckets(lo, hi, lvl)
    return int(np.argmin([abs(x - m) for m in means]))


def main():
    pps = list(ProcessParameter.objects.all())
    kws = {kw.keyword_name: kw for kw in RuleKeyword.objects.all()}

    hr("1. 样本多样性（决定 (b) 实际运行区间能不能建起来）")
    print(f"  ProcessParameter 样本数 = {len(pps)}")
    fks = [f.name for f in ProcessParameter._meta.get_fields()
           if f.get_internal_type() == "ForeignKey"]
    for name in fks:
        vals = {getattr(p, f"{name}_id", None) for p in pps}
        vals.discard(None)
        print(f"  {name:<22}: {len(vals)} 个不同值")
    combos = {(getattr(p, "polymer_id", None), getattr(p, "mold_id", None),
               getattr(p, "injection_machine_id", None)) for p in pps}
    print(f"  『材料×模具×机台』组合数 : {len(combos)}")
    print()
    print("  => (b)『分产品 × 材料的实际运行区间』要求每组有足够样本；")
    print("     组合数少 ⇒ 分位数不稳定 ⇒ 不能直接用分位数定论域。")

    # ---------------------------------------------------- 归一化实际取值
    recs = []
    for pp in pps:
        raw = {f.name: getattr(pp, f.name, None)
               for f in ProcessParameter._meta.get_fields()
               if f.get_internal_type() in ("FloatField", "IntegerField", "DecimalField")}
        raw = {k: v for k, v in raw.items() if v is not None}
        if raw:
            recs.append(_normalize_field_name_by_spec(
                raw,
                FuzzyEngine.FIELD_NAME_ALIAS,
                FuzzyEngine.FIELD_INDEX_OFFSET,
                FuzzyEngine.FAMILY_FIELD_ALIAS,
            ))

    hr("2. 参数取值分布（样本退化检查）")
    focus = ["IV0", "IV1", "IV2", "IP0", "PP0", "PP1", "PV0", "PV1", "MBP0",
             "MP0", "MSR0", "IT", "BT", "BT2", "NT", "PT0", "PT1", "MEL",
             "VPTL", "CT", "IL0", "IL2"]
    print(f"  {'参数':<7}{'样本':>6}{'不同值':>8}{'最小':>9}{'最大':>9}"
          f"{'跨度':>9}  取值集合")
    print("  " + "-" * 96)
    dist = {}
    for name in focus:
        vals = [r[name] for r in recs if name in r]
        if not vals:
            continue
        arr = np.array(vals, dtype=float)
        uniq = sorted(set(arr.tolist()))
        dist[name] = arr
        show = uniq[:6] + (["…"] if len(uniq) > 6 else [])
        print(f"  {name:<7}{len(arr):>6}{len(uniq):>8}{arr.min():>9.1f}"
              f"{arr.max():>9.1f}{arr.max() - arr.min():>9.1f}  {show}")

    # ---------------------------------------------------- 可分档性
    hr("3. 可分档性：当前论域 vs『贴合真实分布』论域（3 档）")
    print("  有效档 = 该档样本占比 ≥10%；有效档数=1 ⇒ 门控无区分度")
    print()
    print(f"  {'参数':<7}{'当前论域':>15}{'当前有效档':>12}{'当前分布':>22}"
          f"{'贴合论域':>15}{'贴合有效档':>12}{'贴合分布':>20}")
    print("  " + "-" * 100)

    rows = []
    for name in sorted(dist):
        arr = dist[name]
        kw = kws.get(name)
        if kw is None or kw.range_max in (None, 0):
            continue
        lvl = int(kw.fuzzy_level or 3)
        lo, hi = float(kw.range_min or 0), float(kw.range_max)
        if hi <= lo:
            continue

        cur = collections.Counter(bucket_of(x, lo, hi, lvl) for x in arr)
        cur_eff = sum(1 for v in cur.values() if v / len(arr) >= 0.10)

        tlo, thi = float(arr.min()), float(arr.max())
        if thi - tlo < 1e-9:
            thi = tlo + 1.0
        new = collections.Counter(bucket_of(x, tlo, thi, lvl) for x in arr)
        new_eff = sum(1 for v in new.values() if v / len(arr) >= 0.10)

        def fmt(c):
            return " ".join(f"L{k}:{v * 100 // len(arr)}%" for k, v in sorted(c.items()))

        rows.append((name, cur_eff, new_eff, len(set(arr.tolist()))))
        print(f"  {name:<7}{f'[{lo:g},{hi:g}]':>15}{cur_eff:>12}{fmt(cur):>22}"
              f"{f'[{tlo:g},{thi:g}]':>15}{new_eff:>12}{fmt(new):>20}")

    print("  " + "-" * 100)

    hr("4. 结论")
    deg = [r for r in rows if r[3] <= 2]
    print(f"  取值只有 ≤2 个不同值的参数（样本退化）: "
          f"{[r[0] for r in deg] or '无'}")
    one_cur = [r[0] for r in rows if r[1] == 1]
    one_new = [r[0] for r in rows if r[2] == 1]
    print(f"  当前论域下有效档=1（无区分度）: {one_cur or '无'}")
    print(f"  贴合论域后仍有效档=1      : {one_new or '无'}")
    fixed = [r[0] for r in rows if r[1] == 1 and r[2] > 1]
    print(f"  改论域即可恢复区分度的参数  : {fixed or '无'}")
    print()
    print("  => 『难区分低中高』的两种成因要分开处理：")
    print("     (i)  样本退化（取值就那么几个）=> 需要更多真实数据，算法改不了")
    print("     (ii) 论域退化（分布正常但被钳住）=> 改论域即可，属于本次重构要解决的")
    
    # ---------------------------------------------------- 全量离散度
    hr("5. 全量参数的取值离散度（是否为『档位型』参数）")
    print("  离散度 = 该参数在样本中出现的不同取值个数")
    print("  取值越少 => 越像『工艺档位』而非连续量 => 连续区间分档天然对不齐")
    print()
    info = []
    for name in sorted({k for r in recs for k in r}):
        vals = [r[name] for r in recs if name in r]
        if len(vals) < 5:
            continue
        c = collections.Counter(vals)
        top = c.most_common(1)[0]
        info.append((len(c), name, len(vals), top[1] / len(vals)))
    info.sort()
    print(f"  {'参数':<10}{'样本':>6}{'不同值':>8}{'众数占比':>10}")
    print("  " + "-" * 40)
    for d, name, n, ratio in info:
        print(f"  {name:<10}{n:>6}{d:>8}{ratio * 100:>9.0f}%")
    print("  " + "-" * 40)
    buckets = collections.Counter(d for d, _, _, _ in info)
    print(f"  不同值个数分布: {dict(sorted(buckets.items()))}")
    le6 = [x for x in info if x[0] <= 6]
    print(f"  不同值 <=6 个的参数: {len(le6)}/{len(info)} "
          f"({len(le6) * 100 // max(len(info), 1)}%)")
    print(f"  其中众数占比 >=70% 的（分布极偏，无法分档）: "
          f"{[x[1] for x in info if x[3] >= 0.70]}")
    
    # ---------------------------------------------------- IF/THEN 角色错配
    hr("6. 参数的『角色』：作前件条件 还是 被调整对象")
    print("  IF 侧 = 当前值处于什么档位（需要可分档才有意义）")
    print("  THEN 侧 = 往哪个方向调、调多少（只需可调，不需可分档）")
    print()
    rules = list(
        RuleMethod.objects.filter(is_deleted=False).filter(is_active=True)
        .values_list("rule_description", flat=True)
    )
    rule_re = re.compile(r"^IF\s+(.+?)\s+THEN\s+(.+)$", re.S)
    pre_cnt, then_cnt = collections.Counter(), collections.Counter()
    for desc in rules:
        m = rule_re.match(desc.strip())
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
    
    def base_of(name, kind):
        pat = r"_(low|high|medium|mid|worse|adjust.*)$" if kind == "pre" \
            else r"_(add|reduce|adjust).*$"
        return re.sub(pat, "", name)
    
    pre_by_base = collections.Counter()
    then_by_base = collections.Counter()
    for k, v in pre_cnt.items():
        pre_by_base[base_of(k, "pre")] += v
    for k, v in then_cnt.items():
        then_by_base[base_of(k, "then")] += v
    
    no_sep = {r[0] for r in rows if r[2] == 1}
    print(f"  {'参数':<10}{'IF门控':>8}{'THEN调整':>10}{'  判定'}")
    print("  " + "-" * 56)
    mismatch = []
    for name in sorted(set(pre_by_base) | set(then_by_base)):
        p, t = pre_by_base.get(name, 0), then_by_base.get(name, 0)
        if p == 0:
            continue
        if name in no_sep:
            verdict = "★ 当条件用但分不出档"
            mismatch.append((name, p, t))
        else:
            verdict = ""
        print(f"  {name:<10}{p:>8}{t:>10}  {verdict}")
    print("  " + "-" * 56)
    print(f"  合计：{len(mismatch)} 个参数被当作前件条件使用，但样本下无法分档")
    for name, p, t in mismatch:
        print(f"    · {name:<8} IF {p:>4} 条 / THEN {t:>4} 条")
    print()
    print("  => 这类参数的正确角色是【被调整对象】，把它们当前件门控是结构错配。")
    
    # ---------------------------------------------------- 取界方式对比
    hr("7. 论域取界方式对比（『数据越精准越有效』的操作化）")
    print("  方式 A 现版静态论域 : RuleKeyword.range（种子默认值）")
    print("  方式 B 贴 min/max   : [实验值最小, 实验值最大]")
    print("  方式 C 取值集合切   : 实验值去重排序，相邻取值中点为桶边界")
    print("  指标：最大档占比（越小越均匀）、归一化熵 H/log(k)（1=完全均匀）")
    print()
    print(f"  {'参数':<7}{'A静态':>16}{'B min/max':>16}{'C 取值集合':>18}")
    print(f"  {'':<7}{'熵  最大档':>16}{'熵  最大档':>16}{'熵  最大档  桶数':>18}")
    print("  " + "-" * 72)

    def entropy(counts):
        tot = sum(counts)
        if tot == 0 or len(counts) <= 1:
            return 0.0
        h = 0.0
        for c in counts:
            if c > 0:
                p = c / tot
                h -= p * np.log(p)
        return float(h / np.log(len(counts)))

    cmp_rows = []
    for name in sorted(dist):
        arr = dist[name]
        kw = kws.get(name)
        if kw is None or kw.range_max in (None, 0):
            continue
        lvl = int(kw.fuzzy_level or 3)
        lo, hi = float(kw.range_min or 0), float(kw.range_max)
        if hi <= lo:
            continue

        def stats(bounds):
            counts = []
            for x in arr:
                idx = int(np.clip(np.searchsorted(bounds, x, side="right") - 1,
                                  0, len(bounds) - 2))
                counts.append(idx)
            c = collections.Counter(counts)
            ordered = [c.get(i, 0) for i in range(len(bounds) - 1)]
            return entropy(ordered), max(ordered) / len(arr) if ordered else 1.0

        # A：静态
        if lvl > 1:
            step = (hi - lo) / (lvl - 1)
            a_bounds = [lo + i * step for i in range(lvl)]
        else:
            a_bounds = [lo, hi]
        ea, ma = stats(a_bounds)

        # B：min/max
        tlo, thi = float(arr.min()), float(arr.max())
        if thi - tlo < 1e-9:
            thi = tlo + 1.0
        b_bounds = [tlo + i * (thi - tlo) / (lvl - 1) for i in range(lvl)]
        eb, mb = stats(b_bounds)

        # C：取值集合中点切
        uniq = sorted(set(arr.tolist()))
        if len(uniq) >= 2:
            c_bounds = [uniq[0]] + [(uniq[i] + uniq[i + 1]) / 2
                                    for i in range(len(uniq) - 1)] + [uniq[-1]]
            ec, mc = stats(c_bounds)
            nk = len(uniq)
        else:
            ec, mc, nk = 0.0, 1.0, 1

        cmp_rows.append((name, ea, ma, eb, mb, ec, mc, nk))
        print(f"  {name:<7}{ea:>8.2f}{ma * 100:>7.0f}%{eb:>8.2f}{mb * 100:>7.0f}%"
              f"{ec:>8.2f}{mc * 100:>7.0f}%{nk:>11}")

    print("  " + "-" * 72)
    better = [r for r in cmp_rows if r[5] > r[1] + 0.05]
    print(f"  方式 C 明显优于方式 A（熵提升 >0.05）的参数: "
          f"{len(better)}/{len(cmp_rows)}")
    print(f"  方式 C 平均最大档占比: "
          f"{np.mean([r[6] for r in cmp_rows]) * 100:.0f}%  vs  "
          f"方式 A: {np.mean([r[2] for r in cmp_rows]) * 100:.0f}%  vs  "
          f"方式 B: {np.mean([r[4] for r in cmp_rows]) * 100:.0f}%")
    print()
    print("  => 结论：论域边界取『实验取值集合的中点』，判档才能对齐真实档位；")
    print("     只贴 min/max 对离散取值仍然不均匀（众数独占一档）。")

    print()
    print("=" * 100)
    print("可分档性体检结束（只读，未写库）")
    print("=" * 100)
    return 0


if __name__ == "__main__":
    sys.exit(main())
