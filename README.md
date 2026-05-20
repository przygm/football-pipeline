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

### Data flow:
```
football-data.org API  ──┐
                         ├──▶ Python ingestion  ──▶ Snowflake BRONZE layer
TheRundown Odds API    ──┘         │
                                   │
                              MATCHES_RAW
                              TEAMS_RAW
                              ODDS_RAW
                                   │
                              dbt models
                                   │
                    ┌──────────────┼──────────────┐
                  stg_matches   stg_teams       stg_odds
                  stg_odds        │
                    │       (SILVER layer)
                    │
               int_matches_normalized
               int_matches_with_odds
                    │
               fct_matches
               fct_daily_competition
                  (GOLD layer)
```

### Layers:
- **BRONZE** – Raw VARIANT data loaded directly from APIs, with `batch_id` and `loaded_at`
- **SILVER** – Staging and intermediate models: cleaned, typed, deduplicated (dbt views / tables)
- **GOLD** – Final fact tables ready for analytics (dbt tables)

## Features
- Multi-source ingestion: football matches + betting odds from two separate APIs
- Separation of data layers: Bronze / Silver / Gold
- Batch-based pipeline with unique `batch_id` per run for traceability
- Idempotent ingestion — safe to rerun without duplicating data
- Deduplication in staging models using `ROW_NUMBER() OVER (PARTITION BY ... ORDER BY loaded_at DESC)`
- Resilient API ingestion: retry logic with exponential backoff, rate limit handling (HTTP 429)
- Pagination support for APIs returning large result sets
- Sensitive parameters stripped from logs (API keys, tokens)
- Team name mapping: seed-based lookup table (`map_teams.csv`) with fuzzy matching diagnostics (`diag_missing_team_mappings`)
- Timezone handling: UTC stored in BRONZE, converted to `Europe/Warsaw` via dbt macro
- Data quality tests (dbt built-in + custom SQL tests)
- Schema isolation per environment: `prod` vs `dev` schema naming via custom `generate_schema_name` macro
- Cloud orchestration via GCP Cloud Run Jobs (Docker + Flask + Gunicorn)
- JSON logging with `batch_id` context on every log line

## Project structure
```
├── scripts/
│   ├── extract_football.py   # Football matches + teams ingestion
│   ├── extract_odds.py       # Betting odds ingestion
│   └── run_pipeline.py       # Pipeline orchestrator (main entry point)
├── utils/
│   ├── api.py                # HTTP client: retry, pagination, logging
│   ├── config_loader.py      # YAML config loader
│   ├── snowflake_conn.py     # Snowflake connector
│   ├── snowflake_loader.py   # PUT + COPY INTO logic with retry
│   └── storage.py            # NDJSON file serialization
├── dbt_project/
│   ├── models/
│   │   ├── staging/          # stg_matches, stg_teams, stg_odds
│   │   ├── intermediate/     # int_matches_normalized, int_matches_with_odds
│   │   ├── marts/            # fct_matches, fct_daily_competition
│   │   └── diagnostics/      # diag_missing_team_mappings
│   ├── seeds/                # map_teams.csv (team name mapping)
│   ├── macros/               # utc_to_pl, generate_schema_name
│   └── tests/                # test_duplicate_matches
├── config/
│   └── config.yaml           # Competitions, sports, date windows, rate limits
├── scripts/snowflake_setup.sql
├── main.py                   # Flask app for GCP Cloud Run
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

Run dbt models:
```bash
cd dbt_project
dbt run
dbt test
```

## Configuration

Pipeline behavior is controlled via `config/config.yaml`:
```yaml
competitions: ["PL", "CL", "BL1", "SA", "PD"]   # football competitions
sports:                                             # odds API sport IDs
  PL: 11
  CL: 16
  ...
dates:
  lookback_days: 1    # days of historical data to fetch
  forward_days: 0     # days of future data to fetch
api:
  rate_limit_delay: 1.5  # seconds between odds API requests
```

## Snowflake setup

Run the setup script once before first use:
```sql
-- scripts/snowflake_setup.sql
CREATE DATABASE IF NOT EXISTS FOOTBALL_DB;
CREATE SCHEMA IF NOT EXISTS FOOTBALL_DB.BRONZE;
-- tables: MATCHES_RAW, TEAMS_RAW, ODDS_RAW, WEATHER_RAW
-- file format: JSON_FORMAT
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

## Data quality tests

**dbt built-in tests:**
- `match_id` — unique, not_null (stg_matches, int_matches_with_odds, fct_matches)
- `match_at_utc`, `home_team_name`, `away_team_name` — not_null

**Custom SQL tests:**
- `test_duplicate_matches` — verifies no duplicate `match_id` in `fct_matches`

**Diagnostics:**
- `diag_missing_team_mappings` — identifies team names from the odds API not yet covered by `map_teams.csv`, with fuzzy match proposals using `JAROWINKLER_SIMILARITY`

## Notes
- All timestamps ingested in UTC; timezone conversion to `Europe/Warsaw` happens in the dbt Silver/Gold layer
- Teams are fetched only on Mondays (`is_teams_day`) to avoid unnecessary API calls
- NDJSON format is used for Snowflake `PUT + COPY INTO` to support multi-record batch files
- `ON_ERROR = 'ABORT_STATEMENT'` used in COPY INTO to catch data issues early
- dbt schema naming differs between `prod` and `dev` targets via the `generate_schema_name` macro
- dbt transformations are still under active development
