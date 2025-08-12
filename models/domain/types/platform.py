from uuid import uuid4
from models.domain.base_object import BaseObject
from models.enums.object_type import ObjectType

class Platform(BaseObject):
    name: str
    frequency_mhz: float
    bw_khz: float
    tx_power_dbm: float
    antenna_height_m: float
    
    def __init__(self, **data):
        data["id"] = data.get("id", uuid4())
        data["type"] = ObjectType.PLATFORM
        super().__init__(**data)