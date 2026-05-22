SELECT
    team,
    competition,
    match_at_utc,
    match_result,
    points,

    SUM(points) OVER (
        PARTITION BY team, competition
        ORDER BY match_at_utc
        ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
    ) AS points_last_5,

    AVG(goals_for) OVER (
        PARTITION BY team, competition
        ORDER BY match_at_utc
        ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
    ) AS avg_goals_last_5,

    ROW_NUMBER() OVER (
        PARTITION BY team, competition
        ORDER BY match_at_utc DESC
    ) AS match_number_desc

FROM {{ ref('fct_team_match_stats') }}