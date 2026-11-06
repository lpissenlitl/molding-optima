"""
规则挖掘算法模块（algorithm_type='mining'）

模块分层（每层职责单一）：
- 【0 契约】contracts: SampleRecord（来源无关样本档案）+ MiningSampleRepository 协议
- 【1 内核】core: Apriori 频繁项集挖掘（**纯函数**，零 ORM，可离线跑）
- 【2 来源】samples: 文件来源的样本仓库（JSONL 语料，append-only）
           collect: 数据库来源的样本采集器（调机流水 → 样本）
- 【3 应用】provider: 语料目录解析 + 样本仓库构造（**唯一引入 Django 的层**）
- 【4 外壳】rule_miner: RuleMinerEngine（统一入口，algorithm_type='mining'）

⚠️ **Django 只出现在 provider 层**：内核与来源层保持零 Django ⇒
  离线 runner 可在不连库、不 setup() 的环境下跑挖掘。

algorithm_type='mining'，**不注册**到 AlgorithmRegistry。
未来由独立 mining_service 编排。
"""

from .collect import TuningRecordCollector
from .contracts import MiningSampleRepository, SampleRecord
from .core import (
    MinedRule,
    encode_sample,
    mine_association_rules,
    rule_fingerprint,
)
from .provider import (
    CORPUS_SUBDIR,
    resolve_corpus_dir,
    resolve_sample_repository,
    validate_tenant_slug,
)
from .rule_miner import RuleMinerEngine
from .samples import FileSampleRepository, format_sample_id, parse_sample_id

__all__ = [
    "MiningSampleRepository",
    "SampleRecord",
    "MinedRule",
    "mine_association_rules",
    "encode_sample",
    "rule_fingerprint",
    "FileSampleRepository",
    "TuningRecordCollector",
    "format_sample_id",
    "parse_sample_id",
    "RuleMinerEngine",
    "resolve_sample_repository",
    "resolve_corpus_dir",
    "validate_tenant_slug",
    "CORPUS_SUBDIR",
]
