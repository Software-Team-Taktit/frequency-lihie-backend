from services.base_propagation_model import BasePropagationModel
from services.co_existing_service.utils.helpers import clamp_positive
import math

class EgliModel(BasePropagationModel):
    """
    Egli (common approximation)
    Used here for mountainous/rolling terrain MVP.
    """
    def calculate_path_loss(self, freq_mhz: float, distance_km: float,
                            tx_height_m: float, rx_height_m: float) -> float:
        d = clamp_positive(distance_km, 0.001)
        f = clamp_positive(freq_mhz, 1.0)
        ht = clamp_positive(tx_height_m, 1.0)
        hr = clamp_positive(rx_height_m, 1.0)

        # Egli (dB) ≈ 117 + 40log10(d_km) + 20log10(f_MHz) - 20log10(ht*hr)
        return (117.0 +
                40.0 * math.log10(d) +
                20.0 * math.log10(f) -
                20.0 * math.log10(ht * hr))