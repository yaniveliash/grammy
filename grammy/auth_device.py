import json
import logging
from pathlib import Path
from instagrapi import Client
import pyotp
from instagrapi.exceptions import LoginRequired, ChallengeRequired

def load_device_profile(config: dict) -> dict:
    if 'device' in config:
        return config['device']
    device_file = config['paths'].get('device_profile')
    if device_file and Path(device_file).exists():
        with open(device_file, 'r') as f:
            return json.load(f)
    return {}

def apply_device(cl: Client, device: dict, config: dict):
    if device:
        cl.set_device(device)
        cl.settings['device'] = device
        logging.info(f"Using device: {device.get('model', 'unknown')}")
    elif 'instagram' in config and 'username' in config['instagram']:
        device = cl.generate_device(seed=config['instagram']['username'])
        cl.set_device(device)
        cl.settings['device'] = device
        logging.info("Generated new device profile")
        device_file = config['paths'].get('device_profile')
        if device_file:
            with open(device_file, 'w') as f:
                json.dump(device, f)
            logging.info("Saved device profile to %s", device_file)


def authenticate(cl: Client, config: dict, conn):
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS session (id INTEGER PRIMARY KEY, session_json TEXT)")
    conn.commit()

    device = load_device_profile(config)

    # Try loading session
    c.execute("SELECT session_json FROM session WHERE id = 1")
    session_row = c.fetchone()
    if session_row:
        try:
            session_data = json.loads(session_row[0])
            cl.set_settings(session_data)
            apply_device(cl, device, config)
            cl.login(config['instagram']['username'], config['instagram']['password'])
            cl.get_timeline_feed()
            logging.info("✅ Logged in using saved session")
            return
        except LoginRequired:
            logging.info("⚠️ Session invalid, logging in with credentials")
            old_session = cl.get_settings()
            cl.set_settings({})
            cl.set_uuids(old_session.get("uuids"))
        except Exception as e:
            logging.warning("❌ Failed to load session: %s", e)

    # Fallback to login
    apply_device(cl, device, config)
    logging.info("🔐 Logging in with username and password")
    try:
        if config['instagram']['totp_enabled']:
            totp = pyotp.TOTP(config['instagram']['totp_secret'])
            code = totp.now()
            logging.info(f"Generated 2FA code: {code}")
            cl.login(config['instagram']['username'], config['instagram']['password'], verification_code=code)
        else:
            cl.login(config['instagram']['username'], config['instagram']['password'])
    except ChallengeRequired:
        logging.error("🚨 Instagram triggered a challenge (e.g. phone verification). Manual login required.")
        raise SystemExit("Bot stopped: challenge_required")

    session_data = json.dumps(cl.get_settings())
    c.execute("INSERT OR REPLACE INTO session (id, session_json) VALUES (1, ?)", (session_data,))
    conn.commit()
    logging.info("💾 New session saved to database")