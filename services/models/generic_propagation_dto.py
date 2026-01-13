from pydantic import BaseModel
from typing import Optional
from .enums.pathloss_models_enum import PropagationModelType

class GenericPropagationDTO(BaseModel):
    model_type: PropagationModelType
    freq_mhz: float
    distance_km: float
    tx_height_m: Optional[float] = None
    rx_height_m: Optional[float] = None