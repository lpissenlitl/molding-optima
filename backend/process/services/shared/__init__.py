"""服务层共用件 —— **被多条链路（初始化 / 优化）共用**的件。

按**角色**分组（对照 ``optimize_chain/`` 的按领域分组）：本目录的件被多条链路引用，
与「一个业务用例一个文件」的根目录平铺分开。

【注意】**参数限值整体在本目录**（1 个模块，两个功能）：
  - ``param_limits`` —— **准备 + 校验**：从设定值上下文挖出各设定工艺参数的
    允许区间（**有配置则校验、没有配置则不校验**）⇒ 再把当前值与区间比对 ⇒
    命中按严格度抛 ``BizException``（400）或只报不拒（**校验只收表**，不碰设定值上下文）。
字段**契约**（哪个算法族要哪个设备字段）在算法层 ``algorithms/fuzzy/device_limits.py``
⇒ **契约归算法层，取值与校验归 service 层**；「值 vs 区间」这条链路只跨 1 层。

【注意】**依赖方向**：``param_limits`` 与 ``param_naming`` **零算法层依赖**
（不 import ``process.algorithms.*``）⇒ 限值域与命名域是纯 service 层的公共底座；
只有 ``spec_extract`` 引算法层的 **spec 契约**（``algorithms.expert.specs`` /
``algorithms.fuzzy.specs``）—— 契约归算法层，取值归 service 层。
算法层不反向依赖本目录（``algorithms/fuzzy/examples/export_case.py`` 与
``run_demo.py`` 是开发期工具、已声明的例外）。

【注意】本包**不 re-export 任何模块**（刻意）：包初始化期就 import 算法子包会拖重
离线 runner 的「不碰 service 层启动期」⇒ 调用方一律写**完整模块路径**。
"""
