"""契约 —— 样本仓库层对外的能力契约。

- `SampleRecord`：训练样本档案（**来源无关**）。
- `MiningSampleRepository`：取样本的取用契约。

用 `Protocol`（结构化子类型）表达，实现方无需显式继承，也不会引入 import 环。
本模块零 ORM 依赖，不得 import `process.models`（那会把数据库拖进编排层）。

⚠️ **为什么样本是「来源无关记录」而不是裸 dict**
   样本的来源有两类：
   - 文件来源：JSONL 语料（自持、版本化、离线可跑）
   - 数据库来源：将来若要做样本人工标注 / 可视化浏览，换一个实现即可
   两类来源都先把自己那一侧的数据规约成 `SampleRecord`，再由共用编排层
   组装 ⇒ 挖掘内核只认这一种形态，来源可互换。

   本模式与 `fuzzy/library/contracts.py` 的 `AlgorithmResourceRepository`
   完全同构（契约先行、来源实现后置）。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol, runtime_checkable


# --- 标签常量 ---------------------------------------------------------

#: 样本标签 —— 试模结果。只有「出了结果」的轮次才是样本，
#: `pending`（待验证）不构成证据，不沉淀。
#:
#: ⚠️ **分两族：绝对评价 / 相对变化**
#:    - 绝对评价（无基准时用）：``qualified``（合格）/ ``unqualified``（不合格）
#:    - 相对变化（有上一轮可比时用）：``improved`` / ``worse`` / ``unchanged``
#:    调机是**逐步逼近**的过程 —— 一次调到合格是少数，靠「每轮都有改善」
#:    才能把长尾的调机经验积累起来 ⇒ ``improved`` 与 ``qualified`` 同为
#:    正向信号，都要挖、都要落地（见 `POSITIVE_LABELS`）。
LABEL_QUALIFIED = 'qualified'      # 合格（绝对评价）
LABEL_UNQUALIFIED = 'unqualified'  # 不合格（绝对评价）
LABEL_IMPROVED = 'improved'        # 相对上一轮改善
LABEL_WORSE = 'worse'              # 相对上一轮恶化
LABEL_UNCHANGED = 'unchanged'      # 相对上一轮无变化

#: 参与挖掘的标签白名单
#: ⚠️ `unchanged` **不在**内：它没有方向性（既非改善也非恶化），
#:    不构成「某个动作带来了某种结果」的证据。
VALID_LABELS = (
    LABEL_QUALIFIED, LABEL_UNQUALIFIED, LABEL_IMPROVED, LABEL_WORSE,
)

#: 正向标签 —— 落地为 RuleMethod 的候选（「这样做会变好」）
POSITIVE_LABELS = (LABEL_QUALIFIED, LABEL_IMPROVED)

#: 负向标签 —— 只作反面参考（「这样做不会变好」），不落地为 RuleMethod
NEGATIVE_LABELS = (LABEL_UNQUALIFIED, LABEL_WORSE)


# --- 缺陷项形态 ---------------------------------------------------------

def normalize_defect(item) -> Dict[str, str]:
    """缺陷项 → 规范形态 ``{'name': str, 'level': str}``。

    ⚠️ **为什么缺陷与等级合成一项**
        缺陷名与缺陷等级本就是**同一条缺陷反馈的两个侧面**
        （``TuningRecord.defect_feedbacks`` 每项 = ``keyword_name`` + ``level``），
        拆成两个字段就会出现「名单里有、等级表里没有」的错配可能。

    ⚠️ **兼容裸字符串**：旧版语料行的 ``defects`` 存的是裸缺陷名
        （``['SHORTSHOT']``），等级另存于 ``defect_levels`` ⇒ 这里按裸名解析，
        等级留空（由调用方从旧字段补齐，见 `samples._decode_defects`）。

    Args:
        item: 缺陷项（dict / 裸字符串 / 其它）。

    Returns:
        ``{'name': 缺陷名, 'level': 等级}``；无法解析时 name 为空串。
    """
    if isinstance(item, str):
        return {'name': item, 'level': ''}
    if isinstance(item, dict):
        return {
            'name': str(item.get('name') or item.get('defect') or ''),
            'level': str(item.get('level') or ''),
        }
    return {'name': '', 'level': ''}


def defect_name(item) -> str:
    """缺陷项 → 缺陷名（兼容裸字符串）。

    统计维度只认**名字**（``D:SHORTSHOT``）—— 等级不是统计维度，
    同一缺陷的不同等级应合并统计才有意义。
    """
    return normalize_defect(item)['name']


def defect_level(item) -> str:
    """缺陷项 → 缺陷等级（兼容裸字符串；无等级时为空串）。"""
    return normalize_defect(item)['level']


# --- 数据类型 ---------------------------------------------------------

@dataclass
class SampleRecord:
    """训练样本档案（**来源无关**）。

    一条样本 = 一次「调机轮次 + 试模结果」的证据。

    Attributes
    ----------
    sample_id : str
        样本标识（来源侧主键，如 ``"tr:70"``）。**单调递增**是增量挖掘的前提。
    defects : List[Dict]
        本轮出现的缺陷，元素形如 ``{'name': 'SHORTSHOT', 'level': 'medium'}``。
        缺陷名取**算法命名空间**的英文名（如 ``'SHORTSHOT'``）
        —— 与 ``RuleKeyword.keyword_name``（defect 类）同构，无需再翻译。
        ⚠️ **等级与缺陷合成一项**：两者同源于一条缺陷反馈
        （``TuningRecord.defect_feedbacks``），拆开就会出现错配可能。
        ⚠️ **等级不是统计维度**（同一缺陷的不同等级应合并统计才有意义），
        只作为落地成 RuleMethod 时的条件词来源
        （``SHORTSHOT`` + ``medium`` ⇒ ``SHORTSHOT_medium``）。
        ⚠️ 合格态的样本没有缺陷 ⇒ 该列表为空，属正常。
    changes : List[Dict]
        本轮的参数变更，元素形如
        ``{'param': 'inj_pres_1', 'direction': 'increase'}``。
        `param` 取**业务字段名**（与 ``adjustments.changes[].param`` 一致）。
    label : str
        标签（``qualified`` / ``unqualified``）。
    context : Dict
        挖掘条件化所需的上下文（如 ``{'polymer': 'PP', 'mold_id': 12}``）。
        **不参与**频繁项集计算，只作为规则附加维度。
    source_ref : str
        溯源标识（字符串），回指到业务流水（如 ``"tuning_record:70"``）。
    """

    sample_id: str
    defects: List[Dict] = field(default_factory=list)
    changes: List[Dict] = field(default_factory=list)
    label: str = ''
    context: Dict = field(default_factory=dict)
    source_ref: str = ''

    def is_usable(self) -> bool:
        """是否是可参与挖掘的样本。

        两个条件缺一不可：
        - 有标签（``pending`` 不算；``unchanged`` 没有方向性，也不算）
        - 有变更（没有变更就没有可学习的动作）

        ⚠️ **不要求有缺陷**
           合格态的产品没有缺陷 —— 业务规则会**清空**缺陷反馈
           （见 ``tuning.TuningService.upsert_tuning_record``）⇒
           若把「有缺陷」当成必要条件，所有合格样本都会被丢弃，
           语料里只剩不合格样本 ⇒ 永远挖不出任何正向规则。
        """
        return (
            self.label in VALID_LABELS
            and bool(self.changes)
        )


@runtime_checkable
class MiningSampleRepository(Protocol):
    """训练样本的取用契约。

    只管「取样本」，不管「挖规则」：样本怎么规约成事务、怎么算支持度，
    住在 ``rule_miner.py``，编排层直接调用。

    编排层只依赖本协议。默认实现是 ``samples.FileSampleRepository``
    （文件来源）；数据库来源留位（实现同一协议即可互换）。

    ⚠️ **标了 `@runtime_checkable`**：允许用 `isinstance` 校验实现方
      （只校验方法是否存在，不校验签名）⇒ 「契约满足」可被自动断言。
    """

    def get_samples(self, since: Optional[str] = None) -> List[SampleRecord]:
        """取训练样本列表。

        Args:
            since: 增量游标 —— 只返回 ``sample_id`` 严格大于该值的样本。
                None 表示取全量。

        Returns:
            样本列表（按 ``sample_id`` 升序）。
        """
