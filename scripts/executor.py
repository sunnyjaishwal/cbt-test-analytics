#!/usr/bin/env python3
"""Cross-platform project executor for cbt-test-analytics (dbt + Postgres).

Deploys and runs the dbt medallion pipeline from a clean checkout in one
command. Works on Linux (server) and Windows (dev) with the same invocation.

Steps:
  1. Create (or reuse) a Python venv with a dbt-supported interpreter.
  2. Upgrade pip and install requirements.txt.
  3. Install dbt packages (dbt deps).
  4. Load .env into the environment passed to dbt.
  5. Verify the connection (dbt debug), then build the models (dbt build),
     which materializes the ore -> alloy -> ingot tables.

Idempotent: reuses an existing venv unless --recreate is given.

Usage:
  python scripts/executor.py                        # full build (run + test)
  python scripts/executor.py --command run          # models only
  python scripts/executor.py --select tag:ore       # one layer
  python scripts/executor.py --target server --full-refresh
  python scripts/executor.py --recreate             # rebuild the venv
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# dbt-core supports these Python minors. 3.14 is NOT supported.
SUPPORTED_PY = ((3, 9), (3, 10), (3, 11), (3, 12), (3, 13))

# Repo root = parent of this script's directory.
REPO_ROOT = Path(__file__).resolve().parent.parent
VENV_DIR = REPO_ROOT / ".venv"
REQ_FILE = REPO_ROOT / "requirements.txt"
ENV_FILE = REPO_ROOT / ".env"

IS_WINDOWS = os.name == "nt"


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def step(msg: str) -> None:
    print(f"\n==> {msg}", flush=True)


def info(msg: str) -> None:
    print(f"    {msg}", flush=True)


def fail(msg: str) -> "None":
    print(f"\nERROR: {msg}", file=sys.stderr, flush=True)
    sys.exit(1)


def venv_bin(name: str) -> Path:
    """Path to an executable inside the venv, cross-platform."""
    sub = "Scripts" if IS_WINDOWS else "bin"
    exe = f"{name}.exe" if IS_WINDOWS else name
    return VENV_DIR / sub / exe


def run(cmd: list[str], env: dict | None = None) -> None:
    """Run a command, streaming output; exit the script on failure."""
    printable = " ".join(str(c) for c in cmd)
    info(f"$ {printable}")
    result = subprocess.run(cmd, env=env)
    if result.returncode != 0:
        fail(f"command failed (exit {result.returncode}): {printable}")


# --------------------------------------------------------------------------- #
# Steps
# --------------------------------------------------------------------------- #
def find_base_python(requested: str | None) -> str:
    """Resolve a dbt-supported base interpreter to build the venv from."""
    if requested:
        if not shutil.which(requested) and not Path(requested).exists():
            fail(f"requested Python '{requested}' not found on PATH.")
        return requested

    # Default: the interpreter running this script, if it's supported.
    cur = sys.version_info[:2]
    if cur in SUPPORTED_PY:
        return sys.executable

    # Otherwise, hunt for a supported one on PATH.
    for minor in (11, 13, 12, 10, 9):
        for cand in (f"python3.{minor}", f"python{minor}"):
            if shutil.which(cand):
                info(f"current Python {cur[0]}.{cur[1]} unsupported; using {cand}")
                return cand

    fail(
        f"running Python {cur[0]}.{cur[1]} is not dbt-supported "
        f"(need 3.9-3.13) and no supported interpreter was found on PATH. "
        f"Pass --python /path/to/python3.11."
    )


def ensure_venv(base_python: str, recreate: bool) -> None:
    vpy = venv_bin("python")

    if recreate and VENV_DIR.exists():
        step("Removing existing venv (--recreate)")
        shutil.rmtree(VENV_DIR)

    if vpy.exists():
        step("Reusing existing venv (.venv)")
        return

    step(f"Creating venv (.venv) from {base_python}")
    run([base_python, "-m", "venv", str(VENV_DIR)])
    if not vpy.exists():
        fail("venv creation did not produce a python executable.")


def install_requirements() -> None:
    vpy = str(venv_bin("python"))
    step("Upgrading pip")
    run([vpy, "-m", "pip", "install", "--upgrade", "pip", "--quiet"])

    if not REQ_FILE.exists():
        fail(f"requirements file not found: {REQ_FILE}")
    step(f"Installing requirements ({REQ_FILE.name})")
    run([vpy, "-m", "pip", "install", "-r", str(REQ_FILE)])


def load_env(target_override: str | None) -> dict:
    """Parse .env into a copy of the current environment for dbt."""
    if not ENV_FILE.exists():
        fail(
            f".env not found at {ENV_FILE}. "
            f"Copy .env.example to .env and configure it (see RUNBOOK.md)."
        )

    step("Loading .env")
    env = os.environ.copy()
    for raw in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key:
            env[key] = val

    if target_override:
        env["DBT_TARGET"] = target_override

    # dbt must read profiles.yml from the repo root.
    env.setdefault("DBT_PROFILES_DIR", ".")
    info(
        f"DBT_TARGET = {env.get('DBT_TARGET')}  "
        f"DBT_PROFILES_DIR = {env.get('DBT_PROFILES_DIR')}"
    )

    # Preflight: the 'server' profile has no defaults, so a missing credential
    # otherwise surfaces as an opaque DB-side auth error. Fail fast instead.
    target = env.get("DBT_TARGET", "local")
    if target == "server":
        required = ("PG_HOST", "PG_PORT", "PG_USER", "PG_PASSWORD", "PG_DATABASE")
        missing = [k for k in required if not env.get(k, "").strip()]
        if missing:
            fail(
                f"missing required credential(s) for DBT_TARGET=server: "
                f"{', '.join(missing)}. Add them to {ENV_FILE.name} "
                f"(see .env.example / RUNBOOK.md)."
            )

    return env


def run_dbt(env: dict, command: str, select: str | None,
            full_refresh: bool, skip_deps: bool) -> None:
    dbt = str(venv_bin("dbt"))

    if not skip_deps:
        step("Installing dbt packages (dbt deps)")
        run([dbt, "deps"], env=env)

    step("Verifying connection (dbt debug)")
    run([dbt, "debug"], env=env)

    dbt_args = [dbt, command]
    if select:
        dbt_args += ["--select", select]
    if full_refresh:
        dbt_args.append("--full-refresh")

    step(f"Running: dbt {' '.join(dbt_args[1:])}")
    run(dbt_args, env=env)


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Deploy and run the cbt-test-analytics dbt project.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--command", default="build",
                   help="dbt command to run (build, run, test, debug, ...).")
    p.add_argument("--select", default=None,
                   help="dbt --select expression (e.g. tag:ore, alloy_geo+).")
    p.add_argument("--target", default=None, choices=["local", "server"],
                   help="Override DBT_TARGET from .env.")
    p.add_argument("--full-refresh", action="store_true",
                   help="Pass --full-refresh (drops & rebuilds ingot tables).")
    p.add_argument("--python", default=None,
                   help="Base interpreter to build the venv (e.g. python3.11).")
    p.add_argument("--recreate", action="store_true",
                   help="Delete and recreate the venv from scratch.")
    p.add_argument("--skip-deps", action="store_true",
                   help="Skip 'dbt deps' (packages already installed).")
    p.add_argument("--setup-only", action="store_true",
                   help="Only set up env + install deps; do not run dbt.")
    return p.parse_args(argv)


def main(argv: list[str]) -> None:
    args = parse_args(argv)
    os.chdir(REPO_ROOT)

    base_python = find_base_python(args.python)
    ensure_venv(base_python, args.recreate)
    install_requirements()
    env = load_env(args.target)

    if args.setup_only:
        step("Setup complete (--setup-only); skipping dbt run.")
        return

    run_dbt(env, args.command, args.select, args.full_refresh, args.skip_deps)

    step(f"Done. Tables built via '{args.command}'.")
    info("Schemas: ore (views) -> alloy (views) -> ingot (tables)")


if __name__ == "__main__":
    main(sys.argv[1:])
