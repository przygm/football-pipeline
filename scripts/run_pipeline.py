import logging
from datetime import datetime, timezone

from scripts.extract_football import run_football_etl
from scripts.extract_odds import run_odds_etl
from utils.snowflake_loader import run_etl_pipeline


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

#---------------------------------------------------------------------------------------------------
def generate_batch_id() -> str:
    return datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')


#---------------------------------------------------------------------------------------------------
def main() -> None:
    batch_id = generate_batch_id()

    logging.info(f"START PIPELINE | batch_id={batch_id}")

    try:
        football_batches = run_football_etl(batch_id)
        odds_batches = run_odds_etl(batch_id)
        #odds_batches = [] # TEMP - for testting empty data scenario

        all_batches = []

        if football_batches:
            all_batches.extend(football_batches)

        if odds_batches:
            all_batches.extend(odds_batches)

        if all_batches:
            run_etl_pipeline(all_batches, batch_id)
            logging.info(f"PIPELINE SUCCESS | batch_id={batch_id}")
        else:
            logging.warning(f"PIPELINE FINISHED - No data collected | batch_id={batch_id}")


    except Exception as e:
        logging.error(f"PIPELINE FAILED: {e} | batch_id={batch_id}")
        raise

#---------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()