# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py ./
COPY realtime_bot_engine.py ./
COPY bot_activity_logger.py ./
COPY historical_data_manager.py ./
COPY backtest_pdf_export.py ./
COPY alpha_ensemble_strategy.py ./
COPY advanced_screening_manager.py ./
COPY ml_data_logger.py ./
COPY ironclad_strategy.py ./
COPY defining_order_strategy.py ./
COPY entrypoint.sh ./
COPY ws_manager/ ./ws_manager/
COPY trading/ ./trading/

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Expose port
EXPOSE 8080

# Test if files exist, then run gunicorn
CMD ["sh", "-c", "ls -la /app/main.py && python3 -c 'import main; print(\"Import successful\")' && gunicorn --bind 0.0.0.0:8080 --workers 1 --threads 4 --timeout 0 --chdir /app main:app"]
