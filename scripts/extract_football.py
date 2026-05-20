import os
import logging
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv

from utils.api import fetch_data
from utils.config_loader import load_config
from utils.snowflake_loader import run_etl_pipeline

# CONFIG -----------------------------------------------------------------------------  
load_dotenv()
config = load_config()

LOOKBACK_DAYS = config["dates"]["lookback_days"]
FORWARD_DAYS = config["dates"]["forward_days"]
COMPETITIONS = config["competitions"]

FOOTBALL_API_KEY = os.getenv('FOOTBALL_API_KEY')
if not FOOTBALL_API_KEY:
    raise ValueError("Missing FOOTBALL_API_KEY")

MATCHES_SELECT_SQL = """
        $1:match,
        $1:competition::string,
        $1:batch_id::string,
        CONVERT_TIMEZONE('UTC', CURRENT_TIMESTAMP())::timestamp_ntz        
    """               

TEAMS_SELECT_SQL = """
        $1:team,
        $1:competition::string,
        $1:batch_id::string,
        CONVERT_TIMEZONE('UTC', CURRENT_TIMESTAMP())::timestamp_ntz        
    """            

#---------------------------------------------------------------------------------------------------
def run_football_etl(batch_id: str) -> list:

    today = datetime.now(timezone.utc).date()
    
    all_matches = []
    all_teams = []
    is_teams_day = today.weekday() in [0] # 0 = monday

    date_from = (today - timedelta(days=LOOKBACK_DAYS)).strftime('%Y-%m-%d')
    date_to   = (today + timedelta(days=FORWARD_DAYS)).strftime('%Y-%m-%d')

    logging.info(f"Starting Football | batch_id={batch_id}")

    try:
        for competition in COMPETITIONS:
            logging.info(f"Processing competition: {competition} | batch_id={batch_id}")

            matches = fetch_data(
                url=f"https://api.football-data.org/v4/competitions/{competition}/matches",
                data_key="matches",
                headers={'X-Auth-Token': FOOTBALL_API_KEY},
                params={'dateFrom': date_from, 'dateTo': date_to}, 
                paginate=True
            )

            if matches:
                for match in matches:
                    all_matches.append({
                        "competition": competition,
                        "batch_id": batch_id,
                        "source": "football_api",
                        "match": match
                    })
            else:           
                logging.info(f"No matches for {competition} | batch_id={batch_id}")


            if is_teams_day:
                logging.info(f"Fetching teams for {competition} | batch_id={batch_id}")
                teams = fetch_data(
                    url=f"https://api.football-data.org/v4/competitions/{competition}/teams",
                    data_key="teams",
                    headers={'X-Auth-Token': FOOTBALL_API_KEY},
                    paginate=True
                )


                if teams:
                    for team in teams:
                        all_teams.append({
                            "competition": competition,
                            "batch_id": batch_id,
                            "source": "football_api",
                            "team": team
                        })

    except Exception as e:
        logging.error(f"CRITICAL ERROR - Stopping loop: {e} | batch_id={batch_id}")
        raise


    batches = []
    if all_matches:
        batches.append({
            "data": all_matches,
            "table": "MATCHES_RAW",
            "select_sql": MATCHES_SELECT_SQL,
            "prefix": "matches_batch"
        })
    
    if is_teams_day and all_teams:
        batches.append({
            "data": all_teams,
            "table": "TEAMS_RAW",
            "select_sql": TEAMS_SELECT_SQL,
            "prefix": "teams_weekly"
        })

    return batches
