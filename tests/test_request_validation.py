import pytest
from pydantic import ValidationError

from models.requests.platform_request import PlatformCreateRequest
from models.requests.user_request import UserCreateRequest, UserLogInRequest


def test_user_create_request_accepts_valid_personal_id():
    dto = UserCreateRequest(
        personal_id="1234567",
        first_name="Test",
        last_name="User",
        unit="Unit 1",
    )

    assert dto.personal_id == "1234567"


def test_user_create_request_rejects_invalid_personal_id():
    with pytest.raises(ValidationError):
        UserCreateRequest(
            personal_id="123",
            first_name="Test",
            last_name="User",
            unit="Unit 1",
        )


def test_user_login_request_rejects_non_numeric_personal_id():
    with pytest.raises(ValidationError):
        UserLogInRequest(personal_id="abcdefg")


def test_platform_create_request_uses_default_rf_values():
    dto = PlatformCreateRequest(
        name="Test Platform",
        tx_gain=2.0,
        rx_gain=2.0,
    )

    assert dto.bw_khz == 20.0
    assert dto.tx_height_m == 30.0
    assert dto.rx_height_m == 1.5
    assert dto.min_sinr_required_db == 12.0
    assert dto.noise_figure_db == 3.0