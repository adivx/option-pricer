# Changelog

## 0.1.1 — 2026-08-06

- Test suite: 15 unittests across normal functions, pricing, and Greeks
  (known values, put-call parity, bounds, symmetry, input validation).
- CI on Python 3.9 / 3.11 / 3.12.
- README badges: build status, license, last commit, repo size.
- Contributing guide for new contributors.

## 0.1.0 — 2026-08-02

- Pure-stdlib Black-Scholes pricer: closed-form call/put prices.
- Full Greeks: delta, gamma, theta, vega, rho — both raw and per-contract scaled.
- CLI for one-shot quotes, interactive prompts, and a `--scan` sensitivity table.
