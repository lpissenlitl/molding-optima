# 03 · 术语映射与判据速查（Glossary & Field Mapping）

> 用途：把《Injection Molding Advanced Troubleshooting Guide》里的**行业术语**
> 对应到本项目的**业务字段 / 算法字段 / 缺陷码 / 现有规则**，供写规则与评审规则时对齐口径。
>
> ⚠️ 映射表中标 ⚠️ 的行表示**语义近似或缺口**，不可当作等价使用。
>
> 🔻 **总原则：本书是「参考信息源」，不是「判据」。**
> 书里的做法是行业经验的一部分，用来**补充信息**；**落地前必须与本项目工艺语义核对**，
> 冲突时**以本项目为准**。**名同未必义同**：术语名对上了，
> 还要看该参数在本项目的**作用与优先级**（典型：充填量的两个旋钮，见第一节）。

---

## 一、参数映射：行业术语 ↔ 本项目字段

字段来源：`backend/process/algorithms/fuzzy/field_names.py`（业务名 ↔ 算法名）。

### ✅ 有对应字段

| 书中术语 | 中文 | 业务字段 | 算法名 | 说明 |
|---|---|---|---|---|
| **shot size**（胶量端） | 射胶量 / 胶量 | `met_end_pos` | `MEL` | ✅ **短射的首选落点**；`MEL` 是**标**（= `ML_N + DDAM`），落库量为末段计量位置 `met_pos_N`；注射行程 = `ML_N − VPTL` |
| first-stage fill velocity | 一段充填速度 | `inj_spd_1..6` | `IV0..IV5` | 段 1 为充填段 |
| peak injection pressure | 峰值注射压力 | `inj_pres_1..6` | `IP0..IP5` | 段 1 为峰值段 |
| second-stage pressure | 二段压力（保压压力） | `hold_pres_1..5` | `PP0..PP4` | **补缩的主手段** |
| second-stage time | 二段时间（保压时间） | `hold_t_1..5` | `PT0..PT4` | 锚点是"浇口封冻" |
| hold/pack speed | 保压速度 | `hold_spd_1..5` | `PV0..PV4` | |
| back pressure | 背压 | `met_back_pres_1..4` | `MBP0..MB3` | 影响熔体温度与射胶一致性 |
| cooling time | 冷却时间 | `cool_t` | `CT` | |
| decompression | 松退 | `pre_met_decomp_dist` / `pst_met_decomp_dist` | `DDBM` / `DDAM` | |
| screw recovery speed | 螺杆回收速度 | `met_rot_spd_1..4` | `MSR0..MSR3` | 影响熔体温度 |
| injection time | 注射时间 | `inj_t` | `IT` | ⚠️ 与"充填时间"不等价，见下 |

### ⚠️ 近似 / 缺口

| 书中术语 | 中文 | 本项目情况 | 缺口性质 |
|---|---|---|---|
| **transfer position** | 转位（速度→压力切换位置） | 本项目 `vps_pos`(`VPTL`) = **注射行程的起点下界 / 缓冲量**（注射行程 = `ML_N − VPTL`） | ✅ **语义相容、优先级不同**：书里"调转位"用于改变充填量；本项目**先动胶量端 `met_end_pos`，MEL 偏大后**才考虑 `vps_pos`（工艺初始化已按产品状态设过） |
| **melt temperature** | 熔体温度 | `brl_temp_1..9`(BT) + `noz_temp`(NT) | ⚠️ 熔温是**料筒温度 + 背压 + 回收速度的综合结果**，不是单一设定值 |
| **mold temperature** | 模温 | 仅在**初始化参数推理**里有 `mold_temp`（标量，℃）；**优化链路无此字段** | ⚠️ **重大缺口**：缩痕 / 周期 / 短射三章都把模温列为首要工艺原因之一 |
| **fill only weight** | 仅充填重量 | `actual_weight` / `target_weight` / `fill_gap`（= 目标 − 实测） | ✅ 概念对应，已是本项目的 `fill_ratio` 口径基础 |
| **fill time** | 充填时间 | 无字段；`inj_t` 是**注射时间**，不等价 | ⚠️ 书中以"充填时间是否匹配 setup sheet"作为速度是否够快的判据 |
| **cushion** | 余料（螺杆尖前余料） | **无字段** | ⚠️ 书中多个判据的前置条件（"有泄漏就别加大射胶量"）依赖它 |
| **gate seal** | 浇口封冻 | **无字段** | ⚠️ 二段时间的定量锚点，缺它则 PT 只能定性"延长" |
| **shot cushion 0.25 in** | 余料下限 | 无字段 | ⚠️ 方向性参考值 |

---

## 二、缺陷码 ↔ 书中章节

本项目缺陷码共 **17 类**（`backend/_data/rule_method_by_library.json`）：

| 缺陷码 | 中文 | 规则条数 | 书中章节 | 对应度 |
|---|---|---|---|---|
| `SHORTSHOT` | 短射 | 109 | 第 40 章 Short Shot | ✅ 直接 |
| `SHRINKAGE` | 缩水 | 93 | 第 41 章 Sink | ✅ 直接 |
| `FLASH` | 飞边 | 124 | 第 30 章 Flash | ✅ 直接 |
| `BURN` | 烧焦 | 114 | 第 20 章 Burns | ✅ 直接 |
| `WELDLINE` | 熔接痕 | 127 | 第 47 章 Weld Lines | ✅ 直接 |
| `WARPING` | 变形 | 65 | 第 46 章 Warp | ✅ 直接 |
| `UNDERSIZE` | 尺寸偏小 | 66 | 第 26 章 Dimensions | ✅ 直接 |
| `OVERSIZE` | 尺寸偏大 | 62 | 第 26 章 Dimensions | ✅ 直接 |
| `AIRTRAP` | 困气 | 116 | 第 18 章 Bubbles | ✅ 直接 |
| `GASVEINS` | 气纹 | 152 | 第 45 章 Voids | ⚠️ 气纹与真空泡相关但不等同 |
| `TOPWHITE` | 顶白 | 148 | 第 16 章 Blush | ✅ 直接 |
| `MATERIALFLOWER` | 料花 | 114 | 第 31 章 Flow Lines | ✅ 直接 |
| `HARDDEMOLDING` | 脱模不良 | 135 | 第 35/36 章 Part Sticking | ⚠️ 书中为"粘模"，"脱模不良"范围更宽 |
| `ABERRATION` | 色差 | 129 | 第 22 章 Color Swirls / 第 33 章 Gloss Variation | ⚠️ 二选一需确认 |
| `GATEMARK` | 浇口印 | 18 | 第 43 章 Sprue Sticking | ⚠️ 书中无"浇口印"专章 |
| `WATERRIPPLE` | 水波纹 | 165 | — | ⚠️ **书中无对应章**，需另找资料 |
| `SHADING` | 阴阳面 | 15 | — | ⚠️ **书中无对应章**，需另找资料 |

> 📌 **条数分布本身就是信息**：水波纹(165)、气纹(152)、顶白(148) 条数最多，
> 而**短射(109)、缩水(93) 相对靠后**。
> 这提示当前规则库是**按外观缺陷为主**建的，而**短射/缩水才是"先做对再做漂亮"的顺序前置项**。

---

## 三、判据速查（方向性参考值，落地前必须用本项目 setup sheet 校准）

| 对象 | 书中的判据 | 性质 |
|---|---|---|
| 充填比例 | 一段充填到 **95–98%**，剩余 2–5% 由二段压力补齐 | 工艺体系特定（Decoupled®），非普适 |
| 充填量 | 用 **fill only weight** 标定，每副模记录 | 判据来源 ✔ |
| 余料 | 至少约 **0.25 in**（约 6 mm） | 设备相关 |
| 峰值注射压力 | 比所需段一峰值压力**高约 20%** | 留粘度波动余量 |
| 二段时间 | **刚好超过浇口封冻**所需时间 | 需做 gate seal 研究 |
| 熔体温度 | 与 setup sheet 一致，容差约 **±10 °F** | 测量误差范围内 |
| 模温 | **控制器设定值 ≠ 实际模面温度**，须实测/热成像 | 认知陷阱 |
| 充填速度 | 以**充填时间**匹配 setup sheet 为准；控制器速度百分比设定**可能不代表实际速度** | 认知陷阱 |
| 熔温核对 | 受**料筒温度 / 背压 / 螺杆回收速度**三者影响 | 组合量 |
| 换温控机 | 新机**冷却能力**必须相当（hp / GPM / 湍流） | 设备陷阱 |

---

## 四、现有规则与本书的对照（差距清单）

> 这些是**读这本书之后暴露出的差距**，尚未处理，等排期。

| # | 差距 | 证据位置 | 影响 |
|---|---|---|---|
| **G1** | **模温在优化链路里不可调**：`mold_temp` 只在初始化推理产出，优化链路的字段翻译表 `FIELD_NAME_ALIAS` 里没有 `mold_temp → MT` | `algorithms/fuzzy/field_names.py`；`algorithms/expert/param_types.py`（`MoldTempParams`） | 缩痕 / 周期 / 短射三章的首要工艺原因之一，算法完全看不到 |
| **G2** | **规则多为定性，缺判据**：如 `hints.py` 的 `"SHRINKAGE": {"increase": ["PP0","PT0","CT"]}` 只说"加大/延长"，没有目标值 | `algorithms/empirical/hints.py` | "加多少"落回拍脑袋；书里二段压力/二段时间都有明确锚点 |
| **G3** | **缺 `cushion` / `fill time` / `gate seal` 三个前置判据** | — | 多条对策的前置条件无法校验（如"有泄漏就别加大射胶量"） |
| **G4** | **策略层无 4M 归因**：无法区分"对症调整"与"绕过问题" | `services/optimize_chain/tuning_strategy.py`（原 `algorithms/strategies.py`，场景清单已并入 `SCENARIO_STRATEGIES`） | 会把模/机/料根因当成工艺问题去调参 |
| **G5** | **验收只有"参数物理合理性"**，缺书中的四问（工艺窗口 / 外观 / 尺寸 / 测试） | 第 4 层 `check_params` | 调完不知道算不算成功 |
| **G6** | **充填量有两个旋钮，优先级要明确**：① 胶量端 `met_end_pos`（先动）；② `vps_pos`（缓冲量 / 行程起点，**MEL 偏大后**才轮到；工艺初始化已按产品状态设过） | `services/optimize_chain/anchors.py`（注射行程 = `ML_N − VPTL`）；`services/parameter_initialize.py`（`vps_pos` 初始化） | 策略层需能表达"**胶量已到上限 ⇒ 退到下一旋钮**"，否则只会反复加 MEL |
| **G7** | **胶量端的「标 vs 决策量」要分清**：`MEL`(`met_end_pos`) 是**标**（= `ML_N + DDAM`），真正落库的是末段计量位置 `met_pos_N` | `services/optimize_chain/anchors.py`（`resolve_mel_target` / `resolve_fill_target`） | 书里的 "shot size" 在本项目落在 `met_end_pos` 口径（不是独立字段） |
| **G8** | **缺陷优先级无 Pareto 依据** | — | 短射/缩水是前置项，却排在外观缺陷之后 |
| **G9** | 🔻 **书本是参考信息源，不是判据**：书中的做法须与本项目工艺语义核对后才能落地 | 本文件全部 | 与本项目语义冲突时**以本项目为准**；术语名相同**不代表作用相同** |

---

## 五、维护约定

1. **本文件是映射表，不是规则源。** 规则源在 `algorithms/` 与规则库表中；
   这里只放"术语 ↔ 字段"的对照，避免两处各写一份口径。
2. **改字段名必须回来更新本文件。** 尤其 `FIELD_NAME_ALIAS` 增删时，
   同步检查第一节的映射表与第四节的 G1 结论。
3. **新增缺陷码时**，先查第二节有没有对应章节；没有就在本表标 ⚠️ 并注明"需另找资料"，
   **不要臆造对应关系**。
4. **第三节的数值只作方向性参考。** 真要写进规则，必须换成本项目自己的实测值
   （或明确标注为"待校准的默认值"）。
5. **书里每条对策都有前提。** 往规则里搬时，
   **前提和结论一起搬**（如"若有余料则减小转位"不能简化成"减小转位"）。
