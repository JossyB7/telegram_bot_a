import os
import logging
import asyncio
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import TELEGRAM_BOT_TOKEN, PSD_TEMPLATE_PATH, OUTPUT_DIR, USER_IMAGE_DIR

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎉 እንኳን ደህና መጡ!\n📸 እባክዎን ፎቶዎን ይላኩ።")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    processing_msg = await update.message.reply_text("⏳ AI ዳራውን እያነሳ ነው (Processing)...")
    user_id = update.effective_user.id
    timestamp = int(asyncio.get_event_loop().time())

    input_path = os.path.join(USER_IMAGE_DIR, f"{user_id}_{timestamp}.jpg")
    output_path = os.path.join(OUTPUT_DIR, f"{user_id}_{timestamp}_out.jpg")

    try:
        # Download
        photo = await update.message.photo[-1].get_file()
        await photo.download_to_drive(input_path)

        # Process (Filter + Zoom + Merge)
        from image_processor import process_image_with_psd
        process_image_with_psd(input_path, PSD_TEMPLATE_PATH, output_path)

        # Reply
        with open(output_path, "rb") as f:
            await update.message.reply_photo(
                photo=InputFile(f),
                caption="✅ በተሳካ ሁኔታ አልቋል! ከወጣቶች አገልግሎጥ።"
            )

    except Exception as e:
        logger.error(f"Execution error: {e}")
        await update.message.reply_text("❌ ይቅርታ አልተሳካም። እባክዎን ፎቶው ግልጽ መሆኑን ያረጋግጡ።")
    finally:
        # CLEANUP: Crucial for Railway stability
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)
        await processing_msg.delete()

if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(USER_IMAGE_DIR, exist_ok=True)
    
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    logger.info("Bot is active...")
    app.run_polling()
