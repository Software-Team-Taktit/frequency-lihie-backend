from types import SimpleNamespace

import pytest

from services.co_existing_service.newton_raphson import (
    NewtonConfig,
    StoppingReason,
    optimize_tx_power_newton_raphson,
    solve_tx_power_newton_raphson,
)


def test_newton_raphson_converges_with_simple_linear_sinr_function():
    def fake_sinr_calculated(tx_power, selected_frequency, context):
        return tx_power - 10.0

    result = optimize_tx_power_newton_raphson(
        selected_frequency=50.0,
        initial_tx_power=30.0,
        sinr_required=0.0,
        context=None,
        sinr_calculated=fake_sinr_calculated,
        max_iterations=10,
        tolerance=0.001,
        min_tx_power=-100.0,
        max_tx_power=100.0,
        derivative_step=0.1,
    )

    assert result.converged is True
    assert result.stopping_reason == StoppingReason.CONVERGED
    assert result.optimal_tx_power == pytest.approx(10.0, abs=0.001)


def test_newton_raphson_returns_immediate_success_when_initial_power_is_good():
    def fake_sinr_calculated(tx_power, selected_frequency, context):
        return 12.0

    result = optimize_tx_power_newton_raphson(
        selected_frequency=50.0,
        initial_tx_power=20.0,
        sinr_required=12.0,
        context=None,
        sinr_calculated=fake_sinr_calculated,
        max_iterations=10,
        tolerance=0.1,
        min_tx_power=-100.0,
        max_tx_power=100.0,
        derivative_step=0.1,
    )

    assert result.converged is True
    assert result.iterations == 0
    assert result.stopping_reason == StoppingReason.INITIAL_POWER_WITHIN_TOLERANCE


def test_solve_tx_power_requires_selected_frequency():
    platform = SimpleNamespace(
        tx_gain=2.0,
        rx_gain=2.0,
        bw_khz=20.0,
        noise_figure_db=3.0,
    )

    with pytest.raises(ValueError):
        solve_tx_power_newton_raphson(
            platform=platform,
            path_loss_db=80.0,
            interference_mw=0.0,
            sinr_required_db=12.0,
            selected_frequency=None,
        )


def test_solve_tx_power_returns_result_object_when_requested():
    platform = SimpleNamespace(
        tx_gain=2.0,
        rx_gain=2.0,
        bw_khz=20.0,
        noise_figure_db=3.0,
    )

    result = solve_tx_power_newton_raphson(
        platform=platform,
        path_loss_db=80.0,
        interference_mw=0.0,
        sinr_required_db=12.0,
        selected_frequency=50.0,
        config=NewtonConfig(
            tol_db=0.1,
            max_iter=20,
            ptx_min_dbm=-100.0,
            ptx_max_dbm=100.0,
            numeric_derivative_step_db=0.1,
        ),
        return_result=True,
    )

    assert result.optimal_tx_power >= -100.0
    assert result.optimal_tx_power <= 100.0
    assert result.iterations >= 0