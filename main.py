import requests
import time
import telebot
import threading
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

# Your config
BOT_TOKEN = "8687556447:AAElwUSar-ZaVZpk0K-8Cp7nSELlv9EKwt4"
CHANNEL_ID = "@dexupdateslive"

bot = telebot.TeleBot(BOT_TOKEN)

seen_profiles = set()
seen_boosts = set()

# Health server to keep Render awake
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK - DexUpdatesLive Bot is running')

def run_health_server():
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('', port), HealthHandler)
    print(f"Health server listening on port {port}")
    server.serve_forever()

threading.Thread(target=run_health_server, daemon=True).start()

print("🤖 Starting DexUpdatesLive Bot - polling every 20s...")

while True:
    try:
        # New DEX Paid Profiles
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
🚨 **NEW DEX PAID PROFILE!**

**{name} ({symbol})**
Chain: {chain}
FDV: {fdv}
Liquidity: {liq}

[📈 View on DexScreener]({url})
            """.strip()

            if image:
                bot.send_photo(CHANNEL_ID, image, caption=caption, parse_mode="Markdown")
            else:
                bot.send_message(CHANNEL_ID, caption, parse_mode="Markdown")

        # New Trending Boosts
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
🔥 **NEW TRENDING BOOST!**

**{name} ({symbol})**
Chain: {chain}
FDV: {fdv}

[📈 View on DexScreener]({url})
            """.strip()

            if image:
                bot.send_photo(CHANNEL_ID, image, caption=caption, parse_mode="Markdown")
            else:
                bot.send_message(CHANNEL_ID, caption, parse_mode="Markdown")

    except Exception as e:
        print(f"Poll error: {str(e)}")

    time.sleep(20)
