import json
import logging
from pathlib import Path
from instagrapi import Client
import pyotp


def prepare_device(cl: Client, config: dict):
    device_file = config['paths'].get('device_profile')

    if 'device' in config:
        cl.set_device(config['device'])
        logging.info("Using device profile from config.yaml")
    elif device_file and Path(device_file).exists():
        with open(device_file, 'r') as f:
            cl.set_device(json.load(f))
        logging.info("Loaded existing device profile from %s", device_file)
    else:
        cl.set_device(cl.generate_device(seed=config['instagram']['username']))
        logging.info("Generated new device profile")
        if device_file:
            with open(device_file, 'w') as f:
                json.dump(cl.device, f)
            logging.info("Saved device profile to %s", device_file)


def authenticate(cl: Client, config: dict):
    if config['instagram']['totp_enabled']:
        totp = pyotp.TOTP(config['instagram']['totp_secret'])
        code = totp.now()
        logging.info(f"Generated 2FA code: {code}")
        cl.login(config['instagram']['username'], config['instagram']['password'], verification_code=code)
    else:
        cl.login(config['instagram']['username'], config['instagram']['password'])
