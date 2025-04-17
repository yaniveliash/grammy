import json
import yaml
from pathlib import Path
from datetime import datetime, timedelta
import random

def load_config(path="config.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def resolve_runtime_seed(config, seed_path=".runtime_seed.json", force_now=False):
    now = datetime.now()
    runtime_file = Path(seed_path)

    run_time = config["timing"].get("run_time", "02:00")
    window = int(config["timing"].get("run_time_random_window", 60))

    if runtime_file.exists():
        with open(runtime_file, "r") as f:
            runtime_seed = json.load(f)
        if runtime_seed.get("date") == now.strftime("%Y-%m-%d"):
            return datetime.strptime(f"{now.date()} {runtime_seed['target']}", "%Y-%m-%d %H:%M")

    base_hour, base_minute = map(int, run_time.split(":"))
    base_time = datetime(now.year, now.month, now.day, base_hour, base_minute)
    offset = random.randint(-window, window)
    target_run = base_time + timedelta(minutes=offset)
    with open(runtime_file, "w") as f:
        json.dump({"date": now.strftime("%Y-%m-%d"), "target": target_run.strftime("%H:%M")}, f)

    return target_run
