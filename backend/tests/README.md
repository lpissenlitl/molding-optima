# backend/tests —— 测试资产索引

跨模块的冒烟 / 接口对接 / 契约护栏。各模块自己的单元测试仍**就近**放在子包下
（`masterdata/tests/`、`process/algorithms/expert/tests/`、`process/algorithms/fuzzy/fuzzy_core/tests/`）。

## 三类文件（前缀 = 生命周期承诺）

| 前缀 | 角色 | pytest 收集 | 生命周期 |
|---|---|---|---|
| `test_*.py` | **pytest 用例** | ✅ 自动收集 | 长期回归资产 |
| `_verify_*.py` | **独立护栏脚本** | ❌ 不收集 | 长期回归资产 |
| `verify_*.py` | **一次性取证脚本** | ❌ 不收集 | **用完即删** |

**为什么 `_verify_` 前缀不能改成 `test_`**：这些脚本的断言走自带收集器 + 退出码，
**不抛 pytest 异常** ⇒ 改成 `test_` 前缀后，pytest 会把「断言值不对」也报成 PASS ⇒ **假绿**。

**判断新文件该归哪类**：看断言**钉的是什么**
- 钉**生产契约** ⇒ 长期资产（`test_` 或 `_verify_`）
- 钉**某次改造的中间态 / 修复前的失败症状** ⇒ 一次性（`verify_`，用完即删）

---

## 一、pytest 用例（`test_*.py`，25 个文件 / 247 个用例）

| 文件 | 用例 | 钉的是什么 |
|---|---|---|
| `test_check_params_layer.py` | 9 | 第4层（校验参数合理性）三类检查：差值越限 / 工艺窗口 / 锚点失配 |
| `test_check_params_over_limit_violations.py` | 9 | 超机台可设定上限的识别（**所有参数一视同仁**：位置类与压力 / 速度类同判） |
| `test_check_params_range_limits.py` | 12 | 区间限值口径 |
| `test_decide_adjustment_layer.py` | 26 | L2 策略层（场景 / 名额）方向裁决 |
| `test_empirical_current_value.py` | 9 | 经验推理 `current_value` 的「参数不存在 ≠ 当前值 0」语义 |
| `test_fuzzy_algo_offline.py` | 16 | 模糊推理 L1 离线自检（数学口径手算的精确断言）+ 零依赖不变量（子进程验证） |
| `test_fuzzy_engine_limits.py` | 8 | 设备上限 → 族表翻译 → 查表 → 越限封顶与方向重算 |
| `test_fuzzy_field_report.py` | 5 | 字段级留痕 |
| `test_fuzzy_nested_context.py` | 3 | `engine.recommend` → `RuleQueryContext` 的上下文取值 |
| `test_fuzzy_declared_domain.py` | 4 | 判级论域 = [0, 机台可设定上限]（**所有参数一视同仁**） |
| `test_fuzzy_recommendations.py` | 6 | 推荐生成 |
| `test_fuzzy_temperature_domain.py` | 10 | 温度论域 |
| `test_initialize_flat.py` | 9 | initialize 响应的 flat 契约（落库与响应同源、温度段位不错位） |
| `test_initialize_over_limit_guard.py` | 10 | 初始化链路的越限守卫 |
| `test_integrate_params_layer.py` | 17 | 参数整合层 |
| `test_meter_pres_power_branch.py` | 4 | 熔胶压力的动力源分支（液压 / 电动） |
| `test_optimize_smoke.py` | 29 | 调优调用链冒烟：schema 校验 / service 入口 / URL 路由 / 算法层契约 |
| `test_provided_smoke.py` | 7 | `optimize_from_provided` 成功路径的载荷结构 + 缺行程必拒 |
| `test_qualified_flow.py` | 9 | 合格态（qualified）语义：丢弃缺陷、允许空缺陷 |
| `test_qualified_optimize_path.py` | 4 | 合格态走 optimize 接口：**不短路**（§5.2 契约）+ 引擎零产出仍产出变更；对照非合格态仍被拒 |
| `test_qualified_strategy.py` | 7 | 合格态调机**策略层**：场景命中 / 自带候选 / `step_down` 口径 / **合格只认 feedback** |
| `test_spec_contract_alignment.py` | 7 | spec 与字段契约对齐 |
| `test_spec_extract.py` | 16 | spec 抽取 |
| `test_tuning_result_map.py` | 5 | `tuning_result` → 落库 `result` 的映射链路 |
| `test_tuning_rounds_echo.py` | 6 | 轮次回显：第 N 轮 = 参数(N) + 反馈(N)，不串轮 |

**全部离线**：不连 DB、不依赖规则库数据。需要规则库的那一处（`_resolve_visible_libraries`）
在用例里桩掉。

---

## 二、独立护栏脚本（`_verify_*.py`，4 个）

pytest **不**收集，需手动跑（退出码即结果）。

| 文件 | 用途 | 前提 |
|---|---|---|
| `_verify_fuzzy_algo_db.py` | 规则层连库端到端复验（止步 `build_rule_objects`） | **需要真实 DB** |
| `_verify_e2_offline.py` | 离线契约验证（脏规则隔离、DB 故障降级） | 无 |
| `_verify_zero_dep.py` | 零依赖不变量检查 | 无 |
| `_verify_expert_smoke.py` | 专家引擎 smoke 批量 runner | 无 |

```powershell
cd backend
..\.venv\Scripts\python.exe tests\_verify_zero_dep.py
```

---

## 三、快照对拍工具（`fuzzy_kernel/`，3 个）

改算法前后证明「输出没变」用。

| 文件 | 用途 |
|---|---|
| `fuzzy_kernel/_snapshot_core.py` | 抓一份核心输出快照（`python ... _snapshot_core.py <输出json路径>`） |
| `fuzzy_kernel/_compare_golden.py` | 与黄金快照逐条比对 |
| `fuzzy_kernel/_golden_M1.json` | 黄金快照基准 |

用法见 `process/algorithms/fuzzy/examples/README.md`。

---

## 四、运行

```powershell
cd backend
set PYTHONPATH=.
set DJANGO_SETTINGS_MODULE=_moldx.settings

# 全部 pytest 用例（247 个）
..\.venv\Scripts\python.exe -m pytest tests -q

# 单个文件
..\.venv\Scripts\python.exe -m pytest tests/test_qualified_flow.py -q

# 独立护栏脚本
..\.venv\Scripts\python.exe tests\_verify_zero_dep.py
```

【注意】仓库**没有** `pytest.ini` / `conftest.py` ⇒
- ``DJANGO_SETTINGS_MODULE`` **必须**在命令行设（否则收集期报 ``ImproperlyConfigured``）——
  新写的测试文件会自建 ``django.setup()``，但并非每个文件都这么做；
- pytest-django 未启用 ⇒ 用例里访问 DB 会被拦（``Database access not allowed``）
  ⇒ 需要连库的检查一律走 `_verify_*.py` 脚本。