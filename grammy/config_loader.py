from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import yaml
import random

def load_config(path="config.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)


def get_timezone(config):
    tz_name = config.get("timing", {}).get("timezone", "UTC")
    try:
        return ZoneInfo(tz_name)
    except Exception:
        print(f"[WARN] Invalid timezone '{tz_name}', defaulting to UTC")
        return ZoneInfo("UTC")


def is_within_run_window(config):
    tz = get_timezone(config)
    now_local = datetime.now(timezone.utc).astimezone(tz)

    start_str = config.get("timing", {}).get("start_run_time")
    end_str = config.get("timing", {}).get("end_run_time")
    start_jitter = int(config.get("timing", {}).get("start_random_window", 0))
    end_jitter = int(config.get("timing", {}).get("end_random_window", 0))

    if not start_str or not end_str:
        print("[INFO] No run window defined – running immediately.")
        return True

    base_start = datetime.strptime(start_str, "%H:%M").replace(
        year=now_local.year, month=now_local.month, day=now_local.day, tzinfo=tz
    )
    base_end = datetime.strptime(end_str, "%H:%M").replace(
        year=now_local.year, month=now_local.month, day=now_local.day, tzinfo=tz
    )

    offset_start = timedelta(minutes=random.randint(-start_jitter, start_jitter))
    offset_end = timedelta(minutes=random.randint(-end_jitter, end_jitter))

    randomized_start = base_start + offset_start
    randomized_end = base_end + offset_end

    return randomized_start <= now_local <= randomized_end
