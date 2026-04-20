FROM python:3.10-slim

WORKDIR /app

# 1. Install system dependencies for OpenCV and image processing
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 2. Copy the requirements file FIRST (this helps with building speed)
COPY requirements.txt .

# 3. Install the Python libraries
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy EVERYTHING else (your bot.py, config.py, and folders)
COPY . .

# 5. Run the bot
CMD ["python", "bot.py"]


# 5. COPY everything else
COPY . .

# 6. Run the bot
CMD ["python", "bot.py"]
