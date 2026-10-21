"""管理命令控制台编码兼容

Windows 控制台默认编码是 GBK(cp936)，命令输出里一旦出现非 GBK 字符
（如 ✓ / emoji / 特殊符号）就会直接抛 UnicodeEncodeError 中断整个命令。

这里保留当前编码，只把 errors 策略改成 replace：
- 中文等本编码可表示的字符照常输出（显示不变）
- 生僻字符用 '?' 兜底，而不是让整个导入脚本半途失败
"""
import sys


def configure_console_encoding():
    """让 stdout / stderr 遇到不可编码字符时不再抛异常（幂等）"""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, 'reconfigure', None)
        if reconfigure is None:
            # 已被重定向为不支持 reconfigure 的流，忽略
            continue
        try:
            # 不传 encoding：沿用当前编码（GBK / UTF-8 均可）
            reconfigure(errors='replace')
        except (ValueError, OSError):
            # 流已关闭等情况，忽略
            pass
