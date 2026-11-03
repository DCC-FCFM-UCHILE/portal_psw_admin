SHELL := /bin/bash

.PHONY: migrations migrate format lint security test coverage

# Base de datos
migrations:
	python manage.py makemigrations

migrate:
	python manage.py migrate

format:
	ruff check --select I --fix .
	ruff format .

lint:
	ruff check .
	ruff format --check .

security:
	bandit -r core cuentas interfaz convenios postulaciones -x postulaciones/tests.py

test:
	pytest

coverage:
	coverage run -m pytest
	coverage report
