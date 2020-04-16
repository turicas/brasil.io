run_django:
	python manage.py runserver

run_rqworker:
	python manage.py rqworker

run:
	make -j2 run_django run_rqworker
