import math

from config.settings import ContinuousMappingConfig


def linear_map(value: float, lower: float, upper: float, max_bonus: float, max_penalty: float, coefficient: float = 1.0) -> float:
    if upper <= lower:
        return 0.0
    if value < lower:
        ratio = (lower - value) / (upper - lower)
        return -max_penalty * min(ratio * coefficient, 1.0)
    if value > upper:
        return max_bonus
    ratio = (value - lower) / (upper - lower)
    return max_bonus * min(ratio * coefficient, 1.0)


def sigmoid_map(value: float, lower: float, upper: float, max_bonus: float, max_penalty: float, coefficient: float = 1.0) -> float:
    if upper <= lower:
        return 0.0
    mid = (lower + upper) / 2.0
    span = (upper - lower) / 2.0
    if span == 0:
        return 0.0
    x = (value - mid) / span * coefficient
    x = max(-20.0, min(20.0, x))
    sigmoid_val = 1.0 / (1.0 + math.exp(-x))
    result = (sigmoid_val - 0.5) * 2.0 * max_bonus
    if result > max_bonus:
        result = max_bonus
    if result < -max_penalty:
        result = -max_penalty
    return result


def tanh_map(value: float, lower: float, upper: float, max_bonus: float, max_penalty: float, coefficient: float = 1.0) -> float:
    if upper <= lower:
        return 0.0
    mid = (lower + upper) / 2.0
    span = (upper - lower) / 2.0
    if span == 0:
        return 0.0
    x = (value - mid) / span * coefficient
    x = max(-20.0, min(20.0, x))
    tanh_val = math.tanh(x)
    result = tanh_val * max_bonus
    if result > max_bonus:
        result = max_bonus
    if result < -max_penalty:
        result = -max_penalty
    return result


def apply_mapping(value: float, config: ContinuousMappingConfig) -> float:
    if math.isnan(value) or math.isinf(value):
        return 0.0
    func_map = {
        "linear": linear_map,
        "sigmoid": sigmoid_map,
        "tanh": tanh_map,
    }
    func = func_map.get(config.func_type, linear_map)
    return func(
        value,
        config.lower_bound,
        config.upper_bound,
        config.max_bonus,
        config.max_penalty,
        config.coefficient,
    )


def normalize_to_range(value: float, old_lower: float, old_upper: float, new_lower: float, new_upper: float) -> float:
    if old_upper <= old_lower:
        return (new_lower + new_upper) / 2.0
    ratio = (value - old_lower) / (old_upper - old_lower)
    ratio = max(0.0, min(1.0, ratio))
    return new_lower + ratio * (new_upper - new_lower)
