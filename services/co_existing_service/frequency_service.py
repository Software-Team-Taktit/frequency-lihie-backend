from fastapi import HTTPException, status

from models.requests.frequency_req_res import FrequencyRequest, FrequencyResponse
from repositories.types_repositories.platform_repository import PlatformRepository
from repositories.types_repositories.mission_repository import MissionRepository
from repositories.types_repositories.frequency_range_repository import FrequencyRangeRepository

from services.co_existing_service.frequency_scanner import FrequencyScanner, CoarseFineScanConfig, Band


class FrequencyService:
    def __init__(
        self,
        platform_repo: PlatformRepository,
        mission_repo: MissionRepository,
        freq_range_repo: FrequencyRangeRepository,
        scanner: FrequencyScanner,
        config: CoarseFineScanConfig,
    ):
        self.platform_repo = platform_repo
        self.mission_repo = mission_repo
        self.freq_range_repo = freq_range_repo
        self.scanner = scanner
        self.config = config

    async def calculate(self, request: FrequencyRequest) -> FrequencyResponse:
        platform = await self.platform_repo.get_by_id(request.platform_id)
        missions = await self.mission_repo.get_all()

        approved = await self.freq_range_repo.get()
        min_mhz = float(approved.min_mhz)
        max_mhz = float(approved.max_mhz)

        runtime_config = CoarseFineScanConfig(
            bands=[Band(min_mhz, max_mhz)],
            # safety: coarse step must not be larger than fine window
            coarse_step_mhz=min(float(self.config.coarse_step_mhz), float(self.config.fine_window_mhz)),
            fine_step_mhz=self.config.fine_step_mhz,
            fine_window_mhz=self.config.fine_window_mhz,
            top_k=self.config.top_k,
            interference_window_mhz=self.config.interference_window_mhz,
            guard_mhz=self.config.guard_mhz,
            link_distance_km=self.config.link_distance_km,
            path_loss_weight=self.config.path_loss_weight,
            interference_weight=self.config.interference_weight,
        )

        best_freq = self.scanner.coarse_then_fine_best_freq(
            request=request,
            platform=platform,
            missions=missions,
            config=runtime_config,
        )

        if best_freq is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"לא הצלחנו למצוא תדר מתאים בתוך הטווח המאושר ({min_mhz}-{max_mhz} MHz).",
            )

        return FrequencyResponse(freq_mhz=float(best_freq), tx_power_dbm=30.0)
