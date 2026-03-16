import requests
import time
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import threading
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

# CONFIG
BOT_TOKEN = "8687556447:AAElwUSar-ZaVZpk0K-8Cp7nSELlv9EKwt4"
CHANNEL_ID = "@dexupdateslive"

bot = telebot.TeleBot(BOT_TOKEN)

seen_profiles = set()
seen_boosts = set()

# Your referral buy links
TERMINAL_REF = "https://trade.padre.gg/rk/420x69"
AXIOM_REF = "https://axiom.trade/@phineas"
TROJAN_REF = "https://t.me/solana_trojanbot?start=r-totoxapl"

# Health server for Render
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')

def run_health_server():
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('', port), HealthHandler)
    print(f"Health on {port}")
    server.serve_forever()

threading.Thread(target=run_health_server, daemon=True).start()

print("Bot live - polling...")

def get_chain_name(chain_id):
    chain_map = {
        "solana": "SOLANA",
        "ethereum": "ETHEREUM",
        "base": "BASE",
        "bsc": "BSC",
        # add more if needed
    }
    return chain_map.get(chain_id.lower(), chain_id.upper())

def create_buy_buttons(ca):
    markup = InlineKeyboardMarkup(row_width=1)
    if TERMINAL_REF:
        markup.add(InlineKeyboardButton("Buy on Terminal", url=f"{TERMINAL_REF}?ca={ca}" if "?ca=" in TERMINAL_REF else TERMINAL_REF))
    if AXIOM_REF:
        markup.add(InlineKeyboardButton("Buy on Axiom", url=AXIOM_REF))
    if TROJAN_REF:
        markup.add(InlineKeyboardButton("Buy on Trojan", url=TROJAN_REF))
    return markup if markup.keyboard else None

while True:
    try:
        # Paid Profiles (NEW TOKEN)
        profiles_resp = requests.get("https://api.dexscreener.com/token-profiles/latest/v1")
        profiles_resp.raise_for_status()
        profiles = profiles_resp.json()

        for p in profiles:
            token_addr = p.get("tokenAddress")
            if not token_addr or token_addr in seen_profiles:
                continue
            seen_profiles.add(token_addr)

            chain_raw = p.get("chainId", "unknown")
            chain = get_chain_name(chain_raw)
            search_resp = requests.get(f"https://api.dexscreener.com/latest/dex/search?q={token_addr}")
            search_resp.raise_for_status()
            search = search_resp.json()
            pair = search.get("pairs", [{}])[0] if search.get("pairs") else {}

            name = pair.get("baseToken", {}).get("name", "Unknown")
            symbol = pair.get("baseToken", {}).get("symbol", "???")
            ca = pair.get("baseToken", {}).get("address", token_addr)
            fdv = f"${pair.get('fdv', 0):,}" if pair.get('fdv') else "N/A"
            liq = f"${pair.get('liquidity', {}).get('usd', 0):,}" if pair.get('liquidity') else "N/A"
            chart_url = pair.get("url", f"https://dexscreener.com/{chain_raw.lower()}/{token_addr}")
            image = pair.get("info", {}).get("imageUrl")

            # Socials & description (prefer profile if available, fallback to pair)
            info = pair.get("info", {})
            desc = p.get("description") or ""  # from profile if present

            social_text = ""
            websites = info.get("websites", [])
            if websites:
                social_text += f"🌐 Website: Visit [{websites[0].get('url')}]({websites[0].get('url')})\n"

            socials = info.get("socials", [])
            for s in socials:
                plat = s.get("platform", "").lower()
                handle = s.get("handle", "")
                if not handle:
                    continue
                if "telegram" in plat:
                    link = f"https://t.me/{handle.lstrip('@')}"
                    social_text += f"📱 Telegram: Join Group [{handle}]({link})\n"
                elif "twitter" in plat or "x" in plat:
                    link = f"https://x.com/{handle.lstrip('@')}"
                    social_text += f"🐦 Twitter: Follow [{handle}]({link})\n"

            if social_text:
                social_text = "\n" + social_text.strip()

            caption = f"""
🔔 NEW TOKEN

**{name} ({symbol})**
⛓️ CHAIN: {chain}

📝 Contract:
{ca}

📊 Chart: [View on DEXScreener]({chart_url})
{social_text}

{desc}
""".strip()

            markup = create_buy_buttons(ca)

            if image:
                bot.send_photo(CHANNEL_ID, image, caption=caption, parse_mode="Markdown", reply_markup=markup)
            else:
                bot.send_message(CHANNEL_ID, caption, parse_mode="Markdown", reply_markup=markup)

        # Boosts
        boosts_resp = requests.get("https://api.dexscreener.com/token-boosts/latest/v1")
        boosts_resp.raise_for_status()
        boosts = boosts_resp.json()

        for b in boosts:
            token_addr = b.get("tokenAddress")
            if not token_addr or token_addr in seen_boosts:
                continue
            seen_boosts.add(token_addr)

            chain_raw = b.get("chainId", "unknown")
            chain = get_chain_name(chain_raw)
            search_resp = requests.get(f"https://api.dexscreener.com/latest/dex/search?q={token_addr}")
            search_resp.raise_for_status()
            search = search_resp.json()
            pair = search.get("pairs", [{}])[0] if search.get("pairs") else {}

            name = pair.get("baseToken", {}).get("name", "Unknown")
            symbol = pair.get("baseToken", {}).get("symbol", "???")
            ca = pair.get("baseToken", {}).get("address", token_addr)
            fdv = f"${pair.get('fdv', 0):,}" if pair.get('fdv') else "N/A"
            chart_url = pair.get("url", f"https://dexscreener.com/{chain_raw.lower()}/{token_addr}")
            image = pair.get("info", {}).get("imageUrl")

            caption = f"""
🔔 boost

**{name} ({symbol})**
⛓️ CHAIN: {chain}

📝 Contract:
{ca}

📊 Chart: [View on DEXScreener]({chart_url})
""".strip()  # Boosts often have less info; add socials/desc if needed later

            markup = create_buy_buttons(ca)

            if image:
                bot.send_photo(CHANNEL_ID, image, caption=caption, parse_mode="Markdown", reply_markup=markup)
            else:
                bot.send_message(CHANNEL_ID, caption, parse_mode="Markdown", reply_markup=markup)

    except Exception as e:
        print(f"Error: {e}")

    time.sleep(20)
