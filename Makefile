_prepare:
	touch docker/env/web.local docker/env/db.local docker/env/redis.local docker/env/mail.local docker/env/storage.local

bash:
	docker compose exec web bash

bash-root:
	docker compose exec -u root web bash

build: _prepare
	docker compose build

build-no-cache: _prepare
	docker compose build --no-cache

collect-static-no-input:
	docker compose exec web python manage.py collectstatic --no-input

clean: stop
	docker compose down -v --remove-orphans

clear-cache:
	docker compose exec web python manage.py clear_cache

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

start: _prepare
	docker compose up -d

stop:
	docker compose kill
	docker compose rm --force

test:
	docker compose exec web pytest

test-v:
	docker compose exec web pytest -vvv

.PHONY: _prepare bash bash-root build build-no-cache clean clear-cache collect-static-no-input lint lint-check logs migrate migrate-no-input restart scheduler shell start stop test test-v
