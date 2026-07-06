"""全局通用变量"""


# --- 数据库字段长度标准 ---
MAX_CODE_LENGTH = 50
MAX_NAME_LENGTH = 50
MAX_STATUS_LENGTH = 20


# --- 流道类型枚举（跨算法复用）---
# 背景：算法 #6 保压压力 / #8 保压时间 / 冷却 / 松退等多个算法依赖流道类别。
# 热转冷是混合系统（热流道 + 冷流道），需要独立识别。
RUNNER_TYPE_HOT = '热流道'              # runner_type 始终熔融，无流道冷却
RUNNER_TYPE_COLD = '冷流道'             # runner_type 随制品冷却，需流道补缩
RUNNER_TYPE_HOT_TO_COLD = '热转冷'      # 部分热部分冷，介于两者之间

RUNNER_TYPES = (RUNNER_TYPE_HOT, RUNNER_TYPE_COLD, RUNNER_TYPE_HOT_TO_COLD)