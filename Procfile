web: gunicorn brasilio.wsgi:application --bind=0.0.0.0:5000 --workers=4 --log-file -

release: python manage.py migrate --no-input
