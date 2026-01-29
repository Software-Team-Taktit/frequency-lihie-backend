from dataclasses import dataclass
from typing import Callable, Optional

from services.utils.helpers import clamp_positive, dbm_to_mw, mw_to_dbm, noise_floor_dbm, sinr_db
from models.domain.types.platform import Platform

@dataclass
class NewtonConfig:
    tol_db: float = 0.1 # כמה קרוב ל-0 נחשב מספיק טוב
    max_iter: int = 20
    ptx_min_dbm: float = -100.0
    ptx_max_dbm: float = 100.0
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
    sinr_required_db: float,
    config: Optional[NewtonConfig] = None,
    ptx0_dbm: Optional[float] = None
) -> float:
    cfg = config or NewtonConfig()
    
    p = float(ptx0_dbm) if ptx0_dbm is not None else initial_guess_tx_power_dbm(
        platform=platform,
        path_loss_db=path_loss_db,
        interference_mw=interference_mw,
        sinr_required_db=sinr_required_db,
    )
    
    p = _clamp(p, cfg.ptx_min_dbm, cfg.ptx_max_dbm)
    
    def f(ptx_dbm: float) -> float:
        sinr_val = sinr_db(
            p_tx_dbm=ptx_dbm,
            platform=platform,
            path_loss_db=path_loss_db,
            interference_mw=interference_mw
        )
        return float(sinr_val) - float(sinr_required_db)
        
    def fprime(ptx_dbm: float) -> float:
        return 1.0
    
    for i in range(cfg.max_iter):
        fx = f(p)
        print(f"iter {i}: p={p:.2f}, error(fx)={fx:.2f}") 

        if abs(fx) <= cfg.tol_db:
            return p

        dfx = fprime(p)
        
        next_p = p - (fx / dfx)
        
        if next_p > cfg.ptx_max_dbm:
            print(f"Warning: Optimal power {next_p:.2f} exceeds max {cfg.ptx_max_dbm}")
           
            raise NewtonRaphsonError(
                f"Cannot achieve required SINR. Required: {next_p:.2f} dBm, Max allowed: {cfg.ptx_max_dbm} dBm"
            )

        if next_p < cfg.ptx_min_dbm:
             return cfg.ptx_min_dbm

        p = next_p
        p = _clamp(p, cfg.ptx_min_dbm, cfg.ptx_max_dbm)

    raise NewtonRaphsonError(f"Newton-Raphson did not converge within {cfg.max_iter} iterations. Final Error: {fx}")