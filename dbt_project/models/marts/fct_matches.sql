with localized AS (

    SELECT
        *,
        {{ utc_to_pl('match_at_utc') }} AS match_at_pl

    FROM {{ ref('int_matches_with_odds') }}
)

SELECT
    match_id,
    competition,

    match_at_utc,
    match_at_pl,
    CAST(match_at_pl AS DATE) AS match_date_pl,
    TO_CHAR(match_at_pl, 'HH24:MI') AS match_time_pl,

    home_team_name,
    away_team_name,

    home_score,
    away_score,

    CASE
        WHEN home_score > away_score THEN 'HOME_WIN'
        WHEN away_score > home_score THEN 'AWAY_WIN'
        ELSE 'DRAW'
    END AS result

FROM localized

ORDER BY competition, match_date_pl DESC, match_time_pl DESC