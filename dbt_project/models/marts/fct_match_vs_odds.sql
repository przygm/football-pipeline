WITH matches AS (
    SELECT  
        match_id,
        competition_code,
        match_at_utc,
        match_date_pl,
        home_team_name,
        away_team_name,
        home_score,
        away_score,
        result AS actual_result,
        odds_event_id
    FROM {{ ref('fct_matches') }}
    WHERE result IS NOT NULL
),

odds_teams AS (
    SELECT
        odds_event_id,
        LOWER(TRIM(home_team_name)) AS odds_home_team,
        LOWER(TRIM(away_team_name)) AS odds_away_team
    FROM {{ ref('stg_odds_events') }}

),

latest_market_lines AS (
    SELECT
        ml.odds_event_id,
        LOWER(TRIM(ml.participant_name)) AS participant_name,
        ml.sportsbook_id,
        ml.decimal_price,
        ml.odds_updated_at
    FROM {{ ref('stg_odds_market_lines') }} ml
    INNER JOIN matches m 
        ON ml.odds_event_id = m.odds_event_id
    WHERE ml.market_id = 1
      AND ml.odds_updated_at < m.match_at_utc
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY 
            ml.odds_event_id,
            LOWER(TRIM(ml.participant_name)),
            ml.sportsbook_id
        ORDER BY ml.odds_updated_at DESC
    ) = 1
),

market_consensus_odds AS (
    SELECT
        odds_event_id,
        participant_name,
        AVG(decimal_price) AS avg_decimal_odds
    FROM latest_market_lines
    GROUP BY 1,2
),

moneyline_pivoted AS (
    SELECT
        m.odds_event_id,
        MAX(CASE WHEN participant_name = 'draw'           THEN avg_decimal_odds END) AS draw_odds,
        MAX(CASE WHEN participant_name = t.odds_home_team THEN avg_decimal_odds END) AS home_odds,
        MAX(CASE WHEN participant_name = t.odds_away_team THEN avg_decimal_odds END) AS away_odds
    FROM market_consensus_odds m
    INNER JOIN odds_teams t
        ON m.odds_event_id = t.odds_event_id
    GROUP BY m.odds_event_id

),

prediction_applied AS (
    SELECT
        m.match_id,
        m.competition_code,
        m.match_date_pl,
        m.home_team_name,
        m.away_team_name,
        m.home_score,
        m.away_score,
        m.actual_result,
        p.home_odds,
        p.away_odds,
        p.draw_odds,
        ROUND(1.0 / NULLIF(p.home_odds, 0), 4) AS home_implied_prob,
        ROUND(1.0 / NULLIF(p.away_odds, 0), 4) AS away_implied_prob,
        ROUND(1.0 / NULLIF(p.draw_odds, 0), 4) AS draw_implied_prob,
        ROUND(
            COALESCE(1.0 / NULLIF(p.home_odds, 0), 0) +
            COALESCE(1.0 / NULLIF(p.away_odds, 0), 0) +
            COALESCE(1.0 / NULLIF(p.draw_odds, 0), 0),
            4
        ) AS market_overround,
        CASE WHEN p.home_odds IS NULL  OR  p.away_odds IS NULL  OR  p.draw_odds IS NULL THEN NULL
             WHEN p.home_odds < p.away_odds  AND  p.home_odds < p.draw_odds              THEN 'HOME_WIN'
             WHEN p.away_odds < p.home_odds  AND  p.away_odds < p.draw_odds              THEN 'AWAY_WIN'
             ELSE 'DRAW'
        END AS market_predicted_result,
        CASE WHEN p.home_odds IS NULL  OR  p.away_odds IS NULL  OR  p.draw_odds IS NULL THEN NULL
             WHEN p.home_odds < p.away_odds  AND  p.home_odds < p.draw_odds             THEN m.home_team_name
             WHEN p.away_odds < p.home_odds  AND  p.away_odds < p.draw_odds             THEN m.away_team_name
             ELSE 'DRAW'
        END AS market_favorite
    FROM matches m
    LEFT JOIN moneyline_pivoted p
        ON m.odds_event_id = p.odds_event_id
)

SELECT
    match_id,
    competition_code,
    match_date_pl,
    home_team_name,
    away_team_name,
    home_score,
    away_score,
    actual_result,
    home_odds,
    away_odds,
    draw_odds,
    home_implied_prob,
    away_implied_prob,
    draw_implied_prob,
    market_overround,
    market_predicted_result,
    market_favorite,
    CASE WHEN market_predicted_result IS NULL         THEN NULL
         WHEN market_predicted_result = actual_result THEN TRUE
         ELSE FALSE
    END AS market_correct,
    (home_odds IS NOT NULL  AND  away_odds IS NOT NULL  AND  draw_odds IS NOT NULL) AS has_complete_odds
FROM prediction_applied