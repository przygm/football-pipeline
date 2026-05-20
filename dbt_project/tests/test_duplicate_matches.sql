SELECT
    match_id,
    COUNT(*)
FROM {{ ref('fct_matches') }}
GROUP BY 1
HAVING COUNT(*) > 1