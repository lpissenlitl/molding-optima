"""工艺模块 - 服务层。

按领域平铺业务用例（根目录一个用例一个文件）；两个子目录各按一条轴分：
``shared/`` 收**多条链路共用**的件，``optimize_chain/`` 收**优化链路 4 层编排**。

业务模型：
- ProcessCondition（工艺条件）是一等公民，所有 CRUD 都通过 condition
- ProcessParameter（工艺参数 / 调机轮次）是 condition 的子资源，必须依附 condition
- view_type 区分应用场景：parameter / optimization / all
- condition 一旦创建不轻易变更，变更 = 新建 condition
- condition 内容允许重复（同样 mold+polymer+machine 可有多个 condition）

服务层形态：以「模块级函数 + 数据类」为默认 —— 服务不持有实例状态（租户 / 用户等
上下文一律显式透传），封装成类只会退化成一组 staticmethod。

【注意】**本包不 re-export 任何模块**：包初始化期 import 业务模块会拉起整条算法链
（``parameter_initialize`` → ``algorithms.*``）⇒ 拖重离线 runner 启动期；调用方一律
按需导入并自己指明来源（``from process.services.tuning import TuningService``）。
"""