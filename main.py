import requests
import time
import re
import telebot
import threading
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

BOT_TOKEN = "8655274276:AAFbqvqc3-B6-8wLqpUMPPKTBVF3CEKFy-I"
ALERT_CHANNEL = "@DEXSTRACKON"

bot = telebot.TeleBot(BOT_TOKEN)

monitored = {}  # username -> last_checked_time

print("🕵️ Deleted TG Username Tracker Started (Improved Version)")

# Health server
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK - Tracker Running')

def run_health():
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('', port), HealthHandler)
    print(f"✅ Health server running on port {port}")
    server.serve_forever()

threading.Thread(target=run_health, daemon=True).start()

def extract_usernames(text):
    if not text:
        return []
    # Improved regex for @username and t.me/ links
    patterns = [
        r'@([a-zA-Z0-9_]{5,32})',
        r't\.me/([a-zA-Z0-9_]{5,32})',
        r'telegram\.me/([a-zA-Z0-9_]{5,32})'
    ]
    found = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        found.extend(matches)
    return [u.lower().strip() for u in found if len(u) >= 5]

def is_username_deleted(username):
    try:
        r = requests.get(f"https://t.me/{username}", timeout=10)
        if r.status_code != 200:
            return True
        content = r.text.lower()
        if any(phrase in content for phrase in ["doesn't exist", "channel not found", "no longer exists", "this channel doesn't exist"]):
            return True
        return False
    except:
        return False

print("🔄 Starting main loop...")

while True:
    try:
        # Scan alert channel for forwarded messages
        messages = bot.get_chat_history(ALERT_CHANNEL, limit=120)
        
        added_count = 0
        for msg in messages:
            if msg.text:
                usernames = extract_usernames(msg.text)
                for u in usernames:
                    if u not in monitored:
                        monitored[u] = time.time()
                        added_count += 1
                        print(f"✅ Added new username to monitor: @{u}")

        if added_count > 0:
            print(f"Total monitored usernames: {len(monitored)}")

        # Check for deletions
        now = time.time()
        for username in list(monitored.keys()):
            if now - monitored[username] > 35:  # Check roughly every 35 seconds
                if is_username_deleted(username):
                    alert = f"""
🔓 **USERNAME NOW AVAILABLE!**

**@{username}** has been **deleted** and is ready to claim!

🕒 Detected: {time.strftime('%Y-%m-%d %H:%M:%S')}
                    """.strip()
                    
                    bot.send_message(ALERT_CHANNEL, alert, parse_mode="Markdown")
                    print(f"🚨 ALERT SENT → @{username} is available!")
                    del monitored[username]   # Stop monitoring after alert
                else:
                    monitored[username] = now

    except Exception as e:
        print(f"Loop error: {e}")

    time.sleep(10)  # Main loop every 10 seconds
