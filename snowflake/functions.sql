SET env_prefix = 'PROD';    

SET schema_name = $env_prefix || '_UTIL';

USE DATABASE FOOTBALL_DB;

CREATE SCHEMA IF NOT EXISTS IDENTIFIER($schema_name);
USE SCHEMA IDENTIFIER($schema_name);


-- =======================================================================================
CREATE OR REPLACE FUNCTION GET_MATCH_RESULT(
    HOME_SCORE NUMBER,
    AWAY_SCORE NUMBER
)
RETURNS STRING
AS
$$
    CASE
        WHEN HOME_SCORE IS NULL OR AWAY_SCORE IS NULL THEN NULL 
        WHEN HOME_SCORE > AWAY_SCORE THEN 'HOME_WIN'
        WHEN AWAY_SCORE > HOME_SCORE THEN 'AWAY_WIN'
        ELSE 'DRAW'
    END
$$;

-- =======================================================================================
CREATE OR REPLACE FUNCTION GET_POINTS(
    team_score NUMBER,
    opponent_score NUMBER
)
RETURNS NUMBER
AS
$$
    CASE
        WHEN team_score IS NULL OR opponent_score IS NULL THEN NULL
        WHEN team_score > opponent_score THEN 3
        WHEN team_score = opponent_score THEN 1
        ELSE 0
    END
$$;


-- =======================================================================================
