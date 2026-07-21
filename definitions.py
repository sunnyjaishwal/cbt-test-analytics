from pathlib import Path

from dagster import Definitions

from smelter.sdk.config import load_tenant_config
from smelter.sdk.dbt_integration import dbt_assets_for_project, dbt_resource_for_project
from smelter.sdk.factories import assets_from_config, publish_assets_from_config
from smelter.sdk.resources import smelter_resources
from smelter.sdk.scheduling import schedules_from_config

_DIR = Path(__file__).parent
config = load_tenant_config(_DIR / "config.yml")

# dbt models become Dagster assets when the project has a dbt project + manifest.
# dbt_resource_for_project()/dbt_assets_for_project() return None/[] when it
# doesn't, so ingest-only projects are unaffected.
_dbt_dir = _DIR / "dbt"
_resources = smelter_resources(namespace=config.namespace)
_dbt_res = dbt_resource_for_project(_dbt_dir)
if _dbt_res is not None:
    _resources = {**_resources, "dbt": _dbt_res}

# Hoisted so the project-level `transform` schedule can target exactly this
# project's dbt model assets (by key) rather than a global group selection.
_dbt_asset_defs = dbt_assets_for_project(_dbt_dir)
_dbt_keys = [k for a in _dbt_asset_defs for k in getattr(a, "keys", [])]

defs = Definitions(
    assets=[
        *assets_from_config(config),
        *_dbt_asset_defs,
        *publish_assets_from_config(config),
    ],
    resources=_resources,
    schedules=schedules_from_config(config, dbt_asset_keys=_dbt_keys),
)
