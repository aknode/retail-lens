.PHONY: setup test run
setup:
	python -m app.bootstrap
test:
	python -m unittest discover -s tests -v
run:
	python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
