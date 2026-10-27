"""
模糊推理核心模块

包含隶属度函数（memberships）、反模糊化（defuzz）、常量定义（macros）等

⚠️ 顶层不导出 `defuzz` **函数** —— 它与子模块 `fuzzy_core.defuzz` 同名，
同时导出会让包属性指向函数、遮蔽子模块（`from fuzzy_core import defuzz`
拿到的是函数而非模块）。反模糊化函数一律经子模块访问：
`from fuzzy_core.defuzz import defuzz`（相对导入）或
`fuzzy_core.defuzz.centroid`。
"""

from .memberships import *
from .defuzz import centroid
from .macros import *
