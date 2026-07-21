-- ingot (gold): coverage rollup by zone — how many geographies each source
-- covers, split by geo type. Demonstrates the aggregate/marts nature of gold.

with dim as (

    select * from {{ ref('ingot_dim_geo') }}

)

select
    geo_zone,
    count(*)                                          as geo_count,
    count(*) filter (where geo_type = 'CITY')         as city_count,
    count(*) filter (where geo_type = 'STATE')        as state_count,
    count(*) filter (where geo_type = 'REGION')       as region_count,
    count(*) filter (where is_kantar_covered)         as kantar_covered_count,
    count(*) filter (where is_nielsen_source)         as nielsen_count,
    count(*) filter (where is_price_tracker_source)   as price_tracker_count
from dim
group by geo_zone
order by geo_zone
