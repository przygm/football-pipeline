WITH source_data AS (

    SELECT
        data:id::integer             AS team_id,
        data:name::string            AS team_name,
        data:shortName::string       AS short_name,
        data:tla::string             AS tla,
        data:area:name::string       AS country,
        competition,
        batch_id,
        loaded_at
    FROM {{ source('bronze', 'teams_raw') }}
),

deduplicated AS (

    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY competition, team_id
               ORDER BY loaded_at DESC
           ) AS rn
    FROM source_data
)

SELECT 
    team_id,
    team_name,
    short_name,
    tla,
    country,
    competition,
    batch_id,
    loaded_at
FROM deduplicated
WHERE rn = 1