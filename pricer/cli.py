"""Rich CLI: price an option and print a valuation table with full Greeks.

Run ``python -m pricer`` for the interactive prompt, or pass flags for a
one-shot quote:

    python -m pricer --spot 100 --strike 105 --t 90d --r 5% --vol 20%
    python -m pricer --spot 5400 --strike 5500 --t 0.25 --r 6.5% --vol 14% --scan spot
"""

import argparse

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from . import __version__
from .black_scholes import greeks, implied_vol, parity_residual, price
from .models import OptionParams, parse_rate_or_vol, parse_time

console = Console()

DEFAULTS = OptionParams(spot=100.0, strike=105.0, t=parse_time("90d"), r=0.05, sigma=0.20)

_INTUITION = [
    ("Delta", "directional exposure — option P&L per $1 move in the stock"),
    ("Gamma", "convexity — how fast delta changes; peaks near the money, decays as t -> 0"),
    ("Vega", "sensitivity to implied vol — P&L per +1 vol point; highest near the money"),
    ("Theta", "time decay per day — typically negative for long options, positive for short"),
    ("Rho", "sensitivity to a 1% move in the risk-free rate; tiny for short expiries"),
]


def _human_time(t: float) -> str:
    days = t * 365.25
    if days < 1:
        return f"{days * 24:.0f}h"
    if days < 60:
        return f"{days:.0f}d"
    if days < 730:
        return f"{days / 30.4375:.1f}m"
    return f"{t:.2f}y"


def _ask_float(label: str, default: float) -> float:
    raw = Prompt.ask(label, default=str(default), console=console)
    try:
        return float(raw)
    except ValueError:
        console.print(f"[red]Invalid number:[/] {raw!r}")
        return _ask_float(label, default)


def _resolve_params(args) -> OptionParams:
    if args.spot is not None and args.strike is not None and args.t and args.r and args.vol:
        return OptionParams(
            spot=float(args.spot),
            strike=float(args.strike),
            t=parse_time(args.t),
            r=parse_rate_or_vol(args.r),
            sigma=parse_rate_or_vol(args.vol),
        )

    # Interactive: prompt only for whatever is missing, defaulting to DEFAULTS.
    console.print(Panel("[bold]Option inputs[/]", box=box.SQUARE))
    spot = float(args.spot) if args.spot is not None else _ask_float("Spot price", DEFAULTS.spot)
    strike = float(args.strike) if args.strike is not None else _ask_float("Strike", DEFAULTS.strike)
    if args.t:
        t = parse_time(args.t)
    else:
        t = parse_time(Prompt.ask("Time to expiry (e.g. 90d, 3m, 0.5)", default="90d", console=console))
    if args.r:
        r = parse_rate_or_vol(args.r)
    else:
        r = parse_rate_or_vol(Prompt.ask("Risk-free rate (e.g. 5% or 0.05)", default="5%", console=console))
    if args.vol:
        sigma = parse_rate_or_vol(args.vol)
    else:
        sigma = parse_rate_or_vol(Prompt.ask("Implied vol (e.g. 20% or 0.2)", default="20%", console=console))
    return OptionParams(spot=spot, strike=strike, t=t, r=r, sigma=sigma)


def render_quote(p: OptionParams) -> None:
    call = price(p.spot, p.strike, p.t, p.r, p.sigma, "call")
    put = price(p.spot, p.strike, p.t, p.r, p.sigma, "put")
    g = greeks(p.spot, p.strike, p.t, p.r, p.sigma)

    inputs = Table(box=box.SQUARE, title="Inputs", show_header=False, pad_edge=False)
    for label, value in (
        ("Spot", f"{p.spot:,.2f}"),
        ("Strike", f"{p.strike:,.2f}"),
        ("Expiry", f"{_human_time(p.t)}  ({p.t:.4f} y)"),
        ("Rate", f"{p.r * 100:.2f}%"),
        ("Vol", f"{p.sigma * 100:.2f}%"),
    ):
        inputs.add_row(f"[bold cyan]{label}[/]", value)
    console.print(inputs)

    table = Table(box=box.ROUNDED, title="Black-Scholes Valuation")
    table.add_column("Side", style="bold")
    table.add_column("Price", justify="right")
    for name in ("Delta", "Gamma", "Vega", "Theta/day", "Rho"):
        table.add_column(name, justify="right")

    table.add_row(
        "Call",
        f"${call:,.2f}",
        f"{g['delta_call']:+.4f}",
        f"{g['gamma']:.4f}",
        f"{g['vega']:+.4f}",
        f"{g['theta_call']:+.4f}",
        f"{g['rho_call']:+.4f}",
    )
    table.add_row(
        "Put",
        f"${put:,.2f}",
        f"{g['delta_put']:+.4f}",
        f"{g['gamma']:.4f}",
        f"{g['vega']:+.4f}",
        f"{g['theta_put']:+.4f}",
        f"{g['rho_put']:+.4f}",
    )
    console.print(table)

    residual = parity_residual(p.spot, p.strike, p.t, p.r, call, put)
    console.print(f"[dim]Put-call parity check:  C − P − (S − K·e⁻ʳᵀ) = {residual:+.2e}[/]")

    sense = Table(box=box.SIMPLE_HEAVY, title="What each Greek tells you", show_header=False, pad_edge=False)
    for name, text in _INTUITION:
        sense.add_row(f"[bold cyan]{name}[/]", text)
    console.print(sense)


def render_scan(p: OptionParams, axis: str) -> None:
    if axis == "spot":
        labels, params = [], []
        for f in (0.8, 0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.15, 1.2):
            labels.append(f"{p.spot * f:,.2f}")
            params.append((p.spot * f, p.strike, p.t, p.r, p.sigma))
        title = "Spot sensitivity"
    elif axis == "vol":
        labels, params = [], []
        for v in range(5, 51, 5):  # 5% .. 50%
            labels.append(f"{v}%")
            params.append((p.spot, p.strike, p.t, p.r, v / 100.0))
        title = "Implied-vol sensitivity"
    else:  # time
        labels, params = [], []
        for s in ("1m", "2m", "3m", "6m", "9m", "1y", "18m", "2y"):
            labels.append(s)
            params.append((p.spot, p.strike, parse_time(s), p.r, p.sigma))
        title = "Time-to-expiry sensitivity"

    table = Table(box=box.ROUNDED, title=title)
    table.add_column(axis.capitalize(), justify="right")
    table.add_column("Call", justify="right")
    table.add_column("Put", justify="right")
    table.add_column("Call Δ", justify="right")
    for label, (s, k, t, r, sig) in zip(labels, params):
        c = price(s, k, t, r, sig, "call")
        put = price(s, k, t, r, sig, "put")
        d = greeks(s, k, t, r, sig)["delta_call"]
        table.add_row(label, f"{c:,.2f}", f"{put:,.2f}", f"{d:+.3f}")
    console.print(table)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="option-pricer",
        description="Black-Scholes European option pricer with full Greeks.",
        epilog=(
            "EXAMPLES\n"
            "  option-pricer\n"
            "  option-pricer --spot 100 --strike 105 --t 90d --r 5% --vol 20%\n"
            "  option-pricer --spot 100 --strike 105 --t 0.5 --r 0.05 --vol 0.2 --scan spot\n\n"
            "NOTES\n"
            "  --t     accepts '0.5' (years), '90d', '3m', '1y'\n"
            "  --r/--vol  accept decimals (0.05, 0.2) or percents (5%, 20%)\n"
            "  Missing inputs fall back to an interactive prompt.\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--spot", type=float, help="underlying price")
    parser.add_argument("--strike", type=float, help="strike price")
    parser.add_argument("--t", type=str, metavar="T", help="time to expiry (years, or 30d / 3m / 1y)")
    parser.add_argument("--r", type=str, metavar="R", help="risk-free rate, decimal or percent")
    parser.add_argument("--vol", type=str, metavar="V", help="implied volatility, decimal or percent")
    parser.add_argument("--scan", choices=["spot", "vol", "time"], help="print a sensitivity table instead of a single quote")
    parser.add_argument("--iv", type=float, metavar="PRICE",
                        help="market price to invert for implied volatility "
                             "(with spot/strike/t/r)")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv=None) -> None:
    try:
        args = build_arg_parser().parse_args(argv)
        params = _resolve_params(args)
        if args.iv is not None:
            iv = implied_vol(params.spot, params.strike, params.t, params.r,
                             args.iv)
            console.print(f"[bold cyan]Implied vol:[/] {iv * 100:.2f}%  "
                          f"(market price ${args.iv:,.2f})")
            return
        if args.scan:
            render_scan(params, args.scan)
        else:
            render_quote(params)
    except ValueError as exc:
        console.print(f"[red]Error:[/] {exc}")
        raise SystemExit(2) from None


if __name__ == "__main__":
    main()
