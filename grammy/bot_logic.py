import logging
import random
import time
import sys
from datetime import datetime, time as dt_time, timezone, timedelta
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ChallengeRequired
from grammy.telegram_notify import TelegramNotifier
from grammy.utils import get_local_interaction_totals
import zoneinfo


def log_sleep(min_sleep: float, max_sleep: float):
    sleep_time = random.uniform(min_sleep, max_sleep)
    logging.info(f"Sleeping for {sleep_time:.2f} seconds")
    time.sleep(sleep_time)


def log_batch_sleep(min_sleep: float, max_sleep: float):
    sleep_time = random.uniform(min_sleep, max_sleep)
    logging.info(f"Batch sleep for {sleep_time:.2f} seconds")
    time.sleep(sleep_time)


def log_progress(conn, timezone_name, limits):
    comments_done, likes_done, interactions_done = get_local_interaction_totals(
        conn, timezone_name
    )
    logging.info(
        "Progress - Comments: %d/%d, Likes: %d/%d, Total Interactions: %d/%d",
        comments_done,
        limits["daily_comments"],
        likes_done,
        limits["daily_likes"],
        interactions_done,
        limits["daily_interactions"],
    )
    return comments_done, likes_done, interactions_done


def is_outside_time_window(config):
    tz = zoneinfo.ZoneInfo(config["timing"]["timezone"])
    now = datetime.now(tz).time()

    base_start = dt_time.fromisoformat(config["timing"]["start_run_time"])
    base_end = dt_time.fromisoformat(config["timing"]["end_run_time"])

    start_offset = random.randint(
        -config["timing"]["start_random_window"],
        config["timing"]["start_random_window"],
    )
    end_offset = random.randint(
        -config["timing"]["end_random_window"], config["timing"]["end_random_window"]
    )

    today = datetime.now(tz).date()
    start_datetime = datetime.combine(today, base_start) + timedelta(
        minutes=start_offset
    )
    end_datetime = datetime.combine(today, base_end) + timedelta(minutes=end_offset)

    randomized_start = start_datetime.time()
    randomized_end = end_datetime.time()

    if randomized_start <= randomized_end:
        return not (randomized_start <= now <= randomized_end)
    else:
        return not (now >= randomized_start or now <= randomized_end)


def get_random_media_with_commenters(cl, user_id, media_amount=5, comment_pages=3):
    all_commenters = []
    medias = cl.user_medias(user_id, amount=media_amount)
    if not medias:
        return None, []

    random.shuffle(medias)
    target_media = random.choice(medias)

    max_id = None
    for _ in range(comment_pages):
        try:
            result = cl.media_comments_chunk(target_media.id, max_id=max_id)
            all_commenters.extend(result[0])
            max_id = result[1]
            if not max_id:
                break
        except Exception as e:
            logging.warning("Failed to fetch comment chunk: %s", e)
            break

    random.shuffle(all_commenters)
    return target_media, all_commenters


def run_bot(
    cl: Client,
    config: dict,
    conn,
    comment_bank: list,
    limits: dict,
    force_run: bool = False,
    notifier: TelegramNotifier = None,
    start_time: datetime = None,
):
    tz_name = config["timing"]["timezone"]
    c = conn.cursor()
    random.shuffle(config["targets"]["accounts"])
    notified_exit = False

    if is_outside_time_window(config):
        logging.info("⏰ Current time is outside of allowed timeframe. Exiting.")
        if notifier and not notified_exit:
            notifier.send("⏰ Bot run skipped – outside of allowed timeframe.")
            notified_exit = True
        return

    comments_done, likes_done, interactions_done = log_progress(conn, tz_name, limits)
    progress_counter = 0
    batch_counter = 0
    batch_size = random.randint(
        config["batch"]["size_min"], config["batch"]["size_max"]
    )

    verbosity = config.get("telegram", {}).get("verbosity", "all")

    def notify(message, level="info"):
        if notifier and (verbosity == "all" or level == "error"):
            notifier.send(message)

    notify(
        f"🚀 Bot started\nProgress so far: 💬 {comments_done}/{limits['daily_comments']}, ❤️ {likes_done}/{limits['daily_likes']}, 📏 {interactions_done}/{limits['daily_interactions']}"
    )

    for target_account in config["targets"]["accounts"]:
        comments_done, likes_done, interactions_done = get_local_interaction_totals(
            conn, tz_name
        )
        if not force_run and (
            interactions_done >= limits["daily_interactions"]
            or (
                likes_done >= limits["daily_likes"]
                and comments_done >= limits["daily_comments"]
            )
        ):
            logging.info(
                "✅ Exit condition met. Interactions: %s, Likes: %s, Comments: %s",
                interactions_done,
                likes_done,
                comments_done,
            )
            if notifier and not notified_exit:
                notifier.send(
                    f"✅ Bot stopped due to reaching limit. Interactions: {interactions_done}, Likes: {likes_done}, Comments: {comments_done}"
                )
                notified_exit = True
            break

        logging.info("Targeting account: %s", target_account)
        try:
            user_id = cl.user_id_from_username(target_account)
        except ChallengeRequired:
            notify(
                f"🚨 Challenge required for account: `{target_account}`. Bot will stop.",
                level="error",
            )
            sys.exit(1)
        except LoginRequired:
            notify(
                "❌ Login required. Bot session invalid. Stopping bot.", level="error"
            )
            sys.exit(1)
        except Exception as e:
            logging.warning("Failed to get user_id for %s: %s", target_account, e)
            continue

        medias = cl.user_medias(user_id, amount=5)
        if not medias:
            logging.info("No posts found for %s", target_account)
            continue

        target_media = random.choice(medias)
        commenters = cl.media_comments(target_media.id)
        if not commenters:
            logging.info("No comments found on post")
            continue

        random.shuffle(commenters)
        for commenter in commenters:
            comments_done, likes_done, interactions_done = get_local_interaction_totals(
                conn, tz_name
            )
            if not force_run and (
                interactions_done >= limits["daily_interactions"]
                or (
                    likes_done >= limits["daily_likes"]
                    and comments_done >= limits["daily_comments"]
                )
            ):
                logging.info(
                    "✅ Exit condition met. Interactions: %s, Likes: %s, Comments: %s",
                    interactions_done,
                    likes_done,
                    comments_done,
                )
                if notifier and not notified_exit:
                    notifier.send(
                        f"✅ Bot stopped due to reaching limit. Interactions: {interactions_done}, Likes: {likes_done}, Comments: {comments_done}"
                    )
                    notified_exit = True
                break

            username = commenter.user.username
            c.execute("SELECT * FROM users WHERE username=?", (username,))
            if c.fetchone():
                logging.info("Already seen user: %s", username)
                continue

            try:
                user_info = cl.user_info_by_username(username)
            except ChallengeRequired:
                notify(
                    f"🚨 Challenge required when accessing user `{username}`. Stopping bot.",
                    level="error",
                )
                sys.exit(1)
            except LoginRequired:
                notify(
                    "❌ Login required during user fetch. Stopping bot.", level="error"
                )
                sys.exit(1)
            except Exception as e:
                logging.warning("Error fetching user %s: %s", username, e)
                continue

            if user_info.is_private:
                logging.info("User is private: %s", username)
                c.execute(
                    "INSERT OR IGNORE INTO users VALUES (?, ?, CURRENT_TIMESTAMP)",
                    (username, 1),
                )
                conn.commit()
                continue

            user_posts = cl.user_medias(user_info.pk, amount=5)
            if not user_posts:
                continue

            random.shuffle(user_posts)
            comment_post = user_posts[0]
            like_post = user_posts[1] if len(user_posts) > 1 else comment_post

            can_comment = (
                force_run or comments_done < limits["daily_comments"]
            ) and limits["max_comments_per_user"] > 0
            if can_comment:
                comment = random.choice(comment_bank)
                try:
                    cl.media_comment(comment_post.id, comment)
                    logging.info("Commented on %s: %s", username, comment)
                    c.execute(
                        "INSERT INTO interactions VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
                        (username, comment_post.id, "comment"),
                    )
                    conn.commit()
                except Exception as e:
                    logging.warning("Failed to comment on %s: %s", username, e)
            else:
                logging.debug("Skipping comment for %s (limit reached)", username)

            can_like = (force_run or likes_done < limits["daily_likes"]) and limits[
                "max_likes_per_user"
            ] > 0
            if can_like and (
                force_run or interactions_done < limits["daily_interactions"]
            ):
                try:
                    cl.media_like(like_post.id)
                    logging.info(
                        "Liked post by %s – Media ID: %s", username, like_post.id
                    )
                    c.execute(
                        "INSERT INTO interactions VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
                        (username, like_post.id, "like"),
                    )
                    conn.commit()
                except Exception as e:
                    logging.warning("Failed to like post for %s: %s", username, e)
            else:
                logging.debug("Skipping like for %s (limit reached)", username)

            c.execute(
                "INSERT OR IGNORE INTO users VALUES (?, ?, CURRENT_TIMESTAMP)",
                (username, 0),
            )
            conn.commit()

            progress_counter += 1
            batch_counter += 1

            if progress_counter % 10 == 0:
                log_progress(conn, tz_name, limits)

            if batch_counter >= batch_size:
                log_batch_sleep(
                    config["batch"]["sleep_min"], config["batch"]["sleep_max"]
                )
                batch_counter = 0
                batch_size = random.randint(
                    config["batch"]["size_min"], config["batch"]["size_max"]
                )

            log_sleep(config["timing"]["min_sleep"], config["timing"]["max_sleep"])
            log_progress(conn, tz_name, limits)

    comments_done, likes_done, interactions_done = get_local_interaction_totals(
        conn, tz_name
    )
    logging.info("Finished for today. Total interactions: %s", interactions_done)
    if notifier and not notified_exit:
        notifier.send(f"🔚 Bot finished. Total interactions today: {interactions_done}")
        notified_exit = True
