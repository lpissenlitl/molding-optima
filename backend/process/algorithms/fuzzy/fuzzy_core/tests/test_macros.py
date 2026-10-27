"""
档位词表与桶索引解析单元测试（不依赖 Django/DB）

运行：
  cd backend
  pytest process/algorithms/fuzzy/fuzzy_core/tests/test_macros.py
  # 或独立跑：
  python -m process.algorithms.fuzzy.fuzzy_core.tests.test_macros

覆盖：
  - LEVEL_WORDS_BY_LVL 的自洽性（桶数 == 等级数、必含 low/medium/high）
  - resolve_bucket() 的双轨解析（levelN 编号 / 自然语言词）
  - split_phase() 的多段后缀匹配
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FUZZY_CORE = os.path.dirname(HERE)
BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(FUZZY_CORE))))

# 只把 backend 根目录（包的父目录）加进 sys.path。
# ⚠️ 不要把 `fuzzy/` 目录加进来：那等于宣布「该目录下每个带 __init__.py 的子目录
#    都是顶层包」，于是包内子模块（`fuzzy_core` / `library` …）泄漏成
#    顶层名，将来撞名即**静默劫持**。内核一律用完整点分路径导入。
sys.path.insert(0, BACKEND_ROOT)

from process.algorithms.fuzzy.fuzzy_core.macros import (  # noqa: E402
    ALL_LEVEL_WORDS,
    FUZZY_LEVELS,
    LEVEL_NUMBER_TO_BUCKET,
    LEVEL_WORD_ALIASES,
    LEVEL_WORDS_BY_LVL,
    bucket_centers,
    resolve_bucket,
)
from process.algorithms.fuzzy.fuzzy_core.parsing import split_phase  # noqa: E402


FAIL = '\033[91m'
PASS = '\033[92m'
NC = '\033[0m'


def _assert_eq(actual, expected, label):
    if actual != expected:
        raise AssertionError(f'{label}: expected={expected!r}, actual={actual!r}')


def _assert_close(actual, expected, label, eps=1e-9):
    if abs(float(actual) - float(expected)) > eps:
        raise AssertionError(f'{label}: expected={expected!r}, actual={actual!r}')


def _assert_raises(fn, label):
    try:
        fn()
    except ValueError:
        return
    except Exception as exc:
        raise AssertionError(
            f'{label}: 期望 ValueError，实际 {type(exc).__name__}: {exc}'
        ) from exc
    raise AssertionError(f'{label}: 未抛出 ValueError')


def test_word_table_self_consistency():
    """词表自洽：桶数 == 等级数、必含 low/medium/high、词不重复。"""
    for lvl, words in sorted(LEVEL_WORDS_BY_LVL.items()):
        _assert_eq(len(words), lvl, f'lvl={lvl} 词表长度 == 等级数')
        _assert_eq(len(set(words)), len(words), f'lvl={lvl} 词表无重复')
        for core in ('low', 'medium', 'high'):
            _assert_eq(core in words, True, f'lvl={lvl} 含核心词 {core}')
    # FUZZY_LEVELS 是 LEVEL_WORDS_BY_LVL 的别名，不应分叉
    _assert_eq(
        {k: tuple(v) for k, v in FUZZY_LEVELS.items()},
        dict(LEVEL_WORDS_BY_LVL),
        'FUZZY_LEVELS 与 LEVEL_WORDS_BY_LVL 一致',
    )
    # ALL_LEVEL_WORDS 必须覆盖所有词表
    for lvl, words in LEVEL_WORDS_BY_LVL.items():
        for w in words:
            _assert_eq(w in ALL_LEVEL_WORDS, True, f'ALL_LEVEL_WORDS 含 {w!r}')
    # 别名也要能被词法层认出
    for alias in LEVEL_WORD_ALIASES:
        _assert_eq(alias in ALL_LEVEL_WORDS, True, f'ALL_LEVEL_WORDS 含别名 {alias!r}')


def test_resolve_bucket_natural_words():
    """自然语言词按字段自己的词表定位。"""
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
            _assert_eq(
                resolve_bucket(lvl, word), bucket, f'lvl={lvl} {word!r} -> 桶{bucket}'
            )
    # 别名 mid == medium
    _assert_eq(resolve_bucket(3, 'mid'), 1, "lvl=3 'mid' -> 桶1（别名）")
    _assert_eq(resolve_bucket(5, 'MID'), 2, "lvl=5 'MID' -> 桶2（大小写不敏感）")


def test_resolve_bucket_level_number():
    """编号形式 levelN：与字段级数解耦，仅要求 N <= lvl。"""
    _assert_eq(resolve_bucket(3, 'level1'), 0, 'lvl=3 level1 -> 桶0')
    _assert_eq(resolve_bucket(3, 'level3'), 2, 'lvl=3 level3 -> 桶2')
    _assert_eq(resolve_bucket(5, 'level5'), 4, 'lvl=5 level5 -> 桶4')
    _assert_eq(resolve_bucket(9, 'level9'), 8, 'lvl=9 level9 -> 桶8')
    # 越界必须报错，而不是静默夹取
    _assert_raises(lambda: resolve_bucket(3, 'level5'), 'lvl=3 level5 越界报错')
    _assert_raises(lambda: resolve_bucket(3, 'level0'), 'lvl=3 level0 越界报错')
    # 自然语言词不在该等级词表内必须报错
    _assert_raises(lambda: resolve_bucket(3, 'very_low'), 'lvl=3 very_low 不在词表')
    # 等级数没有词表
    _assert_raises(lambda: resolve_bucket(4, 'low'), 'lvl=4 无对应词表')
    # 自定义词表覆盖默认
    _assert_eq(
        resolve_bucket(3, 'p_low', field_words=('p_low', 'p_mid', 'p_high')),
        0, '自定义词表覆盖默认',
    )
    # 自定义词表长度与等级数不符必须报错
    _assert_raises(
        lambda: resolve_bucket(3, 'p_low', field_words=('p_low', 'p_mid')),
        '自定义词表长度与等级数不符报错',
    )


def test_level_number_table_alignment():
    """桶编号表与词表必须严格对应（编号形式 N ↔ 词表第 N 个词）。"""
    max_lvl = max(LEVEL_WORDS_BY_LVL)
    _assert_eq(
        len(LEVEL_NUMBER_TO_BUCKET), max_lvl,
        f'编号表长度 == 最大等级数({max_lvl})',
    )
    _assert_eq(
        max(LEVEL_NUMBER_TO_BUCKET.values()) + 1, max_lvl,
        '编号表最大桶索引 + 1 == 最大等级数',
    )
    for lvl in sorted(LEVEL_WORDS_BY_LVL):
        words = LEVEL_WORDS_BY_LVL[lvl]
        for i in range(1, lvl + 1):
            number_word = f'level{i}'
            bucket = resolve_bucket(lvl, number_word)
            # 编号轨道：桶索引恒为 N-1
            _assert_eq(bucket, i - 1, f'lvl={lvl} {number_word} -> 桶{i - 1}')
            # 与词表对应：levelN 指向词表里第 N 个词
            _assert_eq(
                words[bucket], words[i - 1],
                f'lvl={lvl} {number_word} 对应词表第{i}个词 {words[i - 1]!r}',
            )
    # 越界：level{lvl+1} 必须报错
    _assert_raises(
        lambda: resolve_bucket(3, 'level4'), 'lvl=3 level4 越界报错',
    )
    # 超出编号表范围（level10）必须报错而不是被当成合法编号
    _assert_raises(
        lambda: resolve_bucket(9, 'level10'), 'level10 超出编号表报错',
    )


def test_bucket_centers_direct_values():
    """桶中心纯函数的直接断言（3/5/7/9 档全列）。

    此前桶中心只以「内联表达式」形式存在于 features.py，
    没有任何直接断言；本表把 3/5/7/9 档的桶中心**写死**，
    任何分位点口径变动都会立刻暴露。
    """
    iv = [0.0, 200.0]
    expected = {
        3: [0.0, 100.0, 200.0],
        5: [0.0, 50.0, 100.0, 150.0, 200.0],
        7: [0.0, 200.0 / 6, 200.0 / 3, 100.0, 400.0 / 3, 500.0 / 3, 200.0],
        9: [0.0, 25.0, 50.0, 75.0, 100.0, 125.0, 150.0, 175.0, 200.0],
    }
    for lvl, want in sorted(expected.items()):
        got = list(bucket_centers(iv, lvl))
        _assert_eq(len(got), lvl, f'lvl={lvl} 桶中心数量 == 桶数')
        for i, (g, w) in enumerate(zip(got, want)):
            _assert_close(g, w, f'lvl={lvl} 桶{i} 中心')


def test_bucket_centers_align_with_word_table():
    """词表下标 == 桶中心下标：把「人工保持一致」变成可执行断言。

    词表（LEVEL_WORDS_BY_LVL）与桶中心（features.py 的分位点）必须同源，
    否则 7/9 档会零覆盖。
    """
    iv = [0.0, 200.0]
    # 核心词占论域的百分比（与本文件 LEVEL_WORDS_BY_LVL 上方注释同口径）
    core_ratio = {
        3: {'low': 0.0, 'medium': 0.5, 'high': 1.0},
        5: {'low': 0.25, 'medium': 0.5, 'high': 0.75},
        7: {'low': 1.0 / 3, 'medium': 0.5, 'high': 2.0 / 3},
        9: {'low': 0.25, 'medium': 0.5, 'high': 0.75},
    }
    for lvl, words in sorted(LEVEL_WORDS_BY_LVL.items()):
        centers = list(bucket_centers(iv, lvl))
        _assert_eq(len(centers), lvl, f'lvl={lvl} 桶中心数量 == 等级数')
        # 桶中心必须严格递增（论域单调）
        for i in range(1, lvl):
            _assert_eq(centers[i] > centers[i - 1], True,
                       f'lvl={lvl} 桶中心严格递增（第{i}个）')
        for word, ratio in sorted(core_ratio[lvl].items()):
            idx = words.index(word)
            _assert_close(centers[idx], 200.0 * ratio,
                          f'lvl={lvl} {word!r}（桶{idx}）占论域 {ratio:.0%}')


def test_split_phase_multi_segment():
    """split_phase 的多段后缀匹配。"""
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
        _assert_eq(info.get('name'), name, f'{phrase} -> name')
        _assert_eq(info.get('level'), level, f'{phrase} -> level')
    # 结论词不受影响
    sol = split_phase('MEL_add_low')
    _assert_eq(sol.get('name'), 'MEL', "MEL_add_low -> name")
    _assert_eq(sol.get('action'), 'add', "MEL_add_low -> action")
    _assert_eq(sol.get('value'), 'low', "MEL_add_low -> value")


def test_regression_existing_rule_forms():
    """回归：现有规则库使用的词形解析结果必须不变。"""
    # 现有规则的前件只用单段词 low/medium/high/worse
    for phrase, name, level in [
        ('IV0_low', 'IV0', 'low'),
        ('IV0_medium', 'IV0', 'medium'),
        ('IV0_high', 'IV0', 'high'),
        ('IV0_worse', 'IV0', 'worse'),   # worse 不在词表 → 走兜底
    ]:
        info = split_phase(phrase)
        _assert_eq(info.get('name'), name, f'{phrase} -> name')
        _assert_eq(info.get('level'), level, f'{phrase} -> level')


def main():
    cases = [
        ('档位词表自洽性', test_word_table_self_consistency),
        ('resolve_bucket —— 自然语言词', test_resolve_bucket_natural_words),
        ('resolve_bucket —— 编号形式 levelN', test_resolve_bucket_level_number),
        ('桶编号表与词表对齐', test_level_number_table_alignment),
        ('桶中心 —— 直接断言（3/5/7/9 档）', test_bucket_centers_direct_values),
        ('桶中心 —— 词表对齐', test_bucket_centers_align_with_word_table),
        ('split_phase —— 多段后缀', test_split_phase_multi_segment),
        ('回归 —— 现有规则词形解析不变', test_regression_existing_rule_forms),
    ]
    passed = 0
    failed = 0
    for name, fn in cases:
        try:
            print(f'\n[TEST] {name}')
            fn()
            passed += 1
        except Exception as e:
            import traceback
            print(f'  {FAIL}[ERROR]{NC} {name}: {e}')
            traceback.print_exc()
            failed += 1

    print('\n' + ('=' * 60))
    print(f'{"ALL PASS" if failed == 0 else "HAS FAILURE"}  '
          f'({passed}/{len(cases)} 组通过)')
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
