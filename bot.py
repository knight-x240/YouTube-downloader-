import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from youtube_utils import get_formats, download_media
from uploader import upload_to_transfer_sh
from config import BOT_TOKEN, TELEGRAM_SIZE_LIMIT

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Send me a YouTube link and I'll help you download it as audio or video in your preferred quality!"
    )

def is_youtube_url(url: str) -> bool:
    return "youtube.com" in url or "youtu.be" in url

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if is_youtube_url(text):
        await update.message.reply_text("🔎 Fetching available formats, please wait…")
        formats = get_formats(text)
        if not formats:
            await update.message.reply_text("❗ Could not fetch available qualities. Please check your link or try another video.")
            return
        buttons = []
        for fmt in formats:
            # Show type, quality, extension, and (if available) size in MB
            size_str = f"{fmt['filesize']//(1024*1024)}MB" if fmt.get('filesize') else "?"
            label = f"{fmt['type'].capitalize()} {fmt['quality']} {fmt['ext']} ({size_str})"
            cb_data = f"{fmt['type']}|{fmt['format_id']}|{fmt.get('filesize',0)}|{text}"
            buttons.append([InlineKeyboardButton(label, callback_data=cb_data)])
        reply_markup = InlineKeyboardMarkup(buttons)
        await update.message.reply_text("🎬 Choose format and quality:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("❗ Please send a valid YouTube URL.")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice, format_id, filesize, url = query.data.split("|", 3)
    filesize = int(filesize)
    downloading_msg = await query.edit_message_text("⬇️ Downloading your selection…")
    try:
        filename = download_media(url, format_id, choice)
        # Check file size
        actual_size = os.path.getsize(filename)
        if actual_size <= TELEGRAM_SIZE_LIMIT:
            await downloading_msg.edit_text("📤 Uploading to Telegram…")
            if choice == "audio":
                await context.bot.send_audio(chat_id=update.effective_chat.id, audio=open(filename, "rb"))
            else:
                await context.bot.send_video(chat_id=update.effective_chat.id, video=open(filename, "rb"))
        else:
            await downloading_msg.edit_text("☁️ File too large for Telegram. Uploading to cloud…")
            link = upload_to_transfer_sh(filename)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"✅ Your file is ready!\nDownload: {link}\n(Expires in 14 days)"
            )
        await downloading_msg.delete()
        os.remove(filename)
    except Exception as e:
        logger.error(e)
        await query.edit_message_text(f"❌ Error: {e}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()

if __name__ == '__main__':
    main()