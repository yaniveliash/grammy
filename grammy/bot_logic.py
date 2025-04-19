import logging
import random
import time
from instagrapi import Client

def log_sleep(min_sleep: float, max_sleep: float):
    sleep_time = random.uniform(min_sleep, max_sleep)
    logging.info(f"Sleeping for {sleep_time:.2f} seconds")
    time.sleep(sleep_time)

def run_bot(cl: Client, config: dict, conn, comment_bank: list, limits: dict,
            comments_done: int, likes_done: int, interactions_done: int,
            force_run: bool = False):
    cl.delay_range = [config['timing']['min_sleep'], config['timing']['max_sleep']]
    c = conn.cursor()
    random.shuffle(config['targets']['accounts'])

    for target_account in config['targets']['accounts']:
        if not force_run and interactions_done >= limits['daily_interactions']:
            break

        logging.info("Targeting account: %s", target_account)
        user_id = cl.user_id_from_username(target_account)
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
            if not force_run and interactions_done >= limits['daily_interactions']:
                break

            username = commenter.user.username
            c.execute("SELECT * FROM users WHERE username=?", (username,))
            if c.fetchone():
                logging.info("Already seen user: %s", username)
                continue

            try:
                user_info = cl.user_info_by_username(username)
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
                    comments_done += 1
                    interactions_done += 1
                    c.execute("INSERT INTO interactions VALUES (?, ?, ?, CURRENT_TIMESTAMP)", (username, comment_post.id, 'comment'))
                    conn.commit()
                except Exception as e:
                    logging.warning("Failed to comment on %s: %s", username, e)

            log_sleep(config['timing']['min_sleep'], config['timing']['max_sleep'])

            if (force_run or likes_done < limits['daily_likes']) and limits['max_likes_per_user'] > 0 and (force_run or interactions_done < limits['daily_interactions']):
                try:
                    cl.media_like(like_post.id)
                    logging.info("Liked post for %s", username)
                    likes_done += 1
                    interactions_done += 1
                    c.execute("INSERT INTO interactions VALUES (?, ?, ?, CURRENT_TIMESTAMP)", (username, like_post.id, 'like'))
                    conn.commit()
                except Exception as e:
                    logging.warning("Failed to like post for %s: %s", username, e)

            c.execute("INSERT OR IGNORE INTO users VALUES (?, ?, CURRENT_TIMESTAMP)", (username, 0))
            conn.commit()

            log_sleep(config['timing']['min_sleep'], config['timing']['max_sleep'])

    logging.info("Finished for today. Total interactions: %s", interactions_done)
