WITH matches_base AS (
    SELECT
        match_id, match_at_utc, competition_code, season_name, match_status,
        home_team_norm, away_team_norm,
        home_score, away_score,
        batch_id, loaded_at
    FROM {{ ref('int_matches_with_odds') }}
    WHERE match_status = 'FINISHED'
),

unpivoted AS (
    SELECT
        match_id,  
        match_at_utc, 
        competition_code, 
        season_name,
        batch_id, 
        loaded_at,
        team_perspective,
        CASE team_perspective
            WHEN 'HOME' THEN home_team_norm
            WHEN 'AWAY' THEN away_team_norm
        END AS team,
        CASE team_perspective
            WHEN 'HOME' THEN away_team_norm
            WHEN 'AWAY' THEN home_team_norm
        END AS opponent,
        CASE team_perspective
            WHEN 'HOME' THEN home_score
            WHEN 'AWAY' THEN away_score
        END AS goals_for,
        CASE team_perspective
            WHEN 'HOME' THEN away_score
            WHEN 'AWAY' THEN home_score
        END AS goals_against
    FROM matches_base
    CROSS JOIN (SELECT 'HOME' AS team_perspective
                UNION ALL SELECT 'AWAY') AS perspectives
)

SELECT
    {{ dbt_utils.generate_surrogate_key(['match_id', 'team']) }} AS team_match_pk,
    match_id,
    match_at_utc,
    competition_code,
    season_name,
    team,
    opponent,
    team_perspective AS match_location,
    goals_for,
    goals_against,
    goals_for - goals_against AS goal_differential,
    {{ target.schema }}_UTIL.GET_POINTS(goals_for, goals_against) AS points,
    CASE
        WHEN {{ target.schema }}_UTIL.GET_POINTS(goals_for, goals_against) = 3 THEN 'WIN'
        WHEN {{ target.schema }}_UTIL.GET_POINTS(goals_for, goals_against) = 1 THEN 'DRAW'
        ELSE 'LOSS'
    END AS match_result,
    batch_id,
    loaded_at
FROM unpivoted