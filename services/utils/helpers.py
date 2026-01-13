import math
from models.domain.types.platform import Platform
from models.helpers.coordinate import Coordinate
from services.models.generic_propagation_dto import GenericPropagationDTO
from services.utils.constants import MODEL_ALLOWED_FIELDS, MODEL_REQUIRED_FIELDS

def clamp_positive(x: float, min_value: float) -> float:
    """Ensures x is at least min_val (prevents log10(0)) and negative values"""
    return x if x >= min_value else min_value

def haversine_km(c1: Coordinate, c2: Coordinate) -> float:
    """Distance between 2 lat/lon points in KM"""
    R = 6371.0 # Earth radius in km
    
    lat1 = math.radians(c1.latitude)
    lon1 = math.radians(c1.longitude)
    lat2 = math.radians(c2.latitude)
    lon2 = math.radians(c2.longitude)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)

    return 2 * R * math.asin(math.sqrt(a))
    
def dbm_to_mw(dbm: float) -> float:
    return 10 ** (dbm / 10.0)

def mw_to_dbm(mw: float) -> float:
    mw = clamp_positive(mw, 1e-12)
    return 10.0 * math.log10(mw)

def noise_floor_dbm(platform: Platform) -> float:
    # -174 dBm/Hz + 10log10(BW_Hz) + NF
    bw_hz = clamp_positive(platform.bw_khz * 1000.0, 1.0)
    return -174.0 + 10.0 * math.log10(bw_hz) + platform.noise_figure_db

def all_fields(dto: GenericPropagationDTO) -> dict:
    data = dto.model_dump(exclude_none=True)
    
    required = MODEL_REQUIRED_FIELDS[dto.model_type]
    allowed = MODEL_ALLOWED_FIELDS[dto.model_type]
    
    missing = [k for k in required if k not in data]
    if missing:
        raise ValueError(f"Missing required fields for {dto.model_type}: {missing}")
    
    return {k: v for k, v in data.items() if k in allowed}