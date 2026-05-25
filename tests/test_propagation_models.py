import math

import pytest

from models.enums.enviroment_type import EnviromentType
from services.models.enums.pathloss_models_enum import PropagationModelType
from services.models.generic_propagation_dto import GenericPropagationDTO
from services.models.types.fspl_dto import FsplDTO
from services.models.types.hata_dto import HataDTO
from services.models.types.egli_dto import EgliDTO

from services.co_existing_service.propagation_factory import PropagationFactory
from services.domain_propagation_models.fspl_model import FSPLModel
from services.domain_propagation_models.hata_model import HataModel
from services.domain_propagation_models.egli_model import EgliModel


def test_fspl_model_calculates_expected_path_loss():
    dto = FsplDTO(
        freq_mhz=100.0,
        distance_km=1.0,
    )

    result = FSPLModel().calculate_path_loss(dto)

    expected = 32.45 + 20 * math.log10(1.0) + 20 * math.log10(100.0)
    assert result == pytest.approx(expected, abs=0.001)


def test_egli_model_calculates_expected_path_loss():
    dto = EgliDTO(
        freq_mhz=100.0,
        distance_km=1.0,
        tx_height_m=10.0,
        rx_height_m=2.0,
    )

    result = EgliModel().calculate_path_loss(dto)

    expected = (
        117.0
        + 40.0 * math.log10(1.0)
        + 20.0 * math.log10(100.0)
        - 20.0 * math.log10(10.0 * 2.0)
    )

    assert result == pytest.approx(expected, abs=0.001)


def test_hata_model_path_loss_increases_when_distance_increases():
    model = HataModel()

    near = HataDTO(
        freq_mhz=150.0,
        distance_km=1.0,
        tx_height_m=30.0,
        rx_height_m=1.5,
    )

    far = HataDTO(
        freq_mhz=150.0,
        distance_km=10.0,
        tx_height_m=30.0,
        rx_height_m=1.5,
    )

    near_loss = model.calculate_path_loss(near)
    far_loss = model.calculate_path_loss(far)

    assert far_loss > near_loss


def test_propagation_factory_maps_environment_to_correct_model_type():
    factory = PropagationFactory()

    assert factory.get_model_type(EnviromentType.OPEN_SPACE) == PropagationModelType.FSPL
    assert factory.get_model_type(EnviromentType.URBAN) == PropagationModelType.HATA
    assert factory.get_model_type(EnviromentType.MOUNT) == PropagationModelType.EGLI


def test_propagation_factory_calculates_path_loss_from_generic_dto():
    factory = PropagationFactory()

    dto = GenericPropagationDTO(
        model_type=PropagationModelType.FSPL,
        freq_mhz=100.0,
        distance_km=1.0,
        tx_height_m=30.0,
        rx_height_m=1.5,
    )

    result = factory.path_loss_db(dto)

    assert result > 0
    assert result == pytest.approx(72.45, abs=0.01)