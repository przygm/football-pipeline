import os

# Definicja PEŁNEJ struktury i zawartości na podstawie wszystkich 20 punktów
project_files = {
    # 1. ROOT CONFIGS
    "dbt_project.yml": """
name: 'football_analytics'
version: '1.0.0'
config-version: 2

profile: 'football_analytics'

model-paths: ["models"]
seed-paths: ["seeds"]
test-paths: ["tests"]

models:
  football_analytics:
    staging:
      +materialized: view
      +schema: SILVER
    intermediate:
      +materialized: table
      +schema: SILVER
    marts:
      +materialized: table
      +schema: GOLD

seeds:
  football_analytics:
    +schema: SILVER
""",
    "packages.yml": """
packages:
  - package: dbt-labs/dbt_utils
    version: 1.1.1
""",

    # 3. STAGING - FOOTBALL SOURCES
    "models/staging/football/football_sources.yml": """
version: 2
sources:
  - name: bronze
    database: FOOTBALL_DB
    schema: BRONZE
    tables:
      - name: matches_raw
      - name: teams_raw
""",
    # 4. STAGING - ODDS SOURCES
    "models/staging/odds/odds_sources.yml": """
version: 2
sources:
  - name: bronze
    database: FOOTBALL_DB
    schema: BRONZE
    tables:
      - name: odds_raw
""",
    # 5. stg_matches.sql
    "models/staging/football/stg_matches.sql": """
SELECT
    data:id::integer                 AS match_id,
    data:utcDate::timestamp          AS match_date_utc,
    data:status::string              AS match_status,
    data:homeTeam:id::integer        AS home_team_id,
    data:homeTeam:name::string       AS home_team_name,
    data:awayTeam:id::integer        AS away_team_id,
    data:awayTeam:name::string       AS away_team_name,
    data:score:fullTime:home::int    AS home_score,
    data:score:fullTime:away::int    AS away_score,
    competition,
    batch_id,
    loaded_at
FROM {{ source('bronze', 'matches_raw') }}
""",
    # 6. stg_teams.sql
    "models/staging/football/stg_teams.sql": """
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
""",
    # 7. stg_odds.sql
    "models/staging/odds/stg_odds.sql": """
SELECT
    data:event_id::integer           AS event_id,
    data:teams[0]::string            AS home_team,
    data:teams[1]::string            AS away_team,
    data:commence_time::timestamp    AS event_time,
    data:sites_count::integer        AS bookmakers_count,
    sport,
    event_date,
    batch_id,
    loaded_at
FROM {{ source('bronze', 'odds_raw') }}
""",
    # 8. stg_matches.yml
    "models/staging/football/stg_matches.yml": """
version: 2
models:
  - name: stg_matches
    columns:
      - name: match_id
        tests:
          - unique
          - not_null
      - name: match_date_utc
        tests:
          - not_null
      - name: home_team_name
        tests:
          - not_null
      - name: away_team_name
        tests:
          - not_null
""",
    # 9. stg_odds.yml
    "models/staging/odds/stg_odds.yml": """
version: 2
models:
  - name: stg_odds
    columns:
      - name: home_team
        tests:
          - not_null
      - name: away_team
        tests:
          - not_null
""",
    "models/staging/staging.yml": "",

    # 10 & 11. SEEDS
    "seeds/map_teams.csv": """football_api_name,odds_api_name
Arsenal FC,Arsenal
Manchester City FC,Manchester City
FC Barcelona,Barcelona
Inter Milan,Inter
""",
    "seeds/seeds.yml": """
version: 2
seeds:
  - name: map_teams
    columns:
      - name: football_api_name
        tests:
          - unique
          - not_null
      - name: odds_api_name
        tests:
          - not_null
""",

    # 12. int_team_mapping.sql
    "models/intermediate/int_team_mapping.sql": """
SELECT *
FROM {{ ref('map_teams') }}
""",
    # 13. int_matches_normalized.sql
    "models/intermediate/int_matches_normalized.sql": """
WITH matches AS (
    SELECT * FROM {{ ref('stg_matches') }}
),
mapping AS (
    SELECT * FROM {{ ref('int_team_mapping') }}
)
SELECT
    m.*,
    COALESCE(mt1.odds_api_name, m.home_team_name) AS home_team_norm,
    COALESCE(mt2.odds_api_name, m.away_team_name) AS away_team_norm
FROM matches m
LEFT JOIN mapping mt1 ON m.home_team_name = mt1.football_api_name
LEFT JOIN mapping mt2 ON m.away_team_name = mt2.football_api_name
""",
    # 14. int_matches_with_odds.sql
    "models/intermediate/int_matches_with_odds.sql": """
WITH matches AS (
    SELECT * FROM {{ ref('int_matches_normalized') }}
),
odds AS (
    SELECT * FROM {{ ref('stg_odds') }}
)
SELECT
    m.*,
    o.bookmakers_count,
    o.event_time
FROM matches m
LEFT JOIN odds o
    ON m.home_team_norm = o.home_team
   AND m.away_team_norm = o.away_team
""",
    # 15. intermediate.yml
    "models/intermediate/intermediate.yml": """
version: 2
models:
  - name: int_matches_with_odds
    columns:
      - name: match_id
        tests:
          - unique
          - not_null
""",

    # 16. gold_matches.sql
    "models/marts/gold_matches.sql": """
SELECT
    match_id,
    competition,
    match_date_utc,
    home_team_name,
    away_team_name,
    home_score,
    away_score,
    bookmakers_count,
    CASE
        WHEN home_score > away_score THEN 'HOME_WIN'
        WHEN away_score > home_score THEN 'AWAY_WIN'
        ELSE 'DRAW'
    END AS result
FROM {{ ref('int_matches_with_odds') }}
""",
    # 17. gold_daily_competition_stats.sql
    "models/marts/gold_daily_competition_stats.sql": """
SELECT
    DATE(match_date_utc) AS match_day,
    competition,
    COUNT(*) AS matches_count,
    AVG(bookmakers_count) AS avg_bookmakers
FROM {{ ref('gold_matches') }}
GROUP BY 1,2
""",
    # 18. marts.yml
    "models/marts/marts.yml": """
version: 2
models:
  - name: gold_matches
    columns:
      - name: match_id
        tests:
          - unique
          - not_null
""",

    # 19 & 20. CUSTOM TESTS
    "tests/test_duplicate_matches.sql": """
SELECT
    match_id,
    COUNT(*)
FROM {{ ref('gold_matches') }}
GROUP BY 1
HAVING COUNT(*) > 1
""",
    "tests/test_missing_odds.sql": """
SELECT *
FROM {{ ref('gold_matches') }}
WHERE bookmakers_count IS NULL
"""
}

def create_dbt_project():
    root_name = "dbt_project"
    base_path = os.path.join(os.getcwd(), root_name)
    print(f"Tworzę projekt dbt w: {base_path}")

    for rel_path, content in project_files.items():
        target_path = os.path.join(base_path, rel_path)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"  [UTWORZONO] {rel_path}")

if __name__ == "__main__":
    create_dbt_project()
    print("\nGotowe! Struktura została wygenerowana.")