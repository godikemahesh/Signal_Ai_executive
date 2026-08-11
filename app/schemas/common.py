"""
Signal — Common Pydantic Schemas
Pagination, generic API responses, status schemas.
"""

from typing import Generic, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Success"
    data: Optional[T] = None


class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 20


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
