WITH base AS (

    SELECT
        data,
        batch_id,
        loaded_at
    FROM {{ source('bronze', 'odds_raw') }}
),

teams AS (

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
    FROM base b,
    LATERAL FLATTEN(input => b.data:teams) t
),

pivoted AS (

    SELECT
        odds_event_id,
        MAX(CASE WHEN is_home THEN team_name END) AS home_team_name,
        MAX(CASE WHEN is_away THEN team_name END) AS away_team_name,
        MAX(CASE WHEN is_home THEN team_id END) AS home_team_odds_id,
        MAX(CASE WHEN is_away THEN team_id END) AS away_team_odds_id,
        MAX(event_at_utc) AS event_at_utc,
        MAX(REPLACE(raw_status, 'STATUS_', '')) AS match_status,
        MAX(home_goals) AS home_goals,
        MAX(away_goals) AS away_goals,
        MAX(venue_name) AS venue_name,
        MAX(season_name) AS season_name,
        MAX(sport_id) AS sport_id,
        MAX(batch_id) AS batch_id,
        MAX(loaded_at) AS loaded_at
    FROM teams
    GROUP BY odds_event_id
),

deduplicated AS (

    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY odds_event_id
               ORDER BY loaded_at DESC
           ) AS rn
    FROM pivoted
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
FROM deduplicated
WHERE rn = 1