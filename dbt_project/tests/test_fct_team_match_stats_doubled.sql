SELECT
    match_id,
    COUNT(*) AS row_count
FROM {{ ref('fct_team_match_stats') }}
GROUP BY match_id
HAVING COUNT(*) != 2