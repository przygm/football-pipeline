import os
import json
import logging

def save_ndjson(records: list, prefix: str, batch_id: str) -> str:
    os.makedirs("raw", exist_ok=True)

    filename = f"raw/{prefix}_{batch_id}.json"

    try:
        with open(filename, "w", encoding="utf-8") as f:
            for row in records:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        
        logging.info(f"Successfully saved {len(records)} records to {filename}")
        
    except Exception as e:
        logging.error(f"Failed to save NDJSON file {filename}: {e}")
        raise

    return filename    