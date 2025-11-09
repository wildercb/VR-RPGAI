FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Piper TTS, FFmpeg, and PostgreSQL
RUN apt-get update && apt-get install -y \
    wget \
    libsndfile1 \
    espeak-ng \
    postgresql-client \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Piper TTS
RUN wget -O /tmp/piper.tar.gz https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_amd64.tar.gz \
    && tar -xzf /tmp/piper.tar.gz -C /usr/local/bin/ \
    && rm /tmp/piper.tar.gz \
    && chmod +x /usr/local/bin/piper

# Create directories
RUN mkdir -p /app/tts_models /app/audio_cache

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Download default Piper voice model
RUN mkdir -p /app/tts_models/en_US-lessac-medium \
    && wget -O /app/tts_models/en_US-lessac-medium/en_US-lessac-medium.onnx \
    https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx \
    && wget -O /app/tts_models/en_US-lessac-medium/en_US-lessac-medium.onnx.json \
    https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
