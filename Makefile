bash:
	docker compose exec web bash

bash-root:
	docker compose exec -u root web bash

build:
	docker compose build

clean: stop
	docker compose down -v --remove-orphans

clear_cache:
	python manage.py clear_cache

lint:
	docker compose exec web /app/lint.sh

logs:
	docker compose logs -f

restart: stop start

scheduler:
	docker compose exec web python manage.py rqscheduler

shell:
	docker compose exec web python manage.py shell

start:
	docker compose up -d

stop:
	docker compose kill
	docker compose rm --force

test:
	docker compose exec web pytest

test-v:
	docker compose exec web pytest -vvv

.PHONY: bash-root bash build clean clear_cache lint logs restart scheduler shell start stop test-v test
