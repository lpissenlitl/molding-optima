# Archive - 调试与分析脚本

此目录包含提取 SQL 数据过程中使用的调试/分析脚本，仅供回溯参考。

## 文件清单

| 文件 | 用途 | 状态 |
|------|------|------|
| `analyze_libraries.py` | 分析各库之间的重合度（Jaccard 相似度）| 已分析完成 |
| `check_deleted.py` | 检查 SQL 中 deleted 字段、ID gaps | 已完成 |
| `check_library.py` | 检查 subrule_no / rule_type 字段分布 | 已完成 |
| `check_library_grouping.py` | 按 library_code 分组统计 | 已完成 |
| `verify_output.py` | 验证 JSON 输出文件的完整性 | 已完成 |

## 主要结论

各库之间的关系：**继承 + 特化**

- 基础库（基础规则）覆盖最广（17 个缺陷）
- 子规则库针对特定产品类型（碗、把手、微波炉控制盒等）
- 同缺陷在不同库的规则可能：调整量不同、条件组合不同
- 多个子库之间存在缺陷集合 100% 重叠的情况

## 后续清理

如不需要追溯，可以删除整个 `_archive/` 目录。
提取和分组的最终脚本（`extract_data.py`、`group_by_library.py`）保留在上级目录。