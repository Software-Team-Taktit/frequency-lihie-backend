from datetime import datetime, timedelta, timezone
from pydantic  import Field
from uuid import uuid4, UUID
from models.domain.base_object import BaseObject
from models.enums.object_type import ObjectType
from models.helpers.coordinate import Coordinate

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Mission(BaseObject):
    name: str = Field(..., min_length=2, max_length=80)
    coordinate: Coordinate
    freq_mhz: float
    tx_power_dbm: float
    platform_id: str
    
    is_active: bool = True
    created_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime | None = None
    
    def __init__(self, **data):
        data["id"] = data.get("id", str(uuid4()))
        data["type"] = ObjectType.MISSION
        
        if "created_at" not in data:
            data["created_at"] = utc_now()
            
        if data.get("time") and data.get("expires_at") is None:
            data["expires_at"] = data["created_at"] + timedelta(minutes=data["time"])
        
        super().__init__(**data)