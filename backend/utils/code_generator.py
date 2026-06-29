# utils/code_generator.py
"""
通用唯一码生成模块
用于生成基于时间的、带前缀的唯一识别码。
"""

import random
from datetime import datetime

def generate_unique_code(
    prefix: str = 'ID',
    timestamp_length: int = 12,
    random_length: int = 4,
    exclude_chars: str = '0O1I',
    custom_chars: str = None
) -> str:
    """
    生成唯一码。
    
    格式: [PREFIX]-[时间部分]-[随机部分]
    示例: RES-2511031705-AB3X, ORD-20251103-KL9R
    
    Args:
        prefix (str): 前缀，用于标识业务类型，默认 'ID'。
        timestamp_length (int): 时间戳部分的长度。
            - 6: YYMMDD
            - 8: YYMMDDHH
            - 10: YYMMDDHHmm
            - 12: YYMMDDHHmmss (默认)
        random_length (int): 随机码的长度，默认 4。
        exclude_chars (str): 要排除的易混淆字符，默认 '0O1I'。
        custom_chars (str): 自定义字符集，如果提供，将覆盖 exclude_chars 的设置。
    
    Returns:
        str: 生成的唯一码。
    """
    now = datetime.now()
    
    # 生成时间部分
    if timestamp_length == 6:
        timestamp_part = now.strftime('%y%m%d')  # YYMMDD
    elif timestamp_length == 8:
        timestamp_part = now.strftime('%y%m%d%H')  # YYMMDDHH
    elif timestamp_length == 10:
        timestamp_part = now.strftime('%y%m%d%H%M')  # YYMMDDHHmm
    else:  # 默认 12
        timestamp_part = now.strftime('%y%m%d%H%M%S')  # YYMMDDHHmmss
    
    # 生成字符集
    base_chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    if custom_chars:
        chars = custom_chars
    else:
        chars = ''.join(c for c in base_chars if c not in exclude_chars)
    
    # 生成随机部分
    random_part = ''.join(random.choices(chars, k=random_length))
    
    # 组合返回
    return f"{prefix}-{timestamp_part}-{random_part}"

# --- 使用示例 ---
if __name__ == "__main__":
    # 1. 默认调用
    print(generate_unique_code()) 
    # 示例输出: ID-251103170512-AB3X

    # 2. 预约 (Reservation)
    print(generate_unique_code(prefix='RES')) 
    # 示例输出: RES-251103170512-MN2P

    # 3. 订单 (Order)，时间精确到天
    print(generate_unique_code(prefix='ORD', timestamp_length=8)) 
    # 示例输出: ORD-25110317-KL9R

    # 4. 用户邀请码，6位随机码
    print(generate_unique_code(prefix='USR', random_length=6, timestamp_length=6)) 
    # 示例输出: USR-251103-AB3XMN

    # 5. 自定义字符集（例如只用字母）
    print(generate_unique_code(prefix='SPECIAL', custom_chars='ABCDEF'))
    # 示例输出: SPECIAL-251103170512-ABCD