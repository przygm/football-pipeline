WITH matches AS (
    SELECT * FROM {{ ref('stg_matches') }}
),

mapping AS (
    SELECT * FROM {{ ref('int_team_mapping') }}
)

SELECT
    m.*,
    COALESCE(mt1.odds_api_name, m.home_team_name) AS home_team_norm,
    COALESCE(mt2.odds_api_name, m.away_team_name) AS away_team_norm
FROM matches m
LEFT JOIN mapping mt1 ON m.home_team_name = mt1.football_api_name
LEFT JOIN mapping mt2 ON m.away_team_name = mt2.football_api_name