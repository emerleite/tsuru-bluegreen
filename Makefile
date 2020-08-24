.PHONY: testdeps test docker-test

testdeps:
	pip install -r test_requirements.txt

test:
	nosetests test/*.py

docker-test:
	docker-compose -f test/tests.compose up -d tests
	docker-compose -f test/tests.compose exec tests sh -c "make testdeps"
	docker-compose -f test/tests.compose exec tests sh -c "make test"
