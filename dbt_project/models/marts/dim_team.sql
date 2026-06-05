WITH teams AS (
    SELECT 
        team_id,
        team_name,
        short_name,
        tla,
        country
    FROM {{ ref('stg_teams') }}
),

mapping AS (
    SELECT DISTINCT 
        football_api_name,
        canonical_name
    FROM {{ ref('map_teams') }}
)

SELECT
    t.team_id,
    COALESCE(m.canonical_name, t.team_name) AS team_name,
    t.team_name AS raw_football_api_name, 
    t.short_name,
    t.tla,
    t.country
FROM teams t
LEFT JOIN mapping m  ON  t.team_name = m.football_api_name