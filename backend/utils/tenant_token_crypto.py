"""租户 Token 加密/解密工具
使用 XOR + Base64 编码生成短 token
"""

import base64
import hashlib
import hmac
import json
import time
from django.conf import settings


class TenantTokenCrypto:
    """租户 Token 加密/解密工具"""

    CHECKSUM_LEN = 16  # 校验和字节数

    @staticmethod
    def _get_key_bytes() -> bytes:
        """获取密钥字节"""
        secret = getattr(settings, 'TENANT_TOKEN_SECRET', None) or settings.SECRET_KEY
        return secret.encode()

    @staticmethod
    def _xor(data: bytes, key: bytes) -> bytes:
        """XOR 异或运算"""
        key_len = len(key)
        return bytes(b ^ key[i % key_len] for i, b in enumerate(data))

    @staticmethod
    def _checksum(data: bytes) -> bytes:
        """HMAC-SHA256 校验和"""
        return hmac.new(TenantTokenCrypto._get_key_bytes(), data, hashlib.sha256).digest()[:TenantTokenCrypto.CHECKSUM_LEN]

    @staticmethod
    def encrypt(tenant_slug: str, expiry_seconds: int = None) -> str:
        """
        加密 tenant_slug 为 token

        Token 格式: Base64 编码字符串
        示例: H0gSTF1Nal8sIlUsMSUDSjJTJXkcMUsj3UokD8ZaD
        """
        payload = {'s': tenant_slug}
        if expiry_seconds is not None:
            payload['e'] = int(time.time()) + expiry_seconds

        data = json.dumps(payload, separators=(',', ':')).encode()
        key = TenantTokenCrypto._get_key_bytes()
        encrypted = TenantTokenCrypto._xor(data, key)
        sig = TenantTokenCrypto._checksum(encrypted)
        return base64.urlsafe_b64encode(encrypted + sig).decode().rstrip('=')

    @staticmethod
    def decrypt(token: str) -> dict:
        """
        解密 token 获取 payload

        Raises:
            ValueError: token 无效、已过期或格式错误
        """
        try:
            # 补回被截断的填充符
            padding = 4 - len(token) % 4
            if padding != 4:
                token += '=' * padding
            raw = base64.urlsafe_b64decode(token)
            if len(raw) <= TenantTokenCrypto.CHECKSUM_LEN:
                raise ValueError("Invalid token format")

            encrypted = raw[:-TenantTokenCrypto.CHECKSUM_LEN]
            sig = raw[-TenantTokenCrypto.CHECKSUM_LEN:]

            # 验证校验和
            if sig != TenantTokenCrypto._checksum(encrypted):
                raise ValueError("Invalid token signature")

            key = TenantTokenCrypto._get_key_bytes()
            data = TenantTokenCrypto._xor(encrypted, key)
            payload = json.loads(data.decode())

            # 验证过期时间
            if 'e' in payload and time.time() > payload['e']:
                raise ValueError("Token has expired")

            return {
                'tenant_slug': payload['s'],
                **({} if 'e' not in payload else {'exp': payload['e']}),
            }

        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Invalid token: {str(e)}")

    @staticmethod
    def decrypt_tenant_slug(token: str) -> str:
        """解密 token 直接获取 tenant_slug"""
        return TenantTokenCrypto.decrypt(token)['tenant_slug']


# ==================== 命令行工具 ====================

if __name__ == '__main__':
    """
    独立运行测试和演示
    可以直接调用此脚本进行加密/解密测试
    """
    import sys
    import os
    import django

    # 确保项目根目录在 sys.path 中
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # 初始化 Django 环境
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', '_moldx.settings')
    django.setup()
    
    def print_usage():
        print("用法:")
        print("  python tenant_token_crypto.py encrypt <tenant_slug> [expiry_seconds]")
        print("  python tenant_token_crypto.py decrypt <token>")
        print("\n示例:")
        print("  python tenant_token_crypto.py encrypt company-abc")
        print("  python tenant_token_crypto.py encrypt company-abc 31536000")
        print("  python tenant_token_crypto.py decrypt H0gSTF1Nal8sIlUsMSUDSjJTJXkcMUsj3UokD8ZaD")
    
    if len(sys.argv) < 3:
        print_usage()
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'encrypt':
        tenant_slug = sys.argv[2]
        expiry_seconds = int(sys.argv[3]) if len(sys.argv) > 3 else None
        
        token = TenantTokenCrypto.encrypt(tenant_slug, expiry_seconds)
        print(f"Tenant Slug: {tenant_slug}")
        print(f"Upload Token: {token}")
        if expiry_seconds:
            print(f"Expires In: {expiry_seconds} seconds")
        print(f"\n使用方法:")
        print(f"  Header: X-Tenant-Token: {token}")
        
    elif command == 'decrypt':
        token = sys.argv[2]
        
        try:
            payload = TenantTokenCrypto.decrypt(token)
            print(f"Token: {token}")
            print(f"Decoded Payload: {payload}")
            print(f"Tenant Slug: {payload['tenant_slug']}")
            if 'exp' in payload:
                exp_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(payload['exp']))
                print(f"Expires At: {exp_time}")
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)
    
    else:
        print(f"未知命令: {command}")
        print_usage()
        sys.exit(1)
