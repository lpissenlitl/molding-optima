"""规则库适配 —— 把外部存储里的规则与关键字读出来，转成内核输入契约。

与 ORM 模型 `process.models.rules.RuleLibrary` 同名不同物：ORM 侧是数据库表
（按租户/系统隔离的分组容器），本包是算法侧视图（读库 → 转契约），不暴露 ORM
对象；两侧靠 `library_code` / `library_type='fuzzy'` 对齐。

本包文件：`contracts.py`（对外契约）、`rules.py`（规则取数与语义判定）、
`keywords.py`（关键字取数与转换）、`repository.py`（资源编排）、
`files/`（文件来源，预留）。

本包不 import 子模块：`rules` / `keywords` / `repository` 都依赖 Django ORM，
若在包初始化时 import，编排层 `engine` 会被拖进 ORM。
`engine._get_repository()` 用延迟导入触达。
"""
