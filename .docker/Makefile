.PHONY: up down logs shell migrate superuser deploy

PROYECTO = portal-admin-psw

up:
	docker compose --env-file app/.env --project-name $(PROYECTO) up -d --build --remove-orphans
	docker ps

down:
	docker compose --env-file app/.env --project-name $(PROYECTO) down

logs:
	docker logs -f $(PROYECTO)

shell:
	docker exec -it $(PROYECTO) bash

migrate:
	docker exec $(PROYECTO) python manage.py migrate

superuser:
	docker exec -it $(PROYECTO) python manage.py createsuperuser

deploy:
	docker compose --env-file app/.env --file dc-produccion.yml --project-name $(PROYECTO) up -d --build --force-recreate --remove-orphans
	docker ps
