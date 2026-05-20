WITH matches AS (
    SELECT * FROM {{ ref('int_matches_normalized') }}
),

mapping AS (
    SELECT * FROM {{ ref('int_team_mapping') }}
),

odds AS (
    SELECT * FROM {{ ref('stg_odds') }}
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

LEFT JOIN mapping map_h
    ON m.home_team_norm = map_h.football_api_name

LEFT JOIN mapping map_a
    ON m.away_team_norm = map_a.football_api_name

LEFT JOIN odds o
    ON COALESCE(map_h.odds_api_name, m.home_team_norm) = o.home_team_name
   AND COALESCE(map_a.odds_api_name, m.away_team_norm) = o.away_team_name