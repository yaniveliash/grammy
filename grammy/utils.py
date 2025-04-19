import logging
import time
import random
from datetime import datetime, time as dt_time, timezone
import zoneinfo


def log_sleep(min_sleep: float, max_sleep: float):
    sleep_time = random.uniform(min_sleep, max_sleep)
    logging.info(f"Sleeping for {sleep_time:.2f} seconds")
    time.sleep(sleep_time)


def get_local_interaction_totals(conn, tz_name: str):
    try:
        tz = zoneinfo.ZoneInfo(tz_name)
    except Exception:
        logging.warning(
            f"[WARNING] Invalid timezone in config: {tz_name}. Defaulting to UTC."
        )
        tz = timezone.utc

    today_local = datetime.now(tz).date()
    local_start = datetime.combine(today_local, dt_time.min, tzinfo=tz)
    local_end = datetime.combine(today_local, dt_time.max, tzinfo=tz)

    start_utc = local_start.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    end_utc = local_end.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    c = conn.cursor()
    c.execute(
        "SELECT COUNT(*) FROM interactions WHERE timestamp >= ? AND timestamp <= ? AND type = 'comment'",
        (start_utc, end_utc),
    )
    comments_done = c.fetchone()[0]

    c.execute(
        "SELECT COUNT(*) FROM interactions WHERE timestamp >= ? AND timestamp <= ? AND type = 'like'",
        (start_utc, end_utc),
    )
    likes_done = c.fetchone()[0]

    interactions_done = comments_done + likes_done
    return comments_done, likes_done, interactions_done
