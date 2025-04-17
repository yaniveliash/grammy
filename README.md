# 📸 Grammy – Instagram Growth Bot

**Grammy** is your smart assistant for organic Instagram growth. It interacts daily with like-minded users who comment on major photography and nature-related accounts, leaving friendly comments and likes. All interactions are tracked to prevent duplication and respect daily interaction limits.

---

## 🔧 Configuration (`config.yaml`)

### `instagram`
| Key             | Description                                  |
|----------------|----------------------------------------------|
| `username`      | Your Instagram username                      |
| `password`      | Your Instagram password                      |
| `totp_enabled`  | `true` if you use 2FA with an authenticator  |
| `totp_secret`   | TOTP base32 secret                           |

### `paths`
| Key          | Description                                      |
|---------------|--------------------------------------------------|
| `db_path`     | Absolute path to SQLite DB (can be on NAS)       |
| `logs_path`   | Folder to store daily logs                       |

### `limits`
| Key                     | Description                                 |
|-------------------------|---------------------------------------------|
| `daily_interactions`    | Max combined actions (likes + comments)     |
| `daily_likes`           | Max likes per day                           |
| `daily_comments`        | Max comments per day                        |
| `max_likes_per_user`    | Max likes per user                          |
| `max_comments_per_user` | Max comments per user                       |

### `targets.accounts`
A list of Instagram accounts to pull random commenters from.

### `timing`
| Key         | Description                                       |
|-------------|---------------------------------------------------|
| `min_sleep` | Minimum delay (seconds) between actions           |
| `max_sleep` | Maximum delay (seconds) between actions           |
| `run_time`  | Daily scheduled time to run (e.g. `"02:00"`)      |

### `comments`
A list of generic, friendly comments to use randomly.

---

## 🛠 Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## ⏱ Automatic Daily Execution

To run Grammy once per day at the time defined in `config.yaml`:

1. **Ensure `run.sh` is executable**
```bash
chmod +x run.sh
```

2. **Add to crontab**
```bash
crontab -e
```
Add:
```bash
* * * * * /path/to/grammy/run.sh >> /dev/null 2>&1
```
This runs `run.sh` every minute. `run.sh` checks if:
- Current time matches `run_time`
- The script is not already running
- The interaction limits are not already reached

---

## 💾 Database

SQLite is used to track users and interactions:
- `users` table tracks private vs public and avoids reprocessing.
- `interactions` logs each comment or like per post.

Inspect with:
```bash
sqlite3 /path/to/bot.db "SELECT * FROM interactions ORDER BY timestamp DESC LIMIT 10;"
```

---

## 📋 Daily Stats

Run the housekeeping tool to see progress:
```bash
python3 housekeeping_report.py
```
This shows:
- Daily usage vs limits
- Daily and all-time interacted users

---

Let me know if you'd like to add:
- Email summaries
- Markdown/CSV output for logs
- A web UI for visualizing growth
