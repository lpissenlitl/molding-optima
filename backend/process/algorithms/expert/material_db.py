"""
材料族智能默认值——按 abbreviation 查材料物理参数

兑底范围【仅限材料参数】polymer_info：
- 材料族推荐值是「行业经验值」（PP density=0.91, melt_temp=220）
- 模具/注塑机参数是「设备/模具实测值」，不在本文件兑底
  - mold_info / machine_info 缺必填 → audit 严格拦
  - 不要在本文件加 mold/machine 兑底机制

解决问题：
- 部分材料物理参数（如 melt_density / recommended_melt_temp）业务侧不一定采集
- 不能用统一默认值（PP 用 0.95 密度是正确的，POM 用 0.95 算出来会错）
- 解决方案：按材料 abbreviation 查材料族默认值

调用方：
- DataValidator.validate() 在校验前调用 MaterialDatabase.fill_defaults()
- 缺失字段按材料族自动填充，业务侧可补充新材料

混合材料处理（2026-10-14）：
- 优先全名匹配（PC+ABS / PA66+GF30 等预填的）
- 全名未匹配 → 拆 '+' 取第一个主材料兑底（PP+PA66 → 取 PP）
- 主料也查不到 → 返回空（让上游 audit 拦）

字段名约定：
- 用 POLYMER_INFO_FIELDS 的"外层字段名"（即 algorithm 入参 dict 的 key）
- 例：recommend_melt_temperature（不是 recommended_melt_temp）
- 这样智能填充能直接填到 POLYMER_INFO_FIELDS 定义的字段上
"""

from typing import Any, Dict


# 材料族默认物理参数（业务可补充新材料）
# 行业经验值，按材料族归类
# 字段名用 POLYMER_INFO_FIELDS 的"外层字段名"
MATERIAL_DEFAULTS: Dict[str, Dict[str, float]] = {
    # 通用塑料
    'PP':  {'melt_density': 0.91, 'recommend_melt_temperature': 220, 'recommend_shear_linear_speed': 150, 'recommend_back_pressure': 8.0, 'recommend_mold_temperature': 50},
    'PE':  {'melt_density': 0.95, 'recommend_melt_temperature': 200, 'recommend_shear_linear_speed': 140, 'recommend_back_pressure': 8.0, 'recommend_mold_temperature': 40},
    'PS':  {'melt_density': 1.05, 'recommend_melt_temperature': 220, 'recommend_shear_linear_speed': 150, 'recommend_back_pressure': 10.0, 'recommend_mold_temperature': 50},
    'ABS': {'melt_density': 1.05, 'recommend_melt_temperature': 230, 'recommend_shear_linear_speed': 160, 'recommend_back_pressure': 10.0, 'recommend_mold_temperature': 60},
    'PC':  {'melt_density': 1.20, 'recommend_melt_temperature': 300, 'recommend_shear_linear_speed': 180, 'recommend_back_pressure': 12.0, 'recommend_mold_temperature': 90},
    'PMMA':{'melt_density': 1.18, 'recommend_melt_temperature': 240, 'recommend_shear_linear_speed': 150, 'recommend_back_pressure': 10.0, 'recommend_mold_temperature': 70},

    # 工程塑料
    'POM': {'melt_density': 1.42, 'recommend_melt_temperature': 200, 'recommend_shear_linear_speed': 140, 'recommend_back_pressure': 8.0, 'recommend_mold_temperature': 80},
    'PA':  {'melt_density': 1.14, 'recommend_melt_temperature': 260, 'recommend_shear_linear_speed': 200, 'recommend_back_pressure': 10.0, 'recommend_mold_temperature': 80},
    'PA66':{'melt_density': 1.14, 'recommend_melt_temperature': 280, 'recommend_shear_linear_speed': 200, 'recommend_back_pressure': 10.0, 'recommend_mold_temperature': 80},
    'PBT': {'melt_density': 1.31, 'recommend_melt_temperature': 250, 'recommend_shear_linear_speed': 160, 'recommend_back_pressure': 10.0, 'recommend_mold_temperature': 80},
    'PET': {'melt_density': 1.40, 'recommend_melt_temperature': 270, 'recommend_shear_linear_speed': 160, 'recommend_back_pressure': 10.0, 'recommend_mold_temperature': 90},

    # 高温塑料
    'PVC': {'melt_density': 1.40, 'recommend_melt_temperature': 190, 'recommend_shear_linear_speed': 130, 'recommend_back_pressure': 8.0, 'recommend_mold_temperature': 40},
    'PEEK':{'melt_density': 1.30, 'recommend_melt_temperature': 380, 'recommend_shear_linear_speed': 200, 'recommend_back_pressure': 12.0, 'recommend_mold_temperature': 170},
    'PTFE':{'melt_density': 2.20, 'recommend_melt_temperature': 380, 'recommend_shear_linear_speed': 100, 'recommend_back_pressure': 6.0, 'recommend_mold_temperature': 200},

    # ========== 混合材料 / 增强材料（按业务补充）==========
    # 说明：
    # - 优先全名匹配（get_defaults 优先级：全名 > 取第一个主材料）
    # - 业务侧可以继续补充混合材料的工程经验值（精确度 > 取第一个主材料兑底）
    # - 找不到时才 fallback 到「取第一个主材料」兑底（80% 场景够用）
    #
    # 取值依据：各主材料均值 + 合金/增强体系的工程经验调整
    # - PC+ABS: 高温低于 PC、高于 ABS；表面质量好于 ABS；流动性优于 PC
    # - PA66+GF30: 高于 PA66，流动性下降，背压上升
    # - PP+GF20: 高于 PP 纯料，流动性下降，熔体温度升高
    'PC+ABS':   {'melt_density': 1.10, 'recommend_melt_temperature': 250, 'recommend_shear_linear_speed': 170, 'recommend_back_pressure': 10.0, 'recommend_mold_temperature': 70},
    'PA66+GF30':{'melt_density': 1.36, 'recommend_melt_temperature': 290, 'recommend_shear_linear_speed': 180, 'recommend_back_pressure': 12.0, 'recommend_mold_temperature': 90},
    'PP+GF20':  {'melt_density': 1.04, 'recommend_melt_temperature': 240, 'recommend_shear_linear_speed': 130, 'recommend_back_pressure': 10.0, 'recommend_mold_temperature': 60},
    'PBT+GF30': {'melt_density': 1.52, 'recommend_melt_temperature': 260, 'recommend_shear_linear_speed': 150, 'recommend_back_pressure': 12.0, 'recommend_mold_temperature': 90},
    'PA66+PA6': {'melt_density': 1.13, 'recommend_melt_temperature': 275, 'recommend_shear_linear_speed': 200, 'recommend_back_pressure': 10.0, 'recommend_mold_temperature': 80},
}


class MaterialDatabase:
    """材料族默认物理参数（智能兜底）"""

    DEFAULTS = MATERIAL_DEFAULTS

    @classmethod
    def get_defaults(cls, abbreviation: str) -> Dict[str, float]:
        """按 abbreviation 查材料族默认值

        Returns:
            材料族默认参数字典；无匹配返回空 dict

        混合材料处理（PP+PA66 / PA66+GF30 等）：
            1. 优先全名匹配（如 PA66+GF30、PA66+PA6 等已预填）
            2. 全名未匹配 → 拆分 '+' 取第一个主材料兜底（如 PP+PA66 → PP）
            3. 主材料查不到 → 返回空 dict（让上游报缺失）
        """
        if not abbreviation:
            return {}
        abbr_upper = abbreviation.upper().strip()

        # 1. 优先全名匹配（处理预填的混合材料经验值）
        if abbr_upper in cls.DEFAULTS:
            return cls.DEFAULTS[abbr_upper]

        # 2. 拆 '+' 取第一个主材料兑底（业务上 80% 场景够用）
        if '+' in abbr_upper:
            main = abbr_upper.split('+', 1)[0].strip()
            if main and main in cls.DEFAULTS:
                return cls.DEFAULTS[main]

        # 3. 全查不到 → 返回空（让上游报缺失）
        return {}

    @classmethod
    def fill_defaults(cls, material_info: Dict[str, Any]) -> None:
        """智能填充：缺失字段按 abbreviation 查材料族

        Args:
            material_info: 材料信息 dict（会被直接修改，填充默认值）

        Note:
            只填充"业务上可能缺失"的物理参数（melt_density / recommended_melt_temp 等）
            已存在的字段不会被覆盖
        """
        abbreviation = material_info.get('abbreviation')
        if not abbreviation:
            return
        defaults = cls.get_defaults(abbreviation)
        for key, value in defaults.items():
            if not material_info.get(key):
                material_info[key] = value

    @classmethod
    def has_defaults(cls, abbreviation: str) -> bool:
        """检查材料族是否有默认参数（用于业务侧补充提示）"""
        return bool(cls.get_defaults(abbreviation))


__all__ = [
    "MaterialDatabase",
    "MATERIAL_DEFAULTS",
]
