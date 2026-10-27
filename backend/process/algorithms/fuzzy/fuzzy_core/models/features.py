"""论域实例 —— FuzzyFeature。

**层定位**：内核内部的**论域实例**（某一个具体变量的隶属度表示）。

与 `fuzzy_core.profiles.KeywordProfile` 的分工：

- `KeywordProfile` = **字段元数据**（一个工艺参数的档案：名字 / 档位数 /
  论域上下界 / 步长）
- `FuzzyFeature` = **论域实例**（把某个 Profile 的某一侧论域变成可计算的
  隶属度函数）

⇒ 一个字段会派生**两个** `FuzzyFeature`：输入侧论域 `[min_val, max_val]`
（算前件隶属度）与输出侧论域 `[0, step]`（Mamdani 输出反模糊化）。
所以两者**不是一对一**，不是重复定义。

`FuzzyFeature` 由内核在构建网络时从 Profile 派生，**不是外部契约**。

⚠️ **本类不持有特征名与特征类别**：特征名由调用方（`nets.py` 的 `k_dict`）
持有，特征类别由「输入侧论域 / 输出侧论域」天然区分 —— 内核里没有任何分支
依赖特征名或特征类别，故二者既不入参数、也不入实例属性。
"""

import logging

import numpy as np

from ..memberships import MEMBERSHIP_SPECS
from ..macros import DEFAULT_MEMBERSHIP_TYPE, MEMBERSHIP_TYPES, bucket_centers


__all__ = ['FuzzyFeature']

logger = logging.getLogger(__name__)


class FuzzyFeature:
    """每一个特征模糊化表示类。

    用作规则条件词，储存模糊化数值、对应的隶属度函数参数。

    Parameters
    ----------
    f_interval : list[float]
        特征取值区间 [min_val, max_val]（输入侧）或 [0, step]（输出侧）
    f_membership_type : str
        隶属度函数类型；取值范围见 `macros.MEMBERSHIP_TYPES`
        （由 `memberships.MEMBERSHIP_SPECS` 派生：高斯 / 双高斯 / 三角 / 梯形 /
        钟形 / 代数钟形 / S 型 / Z 型 / 单点）
    f_level : int
        特征模糊划分数量 (3 / 5 / 7 / 9)

    Attributes
    ----------
    f_level : int
        特征模糊划分数量
    membership_func : Callable
        隶属度函数实现（由 `memberships.MEMBERSHIP_SPECS` 按类型分派）
    membership_shape : Any
        该类型的形状参数（取自 `MEMBERSHIP_SPECS.default_shape`，
        是形状参数的**唯一真源**，避免函数内默认值与分派表各写一份）
    membership_dict : dict
        {degree_i: [中心, 总跨度]} —— 统一签名 `(x, center, width, shape=None)`
        的前两个参数
    """

    def __init__(self, f_interval, f_membership_type=DEFAULT_MEMBERSHIP_TYPE, f_level=3):
        self.f_level = f_level
        self.membership_dict = {}

        # 类型白名单来自 macros.MEMBERSHIP_TYPES（声明与实现同源，不再各说各话）
        if f_membership_type not in MEMBERSHIP_TYPES:
            raise ValueError(
                f'不支持的隶属度函数类型: {f_membership_type}'
                f'（当前支持: {", ".join(MEMBERSHIP_TYPES)}）'
            )

        spec = MEMBERSHIP_SPECS[f_membership_type]
        self.membership_func = spec.func
        self.membership_shape = spec.default_shape

        # 论域跨度取**绝对值**：
        #   上游可能给出倒序论域 —— engine.py 缺权威元数据时按实时值推测论域
        #   （`max_val = 当前值 * 2`），当前值为负时区间倒挂。
        #   σ 若**带符号**，高斯只用 σ² ⇒ 取绝对后数值**逐位不变**；
        #   对其余形状则是唯一自洽的定义（跨度非负）⇒ 倒序论域不再让内核抛错。
        low, high = float(f_interval[0]), float(f_interval[1])
        span = abs(high - low)
        if high < low:
            logger.warning(
                'FuzzyFeature 论域倒序：interval=[%s, %s] ⇒ 跨度取绝对值 %s',
                low, high, span,
            )
        elif span == 0:
            # 退化论域：隶属度恒为 0（中心点为 nan）。上游成因同 engine.py
            # 的推测分支 —— 当前实时值为 0 时 `max_val = 当前值 * 2` 也为 0。
            # 这里只告警不改数值：改数值会动到生产推理结果，属另一轮改造。
            logger.warning(
                'FuzzyFeature 论域退化：interval=[%s, %s] ⇒ 隶属度恒为 0/nan'
                '（该字段缺有效元数据？）', low, high,
            )

        # σ 的推导式保持不变；统一签名的 width 是**总跨度** = 2σ，
        # 函数内再除回 2 ⇒ σ 逐位还原，生产数值零变化。
        sigmas = np.array([span / (2 * (f_level - 1))] * f_level)
        means = bucket_centers(f_interval, f_level)
        for i in range(f_level):
            self.membership_dict['degree_' + str(i)] = [float(means[i]), float(sigmas[i]) * 2.0]

    def get_value_by_level(self, x, level):
        """获取给定值 x 在指定模糊级别上的隶属度值。"""
        if 0 <= level < self.f_level:
            degree_key = 'degree_' + str(level)
            center, width = self.membership_dict[degree_key]
            return self.membership_func(x, center, width, self.membership_shape)
        raise ValueError('level 超出定义范围！')
