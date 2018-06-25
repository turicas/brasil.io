web: gunicorn brasilio.wsgi:application --bind=0.0.0.0 --log-file -

release: python manage.py migrate --no-input
