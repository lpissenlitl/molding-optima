"""backend 顶层测试包

存放跨模块的集成 / 冒烟测试脚本。

约定：
- 各模块/引擎自己的单元测试仍就近放在子包下：
  * backend/masterdata/tests/
  * backend/process/algorithms/expert/tests/
  * backend/process/algorithms/fuzzy/fuzzy_core/tests/
- 跨模块冒烟 / 接口对接测试集中放本目录下，命名 test_<功能>_smoke.py
- 一次性验证脚本（verify_*.py）随对应缺陷修复完结后即可删除，不作为长期回归资产维护

⚠️ **两类 verify_ 脚本要分清**：
- **临时验证脚本**（一次性取证 / 迁移期新旧对拍）—— 用完即删，**不作为长期回归资产**；
- **业务护栏脚本**（_verify_*.py：零依赖不变量 / 离线契约 / 连库端到端 / expert runner）
  —— 断言的是**生产契约**，属长期回归资产，**保留**。

⚠️ **`verify_` / `_verify_` 前缀 ⇒ pytest 不收集**（断言走脚本自带 `_failures` 收集器 + 退出码，
不抛 pytest 异常 ⇒ 改回 `test_*` 前缀会让 pytest 把「断言值不对」也报成 PASS ⇒ **假绿**）。

运行方式（需在 backend 目录下）：
    set PYTHONPATH=.
    python tests/<脚本名>.py
    python tests/fuzzy_kernel/_snapshot_core.py <输出json路径>
"""