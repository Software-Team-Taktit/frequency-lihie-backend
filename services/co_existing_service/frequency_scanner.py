import math
from dataclasses import dataclass
from typing import Iterable, List, Optional, Dict, Tuple

from models.domain.types.platform import Platform
from models.domain.types.mission import Mission
from models.requests.frequency_req_res import FrequencyRequest

from services.utils.helpers import clamp_positive, dbm_to_mw, noise_floor_dbm
from services.co_existing_service.propagation_factory import PropagationFactory
from services.models.generic_propagation_dto import GenericPropagationDTO

from services.co_existing_service.utils.avl_node import _AVLFrequencyTree

# scan config
# ---------------------
@dataclass(frozen=True)
class Band:
    start_mhz: float
    end_mhz: float


@dataclass(frozen=True)
class CoarseFineScanConfig:
    bands: List[Band]
    coarse_step_mhz: float = 2.0
    fine_step_mhz: float = 0.1
    fine_window_mhz: float = 5.0
    top_k: int = 5
    interference_window_mhz: float = 5.0

    # Legacy field. Do not use this as the real channel width.
    guard_mhz: float = 0.0

    # Optional extra spacing beyond the real bandwidth overlap.
    # 0.05 MHz = 50 kHz extra safety gap.
    safety_gap_mhz: float = 0.05

    link_distance_km: float = 1.0
    path_loss_weight: float = 1.0
    interference_weight: float = 1.0

# frequency scanner
# ---------------------
class FrequencyScanner:
    def __init__(self, propagation: PropagationFactory):
        self.propagation = propagation

    def _platform_bw_mhz(self, platform: Platform) -> float:
        return clamp_positive(float(getattr(platform, "bw_khz", 0.0)) / 1000.0, 1e-6)

    def _config_safety_gap_mhz(self, config: CoarseFineScanConfig) -> float:
        return max(0.0, float(getattr(config, "safety_gap_mhz", 0.0) or 0.0))

    def _existing_platform_for_mission(
        self,
        mission: Mission,
        fallback_platform: Platform,
        platforms_by_id: Optional[Dict[str, Platform]],
    ) -> Platform:
        if not platforms_by_id:
            return fallback_platform

        platform_id = getattr(mission, "platform_id", None)
        if platform_id is None:
            return fallback_platform

        return platforms_by_id.get(str(platform_id), fallback_platform)

    def _build_occupied_channels_index(
        self,
        missions: Iterable[Mission],
        platform: Platform,
        platforms_by_id: Optional[Dict[str, Platform]],
    ) -> Tuple[_AVLFrequencyTree, Dict[float, List[float]], float]:
        tree = _AVLFrequencyTree()
        channel_half_bws_by_freq: Dict[float, List[float]] = {}
        max_existing_half_bw = 0.0

        for mission in missions:
            try:
                freq = round(float(mission.freq_mhz), 6)

                existing_platform = self._existing_platform_for_mission(
                    mission=mission,
                    fallback_platform=platform,
                    platforms_by_id=platforms_by_id,
                )

                existing_half_bw = self._platform_bw_mhz(existing_platform) / 2.0
                max_existing_half_bw = max(max_existing_half_bw, existing_half_bw)

                channel_half_bws_by_freq.setdefault(freq, []).append(existing_half_bw)

                try:
                    tree.insert(freq, 0.0)
                except Exception:
                    pass

            except Exception:
                pass

        return tree, channel_half_bws_by_freq, max_existing_half_bw

    def _generate_freqs(self, start: float, end: float, step: float) -> List[float]:
        step = clamp_positive(step, 1e-6)
        freqs = []
        f = start

        while f <= end + 1e-9:
            freqs.append(round(f, 6))
            f += step

        return freqs

    def _interference_mw(
        self,
        request: FrequencyRequest,
        platform: Platform,
        missions: Iterable[Mission],
        candidate_freq_mhz: float,
        interference_window_mhz: float,
        platforms_by_id: Optional[Dict[str, Platform]] = None,
    ) -> float:
        """
        Interference only from other missions around candidate frequency.
        Does not include noise.
        """

        sigma = clamp_positive(interference_window_mhz, 0.001)
        interf_mw = 0.0

        for m in missions:
            delta = abs(float(m.freq_mhz) - float(candidate_freq_mhz))
            weight = math.exp(-(delta**2) / (2 * (sigma**2)))

            if weight < 1e-9:
                continue

            existing_platform = self._existing_platform_for_mission(
                mission=m,
                fallback_platform=platform,
                platforms_by_id=platforms_by_id,
            )

            d_km = clamp_positive(
                self.propagation.distance_km(m.coordinate, request.coordinate),
                0.001
            )

            model_type = self.propagation.get_model_type(request.enviroment_type)

            dto = GenericPropagationDTO(
                model_type=model_type,
                freq_mhz=float(m.freq_mhz),
                distance_km=d_km,
                tx_height_m=existing_platform.tx_height_m,
                rx_height_m=platform.rx_height_m,
            )

            pl_db = self.propagation.path_loss_db(dto)

            p_rx_dbm = (
                float(m.tx_power_dbm)
                + float(existing_platform.tx_gain)
                + float(platform.rx_gain)
                - float(pl_db)
            )

            interf_mw += weight * dbm_to_mw(p_rx_dbm)

        return float(interf_mw)

    def _build_mission_index(
        self,
        request: FrequencyRequest,
        platform: Platform,
        missions: Iterable[Mission],
        platforms_by_id: Optional[Dict[str, Platform]] = None,
    ) -> _AVLFrequencyTree:
        model_type = self.propagation.get_model_type(request.enviroment_type)
        tree = _AVLFrequencyTree()

        for mission in missions:
            existing_platform = self._existing_platform_for_mission(
                mission=mission,
                fallback_platform=platform,
                platforms_by_id=platforms_by_id,
            )

            d_km = clamp_positive(
                self.propagation.distance_km(mission.coordinate, request.coordinate),
                0.001
            )

            dto = GenericPropagationDTO(
                model_type=model_type,
                freq_mhz=float(mission.freq_mhz),
                distance_km=d_km,
                tx_height_m=existing_platform.tx_height_m,
                rx_height_m=platform.rx_height_m,
            )

            pl_db = self.propagation.path_loss_db(dto)

            p_rx_dbm = (
                float(mission.tx_power_dbm)
                + float(existing_platform.tx_gain)
                + float(platform.rx_gain)
                - float(pl_db)
            )

            tree.insert(
                key=round(float(mission.freq_mhz), 6),
                value=float(dbm_to_mw(p_rx_dbm)),
            )

        return tree

    
    def _interference_radius_mhz(
        self,
        interference_window_mhz: float,
        weight_floor: float = 1e-9,
    ) -> float:
        sigma = clamp_positive(interference_window_mhz, 0.001)
        floor = clamp_positive(weight_floor, 1e-12)
        return float(sigma * math.sqrt(2.0 * math.log(1.0 / floor)))

    def _interference_mw_from_index(
        self,
        mission_tree: _AVLFrequencyTree,
        candidate_freq_mhz: float,
        interference_window_mhz: float,
    ) -> float:
        sigma = clamp_positive(interference_window_mhz, 0.001)
        radius = self._interference_radius_mhz(interference_window_mhz)
        candidate = round(float(candidate_freq_mhz), 6)

        interf_mw = 0.0
        for freq_mhz, aggregated_rx_mw in mission_tree.iter_range(candidate - radius, candidate + radius):
            delta = abs(freq_mhz - candidate)
            weight = math.exp(-(delta**2) / (2 * (sigma**2)))
            interf_mw += weight * aggregated_rx_mw

        return float(interf_mw)


    def _link_path_loss_db(
        self,
        request: FrequencyRequest,
        platform: Platform,
        candidate_freq_mhz: float,
        link_distance_km: float,
    ) -> float:
        """Path loss for the desired link at a nominal distance."""
        model_type = self.propagation.get_model_type(request.enviroment_type)
        dto = GenericPropagationDTO(
            model_type=model_type,
            freq_mhz=float(candidate_freq_mhz),
            distance_km=float(clamp_positive(link_distance_km, 0.001)),
            tx_height_m=platform.tx_height_m,
            rx_height_m=platform.rx_height_m,
        )
        return float(self.propagation.path_loss_db(dto))


    def _quality_score_from_index(
        self,
        request: FrequencyRequest,
        platform: Platform,
        mission_tree: _AVLFrequencyTree,
        candidate_freq_mhz: float,
        config: CoarseFineScanConfig,
    ) -> float:
        pl_db = self._link_path_loss_db(
            request=request,
            platform=platform,
            candidate_freq_mhz=candidate_freq_mhz,
            link_distance_km=config.link_distance_km,
        )

        noise_mw = dbm_to_mw(noise_floor_dbm(platform))
        interf_mw = self._interference_mw_from_index(
            mission_tree=mission_tree,
            candidate_freq_mhz=float(candidate_freq_mhz),
            interference_window_mhz=float(config.interference_window_mhz),
        )

        total_interf_mw = float(interf_mw) + float(noise_mw)
        if total_interf_mw <= 0 or math.isnan(total_interf_mw) or math.isinf(total_interf_mw):
            return float("inf")

        interf_dbm = 10.0 * math.log10(total_interf_mw)

        return (
            float(config.path_loss_weight) * float(pl_db)
            + float(config.interference_weight) * float(interf_dbm)
        )

    def coarse_then_fine_best_freq(
        self,
        request,
        platform,
        missions,
        config,
        platforms_by_id: Optional[Dict[str, Platform]] = None,
    ) -> Optional[float]:
        best_freq = None
        best_score = float("inf")

        EPS = 1e-6
        mission_list = list(missions)

        mission_tree = self._build_mission_index(
            request=request,
            platform=platform,
            missions=mission_list,
            platforms_by_id=platforms_by_id,
        )

        used_freqs_tree, used_channel_half_bws_by_freq, max_used_half_bw = (
            self._build_occupied_channels_index(
                missions=mission_list,
                platform=platform,
                platforms_by_id=platforms_by_id,
            )
        )

        candidate_half_bw = self._platform_bw_mhz(platform) / 2.0
        safety_gap = self._config_safety_gap_mhz(config)

        max_block_lookup_radius = (
            candidate_half_bw
            + max_used_half_bw
            + safety_gap
            + EPS
        )

        def is_blocked(f: float) -> bool:
            candidate = round(float(f), 6)

            if max_used_half_bw <= 0:
                return False

            for existing_freq, _ in used_freqs_tree.iter_range(
                candidate - max_block_lookup_radius,
                candidate + max_block_lookup_radius,
            ):
                existing_freq = round(float(existing_freq), 6)
                existing_half_bws = used_channel_half_bws_by_freq.get(existing_freq, [])

                for existing_half_bw in existing_half_bws:
                    min_required_distance = (
                        candidate_half_bw
                        + existing_half_bw
                        + safety_gap
                    )

                    if abs(candidate - existing_freq) <= min_required_distance + EPS:
                        return True

            return False

        def safe_score(f: float) -> float:
            s = self._quality_score_from_index(
                request=request,
                platform=platform,
                mission_tree=mission_tree,
                candidate_freq_mhz=float(f),
                config=config,
            )

            if s is None or math.isnan(s) or math.isinf(s):
                return float("inf")

            return float(s)

        def add_block_edge_centers(band: Band, centers: set) -> None:
            if max_used_half_bw <= 0:
                return

            band_start = float(band.start_mhz)
            band_end = float(band.end_mhz)

            for existing_freq, _ in used_freqs_tree.iter_range(
                band_start - max_block_lookup_radius,
                band_end + max_block_lookup_radius,
            ):
                existing_freq = round(float(existing_freq), 6)
                existing_half_bws = used_channel_half_bws_by_freq.get(existing_freq, [])

                for existing_half_bw in existing_half_bws:
                    blocked_radius = (
                        candidate_half_bw
                        + existing_half_bw
                        + safety_gap
                    )

                    left_edge = existing_freq - blocked_radius
                    right_edge = existing_freq + blocked_radius

                    if band_start <= left_edge <= band_end:
                        centers.add(round(left_edge, 6))

                    if band_start <= right_edge <= band_end:
                        centers.add(round(right_edge, 6))

        def fallback_best_unblocked_in_range() -> Optional[float]:
            fallback_freq = None
            fallback_score = float("inf")

            for band in config.bands:
                freqs = self._generate_freqs(
                    band.start_mhz,
                    band.end_mhz,
                    config.fine_step_mhz,
                )

                for f in freqs:
                    if is_blocked(f):
                        continue

                    score = safe_score(f)
                    if score == float("inf"):
                        continue

                    if score < fallback_score:
                        fallback_score = score
                        fallback_freq = f

            return fallback_freq

        for band in config.bands:
            coarse_freqs = self._generate_freqs(
                band.start_mhz,
                band.end_mhz,
                config.coarse_step_mhz,
            )

            coarse_scored = []

            for f in coarse_freqs:
                if is_blocked(f):
                    continue

                score = safe_score(f)
                if score == float("inf"):
                    continue

                coarse_scored.append((score, f))

            coarse_scored.sort(key=lambda x: x[0])
            top = coarse_scored[: max(1, config.top_k)]

            fine_centers = {round(float(center_f), 6) for _, center_f in top}

            add_block_edge_centers(band, fine_centers)

            scanned_fine_freqs = set()

            for center_f in sorted(fine_centers):
                fine_start = max(band.start_mhz, center_f - config.fine_window_mhz)
                fine_end = min(band.end_mhz, center_f + config.fine_window_mhz)

                fine_freqs = self._generate_freqs(
                    fine_start,
                    fine_end,
                    config.fine_step_mhz,
                )

                for f in fine_freqs:
                    f = round(float(f), 6)

                    if f in scanned_fine_freqs:
                        continue

                    scanned_fine_freqs.add(f)

                    if is_blocked(f):
                        continue

                    score = safe_score(f)
                    if score == float("inf"):
                        continue

                    if score < best_score:
                        best_score = score
                        best_freq = f

        if best_freq is None:
            return fallback_best_unblocked_in_range()

        return float(best_freq)