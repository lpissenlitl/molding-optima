"""转换层 —— 来源侧记录 → 内核输入契约（零 ORM）。

两条线的**转换类**都在这里：

- `RuleAdapter`：`RuleRecord` → `RuleProfile`（规则侧）
- `RuleKeywordAdapter`：ORM 实例 / dict → `KeywordProfile`（关键字侧）

⚠️ **为什么独立成文件**：转换器必须能被**零 ORM** 地引入 —— 文件来源
（`library/files/`）要用它们把本地数据规约成内核契约，不能因为一个转换器
就把 Django ORM 拖进来。

⚠️ **转换器接受来源无关的输入**：
- `RuleAdapter` 收 `RuleRecord`（`library/contracts.py`），**不收 ORM 实例** ——
  数据库来源先把 `RuleMethod` 规约成 `RuleRecord`，文件来源把 JSON 规约成
  `RuleRecord`，转换器只认后者 ⇒ 两个来源的契约构造口径完全一致。
- `RuleKeywordAdapter` 同时收 ORM 实例（鸭子类型，不 import ORM）与 dict ——
  dict 分支是文件来源的直接入口。

`library/rules.py` / `library/keywords.py` 保留兼容导出，既有引用路径不变。
"""

import logging
from typing import Any, Dict, List, Optional

from process.algorithms.fuzzy.fuzzy_core.profiles import KeywordProfile, RuleProfile
from process.algorithms.fuzzy.library.contracts import (
    LibraryRecord,
    RuleRecord,
)
from process.algorithms.fuzzy.library.semantics import RuleService


logger = logging.getLogger(__name__)


# --- RuleRecordAdapter: ORM RuleMethod → RuleRecord ---

class RuleRecordAdapter:
    """ORM `RuleMethod`（鸭子类型）→ `RuleRecord`（来源无关记录）。纯转换器。

    ⚠️ **不 import ORM**：只按属性名读取（`getattr`），因此本类零 ORM 依赖，
      可与文件来源的转换器同处一个文件。

    `source_ref` 格式与原实现保持一致（`RuleMethod:<id>`）⇒ 溯源信息不因
    本次重构而变化。
    """

    @staticmethod
    def to_record(method: Any) -> RuleRecord:
        return RuleRecord(
            defect_code=getattr(method, 'defect_code', None) or '',
            rule_description=getattr(method, 'rule_description', None) or '',
            priority=float(getattr(method, 'priority', None) or 1.0),
            polymer_abbreviation=getattr(method, 'polymer_abbreviation', None),
            product_category=getattr(method, 'product_category', None),
            source_ref=f'RuleMethod:{getattr(method, "id", "")}',
        )

    @staticmethod
    def from_dict(data: Dict[str, Any], library_code: str = '') -> RuleRecord:
        """dict（文件来源）→ `RuleRecord`。纯转换器。

        ⚠️ **与 `to_record` 的字段口径逐条一致**（包括 ``priority`` 的
          ``or 1.0`` 归一）—— 两侧转出来的记录**逐字段相等** ⇒ 编排层
          在两条路径下的行为必然相同。

        ⚠️ ``source_ref`` 用 ``file:<库码>#<规则主键>`` 格式（与数据库来源的
          ``RuleMethod:<id>`` 区分开）⇒ 溯源时能一眼看出这条规则来自哪个通道。
        """
        return RuleRecord(
            defect_code=data.get('defect_code') or '',
            rule_description=data.get('rule_description') or '',
            priority=float(data.get('priority') or 1.0),
            polymer_abbreviation=data.get('polymer_abbreviation'),
            product_category=data.get('product_category'),
            source_ref=(data.get('source_ref')
                        or f'file:{library_code}#{data.get("id", "")}'),
        )


# --- LibraryRecordAdapter: ORM RuleLibrary → LibraryRecord ---

class LibraryRecordAdapter:
    """ORM `RuleLibrary`（鸭子类型）→ `LibraryRecord`（来源无关记录）。纯转换器。

    ⚠️ **不 import ORM**：只按属性名读取（`getattr`）。
    """

    @staticmethod
    def to_record(library: Any) -> LibraryRecord:
        return LibraryRecord(
            library_code=getattr(library, 'library_code', None) or '',
            library_name=getattr(library, 'library_name', None) or '',
            library_type=getattr(library, 'library_type', None) or '',
            priority=int(getattr(library, 'priority', None) or 0),
            is_active=bool(getattr(library, 'is_active', True)),
            library_id=getattr(library, 'id', None),
            source_ref=f'RuleLibrary:{getattr(library, "id", "")}',
        )

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> LibraryRecord:
        """dict（文件来源）→ `LibraryRecord`。纯转换器。

        ⚠️ **与 `to_record` 的字段口径逐条一致**（含 ``library_type`` 的
          ``or ''`` 归一、``priority`` 的 ``or 0`` 归一）⇒ 两侧转出来的记录
          **逐字段相等** ⇒ 选库与排序在两条路径下的结果必然相同。
        """
        return LibraryRecord(
            library_code=data.get('library_code') or '',
            library_name=data.get('library_name') or '',
            library_type=data.get('library_type') or '',
            priority=int(data.get('priority') or 0),
            is_active=bool(data.get('is_active', True)),
            library_id=data.get('library_id'),
            source_ref=data.get('source_ref') or '',
        )


# --- RuleAdapter: RuleRecord → RuleProfile ---

class RuleAdapter:
    """`RuleRecord` → `RuleProfile`（内核输入契约）。纯转换器，不访问数据库。

    与 `RuleKeywordAdapter` 成对：那边管关键字侧，这边管规则侧。

    规则串取记录里的 `rule_description`（权威来源）；结论形态由
    `RuleService.classify_conclusion_kind` 判定 —— 语义判定归 `RuleService`，
    本类只负责把来源侧字段搬进契约档案。

    ⚠️ **本类也是规则串的唯一解析点**：拆一次，把产物放进 `RuleProfile.parsed`，
    下游（编排层 / 内核第 4 层）一律复用 ⇒ 同一条规则串在整条链路上只拆一次。
    """

    @staticmethod
    def to_rule_profile(
        record: RuleRecord,
        specificity: int,
    ) -> Optional[RuleProfile]:
        """`RuleRecord` → `RuleProfile`；规则串为空返回 `None`。

        Args:
            record: 来源无关的规则记录（`library/contracts.py`）。
            specificity: 特异级 1~4（**规则相对当前上下文**的特异度，
                由 `RuleService.resolve_specificity` 算出，不在规则记录里）。
        """
        rule_description = (record.rule_description or '').strip()
        if not rule_description:
            return None
        # ★ 规则串**只拆一次**：拆解产物随档案一起传给下游
        #   （编排层判缺陷名、内核第 4 层建对象都直接复用它）。
        #   拆解是纯函数，结果只与规则串有关 ⇒ 拆一次无损。
        parsed = RuleService.parse_rule(rule_description)
        return RuleProfile(
            rule_description=rule_description,
            priority=float(record.priority or 1.0),
            conclusion_kind=RuleService.classify_conclusion_kind(
                rule_description, parsed,
            ),
            specificity=specificity,
            # 溯源标识（字符串，不携带来源对象）
            source_ref=record.source_ref,
            # 拆解产物（下游复用，避免重复拆解）
            parsed=parsed,
        )


# --- RuleKeywordAdapter: ORM 实例 / dict → KeywordProfile ---

class RuleKeywordAdapter:
    """关键字元数据 → `KeywordProfile`（内核输入契约）。纯转换器，不访问数据库。

    产出**契约对象**而不是裸 dict —— 内核输入格式由 `fuzzy_core/profiles.py`
    定义，本适配器只负责把来源侧的字段搬过去。

    输入两种形态（鸭子类型，**不 import ORM**）：
    - ORM 实例（数据库来源）：读 `.keyword_name` / `.range_min` / ... 属性；
    - dict（文件来源）：读 ``keyword_name`` / ``range_min`` / ... 键。
    """

    @staticmethod
    def to_keyword_profiles(keywords: List[Any]) -> List[KeywordProfile]:
        """ORM 实例 / dict 列表 → `KeywordProfile` 列表。

        ⚠️ **论域不可用的条目会被跳过**（并留一条 warning），而不是让整批崩掉。

        历史行为：一条 `range_min/range_max` 缺失或非数值的 keyword ⇒
        `float(None)` 抛 TypeError ⇒ 整个 `get_keywords_by_names` 失败 ⇒
        engine 兜底 ⇒ **全部字段**退化为「推测论域」（门控位置靠猜）。
        一条脏数据拖垮整批元数据 ⇒ 现改为「跳过坏数据、保住好数据」。
        """
        profiles: List[KeywordProfile] = []
        for kw in keywords:
            profile = (RuleKeywordAdapter._dict_to_profile(kw)
                       if isinstance(kw, dict)
                       else RuleKeywordAdapter._attr_to_profile(kw))
            if profile is not None:
                profiles.append(profile)
        return profiles

    @staticmethod
    def _derive_step(min_val: float, max_val: float, source: str) -> float:
        """论域跨度 → step（跨度 / 3，下限 0.01）。

        ⚠️ **不留裸 except**：算不出来就记一条 warning 再退回 1.0。
        静默兜底会让「论域取错」变得不可查 —— 与 `nets.py` 的
        「禁止静默降级」是同一原则。
        """
        span = max_val - min_val
        if span <= 0:
            logger.warning(
                '[RuleKeywordAdapter] %s 论域跨度非法（%r ~ %r），step 退回 1.0',
                source, min_val, max_val)
            return 1.0
        return max(span / 3.0, 0.01)

    @staticmethod
    def _attr_to_profile(keyword: Any) -> Optional[KeywordProfile]:
        """ORM 实例（鸭子类型）→ `KeywordProfile`；**论域不可用时返回 None**（跳过该条）。"""
        name = getattr(keyword, 'keyword_name', None)
        raw_min = getattr(keyword, 'range_min', None)
        raw_max = getattr(keyword, 'range_max', None)
        try:
            min_val = float(raw_min)
            max_val = float(raw_max)
        except (TypeError, ValueError):
            logger.warning(
                '[RuleKeywordAdapter] %s 论域边界不可用（range_min=%r, range_max=%r），已跳过该关键词',
                name, raw_min, raw_max)
            return None
        if min_val >= max_val:
            logger.warning(
                '[RuleKeywordAdapter] %s 论域区间非法（range_min=%r >= range_max=%r），已跳过该关键词',
                name, min_val, max_val)
            return None

        step = getattr(keyword, 'step', None)
        if step is None:
            # 兜底：step 字段为空时使用区间范围的 1/3
            step = RuleKeywordAdapter._derive_step(min_val, max_val, name)
        else:
            try:
                step = float(step)
            except (TypeError, ValueError):
                logger.warning(
                    '[RuleKeywordAdapter] %s step 非数值（%r），按论域跨度重算',
                    name, getattr(keyword, 'step', None))
                step = RuleKeywordAdapter._derive_step(min_val, max_val, name)

        return KeywordProfile(
            keyword=name,
            lvl=int(getattr(keyword, 'fuzzy_level', None) or 3),
            min_val=min_val,
            max_val=max_val,
            step=float(step),
        )

    @staticmethod
    def _dict_to_profile(keyword: Dict[str, Any]) -> Optional[KeywordProfile]:
        """dict → `KeywordProfile`；**论域不可用时返回 None**（跳过该条）。"""
        name = keyword.get('keyword_name') or keyword.get('keyword')
        try:
            min_val = float(keyword.get('range_min', 0))
            max_val = float(keyword.get('range_max', 1))
        except (TypeError, ValueError):
            logger.warning(
                '[RuleKeywordAdapter] %s 论域边界不可用（range_min=%r, range_max=%r），已跳过该关键词',
                name, keyword.get('range_min'), keyword.get('range_max'))
            return None
        if min_val >= max_val:
            logger.warning(
                '[RuleKeywordAdapter] %s 论域区间非法（range_min=%r >= range_max=%r），已跳过该关键词',
                name, min_val, max_val)
            return None

        step = keyword.get('step')
        if step is None:
            step = RuleKeywordAdapter._derive_step(min_val, max_val, name)
        else:
            try:
                step = float(step)
            except (TypeError, ValueError):
                logger.warning(
                    '[RuleKeywordAdapter] %s step 非数值（%r），按论域跨度重算',
                    name, keyword.get('step'))
                step = RuleKeywordAdapter._derive_step(min_val, max_val, name)

        return KeywordProfile(
            keyword=name,
            lvl=int(keyword.get('fuzzy_level', 3)),
            min_val=min_val,
            max_val=max_val,
            step=float(step),
            # dict 输入可带元数据来源标记（推测论域）；ORM 输入无此概念
            meta_source=keyword.get('meta_source', ''),
        )
