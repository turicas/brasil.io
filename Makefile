lint:
	autoflake --in-place --recursive --remove-unused-variables --remove-all-unused-imports .
	isort --skip migrations --skip brasilio/wsgi.py -rc .
	black . --exclude "docker" -l 120

clear_cache:
	python manage.py clear_cache

run_django:
	python manage.py runserver 0.0.0.0:8000

run_rqworker:
	python manage.py rqworker  --sentry-dsn=""

run: clear_cache
	make -j2 run_django run_rqworker

.PHONY: black clear_cache run_django run_rqworker run
