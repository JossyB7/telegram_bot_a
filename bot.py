import logging
import os
import asyncio
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import TELEGRAM_BOT_TOKEN, PSD_TEMPLATE_PATH, OUTPUT_DIR, USER_IMAGE_DIR
from image_processor import process_image_with_psd

# Configure logging to console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Greets the user in Amharic"""
    await update.message.reply_text("🎉 እንኳን ደህና መጡ!\n📸 እባክዎን ፎቶዎን ይላኩ።")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes incoming photos for the choir flyer"""
    processing_msg = await update.message.reply_text("⏳ በሂደት ላይ ነው...")
    user_id = update.effective_user.id
    timestamp = int(asyncio.get_event_loop().time())

    # Define temporary file paths
    input_path = os.path.join(USER_IMAGE_DIR, f"{user_id}_{timestamp}.jpg")
    output_path = os.path.join(OUTPUT_DIR, f"{user_id}_{timestamp}_out.jpg")

    try:
        # Download the user's photo
        photo = await update.message.photo[-1].get_file()
        await photo.download_to_drive(input_path)

        # Call the refined image processor
        processed = process_image_with_psd(input_path, PSD_TEMPLATE_PATH, output_path)

        # Send the final flyer back to the user
        with open(processed, "rb") as f:
            await update.message.reply_photo(
                photo=InputFile(f),
                caption="✅ በተሳካ ሁኔታ አልቋል! የመካነ ኢየሱስ ወጣቶች አገልግሎት"
            )

    except Exception as e:
        logger.error(f"Bot execution error: {e}")
        await update.message.reply_text("❌ ይቅርታ አልተሳካም። እባክዎን በኋላ ይሞክሩ።")
    finally:
        # Clean up files to save disk space
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)
        await processing_msg.delete()


if __name__ == "__main__":
    # Ensure directories exist before starting
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(USER_IMAGE_DIR, exist_ok=True)

    # Initialize and run the Telegram Application
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    logger.info("Bot is active and waiting for photos...")
    app.run_polling()
