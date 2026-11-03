"""文件来源的资源仓库 —— `FileResourceRepository`（**零 ORM**）。

是 `library/contracts.py::AlgorithmResourceRepository` 协议的第二个实现
（兄弟实现：数据库来源 `library/repository.py::ResourceRepository`）。

两者对外契约**完全一致** ⇒ 编排层（`engine.py`）可以互换，不用知道
当前用的是哪个来源。

⚠️ **零 ORM**：本模块不 import 任何 Django 模块 —— 文件来源必须能在
  没有数据库的环境里跑。

⚠️ **共用编排层**：选库（`RuleAssembler.select_libraries`）与组装
  （`RuleAssembler.assemble`）都调 `library/assembly.py` 里的同一份实现
  ⇒ 两条路径的**选库结果、特异级、去重、排序必然一致**。
  本模块只负责两步：**选库索引从哪来** + **规则条目从哪来**。
"""

import logging
from typing import Dict, List, Optional

from process.algorithms.fuzzy.fuzzy_core.profiles import KeywordProfile, RuleProfile
from process.algorithms.fuzzy.library.assembly import (
    KeywordAssembler,
    RuleAssembler,
)
from process.algorithms.fuzzy.library.contracts import (
    LibraryRecord,
    RuleQueryContext,
)
from process.algorithms.fuzzy.library.files.loader import FileLibraryLoader
from process.algorithms.fuzzy.library.adapters import RuleKeywordAdapter


logger = logging.getLogger(__name__)


class FileResourceRepository:
    """**文件来源**的资源仓库。

    与 `ResourceRepository`（数据库来源）实现同一个协议
    （`AlgorithmResourceRepository`）⇒ 引擎侧可互换。

    用法：

    ```python
    from process.algorithms.fuzzy.library.files.repository import (
        FileResourceRepository,
    )
    repo = FileResourceRepository()                      # 默认目录
    repo = FileResourceRepository(root_dir='/tmp/rules') # 指定目录
    ```
    """

    #: 日志前缀（区分来源，便于排查是哪条通道触发的）
    SOURCE_LABEL = 'FileResourceRepository'

    def __init__(
        self,
        root_dir: Optional[str] = None,
        auto_reload: bool = True,
    ):
        """构造仓库。

        Args:
            root_dir: 数据根目录（默认 `library/files/data/`）。
            auto_reload: 文件改动后自动重读（改 JSON 立即生效）。
        """
        self._loader = FileLibraryLoader(root_dir=root_dir, auto_reload=auto_reload)

    @property
    def loader(self) -> FileLibraryLoader:
        """底层读取器（排查 / 自检用）。"""
        return self._loader

    # —— 编排：把规则库组织成算法要用的规则 ——————————————————

    def select_libraries(self, context: RuleQueryContext) -> List[LibraryRecord]:
        """根据上下文解析目标规则库（按优先级排序）。

        与数据库来源 `ResourceRepository.select_libraries` **对称**：
        候选编码与选库规则都调 `library/assembly.py` 的同一份实现 ⇒
        两条路径选中的库**逐条相同**（含顺序）。

        口径：显式指定 ⇒ 只用它；未指定 ⇒ **全量模糊库**
        （本仓库的 `load_libraries()` 本来就是全量索引，
        适用性交由 `RuleService.matches_context` / `resolve_specificity` 判定）。
        """
        codes = RuleAssembler.library_code_candidates(context)
        index = self._loader.load_libraries()
        return RuleAssembler.select_libraries(codes, index)

    def get_rules(self, context: RuleQueryContext) -> List[RuleProfile]:
        """按上下文匹配拉出规则，组装成内核输入契约。

        与数据库来源的 `ResourceRepository.get_rules` **逐条等价**：
        同一套选库逻辑（`RuleAssembler.select_libraries`）、同一套适用性
        判定（`RuleService.matches_context`）、同一套去重与排序
        （`RuleAssembler.assemble`）。
        """
        codes = RuleAssembler.library_code_candidates(context)
        index = self._loader.load_libraries()
        libraries = RuleAssembler.select_libraries(codes, index)
        if not libraries:
            logger.warning('[%s] 未找到任何可用规则库: %s',
                           self.SOURCE_LABEL, context)
            return []

        methods_by_library: Dict[str, List] = {}
        for lib in libraries:
            methods_by_library[lib.library_code] = (
                self._loader.get_candidate_methods(
                    lib.library_code, context.defect_name,
                )
            )

        return RuleAssembler.assemble(libraries, context, methods_by_library)

    # —— 组合：把 keyword 资源并进来 ——————————————————————————

    def get_keywords_by_names(self, names) -> List[KeywordProfile]:
        """按参数名批量取论域元数据（本地 `keywords.json`）。

        与数据库来源同一口径：转成内核契约 `KeywordProfile`，再过契约
        校验关口（`KeywordAssembler.filter_valid`）—— 校验实现在共用层，
        两条路径不会分叉。
        """
        if not names:
            return []
        rows = self._loader.get_keyword_rows(sorted(names))
        profiles = RuleKeywordAdapter.to_keyword_profiles(rows)
        return KeywordAssembler.filter_valid(profiles, self.SOURCE_LABEL)


__all__ = ['FileResourceRepository']