import secrets
import string


def generate_tenant_slug(length: int = 16) -> str:
    """
    生成仅含字母和数字的租户唯一标识（无 - _ 等符号）
    
    Args:
        length: 生成字符串长度，默认 16（约 95 bits 熵，足够唯一）
    
    Returns:
        如 'xK9m2QzLpR7vNwEa'（但保证不含 - _）
    """
    alphabet = string.ascii_letters + string.digits  # a-z A-Z 0-9
    return ''.join(secrets.choice(alphabet) for _ in range(length))
