# Stage 1: Base image with system dependencies
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # FFmpeg for video processing
    ffmpeg \
    # Build tools for Python packages
    build-essential \
    gcc \
    g++ \
    # Libraries for OpenCV
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1 \
    # Audio processing
    libsndfile1 \
    # Networking
    wget \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Deno (JavaScript runtime for yt-dlp to bypass YouTube bot detection)
# yt-dlp uses Deno by default to execute JavaScript challenges from YouTube
RUN curl -fsSL https://deno.land/install.sh | sh && \
    mv /root/.deno/bin/deno /usr/local/bin/deno && \
    chmod +x /usr/local/bin/deno && \
    deno --version

# Stage 2: Python dependencies
FROM base AS dependencies

WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    # Update yt-dlp to latest version to avoid bot detection issues
    pip install --upgrade yt-dlp

# Stage 3: Final production image
FROM base AS production

WORKDIR /app

# Copy Python packages from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Create necessary directories
RUN mkdir -p downloads fonts models outputs outputs/clips

# Copy application code (includes cookies.txt for YouTube authentication)
COPY . .

# Verify cookies.txt was copied and set correct permissions
RUN if [ -f cookies.txt ]; then \
        echo "✅ cookies.txt found"; \
        ls -lh cookies.txt; \
    else \
        echo "⚠️  WARNING: cookies.txt not found!"; \
    fi

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Ensure cookies.txt is readable by appuser
RUN if [ -f cookies.txt ]; then chmod 644 cookies.txt; fi

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
