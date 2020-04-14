web: gunicorn brasilio.wsgi:application --bind=0.0.0.0:5000 --workers=$WORKERS --log-file -
worker: python manage.py rqworker
release: python manage.py migrate --no-input
