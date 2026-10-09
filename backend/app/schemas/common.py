"""
common.py — shared Pydantic response envelopes and error models.
Every route handler returns ApiResponse or raises an HTTPException.
"""

from typing import Generic, TypeVar
from pydantic import BaseModel

DataT = TypeVar("DataT")


class Meta(BaseModel):
    count: int = 0
    page: int = 1
    page_size: int = 20


class ApiResponse(BaseModel, Generic[DataT]):
    """Standard success envelope used by all list and detail endpoints."""
    data: DataT
    meta: Meta = Meta()


class ErrorResponse(BaseModel):
    """Standard error body returned with 4xx / 5xx responses."""
    error: str
    code: str = "INTERNAL_ERROR"


class DataStatus(BaseModel):
    """
    Attached to every response so consumers know the data origin.
    data_source values: 'demo' | 'live'
    """
    data_source: str = "demo"
    note: str = "DEMO DATA — not real hospital information"

    @classmethod
    def from_source(cls, source: str) -> "DataStatus":
        """
        Factory that sets the note text based on data_source.
        Use this everywhere instead of constructing DataStatus() directly.
        """
        if source == "live":
            return cls(data_source="live", note="Live data")
        return cls(data_source="demo", note="DEMO DATA — not real hospital information")
