.PHONY: clean build check upload upload-test

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
