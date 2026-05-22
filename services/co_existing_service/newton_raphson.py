import math
from dataclasses import asdict, dataclass
from typing import Any, Callable, Optional

from models.domain.types.platform import Platform
from services.utils.helpers import (
    clamp_positive,
    dbm_to_mw,
    mw_to_dbm,
    noise_floor_dbm,
    sinr_db,
)


SinrCalculator = Callable[[float, float, Any], float]
DerivativeCalculator = Callable[[float, float, Any], float]
ObjectiveFunction = Callable[[float], float]


class StoppingReason:
    INVALID_SINR_AT_INITIAL_POWER = "invalid_sinr_value_at_initial_power"
    INITIAL_POWER_WITHIN_TOLERANCE = "initial_power_within_tolerance"
    BOUNDARY_PREVENTS_CENTRAL_DERIVATIVE = (
        "tx_power_boundary_prevents_central_derivative"
    )
    INVALID_SINR_DURING_DERIVATIVE = (
        "invalid_sinr_value_during_derivative_calculation"
    )
    DERIVATIVE_TOO_CLOSE_TO_ZERO = "derivative_too_close_to_zero"
    INVALID_NEWTON_STEP = "invalid_newton_step"
    INVALID_SINR_AT_POWER_BOUNDARY = "invalid_sinr_value_at_power_boundary"
    CONVERGED_AT_POWER_BOUNDARY = "converged_at_tx_power_boundary"
    POWER_BOUNDARY_REACHED = "tx_power_boundary_reached"
    INVALID_SINR_AFTER_NEWTON_STEP = "invalid_sinr_value_after_newton_step"
    CONVERGED = "converged"
    MAX_ITERATIONS_REACHED = "max_iterations_reached"


@dataclass(frozen=True)
class NewtonConfig:
    """Configuration for the fixed-frequency Newton-Raphson power optimizer."""

    tol_db: float = 0.1
    max_iter: int = 20
    ptx_min_dbm: float = -100.0
    ptx_max_dbm: float = 100.0
    numeric_derivative_step_db: float = 0.1
    derivative_epsilon: float = 0.01


@dataclass(frozen=True)
class NewtonRaphsonResult:
    """Full optimization result returned by the academic fixed-frequency solver."""

    optimal_tx_power: float
    final_sinr_error: float
    iterations: int
    converged: bool
    stopping_reason: str

    def to_dict(self) -> dict[str, float | int | bool | str]:
        return asdict(self)


@dataclass(frozen=True)
class FixedFrequencySinrContext:
    """
    Context for the existing link-budget SINR calculation.

    The selected frequency is already represented by path_loss_db and
    interference_mw before Newton-Raphson is called.
    """

    platform: Platform
    path_loss_db: float
    interference_mw: float


@dataclass(frozen=True)
class _NewtonOptimizerInputs:
    selected_frequency: float
    initial_tx_power: float
    sinr_required: float
    max_iterations: int
    tolerance: float
    derivative_epsilon: float
    min_tx_power: float
    max_tx_power: float
    derivative_step: float


@dataclass(frozen=True)
class _NewtonIterationState:
    current_power: float
    current_error: float
    best_power: float
    best_error: float

    @classmethod
    def initial(cls, power: float, error: float) -> "_NewtonIterationState":
        return cls(
            current_power=power,
            current_error=error,
            best_power=power,
            best_error=error,
        )

    def with_current(self, power: float, error: float) -> "_NewtonIterationState":
        return _NewtonIterationState(
            current_power=power,
            current_error=error,
            best_power=self.best_power,
            best_error=self.best_error,
        )

    def with_best_candidate(
        self,
        power: float,
        error: float,
    ) -> "_NewtonIterationState":
        if abs(error) >= abs(self.best_error):
            return self

        return _NewtonIterationState(
            current_power=self.current_power,
            current_error=self.current_error,
            best_power=power,
            best_error=error,
        )


class NewtonRaphsonError(RuntimeError):
    pass


class _CentralDerivativeStepUnavailable(RuntimeError):
    pass


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _require_finite_number(name: str, value: float) -> float:
    try:
        numeric_value = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a numeric value.") from exc

    if not math.isfinite(numeric_value):
        raise ValueError(f"{name} must be finite.")

    return numeric_value


def _make_result(
    *,
    optimal_tx_power: float,
    final_sinr_error: float,
    iterations: int,
    converged: bool,
    stopping_reason: str,
) -> NewtonRaphsonResult:
    return NewtonRaphsonResult(
        optimal_tx_power=optimal_tx_power,
        final_sinr_error=final_sinr_error,
        iterations=iterations,
        converged=converged,
        stopping_reason=stopping_reason,
    )


def _best_result(
    *,
    state: _NewtonIterationState,
    iterations: int,
    converged: bool,
    stopping_reason: str,
) -> NewtonRaphsonResult:
    return _make_result(
        optimal_tx_power=state.best_power,
        final_sinr_error=state.best_error,
        iterations=iterations,
        converged=converged,
        stopping_reason=stopping_reason,
    )


def _has_converged(error: float, tolerance: float) -> bool:
    return abs(error) <= tolerance


def _is_derivative_unstable(derivative: float, derivative_epsilon: float) -> bool:
    return abs(derivative) < derivative_epsilon


def _is_outside_power_bounds(power: float, inputs: _NewtonOptimizerInputs) -> bool:
    return power < inputs.min_tx_power or power > inputs.max_tx_power


def _newton_next_power(current_power: float, current_error: float, derivative: float) -> float:
    return current_power - (current_error / derivative)


def _validate_positive(name: str, value: float) -> float:
    value = _require_finite_number(name, value)

    if value <= 0.0:
        raise ValueError(f"{name} must be positive.")

    return value


def _validate_optimizer_inputs(
    *,
    selected_frequency: float,
    initial_tx_power: float,
    sinr_required: float,
    max_iterations: int,
    tolerance: float,
    derivative_epsilon: float,
    min_tx_power: float,
    max_tx_power: float,
    derivative_step: float,
) -> _NewtonOptimizerInputs:
    selected_frequency = _validate_positive(
        "selected_frequency",
        selected_frequency,
    )

    sinr_required = _require_finite_number("sinr_required", sinr_required)
    current_power = _require_finite_number("initial_tx_power", initial_tx_power)
    min_tx_power = _require_finite_number("min_tx_power", min_tx_power)
    max_tx_power = _require_finite_number("max_tx_power", max_tx_power)

    tolerance = _validate_positive("tolerance", tolerance)
    derivative_epsilon = _validate_positive(
        "derivative_epsilon",
        derivative_epsilon,
    )
    derivative_step = _validate_positive("derivative_step", derivative_step)

    if min_tx_power >= max_tx_power:
        raise ValueError("min_tx_power must be smaller than max_tx_power.")

    if not min_tx_power <= current_power <= max_tx_power:
        raise ValueError(
            "initial_tx_power must be inside the allowed transmission-power bounds."
        )

    if max_iterations <= 0:
        raise ValueError("max_iterations must be positive.")

    return _NewtonOptimizerInputs(
        selected_frequency=selected_frequency,
        initial_tx_power=current_power,
        sinr_required=sinr_required,
        max_iterations=max_iterations,
        tolerance=tolerance,
        derivative_epsilon=derivative_epsilon,
        min_tx_power=min_tx_power,
        max_tx_power=max_tx_power,
        derivative_step=derivative_step,
    )


def _evaluate_sinr_error(
    *,
    tx_power: float,
    selected_frequency: float,
    sinr_required: float,
    context: Any,
    sinr_calculated: SinrCalculator,
) -> float:
    """Evaluate f(tx_power) = SINR(tx_power, selected_frequency) - SINR_required."""

    sinr_value = sinr_calculated(tx_power, selected_frequency, context)
    sinr_value = _require_finite_number("calculated SINR", sinr_value)
    return sinr_value - sinr_required


def _build_objective(
    *,
    inputs: _NewtonOptimizerInputs,
    context: Any,
    sinr_calculated: SinrCalculator,
) -> ObjectiveFunction:
    def objective(power: float) -> float:
        return _evaluate_sinr_error(
            tx_power=power,
            selected_frequency=inputs.selected_frequency,
            sinr_required=inputs.sinr_required,
            context=context,
            sinr_calculated=sinr_calculated,
        )

    return objective


def numerical_derivative_central_difference(
    function: ObjectiveFunction,
    x: float,
    h: float,
) -> float:
    """
    Approximate f'(x) with the central difference formula.

    f'(x) ~= (f(x + h) - f(x - h)) / (2h)
    """

    step = _require_finite_number("central-difference step", h)
    if step <= 0.0:
        raise ValueError("central-difference step must be positive.")

    f_plus = _require_finite_number("f(x + h)", function(x + step))
    f_minus = _require_finite_number("f(x - h)", function(x - step))
    return (f_plus - f_minus) / (2.0 * step)


def _central_difference_step(
    *,
    current_power: float,
    inputs: _NewtonOptimizerInputs,
) -> float:
    lower_margin = current_power - inputs.min_tx_power
    upper_margin = inputs.max_tx_power - current_power
    return min(inputs.derivative_step, lower_margin, upper_margin)


def _calculate_derivative(
    *,
    state: _NewtonIterationState,
    inputs: _NewtonOptimizerInputs,
    context: Any,
    objective: ObjectiveFunction,
    analytic_derivative: Optional[DerivativeCalculator],
) -> float:
    if analytic_derivative is not None:
        derivative = analytic_derivative(
            state.current_power,
            inputs.selected_frequency,
            context,
        )
        return _require_finite_number("analytic derivative", derivative)

    bounded_step = _central_difference_step(
        current_power=state.current_power,
        inputs=inputs,
    )
    if bounded_step <= 0.0:
        raise _CentralDerivativeStepUnavailable

    return numerical_derivative_central_difference(
        objective,
        state.current_power,
        bounded_step,
    )


def _handle_out_of_bounds_power(
    *,
    next_power: float,
    state: _NewtonIterationState,
    inputs: _NewtonOptimizerInputs,
    objective: ObjectiveFunction,
    iteration: int,
) -> NewtonRaphsonResult:
    boundary_power = _clamp(
        next_power,
        inputs.min_tx_power,
        inputs.max_tx_power,
    )

    try:
        boundary_error = objective(boundary_power)
    except ValueError:
        return _best_result(
            state=state,
            iterations=iteration,
            converged=False,
            stopping_reason=StoppingReason.INVALID_SINR_AT_POWER_BOUNDARY,
        )

    updated_state = state.with_best_candidate(boundary_power, boundary_error)
    boundary_converged = _has_converged(boundary_error, inputs.tolerance)
    stopping_reason = (
        StoppingReason.CONVERGED_AT_POWER_BOUNDARY
        if boundary_converged
        else StoppingReason.POWER_BOUNDARY_REACHED
    )

    return _best_result(
        state=updated_state,
        iterations=iteration,
        converged=boundary_converged,
        stopping_reason=stopping_reason,
    )


def optimize_tx_power_newton_raphson(
    *,
    selected_frequency: float,
    initial_tx_power: float,
    sinr_required: float,
    context: Any,
    sinr_calculated: SinrCalculator,
    max_iterations: int = 20,
    tolerance: float = 0.1,
    derivative_epsilon: float = 0.01,
    min_tx_power: float = -100.0,
    max_tx_power: float = 100.0,
    derivative_step: float = 0.1,
    analytic_derivative: Optional[DerivativeCalculator] = None,
) -> NewtonRaphsonResult:
    """
    Find the transmission power for one already-selected frequency.

    The objective is:
        f(tx_power) = sinr_calculated(tx_power, selected_frequency, context)
                      - sinr_required

    Newton-Raphson update:
        x_next = x - f(x) / f'(x)

    If no analytic derivative is supplied, f'(x) is computed by central
    difference. The optimizer never scans candidate frequencies.
    """

    if not callable(sinr_calculated):
        raise ValueError("sinr_calculated must be callable.")

    inputs = _validate_optimizer_inputs(
        selected_frequency=selected_frequency,
        initial_tx_power=initial_tx_power,
        sinr_required=sinr_required,
        max_iterations=max_iterations,
        tolerance=tolerance,
        derivative_epsilon=derivative_epsilon,
        min_tx_power=min_tx_power,
        max_tx_power=max_tx_power,
        derivative_step=derivative_step,
    )
    objective = _build_objective(
        inputs=inputs,
        context=context,
        sinr_calculated=sinr_calculated,
    )

    try:
        current_error = objective(inputs.initial_tx_power)
    except ValueError:
        return _make_result(
            optimal_tx_power=inputs.initial_tx_power,
            final_sinr_error=math.nan,
            iterations=0,
            converged=False,
            stopping_reason=StoppingReason.INVALID_SINR_AT_INITIAL_POWER,
        )

    state = _NewtonIterationState.initial(inputs.initial_tx_power, current_error)

    if _has_converged(state.current_error, inputs.tolerance):
        return _make_result(
            optimal_tx_power=state.current_power,
            final_sinr_error=state.current_error,
            iterations=0,
            converged=True,
            stopping_reason=StoppingReason.INITIAL_POWER_WITHIN_TOLERANCE,
        )

    for iteration in range(1, inputs.max_iterations + 1):
        try:
            derivative = _calculate_derivative(
                state=state,
                inputs=inputs,
                context=context,
                objective=objective,
                analytic_derivative=analytic_derivative,
            )
        except _CentralDerivativeStepUnavailable:
            return _best_result(
                state=state,
                iterations=iteration - 1,
                converged=False,
                stopping_reason=StoppingReason.BOUNDARY_PREVENTS_CENTRAL_DERIVATIVE,
            )
        except ValueError:
            return _best_result(
                state=state,
                iterations=iteration - 1,
                converged=False,
                stopping_reason=StoppingReason.INVALID_SINR_DURING_DERIVATIVE,
            )

        if _is_derivative_unstable(derivative, inputs.derivative_epsilon):
            return _best_result(
                state=state,
                iterations=iteration - 1,
                converged=False,
                stopping_reason=StoppingReason.DERIVATIVE_TOO_CLOSE_TO_ZERO,
            )

        next_power = _newton_next_power(
            state.current_power,
            state.current_error,
            derivative,
        )
        if not math.isfinite(next_power):
            return _best_result(
                state=state,
                iterations=iteration - 1,
                converged=False,
                stopping_reason=StoppingReason.INVALID_NEWTON_STEP,
            )

        if _is_outside_power_bounds(next_power, inputs):
            return _handle_out_of_bounds_power(
                next_power=next_power,
                state=state,
                inputs=inputs,
                objective=objective,
                iteration=iteration,
            )

        try:
            next_error = objective(next_power)
        except ValueError:
            return _best_result(
                state=state,
                iterations=iteration,
                converged=False,
                stopping_reason=StoppingReason.INVALID_SINR_AFTER_NEWTON_STEP,
            )

        state = state.with_current(next_power, next_error)
        state = state.with_best_candidate(next_power, next_error)

        if _has_converged(state.current_error, inputs.tolerance):
            return _make_result(
                optimal_tx_power=state.current_power,
                final_sinr_error=state.current_error,
                iterations=iteration,
                converged=True,
                stopping_reason=StoppingReason.CONVERGED,
            )

    return _best_result(
        state=state,
        iterations=inputs.max_iterations,
        converged=False,
        stopping_reason=StoppingReason.MAX_ITERATIONS_REACHED,
    )


def initial_guess_tx_power_dbm(
    platform: Platform,
    path_loss_db: float,
    interference_mw: float,
    sinr_required_db: float,
) -> float:
    noise_mw = dbm_to_mw(noise_floor_dbm(platform))
    denom_mw = clamp_positive(float(interference_mw) + float(noise_mw), 1e-12)
    denom_dbm = mw_to_dbm(denom_mw)

    return (
        float(sinr_required_db)
        + float(denom_dbm)
        - float(platform.tx_gain)
        - float(platform.rx_gain)
        + float(path_loss_db)
    )


def _fixed_frequency_sinr_db(
    tx_power: float,
    selected_frequency: float,
    context: FixedFrequencySinrContext,
) -> float:
    """Existing SINR model adapted to the generic fixed-frequency optimizer."""

    _ = selected_frequency
    return sinr_db(
        p_tx_dbm=tx_power,
        platform=context.platform,
        path_loss_db=context.path_loss_db,
        interference_mw=context.interference_mw,
    )


def solve_tx_power_newton_raphson(
    platform: Platform,
    path_loss_db: float,
    interference_mw: float,
    sinr_required_db: float,
    config: Optional[NewtonConfig] = None,
    ptx0_dbm: Optional[float] = None,
    selected_frequency: Optional[float] = None,
    return_result: bool = False,
) -> float | NewtonRaphsonResult:
    """
    Compatibility wrapper for the service layer.

    The service has already chosen one frequency and calculated its path loss
    and interference. This wrapper optimizes only transmission power.
    """

    cfg = config or NewtonConfig()

    initial_power = (
        float(ptx0_dbm)
        if ptx0_dbm is not None
        else initial_guess_tx_power_dbm(
            platform=platform,
            path_loss_db=path_loss_db,
            interference_mw=interference_mw,
            sinr_required_db=sinr_required_db,
        )
    )

    initial_power = _clamp(initial_power, cfg.ptx_min_dbm, cfg.ptx_max_dbm)
    if selected_frequency is None:
        raise ValueError(
            "selected_frequency is required because the frequency must already be selected."
        )
    context = FixedFrequencySinrContext(
        platform=platform,
        path_loss_db=float(path_loss_db),
        interference_mw=float(interference_mw),
    )

    result = optimize_tx_power_newton_raphson(
        selected_frequency=selected_frequency,
        initial_tx_power=initial_power,
        sinr_required=float(sinr_required_db),
        context=context,
        sinr_calculated=_fixed_frequency_sinr_db,
        max_iterations=cfg.max_iter,
        tolerance=cfg.tol_db,
        derivative_epsilon=cfg.derivative_epsilon,
        min_tx_power=cfg.ptx_min_dbm,
        max_tx_power=cfg.ptx_max_dbm,
        derivative_step=cfg.numeric_derivative_step_db,
    )

    if return_result:
        return result

    if not result.converged:
        raise NewtonRaphsonError(
            "Newton-Raphson did not converge. "
            f"reason={result.stopping_reason}, "
            f"best_tx_power={result.optimal_tx_power:.6f}, "
            f"final_sinr_error={result.final_sinr_error:.6f}, "
            f"iterations={result.iterations}"
        )

    return result.optimal_tx_power


# Example for the generic academic solver:
#
# result = optimize_tx_power_newton_raphson(
#     selected_frequency=2500.0,
#     initial_tx_power=10.0,
#     sinr_required=12.0,
#     context=my_mission_context,
#     sinr_calculated=my_sinr_calculated,
#     max_iterations=20,C
#     tolerance=0.1,
#     derivative_epsilon=0.01,
#     min_tx_power=-100.0,
#     max_tx_power=100.0,
# )
# print(result.to_dict())
