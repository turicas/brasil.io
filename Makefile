run_django:
	python manage.py runserver 0.0.0.0:8000

run_rqworker:
	python manage.py rqworker  --sentry-dsn=""

run:
	make -j2 run_django run_rqworker
