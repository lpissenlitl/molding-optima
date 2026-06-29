from dataclasses import is_dataclass, asdict
import json
from decimal import Decimal
from datetime import datetime, date, time
from enum import Enum
from uuid import UUID


class JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(obj, date):
            return obj.strftime("%Y-%m-%d")
        elif isinstance(obj, time):
            return obj.strftime("%H:%M:%S")
        elif isinstance(obj, Decimal):
            return str(obj)
        elif isinstance(obj, Enum):
            return str(obj.value)
        elif isinstance(obj, UUID):
            return str(obj)
        elif is_dataclass(obj):
            return asdict(obj)
        else:
            return super().default(obj)