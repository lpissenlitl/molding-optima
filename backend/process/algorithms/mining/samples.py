"""文件来源的训练样本仓库（JSONL 语料）。

与 `fuzzy/library/files/repository.py`（规则库的文件来源）同构：
两边都实现同一个 Protocol，实现方可互换 ⇒ 将来加数据库来源时，
挖掘内核与编排层一行都不用改。

⚠️ **为什么语料用 JSONL 而不是 JSON 数组**
   语料是 **append-only 事实流**（每次调机出结果就追加一条，历史样本永不修改）。
   JSONL 的追加写是 O(1) 且天然抗中断（半行写坏了不影响前面的行），
   数组则每次都要整体重写。

⚠️ **为什么按公司分片**
   规则库按公司隔离（`RuleLibrary` / `RuleMethod` 都有 company 外键），
   样本是规则的证据 ⇒ 语料必须同样隔离，否则跨公司的调机经验会被
   混成一条规则。一个公司一个文件：`{root_dir}/company_{id}.jsonl`。

   ⚠️ **`root_dir` 本身已按租户隔离**：应用层（`provider.py`）把它解析成
   `{STORE_PATH}/{tenant_slug}/mining/samples` ⇒ 租户级隔离靠目录，
   公司级隔离靠文件名，两级不混。

⚠️ **`sample_id` 必须字典序可比**
   增量挖掘靠游标 `since` 截断，判定是字符串比较 ⇒ id 必须零填充
   （如 ``"tr:000000000070"``），否则 ``"tr:99"`` 会排在 ``"tr:100"`` 之后。

⚠️ **语料是 append-only 日志，允许同 id 多行**
   源侧样本会漂移（调机记录的 ``adjustments`` 会被重算、试模结果后补）
   ⇒ 修订以**新行追加**，读取时同 ``sample_id`` 取**最后一行**为准
   （见 `get_samples`）。
"""

import json
import os
from typing import Dict, Iterable, List, Optional

from .contracts import MiningSampleRepository, SampleRecord, normalize_defect


#: 样本 id 的零填充宽度（保证字典序 = 数值序）
SAMPLE_ID_PAD = 12


def format_sample_id(prefix: str, numeric_id: int) -> str:
    """生成字典序可比的样本 id。

    Args:
        prefix: 源类型前缀（如 ``'tr'`` 表示来自调机记录）。
        numeric_id: 源侧数字主键。

    Returns:
        形如 ``'tr:000000000070'`` 的样本 id。
    """
    return f'{prefix}:{int(numeric_id):0{SAMPLE_ID_PAD}d}'


def parse_sample_id(sample_id: str) -> Optional[int]:
    """把样本 id 解析回源侧数字主键。

    Args:
        sample_id: 样本 id（如 ``'tr:000000000070'``）。

    Returns:
        数字主键（70）；格式不合法或为空时返回 None。
    """
    if not sample_id:
        return None
    _, _, tail = sample_id.rpartition(':')
    if not tail.isdigit():
        return None
    return int(tail)


def _decode_defects(data: Dict) -> List[Dict]:
    """JSON 里的 ``defects`` → 规范形态（``[{'name','level'}]``）。

    ⚠️ **必须兼容旧格式**：旧语料行的 ``defects`` 存的是裸缺陷名
        （``['SHORTSHOT']``），等级另存于 ``defect_levels``。
        语料是 **append-only** 日志（历史行永不删除）⇒ 读取时必须认旧格式，
        否则历史行会退化成「有名字、没等级」，与新采集的行产生**伪差异**
        （采集的 diff 判定会把每条都当成「变了」⇒ 重复追加同一份样本）。
    """
    raw = data.get('defects') or []
    legacy_levels = data.get('defect_levels') or {}
    result: List[Dict] = []
    for item in raw:
        defect = normalize_defect(item)
        if not defect['name']:
            continue
        if not defect['level']:
            defect['level'] = str(legacy_levels.get(defect['name']) or '')
        result.append(defect)
    return result


def _record_from_dict(data: Dict) -> SampleRecord:
    """JSON dict → SampleRecord。"""
    return SampleRecord(
        sample_id=data.get('sample_id', ''),
        defects=_decode_defects(data),
        changes=list(data.get('changes') or []),
        label=data.get('label', ''),
        context=dict(data.get('context') or {}),
        source_ref=data.get('source_ref', ''),
    )


def _record_to_dict(record: SampleRecord) -> Dict:
    """SampleRecord → JSON dict。"""
    return {
        'sample_id': record.sample_id,
        'defects': [normalize_defect(d) for d in record.defects],
        'changes': list(record.changes),
        'label': record.label,
        'context': dict(record.context),
        'source_ref': record.source_ref,
    }


class FileSampleRepository:
    """训练样本的文件来源实现（JSONL 语料）。

    满足 `MiningSampleRepository` 协议 ⇒ 可与数据库来源互换。
    """

    def __init__(self, root_dir: str, company_id: Optional[int] = None):
        """
        Args:
            root_dir: 语料根目录。
            company_id: 公司 id；None 用 ``default.jsonl``（单公司 / 本地试验）。
        """
        self.root_dir = root_dir
        self.company_id = company_id

    # --- 路径 ---

    @property
    def corpus_path(self) -> str:
        """当前分片的语料文件路径。"""
        name = (
            'default.jsonl'
            if self.company_id is None
            else f'company_{self.company_id}.jsonl'
        )
        return os.path.join(self.root_dir, name)

    # --- 取用契约 ---

    def get_samples(self, since: Optional[str] = None) -> List[SampleRecord]:
        """取训练样本列表（按 `sample_id` 升序）。

        ⚠️ **同 id 后写覆盖先写**：语料是 append-only 日志，而源侧样本会漂移
          （调机记录的 `adjustments` 会被重算、试模结果后补）⇒ 修订以**新行追加**，
          读取时同 `sample_id` 取**最后一行**为准。

        Args:
            since: 增量游标 —— 只返回 `sample_id` 严格大于该值的样本。

        Returns:
            样本列表（按 `sample_id` 升序）。
        """
        path = self.corpus_path
        if not os.path.exists(path):
            return []

        latest: Dict[str, SampleRecord] = {}
        with open(path, 'r', encoding='utf-8') as handle:
            for line_no, line in enumerate(handle, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f'样本语料第 {line_no} 行 JSON 解析失败：{exc}'
                    ) from exc
                record = _record_from_dict(data)
                latest[record.sample_id] = record

        records = [latest[key] for key in sorted(latest)]
        if since is not None:
            records = [r for r in records if r.sample_id > since]
        return records

    # --- 写入 ---

    def append_samples(self, samples: Iterable[SampleRecord]) -> int:
        """追加样本到语料（append-only）。

        Args:
            samples: 待追加的样本。

        Returns:
            实际追加的条数。
        """
        records = list(samples)
        if not records:
            return 0

        os.makedirs(self.root_dir, exist_ok=True)
        with open(self.corpus_path, 'a', encoding='utf-8') as handle:
            for record in records:
                handle.write(json.dumps(
                    _record_to_dict(record), ensure_ascii=False,
                ))
                handle.write('\n')
        return len(records)

    def last_sample_id(self) -> Optional[str]:
        """语料中最大的 `sample_id`（增量游标起点）。"""
        samples = self.get_samples()
        return samples[-1].sample_id if samples else None


__all__ = [
    'FileSampleRepository',
    'format_sample_id',
    'parse_sample_id',
    'SAMPLE_ID_PAD',
]
