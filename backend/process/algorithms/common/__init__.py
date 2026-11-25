"""跨算法线公共底座 —— **不是算法子包**。

【注意】**本目录不注册任何 ``algorithm_type`` / ``algorithm_subtype``**：它不是一条
算法线，而是**被多条算法线与 service 层共同引用**的公共件所在处（对照 ``fuzzy/`` /
``llm/`` / ``empirical/`` / ``expert/`` / ``mining/`` —— 那些才是算法子包，各自
注册一个 subtype）。

【注意】**入件判据**（谁引用它 / 变更原因是否相同）：多方引用且变更原因相同 ⇒ 入本
目录；只在单条链路内部按单向链引用 ⇒ 不入。

【注意】**导入约定**：本目录的每个模块都零外部依赖（不 import 任何算法包 / Django /
ORM）⇒ 依赖方向恒为「算法包 / service 层 → common」⇒ **无循环导入风险** ⇒ 均可
在本包 re-export（``from process.algorithms.common import field_contract``）；
需要完整模块路径时写 ``from process.algorithms.common.<模块>
import ...``（两种写法等价）。

【注意】**本目录只放「跨算法线真公共」的东西**：**字段契约机制**
（``field_contract``）+ 材料物理常量（``material_physics``）+ 缺陷码词表
（``defect_codes``）。
【注意】**算法命名空间不在这里**：**字段映射**（``field_names``）与**算法族表**
（``device_limits``）是模糊规则库的内部命名（``IV0`` / ``IP0`` / ``MEL``），
只在 ``fuzzy/`` 内成立 ⇒ 已归位到 ``process/algorithms/fuzzy/``。
越限相关的**来源声明 / 取值 / 识别 / 拦截**都不在这里
（在 service 层 ``services/shared/param_limits.py``）
⇒ 算法层**不知道**参数有没有上下限、也不碰「字段存不存在、值多少、
要不要拒绝」。
"""

from . import defect_codes, field_contract, material_physics  # noqa: F401

__all__ = [
    'defect_codes',
    'field_contract',
    'material_physics',
]
