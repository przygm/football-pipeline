SELECT
    match_date_pl,
    competition,
    COUNT(*) AS matches_count,
    AVG(home_score + away_score) AS avg_goals
FROM {{ ref('fct_matches') }}
GROUP BY 1,2
ORDER BY match_date_pl DESC, competition