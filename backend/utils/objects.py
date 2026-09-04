from typing import List, Dict, Any
    
def safe_get(obj: Any, attr_path: str, default: Any = "") -> Any:
    """
    安全获取嵌套属性或字典值，支持点号路径。
    自动识别对象属性（obj.attr）和字典键（dict['key']）。
    
    示例：
        safe_get(item, "reservation.trial_purpose.trial_aim_selections")
        # 若 reservation 是对象，trial_purpose 是 dict，则正确访问
    """
    try:
        for attr in attr_path.split("."):
            if obj is None:
                return default
            
            # 如果 obj 是字典类型，用键访问
            if isinstance(obj, dict):
                obj = obj.get(attr, default)
            else:
                # 否则当作对象，用属性访问
                obj = getattr(obj, attr)
        return obj
    except (AttributeError, KeyError, TypeError):
        return default

def join_labels(selections: List[Dict[str, Any]]) -> str:
    """将 selections 中 label 拼接为 '、' 分隔的字符串"""
    if not selections:
        return ""
    return "、".join(
        slct["label"] for slct in selections
        if slct.get("label") and slct.get("value")
    )

from datetime import datetime, date
from decimal import Decimal

def safe_json(obj):
    if obj is None:
        return None
    elif isinstance(obj, dict):
        return {k: safe_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [safe_json(x) for x in obj]
    elif isinstance(obj, datetime):
        return obj.strftime("%Y-%m-%d %H:%M:%S")
    elif isinstance(obj, date):
        return obj.strftime("%Y-%m-%d")
    elif isinstance(obj, Decimal):
        # 如果需要保留精确字符串（如财务），可用 str(obj)
        return str(obj)
    else:
        return obj