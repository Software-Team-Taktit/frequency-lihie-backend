from dataclasses import dataclass
from typing import Callable, Optional

from services.utils.helpers import clamp_positive, dbm_to_mw, mw_to_dbm, noise_floor_dbm, sinr_db
from models.domain.types.platform import Platform

@dataclass
class NewtonConfig:
    tol_db: float = 0.1 # כמה קרוב ל-0 נחשב מספיק טוב
    max_iter: int = 20
    ptx_min_dbm: float = -30.0
    ptx_max_dbm: float = 50.0
    numeric_derivative_step_db: float = 0.1
    
class NewtonRaphsonError(RuntimeError):
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

def solve_tx_power_newton_raphson(
    platform: Platform,
    path_loss_db: float,
    interference_mw: float,
    sinr_requird_db: float,
    config: Optional[NewtonConfig] = None,
    ptx0_dbm: Optional[float] = None
) -> float:
    cfg = config or NewtonConfig()
    
    p = float(ptx0_dbm) if ptx0_dbm is not None else initial_guess_tx_power_dbm(
        platform=platform,
        path_loss_db=path_loss_db,
        interference_mw=interference_mw,
        sinr_required_db=sinr_requird_db,
    )
    p = _clamp(p, cfg.ptx_min_dbm, cfg.ptx_max_dbm)
    
    def f(ptx_dbm: float) -> float:
        return sinr_db(
            p_tx_dbm=ptx_dbm,
            platform=platform,
            path_loss_db=path_loss_db,
            interference_mw=interference_mw
        ) - float(sinr_requird_db)
        
    def fprime(ptx_dbm: float) -> float:
        return 1.0
    
    for _ in range(cfg.max_iter):
        fx = f(p)
        if abs(fx) <= cfg.tol_db:
            return p
        
        dfx = fprime(p)
        
        if abs(dfx) < 1e-6:
            h = cfg.numeric_derivative_step_db
            dfx = (f(p+h) - f(p-h)) / (2.0*h)
            
            if abs(dfx) <= 1e-6:
                raise NewtonRaphsonError("Newton derivative too small; cannot converge safely.")
            
            p = p - (fx / dfx)
            p = _clamp(p, cfg.ptx_min_dbm, cfg.ptx_max_dbm)
            
    raise NewtonRaphsonError(f"Newton-Raphson did not converge within {cfg.max_iter} iterations.")