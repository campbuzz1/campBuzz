import sqlite3
import dateparser
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- CONFIGURATION ---
BOT_TOKEN = "8395675189:AAEO71k7E5RDyA0WZyyxROPc36GnqMfEGMA"  # <--- PASTE YOUR TOKEN

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 **Hello! I am the Smart Event Bot.**\n\n"
        "Just send me a message with the event details.\n"
        "I will try to auto-extract the Title and Date.\n\n"
        "**Try sending this:**\n"
        "`Coding Contest 2026`\n"
        "`Happening next Friday at 10 AM. It will be fun!`",
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    # --- 🧠 THE BRAIN: EXTRACTION LOGIC ---
    lines = text.split('\n')
    
    # 1. Extract Title (Assume it's the first non-empty line)
    title = lines[0].strip() if lines else "Untitled Event"
    
    # 2. Extract Date (Search the whole text for a date)
    # dateparser is very smart. It finds "next friday", "tomorrow", "Jan 25", etc.
    extracted_date_obj = dateparser.parse(text, settings={'PREFER_DATES_FROM': 'future'})
    
    if extracted_date_obj:
        date_str = extracted_date_obj.strftime('%Y-%m-%d') # Format for our DB
    else:
        # Fallback if no date is found
        date_str = "TBD" 

    # 3. Extract Description (Everything after the first line)
    if len(lines) > 1:
        description = "\n".join(lines[1:]).strip()
    else:
        description = text # If only one line, use it as description too

    # --- SAVE TO DB ---
    save_event_to_db(title, date_str, description)
    
    # --- REPLY TO USER ---
    response = (
        f"✅ **Event Received!**\n\n"
        f"📌 **Title:** {title}\n"
        f"📅 **Date:** {date_str}\n"
        f"📝 **Desc:** {description}\n\n"
        f"_Sent to Admin for approval._"
    )
    
    if date_str == "TBD":
        response += "\n\n⚠️ **Warning:** I couldn't find a specific date. Please edit it in the Admin Panel."

    await update.message.reply_text(response, parse_mode='Markdown')

def save_event_to_db(title, date, description):
    conn = sqlite3.connect('events.db')
    c = conn.cursor()
    c.execute("INSERT INTO events (title, date, description) VALUES (?, ?, ?)",
              (title, date, description))
    conn.commit()
    conn.close()

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Commands
    application.add_handler(CommandHandler("start", start))
    
    # Handle ANY text message (Smart Mode)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Smart Bot is listening...")
    application.run_polling()

if __name__ == '__main__':
    main()