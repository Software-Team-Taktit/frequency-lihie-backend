from pydantic import BaseModel

class PlatformCreateRequest(BaseModel):
    """
    Request to create a new RF platform profile.
    If some fields are omitted, backend defaults will be used.
    """
    name: str
    bw_khz: float | None = 20.0
    tx_gain: float
    tx_height_m: float | None = 30.0
    rx_gain: float
    rx_height_m: float | None = 1.5
    min_sinr_required_db: float | None = 12.0
    noise_figure_db: float | None = 3.0
    
class PlatformUpdateRequest(BaseModel):
    """
    Partial update of an existing platform.
    All fields are optional.
    """
    name: str | None = None
    bw_khz: float | None = None
    tx_gain: float | None = None
    tx_height_m: float | None = None
    rx_gain: float | None = None
    rx_height_m: float | None = None
    min_sinr_required_db: float | None = None
    noise_figure_db: float | None = None