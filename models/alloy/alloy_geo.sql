-- alloy (silver): cleaned & conformed geography.
-- Standardizes casing, turns Y/NULL flags into real booleans, normalizes the
-- internal sales region to zone-style tokens, and parses raw_spellings
-- (which may be pipe-delimited, e.g. "KANO | Kano") into a variant array.

with ore as (

    select * from {{ ref('ore_geo_master') }}

),

conformed as (

    select
        geo_key,
        initcap(geo_name)                              as geo_name,
        upper(geo_type)                                as geo_type,
        upper(geo_zone)                                as geo_zone,
        initcap(state)                                 as state,
        nielsen_region,

        -- internal sales region uses spaces ("SOUTH WEST"); align to the
        -- underscore convention used by geo_zone ("SOUTH_WEST").
        upper(replace(internal_sales, ' ', '_'))       as internal_sales_region,

        -- source / coverage flags: 'Y' or NULL -> boolean
        (kantar_covered    is not null)                as is_kantar_covered,
        (src_nielsen       is not null)                as is_nielsen_source,
        (src_price_tracker is not null)                as is_price_tracker_source,

        nielsen_file,

        -- raw_spellings may hold several pipe-delimited variants.
        string_to_array(raw_spellings, '|')            as raw_spelling_variants,
        initcap(trim(split_part(raw_spellings, '|', 1))) as primary_spelling,

        -- "<Name> City" rows are finer-grained duplicates of a base city.
        (geo_name ilike '% City')                      as is_city_named_variant

    from ore

)

select * from conformed
