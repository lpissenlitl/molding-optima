"""样本来源提供者 —— 解析样本池语料目录并构造样本仓库（应用层接线点）。

⚠️ **为什么语料不放在仓库里**
   样本语料是**持续增长的客户经营数据**（缺陷 + 参数变更 + 试模结果），
   属于运行时数据而非源码资产 ⇒ 落在 `settings.STORE_PATH` 下，与
   filecenter（`{STORE_PATH}/{tenant_slug}/files/...`）、
   reporting（`{STORE_PATH}/{tenant_slug}/archives/...`）同一目录约定。

   ⚠️ **不要放 `backend/_data/`**：那里放的是**版本库内的种子主数据**
   （`rule_keyword_curated.json` 等人工审校数据），语料进那里会被 git 跟踪。

   路径格式：
   ```
   {STORE_PATH}/{tenant_slug}/mining/samples/company_{company_id}.jsonl
   ```
   - 目录层按 `tenant_slug` 隔离（与 filecenter / reporting 一致）
   - 文件名按 `company_id` 分片（与规则库的 company 外键一致）

⚠️ **`tenant_slug` 必须做目录穿越校验**
   它虽是库里的字段，仍属外部可控字符串 ⇒ 未校验会允许 `../` 逃出
   STORE_PATH（处置方式与 `filecenter.utils.build_*` 一致）。

⚠️ **本模块是应用层**：算法内核（`core.py` / `samples.py`）保持零 Django，
   Django 只在本模块与调用方出现 ⇒ 离线 runner 仍可不连库跑。

⚠️ **数据库来源留位**：样本池已定用文件（见 contracts 协议注释）；
   若将来要换来源，实现同一个 `MiningSampleRepository` 协议即可替换，
   挖掘内核与编排层一行都不用改。
"""

import logging
import os
import re
from typing import Optional

from .contracts import MiningSampleRepository


logger = logging.getLogger(__name__)


#: 合法的租户标识（与 filecenter / reporting 的目录穿越校验同规则）
TENANT_SLUG_PATTERN = re.compile(r'[a-zA-Z0-9_-]+')

#: 语料在租户目录下的子路径（mining/samples）
#:
#: ⚠️ **写成 posix 风格再 split**（与 filecenter.utils.EXPORT_LIST_DIR 同写法）：
#:   直接用 os.path.join 拼多段会混出 '/data/x\\y' 这种 Windows 混合分隔符。
CORPUS_SUBDIR = 'mining/samples'


def _store_path() -> str:
    """取运行时数据根目录（`settings.STORE_PATH`）。

    ⚠️ **延迟 import**：本模块被 `mining/__init__.py` 导出，
      顶层若直接 import Django，未 `setup()` 的离线环境会连带崩掉。

    Raises:
        ImproperlyConfigured: Django 未配置 settings。
    """
    from django.conf import settings

    return str(settings.STORE_PATH)


def validate_tenant_slug(tenant_slug: str) -> str:
    """校验租户标识（防目录穿越）。

    Args:
        tenant_slug: 租户标识。

    Returns:
        原样返回合法的 `tenant_slug`。

    Raises:
        ValueError: 标识为空或含非法字符。
    """
    if not tenant_slug or not TENANT_SLUG_PATTERN.fullmatch(tenant_slug):
        raise ValueError(
            f'非法的租户标识：{tenant_slug!r}（只允许字母、数字、下划线与短横线）'
        )
    return tenant_slug


def resolve_corpus_dir(
    tenant_slug: str,
    corpus_dir: Optional[str] = None,
) -> str:
    """解析样本语料的根目录。

    Args:
        tenant_slug: 租户标识（`Company.tenant_slug`），用于目录级隔离。
        corpus_dir: 显式指定语料根目录；给了就用它（跳过租户目录拼接）。

    Returns:
        语料根目录的绝对路径。
    """
    if corpus_dir:
        return str(corpus_dir)

    validate_tenant_slug(tenant_slug)
    return os.path.join(
        _store_path(), tenant_slug, *CORPUS_SUBDIR.split('/')
    )


def resolve_sample_repository(
    tenant_slug: str,
    company_id: Optional[int] = None,
    corpus_dir: Optional[str] = None,
) -> MiningSampleRepository:
    """构造样本仓库（当前唯一来源 = 文件语料）。

    Args:
        tenant_slug: 租户标识（`Company.tenant_slug`）。
        company_id: 公司 id；None 时语料落在 `default.jsonl`（单分片）。
        corpus_dir: 显式指定语料根目录；给了就用它。

    Returns:
        满足 `MiningSampleRepository` 协议的样本仓库实例。
    """
    from .samples import FileSampleRepository

    root = resolve_corpus_dir(tenant_slug, corpus_dir)
    repo = FileSampleRepository(root_dir=root, company_id=company_id)
    logger.info(
        '[mining.provider] 样本池 = 文件语料（租户: %s，语料: %s）',
        tenant_slug, repo.corpus_path,
    )
    return repo


__all__ = [
    'resolve_sample_repository',
    'resolve_corpus_dir',
    'validate_tenant_slug',
    'TENANT_SLUG_PATTERN',
    'CORPUS_SUBDIR',
]
