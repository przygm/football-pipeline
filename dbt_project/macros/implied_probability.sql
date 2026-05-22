{% macro implied_probability(odds_col) %}
    CASE
        WHEN {{ odds_col }} < 0
            THEN ABS({{ odds_col }}) / (ABS({{ odds_col }}) + 100.0)
        WHEN {{ odds_col }} > 0
            THEN 100.0 / ({{ odds_col }} + 100.0)
        ELSE NULL
    END
{% endmacro %}