from pydantic import BaseModel

class BasePropagationDTO(BaseModel):
    freq_mhz: float
    distance_km: float