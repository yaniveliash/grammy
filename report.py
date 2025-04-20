import argparse
import re
import yaml
from datetime import datetime, time, timedelta, timezone
import zoneinfo
from pathlib import Path
from rich.console import Console
from rich.table import Table
import sqlite3


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a log summary report for the Instagram bot"
    )
    parser.add_argument(
        "--range",
        dest="range_arg",
        type=str,
        default="1d",
        help="Time range: Nd (days) or Nw (weeks), e.g., 3d or 2w",
    )
    parser.add_argument(
        "--limit",
        dest="limit",
        type=int,
        default=20,
        help="Max users to display for all-time and ignored lists",
    )
    return parser.parse_args()
    parser = argparse.ArgumentParser(
        description="Generate a log summary report for the Instagram bot"
    )
    parser.add_argument(
        "--range",
        dest="range_arg",
        type=str,
        default="1d",
        help="Time range: Nd (days) or Nw (weeks), e.g., 3d or 2w",
    )
    return parser.parse_args()


def parse_range(range_arg: str) -> int:
    m = re.match(r"^(?P<n>\d+)(?P<unit>[dw])$", range_arg)
    if not m:
        raise ValueError("Invalid range format. Use formats like '3d' or '2w'.")
    n = int(m.group("n"))
    unit = m.group("unit")
    return n if unit == "d" else n * 7


def main():
    args = parse_args()
    days = parse_range(args.range_arg)

    # Load config
    cfg = yaml.safe_load(Path("config.yaml").read_text())
    logs_dir = Path(cfg.get("paths", {}).get("logs_path", "./logs"))

    # Timezone setup
    tz_name = cfg.get("timing", {}).get("timezone", "UTC")
    try:
        tz = zoneinfo.ZoneInfo(tz_name)
    except Exception:
        print(f"[WARNING] Invalid timezone {tz_name}, defaulting to UTC.")
        tz = timezone.utc

    today = datetime.now(tz).date()
    threshold = today - timedelta(days=days - 1)

    # Gather log files within range
    log_files = []  # list of (date, Path)
    for path in logs_dir.glob("bot_*.log"):
        m = re.match(r"bot_(\d{4}-\d{2}-\d{2})\.log$", path.name)
        if not m:
            continue
        log_date = datetime.strptime(m.group(1), "%Y-%m-%d").date()
        if threshold <= log_date <= today:
            log_files.append((log_date, path))

    # Sort by date
    log_files.sort(key=lambda x: x[0])

    # Initialize summary counters
    total_success = total_warnings = total_errors = 0

    # Build tables
    console = Console()
    summary_table = Table(show_header=True, header_style="bold magenta")
    summary_table.add_column("Type")
    summary_table.add_column("Count", justify="right")

    breakdown_table = Table(show_header=True, header_style="bold cyan")
    breakdown_table.add_column("Date")
    breakdown_table.add_column("✅ Success", justify="right")
    breakdown_table.add_column("⚠️ Warnings", justify="right")
    breakdown_table.add_column("❌ Errors", justify="right")

    # Process each log file
    for log_date, path in log_files:
        success = warnings = errors = 0
        with path.open("r") as f:
            for line in f:
                if "- INFO - Commented on" in line:
                    success += 1
                elif "- WARNING -" in line:
                    warnings += 1
                elif "- ERROR -" in line:
                    errors += 1
        breakdown_table.add_row(str(log_date), str(success), str(warnings), str(errors))
        total_success += success
        total_warnings += warnings
        total_errors += errors

    # Populate summary table
    summary_table.add_row("✅ Success", str(total_success))
    summary_table.add_row("⚠️ Warnings", str(total_warnings))
    summary_table.add_row("❌ Errors", str(total_errors))

    # Print report
    console.print("\n=== 📈 LOG SUMMARY (Last {} days) ===".format(args.range_arg))
    console.print(summary_table)
    console.print("\n=== 📅 LOG BREAKDOWN ({} files) ===".format(len(log_files)))
    console.print(breakdown_table)

    # === SQLITE REPORTING ===
    db_path = Path(cfg["paths"]["db_path"])
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    local_start = datetime.combine(today, time.min, tzinfo=tz)
    local_end = datetime.combine(today, time.max, tzinfo=tz)
    start_utc = local_start.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    end_utc = local_end.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    c.execute(
        "SELECT COUNT(*) FROM interactions WHERE timestamp >= ? AND timestamp <= ?",
        (start_utc, end_utc),
    )
    daily_total = c.fetchone()[0]

    c.execute(
        "SELECT COUNT(*) FROM interactions WHERE timestamp >= ? AND timestamp <= ? AND type = 'comment'",
        (start_utc, end_utc),
    )
    daily_comments = c.fetchone()[0]

    c.execute(
        "SELECT COUNT(*) FROM interactions WHERE timestamp >= ? AND timestamp <= ? AND type = 'like'",
        (start_utc, end_utc),
    )
    daily_likes = c.fetchone()[0]

    limits = cfg["limits"]

    c.execute("SELECT running, last_updated FROM status WHERE id = 1")
    row = c.fetchone()
    if row:
        running, last_updated = row
        status_msg = "🟢 RUNNING" if running else "🔴 NOT RUNNING"
        print(
            "\n=== 🤖 BOT STATUS ===\nStatus   : {}\nUpdated  : {}".format(
                status_msg, last_updated
            )
        )
    else:
        print(
            "\n=== 🤖 BOT STATUS ===\nStatus   : Unknown\nUpdated  : - (no DB row found)"
        )

    print("=== 📊 DAILY USAGE ===")
    print(f"{'Comments':<10}: {daily_comments}/{limits['daily_comments']}")
    print(f"{'Likes':<10}: {daily_likes}/{limits['daily_likes']}")
    print(f"{'Total':<10}: {daily_total}/{limits['daily_interactions']}")

    c.execute(
        "SELECT DISTINCT username FROM interactions WHERE timestamp >= ? AND timestamp <= ?",
        (start_utc, end_utc),
    )
    daily_users = sorted({row[0] for row in c.fetchall()})

    c.execute("SELECT DISTINCT username FROM interactions")
    all_time_users = sorted({row[0] for row in c.fetchall()})

    c.execute("SELECT username FROM users WHERE is_private = 1 ORDER BY username")
    private_users = sorted({row[0] for row in c.fetchall()})

    print("\n=== 👥 Interacted Today ({} users) ===".format(len(daily_users)))
    if daily_users:
        print(", ".join(daily_users))
    else:
        print("(none)")

    def print_user_list(title, users, total_count):
        print("\n=== 👥 {} ({}) ===".format(title, total_count))
        if users:
            shown_users = users[: args.limit]
            print(", ".join(shown_users) + (" ..." if total_count > args.limit else ""))
        else:
            print("(none)")

    print_user_list("All-Time Interactions", all_time_users, len(all_time_users))
    print_user_list("Ignored (Private Accounts)", private_users, len(private_users))

    conn.close()


if __name__ == "__main__":
    main()
