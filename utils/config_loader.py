import yaml
import os

def load_config() -> dict:
    config_path = os.path.join("config", "config.yaml")

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config not found: {config_path}")
    
    with open(config_path, "r") as f:
        return yaml.safe_load(f)