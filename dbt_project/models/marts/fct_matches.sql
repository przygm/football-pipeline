{{ config(
    materialized='incremental',
    unique_key='match_id'
) }}

with source_data as (

    SELECT *
    FROM {{ ref('int_matches_with_odds') }}

    {% if is_incremental() %}
        WHERE loaded_at >= (SELECT MAX(loaded_at) FROM {{ this }})
    {% endif %}
),

localized AS (

    SELECT
        *,
        {{ utc_to_pl('match_at_utc') }} AS match_at_pl
    FROM source_data
)

SELECT
    match_id,
    competition,
    match_at_utc,
    match_at_pl,
    CAST(match_at_pl AS DATE) AS match_date_pl,
    TO_CHAR(match_at_pl, 'HH24:MI') AS match_time_pl,
    home_team_name,
    away_team_name,
    home_score,
    away_score,
    match_status,
    FOOTBALL_DB.UTIL.GET_MATCH_RESULT(home_score, away_score) AS result,
    loaded_at
FROM localized
ORDER BY competition, match_date_pl DESC, match_time_pl DESC