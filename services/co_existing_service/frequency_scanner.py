import math
from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from typing import Iterable, List, Optional

from models.domain.types.platform import Platform
from models.domain.types.mission import Mission
from models.requests.frequency_req_res import FrequencyRequest

from services.utils.helpers import clamp_positive, dbm_to_mw, noise_floor_dbm
from services.co_existing_service.propagation_factory import PropagationFactory
from services.models.generic_propagation_dto import GenericPropagationDTO


# scan config
# ---------------------
@dataclass(frozen=True)
class Band:
    start_mhz: float
    end_mhz: float


@dataclass(frozen=True)
class CoarseFineScanConfig:
    bands: List[Band]
    coarse_step_mhz: float = 5.0
    fine_step_mhz: float = 0.1
    fine_window_mhz: float = 5.0
    top_k: int = 5
    interference_window_mhz: float = 5.0
    guard_mhz: float = 0.0
    link_distance_km: float = 1.0
    path_loss_weight: float = 1.0
    interference_weight: float = 1.0


@dataclass(frozen=True)
class MissionInfluence:
    freq_mhz: float
    rx_mw: float


# frequency scanner
# ---------------------
class FrequencyScanner:
    def __init__(self, propagation: PropagationFactory):
        self.propagation = propagation

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
    ) -> float:
        """
        Interfernce only from other missions around candidate frequency.
        does not include noise.
        """

        sigma = clamp_positive(interference_window_mhz, 0.001)
        interf_mw = 0.0

        for m in missions:
            delta = abs(m.freq_mhz - candidate_freq_mhz)
            weight = math.exp(-(delta**2) / (2 * (sigma**2)))

            if weight < 1e-9:
                continue

            d_km = self.propagation.distance_km(m.coordinate, request.coordinate)
            model_type = self.propagation.get_model_type(request.enviroment_type)

            dto = GenericPropagationDTO(
                model_type=model_type,
                freq_mhz=float(m.freq_mhz),
                distance_km=d_km,
                tx_height_m=platform.tx_height_m,
                rx_height_m=platform.rx_height_m,
            )

            pl_db = self.propagation.path_loss_db(dto)

            p_rx_dbm = m.tx_power_dbm - pl_db
            interf_mw += weight * dbm_to_mw(p_rx_dbm)

        return float(interf_mw)

    def _build_mission_index(
        self,
        request: FrequencyRequest,
        platform: Platform,
        missions: Iterable[Mission],
    ) -> List[MissionInfluence]:
        model_type = self.propagation.get_model_type(request.enviroment_type)
        indexed: List[MissionInfluence] = []

        for mission in missions:
            d_km = self.propagation.distance_km(mission.coordinate, request.coordinate)
            dto = GenericPropagationDTO(
                model_type=model_type,
                freq_mhz=float(mission.freq_mhz),
                distance_km=d_km,
                tx_height_m=platform.tx_height_m,
                rx_height_m=platform.rx_height_m,
            )

            pl_db = self.propagation.path_loss_db(dto)
            p_rx_dbm = mission.tx_power_dbm - pl_db
            indexed.append(
                MissionInfluence(
                    freq_mhz=round(float(mission.freq_mhz), 6),
                    rx_mw=float(dbm_to_mw(p_rx_dbm)),
                )
            )

        indexed.sort(key=lambda item: item.freq_mhz)
        return indexed

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
        mission_index: List[MissionInfluence],
        mission_freqs: List[float],
        candidate_freq_mhz: float,
        interference_window_mhz: float,
    ) -> float:
        sigma = clamp_positive(interference_window_mhz, 0.001)
        radius = self._interference_radius_mhz(interference_window_mhz)
        candidate = round(float(candidate_freq_mhz), 6)

        left = bisect_left(mission_freqs, candidate - radius)
        right = bisect_right(mission_freqs, candidate + radius)

        interf_mw = 0.0
        for item in mission_index[left:right]:
            delta = abs(item.freq_mhz - candidate)
            weight = math.exp(-(delta**2) / (2 * (sigma**2)))
            interf_mw += weight * item.rx_mw

        return float(interf_mw)

    def _interference_score_mw(
        self,
        request: FrequencyRequest,
        platform: Platform,
        missions: Iterable[Mission],
        candidate_freq_mhz: float,
        interference_window_mhz: float,
    ) -> float:
        """
        Interference + Noise (mW) used for frequency scoring.
        This keeps the existing scanning behavior unchanged.
        """
        noise_mw = dbm_to_mw(noise_floor_dbm(platform))
        interf_mw = self._interference_mw(
            request=request,
            platform=platform,
            missions=missions,
            candidate_freq_mhz=candidate_freq_mhz,
            interference_window_mhz=interference_window_mhz,
        )
        return float(interf_mw) + float(noise_mw)

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

    def _quality_score(
        self,
        request: FrequencyRequest,
        platform: Platform,
        missions: Iterable[Mission],
        candidate_freq_mhz: float,
        config: CoarseFineScanConfig,
    ) -> float:
        """Single score: lower is better."""
        pl_db = self._link_path_loss_db(
            request=request,
            platform=platform,
            candidate_freq_mhz=candidate_freq_mhz,
            link_distance_km=config.link_distance_km,
        )

        interf_mw = self._interference_score_mw(
            request=request,
            platform=platform,
            missions=missions,
            candidate_freq_mhz=float(candidate_freq_mhz),
            interference_window_mhz=float(config.interference_window_mhz),
        )

        interf_mw = float(interf_mw)
        if interf_mw <= 0 or math.isnan(interf_mw) or math.isinf(interf_mw):
            return float("inf")

        interf_dbm = 10.0 * math.log10(interf_mw)

        return (
            float(config.path_loss_weight) * float(pl_db)
            + float(config.interference_weight) * float(interf_dbm)
        )

    def _quality_score_from_index(
        self,
        request: FrequencyRequest,
        platform: Platform,
        mission_index: List[MissionInfluence],
        mission_freqs: List[float],
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
            mission_index=mission_index,
            mission_freqs=mission_freqs,
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
    ) -> Optional[float]:
        best_freq = None
        best_score = float("inf")

        EPS = 1e-6
        mission_list = list(missions)
        mission_index = self._build_mission_index(
            request=request,
            platform=platform,
            missions=mission_list,
        )
        mission_freqs = [item.freq_mhz for item in mission_index]

        used_freqs = []
        for mission in mission_list:
            try:
                used_freqs.append(round(float(mission.freq_mhz), 6))
            except Exception:
                pass
        used_freqs.sort()

        def is_blocked(f: float) -> bool:
            f = round(float(f), 6)
            guard = float(getattr(config, "guard_mhz", 0.0) or 0.0)
            radius = guard + EPS if guard > 0 else EPS
            idx = bisect_left(used_freqs, f)

            if idx < len(used_freqs) and abs(used_freqs[idx] - f) <= radius:
                return True

            if idx > 0 and abs(used_freqs[idx - 1] - f) <= radius:
                return True

            return False

        def safe_score(f: float) -> float:
            s = self._quality_score_from_index(
                request=request,
                platform=platform,
                mission_index=mission_index,
                mission_freqs=mission_freqs,
                candidate_freq_mhz=float(f),
                config=config,
            )
            if s is None or math.isnan(s) or math.isinf(s):
                return float("inf")
            return float(s)

        def first_unblocked_in_range() -> float:
            for band in config.bands:
                freqs = self._generate_freqs(band.start_mhz, band.end_mhz, config.coarse_step_mhz)
                for f in freqs:
                    if not is_blocked(f):
                        return float(f)
            return None

        for band in config.bands:
            coarse_freqs = self._generate_freqs(band.start_mhz, band.end_mhz, config.coarse_step_mhz)
            coarse_scored = []

            for f in coarse_freqs:
                if is_blocked(f):
                    continue

                score = safe_score(f)
                if score == float("inf"):
                    continue

                coarse_scored.append((score, f))

            if not coarse_scored:
                continue

            coarse_scored.sort(key=lambda x: x[0])
            top = coarse_scored[: max(1, config.top_k)]

            for _, center_f in top:
                fine_start = max(band.start_mhz, center_f - config.fine_window_mhz)
                fine_end = min(band.end_mhz, center_f + config.fine_window_mhz)
                fine_freqs = self._generate_freqs(fine_start, fine_end, config.fine_step_mhz)

                for f in fine_freqs:
                    if is_blocked(f):
                        continue

                    score = safe_score(f)
                    if score == float("inf"):
                        continue

                    if score < best_score:
                        best_score = score
                        best_freq = f

        if best_freq is None:
            return first_unblocked_in_range()

        return float(best_freq)
