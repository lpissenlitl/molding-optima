"""工艺模块（Process）业务错误码定义。

模块编号：07（与 extensions/exceptions.py 中的 MOD_COMMON 同级）

错误码分段规划：
    01-09  模具（Mold）
    10-19  注塑机（InjectionMoldingMachine / InjectionUnit）
    20-29  材料（Polymer）
    30-49  工艺条件（ProcessCondition / ProcessParameter）
    50-69  工艺规则（Rule）
    70-89  工艺优化（Optimization）
    90-99  其他
"""
from extensions.exceptions import BizErrorCode


# ============================================================
# 模块编号
# ============================================================
MOD_PROCESS = "07"


# ============================================================
# 01-09 模具（Mold）相关
# ============================================================
ERROR_MOLD_NOT_FOUND               = BizErrorCode.create(MOD_PROCESS, 1, "模具不存在")
ERROR_MOLD_GATING_SYSTEM_EMPTY     = BizErrorCode.create(MOD_PROCESS, 2, "模具未配置浇注系统")
ERROR_MOLD_GATING_SYSTEM_MISSING   = BizErrorCode.create(MOD_PROCESS, 3, "指定的浇注系统不存在")
ERROR_MOLD_CAVITY_MISSING          = BizErrorCode.create(MOD_PROCESS, 4, "模具型腔不存在")
ERROR_MOLD_GATE_MISSING            = BizErrorCode.create(MOD_PROCESS, 5, "模具浇口不存在")
ERROR_MOLD_SHOT_INDEX_OUT_OF_RANGE = BizErrorCode.create(
    MOD_PROCESS, 6, "shot_index 超出模具射数范围"
)


# ============================================================
# 10-19 注塑机（InjectionMoldingMachine / InjectionUnit）相关
# ============================================================
ERROR_MACHINE_NOT_FOUND              = BizErrorCode.create(MOD_PROCESS, 10, "注塑机不存在")
ERROR_MACHINE_UNIT_MISSING           = BizErrorCode.create(MOD_PROCESS, 11, "注塑机的注射单元不存在")
ERROR_MACHINE_INJECTION_INDEX_OUT_OF_RANGE = BizErrorCode.create(
    MOD_PROCESS, 12, "injection_index 超出注塑机射台数范围"
)


# ============================================================
# 20-29 材料（Polymer）相关
# ============================================================
ERROR_POLYMER_NOT_FOUND = BizErrorCode.create(MOD_PROCESS, 20, "材料不存在")


# ============================================================
# 30-49 工艺条件（ProcessCondition / ProcessParameter）相关
# ============================================================
ERROR_PROCESS_CONDITION_NOT_FOUND      = BizErrorCode.create(MOD_PROCESS, 30, "工艺条件不存在")
ERROR_PROCESS_CONDITION_ALREADY_EXISTS  = BizErrorCode.create(MOD_PROCESS, 31, "工艺条件已存在")
ERROR_PROCESS_PARAMETER_NOT_FOUND      = BizErrorCode.create(MOD_PROCESS, 32, "工艺参数不存在")
# 【注意】code 33 原为「工艺参数无效」（ERROR_PROCESS_PARAMETER_INVALID）——
#    全项目零引用 ⇒ 按 YAGNI 删掉，需要时再加；**code 33 留空不复用**。
ERROR_PROCESS_PARAMETER_GENERATION_FAILED = BizErrorCode.create(MOD_PROCESS, 34, "工艺参数生成失败")
ERROR_PROCESS_SNAPSHOT_INVALID         = BizErrorCode.create(MOD_PROCESS, 35, "工艺条件快照无效")
ERROR_PROCESS_INSUFFICIENT_FIELDS      = BizErrorCode.create(MOD_PROCESS, 36, "工艺参数输入字段不足")
# 归档轮次（已落库试模评价）参数不可改；评价仍可改（两者生命周期不同，分开设防）
ERROR_PROCESS_ROUND_SEALED             = BizErrorCode.create(MOD_PROCESS, 37, "该调机轮次已归档，参数不可修改")
# 算出来的参数值超出机台对它设定的可设定上限（注射压力 / 保压压力 / 注射位置 …）
# ⇒ 机台根本设不进去 ⇒ 直接拒绝本轮优化。
# 【注意】**标题只说事实、不下结论**：超出上限有两种可能 ——
#    ① 机台能力确实不够（要换机）；② **用户误输入**（改参数即可）⇒
#    结论由正文给出两条出路（「请检查参数设置或更换设备」），标题不预设是哪一种。
# 【注意】**所有参数一视同仁**：位置参数与压力 / 速度参数同构，唯一的差别是
#    「上限取自哪个能力项」（实测行程 vs 可设定最大值）—— 概念上是同一类东西。
ERROR_PROCESS_UNFIT_PARAM               = BizErrorCode.create(MOD_PROCESS, 38, "参数不符合机台设定要求")


# ============================================================
# 50-69 工艺规则（Rule）相关
# ============================================================
ERROR_RULE_KEYWORD_NOT_FOUND = BizErrorCode.create(MOD_PROCESS, 50, "工艺规则关键字不存在")
ERROR_RULE_KEYWORD_ALREADY_EXISTS = BizErrorCode.create(MOD_PROCESS, 51, "工艺规则关键字已存在")
ERROR_RULE_LIBRARY_NOT_FOUND  = BizErrorCode.create(MOD_PROCESS, 52, "规则库不存在")
ERROR_RULE_METHOD_NOT_FOUND   = BizErrorCode.create(MOD_PROCESS, 53, "规则方法不存在")


# ============================================================
# 70-89 工艺优化（Optimization）相关
# ============================================================
ERROR_OPTIMIZE_RECORD_NOT_FOUND = BizErrorCode.create(MOD_PROCESS, 70, "工艺优化记录不存在")
ERROR_OPTIMIZE_INFER_FAILED     = BizErrorCode.create(MOD_PROCESS, 71, "工艺优化推理失败")


# ============================================================
# 90-99 其他
# ============================================================
ERROR_DEFECT_FEEDBACK_INVALID = BizErrorCode.create(MOD_PROCESS, 90, "缺陷反馈无效")

# 91-99 规则挖掘（候选规则审核流）
ERROR_MINING_RULE_NOT_FOUND    = BizErrorCode.create(MOD_PROCESS, 91, "候选规则不存在")
ERROR_MINING_RULE_REVIEWED     = BizErrorCode.create(MOD_PROCESS, 92, "候选规则已审核")
ERROR_MINING_RULE_NOT_LANDABLE = BizErrorCode.create(MOD_PROCESS, 93, "候选规则无法落地")
