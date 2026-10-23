"""论域接线体检：RuleKeyword.range vs 设备实际量程（2026-10-23）

回答三个问题：
  1. 哪些参数在【当前机台】上论域就不对（不换机台就已经错）
  2. 换机台后哪些参数的判定会变（跨机台一致性的实际影响面）
  3. 温度/时间类单独列出（旧版就没覆盖，需要另找基准）

只读脚本：不写库、不改数据。所有判级计算直接复刻现版 fuzzy_core 的分桶公式
（nets.py L93-102：gauss，σ=(hi-lo)/(2*(lvl-1))，means 等距）。

运行：cd backend; ../.venv/Scripts/python.exe _dev_refs/diag_fuzzy_domain_device.py
"""

import os
import sys

# 控制台默认 GBK：'⇒' 等符号会报 UnicodeEncodeError，用 errors='replace' 兑底
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
from django.db.models import Avg, Count, Max, Min

from masterdata.models import InjectionMoldingMachine, InjectionUnit
from process.models import ProcessParameter
from process.models.rules import RuleKeyword


# --------------------------------------------------------------------------
# 旧版 read_machine_setting_para 的映射（只换 max_val，不换 min_val）
# 设备字段名按现版 masterdata.InjectionUnit 校正：
#   旧版 max_set_holding_velocity  →  现版改名 max_set_holding_speed
# --------------------------------------------------------------------------
DEVICE_FIELD = {
    "IP0": "max_set_injection_pressure", "IP1": "max_set_injection_pressure",
    "IP2": "max_set_injection_pressure", "IP3": "max_set_injection_pressure",
    "IP4": "max_set_injection_pressure", "IP5": "max_set_injection_pressure",
    "IV0": "max_set_injection_speed", "IV1": "max_set_injection_speed",
    "IV2": "max_set_injection_speed", "IV3": "max_set_injection_speed",
    "IV4": "max_set_injection_speed", "IV5": "max_set_injection_speed",
    "IL0": "max_injection_stroke", "IL1": "max_injection_stroke",
    "IL2": "max_injection_stroke", "IL3": "max_injection_stroke",
    "IL4": "max_injection_stroke", "IL5": "max_injection_stroke",
    "PP0": "max_set_holding_pressure", "PP1": "max_set_holding_pressure",
    "PP2": "max_set_holding_pressure", "PP3": "max_set_holding_pressure",
    "PP4": "max_set_holding_pressure",
    "PV0": "max_set_holding_speed", "PV1": "max_set_holding_speed",
    "PV2": "max_set_holding_speed", "PV3": "max_set_holding_speed",
    "PV4": "max_set_holding_speed",
    "MP0": "max_set_metering_pressure", "MP1": "max_set_metering_pressure",
    "MP2": "max_set_metering_pressure", "MP3": "max_set_metering_pressure",
    "MBP0": "max_set_metering_back_pressure", "MBP1": "max_set_metering_back_pressure",
    "MBP2": "max_set_metering_back_pressure", "MBP3": "max_set_metering_back_pressure",
    "MSR0": "max_set_screw_rotation_speed", "MSR1": "max_set_screw_rotation_speed",
    "MSR2": "max_set_screw_rotation_speed", "MSR3": "max_set_screw_rotation_speed",
    "ML0": "max_injection_stroke", "ML1": "max_injection_stroke",
    "ML2": "max_injection_stroke", "ML3": "max_injection_stroke",
    "VPTL": "max_injection_stroke", "MEL": "max_injection_stroke",
}

# 算法参数名 → ProcessParameter 业务字段名（对齐 FuzzyEngine.FIELD_NAME_ALIAS）
def _build_algo_to_biz():
    m = {}
    for i in range(6):
        m[f"IV{i}"] = f"inj_spd_{i+1}"
        m[f"IP{i}"] = f"inj_pres_{i+1}"
        m[f"IL{i}"] = f"inj_pos_{i+1}"
    for i in range(5):
        m[f"PP{i}"] = f"hold_pres_{i+1}"
        m[f"PV{i}"] = f"hold_spd_{i+1}"
        m[f"PT{i}"] = f"hold_t_{i+1}"
    for i in range(4):
        m[f"MP{i}"] = f"met_pres_{i+1}"
        m[f"MBP{i}"] = f"met_back_pres_{i+1}"
        m[f"MSR{i}"] = f"met_rot_spd_{i+1}"
    for i in range(9):
        m[f"BT{i+1}"] = f"brl_temp_{i+1}"
    m["BT"] = "brl_temp_stg"
    m["NT"] = "noz_temp"
    return m


ALGO_TO_BIZ = _build_algo_to_biz()


def hr(title):
    print()
    print("=" * 96)
    print(title)
    print("=" * 96)


# --- 复刻现版 fuzzy_core 的分桶与隶属度（nets.py L93-102） ---
def buckets(lo, hi, lvl):
    """返回 (各档中心, σ)。σ 随论域线性缩放 ⇒ 论域越宽门控越钝。"""
    if hi <= lo:
        return [lo], 1.0
    step = (hi - lo) / (lvl - 1)
    means = [lo + i * step for i in range(lvl)]
    sigma = (hi - lo) / (2 * (lvl - 1))
    return means, sigma


def memberships(x, lo, hi, lvl):
    means, sigma = buckets(lo, hi, lvl)
    return [float(np.exp(-0.5 * ((x - m) / sigma) ** 2)) for m in means]


def dominant(x, lo, hi, lvl):
    mus = memberships(x, lo, hi, lvl)
    return int(np.argmax(mus)), max(mus)


def device_limits():
    """机台 → 设备上限。同一台机多射台取非空中的最大值。"""
    out = {}
    for machine in InjectionMoldingMachine.objects.all():
        limits = {}
        for unit in machine.injection_units.all():
            for fname in set(DEVICE_FIELD.values()):
                val = getattr(unit, fname, None)
                if val is None:
                    continue
                limits[fname] = max(limits.get(fname, 0.0), float(val))
        out[machine] = limits
    return out


def main():
    kws = {kw.keyword_name: kw for kw in RuleKeyword.objects.all()}
    machines = device_limits()
    pps = ProcessParameter.objects.all()

    hr("1. 数据源概览")
    print(f"  RuleKeyword      : {len(kws)} 条")
    print(f"  注塑机           : {len(machines)} 台")
    print(f"  ProcessParameter : {pps.count()} 条")
    covered = {k for k in kws if k in DEVICE_FIELD}
    print(f"  有设备基准的参数 : {len(covered)} / {len(kws)}"
          f"  （无基准 {len(kws) - len(covered)} 个）")

    # ---------------------------------------------------------------- 表 A
    hr("2. 表 A · 全库静态论域 vs 各机台设备量程（跨机台影响面）")
    print("  判定：一致=|比值-1|<5%；设备更小=论域偏大；设备更大=论域偏小")
    print()
    print(f"  {'参数':<7}{'设备字段':<28}{'论域上界':>9}{'设备上限':>9}"
          f"{'比值':>8}{'不一致机台':>11}  判定")
    print("  " + "-" * 92)

    table_a = {}
    for name in sorted(covered):
        kw = kws.get(name)
        if kw is None or kw.range_max in (None, 0):
            continue
        fname = DEVICE_FIELD[name]
        lo = float(kw.range_min or 0)
        hi = float(kw.range_max)
        ratios = []
        for machine, limits in machines.items():
            dv = limits.get(fname)
            if dv:
                ratios.append(dv / hi)
        if not ratios:
            continue
        r = np.array(ratios)
        n_bad = int(np.sum(np.abs(r - 1.0) >= 0.05))
        if n_bad == 0:
            verdict = "一致"
        elif r.mean() < 1.0:
            verdict = "设备更小（论域偏大）"
        else:
            verdict = "设备更大（论域偏小）"
        table_a[name] = (fname, lo, hi, r, n_bad, verdict)
        print(f"  {name:<7}{fname:<28}{hi:>9g}{hi * r.mean():>9.1f}"
              f"{r.mean():>8.2f}{n_bad:>6}/{len(ratios):<4}  {verdict}")

    print("  " + "-" * 92)
    print("  说明：'设备上限'列 = 各机台设备上限均值；'比值'列 = 设备上限均值 / 论域上界")

    # ---------------------------------------------------------------- 表 B
    hr("3. 表 B · 接线收益：真实值判级会不会改变")
    print("  取真实值分布 p10/p50/p90，分别在【现版论域】与【接入设备上限后】下算 dominant 档")
    print()
    print(f"  {'参数':<7}{'真实p10':>9}{'p50':>8}{'p90':>8}"
          f"{'现版档位(p50)':>16}{'接线后档位(p50)':>18}{'改变档数':>9}")
    print("  " + "-" * 82)

    changed_rows = []
    for name in sorted(table_a):
        kw = kws.get(name)
        biz = ALGO_TO_BIZ.get(name)
        if not biz:
            continue
        try:
            vals = [v for v in pps.values_list(biz, flat=True) if v is not None]
        except Exception:
            continue
        if len(vals) < 3:
            continue
        arr = np.array(vals, dtype=float)
        fname, lo, hi, r, n_bad, verdict = table_a[name]
        dev_hi = float(r.mean() * hi)
        lvl = int(kw.fuzzy_level or 3)
        p10, p50, p90 = np.percentile(arr, [10, 50, 90])

        old_buckets = set()
        new_buckets = set()
        for x in (p10, p50, p90):
            old_buckets.add(dominant(x, lo, hi, lvl)[0])
            new_buckets.add(dominant(x, lo, dev_hi, lvl)[0])
        n_changed = len(old_buckets ^ new_buckets)
        o50, _ = dominant(p50, lo, hi, lvl)
        n50, _ = dominant(p50, lo, dev_hi, lvl)
        if n_changed:
            changed_rows.append((name, n_changed))
        print(f"  {name:<7}{p10:>9.1f}{p50:>8.1f}{p90:>8.1f}"
              f"{f'L{o50}':>16}{f'L{n50}':>18}{n_changed:>9}")

    print("  " + "-" * 82)
    print(f"  判级会改变的参数 = {len(changed_rows)} / {len(table_a)}"
          f"   → {changed_rows if changed_rows else '无'}")

    # ---------------------------------------------------------------- 表 C
    hr("4. 表 C · 真实值分位落点（论域宽度是否合理）")
    print("  真实值区间在论域中占的百分比 —— 占比过小 = 门控迟钝（σ 随论域放大）")
    print()
    print(f"  {'参数':<7}{'业务字段':<18}{'论域':>16}{'真实[p10,p90]':>20}"
          f"{'占论域':>9}  判定")
    print("  " + "-" * 84)

    narrow = []
    for name in sorted(kws):
        kw = kws[name]
        biz = ALGO_TO_BIZ.get(name)
        if not biz or kw.range_max in (None, 0):
            continue
        try:
            vals = [v for v in pps.values_list(biz, flat=True) if v is not None]
        except Exception:
            continue
        if len(vals) < 3:
            continue
        arr = np.array(vals, dtype=float)
        lo, hi = float(kw.range_min or 0), float(kw.range_max)
        if hi <= lo:
            continue
        p10, p90 = np.percentile(arr, [10, 90])
        span = (p90 - p10) / (hi - lo) * 100
        if span < 40:
            verdict = "!! 门控迟钝"
            narrow.append(name)
        elif p90 > hi * 1.05 or p10 < lo * 0.95:
            verdict = "!! 真实值越界"
            narrow.append(name)
        else:
            verdict = ""
        print(f"  {name:<7}{biz:<18}{f'[{lo:g},{hi:g}]':>16}"
              f"{f'[{p10:g},{p90:g}]':>20}{span:>8.0f}%  {verdict}")

    print("  " + "-" * 84)
    print(f"  论域宽度不合理的参数 = {len(narrow)}   → {narrow if narrow else '无'}")

    # ---------------------------------------------------------------- 表 D
    hr("5. 表 D · 无设备基准的参数（旧版也没覆盖，需要另找基准）")
    no_dev = sorted(k for k in kws if k not in DEVICE_FIELD
                     and kws[k].category == 'parameter')
    print(f"  数量 = {len(no_dev)}（仅参数类；缺陷/缺陷位置类与论域议题无关，已剔除）")
    print()
    print(f"  {'参数':<7}{'lvl':>4}{'range_min':>11}{'range_max':>11}"
          f"{'业务字段':<18}{'真实p50':>10}  别名")
    print("  " + "-" * 96)
    for name in no_dev:
        kw = kws[name]
        biz = ALGO_TO_BIZ.get(name, "—")
        p50 = "—"
        if biz != "—":
            try:
                vals = [v for v in pps.values_list(biz, flat=True) if v is not None]
                if len(vals) >= 3:
                    p50 = f"{np.percentile(vals, 50):.1f}"
            except Exception:
                pass
        lo = kw.range_min if kw.range_min is not None else "—"
        hi = kw.range_max if kw.range_max is not None else "—"
        print(f"  {name:<7}{kw.fuzzy_level or 3:>4}{str(lo):>11}{str(hi):>11}"
              f"{biz:<18}{p50:>10}  {kw.keyword_alias or ''}")

    # ---------------------------------------------------------------- 表 E
    hr("6. 表 E · 同类语义组的论域一致性核对（同一物理量论域是否自相矛盾）")
    import re
    groups = {}
    for name, kw in kws.items():
        if kw.category != 'parameter':
            continue
        base = re.sub(r'\d+$', '', name)
        groups.setdefault(base, []).append(kw)

    inconsistent = []
    for base, items in sorted(groups.items()):
        if len(items) < 2:
            continue
        ranges = sorted({(float(i.range_min or 0), float(i.range_max or 0)) for i in items})
        if len(ranges) == 1:
            continue
        inconsistent.append((base, items, ranges))

    print(f"  语义组内论域不一致的组 = {len(inconsistent)}")
    print()
    for base, items, ranges in inconsistent:
        aliases = sorted({(i.keyword_alias or '') for i in items})
        print(f"  ● {base} 组（{len(items)} 个成员，别名：{aliases}）")
        for rng in ranges:
            members = sorted(i.keyword_name for i in items
                             if (float(i.range_min or 0), float(i.range_max or 0)) == rng)
            print(f"      论域 {str(rng):<16} ← {members}")
        print()

    # ---------------------------------------------------------------- 表 F
    hr("7. 表 F · BT 组逐段实测（验证 BT[0,50] vs BT1-9[150,350] 哪个对）")
    print(f"  {'参数':<7}{'业务字段':<18}{'论域':>16}{'真实p10':>10}{'p50':>8}"
          f"{'p90':>8}  判定")
    print("  " + "-" * 84)
    bt_rows = []
    for name in ["BT"] + [f"BT{i}" for i in range(1, 10)]:
        kw = kws.get(name)
        biz = ALGO_TO_BIZ.get(name)
        if not kw or not biz:
            continue
        try:
            vals = [v for v in pps.values_list(biz, flat=True) if v is not None]
        except Exception:
            continue
        if len(vals) < 3:
            print(f"  {name:<7}{biz:<18}{'（无数据）'}")
            continue
        arr = np.array(vals, dtype=float)
        lo, hi = float(kw.range_min or 0), float(kw.range_max)
        p10, p50, p90 = np.percentile(arr, [10, 50, 90])
        if p50 > hi * 1.05 or p50 < lo * 0.95:
            verdict = "!! 真实值越界（论域错）"
        elif (p90 - p10) / (hi - lo) < 0.4:
            verdict = "!! 门控迟钝"
        else:
            verdict = "OK"
        bt_rows.append((name, biz, lo, hi, p50, verdict))
        print(f"  {name:<7}{biz:<18}{f'[{lo:g},{hi:g}]':>16}{p10:>10.1f}"
              f"{p50:>8.1f}{p90:>8.1f}  {verdict}")
    print("  " + "-" * 84)

    # ---------------------------------------------------------------- 结论
    hr("8. 结论")
    n_a_changed = sum(1 for v in table_a.values() if v[4] > 0)
    print(f"  A 跨机台不一致的参数     : {n_a_changed} / {len(table_a)}")
    print(f"  B 接线后判级会变的参数   : {len(changed_rows)} / {len(table_a)}")
    print(f"    （注：分母 = 有设备基准且有真实值的参数；能算出真实值的共 {len(table_a)} 个中的一部分）")
    print(f"  C 论域宽度不合理的参数   : {len(narrow)}")
    print(f"  D 无设备基准的参数       : {len(no_dev)}")
    print(f"  E 语义组内论域不一致     : {len(inconsistent)}")
    print(f"  F BT 组越界成员          : "
          f"{[r[0] for r in bt_rows if '越界' in r[5]] or '无'}")
    print()
    print("  => '设备量程接入论域' 的实际影响面 = 上面 A/B 两项决定；")
    print("     C/D 两项是设备量程【解决不了】的部分，必须靠 (b) 实际运行区间。")

    print()
    print("=" * 96)
    print("论域接线体检结束（只读，未写库）")
    print("=" * 96)
    return 0


if __name__ == "__main__":
    sys.exit(main())
