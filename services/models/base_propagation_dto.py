from pydantic import BaseModel
from pydantic import PositiveFloat

class BasePropagationDTO(BaseModel):
    freq_mhz: PositiveFloat
    distance_km: PositiveFloat