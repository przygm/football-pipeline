WITH matches AS (
    SELECT * 
    FROM {{ ref('stg_matches') }}
),

mapping AS (
    SELECT * FROM {{ ref('map_teams') }}
)

SELECT
    m.match_id,
    m.match_at_utc,
    m.match_status,
    m.home_team_id,
    m.home_team_name,
    m.away_team_id,
    m.away_team_name,
    m.home_score,
    m.away_score,
    m.competition AS competition_code,
    m.batch_id,
    m.loaded_at,
    COALESCE(mt1.canonical_name, m.home_team_name) AS home_team_norm,
    COALESCE(mt2.canonical_name, m.away_team_name) AS away_team_norm    
FROM matches m
LEFT JOIN mapping mt1 ON m.home_team_name = mt1.football_api_name
LEFT JOIN mapping mt2 ON m.away_team_name = mt2.football_api_name
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY m.match_id
    ORDER BY mt1.canonical_name, mt2.canonical_name
) = 1