FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY waze_accident_monitor.py .

# Run the application
CMD ["python", "waze_accident_monitor.py"]
