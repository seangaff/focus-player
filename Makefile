.PHONY: run test

run:
	python src/main.py --config sampleConfig.toml

test:
	python -m pytest
