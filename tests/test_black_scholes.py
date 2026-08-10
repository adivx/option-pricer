"""Unit tests for the pure-stdlib Black-Scholes implementation."""

import math
import unittest

from pricer.black_scholes import (
    d1_d2,
    greeks,
    implied_vol,
    norm_cdf,
    norm_pdf,
    parity_residual,
    price,
)


class TestNormalFunctions(unittest.TestCase):
    def test_pdf_at_zero(self):
        # phi(0) = 1 / sqrt(2*pi)
        self.assertAlmostEqual(norm_pdf(0.0), 1.0 / math.sqrt(2.0 * math.pi), places=12)

    def test_cdf_at_zero(self):
        self.assertAlmostEqual(norm_cdf(0.0), 0.5, places=12)

    def test_cdf_symmetry(self):
        for x in (0.5, 1.0, 2.0):
            self.assertAlmostEqual(norm_cdf(-x), 1.0 - norm_cdf(x), places=12)

    def test_cdf_tails(self):
        self.assertAlmostEqual(norm_cdf(-10.0), 0.0, places=10)
        self.assertAlmostEqual(norm_cdf(10.0), 1.0, places=10)


class TestPricing(unittest.TestCase):
    # Classic textbook case: S=K=100, r=5%, sigma=20%, T=1y.
    S, K, T, R, SIG = 100.0, 100.0, 1.0, 0.05, 0.20

    def test_known_call_price(self):
        # Reference value from the standard closed form.
        c = price(self.S, self.K, self.T, self.R, self.SIG, "call")
        self.assertAlmostEqual(c, 10.4505835722, places=6)

    def test_put_from_parity(self):
        c = price(self.S, self.K, self.T, self.R, self.SIG, "call")
        p = price(self.S, self.K, self.T, self.R, self.SIG, "put")
        expected_p = c - self.S + self.K * math.exp(-self.R * self.T)
        self.assertAlmostEqual(p, expected_p, places=10)

    def test_parity_residual_is_zero(self):
        c = price(self.S, self.K, self.T, self.R, self.SIG, "call")
        p = price(self.S, self.K, self.T, self.R, self.SIG, "put")
        self.assertAlmostEqual(parity_residual(self.S, self.K, self.T, self.R, c, p), 0.0, places=10)

    def test_deep_itm_call_trades_at_intrinsic(self):
        c = price(200.0, 100.0, 0.01, 0.0, 0.10, "call")
        self.assertAlmostEqual(c, 100.0, places=2)

    def test_call_lower_bound(self):
        # C >= S - K*exp(-rT)
        c = price(self.S, self.K, self.T, self.R, self.SIG, "call")
        self.assertGreaterEqual(c, self.S - self.K * math.exp(-self.R * self.T))

    def test_invalid_inputs_raise(self):
        with self.assertRaises(ValueError):
            price(0.0, self.K, self.T, self.R, self.SIG, "call")
        with self.assertRaises(ValueError):
            price(self.S, -1.0, self.T, self.R, self.SIG, "call")
        with self.assertRaises(ValueError):
            price(self.S, self.K, 0.0, self.R, self.SIG, "call")
        with self.assertRaises(ValueError):
            price(self.S, self.K, self.T, self.R, 0.0, "call")
        with self.assertRaises(ValueError):
            price(self.S, self.K, self.T, self.R, self.SIG, "straddle")


class TestGreeks(unittest.TestCase):
    S, K, T, R, SIG = 100.0, 100.0, 1.0, 0.05, 0.20

    def test_delta_bounds(self):
        g = greeks(self.S, self.K, self.T, self.R, self.SIG)
        self.assertGreater(g["delta_call"], 0.0)
        self.assertLess(g["delta_call"], 1.0)
        self.assertAlmostEqual(g["delta_put"], g["delta_call"] - 1.0, places=12)

    def test_gamma_positive(self):
        g = greeks(self.S, self.K, self.T, self.R, self.SIG)
        self.assertGreater(g["gamma"], 0.0)

    def test_atm_delta_matches_analytic(self):
        # With S=K=100, r=5%, sigma=20%, T=1y: d1 = (0.05+0.02)/0.20 = 0.35,
        # so delta_call = N(0.35) = 0.6368306511756191 (carry lifts it off 0.5).
        g = greeks(self.S, self.K, self.T, self.R, self.SIG)
        self.assertAlmostEqual(g["delta_call"], 0.6368306511756191, places=10)

    def test_theta_and_vega_are_scaled(self):
        g = greeks(self.S, self.K, self.T, self.R, self.SIG)
        self.assertAlmostEqual(g["theta_call"] * 365.0, g["theta_call_raw"], places=9)
        self.assertAlmostEqual(g["vega"] * 100.0, g["vega_raw"], places=9)

    def test_p_itm_complements(self):
        g = greeks(self.S, self.K, self.T, self.R, self.SIG)
        self.assertAlmostEqual(g["p_itm_call"] + g["p_itm_put"], 1.0, places=12)

    def test_p_itm_equals_n_of_d2(self):
        _, d2 = d1_d2(self.S, self.K, self.T, self.R, self.SIG)
        g = greeks(self.S, self.K, self.T, self.R, self.SIG)
        self.assertAlmostEqual(g["p_itm_call"], norm_cdf(d2), places=12)

    def test_deep_itm_call_probability_high(self):
        g = greeks(200.0, 100.0, 1.0, 0.05, 0.20)
        self.assertGreater(g["p_itm_call"], 0.9)

    def test_deep_otm_call_probability_low(self):
        g = greeks(100.0, 200.0, 1.0, 0.05, 0.20)
        self.assertLess(g["p_itm_call"], 0.1)

    def test_d1_d2_relation(self):
        d1, d2 = d1_d2(self.S, self.K, self.T, self.R, self.SIG)
        self.assertAlmostEqual(d2, d1 - self.SIG * math.sqrt(self.T), places=12)


class TestGreeksFiniteDiff(unittest.TestCase):
    """Cross-check the closed-form Greeks against numeric central differences.

    h=1e-5 gives O(h^2) central-difference error, so agreement to ~6 places
    means the analytic formulas (and their market scalings) are right.
    """
    S, K, T, R, SIG = 100.0, 105.0, 0.5, 0.04, 0.25
    H = 1e-5

    def _c(self, **kw):
        p = dict(spot=self.S, strike=self.K, t=self.T, r=self.R, sigma=self.SIG)
        p.update(kw)
        return price(**p, option_type="call")

    def test_delta_call_matches_central_difference(self):
        d = (self._c(spot=self.S + self.H) - self._c(spot=self.S - self.H)) / (2 * self.H)
        self.assertAlmostEqual(greeks(self.S, self.K, self.T, self.R, self.SIG)["delta_call"], d, places=6)

    def test_delta_put_matches_central_difference(self):
        p_plus = price(self.S + self.H, self.K, self.T, self.R, self.SIG, "put")
        p_minus = price(self.S - self.H, self.K, self.T, self.R, self.SIG, "put")
        d = (p_plus - p_minus) / (2 * self.H)
        self.assertAlmostEqual(greeks(self.S, self.K, self.T, self.R, self.SIG)["delta_put"], d, places=6)

    def test_gamma_matches_delta_difference(self):
        # Second difference of prices suffers cancellation in double precision;
        # differencing delta (a first difference of a smooth function) is stable.
        d_up = greeks(self.S + self.H, self.K, self.T, self.R, self.SIG)["delta_call"]
        d_dn = greeks(self.S - self.H, self.K, self.T, self.R, self.SIG)["delta_call"]
        g = (d_up - d_dn) / (2 * self.H)
        self.assertAlmostEqual(greeks(self.S, self.K, self.T, self.R, self.SIG)["gamma"], g, places=6)

    def test_vega_raw_matches_central_difference(self):
        # vega_raw is dC/d(sigma) at full scale; vega is that /100.
        v = (self._c(sigma=self.SIG + self.H) - self._c(sigma=self.SIG - self.H)) / (2 * self.H)
        self.assertAlmostEqual(greeks(self.S, self.K, self.T, self.R, self.SIG)["vega_raw"], v, places=6)

    def test_theta_call_raw_matches_central_difference(self):
        # Finite difference in remaining time gives +dC/dT (more time -> more
        # value), but the analytic theta is the calendar-time decay, i.e. the
        # negative of that. theta_call is the raw per-year value / 365.
        th = -(self._c(t=self.T + self.H) - self._c(t=self.T - self.H)) / (2 * self.H)
        self.assertAlmostEqual(greeks(self.S, self.K, self.T, self.R, self.SIG)["theta_call_raw"], th, places=6)

    def test_rho_call_raw_matches_central_difference(self):
        # rho is dC/dr; rho_call is that /100 (per 1% move).
        rho = (self._c(r=self.R + self.H) - self._c(r=self.R - self.H)) / (2 * self.H)
        self.assertAlmostEqual(greeks(self.S, self.K, self.T, self.R, self.SIG)["rho_call_raw"], rho, places=6)

    def test_rho_put_raw_matches_central_difference(self):
        p_plus = price(self.S, self.K, self.T, self.R + self.H, self.SIG, "put")
        p_minus = price(self.S, self.K, self.T, self.R - self.H, self.SIG, "put")
        rho = (p_plus - p_minus) / (2 * self.H)
        self.assertAlmostEqual(greeks(self.S, self.K, self.T, self.R, self.SIG)["rho_put_raw"], rho, places=6)

    def test_market_scalings_consistent(self):
        g = greeks(self.S, self.K, self.T, self.R, self.SIG)
        self.assertAlmostEqual(g["vega"] * 100.0, g["vega_raw"], places=12)
        self.assertAlmostEqual(g["theta_call"] * 365.0, g["theta_call_raw"], places=12)
        self.assertAlmostEqual(g["rho_call"] * 100.0, g["rho_call_raw"], places=12)
        self.assertAlmostEqual(g["rho_put"] * 100.0, g["rho_put_raw"], places=12)


class TestImpliedVol(unittest.TestCase):
    S, K, T, R, SIG = 100.0, 100.0, 1.0, 0.05, 0.20

    def test_recovers_known_call_vol(self):
        c = price(self.S, self.K, self.T, self.R, self.SIG, "call")
        iv = implied_vol(self.S, self.K, self.T, self.R, c, "call")
        self.assertAlmostEqual(iv, self.SIG, places=6)

    def test_recovers_known_put_vol(self):
        p = price(self.S, self.K, self.T, self.R, self.SIG, "put")
        iv = implied_vol(self.S, self.K, self.T, self.R, p, "put")
        self.assertAlmostEqual(iv, self.SIG, places=6)

    def test_monotonic_in_market_price(self):
        lo_iv = implied_vol(self.S, self.K, self.T, self.R, 10.0, "call")
        hi_iv = implied_vol(self.S, self.K, self.T, self.R, 15.0, "call")
        self.assertGreater(hi_iv, lo_iv)

    def test_below_no_arbitrage_bound_raises(self):
        # S=100, K=90, r=0: the call cannot trade below its intrinsic 10.
        with self.assertRaises(ValueError):
            implied_vol(100.0, 90.0, 1.0, 0.0, 5.0, "call")


if __name__ == "__main__":
    unittest.main()
