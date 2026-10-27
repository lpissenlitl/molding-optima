"""零依赖不变量检查（E10 口径，E12 复验，E15/E16 更新）。

**不变量**：`fuzzy` 包的**编排层与契约层**必须能在**不加载 Django ORM** 的
前提下被 import —— 编排层拿的是契约，ORM 只在真正要访问数据库时才被
延迟导入（`engine._get_repository()`）。

检查口径：
1. import `library.contracts`（契约）/ `library`（**包**）/ `engine` 之后，
   `django` / `process.models` / `library.rules` / `library.keywords`
   / `library.repository` 都**不得**出现在 `sys.modules`；
2. 不得有**顶层名泄漏**（`contracts` / `library` / `engine` /
   `fuzzy` / `fuzzy_core` 等不得成为顶层模块名）。

⚠️ 注意口径：只 import `library` **包**，不 import `library.keywords` /
   `library.rules` —— 后两者**本来就**依赖 Django ORM（顶层 import
   `process.models.rules`），它们只应在真正访问数据库时被加载。

⚠️ `library.repository`（E16 新增，**资源集合层**）虽然它内部转手 ORM，
   但它**本身**是「编排层默认实现」—— 编排层只跟**契约**打交道，
   不该直接依赖任何具体实现（含资源集合层）。
   锁住这条，才能保证「新增来源 → 编排层零改动」。

运行：../.venv/Scripts/python.exe _dev_refs/_verify_zero_dep.py
"""
import sys

_BANNED = [
    'django',
    'process.models',
    'process.algorithms.fuzzy.library.rules',
    'process.algorithms.fuzzy.library.keywords',
    # E16：资源集合层（编排实现），编排层只跟契约打交道
    'process.algorithms.fuzzy.library.repository',
]
_LEAKED_TOPLEVEL = [
    'contracts', 'library', 'engine', 'fuzzy', 'fuzzy_core',
    'sources', 'elements', 'specs', 'recommendations', 'field_names',
    'contracts', 'rules', 'keywords', 'repository', 'models',
]

from process.algorithms.fuzzy.library import contracts  # noqa: E402
from process.algorithms.fuzzy import library  # noqa: E402
from process.algorithms.fuzzy import engine  # noqa: E402

print('=' * 68)
print('1) 编排层/契约层 import 成功（未触发 ORM）')
print('   contracts     =', contracts.__name__)
print('   library        =', library.__name__)
print('   engine=', engine.__name__)

print()
print('2) 禁止进 sys.modules 的模块')
leaked = [m for m in _BANNED if m in sys.modules]
for m in _BANNED:
    print('   %-46s in sys.modules = %s' % (m, m in sys.modules))

print()
print('3) 顶层名泄漏')
top = sorted({m for m in sys.modules if m in _LEAKED_TOPLEVEL})
print('   泄漏的顶层名 =', top if top else 'NONE')

ok = not leaked and not top
print()
print('=' * 68)
print('[%s] 零依赖不变量' % ('PASS' if ok else 'FAIL'))
sys.exit(0 if ok else 1)
