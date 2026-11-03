"""关键字元数据来源 —— `RuleKeyword`（ORM）↔ 内核 keyword 契约。

- `KeywordQueryService`：查库（依赖 ORM）
- `RuleKeywordAdapter`：契约转换（不查库）

关键字（`RuleKeyword`）没有 `rule_library` 外键，是公司级系统参数元数据
（ORM 侧 `unique_together = (company, keyword_name)`），与规则的隔离维度不同，
故分文件。

⚠️ **转换类已迁出本模块**（2026-10-28）：

- `RuleKeywordAdapter`（契约转换，零 ORM）→ `library/adapters.py`

迁出的原因与规则侧一致：文件来源（`library/files/`）要用同一个转换器把
本地 JSON 规约成内核契约，若转换器留在本模块，文件通道就得 import ORM
（依赖倒置的实质检验 = 高层不被低层实现拖住）。
本模块保留**兼容导出**，既有引用路径（`library.keywords.RuleKeywordAdapter`）不变。
"""

from typing import List

from process.algorithms.fuzzy.fuzzy_core.profiles import KeywordProfile
from process.algorithms.fuzzy.library.adapters import RuleKeywordAdapter
from process.models.rules import RuleKeyword


__all__ = ['KeywordQueryService', 'RuleKeywordAdapter']  # 后者为兼容导出


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
