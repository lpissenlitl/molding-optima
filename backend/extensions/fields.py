# extensions/fields.py
from mongoengine import FloatField

class SafeFloatField(FloatField):
    def to_python(self, value):
        # 显式处理 None，不调用 float(None)
        if value is None:
            return None
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            s = value.strip().lower()
            if s in ("", "none", "null", "nan"):
                return None
            try:
                return float(s)
            except (ValueError, TypeError):
                return None
        return None

    def validate(self, value):
        # validate 只做业务校验，不重复 to_python 的工作
        if value is not None and not isinstance(value, (int, float)):
            self.error("Value must be a number or null.")