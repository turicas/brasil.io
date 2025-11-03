TAGS_FILE = .tags

bash: 					# Run bash inside `web` container
	docker compose exec -it web bash

bash-root: 				# Run bash as root inside `web` container
	docker compose exec -itu root web bash

build:					# Build containers and pull images
	docker compose pull
	docker compose build

build-no-cache:			# Build containers without using cache
	docker compose pull
	docker compose build --no-cache

clean: stop				# Stop and clean orphan containers
	rm -f $(TAGS_FILE)
	docker compose down -v --remove-orphans

clear-cache:			# Clear Django cache stored on Redis
	docker compose exec web python manage.py clear_cache

dbshell: 				# Connect to database shell using `web` container
	docker compose exec -it web python manage.py dbshell

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

start:					# Start all containers in background
	docker compose up -d

stop:					# Stop all containers
	docker compose down

tags:					# Generate tags file for the entire project (requires universal-ctags)
	@git ls-files | ctags -L - --tag-relative=yes --quiet --append -f "$(TAGS_FILE)"

test:					# Execute `pytest` and coverage report inside `web` container
	docker compose exec -it web bash -c 'coverage run -m pytest $(TEST_ARGS) && coverage report'

.PHONY: bash bash-root build build-no-cache clean clear-cache dbshell help kill lint lint-check logs migrate migrations restart shell start stop tags test
