from uuid import UUID
from pydantic import BaseModel, Field
from models.helpers.coordinate import Coordinate

class MissionCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)
    coordinate: Coordinate
    enviroment_type: str
    platform_id: str
    
class MissionUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=80)
    coordinate: Coordinate
    enviroment_type: str
    platform_id: str