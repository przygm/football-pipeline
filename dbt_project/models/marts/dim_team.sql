SELECT DISTINCT
    team_id,
    team_name,
    short_name,
    tla,
    country 
FROM {{ ref('stg_teams') }}
ORDER BY  team_name