from typing import Literal

from pydantic import BaseModel


class HealthDTO(BaseModel):
    status: Literal["ok"]
    service: str
    environment: str


class DatabaseHealthDTO(HealthDTO):
    database: Literal["ok"]
