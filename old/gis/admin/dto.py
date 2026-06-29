from dataclasses import dataclass
from datetime import datetime

from gis.common.dto.base import PaginationCriteriaDTO, ExportCriteriaDTO


@dataclass
class UserListCriteria(PaginationCriteriaDTO):
    name: str = None
    enable: bool = None
    role_id: int = None
    engineer: str = None
    email: str = None
    phone: str = None
    department_id: int = None
    department_name: str = None
    group_id: int = None
    group_name: str = None
    company_id: int = None
    company_name: str = None
    order_by: str = "-id"


@dataclass
class RoleListCriteria(PaginationCriteriaDTO):
    name: str = None
    company_name: str = None
    company_id: int = None
    deleted: int = None


@dataclass
class RecordListCriteria(ExportCriteriaDTO):
    resources: list = None
    operator: int = None
    action: int = None
    ip: str = None
    created_at_begin: datetime = None
    created_at_end: datetime = None
