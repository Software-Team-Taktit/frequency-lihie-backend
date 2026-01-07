from models.requests.frequency_req_res import FrequencyRequest, FrequencyResponse
from repositories.types_repositories.platform_repository import PlatformRepository
from repositories.types_repositories.mission_repository import MissionRepository
from services.co_existing_service.propagation_factory import PropagationFactory
from services.co_existing_service.frequency_scanner import FrequencyScanner, CoarseFineScanConfig, Band

class FrequencyService:
    def __init__(
        self,
        platform_repo: PlatformRepository,
        mission_repo: MissionRepository,
        scanner: FrequencyScanner,
        config: CoarseFineScanConfig,
    ):
        self.platform_repo = platform_repo
        self.mission_repo = mission_repo
        self.scanner = scanner
        self.config = config
        
    async def calculate(self, request: FrequencyRequest) -> FrequencyResponse:
        platform = await self.platform_repo.get_by_id(request.platform_id)
        missions = await self.mission_repo.get_all()

        best_freq = self.scanner.coarse_then_fine_best_freq(
            request=request,
            platform=platform,
            missions=missions,
            config=self.config,
        )

        return FrequencyResponse(freq_mhz=best_freq, tx_power_dbm=30.0) 