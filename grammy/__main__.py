import argparse
import logging
from datetime import datetime
import zoneinfo
from instagrapi import Client

from grammy.config_loader import load_config, is_within_run_window
from grammy.auth_device import authenticate
from grammy.database_ops import init_db, set_status
from grammy.bot_logic import run_bot
from grammy.telegram_notify import TelegramNotifier
from grammy.utils import get_local_interaction_totals


def print_enabled_features(config):
    print("\n🔧 Enabled Features:")
    if config.get("batch", {}).get("enabled", False):
        print(
            f"  ✅ Batch sleeping enabled: {config['batch']['size_min']}–{config['batch']['size_max']} users, sleep {config['batch']['sleep_min']}–{config['batch']['sleep_max']}s"
        )
    if config.get("telegram", {}).get("enabled", False):
        print(
            f"  ✅ Telegram notifications: {config['telegram'].get('verbosity', 'all')}"
        )
    if config.get("limits", {}).get("max_likes_per_user", 1) == 0:
        print("  ❌ Likes disabled")
    if config.get("limits", {}).get("max_comments_per_user", 1) == 0:
        print("  ❌ Comments disabled")
    print()


if __name__ == "__main__":
    start_time = datetime.now()

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--now", action="store_true", help="Force run ignoring schedule"
    )
    parser.add_argument(
        "--force", action="store_true", help="Ignore daily interaction limits"
    )
    parser.add_argument(
        "--seed-path", type=str, default=".runtime_seed.json", help="Path to seed file"
    )
    args = parser.parse_args()

    config = load_config()
    tz = zoneinfo.ZoneInfo(config.get("timezone", "UTC"))

    if not args.now:
        if not is_within_run_window(config):
            print("❌ Not within allowed run window. Exiting.")
            exit(0)
        print("✅ Allowed run window – proceeding")
    else:
        print("⏩ Forced run: skipping time check")

    print_enabled_features(config)

    comment_bank = config.get("comments", [])
    if not comment_bank:
        print("❌ No comments found in config.")
        exit(1)

    log_file = (
        config["paths"]["logs_path"]
        + f"/bot_{datetime.now(tz).strftime('%Y-%m-%d')}.log"
    )
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
    )

    db_path = config["paths"]["db_path"]
    conn = init_db(db_path)

    comments, likes, total = get_local_interaction_totals(
        conn, config.get("timezone", "UTC")
    )

    if not args.force and total >= config["limits"]["daily_interactions"]:
        logging.info("Reached daily interaction limit. Exiting.")
        exit(0)
    elif args.force:
        logging.info("⚠️  Forcing run despite interaction limits.")

    cl = Client()
    authenticate(cl, config, conn)

    telegram_conf = config.get("telegram", {})
    notifier = TelegramNotifier(
        bot_token=telegram_conf.get("bot_token"),
        chat_id=telegram_conf.get("chat_id"),
        enabled=telegram_conf.get("enabled", False),
    )

    try:
        set_status(conn, True)
        run_bot(
            cl=cl,
            config=config,
            conn=conn,
            comment_bank=comment_bank,
            limits=config["limits"],
            force_run=args.force,
            notifier=notifier,
            start_time=start_time,
        )
    except KeyboardInterrupt:
        logging.warning("Interrupted by user (Ctrl+C)")
    except Exception as e:
        logging.exception("Unhandled exception: %s", e)
    finally:
        comments_done, likes_done, interactions_done = get_local_interaction_totals(
            conn, config.get("timezone", "UTC")
        )
        elapsed = datetime.now() - start_time
        verbosity = config.get("telegram", {}).get("verbosity", "all")
        if notifier and verbosity == "all":
            notifier.send(
                f"🚀 Bot Ended\nToday's totals: 💬 {comments_done}/{config['limits']['daily_comments']}, ❤️ {likes_done}/{config['limits']['daily_likes']}, 📏 {interactions_done}/{config['limits']['daily_interactions']}"
            )
        conn.close()
        set_status(init_db(db_path), False)
        logging.info("Bot marked as not running.")
