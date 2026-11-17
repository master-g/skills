.PHONY: install run test test-integration lint fmt db-reset

DATABASE_URL ?= postgresql+psycopg://exportkit:exportkit@localhost:5432/exportkit

install:
	uv sync

run:
	uv run uvicorn exportkit.api:app --reload --port 8040

test:
	uv run pytest

test-integration:
	DATABASE_URL=$(DATABASE_URL) uv run pytest -m integration

lint:
	uv run ruff check src tests
	uv run ruff format --check src tests

fmt:
	uv run ruff format src tests

db-reset:
	psql "$(subst +psycopg,,$(DATABASE_URL))" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
	DATABASE_URL=$(DATABASE_URL) uv run alembic upgrade head
