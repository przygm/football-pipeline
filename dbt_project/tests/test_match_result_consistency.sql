SELECT
    match_id,
    home_score,
    away_score,
    result
FROM {{ ref('fct_matches') }}
WHERE result IS NOT NULL  
  AND match_status = 'FINISHED'  
  AND (
    (home_score > away_score AND result != 'HOME_WIN') OR
    (away_score > home_score AND result != 'AWAY_WIN') OR
    (home_score = away_score AND result != 'DRAW')
  )