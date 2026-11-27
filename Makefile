PYTHON ?= python3

.PHONY: clean build check upload upload-test docs docs-serve

clean:
	rm -rf dist build *.egg-info pie_extended.egg-info

build: clean
	python3 -m build .

check: build
	twine check dist/*

upload-test: clean build check
	twine upload --repository testpypi dist/*

upload: clean build check
	twine upload dist/*

# Documentation (pip install -e ".[docs]"): the result is in docs/_build/html
docs:
	$(PYTHON) -m sphinx -W --keep-going -b html docs docs/_build/html

docs-serve: docs
	$(PYTHON) -m http.server 8000 --directory docs/_build/html
