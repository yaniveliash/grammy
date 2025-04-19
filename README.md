<p align="center">
  <img src="assets/logo.png" alt="Grammy logo" width="300"/>
</p>

# 📸 Grammy – Your Friendly Instagram Growth Assistant

**Grammy** helps you grow your Instagram account naturally by interacting with real people who comment on big accounts like NatGeo, BBC Earth, and National Park Service. It likes and replies to their posts in a human-like way — safely and slowly.

---

## ⚠️ Disclaimer

Using automation tools on Instagram is against their terms of service. While **Grammy** is designed with safety in mind (slow, randomized, human-like behavior), there is still a **risk that your account could be temporarily limited, flagged, or banned**.

You are solely responsible for any consequences resulting from using this tool. Use it at your own risk.

---

## ✨ What It Does
- 💬 Likes and comments on posts from people interested in nature and photography
- ⏰ Runs at random times during your set hours
- 🔒 Supports 2FA with TOTP codes
- 💾 Remembers your login and device (like a real phone!)
- 🧠 Avoids repeating actions or spamming the same users
- 🌍 Respects your local timezone and daily limits
- 🗂 Saves everything in a lightweight local database
- 📊 Shows what it did today via a simple report

---

## 🚀 Quick Start Guide (No Tech Skills Needed!)

### 1. **Install Grammy**
Open your terminal and run:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. **Set Up Your Settings File**
Copy the default setup:
```bash
cp config.yaml.default config.yaml
```
Then open `config.yaml` and:
- Add your Instagram username & password
- Paste your 2FA secret (if you use an app like Google Authenticator)
- Choose which accounts you want to target (like `natgeo`, `bbcearth`, etc.)
- Set daily limits and hours Grammy should run:

```yaml
timing:
  timezone: "Asia/Jerusalem"
  start_run_time: "08:00"
  end_run_time: "14:00"
```

You can also add a **device profile** if you want Grammy to pretend it's your real phone.

### 3. **Create the Runner Script**
Make sure you have a file named `run.sh`:
```bash
#!/bin/bash
cd "$(dirname "$0")"
. .venv/bin/activate
python3 -m grammy "$@"
```
Make it executable:
```bash
chmod +x run.sh
```

### 4. **Schedule It Automatically**
Let Grammy decide when to run each day. Add this to your crontab:
```bash
* * * * * /path/to/grammy/run.sh >> /dev/null 2>&1
```
Grammy will check every minute and only run during the window you chose.

### 5. **Run It Now (If You Want)**
```bash
./run.sh --now
```
To ignore limits and run everything:
```bash
./run.sh --now --force
```

---

## 📱 Real Phone Emulation
Want it to act like your real Samsung? You can! Just add a `device` section in `config.yaml`, or let Grammy generate one for you and save it for next time.

---

## 📊 See What Grammy Did
Run this command to get a report:
```bash
./report.sh
```
(This is a wrapper around `report.py` for convenience)
You'll see:
- ✅ If the bot is currently running
- 💬 Number of likes, comments, and users today
- 👥 Who it interacted with (today and forever)

---

## 🧠 Smart & Safe By Design
Grammy is built to avoid Instagram's radar:
- Mimics real human timing
- Remembers who it interacted with
- Stays within safe limits
- Avoids private users automatically
- Keeps your session saved, so you don't get logged out

---

## ❤️ Built On
- [instagrapi](https://github.com/adw0rd/instagrapi)

Grammy is private, local, and yours. No cloud. No API keys. Just safe, organic growth. 🌱
