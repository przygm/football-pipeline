{% macro market_predicted_result(home_odds, away_odds, draw_odds) %}
    CASE
        WHEN {{ home_odds }} < {{ away_odds }}
         AND {{ home_odds }} < {{ draw_odds }} THEN 'HOME_WIN'
        WHEN {{ away_odds }} < {{ home_odds }}
         AND {{ away_odds }} < {{ draw_odds }} THEN 'AWAY_WIN'
        ELSE 'DRAW'
    END
{% endmacro %}