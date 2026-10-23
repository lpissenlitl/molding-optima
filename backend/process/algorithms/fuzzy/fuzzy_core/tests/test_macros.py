"""
档位词表与桶索引解析单元测试（不依赖 Django/DB）

运行：
  cd backend/process/algorithms/fuzzy/fuzzy_core
  python -m tests.test_macros

覆盖 2026-10-22 E2 引入的：
  - LEVEL_WORDS_BY_LVL 的自洽性（桶数 == 等级数、必含 low/medium/high）
  - resolve_bucket() 的双轨解析（levelN 编号 / 自然语言词）
  - split_phase() 的多段后缀匹配
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FUZZY_CORE = os.path.dirname(HERE)

# 让 fuzzy_core 作为顶层 package 可被发现
sys.path.insert(0, os.path.dirname(FUZZY_CORE))

from fuzzy_core.macros import (  # noqa: E402
    ALL_LEVEL_WORDS,
    FUZZY_LEVELS,
    LEVEL_NUMBER_TO_BUCKET,
    LEVEL_WORD_ALIASES,
    LEVEL_WORDS_BY_LVL,
    resolve_bucket,
)
from fuzzy_core.parsing import split_phase  # noqa: E402


FAIL = '\033[91m'
PASS = '\033[92m'
NC = '\033[0m'


def _assert_eq(actual, expected, label):
    if actual == expected:
        print(f'  {PASS}[PASS]{NC} {label}: {actual!r}')
        return True
    print(f'  {FAIL}[FAIL]{NC} {label}: expected={expected!r}, actual={actual!r}')
    return False


def _assert_raises(fn, label):
    try:
        fn()
    except ValueError as exc:
        print(f'  {PASS}[PASS]{NC} {label}: raised ValueError({exc})')
        return True
    print(f'  {FAIL}[FAIL]{NC} {label}: 未抛出 ValueError')
    return False


def test_word_table_self_consistency():
    """词表自洽：桶数 == 等级数、必含 low/medium/high、词不重复。"""
    print('\n[TEST] 档位词表自洽性')
    ok = True
    for lvl, words in sorted(LEVEL_WORDS_BY_LVL.items()):
        ok &= _assert_eq(len(words), lvl, f'lvl={lvl} 词表长度 == 等级数')
        ok &= _assert_eq(len(set(words)), len(words), f'lvl={lvl} 词表无重复')
        for core in ('low', 'medium', 'high'):
            ok &= _assert_eq(core in words, True, f'lvl={lvl} 含核心词 {core}')
    # FUZZY_LEVELS 是 LEVEL_WORDS_BY_LVL 的别名，不应分叉
    ok &= _assert_eq(
        {k: tuple(v) for k, v in FUZZY_LEVELS.items()},
        dict(LEVEL_WORDS_BY_LVL),
        'FUZZY_LEVELS 与 LEVEL_WORDS_BY_LVL 一致',
    )
    # ALL_LEVEL_WORDS 必须覆盖所有词表
    for lvl, words in LEVEL_WORDS_BY_LVL.items():
        for w in words:
            ok &= _assert_eq(w in ALL_LEVEL_WORDS, True, f'ALL_LEVEL_WORDS 含 {w!r}')
    # 别名也要能被词法层认出
    for alias in LEVEL_WORD_ALIASES:
        ok &= _assert_eq(alias in ALL_LEVEL_WORDS, True, f'ALL_LEVEL_WORDS 含别名 {alias!r}')
    return ok


def test_resolve_bucket_natural_words():
    """自然语言词按字段自己的词表定位。"""
    print('\n[TEST] resolve_bucket —— 自然语言词')
    ok = True
    expect = {
        3: {'low': 0, 'medium': 1, 'high': 2},
        5: {'very_low': 0, 'low': 1, 'medium': 2, 'high': 3, 'very_high': 4},
        7: {'extremely_low': 0, 'very_low': 1, 'low': 2, 'medium': 3,
            'high': 4, 'very_high': 5, 'extremely_high': 6},
        9: {'extremely_low': 0, 'very_low': 1, 'low': 2, 'ultra_low': 3,
            'medium': 4, 'ultra_high': 5, 'high': 6, 'very_high': 7,
            'extremely_high': 8},
    }
    for lvl, mapping in expect.items():
        for word, bucket in mapping.items():
            ok &= _assert_eq(
                resolve_bucket(lvl, word), bucket, f'lvl={lvl} {word!r} -> 桶{bucket}'
            )
    # 别名 mid == medium
    ok &= _assert_eq(resolve_bucket(3, 'mid'), 1, "lvl=3 'mid' -> 桶1（别名）")
    ok &= _assert_eq(resolve_bucket(5, 'MID'), 2, "lvl=5 'MID' -> 桶2（大小写不敏感）")
    return ok


def test_resolve_bucket_level_number():
    """编号形式 levelN：与字段级数解耦，仅要求 N <= lvl。"""
    print('\n[TEST] resolve_bucket —— 编号形式 levelN')
    ok = True
    ok &= _assert_eq(resolve_bucket(3, 'level1'), 0, 'lvl=3 level1 -> 桶0')
    ok &= _assert_eq(resolve_bucket(3, 'level3'), 2, 'lvl=3 level3 -> 桶2')
    ok &= _assert_eq(resolve_bucket(5, 'level5'), 4, 'lvl=5 level5 -> 桶4')
    ok &= _assert_eq(resolve_bucket(9, 'level9'), 8, 'lvl=9 level9 -> 桶8')
    # 越界必须报错，而不是静默夹取
    ok &= _assert_raises(lambda: resolve_bucket(3, 'level5'), 'lvl=3 level5 越界报错')
    ok &= _assert_raises(lambda: resolve_bucket(3, 'level0'), 'lvl=3 level0 越界报错')
    # 自然语言词不在该等级词表内必须报错
    ok &= _assert_raises(lambda: resolve_bucket(3, 'very_low'), 'lvl=3 very_low 不在词表')
    # 等级数没有词表
    ok &= _assert_raises(lambda: resolve_bucket(4, 'low'), 'lvl=4 无对应词表')
    # 自定义词表覆盖默认
    ok &= _assert_eq(
        resolve_bucket(3, 'p_low', field_words=('p_low', 'p_mid', 'p_high')),
        0, '自定义词表覆盖默认',
    )
    # 自定义词表长度与等级数不符必须报错
    ok &= _assert_raises(
        lambda: resolve_bucket(3, 'p_low', field_words=('p_low', 'p_mid')),
        '自定义词表长度与等级数不符报错',
    )
    return ok


def test_level_number_table_alignment():
    """桶编号表与词表必须严格对应（编号形式 N ↔ 词表第 N 个词）。"""
    print('\n[TEST] 桶编号表与词表对齐')
    ok = True
    max_lvl = max(LEVEL_WORDS_BY_LVL)
    ok &= _assert_eq(
        len(LEVEL_NUMBER_TO_BUCKET), max_lvl,
        f'编号表长度 == 最大等级数({max_lvl})',
    )
    ok &= _assert_eq(
        max(LEVEL_NUMBER_TO_BUCKET.values()) + 1, max_lvl,
        '编号表最大桶索引 + 1 == 最大等级数',
    )
    for lvl in sorted(LEVEL_WORDS_BY_LVL):
        words = LEVEL_WORDS_BY_LVL[lvl]
        for i in range(1, lvl + 1):
            number_word = f'level{i}'
            bucket = resolve_bucket(lvl, number_word)
            # 编号轨道：桶索引恒为 N-1
            ok &= _assert_eq(bucket, i - 1, f'lvl={lvl} {number_word} -> 桶{i - 1}')
            # 与词表对应：levelN 指向词表里第 N 个词
            ok &= _assert_eq(
                words[bucket], words[i - 1],
                f'lvl={lvl} {number_word} 对应词表第{i}个词 {words[i - 1]!r}',
            )
    # 越界：level{lvl+1} 必须报错
    ok &= _assert_raises(
        lambda: resolve_bucket(3, 'level4'), 'lvl=3 level4 越界报错',
    )
    # 超出编号表范围（level10）必须报错而不是被当成合法编号
    ok &= _assert_raises(
        lambda: resolve_bucket(9, 'level10'), 'level10 超出编号表报错',
    )
    return ok


def test_split_phase_multi_segment():
    """split_phase 的多段后缀匹配（E1 补齐项）。"""
    print('\n[TEST] split_phase —— 多段后缀')
    ok = True
    cases = [
        ('IV0_low', 'IV0', 'low'),
        ('IV0_very_low', 'IV0', 'very_low'),
        ('IV0_extremely_high', 'IV0', 'extremely_high'),
        ('IV0_ultra_low', 'IV0', 'ultra_low'),
        ('inj_pres_1_low', 'inj_pres_1', 'low'),
        ('SHORTSHOT_high', 'SHORTSHOT', 'high'),
    ]
    for phrase, name, level in cases:
        info = split_phase(phrase)
        ok &= _assert_eq(info.get('name'), name, f'{phrase} -> name')
        ok &= _assert_eq(info.get('level'), level, f'{phrase} -> level')
    # 结论词不受影响
    sol = split_phase('MEL_add_low')
    ok &= _assert_eq(sol.get('name'), 'MEL', "MEL_add_low -> name")
    ok &= _assert_eq(sol.get('action'), 'add', "MEL_add_low -> action")
    ok &= _assert_eq(sol.get('value'), 'low', "MEL_add_low -> value")
    return ok


def test_regression_existing_rule_forms():
    """回归：现有规则库使用的词形解析结果必须不变。"""
    print('\n[TEST] 回归 —— 现有规则词形解析不变')
    ok = True
    # 现有 1646 条规则的前件只用单段词 low/medium/high/worse
    for phrase, name, level in [
        ('IV0_low', 'IV0', 'low'),
        ('IV0_medium', 'IV0', 'medium'),
        ('IV0_high', 'IV0', 'high'),
        ('IV0_worse', 'IV0', 'worse'),   # worse 不在词表 → 走兜底
    ]:
        info = split_phase(phrase)
        ok &= _assert_eq(info.get('name'), name, f'{phrase} -> name')
        ok &= _assert_eq(info.get('level'), level, f'{phrase} -> level')
    return ok


def main():
    results = [
        test_word_table_self_consistency(),
        test_resolve_bucket_natural_words(),
        test_resolve_bucket_level_number(),
        test_level_number_table_alignment(),
        test_split_phase_multi_segment(),
        test_regression_existing_rule_forms(),
    ]
    passed = all(results)
    print('\n' + ('=' * 60))
    print(f'{"ALL PASS" if passed else "HAS FAILURE"}  '
          f'({sum(1 for r in results if r)}/{len(results)} 组通过)')
    return 0 if passed else 1


if __name__ == '__main__':
    sys.exit(main())
