"""
工艺设置字段定义 + 默认值兜底

process_set 是 ProcessInitializer 的第 4 个入参维度，
与 mold/machine/polymer 性质不同：
- mold/machine/polymer: 数据契约（来自 ORM 提取，必填校验，缺失报错）
- process_set: 行为配置（来自前端用户输入，可选，缺失用 default 兜底）

设计要点：
- 字段定义与 specs.MOLD_INFO_SPEC 等保持一致结构（source_model/source/attr_name/desc/type/condition）
- 增加 default 字段（默认值）
- condition 全部为 "可选"（不参与 DataValidator 校验）
- 由 ProcessSetDefaults.fill_defaults() 在 ProcessInitializer.__init__ 中调用
"""

from typing import Any, Dict


# ---- process_set 工艺设置字段定义（前端输入 + 默认值兜底） ----
PROCESS_SET_FIELDS: Dict[str, Dict[str, Any]] = {
    'inj_stg': {
        'source_model': 'ProcessSet',  # 虚拟模型名（无 ORM）
        'source': '前端用户输入（未传时为 None，算法层走自动推荐）',
        'attr_name': 'inj_stg',
        'desc': '注射段数（1-6），未指定时由算法按 total_len 推荐',
        'type': int,
        'condition': '可选',
        'default': None,  # sentinel：None 表示「未指定」→ 算法推荐
    },
    'hold_stg': {
        'source_model': 'ProcessSet',
        'source': '前端用户输入（未传时取行业标准默认值 2）',
        'attr_name': 'hold_stg',
        'desc': '保压段数（1-5），行业标准 2 段',
        'type': int,
        'condition': '可选',
        'default': 2,  # 业务默认：保压 2 段（不是 sentinel，因为算法层没「自动推荐」逻辑）
    },
    'met_stg': {
        'source_model': 'ProcessSet',
        'source': '前端用户输入（未传时取行业标准默认值 1）',
        'attr_name': 'met_stg',
        'desc': '计量段数（1-4），行业标准 1 段',
        'type': int,
        'condition': '可选',
        'default': 1,  # 业务默认：单段计量（不是 sentinel，理由同 hold_stg）
    },
    'brl_temp_stg': {
        'source_model': 'ProcessSet',
        'source': '前端用户输入（缺失时取 default）',
        'attr_name': 'brl_temp_stg',
        'desc': '料筒温度段数（1-10）',
        'type': int,
        'condition': '可选',
        'default': 5,  # 行业标准：5 段温度
    },
    'vps_mode': {
        'source_model': 'ProcessSet',
        'source': '前端用户输入（缺失时取 default）',
        'attr_name': 'vps_mode',
        'desc': 'VP 切换模式（0=位置/1=时间/2=其他）',
        'type': int,
        'condition': '可选',
        'default': 0,  # 位置切换（最常见）
    },
    'pre_met_decomp_mode': {
        'source_model': 'ProcessSet',
        'source': '前端用户输入（缺失时取 default）',
        'attr_name': 'pre_met_decomp_mode',
        'desc': '熔胶前松退模式（0=否/1=是）',
        'type': int,
        'condition': '可选',
        'default': 0,  # 否（默认不松退）
    },
    'pst_met_decomp_mode': {
        'source_model': 'ProcessSet',
        'source': '前端用户输入（缺失时取 default）',
        'attr_name': 'pst_met_decomp_mode',
        'desc': '熔胶后松退模式（0=否/1=是）',
        'type': int,
        'condition': '可选',
        'default': 0,  # 否（默认不松退）
    },
}


# ---- 工艺设置默认值（前端不传时填充） ----
# 区分两种默认值语义：
# 1. Sentinel 默认值（None）：明确表达「未指定」，算法层走自动推荐
#    目前只有 inj_stg——因为算法会按 total_len 自动推荐多级注射
# 2. 业务默认值（2 / 1 / 5 / 0）：走这个值业务上是合理的
#    （如 hold_stg=2 是行业标准, met_stg=1 是单段计量, brl_temp_stg=5 是 5 段温度）
#    算法层没「自动推荐」逻辑时，必须保留业务默认（否则 `ps.get('hold_stg', 2)` 会因 None 漏洞返回 None）
#
# 为什么 inj_stg 要用 None 而 hold_stg/met_stg 不用：
# - inj_stg 有「按 total_len 推荐」算法 → None 表示「走推荐」
# - hold_stg/met_stg 没自动推荐算法 → 业务默认（2/1）就是正确答案
# - 如果 hold_stg 也改 None，会触发 dict.get(k, default) 的 None 漏洞
PROCESS_SET_DEFAULTS: Dict[str, Any] = {
    # 多级注射：sentinel（None = 走算法推荐）
    'inj_stg': None,
    # 多级保压 / 计量：保留业务默认（没有自动推荐算法）
    'hold_stg': 2,  # 行业标准：保压 2 段
    'met_stg': 1,  # 行业标准：单段计量
    # 其他业务参数：保留业务默认
    'brl_temp_stg': 5,  # 行业标准：5 段温度
    'vps_mode': 0,  # 位置切换（最常见）
    'pre_met_decomp_mode': 0,  # 否（默认不松退）
    'pst_met_decomp_mode': 0,  # 否（默认不松退）
}


class ProcessSetDefaults:
    """工艺设置默认值（前端不传时填充）

    类似 MaterialDatabase，但针对 process_set 维度。
    在 ProcessInitializer.__init__ 中调用 fill_defaults()，
    保证 process_set 字段齐全，算法层无需再判断字段是否缺失。
    """

    DEFAULTS = PROCESS_SET_DEFAULTS

    @classmethod
    def fill_defaults(cls, process_set: Dict[str, Any]) -> None:
        """按 PROCESS_SET_DEFAULTS 填充缺失字段

        Args:
            process_set: 工艺设置 dict（会被直接修改，填充默认值）

        Note:
            只填充缺失字段，已存在的字段不会被覆盖
        """
        for key, value in cls.DEFAULTS.items():
            if not process_set.get(key):
                process_set[key] = value


__all__ = [
    "PROCESS_SET_FIELDS",
    "PROCESS_SET_DEFAULTS",
    "ProcessSetDefaults",
]
