.PHONY: install fmt test

install:
	pip install -e .

fmt:
	black apps tests && isort apps tests

test:
	pytest --maxfail=1 --disable-warnings -q
