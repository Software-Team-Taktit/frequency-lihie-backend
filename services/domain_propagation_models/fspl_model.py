from services.base_propagation_model import BasePropagationModel
from services.co_existing_service.utils.helpers import clamp_positive
import math

class FSPLModel(BasePropagationModel):
    """
    Free Space Path Loss (FSPL)
    Suitable for open space with clear line-of-sight (MVP).
    """
    def calculate_path_loss(self, freq_mhz: float, distance_km: float, 
                            tx_height_m: float, rx_height_m: float) -> float:
        d = clamp_positive(distance_km, 0.001)
        f = clamp_positive(freq_mhz, 0.1)
        
        return 32.45 + 20 * math.log10(d) + 20 * math.log10(f)