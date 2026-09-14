"""Department schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DepartmentCreate(BaseModel):
    """Create a hospital department."""

    name: str = Field(min_length=2, max_length=200)
    description: str | None = None
    is_active: bool = True
    extra: dict[str, Any] | None = None


class DepartmentUpdate(BaseModel):
    """Department update."""

    name: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = None
    is_active: bool | None = None
    extra: dict[str, Any] | None = None


class DepartmentRead(BaseModel):
    """Department response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    is_active: bool = True
    extra: dict[str, Any] | None = None
    created_at: datetime | None = None
