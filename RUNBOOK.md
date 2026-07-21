# Runbook — cbt-test-analytics

Operational guide for running the dbt medallion pipeline (ore → alloy → ingot)
against Postgres.

---

## 1. Prerequisites (one-time)

| Requirement | Notes |
|---|---|
| Python **3.9–3.13** | dbt does **not** support 3.14. This repo uses `.venv` on 3.11. |
| Git | Required by dbt. |
| Docker | Optional — only for the `local` target. |

> The `env/` folder is a Python 3.14 venv and is **not** used for dbt. The dbt
> environment is `.venv`.

---

## 2. Environment setup (one-time)

```powershell
# from the repo root
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\dbt.exe deps        # installs dbt_utils
```

Create your local config:

```powershell
Copy-Item .env.example .env
# then edit .env (see section 3)
```

`.env` is git-ignored — credentials never get committed.

---

## 3. Configuration — choosing the database

Everything is driven by `.env`. The active connection is picked by `DBT_TARGET`.

### Server (current)
```
DBT_TARGET=server
PG_HOST=pg-181c8b4c-engineosol-98a5.l.aivencloud.com
PG_PORT=13144
PG_USER=avnadmin
PG_PASSWORD=********
PG_DATABASE=defaultdb
PG_SCHEMA=public
PG_SSLMODE=require
```

### Local (Docker)
```
DBT_TARGET=local
PG_HOST=localhost
PG_PORT=5432
PG_USER=dbt
PG_PASSWORD=dbt
PG_DATABASE=analytics
PG_SSLMODE=disable
```
Then `docker compose up -d` to start Postgres.

Switching environments = edit `.env` only. No code changes.

---

## 4. Loading `.env` before running dbt

dbt reads these as environment variables, so load `.env` into the shell first.

**PowerShell:**
```powershell
Get-Content .env | Where-Object { $_ -match '^\s*[^#].*=' } | ForEach-Object {
    $k,$v = $_ -split '=',2
    [Environment]::SetEnvironmentVariable($k.Trim(), $v.Trim())
}
```

**Git Bash / WSL:**
```bash
set -a && . ./.env && set +a
```

> Tip: on Windows, use the full path `.venv\Scripts\dbt.exe`, or activate the
> venv first with `.venv\Scripts\Activate.ps1` and just call `dbt`.

---

## 5. Daily commands

| Goal | Command |
|---|---|
| Verify connection | `.venv\Scripts\dbt.exe debug` |
| Build everything (run + test) | `.venv\Scripts\dbt.exe build` |
| Run models only | `.venv\Scripts\dbt.exe run` |
| Run one layer | `.venv\Scripts\dbt.exe run --select tag:ore` (or `alloy`, `ingot`) |
| Run one model + downstream | `.venv\Scripts\dbt.exe run --select alloy_geo+` |
| Test only | `.venv\Scripts\dbt.exe test` |
| Full refresh (rebuild tables) | `.venv\Scripts\dbt.exe build --full-refresh` |
| Compile SQL (no run) | `.venv\Scripts\dbt.exe compile` |
| Docs site | `.venv\Scripts\dbt.exe docs generate` then `dbt docs serve` |
| Clean artifacts | `.venv\Scripts\dbt.exe clean` |

`--select` accepts: `tag:ore`, `alloy_geo`, `alloy_geo+` (downstream),
`+ingot_dim_geo` (upstream), `models/ingot` (path).

---

## 6. Standard operating procedure — a normal run

```powershell
# 1. load env
Get-Content .env | Where-Object { $_ -match '^\s*[^#].*=' } | ForEach-Object { $k,$v = $_ -split '=',2; [Environment]::SetEnvironmentVariable($k.Trim(), $v.Trim()) }

# 2. sanity-check the connection
.venv\Scripts\dbt.exe debug

# 3. build + test
.venv\Scripts\dbt.exe build
```

Expected tail: `Done. PASS=16 WARN=0 ERROR=0 SKIP=0`.

---

## 7. Pipeline layout

```
cbt_analytics.geo_master1  (source, schema: cbt_analytics)
        │
   ore.ore_geo_master               view    1:1, trim + blank→null
        │
   alloy.alloy_geo                  view    conform casing, booleans, parse spellings
        │
   ingot.ingot_dim_geo              table   clean geography dimension
   ingot.ingot_geo_coverage_summary table   coverage rollup by zone
```

Physical schemas `ore`, `alloy`, `ingot` are created automatically by the
`generate_schema_name` macro (named exactly, no target prefix).

---

## 8. Verifying output

```powershell
.venv\Scripts\python.exe -c "import psycopg2,os; c=psycopg2.connect(host=os.environ['PG_HOST'],port=os.environ['PG_PORT'],user=os.environ['PG_USER'],password=os.environ['PG_PASSWORD'],dbname=os.environ['PG_DATABASE'],sslmode=os.environ['PG_SSLMODE']); cur=c.cursor(); cur.execute('select count(*) from ingot.ingot_dim_geo'); print('ingot_dim_geo rows:', cur.fetchone()[0])"
```

Or with `dbt`:
```powershell
.venv\Scripts\dbt.exe show --select ingot_dim_geo --limit 10
```

---

## 9. Troubleshooting

| Symptom | Cause / Fix |
|---|---|
| `env_var` errors / connection uses wrong host | `.env` not loaded into the shell — redo section 4. |
| `Could not find profile named 'cbt_test_analytics'` | `DBT_PROFILES_DIR` not set to `.` — it's in `.env`; reload it. |
| `dbt` install fails / `No module named ...` on 3.14 | Wrong Python. Recreate `.venv` with `py -3.11` (section 2). |
| `ModuleNotFoundError: psycopg` in ad-hoc scripts | dbt ships **psycopg2**, not psycopg3 — `import psycopg2`. |
| `Connection test` hangs then fails | Check network/VPN, and `PG_SSLMODE=require` for Aiven. |
| Permission denied creating schema | DB user needs `CREATE` on the database. |
| Tests fail with unexpected values | Source data changed — inspect, then update `accepted_values` in the `_*.yml` files. |

---

## 10. Safety notes

- **Never commit `.env`.** It's git-ignored; keep it that way.
- Rotate the DB password if it has been shared in plaintext (chat, tickets).
- `--full-refresh` **drops and rebuilds** `ingot` tables — fine here (they're
  derived), but be deliberate on large tables.
- `dbt clean` only removes local `target/` and `dbt_packages/` — it never
  touches the database.
```
