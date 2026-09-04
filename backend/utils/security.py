import string
import random


def generate_random_password(
    length: int = 13,
    min_digits: int = 1,
    min_upper: int = 1,
    min_lower: int = 1,
    min_special: int = 1,
    special_chars: str = "!@#$%^&*"
) -> str:
    """
    生成随机密码
    :param length: 密码长度
    :param min_digits: 最少位数
    :param min_upper: 最少大写字母
    :param min_lower: 最少小写字母
    :param min_special: 最少特殊字符
    :param special_chars: 特殊字符
    :return: 随机密码
    """
    if length < min_digits + min_upper + min_lower + min_special:
        raise ValueError("密码长度不足，无法满足最小字符要求")
    
    # 确保至少包含要求的字符
    password = []
    password += random.choices(string.digits, k=min_digits)
    password += random.choices(string.ascii_uppercase, k=min_upper)
    password += random.choices(string.ascii_lowercase, k=min_lower)
    password += random.choices(special_chars, k=min_special)
    
    # 填充剩余字符
    all_chars = string.digits + string.ascii_uppercase + string.ascii_lowercase + special_chars
    password += random.choices(all_chars, k=length - len(password))
    
    # 随机打乱字符顺序
    random.shuffle(password)
    return "".join(password)

