SELECT DISTINCT
    competition AS competition_code,
    CASE competition
        WHEN 'PL' THEN 'Premier League'
        WHEN 'BL1' THEN 'Bundesliga'
        WHEN 'PD' THEN 'La Liga'
        WHEN 'SA' THEN 'Serie A'
        WHEN 'CL' THEN 'Champions League'
        ELSE competition
    END AS competition_name
FROM {{ ref('stg_matches') }}
ORDER BY competition_code