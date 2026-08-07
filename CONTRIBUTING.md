# Contributing

## Setup
    python3 -m venv .venv
    .venv/bin/pip install -e .

## Run the tests
    .venv/bin/python -m unittest discover -s tests -v

## Layout
- `pricer/` — package: `black_scholes.py` (closed forms + Greeks), CLI.
- `tests/` — unittest suite: normal functions, pricing, Greeks.

## Style
- Pure stdlib, period. No NumPy, no third-party math.
- One formula, one function; every function has a docstring naming its units.
- Every pricing function / Greek needs a unittest on a known-value case and a
  put-call parity check.

## Adding a new Greek
- Implement the closed form next to the existing ones in `black_scholes.py`.
- Add it to the `greeks()` return dict and the CLI table.
- A unittest on the known-value case, plus a parity/dimensional sanity check.

## Pull requests
- Small, single-purpose commits. Back every claim with a test.
- The stdlib constraint is the whole point — no new packages without discussion.
