from pydantic  import Field
from uuid import uuid4, UUID
from models.domain.base_object import BaseObject
from models.enums.object_type import ObjectType
from models.helpers.coordinate import Coordinate

class Mission(BaseObject):
    name: str = Field(..., min_length=2, max_length=80)
    coordinate: Coordinate
    enviroment_type: str
    platform_id: str
    
    def __init__(self, **data):
        data["id"] = data.get("id", str(uuid4()))
        data["type"] = ObjectType.MISSION
        super().__init__(**data)