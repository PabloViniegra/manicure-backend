from pydantic import BaseModel
from typing import Optional, List, TypeVar, Generic
from pydantic.generics import GenericModel

T = TypeVar('T')


class PaginationInfo(BaseModel):
    page: int
    per_page: int
    total: int
    total_pages: int


class PaginationResponse(GenericModel, Generic[T]):
    info: PaginationInfo
    data: List[T]
