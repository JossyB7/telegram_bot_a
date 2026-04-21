import os
import logging
import asyncio

from telegram import Update, InputFile
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from telegram.request import HTTPXRequest
from keep_alive import keep_alive

from config import TELEGRAM_BOT_TOKEN, PSD_TEMPLATE_PATH, OUTPUT_DIR, USER_IMAGE_DIR

# ======================
# LOGGING
# ======================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ======================
# HANDLERS (AMHARIC)
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎉 እንኳን ደህና መጡ!\n📸 ፎቶዎን ይላኩ።"
    )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text(
        "⏳ ፎቶው ደርሶናል... ትንሽ ይጠብቁ"
    )

    user_id = update.effective_user.id

    os.makedirs(USER_IMAGE_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    input_path = f"{USER_IMAGE_DIR}/{user_id}.jpg"
    output_path = f"{OUTPUT_DIR}/{user_id}_out.jpg"

    try:
        photo = await update.message.photo[-1].get_file()
        await photo.download_to_drive(input_path)

        from image_processor import process_image_with_psd
        process_image_with_psd(input_path, PSD_TEMPLATE_PATH, output_path)

        with open(output_path, "rb") as f:
            await update.message.reply_photo(
                photo=InputFile(f),
                caption="✅ በተሳካ ሁኔታ አልቋል!"
            )

    except Exception as e:
        logger.error(e)
        await update.message.reply_text("❌ አልተሳካም እንደገና ይሞክሩ")

    finally:
        for p in [input_path, output_path]:
            if os.path.exists(p):
                os.remove(p)

        try:
            await msg.delete()
        except:
            pass


# ======================
# MAIN
# ======================
def main():
    if not TELEGRAM_BOT_TOKEN:
        print("Missing token")
        return

    request = HTTPXRequest(connect_timeout=30, read_timeout=30)

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).request(request).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("Bot is running...")

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    keep_alive()   # keeps Replit alive
    main()
