"""Black-Scholes European option pricing and Greeks.

Pure standard-library implementation: the normal CDF is computed with
``math.erf``, so there are no compiled dependencies.

Conventions:
  * ``t`` (time to expiry) is always in YEARS.
  * Rates and vols are always DECIMALS (``r=0.05``, ``sigma=0.20``). The CLI
    layer handles % <-> decimal conversion for humans.
  * ``theta`` is reported per calendar day (raw per-year value / 365).
  * ``vega``  is reported per 1 vol point (raw value / 100).
  * ``rho``   is reported per 1% move in the rate (raw value / 100).
"""

import math

_SQRT_2PI = math.sqrt(2.0 * math.pi)


def norm_pdf(x: float) -> float:
    """Standard normal probability density function phi(x)."""
    return math.exp(-0.5 * x * x) / _SQRT_2PI


def norm_cdf(x: float) -> float:
    """Standard normal cumulative distribution function N(x), via erf."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _validate(spot: float, strike: float, t: float, r: float, sigma: float) -> None:
    if spot <= 0:
        raise ValueError("spot must be > 0")
    if strike <= 0:
        raise ValueError("strike must be > 0")
    if t <= 0:
        raise ValueError("time to expiry must be > 0")
    if sigma <= 0:
        raise ValueError("volatility must be > 0")


def d1_d2(spot: float, strike: float, t: float, r: float, sigma: float):
    """Black-Scholes d1/d2. Returns ``(d1, d2)``."""
    _validate(spot, strike, t, r, sigma)
    sqrt_t = math.sqrt(t)
    d1 = (math.log(spot / strike) + (r + 0.5 * sigma * sigma) * t) / (sigma * sqrt_t)
    return d1, d1 - sigma * sqrt_t


def price(
    spot: float,
    strike: float,
    t: float,
    r: float,
    sigma: float,
    option_type: str = "call",
) -> float:
    """European call/put price under Black-Scholes."""
    d1, d2 = d1_d2(spot, strike, t, r, sigma)
    disc = math.exp(-r * t)
    if option_type == "call":
        return spot * norm_cdf(d1) - strike * disc * norm_cdf(d2)
    if option_type == "put":
        return strike * disc * norm_cdf(-d2) - spot * norm_cdf(-d1)
    raise ValueError("option_type must be 'call' or 'put'")


def greeks(spot: float, strike: float, t: float, r: float, sigma: float) -> dict:
    """All first- and second-order Greeks.

    Keys carry market conventions baked in: theta per calendar day, vega per
    1 vol point, rho per 1% rate move. Raw per-year / per-100%-values are kept
    under ``*_raw``.
    """
    d1, d2 = d1_d2(spot, strike, t, r, sigma)
    pdf = norm_pdf(d1)
    sqrt_t = math.sqrt(t)
    disc = math.exp(-r * t)

    delta_call = norm_cdf(d1)
    delta_put = delta_call - 1.0
    gamma = pdf / (spot * sigma * sqrt_t)

    vega_raw = spot * pdf * sqrt_t          # P&L per +1.0 in sigma
    theta_first = -(spot * pdf * sigma) / (2 * sqrt_t)  # shared first term

    theta_call_raw = theta_first - r * strike * disc * norm_cdf(d2)
    theta_put_raw = theta_first + r * strike * disc * norm_cdf(-d2)

    rho_call_raw = strike * t * disc * norm_cdf(d2)
    rho_put_raw = -strike * t * disc * norm_cdf(-d2)

    return {
        "delta_call": delta_call,
        "delta_put": delta_put,
        "gamma": gamma,
        "vega": vega_raw / 100.0,
        "vega_raw": vega_raw,
        "theta_call": theta_call_raw / 365.0,
        "theta_put": theta_put_raw / 365.0,
        "theta_call_raw": theta_call_raw,
        "theta_put_raw": theta_put_raw,
        "rho_call": rho_call_raw / 100.0,
        "rho_put": rho_put_raw / 100.0,
        "rho_call_raw": rho_call_raw,
        "rho_put_raw": rho_put_raw,
    }


def parity_residual(spot: float, strike: float, t: float, r: float, call: float, put: float) -> float:
    """Put-call parity check: C - P - (S - K*e^-rT) should be ~0."""
    return call - put - (spot - strike * math.exp(-r * t))
