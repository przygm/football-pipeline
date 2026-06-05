# Football Analytics Pipeline

## Overview

Data engineering project that collects football match data and betting odds from external APIs, loads raw data into Snowflake, and transforms it using dbt.

The project combines data from multiple sources and stores it using a Bronze → Silver → Gold architecture.

Current functionality includes:

- football match ingestion
- betting odds ingestion
- Snowflake data warehouse
- dbt transformations
- data quality tests
- deployment to GCP Cloud Run

---

## Tech Stack

### Ingestion

- Python
- Requests
- Snowflake Connector

### Data Warehouse

- Snowflake

### Transformations

- dbt Core
- dbt-utils

### Cloud

- GCP Cloud Run
- Docker

---

## Architecture
```text
football-data.org API                        TheRundown API
        |                                         | 
        v                                         v
    Python ETL                                Python ETL
        |                                         |
        |                                         |
        +--------------------+--------------------+
                             |
                             v
                      Snowflake Bronze
                             |
                             v
                        dbt Silver
                             |
                             v
                         dbt Gold

```
---

## Data Sources

### football-data.org

Used to collect:

- matches
- teams

### TheRundown API

Used to collect:

- football events
- betting odds

---

## Data Model

### Bronze

Raw JSON data loaded directly from APIs.

Tables:

- MATCHES_RAW
- TEAMS_RAW
- ODDS_RAW

Each record contains:

- batch_id
- loaded_at

which allows identification of:

- when data was loaded
- which pipeline execution produced the record

---

### Silver

Technical transformation layer.

Responsibilities:

- parsing JSON fields
- converting data into structured columns
- deduplication
- team name normalization
- matching records between data sources

Examples:

- stg_matches
- stg_teams
- stg_odds_events
- stg_odds_market_lines
- int_matches_normalized
- int_matches_with_odds

---

### Gold

Business-ready analytical models.

Examples:

- fct_matches
- fct_match_vs_odds
- fct_team_match_stats
- fct_team_rolling_form_last_5
- fct_daily_competition
- dim_team

---

## Local Setup

Install dependencies:

pip install -r requirements.txt

Create .env file:

SNOWFLAKE_USER=
SNOWFLAKE_PASSWORD=
SNOWFLAKE_ACCOUNT=
SNOWFLAKE_WAREHOUSE=
SNOWFLAKE_DATABASE=
SNOWFLAKE_SCHEMA=

FOOTBALL_API_KEY=
ODDS_API_KEY=

---

## Run Pipeline

python -m scripts.run_pipeline

---

## Run dbt

cd dbt_project

dbt seed
dbt run
dbt test

---

## Configuration

Pipeline behaviour is controlled by:

config/config.yaml

Current configuration:

competitions:
  - PL
  - CL
  - BL1
  - SA
  - PD

sports:
  PL: 11
  CL: 16
  BL1: 13
  PD: 14
  SA: 15

dates:
  lookback_days: 1
  forward_days: 0

api:
  rate_limit_delay: 1.5

---

## Snowflake Setup

Create database objects:
snowflake/setup.sql

Create utility functions:
snowflake/functions.sql

---

## Deployment

The ingestion layer is deployed to GCP Cloud Run.

The container executes:

1. Python ingestion
2. Snowflake loading
3. dbt run
4. dbt test

Environment variables are provided through Cloud Run configuration and/or GCP Secret Manager.

---

## Data Quality

Implemented checks include:

### dbt Tests

- unique
- not_null
- accepted_values
- relationships

### Custom SQL Tests

- duplicate match detection
- match result consistency
- team statistics validation

### Diagnostic Models

- missing team mappings
- missing participant mappings
