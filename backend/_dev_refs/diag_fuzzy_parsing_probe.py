"""词法层探针：把 split_phase / collect_param_names 的实际行为摊开看。

用途：规划阶段确认「词法层」到底有多少种真实 token 形态、当前解析对不对。
只读脚本。
"""
import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

import django  # noqa: E402

django.setup()

from process.algorithms.fuzzy.fuzzy_core.parsing import (  # noqa: E402
    collect_param_names,
    split_phase,
)

TOKENS = [
    'IV0_very_low', 'IV0_extremely_low', 'IV0_slightly_low', 'IV0_ultra_low',
    'IV0_low', 'IV0_medium', 'IV0_mid', 'IV0_high', 'IV0_very_high',
    'IV0_level3', 'IV0_level9',
    'MEL_medium', 'PP0_low', 'IV0',
    'SHORTSHOT_low', 'DL飞边3_low',
]


def main():
    print("=" * 74)
    print("1. split_phase 实际解析结果")
    print("=" * 74)
    for t in TOKENS:
        r = split_phase(t)
        name = r.get('name')
        level = r.get('level')
        flag = ''
        if name and name.startswith('IV0') and name != 'IV0':
            flag = '  <== 字段名被污染'
        print(f"  {t:<22} name={str(name):<16} level={str(level):<16}{flag}")

    print()
    print("=" * 74)
    print("2. collect_param_names 对整条规则的提取")
    print("=" * 74)
    cases = [
        'IF IV0_very_low AND PP0_high THEN IV0_add_10',
        'IF IV0_low AND PP0_high THEN IV0_add_10',
        'IF IV0_extremely_low AND PP0_high THEN IV0_add_10',
    ]
    for c in cases:
        print(f"  {c}")
        print(f"      -> {sorted(collect_param_names([c]))}")


if __name__ == '__main__':
    main()
