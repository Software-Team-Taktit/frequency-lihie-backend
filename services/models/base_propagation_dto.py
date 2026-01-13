from pydantic import BaseModel
from .enums.pathloss_models_enum import PropagationModelType

class BasePropagationDTO(BaseModel):
    model_type: PropagationModelType
    freq_mhz: float
    distance_km: float