-- fct_match_vs_odds.sql
WITH matches AS (
    SELECT 
        m.*,
        i.odds_event_id -- Pobieramy brakujący identyfikator z modelu intermediate
    FROM {{ ref('fct_matches') }} m
    LEFT JOIN {{ ref('int_matches_with_odds') }} i ON m.match_id = i.match_id
    WHERE m.result IS NOT NULL
),

odds_events AS (
    SELECT
        odds_event_id,
        home_team_name  AS odds_home_team,
        away_team_name  AS odds_away_team,
        home_goals      AS odds_home_goals,
        away_goals      AS odds_away_goals
    FROM {{ ref('stg_odds_events') }}
),

moneyline AS (
    SELECT
        odds_event_id,
        participant_name,
        AVG(odds_price) AS avg_closing_price    
    FROM {{ ref('stg_odds_market_lines') }}
    WHERE market_id = 1
      AND odds_closed_at IS NOT NULL
    GROUP BY 1, 2
),

moneyline_pivoted AS (
    SELECT
        odds_event_id,
        MAX(CASE WHEN participant_name = 'Draw'      THEN avg_closing_price END) AS draw_odds,
        MAX(CASE WHEN participant_type_home = TRUE   THEN avg_closing_price END) AS home_odds,
        MAX(CASE WHEN participant_type_away = TRUE   THEN avg_closing_price END) AS away_odds
    FROM (
        SELECT ml.*, 
               (ml.participant_name = e.odds_home_team) AS participant_type_home,
               (ml.participant_name = e.odds_away_team) AS participant_type_away
        FROM moneyline ml
        JOIN odds_events e USING (odds_event_id)
    )
    GROUP BY 1
)

SELECT
    m.match_id,
    m.competition,
    m.match_date_pl,
    m.home_team_name,
    m.away_team_name,
    m.home_score,
    m.away_score,
    m.result                                  AS actual_result,
    p.home_odds,
    p.away_odds,
    p.draw_odds,
    
    -- implied probability from American
    {{ implied_probability('p.home_odds') }}  AS home_implied_prob,
    {{ implied_probability('p.away_odds') }}  AS away_implied_prob,
    {{ implied_probability('p.draw_odds') }}  AS draw_implied_prob,

    -- who was favourite according to the odds?
    CASE
        WHEN p.home_odds IS NULL OR p.away_odds IS NULL OR p.draw_odds IS NULL 
        THEN NULL
        ELSE {{ market_predicted_result('p.home_odds', 'p.away_odds', 'p.draw_odds') }}
    END AS market_predicted_result,

    -- if market_predicted_result matches actual result
    CASE
        WHEN p.home_odds IS NULL OR p.away_odds IS NULL OR p.draw_odds IS NULL 
        THEN NULL
        WHEN {{ market_predicted_result('p.home_odds', 'p.away_odds', 'p.draw_odds') }} = m.result 
        THEN TRUE
        ELSE FALSE
    END AS market_correct,

    (p.home_odds IS NOT NULL  AND  p.away_odds IS NOT NULL  AND  p.draw_odds IS NOT NULL) AS has_complete_odds

FROM matches m
LEFT JOIN moneyline_pivoted p ON m.odds_event_id = p.odds_event_id