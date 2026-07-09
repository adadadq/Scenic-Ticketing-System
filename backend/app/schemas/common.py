from typing import Generic, Literal, TypeVar

from pydantic import BaseModel


DataT = TypeVar("DataT")


class ApiSuccessDTO(BaseModel, Generic[DataT]):
    success: Literal[True]
    data: DataT
    request_id: str


class ApiFailureDTO(BaseModel):
    success: Literal[False]
    code: str
    message: str
    request_id: str
