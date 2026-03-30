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

monitored = {}   # username: last_checked_time

print("🕵️ Deleted Username Tracker (Forward Method) Started...")

# Health server
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')

def run_health():
    port = int(os.environ.get('PORT', 8080))
    HTTPServer(('', port), HealthHandler).serve_forever()

threading.Thread(target=run_health, daemon=True).start()

def extract_usernames(text):
    if not text:
        return []
    patterns = [r'@([a-zA-Z0-9_]{5,32})', r't\.me/([a-zA-Z0-9_]{5,32})']
    found = []
    for p in patterns:
        found.extend(re.findall(p, text, re.IGNORECASE))
    return [u.lower() for u in found if len(u) >= 5]

def is_available(username):
    try:
        r = requests.get(f"https://t.me/{username}", timeout=10, allow_redirects=True)
        if r.status_code == 200:
            text = r.text.lower()
            if any(word in text for word in ["doesn't exist", "channel not found", "no longer exists", "private group"]):
                return True
        return False
    except:
        return False

# Main loop - check every ~45 seconds
while True:
    try:
        # Get recent messages from your alert channel (forwarded ones)
        updates = bot.get_chat_history(ALERT_CHANNEL, limit=100)
        
        for msg in updates:
            if not msg.text:
                continue
            usernames = extract_usernames(msg.text)
            for u in usernames:
                if u not in monitored:
                    monitored[u] = time.time()
                    print(f"Added @{u} to monitoring")

        # Check monitored usernames
        now = time.time()
        for username in list(monitored.keys()):
            if now - monitored[username] > 45:   # check every 45 seconds
                if is_available(username):
                    alert = f"""
🔓 **USERNAME AVAILABLE NOW!**

**@{username}** has been deleted and is ready to use!

🕒 Detected: {time.strftime('%H:%M:%S')}
                    """.strip()
                    
                    bot.send_message(ALERT_CHANNEL, alert, parse_mode="Markdown")
                    print(f"ALERT: @{username} is available!")
                    
                    # Remove so we don't spam
                    del monitored[username]
                else:
                    monitored[username] = now   # update timestamp

    except Exception as e:
        print(f"Error: {e}")

    time.sleep(8)
