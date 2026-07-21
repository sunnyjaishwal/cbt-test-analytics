# alloy (silver)

Cleaned and conformed layer. Reads from `ore` models via `ref()`. This is where
deduplication, standardization, type casting, joins across sources, and
business keys happen. Still normalized — not yet aggregated for consumption.

Materialized as **views**. Schema: `alloy`.
