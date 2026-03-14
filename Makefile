.PHONY: test
test:
	uv run python -m pytest -v --cov=. --cov-config=.coveragerc --cov-fail-under=80 --cov-report term-missing
	.github/scripts/env_vars_check.sh

.PHONY: clean
clean:
	rm -rf .pytest_cache .coverage __pycache__

.PHONY: lint
lint:
	# stop the build if there are Python syntax errors or undefined names
	uv run python -m flake8 . --config=.github/linters/.flake8 --count --select=E9,F63,F7,F82 --show-source
	# exit-zero treats all errors as warnings. The GitHub editor is 127 chars wide
	uv run python -m flake8 . --config=.github/linters/.flake8 --count --exit-zero --max-complexity=15 --max-line-length=127
	uv run isort --settings-file=.github/linters/.isort.cfg .
	uv run python -m pylint --rcfile=.github/linters/.python-lint *.py
	uv run python -m mypy --config-file=.github/linters/.mypy.ini *.py
	uv run black .
