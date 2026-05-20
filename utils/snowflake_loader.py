import os
import logging
import time

from utils.snowflake_conn import get_connection
from utils.storage import save_ndjson


def execute_with_retry(cs, query, max_retries=3):
    for attempt in range(max_retries):
        try:
            cs.execute(query)
            return
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait = 2 ** attempt
            logging.warning(f"Snowflake retry in {wait}s: {e}")
            time.sleep(wait)

#---------------------------------------------------------------------------------------------------
def load_json_to_snowflake(cs, filename: str, table_name: str, select_sql: str) -> None:
    execute_with_retry(cs, f"PUT file://{os.path.abspath(filename)} @%{table_name}")

    logging.info(f"Loading data into {table_name}")
    execute_with_retry(cs, f"""
        COPY INTO {table_name}
        FROM (
            SELECT {select_sql}
            FROM @%{table_name}
        )
        FILE_FORMAT = FOOTBALL_DB.BRONZE.JSON_FORMAT
        PURGE = TRUE
        ON_ERROR = 'ABORT_STATEMENT'
    """)

    logging.info(f"Finished loading data into {table_name}")

#---------------------------------------------------------------------------------------------------
def load_to_snowflake(cs, data: list, table_name: str, select_sql: str, prefix: str, batch_id: str) -> None:

    if not data:
        return

    filename = save_ndjson(data, prefix, batch_id)
    load_json_to_snowflake(cs, filename, table_name, select_sql)      
    logging.info(f"Loaded {filename} into {table_name} | batch_id={batch_id}")

#---------------------------------------------------------------------------------------------------
def run_etl_pipeline(data_batches: list, batch_id: str) -> None:
    """
    data_batches = [
        {
            "data": [...],
            "table": "MATCHES_RAW",
            "select_sql": "...",
            "prefix": "matches_batch"
        }
    ]
    """

    if not any(batch["data"] for batch in data_batches):
        logging.info(f"No data found. Skipping Snowflake connection | batch_id={batch_id}")
        return

    conn = None
    cs = None
    
    try:
        logging.info(f"Opening Snowflake connection | batch_id={batch_id}")
        conn = get_connection("BRONZE")
        cs = conn.cursor()
        cs.execute("ALTER SESSION SET STATEMENT_TIMEOUT_IN_SECONDS = 60")
        
        for batch in data_batches:
            logging.info(f"Loading {len(batch['data'])} into {batch['table']} | batch_id={batch_id}")
            load_to_snowflake(
                cs,
                batch["data"],
                batch["table"],
                batch["select_sql"],
                batch["prefix"],
                batch_id
            )

        logging.info(f"ETL completed successfully | batch_id={batch_id}")

    except Exception as e:
        logging.error(f"PIPELINE FAILED: {e} | batch_id={batch_id}")
        raise

    finally:
        if cs:
            cs.close()
        if conn:
            conn.close()      