def ok(data):
    return {"code": 200, "message": "success", "data": data}

from typing import Generic, TypeVar, List
from pydantic import BaseModel
from pydantic.generics import GenericModel

T = TypeVar("T")

class ResponseOk(GenericModel, Generic[T]):
    code: int = 200
    message: str = "success"
    data: T

    model_config = {"from_attributes": True}  # V2 ORM 模式
