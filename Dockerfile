FROM python:3.10-slim

# 1. Set the working directory
WORKDIR /app

# 2. Install updated system dependencies for OpenCV and rembg
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 3. COPY the requirements file FIRST
COPY requirements.txt .

# 4. Install python requirements
RUN pip install --no-cache-dir -r requirements.txt

# 5. COPY everything else
COPY . .

# 6. Run the bot
CMD ["python", "bot.py"]
