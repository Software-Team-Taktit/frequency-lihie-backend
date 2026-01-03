from services.base_propagation_model import BasePropagationModel
from services.helpers import clamp_positive
import math

class HataModel(BasePropagationModel):
    """
    Okumura-Hata Urban (small/medium city)
    """
    def calculate_path_loss(self, freq_mhz: float, distance_km: float, 
                            tx_height_m: float, rx_height_m: float) -> float:
        d = clamp_positive(distance_km, 0.001)
        f = clamp_positive(freq_mhz, 1.0)
        hb = clamp_positive(tx_height_m, 1.0)
        hm = clamp_positive(rx_height_m, 1.0)
        
        if f <= 200:
            a_hm = 8.29 * (math.log10(1.54 * hm) ** 2) - 1.1
        else:
            a_hm = 3.2 * (math.log10(11.75 * hm) ** 2) - 4.97
        
        pl = (69.55 + 
              26.16 * math.log10(f) - 
              13.82 * math.log10(hb) -
              a_hm +
              (44.9 - 6.55 * math.log10(hb)) * math.log10(d))
        
        return pl