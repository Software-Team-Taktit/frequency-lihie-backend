from abc import ABC
from typing import Optional

class GenericPropagationDTO(ABC):
    freq_mhz: float
    distance_km: float
    tx_height_m: Optional[float] = None
    rx_height_m: Optional[float] = None