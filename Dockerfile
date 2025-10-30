# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose a port for Render health check
EXPOSE 8080

# Run your app
CMD ["python", "main.py"]
