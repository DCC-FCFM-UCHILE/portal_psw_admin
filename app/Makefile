SHELL := /bin/bash

# Base de datos
migraciones:
	python manage.py makemigrations

migrar:
	python manage.py migrate

formato:
	black .
	isort .

revisar:
	flake8 .

seguridad:
	bandit -r core cuentas convenios postulaciones -x postulaciones/tests.py

test:
	pytest

cobertura:
	coverage run -m pytest
	coverage report
