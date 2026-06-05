{% macro american_to_decimal(odds_col) %}
    CASE
        WHEN {{ odds_col }} < 0 THEN (100.0 / ABS({{ odds_col }})) + 1.0
        WHEN {{ odds_col }} > 0 THEN ({{ odds_col }} / 100.0) + 1.0
        ELSE NULL
    END
{% endmacro %}