#!/bin/sh

docker-compose up -d tests
docker-compose exec tests sh -c "make testdeps"
docker-compose exec tests sh -c "make test"
