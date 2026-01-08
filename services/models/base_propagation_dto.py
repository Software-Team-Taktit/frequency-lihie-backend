from abc import ABC

class BasePropagationDTO(ABC):
    freq_mhz: float
    distance_km: float