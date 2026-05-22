CREATE OR REPLACE FUNCTION FOOTBALL_DB.UTIL.GET_MATCH_RESULT(
    HOME_SCORE NUMBER,
    AWAY_SCORE NUMBER
)
RETURNS STRING
AS
$$
    CASE
        WHEN HOME_SCORE > AWAY_SCORE THEN 'HOME_WIN'
        WHEN AWAY_SCORE > HOME_SCORE THEN 'AWAY_WIN'
        ELSE 'DRAW'
    END
$$;

-- =======================================================================================

CREATE OR REPLACE FUNCTION FOOTBALL_DB.UTIL.GET_POINTS(
    team_score NUMBER,
    opponent_score NUMBER
)
RETURNS NUMBER
AS
$$
    CASE
        WHEN team_score > opponent_score THEN 3
        WHEN team_score = opponent_score THEN 1
        ELSE 0
    END
$$;

-- =======================================================================================
