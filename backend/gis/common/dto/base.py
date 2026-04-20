import typing
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class IdentityDTO:
    """
    包含`id`字段
    """

    id: int = None
    created_at: datetime = None
    updated_at: datetime = None

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        return type(other) == type(self) and other.id == self.id


@dataclass
class PaginationCriteriaDTO:
    """
    分页查询器
    """

    page_no: int = 1
    page_size: int = 30


class ExportCriteriaDTO(PaginationCriteriaDTO):
    export: bool = False


T = typing.TypeVar("T")


@dataclass
class PaginationResultDTO(typing.Generic[T]):
    """
    分页返回结果
    """

    total: int = 0
    data: typing.List[T] = field(default_factory=list)
