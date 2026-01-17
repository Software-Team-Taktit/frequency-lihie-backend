import math
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

    def _interference_score_mw(
        self,
        request: FrequencyRequest,
        platform: Platform,
        missions: Iterable[Mission],
        candidate_freq_mhz: float,
        interference_window_mhz: float,
    ) -> float:
        noise_mw = dbm_to_mw(noise_floor_dbm(platform))

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

        return interf_mw + noise_mw

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

        used_freqs = []
        for m in missions:
            try:
                used_freqs.append(round(float(m.freq_mhz), 6))
            except Exception:
                pass

        def is_blocked(f: float) -> bool:
            f = round(float(f), 6)
            guard = float(getattr(config, "guard_mhz", 0.0) or 0.0)

            if guard > 0:
                return any(abs(u - f) <= guard + EPS for u in used_freqs)

            return any(abs(u - f) <= EPS for u in used_freqs)

        def safe_score(f: float) -> float:
            s = self._quality_score(
                request=request,
                platform=platform,
                missions=missions,
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
