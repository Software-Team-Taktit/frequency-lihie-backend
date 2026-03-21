from uuid import UUID
from pydantic import BaseModel, Field
from models.helpers.coordinate import Coordinate

class MissionCreateRequest(BaseModel):
    """
    Request to create a mission AFTER frequency & tx power
    were already calculated by the Co-existing Service.
    """
    name: str = Field(..., min_length=2, max_length=80)
    time: int = Field(..., gt=0)
    coordinate: Coordinate
    freq_mhz: float
    tx_power_dbm: float
    platform_id: str
    
class MissionUpdateRequest(BaseModel):
    """
    Partial update of an existing mission.
    All fields are optional.
    """
    name: str | None = Field(None, min_length=2, max_length=80)
    time: int | None = Field(None, gt=0)
    coordinate: Coordinate | None = None
    freq_mhz: float | None = None
    tx_power_dbm: float | None = None
    platform_id: str | None = None