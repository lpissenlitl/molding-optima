"""关键字元数据来源 —— `RuleKeyword`（ORM）↔ 内核 keyword 契约。

- `KeywordQueryService`：查库（依赖 ORM）
- `RuleKeywordAdapter`：契约转换（不查库）

关键字（`RuleKeyword`）没有 `rule_library` 外键，是公司级系统参数元数据
（ORM 侧 `unique_together = (company, keyword_name)`），与规则的隔离维度不同，
故分文件。
"""

from typing import Any, Dict, List

from process.algorithms.fuzzy.fuzzy_core.profiles import KeywordProfile
from process.models.rules import RuleKeyword


# --- KeywordQueryService: 查库 → 内核契约 ---

class KeywordQueryService:
    """关键字（论域元数据）查询服务。

    产出同一种内核契约：规则侧取 `List[RuleProfile]`，本类取 `List[KeywordProfile]`。

    关键字侧比规则侧简单：没有选库 / 特异级 / 档位过滤那套路由，
    只需按参数名批量取。
    """

    @staticmethod
    def get_keywords_by_names(names: List[str]) -> List[KeywordProfile]:
        """按参数名批量查询 `RuleKeyword`，产出内核契约 `KeywordProfile`。

        不排序：ORM 的 `__in` 查询与顺序无关。需要稳定序的调用方要自己先排 ——
        `ResourceRepository.get_keywords_by_names` 就是先排再转发。
        """
        if not names:
            return []
        keywords = RuleKeyword.objects.filter(keyword_name__in=names)
        return RuleKeywordAdapter.to_keyword_profiles(keywords)


# --- RuleKeywordAdapter: RuleKeyword → KeywordProfile ---

class RuleKeywordAdapter:
    """`RuleKeyword` → `KeywordProfile`（内核输入契约）。纯转换器，不访问数据库。

    产出**契约对象**而不是裸 dict —— 内核输入格式由 `fuzzy_core/profiles.py`
    定义，本适配器只负责把来源侧的字段搬过去。
    """

    @staticmethod
    def to_keyword_profiles(keywords: List[Any]) -> List[KeywordProfile]:
        """ORM 实例 / dict 列表 → `KeywordProfile` 列表。"""
        return [
            RuleKeywordAdapter._dict_to_profile(kw)
            if isinstance(kw, dict)
            else RuleKeywordAdapter._orm_to_profile(kw)
            for kw in keywords
        ]

    @staticmethod
    def _orm_to_profile(keyword: RuleKeyword) -> KeywordProfile:
        step = getattr(keyword, 'step', None)
        if step is None:
            # 兜底：step 字段为空时使用区间范围的 1/3
            try:
                span = float(keyword.range_max) - float(keyword.range_min)
                step = max(span / 3.0, 0.01)
            except Exception:
                step = 1.0
        return KeywordProfile(
            keyword=keyword.keyword_name,
            lvl=int(keyword.fuzzy_level or 3),
            min_val=float(keyword.range_min),
            max_val=float(keyword.range_max),
            step=float(step),
        )

    @staticmethod
    def _dict_to_profile(keyword: Dict[str, Any]) -> KeywordProfile:
        step = keyword.get('step')
        if step is None:
            try:
                span = float(keyword['range_max']) - float(keyword['range_min'])
                step = max(span / 3.0, 0.01)
            except Exception:
                step = 1.0
        return KeywordProfile(
            keyword=keyword.get('keyword_name') or keyword.get('keyword'),
            lvl=int(keyword.get('fuzzy_level', 3)),
            min_val=float(keyword.get('range_min', 0)),
            max_val=float(keyword.get('range_max', 1)),
            step=float(step),
            # dict 输入可带元数据来源标记（推测论域）；ORM 输入无此概念
            meta_source=keyword.get('meta_source', ''),
        )
