FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Environment variables
ENV PYTHONPATH=/app
ENV DATABASE_URL=postgresql://nanobot:password@localhost/memorydb
ENV CONSULT_MODEL=gpt-3.5-turbo

# Expose port
EXPOSE 5000

# Run uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]
