from pydantic import BaseModel, Field
from abc import ABC
from models.enums.object_type import ObjectType

class BaseObject(ABC, BaseModel):
    id: str
    type: ObjectType 