"""数据文件（_data）路径解析

backend/_data 是后端数据文件目录，存放管理命令导入脚本的默认数据源：

    backend/_data/
    ├── rule_keyword_curated.json     ← 规则关键词主数据（已人工审校）
    └── rule_method_by_library.json   ← 模糊规则按库分组清单（RuleMethod 导入源）

导入脚本的默认数据路径统一基于 settings.BASE_DIR（backend 根目录）解析，
不再依赖执行命令时的工作目录，避免因启动目录不同导致「文件不存在」。
"""
from pathlib import Path

from django.conf import settings


# backend 根目录
BASE_DIR = Path(settings.BASE_DIR)

# 数据文件目录
DATA_DIR = BASE_DIR / '_data'

# --- 管理命令的默认数据文件（相对 backend 根目录）---

# 规则关键词主数据（310 条，已人工审校）
RULE_KEYWORD_JSON = '_data/rule_keyword_curated.json'

# 模糊规则按库分组清单（RuleMethod 导入源）
RULE_METHOD_JSON = '_data/rule_method_by_library.json'

# 专家规则（工艺参数初始化规则）
EXPERT_RULES_JSON = 'process/algorithms/expert/expert_rules/expert_rules.json'

# 老 fuzzykit 的推理步长表（legacy，仓库内无此文件，需手动提供）
RULE_KEYWORD_STEPS_CSV = '_data/process_ranges.csv'


def resolve_data_path(path) -> Path:
    """把数据文件路径解析为绝对路径

    解析优先级：
      1. 绝对路径 → 原样返回
      2. 相对 backend 根目录（BASE_DIR）存在 → 返回 BASE_DIR 下的绝对路径
      3. 否则按当前工作目录解析（兼容用户手动传入的相对路径）

    Args:
        path: 路径字符串或 Path 对象

    Returns:
        Path: 解析后的绝对路径（不保证存在）
    """
    p = Path(path)
    if p.is_absolute():
        return p

    base_relative = BASE_DIR / p
    if base_relative.exists():
        return base_relative

    cwd_relative = Path.cwd() / p
    if cwd_relative.exists():
        return cwd_relative

    # 都不存在时返回 BASE_DIR 下的路径，便于报错信息定位到仓库内
    return base_relative
