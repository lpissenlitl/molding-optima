import string
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

special_chars = set(string.punctuation)

def check_pwd_strength(pwd: str, min_len=6, max_len=15, strict=False) -> tuple[bool, str]:
    """
    验证密码强度。

    Args:
        pwd (str): 待验证的密码。
        min_len (int): 最小长度，默认 6。
        max_len (int): 最大长度，默认 15。
        strict (bool): 是否启用严格模式。
                       严格模式要求：数字、大写字母、小写字母、特殊字符至少各一个。

    Returns:
        tuple[bool, str]: (是否通过, 错误信息)。通过时错误信息为空字符串。
    """

    if not pwd:
        raise ValueError("密码不能为空")
    if min_len > max_len:
        raise ValueError("最小长度不能大于最大长度")
    if not isinstance(pwd, str):
        raise ValueError("密码必须是字符串")
    
    
    if len(pwd) < min_len:
        return False, f"密码长度不能小于{min_len}位"

    if len(pwd) > max_len:
        return False, f"密码长度不能大于{max_len}位"
    
    if not strict:
        return True, ""
    
    if not any(char.isdigit() for char in pwd):
        return False, "密码必需包含至少一位数字"
    
    if not any(char.isupper() for char in pwd):
        return False, "密码必需包含至少一位大写字母"
    
    if not any(char.islower() for char in pwd):
        return False, "密码必需包含至少一位小写字母"
    
    if not any(char in special_chars for char in pwd):
        return False, f"密码必需包含至少一位特殊字符：{''.join(sorted(special_chars))}"

    return True, ""
    

def hash_pwd(pwd: str) -> str:
    """
    对密码进行哈希处理。

    Args:
        pwd (str): 待处理的密码。

    Returns:
        str: 哈希后的密码。
    """
    
    if not pwd:
        raise ValueError("密码不能为空")
    if not isinstance(pwd, str):
        raise ValueError("密码必须是字符串")
    
    return pwd_context.hash(pwd)


def check_pwd(pwd: str, hashed_pwd: str) -> bool:
    """
    验证密码是否匹配。

    Args:
        pwd (str): 待验证的密码。
        hashed_pwd (str): 已哈希的密码。

    Returns:
        bool: 密码是否匹配。
    """
    
    if not pwd:
        raise ValueError("密码不能为空")
    if not hashed_pwd:
        raise ValueError("已哈希的密码不能为空")
    if not isinstance(pwd, str):
        raise ValueError("密码必须是字符串")
    if not isinstance(hashed_pwd, str):
        raise ValueError("已哈希的密码必须是字符串")
    
    return pwd_context.verify(pwd, hashed_pwd)
    
