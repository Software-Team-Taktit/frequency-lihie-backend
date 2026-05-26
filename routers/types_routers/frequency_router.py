from fastapi import APIRouter, Depends

from models.requests.frequency_req_res import FrequencyRequest, FrequencyResponse
from repositories.types_repositories.platform_repository import PlatformRepository
from repositories.types_repositories.mission_repository import MissionRepository
from repositories.types_repositories.frequency_range_repository import FrequencyRangeRepository

from services.co_existing_service.propagation_factory import PropagationFactory
from services.co_existing_service.frequency_scanner import FrequencyScanner, CoarseFineScanConfig, Band
from services.co_existing_service.frequency_service import FrequencyService

freq_router = APIRouter(prefix="/frequency", tags=["frequency"])

prop_factory = PropagationFactory()
scanner = FrequencyScanner(prop_factory)

config = CoarseFineScanConfig(
    bands=[Band(0.0, 0.0)],  
    coarse_step_mhz=1.0,       
    fine_step_mhz=0.1,         
    fine_window_mhz=2.0,
    top_k=10,
    interference_window_mhz=2.5, 
    guard_mhz=2.0,
    path_loss_weight=1.0,
    interference_weight=10.0,
    link_distance_km=1.0
)

def get_frequency_service(
    platform_repo: PlatformRepository = Depends(PlatformRepository),
    mission_repo: MissionRepository = Depends(MissionRepository),
    freq_range_repo: FrequencyRangeRepository = Depends(FrequencyRangeRepository),
) -> FrequencyService:
    return FrequencyService(platform_repo, mission_repo, freq_range_repo, scanner, config)

@freq_router.post("/calculate", response_model=FrequencyResponse)
async def calculate_frequency(
    request: FrequencyRequest,
    service: FrequencyService = Depends(get_frequency_service),
) -> FrequencyResponse:
    return await service.calculate(request)
