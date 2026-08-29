import time
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = "8626583730:AAEIdxMaGfrARWCnHlqI6-5Ov4F6HmAVXAM"
BASE_URL = "https://dark-info.site/test/api.php"
API_KEY = "JSON-0018"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hello! Mujhe 10-digit mobile number bhejo, live fresh data fetch karke dunga.")

async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    
    if user_input.isdigit() and len(user_input) == 10:
        phone_num = "91" + user_input
        await update.message.reply_text(f"🔍 Fetching latest live data for: `{user_input}`...", parse_mode="Markdown")
        
        try:
            # Live fresh data fetch karne ke liye timestamp (_ts) parameter
            params = {
                'key': API_KEY, 
                'num': phone_num,
                '_ts': int(time.time())
            }
            
            headers = {'Cache-Control': 'no-cache', 'Pragma': 'no-cache'}
            response = requests.get(BASE_URL, params=params, headers=headers, timeout=12)
            
            if response.status_code == 200:
                reply_msg = (
                    f"📱 **Searched Number:** `{user_input}`\n"
                    f"⚡ **Status:** Live Fresh Data\n\n"
                    f"📥 **Full JSON Data:**\n"
                    f"```json\n{response.text}\n```"
                )
                await update.message.reply_text(reply_msg, parse_mode="Markdown")
            else:
                await update.message.reply_text(f"❌ Server Error: Status Code {response.status_code}")
                
        except Exception as e:
            await update.message.reply_text(f"⚠️ Network Error: {str(e)}")
    else:
        await update.message.reply_text("❌ Valid 10-digit number enter karein.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))
    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
