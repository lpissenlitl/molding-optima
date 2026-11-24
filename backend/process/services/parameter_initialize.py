"""工艺参数初始化推理服务。

对应接口：
- POST /api/processes/algorithms/initialize/                  业务主流程：基于 masterdata ID 推理初始工艺
- POST /api/processes/algorithms/initialize-from-condition/   业务另一场景：基于源 condition 复制初始工艺
- POST /api/processes/algorithms/initialize-from-provided/    纯推理：调用方提供完整 4 维 dict

流程逻辑：入口适配 → 数据前处理 → 推理算法 → 输出后处理。
术语：4 维上下文统一顺序 mold → machine → polymer → process_set；一律用 "mold" 不用 "product"
（mold_info 覆盖模具级 + 产品/浇口/壁厚派生）。
process_context 记录本次接口调用的入参快照（shot_index / injection_index / process_set），
便于事后审计与调用复现——ORM 表达不了。

Service 层职责：
- 入口适配：masterdata ID → ORM 实例
- 数据前处理：ORM → process_context_snapshot（完整快照，便于历史回溯）
- 输出后处理：4 维算法结果 → 拍扁为 ProcessParameter + TuningRecord 落库
- 推理算法：委托给 algorithms/expert/ProcessInitializer（含 DataValidator）
  校验失败 raise ValueError，service 层转 BizException 400
- 设定值能力校验：算出来的初值超出允许区间（上限按参数取自哪个设备字段）⇒
  BizException 400（初值根本设不进去 ⇒ 不产出错参数）
"""

import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional

from django.db import transaction
from extensions.exceptions import BizException
from masterdata.models.injection import InjectionMoldingMachine
from masterdata.models.material import Polymer
from masterdata.models.mold import Mold
from process.algorithms.expert.initializer import ProcessInitializer
from process.algorithms.expert.rule_matcher import InitRuleMatcher
from .optimize_chain.integrate_params import (  # 第3层：整合参数
    integrate,
    numeric_snapshot,
)
from .optimize_chain.check_params import validate  # 第4层：校验参数合理性
from process.exceptions import (
    ERROR_MACHINE_NOT_FOUND,
    ERROR_MOLD_NOT_FOUND,
    ERROR_POLYMER_NOT_FOUND,
    ERROR_PROCESS_CONDITION_NOT_FOUND,
    ERROR_PROCESS_INSUFFICIENT_FIELDS,
    ERROR_PROCESS_PARAMETER_NOT_FOUND,
)
from process.models.condition import ProcessCondition
from process.models.parameter import ProcessParameter
from process.models.tuning_record import TuningRecord
from utils.objects import safe_json
from .shared.spec_extract import (  # 参数提取专区（优化 / 初始化两条链路共用；按需自取）
    build_machine_info_from_snapshot,
    build_mold_info_from_snapshot,
    build_polymer_info_from_snapshot,
)
from .shared.param_limits import (  # 参数限值专区（准备 + 校验，与优化链路共用同一判据与文案）
    build_limits,  # 允许区间表取值（守卫只收表，取值归本层）
    guard_parameter_limits,  # 统一的参数区间守卫
)

logger = logging.getLogger(__name__)


# --- 快照构建层：ORM → 完整快照（process_context_snapshot） ---
# 设计原则：
#   - 快照是"完整的工艺上下文"，落库到 ProcessCondition.process_context_snapshot
#   - 快照包含：模具 + 选定 GatingSystem（含全部 cavities/gates）+ 选定 InjectionUnit + Polymer
#   - 快照与算法入参严格分离：快照完整结构 → service 从中抽取算法需要的字段
#   - 快照保留 masterdata 原始完整字段，便于历史回溯（masterdata 变更也不影响历史快照）
#
# 算法层不需要的字段依然保留在快照中：这是为了"反查 / 复现 / 调试"。
# 不要在快照层做"选 cavity / 选 gate"的操作——那是算法的职责。

def _build_mold_snapshot(
    mold,
    shot_index: int = 0,
) -> Dict[str, Any]:
    """从 Mold 主表 + 选定的 GatingSystem 构建完整 mold 快照。

    Args:
        mold: Mold ORM 实例
        shot_index: 模具的第几射（0-based），对应 mold.gating_systems[shot_index]

    Returns:
        {
            "mold": {Mold 主表全部字段},
            "gating_system": {
                ...GatingSystem 字段,
                "cavities": [{Cavity 字段, "gates": [{Gate 字段}]}],
            }
        }
    """
    # 重新查询以触发 prefetch（下游 to_dict(include_rvs=True) 需要 _prefetched_objects_cache）
    mold_cls = type(mold)
    fresh_mold = mold_cls.objects.filter(pk=mold.pk, is_deleted=False).prefetch_related(
        'gating_systems__cavities__gates'
    ).first()
    if fresh_mold is None:
        raise BizException(ERROR_MOLD_NOT_FOUND, f"模具不存在或已删除: id={mold.pk}")
    mold = fresh_mold

    snapshot: Dict[str, Any] = {
        "mold": mold.to_dict(),
    }

    gating_systems = list(mold.gating_systems.all() if hasattr(mold, 'gating_systems') else [])
    if shot_index < len(gating_systems):
        gating = gating_systems[shot_index]
        snapshot["gating_system"] = gating.to_dict(include_rvs=True)
    else:
        snapshot["gating_system"] = None
        logger.warning(
            "shot_index=%s 超出 mold(id=%s) 的 gating_systems 范围（共 %s 套）",
            shot_index, mold.id, len(gating_systems),
        )

    return snapshot


def _build_machine_snapshot(
    machine,
    injection_index: int = 0,
) -> Dict[str, Any]:
    """从 InjectionMoldingMachine 主表 + 选定的 InjectionUnit 构建完整 machine 快照。

    Args:
        machine: InjectionMoldingMachine ORM 实例
        injection_index: 注塑机的第几个射台（0-based），对应 machine.injection_units[injection_index]

    Returns:
        {
            "machine": {Machine 主表全部字段},
            "injection_unit": {InjectionUnit 全部字段} | None
        }
    """
    snapshot: Dict[str, Any] = {
        "machine": machine.to_dict(),
    }

    injection_units = list(machine.injection_units.all() if hasattr(machine, 'injection_units') else [])
    if injection_index < len(injection_units):
        unit = injection_units[injection_index]
        snapshot["injection_unit"] = unit.to_dict()
    else:
        snapshot["injection_unit"] = None
        logger.warning(
            "injection_index=%s 超出 machine(id=%s) 的 injection_units 范围（共 %s 个）",
            injection_index, machine.id, len(injection_units),
        )

    return snapshot


def _build_polymer_snapshot(polymer) -> Dict[str, Any]:
    """从 Polymer 构建完整 polymer 快照（Polymer 无 1:N 关系，扁平即可）。

    Returns:
        {"polymer": {Polymer 全部字段}}
    """
    return {
        "polymer": polymer.to_dict(),
    }


def _build_process_context_snapshot(
    mold_snapshot: Dict[str, Any],
    machine_snapshot: Dict[str, Any],
    polymer_snapshot: Dict[str, Any],
    process_set: Optional[Dict[str, Any]] = None,
    shot_index: int = 0,
    injection_index: int = 0,
) -> Dict[str, Any]:
    """聚合 4 个维度的快照为完整的 process_context_snapshot。

    顶层额外字段：
      - version: 快照格式版本
      - captured_at: 快照生成时间（strftime 格式）
      - shot_index / injection_index: 索引信息

    datetime/date 字段统一走 utils.objects.safe_json 处理
    （递归把 datetime/date 转 strftime 字符串，处理 Decimal/None）。
    """
    raw = {
        "version": "1.0",
        "captured_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "shot_index": shot_index,
        "injection_index": injection_index,
        "mold_info": mold_snapshot,
        "machine_info": machine_snapshot,
        "polymer_info": polymer_snapshot,
        "process_set": process_set or {},
    }
    return safe_json(raw)


# --- 越限守卫（所有参数统一按允许区间判）---
# 【注意】实现见 :mod:`process.services.shared.param_limits` —— 与优化链路共用同一判据、
#    同一错误码、同一文案 ⇒ 同一台机、同一产品，初始化报错说什么、优化报错也说什么。


# 快照路径：ORM → snapshot → 4 维算法入参
# 快照保留完整 masterdata 上下文（便于反查/复现/历史回溯），两个 Mode 共享同一套 snapshot builders。
# initialize-from-provided 入口跳过这一步（前端已直接提供完整 4 维 dict）。

# --- 顶层常量 + 核心推理算法 ---
_INIT_PARAM_SOURCE = "algorithm_init"  # 工艺参数源标记，写入 ProcessParameter.param_source


# ProcessParameter 可拷贝的业务字段名（手工列出，避免依赖 Django ORM 不在 service 内启动）
_COPYABLE_PARAM_FIELDS = (
    # 注射参数
    'inj_stg',
    'inj_spd_1', 'inj_spd_2', 'inj_spd_3', 'inj_spd_4', 'inj_spd_5', 'inj_spd_6',
    'inj_pres_1', 'inj_pres_2', 'inj_pres_3', 'inj_pres_4', 'inj_pres_5', 'inj_pres_6',
    'inj_pos_1', 'inj_pos_2', 'inj_pos_3', 'inj_pos_4', 'inj_pos_5', 'inj_pos_6',
    'inj_t', 'inj_dly_t',
    # VP 切换参数
    'vps_mode', 'vps_pos', 'vps_t', 'vps_pres', 'vps_spd',
    # 保压参数
    'hold_stg',
    'hold_pres_1', 'hold_pres_2', 'hold_pres_3', 'hold_pres_4', 'hold_pres_5',
    'hold_spd_1', 'hold_spd_2', 'hold_spd_3', 'hold_spd_4', 'hold_spd_5',
    'hold_t_1', 'hold_t_2', 'hold_t_3', 'hold_t_4', 'hold_t_5',
    # 冷却
    'cool_t',
    # 熔胶参数
    'met_stg',
    'met_pres_1', 'met_pres_2', 'met_pres_3', 'met_pres_4',
    'met_rot_spd_1', 'met_rot_spd_2', 'met_rot_spd_3', 'met_rot_spd_4',
    'met_back_pres_1', 'met_back_pres_2', 'met_back_pres_3', 'met_back_pres_4',
    'met_pos_1', 'met_pos_2', 'met_pos_3', 'met_pos_4',
    # 松退参数
    'pre_met_decomp_mode', 'pre_met_decomp_pres', 'pre_met_decomp_spd',
    'pre_met_decomp_t', 'pre_met_decomp_dist',
    'pst_met_decomp_mode', 'pst_met_decomp_pres', 'pst_met_decomp_spd',
    'pst_met_decomp_t', 'pst_met_decomp_dist',
    'met_lim_t', 'met_end_pos',
    # 料筒温度
    'brl_temp_stg', 'noz_temp',
    'brl_temp_1', 'brl_temp_2', 'brl_temp_3', 'brl_temp_4', 'brl_temp_5',
    'brl_temp_6', 'brl_temp_7', 'brl_temp_8', 'brl_temp_9',
)


class ParameterInitializeService:
    """工艺参数初始化推理服务（3 个公开入口）。

    字段约定：
      - process_context_snapshot: 后端自动构建的不可变快照（完整 masterdata 上下文）
      - process_context:         后端自动填的"调用入参快照"（记录本次调用传了什么，便于审计）

    入口见模块 docstring。
    """
    # --- initialize_from_masterdata 入口（完整链路：入口适配 + 快照 + 推理 + 落库） ---
    @staticmethod
    def initialize_from_masterdata(
        mold_id: int,
        injection_machine_id: int,
        polymer_id: int,
        shot_index: int = 0,
        injection_index: int = 0,
        process_set: Optional[Dict[str, Any]] = None,
        company_id: Optional[int] = None,
        organization_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """【from_masterdata】基于 masterdata ID 入口（首次推理 + 建档）。

        status / origin_type 由后端固定为 draft / ai_recommendation。
        condition_no 由 service 层自动生成（后端不可用户改）。

        shot_index = 模具的"第几射"（0=第一射）；injection_index = 注塑机的"第几个射台"（0=第一台）。
        二者决定本次工艺条件"哪台机哪个射台打哪个产品"。
        """

        with transaction.atomic():
            # Step 1: 入口适配
            mold = Mold.objects.filter(pk=mold_id).first()
            if mold is None:
                raise BizException(ERROR_MOLD_NOT_FOUND, f"模具不存在: id={mold_id}")

            machine = InjectionMoldingMachine.objects.filter(pk=injection_machine_id).first()
            if machine is None:
                raise BizException(ERROR_MACHINE_NOT_FOUND, f"注塑机不存在: id={injection_machine_id}")

            polymer = Polymer.objects.filter(pk=polymer_id).first()
            if polymer is None:
                raise BizException(ERROR_POLYMER_NOT_FOUND, f"材料不存在: id={polymer_id}")

            # Step 2a: 构建完整快照（ORM → snapshot）
            mold_snapshot = _build_mold_snapshot(mold, shot_index=shot_index)
            machine_snapshot = _build_machine_snapshot(machine, injection_index=injection_index)
            polymer_snapshot = _build_polymer_snapshot(polymer)
            snapshot = _build_process_context_snapshot(
                mold_snapshot=mold_snapshot,
                machine_snapshot=machine_snapshot,
                polymer_snapshot=polymer_snapshot,
                process_set=process_set,
                shot_index=shot_index,
                injection_index=injection_index,
            )

            # Step 2b: 从快照构建算法入参
            mold_info = build_mold_info_from_snapshot(mold_snapshot)
            machine_info = build_machine_info_from_snapshot(machine_snapshot)
            polymer_info = build_polymer_info_from_snapshot(polymer_snapshot)

            # Step 3: 推理算法
            result = ParameterInitializeService._infer_kernel(
                mold_info=mold_info,
                machine_info=machine_info,
                polymer_info=polymer_info,
                process_set=process_set,
                # 当前租户（**专家规则库的可见性上下文**）——
                # 平台公共大库 + 该租户自己的专家私库（后者覆盖前者同名 key）
                company_id=company_id,
            )

            # call_context：记录本次接口调用传了什么，审计/调试用
            call_context = {
                "interface": "from_masterdata",
                "shot_index": shot_index,
                "injection_index": injection_index,
                "process_set": process_set,
            }

            # Step 3.5: 设定值能力校验 —— 初值超出可设定范围 ⇒ 400 拒绝
            # （算出来的初值根本设不进去 ⇒ 落库就是让操作工去设一个
            #   设不进去的值 ⇒ 拒绝，不产出错参数）
            _guard_initial_params(
                values=process_params_to_flat(result['process']),
                machine_info=machine_info,
                interface_tag='from_masterdata',
            )

            # Step 4: 落库
            condition = ProcessCondition.objects.create(
                condition_no=_auto_condition_no(mold_id, shot_index),
                status="draft",
                origin_type="ai_recommendation",
                mold_id=mold_id,
                shot_index=shot_index,
                injection_machine_id=injection_machine_id,
                injection_index=injection_index,
                polymer_id=polymer_id,
                process_context=call_context,
                process_context_snapshot=snapshot,
                company_id=company_id,
                organization_id=organization_id,
            )
            parameter = _create_process_parameter(
                condition, result, company_id=company_id, organization_id=organization_id
            )
            # 对外响应 = 落库后的 condition / parameter 完整对象（与 optimize 同形）；
            # 顶层只留对外字段（零散 id 与 parameter 的 nested 形态不进响应，见 docs/optimize-api-contract.md §8）
            result = {k: v for k, v in result.items() if k not in ('process', 'param_source')}
            result['condition'] = condition.to_dict()
            result['parameter'] = parameter.to_dict()

            logger.info(
                "from_masterdata 完成: condition_id=%s, parameter_id=%s, shot_index=%s, injection_index=%s, rules=%s",
                condition.id, parameter.id, shot_index, injection_index, result['matched_rules'],
            )
        return result

    # ---------- initialize_from_condition 入口 ----------
    @staticmethod
    def initialize_from_condition(
        source_condition_id: int,
        process_set: Optional[Dict[str, Any]] = None,
        company_id: Optional[int] = None,
        organization_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """【from_condition】基于源 condition 复制初始工艺参数（不调推理算法）。

        复用已有合格工艺为新工艺起点，snapshot 用最新 masterdata 重建。
        输出：Condition(origin_type='legacy_import') + 拷贝自源 param 的 ProcessParameter。
        """
        with transaction.atomic():
            # Step 1: 入口适配（读源 condition 拿元数据）
            source = (
                ProcessCondition.objects
                .select_related('mold', 'injection_machine', 'polymer')
                .filter(pk=source_condition_id)
                .first()
            )
            if source is None:
                raise BizException(
                    ERROR_PROCESS_CONDITION_NOT_FOUND,
                    f"源工艺条件不存在: id={source_condition_id}",
                )

            source_mold_id = source.mold_id
            source_machine_id = source.injection_machine_id
            source_polymer_id = source.polymer_id
            source_shot_index = source.shot_index or 0
            source_injection_index = source.injection_index or 0

            # Step 2a: 重新检索最新 masterdata
            mold = Mold.objects.filter(pk=source_mold_id).first()
            if mold is None:
                raise BizException(ERROR_MOLD_NOT_FOUND, f"模具不存在: id={source_mold_id}")
            machine = InjectionMoldingMachine.objects.filter(pk=source_machine_id).first()
            if machine is None:
                raise BizException(ERROR_MACHINE_NOT_FOUND, f"注塑机不存在: id={source_machine_id}")
            polymer = Polymer.objects.filter(pk=source_polymer_id).first()
            if polymer is None:
                raise BizException(ERROR_POLYMER_NOT_FOUND, f"材料不存在: id={source_polymer_id}")

            mold_snapshot = _build_mold_snapshot(mold, shot_index=source_shot_index)
            machine_snapshot = _build_machine_snapshot(machine, injection_index=source_injection_index)
            polymer_snapshot = _build_polymer_snapshot(polymer)
            new_snapshot = _build_process_context_snapshot(
                mold_snapshot=mold_snapshot,
                machine_snapshot=machine_snapshot,
                polymer_snapshot=polymer_snapshot,
                process_set=process_set,
                shot_index=source_shot_index,
                injection_index=source_injection_index,
            )

            # Step 2b: 读源 condition 的最新 ProcessParameter（复制源）
            source_param = (
                ProcessParameter.objects
                .filter(process_condition_id=source_condition_id, is_deleted=False)
                .order_by('-id')
                .first()
            )
            if source_param is None:
                raise BizException(
                    ERROR_PROCESS_PARAMETER_NOT_FOUND,
                    f"源工艺条件下未找到工艺参数: condition_id={source_condition_id}",
                )

            # Step 3: 跳过推理算法

            # Step 4: 创建新 condition + 拷贝参数
            call_context = {
                "interface": "from_source_condition",
                "source_condition_id": source_condition_id,
                "source_parameter_id": source_param.id,
                "process_set": process_set,
            }
            new_condition = ProcessCondition.objects.create(
                condition_no=_auto_condition_no(source_mold_id, source_shot_index),
                status="draft",
                origin_type="legacy_import",
                mold_id=source_mold_id,
                shot_index=source_shot_index,
                injection_machine_id=source_machine_id,
                injection_index=source_injection_index,
                polymer_id=source_polymer_id,
                process_context=call_context,
                process_context_snapshot=new_snapshot,
                company_id=company_id,
                organization_id=organization_id,
            )
            new_parameter = _copy_process_parameter(
                source_param, new_condition, company_id=company_id, organization_id=organization_id
            )

            logger.info(
                "from_source_condition 完成: source_condition_id=%s, condition_id=%s, parameter_id=%s, copied_from_param_id=%s",
                source_condition_id, new_condition.id, new_parameter.id, source_param.id,
            )

            # 本入口复制源参数、不跑推理 ⇒ 没有推理产物
            return {
                "condition": new_condition.to_dict(),
                "parameter": new_parameter.to_dict(),
            }

    # --- initialize_from_provided 入口（只跑推理算法，跳过入口适配和落库） ---
    @staticmethod
    def initialize_from_provided(
        mold_info: Dict[str, Any],
        machine_info: Dict[str, Any],
        polymer_info: Dict[str, Any],
        process_set: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """【from_provided】纯推理入口：不查 DB、不落库、4 维 dict 直传（Provided）。

        适用场景：第三方集成（无 masterdata）、算法试算。
        service 既不查 DB，也不写 DB。
        """
        result = ParameterInitializeService._infer_kernel(
            mold_info=mold_info,
            machine_info=machine_info,
            polymer_info=polymer_info,
            process_set=process_set,
        )
        # 对外响应里的工艺参数一律 flat（与 optimize 的 parameter 同形）；顶层不保留 nested 的 process
        flat = process_params_to_flat(result['process'])
        result = {k: v for k, v in result.items() if k != 'process'}
        result['parameter'] = flat
        # 设定值能力校验（与 from_masterdata 同口径）：初值超出可设定范围 ⇒ 400 拒绝
        _guard_initial_params(
            values=result['parameter'],
            machine_info=machine_info,
            interface_tag='from_provided',
        )
        return result

    # --- 核心算法 —— 私有方法，三个入口共用 ---
    @staticmethod
    def _infer_kernel(
        mold_info: Dict[str, Any],
        machine_info: Dict[str, Any],
        polymer_info: Dict[str, Any],
        process_set: Optional[Dict[str, Any]] = None,
        company_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """纯算法推理：4 维输入 → 4 维参数输出（不查 DB、不写 DB、不涉及 ID）。

        三个公开入口（initialize_from_masterdata / initialize_from_condition /
        initialize_from_provided）共用本方法；
        不依赖 self/cls，无副作用（其他 _helper 全是模块顶层函数）。
        对应 parameter_optimize.py 的 _infer_kernel（同构、同名）。

        Args:
            mold_info / machine_info / polymer_info / process_set: 4 维推理上下文
            company_id: 当前租户（**专家规则库的可见性上下文**）——
                平台公共大库（全平台共用）+ 该租户自己的专家私库；
                私库**后加载 ⇒ 覆盖平台同名 key**（叶子级覆盖）。
                None = **无租户上下文**（第三方集成 / 离线 runner / 烟测）
                ⇒ 只用平台层（不过滤），保持现状。

        Returns:
            {
                "param_source", "matched_rules",
                "process": {...}, "mold_temp": {...}, "hot_runner": {...},
                "summary": {...}
            }
        """
        process_set = process_set or {}
        # 每次新建实例（不做类级缓存）—— 用户手动触发，低频，无性能问题
        rule_matcher = InitRuleMatcher(company_id=company_id)

        logger.info(
            "工艺参数推理: polymer=%s, gate_type=%s, weight=%s",
            polymer_info.get("abbreviation"),
            mold_info.get("gate_type"),
            mold_info.get("product_weight"),
        )

        # 算法层 DataValidator.validate 失败会 raise ValueError（如 "mold_info.runner_weight 缺失"）
        # service 层负责把 ValueError 转 BizException 400 + 保留真实错误信息
        # 避免中间件把它当 500 "内部错误" 丢参真实信息
        try:
            initializer = ProcessInitializer(
                mold_info=mold_info,
                machine_info=machine_info,
                polymer_info=polymer_info,
                process_set=process_set,
                rule_matcher=rule_matcher,
            )
            params = initializer.derive()
        except ValueError as e:
            logger.warning("工艺推理参数校验失败: %s", e)
            raise BizException(
                ERROR_PROCESS_INSUFFICIENT_FIELDS,
                f"算法参数校验失败 - {e}",
            ) from e
        matched_rules = list(rule_matcher.last_matched_codes)

        result = {
            "param_source": _INIT_PARAM_SOURCE,
            "matched_rules": matched_rules,
            "process": params.process.to_dict(),
            "mold_temp": params.mold_temp.to_dict(),
            "hot_runner": params.hot_runner.to_dict(),
        }

        logger.info("推理完成: 规则=%s", matched_rules)
        return result


def _auto_condition_no(mold_id: int, shot_index: int) -> str:
    """自动生成 condition_no：格式 C-{mold_id}-S{shot_index}-{ts}。"""
    ts = int(time.time() * 1000000) % 1000000
    return f"C-{mold_id}-S{shot_index}-{ts:06d}"


# --- 算法 nested 工艺参数 → flat 字段镜像（落库与 HTTP 响应共用）---
#
# 单一事实来源（契约统一）：
#   落库（ProcessParameter ORM）与对外 HTTP 响应都走本函数
#   ⇒ 落库的值与前端看到的值必然一致，不会出现「两处各拍一次」的语义漂移。
#
# 【注意】温度段位语义说明：
#   nested 的 brl_temp_steps[0] 是「料筒 1 段」，而前端 nested 结构约定
#   sections[0]=喷嘴、sections[1..9]=料筒 1..9 —— nested 下二者无法对齐。
#   flat 用 noz_temp + brl_temp_1..9 两个独立字段表达，歧义消失。
#
# 字段语义与 ProcessParameter ORM 一一对应（见 process/schemas/parameter.py）。
_FLAT_SINGLE_VALUE_FIELDS = [
    'inj_stg', 'inj_t', 'inj_dly_t',
    'vps_mode', 'vps_pos', 'vps_t', 'vps_pres', 'vps_spd',
    'hold_stg', 'cool_t',
    'met_stg', 'met_lim_t', 'met_end_pos',
    'pre_met_decomp_mode', 'pre_met_decomp_pres', 'pre_met_decomp_spd',
    'pre_met_decomp_t', 'pre_met_decomp_dist',
    'pst_met_decomp_mode', 'pst_met_decomp_pres', 'pst_met_decomp_spd',
    'pst_met_decomp_t', 'pst_met_decomp_dist',
    'brl_temp_stg', 'noz_temp',
]

# (nested 数组字段, flat 字段模板, 段数)
_FLAT_STEPS_MAPPINGS = [
    ('inj_spd_steps',   'inj_spd_{}', 6),
    ('inj_pres_steps',  'inj_pres_{}', 6),
    ('inj_pos_steps',   'inj_pos_{}', 6),
    ('hold_pres_steps', 'hold_pres_{}', 5),
    ('hold_spd_steps',  'hold_spd_{}', 5),
    ('hold_time_steps', 'hold_t_{}', 5),
    ('met_pres_steps',  'met_pres_{}', 4),
    ('met_rot_spd_steps', 'met_rot_spd_{}', 4),
    ('met_back_pres_steps', 'met_back_pres_{}', 4),
    ('met_pos_steps',   'met_pos_{}', 4),
    ('brl_temp_steps',  'brl_temp_{}', 9),
]


def process_params_to_flat(proc_dict: Dict[str, Any]) -> Dict[str, Any]:
    """算法 nested 工艺参数 → flat 字段镜像（与 ProcessParameter ORM 一一对应）。

    Args:
        proc_dict: ProcessParams.to_dict() 形态（含 inj_spd_steps 等数组字段）

    Returns:
        flat 字段 dict（inj_spd_1..6 / hold_t_1..5 / brl_temp_1..9 / noz_temp ...）

    输出约定：
    - 单值字段：值为 None 时**不输出**该 key（与历史落库行为一致）
    - 数组段字段：**恒输出**全部段位（缺位补 None），保证前端拿到完整段数
    """
    flat: Dict[str, Any] = {}
    for f in _FLAT_SINGLE_VALUE_FIELDS:
        if f in proc_dict and proc_dict[f] is not None:
            flat[f] = proc_dict[f]
    for src_attr, fmt, n_stages in _FLAT_STEPS_MAPPINGS:
        steps = proc_dict.get(src_attr) or []
        for i in range(n_stages):
            flat[fmt.format(i + 1)] = steps[i] if i < len(steps) else None
    return flat


def _guard_initial_params(
    *,
    values: Dict[str, Any],
    machine_info: Dict[str, Any],
    interface_tag: str,
    strict: bool = True,
) -> None:
    """初始化算出的初值 —— 统一的参数区间守卫。

    **所有参数都跟「允许区间」比**：parameter 里的参数**全都是设定值**（位置参数
    也是）⇒ 上限按参数取自哪个设备字段而定（机台可设定最大值 / 机台实测注射
    行程）⇒ **不分类、不设特例**，越界即拒绝（与优化链路同口径：同一守卫、
    同一错误码、同一文案）。

    【注意】**拒不拒是严格度策略**：strict=True ⇒ 越界即 400；strict=False ⇒
    只报不拒（测试算法时仍要拿到这组参数）。

    【注意】``initialize_from_condition`` **不跑推理算法**（复制源工艺的已有
    参数）⇒ 没有算法初值 ⇒ 不经过本函数。

    Args:
        values: 拍扁后的初值（业务字段名 → 数值）。
        machine_info: 算法入参 machine_info（含机台上限字段）。
        interface_tag: 本次调用标识（进日志，便于定位是哪一次调用）。
        strict: True ⇒ 越界即拒绝（400）；False ⇒ 只报不拒。

    Raises:
        BizException: 初值越限（ERROR_DATA_INVALID）。
    """
    guard_parameter_limits(
        parameters=values,
        limits=build_limits(machine_info),
        strict=strict,
        scope='initialize',
        interface_tag=interface_tag,
    )


def _create_process_parameter(
    condition,
    params_result: Dict[str, Any],
    company_id: Optional[int] = None,
    organization_id: Optional[int] = None,
):
    """把推理结果拍扁为 ProcessParameter 字段并落库（输出后处理）。

    接收 _infer_kernel 的返回 dict（4 维输出）。

    原子语义：
        本方法负责创建 ProcessParameter + 同步创建 TuningRecord；ProcessCondition
        由调用方负责创建。两者必须在同一个 `with transaction.atomic():` 里依次
        创建——任何一个报错都回滚，保证「工艺条件 ↔ 工艺参数 ↔ 试模记录」
        三元组的不可分性。详见 initialize_from_masterdata /
        initialize_from_condition 入口实现。

    业务契约：
        每个 ProcessParameter 同步创建 1 条 TuningRecord（result=pending），
        保证后续 optimize_from_condition 路径的 parameter_optimize._record_tuning_round
        能找到上一轮记录，避免「父参数缺少 TuningRecord」WARNING。
    """
    proc_dict = params_result['process']
    flat = {
        'process_condition': condition,
        'param_source': _INIT_PARAM_SOURCE,
        **process_params_to_flat(proc_dict),
    }

    # 第3层：整合参数（新建轮次没有旧值可比 ⇒ 不传导）
    integrated = integrate(flat)

    # 第4层：校验参数合理性（只报不阻断）
    validation = validate(integrated.values)
    if not validation.ok:
        logger.warning('create_process_parameter validation: %s', validation.summary())

    new_param = ProcessParameter.objects.create(
        **integrated.values, company_id=company_id, organization_id=organization_id
    )

    # 同步创建初始 TuningRecord（pending 状态，无缺陷反馈与实测观察）
    # 业务契约：ProcessParameter ↔ TuningRecord 1:1（见 parameter_optimize._create_new_round）
    TuningRecord.objects.create(
        process_parameter=new_param,
        defect_feedbacks=[],
        observations=[],
        result="pending",
        company_id=company_id,
        organization_id=organization_id,
    )

    return new_param


def _copy_process_parameter(
    source_param,
    target_condition,
    company_id: Optional[int] = None,
    organization_id: Optional[int] = None,
):
    """从 source_param 拷贝业务字段，创建新 ProcessParameter 挂到 target_condition。

    不拷贝的字段：
      - pk / id / created_at / updated_at / is_deleted / created_by / ...（系统字段）
      - process_condition（FK，必须重写）
      - parameter_no（新参数生成）
      - parent_param / seq_idx（调机树字段，新一轮调参重置）
      - param_source（标记为 template_copy）

    业务契约：同步创建 1 条初始 TuningRecord（result=pending），与 _create_process_parameter 一致，
    保证 ProcessParameter ↔ TuningRecord 1:1。
    """
    flat = {
        'process_condition': target_condition,
        'param_source': 'template_copy',
    }
    for field_name in _COPYABLE_PARAM_FIELDS:
        value = getattr(source_param, field_name, None)
        if value is not None:
            flat[field_name] = value

    # 第3层：整合参数（复制是「原样复制」⇒ 没有数值改动 ⇒ 不传导）
    integrated = integrate(flat, numeric_snapshot(source_param))

    # 第4层：校验参数合理性（只报不阻断）
    validation = validate(integrated.values)
    if not validation.ok:
        logger.warning('copy_process_parameter validation: %s', validation.summary())

    new_param = ProcessParameter.objects.create(
        **integrated.values, company_id=company_id, organization_id=organization_id
    )

    # 同步创建初始 TuningRecord（pending 状态）
    TuningRecord.objects.create(
        process_parameter=new_param,
        defect_feedbacks=[],
        observations=[],
        result="pending",
        company_id=company_id,
        organization_id=organization_id,
    )

    return new_param
