"""来源选择器 —— 决定资源仓库走**数据库**还是**本地文件**（延迟导入）。

两条来源实现同一个契约（`AlgorithmResourceRepository`）：

| 来源 | 实现 | 依赖 |
|---|---|---|
| 数据库 | `library/repository.py::ResourceRepository` | Django ORM |
| 本地文件 | `library/files/repository.py::FileResourceRepository` | 纯 JSON（零 ORM） |

⚠️ **为什么单独一个模块**：它同时要 import 两个来源，但**只能在运行时
  按需 import** —— 若在模块顶层把两个来源都 import 了，「用文件来源」
  也会把 Django ORM 拖进依赖链，文件通道就失去意义了
  （依赖倒置的实质检验 = 高层不被低层实现拖住）。

⚠️ **配置开关 + 显式注入双支持**：

- 配置开关：`settings.FUZZY_LIBRARY_SOURCE`（`'db'` / `'file'`），
  配 `settings.FUZZY_LIBRARY_FILE_DIR` 指定数据目录；
- 显式注入：直接 `FuzzyEngine(repository=FileResourceRepository())`
  —— 优先级高于配置（引擎已收到实例就不再看配置）。
"""

import logging
from typing import Optional

from process.algorithms.fuzzy.library.contracts import AlgorithmResourceRepository


logger = logging.getLogger(__name__)


# —— 来源标识 ————————————————————————————————————————————————

SOURCE_DB = 'db'
SOURCE_FILE = 'file'
DEFAULT_SOURCE = SOURCE_DB

SETTING_SOURCE = 'FUZZY_LIBRARY_SOURCE'
SETTING_FILE_DIR = 'FUZZY_LIBRARY_FILE_DIR'


def _setting(name: str, default=None):
    """读 Django settings（未配置 Django 环境时返回默认值）。

    ⚠️ **只捕获 `ImproperlyConfigured`**：Django 未 `setup()` 时访问
      settings 会抛这个异常；其它异常（配置写错等）应当暴露出来，
      不能被静默吞成默认值。
    """
    from django.conf import settings
    from django.core.exceptions import ImproperlyConfigured

    try:
        return getattr(settings, name, default)
    except ImproperlyConfigured:
        return default


def resolve_source(source: Optional[str] = None) -> str:
    """决定资源来源（显式参数 > 配置 > 默认 `'db'`）。

    Args:
        source: 显式指定（`'db'` / `'file'`）；None 则读配置。

    Returns:
        来源标识。
    """
    if source:
        return source
    return _setting(SETTING_SOURCE, DEFAULT_SOURCE) or DEFAULT_SOURCE


def resolve_file_dir(file_dir: Optional[str] = None) -> Optional[str]:
    """决定文件来源的数据目录（显式参数 > 配置 > None=默认目录）。"""
    if file_dir:
        return file_dir
    return _setting(SETTING_FILE_DIR, '') or None


def resolve_repository(
    source: Optional[str] = None,
    file_dir: Optional[str] = None,
    auto_reload: bool = True,
) -> AlgorithmResourceRepository:
    """按来源构造资源仓库。

    Args:
        source: 显式指定来源（`'db'` / `'file'`）；None 则读配置。
        file_dir: 文件来源的数据目录；None 则读配置 / 用默认目录。
        auto_reload: 文件来源是否在文件改动后自动重读。

    Returns:
        资源仓库实例（实现 `AlgorithmResourceRepository` 协议）。
    """
    resolved = resolve_source(source)

    if resolved == SOURCE_FILE:
        # 延迟 import：只有真走文件来源时才引入文件通道（它不碰 ORM）
        from process.algorithms.fuzzy.library.files.repository import (
            FileResourceRepository,
        )
        repo = FileResourceRepository(
            root_dir=resolve_file_dir(file_dir),
            auto_reload=auto_reload,
        )
        logger.info('[library.provider] 资源来源 = 本地文件（目录: %s）',
                    repo.loader.root_dir)
        return repo

    # 延迟 import：只有真走数据库来源时才引入 ORM
    from process.algorithms.fuzzy.library.repository import ResourceRepository
    logger.info('[library.provider] 资源来源 = 数据库')
    return ResourceRepository()


__all__ = [
    'resolve_repository',
    'resolve_source',
    'resolve_file_dir',
    'SOURCE_DB',
    'SOURCE_FILE',
    'DEFAULT_SOURCE',
]