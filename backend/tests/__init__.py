"""backend 顶层测试包

存放跨模块的集成 / 冒烟测试脚本。

约定：
- 各模块/引擎自己的单元测试仍就近放在子包下：
  * backend/masterdata/tests/
  * backend/process/algorithms/expert/tests/
  * backend/process/algorithms/fuzzy/fuzzy_core/tests/
- 跨模块冒烟 / 接口对接测试集中放本目录下，命名 test_<功能>_smoke.py
- 一次性验证脚本（verify_*.py）随对应缺陷修复完结后即可删除，不作为长期回归资产维护

运行方式（需在 backend 目录下）：
    set PYTHONPATH=.
    python tests/<脚本名>.py
"""