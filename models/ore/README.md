# ore (bronze)

Raw ingestion layer. Models here read directly from `source()` tables and stay
as close to the source as possible: light typing/renaming only, no business
logic, no joins. One ore model per source table.

Materialized as **views**. Schema: `ore`.
