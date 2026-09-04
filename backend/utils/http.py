from django.http import HttpRequest, QueryDict
import json
from extensions.exceptions import BizException, ERROR_ILLEGAL_ARGUMENT


def smart_type_convert(value: str):
    """
    智能类型转换，支持：
      - 'null', 'undefined', '' → None
      - 'true'/'false' → bool
      - 纯数字 → int/float
      - 其他保留字符串
    """
    if not isinstance(value, str):
        return value

    stripped = value.strip()

    # 处理前端传来的 "null"、"undefined"、空字符串等
    if stripped.lower() in ('null', 'undefined', '') or stripped == 'NaN':
        return None

    # 布尔值（注意：必须在数字之前判断，避免 'true' 被误判）
    if stripped.lower() in ('true', 'false'):
        return stripped.lower() == 'true'

    # 整数（支持负数）
    if stripped.isdigit() or (stripped.startswith('-') and stripped[1:].isdigit()):
        return int(stripped)

    # 浮点数
    try:
        # 避免 '123abc' 被转成 123.0
        if stripped.replace('.', '').replace('-', '').replace('e', '').replace('+', '').isdigit():
            return float(stripped)
    except (ValueError, AttributeError):
        pass

    # 默认返回原字符串
    return value

def querydict_to_dict(query_dict: QueryDict) -> dict:
    """
    将 Django QueryDict 转换为普通字典
    - 自动识别 xxx[] 后缀字段，去除 [] 后缀
    - 单值列表自动解包（除非字段名包含 'list', 'polymer_info_ids', 'testing_material'）
    - 多值字段保留为列表

    示例:
        QueryDict('name=Bob&tags[]=a&tags[]=b&ids[]=1') ->
        {'name': 'Bob', 'tags': ['a', 'b'], 'ids': ['1']}

    Args:
        query_dict (QueryDict): Django 的 QueryDict 对象

    Returns:
        dict: 转换后的字典
    """
    FLAT_EXCLUDE_KEYS = {'list', 'polymer_info_ids', 'testing_material'}
    return {
        k[:-2] if k.endswith("[]") else k
        :
        v[0] if len(v) == 1 and not any(key in k for key in FLAT_EXCLUDE_KEYS) else v
        for k, v in query_dict.lists()
    }


def querydict_to_dict_with_type_convert(query_dict: QueryDict) -> dict:
    """
    将 Django QueryDict 转换为普通字典
    - 自动识别 xxx[] 后缀字段，去除 [] 后缀
    - 单值列表自动解包（除非字段名包含 'list', 'polymer_info_ids', 'testing_material'）
    - 多值字段保留为列表

    示例:
        QueryDict('name=Bob&tags[]=a&tags[]=b&ids[]=1') ->
        {'name': 'Bob', 'tags': ['a', 'b'], 'ids': ['1']}

    Args:
        query_dict (QueryDict): Django 的 QueryDict 对象

    Returns:
        dict: 转换后的字典
    """
    FLAT_EXCLUDE_KEYS = {'list', 'polymer_info_ids', 'testing_material'}
    raw = {
        k[:-2] if k.endswith("[]") else k
        :
        v[0] if len(v) == 1 and not any(key in k for key in FLAT_EXCLUDE_KEYS) else v
        for k, v in query_dict.lists()
    }
    return {
        k: [smart_type_convert(x) for x in v] if isinstance(v, list) else smart_type_convert(v)
        for k, v in raw.items()
    }


def parse_get_params(request: HttpRequest) -> dict:
    """
    统一解析 GET 请求参数，支持两种格式：
      1. 标准查询参数: ?trial_session_id=6
      2. JSON 包装参数: ?p={"trial_session_id":6}
    
    优先使用 p 参数（如果存在且有效），否则使用普通参数。
    """
    if "p" in request.GET:
        try:
            return json.loads(request.GET["p"])
        except (ValueError, TypeError, json.JSONDecodeError):
            # 可选：记录警告，但 fallback 到普通参数（或直接报错）
            raise BizException(ERROR_ILLEGAL_ARGUMENT, "Invalid JSON in 'p' parameter")
    else:
        return querydict_to_dict(request.GET)


def get_client_ip(request: HttpRequest) -> str:
    """获取客户端 IP """
    # 优先从 X-Forwarded-For 获取
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    
    # 其次尝试从 X-Real-IP 获取（Nginx 常用）
    x_real_ip = request.META.get('HTTP_X_REAL_IP')
    if x_real_ip:
        return x_real_ip.strip()
    
    # 最后尝试从 REMOTE_ADDR 获取
    return request.META.get('REMOTE_ADDR', '').strip()
