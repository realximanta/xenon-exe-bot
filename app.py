import os
import asyncio
import logging
import time
import threading

from flask import Flask, jsonify
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import InputPhoneContact
from telethon.tl.functions.contacts import ImportContactsRequest, DeleteContactsRequest
from telethon.errors import FloodWaitError, PeerFloodError

# --- Configuration ---
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))  # Your personal Telegram User ID

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Flask App for Health Check ---
app = Flask(__name__)

@app.route('/health')
@app.route('/')
def health():
    return jsonify({
        "status": "ok",
        "timestamp": time.time(),
        "service": "telegram-broadcaster"
    })

# --- Telethon Client ---
client = TelegramClient(
    StringSession(SESSION_STRING),
    API_ID,
    API_HASH,
    connection_retries=None,
    retry_delay=5,
    auto_reconnect=True
)

# --- Contact Cache Management ---
contact_cache = {}  # phone_number -> user_id

async def resolve_contact(phone):
    """Resolves a phone number to a Telegram user, with caching."""
    if phone in contact_cache:
        return contact_cache[phone]

    try:
        contact = InputPhoneContact(client_id=0, phone=phone, first_name="", last_name="")
        result = await client(ImportContactsRequest([contact]))

        if result.users:
            user_id = result.users[0].id
            contact_cache[phone] = user_id
            # Clean up: remove from contacts immediately after resolving
            await client(DeleteContactsRequest(id=[result.users[0]]))
            return user_id
        else:
            logger.warning(f"Phone {phone} not registered on Telegram.")
            return None
    except Exception as e:
        logger.error(f"Failed to resolve {phone}: {e}")
        return None

# --- Broadcast Logic ---
async def broadcast_message(text, recipients):
    """
    Sends a message to all recipients sequentially.
    Handles FloodWait by waiting the required time.
    """
    success_count = 0
    fail_count = 0

    for recipient in recipients:
        try:
            await client.send_message(recipient, text)
            success_count += 1
            logger.info(f"Sent to {recipient}")
            # Delay between messages to avoid flood
            await asyncio.sleep(2)
        except FloodWaitError as e:
            logger.warning(f"FloodWait: Sleeping for {e.seconds} seconds.")
            await asyncio.sleep(e.seconds + 5)
            # Retry once after flood wait
            try:
                await client.send_message(recipient, text)
                success_count += 1
                logger.info(f"Sent to {recipient} after flood wait")
            except Exception as retry_e:
                logger.error(f"Failed to send to {recipient} after retry: {retry_e}")
                fail_count += 1
        except PeerFloodError:
            logger.error("PeerFloodError: Too many messages. Stopping broadcast.")
            await client.send_message(ADMIN_ID, "⚠️ Broadcast stopped: PeerFloodError. Account temporarily limited.")
            break
        except Exception as e:
            logger.error(f"Failed to send to {recipient}: {e}")
            fail_count += 1

    return success_count, fail_count

# --- Telegram Event Handlers ---
@client.on(events.NewMessage(chats=ADMIN_ID))
async def handle_broadcast(event):
    """
    Listens for messages from the admin (you).
    Format: /send <target1>,<target2>,... | <message>
    Or simply: <message> (for a simple forward to groups)
    """
    if not event.message.text:
        return

    text = event.message.text

    # Check for a custom command format
    if text.startswith("/send "):
        try:
            # Format: /send @user1,+1234567890,@group | Hello world
            parts = text[6:].split("|", 1)
            if len(parts) != 2:
                await event.reply("❌ Format: `/send <targets> | <message>`")
                return

            target_str = parts[0].strip()
            message_text = parts[1].strip()
            targets = [t.strip() for t in target_str.split(",") if t.strip()]

            if not targets:
                await event.reply("❌ No targets provided.")
                return

            await event.reply(f"🚀 Starting broadcast to {len(targets)} targets...")

            # Resolve phone numbers in the target list
            resolved_targets = []
            for target in targets:
                if target.startswith("+") and target[1:].isdigit():
                    uid = await resolve_contact(target)
                    if uid:
                        resolved_targets.append(uid)
                    else:
                        await event.reply(f"⚠️ Could not resolve {target}, skipping.")
                else:
                    resolved_targets.append(target)

            if not resolved_targets:
                await event.reply("❌ No valid targets resolved.")
                return

            # Run broadcast in background to not block
            async def run_broadcast():
                success, fail = await broadcast_message(message_text, resolved_targets)
                await client.send_message(ADMIN_ID, f"✅ Broadcast complete.\nSuccess: {success}\nFailed: {fail}")

            asyncio.create_task(run_broadcast())

        except Exception as e:
            await event.reply(f"❌ Error: {e}")
    else:
        # Fallback: Treat any other message as a simple forward to a predefined list
        # You can customize this to forward to specific groups/users
        await event.reply("ℹ️ Send `/send <targets> | <message>` to broadcast.\nExample: `/send @user1, +1234567890 | Hello!`")

# --- Main Startup ---
async def start_telethon():
    """Starts the Telethon client."""
    await client.start()
    me = await client.get_me()
    logger.info(f"Logged in as {me.first_name} (@{me.username})")
    await client.send_message(ADMIN_ID, "🤖 Bot is online and ready.")

def run_telethon_loop():
    """Runs the Telethon client in a separate thread with its own event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def main():
        await start_telethon()
        await client.run_until_disconnected()

    loop.run_until_complete(main())

# Start Telethon in a background thread when the Flask app starts
# This prevents the Flask health check from blocking the Telegram client.
telethon_thread = threading.Thread(target=run_telethon_loop, daemon=True)
telethon_thread.start()

# --- Flask Run (for local testing, Render uses gunicorn) ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
