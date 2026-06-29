"""
password tool
"""
import bcrypt


def check_pwd_strength(pwd, min_len=6, max_len=15) -> (bool, str):
    """
    验证密码安全强度
    :return: True 表示通过安全强度验证, 如果验证失败，可返回失败原因
    """
    assert pwd
    assert min_len <= max_len

    # special_chars = ["$", "@", "#", "%"]

    if len(pwd) < min_len:
        return False, f"密码长度不能小于{min_len}"

    if len(pwd) > max_len:
        return False, f"密码长度不能大于{max_len}"

    # if not any(char.isdigit() for char in pwd):
    #     return False, "密码必需包含至少一位数字"
    #
    # if not any(char.isupper() for char in pwd):
    #     return False, "密码必需包含至少一位大写字母"
    #
    # if not any(char.islower() for char in pwd):
    #     return False, "密码必需包含至少一位小写字母"
    #
    # if not any(char in special_chars for char in pwd):
    #     return False, f"密码必需包含至少一位特殊字符：{special_chars}"

    return True, None


def hash_pwd(pwd: str) -> str:
    return bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()


def check_pwd(pwd: str, hashed_pwd) -> str:
    return bcrypt.checkpw(pwd.encode(), hashed_pwd.encode())
