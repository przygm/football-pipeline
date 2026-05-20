WITH current_odds_names AS (
    SELECT DISTINCT home_team_name AS odds_api_name FROM {{ ref('stg_odds') }}
    UNION
    SELECT DISTINCT away_team_name AS odds_api_name FROM {{ ref('stg_odds') }}
),

missing_from_seed AS (
    SELECT o.odds_api_name
    FROM current_odds_names o
    LEFT JOIN {{ ref('map_teams') }} m  ON o.odds_api_name = m.odds_api_name
    WHERE m.odds_api_name IS NULL
),

official_teams AS (
    SELECT DISTINCT team_name AS football_api_name  FROM {{ ref('stg_teams') }}
),

scored_proposals AS (
    SELECT 
        m.odds_api_name,
        t.football_api_name,
        CASE 
            WHEN LOWER(TRIM(t.football_api_name)) = LOWER(TRIM(m.odds_api_name))
            THEN 100
            WHEN CONTAINS(LOWER(t.football_api_name), LOWER(m.odds_api_name)) 
              OR CONTAINS(LOWER(m.odds_api_name), LOWER(t.football_api_name)) 
            THEN 95 
            ELSE JAROWINKLER_SIMILARITY(m.odds_api_name, t.football_api_name) 
        END AS confidence
    FROM missing_from_seed m
    CROSS JOIN official_teams t
)

SELECT 
    odds_api_name,
    football_api_name AS proposed_football_api_name,
    confidence
FROM scored_proposals
QUALIFY ROW_NUMBER() OVER (PARTITION BY odds_api_name ORDER BY confidence DESC) = 1
ORDER BY confidence DESC