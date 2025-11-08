TAGS_FILE = .tags
ifeq ($(CI),true)
    DOCKER_EXEC_FLAGS = -T
else
    DOCKER_EXEC_FLAGS = -it
endif
COMPOSE = docker compose
COMPOSE_EXEC = $(COMPOSE) exec $(DOCKER_EXEC_FLAGS)

bash: 					# Run bash inside `web` container
	$(COMPOSE_EXEC) web bash

bash-root: 				# Run bash as root inside `web` container
	$(COMPOSE_EXEC) -u root web bash

build:					# Build containers and pull images
	$(COMPOSE) pull
	$(COMPOSE) build

build-ci:					# Build only containers and pull images (only the needed ones)
	# Remove definition of user as stated in <https://docs.github.com/en/actions/reference/workflows-and-actions/dockerfile-support#user>
	sed -i '/^\s\?USER/d' Dockerfile
	sed -i '/# Create a non-root user to run the app/,/&& chown -R django:django \/app/d' Dockerfile
	sed -i '/^\s\+user:/d' compose.yml
	$(COMPOSE) pull db messaging storage
	$(COMPOSE) build web

build-no-cache:			# Build containers without using cache
	$(COMPOSE) pull
	$(COMPOSE) build --no-cache

clean: stop				# Stop and clean orphan containers
	rm -f $(TAGS_FILE)
	$(COMPOSE) down -v --remove-orphans

clear-cache:			# Clear Django cache stored on Redis
	$(COMPOSE_EXEC) web python manage.py clear_cache

dbshell: 				# Connect to database shell using `web` container
	$(COMPOSE_EXEC) web python manage.py dbshell

help:					# List all make commands
	@awk -F ':.*#' '/^[a-zA-Z_-]+:.*?#/ { printf "\033[36m%-15s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST) | sort

kill:					# Force stop (kill) and remove containers
	$(COMPOSE) kill
	$(COMPOSE) rm --force

lint:					# Run linter script
	$(COMPOSE_EXEC) web /app/lint.sh

lint-check:				# Run the linter without changing files
	$(COMPOSE_EXEC) web /app/lint.sh --check

logs:					# Show all containers' logs (tail)
	$(COMPOSE) logs -tf

migrate:				# Execute Django migrations inside `web` container
	$(COMPOSE_EXEC) web python manage.py migrate

migrations:				# Execute `makemigrations` inside `web` container
	$(COMPOSE_EXEC) web python manage.py makemigrations

shell:					# Execute Django shell inside `web` container
	$(COMPOSE_EXEC) web python manage.py shell

restart: stop start		# Stop all containers and start all containers in background

start:					# Start all containers in background
	$(COMPOSE) up -d

stop:					# Stop all containers
	$(COMPOSE) down

tags:					# Generate tags file for the entire project (requires universal-ctags)
	@git ls-files | ctags -L - --tag-relative=yes --quiet --append -f "$(TAGS_FILE)"

test:					# Execute `pytest` and coverage report inside `web` container
	$(COMPOSE_EXEC) web bash -c 'coverage run -m pytest $(TEST_ARGS) && coverage report'

test-ci:				# Execute tests in CI environment (uses less memory)
	$(COMPOSE) up -d db messaging storage
	$(COMPOSE) run --rm web bash -c 'coverage run -m pytest $(TEST_ARGS) && coverage report'

.PHONY: bash bash-root build build-ci build-no-cache clean clear-cache dbshell help kill lint lint-check logs migrate migrations restart shell start stop tags test test-ci
