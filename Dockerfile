FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# 1. Install system dependencies
# These are required for OpenCV (libgl) and general image processing (libglib)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 2. Copy the requirements file first
# This allows Docker to cache the 'pip install' step
COPY requirements.txt .

# 3. Install Python dependencies
# Ensure your requirements.txt has the httpx fix discussed!
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy the rest of your application code
# This includes bot.py, config.py, image_processor.py, and the psd_templates folder
COPY . .

# 5. Start the bot
CMD ["python", "bot.py"]
