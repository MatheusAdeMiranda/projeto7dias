from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ServiceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    url: HttpUrl
    expected_status: int = Field(default=200, ge=100, le=599)
    timeout_seconds: int = Field(default=5, ge=1, le=30)
    active: bool = True


class ServiceRead(ServiceCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
