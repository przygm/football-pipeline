{% macro utc_to_pl(column_name) %}
    CONVERT_TIMEZONE(
        'UTC',
        'Europe/Warsaw',
        {{ column_name }}
    )
{% endmacro %}