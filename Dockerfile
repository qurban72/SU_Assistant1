# Base image
FROM python:3.10-slim

# Working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire project
COPY . .

# Expose port (Railway automatically uses $PORT)
ENV PORT=8000
EXPOSE 8000

# Command to run FastAPI
CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 --port ${PORT:-8000}"]

