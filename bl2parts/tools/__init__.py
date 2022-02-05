import math as maths
from typing import Any, Dict

YAML = Dict[str, Any]


def float_error(val: float) -> float:
    # Hacky way to deal with precision
    round_decimals = 5
    if val != 0:
        digits = maths.log10(abs(val))
        if digits < 0:
            round_decimals += -int(digits)

    rounded = round(val, round_decimals)

    if int(rounded) == rounded:
        return int(rounded)
    return rounded
