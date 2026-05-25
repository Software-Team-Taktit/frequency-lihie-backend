from types import SimpleNamespace

from models.enums.enviroment_type import EnviromentType
from services.models.enums.pathloss_models_enum import PropagationModelType

from services.co_existing_service.frequency_scanner import (
    Band,
    CoarseFineScanConfig,
    FrequencyScanner,
)


class FakePropagationFactory:
    def get_model_type(self, env_type):
        return PropagationModelType.FSPL

    def distance_km(self, a, b):
        return 1.0

    def path_loss_db(self, dto):
        return 80.0


def make_platform():
    return SimpleNamespace(
        tx_gain=2.0,
        rx_gain=2.0,
        tx_height_m=30.0,
        rx_height_m=1.5,
        bw_khz=20.0,
        noise_figure_db=3.0,
        min_sinr_required_db=12.0,
    )


def make_request():
    return SimpleNamespace(
        name="Test Mission",
        coordinate=SimpleNamespace(lat=32.0, lon=35.0),
        enviroment_type=EnviromentType.OPEN_SPACE,
        platform_id="platform-1",
        exclude_mission_id=None,
    )


def make_mission(freq_mhz, tx_power_dbm=30.0, is_active=True):
    return SimpleNamespace(
        id=f"mission-{freq_mhz}",
        freq_mhz=freq_mhz,
        tx_power_dbm=tx_power_dbm,
        coordinate=SimpleNamespace(lat=32.0, lon=35.0),
        is_active=is_active,
    )


def test_generate_freqs_creates_expected_frequency_steps():
    scanner = FrequencyScanner(FakePropagationFactory())

    result = scanner._generate_freqs(33.0, 35.0, 1.0)

    assert result == [33.0, 34.0, 35.0]


def test_frequency_scanner_does_not_select_used_frequency():
    scanner = FrequencyScanner(FakePropagationFactory())

    config = CoarseFineScanConfig(
        bands=[Band(33.0, 36.0)],
        coarse_step_mhz=1.0,
        fine_step_mhz=1.0,
        fine_window_mhz=1.0,
        top_k=3,
        interference_window_mhz=1.0,
        guard_mhz=0.1,
        link_distance_km=1.0,
        path_loss_weight=1.0,
        interference_weight=1.0,
    )

    selected = scanner.coarse_then_fine_best_freq(
        request=make_request(),
        platform=make_platform(),
        missions=[
            make_mission(33.0),
            make_mission(35.0),
        ],
        config=config,
    )

    assert selected is not None
    assert 33.0 <= selected <= 36.0
    assert selected not in [33.0, 35.0]


def test_interference_is_higher_near_existing_mission_frequency():
    scanner = FrequencyScanner(FakePropagationFactory())
    request = make_request()
    platform = make_platform()

    missions = [
        make_mission(40.0, tx_power_dbm=30.0),
    ]

    near_interference = scanner._interference_mw(
        request=request,
        platform=platform,
        missions=missions,
        candidate_freq_mhz=40.0,
        interference_window_mhz=1.0,
    )

    far_interference = scanner._interference_mw(
        request=request,
        platform=platform,
        missions=missions,
        candidate_freq_mhz=50.0,
        interference_window_mhz=1.0,
    )

    assert near_interference > far_interference