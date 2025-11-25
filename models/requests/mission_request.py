from uuid import UUID
from pydantic import BaseModel, Field
from models.helpers.coordinate import Coordinate
from models.enums.enviroment_type import EnviromentType

class FrequencyRequest(BaseModel):
    """
    Request sent from the Hamal client in order to calculate
    an optimal frequency and transmit power for a new mission.
    """
    name: str = Field(..., min_length=2, max_length=80)
    coordinate: Coordinate
    enviroment_type: EnviromentType
    platform_id: str

class MissionCreateRequest(BaseModel):
    """
    Request to create a mission AFTER frequency & tx power
    were already calculated by the Co-existing Service.
    """
    name: str = Field(..., min_length=2, max_length=80)
    coordinate: Coordinate
    freq_mhz: float
    tx_power_dbm: float
    platform_id: str
    
class MissionUpdateRequest(BaseModel):
    """
    Partial update of an existing mission.
    All fields are optional.
    """
    name: str = Field(..., min_length=2, max_length=80)
    coordinate: Coordinate
    freq_mhz: float
    tx_power_dbm: float
    platform_id: str