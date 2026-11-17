.PHONY: install run test lint typecheck migrate migration-dryrun release-tag

install:
	uv sync

run:
	uv run uvicorn settlekit.api:app --reload --port 8060

test:
	uv run pytest

lint:
	uv run ruff check src tests
	uv run ruff format --check src tests

typecheck:
	uv run mypy

migrate:
	uv run alembic upgrade head

migration-dryrun:
	mkdir -p build
	uv run alembic upgrade head --sql > build/migration.sql
	@echo "SQL 已写到 build/migration.sql"

release-tag:
	@test -n "$(VERSION)" || (echo "用法: make release-tag VERSION=1.9.0"; exit 1)
	uv run python scripts/stamp_changelog.py $(VERSION)
	git tag -s v$(VERSION) -m "settlekit $(VERSION)"
