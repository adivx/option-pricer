"""Input model and friendly parsing for the CLI."""

import re
from dataclasses import dataclass

_DAYS_PER_YEAR = 365.25
_UNIT_DAYS = {"d": 1.0, "w": 7.0, "m": 30.4375, "y": _DAYS_PER_YEAR}


def parse_time(value: str) -> float:
    """Parse a time-to-expiry into years.

    Accepts a unit suffix (``d``/``w``/``m``/``y``) or a bare number, which is
    taken as YEARS (the standard Black-Scholes unit).

        parse_time("0.5")  -> 0.5        (6 months)
        parse_time("90d")  -> ~0.246
        parse_time("2w")   -> ~0.038
        parse_time("3m")   -> ~0.25
    """
    match = re.fullmatch(r"\s*([0-9]*\.?[0-9]+)\s*([dwmy]?)\s*", str(value).strip().lower())
    if not match:
        raise ValueError(f"cannot parse time-to-expiry: {value!r}")
    number, unit = float(match.group(1)), match.group(2)
    if not unit:
        return number
    return number * _UNIT_DAYS[unit] / _DAYS_PER_YEAR


def parse_rate_or_vol(value: str) -> float:
    """Decimal value; accepts a ``%`` suffix as shorthand.

        parse_rate_or_vol("0.05") -> 0.05
        parse_rate_or_vol("5%")   -> 0.05
    """
    text = value.strip()
    if text.endswith("%"):
        return float(text[:-1]) / 100.0
    return float(text)


@dataclass
class OptionParams:
    spot: float
    strike: float
    t: float      # years
    r: float      # decimal
    sigma: float  # decimal
