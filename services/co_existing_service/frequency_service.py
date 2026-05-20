from fastapi import HTTPException, status

from models.requests.frequency_req_res import FrequencyRequest, FrequencyResponse
from repositories.types_repositories.platform_repository import PlatformRepository
from repositories.types_repositories.mission_repository import MissionRepository
from repositories.types_repositories.frequency_range_repository import FrequencyRangeRepository

from services.co_existing_service.frequency_scanner import FrequencyScanner, CoarseFineScanConfig, Band
from services.co_existing_service.newton_raphson import solve_tx_power_newton_raphson, NewtonConfig, NewtonRaphsonError

from deps.rabbitmq import publish_tts_result

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
        missions = [
            mission for mission in missions
            if getattr(mission, "is_active", False) is True
        ]
        
        if request.exclude_mission_id:
            missions = [
                mission for mission in missions
                if getattr(mission, "id", None) != request.exclude_mission_id
            ]

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
            
    
        path_loss_db = self.scanner._link_path_loss_db(
            request=request,
            platform=platform,
            candidate_freq_mhz=float(best_freq),
            link_distance_km=float(runtime_config.link_distance_km)
        )
        
        interference_mw = self.scanner._interference_mw(
            request=request,
            platform=platform,
            missions=missions,
            candidate_freq_mhz=float(best_freq),
            interference_window_mhz=float(runtime_config.interference_window_mhz)
        )
        
        print("best_freq:", best_freq)
        print("path_loss_db:", path_loss_db)
        print("interference_mw:", interference_mw)
        print("sinr_required:", platform.min_sinr_required_db)
        print("tx_gain:", platform.tx_gain, "rx_gain:", platform.rx_gain)
        print("tx_height_m:", platform.tx_height_m, "rx_height_m:", platform.rx_height_m)

        try:
            tx_power_dbm = solve_tx_power_newton_raphson(
                platform=platform,
                path_loss_db= float(path_loss_db),
                interference_mw=float(interference_mw),
                sinr_required_db=float(platform.min_sinr_required_db),
                config=NewtonConfig(
                    tol_db=0.1,
                    max_iter=20,
                    ptx_min_dbm=-100.0,
                    ptx_max_dbm=100.0,
                    numeric_derivative_step_db=0.1
                ),
            )
        except NewtonRaphsonError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"נכשל חישוב עוצמת שידור (Newton-Raphson): {str(e)}",
            )
        
        freq_hz = float(best_freq) * 1e6
        publish_tts_result(
            is_freq=True,
            freq_hz=freq_hz,
            tx_power_dbm=float(tx_power_dbm),
        )
        
        return FrequencyResponse(freq_mhz=float(best_freq), tx_power_dbm=round(float(tx_power_dbm)))
