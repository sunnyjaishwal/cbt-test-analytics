# Convenience wrapper. Loads .env so dbt + docker share one config.
# On Windows, run these via `make` (Git Bash / WSL) or copy the commands.

ifneq (,$(wildcard .env))
include .env
export
endif

.PHONY: help up down logs psql deps debug run test build clean

help:
	@echo "up      - start local Postgres (Docker)"
	@echo "down    - stop local Postgres"
	@echo "psql    - open psql shell into local Postgres"
	@echo "deps    - install dbt packages"
	@echo "debug   - dbt debug (verify connection for current DBT_TARGET)"
	@echo "run     - dbt run"
	@echo "test    - dbt test"
	@echo "build   - dbt build (run + test)"
	@echo "clean   - dbt clean"

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f postgres

psql:
	docker compose exec postgres psql -U $(PG_USER) -d $(PG_DATABASE)

deps:
	dbt deps

debug:
	dbt debug

run:
	dbt run

test:
	dbt test

build:
	dbt build

clean:
	dbt clean
