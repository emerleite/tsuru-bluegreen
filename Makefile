.PHONY: testdeps test

testdeps:
	pip install -r test_requirements.txt

test:
	nosetests test/*.py
