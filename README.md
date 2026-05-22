# Football Analytics Pipeline (Snowflake)

## Overview
End-to-end data pipeline that ingests football match data and betting odds from external APIs, stores them in Snowflake, and transforms them using dbt into analytics-ready models.

The project demonstrates a full data engineering workflow: multi-source ingestion, layered storage (Bronze / Silver / Gold), transformation, data quality testing, and cloud-based orchestration.

It follows production-like patterns such as batch processing with unique batch IDs, idempotent ingestion, deduplication logic, and automated scheduling via GCP Cloud Run Jobs.

> **Note:** dbt transformations are still under active development.

## Tech stack
- Python (multi-source API ingestion, retry logic, logging, NDJSON serialization)
- Snowflake (data warehouse, Bronze / Silver / Gold architecture)
- dbt (transformations, tests, seeds, macros)
- GCP Cloud Run Jobs (pipeline orchestration via Flask + Gunicorn)
- Docker (containerization)

## Architecture

### Data flow

```
football-data.org API  ──┐
                         ├──▶ Python ingestion
TheRundown Odds API    ──┘         │
                                   │ PUT + COPY INTO
                                   ▼
                         ┌─────────────────────┐
                         │   SNOWFLAKE BRONZE   │
                         │   MATCHES_RAW        │
                         │   TEAMS_RAW          │
                         │   ODDS_RAW           │
                         └──────────┬──────────┘
                                    │ dbt run
                                    ▼
                         ┌─────────────────────┐
                         │   SILVER (dbt views  │
                         │   and tables)        │
                         │                      │
                         │   stg_matches        │
                         │   stg_teams          │
                         │   stg_odds_events    │
                         │   stg_odds_market_   │
                         │     lines            │
                         │                      │
                         │   int_matches_       │
                         │     normalized       │
                         │   int_matches_       │
                         │     with_odds        │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   GOLD (dbt tables)  │
                         │                      │
                         │   fct_matches        │
                         │   fct_match_vs_odds  │
                         │   fct_team_match_    │
                         │     stats            │
                         │   fct_team_form      │
                         │   fct_daily_         │
                         │     competition      │
                         │   dim_team           │
                         │   dim_competition    │
                         └─────────────────────┘
```

### Layers
- **BRONZE** – Raw VARIANT data loaded directly from APIs, with `batch_id` and `loaded_at`
- **SILVER** – Staging and intermediate models: cleaned, typed, deduplicated (dbt views and tables)
- **GOLD** – Final fact and dimension tables ready for analytics (dbt tables)

## Project structure

```
├── scripts/
│   ├── extract_football.py        # Football matches + teams ingestion
│   ├── extract_odds.py            # Betting odds ingestion
│   └── run_pipeline.py            # Pipeline orchestrator (main entry point)
├── utils/
│   ├── api.py                     # HTTP client: retry, pagination, logging
│   ├── config_loader.py           # YAML config loader
│   ├── snowflake_conn.py          # Snowflake connector
│   ├── snowflake_loader.py        # PUT + COPY INTO logic with retry
│   └── storage.py                 # NDJSON file serialization
├── dbt_project/
│   ├── models/
│   │   ├── staging/               # stg_matches, stg_teams, stg_odds_events, stg_odds_market_lines
│   │   ├── intermediate/          # int_matches_normalized, int_matches_with_odds
│   │   ├── marts/                 # fct_matches, fct_match_vs_odds, fct_team_match_stats,
│   │   │                          # fct_team_form, fct_daily_competition, dim_team, dim_competition
│   │   └── diagnostics/           # diag_missing_team_mappings, diag_missing_participant_mappings
│   ├── seeds/                     # map_teams.csv, map_participants.csv, dim_date.csv
│   ├── macros/                    # utc_to_pl, generate_schema_name
│   └── tests/                     # test_duplicate_matches
├── config/
│   └── config.yaml                # Competitions, sports, date windows, rate limits
├── snowflake/
│   ├── setup.sql                  # Database, schema and table definitions, resource monitor
│   └── functions.sql              # UDFs: GET_MATCH_RESULT, GET_POINTS
├── main.py                        # Flask app for GCP Cloud Run
├── Dockerfile
└── requirements.txt
```

## Local setup

Install dependencies:
```bash
pip install -r requirements.txt
```

Create `.env` file in the root directory:
```env
SNOWFLAKE_USER=your_user
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_DATABASE=FOOTBALL_DB
SNOWFLAKE_SCHEMA=BRONZE

FOOTBALL_API_KEY=your_football_api_key
ODDS_API_KEY=your_odds_api_key
```

Run pipeline locally:
```bash
python -m scripts.run_pipeline
```

Run dbt:
```bash
cd dbt_project
dbt seed
dbt run --exclude tag:diagnostic
dbt test
```

## Configuration

Pipeline behavior is controlled via `config/config.yaml`:
```yaml
competitions: ["PL", "CL", "BL1", "SA", "PD"]   # football competitions

sports:                                             # odds API sport IDs
  PL: 11
  CL: 16
  BL1: 13
  PD: 14
  SA: 15

dates:
  lookback_days: 1    # days of historical data to fetch
  forward_days: 0     # days of future data to fetch

api:
  rate_limit_delay: 1.5  # seconds between odds API requests
```

## Snowflake setup

Run the setup scripts once before first use:
```sql
-- snowflake/setup.sql   — creates database, schemas, tables, resource monitor
-- snowflake/functions.sql — creates UDFs
```

## GCP Cloud Run deployment

The pipeline runs as a Flask application containerized with Docker and deployed to GCP Cloud Run Jobs.

Build and push Docker image:
```bash
docker build -t gcr.io/<your-project>/football-pipeline .
docker push gcr.io/<your-project>/football-pipeline
```

The Flask app exposes a single endpoint:
- `GET /` — triggers the full pipeline and returns status

Environment variables (API keys, Snowflake credentials) are injected via GCP Secret Manager or Cloud Run environment variable configuration.

## Data quality

### dbt built-in tests
- `match_id` — unique, not_null (stg_matches, int_matches_with_odds, fct_matches, fct_match_vs_odds)
- `team_match_pk` — unique, not_null (fct_team_match_stats)
- `price_id` — unique, not_null (stg_odds_market_lines)
- `match_at_utc`, `home_team_name`, `away_team_name` — not_null
- `match_result` — accepted_values: WIN, DRAW, LOSS (fct_team_form)

### Custom SQL tests
- `test_duplicate_matches` — verifies no duplicate `match_id` in `fct_matches`

### Diagnostics
Diagnostic models are not part of the regular pipeline run. They are run manually when data quality issues are suspected:

```bash
dbt run --select tag:diagnostic
```

- `diag_missing_team_mappings` — identifies team names from the odds API not covered by `map_teams` seed, with fuzzy match proposals using `JAROWINKLER_SIMILARITY`. Run when new competitions or teams are added.
- `diag_missing_participant_mappings` — identifies raw participant names from market lines that do not match any team in `stg_odds_events` and are not yet in `map_participants` seed. Run when null odds appear in `fct_match_vs_odds`.

### Team name mapping
Two separate APIs use different team name conventions. Mismatches are resolved via seed-based lookup tables:
- `map_teams.csv` — maps football-data.org names to TheRundown names at the event level
- `map_participants.csv` — maps malformed or inconsistent participant names within market lines to their correct form

## Notes
- All timestamps ingested in UTC; timezone conversion to `Europe/Warsaw` happens in the dbt Silver/Gold layer
- Teams are fetched only on Mondays (`is_teams_day`) to avoid unnecessary API calls
- NDJSON format is used for Snowflake `PUT + COPY INTO` to support multi-record batch files
- `ON_ERROR = 'ABORT_STATEMENT'` used in COPY INTO to catch data issues early
- dbt schema naming differs between `prod` and `dev` targets via the `generate_schema_name` macro
- `has_complete_odds` flag in `fct_match_vs_odds` marks records where all three moneyline odds (home, away, draw) are available; records with incomplete odds have `market_predicted_result` and `market_correct` set to NULL
- dbt transformations are still under active development