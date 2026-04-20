FROM python:3.10-slim

# 1. Set the working directory inside the container
WORKDIR /app

# 2. Install system dependencies for OpenCV and rembg
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 3. COPY the requirements file FIRST (for better caching)
COPY requirements.txt .

# 4. NOW run the pip install
RUN pip install --no-cache-dir -r requirements.txt

# 5. COPY everything else (the rest of your code)
COPY . .

# 6. Run the bot
CMD ["python", "bot.py"]
