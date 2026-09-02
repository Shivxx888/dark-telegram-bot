import os
import time
import sqlite3
import threading
import requests
from datetime import date
from http.server import HTTPServer, SimpleHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

# ----------------------------
# CONFIGURATION
# ----------------------------
BOT_TOKEN = "8626583730:AAEIdxMaGfrARWCnHlqI6-5Ov4F6HmAVXAM"
BOT_OWNER = "@shivxx"

# Payment Details
UPI_ID = "shivxxbot01234@axl"
FULL_PASS_PRICE_INR = "50"

# Purani API Configuration
OLD_BASE_URL = "https://dark-info.site/test/api.php"
OLD_API_KEY = "JSON-0018"

# Nayi API Configuration
NEW_API_TOKEN = "xpol_Demo_combo_a811c2fb"
NEW_API_HOST = "https://xpolitesupgrade-api.darrify-api.workers.dev/api"

# Daily Free Limit Configuration
DAILY_LIMIT = 2

# ----------------------------
# 1. RENDER DUMMY HTTP SERVER
# ----------------------------
def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# ----------------------------
# 2. DATABASE (LIMIT & VIP TRACKING)
# ----------------------------
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        last_date TEXT,
        search_count INTEGER DEFAULT 0,
        is_vip INTEGER DEFAULT 0
    )
''')
conn.commit()

def check_and_update_limit(user_id):
    today = str(date.today())
    cursor.execute('SELECT last_date, search_count, is_vip FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()

    if not row:
        cursor.execute('INSERT INTO users (user_id, last_date, search_count) VALUES (?, ?, 1)', (user_id, today))
        conn.commit()
        return True

    last_date, count, is_vip = row
    if is_vip == 1:
        return True

    if last_date != today:
        cursor.execute('UPDATE users SET last_date = ?, search_count = 1 WHERE user_id = ?', (today, user_id))
        conn.commit()
        return True
    else:
        if count < DAILY_LIMIT:
            cursor.execute('UPDATE users SET search_count = search_count + 1 WHERE user_id = ?', (user_id,))
            conn.commit()
            return True
        else:
            return False

# ----------------------------
# 3. HELPER FUNCTIONS FOR APIS
# ----------------------------
def fetch_new_api_data(endpoint: str, params: dict):
    params['token'] = NEW_API_TOKEN
    headers = {'Cache-Control': 'no-cache', 'Pragma': 'no-cache'}
    try:
        url = f"{NEW_API_HOST}/{endpoint}"
        response = requests.get(url, params=params, headers=headers, timeout=30)
        if response.status_code == 200:
            return True, response.text
        return False, f"❌ Server Error (Status Code: {response.status_code})"
    except requests.exceptions.Timeout:
        return False, "⚠️ Request Timed Out (Server Slow)"
    except Exception as e:
        return False, f"⚠️ Error: {str(e)}"

def fetch_old_phone_data(phone_input: str):
    phone_num = "91" + phone_input
    params = {
        'key': OLD_API_KEY, 
        'num': phone_num,
        '_ts': int(time.time())
    }
    headers = {'Cache-Control': 'no-cache', 'Pragma': 'no-cache'}
    try:
        response = requests.get(OLD_BASE_URL, params=params, headers=headers, timeout=30)
        if response.status_code == 200:
            return True, response.text
        return False, f"❌ Server Error: Status Code {response.status_code}"
    except requests.exceptions.Timeout:
        return False, "⚠️ Read Timed Out! Purani API slow chal rahi hai."
    except Exception as e:
        return False, f"⚠️ Network Error: {str(e)}"

# ----------------------------
# 4. PAYMENT PROMPT FUNCTION
# ----------------------------
async def send_payment_prompt(chat_id, context: ContextTypes.DEFAULT_TYPE):
    payment_msg = (
        "⚠️ **Daily Free Search Limit Reached!**\n\n"
        f"Aapki aaj ki **{DAILY_LIMIT} free search limit** khatam ho gayi hai.\n\n"
        f"🚀 **Full Pass (Unlimited Access):** ₹{FULL_PASS_PRICE_INR}\n"
        f"📌 **Pay via UPI ID:** `{UPI_ID}`\n\n"
        f"💳 Kisi bhi UPI app se **₹{FULL_PASS_PRICE_INR}** upar di gayi UPI ID par send karein.\n\n"
        f"📩 Payment ka **Screenshot** Owner {BOT_OWNER} ko bhejin, aapka Full Pass instant active ho jayega!"
    )
    await context.bot.send_message(
        chat_id=chat_id,
        text=payment_msg,
        parse_mode="Markdown"
    )

# ----------------------------
# 5. BOT HANDLERS & MENU
# ----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("🚗 Vehicle Info", callback_data="help_vehicle"),
            InlineKeyboardButton("🌐 IP Tracker", callback_data="help_ip")
        ],
        [
            InlineKeyboardButton("🏦 IFSC Lookup", callback_data="help_ifsc"),
            InlineKeyboardButton("📍 Pincode Info", callback_data="help_pincode")
        ],
        [
            InlineKeyboardButton("🎬 Movie Search", callback_data="help_omdb"),
            InlineKeyboardButton("🎵 JioSaavn", callback_data="help_saavn")
        ],
        [
            InlineKeyboardButton("🐙 GitHub User", callback_data="help_github"),
            InlineKeyboardButton("🪙 Crypto Price", callback_data="help_crypto")
        ],
        [
            InlineKeyboardButton("🤖 AI Chat", callback_data="help_ai"),
            InlineKeyboardButton("🌟 Buy Full Pass (₹50)", callback_data="buy_vip_info")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_text = (
        "👋 **Welcome to Ultimate Multi-Utility Bot!**\n\n"
        f"👑 **Owner:** {BOT_OWNER}\n"
        f"🎁 **Free Daily Limit:** {DAILY_LIMIT} Searches/Day\n"
        "• Direct **10-Digit Mobile Number** bhejin (Old API se fetch hoga)\n\n"
        "**Available Commands:**\n"
        "🚗 `/vehicle <RC_Number>` - Vehicle Details\n"
        "🌐 `/ip <IP_Address>` - IP Tracker\n"
        "🏦 `/ifsc <Code>` - Bank IFSC Info\n"
        "📍 `/pincode <Code>` - Pincode Search\n"
        "🎬 `/movie <Title>` - OMDb Movie Info\n"
        "🎵 `/saavn <Query>` - JioSaavn Song Search\n"
        "🐙 `/github <Username>` - GitHub User Info\n"
        "🪙 `/crypto <Coin>` - Crypto Prices\n"
        "📲 `/qr <Text>` - Generate QR Code\n"
        "🍗 `/meal <Recipe>` - Meal Search\n"
        "🤖 `/ask <Query>` - AI Assistant"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)

async def cmd_owner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"👑 **Bot Owner:** {BOT_OWNER}\nKisi bhi query ya Full Pass activation ke liye contact karein.", parse_mode="Markdown")

# ADMIN VIP COMMAND
async def cmd_addvip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.username != "shivxx":
        await update.message.reply_text("❌ Aap Admin nahi hain!")
        return

    if not context.args:
        await update.message.reply_text("❌ Usage: `/addvip <user_id>`\nExample: `/addvip 123456789`", parse_mode="Markdown")
        return

    target_user_id = context.args[0]

    if not target_user_id.isdigit():
        await update.message.reply_text("❌ Valid Numeric User ID enter karein!")
        return

    cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (target_user_id,))
    row = cursor.fetchone()

    if not row:
        cursor.execute('INSERT INTO users (user_id, last_date, search_count, is_vip) VALUES (?, ?, 0, 1)', (target_user_id, str(date.today())))
    else:
        cursor.execute('UPDATE users SET is_vip = 1 WHERE user_id = ?', (target_user_id,))
    
    conn.commit()
    await update.message.reply_text(f"✅ User ID `{target_user_id}` ko successfully **VIP Access** de diya gaya hai! 🚀", parse_mode="Markdown")

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data == "help_vehicle":
        await query.message.reply_text("🚗 **Vehicle Search:** `/vehicle MH02DG4444`", parse_mode="Markdown")
    elif data == "help_ip":
        await query.message.reply_text("🌐 **IP Search:** `/ip 8.8.8.8`", parse_mode="Markdown")
    elif data == "help_ifsc":
        await query.message.reply_text("🏦 **IFSC Search:** `/ifsc SBIN0004843`", parse_mode="Markdown")
    elif data == "help_pincode":
        await query.message.reply_text("📍 **Pincode Search:** `/pincode 110001`", parse_mode="Markdown")
    elif data == "help_omdb":
        await query.message.reply_text("🎬 **Movie Search:** `/movie KGF`", parse_mode="Markdown")
    elif data == "help_saavn":
        await query.message.reply_text("🎵 **JioSaavn Search:** `/saavn Honey Singh`", parse_mode="Markdown")
    elif data == "help_github":
        await query.message.reply_text("🐙 **GitHub User:** `/github octocat`", parse_mode="Markdown")
    elif data == "help_crypto":
        await query.message.reply_text("🪙 **Crypto Search:** `/crypto bitcoin`", parse_mode="Markdown")
    elif data == "help_ai":
        await query.message.reply_text("🤖 **AI Chat:** `/ask Hello`", parse_mode="Markdown")
    elif data == "buy_vip_info":
        await send_payment_prompt(query.from_user.id, context)

# --- PURANI API HANDLER ---
async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_input = update.message.text.strip()

    if user_input.isdigit() and len(user_input) == 10:
        if check_and_update_limit(user_id):
            await update.message.reply_text(f"🔍 Fetching live data from Old API for: `{user_input}`...", parse_mode="Markdown")
            success, res = fetch_old_phone_data(user_input)
            
            if success:
                reply_msg = (
                    f"📱 **Searched Number:** `{user_input}`\n"
                    f"⚡ **Status:** Live Data (Old API)\n\n"
                    f"📥 **JSON Data:**\n```json\n{res}\n```"
                )
            else:
                reply_msg = res

            await update.message.reply_text(reply_msg, parse_mode="Markdown")
        else:
            await send_payment_prompt(user_id, context)
    else:
        await update.message.reply_text("❌ Valid 10-digit number enter karein ya /start dabakar menu dekhein.")

# --- NEW UTILITY COMMAND HANDLERS ---
async def generic_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, endpoint: str, param_name: str, usage_msg: str):
    user_id = update.message.from_user.id
    if not check_and_update_limit(user_id):
        await send_payment_prompt(user_id, context)
        return

    if not context.args:
        await update.message.reply_text(usage_msg, parse_mode="Markdown")
        return

    query_val = " ".join(context.args)
    await update.message.reply_text(f"🔍 Fetching data for `{query_val}`...", parse_mode="Markdown")
    success, res = fetch_new_api_data(endpoint, {param_name: query_val})
    await update.message.reply_text(f"```json\n{res}\n```" if success else res, parse_mode="Markdown")

async def cmd_vehicle(u, c): await generic_command_handler(u, c, "vehicle-master", "rc", "❌ Usage: `/vehicle MH02DG4444`")
async def cmd_ip(u, c): await generic_command_handler(u, c, "ip-master", "ip", "❌ Usage: `/ip 8.8.8.8`")
async def cmd_ifsc(u, c): await generic_command_handler(u, c, "ifsc-master", "ifsc", "❌ Usage: `/ifsc SBIN0004843`")
async def cmd_pincode(u, c): await generic_command_handler(u, c, "pincode", "pincode", "❌ Usage: `/pincode 110001`")
async def cmd_movie(u, c): await generic_command_handler(u, c, "omdb-search", "s", "❌ Usage: `/movie kgf`")
async def cmd_saavn(u, c): await generic_command_handler(u, c, "saavn-search", "query", "❌ Usage: `/saavn honey singh`")
async def cmd_github(u, c): await generic_command_handler(u, c, "github-user", "username", "❌ Usage: `/github octocat`")
async def cmd_crypto(u, c): await generic_command_handler(u, c, "coingecko-price", "ids", "❌ Usage: `/crypto bitcoin`")
async def cmd_qr(u, c): await generic_command_handler(u, c, "qrcode", "data", "❌ Usage: `/qr text_or_link`")
async def cmd_meal(u, c): await generic_command_handler(u, c, "meal-search", "s", "❌ Usage: `/meal chicken`")
async def cmd_ask(u, c):
    user_id = u.message.from_user.id
    if not check_and_update_limit(user_id):
        await send_payment_prompt(user_id, c)
        return
        
    if not c.args:
        await u.message.reply_text("❌ Usage: `/ask Your Question`", parse_mode="Markdown")
        return
    q = " ".join(c.args)
    success, res = fetch_new_api_data("gpt-ask", {"q": q})
    await u.message.reply_text(f"🤖 **AI Response:**\n{res}" if success else res, parse_mode="Markdown")

# ----------------------------
# 6. MAIN EXECUTION
# ----------------------------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Commands Registration
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("owner", cmd_owner))
    app.add_handler(CommandHandler("addvip", cmd_addvip))
    app.add_handler(CommandHandler("vehicle", cmd_vehicle))
    app.add_handler(CommandHandler("ip", cmd_ip))
    app.add_handler(CommandHandler("ifsc", cmd_ifsc))
    app.add_handler(CommandHandler("pincode", cmd_pincode))
    app.add_handler(CommandHandler("movie", cmd_movie))
    app.add_handler(CommandHandler("saavn", cmd_saavn))
    app.add_handler(CommandHandler("github", cmd_github))
    app.add_handler(CommandHandler("crypto", cmd_crypto))
    app.add_handler(CommandHandler("qr", cmd_qr))
    app.add_handler(CommandHandler("meal", cmd_meal))
    app.add_handler(CommandHandler("ask", cmd_ask))

    # Callbacks & Text
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))

    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
