#!/bin/sh

PROJECT_NAME=$(basename $(pwd))
ENV_FILE=.env
DOCKER_COMPOSE_FILE=compose.yml

function compose() {
	docker compose -p $PROJECT_NAME -f $DOCKER_COMPOSE_FILE $@
}

# Run needed containers
compose up -d
