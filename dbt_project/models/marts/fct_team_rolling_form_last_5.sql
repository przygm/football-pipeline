WITH match_history AS (
    SELECT 
        match_id,
        match_at_utc,
        competition_code,
        team,
        opponent,
        match_location,
        goals_for,
        goals_against,
        match_result,
        points
    FROM {{ ref('fct_team_match_stats') }}
),

rolling_metrics AS (
    SELECT 
        *,
        ROUND(AVG(goals_for) OVER (
            PARTITION BY team
            ORDER BY match_at_utc, match_id
            ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
        ), 2) AS avg_goals_scored_previous_5_matches,

        ROUND(AVG(goals_against) OVER (
            PARTITION BY team
            ORDER BY match_at_utc, match_id
            ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
        ), 2) AS avg_goals_conceded_previous_5_matches,

        SUM(points) OVER (
            PARTITION BY team
            ORDER BY match_at_utc, match_id
            ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
        ) AS points_previous_5_matches
    FROM match_history
),

streaks_base AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (PARTITION BY team ORDER BY match_at_utc, match_id) -
        ROW_NUMBER() OVER (PARTITION BY team,  match_result ORDER BY match_at_utc, match_id) AS streak_group
    FROM rolling_metrics
),

streaks_calculated AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (
            PARTITION BY team,  match_result, streak_group 
            ORDER BY match_at_utc, match_id
        ) AS current_streak_length
    FROM streaks_base
)

SELECT 
    match_id,
    match_at_utc,
    competition_code,
    team,
    opponent,
    match_location,
    match_result,
    goals_for,
    goals_against,
    avg_goals_scored_previous_5_matches,
    avg_goals_conceded_previous_5_matches,
    points_previous_5_matches,
    match_result AS current_streak_result,
    current_streak_length
FROM streaks_calculated