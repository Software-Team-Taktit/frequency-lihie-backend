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

def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

def initial_guess_tx_power_dbm(
    platform: Platform,
    path_loss_db: float,
    interference_mw: float,
    sinr_required_db: float
) -> float:
    noise_mw = dbm_to_mw(noise_floor_dbm(platform))
    denom_mw = clamp_positive(float(interference_mw) + float(noise_mw), 1e-12)
    denom_dbm = mw_to_dbm(denom_mw)
    
    return float(sinr_required_db) + float(denom_dbm) - float(platform.tx_gain) - float(platform.rx_gain) + float(path_loss_db)