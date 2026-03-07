.PHONY: install install-dev format lint typecheck test ci demo demo-run clean

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

format:
	python -m compileall src

lint:
	ruff check .

typecheck:
	mypy src

test:
	pytest

ci: lint typecheck test

demo:
	fgdm-demo-data --output-dir demo_data

demo-run:
	fgdm --input demo_data/forecast_demo.csv --output-dir demo_output --run-id demo_run

clean:
	python -c "from pathlib import Path; [p.unlink() for p in Path('.').rglob('*.pyc')]"
	python -c "from pathlib import Path; [p.rmdir() for p in sorted(Path('.').rglob('__pycache__'), reverse=True) if p.exists()]"