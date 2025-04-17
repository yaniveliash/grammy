import logging
import time
import random

def log_sleep(min_sleep: float, max_sleep: float):
    sleep_time = random.uniform(min_sleep, max_sleep)
    logging.info(f"Sleeping for {sleep_time:.2f} seconds")
    time.sleep(sleep_time)