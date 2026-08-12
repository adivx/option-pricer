# option-pricer
<p align="center">
  <a href="https://github.com/adivx/option-pricer/actions"><img src="https://img.shields.io/github/actions/workflow/status/adivx/option-pricer/ci.yml?branch=main&label=CI&logo=github" /></a>
  <img src="https://img.shields.io/github/license/adivx/option-pricer" />
  <img src="https://img.shields.io/github/last-commit/adivx/option-pricer" />
  <img src="https://img.shields.io/github/repo-size/adivx/option-pricer" />
</p>



A zero-compiled-deps **Black-Scholes option pricer** with full **Greeks**, shipped as a pretty terminal CLI. Type a few numbers — get call/put prices, delta/gamma/vega/theta/rho, and a sensitivity scan — without a single API key.

```
$ option-pricer --spot 100 --strike 105 --t 90d --r 5% --vol 20%

          Inputs
┌───────┬─────────────────┐
│Spot   │ 100.00          │
│Strike │ 105.00          │
│Expiry │ 3.0m  (0.2464 y)│
│Rate   │ 5.00%           │
│Vol    │ 20.00%          │
└───────┴─────────────────┘
                      Black-Scholes Valuation
╭──────┬───────┬─────────┬────────┬─────────┬───────────┬─────────╮
│ Side │ Price │   Delta │  Gamma │    Vega │ Theta/day │     Rho │
├──────┼───────┼─────────┼────────┼─────────┼───────────┼─────────┤
│ Call │ $2.44 │ +0.3754 │ 0.0382 │ +0.1883 │   -0.0257 │ +0.0865 │
│ Put  │ $6.16 │ -0.6246 │ 0.0382 │ +0.1883 │   -0.0115 │ -0.1691 │
╰──────┴───────┴─────────┴────────┴─────────┴───────────┴─────────╯
Put-call parity check:  C − P − (S − K·e⁻ʳᵀ) = +0.00e+00
```

## Features

- **European call & put pricing** under Black-Scholes — pure `stdlib` math (`math.erf`), zero compiled dependencies
- **Full Greeks**: delta, gamma, vega, theta, rho — each verified against finite-difference numerics
- **Put-call parity check** (`C − P − (S − K·e⁻ʳᵀ) = 0`) as a built-in correctness gate
- **Three interfaces**: one-shot flags, an interactive prompt, and a `--scan` sensitivity table
- **Human-friendly inputs**: `--t 90d`, `--r 5%` or `0.05`, `--vol 20%` or `0.2`
- Friendly Greek intuition printed with every quote

## Install

Requires Python 3.9+.

```bash
git clone https://github.com/adivx/option-pricer.git
cd option-pricer
pip install -e .          # installs the `option-pricer` command
```

## Usage

```bash
# One-shot quote
option-pricer --spot 100 --strike 105 --t 90d --r 5% --vol 20%

# NIFTY-style example, spot sensitivity table
option-pricer --spot 5400 --strike 5500 --t 0.25 --r 6.5% --vol 14% --scan spot

# Solve for the implied vol that prices the market quote
option-pricer --spot 100 --strike 105 --t 90d --r 5% --vol 20% --iv 3.5

# Run without flags → interactive prompt
option-pricer
```

| Flag | Meaning | Examples |
|------|---------|----------|
| `--spot S` | Underlying price | `100`, `5400` |
| `--strike K` | Strike price | `105`, `5500` |
| `--t T` | Time to expiry | `0.5` (years), `90d`, `3m`, `1y` |
| `--r R` | Risk-free rate | `0.05` or `5%` |
| `--vol V` | Implied volatility | `0.2` or `20%` |
| `--scan {spot,vol,time}` | Sensitivity table instead of a quote | `--scan vol` |
| `--iv PRICE` | Invert a market price for implied vol (with spot/strike/t/r) | `--iv 3.5` |

## The math

Under Black-Scholes the price of a European option on a non-dividend-paying asset is

$$C = S\,N(d_1) - K e^{-rT} N(d_2)$$
$$P = K e^{-rT} N(-d_2) - S\,N(-d_1)$$

where

$$d_1 = \frac{\ln(S/K) + \left(r + \frac{1}{2}\sigma^2\right)T}{\sigma\sqrt{T}}, \qquad d_2 = d_1 - \sigma\sqrt{T}$$

and the Greeks:

| Greek | Call | Put |
|-------|------|-----|
| **Δ (delta)** | $N(d_1)$ | $N(d_1) - 1$ |
| **Γ (gamma)** | $\dfrac{\varphi(d_1)}{S\sigma\sqrt{T}}$ (same for both) | |
| **V (vega)** | $S\,\varphi(d_1)\sqrt{T}$ (same for both) | |
| **Θ (theta)** | $-\dfrac{S\varphi(d_1)\sigma}{2\sqrt{T}} - rKe^{-rT}N(d_2)$ | $-\dfrac{S\varphi(d_1)\sigma}{2\sqrt{T}} + rKe^{-rT}N(-d_2)$ |
| **ρ (rho)** | $KTe^{-rT}N(d_2)$ | $-KTe^{-rT}N(-d_2)$ |

with $N(x)$ the standard normal CDF (computed via $\mathrm{erf}$) and $\varphi(x)$ its PDF.

**Display conventions** (standard market practice):
- **Theta** is per *calendar day* (raw per-year value ÷ 365)
- **Vega** is per *1 vol point* (raw per-100%-value ÷ 100)
- **Rho** is per *1% move in the rate* (raw value ÷ 100)

## Structure

```
pricer/
├── black_scholes.py   # pricing + Greeks, pure stdlib math
├── models.py          # input parsing: "90d", "3m", "5%", "0.05"
├── cli.py             # rich CLI: quote, scan, interactive
└── __main__.py        # enables python -m pricer
```

## Roadmap

- [x] Implied-volatility solver (bisection, `--iv`) → next: a vol smile
- [ ] Binomial/trinomial tree for **American** options (early-exercise + dividends)
- [ ] yfinance integration to price real strikes and build a live surface
- [ ] Plot Greeks across spot/vol in the terminal

## Disclaimer

Educational tool for learning the mechanics of derivatives pricing. Not investment advice.

## License

MIT
