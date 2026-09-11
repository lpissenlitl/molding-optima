"""backend 顶层测试包

存放跨模块的集成 / 冒烟测试。

约定：
- 各模块/引擎自己的单元测试仍就近放在子包下：
  * backend/masterdata/tests/
  * backend/process/engines/expert/tests/
  * backend/process/engines/fuzzy/fuzzy_core/tests/
- 跨模块冒烟 / 接口对接测试 集中放本目录下，命名 test_<功能>_smoke.py
- 配套 _run_all_smoke.py 一键运行全部
"""