default: test

COMPOSE_FILE_DEV = 'compose/dev/docker-compose.yml'


############################################
## atalhos docker-compose desenvolvimento ##
############################################

dev_compose_build:
	@docker-compose -f $(COMPOSE_FILE_DEV) build

dev_compose_up:
	@docker-compose -f $(COMPOSE_FILE_DEV) up -d

dev_compose_logs:
	@docker-compose -f $(COMPOSE_FILE_DEV) logs -f

dev_compose_stop:
	@docker-compose -f $(COMPOSE_FILE_DEV) stop

dev_compose_ps:
	@docker-compose -f $(COMPOSE_FILE_DEV) ps

dev_compose_rm:
	@docker-compose -f $(COMPOSE_FILE_DEV) rm -f

dev_compose_django_shell:
	@docker-compose -f $(COMPOSE_FILE_DEV) run --rm django python manage.py shell

dev_compose_django_createsuperuser:
	@docker-compose -f $(COMPOSE_FILE_DEV) run --rm django python manage.py createsuperuser

dev_compose_django_bash:
	@docker-compose -f $(COMPOSE_FILE_DEV) run --rm django bash

dev_compose_django_test:
	@docker-compose -f $(COMPOSE_FILE_DEV) run --rm django python manage.py test

dev_compose_django_test_fast:
	@docker-compose -f $(COMPOSE_FILE_DEV) run --rm django python manage.py test --failfast

dev_compose_django_makemigrations:
	@docker-compose -f $(COMPOSE_FILE_DEV) run --rm django python manage.py makemigrations

dev_compose_django_migrate:
	@docker-compose -f $(COMPOSE_FILE_DEV) run --rm django python manage.py migrate


#########
## test #
#########

test:
	@python manager test
