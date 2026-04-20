# Use Python 3.10
FROM python:3.10-slim

# Install system libraries needed for image processing
RUN apt-get update && apt-get install -y \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Set up a working directory
WORKDIR /app

# Copy your local files to the server
COPY psd_templates .

# Install Python requirements
RUN pip install --no-cache-dir -r requirements.txt

# Run the bot
CMD ["python", "bot.py"]