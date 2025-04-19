import logging
import random
import time
import sys
from datetime import datetime, time as dt_time, timezone
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ChallengeRequired
from grammy.telegram_notify import TelegramNotifier
from grammy.utils import get_local_interaction_totals
import zoneinfo

def log_sleep(min_sleep: float, max_sleep: float):
    sleep_time = random.uniform(min_sleep, max_sleep)
    logging.info(f"Sleeping for {sleep_time:.2f} seconds")
    time.sleep(sleep_time)

def log_progress(conn, timezone_name, limits):
    comments_done, likes_done, interactions_done = get_local_interaction_totals(conn, timezone_name)
    logging.info(
        "Progress - Comments: %d/%d, Likes: %d/%d, Total Interactions: %d/%d",
        comments_done, limits['daily_comments'],
        likes_done, limits['daily_likes'],
        interactions_done, limits['daily_interactions']
    )
    return comments_done, likes_done, interactions_done

def run_bot(cl: Client, config: dict, conn, comment_bank: list, limits: dict,
            force_run: bool = False, notifier: TelegramNotifier = None, start_time: datetime = None):
    tz_name = config['timing']['timezone']
    c = conn.cursor()
    random.shuffle(config['targets']['accounts'])

    comments_done, likes_done, interactions_done = log_progress(conn, tz_name, limits)
    progress_counter = 0

    verbosity = config.get('telegram', {}).get('verbosity', 'all')

    def notify(message, level='info'):
        if notifier and (verbosity == 'all' or level == 'error'):
            notifier.send(message)

    notify(f"🚀 Bot started\nProgress so far: 💬 {comments_done}/{limits['daily_comments']}, ❤️ {likes_done}/{limits['daily_likes']}, 📏 {interactions_done}/{limits['daily_interactions']}")

    for target_account in config['targets']['accounts']:
        comments_done, likes_done, interactions_done = get_local_interaction_totals(conn, tz_name)
        if not force_run and (interactions_done >= limits['daily_interactions'] or \
            (likes_done >= limits['daily_likes'] and comments_done >= limits['daily_comments'])):
            break

        logging.info("Targeting account: %s", target_account)
        try:
            user_id = cl.user_id_from_username(target_account)
        except ChallengeRequired as e:
            message = f"🚨 Challenge required for account: `{target_account}`. Bot will stop."
            logging.error(message)
            notify(message, level='error')
            sys.exit(1)
        except LoginRequired as e:
            logging.error("❌ Login required: session expired or invalid. Stopping bot.")
            notify("❌ Login required. Bot session invalid. Stopping bot.", level='error')
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
            comments_done, likes_done, interactions_done = get_local_interaction_totals(conn, tz_name)
            if not force_run and (interactions_done >= limits['daily_interactions'] or \
                (likes_done >= limits['daily_likes'] and comments_done >= limits['daily_comments'])):
                break

            username = commenter.user.username
            c.execute("SELECT * FROM users WHERE username=?", (username,))
            if c.fetchone():
                logging.info("Already seen user: %s", username)
                continue

            try:
                user_info = cl.user_info_by_username(username)
            except ChallengeRequired as e:
                message = f"🚨 Challenge required when accessing user `{username}`. Stopping bot."
                logging.error(message)
                notify(message, level='error')
                sys.exit(1)
            except LoginRequired as e:
                logging.error("❌ Login required during user fetch. Stopping bot.")
                notify("❌ Login required during user fetch. Stopping bot.", level='error')
                sys.exit(1)
            except Exception as e:
                logging.warning("Error fetching user %s: %s", username, e)
                continue

            if user_info.is_private:
                logging.info("User is private: %s", username)
                c.execute("INSERT OR IGNORE INTO users VALUES (?, ?, CURRENT_TIMESTAMP)", (username, 1))
                conn.commit()
                continue

            user_posts = cl.user_medias(user_info.pk, amount=5)
            if not user_posts:
                continue

            random.shuffle(user_posts)
            comment_post = user_posts[0]
            like_post = user_posts[1] if len(user_posts) > 1 else comment_post

            if (force_run or comments_done < limits['daily_comments']) and limits['max_comments_per_user'] > 0:
                comment = random.choice(comment_bank)
                try:
                    cl.media_comment(comment_post.id, comment)
                    logging.info("Commented on %s: %s", username, comment)
                    c.execute("INSERT INTO interactions VALUES (?, ?, ?, CURRENT_TIMESTAMP)", (username, comment_post.id, 'comment'))
                    conn.commit()
                except Exception as e:
                    logging.warning("Failed to comment on %s: %s", username, e)

            if (force_run or likes_done < limits['daily_likes']) and limits['max_likes_per_user'] > 0 and (force_run or interactions_done < limits['daily_interactions']):
                try:
                    cl.media_like(like_post.id)
                    logging.info("Liked post for %s", username)
                    c.execute("INSERT INTO interactions VALUES (?, ?, ?, CURRENT_TIMESTAMP)", (username, like_post.id, 'like'))
                    conn.commit()
                except Exception as e:
                    logging.warning("Failed to like post for %s: %s", username, e)

            c.execute("INSERT OR IGNORE INTO users VALUES (?, ?, CURRENT_TIMESTAMP)", (username, 0))
            conn.commit()

            progress_counter += 1
            if progress_counter % 10 == 0:
                log_progress(conn, tz_name, limits)

            log_sleep(config['timing']['min_sleep'], config['timing']['max_sleep'])

    comments_done, likes_done, interactions_done = get_local_interaction_totals(conn, tz_name)
    logging.info("Finished for today. Total interactions: %s", interactions_done)