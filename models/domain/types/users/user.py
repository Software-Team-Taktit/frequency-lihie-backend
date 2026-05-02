from models.domain.base_object import BaseObject
from models.enums.object_type import ObjectType

class User(BaseObject):
    personal_id: str
    first_name: str
    last_name: str
    unit: str
    
    def __init__(self, **data):
        data.setdefault("id", data["personal_id"])
        data.setdefault("type", ObjectType.USER)
        super().__init__(**data)