{#
    Custom schema resolution.

    dbt's default prepends the target schema (e.g. `public_ore`). We instead
    use the +schema value from dbt_project.yml verbatim (`ore`, `alloy`,
    `ingot`), so physical schemas match the medallion layer names exactly.

    If a model sets no custom schema, fall back to the profile's default schema.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
