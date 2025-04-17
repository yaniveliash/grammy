# 📸 Grammy – Instagram Growth Bot

**Grammy** is your smart assistant for organic Instagram growth. It interacts daily with like-minded users who comment on major photography and nature-related accounts, leaving friendly comments and likes. All interactions are tracked to prevent duplication and respect daily interaction limits.

---

## 📦 Features
- Daily interactions (likes & comments) based on your interests
- Randomized execution time to avoid detection
- 2FA login with TOTP support
- SQLite database for tracking users and history
- Configurable through YAML file
- Customizable mobile device simulation
- Timezone-aware logic for accurate daily tracking and reporting
- Tracks whether the bot is currently running via a status table
- Runs via cron or manually with `--now` override

---

## 🛠 Setup Instructions

1. **Install dependencies:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Create and Edit your `config.yaml`:**

   Copy the provided config.yaml.default to config.yaml, and fill in your personal credentials, target accounts, limits, and other settings.

   This ensures you:
   * Keep a clean default config for reference
   * Avoid merge conflicts when pulling updates from the repository

   ```bash
   cp config.yaml.default config.yaml
   ```

   Define your credentials, limits, target accounts, sleep intervals, comments, and (optionally) your device profile.

   Include a timezone (optional, defaults to UTC):
   ```yaml
   timing:
     timezone: "Asia/Jerusalem"
   ```

3. **Create your execution script:**
   Make sure `run.sh` runs the bot using the Python module and prevents overlapping executions.

4. **Schedule execution:**
   Add `run.sh` to your crontab to run every minute:
   ```bash
   * * * * * /path/to/grammy/run.sh >> /dev/null 2>&1
   ```
   The script will self-schedule a randomized run-time daily and auto-skip until it matches.

5. **Run manually (any time):**
   ```bash
   ./run.sh --now
   ```

   You can also bypass daily interaction limits:
   ```bash
   ./run.sh --now --force
   ```

---

## 📱 Device Emulation
You can optionally specify your own device profile to simulate a real phone. If not set, one is generated and saved automatically.

---

## 📋 Reports & Housekeeping
Run the report script to check current usage and bot status:
```bash
python3 report.py
```

### Output includes:
- Bot status (running/idle with timestamp)
- Today's likes, comments, and total interactions
- Interacted usernames (today/all-time/ignored)

Timezone-aware reporting ensures accurate filtering even when running near UTC boundaries.

---

## 📎 Credits
- Powered by [instagrapi](https://github.com/adw0rd/instagrapi)
