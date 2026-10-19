"""molding-optima 工艺参数 Schema 定义

字段命名严格匹配 process/models/parameter.py。

对应 Model：ProcessParameter

包含：注射参数（6 段）、VP 切换、保压参数（5 段）、冷却参数、熔胶参数（4 段）、
      松退参数、料筒温度参数（10 段）。

独立 parameter service 的三类契约:
- ProcessParameterSchema       入参（flat 92 字段, 算法/优化/移植用）
- ProcessParameterListSchema   列表查询条件（按 parameter 字段过滤）

注 (2026-10-10): BatchDeleteParameterSchema 已删除, 批量删除 parameter 需求
应走 /processes/records/batch-delete/ (级联软删 condition + parameter)

UI 嵌套格式（前端 records 写入用, 独立于上面 92 字段 flat 契约）:
- SettingProcessSchema         嵌套结构 (5 段: injection/vp_switch/holding/metering/barrel_temperature)
- ProcessParameterNestSchema   顶层包装 (parameter 业务容器, 当前含 setting_process, 未来可扩展)

records 段子资源端点写入契约 (B 方案拆分后, condition_id 与 parameter_id 同在 URL):
- ProcessParameterUpdateSchema     更新 parameter (PUT /records/<condition_id>/parameter/<parameter_id>/)
                                 内部为 NEST 验证 (setting_process)

注: ProcessParameterSchema (FLAT) 与 ProcessParameterNestSchema (NEST) 互不替代,
    分别服务算法 / 移植 (FLAT) 与前端 UI (NEST) 两个业务场景。
"""
from datetime import date
from typing import Optional

from pydantic import Field

from extensions.schemas import BaseSchema, PaginationBaseSchema


class ProcessParameterSchema(BaseSchema):
    """工艺参数记录（DB 扁平字段, 与 ProcessParameter model 一一对应）

    用于算法/优化/移植场景的入参, 直接覆盖 DB 扁平列,
    方便算法以数字特征 (inj_pres_1, hold_pres_1 ...) 直接处理。
    """

    process_condition_id: Optional[int] = Field(None, description="所属工艺条件 ID")

    # --- 基本信息 ---
    param_code: Optional[str] = Field(None, description="工艺参数编号")
    param_source: Optional[str] = Field(None, description="参数来源")
    # 业务编号：前端可见，用于确定调机树中的基准节点
    # 与 process_condition_id 联合定位父节点（反查 parent_param.id）
    # 注意：这是业务编号（condition 内全局递增），不是数据库 ID
    parent_seq_idx: Optional[int] = Field(None, description="父参数业务编号（seq_idx）")
    seq_idx: Optional[int] = Field(None, description="序列序号")

    # --- 注射参数 (6段) ---
    inj_stg: Optional[int] = Field(None, description="注射段数 1-6")

    inj_spd_1: Optional[float] = Field(None, description="一段注射速度")
    inj_spd_2: Optional[float] = Field(None, description="二段注射速度")
    inj_spd_3: Optional[float] = Field(None, description="三段注射速度")
    inj_spd_4: Optional[float] = Field(None, description="四段注射速度")
    inj_spd_5: Optional[float] = Field(None, description="五段注射速度")
    inj_spd_6: Optional[float] = Field(None, description="六段注射速度")

    inj_pres_1: Optional[float] = Field(None, description="一段注射压力")
    inj_pres_2: Optional[float] = Field(None, description="二段注射压力")
    inj_pres_3: Optional[float] = Field(None, description="三段注射压力")
    inj_pres_4: Optional[float] = Field(None, description="四段注射压力")
    inj_pres_5: Optional[float] = Field(None, description="五段注射压力")
    inj_pres_6: Optional[float] = Field(None, description="六段注射压力")

    inj_pos_1: Optional[float] = Field(None, description="一段注射位置")
    inj_pos_2: Optional[float] = Field(None, description="二段注射位置")
    inj_pos_3: Optional[float] = Field(None, description="三段注射位置")
    inj_pos_4: Optional[float] = Field(None, description="四段注射位置")
    inj_pos_5: Optional[float] = Field(None, description="五段注射位置")
    inj_pos_6: Optional[float] = Field(None, description="六段注射位置")

    inj_t: Optional[float] = Field(None, description="注射时间")
    inj_dly_t: Optional[float] = Field(None, description="注射延时")

    # --- VP 切换参数 ---
    vps_mode: Optional[int] = Field(None, description="VP切换模式")
    vps_pos: Optional[float] = Field(None, description="VP切换位置")
    vps_t: Optional[float] = Field(None, description="VP切换时间")
    vps_pres: Optional[float] = Field(None, description="VP切换压力")
    vps_spd: Optional[float] = Field(None, description="VP切换速度")

    # --- 保压参数 (5段) ---
    hold_stg: Optional[int] = Field(None, description="保压段数 1-5")

    hold_pres_1: Optional[float] = Field(None, description="一段保压压力")
    hold_pres_2: Optional[float] = Field(None, description="二段保压压力")
    hold_pres_3: Optional[float] = Field(None, description="三段保压压力")
    hold_pres_4: Optional[float] = Field(None, description="四段保压压力")
    hold_pres_5: Optional[float] = Field(None, description="五段保压压力")

    hold_spd_1: Optional[float] = Field(None, description="一段保压速度")
    hold_spd_2: Optional[float] = Field(None, description="二段保压速度")
    hold_spd_3: Optional[float] = Field(None, description="三段保压速度")
    hold_spd_4: Optional[float] = Field(None, description="四段保压速度")
    hold_spd_5: Optional[float] = Field(None, description="五段保压速度")

    hold_t_1: Optional[float] = Field(None, description="一段保压时间")
    hold_t_2: Optional[float] = Field(None, description="二段保压时间")
    hold_t_3: Optional[float] = Field(None, description="三段保压时间")
    hold_t_4: Optional[float] = Field(None, description="四段保压时间")
    hold_t_5: Optional[float] = Field(None, description="五段保压时间")

    # --- 冷却参数 ---
    cool_t: Optional[float] = Field(None, description="冷却时间")

    # --- 熔胶参数 (4段) ---
    met_stg: Optional[int] = Field(None, description="熔胶段数 1-4")

    met_pres_1: Optional[float] = Field(None, description="一段熔胶压力")
    met_pres_2: Optional[float] = Field(None, description="二段熔胶压力")
    met_pres_3: Optional[float] = Field(None, description="三段熔胶压力")
    met_pres_4: Optional[float] = Field(None, description="四段熔胶压力")

    met_rot_spd_1: Optional[float] = Field(None, description="一段螺杆转速")
    met_rot_spd_2: Optional[float] = Field(None, description="二段螺杆转速")
    met_rot_spd_3: Optional[float] = Field(None, description="三段螺杆转速")
    met_rot_spd_4: Optional[float] = Field(None, description="四段螺杆转速")

    met_back_pres_1: Optional[float] = Field(None, description="一段背压")
    met_back_pres_2: Optional[float] = Field(None, description="二段背压")
    met_back_pres_3: Optional[float] = Field(None, description="三段背压")
    met_back_pres_4: Optional[float] = Field(None, description="四段背压")

    met_pos_1: Optional[float] = Field(None, description="一段熔胶位置")
    met_pos_2: Optional[float] = Field(None, description="二段熔胶位置")
    met_pos_3: Optional[float] = Field(None, description="三段熔胶位置")
    met_pos_4: Optional[float] = Field(None, description="四段熔胶位置")

    # --- 松退参数 ---
    pre_met_decomp_mode: Optional[int] = Field(None, description="熔胶前松退模式")
    pre_met_decomp_pres: Optional[float] = Field(None, description="熔胶前松退压力")
    pre_met_decomp_spd: Optional[float] = Field(None, description="熔胶前松退速度")
    pre_met_decomp_t: Optional[float] = Field(None, description="熔胶前松退时间")
    pre_met_decomp_dist: Optional[float] = Field(None, description="熔胶前松退距离")

    pst_met_decomp_mode: Optional[int] = Field(None, description="熔胶后松退模式")
    pst_met_decomp_pres: Optional[float] = Field(None, description="熔胶后松退压力")
    pst_met_decomp_spd: Optional[float] = Field(None, description="熔胶后松退速度")
    pst_met_decomp_t: Optional[float] = Field(None, description="熔胶后松退时间")
    pst_met_decomp_dist: Optional[float] = Field(None, description="熔胶后松退距离")

    met_lim_t: Optional[float] = Field(None, description="熔胶延时")
    met_end_pos: Optional[float] = Field(None, description="熔胶终止位置")

    # --- 料筒温度参数 (10段) ---
    brl_temp_stg: Optional[int] = Field(None, description="料筒温度段数 1-10")
    noz_temp: Optional[float] = Field(None, description="喷嘴温度")
    brl_temp_1: Optional[float] = Field(None, description="一段料筒温度")
    brl_temp_2: Optional[float] = Field(None, description="二段料筒温度")
    brl_temp_3: Optional[float] = Field(None, description="三段料筒温度")
    brl_temp_4: Optional[float] = Field(None, description="四段料筒温度")
    brl_temp_5: Optional[float] = Field(None, description="五段料筒温度")
    brl_temp_6: Optional[float] = Field(None, description="六段料筒温度")
    brl_temp_7: Optional[float] = Field(None, description="七段料筒温度")
    brl_temp_8: Optional[float] = Field(None, description="八段料筒温度")
    brl_temp_9: Optional[float] = Field(None, description="九段料筒温度")


class ProcessParameterListSchema(PaginationBaseSchema):
    """工艺参数列表查询条件（按 parameter 字段过滤）

    2026-10-12 改造:
    - URL 不再嵌套 /conditions/<id>/parameters/, condition_id 变 query 参数
    - condition_id 不传 -> 查全表 (后台 / 集成 API 场景)
    """

    condition_id: Optional[int] = Field(
        None,
        description="工艺条件 ID (可选, 过滤该 condition 下的 parameter)",
    )
    parent_seq_idx: Optional[int] = Field(None, description="父参数业务编号")
    seq_idx: Optional[int] = Field(None, description="序列序号")
    param_code: Optional[str] = Field(None, description="工艺参数编号（模糊匹配）")
    param_source: Optional[str] = Field(None, description="参数来源")
    created_after: Optional[date] = Field(None, description="创建起始日期")
    created_before: Optional[date] = Field(None, description="创建结束日期")


class ProcessParameterTreeSchema(BaseSchema):
    """工艺参数版本树查询条件

    2026-10-12 改造:
    - URL 不再嵌套 /conditions/<id>/parameter-tree/, condition_id 变 query 参数
    - condition_id 不传 -> 查全表 (后台 / 集成 API 场景)
    """

    condition_id: Optional[int] = Field(
        None,
        description="工艺条件 ID (可选, 过滤该 condition 下的 parameter)",
    )


# BatchDeleteParameterSchema 已删除 (2026-10-10):
# - 原用于 /processes/parameters/batch_delete/ 端点
# - 该端点已废弃 (单段 /parameters/ 段不再提供写操作)
# - 批量删除 parameter 需求应走 /processes/records/batch-delete/ (软删 condition, 级联 parameter)
#   参数: BatchIdsSchema (extensions.schemas 通用)


class SettingProcessSchema(BaseSchema):
    """前端 UI 嵌套结构（setting_process 内部）

    对应前端的 settingProcessForm, 用于 UI 提交 records 写入。
    service 内部通过 _frontend_to_condition_dict 转 130+ flat 字段写入 DB。

    设计选择: 内部字段用 dict (而非强类型子 schema), 因为:
    - table_data 是动态结构 `[{label, unit, sections: [n, ...]}, ...]`, 段数由 max_stage 决定
    - 子结构由前端 SettingProcess 组件维护, 后端只透传
    - 业务上 schema 只需保证 "五大段存在" 这层结构
    """

    injection: Optional[dict] = Field(
        None,
        description=(
            "注射参数 {max_stage, stage, table_data, injection_time, delay_time, cooling_time}"
        ),
    )
    vp_switch: Optional[dict] = Field(
        None,
        description="VP 切换 {mode, position, time, pressure, velocity}",
    )
    holding: Optional[dict] = Field(
        None,
        description="保压参数 {max_stage, stage, table_data}",
    )
    metering: Optional[dict] = Field(
        None,
        description=(
            "熔胶参数 {max_stage, stage, table_data, pre_decompress_mode, "
            "post_decompress_mode, decompress_table_data, delay_time, ending_position}"
        ),
    )
    barrel_temperature: Optional[dict] = Field(
        None,
        description="料筒温度 {max_stage, stage, table_data}",
    )


class ProcessParameterNestSchema(BaseSchema):
    """parameter 业务容器（前端 records 写入用）

    当前含:
    - setting_process: 5 段嵌套 (NEST 强验证)

    未来可扩展字段（直接平铺到本 schema, 不另起 schema）:
    - metadata: 参数元数据
    - algorithm_hint: 算法侧配置
    - 其他 parameter 业务相关字段
    """

    setting_process: Optional[SettingProcessSchema] = Field(
        None,
        description="工艺参数嵌套结构 (5 段: injection/vp_switch/holding/metering/barrel_temperature)",
    )


class ProcessParameterUpdateSchema(BaseSchema):
    """工艺参数更新（PUT /records/<condition_id>/parameter/<parameter_id>/ 写入契约, NEST 强验证）

    URL 同时含 condition_id + parameter_id (B 方案拆分后),
    业务上必校验 parameter_id belongs to condition_id (service 层负责)。

    注: body 仅含 parameter 业务容器 (未来可扩展字段), 无 condition 字段 (URL 提供)。
    """

    parameter: ProcessParameterNestSchema = Field(
        ...,
        description=(
            "parameter 业务容器 (当前含 setting_process)。"
            "PUT 时整个覆盖该 parameter 的字段 (NEST 强验证)。"
            "算法 / 移植请用 ProcessParameterSchema (FLAT)。"
        ),
    )
