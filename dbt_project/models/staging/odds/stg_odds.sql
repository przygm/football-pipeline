WITH source_data AS (

	SELECT
		data:event_id::string AS odds_event_id,

		data:event_date::timestamp_ntz AS event_at_utc,

		data:teams[1].name::string AS home_team_name,
		data:teams[0].name::string AS away_team_name,

		data:teams[1].team_id::integer AS home_team_odds_id,
		data:teams[0].team_id::integer AS away_team_odds_id,

		replace(data:score:event_status::string, 'STATUS_', '') AS match_status,

		data:score:score_home::integer AS home_goals,
		data:score:score_away::integer AS away_goals,

		data:score:venue_name::string AS venue_name,

		data:schedule:season_type::string AS season_name,

		data:sport_id::integer AS sport_id,

		batch_id,
		loaded_at

	FROM {{ source('bronze', 'odds_raw') }}	
),

deduplicated AS (

    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY odds_event_id
               ORDER BY loaded_at DESC
           ) AS rn
    FROM source_data
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