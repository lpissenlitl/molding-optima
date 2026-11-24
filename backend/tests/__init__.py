"""backend 顶层测试包。

存放**跨模块**的集成 / 冒烟 / 契约护栏。

约定：
- 各模块/引擎自己的单元测试仍就近放在子包下：
  * backend/masterdata/tests/
  * backend/process/algorithms/expert/tests/
  * backend/process/algorithms/fuzzy/fuzzy_core/tests/
- 跨模块的冒烟 / 接口对接 / 契约护栏集中放本目录下。

【注意】**三类文件，按前缀分**（前缀 = 生命周期承诺，不是随手起的）：

1. ``test_*.py`` —— **pytest 用例**（长期回归资产，自动收集）
   ⇒ 断言用 ``assert``，不自己收集失败、不自己 exit
   ⇒ 加了新功能 ⇒ **优先写成这里的 pytest 用例**，别再堆一次性脚本

2. ``_verify_*.py`` —— **独立护栏脚本**（长期回归资产，pytest **不**收集）
   ⇒ 用于「pytest 跑不了」的场合：连真实 DB、脱离 Django 独立进程、子进程对拍
   ⇒ 断言走脚本自带收集器 + 退出码，**不抛 pytest 异常**
     （所以**不能**改成 ``test_*`` 前缀 —— 那样 pytest 会把「断言值不对」
     也报成 PASS ⇒ **假绿**）

3. ``verify_*.py`` —— **一次性取证脚本**（用完即删，**不**作为长期回归资产）
   ⇒ 只服务于「某次缺陷取证 / 某步改造的中间态验证」
   ⇒ 目标功能开发完结后**应当删除**
   ⇒ 当前目录**没有**此类文件；新增前先想清楚：它该是 1 还是 2？

【注意】**判断标准是「断言钉的是什么」**：
- 钉**生产契约** ⇒ 长期资产（1 或 2）
- 钉**某次改造的中间态 / 修复前的失败症状** ⇒ 一次性（3），用完即删

运行方式（需在 backend 目录下）：
    set PYTHONPATH=.
    set DJANGO_SETTINGS_MODULE=_moldx.settings
    ..\\.venv\\Scripts\\python.exe -m pytest tests -q          # 全部 pytest 用例
    ..\\.venv\\Scripts\\python.exe tests/_verify_<名>.py         # 独立护栏脚本
    ..\\.venv\\Scripts\\python.exe tests/fuzzy_kernel/_snapshot_core.py <输出json路径>

【注意】``DJANGO_SETTINGS_MODULE`` **必须**设（仓库无 pytest.ini / conftest.py
⇒ 收集期否则报 ImproperlyConfigured）；且 pytest-django 未启用
⇒ 用例里访问 DB 会被拦 ⇒ 连库的检查一律走 `_verify_*.py` 脚本。
"""