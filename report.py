import sqlite3
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
import yaml
import argparse
import zoneinfo

# CLI Argument parsing
parser = argparse.ArgumentParser(description="Instagram Bot Daily Report")
parser.add_argument("--limit", type=int, default=20, help="Max users to display for all-time and ignored lists")
args = parser.parse_args()
limit = args.limit

# Load config
def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)

config = load_config()
db_path = Path(config['paths']['db_path'])
try:
    tz = zoneinfo.ZoneInfo(config.get("timing", {}).get("timezone", "UTC"))
except Exception as e:
    print(f"[WARNING] Invalid timezone in config: {config.get('timezone')}. Defaulting to UTC.")
    tz = timezone.utc

# Get current local date (not time)
today_local = datetime.now(tz).date()
local_start = datetime.combine(today_local, time(0, 0, 0), tzinfo=tz)
local_end = datetime.combine(today_local, time(23, 59, 59), tzinfo=tz)

# Convert to UTC strings for SQLite comparison
start_utc = local_start.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
end_utc = local_end.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

# Connect to DB
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Count interactions
c.execute("SELECT COUNT(*) FROM interactions WHERE timestamp >= ? AND timestamp <= ?", (start_utc, end_utc))
daily_total = c.fetchone()[0]

c.execute("SELECT COUNT(*) FROM interactions WHERE timestamp >= ? AND timestamp <= ? AND type = 'comment'", (start_utc, end_utc))
daily_comments = c.fetchone()[0]

c.execute("SELECT COUNT(*) FROM interactions WHERE timestamp >= ? AND timestamp <= ? AND type = 'like'", (start_utc, end_utc))
daily_likes = c.fetchone()[0]

limits = config['limits']

# Check bot status
c.execute("SELECT running, last_updated FROM status WHERE id = 1")
row = c.fetchone()
if row:
    running, last_updated = row
    status_msg = "🟢 RUNNING" if running else "🔴 NOT RUNNIG"
    print(f"\n=== 🤖 BOT STATUS ===\nStatus   : {status_msg}\nUpdated  : {last_updated}")
else:
    print("\n=== 🤖 BOT STATUS ===\nStatus   : Unknown\nUpdated  : -")

print("=== 📊 DAILY USAGE ===")
print(f"{'Comments':<10}: {daily_comments}/{limits['daily_comments']}")
print(f"{'Likes':<10}: {daily_likes}/{limits['daily_likes']}")
print(f"{'Total':<10}: {daily_total}/{limits['daily_interactions']}")

# Get daily users
c.execute("SELECT DISTINCT username FROM interactions WHERE timestamp >= ? AND timestamp <= ?", (start_utc, end_utc))
daily_users = sorted({row[0] for row in c.fetchall()})

# Get all-time users
c.execute("SELECT DISTINCT username FROM interactions")
all_time_users = sorted({row[0] for row in c.fetchall()})

# Get private/ignored users
c.execute("SELECT username FROM users WHERE is_private = 1 ORDER BY username")
private_users = sorted({row[0] for row in c.fetchall()})

# Print full daily user list
print(f"\n=== \U0001F465 Interacted Today ({len(daily_users)}) ===")
if daily_users:
    print(", ".join(daily_users))
else:
    print("(none)")

# Print top-N from all-time or ignored
def print_user_list(title, users, total_count):
    print(f"\n=== \U0001F465 {title} ({total_count}) ===")
    if users:
        shown_users = users[:limit]
        print(", ".join(shown_users) + (" ..." if total_count > limit else ""))
    else:
        print("(none)")

print_user_list("All-Time Interactions", all_time_users, len(all_time_users))
print_user_list("Ignored (Private Accounts)", private_users, len(private_users))

conn.close()
