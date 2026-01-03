import math
from dataclasses import dataclass
from typing import Iterator, List, Tuple

from models.domain.types.platform import Platform
from models.domain.types.mission import Mission
from models.requests.frequency_req_res import FrequencyRequest

from services.base_propagation_model import BasePropagationModel
from services.helpers import clamp_positive, dbm_to_mw, mw_to_dbm, noise_floor_dbm

# scan config
@dataclass(frozen=True)
class Band:
    start_mhz: float 
    end_mhz: float

@dataclass(frozen=True)
class CoarseFineScanConfig:
    bands: List[Band]
    coarse_step_mhz: float = 5.0
    fine_step_mhz: float = 0.5
    fine_window_mhz: float = 2.0
    top_k: int = 5
    
# frequency scanner