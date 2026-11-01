SHELL := /bin/bash

# Base de datos
migraciones:
	python manage.py makemigrations

migrar:
	python manage.py migrate

formato:
	ruff check --select I --fix .
	ruff format .

revisar:
	ruff check .
	ruff format --check .

seguridad:
	bandit -r core cuentas interfaz convenios postulaciones -x postulaciones/tests.py

test:
	pytest

cobertura:
	coverage run -m pytest
	coverage report
