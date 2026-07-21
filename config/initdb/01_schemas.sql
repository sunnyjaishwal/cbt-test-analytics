-- Runs automatically the first time the local Postgres container is created.
-- Creates the medallion schemas so dbt can write into them.
--   ore   = bronze   (raw)
--   alloy = silver    (cleaned/conformed)
--   ingot = gold      (marts)
-- A `raw` schema holds source tables that feed the ore layer.

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS ore;
CREATE SCHEMA IF NOT EXISTS alloy;
CREATE SCHEMA IF NOT EXISTS ingot;
