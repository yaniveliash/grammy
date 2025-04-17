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
- Runs via cron or manually with `--now` override

---

## 🛠 Setup Instructions

1. **Install dependencies:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Edit your `config.yaml`:**
   Define your credentials, limits, target accounts, sleep intervals, comments, and (optionally) your device profile.

3. **Create your execution script:**
   Make sure `run.sh` runs `main.py` and prevents overlapping executions.

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

---

## 📱 Device Emulation
You can optionally specify your own device profile to simulate a real phone. If not set, one is generated and saved automatically.

---

## 📋 Housekeeping
Run this script to check daily interaction stats:
```bash
python3 housekeeping_report.py
```

---

## 📎 Credits
- Powered by [instagrapi](https://github.com/adw0rd/instagrapi)
