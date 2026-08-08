.PHONY: install test run quote scan

install:
	python -m pip install -e .

test:
	python -m unittest discover -s tests -v

run:
	option-pricer

# A quick demo quote — no flags needed.
quote:
	option-pricer --spot 100 --strike 105 --t 90d --r 5% --vol 20%

scan:
	option-pricer --spot 100 --strike 105 --t 90d --r 5% --vol 20% --scan vol
