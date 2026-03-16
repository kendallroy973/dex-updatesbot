import requests
import time
import telebot
import threading
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

# ============== CONFIG ==============
BOT_TOKEN = "8687556447:AAElwUSar-ZaVZpk0K-8Cp7nSELlv9EKwt4"
CHANNEL_ID = "@dexupdateslive"

bot = telebot.TeleBot(BOT_TOKEN)

seen_profiles = set()
seen_boosts = set()

# === HEALTH CHECK SERVER (keeps Render awake) ===
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK - DexUpdatesLive Bot running')

def run_health_server():
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('', port), HealthHandler)
    print(f"Health server listening on port {port}")
    server.serve_forever()

# Run health server in background thread
threading.Thread(target=run_health_server, daemon=True).start()

print("🤖 DexUpdatesLive Bot started - polling DexScreener 24/7...")

while True:
    try:
        # 1. New DEX Paid Profiles (new pairs with paid profile)
        profiles_resp = requests.get("https://api.dexscreener.com/token-profiles/latest/v1")
        profiles_resp.raise_for_status()
        profiles = profiles_resp.json()

        for p in profiles:
            token_addr = p.get("tokenAddress")
            if not token_addr or token_addr in seen_profiles:
                continue
            seen_profiles.add(token_addr)

            chain = p.get("chainId", "unknown").upper()
            search_resp = requests.get(f"https://api.dexscreener.com/latest/dex/search?q={token_addr}")
            search_resp.raise_for_status()
            search = search_resp.json()
            pair = search.get("pairs", [{}])[0] if search.get("pairs") else {}

            name = pair.get("baseToken", {}).get("name", "Unknown")
            symbol = pair.get("baseToken", {}).get("symbol", "???")
            fdv = f"${pair.get('fdv', 0):,}" if pair.get('fdv') else "N/A"
            liq = f"${pair.get('liquidity', {}).get('usd', 0):,}" if pair.get('liquidity') else "N/A"
            url = pair.get("url", f"https://dexscreener.com/{chain.lower()}/{token_addr}")
            image = pair.get("info", {}).get("imageUrl")

            caption = f"""
🚨 NEW DEX PAID PROFILE DETECTED!

{name} ({symbol})  
Chain: {chain}  
FDV: {fdv}  
Liquidity: {liq}

[📈 View on DexScreener]({url})
            """.strip()

            if image:
                bot.send_photo(CHANNEL_ID, image, caption=caption, parse_mode="Markdown")
            else:
                bot.send_message(CHANNEL_ID, caption, parse_mode="Markdown")

        # 2. New DEX Trending Boosts
        boosts_resp = requests.get("https://api.dexscreener.com/token-boosts/latest/v1")
        boosts_resp.raise_for_status()
        boosts = boosts_resp.json()

        for b in boosts:
            token_addr = b.get("tokenAddress")
            if not token_addr or token_addr in seen_boosts:
                continue
            seen_boosts.add(token_addr)

            chain = b.get("chainId", "unknown").upper()
            search_resp = requests.get(f"https://api.dexscreener.com/latest/dex/search?q={token_addr}")
            search_resp.raise_for_status()
            search = search_resp.json()
            pair = search.get("pairs", [{}])[0] if search.get("pairs") else {}

            name = pair.get("baseToken", {}).get("name", "Unknown")
            symbol = pair.get("baseToken", {}).get("symbol", "???")
            fdv = f"${pair.get('fdv', 0):,}" if pair.get('fdv') else "N/A"
            url = pair.get("url", f"https://dexscreener.com/{chain.lower()}/{token_addr}")
            image = pair.get("info", {}).get("imageUrl")

            caption = f"""
🔥 NEW TRENDING BOOST ALERT!

{name} ({symbol})  
Chain: {chain}  
FDV: {fdv}

[📈 View on DexScreener]({url})
            """.strip()

            if image:
                bot.send_photo(CHANNEL_ID, image, caption=caption, parse_mode="Markdown")
            else:
                bot.send_message(CHANNEL_ID, caption, parse_mode="Markdown")
