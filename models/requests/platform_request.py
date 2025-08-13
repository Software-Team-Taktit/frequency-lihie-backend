from pydantic import BaseModel

class PlatformCreateRequest(BaseModel):
    name: str
    frequency_mhz: float
    bw_khz: float
    tx_power_dbm: float
    antenna_height_m: float