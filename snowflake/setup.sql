-- Snowflake Setup Script

-- Create database
CREATE DATABASE IF NOT EXISTS FOOTBALL_DB;

-- Create schemas (layers)
CREATE SCHEMA IF NOT EXISTS FOOTBALL_DB.BRONZE;
CREATE SCHEMA IF NOT EXISTS FOOTBALL_DB.UTIL;

-- ============================================
-- BRONZE LAYER - Raw data tables
-- ============================================

CREATE OR REPLACE TABLE FOOTBALL_DB.BRONZE.MATCHES_RAW (
    DATA VARIANT,
    COMPETITION VARCHAR,
    BATCH_ID VARCHAR,
    LOADED_AT TIMESTAMP
);

CREATE OR REPLACE TABLE FOOTBALL_DB.BRONZE.TEAMS_RAW (
    DATA VARIANT,
    COMPETITION VARCHAR,
    BATCH_ID VARCHAR,
    LOADED_AT TIMESTAMP
);

CREATE OR REPLACE TABLE FOOTBALL_DB.BRONZE.ODDS_RAW (
    DATA VARIANT,
	SPORT VARCHAR,
    EVENT_DATE DATE,
    BATCH_ID VARCHAR,
    LOADED_AT TIMESTAMP
);

CREATE OR REPLACE TABLE FOOTBALL_DB.BRONZE.WEATHER_RAW (
    DATA VARIANT,
    BATCH_ID VARCHAR,
    LOADED_AT TIMESTAMP
);

CREATE OR REPLACE FILE FORMAT FOOTBALL_DB.BRONZE.JSON_FORMAT
TYPE = JSON;

-- ============================================
-- SILVER LAYER - Views (created by dbt)
-- ============================================
-- These will be created automatically when dbt runs

-- ============================================
-- GOLD LAYER - Views (created by dbt)
-- ============================================
-- These will be created automatically when dbt runs



CREATE RESOURCE MONITOR football_monitor
WITH CREDIT_QUOTA = 20
     FREQUENCY = MONTHLY
     START_TIMESTAMP = IMMEDIATELY
TRIGGERS ON 50 PERCENT DO NOTIFY
         ON 80 PERCENT DO NOTIFY
         ON 100 PERCENT DO SUSPEND;

ALTER WAREHOUSE COMPUTE_WH 
SET RESOURCE_MONITOR = football_monitor;