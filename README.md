<p align="center">
 <p align="center">
  <img src="https://cdn.simpleicons.org/telegram/26A5E4" alt="Telegram Broadcaster" width="200" height="200"/>
</p>

<h1 align="center">📡 Telegram Broadcaster - xenon exe bot</h1>

<p align="center">
  <em>A 24/7 Telegram automation bot that broadcasts your messages to contacts, non-contacts, and groups — deployed on Render, kept alive by UptimeRobot.</em>
</p>

<p align="center">
  <a href="https://render.com"><img src="https://img.shields.io/badge/Deploy-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white" alt="Deploy on Render"/></a>
  <a href="https://uptimerobot.com"><img src="https://img.shields.io/badge/Keep--Alive-UptimeRobot-3FBE7B?style=for-the-badge&logo=uptimerobot&logoColor=white" alt="UptimeRobot"/></a>
  <a href="https://telegram.org"><img src="https://img.shields.io/badge/Telegram-API-26A5E4?style=for-the-badge&logo=telegram&logoColor=white" alt="Telegram API"/></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Telethon-1.36+-blue?style=flat-square" alt="Telethon"/>
  <img src="https://img.shields.io/badge/Flask-3.0+-000000?style=flat-square&logo=flask&logoColor=white" alt="Flask"/>
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" alt="License"/>
  <img src="https://img.shields.io/badge/Status-Active-success?style=flat-square" alt="Status"/>
  <img src="https://img.shields.io/badge/PRs-Welcome-brightgreen?style=flat-square" alt="PRs Welcome"/>
</p>

---

## 🧭 Overview

**Telegram Broadcaster** is a self-hosted automation tool that runs on [Render](https://render.com)'s free tier and stays alive 24/7 thanks to a `/health` endpoint pinged by [UptimeRobot](https://uptimerobot.com). It uses your **personal Telegram account** (via a Telethon session string) to send messages to:

- ✅ Personal contacts (by username or user ID)
- ✅ Non-contacts (by phone number — imported, messaged, then removed)
- ✅ Group chats and channels (by group ID)
- ✅ Usernames (`@someone`)

Send one command to your own "Saved Messages", and the bot fans it out to everyone on your list — patiently, with flood protection, no matter how long it takes.

> ⚠️ **Heads up:** Telegram does **not** allow bot-token bots to DM users who haven't started a chat first. That's why this project uses your **user account** session instead. Read the [Disclaimer](#-disclaimer) before using.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔁 **24/7 Uptime** | Flask `/health` endpoint designed for UptimeRobot cron pings. |
| 🧠 **Session String Auth** | No interactive login — runs headless from an env var. |
| 📨 **Bulk Broadcasting** | Send one message to unlimited targets, sequentially. |
| 📞 **Non-Contact Support** | Resolves phone numbers via `ImportContactsRequest`, sends, then cleans up. |
| ⏳ **FloodWait Handling** | Automatically waits and retries when Telegram rate-limits you. |
| 🛡️ **PeerFlood Guard** | Stops the broadcast if your account is temporarily limited. |
| 💾 **Contact Cache** | Avoids re-resolving the same phone number repeatedly. |
| 📊 **Delivery Report** | Sends you a success/fail summary when the broadcast finishes. |
| 🔌 **Zero-Config Deploy** | `render.yaml` blueprint + env vars = one-click deploy. |

---

## 🚀 Quick Start

### 1. Prerequisites

- A [Render](https://render.com) account (free tier works)
- A [UptimeRobot](https://uptimerobot.com) account (free tier works)
- Your Telegram `API_ID`, `API_HASH`, and a `SESSION_STRING`
- Your Telegram numeric `ADMIN_ID`

### 2. Generate Your Session String

Run this locally **once**:

```python
# generate_session.py
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

API_ID = int(input("API_ID: "))
API_HASH = input("API_HASH: ")

with TelegramClient(StringSession(), API_ID, API_HASH) as client:
    print("\nYour SESSION_STRING:\n")
    print(client.session.save())
```

Install and run:

```bash
pip install telethon
python generate_session.py
```

Copy the printed string — that's your `SESSION_STRING`.

### 3. Get Your Admin ID

Message [@userinfobot](https://t.me/userinfobot) on Telegram. It replies with your numeric `Id`. That's your `ADMIN_ID`.

### 4. Deploy to Render

1. Fork / push this repo to GitHub.
2. In Render: **New +** → **Blueprint** → select your repo.
3. Render reads `render.yaml` and creates the service.
4. Add these **Environment Variables** in the dashboard:

   | Key | Value |
   |---|---|
   | `API_ID` | Your Telegram API ID |
   | `API_HASH` | Your Telegram API Hash |
   | `SESSION_STRING` | The string from step 2 |
   | `ADMIN_ID` | Your numeric Telegram ID |

5. Click **Deploy**.

### 5. Keep It Alive with UptimeRobot

1. Copy your Render URL: `https://your-app.onrender.com`
2. In UptimeRobot: **Add New Monitor** → **HTTP(s)**
3. **URL:** `https://your-app.onrender.com/health`
4. **Interval:** 5 minutes
5. Save. Done — Render will never sleep.

---

## 🎮 Usage

From your own Telegram account, message the broadcast account:

### Broadcast syntax

```
/send <target1>,<target2>,... | <your message>
```

### Examples

**To a username and a group:**
```
/send @friend_username, -1001234567890 | Hello everyone! 👋
```

**To a non-contact by phone number:**
```
/send +1234567890 | Hey, long time no see!
```

**To a mixed list:**
```
/send @alice, +15551234567, -1009876543210 | Big announcement coming...
```

### What happens next

1. Bot replies `🚀 Starting broadcast to N targets...`
2. Sends the message to each target with a **2-second delay** between sends
3. If Telegram returns `FloodWaitError`, it waits the required time, then retries
4. If a `PeerFloodError` occurs, it stops and warns you
5. Finally, it DMs you: `✅ Broadcast complete. Success: X / Failed: Y`

---

## 🗂️ Project Structure

```
telegram-broadcaster/
├── app.py               # Main app: Flask health server + Telethon client
├── requirements.txt     # Python dependencies
├── render.yaml          # Render deployment blueprint
├── README.md            # You are here
```

---

## 🧩 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `API_ID` | ✅ | Telegram API ID from [my.telegram.org](https://my.telegram.org) |
| `API_HASH` | ✅ | Telegram API Hash |
| `SESSION_STRING` | ✅ | Telethon session string (from `generate_session.py`) |
| `ADMIN_ID` | ✅ | Your numeric Telegram user ID (receives reports) |
| `PORT` | ❌ | Auto-set by Render |

---

## 🔐 Security Notes

- **Never commit** your `SESSION_STRING`, `API_HASH`, or `API_ID` to GitHub.
- Use Render's **Environment Variables** panel — never hardcode secrets.
- The `SESSION_STRING` grants **full access** to your Telegram account. Treat it like a password.
- If leaked: revoke sessions in Telegram → **Settings → Devices → Terminate All Other Sessions**.

---

## ⚠️ Disclaimer

This project uses your **personal Telegram user account**, not a bot token. That means:

- **Telegram's ToS applies to your user account.** Mass-messaging strangers is against Telegram's policy and may get your account **limited or banned**.
- **Flood limits are real.** Even with the built-in delays, sending hundreds of messages in a short window will trigger `FloodWaitError` or worse.
- **Non-contact messaging is intrusive.** Only message people who have consented to hear from you.
- **Use responsibly.** This tool is intended for legitimate use cases like notifying your own groups, contacts, or communities — not for spam.

The author assumes **no responsibility** for account bans, suspensions, or misuse.

---

## 🛠️ Roadmap

- [ ] CSV upload of targets
- [ ] Scheduled broadcasts (cron-based)
- [ ] Media support (images, videos, files)
- [ ] Per-target delivery log in SQLite
- [ ] Web UI for target management
- [ ] Retry queue for failed sends

PRs welcome!

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/amazing-thing`
3. Commit: `git commit -m "Add amazing thing"`
4. Push: `git push origin feature/amazing-thing`
5. Open a Pull Request

---

## 📜 License

Released under the **MIT License**. See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgements

- [Telethon](https://github.com/LonamiWebs/Telethon) — the async Telegram client that makes this possible
- [Render](https://render.com) — free hosting with a generous free tier
- [UptimeRobot](https://uptimerobot.com) — the keep-alive cron that never sleeps
- [shields.io](https://shields.io) — all the pretty badges above

---

<p align="center">
  <sub>Built with ❤️ and a mild fear of <code>FloodWaitError</code>.</sub>
</p>

<p align="center">
  <a href="#top">⬆️ Back to top</a>
</p>
