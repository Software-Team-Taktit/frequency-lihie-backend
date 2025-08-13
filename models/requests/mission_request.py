from uuid import UUID
from pydantic import BaseModel
from models.helpers.coordinate import Coordinate

class MissionCreateRequest(BaseModel):
    coordinate: Coordinate
    enviroment_type: str
    platform_id: UUID