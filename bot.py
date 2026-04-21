import os
import logging
import asyncio
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import TELEGRAM_BOT_TOKEN, PSD_TEMPLATE_PATH, OUTPUT_DIR, USER_IMAGE_DIR

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎉 እንኳን ደህና መጡ!\n📸 እባክዎን ፎቶዎን ይላኩ።")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    processing_msg = await update.message.reply_text("⏳ ፎቶው ደርሶናል! እባክዎን ትንሽ ይጠብቁ...")
    user_id = update.effective_user.id
    timestamp = int(asyncio.get_event_loop().time())

    # Ensure paths exist before using them 
    os.makedirs(USER_IMAGE_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    input_path = os.path.join(USER_IMAGE_DIR, f"{user_id}_{timestamp}.jpg")
    output_path = os.path.join(OUTPUT_DIR, f"{user_id}_{timestamp}_out.jpg")

    try:
        # Download the photo from Telegram
        photo = await update.message.photo[-1].get_file()
        await photo.download_to_drive(input_path)

        # Import the processor here to catch syntax errors immediately
        from image_processor import process_image_with_psd
        process_image_with_psd(input_path, PSD_TEMPLATE_PATH, output_path)

        # Send the final processed photo back
        with open(output_path, "rb") as f:
            await update.message.reply_photo(
                photo=InputFile(f),
                caption="✅ በተሳካ ሁኔታ አልቋል! \n ከአምቢቾ ጎዴ መካነ ኢየሱስ ወጣቶች አገልግሎት።"
            )

    except Exception as e:
        logger.error(f"Execution error: {e}")
        await update.message.reply_text("❌ ይቅርታ አልተሳካም። እባክዎን እንደገና ይሞክሩ")
    finally:
        # CLEANUP: Remove files to save space/RAM
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)
        try:
            await processing_msg.delete()
        except:
            pass

if __name__ == "__main__":
    # Final check for environment variables
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found! Check your Secrets/Env.")
    else:
        app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        
        logger.info("Bot is active...")
        app.run_polling(drop_pending_updates=True)
