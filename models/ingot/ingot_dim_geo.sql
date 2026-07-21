-- ingot (gold): business-facing geography dimension.
-- One clean row per geography with a consolidated source-coverage label,
-- ready for BI / joins from fact tables.

with alloy as (

    select * from {{ ref('alloy_geo') }}

)

select
    geo_key,
    geo_name,
    geo_type,
    geo_zone,
    state,
    nielsen_region,
    internal_sales_region,
    is_kantar_covered,
    is_nielsen_source,
    is_price_tracker_source,
    primary_spelling,

    -- single label describing which source(s) cover this geography
    case
        when is_nielsen_source and is_price_tracker_source then 'BOTH'
        when is_nielsen_source                             then 'NIELSEN'
        when is_price_tracker_source                       then 'PRICE_TRACKER'
        else 'NONE'
    end as source_coverage

from alloy
