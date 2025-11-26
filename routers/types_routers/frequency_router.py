from fastapi import APIRouter
from models.requests.frequency_req_res import FrequencyRequest, FrequencyResponse

freq_router = APIRouter(
    prefix="/frequency",
    tags=["frequency"]
)

@freq_router.post("/calculate", response_model=FrequencyResponse)
async def calculate_frequency(request: FrequencyRequest) -> FrequencyResponse:
    """
    Temporary stub endpoint:
    Gets a FrequencyRequest and returns default / dummy values
    until the real algorithm is implemented.
    """
    dummy_freq_mhz = 900.0
    dummy_tx_power_dbm = 30.0
    
    return FrequencyResponse(
        freq_mhz=dummy_freq_mhz,
        tx_power_dbm=dummy_tx_power_dbm
    )