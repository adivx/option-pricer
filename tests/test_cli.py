"""Smoke tests for the CLI wiring (parse → resolve → render)."""

import io
import unittest
from contextlib import redirect_stdout

from pricer.cli import _join_negative_percent, build_arg_parser, main

BASIC = ["--spot", "100", "--strike", "105", "--t", "90d",
         "--r", "5%", "--vol", "20%"]


class TestQuote(unittest.TestCase):
    def test_quote_renders_call_and_put(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            main(BASIC)
        out = buf.getvalue()
        self.assertIn("Call", out)
        self.assertIn("Put", out)

    def test_quote_prints_prices(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            main(BASIC)
        self.assertIn("$", buf.getvalue())

    def test_scan_table_renders(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            main(BASIC + ["--scan", "vol"])
        self.assertIn("Vol", buf.getvalue())

    def test_iv_flag_solves_for_vol(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            main(["--spot", "100", "--strike", "100", "--t", "1y",
                  "--r", "5%", "--vol", "20%", "--iv", "10.4505835722"])
        out = buf.getvalue()
        self.assertIn("Implied vol", out)
        self.assertIn("20.00%", out)


class TestErrors(unittest.TestCase):
    def test_bad_time_exits_2(self):
        with self.assertRaises(SystemExit) as ctx:
            main(["--spot", "100", "--strike", "105", "--t", "nonsense",
                  "--r", "0.05", "--vol", "0.2"])
        self.assertEqual(ctx.exception.code, 2)

    def test_bad_rate_exits_2(self):
        with self.assertRaises(SystemExit) as ctx:
            main(["--spot", "100", "--strike", "105", "--t", "1y",
                  "--r", "five", "--vol", "0.2"])
        self.assertEqual(ctx.exception.code, 2)


class TestNegativePercent(unittest.TestCase):
    def test_space_form_negative_rate_parses(self):
        # argparse rejects " --r -5%" as an unknown flag; the preprocessor
        # rewrites it to "--r=-5%" so negative rates stay usable.
        buf = io.StringIO()
        with redirect_stdout(buf):
            main(["--spot", "100", "--strike", "105", "--t", "90d",
                  "--r", "-5%", "--vol", "20%"])
        self.assertIn("Call", buf.getvalue())

    def test_join_rewrites_space_form(self):
        self.assertEqual(_join_negative_percent(["--r", "-5%"]), ["--r=-5%"])
        self.assertEqual(_join_negative_percent(["--vol", "-20%"]), ["--vol=-20%"])

    def test_join_leaves_other_tokens_alone(self):
        self.assertEqual(_join_negative_percent(["--spot", "100"]), ["--spot", "100"])
        self.assertEqual(_join_negative_percent(["--r=-5%"]), ["--r=-5%"])


class TestOverflow(unittest.TestCase):
    def test_huge_expiry_exits_2_not_traceback(self):
        # r=-50%, t=10000y makes exp(-r*t) = exp(5000) overflow float; the CLI
        # must surface a clean error instead of a raw traceback.
        with self.assertRaises(SystemExit) as ctx:
            main(["--spot", "100", "--strike", "105", "--t", "10000y",
                  "--r", "-50%", "--vol", "20%"])
        self.assertEqual(ctx.exception.code, 2)


class TestArgParser(unittest.TestCase):
    def test_version_flag(self):
        with self.assertRaises(SystemExit) as ctx:
            build_arg_parser().parse_args(["--version"])
        self.assertEqual(ctx.exception.code, 0)

    def test_scan_choices(self):
        for axis in ("spot", "vol", "time"):
            args = build_arg_parser().parse_args(BASIC + ["--scan", axis])
            self.assertEqual(args.scan, axis)


if __name__ == "__main__":
    unittest.main()
