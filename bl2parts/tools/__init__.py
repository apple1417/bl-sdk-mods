from typing import Any, Dict

YAML = Dict[str, Any]


def float_error(val: float) -> float:
    rounded = round(val, 5)
    if int(rounded) == rounded:
        return int(rounded)
    return rounded
