"""Unit tests for the friendly input model (time/rate/vol parsing)."""

import unittest

from pricer.models import parse_rate_or_vol, parse_time


class TestParseTime(unittest.TestCase):
    def test_bare_number_is_years(self):
        self.assertAlmostEqual(parse_time("0.5"), 0.5)
        self.assertAlmostEqual(parse_time("1"), 1.0)

    def test_day_suffix(self):
        # 90 days out of a 365.25-day year.
        self.assertAlmostEqual(parse_time("90d"), 90 / 365.25)

    def test_week_suffix(self):
        self.assertAlmostEqual(parse_time("2w"), 14 / 365.25)

    def test_month_suffix(self):
        # 3 months of 30.4375 days lands exactly on a quarter-year.
        self.assertAlmostEqual(parse_time("3m"), 0.25)

    def test_year_suffix(self):
        self.assertAlmostEqual(parse_time("1y"), 1.0)

    def test_case_and_whitespace_insensitive(self):
        self.assertAlmostEqual(parse_time(" 90D "), 90 / 365.25)

    def test_invalid_time_raises(self):
        for bad in ("abc", "90z", "", "--"):
            with self.assertRaises(ValueError):
                parse_time(bad)


class TestParseRateOrVol(unittest.TestCase):
    def test_decimal(self):
        self.assertAlmostEqual(parse_rate_or_vol("0.05"), 0.05)

    def test_percent(self):
        self.assertAlmostEqual(parse_rate_or_vol("5%"), 0.05)
        self.assertAlmostEqual(parse_rate_or_vol("20%"), 0.20)

    def test_whitespace(self):
        self.assertAlmostEqual(parse_rate_or_vol(" 5% "), 0.05)

    def test_invalid_raises(self):
        for bad in ("five", "%", "5%%"):
            with self.assertRaises(ValueError):
                parse_rate_or_vol(bad)


if __name__ == "__main__":
    unittest.main()
