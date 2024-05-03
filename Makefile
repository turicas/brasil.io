bash:
	docker compose exec web bash

bash-root:
	docker compose exec -u root web bash

build:
	docker compose build

build-no-cache:
	docker compose build --no-cache

collect-static-no-input:
	docker compose exec web python manage.py collectstatic --no-input

clean: stop
	docker compose down -v --remove-orphans

clear_cache:
	python manage.py clear_cache

lint:
	docker compose exec web /app/lint.sh

lint-check:
	docker compose exec web /app/lint.sh --check

logs:
	docker compose logs -f

migrate:
	docker compose exec -it web python manage.py migrate

migrate-no-input:
	docker compose exec web python manage.py migrate --no-input

restart: stop start

scheduler:
	docker compose exec web python manage.py rqscheduler

shell:
	docker compose exec web python manage.py shell

start:
	touch docker/env/web.local docker/env/db.local docker/env/redis.local docker/env/mail.local docker/env/storage.local
	docker compose up -d

stop:
	docker compose kill
	docker compose rm --force

test:
	docker compose exec web pytest

test-v:
	docker compose exec web pytest -vvv

.PHONY: bash-root bash build clean clear_cache lint logs restart scheduler shell start stop test-v test
