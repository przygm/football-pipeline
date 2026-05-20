import os
import time
import logging
from datetime import datetime, timedelta, timezone 

from dotenv import load_dotenv

from utils.api import fetch_data
from utils.config_loader import load_config


# CONFIG -----------------------------------------------------------------------------
load_dotenv()

config = load_config()

SPORTS = config["sports"]
LOOKBACK_DAYS = config["dates"]["lookback_days"]
FORWARD_DAYS = config["dates"]["forward_days"]
RATE_LIMIT_DELAY = config["api"]["rate_limit_delay"]

ODDS_API_KEY = os.getenv("ODDS_API_KEY")
if not ODDS_API_KEY:
    raise ValueError("Missing ODDS_API_KEY")

ODDS_SELECT_SQL = """
        $1:event,
        $1:sport::string,
        $1:event_date::date,
        $1:batch_id::string,
        CONVERT_TIMEZONE('UTC', CURRENT_TIMESTAMP())::timestamp_ntz        
    """ 

#---------------------------------------------------------------------------------------------------
def run_odds_etl(batch_id: str) -> list:
              
    today = datetime.now(timezone.utc).date()

    all_odds = []

    logging.info(f"Starting Odds | batch_id={batch_id}")

    try:
        for sport_name, sport_id in SPORTS.items():
            logging.info(f"Fetching data for sport: {sport_name} | batch_id={batch_id}")

            for offset in range(-LOOKBACK_DAYS, FORWARD_DAYS + 1): 
                date = (today + timedelta(days=offset)).strftime("%Y-%m-%d")

                events = fetch_data(
                    url=f"https://therundown.io/api/v2/sports/{sport_id}/events/{date}",
                    data_key="events",
                    params={"key": ODDS_API_KEY}
                )

                if events:
                    for event in events:
                        all_odds.append({
                            "sport": sport_name,
                            "event_date": date,
                            "batch_id": batch_id,
                            "source": "odds_api",
                            "event": event
                        })
                else:
                    logging.info(f"No data for {sport_name} on {date} | batch_id={batch_id}")

                time.sleep(RATE_LIMIT_DELAY)  # Rate limiting for API

    except Exception as e:
        logging.error(f"CRITICAL ERROR in Odds - Stopping all fetches: {e} | batch_id={batch_id}")
        raise


    batches = []
    if all_odds:
        batches.append({
            "data": all_odds,
            "table": "ODDS_RAW",
            "select_sql": ODDS_SELECT_SQL,
            "prefix": "odds_batch"
        })

    return batches

