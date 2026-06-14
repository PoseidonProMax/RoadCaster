FROM python:3.12-slim

# Install system dependencies for phonemizer/soundfile
RUN apt-get update && apt-get install -y \
    espeak-ng \
    libsndfile1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project specification
COPY pyproject.toml .
COPY README.md .

# Install dependencies using pip
RUN pip install --no-cache-dir .

# Copy application files
COPY . .

# Expose port (HF Spaces will bind to the PORT environment variable, default to 7860)
ENV PORT=7860
EXPOSE 7860

# Run the Flask app
CMD ["python", "app.py"]
