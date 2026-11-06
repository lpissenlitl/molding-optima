"""规则资源 —— 规则的**取数**（查询线，依赖 ORM）。

规则分两层：library（规则库分组 `RuleLibrary`）、method（挂在库下的规则条目 `RuleMethod`）。

- `RuleQueryService`：查库（依赖 ORM），产出**来源无关记录**（`RuleRecord` / `LibraryRecord`）
- `ResourceRepository`（`library/repository.py`）负责把规则组织成算法要用的资源

⚠️ **语义类与转换类在本模块之外**（均零 ORM）：

- `RuleService`（规则串语义判定）→ `library/semantics.py`
- `RuleAdapter` / `RuleRecordAdapter` / `LibraryRecordAdapter`（契约转换）
  → `library/adapters.py`

原因：文件来源（`library/files/`）必须**零 ORM** 地复用这些判定，
否则会把 Django ORM 拖进文件通道（依赖倒置的实质检验 = 高层不被低层实现拖住）。
本模块保留**兼容导出**，既有引用路径（`library.rules.RuleService` 等）不变。
"""

from typing import List, Optional

from process.algorithms.fuzzy.library.adapters import (
    LibraryRecordAdapter,
    RuleAdapter,
    RuleRecordAdapter,
)
from process.algorithms.fuzzy.library.contracts import (
    LibraryIndex,
    RuleRecord,
)
from process.algorithms.fuzzy.library.semantics import RuleService
from process.models.rules import RuleLibrary, RuleMethod


__all__ = [
    'RuleQueryService',
    'RuleService',          # 兼容导出（实体在 library/semantics.py）
    'RuleAdapter',          # 兼容导出（实体在 library/adapters.py）
    'RuleRecordAdapter',
    'LibraryRecordAdapter',
]


# --- RuleQueryService: 查询侧（只访问数据库，不含业务判断） ---

def _index_add(index: LibraryIndex, lib: RuleLibrary) -> None:
    """把一条库记录并入索引（**同码追加**，重复记录不重复并入）。

    ⚠️ **去重按记录本身**（不是按编码）：同码的两条记录是**两个不同的库**
      （分属不同租户）⇒ 都必须留在索引里。
    """
    record = LibraryRecordAdapter.to_record(lib)
    records = index.setdefault(record.library_code, [])
    if record not in records:
        records.append(record)


class RuleQueryService:
    """规则查询服务 —— 只把数据从库里取出来，不做业务判断。

    「哪条规则适用」由 `RuleService` 判断。

    规则库以 ORM 实例在内部传递（而非 `library_code` 字符串）：同一
    `library_code` 可能对应多条库记录（不同 company），改用字符串会改变
    SQL 语义与命中条数。
    """

    @staticmethod
    def get_libraries_by_codes(
        codes: List[str],
        library_type: Optional[str] = None,
    ) -> List[RuleLibrary]:
        """按候选编码逐个查库，返回命中的规则库（保持候选顺序）。

        逐个查（而非 `library_code__in` 一次查完）是有意为之：命中结果最终按
        `priority` 降序稳定排序，同 priority 时候选顺序决定先后。改成批量查询
        会改变同 priority 库的相对顺序，进而改变下游规则遍历顺序。

        ⚠️ **同编码返回全部记录**（不再只取第一条）：`library_code` 是业务分类
          编码，**跨租户可重复**（`add_rule_library` 只校验「同公司内不重复」）
          ⇒ 同码多库是**合法状态**。只取第一条 ⇒ 别家的库被静默丢掉，
          它库里的规则不报错、只是不参与推理。
          **谁该被看到由编排层的可见性判据裁决**（`assembly.is_library_visible`），
          取数层不做取舍 —— 取舍一旦在取数层做，两个来源必然分叉。

        Args:
            codes: 候选规则库编码（按优先级从高到低）。
            library_type: 可选的库类型过滤（兜底库用 `'fuzzy'`）。

        Returns:
            命中的 `RuleLibrary` 列表（去重，顺序 = 候选顺序）。
        """
        libraries: List[RuleLibrary] = []
        for code in codes:
            qs = RuleLibrary.objects.filter(
                library_code=code,
                is_active=True,
                is_deleted=False,
            )
            if library_type:
                qs = qs.filter(library_type=library_type)
            # ⚠️ `order_by('id')` 与旧口径（`qs.first()` 的隐式主键升序）一致
            for lib in qs.order_by('id'):
                if lib not in libraries:
                    libraries.append(lib)
        return libraries

    @staticmethod
    def get_methods(
        library_id: int,
        defect_code: str,
    ) -> List[RuleRecord]:
        """按「规则库 + 缺陷」取**候选**规则方法。

        返回**来源无关记录** `RuleRecord`（不是 ORM 实例）—— 编排层只认这一种
        形态，数据库来源与文件来源在此汇流。

        ⚠️ **入参用 `library_id`（主键）而不是 ORM 实例**：编排层拿到的是
          `LibraryRecord`（来源无关），只有主键能跨来源地定位到库。

        ⚠️ **本方法只取「候选」，不做适用性判定**：聚合物 / 产品两维的筛选
          在编排层（`RuleAssembler.assemble`）用 `RuleService.matches_context`
          统一完成 —— **匹配谓词只在那一处实现**，两个来源共用。

        ⚠️ **「通用」的判定不只看 NULL**：``polymer_abbreviation`` /
          ``product_category`` **无空串**（只有 NULL 与有值两种），
          但**有值里包含字面值「通用」**
          —— 那是「明确写了适用于所有产品/材料」，业务含义与 NULL 相同
          （该维不设限）。⇒ 判定统一走 ``RuleService.is_generic_label``
          （NULL **或** 字面值「通用」都算通用），**不要**在本层另写一套。

        排序：``priority`` 降序、``id`` 升序（与文件来源的排序口径一致）。
        """
        qs = RuleMethod.objects.filter(
            rule_library_id=library_id,
            defect_code=defect_code,
            is_active=True,
            is_deleted=False,
        )
        methods = list(qs.order_by('-priority', 'id'))
        return [RuleRecordAdapter.to_record(m) for m in methods]

    @staticmethod
    def get_all_libraries() -> List[RuleLibrary]:
        """取**全部**规则库（``is_deleted=False``，按主键升序）。
    
        ⚠️ **口径与文件来源逐条一致**：`library/files/export.py::export_libraries`
          用的就是 ``filter(is_deleted=False).order_by('id')`` + **同码全保留**
          ⇒ 两条来源的库索引**内容与顺序完全相同**（顺序决定同 priority 库的
          相对先后，进而决定下游规则遍历顺序）。
    
        ⚠️ **不过滤 ``is_active``**：停用库保留在索引里（``LibraryRecord.is_active``），
          由 `RuleAssembler.select_libraries` 统一判断 —— 与文件来源
          （`libraries.json` 里带 ``is_active`` 字段、读取时再判）口径一致。
        """
        return list(RuleLibrary.objects.filter(is_deleted=False).order_by('id'))
    
    @staticmethod
    def get_library_index(codes: Optional[List[str]]) -> LibraryIndex:
        """按候选编码取库，返回 `library_code` → **同码全部** `LibraryRecord` 的索引。

        两种口径：

        - ``codes is None``（**未指定规则库**）⇒ **全量索引**：取全部规则库
          （`get_all_libraries`）——「哪条规则适用于当前产品/材料」交给
          规则级判定（`RuleService.matches_context` / `resolve_specificity`）；
        - 否则 ⇒ **候选库**（不按库类型过滤）+ **通用兜底库 `base`**
          （单独按 ``library_type='fuzzy'`` 取，与历史行为一致）。

        ⚠️ **同编码的库全部保留**（不是只留第一条）：`library_code` 是业务分类
          编码，**跨租户可重复** ⇒ 同码多库是合法状态。
          只留第一条 ⇒ 别家的库被静默丢掉，它库里的规则**不报错、只是不参与推理**
          （典型场景：各租户各有一个 `rule_miner` 挖掘私库）。
          **谁该被看到由编排层的可见性判据裁决**（`assembly.is_library_visible`）。

        ⚠️ **兜底库 `base` 也可能同码多条**（系统库 + 租户私库各一个）
          ⇒ 兜底取全部同码记录，再由可见性判据与编排层过滤。
        """
        index: LibraryIndex = {}
        if codes is None:
            # 未指定库 ⇒ 全量（与文件来源 libraries.json 同内容、同顺序）
            for lib in RuleQueryService.get_all_libraries():
                _index_add(index, lib)
            return index
        for lib in RuleQueryService.get_libraries_by_codes(codes):
            _index_add(index, lib)
        # 通用兜底库（必须存在）：**单独按库类型取**，与历史行为逐条一致
        for lib in RuleQueryService.get_libraries_by_codes(['base'], library_type='fuzzy'):
            _index_add(index, lib)
        return index

