# 工艺模块数据模型设计

> 本文档定义了 molding-optima 工艺模块的数据模型设计。

## 0. 工业级优化设计（2026-07-02）

### 0.1 设计哲学

针对工业实际场景，ProcessCondition 采用**三层结构**设计：

| 层级 | 关系类型 | 处理方式 | 理由 |
|------|----------|----------|------|
| **顶层铝定** | 核心实体关系 | FK 外键 | 必须可追溯 |
| **索引定位** | 业务规则映射 | Int 字段 | 通过业务规则推导 |
| **细节上下文** | 动态嵌套关系 | JSON 字段 | 灵活避免僵化 |

### 0.2 核心原则：业务规则 > 硬外键

不是所有关系都需要 FK。业务规则能推导的，用上下文承载：

- **mold + shot_index** → 通过业务规则确定 mold 的哪个浇注系统（GatingSystem）
  - 严格按照注射顺序：第 1 射 → 第 1 个 gating_system
- **injection_machine + injection_index** → 按索引定位注射单元
- **cavity/gate/overrides** → 在 process_context_snapshot JSON 中灵活描述

### 0.3 优化后的 ProcessCondition 结构

```python
class ProcessCondition(BusinessBaseModel):
    """工艺条件（工业级三层设计）"""

    # ====== 业务元信息 ======
    status = CharField()
    condition_code = CharField()
    origin_type = CharField()
    
    # ====== 顶层外键（核心实体） ======
    mold = FK("masterdata.Mold")
    shot_index = IntegerField()           # 业务规则推导 gating_system
    
    injection_machine = FK("masterdata.InjectionMoldingMachine")
    injection_index = IntegerField()      # 索引定位注射单元
    
    polymer = FK("masterdata.Polymer")
    
    # ====== 细节上下文（JSON） ======
    process_context_snapshot = JSONField(default=dict)
    # {
    #   "gating_system_id": 1,    # 由 shot_index 推导
    #   "cavity_id": 1,
    #   "gate_id": 1,
    #   "overrides": {            # 用户前端调整
    #     "product_weight": 85,
    #     "gate_type": "侧浇口"
    #   }
    # }
```

### 0.4 为什么不用硬外键

| 维度 | 硬外键方案 | JSON 上下文方案 |
|------|------------|----------------|
| 数据完整性 | DB 强制约束 | 业务规则约束 |
| 灵活性 | 低（加字段需迁移） | 高（JSON 灵活扩展） |
| 迁移成本 | 高 | 低 |
| 复杂关系 | 难以表达 | 容易表达 |

### 0.5 业务规则推导示例

```python
def get_gating_system(mold, shot_index):
    """mold + shot_index → gating_system"""
    systems = mold.gating_systems.order_by('id')
    if shot_index and 1 <= shot_index <= len(systems):
        return systems[shot_index - 1]
    return systems.first()


def get_injection_unit(machine, injection_index):
    """machine + injection_index → InjectionUnit"""
    units = machine.injection_units.all()
    idx = injection_index or 1
    if 1 <= idx <= len(units):
        return units[idx - 1]
    return units.first()
```

### 0.6 优势

1. **核心可追溯**：mold / injection_machine / polymer 都是 FK，历史数据可追溯
2. **动态关系灵活**：cavity / gate 等复杂嵌套关系用 JSON 描述，避免迁徒
3. **业务规则清晰**：shot_index → gating_system、injection_index → InjectionUnit 是业务规则
4. **保留快照能力**：process_context_snapshot 记录完整上下文，不依赖外部关联

## 1. 设计原则

1. **锚点稳定**：`ProcessCondition + ProcessParameter` 作为稳定锚点
2. **分层扩展**：基础数据 + 可选扩展模块（调试记录、AI推荐等）
3. **版本管理**：通过 `parent_param` 自关联支持树形版本结构
4. **完整上下文**：工艺参数关联模具、机台、材料等完整上下文信息
5. **三层结构**：ProcessCondition 采用顶层外键 + 索引定位 + JSON 上下文快照
6. **业务规则**：能用业务规则推导的关系，避免硬外键（如 shot_index → gating_system）
7. **工业级**：支持多射注塑机、多浇注系统、多型腔、多浇口、多产品等复杂场景

## 2. 模型关系图

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ProcessCondition                              │
│            （顶层外键 + 索引定位 + JSON 上下文快照）                     │
│─────────────────────────────────────────────────────────────────────│
│  id                    │ 主键                                         │
│  status                │ 状态：draft/testing/approved/rejected/obsolete│
│  condition_code        │ 工艺条件编号                                  │
│  origin_type           │ 起源：manual/template/ai/transplant...       │
│  process_context_snapshot│ 上下文快照 JSON （gating_system_id,           │
│                         │ cavity_id, gate_id, overrides）             │
│  mold_id               │ 顶层 FK：模具                                  │
│  shot_index            │ 索引：第几射 → 推导 gating_system              │
│  injection_machine_id  │ 顶层 FK：注塑机                                │
│  injection_index       │ 索引：哪个注射单元                              │
│  polymer_id            │ 顶层 FK：材料                                  │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        ProcessParameter                              │
│              (工艺参数 + 版本树关系 + 参数来源)                       │
│─────────────────────────────────────────────────────────────────────│
│  id                    │ 主键                                         │
│  process_condition_id  │ 工艺条件 FK                                  │
│  param_code            │ 参数编号                                     │
│  param_source          │ 来源：manual/algorithm/equipment/template... │
│  parent_param_id       │ 父版本 FK（自关联，支持版本树）               │
│  seq_idx               │ 序列号（同父节点下递增）                      │
│─────────────────────────────────────────────────────────────────────│
│  注射参数 (6段)                                                       │
│  inj_stg, inj_spd_1~6, inj_pres_1~6, inj_pos_1~6,                    │
│  inj_t, inj_dly_t                                                      │
│─────────────────────────────────────────────────────────────────────│
│  VP切换参数                                                           │
│  vps_mode, vps_pos, vps_t, vps_pres, vps_spd                         │
│─────────────────────────────────────────────────────────────────────│
│  保压参数 (5段)                                                       │
│  hold_stg, hold_pres_1~5, hold_spd_1~5, hold_t_1~5                   │
│─────────────────────────────────────────────────────────────────────│
│  冷却参数                                                             │
│  cool_t                                                                │
│─────────────────────────────────────────────────────────────────────│
│  熔胶参数 (4段)                                                       │
│  met_stg, met_pres_1~4, met_rot_spd_1~4, met_back_pres_1~4,          │
│  met_pos_1~4                                                          │
│─────────────────────────────────────────────────────────────────────│
│  松退参数                                                             │
│  pre_met_decomp_*, pst_met_decomp_*, met_lim_t, met_end_pos          │
│─────────────────────────────────────────────────────────────────────│
│  料筒温度参数 (10段)                                                  │
│  brl_temp_stg, noz_temp, brl_temp_1~9                                │
└─────────────────────────────────────────────────────────────────────┘
           │                                    │
           ▼                                    ▼
┌───────────────────────┐          ┌───────────────────────┐
│    TuningRecord       │          │     Recommendation    │
│     调试记录           │          │      推荐结果         │
│───────────────────────│          │───────────────────────│
│ id                    │          │ id                    │
│ process_parameter_id  │          │ process_parameter_id  │
│ defect_feedbacks JSON │          │ source_type           │
│ note                  │          │ recommendations JSON  │
│ result                │          │ is_adopted            │
│ parameter_snapshot    │          │ adopted_param_id      │
└───────────────────────┘          └───────────────────────┘
```

## 3. 模型详细设计

### 3.1 ProcessCondition（工艺条件）

**三层结构设计**：

| 层级 | 字段 | 说明 |
|------|------|------|
| 顶层外键 | mold, injection_machine, polymer | 核心实体，可追溯 |
| 索引定位 | shot_index, injection_index | 业务规则推导动态关系 |
| JSON 上下文 | process_context_snapshot | 动态细节、用户覆盖 |

```python
class ProcessCondition(BusinessBaseModel):
    """
    工艺条件 - 工艺条件主表

    一条记录对应一组"工艺事件"（参数录入、变更、优化等），
    必须包含模具/机器/材料等上下文。

    设计原则：
    - 每个 ProcessCondition 对应某一射的工艺
    - 多射场景通过 shot_index + injection_index 区分
    """

    # --- 状态信息 ---
    PROCESS_CONDITION_STATUS_CHOICES = [
        ('draft', '草稿'),           # 初始创建，未开始测试
        ('testing', '测试中'),        # 正在打样/验证
        ('approved', '已批准'),       # 合格工艺，可用于量产
        ('rejected', '已废弃'),       # 验证失败，不再使用
        ('obsolete', '已过时'),       # 曾经批准，但被新工艺替代
    ]
    status = models.CharField(null=True, blank=True, max_length=20, verbose_name="状态")

    # --- 基本信息 ---
    condition_code = models.CharField(null=True, blank=True, max_length=50, verbose_name="工艺条件编号")

    PROCESS_CONDITION_ORIGIN_CHOICES = [
        ('manual_creation', '手工新建'),
        ('template_based', '基于模板'),
        ('ai_recommendation', 'AI 推荐启动'),
        ('doe_experiment', '实验设计（DOE）'),
        ('legacy_import', '历史工艺导入'),
        ('equipment_capture', '设备参数捕获'),
        ('process_transplant', '工艺移植'),
    ]
    origin_type = models.CharField(
        max_length=30,
        choices=PROCESS_CONDITION_ORIGIN_CHOICES,
        null=True, blank=True,
        verbose_name="工艺起源类型",
    )

    # --- 上下文快照 JSON ---
    # 动态上下文描述，避免硬外键，保持灵活性
    process_context_snapshot = models.JSONField(null=True, blank=True, verbose_name="工艺条件快照")
    """
    JSON 结构约定：
    {
        # 动态细节（业务规则推导出的具体定位）
        "gating_system_id": 1,        # 由 mold + shot_index 推导
        "cavity_id": 1,               # 该系统的型腔
        "gate_id": 1,                 # 该型腔的浇口（可选）
        
        # 用户覆盖字段（产品/工艺可调整）
        "overrides": {
            "product_weight": 85,     # 覆盖后端默认值
            "runner_weight": 0,
            "gate_type": "侧浇口",
            "ave_thickness": 2.8,
            "max_thickness": 3.5,
            "max_length": 150,
            "gate_radius": 1.5,
            "gate_length": 2.0,
            "gate_width": 3.0
        },
        
        # 快照元信息（可选）
        "source": "initialization_from_ids",
        "matched_rules": ["DEFAULT", "MATERIAL_GENERAL"],
        "created_by": "algorithm_init"
    }
    """

    # --- 模具信息 ---
    mold = models.ForeignKey(
        "masterdata.Mold",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="+",
        verbose_name="模具信息",
    )
    shot_index = models.IntegerField(null=True, blank=True, verbose_name="注射次数")

    # --- 注塑机信息 ---
    injection_machine = models.ForeignKey(
        "masterdata.InjectionMoldingMachine",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="+",
        verbose_name="注塑机信息",
    )
    injection_index = models.IntegerField(null=True, blank=True, verbose_name="注射单元")

    # --- 材料信息 ---
    polymer = models.ForeignKey(
        "masterdata.Polymer",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="+",
        verbose_name="材料信息",
    )

    class Meta:
        verbose_name = "工艺条件"
        verbose_name_plural = verbose_name
```

### 3.2 ProcessParameter（工艺参数）

```python
class ProcessParameter(BusinessBaseModel):
    """
    工艺参数 - 隶属 ProcessCondition 的具体参数

    字段命名参考 molding-expert（inj_spd_1, inj_pres_1, hold_pres_1 等），
    比旧版 molding-optima 的命名（IV0, IP0, IL0）更可读。

    版本管理：
    - parent_param: 自关联，支持树形版本结构
    - seq_idx: 同一父节点下递增，自动分配
    - param_source: 标记参数来源（手动/AI/设备同步等）
    """

    process_condition = models.ForeignKey(
        ProcessCondition,
        on_delete=models.CASCADE,
        verbose_name="所属条件",
        related_name="process_parameters",
    )

    # --- 基本信息 ---
    param_code = models.CharField(
        null=True, blank=True,
        max_length=50,
        verbose_name="工艺参数编号",
    )

    PARAMETER_SOURCE_CHOICES = [
        ('unknown', '未知'),
        ('manual', '手工录入'),
        ('import', '外部导入'),
        ('algorithm_init', '算法初始化'),
        ('system_inferred', '系统推理'),
        ('manual_adjusted', '人工调整'),
        ('equipment_sync', '设备同步'),
        ('template_copy', '模板复制'),
        ('ai_recommended', 'AI 推荐'),
    ]
    param_source = models.CharField(
        max_length=20,
        choices=PARAMETER_SOURCE_CHOICES,
        default="unknown",
        verbose_name="参数来源",
    )

    # --- 版本关系 ---
    parent_param = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="children",
        verbose_name="父版本",
    )

    seq_idx = models.IntegerField(
        null=True, blank=True,
        verbose_name="序列序号",
        default=0,
    )

    # --- 注射参数 (6段) ---
    inj_stg = models.IntegerField(null=True, blank=True, verbose_name="注射段数 1-6")
    inj_spd_1 = models.FloatField(null=True, blank=True, verbose_name="一段注射速度")
    inj_spd_2 = models.FloatField(null=True, blank=True, verbose_name="二段注射速度")
    inj_spd_3 = models.FloatField(null=True, blank=True, verbose_name="三段注射速度")
    inj_spd_4 = models.FloatField(null=True, blank=True, verbose_name="四段注射速度")
    inj_spd_5 = models.FloatField(null=True, blank=True, verbose_name="五段注射速度")
    inj_spd_6 = models.FloatField(null=True, blank=True, verbose_name="六段注射速度")

    inj_pres_1 = models.FloatField(null=True, blank=True, verbose_name="一段注射压力")
    inj_pres_2 = models.FloatField(null=True, blank=True, verbose_name="二段注射压力")
    inj_pres_3 = models.FloatField(null=True, blank=True, verbose_name="三段注射压力")
    inj_pres_4 = models.FloatField(null=True, blank=True, verbose_name="四段注射压力")
    inj_pres_5 = models.FloatField(null=True, blank=True, verbose_name="五段注射压力")
    inj_pres_6 = models.FloatField(null=True, blank=True, verbose_name="六段注射压力")

    inj_pos_1 = models.FloatField(null=True, blank=True, verbose_name="一段注射位置")
    inj_pos_2 = models.FloatField(null=True, blank=True, verbose_name="二段注射位置")
    inj_pos_3 = models.FloatField(null=True, blank=True, verbose_name="三段注射位置")
    inj_pos_4 = models.FloatField(null=True, blank=True, verbose_name="四段注射位置")
    inj_pos_5 = models.FloatField(null=True, blank=True, verbose_name="五段注射位置")
    inj_pos_6 = models.FloatField(null=True, blank=True, verbose_name="六段注射位置")

    inj_t = models.FloatField(null=True, blank=True, verbose_name="注射时间")
    inj_dly_t = models.FloatField(null=True, blank=True, verbose_name="注射延时")

    # --- VP 切换参数 ---
    vps_mode = models.IntegerField(null=True, blank=True, verbose_name="VP切换模式")
    vps_pos = models.FloatField(null=True, blank=True, verbose_name="VP切换位置")
    vps_t = models.FloatField(null=True, blank=True, verbose_name="VP切换时间")
    vps_pres = models.FloatField(null=True, blank=True, verbose_name="VP切换压力")
    vps_spd = models.FloatField(null=True, blank=True, verbose_name="VP切换速度")

    # --- 保压参数 (5段) ---
    hold_stg = models.IntegerField(null=True, blank=True, verbose_name="保压段数 1-5")
    hold_pres_1 = models.FloatField(null=True, blank=True, verbose_name="一段保压压力")
    hold_pres_2 = models.FloatField(null=True, blank=True, verbose_name="二段保压压力")
    hold_pres_3 = models.FloatField(null=True, blank=True, verbose_name="三段保压压力")
    hold_pres_4 = models.FloatField(null=True, blank=True, verbose_name="四段保压压力")
    hold_pres_5 = models.FloatField(null=True, blank=True, verbose_name="五段保压压力")

    hold_spd_1 = models.FloatField(null=True, blank=True, verbose_name="一段保压速度")
    hold_spd_2 = models.FloatField(null=True, blank=True, verbose_name="二段保压速度")
    hold_spd_3 = models.FloatField(null=True, blank=True, verbose_name="三段保压速度")
    hold_spd_4 = models.FloatField(null=True, blank=True, verbose_name="四段保压速度")
    hold_spd_5 = models.FloatField(null=True, blank=True, verbose_name="五段保压速度")

    hold_t_1 = models.FloatField(null=True, blank=True, verbose_name="一段保压时间")
    hold_t_2 = models.FloatField(null=True, blank=True, verbose_name="二段保压时间")
    hold_t_3 = models.FloatField(null=True, blank=True, verbose_name="三段保压时间")
    hold_t_4 = models.FloatField(null=True, blank=True, verbose_name="四段保压时间")
    hold_t_5 = models.FloatField(null=True, blank=True, verbose_name="五段保压时间")

    # --- 冷却参数 ---
    cool_t = models.FloatField(null=True, blank=True, verbose_name="冷却时间")

    # --- 熔胶参数 (4段) ---
    met_stg = models.IntegerField(null=True, blank=True, verbose_name="熔胶段数 1-4")
    met_pres_1 = models.FloatField(null=True, blank=True, verbose_name="一段熔胶压力")
    met_pres_2 = models.FloatField(null=True, blank=True, verbose_name="二段熔胶压力")
    met_pres_3 = models.FloatField(null=True, blank=True, verbose_name="三段熔胶压力")
    met_pres_4 = models.FloatField(null=True, blank=True, verbose_name="四段熔胶压力")

    met_rot_spd_1 = models.FloatField(null=True, blank=True, verbose_name="一段螺杆转速")
    met_rot_spd_2 = models.FloatField(null=True, blank=True, verbose_name="二段螺杆转速")
    met_rot_spd_3 = models.FloatField(null=True, blank=True, verbose_name="三段螺杆转速")
    met_rot_spd_4 = models.FloatField(null=True, blank=True, verbose_name="四段螺杆转速")

    met_back_pres_1 = models.FloatField(null=True, blank=True, verbose_name="一段背压")
    met_back_pres_2 = models.FloatField(null=True, blank=True, verbose_name="二段背压")
    met_back_pres_3 = models.FloatField(null=True, blank=True, verbose_name="三段背压")
    met_back_pres_4 = models.FloatField(null=True, blank=True, verbose_name="四段背压")

    met_pos_1 = models.FloatField(null=True, blank=True, verbose_name="一段熔胶位置")
    met_pos_2 = models.FloatField(null=True, blank=True, verbose_name="二段熔胶位置")
    met_pos_3 = models.FloatField(null=True, blank=True, verbose_name="三段熔胶位置")
    met_pos_4 = models.FloatField(null=True, blank=True, verbose_name="四段熔胶位置")

    # --- 松退参数 ---
    pre_met_decomp_mode = models.IntegerField(null=True, blank=True, verbose_name="熔胶前松退模式")
    pre_met_decomp_pres = models.FloatField(null=True, blank=True, verbose_name="熔胶前松退压力")
    pre_met_decomp_spd = models.FloatField(null=True, blank=True, verbose_name="熔胶前松退速度")
    pre_met_decomp_t = models.FloatField(null=True, blank=True, verbose_name="熔胶前松退时间")
    pre_met_decomp_dist = models.FloatField(null=True, blank=True, verbose_name="熔胶前松退距离")

    pst_met_decomp_mode = models.IntegerField(null=True, blank=True, verbose_name="熔胶后松退模式")
    pst_met_decomp_pres = models.FloatField(null=True, blank=True, verbose_name="熔胶后松退压力")
    pst_met_decomp_spd = models.FloatField(null=True, blank=True, verbose_name="熔胶后松退速度")
    pst_met_decomp_t = models.FloatField(null=True, blank=True, verbose_name="熔胶后松退时间")
    pst_met_decomp_dist = models.FloatField(null=True, blank=True, verbose_name="熔胶后松退距离")

    met_lim_t = models.FloatField(null=True, blank=True, verbose_name="熔胶延时")
    met_end_pos = models.FloatField(null=True, blank=True, verbose_name="熔胶终止位置")

    # --- 料筒温度参数 (10段) ---
    brl_temp_stg = models.IntegerField(null=True, blank=True, verbose_name="料筒温度段数 1-10")
    noz_temp = models.FloatField(null=True, blank=True, verbose_name="喷嘴温度")
    brl_temp_1 = models.FloatField(null=True, blank=True, verbose_name="一段料筒温度")
    brl_temp_2 = models.FloatField(null=True, blank=True, verbose_name="二段料筒温度")
    brl_temp_3 = models.FloatField(null=True, blank=True, verbose_name="三段料筒温度")
    brl_temp_4 = models.FloatField(null=True, blank=True, verbose_name="四段料筒温度")
    brl_temp_5 = models.FloatField(null=True, blank=True, verbose_name="五段料筒温度")
    brl_temp_6 = models.FloatField(null=True, blank=True, verbose_name="六段料筒温度")
    brl_temp_7 = models.FloatField(null=True, blank=True, verbose_name="七段料筒温度")
    brl_temp_8 = models.FloatField(null=True, blank=True, verbose_name="八段料筒温度")
    brl_temp_9 = models.FloatField(null=True, blank=True, verbose_name="九段料筒温度")

    def save(self, *args, **kwargs):
        if self.pk is None:
            # 自动分配 seq_idx
            last_idx = ProcessParameter.all_objects.filter(
                process_condition=self.process_condition
            ).aggregate(Max('seq_idx'))['seq_idx__max'] or 0
            self.seq_idx = last_idx + 1
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "工艺参数"
        verbose_name_plural = "工艺参数"
```

### 3.3 TuningRecord（调试记录）

```python
class TuningRecord(BusinessBaseModel):
    """
    工艺调参记录 - 记录一次调参与试模结果

    用于追踪工艺调整过程，包含：
    - 缺陷反馈（一次试模可能多个缺陷）
    - 试模结果（迭代状态，支持多轮调试）
    - 当次参数快照（冗余存储，方便查询）

    设计说明：
    - 一个 ProcessParameter 可对应多条 TuningRecord（多轮迭代）
    - 缺陷反馈以 JSON 数组存储，支持多个缺陷
    - parameter_snapshot 冗余存储，避免关联查询
    - 迭代状态：pending → improved/worse → qualified/unqualified
    """

    process_parameter = models.ForeignKey(
        ProcessParameter,
        on_delete=models.CASCADE,
        related_name="tuning_records",
        verbose_name="工艺参数",
    )

    # --- 缺陷反馈（JSON 数组）---
    # [
    #     {
    #         "defect_type": "短射",
    #         "level": "medium",
    #         "position": "产品边缘",
    #         "image_url": "..."
    #     },
    #     {
    #         "defect_type": "飞边",
    #         "level": "light",
    #         "position": "分型线"
    #     }
    # ]
    defect_feedbacks = models.JSONField(
        default=list,
        verbose_name="缺陷反馈列表",
        help_text="一次试模可能包含多个缺陷，JSON数组格式"
    )

    # --- 调参备注 ---
    note = models.CharField(
        max_length=500,
        null=True, blank=True,
        verbose_name="调参备注",
    )

    # --- 试模结果（迭代状态）---
    # 状态流转：待验证 → 有改善/恶化/无变化 → 合格/不合格
    TRIAL_RESULT_CHOICES = [
        ('pending', '待验证'),        # 刚提交，等待试模
        ('improved', '有改善'),      # 参数调整后缺陷有所改善
        ('worse', '效果变差'),        # 调整后问题更严重
        ('unchanged', '无变化'),      # 调整后没有效果
        ('qualified', '合格'),       # 达到质量要求
        ('unqualified', '不合格'),     # 无法达到要求，需换方案
    ]
    result = models.CharField(
        max_length=20,
        choices=TRIAL_RESULT_CHOICES,
        default='pending',
        verbose_name="试模结果",
        help_text="描述本次试模的效果，用于追踪调参迭代过程"
    )

    # --- 结果详情 ---
    # 记录本次调整的具体效果描述
    result_detail = models.CharField(
        max_length=500,
        null=True, blank=True,
        verbose_name="结果详情",
        help_text="具体描述本次调整的效果"
    )

    # --- 参数快照（冗余存储）---
    # 存储当次试模使用的完整参数，方便查询
    parameter_snapshot = models.JSONField(
        null=True, blank=True,
        verbose_name="参数快照",
    )

    class Meta:
        verbose_name = "调参记录"
        verbose_name_plural = "调参记录"
        ordering = ['-created_at']
```

### 3.4 Recommendation（推荐结果）

```python
class Recommendation(BusinessBaseModel):
    """
    推荐结果 - 基于缺陷反馈的智能推荐

    可扩展的 AI 推荐插槽，支持多种 AI 算法：
    - fuzzy_rule: 模糊规则推理
    - rule_miner: 规则挖掘学习
    - llm: 大语言模型
    - doe: 实验设计优化

    设计说明：
    - recommendations 格式由 source_type 决定
    - is_adopted + adopted_param 形成采纳闭环
    """

    process_parameter = models.ForeignKey(
        ProcessParameter,
        on_delete=models.CASCADE,
        related_name="ai_recommendations",
        verbose_name="工艺参数",
    )

    # --- 推荐来源 ---
    SOURCE_TYPE_CHOICES = [
        ('fuzzy_rule', '模糊规则推理'),
        ('rule_miner', '规则挖掘学习'),
        ('llm', '大语言模型'),
        ('doe', '实验设计优化'),
        ('genetic', '遗传算法'),
    ]
    source_type = models.CharField(
        max_length=20,
        choices=SOURCE_TYPE_CHOICES,
        verbose_name="推荐来源类型",
    )

    # --- 推荐方案（JSON 格式）---
    # fuzzy_rule 格式：
    # [
    #     {
    #         "defect": "短射",
    #         "param": "inj_pres_1",
    #         "action": "increase",
    #         "current_value": 50,
    #         "recommended_value": 60,
    #         "confidence": 0.85
    #     }
    # ]
    #
    # llm 格式：
    # [
    #     {
    #         "strategy": "...",
    #         "params": {...},
    #         "reasoning": "..."
    #     }
    # ]
    recommendations = models.JSONField(
        default=list,
        verbose_name="推荐方案列表",
    )

    # --- 采纳状态 ---
    is_adopted = models.BooleanField(
        default=False,
        verbose_name="是否已采纳",
    )

    adopted_param = models.ForeignKey(
        ProcessParameter,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="adopted_from_recommendations",
        verbose_name="采纳后的参数版本",
    )

    class Meta:
        verbose_name = "推荐结果"
        verbose_name_plural = "推荐结果"
        ordering = ['-created_at']
```

## 4. 版本树示例

```
ProcessCondition (同一模具+机台+材料)
└── Parameter v1 (seq_idx=1, parent=null, source=manual)
    ├── Parameter v1.1 (seq_idx=1, parent=v1, source=manual_adjusted)
    │   ├── Parameter v1.1.1 (seq_idx=1, parent=v1.1, source=ai_recommended)
    │   │   └── Parameter v1.1.1.1 (seq_idx=1, parent=v1.1.1, source=manual_adjusted)
    │   └── Parameter v1.1.2 (seq_idx=2, parent=v1.1, source=manual_adjusted)
    └── Parameter v1.2 (seq_idx=2, parent=v1, source=manual_adjusted)
        └── Parameter v1.2.1 (seq_idx=1, parent=v1.2, source=manual_adjusted)
            └── Parameter v1.2.1.1 (seq_idx=1, parent=v1.2.1, source=manual_adjusted)
```

## 5. 场景组合

| 场景 | 模型组合 | 说明 |
|------|----------|------|
| **基础工艺存储** | `Condition + Parameter` | 仅保存工艺参数，方便调用 |
| **调参过程追踪** | `Condition + Parameter + TuningRecord` | 记录调试历史、缺陷反馈 |
| **工艺模板** | `Condition + Parameter` | 作为模板引导用户 |
| **推荐** | `Condition + Parameter + Recommendation` | 基于缺陷反馈的智能推荐 |
| **完整调优闭环** | `Condition + Parameter + TuningRecord + Recommendation` | 完整场景 |

## 6. 字段说明

### 6.1 关键枚举值

**status（工艺状态）**
- `draft`: 草稿
- `testing`: 测试中
- `approved`: 已批准
- `rejected`: 已废弃
- `obsolete`: 已过时

**origin_type（工艺起源）**
- `manual_creation`: 手工新建
- `template_based`: 基于模板
- `ai_recommendation`: AI 推荐启动
- `doe_experiment`: 实验设计
- `legacy_import`: 历史导入
- `equipment_capture`: 设备参数捕获
- `process_transplant`: 工艺移植

**param_source（参数来源）**
- `unknown`: 未知
- `manual`: 手工录入
- `import`: 外部导入
- `algorithm_init`: 算法初始化
- `system_inferred`: 系统推理
- `manual_adjusted`: 人工调整
- `equipment_sync`: 设备同步
- `template_copy`: 模板复制
- `ai_recommended`: AI 推荐

**result（试模结果）**
- `pending`: 待验证
- `qualified`: 合格
- `unqualified`: 不合格

**source_type（AI来源）**
- `fuzzy_rule`: 模糊规则推理
- `rule_miner`: 规则挖掘学习
- `llm`: 大语言模型
- `doe`: 实验设计优化
- `genetic`: 遗传算法

---

*文档生成时间：2026-06-29*

## 7. 规则库模型（层级化设计）

### 7.1 设计原则

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        规则库层级结构                                      │
└─────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────┐
    │  RuleLibrary    │  租户级：不同租户/产品线拥有独立规则库
    │  (规则库顶层)    │
    └────────┬────────┘
             │
             ├──────────────────┬──────────────────┐
             ▼                  ▼                  ▼
    ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
    │   RuleKeyword    │ │   RuleMethod     │ │ TenantKeywordOverride│
    │   (系统级)       │ │   (规则库级)     │ │   (租户覆盖)     │
    │                 │ │                 │ │                 │
    │ - 参数元数据     │ │ - 缺陷调整规则   │ │ - 展示偏好      │
    │ - 默认值/范围    │ │ - 模糊规则       │ │ - 覆盖值        │
    └─────────────────┘ └─────────────────┘ └─────────────────┘
```

| 模型 | 层级 | 说明 |
|------|------|------|
| **RuleLibrary** | 租户级 | 规则库顶层，支持多租户/多产品线隔离 |
| **RuleKeyword** | 系统级 | 参数元数据（通用默认值），系统统一维护 |
| **RuleMethod** | 规则库级 | 缺陷→调整规则，按规则库隔离 |
| **TenantKeywordOverride** | 租户级 | 租户对关键词的覆盖（如界面展示偏好） |
| **MinedRule** | 规则库级 | 规则挖掘结果，待审核的规则 |
| **ExpertRule** | 规则库级 | 专家规则，用于工艺初始化 |

**取值范围加载逻辑：**

```python
def get_param_range(param_name: str, context: dict) -> tuple:
    """
    获取参数有效范围
    优先级：设备真实范围 > RuleKeyword 默认值
    """
    # 1. 优先使用设备的真实范围
    machine = context.get('machine')
    if machine and machine.has_capability(param_name):
        return machine.get_capability_range(param_name)
    
    # 2. Fallback 到 RuleKeyword 默认值（通用推荐范围）
    keyword = RuleKeyword.objects.get(keyword_name=param_name)
    return keyword.range_min, keyword.range_max
```

### 7.2 RuleLibrary - 规则库

```python
class RuleLibrary(BusinessBaseModel):
    """
    规则库 - 规则库顶层，支持多租户/多产品线隔离
    """
    
    # --- 规则库标识 ---
    library_code = models.CharField(max_length=50, unique=True, verbose_name="规则库编码")
    # 示例: 'general' / 'auto_parts' / 'medical'
    
    library_name = models.CharField(max_length=100, verbose_name="规则库名称")
    description = models.TextField(null=True, blank=True, verbose_name="规则库描述")
    
    # --- 归属信息 ---
    OWNER_TYPES = [
        ('system', '系统级'),
        ('tenant', '租户级'),
        ('user', '用户级'),
    ]
    owner_type = models.CharField(max_length=20, choices=OWNER_TYPES, verbose_name="归属类型")
    
    tenant = models.ForeignKey(
        'identity.Tenant',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name="rule_libraries",
        verbose_name="所属租户",
    )
    
    user = models.ForeignKey(
        'identity.User',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name="rule_libraries",
        verbose_name="所属用户",
    )
    
    # --- 规则库元数据 ---
    priority = models.IntegerField(default=0, verbose_name="优先级")
    # 高优先级规则库可覆盖低优先级规则库
    
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    
    # --- 版本管理 ---
    version = models.IntegerField(default=1, verbose_name="版本号")
    parent_library = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='children',
        verbose_name="父规则库",
    )
    
    class Meta:
        verbose_name = "规则库"
        verbose_name_plural = "规则库"
```

### 7.3 RuleKeyword - 规则关键词（系统级）

```python
class RuleKeyword(BusinessBaseModel):
    """
    规则关键词 - 系统级参数元数据定义
    
    注意：
    - 取值范围是通用默认值/模拟推荐值，非设备物理极限
    - 实际推理时：设备真实范围 > RuleKeyword 默认值
    """
    
    # --- 参数标识 ---
    keyword_name = models.CharField(max_length=50, unique=True, verbose_name="关键词名称")
    # 示例: 'inj_pres_1', 'hold_pres_1'
    
    keyword_alias = models.CharField(max_length=100, verbose_name="关键词别名")
    # 示例: '注射压力1', '保压压力1'
    
    # --- 参数分组 ---
    PARAM_GROUPS = [
        ('injection', '注射参数'),
        ('holding', '保压参数'),
        ('cooling', '冷却参数'),
        ('metering', '计量参数'),
        ('temperature', '温度参数'),
    ]
    param_group = models.CharField(max_length=20, choices=PARAM_GROUPS, verbose_name="参数分组")
    
    # --- 通用默认值/推荐范围（无设备数据时的参考值）---
    range_min = models.FloatField(verbose_name="默认最小值")
    range_max = models.FloatField(verbose_name="默认最大值")
    
    # --- 调整参数 ---
    action_range_min = models.FloatField(null=True, blank=True, verbose_name="调整区间最小值")
    action_range_max = models.FloatField(null=True, blank=True, verbose_name="调整区间最大值")
    action_max_val = models.FloatField(null=True, blank=True, verbose_name="最大调整值")
    
    # --- 模糊参数 ---
    FUZZY_LEVELS = [(3, '3级'), (5, '5级')]
    fuzzy_level = models.IntegerField(choices=FUZZY_LEVELS, default=3, verbose_name="模糊级别")
    
    # --- 参数类型 ---
    keyword_type = models.CharField(max_length=45, verbose_name="参数类型")
    # 示例: 'pressure', 'speed', 'time', 'temperature'
    
    # --- 单位 ---
    unit = models.CharField(max_length=20, verbose_name="单位")
    # 示例: 'MPa', 'mm/s', 's', '℃'
    
    # --- 分类维度（可选，用于规则匹配）---
    subrule_no = models.CharField(max_length=45, null=True, blank=True, verbose_name="子规则编号")
    product_small_type = models.CharField(max_length=45, null=True, blank=True, verbose_name="产品小类")
    polymer_abbreviation = models.CharField(max_length=45, null=True, blank=True, verbose_name="材料简称")
    
    class Meta:
        verbose_name = "规则关键词"
        verbose_name_plural = "规则关键词"
```

### 7.4 TenantKeywordOverride - 租户关键词覆盖

```python
class TenantKeywordOverride(BusinessBaseModel):
    """
    租户关键词覆盖 - 租户可覆盖部分 RuleKeyword 行为
    """
    
    keyword = models.ForeignKey(
        RuleKeyword,
        on_delete=models.CASCADE,
        related_name='tenant_overrides',
        verbose_name="关键词",
    )
    
    tenant = models.ForeignKey(
        'identity.Tenant',
        on_delete=models.CASCADE,
        related_name='keyword_overrides',
        verbose_name="租户",
    )
    
    # --- 覆盖的默认值 ---
    action_range_max = models.FloatField(null=True, blank=True, verbose_name="覆盖调整区间最大值")
    
    # --- 展示偏好 ---
    show_on_page = models.BooleanField(null=True, blank=True, verbose_name="是否在界面展示")
    show_order = models.IntegerField(null=True, blank=True, verbose_name="展示顺序")
    
    class Meta:
        verbose_name = "租户关键词覆盖"
        verbose_name_plural = "租户关键词覆盖"
        unique_together = ['keyword', 'tenant']
```

### 7.5 RuleMethod - 规则方法（模糊规则）

```python
class RuleMethod(BusinessBaseModel):
    """
    规则方法 - 缺陷→参数调整规则
    属于某个规则库，按租户/产品线隔离
    """
    
    rule_library = models.ForeignKey(
        RuleLibrary,
        on_delete=models.CASCADE,
        related_name='rule_methods',
        verbose_name="所属规则库",
    )
    
    # --- 规则标识 ---
    subrule_no = models.CharField(max_length=45, verbose_name="子规则编号")
    rule_code = models.CharField(max_length=50, verbose_name="规则编码")
    
    # --- 匹配条件 ---
    polymer_category = models.CharField(max_length=45, null=True, blank=True, verbose_name="材料类别")
    product_category = models.CharField(max_length=45, null=True, blank=True, verbose_name="产品类别")
    
    # --- 缺陷信息 ---
    defect_name = models.CharField(max_length=45, verbose_name="缺陷名称")
    defect_desc = models.CharField(max_length=200, null=True, blank=True, verbose_name="缺陷描述")
    
    # --- 规则内容 ---
    rule_description = models.TextField(verbose_name="规则描述")
    rule_explanation = models.TextField(null=True, blank=True, verbose_name="规则解释")
    
    # --- 规则内容（JSON格式）---
    # 示例:
    # {
    #     "conditions": [
    #         {"param": "inj_pres_1", "operator": "<", "value": 60}
    #     ],
    #     "adjustments": [
    #         {"param": "inj_pres_1", "action": "increase", "value": 10}
    #     ]
    # }
    rule_content = models.JSONField(verbose_name="规则内容")
    
    # --- 规则元数据 ---
    rule_type = models.CharField(max_length=45, verbose_name="规则类型")
    priority = models.FloatField(default=1.0, verbose_name="优先级")
    confidence = models.FloatField(default=1.0, verbose_name="置信度")
    
    # --- 启用控制 ---
    is_auto = models.BooleanField(default=True, verbose_name="是否自动应用")
    enable = models.BooleanField(default=True, verbose_name="是否启用")
    
    # --- 规则来源 ---
    SOURCE_TYPES = [
        ('expert', '专家经验'),
        ('rule_miner', '规则挖掘'),
        ('llm', '大模型生成'),
    ]
    source = models.CharField(max_length=20, choices=SOURCE_TYPES, verbose_name="规则来源")
    
    class Meta:
        verbose_name = "规则方法"
        verbose_name_plural = "规则方法"
        unique_together = ['rule_library', 'rule_code']
```

### 7.6 MinedRule - 挖掘规则结果

```python
class MinedRule(BusinessBaseModel):
    """
    挖掘规则 - 规则挖掘引擎生成的结果，待审核入库
    """
    
    rule_library = models.ForeignKey(
        RuleLibrary,
        on_delete=models.CASCADE,
        related_name='mined_rules',
        verbose_name="所属规则库",
    )
    
    # --- 规则内容 ---
    # 示例:
    # {
    #     "defect_type": "短射",
    #     "conditions": [...],
    #     "adjustments": [...],
    #     "confidence": 0.85,
    #     "support": 15,
    #     "lift": 2.3
    # }
    rule_content = models.JSONField(verbose_name="规则内容")
    
    # --- 统计信息 ---
    support_count = models.IntegerField(verbose_name="支持次数")
    confidence = models.FloatField(verbose_name="置信度")
    lift = models.FloatField(verbose_name="提升度")
    
    # --- 审核状态 ---
    REVIEW_STATUS = [
        ('pending', '待审核'),
        ('approved', '已通过'),
        ('rejected', '已拒绝'),
    ]
    review_status = models.CharField(
        max_length=20,
        choices=REVIEW_STATUS,
        default='pending',
        verbose_name="审核状态",
    )
    
    # --- 审核信息 ---
    reviewed_by = models.ForeignKey(
        'identity.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='reviewed_mined_rules',
        verbose_name="审核人",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name="审核时间")
    review_comment = models.TextField(null=True, blank=True, verbose_name="审核意见")
    
    class Meta:
        verbose_name = "挖掘规则"
        verbose_name_plural = "挖掘规则"
        ordering = ['-created_at']
```

### 7.7 ExpertRule - 专家规则（初始化规则）

```python
class ExpertRule(BusinessBaseModel):
    """
    专家规则 - 工艺初始化引擎使用的专家规则
    用于 ExpertEngine 根据模具/材料/机台推理初始工艺参数
    """
    
    rule_library = models.ForeignKey(
        RuleLibrary,
        on_delete=models.CASCADE,
        related_name='expert_rules',
        verbose_name="所属规则库",
    )
    
    # --- 规则标识 ---
    rule_code = models.CharField(max_length=50, unique=True, verbose_name="规则编码")
    rule_name = models.CharField(max_length=100, verbose_name="规则名称")
    
    # --- 规则条件 ---
    # 示例:
    # {
    #     "polymer.category": "结晶型",
    #     "product.max_thickness": {">": 2.0}
    # }
    condition = models.JSONField(verbose_name="规则条件")
    
    # --- 规则结论 ---
    # 示例:
    # {
    #     "hold_pressure": {"formula": "max_pressure * 0.7"},
    #     "cooling_time": {"formula": "5 * max_thickness"}
    # }
    conclusion = models.JSONField(verbose_name="规则结论")
    
    # --- 规则元数据 ---
    priority = models.IntegerField(default=0, verbose_name="优先级")
    confidence = models.FloatField(default=1.0, verbose_name="置信度")
    
    SOURCE_TYPES = [
        ('expert', '专家经验'),
        ('rule_miner', '规则挖掘'),
        ('llm', '大模型生成'),
    ]
    source = models.CharField(max_length=20, choices=SOURCE_TYPES, verbose_name="规则来源")
    
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    
    # --- 版本管理 ---
    version = models.IntegerField(default=1, verbose_name="版本号")
    parent_rule = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='children',
        verbose_name="父规则",
    )
    
    class Meta:
        verbose_name = "专家规则"
        verbose_name_plural = "专家规则"

---

## 8. 优化设计总结

### 8.1 ProcessCondition 三层结构

```
┌─────────────────────────────────────────────────────────────┐
│                    ProcessCondition                          │
│                                                              │
│  【顶层外键】核心实体，可追溯                                  │
│  ├── mold (FK)                                               │
│  ├── injection_machine (FK)                                  │
│  └── polymer (FK)                                            │
│                                                              │
│  【索引定位】业务规则推导                                      │
│  ├── shot_index → gating_system（业务规则）                  │
│  └── injection_index → InjectionUnit（索引定位）            │
│                                                              │
│  【JSON 上下文】动态细节 + 用户覆盖                            │
│  └── process_context_snapshot                                │
│      ├── gating_system_id, cavity_id, gate_id               │
│      ├── overrides（产品/工艺字段）                          │
│      └── matched_rules, source（快照元信息）                │
└─────────────────────────────────────────────────────────────┘
```

### 8.2 业务规则推导接口

```python
class ProcessConditionService:
    @staticmethod
    def resolve_gating_system(condition):
        """mold + shot_index → GatingSystem"""
        systems = condition.mold.gating_systems.order_by('id')
        idx = condition.shot_index or 1
        if 1 <= idx <= len(systems):
            return systems[idx - 1]
        return systems.first()
    
    @staticmethod
    def resolve_injection_unit(condition):
        """machine + injection_index → InjectionUnit"""
        units = condition.injection_machine.injection_units.all()
        idx = condition.injection_index or 1
        if 1 <= idx <= len(units):
            return units[idx - 1]
        return units.first()
    
    @staticmethod
    def get_overrides(condition):
        """从快照中提取用户覆盖"""
        snapshot = condition.process_context_snapshot or {}
        return snapshot.get('overrides', {})
```

### 8.3 为什么不用硬外键

| 场景 | 硬外键 | JSON 上下文 |
|------|--------|--------------|
| molding腔变化频繁 | 需频繁迁移 | JSON 灵活扩展 |
| 多射复杂场景 | 多个FK关联难表达 | JSON 嵌套表达 |
| 用户随时调整 | 需要额外字段 | overrides 直接存 |
| 历史快照 | 依赖外部关联 | 快照独立完整 |

### 8.4 适用原则

1. **核心实体必须 FK**：mold、machine、polymer 是不可变的核心
2. **动态关系业务规则推导**：shot_index → gating_system
3. **复杂嵌套 JSON 表达**：cavity、gate、overrides
4. **快照保留独立性**：process_context_snapshot 不依赖外部关联

### 8.5 相关文档

| 文档 | 说明 |
|------|------|
| `_dev_refs/init-api-refactor-design.md` | 工艺初始化接口重构设计 |
| `_dev_refs/algorithm-context-design.md` | 算法上下文双重来源设计 |
| `_dev_refs/process-ai-architecture-design.md` | 工艺智能系统架构设计 |
| `_dev_refs/process-init-rule-design.md` | 工艺初始化规则设计 |

---

*文档生成时间：2026-06-29*
*最后更新：2026-07-02*
