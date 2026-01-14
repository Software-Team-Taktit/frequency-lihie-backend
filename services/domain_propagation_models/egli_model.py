from services.base_propagation_model import BasePropagationModel
from services.models.types.egli_dto import EgliDTO
from services.utils.helpers import clamp_positive
import math

class EgliModel(BasePropagationModel):
    """
    Egli (common approximation)
    Used here for mountainous/rolling terrain MVP.
    """
    def calculate_path_loss(self, dto: EgliDTO) -> float:
        d = clamp_positive(dto.distance_km, 0.001)
        f = clamp_positive(dto.freq_mhz, 1.0)
        ht = clamp_positive(dto.tx_height_m, 1.0)
        hr = clamp_positive(dto.rx_height_m, 1.0)

        # Egli (dB) ≈ 117 + 40log10(d_km) + 20log10(f_MHz) - 20log10(ht*hr)
        return (117.0 +
                40.0 * math.log10(d) +
                20.0 * math.log10(f) -
                20.0 * math.log10(ht * hr))