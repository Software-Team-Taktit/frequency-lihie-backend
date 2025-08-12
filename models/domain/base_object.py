from pydantic import BaseModel, Field
from abc import ABC
from uuid import uuid4, UUID
from models.enums.object_type import ObjectType

class BaseObject(ABC, BaseModel):
    id: UUID
    type: ObjectType 