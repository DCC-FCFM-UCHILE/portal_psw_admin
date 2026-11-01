PROYECTO = portal-admin-psw

levantar:
	docker compose --env-file app/.env --project-name $(PROYECTO) up -d --build --remove-orphans
	docker ps

bajar:
	docker compose --env-file app/.env --project-name $(PROYECTO) down

logs:
	docker logs -f $(PROYECTO)

consola:
	docker exec -it $(PROYECTO) bash

migrar:
	docker exec $(PROYECTO) python manage.py migrate

superusuario:
	docker exec -it $(PROYECTO) python manage.py createsuperuser

desplegar:
	docker compose --env-file app/.env --file dc-produccion.yml --project-name $(PROYECTO) up -d --build --force-recreate --remove-orphans
	docker ps
