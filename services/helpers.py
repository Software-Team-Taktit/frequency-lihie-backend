import math

def clamp_positive(x: float, min_value: float) -> float:
    """Ensures x is at least min_val (prevents log10(0)) and negative values"""
    return x if x >= min_value else min_value