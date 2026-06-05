{{ config(
    materialized='incremental',
    unique_key='match_id',
    incremental_strategy='merge'
) }}

with source_data as (
    SELECT *
    FROM {{ ref('int_matches_with_odds') }}

    {% if is_incremental() %}
       where match_at_utc >= (select DATEADD(day, -1, max(match_at_utc)) from {{ this }})
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
    competition_code,
    match_at_utc,
    match_at_pl,
    CAST(match_at_pl AS DATE) AS match_date_pl,
    TO_CHAR(match_at_pl, 'HH24:MI') AS match_time_pl,
    home_team_name,
    away_team_name,
    home_score,
    away_score,
    match_status,
    {{ target.schema }}_UTIL.GET_MATCH_RESULT(home_score, away_score) AS result,
    odds_event_id,
    loaded_at
FROM localized