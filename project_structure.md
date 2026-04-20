# Project Structure for Telegram PSD Bot

```
telegram_psd_bot/
├── bot.py                  # Main Telegram bot logic
├── image_processor.py      # Handles PSD parsing and image compositing
├── config.py               # Configuration for bot token, PSD path, etc.
├── requirements.txt        # Python dependencies
├── .env.example            # Example environment variables
└── psd_templates/          # Directory for PSD template files
    └── template.psd        # Example PSD template
```

## `bot.py`
- Initializes the Telegram bot.
- Handles `/start` command.
- Handles incoming photo messages: downloads the photo, calls `image_processor.py`, sends back the processed image.

## `image_processor.py`
- Contains functions to:
    - Load a PSD template.
    - Identify a placeholder layer (e.g., by name).
    - Resize and paste the user's image onto the placeholder's position.
    - Composite the final image.

## `config.py`
- Stores configuration variables like `TELEGRAM_BOT_TOKEN` and `PSD_TEMPLATE_PATH`.

## `requirements.txt`
- Lists all Python packages required for the project (`python-telegram-bot`, `psd-tools`, `Pillow`, `python-dotenv`).

## `.env.example`
- Provides an example of how to set environment variables for the bot token.

## `psd_templates/`
- Directory to store the PSD template files. An example `template.psd` will be placed here.
