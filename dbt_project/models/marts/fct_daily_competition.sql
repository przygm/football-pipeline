SELECT
    d.calendar_date,
    d.day_name,
    d.is_weekend,
    c.competition_name,
    COUNT(*) AS matches_count,
    AVG(m.home_score + m.away_score) AS avg_goals
FROM {{ ref('fct_matches') }} m
JOIN {{ ref('map_competitions') }} c ON m.competition_code = c.competition_code
JOIN {{ ref('dim_date') }} d ON m.match_date_pl = d.calendar_date
WHERE m.match_status = 'FINISHED'
GROUP BY 1, 2, 3, 4