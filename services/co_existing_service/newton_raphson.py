from dataclasses import dataclass
from typing import Callable, Optional

from services.utils.helpers import clamp_positive, dbm_to_mw, mw_to_dbm, noise_floor_dbm, sinr_db
from models.domain.types.platform import Platform

@dataclass
class NewtonConfig:
    tol_db: float = 0.1 # כמה קרוב ל-0 נחשב מספיק טוב
    max_iter: int = 20
    ptx_min_dbm: float = -30.0
    ptX_max_dbm: float = 50.0
    numeric_derivative_step_db: float = 0.1
    
class NewtonRphsonError(RuntimeError):
    pass

