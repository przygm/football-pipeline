WITH base AS (
    SELECT
        data,
        batch_id,
        loaded_at
    FROM {{ source('bronze', 'odds_raw') }}
),

latest_events AS (
    SELECT *
    FROM base
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY data:event_id::string 
        ORDER BY loaded_at DESC
    ) = 1
),

teams_raw_extract AS (
    SELECT
        b.data:event_id::string AS odds_event_id,
        t.value:name::string AS team_name,
        t.value:team_id::integer AS team_id,
        t.value:is_home::boolean AS is_home,
        t.value:is_away::boolean AS is_away,
        b.data:event_date::timestamp_ntz AS event_at_utc,
        b.data:score:event_status::string AS raw_status,
        b.data:score:score_home::integer AS home_goals,
        b.data:score:score_away::integer AS away_goals,
        b.data:score:venue_name::string AS venue_name,
        b.data:schedule:season_type::string AS season_name,
        b.data:sport_id::integer AS sport_id,
        b.batch_id,
        b.loaded_at
    FROM latest_events b,
    LATERAL FLATTEN(input => b.data:teams) t
),

pivoted AS (
    SELECT
        odds_event_id,
        MAX(CASE WHEN is_home THEN team_name END) AS home_team_name,
        MAX(CASE WHEN is_away THEN team_name END) AS away_team_name,
        MAX(CASE WHEN is_home THEN team_id END) AS home_team_odds_id,
        MAX(CASE WHEN is_away THEN team_id END) AS away_team_odds_id,
        ANY_VALUE(event_at_utc) AS event_at_utc,
        ANY_VALUE(REPLACE(raw_status, 'STATUS_', '')) AS match_status,
        ANY_VALUE(home_goals) AS home_goals,
        ANY_VALUE(away_goals) AS away_goals,
        ANY_VALUE(venue_name) AS venue_name,
        ANY_VALUE(season_name) AS season_name,
        ANY_VALUE(sport_id) AS sport_id,
        ANY_VALUE(batch_id) AS batch_id,
        ANY_VALUE(loaded_at) AS loaded_at
    FROM teams_raw_extract
    GROUP BY odds_event_id
)

SELECT
    odds_event_id,
    event_at_utc,
    home_team_name,
    away_team_name,
    home_team_odds_id,
    away_team_odds_id,
    match_status,
    home_goals,
    away_goals,
    venue_name,
    season_name,
    sport_id,
    batch_id,
    loaded_at
FROM pivoted