import argparse
import logging
from datetime import datetime
import zoneinfo
from instagrapi import Client

from grammy.config_loader import load_config, resolve_runtime_seed
from grammy.auth_device import prepare_device, authenticate
from grammy.database_ops import init_db, set_status, get_daily_counts_range
from grammy.bot_logic import run_bot

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--now", action="store_true", help="Force run ignoring schedule")
    parser.add_argument("--force", action="store_true", help="Ignore daily interaction limits")
    parser.add_argument("--seed-path", type=str, default=".runtime_seed.json", help="Path to seed file")
    args = parser.parse_args()

    config = load_config()
    tz = zoneinfo.ZoneInfo(config.get("timezone", "UTC"))
    runtime = resolve_runtime_seed(config, seed_path=args.seed_path, force_now=args.now)

    now_str = datetime.now(tz).strftime("%H:%M")
    if not args.now and now_str != runtime.strftime("%H:%M"):
        print(f"⏰ Not the scheduled time yet: {now_str} != {runtime.strftime('%H:%M')}")
        exit(0)
    elif args.now:
        print("⏩ Forced run: skipping time check")

    comment_bank = config.get("comments", [])
    if not comment_bank:
        print("❌ No comments found in config.")
        exit(1)

    log_file = config['paths']['logs_path'] + f"/bot_{datetime.now(tz).strftime('%Y-%m-%d')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

    db_path = config['paths']['db_path']
    conn = init_db(db_path)

    start_of_day = datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day.replace(hour=23, minute=59, second=59)
    total, comments, likes = get_daily_counts_range(conn, start_of_day, end_of_day)
    logging.info("Already done today - Likes: %d, Comments: %d, Total: %d", likes, comments, total)

    if not args.force and total >= config['limits']['daily_interactions']:
        logging.info("Reached daily interaction limit. Exiting.")
        exit(0)
    elif args.force:
        logging.info("⚠️  Forcing run despite interaction limits.")

    cl = Client()
    prepare_device(cl, config)
    authenticate(cl, config)

    try:
        set_status(conn, True)
        run_bot(
            cl=cl,
            config=config,
            conn=conn,
            comment_bank=comment_bank,
            limits=config['limits'],
            comments_done=comments,
            likes_done=likes,
            interactions_done=total,
            force_run=args.force
        )
    except KeyboardInterrupt:
        logging.warning("Interrupted by user (Ctrl+C)")
    except Exception as e:
        logging.exception("Unhandled exception: %s", e)
    finally:
        conn.close()
        set_status(init_db(db_path), False)
        logging.info("Bot marked as not running.")
