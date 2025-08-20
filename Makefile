.PHONY: install fmt test deps-check

install:
	pip install -e .

fmt:
	black apps tests && isort apps tests

test:
	pytest --maxfail=1 --disable-warnings -q

deps-check:
	python scripts/check_dependencies.py
