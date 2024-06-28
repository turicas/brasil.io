bash: 					# Run bash inside `web` container
	docker compose exec -it web bash

bash-root: 				# Run bash as root inside `web` container
	docker compose exec -itu root web bash

build: fix-permissions			# Build containers
	docker compose build

clean: stop				# Stop and clean orphan containers
	docker compose down -v --remove-orphans

clear-cache:			# Clear Django cache stored on Redis
	docker compose exec web python manage.py clear_cache

dbshell: start			# Connect to database shell using `web` container
	docker compose exec -it web python manage.py dbshell

fix-permissions:		# Fix volume permissions on host machine
	userID=$${UID:-1000}
	groupID=$${UID:-1000}
	mkdir -p docker/data/web docker/data/db docker/data/mail docker/data/messaging docker/data/storage
	chown -R $$userID:$$groupID docker/data/web docker/data/db docker/data/mail docker/data/messaging docker/data/storage
	touch docker/env/web.local docker/env/db.local docker/env/mail.local docker/env/messaging.local docker/env/storage.local

help:					# List all make commands
	@awk -F ':.*#' '/^[a-zA-Z_-]+:.*?#/ { printf "\033[36m%-15s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST) | sort

kill:					# Force stop (kill) and remove containers
	docker compose kill
	docker compose rm --force

lint:					# Run linter script
	docker compose exec -it web /app/lint.sh

lint-check:				# Run the linter without changing files
	docker compose exec web /app/lint.sh --check

logs:					# Show all containers' logs (tail)
	docker compose logs -tf

migrate:				# Execute Django migrations inside `web` container
	docker compose exec -it web python manage.py migrate

migrations:				# Execute `makemigrations` inside `web` container
	docker compose exec -it web python manage.py makemigrations

shell:					# Execute Django shell inside `web` container
	docker compose exec -it web python manage.py shell

restart: stop start		# Stop all containers and start all containers in background

start: fix-permissions	# Start all containers in background
	docker compose up -d

stop:					# Stop all containers
	docker compose down

test:					# Execute `pytest` inside `web` container
	docker compose exec -it web pytest

test-v:					# Execute `pytest` with verbose option inside `web` container
	docker compose exec -it web pytest -vvv

.PHONY: bash bash-root build clean dbshell fix-permissions help kill lint lint-check logs migrate migrations restart shell start stop test test-v
