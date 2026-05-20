WITH source_data AS (

    SELECT
        data:id::integer                 AS match_id,
		
        data:utcDate::timestamp_ntz      AS match_at_utc,

        data:status::string              AS match_status,
		
        data:homeTeam:name::string       AS home_team_name,
        data:homeTeam:id::integer        AS home_team_id,
		
        data:awayTeam:name::string       AS away_team_name,
		data:awayTeam:id::integer        AS away_team_id,
		
        data:score:fullTime:home::int    AS home_score,
        data:score:fullTime:away::int    AS away_score,
		
        competition,
		
        batch_id,
        loaded_at

    FROM {{ source('bronze', 'matches_raw') }}
),

deduplicated AS (

    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY match_id
               ORDER BY loaded_at DESC
           ) AS rn
    FROM source_data
)

SELECT 
    match_id,
    match_at_utc,
    match_status,
    home_team_id,
    home_team_name,
    away_team_id,
    away_team_name,
    home_score,
    away_score,
    competition,
    batch_id,
    loaded_at
FROM deduplicated
WHERE rn = 1