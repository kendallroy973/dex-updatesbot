import requests
import time
import re
import telebot
import threading
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

BOT_TOKEN = "8655274276:AAFbqvqc3-B6-8wLqpUMPPKTBVF3CEKFy-I"
ALERT_CHANNEL = "@DEXSTRACKON"

print("1. Starting script...")

bot = telebot.TeleBot(BOT_TOKEN)
print("2. Bot initialized successfully")

monitored = {}

print("3. Health server starting...")

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')

def run_health():
    port = int(os.environ.get('PORT', 8080))
    print(f"4. Health server listening on port {port}")
    HTTPServer(('', port), HealthHandler).serve_forever()

threading.Thread(target=run_health, daemon=True).start()

print("5. Entering main loop...")

def extract_usernames(text):
    if not text:
        return []
    patterns = [r'@([a-zA-Z0-9_]{5,32})', r't\.me/([a-zA-Z0-9_]{5,32})']
    found = []
    for p in patterns:
        found.extend(re.findall(p, text, re.IGNORECASE))
    return [u.lower().strip() for u in found if len(u) >= 5]

while True:
    try:
        print("6. Running scan cycle...")   # This should print every ~10 seconds

        messages = bot.get_chat_history(ALERT_CHANNEL, limit=50)
        print(f"7. Got {len(messages)} messages from channel")

        added = 0
        for msg in messages:
            if msg.text:
                usernames = extract_usernames(msg.text)
                for u in usernames:
                    if u not in monitored:
                        monitored[u] = time.time()
                        added += 1
                        print(f"✅ Added @{u} to monitoring")

        if added > 0:
            print(f"Total monitored: {len(monitored)}")

        # Check for deletions
        now = time.time()
        for username in list(monitored.keys()):
            if now - monitored.get(username, 0) > 40:
                try:
                    if is_username_deleted(username):   # we'll define this below
                        alert = f"🔓 @{username} is now AVAILABLE!"
                        bot.send_message(ALERT_CHANNEL, alert)
                        print(f"🚨 ALERT: @{username} available!")
                        del monitored[username]
                except:
                    pass
                monitored[username] = now

    except Exception as e:
        print(f"ERROR in loop: {e}")

    time.sleep(10)

def is_username_deleted(username):
    try:
        r = requests.get(f"https://t.me/{username}", timeout=8)
        content = r.text.lower()
        return any(x in content for x in ["doesn't exist", "channel not found", "no longer exists"])
    except:
        return False
