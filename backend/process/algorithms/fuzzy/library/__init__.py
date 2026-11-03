"""规则库适配 —— 把外部存储里的规则与关键字读出来，转成内核输入契约。

与 ORM 模型 `process.models.rules.RuleLibrary` 同名不同物：ORM 侧是数据库表
（按租户/系统隔离的分组容器），本包是算法侧视图（读来源 → 转契约），不暴露 ORM
对象；两侧靠 `library_code` / `library_type='fuzzy'` 对齐。

**两个数据源，一个契约**：

| 来源 | 实现 | 依赖 |
|---|---|---|
| 数据库 | `repository.py::ResourceRepository` | Django ORM |
| 本地文件 | `files/repository.py::FileResourceRepository` | 纯 JSON（零 ORM） |

两者实现同一个契约 `contracts.py::AlgorithmResourceRepository` ⇒ 编排层
（`engine.py`）可互换。切换方式：`settings.FUZZY_LIBRARY_SOURCE`
（`'db'` / `'file'`）或显式注入。

**分层**（自外向内，依赖方向单向）：

| 模块 | 职责 | ORM |
|---|---|---|
| `contracts.py` | 对外契约（`RuleQueryContext` / `LibraryRecord` / `RuleRecord` / 协议） | 零 |
| `semantics.py` | 规则语义判定的**唯一口径**（`RuleService`） | 零 |
| `adapters.py` | 来源记录 → 内核契约的转换 | 零 |
| `assembly.py` | **来源无关**的编排（选库 / 组装 / 去重 / 排序） | 零 |
| `provider.py` | 来源选择器（配置开关 + 延迟导入） | 延迟 |
| `rules.py` / `keywords.py` | 数据库来源的**取数**（查询线） | 有 |
| `repository.py` | 数据库来源的资源仓库 | 有 |
| `files/` | 文件来源（读取线 / 仓库 / 导出工具） | 零（导出工具除外） |

⚠️ **语义、转换、编排三层必须零 ORM** —— 文件来源要复用它们，
  一旦被 ORM 拖住，文件通道就失去意义（依赖倒置的实质检验 =
  高层不被低层实现拖住）。

⚠️ **本包不 import 子模块**：`rules` / `keywords` / `repository` 都依赖
  Django ORM，若在包初始化时 import，编排层 `engine` 会被拖进 ORM。
  `engine._get_repository()` 用延迟导入触达。
"""