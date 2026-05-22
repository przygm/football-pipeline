-- diag_missing_participant_mappings.sql
WITH event_teams AS (
    SELECT DISTINCT home_team_name AS team_name 
    FROM {{ ref('stg_odds_events') }}
    UNION
    SELECT DISTINCT away_team_name 
    FROM {{ ref('stg_odds_events') }}
),

unmatched_participants AS (
    SELECT DISTINCT ml.participant_name_raw
    FROM {{ ref('stg_odds_market_lines') }} ml
    LEFT JOIN event_teams e 
        ON ml.participant_name_raw = e.team_name
    LEFT JOIN {{ ref('map_participants') }} mp 
        ON ml.participant_name_raw = mp.participant_name_raw
    WHERE ml.participant_type = 'TYPE_TEAM'
      AND NULLIF(ml.participant_name_raw, '') IS NOT NULL
      AND e.team_name IS NULL
      AND mp.participant_name_raw IS NULL
)

SELECT 
    u.participant_name_raw AS unmatched_name,
    t.team_name AS proposed_match,
    JAROWINKLER_SIMILARITY(u.participant_name_raw, t.team_name) AS confidence
FROM unmatched_participants u
CROSS JOIN event_teams t
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY u.participant_name_raw
    ORDER BY JAROWINKLER_SIMILARITY(u.participant_name_raw, t.team_name) DESC
) = 1
ORDER BY confidence DESC