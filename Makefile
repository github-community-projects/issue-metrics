.PHONY: test
test:
	uv run pytest -v --cov=. --cov-config=.coveragerc --cov-fail-under=80 --cov-report term-missing
	.github/scripts/env_vars_check.sh

.PHONY: clean
clean:
	rm -rf .pytest_cache .coverage __pycache__

.PHONY: lint
lint:
	# stop the build if there are Python syntax errors or undefined names
	uv run flake8 . --config=.github/linters/.flake8 --count --select=E9,F63,F7,F82 --show-source
	# exit-zero treats all errors as warnings. The GitHub editor is 127 chars wide
	uv run flake8 . --config=.github/linters/.flake8 --count --exit-zero --max-complexity=15 --max-line-length=127
	uv run isort --settings-file=.github/linters/.isort.cfg .
	uv run pylint --rcfile=.github/linters/.python-lint --fail-under=9.0 *.py
	uv run mypy --config-file=.github/linters/.mypy.ini *.py
	uv run black .
