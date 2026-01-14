from services.base_propagation_model import BasePropagationModel
from services.models.types.fspl_dto import FsplDTO
from services.utils.helpers import clamp_positive
import math

class FSPLModel(BasePropagationModel):
    """
    Free Space Path Loss (FSPL)
    Suitable for open space with clear line-of-sight (MVP).
    """
    def calculate_path_loss(self, dto: FsplDTO) -> float:
        d = clamp_positive(dto.distance_km, 0.001)
        f = clamp_positive(dto.freq_mhz, 0.1)
        
        return 32.45 + 20 * math.log10(d) + 20 * math.log10(f)