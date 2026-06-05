WITH matches AS (
    SELECT * FROM {{ ref('int_matches_normalized') }}
),

odds AS (
    SELECT 
        o.*,
        COALESCE(mh.canonical_name, o.home_team_name) AS home_team_canon,
        COALESCE(ma.canonical_name, o.away_team_name) AS away_team_canon
    FROM {{ ref('stg_odds_events') }} o
    LEFT JOIN {{ ref('map_teams') }} mh ON o.home_team_name = mh.odds_api_name
    LEFT JOIN {{ ref('map_teams') }} ma ON o.away_team_name = ma.odds_api_name
)

SELECT
    m.*,
    o.odds_event_id,
    o.match_status AS odds_match_status,
    o.home_goals,
    o.away_goals,
    o.venue_name,
    o.season_name,
    o.event_at_utc AS odds_event_at_utc
FROM matches m
LEFT JOIN odds o
    ON m.home_team_norm = o.home_team_canon   
   AND m.away_team_norm = o.away_team_canon 
   AND CAST(o.event_at_utc AS DATE) 
       BETWEEN DATEADD(day,-2, CAST(m.match_at_utc AS DATE))  AND  DATEADD(day, 2, CAST(m.match_at_utc AS DATE))
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY m.match_id 
    ORDER BY ABS(DATEDIFF('minute', m.match_at_utc, o.event_at_utc)) ASC
) = 1   