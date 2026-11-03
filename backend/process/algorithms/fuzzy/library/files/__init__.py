"""文件来源 —— 规则与关键字的**第二数据源**（本地文件）。

数据库来源（`library/repository.py`）与文件来源（`library/files/`）的差别
只有两步：**选库**与**取方法**。从「取回的方法」到「交给内核的契约档案」
这段逻辑**完全来源无关** ⇒ 全部收在 `library/assembly.py`，两个来源共用。

本包文件：

- `loader.py`：读本地 JSON → 来源无关记录（**零 ORM**）
- `repository.py`：`FileResourceRepository`，实现 `AlgorithmResourceRepository`
  协议（**零 ORM**）
- `export.py`：开发期导出工具，数据库 → 本地文件（**碰 ORM**）

⚠️ **本包不 import 子模块**：与 `library/__init__.py` 同一约定 ——
在包初始化时 import 会把「用文件来源」也拖进 Django 依赖链。
`export.py` 碰 ORM，只能作为脚本单独跑，绝不能被运行时代码 import。

默认数据目录：`library/files/data/`（由 `export.py` 生成）。
"""