-- ore (bronze): raw geography master, 1:1 with source.
-- No business logic. Only: trim whitespace and coerce empty strings to NULL so
-- downstream layers get clean, consistent nulls. Types stay as-is (text).

with source as (

    select * from {{ source('cbt_analytics', 'geo_master1') }}

),

renamed as (

    select
        nullif(trim(geo_key), '')           as geo_key,
        nullif(trim(geo_name), '')          as geo_name,
        nullif(trim(geo_type), '')          as geo_type,
        nullif(trim(geo_zone), '')          as geo_zone,
        nullif(trim(state), '')             as state,
        nullif(trim(nielsen_region), '')    as nielsen_region,
        nullif(trim(kantar_covered), '')    as kantar_covered,
        nullif(trim(internal_sales), '')    as internal_sales,
        nullif(trim(src_nielsen), '')       as src_nielsen,
        nullif(trim(src_price_tracker), '') as src_price_tracker,
        nullif(trim(nielsen_file), '')      as nielsen_file,
        nullif(trim(raw_spellings), '')     as raw_spellings
    from source

)

select * from renamed
