from uuid import UUID
from pydantic import BaseModel, Field
from models.helpers.coordinate import Coordinate
from models.enums.enviroment_type import EnviromentType

class MissionCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)
    coordinate: Coordinate
    enviroment_type: EnviromentType
    platform_id: str
    
class MissionUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=80)
    coordinate: Coordinate
    enviroment_type: EnviromentType
    platform_id: str