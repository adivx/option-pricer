"""Smoke tests for the CLI wiring (parse → resolve → render)."""

import io
import unittest
from contextlib import redirect_stdout

from pricer.cli import build_arg_parser, main

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
