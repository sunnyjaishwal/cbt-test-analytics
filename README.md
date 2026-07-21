# cbt-test-analytics

A dbt project that reads from Postgres and transforms data through a medallion
architecture with domain-specific layer names:

| Medallion | This project | Schema  | Materialization | Purpose                                   |
|-----------|--------------|---------|-----------------|-------------------------------------------|
| Bronze    | **ore**      | `ore`   | view            | Raw ingestion, 1:1 with source            |
| Silver    | **alloy**    | `alloy` | view            | Cleaned, conformed, deduplicated, joined  |
| Gold      | **ingot**    | `ingot` | table           | Business-facing marts / aggregates        |

## Configurable Postgres connection

The connection is chosen at runtime by a single variable, `DBT_TARGET`, and all
values come from a `.env` file — nothing is hardcoded.

- `DBT_TARGET=local`  → Postgres running locally in Docker (`docker-compose.yml`)
- `DBT_TARGET=server` → remote Postgres via server-host configuration

`profiles.yml` defines both `local` and `server` outputs, each populated from
`env_var(...)`. `docker-compose.yml` reads the **same** `.env`, so the local DB
and dbt always agree.

## Project structure

```
.
├── dbt_project.yml            # project + per-layer model config
├── profiles.yml              # local/server connections, env-var driven
├── packages.yml              # dbt package deps (dbt_utils)
├── requirements.txt          # dbt-core + dbt-postgres
├── docker-compose.yml        # local Postgres (uses .env)
├── .env.example              # copy to .env
├── Makefile                  # up/down/debug/run/test helpers
├── config/
│   └── initdb/               # SQL run on first Docker DB init
│       └── 01_schemas.sql    # creates raw/ore/alloy/ingot schemas
├── macros/
│   └── generate_schema_name.sql   # schemas named exactly ore/alloy/ingot
├── models/
│   ├── ore/                  # bronze
│   ├── alloy/                # silver
│   └── ingot/                # gold
├── seeds/  snapshots/  tests/  analyses/  scripts/
```

## Prerequisites

- Python **3.9–3.13** for dbt (this repo uses a `.venv` on Python 3.11)
- Docker only if you want the local target (optional; currently we use the server)

> ⚠️ The venv in `./env` is Python 3.14, which **dbt does not support**. This
> project's environment is `./.venv` created with Python 3.11:
> ```
> py -3.11 -m venv .venv
> .venv\Scripts\activate
> pip install -r requirements.txt
> ```

## Setup (current: remote server)

The active target is the Aiven-hosted Postgres, configured in `.env`
(`DBT_TARGET=server`). To reproduce:

```bash
# .env already holds the server connection (git-ignored)
.venv/Scripts/dbt.exe deps      # install packages  ✅ done
.venv/Scripts/dbt.exe debug     # verify connection ✅ passing
.venv/Scripts/dbt.exe build     # run + test (once models exist)
```

Load `.env` before running dbt (bash: `set -a && . ./.env && set +a`).

## Switching between environments

Everything is driven by `.env` — no code changes:

| Target        | `.env` setting     | Connection                          |
|---------------|--------------------|-------------------------------------|
| Remote server | `DBT_TARGET=server`| `PG_HOST` = cloud host, `require` SSL |
| Local Docker  | `DBT_TARGET=local` | `docker compose up -d`, `localhost` |

## Data flow (current build)

Source: `cbt_analytics.geo_master1` (Nigeria FMCG geography master, 22 rows).

```
cbt_analytics.geo_master1  (source)
        │
   ore.ore_geo_master      (view)   trim + blank→null, 1:1
        │
   alloy.alloy_geo          (view)   conform casing, Y/NULL→boolean flags,
        │                            normalize regions, parse raw_spellings
   ingot.ingot_dim_geo             (table)  clean geo dimension + source_coverage
   ingot.ingot_geo_coverage_summary (table)  coverage rollup by zone
```

Run it: `set -a && . ./.env && set +a && .venv/Scripts/dbt.exe build`

## Status

- ✅ Project scaffolding + medallion layers (ore / alloy / ingot)
- ✅ Env-driven, configurable Postgres (local Docker **or** server)
- ✅ Connected & verified against remote Postgres 17 (`dbt debug` passes)
- ✅ ore → alloy → ingot models built on `geo_master1`; **`dbt build` = 16/16 pass**
- ⬜ **Next:** add products/e-commerce facts; docs site (`dbt docs`); scheduling
